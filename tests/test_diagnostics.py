"""Diagnostics download."""

from __future__ import annotations

from unittest.mock import AsyncMock

from pytest_homeassistant_custom_component.common import MockConfigEntry
from pytest_homeassistant_custom_component.components.diagnostics import (
    get_diagnostics_for_config_entry,
)
from pytest_homeassistant_custom_component.typing import ClientSessionGenerator

from custom_components.kidsalert.const import VERSION
from homeassistant.core import HomeAssistant

from .test_init import setup_entry


async def test_diagnostics(
    hass: HomeAssistant,
    hass_client: ClientSessionGenerator,
    config_entry: MockConfigEntry,
    mock_api: AsyncMock,
) -> None:
    await setup_entry(hass, config_entry)

    diagnostics = await get_diagnostics_for_config_entry(hass, hass_client, config_entry)

    assert diagnostics["version"] == VERSION
    assert diagnostics["entry"] == {"data": {"language": "pl"}, "options": {}}
    assert diagnostics["coordinator"]["alert_count"] == 3
    assert diagnostics["coordinator"]["last_seen_id"] == 102
    assert diagnostics["coordinator"]["last_update_success"] is True
    assert [alert["id"] for alert in diagnostics["latest_alerts"]] == [102, 101, 100]
