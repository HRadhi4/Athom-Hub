"""What the Athom Hub page asks the server to do."""

from __future__ import annotations

import asyncio
from typing import Any

import voluptuous as vol

from homeassistant.components import websocket_api
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError

from . import backup, codes, icons, roles, smartir
from .const import DOMAIN, SIGNAL_LOG, LEARN_SECONDS, LEARN_SETTLE_SECONDS, REMOTE_KINDS, VERSION
from .hub import Hub, HubError
from .store import clean_name


def _hub(hass: HomeAssistant) -> Hub:
    hub = hass.data.get(DOMAIN)
    if hub is None:
        raise HubError("Athom Hub is not running. Add it again in Settings.")
    return hub


def _command(schema: dict[Any, Any]):
    """An admin-only command whose errors reach the page as plain sentences."""
    def wrap(func):
        @websocket_api.websocket_command(schema)
        @websocket_api.require_admin
        @websocket_api.async_response
        async def handler(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]) -> None:
            try:
                connection.send_result(msg["id"], await func(hass, _hub(hass), msg))
            except (HomeAssistantError, KeyError, ValueError) as err:
                text = err.args[0] if isinstance(err, KeyError) and err.args else str(err)
                connection.send_error(msg["id"], "athom_hub", str(text) or "Something went wrong.")
        return handler
    return wrap


@_command({vol.Required("type"): "athom_hub/presence_get", vol.Required("device_id"): str})
async def ws_presence_get(hass: HomeAssistant, hub: Hub, msg: dict[str, Any]) -> dict[str, Any]:
    m = hass.data[f"{DOMAIN}_presence"]
    return {"settings": m.get(msg["device_id"]), "live": m.live(msg["device_id"])}


@_command({vol.Required("type"): "athom_hub/presence_save", vol.Required("device_id"): str, vol.Required("settings"): dict})
async def ws_presence_save(hass: HomeAssistant, hub: Hub, msg: dict[str, Any]) -> dict[str, Any]:
    m = hass.data[f"{DOMAIN}_presence"]
    s = await m.async_save(msg["device_id"], msg["settings"])
    return {"settings": s, "live": m.live(msg["device_id"])}


@_command({vol.Required("type"): "athom_hub/overview"})
async def ws_overview(hass: HomeAssistant, hub: Hub, msg: dict[str, Any]) -> dict[str, Any]:
    return {"version": VERSION, "ports": hub.ports(), "devices": hub.devices(), "remotes": hub.remotes_public(),
            "defaults": hub.default_emitters(), "kinds": REMOTE_KINDS,
            "broadlinks": hub.broadlink_senders(),
            "icon_choices": icons.CHOICES, "colours": icons.COLOURS, "role_names": roles.ROLE_NAMES, "kind_roles": roles.KIND_ROLES}


@_command({vol.Required("type"): "athom_hub/self_test", vol.Required("emitter"): str, vol.Required("receiver"): str,
           vol.Required("kind"): vol.In(["ir", "rf"]), vol.Optional("debug", default=False): bool})
async def ws_self_test(hass: HomeAssistant, hub: Hub, msg: dict[str, Any]) -> dict[str, Any]:
    return await hub.async_self_test(msg["emitter"], msg["receiver"], msg["kind"], msg["debug"])


@_command({vol.Required("type"): "athom_hub/remote_save", vol.Optional("remote_id"): str, vol.Optional("name"): str, vol.Optional("kind"): str,
           vol.Optional("emitter_ir"): vol.Any(str, None), vol.Optional("emitter_rf"): vol.Any(str, None),
           vol.Optional("temp_sensor"): vol.Any(str, None)})
async def ws_remote_save(hass: HomeAssistant, hub: Hub, msg: dict[str, Any]) -> dict[str, Any]:
    """Make a remote, or change its name, picture or where it sends from."""
    data = {k: msg[k] for k in ("name", "kind", "emitter_ir", "emitter_rf", "temp_sensor") if k in msg}
    if msg.get("remote_id"):
        hub.store.remote(msg["remote_id"])
        data["id"] = msg["remote_id"]
    elif "emitter_ir" not in data and "emitter_rf" not in data:
        data.update({f"emitter_{k}": v for k, v in hub.default_emitters().items()})
    remote = hub.store.upsert_remote(data)
    await hub.async_changed()
    return {"remote_id": remote["id"]}


