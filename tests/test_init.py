"""Setup, polling, new-alert events and the bundled frontend."""

from __future__ import annotations

from datetime import timedelta
from typing import Any
from unittest.mock import AsyncMock

from freezegun.api import FrozenDateTimeFactory
import pytest
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    async_capture_events,
    async_fire_time_changed,
)

from custom_components.kidsalert.api import KidsAlertApiError
from custom_components.kidsalert.const import EVENT_NEW_ALERT, STATIC_URL
from homeassistant.components.frontend import DATA_EXTRA_MODULE_URL
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.core import HomeAssistant

from .conftest import NOW

SENSOR = "sensor.kidsalert_pl_latest_alert"
EVENT = "event.kidsalert_pl_new_alert"


async def setup_entry(hass: HomeAssistant, entry: MockConfigEntry) -> None:
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()


async def poll(hass: HomeAssistant, freezer: FrozenDateTimeFactory) -> None:
    freezer.tick(timedelta(minutes=10))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()


def new_alert(alert_id: int, *, danger: bool) -> dict[str, Any]:
    return {
        "id": alert_id,
        "title": f"Alert {alert_id}",
        "image": "https://kidsalert.pl/media/alerts/new.jpeg",
        "thumbnail_small": None,
        "is_danger": danger,
        "is_sensitive": False,
        "send_at": NOW,
        "was_sent_at": NOW,
    }


@pytest.mark.freeze_time(NOW)
async def test_setup_and_unload(
    hass: HomeAssistant, config_entry: MockConfigEntry, mock_api: AsyncMock
) -> None:
    await setup_entry(hass, config_entry)
    assert config_entry.state is ConfigEntryState.LOADED
    assert hass.states.get(SENSOR).state == "To nie jest challenge – ale jest gra"

    assert await hass.config_entries.async_unload(config_entry.entry_id)
    await hass.async_block_till_done()
    assert config_entry.state is ConfigEntryState.NOT_LOADED


async def test_setup_retries_when_api_is_down(
    hass: HomeAssistant, config_entry: MockConfigEntry, mock_api: AsyncMock
) -> None:
    mock_api.get_alerts.side_effect = KidsAlertApiError("down")
    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    assert config_entry.state is ConfigEntryState.SETUP_RETRY


async def test_first_run_does_not_announce_backlog(
    hass: HomeAssistant, config_entry: MockConfigEntry, mock_api: AsyncMock
) -> None:
    events = async_capture_events(hass, EVENT_NEW_ALERT)
    await setup_entry(hass, config_entry)

    assert events == []
    assert hass.states.get(EVENT).state == STATE_UNKNOWN
    mock_api.get_alert.assert_not_called()


@pytest.mark.freeze_time(NOW)
async def test_new_alert_fires_bus_event_and_event_entity(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    mock_api: AsyncMock,
    freezer: FrozenDateTimeFactory,
) -> None:
    await setup_entry(hass, config_entry)
    events = async_capture_events(hass, EVENT_NEW_ALERT)

    mock_api.alerts = [new_alert(103, danger=True), *mock_api.alerts]
    await poll(hass, freezer)

    assert len(events) == 1
    data = events[0].data
    assert data["config_entry_id"] == config_entry.entry_id
    assert data["alert_id"] == 103
    assert data["title"] == "Alert 103"
    assert data["is_danger"] is True
    assert data["content"].startswith("Stanowisko KidsAlert jest jednoznaczne: CHALLENGE NIE MA!")
    assert "alert(1)" not in data["content"]
    assert "<" not in data["content"]
    assert data["content"].endswith("Więcej: https://kidsalert.pl/")

    event_state = hass.states.get(EVENT)
    assert event_state.attributes["event_type"] == "danger_alert"
    assert event_state.attributes["content"] == data["content"]
    assert event_state.attributes["alert_id"] == 103
    assert hass.states.get(SENSOR).state == "Alert 103"
    # The excerpt belongs to the event only, not to the list the cards read.
    assert "content_text" not in config_entry.runtime_data.data[0]

    # Nothing new on the next poll: no duplicate announcements.
    await poll(hass, freezer)
    assert len(events) == 1


@pytest.mark.freeze_time(NOW)
async def test_alerts_missed_while_down_are_announced_on_startup(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    mock_api: AsyncMock,
    hass_storage: dict[str, Any],
) -> None:
    hass_storage[f"kidsalert.{config_entry.entry_id}"] = {
        "version": 1,
        "minor_version": 1,
        "key": f"kidsalert.{config_entry.entry_id}",
        "data": {"last_seen_id": 100},
    }
    events = async_capture_events(hass, EVENT_NEW_ALERT)
    await setup_entry(hass, config_entry)

    assert [event.data["alert_id"] for event in events] == [101, 102]
    assert hass.states.get(EVENT).attributes["alert_id"] == 102
    assert config_entry.runtime_data.startup_pending is False


@pytest.mark.freeze_time(NOW)
async def test_last_seen_id_is_persisted(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    mock_api: AsyncMock,
    hass_storage: dict[str, Any],
    freezer: FrozenDateTimeFactory,
) -> None:
    await setup_entry(hass, config_entry)
    freezer.tick(timedelta(seconds=30))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    assert hass_storage[f"kidsalert.{config_entry.entry_id}"]["data"] == {"last_seen_id": 102}


@pytest.mark.freeze_time(NOW)
async def test_backlog_is_capped(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    mock_api: AsyncMock,
    freezer: FrozenDateTimeFactory,
) -> None:
    await setup_entry(hass, config_entry)
    events = async_capture_events(hass, EVENT_NEW_ALERT)

    mock_api.alerts = [new_alert(i, danger=False) for i in range(130, 102, -1)] + mock_api.alerts
    await poll(hass, freezer)

    # The ten newest, announced oldest first.
    assert [event.data["alert_id"] for event in events] == list(range(121, 131))


@pytest.mark.freeze_time(NOW)
async def test_update_failure_marks_entities_unavailable(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    mock_api: AsyncMock,
    freezer: FrozenDateTimeFactory,
) -> None:
    await setup_entry(hass, config_entry)
    mock_api.get_alerts.side_effect = KidsAlertApiError("down")
    await poll(hass, freezer)
    assert hass.states.get(SENSOR).state == STATE_UNAVAILABLE


async def test_card_is_served_and_registered(
    hass: HomeAssistant,
    hass_client,
    config_entry: MockConfigEntry,
    mock_api: AsyncMock,
) -> None:
    await setup_entry(hass, config_entry)

    urls = hass.data[DATA_EXTRA_MODULE_URL].urls
    assert any(url.startswith(f"{STATIC_URL}/kidsalert-card.js?v=") for url in urls)

    client = await hass_client()
    resp = await client.get(f"{STATIC_URL}/kidsalert-card.js")
    assert resp.status == 200
    assert 'define("kidsalert-card"' in await resp.text()
