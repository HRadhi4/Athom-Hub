"""A fan remote as a real fan."""

from __future__ import annotations

from typing import Any

from homeassistant.components.fan import FanEntity, FanEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .entity import RemoteEntity, async_setup_remote_platform


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddConfigEntryEntitiesCallback) -> None:
    async_setup_remote_platform(hass, entry, async_add_entities, "fan", "fan", RemoteFan)


class RemoteFan(RemoteEntity, FanEntity):

    def __init__(self, hub, remote) -> None:
        super().__init__(hub, remote)
        self._on = False
        self._osc = False

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        last = await self.async_get_last_state()
        if last is not None:
            self._on = last.state == "on"
            self._osc = bool(last.attributes.get("oscillating"))

    @property
    def supported_features(self) -> FanEntityFeature:
        f = FanEntityFeature.TURN_ON | FanEntityFeature.TURN_OFF
        if self.has("swing"):
            f |= FanEntityFeature.OSCILLATE
        return f

    @property
    def is_on(self) -> bool:
        return self._on

    @property
    def oscillating(self) -> bool | None:
        return self._osc if self.has("swing") else None

    async def async_turn_on(self, percentage: int | None = None, preset_mode: str | None = None, **kwargs: Any) -> None:
        await self.power(True, self._on)
        self._on = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.power(False, self._on)
        self._on = False
        self.async_write_ha_state()

    async def async_oscillate(self, oscillating: bool) -> None:
        if oscillating != self._osc:
            await self.send("swing")
        self._osc = oscillating
        self.async_write_ha_state()
