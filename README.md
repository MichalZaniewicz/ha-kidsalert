<p align="center">
  <img src="custom_components/kidsalert/brand/icon.png" width="96" alt="">
</p>

<h1 align="center">KidsAlert for Home Assistant</h1>

<p align="center">
  <a href="https://github.com/hacs/integration"><img src="https://img.shields.io/badge/HACS-Custom-41BDF5.svg" alt="HACS Custom"></a>
  <a href="https://github.com/MichalZaniewicz/ha-kidsalert/releases"><img src="https://img.shields.io/github/v/release/MichalZaniewicz/ha-kidsalert" alt="Release"></a>
  <a href="https://github.com/MichalZaniewicz/ha-kidsalert/actions/workflows/tests.yml"><img src="https://github.com/MichalZaniewicz/ha-kidsalert/actions/workflows/tests.yml/badge.svg" alt="Tests"></a>
  <a href="https://github.com/MichalZaniewicz/ha-kidsalert/actions/workflows/validate.yml"><img src="https://github.com/MichalZaniewicz/ha-kidsalert/actions/workflows/validate.yml/badge.svg" alt="Validate"></a>
</p>

<p align="center">
  Alerts about online and offline threats to children from <a href="https://kidsalert.pl">kidsalert.pl</a>,
  as Home Assistant entities, automation events and two dashboard cards that install with the integration.
</p>

<p align="center"><b>🇵🇱 <a href="README.pl.md">Polska wersja dokumentacji</a></b></p>

![Latest alert and alert list cards](docs/images/cards.png)

> [!NOTE]
> This is an unofficial, community integration. It is not affiliated with or endorsed by KidsAlert.
> It reads the same public, read-only API the KidsAlert mobile app uses. Alert texts and images belong to KidsAlert.

## Features

- **Latest alert sensor** with the title as its state and the image, danger flag and send time as attributes.
- **Danger binary sensor** that stays on for a configurable number of hours after a danger alert goes out.
- **New alert event entity** and a `kidsalert_new_alert` bus event carrying the title, a plain-text excerpt and the image, ready for notifications.
- **Two dashboard cards bundled in the integration**: no separate frontend download, no resource to register. Tapping an alert opens its full text, image and video.
- **Notification blueprint**: phone notification with the image, an excerpt and a tap-through link, optionally for danger alerts only.
- Alerts published while Home Assistant was offline are announced once it is back, up to the ten newest.
- Polish or English alerts, UI translated into both.
- Diagnostics download, brand icons for light and dark themes, tested against the oldest and the newest supported Home Assistant.

## Installation

### HACS (recommended)

