"""Binary sensor that is on while a recent danger alert is active."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timedelta
from typing import Any

from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.event import async_track_point_in_utc_time

from . import KidsAlertConfigEntry
from .coordinator import alert_time
from .entity import KidsAlertEntity

PARALLEL_UPDATES = 0


async def async_setup_entry(
    hass: HomeAssistant,
    entry: KidsAlertConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    async_add_entities([KidsAlertDangerBinarySensor(entry.runtime_data, "danger_alert")])


class KidsAlertDangerBinarySensor(KidsAlertEntity, BinarySensorEntity):
    """On when a danger alert went out within the configured number of hours."""

    _attr_device_class = BinarySensorDeviceClass.SAFETY
    _unsub_expiry: Callable[[], None] | None = None

    @property
    def is_on(self) -> bool:
        return self.coordinator.active_danger is not None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        alert = self.coordinator.active_danger
        return {
            "alert_id": alert["id"] if alert else None,
            "title": alert["title"] if alert else None,
            "sent_at": alert["sent_at"] if alert else None,
            "window_hours": self.coordinator.danger_hours,
        }

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        self._schedule_expiry()

    async def async_will_remove_from_hass(self) -> None:
        self._cancel_expiry()
        await super().async_will_remove_from_hass()

    @callback
    def _handle_coordinator_update(self) -> None:
        self._schedule_expiry()
        super()._handle_coordinator_update()

    @callback
    def _schedule_expiry(self) -> None:
        """Turn off exactly when the window closes instead of at the next poll."""
        self._cancel_expiry()
        alert = self.coordinator.active_danger
        sent = alert_time(alert) if alert else None
        if sent is not None:
            self._unsub_expiry = async_track_point_in_utc_time(
                self.hass,
                self._handle_expiry,
                sent + timedelta(hours=self.coordinator.danger_hours),
            )

    @callback
    def _handle_expiry(self, _now: datetime) -> None:
        self._unsub_expiry = None
        self._schedule_expiry()
        self.async_write_ha_state()

    @callback
    def _cancel_expiry(self) -> None:
        if self._unsub_expiry is not None:
            self._unsub_expiry()
            self._unsub_expiry = None
