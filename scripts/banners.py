"""Build the README banners, the social preview and the integration's brand icon.

Every SVG embeds subset Manrope and JetBrains Mono (SIL Open Font License) as WOFF, so
GitHub renders the same type on any machine. The PNG social preview and the brand icons
are rendered with headless Chrome. The icon is our own artwork: the integration is
unofficial and must not use the KidsAlert logo.

    pip install fonttools
    python scripts/banners.py --fonts <dir> [--chrome <path to chrome>]

<dir> holds the variable fonts from https://github.com/google/fonts:
Manrope[wght].ttf saved as Manrope.ttf, JetBrainsMono[wght].ttf saved as JetBrainsMono.ttf.
"""

from __future__ import annotations

import argparse
import base64
import html
import io
from pathlib import Path
import re
import subprocess
import tempfile

from fontTools import subset
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
BRAND = ROOT / "custom_components" / "kidsalert" / "brand"

SANS = "KAManrope, Manrope, 'Segoe UI', sans-serif"
MONO = "KAMono, 'JetBrains Mono', Consolas, monospace"
FACES = [
    ("KAManrope", "Manrope.ttf", 500),
    ("KAManrope", "Manrope.ttf", 700),
    ("KAManrope", "Manrope.ttf", 800),
    ("KAMono", "JetBrainsMono.ttf", 500),
    ("KAMono", "JetBrainsMono.ttf", 700),
]

# Navy from the KidsAlert bear, with an alert red as the accent.
INK = "#f3f4ff"
SOFT = "#c5c8ef"
MUTED = "#8b8fc6"
DIM = "#565a8a"
EYEBROW = "#ff8a7a"
RED = "#ff5d5d"
AMBER = "#f6b14a"
GREEN = "#5fc98a"
INDIGO = "#8e95ff"
CARD = "#1b1d38"
TRACK = "#2c2f52"


def defs(prefix: str, cx: float = 0.15, cy: float = 0, r: float = 1.4) -> str:
    return f"""<defs>
<radialGradient id="{prefix}-bg" cx="{cx}" cy="{cy}" r="{r}"><stop offset="0" stop-color="#262c66"/><stop offset="0.5" stop-color="#13152f"/><stop offset="1" stop-color="#0a0b19"/></radialGradient>
<radialGradient id="{prefix}-gl" cx="0.5" cy="0.5" r="0.5"><stop offset="0" stop-color="{RED}" stop-opacity="0.30"/><stop offset="1" stop-color="{RED}" stop-opacity="0"/></radialGradient>
<radialGradient id="{prefix}-gi" cx="0.5" cy="0.5" r="0.5"><stop offset="0" stop-color="#6f78ff" stop-opacity="0.32"/><stop offset="1" stop-color="#6f78ff" stop-opacity="0"/></radialGradient>
<linearGradient id="{prefix}-img" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#3b2a6e"/><stop offset="1" stop-color="#b03a52"/></linearGradient>
<filter id="{prefix}-sh" x="-20%" y="-20%" width="140%" height="150%"><feDropShadow dx="0" dy="14" stdDeviation="14" flood-color="#000" flood-opacity="0.45"/></filter>
</defs>"""


def sep(items: list[str]) -> str:
    return f'<tspan fill="{DIM}">  ·  </tspan>'.join(html.escape(item) for item in items)


def stats(items: list[tuple[str, str]]) -> str:
    parts = [
        f'<tspan fill="{INK}" font-weight="700">{n}</tspan> {html.escape(label)}'
        for n, label in items
    ]
    return f'<tspan fill="{DIM}">  ·  </tspan>'.join(parts)


# ---------- reusable mock widgets ----------


def shield(x: float, y: float, size: float, color: str) -> str:
    s = size / 24
    return (
        f'<g transform="translate({x},{y}) scale({s})"><path d="M12 2 4 5v6c0 5 3.4 9.4 8 11 '
        f'4.6-1.6 8-6 8-11V5l-8-3Z" fill="{color}" fill-opacity="0.18" stroke="{color}" '
        f'stroke-width="1.8" stroke-linejoin="round"/><path d="M12 7.5v5.2" stroke="{color}" '
        f'stroke-width="2.2" stroke-linecap="round"/><circle cx="12" cy="16" r="1.3" '
        f'fill="{color}"/></g>'
    )


def badge(x: float, y: float, text: str, color: str, width: float) -> str:
    return (
        f'<rect x="{x}" y="{y}" width="{width}" height="20" rx="10" fill="{color}"/>'
        f'<text x="{x + width / 2}" y="{y + 14}" text-anchor="middle" font-size="11" '
        f'font-weight="800" letter-spacing="0.8" fill="#fff">{text}</text>'
    )


