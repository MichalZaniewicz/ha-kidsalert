"""Constants for the KidsAlert integration."""

from __future__ import annotations

from typing import Final

DOMAIN: Final = "kidsalert"
VERSION: Final = "0.1.4"

API_BASE_URL: Final = "https://kidsalert.pl"

CONF_LANGUAGE: Final = "language"
CONF_SCAN_INTERVAL: Final = "scan_interval"
CONF_DANGER_HOURS: Final = "danger_hours"

LANGUAGES: Final = ["pl", "en"]
DEFAULT_LANGUAGE: Final = "pl"

# Minutes between polls of the alert list.
DEFAULT_SCAN_INTERVAL: Final = 10
MIN_SCAN_INTERVAL: Final = 5
MAX_SCAN_INTERVAL: Final = 120

# How long a danger alert keeps the binary sensor on.
DEFAULT_DANGER_HOURS: Final = 24
MAX_DANGER_HOURS: Final = 168

# Cap on events fired after a long downtime, so a backlog does not flood automations.
MAX_EVENTS_PER_UPDATE: Final = 10
# Safety cap on the plain-text content attached to events; real alerts are a few
# thousand characters, so in practice events carry the whole text.
EVENT_CONTENT_LENGTH: Final = 20_000
DETAIL_CACHE_SECONDS: Final = 3600

EVENT_NEW_ALERT: Final = "kidsalert_new_alert"
EVENT_TYPE_ALERT: Final = "alert"
EVENT_TYPE_DANGER: Final = "danger_alert"

STATIC_URL: Final = "/kidsalert_static"
CARD_FILENAME: Final = "kidsalert-card.js"

STORAGE_VERSION: Final = 1
