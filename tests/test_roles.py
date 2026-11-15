"""What buttons do. Run with:  python -m pytest tests"""
import importlib.util
import pathlib

spec = importlib.util.spec_from_file_location("roles", pathlib.Path(__file__).parents[1] / "custom_components" / "athom_hub" / "roles.py")
roles = importlib.util.module_from_spec(spec)
spec.loader.exec_module(roles)


def test_ac_buttons():
    g = lambda n: roles.guess(n, "ac")
    assert [g(n) for n in ["Power 1", "Power 2", "Cool", "Dry", "Fan", "Auto", "Fan speed", "High", "Swing", "Light 1", "Temp +", "Temp down"]] == \
        ["power", "power", "mode_cool", "mode_dry", "mode_fan", "mode_auto", "fan_speed", "fan_high", "swing", None, "temp_up", "temp_down"]


def test_other_kinds():
    assert roles.guess("Open", "curtain") == "open"
    assert roles.guess("Close", "curtain") == "close"
    assert roles.guess("Power", "tv") == "power"
    assert roles.guess("Vol +", "tv") == "vol_up"
    assert roles.guess("Up", "tv") == "vol_up"
    assert roles.guess("Fan", "fan") == "power"
    assert roles.guess("Cool", "tv") is None


def test_platforms_and_choices():
    ac = {"kind": "ac", "buttons": [{"name": "Power 1"}, {"name": "Power 2"}, {"name": "Cool"}, {"name": "Light", "role": "none"}]}
    by = roles.buttons_by_role(ac)
    assert len(by["power"]) == 2 and "mode_cool" in by
    assert roles.platform_for(ac) == "climate"
    assert roles.platform_for({"kind": "curtain", "buttons": [{"name": "Stop"}]}) is None
    assert roles.platform_for({"kind": "other", "buttons": [{"name": "Power"}]}) is None
    assert roles.role_of({"name": "Something", "role": "mute"}, "tv") == "mute"
