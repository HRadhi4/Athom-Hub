"""The working part of Athom Hub: find the devices, send, learn, copy from a Broadlink."""

from __future__ import annotations

import asyncio
import json
import logging
import re
from pathlib import Path
from typing import Any

from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import area_registry as ar, device_registry as dr, entity_registry as er
from homeassistant.helpers.dispatcher import async_dispatcher_send

from . import codes
from .const import DEFAULT_SENDS, DOMAIN, SIGNAL_REMOTES_CHANGED
from .store import HubStore, clean_name, new_id

_LOGGER = logging.getLogger(__name__)

IR_DOMAIN = "infrared"
RF_DOMAIN = "radio_frequency"
# Not real hardware: other tools' virtual emitters, and our own entities.
SKIP_PLATFORMS = {DOMAIN, "hair"}
_RF_WORDS = re.compile(r"(^|[^a-z])(rf|radio|433)([^a-z]|$)")
_ATHOM = re.compile(r"athom", re.I)


class HubError(HomeAssistantError):
    """Something the person should be told in plain words."""


def _is_rf(entity_id: str, name: str) -> bool:
    """Some firmware lists its 433 MHz side as an "infrared" entity: tell by the name."""
    if entity_id.startswith(f"{RF_DOMAIN}."):
        return True
    text = f"{entity_id} {name}".lower().replace("_", " ")
    # A device called "RF/IR remote" says nothing about this one part of it.
    text = re.sub(r"(rf|ir)\s*[/& ]\s*(rf|ir)", " ", text)
    return bool(_RF_WORDS.search(text))