@_command({vol.Required("type"): "athom_hub/remote_delete", vol.Required("remote_id"): str})
async def ws_remote_delete(hass: HomeAssistant, hub: Hub, msg: dict[str, Any]) -> dict[str, Any]:
    hub.store.remote(msg["remote_id"])
    hub.store.remotes.pop(msg["remote_id"])
    await hub.async_changed()
    return {}


@_command({vol.Required("type"): "athom_hub/button_save", vol.Required("remote_id"): str, vol.Optional("button_id"): str,
           vol.Optional("name"): str, vol.Optional("token"): str, vol.Optional("sends"): vol.Coerce(int),
           vol.Optional("icon"): vol.Any(str, None), vol.Optional("colour"): vol.Any(str, None), vol.Optional("role"): vol.Any(str, None)})
async def ws_button_save(hass: HomeAssistant, hub: Hub, msg: dict[str, Any]) -> dict[str, Any]:
    button = await hub.async_save_button(msg["remote_id"], msg)
    return {"button_id": button["id"], "name": button["name"]}


@_command({vol.Required("type"): "athom_hub/button_delete", vol.Required("remote_id"): str, vol.Required("button_id"): str})
async def ws_button_delete(hass: HomeAssistant, hub: Hub, msg: dict[str, Any]) -> dict[str, Any]:
    remote = hub.store.remote(msg["remote_id"])
    hub.store.button(msg["remote_id"], msg["button_id"])
    remote["buttons"] = [b for b in remote["buttons"] if b["id"] != msg["button_id"]]
    await hub.async_changed()
    return {}


@_command({vol.Required("type"): "athom_hub/button_order", vol.Required("remote_id"): str, vol.Required("order"): [str]})
async def ws_button_order(hass: HomeAssistant, hub: Hub, msg: dict[str, Any]) -> dict[str, Any]:
    remote = hub.store.remote(msg["remote_id"])
    place = {button_id: i for i, button_id in enumerate(msg["order"])}
    remote["buttons"].sort(key=lambda b: place.get(b["id"], len(place)))
    await hub.async_changed()
    return {}


@_command({vol.Required("type"): "athom_hub/press", vol.Required("remote_id"): str, vol.Required("button_id"): str})
async def ws_press(hass: HomeAssistant, hub: Hub, msg: dict[str, Any]) -> dict[str, Any]:
    await hub.async_press(msg["remote_id"], msg["button_id"])
    return {}


@_command({vol.Required("type"): "athom_hub/test", vol.Required("token"): str, vol.Required("emitter"): vol.Any(str, None)})
async def ws_test(hass: HomeAssistant, hub: Hub, msg: dict[str, Any]) -> dict[str, Any]:
    code = hub.learned.get(msg["token"])
    if code is None:
        raise HubError("That learned code has expired. Learn the button again.")
    await hub.async_send(msg["emitter"], code, "Just-learned button (try it)")
    return {}


@_command({vol.Required("type"): "athom_hub/broadlink", vol.Required("text"): str})
async def ws_broadlink(hass: HomeAssistant, hub: Hub, msg: dict[str, Any]) -> dict[str, Any]:
    """Read Broadlink codes the user pasted or picked from a file (nothing is read from other integrations)."""
    return {"remotes": await hub.async_broadlink(msg["text"])}


@_command({vol.Required("type"): "athom_hub/broadlink_copy", vol.Required("text"): str, vol.Required("index"): int,
           vol.Optional("name"): str, vol.Optional("kind"): str})
async def ws_broadlink_copy(hass: HomeAssistant, hub: Hub, msg: dict[str, Any]) -> dict[str, Any]:
    return await hub.async_broadlink_copy(msg["text"], msg["index"], msg.get("name"), msg.get("kind"))


@_command({vol.Required("type"): "athom_hub/backup"})
async def ws_backup(hass: HomeAssistant, hub: Hub, msg: dict[str, Any]) -> dict[str, Any]:
    return {"athom_hub": VERSION, "remotes": list(hub.store.remotes.values())}


