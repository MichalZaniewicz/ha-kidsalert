"""Websocket commands used by the bundled dashboard cards."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.components import websocket_api
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import entity_registry as er

from .api import KidsAlertApiError
from .const import DOMAIN
from .coordinator import KidsAlertCoordinator

_TARGET = {
    vol.Optional("entity_id"): str,
    vol.Optional("entry_id"): str,
}


@callback
def async_register_websocket_commands(hass: HomeAssistant) -> None:
    websocket_api.async_register_command(hass, ws_alerts)
    websocket_api.async_register_command(hass, ws_alert)


def _coordinator(hass: HomeAssistant, msg: dict[str, Any]) -> KidsAlertCoordinator | None:
    """Pick the entry behind the card's entity, a given entry, or the first loaded one."""
    entry_id = msg.get("entry_id")
    if entity_id := msg.get("entity_id"):
        reg_entry = er.async_get(hass).async_get(entity_id)
        if reg_entry is None or reg_entry.platform != DOMAIN:
            return None
        entry_id = reg_entry.config_entry_id
    for entry in hass.config_entries.async_entries(DOMAIN):
        if entry.state is not ConfigEntryState.LOADED:
            continue
        if entry_id is None or entry.entry_id == entry_id:
            return entry.runtime_data
    return None


@websocket_api.websocket_command({vol.Required("type"): "kidsalert/alerts", **_TARGET})
@callback
def ws_alerts(
    hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]
) -> None:
    """Return the cached alert list."""
    coordinator = _coordinator(hass, msg)
    if coordinator is None:
        connection.send_error(msg["id"], "not_found", "No loaded KidsAlert entry")
        return
    connection.send_result(
        msg["id"],
        {
            "alerts": coordinator.data or [],
            "language": coordinator.api.language,
            "danger_hours": coordinator.danger_hours,
            "last_update_success": coordinator.last_update_success,
        },
    )


@websocket_api.websocket_command(
    {vol.Required("type"): "kidsalert/alert", vol.Required("alert_id"): int, **_TARGET}
)
@websocket_api.async_response
async def ws_alert(
    hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]
) -> None:
    """Return one alert with its full HTML content."""
    coordinator = _coordinator(hass, msg)
    if coordinator is None:
        connection.send_error(msg["id"], "not_found", "No loaded KidsAlert entry")
        return
    try:
        alert = await coordinator.async_get_alert(msg["alert_id"])
    except KidsAlertApiError as err:
        connection.send_error(msg["id"], "unavailable", str(err))
        return
    connection.send_result(msg["id"], alert)
