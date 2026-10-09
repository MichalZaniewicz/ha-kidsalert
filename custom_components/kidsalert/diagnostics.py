"""Diagnostics for KidsAlert."""

from __future__ import annotations

from typing import Any

from homeassistant.core import HomeAssistant

from . import KidsAlertConfigEntry
from .const import VERSION


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: KidsAlertConfigEntry
) -> dict[str, Any]:
    """Alert data is public, so nothing needs redacting."""
    coordinator = entry.runtime_data
    alerts = coordinator.data or []
    return {
        "version": VERSION,
        "entry": {"data": dict(entry.data), "options": dict(entry.options)},
        "coordinator": {
            "last_update_success": coordinator.last_update_success,
            "update_interval": str(coordinator.update_interval),
            "danger_hours": coordinator.danger_hours,
            "last_seen_id": coordinator.last_seen_id,
            "alert_count": len(alerts),
        },
        "latest_alerts": alerts[:5],
    }