@_command({vol.Required("type"): "athom_hub/restore", vol.Required("remotes"): list})
async def ws_restore(hass: HomeAssistant, hub: Hub, msg: dict[str, Any]) -> dict[str, Any]:
    """Add the remotes of a backup file (remotes already here are replaced by id, others are kept)."""
    added = 0
    for item in msg["remotes"]:
        clean = backup.clean_remote(item, codes.tidy, smartir.clean_table)
        if clean is None:
            continue
        remote = hub.store.upsert_remote({k: clean[k] for k in ("id", "name", "kind", "emitter_ir", "emitter_rf", "temp_sensor")})
        if "table" in clean:
            remote["table"] = clean["table"]
        remote["buttons"] = []
        for b in clean["buttons"]:
            remote["buttons"].append({**b, "name": hub.store.unique_button_name(remote, clean_name(b["name"], "Button"))})
        added += 1
    await hub.async_changed()
    return {"remotes": added}


@websocket_api.websocket_command({vol.Required("type"): "athom_hub/learn", vol.Required("receiver"): str,
                                  vol.Required("kind"): vol.In(["ir", "rf"])})
@websocket_api.require_admin
@websocket_api.async_response
async def ws_learn(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]) -> None:
    """Listen on a receiver until a button is recognised, then say so.

    Events sent to the page: {"state": "listening"}, {"state": "heard", "count": n},
    {"state": "done", "token", "pulses", "ms", "heard"}, {"state": "timeout", "count": n}.
    """
    kind = msg["kind"]
    captures: list[list[int]] = []
    carrier: list[int | None] = [None]
    finished = asyncio.Event()
    result: dict[str, Any] = {}
    settle: list[asyncio.TimerHandle | None] = [None]

    @callback
    def _conclude() -> None:
        best = codes.pick_learned(captures, kind)
        if best:
            result.update(best)
            finished.set()

    @callback
    def _heard(timings: list[int], modulation: int | None) -> None:
        if finished.is_set():
            return
        captures.append(timings)
        if modulation:
            carrier[0] = int(modulation)
        connection.send_message(websocket_api.event_message(msg["id"], {"state": "heard", "count": len(captures)}))
        if kind == codes.KIND_RF:
            _conclude()                       # radio: as soon as the same frame came three times
        elif codes.looks_like_signal(codes.tidy(timings), kind) and settle[0] is None:
            # infrared: wait a moment for the rest of the press, then take the full frame
            settle[0] = hass.loop.call_later(LEARN_SETTLE_SECONDS, _conclude)

    try:
        stop = _hub(hass).async_listen(msg["receiver"], _heard)
    except HomeAssistantError as err:
        connection.send_error(msg["id"], "athom_hub", str(err))
        return

    @callback
    def _stop() -> None:
        if settle[0] is not None:
            settle[0].cancel()
        stop()
        finished.set()

    connection.subscriptions[msg["id"]] = _stop
    connection.send_result(msg["id"])
    connection.send_message(websocket_api.event_message(msg["id"], {"state": "listening", "seconds": LEARN_SECONDS}))
    try:
        await asyncio.wait_for(finished.wait(), LEARN_SECONDS)
    except TimeoutError:
        pass
    if settle[0] is not None:
        settle[0].cancel()
    stop()
    connection.subscriptions.pop(msg["id"], None)
    if result:
        hub = _hub(hass)
        token = hub.keep_learned(kind, result["timings"], carrier[0])
        connection.send_message(websocket_api.event_message(msg["id"], {"state": "done", "token": token, "heard": result["heard"], **codes.describe(result["timings"])}))
    else:
        connection.send_message(websocket_api.event_message(msg["id"], {"state": "timeout", "count": len(captures)}))


@_command({vol.Required("type"): "athom_hub/log"})
async def ws_log(hass: HomeAssistant, hub: Hub, msg: dict[str, Any]) -> dict[str, Any]:
    hub.async_watch_receivers()
    return {"log": list(hub.log)}


@_command({vol.Required("type"): "athom_hub/log_clear"})
async def ws_log_clear(hass: HomeAssistant, hub: Hub, msg: dict[str, Any]) -> dict[str, Any]:
    hub.log.clear()
    return {}


