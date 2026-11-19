"""Tests for the code maths. Run with:  python -m pytest tests"""
import importlib.util
import pathlib
import random

spec = importlib.util.spec_from_file_location("codes", pathlib.Path(__file__).parents[1] / "custom_components" / "athom_hub" / "codes.py")
codes = importlib.util.module_from_spec(spec)
spec.loader.exec_module(codes)

# The start of nearly every NEC code learned by a Broadlink: 9 ms on, 4.5 ms off.
NEC_BROADLINK = "JgBQAAABKZQTEhMSExITEhMSExITEhMSEzcTNxM3EzcTNxM3EzcTNxMSEzcTEhMSExITEhMSExITNxMSEzcTNxM3EzcTNxM3EwAFGQABKUoTAAxSAAENBQ=="


def nec(address=0x04, command=0x08):
    t = [9000, -4500]
    bits = [address, address ^ 0xFF, command, command ^ 0xFF]
    for byte in bits:
        for i in range(8):
            t += [560, -1690 if (byte >> i) & 1 else -560]
    return t + [560, -40000]


def test_broadlink_infrared_code_becomes_timings():
    d = codes.broadlink_decode(NEC_BROADLINK)
    assert d["kind"] == "ir" and d["frequency"] is None and d["repeat"] == 0
    t = d["timings"]
    assert 8800 < t[0] < 9300 and -4700 < t[1] < -4300          # the NEC header
    assert all((v > 0) == (i % 2 == 0) for i, v in enumerate(t))  # pulse, gap, pulse, gap…
    assert t[-1] < 0
    assert codes.broadlink_decode("b64:" + NEC_BROADLINK)["timings"] == t


def test_broadlink_round_trip_keeps_every_pulse_within_one_unit():
    t = nec()
    back = codes.broadlink_decode(codes.broadlink_encode(t))["timings"]
    assert len(back) == len(t)
    assert all(abs(a - b) <= 31 for a, b in zip(t, back))
    rf = [350, -1050, 1050, -350] * 12 + [350, -10850]
    d = codes.broadlink_decode(codes.broadlink_encode(rf, kind="rf", repeat=7))
    assert d["kind"] == "rf" and d["frequency"] == 433_920_000 and d["repeat"] == 7
    assert all(abs(a - b) <= 31 for a, b in zip(rf, d["timings"]))


def test_bad_codes_are_refused():
    for bad in ("", "hello", "AAAA", "!!!!"):
        try:
            codes.broadlink_decode(bad)
        except codes.CodeError:
            continue
        raise AssertionError(bad)


def test_tidy_makes_a_regular_frame():
    assert codes.tidy([-500, 300, 200, -100, 0, -100, 400]) == [500, -200, 400, -12000]
    assert codes.tidy([300, -900_000]) == [300, -120_000]        # endless waiting is cut
    assert codes.tidy([]) == []
    assert codes.default_gap([350, -1050, 350]) == 10_500        # about 30 short pulses


def test_sending_repeats_back_to_back():
    frame = [350, -1050] * 24 + [350, -10850]
    goes = codes.for_sending(frame, 6)
    assert len(goes) == 1 and goes[0] == frame * 6
    long = [500, -500] * 700
    goes = codes.for_sending(long, 3)
    assert len(goes) == 3 and all(len(g) <= codes.MAX_SEND_TIMINGS for g in goes)
    assert codes.for_sending([], 3) == []


def test_radio_learning_needs_the_same_frame_three_times_among_noise():
    random.seed(4)
    frame = [350, -1050, 1050, -350] * 12 + [350]
    wobble = lambda f: [int(v * random.uniform(0.9, 1.1)) for v in f]
    noise = lambda: [random.choice([1, -1]) * random.randint(40, 4000) for _ in range(random.randint(5, 80))]
    heard = [noise(), wobble(frame), noise(), noise(), wobble(frame)]
    assert codes.pick_learned(heard, "rf") is None                # twice is not enough
    got = codes.pick_learned(heard + [noise(), wobble(frame)], "rf")
    assert got and got["heard"] == 3
    assert codes.similar(got["timings"], codes.tidy(frame))
    assert -11_600 < got["timings"][-1] < -9_000                 # the pause to repeat after: about 30 short pulses


def test_infrared_learning_takes_the_full_frame_not_the_repeat_marks():
    full = nec()[:-1]
    repeat = [9000, -2250, 560]
    got = codes.pick_learned([full, repeat, repeat], "ir")
    assert got and codes.similar(got["timings"], codes.tidy(full))
    assert codes.pick_learned([repeat], "ir") is None
    assert codes.describe(got["timings"])["pulses"] == 34


def test_self_test_frames_are_found_in_noise():
    c = codes
    ir = c.nec_frame(0x5A, 0xC3)
    assert len(ir) == 68
    rf = c.ev1527_frame(0xA5F00F)
    assert len(rf) == 50
    noise = [120, -300, 80, -2000, 15000]
    joined = noise + [-9000] + rf + rf + rf
    assert c.heard_frame([noise, joined], rf)
    assert c.heard_frame([[int(v * 1.1) for v in ir]], ir)
    assert not c.heard_frame([noise], rf)
    assert not c.heard_frame([c.ev1527_frame(0x123456)], rf)


def test_swapped_radio_capture_is_put_right():
    rf = codes.ev1527_frame(0x3C5A96)
    flipped = [-v for v in rf] * 3
    assert codes.normalize_capture(flipped)[0] > 0
    assert codes.heard_frame([codes.normalize_capture(flipped)], rf)
    assert codes.normalize_capture([900, 450, 560]) == [900, -450, 560]


def test_pasted_broadlink_lines_become_one_remote():
    text = f"power: {NEC_BROADLINK}\nvolume up = b64:{NEC_BROADLINK}\n{NEC_BROADLINK}\nnot a code\n"
    [(name, cmds)] = codes.parse_broadlink(text)
    assert name == "Pasted remote" and list(cmds) == ["power", "volume up", "Button 3"]
    assert codes.broadlink_decode(cmds["volume up"])["kind"] == "ir"


def test_a_saved_file_of_broadlink_codes():
    import json
    text = json.dumps({"data": {"living_tv": {"power": NEC_BROADLINK, "vol": [NEC_BROADLINK, NEC_BROADLINK]}, "empty": {}}})
    found = codes.parse_broadlink(text)
    assert [n for n, _ in found] == ["living_tv"]
    assert [label for label, _ in codes.each_code(found[0][1])] == ["power", "vol 1", "vol 2"]


def test_nothing_to_read():
    assert codes.parse_broadlink("") == [] and codes.parse_broadlink("hello\nworld") == []
