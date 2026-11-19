"""Smarter presence for Athom radar sensors (LD2450).

The sensor reports where up to three people are (x left/right, y away from it, in millimetres).
From those positions Athom Hub adds what the sensor itself cannot do:
  * a room shape and a range: anyone outside them (behind a wall, in the next room) is ignored;
  * ignore areas: spots where a fan, a curtain or a plant keeps "moving";
  * a small-movement filter: someone must really walk in before the room counts as taken;
  * the motion sensor (PIR) mixed in, and separate delays for on and off;
  * named zones (Bed, Sofa, Desk…), each with its own "someone here" and its own off delay.
Everything is worked out here, on this Home Assistant; nothing on the sensor is changed.
"""

from __future__ import annotations

import math
import re
from collections.abc import Callable
from typing import Any

from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.helpers import device_registry as dr, entity_registry as er
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.event import async_call_later, async_track_state_change_event
from homeassistant.helpers.storage import Store

from .const import DOMAIN

STORAGE_KEY = f"{DOMAIN}_presence"
SIGNAL_PRESENCE = f"{DOMAIN}_presence"          # (device_id) something to show changed
SIGNAL_PRESENCE_SETUP = f"{DOMAIN}_presence_setup"  # the settings changed: entities may come or go

DEFAULTS: dict[str, Any] = {
    "enabled": False,
    "room": None,          # {"x1", "x2", "y1", "y2"} in mm, or None for the whole view
    "range": 6000,         # mm: anyone further away is ignored
    "zones": [],           # [{"id", "name", "kind": "detect" | "ignore", "x1", "x2", "y1", "y2", "off_delay"}]
    "min_move": 300,       # mm someone must move before the room counts as taken (0 = off)
    "use_pir": True,       # the motion sensor also turns presence on, and keeps it on
    "on_delay": 0,         # seconds someone must be there before it turns on
    "off_delay": 30,       # seconds with nobody before it turns off
}
MAX_ZONES = 8


def clean_settings(data: dict[str, Any]) -> dict[str, Any]:
    """Settings from the page, made safe."""
    out = dict(DEFAULTS)
    out["enabled"] = bool(data.get("enabled", True))

    def box(z: Any) -> dict[str, int] | None:
        if not isinstance(z, dict):
            return None
        try:
            x1, x2, y1, y2 = (int(round(float(z[k]))) for k in ("x1", "x2", "y1", "y2"))
        except (KeyError, TypeError, ValueError):
            return None
        x1, x2, y1, y2 = min(x1, x2), max(x1, x2), max(0, min(y1, y2)), max(0, max(y1, y2))
        if x2 - x1 < 200 or y2 - y1 < 200:
            return None
        lim = lambda v, a, b: max(a, min(b, v))  # noqa: E731
        return {"x1": lim(x1, -8000, 8000), "x2": lim(x2, -8000, 8000), "y1": lim(y1, 0, 8000), "y2": lim(y2, 0, 8000)}

    def num(key: str, lo: float, hi: float) -> float:
        try:
            v = float(data.get(key, DEFAULTS[key]))
        except (TypeError, ValueError):
            v = DEFAULTS[key]
        return max(lo, min(hi, v))

    out["room"] = box(data.get("room"))
    out["range"] = int(num("range", 500, 8000))
    out["min_move"] = int(num("min_move", 0, 1500))
    out["use_pir"] = bool(data.get("use_pir", DEFAULTS["use_pir"]))
    out["on_delay"] = num("on_delay", 0, 60)
    out["off_delay"] = num("off_delay", 0, 3600)
    zones, seen = [], set()
    for z in (data.get("zones") or [])[:MAX_ZONES]:
        b = box(z)
        if not b:
            continue
        zid = re.sub(r"[^a-z0-9]", "", str(z.get("id") or ""))[:12] or f"z{len(zones) + 1}"
        while zid in seen:
            zid += "x"
        seen.add(zid)
        kind = "ignore" if z.get("kind") == "ignore" else "detect"
        name = re.sub(r"\s+", " ", str(z.get("name") or "")).strip()[:40] or ("Ignore area" if kind == "ignore" else f"Zone {len(zones) + 1}")
        try:
            off = max(0.0, min(3600.0, float(z.get("off_delay", out["off_delay"]))))
        except (TypeError, ValueError):
            off = out["off_delay"]
        zones.append({"id": zid, "name": name, "kind": kind, "off_delay": off, **b})
    out["zones"] = zones
    return out


def inside(b: dict[str, int] | None, x: float, y: float) -> bool:
    return b is None or (b["x1"] <= x <= b["x2"] and b["y1"] <= y <= b["y2"])


