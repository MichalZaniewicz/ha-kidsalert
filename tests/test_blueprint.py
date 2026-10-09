"""The bundled notification blueprint, run as a real automation."""

from __future__ import annotations

from pathlib import Path
import shutil
from unittest.mock import AsyncMock

from freezegun.api import FrozenDateTimeFactory
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry, async_mock_service

from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.setup import async_setup_component

from .conftest import NOW
from .test_init import new_alert, poll, setup_entry

BLUEPRINT = (
    Path(__file__).parents[1] / "blueprints" / "automation" / "kidsalert" / "notify_new_alert.yaml"
)
EVENT = "event.kidsalert_pl_new_alert"


async def setup_blueprint(hass: HomeAssistant, tmp_path: Path, **inputs: object) -> None:
    hass.config.config_dir = str(tmp_path)
    target = tmp_path / "blueprints" / "automation" / "kidsalert" / BLUEPRINT.name
    target.parent.mkdir(parents=True)
    shutil.copy(BLUEPRINT, target)
    assert await async_setup_component(
        hass,
        "automation",
        {
            "automation": {
                "use_blueprint": {
                    "path": f"kidsalert/{BLUEPRINT.name}",
                    "input": {"event_entity": EVENT, "notify_action": "notify.family", **inputs},
                }
            }
        },
    )
    await hass.async_block_till_done()


@pytest.fixture
def notify_calls(hass: HomeAssistant) -> list[ServiceCall]:
    return async_mock_service(hass, "notify", "family")


@pytest.mark.freeze_time(NOW)
async def test_notifies_with_image_excerpt_and_link(
    hass: HomeAssistant,
    tmp_path: Path,
    config_entry: MockConfigEntry,
    mock_api: AsyncMock,
    freezer: FrozenDateTimeFactory,
    notify_calls: list[ServiceCall],
) -> None:
    await setup_entry(hass, config_entry)
    await setup_blueprint(hass, tmp_path, content_length=20, open_path="/lovelace/kids")

    mock_api.alerts = [new_alert(103, danger=True), *mock_api.alerts]
    await poll(hass, freezer)

    assert len(notify_calls) == 1
    data = notify_calls[0].data
    assert data["title"] == "⚠️ KidsAlert"
    assert data["message"] == "Alert 103\n\nStanowisko KidsAlert…"
    assert data["data"] == {
        "tag": "kidsalert-103",
        "group": "kidsalert",
        "image": "https://kidsalert.pl/media/alerts/new.jpeg",
        "url": "/lovelace/kids",
        "clickAction": "/lovelace/kids",
    }


@pytest.mark.freeze_time(NOW)
async def test_only_danger_skips_regular_alerts(
    hass: HomeAssistant,
    tmp_path: Path,
    config_entry: MockConfigEntry,
    mock_api: AsyncMock,
    freezer: FrozenDateTimeFactory,
    notify_calls: list[ServiceCall],
) -> None:
    await setup_entry(hass, config_entry)
    await setup_blueprint(hass, tmp_path, only_danger=True, attach_image=False, content_length=0)

    mock_api.alerts = [new_alert(103, danger=False), *mock_api.alerts]
    await poll(hass, freezer)
    assert notify_calls == []

    mock_api.alerts = [new_alert(104, danger=True), *mock_api.alerts]
    await poll(hass, freezer)
    assert len(notify_calls) == 1
    assert notify_calls[0].data["message"] == "Alert 104"
    assert notify_calls[0].data["data"] == {"tag": "kidsalert-104", "group": "kidsalert"}


async def test_no_notification_on_startup_or_reload(
    hass: HomeAssistant,
    tmp_path: Path,
    config_entry: MockConfigEntry,
    mock_api: AsyncMock,
    notify_calls: list[ServiceCall],
) -> None:
    await setup_entry(hass, config_entry)
    await setup_blueprint(hass, tmp_path)

    await hass.config_entries.async_reload(config_entry.entry_id)
    await hass.async_block_till_done()
    assert notify_calls == []