def latest_card(x: float, y: float, prefix: str) -> str:
    return f"""<g transform="translate({x},{y})" filter="url(#{prefix}-sh)">
<clipPath id="{prefix}-cc"><rect width="236" height="226" rx="18"/></clipPath>
<rect width="236" height="226" rx="18" fill="{CARD}"/>
<g clip-path="url(#{prefix}-cc)"><rect width="236" height="122" fill="url(#{prefix}-img)"/><rect width="6" height="226" fill="{RED}"/></g>
<rect width="236" height="226" rx="18" fill="none" stroke="#fff" stroke-opacity="0.08"/>
{shield(96, 32, 44, "#ffd7d7")}
{badge(18, 138, "DANGER", RED, 76)}
<text x="18" y="182" font-size="16" font-weight="800" fill="{INK}">New phishing wave</text>
<text x="18" y="204" font-size="12" font-weight="500" fill="{MUTED}">targets parents · 2 hours ago</text>
</g>"""


def notification(x: float, y: float, prefix: str, width: float = 270) -> str:
    return f"""<g transform="translate({x},{y})" filter="url(#{prefix}-sh)">
<rect width="{width}" height="78" rx="18" fill="#22254a" stroke="#fff" stroke-opacity="0.10"/>
<rect x="14" y="16" width="30" height="30" rx="9" fill="{RED}"/>
<text x="29" y="38" text-anchor="middle" font-size="19" font-weight="800" fill="#fff">!</text>
<text x="56" y="30" font-size="13" font-weight="800" fill="{INK}">KidsAlert</text>
<text x="{width - 16}" y="30" text-anchor="end" font-size="11" font-weight="500" fill="{MUTED}">now</text>
<text x="56" y="50" font-size="12.5" font-weight="700" fill="{SOFT}">Danger alert: new phishing wave</text>
<text x="56" y="66" font-size="11.5" font-weight="500" fill="{MUTED}">Don't click links in texts about…</text>
</g>"""


def list_card(x: float, y: float, prefix: str, width: float = 270) -> str:
    rows = [
        ("#4f46a5", "Report: helpless online?", "3 days ago", False),
        ("#2f6f73", "Railway crossing selfies", "3 weeks ago", False),
        ("#7a3346", "Scooter stunt videos", "2 months ago", True),
    ]
    out = [
        f'<g transform="translate({x},{y})" filter="url(#{prefix}-sh)">',
        f'<rect width="{width}" height="124" rx="18" fill="{CARD}" stroke="#fff" stroke-opacity="0.08"/>',
    ]
    for i, (color, title, meta, blurred) in enumerate(rows):
        top = 12 + i * 36
        out.append(
            f'<rect x="14" y="{top}" width="28" height="28" rx="7" fill="{color}"'
            f"{' fill-opacity="0.55"' if blurred else ''}/>"
        )
        out.append(
            f'<text x="54" y="{top + 13}" font-size="12.5" font-weight="700" fill="{INK}">{title}</text>'
        )
        out.append(
            f'<text x="54" y="{top + 27}" font-size="11" font-weight="500" fill="{MUTED}">{meta}</text>'
        )
    out.append("</g>")
    return "\n".join(out)


# ---------- banners ----------


def hero() -> tuple[int, int, str]:
    body = f"""{defs("h", 0.2, 0.1, 1.25)}
<rect width="1200" height="300" fill="url(#h-bg)"/><circle cx="40" cy="-40" r="280" fill="url(#h-gi)"/><circle cx="930" cy="150" r="330" fill="url(#h-gl)"/>
<text x="60" y="80" font-family="{SANS}" font-size="14" font-weight="800" letter-spacing="4.5" fill="{EYEBROW}">UNOFFICIAL HOME ASSISTANT INTEGRATION</text>
<text x="56" y="146" font-family="{SANS}" font-size="62" font-weight="800" letter-spacing="-1.5" fill="{INK}">KidsAlert</text>
<text x="60" y="184" font-family="{SANS}" font-size="20" font-weight="500" fill="{SOFT}">Alerts about threats to children, online and off,</text>
<text x="60" y="210" font-family="{SANS}" font-size="20" font-weight="500" fill="{SOFT}">on your dashboard and your phone.</text>
<text x="60" y="256" font-family="{MONO}" font-size="14" font-weight="500" fill="{MUTED}" xml:space="preserve">{stats([("3", "entities"), ("1", "event"), ("2", "cards"), ("1", "blueprint")])}</text>
<g font-family="{SANS}">
{latest_card(630, 38, "h")}
{notification(890, 46, "h")}
{list_card(890, 140, "h")}
</g>"""
    return 1200, 300, body


