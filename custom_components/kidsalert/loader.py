"""Dashboard resource that loads the cards when the page opened during a restart.

Home Assistant serves the frontend before custom integrations are set up, so a
page opened while it starts misses the extra module URL and the static path of
the cards, and the cards show "Configuration error" until a full reload. The
Lovelace resource list is available that early, so a small loader kept there as
a data URL retries the card module until the integration serves it. The
frontend rebuilds a broken card as soon as its element gets defined.
"""

from __future__ import annotations

import json
from urllib.parse import quote

from homeassistant.components.lovelace.resources import ResourceStorageCollection
from homeassistant.core import HomeAssistant

LOADER_MARKER = "/* kidsalert-loader */"
LOADER_PREFIX = "data:text/javascript," + quote(LOADER_MARKER, safe="")

# The first attempt uses the exact URL of the extra module, so a page that already
# has the cards reuses that module. A failed import stays failed for its URL, so
# retries add a query parameter. 300 attempts, 3 s apart, cover a slow startup.
LOADER_CODE = """{marker}
const url = new URL({card_url}, location.origin).href;
const load = async (attempt) => {{
  try {{
    await import(attempt ? `${{url}}&retry=${{attempt}}` : url);
  }} catch {{
    if (attempt < 300) setTimeout(() => load(attempt + 1), 3000);
  }}
}};
load(0);
"""


def loader_url(card_url: str) -> str:
    """Return the data URL of the loader for the given card module URL."""
    code = LOADER_CODE.format(marker=LOADER_MARKER, card_url=json.dumps(card_url))
    return "data:text/javascript," + quote(code, safe="")


def _storage_resources(hass: HomeAssistant) -> ResourceStorageCollection | None:
    """Return the resource collection, or None when resources live in YAML."""
    resources = getattr(hass.data.get("lovelace"), "resources", None)
    return resources if isinstance(resources, ResourceStorageCollection) else None


async def async_register_loader(hass: HomeAssistant, card_url: str) -> None:
    """Add the loader resource, or update it after the integration was updated."""
    if (resources := _storage_resources(hass)) is None:
        return
    await resources.async_get_info()  # loads the collection from storage
    url = loader_url(card_url)
    ours = [item for item in resources.async_items() if item["url"].startswith(LOADER_PREFIX)]
    if not ours:
        await resources.async_create_item({"res_type": "module", "url": url})
        return
    first, *duplicates = ours
    if first["url"] != url:
        await resources.async_update_item(first["id"], {"res_type": "module", "url": url})
    for item in duplicates:
        await resources.async_delete_item(item["id"])


async def async_remove_loader(hass: HomeAssistant) -> None:
    """Remove the loader resource when the integration is removed."""
    if (resources := _storage_resources(hass)) is None:
        return
    await resources.async_get_info()
    for item in resources.async_items():
        if item["url"].startswith(LOADER_PREFIX):
            await resources.async_delete_item(item["id"])
