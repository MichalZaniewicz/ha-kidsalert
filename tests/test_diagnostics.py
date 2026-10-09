"""Diagnostics download."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock

from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.kidsalert.const import VERSION
from custom_components.kidsalert.diagnostics import async_get_config_entry_diagnostics
from homeassistant.core import HomeAssistant

from .test_init import setup_entry


async def test_diagnostics(
    hass: HomeAssistant, config_entry: MockConfigEntry, mock_api: AsyncMock
) -> None:
    await setup_entry(hass, config_entry)

    diagnostics = await async_get_config_entry_diagnostics(hass, config_entry)

    # The download is served as JSON.
    json.dumps(diagnostics)
    assert diagnostics["version"] == VERSION
    assert diagnostics["entry"] == {"data": {"language": "pl"}, "options": {}}
    assert diagnostics["coordinator"]["alert_count"] == 3
    assert diagnostics["coordinator"]["last_seen_id"] == 102
    assert diagnostics["coordinator"]["last_update_success"] is True
    assert [alert["id"] for alert in diagnostics["latest_alerts"]] == [102, 101, 100]