def section(
    prefix: str, eyebrow: str, title: str, sub: list[str], decoration: str
) -> tuple[int, int, str]:
    body = f"""{defs(prefix)}
<rect width="1200" height="120" fill="url(#{prefix}-bg)"/>
<circle cx="980" cy="60" r="220" fill="url(#{prefix}-gl)"/>
<text x="48" y="40" font-family="{SANS}" font-size="12" font-weight="800" letter-spacing="3.5" fill="{EYEBROW}">{html.escape(eyebrow)}</text>
<text x="46" y="80" font-family="{SANS}" font-size="34" font-weight="800" letter-spacing="-0.8" fill="{INK}">{html.escape(title)}</text>
<text x="48" y="104" font-family="{MONO}" font-size="13" font-weight="500" fill="{MUTED}" xml:space="preserve">{sep(sub)}</text>
<g font-family="{SANS}">{decoration}</g>"""
    return 1200, 120, body


def tile(x: float, inner: str, stroke: str = "#fff", opacity: str = "0.08") -> str:
    return (
        f'<g transform="translate({x},28)"><rect width="64" height="64" rx="14" fill="{CARD}" '
        f'stroke="{stroke}" stroke-opacity="{opacity}"/>{inner}</g>'
    )


def cards_banner() -> tuple[int, int, str]:
    deco = "".join(
        [
            tile(
                840,
                f'<rect x="10" y="10" width="44" height="26" rx="6" fill="url(#c-img)"/>'
                f'<rect x="10" y="42" width="30" height="5" rx="2.5" fill="{INK}" fill-opacity=".8"/>'
                f'<rect x="10" y="51" width="20" height="4" rx="2" fill="{MUTED}"/>',
                RED,
                "0.6",
            ),
            tile(
                916,
                "".join(
                    f'<rect x="12" y="{14 + i * 14}" width="10" height="10" rx="3" fill="{c}"/>'
                    f'<rect x="27" y="{16 + i * 14}" width="{w}" height="5" rx="2.5" fill="#fff" fill-opacity=".7"/>'
                    for i, (c, w) in enumerate([(INDIGO, 24), ("#2f6f73", 18), (RED, 22)])
                ),
            ),
            tile(992, badge(8, 22, "DANGER", RED, 48).replace('font-size="11"', 'font-size="8"')),
            tile(1068, shield(16, 16, 32, GREEN)),
        ]
    )
    return section(
        "c",
        "DASHBOARD CARDS",
        "Two cards, built in",
        ["latest alert", "alert list", "full text and video", "light and dark", "EN / PL"],
        deco,
    )


def notifications_banner() -> tuple[int, int, str]:
    return section(
        "n",
        "NOTIFICATIONS",
        "Know the moment an alert goes out",
        ["event entity", "kidsalert_new_alert", "blueprint", "danger only"],
        notification(856, 21, "n", 300),
    )


def installation_banner() -> tuple[int, int, str]:
    deco = f"""<rect x="740" y="38" width="300" height="44" rx="12" fill="#fff" fill-opacity=".07" stroke="#fff" stroke-opacity=".12"/>
<text x="760" y="66" font-family="{MONO}" font-size="14" fill="#e9eaff">HACS › KidsAlert</text>
<rect x="1056" y="38" width="104" height="44" rx="22" fill="{RED}"/>
<text x="1108" y="65" text-anchor="middle" font-size="15" font-weight="800" fill="#fff">Download</text>"""
    return section(
        "i",
        "INSTALLATION",
        "Up and running in three steps",
        ["HACS", "restart", "add integration"],
        deco,
    )


def social() -> tuple[int, int, str]:
    body = f"""{defs("s", 0.2, 0.1, 1.25)}
<rect width="1280" height="640" fill="url(#s-bg)"/><circle cx="60" cy="0" r="420" fill="url(#s-gi)"/><circle cx="980" cy="330" r="460" fill="url(#s-gl)"/>
<text x="80" y="190" font-family="{SANS}" font-size="17" font-weight="800" letter-spacing="4" fill="{EYEBROW}">UNOFFICIAL HOME ASSISTANT INTEGRATION</text>
<text x="74" y="290" font-family="{SANS}" font-size="104" font-weight="800" letter-spacing="-3" fill="{INK}">KidsAlert</text>
<text x="80" y="350" font-family="{SANS}" font-size="28" font-weight="500" fill="{SOFT}">Alerts about threats to children,</text>
<text x="80" y="388" font-family="{SANS}" font-size="28" font-weight="500" fill="{SOFT}">on your dashboard and your phone.</text>
<text x="80" y="470" font-family="{MONO}" font-size="20" font-weight="500" fill="{MUTED}" xml:space="preserve">{stats([("3", "entities"), ("2", "cards"), ("1", "blueprint")])}</text>
<text x="80" y="560" font-family="{MONO}" font-size="18" font-weight="500" fill="{DIM}">github.com/MichalZaniewicz/ha-kidsalert</text>
<g font-family="{SANS}" transform="translate(740,100) scale(1.28)">
{latest_card(0, 0, "s")}
{notification(46, 246, "s", 290)}
</g>"""
    return 1280, 640, body


