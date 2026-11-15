"""Button pictures. Run with:  python -m pytest tests"""
import importlib.util
import pathlib

spec = importlib.util.spec_from_file_location("icons", pathlib.Path(__file__).parents[1] / "custom_components" / "athom_hub" / "icons.py")
icons = importlib.util.module_from_spec(spec)
spec.loader.exec_module(icons)


def test_common_buttons_get_pictures():
    g = icons.guess
    assert g("Power 1") == ("mdi:power", icons.RED)
    assert g("Open", "curtain")[0] == "mdi:arrow-expand-horizontal"
    assert g("Close")[0] == "mdi:arrow-collapse-horizontal"
    assert g("Stop")[0] == "mdi:stop-circle-outline"
    assert g("Fan speed")[0] == "mdi:fan-chevron-up"
    assert g("fan_speed")[0] == "mdi:fan-chevron-up"
    assert g("Cool")[0] == "mdi:snowflake"
    assert g("Vol +")[0] == "mdi:volume-plus" or g("Vol +")[0] == "mdi:plus"
    assert g("Volume up")[0] == "mdi:volume-plus"
    assert g("3")[0] == "mdi:numeric-3"
    assert g("Something odd", "tv")[0] == "mdi:television"


def test_hand_picked_picture_wins():
    assert icons.for_button({"name": "Power", "icon": "mdi:star-outline", "colour": "none"}) == ("mdi:star-outline", None)
    assert icons.for_button({"name": "X", "colour": "blue"})[1] == icons.BLUE
