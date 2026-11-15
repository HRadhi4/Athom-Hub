"""A TV or audio remote as a real media player."""

from __future__ import annotations

from homeassistant.components.media_player import MediaPlayerDeviceClass, MediaPlayerEntity, MediaPlayerEntityFeature, MediaPlayerState
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .entity import RemoteEntity, async_setup_remote_platform

F = MediaPlayerEntityFeature


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddConfigEntryEntitiesCallback) -> None:
    async_setup_remote_platform(hass, entry, async_add_entities, "media_player", "media_player", RemotePlayer)


class RemotePlayer(RemoteEntity, MediaPlayerEntity):

    def __init__(self, hub, remote) -> None:
        super().__init__(hub, remote)
        self._on = False
        self._muted = False

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        last = await self.async_get_last_state()
        if last is not None:
            self._on = last.state not in ("off", "unavailable", "unknown")
            self._muted = bool(last.attributes.get("is_volume_muted"))

    @property
    def device_class(self) -> MediaPlayerDeviceClass:
        return MediaPlayerDeviceClass.TV if self.remote.get("kind") == "tv" else MediaPlayerDeviceClass.SPEAKER

    @property
    def supported_features(self) -> MediaPlayerEntityFeature:
        f = F.TURN_ON | F.TURN_OFF
        if self.has("vol_up", "vol_down"):
            f |= F.VOLUME_STEP
        if self.has("mute"):
            f |= F.VOLUME_MUTE
        if self.has("ch_up"):
            f |= F.NEXT_TRACK
        if self.has("ch_down"):
            f |= F.PREVIOUS_TRACK
        if self.has("play", "play_pause"):
            f |= F.PLAY
        if self.has("pause", "play_pause"):
            f |= F.PAUSE
        return f

    @property
    def state(self) -> MediaPlayerState:
        return MediaPlayerState.ON if self._on else MediaPlayerState.OFF

    @property
    def is_volume_muted(self) -> bool:
        return self._muted

    async def async_turn_on(self) -> None:
        await self.power(True, self._on)
        self._on = True
        self.async_write_ha_state()

    async def async_turn_off(self) -> None:
        await self.power(False, self._on)
        self._on = False
        self.async_write_ha_state()

    async def async_volume_up(self) -> None:
        await self.send("vol_up")

    async def async_volume_down(self) -> None:
        await self.send("vol_down")

    async def async_mute_volume(self, mute: bool) -> None:
        if mute != self._muted:
            await self.send("mute")
        self._muted = mute
        self.async_write_ha_state()

    async def async_media_next_track(self) -> None:
        await self.send("ch_up")

    async def async_media_previous_track(self) -> None:
        await self.send("ch_down")

    async def async_media_play(self) -> None:
        await self.send("play" if self.has("play") else "play_pause")

    async def async_media_pause(self) -> None:
        await self.send("pause" if self.has("pause") else "play_pause")
