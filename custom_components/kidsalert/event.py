"""Event entity triggered for every new alert."""

from __future__ import annotations

from homeassistant.components.event import EventEntity
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import KidsAlertConfigEntry
from .const import EVENT_TYPE_ALERT, EVENT_TYPE_DANGER
from .coordinator import event_payload
from .entity import KidsAlertEntity

PARALLEL_UPDATES = 0


async def async_setup_entry(
    hass: HomeAssistant,
    entry: KidsAlertConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    async_add_entities([KidsAlertEventEntity(entry.runtime_data, "new_alert")])


class KidsAlertEventEntity(KidsAlertEntity, EventEntity):
    """Fires `alert` or `danger_alert` when a new alert is published."""

    _attr_event_types = [EVENT_TYPE_ALERT, EVENT_TYPE_DANGER]
    # The full alert text stays on the state for automations, out of the history database.
    _unrecorded_attributes = frozenset({"content"})

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        if self.coordinator.startup_pending:
            self._trigger_new_alerts()
            self.async_write_ha_state()

    @callback
    def _handle_coordinator_update(self) -> None:
        self._trigger_new_alerts()
        super()._handle_coordinator_update()

    @callback
    def _trigger_new_alerts(self) -> None:
        for alert in self.coordinator.new_alerts:
            self._trigger_event(
                EVENT_TYPE_DANGER if alert["is_danger"] else EVENT_TYPE_ALERT,
                event_payload(alert),
            )
