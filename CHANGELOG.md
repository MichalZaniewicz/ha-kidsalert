# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses
[Semantic Versioning](https://semver.org/).

## [Unreleased]

## [0.1.0] - 2026-10-09

### Added

- Config flow with one entry per alert language (Polish, English) and options for the polling interval and the danger window.
- Latest alert sensor, danger binary sensor and new alert event entity on a single service device.
- `kidsalert_new_alert` bus event with a plain-text excerpt, including alerts published while Home Assistant was offline.
- Bundled `kidsalert-card` and `kidsalert-list-card` dashboard cards with visual editors, a details dialog and HTML sanitising.
- Notification blueprint.
- Diagnostics and brand icons.

[Unreleased]: https://github.com/MichalZaniewicz/ha-kidsalert/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/MichalZaniewicz/ha-kidsalert/releases/tag/v0.1.0
