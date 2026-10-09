# KidsAlert (unofficial) for Home Assistant

<p align="center">
  <img src="https://raw.githubusercontent.com/MichalZaniewicz/ha-kidsalert/main/docs/hero-banner.svg?v=0.1.2" alt="KidsAlert for Home Assistant">
</p>

<p align="center">
  <a href="LICENSE"><img alt="License" src="https://img.shields.io/github/license/MichalZaniewicz/ha-kidsalert"></a>
  <a href="https://github.com/MichalZaniewicz/ha-kidsalert/releases"><img alt="Release" src="https://img.shields.io/github/v/release/MichalZaniewicz/ha-kidsalert"></a>
  <a href="https://github.com/MichalZaniewicz/ha-kidsalert/actions/workflows/tests.yml"><img alt="Tests" src="https://img.shields.io/github/actions/workflow/status/MichalZaniewicz/ha-kidsalert/tests.yml?branch=main&label=tests"></a>
</p>

[KidsAlert](https://kidsalert.pl) warns Polish parents about new threats to children: online scams, dangerous trends, risky "challenges", and what is happening in schools and on the street. This integration brings those alerts into Home Assistant, as entities, an event for automations, a phone notification and two dashboard cards that come with it.

> [!TIP]
> ⭐ **Enjoying this integration?** Every star is real motivation to keep building new features :)
>
> ☕ Want to say thanks another way? You can [buy me a coffee](https://buymeacoffee.com/zanula).

<!-- The badge lives OUTSIDE the alert on purpose: Home Assistant/HACS rewrites a GitHub alert
into <ha-alert> and drops every child whose textContent is empty, which silently removes any
<img> placed inside it. -->

[![Star this repo](https://img.shields.io/github/stars/MichalZaniewicz/ha-kidsalert?style=for-the-badge&logo=github&label=STAR%20THIS%20REPO&labelColor=555555&color=ff5d5d)](https://github.com/MichalZaniewicz/ha-kidsalert) [![Buy me a coffee](https://img.shields.io/badge/BUY%20ME%20A%20COFFEE-FFDD00?style=for-the-badge&logo=buymeacoffee&logoColor=black)](https://buymeacoffee.com/zanula)

<p align="center">
  <a href="https://my.home-assistant.io/redirect/hacs_repository/?owner=MichalZaniewicz&repository=ha-kidsalert&category=integration"><img alt="Open your Home Assistant instance and open a repository inside the Home Assistant Community Store." src="https://my.home-assistant.io/badges/hacs_repository.svg"></a>
</p>

<p align="center">
  <b><a href="https://github.com/MichalZaniewicz/ha-kidsalert/wiki">Documentation (wiki)</a></b> · <a href="https://github.com/MichalZaniewicz/ha-kidsalert/wiki/Installation">Installation</a> · <a href="https://github.com/MichalZaniewicz/ha-kidsalert/wiki/Configuration">Configuration</a> · <a href="https://github.com/MichalZaniewicz/ha-kidsalert/wiki/Entities">Entities</a> · <a href="https://github.com/MichalZaniewicz/ha-kidsalert/wiki/Cards">Cards</a> · <a href="https://github.com/MichalZaniewicz/ha-kidsalert/wiki/Notifications">Notifications</a>
</p>

## What it does

![KidsAlert for Home Assistant: the cards, the alert dialog, sensitive content and Polish](https://raw.githubusercontent.com/MichalZaniewicz/ha-kidsalert/main/docs/trailer.webp?v=0.1.2)

- 🚨 **Know the moment an alert goes out.** Every new alert fires an event with its title, a plain-text excerpt and the image, once. Alerts published while Home Assistant was off are announced when it's back.
- 📱 **A notification on your phone in one click.** A ready-made blueprint sends the image and the first lines of the alert, opens your dashboard on tap, and can be limited to danger alerts.
- 🛡️ **A danger switch for your home.** A binary sensor stays on for a few hours after a danger alert: turn a light red, play an announcement, or show a banner on the wall tablet.
- 🖼️ **Two dashboard cards, already inside.** The latest alert and a list of recent ones. Nothing else to download from HACS and no resource to register; both have a visual editor.
- 📖 **The whole alert, without leaving Home Assistant.** Tap an alert for its full text, the image and the video. The text is cleaned before display, so a script or a frame can't sneak onto your dashboard.
- 🙈 **Gentle with sensitive content.** Images of alerts marked as sensitive stay blurred until you tap them.
- 🇵🇱 **Polish or English.** Pick the language of the alerts; the interface and the cards speak both.
- 🪶 **Light on a non-profit service.** One small request every 10 minutes by default, the full text only for new alerts, no account and no personal data.

<p align="center">
  <img src="https://raw.githubusercontent.com/MichalZaniewicz/ha-kidsalert/main/docs/notifications-banner.svg?v=0.1.2" alt="Notifications">
</p>

## Notifications

Import the blueprint, pick your phone's notify action, and decide whether you want every alert or danger alerts only.

<p align="center">
  <a href="https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2FMichalZaniewicz%2Fha-kidsalert%2Fblob%2Fmain%2Fblueprints%2Fautomation%2Fkidsalert%2Fnotify_new_alert.yaml"><img alt="Open your Home Assistant instance and show the blueprint import dialog with this blueprint pre-filled." src="https://my.home-assistant.io/badges/blueprint_import.svg"></a>
</p>

Prefer your own automation? Trigger on the **New alert** event entity or the `kidsalert_new_alert` event. **[Examples and every field](https://github.com/MichalZaniewicz/ha-kidsalert/wiki/Notifications)**

<p align="center">
  <img src="https://raw.githubusercontent.com/MichalZaniewicz/ha-kidsalert/main/docs/cards-banner.svg?v=0.1.2" alt="Dashboard cards">
</p>

## Dashboard cards

The cards install and register with the integration. Open a dashboard, **Add card**, search for **KidsAlert**, and they find your alerts on their own. They follow your light or dark theme and your Home Assistant language.

![Latest alert and recent alerts cards](https://raw.githubusercontent.com/MichalZaniewicz/ha-kidsalert/main/docs/images/cards.png?v=0.1.2)

Tap any alert to read it in full:

![Alert details dialog](https://raw.githubusercontent.com/MichalZaniewicz/ha-kidsalert/main/docs/images/dialog.png?v=0.1.2)

<sub>Screenshots show made-up demo alerts.</sub> **[Card options](https://github.com/MichalZaniewicz/ha-kidsalert/wiki/Cards)**

<p align="center">
  <img src="https://raw.githubusercontent.com/MichalZaniewicz/ha-kidsalert/main/docs/installation-banner.svg?v=0.1.2" alt="Installation">
</p>

## Get started

1. **HACS:** click the button below (or add this repository in HACS as an *Integration*) and download **KidsAlert**.

   <p align="center"><a href="https://my.home-assistant.io/redirect/hacs_repository/?owner=MichalZaniewicz&repository=ha-kidsalert&category=integration"><img alt="Open this repository in HACS" src="https://my.home-assistant.io/badges/hacs_repository.svg" height="28"></a></p>

2. **Restart** Home Assistant.
3. **Add the integration:** click the button below (or Settings → Devices & services → **Add integration** → **KidsAlert**) and pick the language of the alerts.

   <p align="center"><a href="https://my.home-assistant.io/redirect/config_flow_start/?domain=kidsalert"><img alt="Add the KidsAlert integration to Home Assistant" src="https://my.home-assistant.io/badges/config_flow_start.svg" height="28"></a></p>

Then add [the cards](https://github.com/MichalZaniewicz/ha-kidsalert/wiki/Cards) and [the notification](https://github.com/MichalZaniewicz/ha-kidsalert/wiki/Notifications). Requires Home Assistant **2025.3** or newer. Full instructions, every option and every entity are in the **[wiki](https://github.com/MichalZaniewicz/ha-kidsalert/wiki)**.

> [!NOTE]
> This is an unofficial, community integration, not affiliated with or endorsed by KidsAlert. It reads the same public, read-only alert feed as the KidsAlert mobile app. The KidsAlert name and the alerts' texts and images belong to their owners; this project does not use the KidsAlert logo.

## Documentation

Everything else is in the **[wiki](https://github.com/MichalZaniewicz/ha-kidsalert/wiki)**:

- **Getting started:** [Installation](https://github.com/MichalZaniewicz/ha-kidsalert/wiki/Installation) · [Configuration](https://github.com/MichalZaniewicz/ha-kidsalert/wiki/Configuration) - setting it up, every option with its default.
- **Features:** [Cards](https://github.com/MichalZaniewicz/ha-kidsalert/wiki/Cards) · [Notifications](https://github.com/MichalZaniewicz/ha-kidsalert/wiki/Notifications) - the two cards with every option, the blueprint and automation examples.
- **Reference:** [Entities](https://github.com/MichalZaniewicz/ha-kidsalert/wiki/Entities) · [Events](https://github.com/MichalZaniewicz/ha-kidsalert/wiki/Events) - every entity and its attributes, the event and its data.
- **Background:** [How it works](https://github.com/MichalZaniewicz/ha-kidsalert/wiki/How-it-works) · [Troubleshooting](https://github.com/MichalZaniewicz/ha-kidsalert/wiki/Troubleshooting) · [Known limitations](https://github.com/MichalZaniewicz/ha-kidsalert/wiki/Known-limitations).

## Acknowledgments

- The people behind [KidsAlert](https://kidsalert.pl), who watch the internet so parents don't have to. If you find the alerts useful, support them directly.

## License

MIT - see [LICENSE](LICENSE).