class Hub:
    """One per Home Assistant."""

    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass
        self.store = HubStore(hass)
        # Codes just learned, waiting to be tested or saved: {token: {"kind", "timings", "carrier"}}
        self.learned: dict[str, dict[str, Any]] = {}

    async def async_load(self) -> None:
        await self.store.async_load()

    # ------------------------------------------------------------------ devices

    @callback
    def ports(self) -> list[dict[str, Any]]:
        """Every emitter and receiver Home Assistant has, described plainly."""
        ent_reg = er.async_get(self.hass)
        dev_reg = dr.async_get(self.hass)
        area_reg = ar.async_get(self.hass)
        out = []
        for entry in ent_reg.entities.values():
            if entry.domain not in (IR_DOMAIN, RF_DOMAIN) or entry.disabled_by or entry.platform in SKIP_PLATFORMS:
                continue
            state = self.hass.states.get(entry.entity_id)
            name = (state and state.attributes.get("friendly_name")) or entry.name or entry.original_name or entry.entity_id
            device_class = (state and state.attributes.get("device_class")) or entry.device_class or entry.original_device_class or ""
            role = "receive" if "receiv" in f"{device_class} {name}".lower() else "send"
            device = dev_reg.async_get(entry.device_id) if entry.device_id else None
            area_id = entry.area_id or (device.area_id if device else None)
            area = area_reg.async_get_area(area_id) if area_id else None
            out.append({
                "entity_id": entry.entity_id,
                "name": name,
                "role": role,
                "kind": codes.KIND_RF if _is_rf(entry.entity_id, name) else codes.KIND_IR,
                "device_id": entry.device_id,
                "device_name": (device.name_by_user or device.name) if device else name,
                "maker": (device.manufacturer or "") if device else "",
                "model": (device.model or "") if device else "",
                "athom": bool(device and _ATHOM.search(f"{device.manufacturer} {device.model} {device.name}")),
                "area": area.name if area else "",
                "online": bool(state and state.state != "unavailable"),
                "last": state.state if state and state.state not in ("unknown", "unavailable") else None,
            })
        out.sort(key=lambda p: (not p["athom"], p["device_name"], p["kind"], p["role"]))
        return out

    @callback
    def devices(self) -> list[dict[str, Any]]:
        """The Athom devices (and any other device that can send or receive), with a few live facts."""
        ent_reg = er.async_get(self.hass)
        dev_reg = dr.async_get(self.hass)
        area_reg = ar.async_get(self.hass)
        ports = self.ports()
        by_device: dict[str, list[dict[str, Any]]] = {}
        for port in ports:
            if port["device_id"]:
                by_device.setdefault(port["device_id"], []).append(port)
        out = []
        for device in dev_reg.devices.values():
            athom = bool(_ATHOM.search(f"{device.manufacturer} {device.model} {device.name}"))
            if device.id not in by_device and not athom:
                continue
            if device.entry_type is not None:      # a "service" entry, not a thing on the wall
                continue
            entries = [e for e in er.async_entries_for_device(ent_reg, device.id) if not e.disabled_by]
            if athom and not entries:
                continue                           # the bare network record of the same device
            facts, wifi, online = [], None, None
            for entry in entries:
                state = self.hass.states.get(entry.entity_id)
                if state is None:
                    continue
                if entry.entity_id.endswith("wifi_signal_percent"):
                    wifi = state.state
                    continue
                if entry.domain == "binary_sensor" and entry.entity_id.endswith("_status"):
                    online = state.state == "on"
                    continue
                if entry.entity_category is None and entry.domain in ("binary_sensor", "sensor", "climate", "switch", "light", "cover", "fan"):
                    unit = state.attributes.get("unit_of_measurement")
                    if state.state in ("unknown", "unavailable"):
                        continue
                    label = state.attributes.get("friendly_name") or entry.entity_id
                    prefix = (device.name_by_user or device.name or "") + " "
                    if label.startswith(prefix):
                        label = label[len(prefix):]
                    facts.append({"entity_id": entry.entity_id, "name": label, "state": state.state + (f" {unit}" if unit else "")})
            if online is None:
                online = any(p["online"] for p in by_device.get(device.id, [])) if device.id in by_device else bool(facts)
            area = area_reg.async_get_area(device.area_id) if device.area_id else None
            out.append({
                "id": device.id,
                "name": device.name_by_user or device.name or "Device",
                "maker": device.manufacturer or "",
                "model": device.model or "",
                "firmware": device.sw_version or "",
                "area": area.name if area else "",
                "athom": athom,
                "online": online,
                "wifi": wifi,
                "ports": by_device.get(device.id, []),
                "facts": facts[:8],
                "more_facts": max(0, len(facts) - 8),
            })
        out.sort(key=lambda d: (not d["athom"], not d["ports"], d["name"]))
        return out

    @callback
    def broadlink_senders(self) -> list[dict[str, Any]]:
        """Broadlink remotes, for the self-test that checks copied codes."""
        ent_reg = er.async_get(self.hass)
        out = []
        for entry in ent_reg.entities.values():
            if entry.domain == "remote" and entry.platform == "broadlink" and not entry.disabled_by:
                state = self.hass.states.get(entry.entity_id)
                out.append({"entity_id": entry.entity_id,
                            "name": (state and state.attributes.get("friendly_name")) or entry.name or entry.original_name or entry.entity_id,
                            "online": bool(state and state.state != "unavailable")})
        return sorted(out, key=lambda p: p["name"])

    async def async_self_test(self, emitter: str, receiver: str, kind: str, debug: bool = False) -> dict[str, Any]:
        """Send a made-up code and check that a receiver hears it. No real device reacts to it."""
        import random  # noqa: PLC0415

        rnd = random.SystemRandom()
        frame = codes.nec_frame(0xD9, rnd.randrange(256)) if kind == codes.KIND_IR else codes.ev1527_frame(rnd.randrange(1 << 24))
        captures: list[list[int]] = []

        @callback
        def _heard(timings: list[int], _modulation: int | None) -> None:
            captures.append(timings)

        stop = self.async_listen(receiver, _heard)
        try:
            await asyncio.sleep(0.3)
            if emitter.startswith("remote."):
                text = codes.broadlink_encode(frame, kind, 0 if kind == codes.KIND_IR else 3)
                frame = codes.broadlink_decode(text)["timings"]       # what a copied code would be
                await self.hass.services.async_call("remote", "send_command", {"entity_id": emitter, "command": f"b64:{text}"}, blocking=True)
            else:
                await self.async_send(emitter, {"kind": kind, "timings": frame, "sends": 1 if kind == codes.KIND_IR else 4})
            for _ in range(30):
                await asyncio.sleep(0.1)
                if codes.heard_frame(captures, frame):
                    break
        finally:
            stop()
        out = {"heard": codes.heard_frame(captures, frame), "captures": len(captures)}
        if debug:
            out["sent"] = frame
            out["heard_raw"] = [c[:160] for c in captures if len(c) >= 16][:12]
        return out

    def _port(self, entity_id: str | None) -> dict[str, Any] | None:
        return next((p for p in self.ports() if p["entity_id"] == entity_id), None)

    def default_emitters(self) -> dict[str, str | None]:
        """Where a new remote sends from: the first Athom emitter of each kind (else any emitter)."""
        out: dict[str, str | None] = {"ir": None, "rf": None}
        for port in self.ports():           # Athom devices are listed first
            if port["role"] == "send" and out[port["kind"]] is None:
                out[port["kind"]] = port["entity_id"]
        return out

    # ------------------------------------------------------------------ sending

    async def async_send(self, emitter: str | None, code: dict[str, Any]) -> None:
        """Send one code from one emitter."""
        kind = code.get("kind") or codes.KIND_IR
        port = self._port(emitter)
        if port is None or port["role"] != "send":
            raise HubError("Choose which device this remote sends from first." if not emitter else "The device this remote sends from is not in Home Assistant any more.")
        if not port["online"]:
            raise HubError(f"{port['device_name']} is offline. Check that it has power and Wi-Fi.")
        if port["kind"] != kind:
            want = "radio (433 MHz)" if kind == codes.KIND_RF else "infrared"
            raise HubError(f"This button is {want}, but {port['name']} cannot send that.")
        sends = int(code.get("sends") or DEFAULT_SENDS[kind])
        timings = code.get("timings") or []
        if len(timings) < 4:
            raise HubError("This button has no code yet. Learn it again.")
        if emitter.startswith(f"{RF_DOMAIN}."):
            await self._send_radio_entity(emitter, timings, sends, code.get("frequency"))
            return
        from homeassistant.components import infrared  # noqa: PLC0415 (only when used)
        from infrared_protocols.commands import Command  # noqa: PLC0415

        class _Raw(Command):
            def __init__(self, raw: list[int], modulation: int) -> None:
                super().__init__(modulation=modulation, repeat_count=0)
                self._raw = raw

            def get_raw_timings(self) -> list[int]:
                return self._raw

        # A radio transmitter listed as "infrared" keys the radio directly: no carrier.
        modulation = 0 if kind == codes.KIND_RF else int(code.get("carrier") or codes.IR_CARRIER)
        goes = codes.for_sending(timings, sends)
        for i, go in enumerate(goes):
            if i:
                await asyncio.sleep(0.05)
            await infrared.async_send_command(self.hass, emitter, _Raw(go, modulation))

    async def _send_radio_entity(self, emitter: str, timings: list[int], sends: int, frequency: int | None) -> None:
        from homeassistant.components import radio_frequency  # noqa: PLC0415
        from rf_protocols import ModulationType, RadioFrequencyCommand  # noqa: PLC0415

        class _Raw(RadioFrequencyCommand):
            def __init__(self, raw: list[int]) -> None:
                super().__init__(frequency=int(frequency or codes.RF_FREQUENCY), modulation=ModulationType.OOK, repeat_count=max(0, sends - 1))
                self._raw = raw

            def get_raw_timings(self) -> list[int]:
                return self._raw

        await radio_frequency.async_send_command(self.hass, emitter, _Raw(codes.tidy(timings)))

    async def async_press(self, remote_id: str, button_id: str) -> None:
        remote = self.store.remote(remote_id)
        button = self.store.button(remote_id, button_id)
        await self.async_send(remote.get(f"emitter_{button.get('kind', 'ir')}"), button)

    # ------------------------------------------------------------------ learning

    @callback
    def async_listen(self, receiver: str, on_signal) -> Any:
        """Call on_signal(timings) for everything a receiver hears. Returns the function that stops it."""
        port = self._port(receiver)
        if port is None or port["role"] != "receive":
            raise HubError("That receiver is not in Home Assistant any more.")
        if not port["online"]:
            raise HubError(f"{port['device_name']} is offline. Check that it has power and Wi-Fi.")

        @callback
        def _heard(signal: Any) -> None:
            timings = [int(v) for v in (getattr(signal, "timings", None) or [])]
            if timings and all(v >= 0 for v in timings):     # unsigned on/off pairs
                timings = [v if i % 2 == 0 else -v for i, v in enumerate(timings)]
            if timings:
                on_signal(timings, getattr(signal, "modulation", None))

        if receiver.startswith(f"{RF_DOMAIN}."):
            from homeassistant.components import radio_frequency  # noqa: PLC0415
            return radio_frequency.async_subscribe_receiver(self.hass, receiver, _heard)
        from homeassistant.components import infrared  # noqa: PLC0415
        return infrared.async_subscribe_receiver(self.hass, receiver, _heard)

    def keep_learned(self, kind: str, timings: list[int], carrier: int | None) -> str:
        token = new_id()
        if len(self.learned) > 20:
            self.learned.pop(next(iter(self.learned)))
        self.learned[token] = {"kind": kind, "timings": timings, "carrier": carrier, "sends": DEFAULT_SENDS[kind], "source": "learned"}
        return token

    # ------------------------------------------------------------------ remotes

    async def async_changed(self) -> None:
        await self.store.async_save()
        async_dispatcher_send(self.hass, SIGNAL_REMOTES_CHANGED)

    @callback
    def remotes_public(self) -> list[dict[str, Any]]:
        """The remotes without the raw codes (the page does not need them)."""
        out = []
        for remote in self.store.remotes.values():
            out.append({
                **{k: remote.get(k) for k in ("id", "name", "kind", "emitter_ir", "emitter_rf")},
                "buttons": [{"id": b["id"], "name": b["name"], "kind": b.get("kind", "ir"), "sends": b.get("sends"),
                             "source": b.get("source"), **codes.describe(b.get("timings") or [])} for b in remote["buttons"]],
            })
        out.sort(key=lambda r: r["name"].lower())
        return out

    async def async_save_button(self, remote_id: str, data: dict[str, Any]) -> dict[str, Any]:
        remote = self.store.remote(remote_id)
        button_id = data.get("button_id")
        token = data.get("token")
        if button_id:
            button = self.store.button(remote_id, button_id)
        else:
            if not token or token not in self.learned:
                raise HubError("Learn the button first.")
            button = {"id": new_id(), "name": ""}
            remote["buttons"].append(button)
        if token:
            if token not in self.learned:
                raise HubError("That learned code has expired. Learn the button again.")
            button.update(self.learned.pop(token))
        if "name" in data or not button.get("name"):
            button["name"] = self.store.unique_button_name(remote, clean_name(data.get("name"), "Button"), button["id"])
        if data.get("sends"):
            button["sends"] = max(1, min(20, int(data["sends"])))
        await self.async_changed()
        return button

    # ------------------------------------------------------------------ Broadlink

    async def async_broadlink(self) -> list[dict[str, Any]]:
        """Every remote a Broadlink has learned through Home Assistant, decoded."""
        names = {}
        for entry in self.hass.config_entries.async_entries("broadlink"):
            if entry.unique_id:
                names[entry.unique_id.lower()] = entry.title
        raw = await self.hass.async_add_executor_job(self._read_broadlink_files)
        out = []
        for key, devices in raw.items():
            for device, commands in sorted(devices.items()):
                buttons = []
                for name, value in sorted(commands.items()):
                    values = value if isinstance(value, list) else [value]
                    for n, text in enumerate(values):
                        label = name if len(values) == 1 else f"{name} {n + 1}"
                        try:
                            code = codes.broadlink_decode(text)
                            buttons.append({"name": label, "kind": code["kind"], "ok": True, **codes.describe(code["timings"])})
                        except codes.CodeError as err:
                            buttons.append({"name": label, "kind": "", "ok": False, "why": str(err)})
                out.append({"source": key, "source_name": names.get(key, "Broadlink"), "device": device, "buttons": buttons,
                            "kinds": sorted({b["kind"] for b in buttons if b["ok"]})})
        return out

    def _read_broadlink_files(self) -> dict[str, dict[str, dict[str, Any]]]:
        out: dict[str, dict[str, dict[str, Any]]] = {}
        folder = Path(self.hass.config.path(".storage"))
        for path in sorted(folder.glob("broadlink_remote_*_codes")):
            try:
                data = json.loads(path.read_text(encoding="utf-8")).get("data") or {}
            except (OSError, ValueError) as err:
                _LOGGER.warning("Could not read %s: %s", path.name, err)
                continue
            key = path.name[len("broadlink_remote_"):-len("_codes")].lower()
            devices = {d: c for d, c in data.items() if isinstance(c, dict) and c}
            if devices:
                out[key] = devices
        return out

    async def async_broadlink_copy(self, source: str, device: str, name: str | None, kind: str | None) -> dict[str, Any]:
        """Copy one Broadlink remote into a new Athom Hub remote."""
        raw = await self.hass.async_add_executor_job(self._read_broadlink_files)
        commands = (raw.get(source) or {}).get(device)
        if not commands:
            raise HubError("That Broadlink remote was not found. Was it learned in Home Assistant?")
        remote = self.store.upsert_remote({"name": name or device.replace("_", " ").title(), "kind": kind or guess_kind(device), **{f"emitter_{k}": v for k, v in self.default_emitters().items()}})
        copied, skipped = 0, []
        for cmd, value in sorted(commands.items()):
            values = value if isinstance(value, list) else [value]
            for n, text in enumerate(values):
                label = cmd.replace("_", " ").strip().capitalize() or "Button"
                if len(values) > 1:
                    label = f"{label} {n + 1}"
                try:
                    code = codes.broadlink_decode(text)
                except codes.CodeError:
                    skipped.append(label)
                    continue
                sends = code["repeat"] + 1
                if code["kind"] == codes.KIND_RF:
                    sends = max(sends, 4)
                remote["buttons"].append({"id": new_id(), "name": self.store.unique_button_name(remote, clean_name(label, "Button")),
                                          "kind": code["kind"], "timings": code["timings"], "carrier": None,
                                          "frequency": code["frequency"], "sends": min(sends, 12), "source": "broadlink"})
                copied += 1
        if not copied:
            self.store.remotes.pop(remote["id"], None)
            raise HubError("None of that remote's buttons could be read.")
        await self.async_changed()
        return {"remote_id": remote["id"], "copied": copied, "skipped": skipped}


def guess_kind(name: str) -> str:
    """A sensible picture for a remote from its name."""
    text = name.lower()
    for kind, words in (("tv", ("tv", "television", "screen", "projector")), ("ac", ("ac", "air", "aircon", "hvac", "climate")),
                        ("fan", ("fan",)), ("curtain", ("curtain", "blind", "shade", "shutter", "roller")),
                        ("light", ("light", "lamp", "led")), ("audio", ("audio", "speaker", "sound", "amp", "receiver", "hifi"))):
        if any(re.search(rf"(^|[^a-z]){w}([^a-z]|$)", text) for w in words):
            return kind
    return "other"
