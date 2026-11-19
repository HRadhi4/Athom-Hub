"""Where the remotes are kept (Home Assistant's own storage, on this machine only)."""

from __future__ import annotations

import re
import uuid
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store

from . import smartir
from .const import REMOTE_KINDS, STORAGE_KEY, STORAGE_VERSION


def new_id() -> str:
    """A short id for a remote or a button."""
    return uuid.uuid4().hex[:10]


def clean_name(name: Any, fallback: str) -> str:
    """A name that is safe to show and to build an entity id from."""
    text = re.sub(r"\s+", " ", str(name or "")).strip()[:60]
    return text or fallback


class HubStore:
    """Remotes and their buttons.

    {"remotes": {id: {"id", "name", "kind", "emitter_ir", "emitter_rf",
                      "buttons": [{"id", "name", "kind", "timings", "carrier", "sends", "source"}]}}}
    """

    def __init__(self, hass: HomeAssistant) -> None:
        self._store: Store[dict[str, Any]] = Store(hass, STORAGE_VERSION, STORAGE_KEY)
        self.remotes: dict[str, dict[str, Any]] = {}

    async def async_load(self) -> None:
        data = await self._store.async_load() or {}
        self.remotes = data.get("remotes") or {}
        for remote in self.remotes.values():
            # a table restored from a hand-edited backup by 0.8.0 could stop the page from loading
            if remote.get("table"):
                try:
                    remote["table"] = smartir.clean_table(remote["table"])
                except Exception:  # noqa: BLE001
                    remote.pop("table", None)

    async def async_save(self) -> None:
        await self._store.async_save({"remotes": self.remotes})

    def remote(self, remote_id: str) -> dict[str, Any]:
        if remote_id not in self.remotes:
            raise KeyError("That remote no longer exists.")
        return self.remotes[remote_id]

    def button(self, remote_id: str, button_id: str) -> dict[str, Any]:
        for button in self.remote(remote_id)["buttons"]:
            if button["id"] == button_id:
                return button
        raise KeyError("That button no longer exists.")

    def upsert_remote(self, data: dict[str, Any]) -> dict[str, Any]:
        remote_id = data.get("id") or new_id()
        remote = self.remotes.get(remote_id) or {"id": remote_id, "buttons": []}
        remote["name"] = clean_name(data.get("name", remote.get("name")), "Remote")
        kind = data.get("kind", remote.get("kind"))
        remote["kind"] = kind if kind in REMOTE_KINDS else "other"
        for key in ("emitter_ir", "emitter_rf", "temp_sensor"):
            if key in data or key not in remote:
                remote[key] = data.get(key) or None
        self.remotes[remote_id] = remote
        return remote

    def unique_button_name(self, remote: dict[str, Any], name: str, skip_id: str | None = None) -> str:
        taken = {b["name"].lower() for b in remote["buttons"] if b["id"] != skip_id}
        if name.lower() not in taken:
            return name
        n = 2
        while f"{name} {n}".lower() in taken:
            n += 1
        return f"{name} {n}"
