"""Client for the public KidsAlert API used by the mobile app."""

from __future__ import annotations

from typing import Any

import aiohttp

from .const import API_BASE_URL, VERSION

REQUEST_TIMEOUT = aiohttp.ClientTimeout(total=20)


class KidsAlertApiError(Exception):
    """Raised when the KidsAlert API cannot be reached or returns bad data."""


class KidsAlertApi:
    """Read-only access to the alert endpoints."""

    def __init__(self, session: aiohttp.ClientSession, language: str) -> None:
        self._session = session
        self.language = language

    async def async_get_alerts(self) -> list[dict[str, Any]]:
        """Return the alert list, newest first as served by the API."""
        data = await self._get("alerts/")
        if not isinstance(data, list):
            raise KidsAlertApiError("Unexpected alert list payload")
        return [item for item in data if isinstance(item, dict) and "id" in item]

    async def async_get_alert(self, alert_id: int) -> dict[str, Any]:
        """Return a single alert with its full content."""
        data = await self._get(f"alerts/{int(alert_id)}/")
        if not isinstance(data, dict) or "id" not in data:
            raise KidsAlertApiError(f"Unexpected payload for alert {alert_id}")
        return data

    async def _get(self, path: str) -> Any:
        try:
            async with self._session.get(
                f"{API_BASE_URL}/{path}",
                params={"lang": self.language},
                headers={"User-Agent": f"HomeAssistant-KidsAlert/{VERSION}"},
                timeout=REQUEST_TIMEOUT,
            ) as resp:
                resp.raise_for_status()
                return await resp.json()
        except (aiohttp.ClientError, TimeoutError, ValueError) as err:
            raise KidsAlertApiError(f"Request to {path} failed: {err}") from err
