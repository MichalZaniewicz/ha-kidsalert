"""Sensor, binary sensor and event entities."""

from __future__ import annotations

from datetime import timedelta
from unittest.mock import AsyncMock

from freezegun.api import FrozenDateTimeFactory
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry, async_fire_time_changed

from custom_components.kidsalert.const import CONF_DANGER_HOURS, CONF_SCAN_INTERVAL
from custom_components.kidsalert.event import KidsAlertEventEntity
from homeassistant.const import STATE_OFF, STATE_ON
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from .conftest import NOW
from .test_init import setup_entry

SENSOR = "sensor.kidsalert_pl_latest_alert"
DANGER = "binary_sensor.kidsalert_pl_danger_alert"
EVENT = "event.kidsalert_pl_new_alert"


def with_options(entry: MockConfigEntry, options: dict[str, int]) -> MockConfigEntry:
    return MockConfigEntry(
        domain=entry.domain,
        title=entry.title,
        data=dict(entry.data),
        options=options,
        unique_id=entry.unique_id,
    )


@pytest.mark.freeze_time(NOW)
async def test_latest_alert_sensor(
    hass: HomeAssistant, config_entry: MockConfigEntry, mock_api: AsyncMock
) -> None:
    await setup_entry(hass, config_entry)

    state = hass.states.get(SENSOR)
    assert state.state == "To nie jest challenge – ale jest gra"
    assert state.attributes["alert_id"] == 102
    assert state.attributes["is_danger"] is True
    assert state.attributes["is_sensitive"] is False
    assert state.attributes["image"] == "https://kidsalert.pl/media/alerts/game.jpeg"
    assert (
        state.attributes["thumbnail"]
        == "https://kidsalert.pl/media/alerts/game.jpeg.200x200_q85.jpg"
    )
    assert state.attributes["sent_at"] == "2026-10-08T15:00:51.947675+02:00"
    assert state.attributes["language"] == "pl"


def test_event_text_is_kept_out_of_the_history_database() -> None:
    assert "content" in KidsAlertEventEntity._unrecorded_attributes


@pytest.mark.freeze_time(NOW)
async def test_entities_share_one_service_device(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    mock_api: AsyncMock,
    entity_registry: er.EntityRegistry,
) -> None:
    await setup_entry(hass, config_entry)
    entries = er.async_entries_for_config_entry(entity_registry, config_entry.entry_id)
    assert {entry.entity_id for entry in entries} == {SENSOR, DANGER, EVENT}
    assert len({entry.device_id for entry in entries}) == 1


@pytest.mark.freeze_time(NOW)
async def test_danger_sensor_turns_off_after_window(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    mock_api: AsyncMock,
    freezer: FrozenDateTimeFactory,
) -> None:
    await setup_entry(hass, config_entry)

    state = hass.states.get(DANGER)
    assert state.state == STATE_ON
    assert state.attributes["alert_id"] == 102
    assert state.attributes["window_hours"] == 24

    # Alert 102 went out 2026-10-08 13:00 UTC; 24 h later the window closes.
    freezer.move_to("2026-10-09T13:10:00+00:00")
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    state = hass.states.get(DANGER)
    assert state.state == STATE_OFF
    assert state.attributes["alert_id"] is None


# 50 s before alert 102 (sent 13:00:51.95 UTC) leaves the 24 h window.
@pytest.mark.freeze_time("2026-10-09T13:00:00+00:00")
async def test_danger_sensor_turns_off_on_time_without_polling(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    mock_api: AsyncMock,
    freezer: FrozenDateTimeFactory,
) -> None:
    await setup_entry(hass, config_entry)
    assert hass.states.get(DANGER).state == STATE_ON
    polls = mock_api.get_alerts.call_count

    freezer.move_to("2026-10-09T13:00:51.900000+00:00")
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    assert hass.states.get(DANGER).state == STATE_ON

    freezer.move_to("2026-10-09T13:00:52+00:00")
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    assert hass.states.get(DANGER).state == STATE_OFF
    assert mock_api.get_alerts.call_count == polls


@pytest.mark.freeze_time(NOW)
async def test_expiry_timer_is_cancelled_on_unload(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    mock_api: AsyncMock,
    freezer: FrozenDateTimeFactory,
) -> None:
    await setup_entry(hass, config_entry)
    assert await hass.config_entries.async_unload(config_entry.entry_id)
    await hass.async_block_till_done()

    freezer.move_to("2026-10-09T14:00:00+00:00")
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    assert hass.states.get(DANGER).state == "unavailable"


@pytest.mark.freeze_time("2026-10-10T10:00:00+00:00")
async def test_danger_window_follows_options(
    hass: HomeAssistant, mock_api: AsyncMock, config_entry: MockConfigEntry
) -> None:
    await setup_entry(hass, with_options(config_entry, {CONF_DANGER_HOURS: 72}))
    assert hass.states.get(DANGER).state == STATE_ON


@pytest.mark.freeze_time(NOW)
async def test_danger_sensor_ignores_non_danger_alerts(
    hass: HomeAssistant, config_entry: MockConfigEntry, mock_api: AsyncMock
) -> None:
    mock_api.alerts = [a for a in mock_api.alerts if not a["is_danger"]]
    await setup_entry(hass, config_entry)
    assert hass.states.get(DANGER).state == STATE_OFF


async def test_empty_alert_list(
    hass: HomeAssistant, config_entry: MockConfigEntry, mock_api: AsyncMock
) -> None:
    mock_api.alerts = []
    await setup_entry(hass, config_entry)
    state = hass.states.get(SENSOR)
    assert state.state == "unknown"
    assert "alert_id" not in state.attributes


async def test_poll_interval_follows_options(
    hass: HomeAssistant, mock_api: AsyncMock, config_entry: MockConfigEntry
) -> None:
    config_entry = with_options(config_entry, {CONF_SCAN_INTERVAL: 30})
    await setup_entry(hass, config_entry)
    assert config_entry.runtime_data.update_interval == timedelta(minutes=30)
