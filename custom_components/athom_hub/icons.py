"""A picture and a colour for every remote button, chosen from its name.

So people who do not read can still find "power" or "open" at a glance.
No Home Assistant imports: tested on its own.
"""

from __future__ import annotations

import re

RED, BLUE, ORANGE, GREEN = "#FF5C7A", "#4C8DFF", "#FF9A3D", "#3DD68C"

# (words, icon, colour). The first rule whose words all appear wins, so longer rules come first.
_RULES: list[tuple[tuple[str, ...], str, str | None]] = [
    (("power", "off"), "mdi:power", RED),
    (("power",), "mdi:power", RED),
    (("on", "off"), "mdi:power", RED),
    (("vol", "up"), "mdi:volume-plus", None),
    (("volume", "up"), "mdi:volume-plus", None),
    (("vol", "down"), "mdi:volume-minus", None),
    (("volume", "down"), "mdi:volume-minus", None),
    (("mute",), "mdi:volume-off", None),
    (("ch", "up"), "mdi:chevron-up-box-outline", None),
    (("channel", "up"), "mdi:chevron-up-box-outline", None),
    (("ch", "down"), "mdi:chevron-down-box-outline", None),
    (("channel", "down"), "mdi:chevron-down-box-outline", None),
    (("temp", "up"), "mdi:thermometer-plus", ORANGE),
    (("temperature", "up"), "mdi:thermometer-plus", ORANGE),
    (("temp", "down"), "mdi:thermometer-minus", BLUE),
    (("temperature", "down"), "mdi:thermometer-minus", BLUE),
    (("fan", "speed"), "mdi:fan-chevron-up", None),
    (("open",), "mdi:arrow-expand-horizontal", GREEN),
    (("close",), "mdi:arrow-collapse-horizontal", None),
    (("stop",), "mdi:stop-circle-outline", RED),
    (("pause",), "mdi:pause", None),
    (("play",), "mdi:play", GREEN),
    (("cool",), "mdi:snowflake", BLUE),
    (("cold",), "mdi:snowflake", BLUE),
    (("heat",), "mdi:fire", ORANGE),
    (("dry",), "mdi:water-percent", BLUE),
    (("auto",), "mdi:thermostat-auto", None),
    (("swing",), "mdi:arrow-oscillating", None),
    (("high",), "mdi:fan-speed-3", None),
    (("medium",), "mdi:fan-speed-2", None),
    (("mid",), "mdi:fan-speed-2", None),
    (("low",), "mdi:fan-speed-1", None),
    (("fan",), "mdi:fan", None),
    (("light",), "mdi:lightbulb-on-outline", ORANGE),
    (("lamp",), "mdi:lightbulb-on-outline", ORANGE),
    (("sleep",), "mdi:power-sleep", None),
    (("timer",), "mdi:timer-outline", None),
    (("mode",), "mdi:swap-horizontal", None),
    (("input",), "mdi:import", None),
    (("source",), "mdi:import", None),
    (("hdmi",), "mdi:video-input-hdmi", None),
    (("home",), "mdi:home-outline", None),
    (("menu",), "mdi:menu", None),
    (("back",), "mdi:arrow-left", None),
    (("return",), "mdi:arrow-left", None),
    (("ok",), "mdi:checkbox-blank-circle-outline", None),
    (("enter",), "mdi:checkbox-blank-circle-outline", None),
    (("select",), "mdi:checkbox-blank-circle-outline", None),
    (("up",), "mdi:chevron-up", None),
    (("down",), "mdi:chevron-down", None),
    (("left",), "mdi:chevron-left", None),
    (("right",), "mdi:chevron-right", None),
    (("plus",), "mdi:plus", None),
    (("minus",), "mdi:minus", None),
    (("netflix",), "mdi:netflix", RED),
    (("youtube",), "mdi:youtube", RED),
]

_REMOTE_ICON = {"tv": "mdi:television", "ac": "mdi:air-conditioner", "fan": "mdi:fan", "curtain": "mdi:curtains",
                "light": "mdi:lightbulb-outline", "audio": "mdi:speaker", "other": "mdi:remote"}

# Icons a person can pick by hand on the page.
CHOICES = ["mdi:power", "mdi:arrow-expand-horizontal", "mdi:arrow-collapse-horizontal", "mdi:stop-circle-outline",
           "mdi:chevron-up", "mdi:chevron-down", "mdi:chevron-left", "mdi:chevron-right", "mdi:plus", "mdi:minus",
           "mdi:volume-plus", "mdi:volume-minus", "mdi:volume-off", "mdi:play", "mdi:pause", "mdi:snowflake", "mdi:fire",
           "mdi:water-percent", "mdi:fan", "mdi:arrow-oscillating", "mdi:thermometer-plus", "mdi:thermometer-minus",
           "mdi:lightbulb-on-outline", "mdi:power-sleep", "mdi:timer-outline", "mdi:swap-horizontal", "mdi:import",
           "mdi:home-outline", "mdi:menu", "mdi:arrow-left", "mdi:checkbox-blank-circle-outline", "mdi:star-outline"]

COLOURS = {"red": RED, "blue": BLUE, "orange": ORANGE, "green": GREEN}


def _words(name: str) -> set[str]:
    text = re.sub(r"([a-z])([A-Z])", r"\1 \2", str(name or ""))
    text = re.sub(r"[^a-z0-9+\-]+", " ", text.lower())
    words = set(text.split())
    if "+" in name:
        words.add("plus")
    if re.search(r"(^|\s)-($|\s)", name):
        words.add("minus")
    return words


def guess(name: str, remote_kind: str | None = None) -> tuple[str, str | None]:
    """(icon, colour or None) for a button name."""
    words = _words(name)
    for need, icon, colour in _RULES:
        if all(w in words for w in need):
            return icon, colour
    number = next((w for w in words if w.isdigit() and len(w) == 1), None)
    if number is not None and len(words) == 1:
        return f"mdi:numeric-{number}", None
    return _REMOTE_ICON.get(remote_kind or "other", "mdi:remote"), None


def for_button(button: dict, remote_kind: str | None = None) -> tuple[str, str | None]:
    """The picture chosen by hand if there is one, otherwise the guess."""
    icon, colour = guess(button.get("name", ""), remote_kind)
    if button.get("icon"):
        icon = button["icon"]
    if button.get("colour") in COLOURS:
        colour = COLOURS[button["colour"]]
    elif button.get("colour") == "none":
        colour = None
    return icon, colour
