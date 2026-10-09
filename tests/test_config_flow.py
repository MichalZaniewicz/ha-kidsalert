"""Config and options flows."""

from __future__ import annotations

from collections.abc import Generator
from datetime import timedelta
from unittest.mock import AsyncMock, patch

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.kidsalert.api import KidsAlertApiError
from custom_components.kidsalert.const import (
    CONF_DANGER_HOURS,
    CONF_LANGUAGE,
    CONF_SCAN_INTERVAL,
    DOMAIN,
)
from homeassistant.config_entries import SOURCE_USER
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from .test_init import setup_entry


@pytest.fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    with patch("custom_components.kidsalert.async_setup_entry", return_value=True) as mock:
        yield mock


async def test_user_flow(
    hass: HomeAssistant, mock_api: AsyncMock, mock_setup_entry: AsyncMock
) -> None:
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_LANGUAGE: "en"}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "KidsAlert (EN)"
    assert result["data"] == {CONF_LANGUAGE: "en"}
    assert result["result"].unique_id == "en"
    assert len(mock_setup_entry.mock_calls) == 1


async def test_user_flow_recovers_from_connection_error(
    hass: HomeAssistant, mock_api: AsyncMock, mock_setup_entry: AsyncMock
) -> None:
    mock_api.get_alerts.side_effect = KidsAlertApiError("down")
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_LANGUAGE: "pl"}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "cannot_connect"}

    mock_api.get_alerts.side_effect = None
    mock_api.get_alerts.return_value = []
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_LANGUAGE: "pl"}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY


async def test_language_configured_once(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    mock_api: AsyncMock,
    mock_setup_entry: AsyncMock,
) -> None:
    config_entry.add_to_hass(hass)
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_LANGUAGE: "pl"}
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"


async def test_options_flow_reloads_entry(
    hass: HomeAssistant, config_entry: MockConfigEntry, mock_api: AsyncMock
) -> None:
    await setup_entry(hass, config_entry)

    result = await hass.config_entries.options.async_init(config_entry.entry_id)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "init"

    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {CONF_SCAN_INTERVAL: 15.0, CONF_DANGER_HOURS: 48.0}
    )
    await hass.async_block_till_done()
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert config_entry.options == {CONF_SCAN_INTERVAL: 15, CONF_DANGER_HOURS: 48}

    coordinator = config_entry.runtime_data
    assert coordinator.update_interval == timedelta(minutes=15)
    assert coordinator.danger_hours == 48