@websocket_api.websocket_command({vol.Required("type"): "athom_hub/log_subscribe"})
@websocket_api.require_admin
@callback
def ws_log_subscribe(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]) -> None:
    """Send every new activity line to the page while it is open."""
    from homeassistant.helpers.dispatcher import async_dispatcher_connect  # noqa: PLC0415

    @callback
    def _new(entry: dict[str, Any]) -> None:
        connection.send_message(websocket_api.event_message(msg["id"], entry))

    connection.subscriptions[msg["id"]] = async_dispatcher_connect(hass, SIGNAL_LOG, _new)
    connection.send_result(msg["id"])


@_command({vol.Required("type"): "athom_hub/smartir"})
async def ws_smartir(hass: HomeAssistant, hub: Hub, msg: dict[str, Any]) -> dict[str, Any]:
    """The SmartIR air conditioners set up here, and the brands in SmartIR's library."""
    configured = await hub.async_smartir_configured()
    for item in configured:
        item["emitter"] = hub.suggest_emitter(item.get("controller"))
        try:
            data = await hub.async_smartir_file(item["code"])
            item["maker"] = data.get("manufacturer", "")
            item["models"] = data.get("supportedModels", [])[:4]
        except HubError as err:
            item["error"] = str(err)
    try:
        index = await hub.async_smartir_index()
        brands = sorted({i["brand"] for i in index}, key=str.lower)
        error = None
    except HubError as err:
        index, brands, error = [], [], str(err)
    return {"configured": configured, "brands": brands, "files": len(index), "index_error": error}


@_command({vol.Required("type"): "athom_hub/smartir_copy", vol.Required("code"): vol.Coerce(int), vol.Optional("name"): str,
           vol.Optional("remote_id"): vol.Any(str, None), vol.Optional("emitter"): vol.Any(str, None),
           vol.Optional("temp_sensor"): vol.Any(str, None)})
async def ws_smartir_copy(hass: HomeAssistant, hub: Hub, msg: dict[str, Any]) -> dict[str, Any]:
    return await hub.async_table_copy(msg["code"], msg.get("name"), msg.get("remote_id"), msg.get("emitter"), msg.get("temp_sensor"))


@websocket_api.websocket_command({vol.Required("type"): "athom_hub/smartir_find", vol.Required("token"): str,
                                  vol.Optional("brand"): vol.Any(str, None)})
@websocket_api.require_admin
@websocket_api.async_response
async def ws_smartir_find(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]) -> None:
    """Search SmartIR's library for the code a real remote just sent. Sends progress, then the result."""
    try:
        hub = _hub(hass)
        learned = hub.learned.get(msg["token"])
        if learned is None or learned["kind"] != codes.KIND_IR:
            raise HubError("Press the remote again: the code was not kept.")
        index = await hub.async_smartir_index()
        brand = (msg.get("brand") or "").strip().lower()
        numbers = [i["code"] for i in index if not brand or i["brand"].lower() == brand]
        if not numbers:
            raise HubError("No code files for that brand.")
    except HomeAssistantError as err:
        connection.send_error(msg["id"], "athom_hub", str(err))
        return
    connection.send_result(msg["id"])

    @callback
    def _progress(done: int, total: int) -> None:
        connection.send_message(websocket_api.event_message(msg["id"], {"state": "searching", "done": done, "total": total}))

    try:
        found = await hub.async_smartir_find(learned["timings"], numbers, _progress)
        connection.send_message(websocket_api.event_message(msg["id"], {"state": "done", "found": found, "searched": len(numbers)}))
    except HomeAssistantError as err:
        connection.send_message(websocket_api.event_message(msg["id"], {"state": "error", "why": str(err)}))


@callback
def async_register_websocket(hass: HomeAssistant) -> None:
    for handler in (ws_overview, ws_remote_save, ws_remote_delete, ws_button_save, ws_button_delete, ws_button_order,
                    ws_press, ws_test, ws_broadlink, ws_broadlink_copy, ws_backup, ws_restore, ws_learn, ws_self_test, ws_log, ws_log_clear, ws_log_subscribe, ws_smartir, ws_smartir_copy, ws_smartir_find, ws_presence_get, ws_presence_save):
        websocket_api.async_register_command(hass, handler)
