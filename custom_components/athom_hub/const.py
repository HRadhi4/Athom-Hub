"""Names used across Athom Hub."""

DOMAIN = "athom_hub"
VERSION = "0.7.0"

STORAGE_KEY = DOMAIN
STORAGE_VERSION = 1

PANEL_URL = "athom-hub"
PANEL_ELEMENT = "athom-hub-panel"
PANEL_TITLE = "Athom Hub"
PANEL_ICON = "mdi:remote"
STATIC_URL = "/athom_hub_static"

SIGNAL_REMOTES_CHANGED = f"{DOMAIN}_remotes_changed"
SIGNAL_LOG = f"{DOMAIN}_log"

# How long the receiver listens for a button press, in seconds.
LEARN_SECONDS = 20
# After the first infrared frame, keep listening this long for the rest of the press.
LEARN_SETTLE_SECONDS = 0.7

# Sends per press when a code does not say (radio remotes always repeat; infrared sends once).
DEFAULT_SENDS = {"ir": 1, "rf": 6}

REMOTE_KINDS = ["tv", "ac", "fan", "curtain", "light", "audio", "other"]

SIGNAL_SETTING_HEARD = f"{DOMAIN}_setting_heard"
# SmartIR's public library of air conditioner code files (what SmartIR itself downloads from).
SMARTIR_RAW = "https://raw.githubusercontent.com/smartHomeHub/SmartIR/master"
