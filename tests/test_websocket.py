"""Websocket API consumed by the dashboard cards."""

from __future__ import annotations

from unittest.mock import AsyncMock

from pytest_homeassistant_custom_component.common import MockConfigEntry
from pytest_homeassistant_custom_component.typing import WebSocketGenerator

from custom_components.kidsalert.api import KidsAlertApiError
from homeassistant.core import HomeAssistant

from .test_init import setup_entry

SENSOR = "sensor.kidsalert_pl_latest_alert"


async def test_alert_list(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    config_entry: MockConfigEntry,
    mock_api: AsyncMock,
) -> None:
    await setup_entry(hass, config_entry)
    client = await hass_ws_client(hass)

    await client.send_json_auto_id({"type": "kidsalert/alerts", "entity_id": SENSOR})
    msg = await client.receive_json()
    assert msg["success"]
    result = msg["result"]
    assert [alert["id"] for alert in result["alerts"]] == [102, 101, 100]
    assert result["language"] == "pl"
    assert result["danger_hours"] == 24
    assert result["alerts"][2] == {
        "id": 100,
        "title": "Przejazd kolejowy",
        "image": None,
        "thumbnail": None,
        "is_danger": False,
        "is_sensitive": True,
        "send_at": "2026-09-20T11:54:50+02:00",
        "sent_at": "2026-09-20T11:54:50+02:00",
    }

    # Without a target the first loaded entry answers.
    await client.send_json_auto_id({"type": "kidsalert/alerts"})
    assert (await client.receive_json())["success"]


async def test_alert_list_unknown_target(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    config_entry: MockConfigEntry,
    mock_api: AsyncMock,
) -> None:
    await setup_entry(hass, config_entry)
    client = await hass_ws_client(hass)

    await client.send_json_auto_id({"type": "kidsalert/alerts", "entity_id": "sensor.other"})
    msg = await client.receive_json()
    assert not msg["success"]
    assert msg["error"]["code"] == "not_found"

    await client.send_json_auto_id({"type": "kidsalert/alerts", "entry_id": "missing"})
    assert (await client.receive_json())["error"]["code"] == "not_found"


async def test_alert_detail_is_cached(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    config_entry: MockConfigEntry,
    mock_api: AsyncMock,
) -> None:
    await setup_entry(hass, config_entry)
    client = await hass_ws_client(hass)

    for _ in range(2):
        await client.send_json_auto_id(
            {"type": "kidsalert/alert", "alert_id": 102, "entity_id": SENSOR}
        )
        msg = await client.receive_json()
        assert msg["success"]

    detail = msg["result"]
    assert detail["id"] == 102
    assert detail["content"].startswith("<p><strong>Stanowisko KidsAlert")
    assert detail["video"] == "https://kidsalert.pl/media/alerts/videos/game.mp4"
    assert detail["is_danger"] is True
    assert mock_api.get_alert.call_count == 1


async def test_alert_detail_unavailable(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    config_entry: MockConfigEntry,
    mock_api: AsyncMock,
) -> None:
    await setup_entry(hass, config_entry)
    mock_api.get_alert.side_effect = KidsAlertApiError("down")
    client = await hass_ws_client(hass)

    await client.send_json_auto_id({"type": "kidsalert/alert", "alert_id": 5})
    msg = await client.receive_json()
    assert not msg["success"]
    assert msg["error"]["code"] == "unavailable"


async def test_commands_without_loaded_entry(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    config_entry: MockConfigEntry,
    mock_api: AsyncMock,
) -> None:
    await setup_entry(hass, config_entry)
    await hass.config_entries.async_unload(config_entry.entry_id)
    client = await hass_ws_client(hass)

    await client.send_json_auto_id({"type": "kidsalert/alert", "alert_id": 102})
    assert (await client.receive_json())["error"]["code"] == "not_found"
