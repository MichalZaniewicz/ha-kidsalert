/* KidsAlert dashboard cards, served and registered by the kidsalert integration. */

const VERSION = "0.1.0";
const DOMAIN = "kidsalert";

const STRINGS = {
  pl: {
    latest_name: "KidsAlert – ostatni alert",
    latest_desc: "Najnowszy alert KidsAlert z obrazkiem i pełną treścią po kliknięciu.",
    list_name: "KidsAlert – lista alertów",
    list_desc: "Ostatnie alerty KidsAlert z miniaturami.",
    danger: "Zagrożenie",
    sensitive: "Treść wrażliwa",
    reveal: "Kliknij, aby pokazać",
    loading: "Ładowanie…",
    empty: "Brak alertów",
    no_entry: "Nie znaleziono integracji KidsAlert. Dodaj ją w Ustawienia → Urządzenia i usługi.",
    error: "Nie udało się pobrać alertów",
    close: "Zamknij",
    entity: "Encja (KidsAlert – ostatni alert)",
    title: "Tytuł karty",
    show_image: "Pokaż obrazek",
    count: "Liczba alertów",
    only_danger: "Tylko zagrożenia",
    show_thumbnails: "Pokaż miniatury",
    blur_sensitive: "Rozmyj wrażliwe obrazy",
  },
  en: {
    latest_name: "KidsAlert – latest alert",
    latest_desc: "Newest KidsAlert alert with its image; tap for the full text.",
    list_name: "KidsAlert – alert list",
    list_desc: "Recent KidsAlert alerts with thumbnails.",
    danger: "Danger",
    sensitive: "Sensitive content",
    reveal: "Tap to show",
    loading: "Loading…",
    empty: "No alerts",
    no_entry: "KidsAlert integration not found. Add it under Settings → Devices & services.",
    error: "Could not load alerts",
    close: "Close",
    entity: "Entity (KidsAlert latest alert)",
    title: "Card title",
    show_image: "Show image",
    count: "Number of alerts",
    only_danger: "Danger alerts only",
    show_thumbnails: "Show thumbnails",
    blur_sensitive: "Blur sensitive images",
  },
};

const uiLanguage = (hass) =>
  (hass?.locale?.language || hass?.language || document.documentElement.lang || navigator.language || "en")
    .toLowerCase()
    .startsWith("pl")
    ? "pl"
    : "en";

const tr = (hass, key) => STRINGS[uiLanguage(hass)][key] ?? STRINGS.en[key] ?? key;

const esc = (value) =>
  String(value ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);

const safeUrl = (value, protocols = ["https:", "http:"]) => {
  if (!value) return null;
  try {
    const url = new URL(value, "https://kidsalert.pl/");
    return protocols.includes(url.protocol) ? url.href : null;
  } catch (_err) {
    return null;
  }
};

/* ---------- HTML sanitizer for alert content (allowlist, rebuilt from scratch) ---------- */

