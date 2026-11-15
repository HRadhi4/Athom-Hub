"""A curtain or blind remote as a real cover."""

from __future__ import annotations

from typing import Any

from homeassistant.components.cover import CoverDeviceClass, CoverEntity, CoverEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .entity import RemoteEntity, async_setup_remote_platform


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddConfigEntryEntitiesCallback) -> None:
    async_setup_remote_platform(hass, entry, async_add_entities, "cover", "cover", RemoteCover)


class RemoteCover(RemoteEntity, CoverEntity):
    _attr_device_class = CoverDeviceClass.CURTAIN

    def __init__(self, hub, remote) -> None:
        super().__init__(hub, remote)
        self._closed: bool | None = None

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        last = await self.async_get_last_state()
        if last is not None and last.state in ("open", "closed"):
            self._closed = last.state == "closed"

    @property
    def supported_features(self) -> CoverEntityFeature:
        f = CoverEntityFeature(0)
        if self.has("open"):
            f |= CoverEntityFeature.OPEN
        if self.has("close"):
            f |= CoverEntityFeature.CLOSE
        if self.has("stop"):
            f |= CoverEntityFeature.STOP
        return f

    @property
    def is_closed(self) -> bool | None:
        return self._closed

    async def async_open_cover(self, **kwargs: Any) -> None:
        await self.send("open")
        self._closed = False
        self.async_write_ha_state()

    async def async_close_cover(self, **kwargs: Any) -> None:
        await self.send("close")
        self._closed = True
        self.async_write_ha_state()

    async def async_stop_cover(self, **kwargs: Any) -> None:
        await self.send("stop")
        self._closed = False
        self.async_write_ha_state()
