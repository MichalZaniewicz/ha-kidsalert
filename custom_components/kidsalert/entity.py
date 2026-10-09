"""Base entity for KidsAlert."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import API_BASE_URL, DOMAIN
from .coordinator import KidsAlertCoordinator


class KidsAlertEntity(CoordinatorEntity[KidsAlertCoordinator]):
    """Entity attached to the KidsAlert service device."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: KidsAlertCoordinator, key: str) -> None:
        super().__init__(coordinator)
        entry = coordinator.config_entry
        self._attr_translation_key = key
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer="KidsAlert",
            entry_type=DeviceEntryType.SERVICE,
            configuration_url=API_BASE_URL,
        )
