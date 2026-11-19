"""Smart presence sums, with a pretend Home Assistant. Run with:  python -m pytest tests"""
import importlib.util
import pathlib
import sys
import types

# A tiny stand-in for the parts of Home Assistant that presence.py uses.
ha = types.ModuleType("homeassistant"); sys.modules.setdefault("homeassistant", ha)
core = types.ModuleType("homeassistant.core"); core.callback = lambda f: f; core.Event = object; core.HomeAssistant = object
sys.modules["homeassistant.core"] = core
helpers = types.ModuleType("homeassistant.helpers"); sys.modules["homeassistant.helpers"] = helpers
for name in ("device_registry", "entity_registry", "dispatcher", "event", "storage"):
    m = types.ModuleType(f"homeassistant.helpers.{name}"); sys.modules[m.__name__] = m; setattr(helpers, name, m)
sys.modules["homeassistant.helpers.dispatcher"].async_dispatcher_send = lambda *a: None
TIMERS = []
def call_later(hass, delay, fn):
    TIMERS.append((delay, fn)); return lambda: TIMERS.remove((delay, fn)) if (delay, fn) in TIMERS else None
sys.modules["homeassistant.helpers.event"].async_call_later = call_later
sys.modules["homeassistant.helpers.event"].async_track_state_change_event = lambda *a: None
sys.modules["homeassistant.helpers.storage"].Store = object

root = pathlib.Path(__file__).parents[1] / "custom_components" / "athom_hub"
pkg = types.ModuleType("ah"); pkg.__path__ = [str(root)]; sys.modules["ah"] = pkg
for name in ("const", "presence"):
    spec = importlib.util.spec_from_file_location(f"ah.{name}", root / f"{name}.py")
    mod = importlib.util.module_from_spec(spec); sys.modules[f"ah.{name}"] = mod; spec.loader.exec_module(mod)
P = sys.modules["ah.presence"]


class State:
    def __init__(self, s): self.state = s
class Hass:
    def __init__(self): self.v = {}
    @property
    def states(self): return self
    def get(self, eid): return State(str(self.v[eid])) if eid in self.v else None


def engine(**settings):
    h = Hass()
    s = P.clean_settings({"enabled": True, **settings})
    e = P.RadarEngine(h, "dev", s)
    e.ents = {f"t{n}{k}": f"sensor.t{n}{k}" for n in (1, 2, 3) for k in "xy"}
    e.ents["pir"] = "binary_sensor.pir"
    h.v["binary_sensor.pir"] = "off"
    def at(n, x, y): h.v[f"sensor.t{n}x"], h.v[f"sensor.t{n}y"] = x, y
    TIMERS.clear()
    return e, at


def test_settings_are_made_safe():
    s = P.clean_settings({"range": 99999, "zones": [{"name": "  Bed  ", "x1": 500, "x2": -500, "y1": 3000, "y2": 1000}, {"x1": 0, "x2": 10, "y1": 0, "y2": 10}], "room": "x"})
    assert s["range"] == 8000 and s["room"] is None and len(s["zones"]) == 1
    z = s["zones"][0]
    assert z["name"] == "Bed" and z["x1"] == -500 and z["y1"] == 1000 and z["kind"] == "detect"


def test_someone_who_walks_in_counts_and_a_fan_does_not():
    e, at = engine(off_delay=0, use_pir=False, min_move=300)
    at(1, 1000, 2000); e.update()
    assert not e.room_on                         # appeared, but has not moved: could be a fan
    at(1, 1050, 2050); e.update()
    assert not e.room_on
    at(1, 1000, 2600); e.update()
    assert e.room_on                             # walked half a metre: a person


def test_outside_the_room_and_ignore_areas():
    e, at = engine(off_delay=0, min_move=0, use_pir=False, room={"x1": -2000, "x2": 2000, "y1": 0, "y2": 4000},
                   zones=[{"name": "Fan", "kind": "ignore", "x1": 1000, "x2": 2000, "y1": 0, "y2": 1000}])
    at(1, 0, 5000); e.update()
    assert not e.room_on and e.people[0]["why"] == "outside the room"
    at(1, 1500, 500); e.update()
    assert not e.room_on and e.people[0]["why"] == "in an ignore area"
    at(1, 0, 2000); e.update()
    assert e.room_on


def test_zone_and_off_delay():
    e, at = engine(off_delay=30, min_move=0, use_pir=False, zones=[{"id": "bed", "name": "Bed", "x1": -1000, "x2": 1000, "y1": 2000, "y2": 4000, "off_delay": 0}])
    at(1, 0, 3000); e.update()
    assert e.room_on and e.zone_on["bed"]
    at(1, 0, 0); e.update()
    assert not e.zone_on["bed"]                  # the zone has no delay
    assert e.room_on and TIMERS and TIMERS[0][0] == 30   # the room waits 30 s
    TIMERS[0][1](None)
    assert not e.room_on


def test_motion_sensor_keeps_it_on():
    e, at = engine(off_delay=0, use_pir=True)
    e.hass.v["binary_sensor.pir"] = "on"; e.update()
    assert e.room_on
