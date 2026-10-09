"""Polling coordinator for KidsAlert."""

from __future__ import annotations

from datetime import datetime, timedelta
import html
import logging
import re
import time
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .api import KidsAlertApi, KidsAlertApiError
from .const import (
    CONF_DANGER_HOURS,
    CONF_SCAN_INTERVAL,
    DEFAULT_DANGER_HOURS,
    DEFAULT_SCAN_INTERVAL,
    DETAIL_CACHE_SECONDS,
    DOMAIN,
    EVENT_CONTENT_LENGTH,
    MAX_EVENTS_PER_UPDATE,
    STORAGE_VERSION,
)

_LOGGER = logging.getLogger(__name__)

_HIDDEN_RE = re.compile(r"<(script|style)\b.*?</\1\s*>", re.IGNORECASE | re.DOTALL)
_TAG_RE = re.compile(r"<[^>]+>")
_BLOCK_END_RE = re.compile(r"</(p|li|h[1-6]|div)>|<br\s*/?>", re.IGNORECASE)
_SPACE_RE = re.compile(r"[ \t\r\f\v]+")


def html_to_text(value: str | None) -> str:
    """Flatten alert HTML into plain text for notifications."""
    if not value:
        return ""
    text = _BLOCK_END_RE.sub("\n", _HIDDEN_RE.sub("", value))
    text = html.unescape(_TAG_RE.sub("", text))
    lines = (_SPACE_RE.sub(" ", line).strip() for line in text.splitlines())
    return "\n".join(line for line in lines if line)


def _media_url(value: Any) -> str | None:
    if isinstance(value, str) and value.startswith(("https://", "http://")):
        return value
    return None


def normalize_alert(raw: dict[str, Any]) -> dict[str, Any]:
    """Keep the fields the integration and card rely on."""
    return {
        "id": int(raw["id"]),
        "title": raw.get("title") or "",
        "image": _media_url(raw.get("image")),
        "thumbnail": _media_url(raw.get("thumbnail_small")) or _media_url(raw.get("image")),
        "is_danger": bool(raw.get("is_danger")),
        "is_sensitive": bool(raw.get("is_sensitive")),
        "send_at": raw.get("send_at"),
        "sent_at": raw.get("was_sent_at") or raw.get("send_at"),
    }


def normalize_alert_detail(raw: dict[str, Any]) -> dict[str, Any]:
    """Normalize a detail payload, which adds content and video."""
    alert = normalize_alert(raw)
    alert["content"] = raw.get("content") or ""
    alert["video"] = _media_url(raw.get("video"))
    alert["modified"] = raw.get("modified")
    return alert


def event_payload(alert: dict[str, Any]) -> dict[str, Any]:
    """Data attached to bus events and event entity triggers."""
    return {
        "alert_id": alert["id"],
        "title": alert["title"],
        "content": alert.get("content_text", ""),
        "is_danger": alert["is_danger"],
        "is_sensitive": alert["is_sensitive"],
        "image": alert["image"],
        "thumbnail": alert["thumbnail"],
        "sent_at": alert["sent_at"],
    }


def alert_time(alert: dict[str, Any]) -> datetime | None:
    """Return when the alert went out."""
    value = alert.get("sent_at") or alert.get("send_at")
    return dt_util.parse_datetime(value) if value else None


class KidsAlertCoordinator(DataUpdateCoordinator[list[dict[str, Any]]]):
    """Fetch the alert list and detect alerts that were not seen before."""

    config_entry: ConfigEntry

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, api: KidsAlertApi) -> None:
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=DOMAIN,
            update_interval=timedelta(
                minutes=entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
            ),
        )
        self.api = api
        self.danger_hours: int = entry.options.get(CONF_DANGER_HOURS, DEFAULT_DANGER_HOURS)
        # Alerts first seen in the latest refresh, oldest first.
        self.new_alerts: list[dict[str, Any]] = []
        # True until setup finishes, so alerts that arrived while Home Assistant was
        # down are announced once the event entity and listeners exist.
        self.startup_pending = True
        self._store: Store[dict[str, Any]] = Store(
            hass, STORAGE_VERSION, f"{DOMAIN}.{entry.entry_id}"
        )
        self._last_seen_id: int | None = None
        self._details: dict[int, tuple[float, dict[str, Any]]] = {}

    async def _async_setup(self) -> None:
        stored = await self._store.async_load()
        if stored and isinstance(stored.get("last_seen_id"), int):
            self._last_seen_id = stored["last_seen_id"]

    async def _async_update_data(self) -> list[dict[str, Any]]:
        try:
            raw_alerts = await self.api.async_get_alerts()
        except KidsAlertApiError as err:
            raise UpdateFailed(str(err)) from err

        alerts = sorted(
            (normalize_alert(item) for item in raw_alerts),
            key=lambda alert: alert["id"],
            reverse=True,
        )

        new_alerts: list[dict[str, Any]] = []
        if alerts:
            newest_id = alerts[0]["id"]
            # Without a stored marker this is the first run: treat the backlog as seen.
            if self._last_seen_id is not None:
                fresh = [a for a in alerts if a["id"] > self._last_seen_id]
                # Copies, so the event excerpt does not leak into the shared list.
                new_alerts = [dict(a) for a in reversed(fresh[:MAX_EVENTS_PER_UPDATE])]
            if newest_id != self._last_seen_id:
                self._last_seen_id = newest_id
                await self._store.async_save({"last_seen_id": newest_id})

        for alert in new_alerts:
            detail = await self._async_fetch_detail(alert["id"])
            alert["content_text"] = html_to_text(detail["content"] if detail else "")[
                :EVENT_CONTENT_LENGTH
            ]

        self.new_alerts = new_alerts
        return alerts

    @property
    def last_seen_id(self) -> int | None:
        """Highest alert id already announced."""
        return self._last_seen_id

    @property
    def latest(self) -> dict[str, Any] | None:
        """Newest alert."""
        return self.data[0] if self.data else None

    @property
    def active_danger(self) -> dict[str, Any] | None:
        """Newest danger alert still inside the configured window."""
        cutoff = dt_util.utcnow() - timedelta(hours=self.danger_hours)
        for alert in self.data or []:
            if not alert["is_danger"]:
                continue
            sent = alert_time(alert)
            # Strict, so the expiry timer that fires exactly at the cutoff sees it closed.
            if sent is not None and sent > cutoff:
                return alert
        return None

    async def async_get_alert(self, alert_id: int) -> dict[str, Any]:
        """Return the full alert, served from cache when fresh."""
        detail = await self._async_fetch_detail(alert_id)
        if detail is None:
            raise KidsAlertApiError(f"Alert {alert_id} is unavailable")
        return detail

    async def _async_fetch_detail(self, alert_id: int) -> dict[str, Any] | None:
        cached = self._details.get(alert_id)
        if cached and time.monotonic() - cached[0] < DETAIL_CACHE_SECONDS:
            return cached[1]
        try:
            detail = normalize_alert_detail(await self.api.async_get_alert(alert_id))
        except KidsAlertApiError as err:
            _LOGGER.debug("Could not fetch alert %s: %s", alert_id, err)
            return cached[1] if cached else None
        self._details[alert_id] = (time.monotonic(), detail)
        return detail
