"""Every remote button as a normal Home Assistant button (dashboards, automations, voice)."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import device_registry as dr, entity_registry as er
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import DOMAIN, SIGNAL_REMOTES_CHANGED
from .hub import Hub

KIND_NAMES = {"tv": "TV", "ac": "Air conditioner", "fan": "Fan", "curtain": "Curtain or blind", "light": "Light", "audio": "Audio", "other": "Remote"}


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddConfigEntryEntitiesCallback) -> None:
    """Make the buttons, and keep them in step with the page."""
    hub: Hub = hass.data[DOMAIN]
    known: dict[str, RemoteButton] = {}

    @callback
    def _sync() -> None:
        wanted: dict[str, tuple[dict, dict]] = {}
        for remote in hub.store.remotes.values():
            for button in remote["buttons"]:
                wanted[f"{remote['id']}_{button['id']}"] = (remote, button)
        new = []
        for key, (remote, button) in wanted.items():
            if key in known:
                known[key].refresh(remote, button)
            else:
                known[key] = RemoteButton(hub, remote, button)
                new.append(known[key])
        if new:
            async_add_entities(new)
        ent_reg = er.async_get(hass)
        for key in [k for k in known if k not in wanted]:
            entity = known.pop(key)
            if entity.entity_id and ent_reg.async_get(entity.entity_id):
                ent_reg.async_remove(entity.entity_id)
        # A remote that was deleted leaves no device behind.
        dev_reg = dr.async_get(hass)
        alive = {(DOMAIN, remote_id) for remote_id in hub.store.remotes}
        for device in dr.async_entries_for_config_entry(dev_reg, entry.entry_id):
            if not device.identifiers & alive:
                dev_reg.async_remove_device(device.id)
            else:
                remote = hub.store.remotes[next(i[1] for i in device.identifiers if i[0] == DOMAIN)]
                if device.name != remote["name"] and not device.name_by_user:
                    dev_reg.async_update_device(device.id, name=remote["name"])

    _sync()
    entry.async_on_unload(async_dispatcher_connect(hass, SIGNAL_REMOTES_CHANGED, _sync))


class RemoteButton(ButtonEntity):
    """One button of one remote."""

    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(self, hub: Hub, remote: dict, button: dict) -> None:
        self._hub = hub
        self._remote_id = remote["id"]
        self._button_id = button["id"]
        self._attr_unique_id = f"{remote['id']}_{button['id']}"
        self._apply(remote, button)

    def _apply(self, remote: dict, button: dict) -> None:
        self._attr_name = button["name"]
        self._attr_icon = "mdi:radio-tower" if button.get("kind") == "rf" else "mdi:remote"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, remote["id"])},
            name=remote["name"],
            manufacturer="Athom Hub",
            model=KIND_NAMES.get(remote.get("kind"), "Remote"),
        )

    @callback
    def refresh(self, remote: dict, button: dict) -> None:
        """The button was renamed on the page."""
        if self._attr_name != button["name"]:
            self._apply(remote, button)
            if self.hass:
                self.async_write_ha_state()

    async def async_press(self) -> None:
        await self._hub.async_press(self._remote_id, self._button_id)
