"""What each remote button does, so a remote can become a real climate, cover,
media player, fan or light in Home Assistant.

No Home Assistant imports: tested on its own.
"""

from __future__ import annotations

import re

# role: plain words shown on the page
ROLE_NAMES = {
    "power": "Power (on and off)",
    "power_on": "Turn on",
    "power_off": "Turn off",
    "open": "Open",
    "close": "Close",
    "stop": "Stop",
    "mode_cool": "Cool mode",
    "mode_heat": "Heat mode",
    "mode_dry": "Dry mode",
    "mode_fan": "Fan only mode",
    "mode_auto": "Auto mode",
    "temp_up": "Temperature up",
    "temp_down": "Temperature down",
    "fan_low": "Fan low",
    "fan_medium": "Fan medium",
    "fan_high": "Fan high",
    "fan_auto": "Fan auto",
    "fan_speed": "Fan speed (next)",
    "swing": "Swing",
    "vol_up": "Volume up",
    "vol_down": "Volume down",
    "mute": "Mute",
    "ch_up": "Channel up",
    "ch_down": "Channel down",
    "play": "Play",
    "pause": "Pause",
    "play_pause": "Play / pause",
}

# Which roles make sense for which kind of remote (in the order shown on the page).
KIND_ROLES = {
    "ac": ["power", "power_on", "power_off", "mode_cool", "mode_heat", "mode_dry", "mode_fan", "mode_auto", "temp_up", "temp_down",
           "fan_low", "fan_medium", "fan_high", "fan_auto", "fan_speed", "swing"],
    "curtain": ["open", "close", "stop"],
    "tv": ["power", "power_on", "power_off", "vol_up", "vol_down", "mute", "ch_up", "ch_down", "play", "pause", "play_pause"],
    "audio": ["power", "power_on", "power_off", "vol_up", "vol_down", "mute", "play", "pause", "play_pause"],
    "fan": ["power", "power_on", "power_off", "fan_speed", "fan_low", "fan_medium", "fan_high", "swing"],
    "light": ["power", "power_on", "power_off"],
    "other": [],
}

# What each kind becomes in Home Assistant.
KIND_PLATFORM = {"ac": "climate", "curtain": "cover", "tv": "media_player", "audio": "media_player", "fan": "fan", "light": "light"}

# (words that must all be there, role). First match wins: longer rules first.
_RULES = [
    (("power", "on"), "power_on"), (("power", "off"), "power_off"), (("turn", "on"), "power_on"), (("turn", "off"), "power_off"),
    (("on", "off"), "power"), (("power",), "power"),
    (("vol", "up"), "vol_up"), (("volume", "up"), "vol_up"), (("vol", "+"), "vol_up"), (("vol", "down"), "vol_down"),
    (("volume", "down"), "vol_down"), (("vol", "-"), "vol_down"), (("mute",), "mute"),
    (("ch", "up"), "ch_up"), (("channel", "up"), "ch_up"), (("ch", "down"), "ch_down"), (("channel", "down"), "ch_down"),
    (("temp", "up"), "temp_up"), (("temperature", "up"), "temp_up"), (("temp", "down"), "temp_down"), (("temperature", "down"), "temp_down"),
    (("temp", "+"), "temp_up"), (("temp", "-"), "temp_down"),
    (("fan", "speed"), "fan_speed"), (("fan", "low"), "fan_low"), (("fan", "medium"), "fan_medium"), (("fan", "mid"), "fan_medium"),
    (("fan", "high"), "fan_high"), (("fan", "auto"), "fan_auto"), (("fan", "only"), "mode_fan"),
    (("play", "pause"), "play_pause"), (("open",), "open"), (("close",), "close"), (("stop",), "stop"),
    (("cool",), "mode_cool"), (("cold",), "mode_cool"), (("heat",), "mode_heat"), (("dry",), "mode_dry"),
    (("auto",), "mode_auto"), (("swing",), "swing"), (("low",), "fan_low"), (("medium",), "fan_medium"), (("mid",), "fan_medium"),
    (("high",), "fan_high"), (("up",), "temp_up"), (("down",), "temp_down"), (("play",), "play"), (("pause",), "pause"),
    (("fan",), "mode_fan"),
]


def _words(name: str) -> set[str]:
    text = re.sub(r"([a-z])([A-Z])", r"\1 \2", str(name or ""))
    text = re.sub(r"([+\-])", r" \1 ", text.lower())
    return set(re.sub(r"[^a-z0-9+\-]+", " ", text).split())


def guess(name: str, kind: str) -> str | None:
    """The most likely role of a button on this kind of remote, or None."""
    allowed = KIND_ROLES.get(kind or "other", [])
    words = _words(name)
    for need, role in _RULES:
        if all(w in words for w in need):
            if role in allowed:
                return role
            # "fan" on a fan remote means power, "up"/"down" on a TV mean volume
            if role == "mode_fan" and kind == "fan":
                return "power"
            if role in ("temp_up", "temp_down") and "vol_up" in allowed:
                return "vol_up" if role == "temp_up" else "vol_down"
            return None
    return None


def role_of(button: dict, kind: str) -> str | None:
    """The role chosen on the page, else the guess. "none" means no role on purpose."""
    chosen = button.get("role")
    if chosen == "none":
        return None
    if chosen in ROLE_NAMES:
        return chosen
    return guess(button.get("name", ""), kind)


def buttons_by_role(remote: dict) -> dict[str, list[dict]]:
    """{role: [buttons]} for a remote. A role can have several buttons (they are used in turn)."""
    out: dict[str, list[dict]] = {}
    for button in remote.get("buttons", []):
        role = role_of(button, remote.get("kind", "other"))
        if role:
            out.setdefault(role, []).append(button)
    return out


def platform_for(remote: dict) -> str | None:
    """Which Home Assistant entity this remote becomes, if it has the buttons for it."""
    platform = KIND_PLATFORM.get(remote.get("kind", "other"))
    if not platform:
        return None
    have = set(buttons_by_role(remote))
    need = {"cover": {"open", "close"}, "climate": {"power", "power_on", "power_off"},
            "media_player": {"power", "power_on", "power_off"}, "fan": {"power", "power_on", "power_off"},
            "light": {"power", "power_on", "power_off"}}[platform]
    return platform if have & need else None