def brand_icon(size: int) -> str:
    """Red shield with an exclamation mark; readable on light and dark backgrounds."""
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" width="{size}" height="{size}">
<defs>
<linearGradient id="ic-fill" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#ff8270"/><stop offset="1" stop-color="#e2364a"/></linearGradient>
</defs>
<path d="M256 44 92 104v122c0 112 70 208 164 244 94-36 164-132 164-244V104Z" fill="url(#ic-fill)" stroke="url(#ic-fill)" stroke-width="36" stroke-linejoin="round"/>
<rect x="228" y="140" width="56" height="176" rx="28" fill="#fff"/>
<circle cx="256" cy="372" r="32" fill="#fff"/>
</svg>
"""


BANNERS = {
    "hero-banner.svg": hero,
    "cards-banner.svg": cards_banner,
    "notifications-banner.svg": notifications_banner,
    "installation-banner.svg": installation_banner,
    "social-preview.svg": social,
}


# ---------- fonts ----------


def used_text(svg_body: str) -> str:
    chunks = re.findall(r">([^<>]+)<", svg_body)
    return "".join(html.unescape(chunk) for chunk in chunks) + " ·…›!?"


def font_faces(fonts: Path, text: str) -> str:
    faces = []
    for family, filename, weight in FACES:
        font = TTFont(fonts / filename)
        font = instancer.instantiateVariableFont(font, {"wght": weight})
        options = subset.Options()
        options.flavor = "woff"
        options.name_IDs = []
        options.layout_features = ["kern", "liga"]
        subsetter = subset.Subsetter(options)
        subsetter.populate(text=text)
        subsetter.subset(font)
        buffer = io.BytesIO()
        font.flavor = "woff"
        font.save(buffer)
        data = base64.b64encode(buffer.getvalue()).decode()
        faces.append(
            f"@font-face{{font-family:{family};font-weight:{weight};"
            f"src:url(data:font/woff;base64,{data}) format('woff');}}"
        )
    return "".join(faces)


def build(fonts: Path, chrome: str | None) -> None:
    for name, factory in BANNERS.items():
        width, height, body = factory()
        svg = (
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
            f'width="{width}" height="{height}">\n'
            f"<style>{font_faces(fonts, used_text(body))}</style>\n{body}\n</svg>\n"
        )
        (DOCS / name).write_text(svg, encoding="utf-8")
        print(f"{name}: {len(svg) // 1024} KiB")

    if chrome:
        with tempfile.TemporaryDirectory() as profile:
            subprocess.run(
                [
                    chrome,
                    "--headless=new",
                    "--disable-gpu",
                    "--hide-scrollbars",
                    f"--user-data-dir={profile}",
                    "--window-size=1280,640",
                    f"--screenshot={DOCS / 'social-preview.png'}",
                    (DOCS / "social-preview.svg").as_uri(),
                ],
                check=True,
                capture_output=True,
            )
        print("social-preview.png")

        for size, name in ((256, "icon.png"), (512, "icon@2x.png")):
            with tempfile.TemporaryDirectory() as tmp:
                source = Path(tmp) / "icon.svg"
                source.write_text(brand_icon(size), encoding="utf-8")
                subprocess.run(
                    [
                        chrome,
                        "--headless=new",
                        "--disable-gpu",
                        "--hide-scrollbars",
                        f"--user-data-dir={Path(tmp) / 'profile'}",
                        f"--window-size={size},{size}",
                        "--default-background-color=00000000",
                        f"--screenshot={BRAND / name}",
                        source.as_uri(),
                    ],
                    check=True,
                    capture_output=True,
                )
            print(f"brand/{name}")
    (DOCS / "brand-icon.svg").write_text(brand_icon(512), encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--fonts", type=Path, required=True)
    parser.add_argument("--chrome")
    args = parser.parse_args()
    build(args.fonts, args.chrome)
