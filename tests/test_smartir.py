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
