"""Air conditioner code sets from SmartIR (the Broadlink code files many people already have).

A SmartIR climate file holds one code for every setting: mode, fan speed and
temperature together. Athom Hub keeps that table on a remote, sends the full
setting every time, and can tell which setting a real remote just sent.

No Home Assistant imports: tested on its own.
"""

from __future__ import annotations

from typing import Any

from . import codes

# SmartIR uses Home Assistant's own mode names; "auto" sometimes appears as "heat_cool".
KNOWN_MODES = ["cool", "heat", "dry", "fan_only", "heat_cool", "auto"]


class TableError(ValueError):
    """The file is not an air conditioner code set we can use."""


def table_from_smartir(data: dict[str, Any]) -> dict[str, Any]:
    """Turn a SmartIR climate JSON (already parsed) into an Athom Hub code table."""
    if str(data.get("supportedController", "")).lower() != "broadlink" or str(data.get("commandsEncoding", "")).lower() != "base64":
        raise TableError("Only Broadlink (Base64) code files can be copied.")
    commands = data.get("commands") or {}
    if not isinstance(commands.get("off"), str):
        raise TableError("The file has no “off” code.")
    modes = [m for m in data.get("operationModes") or [] if m in KNOWN_MODES and isinstance(commands.get(m), dict)]
    if not modes:
        raise TableError("The file has no modes.")
    fans = [f for f in data.get("fanModes") or [] if any(f in commands[m] for m in modes)]
    table_codes: dict[str, Any] = {"off": commands["off"]}
    for mode in modes:
        table_codes[mode] = {}
        for fan, temps in commands[mode].items():
            if isinstance(temps, dict):
                table_codes[mode][fan] = {str(int(float(t))): v for t, v in temps.items() if isinstance(v, str)}
            elif isinstance(temps, str):             # some files have no temperature level
                table_codes[mode][fan] = {"any": temps}
    for text in [table_codes["off"]]:
        codes.broadlink_decode(text)                 # raises CodeError if the codes are not readable
    return {
        "maker": str(data.get("manufacturer") or ""),
        "models": [str(m) for m in data.get("supportedModels") or []][:6],
        "min": int(float(data.get("minTemperature", 16))),
        "max": int(float(data.get("maxTemperature", 30))),
        "step": max(1, int(float(data.get("precision", 1)))),
        "modes": modes,
        "fans": fans,
        "codes": table_codes,
    }


def _whole(value: Any, fallback: int, low: int, high: int) -> int:
    try:
        number = int(float(value))
    except (TypeError, ValueError):
        return fallback
    return max(low, min(high, number))


def clean_table(table: Any) -> dict[str, Any]:
    """A code table from somewhere we don't trust (a backup file), checked the same way as a fresh
    SmartIR file and rebuilt with only the fields Athom Hub uses. Raises TableError when unusable."""
    if not isinstance(table, dict) or not isinstance(table.get("codes"), dict):
        raise TableError("The code table is not readable.")
    raw = table["codes"]
    if not isinstance(raw.get("off"), str):
        raise TableError("The code table has no “off” code.")
    try:
        codes.broadlink_decode(raw["off"])
    except codes.CodeError as err:
        raise TableError("The code table's codes are not readable.") from err
    table_codes: dict[str, Any] = {"off": raw["off"]}
    modes = []
    for mode in table.get("modes") if isinstance(table.get("modes"), list) else []:
        if mode not in KNOWN_MODES or mode in modes or not isinstance(raw.get(mode), dict):
            continue
        by_fan = {}
        for fan, temps in raw[mode].items():
            if not isinstance(fan, str) or not isinstance(temps, dict):
                continue
            kept = {}
            for temp, code in temps.items():
                if not isinstance(code, str):
                    continue
                if temp == "any":
                    kept["any"] = code
                else:
                    try:
                        kept[str(int(float(temp)))] = code
                    except (TypeError, ValueError):
                        continue
            if kept:
                by_fan[fan[:20]] = kept
        if by_fan:
            modes.append(mode)
            table_codes[mode] = by_fan
    if not modes:
        raise TableError("The code table has no modes.")
    low = _whole(table.get("min"), 16, 5, 40)
    high = _whole(table.get("max"), 30, low, 40)
    fans = table.get("fans") if isinstance(table.get("fans"), list) else []
    models = table.get("models") if isinstance(table.get("models"), list) else []
    return {
        "maker": " ".join(str(table.get("maker") or "").split())[:60],
        "models": [" ".join(str(m).split())[:60] for m in models][:6],
        "min": low,
        "max": high,
        "step": _whole(table.get("step"), 1, 1, 5),
        "modes": modes,
        "fans": [f for f in fans if isinstance(f, str) and any(f in table_codes[m] for m in modes)],
        "codes": table_codes,
    }


def count(table: dict[str, Any]) -> int:
    return 1 + sum(len(t) for m in table["modes"] for t in table["codes"].get(m, {}).values())


def code_for(table: dict[str, Any], mode: str, fan: str | None, temp: float | None) -> tuple[str, str, int | None]:
    """The code for a setting, picking the nearest fan speed and temperature the file has.

    Returns (code, fan used, temperature used)."""
    if mode == "off":
        return table["codes"]["off"], fan or "", None
    by_fan = table["codes"].get(mode)
    if not by_fan:
        raise TableError(f"The code file has no “{mode}” mode.")
    use_fan = fan if fan in by_fan else ("auto" if "auto" in by_fan else next(iter(by_fan)))
    temps = by_fan[use_fan]
    if "any" in temps:
        return temps["any"], use_fan, None
    want = round(float(temp if temp is not None else 24))
    use_temp = min(temps, key=lambda t: (abs(int(t) - want), int(t)))
    return temps[use_temp], use_fan, int(use_temp)


def all_codes(table: dict[str, Any]) -> dict[tuple, str]:
    """Every code with its setting: {("off",): code, ("cool", "auto", 24): code, …}."""
    out: dict[tuple, str] = {("off",): table["codes"]["off"]}
    for mode in table["modes"]:
        for fan, temps in table["codes"].get(mode, {}).items():
            for temp, code in temps.items():
                out[(mode, fan, None if temp == "any" else int(temp))] = code
    return out


def describe_setting(key: tuple) -> str:
    """("cool", "auto", 24) -> "Cool 24° · fan auto"."""
    if key[0] == "off":
        return "Off"
    mode = {"fan_only": "Fan", "heat_cool": "Auto", "auto": "Auto"}.get(key[0], key[0].capitalize())
    temp = f" {key[2]}°" if len(key) > 2 and key[2] is not None else ""
    return f"{mode}{temp} · fan {key[1]}"


def parse_index(markdown: str) -> list[dict[str, Any]]:
    """SmartIR's climate list (docs/CLIMATE.md): every Broadlink code file with its brand and models."""
    import re  # noqa: PLC0415

    out, brand = [], ""
    for line in markdown.splitlines():
        if line.startswith("#### "):
            brand = line[5:].strip()
            continue
        m = re.match(r"\|\s*\[(\d+)\]\([^)]*\)\s*\|\s*(.*?)\s*\|\s*(.*?)\s*\|", line)
        if m and brand and "broadlink" in m.group(3).lower():
            models = [x.strip() for x in re.split(r"<br\s*/?>", m.group(2)) if x.strip()]
            out.append({"code": int(m.group(1)), "brand": brand, "models": models})
    return out