[![Open your Home Assistant instance and open this repository in HACS.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=MichalZaniewicz&repository=ha-kidsalert&category=integration)

1. HACS → ⋮ → **Custom repositories** → add `https://github.com/MichalZaniewicz/ha-kidsalert` as an **Integration**.
2. Install **KidsAlert** and restart Home Assistant.

### Manual

Copy `custom_components/kidsalert` from the [latest release](https://github.com/MichalZaniewicz/ha-kidsalert/releases/latest) (`kidsalert.zip`) into `<config>/custom_components/kidsalert` and restart Home Assistant.

Requires Home Assistant **2025.3** or newer.

## Configuration

[![Open your Home Assistant instance and start setting up KidsAlert.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=kidsalert)

**Settings → Devices & services → Add integration → KidsAlert**, then pick the alert language. You can add the integration once per language.

**Configure** on the integration offers:

| Option | Default | Range |
| --- | --- | --- |
| Check for new alerts every | 10 min | 5–120 min |
| Keep the danger sensor on for | 24 h | 1–168 h |

## Entities

Entity IDs follow your Home Assistant language. The examples below are for English with Polish alerts.

| Entity | State | Attributes |
| --- | --- | --- |
| `sensor.kidsalert_pl_latest_alert` | Title of the newest alert | `alert_id`, `is_danger`, `is_sensitive`, `image`, `thumbnail`, `sent_at`, `language` |
| `binary_sensor.kidsalert_pl_danger_alert` | `on` while a danger alert is younger than the configured window | `alert_id`, `title`, `sent_at`, `window_hours` |
| `event.kidsalert_pl_new_alert` | Time of the last new alert; event types `alert` and `danger_alert` | `alert_id`, `title`, `content`, `is_danger`, `is_sensitive`, `image`, `thumbnail`, `sent_at` |

### The `kidsalert_new_alert` event

Fired once for every newly published alert, oldest first:

```yaml
event_type: kidsalert_new_alert
data:
  config_entry_id: 01J…
  alert_id: 177
  title: "It is not a challenge – but there is a game…"
  content: "Plain-text excerpt, up to 500 characters"
  is_danger: true
  is_sensitive: false
  image: https://kidsalert.pl/media/alerts/….jpeg
  thumbnail: https://kidsalert.pl/media/alerts/….200x200_q85.jpg
  sent_at: "2026-10-08T15:00:51.947675+02:00"
```

The first start does not replay the existing backlog. After that, the integration remembers the newest alert it has seen, so a restart neither repeats nor loses alerts.

## Dashboard cards

The cards load automatically with the integration. Open a dashboard, **Add card**, search for **KidsAlert**. Both cards have a visual editor.

![Alert details dialog](docs/images/dialog.png)

### Latest alert: `custom:kidsalert-card`

```yaml
type: custom:kidsalert-card
entity: sensor.kidsalert_pl_latest_alert
```

| Option | Default | Description |
| --- | --- | --- |
| `entity` | first KidsAlert sensor | Latest alert sensor of the entry to show |
| `title` | none | Card header |
| `show_image` | `true` | Show the alert image |
| `blur_sensitive` | `true` | Blur images of alerts marked as sensitive |

### Alert list: `custom:kidsalert-list-card`

```yaml
type: custom:kidsalert-list-card
entity: sensor.kidsalert_pl_latest_alert
count: 5
only_danger: false
```

| Option | Default | Description |
| --- | --- | --- |
| `entity` | first KidsAlert sensor | Latest alert sensor of the entry to show |
| `title` | `KidsAlert` | Card header |
| `count` | `5` | Number of alerts (1–30) |
| `only_danger` | `false` | Show danger alerts only |
| `show_thumbnails` | `true` | Show thumbnails |
| `blur_sensitive` | `true` | Blur thumbnails of sensitive alerts |

Alert text comes from an external server, so the cards sanitise it against an allowlist before display. Scripts, frames, inline handlers and non-HTTP links are removed.

## Notifications

[![Open your Home Assistant instance and show the blueprint import dialog with this blueprint pre-filled.](https://my.home-assistant.io/badges/blueprint_import.svg)](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2FMichalZaniewicz%2Fha-kidsalert%2Fblob%2Fmain%2Fblueprints%2Fautomation%2Fkidsalert%2Fnotify_new_alert.yaml)

The blueprint sends a notification through any notify action (a mobile app, a group, Telegram, …) with the image, an excerpt and an optional dashboard to open on tap. It can be limited to danger alerts.

Or write the automation yourself:

```yaml
triggers:
  - trigger: event
    event_type: kidsalert_new_alert
    event_data:
      is_danger: true
actions:
  - action: notify.mobile_app_my_phone
    data:
      title: "⚠️ KidsAlert"
      message: "{{ trigger.event.data.title }}"
      data:
        image: "{{ trigger.event.data.image }}"
```

## How it works

The integration polls `GET https://kidsalert.pl/alerts/?lang=<pl|en>`, the endpoint the mobile app reads. The full text of an alert (`/alerts/<id>/`) is fetched only for new alerts and when a card opens one, then cached. No account and no personal data are involved. The minimum polling interval is five minutes, to stay polite to a service run by a non-profit.

## Troubleshooting

- **The cards are missing from the card picker**: reload the browser tab, or clear the frontend cache in the Companion app settings. The cards are registered when the integration starts.
- **"KidsAlert integration not found" in a card**: the integration is not set up, or the `entity` in the card points to a different sensor.
- **Diagnostics**: Settings → Devices & services → KidsAlert → ⋮ → **Download diagnostics**. Attach the file to [an issue](https://github.com/MichalZaniewicz/ha-kidsalert/issues).
- **Debug logs**:

  ```yaml
  logger:
    logs:
      custom_components.kidsalert: debug
  ```

## Development

Home Assistant does not run on Windows, so use Linux, macOS, WSL or a dev container.

```bash
python3.14 -m venv .venv && source .venv/bin/activate
pip install -r requirements_test.txt
pytest --cov
ruff check . && ruff format --check .
```

`requirements_test_min.txt` runs the same suite against Home Assistant 2025.3, the oldest supported release.

**Releasing**: bump the version in `manifest.json`, `const.py`, `kidsalert-card.js` and `pyproject.toml` (a test enforces they match), update `CHANGELOG.md`, then publish a GitHub release tagged `vX.Y.Z`. The release workflow checks the tag and attaches `kidsalert.zip` for HACS.

## License

[MIT](LICENSE). The KidsAlert name, logo and alert content belong to their owners.
