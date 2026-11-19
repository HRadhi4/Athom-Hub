"""SmartIR air conditioner code sets. Run with:  python -m pytest tests

smartir_1320.json is SmartIR's public Haier code file (github.com/smartHomeHub/SmartIR)."""
import importlib.util
import json
import pathlib
import sys
import types

root = pathlib.Path(__file__).parents[1] / "custom_components" / "athom_hub"
pkg = types.ModuleType("athom_hub_test"); pkg.__path__ = [str(root)]; sys.modules["athom_hub_test"] = pkg
for name in ("codes", "smartir"):
    spec = importlib.util.spec_from_file_location(f"athom_hub_test.{name}", root / f"{name}.py")
    mod = importlib.util.module_from_spec(spec); sys.modules[f"athom_hub_test.{name}"] = mod; spec.loader.exec_module(mod)
codes = sys.modules["athom_hub_test.codes"]
smartir = sys.modules["athom_hub_test.smartir"]
DATA = json.loads((pathlib.Path(__file__).parent / "smartir_1320.json").read_text())


def test_table_and_lookup():
    t = smartir.table_from_smartir(DATA)
    assert t["maker"] == "Haier" and t["min"] == 16 and t["max"] == 30
    assert "cool" in t["modes"] and "auto" in t["fans"]
    assert smartir.count(t) == 301
    code, fan, temp = smartir.code_for(t, "cool", "auto", 24)
    assert code == DATA["commands"]["cool"]["auto"]["24"] and temp == 24
    assert smartir.code_for(t, "cool", "turbo", 40)[1:] == ("auto", 30)
    assert smartir.code_for(t, "off", None, None)[0] == DATA["commands"]["off"]


def test_every_setting_is_recognised_when_heard():
    t = smartir.table_from_smartir(DATA)
    table = {k: codes.broadlink_decode(v)["timings"] for k, v in smartir.all_codes(t).items()}
    for key in [("off",), ("cool", "auto", 24), ("cool", "high", 17), ("heat", "low", 30), ("dry", "mid", 22)]:
        heard = [int(v * 1.08) for v in table[key]]          # a real receiver is never exact
        assert codes.best_match([[120, -300, 80, -9000] + heard], table) == key
    assert smartir.describe_setting(("cool", "auto", 24)) == "Cool 24° · fan auto"


def test_other_files_are_refused():
    try:
        smartir.table_from_smartir({"supportedController": "Xiaomi", "commandsEncoding": "Raw"})
    except smartir.TableError:
        return
    raise AssertionError


def test_real_remote_off_is_read_from_its_power_bit():
    """A real remote's "off" carries its temperature too, so it is not the table's own off code."""
    t = smartir.table_from_smartir(DATA)
    cand = {k: codes.broadlink_decode(v)["timings"] for k, v in smartir.all_codes(t).items()}
    assert all(codes.read_setting([v], cand) == k for k, v in cand.items())
    off = codes._frames_bits(cand[("off",)])[0]
    frame = codes.split_frames(cand[("cool", "auto", 22)])[0]
    ons = [codes._frames_bits(v)[0] for k, v in cand.items() if k != ("off",)]
    power = [i for i in range(len(off)) if all(b[i] == ons[0][i] for b in ons if len(b) == len(off)) and off[i] != ons[0][i]]
    assert power
    gaps = [abs(x) for x in frame[1::2]]
    short, long = min(gaps), max(g for g in gaps if g <= 4 * min(gaps))
    real_off = list(frame)
    for i in power:
        assert i % 2 == 1
        real_off[i] = -(long if off[i] == "1" else short)
    assert codes.read_setting([real_off], cand) == ("off",)
    assert codes.read_setting([frame], cand) == ("cool", "auto", 22)
    assert codes.read_setting([codes.nec()[:]] if hasattr(codes, "nec") else [[9000, -4500] + [560, -560] * 32 + [560, -40000]], cand) is None


def test_hand_edited_tables_are_checked():
    good = smartir.table_from_smartir(DATA)
    assert smartir.clean_table(good) == good                       # a real table comes back unchanged
    for bad in ({"codes": {"off": good["codes"]["off"]}},           # no modes, fans or min
                {"codes": {"x": 1}}, {"codes": []}, "nope",
                {**good, "codes": {**good["codes"], "off": "not a code"}}):
        try:
            smartir.clean_table(bad)
        except smartir.TableError:
            continue
        raise AssertionError(bad)
    odd = {**good, "min": "cold", "fans": ["auto", 7], "modes": good["modes"] + ["party"]}
    fixed = smartir.clean_table(odd)
    assert fixed["min"] == 16 and 7 not in fixed["fans"] and "party" not in fixed["modes"]
    assert smartir.count(fixed) == smartir.count(good)
