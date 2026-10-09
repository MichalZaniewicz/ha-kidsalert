"""Shared fixtures for KidsAlert tests."""

from __future__ import annotations

from collections.abc import Generator
import copy
import json
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.kidsalert.const import CONF_LANGUAGE, DOMAIN

FIXTURES = Path(__file__).parent / "fixtures"

# Inside the 24 h window of alert 102 (sent 2026-10-08 13:00 UTC).
NOW = "2026-10-09T10:00:00+00:00"


def load_fixture(name: str) -> Any:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations: None) -> None:
    """Load custom_components/ in every test."""


@pytest.fixture
def alerts() -> list[dict[str, Any]]:
    return load_fixture("alerts.json")


@pytest.fixture
def alert_detail() -> dict[str, Any]:
    return load_fixture("alert_102.json")


@pytest.fixture
def mock_api(alerts: list[dict[str, Any]], alert_detail: dict[str, Any]) -> Generator[AsyncMock]:
    """Patch the API client; tests mutate `.alerts` to simulate new publications."""
    with (
        patch(
            "custom_components.kidsalert.api.KidsAlertApi.async_get_alerts",
            autospec=True,
        ) as get_alerts,
        patch(
            "custom_components.kidsalert.api.KidsAlertApi.async_get_alert",
            autospec=True,
        ) as get_alert,
    ):
        state = AsyncMock()
        state.alerts = alerts
        state.get_alerts = get_alerts
        state.get_alert = get_alert

        async def _alerts(_self: Any) -> list[dict[str, Any]]:
            return copy.deepcopy(state.alerts)

        async def _alert(_self: Any, alert_id: int) -> dict[str, Any]:
            return {**copy.deepcopy(alert_detail), "id": alert_id}

        get_alerts.side_effect = _alerts
        get_alert.side_effect = _alert
        yield state


@pytest.fixture
def config_entry() -> MockConfigEntry:
    return MockConfigEntry(
        domain=DOMAIN,
        title="KidsAlert (PL)",
        data={CONF_LANGUAGE: "pl"},
        unique_id="pl",
    )
