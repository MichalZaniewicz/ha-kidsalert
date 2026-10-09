"""Latest alert sensor."""

from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import KidsAlertConfigEntry
from .entity import KidsAlertEntity

PARALLEL_UPDATES = 0


async def async_setup_entry(
    hass: HomeAssistant,
    entry: KidsAlertConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    async_add_entities([KidsAlertLatestSensor(entry.runtime_data, "latest_alert")])


class KidsAlertLatestSensor(KidsAlertEntity, SensorEntity):
    """Title of the newest alert, with its details as attributes."""

    @property
    def native_value(self) -> str | None:
        latest = self.coordinator.latest
        return latest["title"][:255] if latest else None

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        latest = self.coordinator.latest
        if latest is None:
            return None
        return {
            "alert_id": latest["id"],
            "is_danger": latest["is_danger"],
            "is_sensitive": latest["is_sensitive"],
            "image": latest["image"],
            "thumbnail": latest["thumbnail"],
            "sent_at": latest["sent_at"],
            "language": self.coordinator.api.language,
        }
