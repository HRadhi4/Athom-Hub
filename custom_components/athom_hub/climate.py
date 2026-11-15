"""An air conditioner remote as a real thermostat."""

from __future__ import annotations

import asyncio
from typing import Any

from homeassistant.components.climate import ClimateEntity, ClimateEntityFeature, HVACMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.event import async_track_state_change_event

from .entity import RemoteEntity, async_setup_remote_platform, restored

MODE_ROLES = {HVACMode.COOL: "mode_cool", HVACMode.HEAT: "mode_heat", HVACMode.DRY: "mode_dry",
              HVACMode.FAN_ONLY: "mode_fan", HVACMode.AUTO: "mode_auto"}
FAN_ROLES = {"low": "fan_low", "medium": "fan_medium", "high": "fan_high", "auto": "fan_auto"}


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddConfigEntryEntitiesCallback) -> None:
    async_setup_remote_platform(hass, entry, async_add_entities, "climate", "climate", RemoteClimate)


class RemoteClimate(RemoteEntity, ClimateEntity):
    """Modes, temperature, fan and swing, as far as the learned buttons allow."""

    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_min_temp = 16
    _attr_max_temp = 30
    _attr_target_temperature_step = 1

    def __init__(self, hub, remote) -> None:
        super().__init__(hub, remote)
        self._mode = HVACMode.OFF
        self._last_on: HVACMode | None = None
        self._target = 24.0
        self._fan: str | None = None
        self._swing = "off"
        self._unsub_sensor = None
        self._sensor: str | None = None

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        last = await self.async_get_last_state()
        if last is not None and last.state in [m.value for m in HVACMode]:
            self._mode = HVACMode(last.state)
            self._target = float(restored(last, ATTR_TEMPERATURE, 24) or 24)
            self._fan = restored(last, "fan_mode")
            self._swing = restored(last, "swing_mode", "off") or "off"
            self._last_on = HVACMode(restored(last, "last_on", "cool")) if restored(last, "last_on") in [m.value for m in HVACMode] else None
        self._follow_sensor()

    async def async_will_remove_from_hass(self) -> None:
        if self._unsub_sensor:
            self._unsub_sensor()

    @callback
    def _follow_sensor(self) -> None:
        sensor = self.remote.get("temp_sensor")
        if sensor == self._sensor:
            return
        if self._unsub_sensor:
            self._unsub_sensor()
            self._unsub_sensor = None
        self._sensor = sensor
        if sensor:
            self._unsub_sensor = async_track_state_change_event(self.hass, [sensor], lambda _e: self.async_write_ha_state())

    @callback
    def refresh(self) -> None:
        if self.hass:
            self._follow_sensor()
        super().refresh()

    # ---------------------------------------------------------------- what it can do
    @property
    def hvac_modes(self) -> list[HVACMode]:
        modes = [m for m, role in MODE_ROLES.items() if self.has(role)]
        return [HVACMode.OFF, *(modes or [HVACMode.COOL])]

    @property
    def supported_features(self) -> ClimateEntityFeature:
        f = ClimateEntityFeature.TURN_ON | ClimateEntityFeature.TURN_OFF
        if self.has("temp_up") and self.has("temp_down"):
            f |= ClimateEntityFeature.TARGET_TEMPERATURE
        if self.fan_modes:
            f |= ClimateEntityFeature.FAN_MODE
        if self.has("swing"):
            f |= ClimateEntityFeature.SWING_MODE
        return f

    @property
    def fan_modes(self) -> list[str] | None:
        modes = [m for m, role in FAN_ROLES.items() if self.has(role)]
        return modes or None

    @property
    def swing_modes(self) -> list[str] | None:
        return ["off", "on"] if self.has("swing") else None

    # ---------------------------------------------------------------- what it is doing
    @property
    def hvac_mode(self) -> HVACMode:
        return self._mode if self._mode in self.hvac_modes else (HVACMode.OFF if self._mode == HVACMode.OFF else self.hvac_modes[-1])

    @property
    def target_temperature(self) -> float | None:
        return self._target if self.has("temp_up") and self.has("temp_down") else None

    @property
    def current_temperature(self) -> float | None:
        state = self.hass.states.get(self._sensor) if self._sensor else None
        try:
            return float(state.state) if state else None
        except ValueError:
            return None

    @property
    def fan_mode(self) -> str | None:
        return self._fan if self.fan_modes else None

    @property
    def swing_mode(self) -> str | None:
        return self._swing if self.has("swing") else None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {"last_on": self._last_on.value if self._last_on else None}

    # ---------------------------------------------------------------- changing it
    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        was_off = self._mode == HVACMode.OFF
        if hvac_mode == HVACMode.OFF:
            await self.power(False, not was_off)
            self._mode = HVACMode.OFF
        else:
            if was_off:
                await self.power(True, False)
            role = MODE_ROLES.get(hvac_mode)
            if role and self.has(role) and (was_off or hvac_mode != self._mode):
                if was_off:
                    await asyncio.sleep(1.0)
                await self.send(role)
            self._mode = hvac_mode
            self._last_on = hvac_mode
        self.async_write_ha_state()

    async def async_turn_on(self) -> None:
        await self.async_set_hvac_mode(self._last_on or next(m for m in self.hvac_modes if m != HVACMode.OFF))

    async def async_turn_off(self) -> None:
        await self.async_set_hvac_mode(HVACMode.OFF)

    async def async_set_temperature(self, **kwargs: Any) -> None:
        if (mode := kwargs.get("hvac_mode")) is not None:
            await self.async_set_hvac_mode(mode)
        target = kwargs.get(ATTR_TEMPERATURE)
        if target is None:
            return
        target = max(self.min_temp, min(self.max_temp, float(target)))
        steps = round(target - self._target)
        if steps:
            await self.send("temp_up" if steps > 0 else "temp_down", abs(steps))
        self._target = target
        self.async_write_ha_state()

    async def async_set_fan_mode(self, fan_mode: str) -> None:
        if fan_mode in FAN_ROLES and self.has(FAN_ROLES[fan_mode]):
            await self.send(FAN_ROLES[fan_mode])
            self._fan = fan_mode
            self.async_write_ha_state()

    async def async_set_swing_mode(self, swing_mode: str) -> None:
        if swing_mode != self._swing and self.has("swing"):
            await self.send("swing")
        self._swing = swing_mode
        self.async_write_ha_state()
