# Contributing

Thanks for helping! Issues and pull requests in **Polish or English** are both welcome.

## Reporting a problem

Use the [bug report form](https://github.com/MichalZaniewicz/ha-kidsalert/issues/new/choose). A **diagnostics file** (Settings → Devices & services → KidsAlert → ⋮ → Download diagnostics) answers most questions up front; it holds only public alert data and your options. For a card problem, add the browser console output.

Something wrong in an **alert itself** (its text, image or danger flag) comes from KidsAlert, not from this integration. Contact them through [kidsalert.pl](https://kidsalert.pl).

## Where the code lives

- `api.py` talks to the alert feed, `coordinator.py` polls it, spots new alerts and fires the events.
- `sensor.py`, `binary_sensor.py`, `event.py` are the entities; `websocket.py` serves the cards.
- `frontend/kidsalert-card.js` holds both cards, their editors and the details dialog, in plain JavaScript with no build step.
- `blueprints/` holds the notification blueprint, `scripts/banners.py` builds the README artwork and the brand icon.

## Development

```bash
pip install -r requirements_test.txt   # needs Python 3.14
pytest --cov
ruff check . && ruff format --check .
```

The Home Assistant test harness needs Linux or macOS. It doesn't run on Windows, so rely on CI (or WSL) there. `requirements_test_min.txt` runs the suite against the oldest supported Home Assistant.

**Cards** don't need a running Home Assistant. Serve the repository root and open the preview, which renders both cards against a mock `hass` with made-up demo alerts:

```bash
python -m http.server 8765    # then open http://127.0.0.1:8765/dev/
```

Add `?theme=light`, `?lang=pl`, `?open=latest` or `?open=list:2` to check the other theme, language and the dialog.

## Pull requests

- Keep a PR to one change, and add or update a test for it.
- Update `CHANGELOG.md` and translations (`strings.json`, `translations/en.json`, `translations/pl.json`) when user-facing text changes.
- Check card changes in the preview in both themes and both languages.
- **Don't add KidsAlert's logo, images or alert texts** to the repository, screenshots included. Use the demo alerts in `dev/`.
- Keep the polling gentle: KidsAlert is run by a non-profit, and the minimum interval stays at five minutes.

## Releasing

Bump the version in `manifest.json`, `const.py`, `kidsalert-card.js`, `pyproject.toml` and the `?v=` of the README's image links (tests check they all match; the query makes GitHub, HACS and browsers drop cached images), update it in the wiki's image links too, move the *Unreleased* changelog entries under the new version, then publish a GitHub release tagged `vX.Y.Z`. The release workflow checks the tag and attaches `kidsalert.zip`, which HACS installs.

By participating you agree to the [Code of Conduct](CODE_OF_CONDUCT.md).
