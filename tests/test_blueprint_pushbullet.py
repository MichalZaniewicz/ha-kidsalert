"""The Pushbullet blueprint, run as a real automation against a mocked notify action."""

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
    Path(__file__).parents[1] / "blueprints" / "automation" / "kidsalert" / "notify_pushbullet.yaml"
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
                    "input": {"event_entity": EVENT, **inputs},
                }
            }
        },
    )
    await hass.async_block_till_done()


@pytest.fixture
def pushes(hass: HomeAssistant) -> list[ServiceCall]:
    return async_mock_service(hass, "notify", "pushbullet")


async def publish(
    hass: HomeAssistant, mock_api: AsyncMock, freezer: FrozenDateTimeFactory, *, danger: bool
) -> None:
    newest = max(alert["id"] for alert in mock_api.alerts)
    mock_api.alerts = [new_alert(newest + 1, danger=danger), *mock_api.alerts]
    await poll(hass, freezer)


@pytest.mark.freeze_time(NOW)
async def test_pushes_image_by_default(
    hass: HomeAssistant,
    tmp_path: Path,
    config_entry: MockConfigEntry,
    mock_api: AsyncMock,
    freezer: FrozenDateTimeFactory,
    pushes: list[ServiceCall],
) -> None:
    await setup_entry(hass, config_entry)
    await setup_blueprint(hass, tmp_path, content_length=20)

    await publish(hass, mock_api, freezer, danger=True)

    assert len(pushes) == 1
    assert pushes[0].data == {
        "title": "⚠️ KidsAlert: Alert 103",
        "message": "Stanowisko KidsAlert…",
        "target": [],
        "data": {"file_url": "https://kidsalert.pl/media/alerts/new.jpeg"},
    }


@pytest.mark.freeze_time(NOW)
async def test_link_targets_and_full_text(
    hass: HomeAssistant,
    tmp_path: Path,
    config_entry: MockConfigEntry,
    mock_api: AsyncMock,
    freezer: FrozenDateTimeFactory,
    pushes: list[ServiceCall],
) -> None:
    await setup_entry(hass, config_entry)
    await setup_blueprint(
        hass, tmp_path, attachment="link", targets=" device/Pixel 9, ,email/me@example.com"
    )

    await publish(hass, mock_api, freezer, danger=False)

    data = pushes[0].data
    assert data["title"] == "KidsAlert: Alert 103"
    assert data["message"].startswith("Stanowisko KidsAlert jest jednoznaczne")
    assert data["target"] == ["device/Pixel 9", "email/me@example.com"]
    assert data["data"] == {"url": "https://kidsalert.pl/notification/103/"}


@pytest.mark.freeze_time(NOW)
async def test_custom_link(
    hass: HomeAssistant,
    tmp_path: Path,
    config_entry: MockConfigEntry,
    mock_api: AsyncMock,
    freezer: FrozenDateTimeFactory,
    pushes: list[ServiceCall],
) -> None:
    await setup_entry(hass, config_entry)
    await setup_blueprint(
        hass, tmp_path, attachment="link", link_url="https://ha.example.com/lovelace/kids"
    )
    await publish(hass, mock_api, freezer, danger=False)
    assert pushes[0].data["data"] == {"url": "https://ha.example.com/lovelace/kids"}


@pytest.mark.freeze_time(NOW)
async def test_text_only_and_title_only(
    hass: HomeAssistant,
    tmp_path: Path,
    config_entry: MockConfigEntry,
    mock_api: AsyncMock,
    freezer: FrozenDateTimeFactory,
    pushes: list[ServiceCall],
) -> None:
    await setup_entry(hass, config_entry)
    await setup_blueprint(hass, tmp_path, attachment="none", content_length=0)

    await publish(hass, mock_api, freezer, danger=False)

    assert pushes[0].data["message"] == "Alert 103"
    assert pushes[0].data["data"] == {}


@pytest.mark.freeze_time(NOW)
async def test_only_danger(
    hass: HomeAssistant,
    tmp_path: Path,
    config_entry: MockConfigEntry,
    mock_api: AsyncMock,
    freezer: FrozenDateTimeFactory,
    pushes: list[ServiceCall],
) -> None:
    await setup_entry(hass, config_entry)
    await setup_blueprint(hass, tmp_path, only_danger=True)

    await publish(hass, mock_api, freezer, danger=False)
    assert pushes == []
    await publish(hass, mock_api, freezer, danger=True)
    assert len(pushes) == 1


async def test_nothing_on_reload(
    hass: HomeAssistant,
    tmp_path: Path,
    config_entry: MockConfigEntry,
    mock_api: AsyncMock,
    pushes: list[ServiceCall],
) -> None:
    await setup_entry(hass, config_entry)
    await setup_blueprint(hass, tmp_path)

    await hass.config_entries.async_reload(config_entry.entry_id)
    await hass.async_block_till_done()
    assert pushes == []