const ALLOWED_TAGS = new Set([
  "P", "BR", "HR", "STRONG", "B", "EM", "I", "U", "S", "SMALL", "SUB", "SUP", "UL", "OL", "LI",
  "A", "H1", "H2", "H3", "H4", "H5", "H6", "BLOCKQUOTE", "SPAN", "DIV", "IMG", "FIGURE", "FIGCAPTION",
]);
const DROPPED_TAGS = new Set([
  "SCRIPT", "STYLE", "IFRAME", "FRAME", "FRAMESET", "OBJECT", "EMBED", "TEMPLATE", "SVG", "MATH",
  "FORM", "INPUT", "BUTTON", "TEXTAREA", "SELECT", "LINK", "META", "NOSCRIPT", "CANVAS", "AUDIO", "VIDEO",
]);
const URL_RE = /https?:\/\/[^\s<>"']+[^\s<>"'.,;:!?)\]]/g;

function appendLinkified(text, target) {
  let last = 0;
  for (const match of text.matchAll(URL_RE)) {
    const href = safeUrl(match[0]);
    if (!href) continue;
    target.appendChild(document.createTextNode(text.slice(last, match.index)));
    const a = document.createElement("a");
    a.href = href;
    a.target = "_blank";
    a.rel = "noopener noreferrer";
    a.textContent = match[0];
    target.appendChild(a);
    last = match.index + match[0].length;
  }
  target.appendChild(document.createTextNode(text.slice(last)));
}

function copySafe(source, target, inLink) {
  for (const node of source.childNodes) {
    if (node.nodeType === Node.TEXT_NODE) {
      if (inLink) target.appendChild(document.createTextNode(node.textContent));
      else appendLinkified(node.textContent, target);
      continue;
    }
    if (node.nodeType !== Node.ELEMENT_NODE) continue;
    const tag = node.tagName;
    if (DROPPED_TAGS.has(tag)) continue;
    if (!ALLOWED_TAGS.has(tag)) {
      copySafe(node, target, inLink);
      continue;
    }
    const el = document.createElement(tag.toLowerCase());
    if (tag === "A") {
      const href = safeUrl(node.getAttribute("href"), ["https:", "http:", "mailto:", "tel:"]);
      if (href) {
        el.href = href;
        el.target = "_blank";
        el.rel = "noopener noreferrer";
      }
    } else if (tag === "IMG") {
      const src = safeUrl(node.getAttribute("src"));
      if (!src) continue;
      el.src = src;
      el.alt = node.getAttribute("alt") || "";
      el.loading = "lazy";
      el.referrerPolicy = "no-referrer";
    }
    copySafe(node, el, inLink || tag === "A");
    target.appendChild(el);
  }
}

function sanitizeHtml(html) {
  // DOMParser builds an inert document: no scripts run and no resources load.
  const parsed = new DOMParser().parseFromString(html || "", "text/html");
  const fragment = document.createDocumentFragment();
  copySafe(parsed.body, fragment, false);
  return fragment;
}

/* ---------- Dates ---------- */

function formatDate(hass, iso) {
  if (!iso) return "";
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return "";
  const lang = hass?.locale?.language || uiLanguage(hass);
  try {
    return new Intl.DateTimeFormat(lang, {
      dateStyle: "medium",
      timeStyle: "short",
      timeZone: hass?.config?.time_zone,
    }).format(date);
  } catch (_err) {
    return date.toLocaleString();
  }
}

function relativeDate(hass, iso) {
  const date = new Date(iso);
  if (!iso || Number.isNaN(date.getTime())) return "";
  const seconds = (date.getTime() - Date.now()) / 1000;
  const units = [
    ["year", 31536000], ["month", 2592000], ["week", 604800], ["day", 86400], ["hour", 3600], ["minute", 60],
  ];
  const rtf = new Intl.RelativeTimeFormat(hass?.locale?.language || uiLanguage(hass), { numeric: "auto" });
  for (const [unit, size] of units) {
    if (Math.abs(seconds) >= size) return rtf.format(Math.round(seconds / size), unit);
  }
  return rtf.format(0, "minute");
}

/* ---------- Data access ---------- */

function findKidsAlertSensor(hass) {
  const entities = hass?.entities || {};
  return (
    Object.keys(entities).find((id) => id.startsWith("sensor.") && entities[id].platform === DOMAIN) || null
  );
}

// Alerts can be edited after publication, so cached details expire.
const DETAIL_TTL_MS = 10 * 60 * 1000;
const detailCache = new Map();
// Cards bound to the same sensor share one list request per sensor update.
const listRequests = new Map();

function cachedCall(cache, key, call) {
  const hit = cache.get(key);
  if (hit && (hit.expires === undefined || hit.expires > Date.now())) return hit.promise;
  const promise = call().catch((err) => {
    cache.delete(key);
    throw err;
  });
  cache.set(key, { promise, expires: cache === detailCache ? Date.now() + DETAIL_TTL_MS : undefined });
  return promise;
}

function fetchDetail(hass, entityId, alertId) {
  return cachedCall(detailCache, `${entityId || ""}:${alertId}`, () =>
    hass.callWS({ type: "kidsalert/alert", alert_id: alertId, ...(entityId ? { entity_id: entityId } : {}) }),
  );
}

function fetchAlerts(hass, entityId, revision) {
  const current = listRequests.get(entityId);
  if (current?.revision === revision) return current.promise;
  const promise = hass.callWS({ type: "kidsalert/alerts", entity_id: entityId });
  listRequests.set(entityId, { revision, promise });
  promise.catch(() => listRequests.get(entityId)?.promise === promise && listRequests.delete(entityId));
  return promise;
}

/* ---------- Shared styles ---------- */

const BASE_STYLE = `
  :host { display: block; }
  ha-card { overflow: hidden; }
  .header { padding: 16px 16px 4px; font-size: var(--ha-card-header-font-size, 20px); font-weight: 500; color: var(--ha-card-header-color, var(--primary-text-color)); }
  .state { padding: 16px; color: var(--secondary-text-color); }
  .state.error { color: var(--error-color, #db4437); }
  .badge { display: inline-flex; align-items: center; gap: 4px; padding: 2px 8px; border-radius: 999px; font-size: 12px; font-weight: 600; text-transform: uppercase; letter-spacing: .03em; background: var(--error-color, #db4437); color: #fff; }
  .badge.sensitive { background: var(--warning-color, #ff9800); }
  .meta { color: var(--secondary-text-color); font-size: 13px; }
  .clickable { cursor: pointer; outline: none; }
  .clickable:focus-visible { box-shadow: inset 0 0 0 2px var(--primary-color); }
  .blur { filter: blur(18px); transform: scale(1.1); }
`;

/* ---------- Detail dialog ---------- */

class KidsAlertDialog extends HTMLElement {
  static open(hass, entityId, summary) {
    const dialog = document.createElement("kidsalert-dialog");
    dialog.hass = hass;
    dialog.entityId = entityId;
    dialog.summary = summary;
    document.body.appendChild(dialog);
  }

  connectedCallback() {
    this.attachShadow({ mode: "open" });
    this._onKey = (ev) => ev.key === "Escape" && this.close();
    document.addEventListener("keydown", this._onKey);
    this._render(this.summary, true);
    fetchDetail(this.hass, this.entityId, this.summary.id).then(
      (detail) => this.isConnected && this._render(detail, false),
      () => this.isConnected && this._render(this.summary, false, true),
    );
  }

  disconnectedCallback() {
    document.removeEventListener("keydown", this._onKey);
  }

  close() {
    this.remove();
  }

  _render(alert, loading, failed = false) {
    const hass = this.hass;
    const image = safeUrl(alert.image);
    const video = safeUrl(alert.video);
    const hidden = alert.is_sensitive && !this._revealed;
    let media = "";
    if (video) {
      media = `<video class="media" controls preload="metadata" src="${esc(video)}" ${image ? `poster="${esc(image)}"` : ""}></video>`;
    } else if (image) {
      media = `<div class="media-wrap ${hidden ? "clickable" : ""}" ${hidden ? 'role="button" tabindex="0"' : ""}>
          <img class="media ${hidden ? "blur" : ""}" src="${esc(image)}" alt="" referrerpolicy="no-referrer">
          ${hidden ? `<div class="veil">${esc(tr(hass, "sensitive"))}<br><small>${esc(tr(hass, "reveal"))}</small></div>` : ""}
        </div>`;
    }
    this.shadowRoot.innerHTML = `
      <style>
        ${BASE_STYLE}
        .backdrop { position: fixed; inset: 0; z-index: 1000; background: rgba(0,0,0,.6); display: flex; align-items: center; justify-content: center; padding: 16px; box-sizing: border-box; }
        .panel { position: relative; width: min(680px, 100%); max-height: calc(100vh - 32px); overflow-y: auto; border-radius: var(--ha-card-border-radius, 12px); background: var(--card-background-color, var(--ha-card-background, #fff)); color: var(--primary-text-color); box-shadow: 0 8px 32px rgba(0,0,0,.4); }
        .panel.danger { border-top: 6px solid var(--error-color, #db4437); }
        .close { position: absolute; top: 8px; right: 8px; z-index: 2; width: 40px; height: 40px; border: none; border-radius: 50%; background: rgba(0,0,0,.45); color: #fff; font-size: 22px; line-height: 40px; cursor: pointer; }
        .media-wrap { position: relative; overflow: hidden; }
        .media { display: block; width: 100%; max-height: 60vh; object-fit: contain; background: #000; }
        .veil { position: absolute; inset: 0; display: flex; flex-direction: column; align-items: center; justify-content: center; color: #fff; font-weight: 600; text-align: center; background: rgba(0,0,0,.35); }
        .body { padding: 16px 20px 24px; }
        .badges { display: flex; gap: 6px; margin-bottom: 8px; }
        h2 { margin: 0 0 4px; font-size: 22px; line-height: 1.3; }
        .content { margin-top: 16px; line-height: 1.55; font-size: 15px; overflow-wrap: anywhere; }
        .content img { max-width: 100%; height: auto; }
        .content a { color: var(--primary-color); }
      </style>
      <div class="backdrop">
        <div class="panel ${alert.is_danger ? "danger" : ""}" role="dialog" aria-modal="true" aria-label="${esc(alert.title)}">
          <button class="close" aria-label="${esc(tr(hass, "close"))}">×</button>
          ${media}
          <div class="body">
            ${alert.is_danger || alert.is_sensitive ? `<div class="badges">
              ${alert.is_danger ? `<span class="badge">${esc(tr(hass, "danger"))}</span>` : ""}
              ${alert.is_sensitive ? `<span class="badge sensitive">${esc(tr(hass, "sensitive"))}</span>` : ""}
            </div>` : ""}
            <h2>${esc(alert.title)}</h2>
            <div class="meta">${esc(formatDate(hass, alert.sent_at))}</div>
            <div class="content">${loading ? `<p class="meta">${esc(tr(hass, "loading"))}</p>` : ""}${failed ? `<p class="state error">${esc(tr(hass, "error"))}</p>` : ""}</div>
          </div>
        </div>
      </div>`;
    if (!loading && !failed) this.shadowRoot.querySelector(".content").appendChild(sanitizeHtml(alert.content));
    this._alert = alert;
    const root = this.shadowRoot;
    root.querySelector(".backdrop").addEventListener("click", (ev) => ev.target === ev.currentTarget && this.close());
    root.querySelector(".close").addEventListener("click", () => this.close());
    const veil = root.querySelector(".media-wrap.clickable");
    if (veil) {
      const reveal = () => {
        this._revealed = true;
        this._render(this._alert, loading, failed);
      };
      veil.addEventListener("click", reveal);
      veil.addEventListener("keydown", (ev) => (ev.key === "Enter" || ev.key === " ") && reveal());
    }
    root.querySelector(".close").focus({ preventScroll: true });
  }
}

/* ---------- Card base ---------- */

class KidsAlertBaseCard extends HTMLElement {
  setConfig(config) {
    this._config = { ...this.constructor.defaults, ...config };
    this._dataKey = undefined;
    this._render();
  }

  set hass(hass) {
    this._hass = hass;
    const entityId = this._entityId();
    const state = entityId ? hass.states[entityId] : undefined;
    // Refetch the list only when the sensor reports a different newest alert.
    const key = `${entityId}|${state?.attributes?.alert_id}|${state?.last_updated}`;
    if (key !== this._dataKey) {
      this._dataKey = key;
      this._load();
    } else if (!this._renderedAt || Date.now() - this._renderedAt > 60000) {
      // Keeps relative dates ("2 hours ago") current without re-rendering on every state change.
      this._render();
    }
  }

  _entityId() {
    return this._config?.entity || findKidsAlertSensor(this._hass);
  }

  async _load() {
    const hass = this._hass;
    if (!hass || !this._config) return;
    const entityId = this._entityId();
    if (!entityId) {
      this._status = "no_entry";
      this._render();
      return;
    }
    if (!this._alerts) {
      this._status = "loading";
      this._render();
    }
    const key = this._dataKey;
    let alerts;
    let status;
    try {
      alerts = (await fetchAlerts(hass, entityId, key)).alerts || [];
      status = "ok";
    } catch (err) {
      status = err?.code === "not_found" ? "no_entry" : "error";
    }
    // A newer sensor update started another load; let that one win.
    if (key !== this._dataKey) return;
    if (alerts) this._alerts = alerts;
    this._status = status;
    this._render();
  }

  _open(alert) {
    KidsAlertDialog.open(this._hass, this._entityId(), alert);
  }

  _bindOpen(root) {
    root.querySelectorAll("[data-alert]").forEach((el) => {
      const alert = this._alerts.find((a) => String(a.id) === el.dataset.alert);
      if (!alert) return;
      el.addEventListener("click", () => this._open(alert));
      el.addEventListener("keydown", (ev) => {
        if (ev.key === "Enter" || ev.key === " ") {
          ev.preventDefault();
          this._open(alert);
        }
      });
    });
  }

  _statusHtml() {
    if (this._status === "ok") return "";
    const key = this._status || "loading";
    return `<div class="state ${key === "error" ? "error" : ""}">${esc(tr(this._hass, key))}</div>`;
  }

  _shell(style, body) {
    if (!this.shadowRoot) this.attachShadow({ mode: "open" });
    const title = this._config.title;
    this.shadowRoot.innerHTML = `<style>${BASE_STYLE}${style}</style>
      <ha-card>${title ? `<div class="header">${esc(title)}</div>` : ""}${body}</ha-card>`;
    this._bindOpen(this.shadowRoot);
    this._renderedAt = Date.now();
  }

  getGridOptions() {
    return { columns: 12, min_columns: 4 };
  }
}

/* ---------- Latest alert card ---------- */

class KidsAlertCard extends KidsAlertBaseCard {
  static defaults = { show_image: true, blur_sensitive: true };

  static getConfigElement() {
    return document.createElement("kidsalert-card-editor");
  }

  static getStubConfig(hass) {
    return { entity: findKidsAlertSensor(hass) || "" };
  }

  getCardSize() {
    return this._config?.show_image ? 6 : 2;
  }

  _render() {
    if (!this._config) return;
    const alert = this._status === "ok" ? this._alerts?.[0] : undefined;
    if (!alert) {
      this._shell("", this._status === "ok" ? `<div class="state">${esc(tr(this._hass, "empty"))}</div>` : this._statusHtml());
      return;
    }
    const hass = this._hass;
    const image = this._config.show_image ? safeUrl(alert.image) : null;
    const blur = alert.is_sensitive && this._config.blur_sensitive;
    this._shell(
      `
      .latest { display: block; }
      .latest.danger { border-left: 6px solid var(--error-color, #db4437); }
      .image { position: relative; overflow: hidden; aspect-ratio: 16 / 9; background: var(--secondary-background-color, #eee); }
      .image img { width: 100%; height: 100%; object-fit: cover; display: block; }
      .veil { position: absolute; inset: 0; display: flex; align-items: center; justify-content: center; color: #fff; font-weight: 600; background: rgba(0,0,0,.3); }
      .body { padding: 12px 16px 16px; }
      .badges { display: flex; gap: 6px; margin-bottom: 6px; }
      .title { font-size: 18px; font-weight: 500; line-height: 1.3; margin-bottom: 4px; color: var(--primary-text-color); }
      `,
      `<div class="latest clickable ${alert.is_danger ? "danger" : ""}" data-alert="${alert.id}" role="button" tabindex="0">
        ${image ? `<div class="image"><img src="${esc(image)}" alt="" loading="lazy" referrerpolicy="no-referrer" class="${blur ? "blur" : ""}">
          ${blur ? `<div class="veil">${esc(tr(hass, "sensitive"))}</div>` : ""}</div>` : ""}
        <div class="body">
          ${alert.is_danger ? `<div class="badges"><span class="badge">${esc(tr(hass, "danger"))}</span></div>` : ""}
          <div class="title">${esc(alert.title)}</div>
          <div class="meta">${esc(formatDate(hass, alert.sent_at))} · ${esc(relativeDate(hass, alert.sent_at))}</div>
        </div>
      </div>`,
    );
  }
}

/* ---------- Alert list card ---------- */

class KidsAlertListCard extends KidsAlertBaseCard {
  static defaults = { title: "KidsAlert", count: 5, only_danger: false, show_thumbnails: true, blur_sensitive: true };

  static getConfigElement() {
    return document.createElement("kidsalert-list-card-editor");
  }

  static getStubConfig(hass) {
    return { entity: findKidsAlertSensor(hass) || "", title: "KidsAlert", count: 5 };
  }

  getCardSize() {
    return 1 + Math.ceil((this._config?.count || 5) * 1.2);
  }

  _render() {
    if (!this._config) return;
    if (this._status !== "ok") {
      this._shell("", this._statusHtml());
      return;
    }
    const hass = this._hass;
    const count = Math.max(1, Number(this._config.count) || 5);
    const alerts = (this._alerts || []).filter((a) => !this._config.only_danger || a.is_danger).slice(0, count);
    const rows = alerts
      .map((alert) => {
        const thumb = this._config.show_thumbnails ? safeUrl(alert.thumbnail || alert.image) : null;
        const blur = alert.is_sensitive && this._config.blur_sensitive;
        return `<div class="row clickable ${alert.is_danger ? "danger" : ""}" data-alert="${alert.id}" role="button" tabindex="0">
          ${thumb ? `<div class="thumb"><img src="${esc(thumb)}" alt="" loading="lazy" referrerpolicy="no-referrer" class="${blur ? "blur" : ""}"></div>` : ""}
          <div class="text">
            <div class="title">${esc(alert.title)}</div>
            <div class="meta">${alert.is_danger ? `<span class="badge">${esc(tr(hass, "danger"))}</span> ` : ""}${esc(relativeDate(hass, alert.sent_at))}</div>
          </div>
        </div>`;
      })
      .join("");
    this._shell(
      `
      .list { padding: 4px 0 8px; }
      .row { display: flex; gap: 12px; align-items: center; padding: 8px 16px; border-left: 4px solid transparent; }
      .row:hover { background: var(--secondary-background-color, rgba(0,0,0,.04)); }
      .row.danger { border-left-color: var(--error-color, #db4437); }
      .thumb { flex: 0 0 56px; width: 56px; height: 56px; border-radius: 8px; overflow: hidden; background: var(--secondary-background-color, #eee); }
      .thumb img { width: 100%; height: 100%; object-fit: cover; display: block; }
      .text { min-width: 0; flex: 1; }
      .title { color: var(--primary-text-color); font-weight: 500; line-height: 1.3; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
      .meta { margin-top: 2px; display: flex; align-items: center; gap: 6px; }
      .meta .badge { font-size: 10px; padding: 1px 6px; }
      `,
      rows ? `<div class="list">${rows}</div>` : `<div class="state">${esc(tr(hass, "empty"))}</div>`,
    );
  }
}

/* ---------- Visual editors ---------- */

class KidsAlertEditorBase extends HTMLElement {
  setConfig(config) {
    this._config = config;
    this._update();
  }

  set hass(hass) {
    this._hass = hass;
    this._update();
  }

  _update() {
    if (!this._hass || !this._config) return;
    if (!this._form) {
      this._form = document.createElement("ha-form");
      this._form.computeLabel = (schema) => tr(this._hass, schema.name);
      this._form.addEventListener("value-changed", (ev) => {
        this.dispatchEvent(new CustomEvent("config-changed", { detail: { config: ev.detail.value }, bubbles: true, composed: true }));
      });
      this.appendChild(this._form);
    }
    this._form.hass = this._hass;
    this._form.schema = this.constructor.schema;
    this._form.data = { ...this.constructor.defaults, ...this._config };
  }
}

const ENTITY_FIELD = { name: "entity", selector: { entity: { filter: { integration: DOMAIN, domain: "sensor" } } } };

class KidsAlertCardEditor extends KidsAlertEditorBase {
  static defaults = KidsAlertCard.defaults;
  static schema = [
    ENTITY_FIELD,
    { name: "title", selector: { text: {} } },
    { name: "show_image", selector: { boolean: {} } },
    { name: "blur_sensitive", selector: { boolean: {} } },
  ];
}

class KidsAlertListCardEditor extends KidsAlertEditorBase {
  static defaults = KidsAlertListCard.defaults;
  static schema = [
    ENTITY_FIELD,
    { name: "title", selector: { text: {} } },
    { name: "count", selector: { number: { min: 1, max: 30, mode: "box" } } },
    { name: "only_danger", selector: { boolean: {} } },
    { name: "show_thumbnails", selector: { boolean: {} } },
    { name: "blur_sensitive", selector: { boolean: {} } },
  ];
}

/* ---------- Registration ---------- */

const define = (name, cls) => customElements.get(name) || customElements.define(name, cls);
define("kidsalert-dialog", KidsAlertDialog);
define("kidsalert-card", KidsAlertCard);
define("kidsalert-list-card", KidsAlertListCard);
define("kidsalert-card-editor", KidsAlertCardEditor);
define("kidsalert-list-card-editor", KidsAlertListCardEditor);

window.customCards = window.customCards || [];
for (const [type, key] of [["kidsalert-card", "latest"], ["kidsalert-list-card", "list"]]) {
  if (!window.customCards.some((card) => card.type === type)) {
    window.customCards.push({
      type,
      name: tr(null, `${key}_name`),
      description: tr(null, `${key}_desc`),
      preview: true,
    });
  }
}

console.info(`%c KIDSALERT-CARD %c ${VERSION} `, "color:#fff;background:#db4437;font-weight:700", "color:#db4437;background:#fff");
