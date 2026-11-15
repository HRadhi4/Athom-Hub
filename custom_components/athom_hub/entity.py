"""The shared part of the entities a remote becomes (climate, cover, media player, fan, light).

None of these devices tell Home Assistant what they are doing, so their state is
"assumed": it is what Athom Hub last sent, kept across restarts.
"""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from . import roles
from .const import DOMAIN, SIGNAL_REMOTES_CHANGED
from .hub import Hub

KIND_NAMES = {"tv": "TV", "ac": "Air conditioner", "fan": "Fan", "curtain": "Curtain or blind", "light": "Light", "audio": "Audio", "other": "Remote"}


def device_info(remote: dict) -> DeviceInfo:
    return DeviceInfo(identifiers={(DOMAIN, remote["id"])}, name=remote["name"], manufacturer="Athom Hub",
                      model=KIND_NAMES.get(remote.get("kind"), "Remote"))


class RemoteEntity(RestoreEntity):
    """One remote as one Home Assistant entity."""

    _attr_has_entity_name = True
    _attr_name = None
    _attr_should_poll = False
    _attr_assumed_state = True

    def __init__(self, hub: Hub, remote: dict) -> None:
        self._hub = hub
        self._remote_id = remote["id"]
        self._attr_unique_id = f"{remote['id']}_main"
        self._attr_device_info = device_info(remote)

    @property
    def remote(self) -> dict:
        return self._hub.store.remotes.get(self._remote_id) or {"buttons": [], "kind": "other"}

    @property
    def available(self) -> bool:
        return self._remote_id in self._hub.store.remotes

    def has(self, *names: str) -> bool:
        by = roles.buttons_by_role(self.remote)
        return any(n in by for n in names)

    async def send(self, role: str, times: int = 1) -> None:
        for i in range(max(0, times)):
            if i:
                await asyncio.sleep(0.4)
            await self._hub.async_press_role(self._remote_id, role)

    async def power(self, on: bool, currently_on: bool) -> None:
        """Turn on or off with the buttons this remote has."""
        if on and self.has("power_on"):
            await self.send("power_on")
        elif not on and self.has("power_off"):
            await self.send("power_off")
        elif on != currently_on:
            await self.send("power")

    @callback
    def refresh(self) -> None:
        """The remote was changed on the page: features may be different now."""
        if self.hass:
            self.async_write_ha_state()


@callback
def async_setup_remote_platform(hass: HomeAssistant, entry: ConfigEntry, add: AddConfigEntryEntitiesCallback,
                                platform: str, domain: str, factory: Callable[[Hub, dict], RemoteEntity]) -> None:
    """Keep one entity per remote of the right kind, in step with the page."""
    hub: Hub = hass.data[DOMAIN]
    known: dict[str, RemoteEntity] = {}

    @callback
    def _sync() -> None:
        wanted = {rid for rid, r in hub.store.remotes.items() if roles.platform_for(r) == platform}
        new = []
        for rid in wanted:
            if rid in known:
                known[rid].refresh()
            else:
                known[rid] = factory(hub, hub.store.remotes[rid])
                new.append(known[rid])
        if new:
            add(new)
        ent_reg = er.async_get(hass)
        for rid in [r for r in known if r not in wanted]:
            entity = known.pop(rid)
            entity_id = ent_reg.async_get_entity_id(domain, DOMAIN, f"{rid}_main")
            if entity_id:
                ent_reg.async_remove(entity_id)

    _sync()
    entry.async_on_unload(async_dispatcher_connect(hass, SIGNAL_REMOTES_CHANGED, _sync))


def restored(last: Any, key: str, default: Any = None) -> Any:
    return last.attributes.get(key, default) if last is not None else default
