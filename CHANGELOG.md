# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses
[Semantic Versioning](https://semver.org/).

## [Unreleased]

## [0.1.3] - 2026-10-10

### Added

- Pushbullet blueprint: every new alert as a push with the full text and the alert image, a link or the text only, to all your devices or chosen targets.

### Changed

- The `kidsalert_new_alert` event and the event entity carry the whole alert text instead of the first 500 characters. The event entity keeps it out of the history database.
- Alert text in events reads better: a blank line between paragraphs, • for list items, and link addresses kept next to the link text.

## [0.1.2] - 2026-10-10

### Changed

- New integration icon, our own artwork: a red shield with an exclamation mark. The project no longer ships the KidsAlert logo.
- Long alerts fade out at the bottom of the details dialog instead of ending mid-line.
- Documentation moved to the [wiki](https://github.com/MichalZaniewicz/ha-kidsalert/wiki); the README shows demo alerts only.

### Added

- `dev/` preview of the cards with made-up demo alerts, and `scripts/banners.py` for the README artwork and the icon.

## 0.1.1 - 2026-10-10

Release withdrawn: it shipped an icon based on the KidsAlert logo. Its changes are in 0.1.2.

### Changed

- Alert details dialog: a small image next to the title and date, with the text below. Tapping the image opens it full size, and videos open from a ▶ Video button instead of taking up the top of the dialog.
- The dialog takes keyboard focus itself instead of the close button.

## 0.1.0 - 2026-10-09

Release withdrawn: it shipped an icon based on the KidsAlert logo. Its changes are in 0.1.2.

### Added

- Config flow with one entry per alert language (Polish, English) and options for the polling interval and the danger window.
- Latest alert sensor, danger binary sensor and new alert event entity on a single service device.
- `kidsalert_new_alert` bus event with a plain-text excerpt, including alerts published while Home Assistant was offline.
- Bundled `kidsalert-card` and `kidsalert-list-card` dashboard cards with visual editors, a details dialog and HTML sanitising.
- Notification blueprint.
- Diagnostics and brand icons.

[Unreleased]: https://github.com/MichalZaniewicz/ha-kidsalert/compare/v0.1.3...HEAD
[0.1.3]: https://github.com/MichalZaniewicz/ha-kidsalert/compare/v0.1.2...v0.1.3
[0.1.2]: https://github.com/MichalZaniewicz/ha-kidsalert/releases/tag/v0.1.2
