"""A light remote as a real light (on and off)."""

from __future__ import annotations

from typing import Any

from homeassistant.components.light import ColorMode, LightEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .entity import RemoteEntity, async_setup_remote_platform


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddConfigEntryEntitiesCallback) -> None:
    async_setup_remote_platform(hass, entry, async_add_entities, "light", "light", RemoteLight)


class RemoteLight(RemoteEntity, LightEntity):
    _attr_color_mode = ColorMode.ONOFF
    _attr_supported_color_modes = {ColorMode.ONOFF}

    def __init__(self, hub, remote) -> None:
        super().__init__(hub, remote)
        self._on = False

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        last = await self.async_get_last_state()
        self._on = last is not None and last.state == "on"

    @property
    def is_on(self) -> bool:
        return self._on

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self.power(True, self._on)
        self._on = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.power(False, self._on)
        self._on = False
        self.async_write_ha_state()
