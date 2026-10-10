"""KidsAlert integration: alerts from kidsalert.pl with bundled dashboard cards."""

from __future__ import annotations

from pathlib import Path

from homeassistant.components.frontend import add_extra_js_url
from homeassistant.components.http import StaticPathConfig
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.typing import ConfigType

from .api import KidsAlertApi
from .const import (
    CARD_FILENAME,
    CONF_LANGUAGE,
    DEFAULT_LANGUAGE,
    DOMAIN,
    EVENT_NEW_ALERT,
    STATIC_URL,
    VERSION,
)
from .coordinator import KidsAlertCoordinator, event_payload
from .loader import async_register_loader, async_remove_loader
from .websocket import async_register_websocket_commands

PLATFORMS = [Platform.SENSOR, Platform.BINARY_SENSOR, Platform.EVENT]

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

type KidsAlertConfigEntry = ConfigEntry[KidsAlertCoordinator]


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Serve the bundled cards and register the websocket API once."""
    await hass.http.async_register_static_paths(
        [StaticPathConfig(STATIC_URL, str(Path(__file__).parent / "frontend"), True)]
    )
    # The version query busts browser caches whenever the integration is updated.
    card_url = f"{STATIC_URL}/{CARD_FILENAME}?v={VERSION}"
    add_extra_js_url(hass, card_url)
    await async_register_loader(hass, card_url)
    async_register_websocket_commands(hass)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: KidsAlertConfigEntry) -> bool:
    api = KidsAlertApi(
        async_get_clientsession(hass), entry.data.get(CONF_LANGUAGE, DEFAULT_LANGUAGE)
    )
    coordinator = KidsAlertCoordinator(hass, entry, api)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    @callback
    def _fire_bus_events() -> None:
        for alert in coordinator.new_alerts:
            hass.bus.async_fire(
                EVENT_NEW_ALERT,
                {"config_entry_id": entry.entry_id, **event_payload(alert)},
            )

    # Registered after the platforms so entity states are written before the events.
    entry.async_on_unload(coordinator.async_add_listener(_fire_bus_events))
    if coordinator.startup_pending:
        _fire_bus_events()
        coordinator.startup_pending = False

    entry.async_on_unload(entry.add_update_listener(_async_reload_entry))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: KidsAlertConfigEntry) -> bool:
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_remove_entry(hass: HomeAssistant, entry: KidsAlertConfigEntry) -> None:
    """Drop the dashboard loader together with the last KidsAlert entry."""
    if not any(
        other.entry_id != entry.entry_id for other in hass.config_entries.async_entries(DOMAIN)
    ):
        await async_remove_loader(hass)


async def _async_reload_entry(hass: HomeAssistant, entry: KidsAlertConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)
