"""Athom Hub: a friendly page for Athom remotes in Home Assistant.

Learn remote buttons with an Athom RF/IR remote, copy the remotes a Broadlink
already knows, and get every button as a normal Home Assistant button.
Everything stays on this Home Assistant; nothing is sent anywhere.
"""

from __future__ import annotations

from pathlib import Path

from homeassistant.components import frontend, panel_custom
from homeassistant.components.http import StaticPathConfig
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import DOMAIN, PANEL_ELEMENT, PANEL_ICON, PANEL_TITLE, PANEL_URL, STATIC_URL, VERSION
from .hub import Hub
from .websocket import async_register_websocket

PLATFORMS = [Platform.BUTTON, Platform.CLIMATE, Platform.COVER, Platform.MEDIA_PLAYER, Platform.FAN, Platform.LIGHT]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Start the hub, its page and its buttons."""
    hub = Hub(hass)
    await hub.async_load()
    hass.data[DOMAIN] = hub

    if not hass.data.get(f"{DOMAIN}_static"):
        await hass.http.async_register_static_paths(
            [StaticPathConfig(STATIC_URL, str(Path(__file__).parent / "panel"), cache_headers=False)]
        )
        async_register_websocket(hass)
        hass.data[f"{DOMAIN}_static"] = True

    if PANEL_URL not in hass.data.get(frontend.DATA_PANELS, {}):
        await panel_custom.async_register_panel(
            hass,
            frontend_url_path=PANEL_URL,
            webcomponent_name=PANEL_ELEMENT,
            sidebar_title=PANEL_TITLE,
            sidebar_icon=PANEL_ICON,
            module_url=f"{STATIC_URL}/athom-hub-panel.js?v={VERSION}",
            require_admin=True,
            config={"version": VERSION},
        )

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Take the page and the buttons away (the saved remotes stay on disk)."""
    ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if ok:
        frontend.async_remove_panel(hass, PANEL_URL)
        hass.data.pop(DOMAIN, None)
    return ok