class RadarEngine:
    """Works out presence for one radar sensor."""

    def __init__(self, hass: HomeAssistant, device_id: str, settings: dict[str, Any]) -> None:
        self.hass = hass
        self.device_id = device_id
        self.settings = settings
        self.ents: dict[str, str] = {}
        self._unsub: Callable | None = None
        self._first: dict[int, tuple[float, float]] = {}     # where each target slot was first seen
        self._confirmed: set[int] = set()
        self.room_on = False
        self.zone_on: dict[str, bool] = {}
        self.counts: dict[str, int] = {"room": 0}
        self.people: list[dict[str, Any]] = []
        self._timers: dict[str, Callable] = {}

    # ------------------------------------------------------------------ wiring
    def start(self) -> None:
        reg = er.async_get(self.hass)
        for e in er.async_entries_for_device(reg, self.device_id):
            for n in (1, 2, 3):
                for k in ("x", "y"):
                    if e.entity_id.endswith(f"_target_{n}_{k}"):
                        self.ents[f"t{n}{k}"] = e.entity_id
            if e.entity_id.startswith("binary_sensor.") and e.entity_id.endswith("_pir_sensor"):
                self.ents["pir"] = e.entity_id
        watch = list(self.ents.values())
        if watch:
            self._unsub = async_track_state_change_event(self.hass, watch, self._changed)
        self.update()

    def stop(self) -> None:
        if self._unsub:
            self._unsub()
            self._unsub = None
        for cancel in self._timers.values():
            cancel()
        self._timers.clear()

    @callback
    def _changed(self, _event: Event) -> None:
        self.update()

    def _num(self, key: str) -> float | None:
        st = self.hass.states.get(self.ents.get(key, ""))
        try:
            return float(st.state) if st else None
        except ValueError:
            return None

    # ------------------------------------------------------------------ the sums
    @callback
    def update(self) -> None:
        s = self.settings
        ignore = [z for z in s["zones"] if z["kind"] == "ignore"]
        detect = [z for z in s["zones"] if z["kind"] == "detect"]
        pir_st = self.hass.states.get(self.ents.get("pir", ""))
        pir = bool(s["use_pir"] and pir_st and pir_st.state == "on")
        people = []
        for n in (1, 2, 3):
            x, y = self._num(f"t{n}x"), self._num(f"t{n}y")
            if x is None or y is None or (x == 0 and y == 0):
                self._first.pop(n, None)
                self._confirmed.discard(n)
                continue
            y = abs(y)
            why = None
            if math.hypot(x, y) > s["range"]:
                why = "too far"
            elif not inside(s["room"], x, y):
                why = "outside the room"
            elif any(inside(z, x, y) for z in ignore):
                why = "in an ignore area"
            if why:
                self._first.pop(n, None)
                self._confirmed.discard(n)
                people.append({"n": n, "x": x, "y": y, "counted": False, "why": why})
                continue
            start = self._first.setdefault(n, (x, y))
            if n not in self._confirmed and (s["min_move"] <= 0 or self.room_on or pir
                                             or math.hypot(x - start[0], y - start[1]) >= s["min_move"]):
                self._confirmed.add(n)
            counted = n in self._confirmed
            people.append({"n": n, "x": x, "y": y, "counted": counted, "why": None if counted else "not walked in yet"})
        self.people = people
        here = [p for p in people if p["counted"]]
        self.counts = {"room": len(here)}
        self._set("room", bool(here) or pir, s["on_delay"], s["off_delay"])
        for z in detect:
            n = sum(1 for p in here if inside(z, p["x"], p["y"]))
            self.counts[z["id"]] = n
            self._set(z["id"], n > 0, 0, z["off_delay"])
        async_dispatcher_send(self.hass, SIGNAL_PRESENCE, self.device_id)

    def _get(self, key: str) -> bool:
        return self.room_on if key == "room" else self.zone_on.get(key, False)

    def _put(self, key: str, value: bool) -> None:
        if key == "room":
            self.room_on = value
        else:
            self.zone_on[key] = value
        async_dispatcher_send(self.hass, SIGNAL_PRESENCE, self.device_id)

    def _set(self, key: str, want: bool, on_delay: float, off_delay: float) -> None:
        now = self._get(key)
        pending = self._timers.get(key)
        if want == now:
            if pending:
                pending()
                self._timers.pop(key, None)
            return
        if pending:
            return                                  # already waiting to change
        delay = on_delay if want else off_delay
        if delay <= 0:
            self._put(key, want)
            return

        @callback
        def _fire(_now: Any) -> None:
            self._timers.pop(key, None)
            self._put(key, want)
            self.update()
        self._timers[key] = async_call_later(self.hass, delay, _fire)


class PresenceManager:
    """All radar sensors with smart presence turned on, and their saved settings."""

    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass
        self._store: Store[dict[str, Any]] = Store(hass, 1, STORAGE_KEY)
        self.settings: dict[str, dict[str, Any]] = {}
        self.engines: dict[str, RadarEngine] = {}

    async def async_load(self) -> None:
        data = await self._store.async_load() or {}
        self.settings = {k: clean_settings(v) for k, v in (data.get("devices") or {}).items()}

    @callback
    def start(self) -> None:
        for device_id, s in self.settings.items():
            self._start_one(device_id, s)

    @callback
    def stop(self) -> None:
        for engine in self.engines.values():
            engine.stop()
        self.engines.clear()

    def _start_one(self, device_id: str, s: dict[str, Any]) -> None:
        old = self.engines.pop(device_id, None)
        if old:
            old.stop()
        if s["enabled"] and dr.async_get(self.hass).async_get(device_id):
            engine = RadarEngine(self.hass, device_id, s)
            self.engines[device_id] = engine
            engine.start()

    async def async_save(self, device_id: str, data: dict[str, Any]) -> dict[str, Any]:
        s = clean_settings(data)
        self.settings[device_id] = s
        await self._store.async_save({"devices": self.settings})
        self._start_one(device_id, s)
        async_dispatcher_send(self.hass, SIGNAL_PRESENCE_SETUP)
        return s

    def get(self, device_id: str) -> dict[str, Any]:
        return self.settings.get(device_id) or dict(DEFAULTS)

    def live(self, device_id: str) -> dict[str, Any]:
        e = self.engines.get(device_id)
        if not e:
            return {"running": False}
        return {"running": True, "room": e.room_on, "zones": e.zone_on, "counts": e.counts, "people": e.people}
