"""HTTP client and payload helpers."""

from __future__ import annotations

from typing import Any

import pytest
from pytest_homeassistant_custom_component.test_util.aiohttp import AiohttpClientMocker

from custom_components.kidsalert.api import KidsAlertApi, KidsAlertApiError
from custom_components.kidsalert.coordinator import html_to_text, normalize_alert
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

LIST_URL = "https://kidsalert.pl/alerts/"


async def test_get_alerts(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker, alerts: list[dict[str, Any]]
) -> None:
    aioclient_mock.get(LIST_URL, params={"lang": "en"}, json=[*alerts, {"no": "id"}, "junk"])
    api = KidsAlertApi(async_get_clientsession(hass), "en")

    result = await api.async_get_alerts()

    assert [alert["id"] for alert in result] == [102, 101, 100]
    _method, url, _data, headers = aioclient_mock.mock_calls[0]
    assert url.query["lang"] == "en"
    assert headers["User-Agent"].startswith("HomeAssistant-KidsAlert/")


async def test_get_alert(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker, alert_detail: dict[str, Any]
) -> None:
    aioclient_mock.get("https://kidsalert.pl/alerts/102/", json=alert_detail)
    api = KidsAlertApi(async_get_clientsession(hass), "pl")
    assert (await api.async_get_alert(102))["video"].endswith("game.mp4")


@pytest.mark.parametrize(
    "response",
    [
        {"status": 500},
        {"json": {"detail": "not a list"}},
        {"text": "<html>not json</html>"},
        {"exc": TimeoutError()},
    ],
)
async def test_get_alerts_errors(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker, response: dict[str, Any]
) -> None:
    aioclient_mock.get(LIST_URL, **response)
    api = KidsAlertApi(async_get_clientsession(hass), "pl")
    with pytest.raises(KidsAlertApiError):
        await api.async_get_alerts()


async def test_get_alert_rejects_bad_payload(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    aioclient_mock.get("https://kidsalert.pl/alerts/7/", json=[])
    api = KidsAlertApi(async_get_clientsession(hass), "pl")
    with pytest.raises(KidsAlertApiError):
        await api.async_get_alert(7)


def test_html_to_text() -> None:
    html = (
        "<p>Pierwszy&nbsp;akapit &amp; więcej</p>\r\n<ul><li>Jeden</li><li>Dwa</li></ul>"
        "<style>p{}</style><script>alert(1)</script>Linia<br>Druga"
    )
    assert html_to_text(html) == "Pierwszy\xa0akapit & więcej\n\n• Jeden\n• Dwa\nLinia\nDruga"
    assert html_to_text(None) == ""


def test_html_to_text_keeps_link_addresses() -> None:
    html = (
        '<p>See <a href="https://raport.kidsalert.pl/">the report</a>.</p>'
        '<p><a href="https://youtu.be/x">https://youtu.be/x</a></p>'
        '<p><a href="mailto:a@b.pl">write to us</a></p>'
    )
    assert html_to_text(html) == (
        "See the report (https://raport.kidsalert.pl/).\n\nhttps://youtu.be/x\n\nwrite to us"
    )


def test_normalize_alert_rejects_non_http_media() -> None:
    alert = normalize_alert(
        {
            "id": "5",
            "title": None,
            "image": "javascript:alert(1)",
            "thumbnail_small": "/relative.jpg",
            "send_at": "2026-01-01T00:00:00+00:00",
        }
    )
    assert alert["id"] == 5
    assert alert["title"] == ""
    assert alert["image"] is None
    assert alert["thumbnail"] is None
    assert alert["sent_at"] == "2026-01-01T00:00:00+00:00"
