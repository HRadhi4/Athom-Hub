"""Reading a backup file safely. A backup can come from anywhere (shared online, edited by hand),
so nothing in it is trusted: ids must be in Athom Hub's own format, entity ids must look like entity
ids, names are cut to size, and only known fields are kept.

This file has no Home Assistant imports on purpose: it is tested on its own.
"""

from __future__ import annotations

import re
import uuid

ID = re.compile(r"^[0-9a-f]{10}$")
ENTITY_ID = re.compile(r"^(?!.+__)(?!_)[\da-z_]+(?<!_)\.(?!_)[\da-z_]+(?<!_)$")
KINDS = ("ir", "rf")


def new_id() -> str:
    return uuid.uuid4().hex[:10]


def is_id(value: object) -> bool:
    return isinstance(value, str) and bool(ID.match(value))


def _entity(value: object) -> str | None:
    return value if isinstance(value, str) and len(value) <= 255 and ENTITY_ID.match(value) else None


def _number(value: object) -> float | None:
    return value if isinstance(value, (int, float)) and not isinstance(value, bool) else None


def _text(value: object, fallback: str, size: int = 60) -> str:
    text = " ".join(str(value or "").split())[:size]
    return text or fallback


def clean_remote(item: object, tidy=lambda t: t) -> dict | None:
    """One remote from a backup file, made safe; None when it is not a remote."""
    if not isinstance(item, dict) or not isinstance(item.get("buttons"), list):
        return None
    remote = {
        "id": item["id"] if is_id(item.get("id")) else new_id(),
        "name": _text(item.get("name"), "Remote"),
        "kind": str(item.get("kind") or "other")[:20],
        "emitter_ir": _entity(item.get("emitter_ir")),
        "emitter_rf": _entity(item.get("emitter_rf")),
        "temp_sensor": _entity(item.get("temp_sensor")),
        "buttons": [],
    }
    table = item.get("table")
    if isinstance(table, dict) and isinstance(table.get("codes"), (dict, list)) and table["codes"]:
        remote["table"] = table
    taken: set[str] = set()
    for b in item["buttons"]:
        if not isinstance(b, dict):
            continue
        timings = [int(v) for v in (b.get("timings") or []) if isinstance(v, (int, float)) and not isinstance(v, bool)]
        if len(timings) < 4:
            continue
        button_id = b["id"] if is_id(b.get("id")) and b["id"] not in taken else new_id()
        taken.add(button_id)
        sends = _number(b.get("sends"))
        remote["buttons"].append({
            "id": button_id, "name": _text(b.get("name"), "Button"),
            "kind": b.get("kind") if b.get("kind") in KINDS else "ir", "timings": tidy(timings),
            "carrier": _number(b.get("carrier")), "frequency": _number(b.get("frequency")),
            "sends": max(1, min(20, int(sends or 1))), "source": "broadlink" if b.get("source") == "broadlink" else "backup",
        })
    return remote
