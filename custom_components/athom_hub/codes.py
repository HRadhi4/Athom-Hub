"""Remote codes as plain pen-and-paper timings.

Everything in Athom Hub is kept as *raw timings*: a list of whole microseconds,
positive while the signal is on (a pulse) and negative while it is off (a gap).
That is what Home Assistant hands to an emitter and what a receiver reports, so
a code learned on any device can be replayed by any other.

This file has no Home Assistant imports on purpose: it is tested on its own.
"""

from __future__ import annotations

import json
import re

import base64
import binascii
from statistics import median

# One Broadlink time unit in microseconds (the device counts 269 units per 8192 µs).
BROADLINK_TICK = 8192 / 269

KIND_IR = "ir"
KIND_RF = "rf"

IR_CARRIER = 38_000          # nearly every household remote
RF_FREQUENCY = 433_920_000   # the Athom RF/IR remote's radio

# Broadlink packet types
_BL_IR = 0x26
_BL_RF_433 = 0xB2
_BL_RF_315 = 0xD7

MAX_GAP_US = 120_000          # a gap longer than this is only waiting
MAX_SEND_TIMINGS = 2400       # keep one transmission well inside what an ESP32 takes


class CodeError(ValueError):
    """The text is not a remote code we can read."""


def broadlink_decode(code: str) -> dict:
    """Turn a code learned by a Broadlink (base64 text) into raw timings.

    Returns {"kind": "ir"|"rf", "frequency": Hz or None, "repeat": extra sends,
    "timings": [...]}. Raises CodeError when the text is not a Broadlink code.
    """
    text = (code or "").strip()
    if text.startswith("b64:"):
        text = text[4:]
    try:
        data = base64.b64decode(text + "=" * (-len(text) % 4), validate=False)
    except (binascii.Error, ValueError) as err:
        raise CodeError("not base64") from err
    if len(data) < 6:
        raise CodeError("too short")
    kind_byte, repeat = data[0], data[1]
    if kind_byte == _BL_IR:
        kind, frequency = KIND_IR, None
    elif kind_byte in (_BL_RF_433, _BL_RF_315) or kind_byte >= 0xB0:
        kind, frequency = KIND_RF, 315_000_000 if kind_byte == _BL_RF_315 else RF_FREQUENCY
    else:
        raise CodeError(f"unknown Broadlink code type 0x{kind_byte:02x}")
    end = min(len(data), 4 + data[2] + 256 * data[3])
    timings: list[int] = []
    i, on = 4, True
    while i < end:
        units = data[i]
        i += 1
        if units == 0:
            if i + 1 >= end:
                break
            units = 256 * data[i] + data[i + 1]
            i += 2
        micros = max(1, round(units * BROADLINK_TICK))
        timings.append(micros if on else -micros)
        on = not on
    timings = tidy(timings)
    if len(timings) < 4:
        raise CodeError("no signal in the code")
    return {"kind": kind, "frequency": frequency, "repeat": repeat, "timings": timings}


def broadlink_encode(timings: list[int], kind: str = KIND_IR, repeat: int = 0) -> str:
    """Raw timings as a Broadlink code (used by the tests, and handy for moving back)."""
    out = bytearray([_BL_IR if kind == KIND_IR else _BL_RF_433, repeat & 0xFF, 0, 0])
    for value in timings:
        units = max(1, round(abs(value) / BROADLINK_TICK))
        if units > 255:
            out += bytes([0, (units >> 8) & 0xFF, units & 0xFF])
        else:
            out.append(units)
    size = len(out) - 4
    out[2], out[3] = size & 0xFF, size >> 8
    return base64.b64encode(bytes(out)).decode()


def normalize_capture(timings: list[int]) -> list[int]:
    """Signed timings from what a receiver reports.

    Some receivers report only lengths (all positive): those alternate on, off.
    Some radio receivers report on and off swapped, so a capture starts with a
    gap: a signal always starts with a pulse, so swap them back."""
    out = [int(v) for v in timings if int(v)]
    if out and all(v > 0 for v in out):
        out = [v if i % 2 == 0 else -v for i, v in enumerate(out)]
    if out and out[0] < 0:
        out = [-v for v in out]
    return out


