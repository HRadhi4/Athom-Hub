"""Athom Hub: a friendly page for Athom remotes in Home Assistant.

Learn remote buttons with an Athom RF/IR remote, copy the remotes a Broadlink
already knows, and get every button as a normal Home Assistant button.
Everything stays on this Home Assistant; nothing is sent anywhere.
"""

from __future__ import annotations

from datetime import timedelta
from pathlib import Path

from homeassistant.components import frontend, panel_custom
from homeassistant.components.http import StaticPathConfig
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.helpers.start import async_at_started

from .const import DOMAIN, PANEL_ELEMENT, PANEL_ICON, PANEL_TITLE, PANEL_URL, STATIC_URL, VERSION
from .hub import Hub
from .presence import PresenceManager
from .websocket import async_register_websocket

PLATFORMS = [Platform.BINARY_SENSOR, Platform.BUTTON, Platform.CLIMATE, Platform.COVER, Platform.MEDIA_PLAYER, Platform.FAN, Platform.LIGHT]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Start the hub, its page and its buttons."""
    hub = Hub(hass)
    await hub.async_load()
    hass.data[DOMAIN] = hub
    presence = PresenceManager(hass)
    await presence.async_load()
    hass.data[f"{DOMAIN}_presence"] = presence

    if not hass.data.get(f"{DOMAIN}_static"):
        await hass.http.async_register_static_paths(
            [StaticPathConfig(STATIC_URL, str(Path(__file__).parent / "panel"), cache_headers=False)]
        )
        async_register_websocket(hass)
        hass.data[f"{DOMAIN}_static"] = True

    # The file's date in the address makes browsers fetch the new page after every update.
    panel_file = Path(__file__).parent / "panel" / "athom-hub-panel.js"
    stamp = await hass.async_add_executor_job(lambda: int(panel_file.stat().st_mtime))
    if PANEL_URL not in hass.data.get(frontend.DATA_PANELS, {}):
        await panel_custom.async_register_panel(
            hass,
            frontend_url_path=PANEL_URL,
            webcomponent_name=PANEL_ELEMENT,
            sidebar_title=PANEL_TITLE,
            sidebar_icon=PANEL_ICON,
            module_url=f"{STATIC_URL}/athom-hub-panel.js?v={VERSION}-{stamp}",
            require_admin=True,
            config={"version": VERSION},
        )

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    @callback
    def _watch(_now=None) -> None:
        hub.async_watch_receivers()

    # Start listening once everything is up, and check again now and then (devices come and go).
    @callback
    def _started(_hass: HomeAssistant) -> None:
        _watch()
        presence.start()

    entry.async_on_unload(async_at_started(hass, _started))
    entry.async_on_unload(async_track_time_interval(hass, _watch, timedelta(minutes=5)))
    entry.async_on_unload(hub.async_stop_watching)
    entry.async_on_unload(presence.stop)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Take the page and the buttons away (the saved remotes stay on disk)."""
    ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if ok:
        frontend.async_remove_panel(hass, PANEL_URL)
        hass.data.pop(DOMAIN, None)
        hass.data.pop(f"{DOMAIN}_presence", None)
    return ok
