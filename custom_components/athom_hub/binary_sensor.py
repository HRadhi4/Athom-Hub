"""Smart presence: "someone in the room" and one sensor per named zone, for each Athom radar."""

from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import device_registry as dr, entity_registry as er
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import DOMAIN
from .presence import SIGNAL_PRESENCE, SIGNAL_PRESENCE_SETUP, PresenceManager


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, add: AddConfigEntryEntitiesCallback) -> None:
    manager: PresenceManager = hass.data[f"{DOMAIN}_presence"]
    known: dict[str, PresenceSensor] = {}
    # 0.7.0 tied these sensors to the radar by its network address, which made a second device: tidy it away.
    devs = dr.async_get(hass)
    for device in dr.async_entries_for_config_entry(devs, entry.entry_id):
        if not device.identifiers and device.connections:
            devs.async_update_device(device.id, remove_config_entry_id=entry.entry_id)

    @callback
    def _sync() -> None:
        wanted: dict[str, tuple[str, str | None]] = {}
        for device_id, s in manager.settings.items():
            if not s["enabled"]:
                continue
            wanted[f"{device_id}_room"] = (device_id, None)
            for z in s["zones"]:
                if z["kind"] == "detect":
                    wanted[f"{device_id}_{z['id']}"] = (device_id, z["id"])
        new = []
        for uid, (device_id, zid) in wanted.items():
            if uid in known:
                if known[uid].hass:
                    known[uid].async_write_ha_state()
                continue
            device = dr.async_get(hass).async_get(device_id)
            if not device:
                continue
            known[uid] = PresenceSensor(manager, device, zid)
            new.append(known[uid])
        if new:
            add(new)
        reg = er.async_get(hass)
        for uid in [u for u in known if u not in wanted]:
            known.pop(uid)
            entity_id = reg.async_get_entity_id("binary_sensor", DOMAIN, uid)
            if entity_id:
                reg.async_remove(entity_id)

    _sync()
    entry.async_on_unload(async_dispatcher_connect(hass, SIGNAL_PRESENCE_SETUP, _sync))


class PresenceSensor(BinarySensorEntity):
    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(self, manager: PresenceManager, device: dr.DeviceEntry, zone_id: str | None) -> None:
        self._m = manager
        self._dev = device.id
        self._zone = zone_id
        self._attr_unique_id = f"{device.id}_{zone_id or 'room'}"
        self._attr_device_class = BinarySensorDeviceClass.OCCUPANCY
        radar = device.name_by_user or device.name or "Radar"
        self._attr_device_info = DeviceInfo(identifiers={(DOMAIN, f"presence_{device.id}")}, name=f"{radar} smart presence",
                                            manufacturer="Athom Hub", model="Smart presence", suggested_area=None)

    @property
    def _settings(self) -> dict:
        return self._m.get(self._dev)

    @property
    def name(self) -> str:
        if not self._zone:
            return "Someone in the room"
        z = next((z for z in self._settings["zones"] if z["id"] == self._zone), None)
        return f"Someone at {z['name']}" if z else "Zone"

    @property
    def available(self) -> bool:
        return self._dev in self._m.engines

    @property
    def is_on(self) -> bool:
        e = self._m.engines.get(self._dev)
        if not e:
            return False
        return e.room_on if not self._zone else e.zone_on.get(self._zone, False)

    @property
    def extra_state_attributes(self) -> dict:
        e = self._m.engines.get(self._dev)
        return {"people": e.counts.get(self._zone or "room", 0) if e else 0}

    async def async_added_to_hass(self) -> None:
        @callback
        def _changed(device_id: str) -> None:
            if device_id == self._dev:
                self.async_write_ha_state()
        self.async_on_remove(async_dispatcher_connect(self.hass, SIGNAL_PRESENCE, _changed))