def tidy(timings: list[int]) -> list[int]:
    """Make a timing list regular: starts with a pulse, strictly alternates,
    no zeros, and ends with a gap that is long enough to repeat after but not endless."""
    out: list[int] = []
    for value in timings:
        value = int(value)
        if value == 0:
            continue
        if not out:
            if value < 0:
                continue                      # leading silence
            out.append(value)
        elif (out[-1] > 0) == (value > 0):
            out[-1] += value                  # two pulses (or two gaps) in a row are one
        else:
            out.append(value)
    if not out:
        return []
    if out[-1] > 0:
        out.append(-default_gap(out))
    else:
        out[-1] = -min(abs(out[-1]), MAX_GAP_US)
    return out


def default_gap(timings: list[int]) -> int:
    """The silence to leave after a frame that came without one.

    Radio remotes repeat a frame after a pause of about 30 short pulses; infrared
    remotes after some tens of milliseconds. Both are covered by "30 short pulses,
    at least 8 ms"."""
    marks = [v for v in timings if v > 0]
    if not marks:
        return 10_000
    short = min(marks)
    return int(min(MAX_GAP_US, max(8_000, 30 * short)))


def for_sending(timings: list[int], sends: int) -> list[list[int]]:
    """The transmissions to make for `sends` sends of one frame.

    Frames are put back to back in one transmission where they fit, so the pause
    between repeats is exact; very long codes are sent one after another."""
    frame = tidy(timings)
    sends = max(1, min(int(sends), 20))
    if not frame:
        return []
    per_go = max(1, MAX_SEND_TIMINGS // len(frame))
    out = []
    while sends > 0:
        n = min(per_go, sends)
        out.append(frame * n)
        sends -= n
    return out


def similar(a: list[int], b: list[int], tolerance: float = 0.3) -> bool:
    """Are two captures the same button? Same number of pulses and each one
    within `tolerance` (the last gap is ignored: it is only the pause after)."""
    if not a or abs(len(a) - len(b)) > 1:
        return False
    n = min(len(a), len(b))
    if n < 4:
        return False
    for x, y in zip(a[: n - 1], b[: n - 1]):
        if (x > 0) != (y > 0):
            return False
        x, y = abs(x), abs(y)
        if abs(x - y) > tolerance * max(x, y) + 120:
            return False
    return True


def average(group: list[list[int]]) -> list[int]:
    """One clean frame out of several captures of the same button."""
    n = min(len(g) for g in group)
    out = [int(median(g[i] for g in group)) for i in range(n)]
    return tidy(out)


def looks_like_signal(timings: list[int], kind: str) -> bool:
    """Throw away noise: too short, or pulses no remote makes."""
    marks = [v for v in timings if v > 0]
    if kind == KIND_RF:
        if len(timings) < 24 or len(timings) > 1200:
            return False
        return bool(marks) and 60 <= median(marks) <= 3000 and max(marks) <= 25_000
    return len(timings) >= 12 and bool(marks) and max(marks) <= 30_000


def pick_learned(captures: list[list[int]], kind: str) -> dict | None:
    """Choose what was learned from everything the receiver heard.

    A radio receiver hears noise all the time, so a radio code only counts when
    the same frame arrives at least three times (remotes repeat while the button
    is held). An infrared receiver is quiet: the first full frame is the code.
    Returns {"timings": [...], "heard": n} or None when nothing is sure yet."""
    frames = [tidy(c) for c in captures]
    frames = [f for f in frames if looks_like_signal(f, kind)]
    if not frames:
        return None
    groups: list[list[list[int]]] = []
    for frame in frames:
        for group in groups:
            if similar(group[0], frame):
                group.append(frame)
                break
        else:
            groups.append([frame])
    if kind == KIND_RF:
        best = max(groups, key=len)
        if len(best) < 3:
            return None
        return {"timings": average(best), "heard": len(best)}
    # Infrared: the longest frame that came first (short "repeat" frames follow a long one).
    longest = max(len(g[0]) for g in groups)
    for group in groups:
        if len(group[0]) >= 0.6 * longest:
            return {"timings": average(group) if len(group) > 1 else group[0], "heard": len(group)}
    return None


def describe(timings: list[int]) -> dict:
    """A few plain numbers about a code, for showing next to a button."""
    total = sum(abs(v) for v in timings[:-1]) if timings else 0
    return {"pulses": (len(timings) + 1) // 2, "ms": round(total / 1000, 1)}


# ---------------------------------------------------------------- self-test codes
# Made-up codes for the safe self-test: no real device answers to them.

def nec_frame(address: int, command: int) -> list[int]:
    """One infrared NEC frame (the most common TV remote format)."""
    out = [9000, -4500]
    for byte in (address & 0xFF, ~address & 0xFF, command & 0xFF, ~command & 0xFF):
        for bit in range(8):
            out += [562, -1687 if (byte >> bit) & 1 else -562]
    out += [562, -40_000]
    return out


def ev1527_frame(code: int, short: int = 350) -> list[int]:
    """One 433 MHz frame in the EV1527 format most cheap radio remotes use."""
    out: list[int] = []
    for bit in range(23, -1, -1):
        out += [3 * short, -short] if (code >> bit) & 1 else [short, -3 * short]
    out += [short, -31 * short]
    return out


def split_frames(timings: list[int], min_gap: int = 5000) -> list[list[int]]:
    """Cut one long capture into frames at every long silence."""
    frames, current = [], []
    for value in tidy(timings):
        current.append(value)
        if value < 0 and -value >= min_gap:
            frames.append(current)
            current = []
    if current:
        frames.append(tidy(current))
    return frames


def heard_frame(captures: list[list[int]], frame: list[int]) -> bool:
    """Did any capture contain this frame?"""
    want = tidy(frame)
    return any(similar(want, piece) for capture in captures for piece in split_frames(capture))


def best_match(captures: list[list[int]], candidates: dict) -> object | None:
    """Which of the candidate codes ({key: timings}) was heard, if any (the closest one)."""
    best, best_score = None, None
    pieces = [piece for capture in captures for piece in split_frames(capture)]
    for key, timings in candidates.items():
        want = tidy(timings)
        for piece in pieces:
            if similar(want, piece):
                score = sum(abs(abs(x) - abs(y)) for x, y in zip(want[:-1], piece))
                if best_score is None or score < best_score:
                    best, best_score = key, score
    return best


# ---------------------------------------------------------------- reading an AC remote by its bits
# A real AC remote sends its whole setting every press. Its "off" also carries the temperature and fan
# it shows, so it seldom equals the one "off" code in a code table. Comparing bit by bit finds it anyway.

def symbols(frame: list[int]) -> str:
    """One frame as text: two characters per pulse-and-gap pair, "1" for long, "0" for short."""
    def classes(values: list[int]) -> list[str]:
        if not values:
            return []
        lo = min(values)
        usual = [v for v in values if v <= 4 * lo]
        hi = max(usual)
        if hi < 1.6 * lo:
            return ["0"] * len(values)
        cut = (lo + hi) / 2
        return ["1" if v > cut else "0" for v in values]
    frame = tidy(frame)
    marks = [abs(v) for v in frame[0::2]]
    gaps = [abs(v) for v in frame[1::2]][: len(marks)]
    gaps = gaps[:-1] if len(gaps) == len(marks) else gaps      # the pause at the end says nothing
    m, g = classes(marks), classes(gaps) + ["0"]
    return "".join(a + b for a, b in zip(m, g))


def _frames_bits(timings: list[int]) -> list[str]:
    return [symbols(f) for f in split_frames(timings) if len(f) >= 16]


def _distance(a: str, b: str) -> float | None:
    """Share of symbols that differ, or None when the frames are not the same kind."""
    if abs(len(a) - len(b)) > 4 or min(len(a), len(b)) < 16:
        return None
    n = min(len(a), len(b))
    return sum(x != y for x, y in zip(a[:n], b[:n])) / n


def read_setting(captures: list[list[int]], candidates: dict, off_key=("off",), most: float = 0.15) -> object | None:
    """Which setting of an AC code table ({key: timings}) a real remote just sent, if any.

    Off is told apart by the bits that are the same in every "on" code and different in the "off" code
    (the power bit); everything else (mode, fan, temperature) is the closest "on" code."""
    heard = [symbols(f) for c in captures for f in split_frames(c) if len(f) >= 16]
    if not heard:
        return None
    table = {key: _frames_bits(t) for key, t in candidates.items()}
    best, best_d = None, None
    for key, frames in table.items():
        if key == off_key:
            continue
        for h in heard:
            for f in frames:
                d = _distance(h, f)
                if d is not None and (best_d is None or d < best_d):
                    best, best_d = key, d
    off_frames = table.get(off_key) or []
    for h in heard:
        for off in off_frames:
            d_off = _distance(h, off)
            if d_off is None:
                continue
            ons = [f for key, frames in table.items() if key != off_key for f in frames if len(f) == len(off)]
            power = [i for i in range(len(off)) if ons and all(f[i] == ons[0][i] for f in ons) and off[i] != ons[0][i]]
            if power and len(h) >= len(off):
                if sum(h[i] == off[i] for i in power) >= 0.6 * len(power):
                    return off_key
            elif d_off <= most and (best_d is None or d_off < best_d):
                return off_key
    return best if best_d is not None and best_d <= most else None


MAX_PASTE = 2_000_000
_LINE = re.compile(r"^\s*(?:\"?([^:=,\"]{1,60}?)\"?\s*[:=,]\s*)?\"?((?:b64:)?[A-Za-z0-9+/=_-]{16,})\"?,?\s*$")


def parse_broadlink(text: str) -> list[tuple[str, dict[str, object]]]:
    """Broadlink codes as people have them, as a list of (remote name, {button: code or [codes]}).

    Accepts a JSON export ({"data": {remote: {button: code}}}, {remote: {button: code}} or {button: code})
    or plain lines like "power: JgBQAAAB..." (a line with just a code becomes Button 1, Button 2, ...).
    """
    text = (text or "").strip()
    if not text:
        return []
    if len(text) > MAX_PASTE:
        raise CodeError("That is too much text. Paste one remote at a time.")
    if text[0] in "{[":
        try:
            data = json.loads(text)
        except ValueError as err:
            raise CodeError("That looks like a file but could not be read.") from err
        if isinstance(data, dict) and isinstance(data.get("data"), dict):
            data = data["data"]
        if not isinstance(data, dict):
            raise CodeError("No Broadlink codes were found in that file.")
        if data and all(isinstance(v, dict) for v in data.values()):
            return [(str(k)[:60], {str(b)[:60]: c for b, c in v.items() if isinstance(c, (str, list))}) for k, v in data.items() if v]
        commands = {str(k)[:60]: v for k, v in data.items() if isinstance(v, (str, list))}
        return [("Pasted remote", commands)] if commands else []
    commands: dict[str, object] = {}
    n = 0
    for line in text.splitlines():
        m = _LINE.match(line)
        if not m:
            continue
        n += 1
        label, code = (m.group(1) or "").strip(), m.group(2)
        if label.lower() == "b64":  # a bare "b64:..." line has no name
            label, code = "", f"b64:{code}"
        label = label or f"Button {n}"
        commands[label if label not in commands else f"{label} {n}"] = code
    return [("Pasted remote", commands)] if commands else []


def each_code(commands: dict[str, object]):
    """Every (button name, code text) of one remote; a button with several codes gives name 1, name 2, ..."""
    for name, value in sorted(commands.items()):
        values = value if isinstance(value, list) else [value]
        values = [v for v in values if isinstance(v, str)]
        for n, text in enumerate(values):
            yield (name if len(values) == 1 else f"{name} {n + 1}"), text


