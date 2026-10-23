// Stadtmonitor – Karte vollflächig, darüber Liste, Zeitleiste und Detail (Prozesslinie mit Evidenzstatus).
// Übernommen aus der RIS-Karte Bonn (github.com/daimpad/allris-test, MIT) und auf Einladungen (PDF) umgestellt.
// Stadtspezifisches steht in stadt.json (config/stadt.json), die Daten in data/export/vorgaenge.json.
(function () {
  "use strict";
  const CONFIG_URL = "stadt.json";
  const DATA_URL = "data/export/vorgaenge.json";
  const FLAECHEN_URL = "data/export/flaechen.json";  // Ortsbezirke als Flächen (optional, ab Phase 3)
  // Geltungsbereiche der Bauleitplanung: nur als Kartenebene, Nutzung nur nicht kommerziell (siehe stadt.json)
  const PLAENE_URL = "data/export/karte/bauleitplanung.json";
  const DEFAULT_AREA = "stadt:alle";
  const RANK = { hoch: 3, mittel: 2, niedrig: 1 };
  const LIST_STEP = 200;
  const MOBILE = matchMedia("(max-width: 900px)");
  const NARROW = matchMedia("(max-width: 1279px)");
  const REDUCED = matchMedia("(prefers-reduced-motion: reduce)").matches;
  const CONF = { hoch: "Ort gesichert", mittel: "Ort erschlossen", niedrig: "Ort unsicher" };
  // Methoden der Verortung (Stufe A: Gremium, B: Regeln, C: Sprachmodell); Schlüssel wie pipeline/verortung.py
  const METHOD = {
    gremium_ortsbeirat: "Ortsbeirat des Ortsteils (Ortsbezug des Gremiums, nicht zwingend des Gegenstands)",
    gremium_stadtteilbeirat: "Stadtteilbeirat des Ortsteils (Ortsbezug des Gremiums, nicht zwingend des Gegenstands)",
    ortsteil_name: "Ortsteilname im Titel", strasse: "Straßenname im Titel", "strasse+ortsteil": "Straßen- und Ortsteilname im Titel",
    strasse_mehrdeutig: "Straßenname im Titel, mehrere Lagen", gemarkung: "Gemarkung im Titel",
    flurstueck: "Flurstücksangabe im Titel, Lage laut Liegenschaftskataster", bebauungsplan: "Bebauungsplan im Titel, Geltungsbereich der Stadt",
    objekt_name: "Name eines Gebäudes oder einer Anlage im Titel",
    flaechennutzungsplan: "Änderung des Flächennutzungsplans im Titel, Geltungsbereich der Stadt",
    llm: "Mit einem Sprachmodell aus dem Titel erkannt und mit dem Straßen- und Ortsverzeichnis abgeglichen",
  };
  const STATUS = { belegt: "belegt", abgeleitet: "abgeleitet", "nicht_öffentlich": "nicht öffentlich", unklar: "unklar", soll: "soll" };
  const STATUS_TEXT = {
    belegt: "steht so in der Einladung (amtliche Bekanntmachung)",
    abgeleitet: "vom Stadtmonitor erschlossen, etwa über die Vorlagennummer",
    "nicht_öffentlich": "nichtöffentliche Beratung, Inhalt nicht einsehbar",
    unklar: "nicht veröffentlicht oder nicht feststellbar",
    soll: "nach Regelwerk vorgesehen, nicht belegt",
  };
  const RESULT_GAP = "Ergebnis nicht veröffentlicht. Die Einladungen nennen nur die Tagesordnung; Beschlüsse und Niederschriften stehen, soweit veröffentlicht, im Bürgerinformationssystem der Stadt. Der Stadtmonitor leitet keine Ergebnisse ab.";
  const LIMITS = `<details class="acc"><summary>Was diese Darstellung nicht zeigen kann</summary><ul>
    <li>Beschlussergebnisse: Sie sind in den Bekanntmachungen nicht veröffentlicht.</li>
    <li>Vorlagentexte und Niederschriften.</li>
    <li>Nichtöffentliche Beratungen und Sitzungen vor dem Beginn des Datenbestands.</li>
    <li>Verwaltungsinterne Abläufe und den Vollzug von Beschlüssen.</li></ul>
    <p class="hint">Fehlende Angaben sind als Lücke gekennzeichnet, nicht ergänzt.</p></details>`;

  const $ = (s) => document.querySelector(s);
  const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  // nur http(s)-Adressen aus den Daten werden zu Links
  const safeUrl = (u) => (/^https?:\/\//i.test(String(u || "")) ? esc(u) : null);
  const ISO_DAY = /^\d{4}-\d{2}-\d{2}$/;
  const fmtDate = (iso) => iso ? new Date(iso.length === 10 ? iso + "T12:00:00Z" : iso)
    .toLocaleDateString("de-DE", { timeZone: "Europe/Berlin", day: "2-digit", month: "2-digit", year: "numeric" }) : "";
  const fmtDay = (iso) => new Date(iso + "T12:00:00Z").toLocaleDateString("de-DE", { weekday: "short", day: "2-digit", month: "2-digit", year: "numeric", timeZone: "Europe/Berlin" });
  const debounce = (fn, ms) => { let h; return (...a) => { clearTimeout(h); h = setTimeout(() => fn(...a), ms); }; };
  const de = (n) => Number(n || 0).toLocaleString("de-DE");
  const get = (obj, path) => path.split(".").reduce((o, k) => (o == null ? o : o[k]), obj);

  let cfg = null, data = null, flaechen = null, zeit = null, all = [], papers = [], area = null, selected = null, dataStand = null;
  let planData = null, planLayer = null, planOn = false, planShown = null;
  let map, cluster, outline, navLayer = null, markers = new Map(), tl = null, range = null, shown = LIST_STEP, legendEl = null;

  // --- Konfiguration in die Seite einsetzen ----------------------------------------------------------
  function applyConfig() {
    document.querySelectorAll("[data-cfg]").forEach((el) => { const v = get(cfg, el.dataset.cfg); if (v != null) el.textContent = v; });
    document.querySelectorAll("[data-cfg-href]").forEach((el) => { const v = safeUrl(get(cfg, el.dataset.cfgHref)); if (v) el.setAttribute("href", get(cfg, el.dataset.cfgHref)); });
    document.title = `${cfg.stadt.titel} – Sitzungsinformationen auf Karte und Zeitleiste`;
    $("#cta-report").href = `${cfg.projekt.repo}/issues/new/choose`;
  }
  const ortsteile = () => cfg.ortsteile;
  const gremiumShort = (name) => (cfg.gremien.find((g) => g.name === name) || {}).kurz || name;

  // --- Flächen ein- und ausklappen ---------------------------------------------------------------
  const SHEETS = ["panel-list", "panel-detail", "panel-auswertung", "panel-termine", "timeline-wrap"];
  const OVERLAYS = ["panel-auswertung", "panel-termine"];
  const toggleFor = (id) => document.querySelector(`.toggle[data-panel="${id}"]`);
  function setPanel(id, open) {
    const el = document.getElementById(id);
    el.hidden = !open;
    document.querySelectorAll(`.toggle[data-panel="${id}"]`).forEach((b) => b.setAttribute("aria-pressed", String(open)));
    if (id === "panel-list") { document.body.classList.toggle("list-open", open); document.body.classList.toggle("list-closed", !open); }
    if (id === "panel-detail") { document.body.classList.toggle("detail-open", open); document.body.classList.toggle("detail-closed", !open); }
    if (!open) return;
    closeMega();
    // schmale Bildschirme: nur eine Fläche; mittlere Breiten: Liste oder Vorgang, damit die Zeitleiste Platz hat;
    // Kennzahlen und Termine liegen mittig übereinander, daher immer nur eines davon
    const others = MOBILE.matches ? SHEETS : OVERLAYS.includes(id) ? OVERLAYS
      : NARROW.matches && (id === "panel-list" || id === "panel-detail") ? ["panel-list", "panel-detail"] : [];
    for (const other of others) if (other !== id && !document.getElementById(other).hidden) setPanel(other, false);
  }
  function focusPanel(id) {
    const target = document.getElementById(id).querySelector("h2[tabindex], .tl-stage, summary");
    if (target) target.focus();
  }
  function intro() {
    const n = all.length;
    return `<div class="intro">
      <p class="intro-lead">${esc(cfg.texte.lead)}</p>
      <p><strong>So geht's:</strong> Oben ein Gebiet wählen, dann auf der Karte oder in der Liste einen Vorgang anklicken. Hier erscheint die Prozesslinie: in welchen Sitzungen er auf der Tagesordnung stand, mit Fundstelle.</p>
      <p class="intro-actions">
        <button type="button" class="btn btn-soft" data-show="panel-list"><svg class="icon" aria-hidden="true"><use href="#i-list"/></svg>Liste öffnen</button>
        <button type="button" class="btn btn-soft" data-show="timeline-wrap"><svg class="icon" aria-hidden="true"><use href="#i-clock"/></svg>Zeitleiste öffnen</button></p>
      ${n ? "" : '<p class="notice">Noch keine Daten: Die Datenpipeline wird gerade aufgebaut. Karte und Bedienung lassen sich schon ansehen.</p>'}
      <p class="hint">${esc(cfg.texte.datenluecke)}</p></div>${LIMITS}`;
  }
  function showIntro() {
    $("#detail-heading").textContent = "Los geht's";
    $("#detail").innerHTML = intro();
    const t = toggleFor("timeline-wrap");
    if (t && t.hidden) $('#detail [data-show="timeline-wrap"]').hidden = true;
  }
  function closePanel(id) {
    setPanel(id, false);
    const t = toggleFor(id);
    if (t && t.offsetParent) t.focus();
  }
  document.addEventListener("click", (e) => {
    const t = e.target.closest("[data-panel]");
    if (t) {
      const open = document.getElementById(t.dataset.panel).hidden;
      setPanel(t.dataset.panel, open);
      if (open) focusPanel(t.dataset.panel);
    }
    const c = e.target.closest("[data-close]");
    if (c) closePanel(c.dataset.close);
    const s = e.target.closest("[data-show]");
    if (s) { setPanel(s.dataset.show, true); focusPanel(s.dataset.show); }
  });
  document.addEventListener("keydown", (e) => {
    if (e.key !== "Escape" || $("#about").open) return;
    if (openMegaId) return closeMega(true);
    const overlay = OVERLAYS.find((id) => !document.getElementById(id).hidden);
    if (overlay) return closePanel(overlay);
    const inside = SHEETS.find((id) => document.getElementById(id).contains(document.activeElement));
    if (inside) closePanel(inside);
  });
  function applyLayout() {
    if (MOBILE.matches) {
      const open = SHEETS.filter((id) => !document.getElementById(id).hidden);
      open.slice(1).forEach((id) => setPanel(id, false));
    } else if (NARROW.matches && !$("#panel-list").hidden && !$("#panel-detail").hidden) setPanel("panel-detail", false);
    $("#timeline-wrap").classList.toggle("tl-compact", MOBILE.matches);
    clampWidths();
    if (tl) tl.select(selected);
  }

  // --- Mega-Menüs ------------------------------------------------------------------------------------
  let openMegaId = null;
  function openMega(id) {
    if (openMegaId && openMegaId !== id) closeMega();
    document.getElementById(id).hidden = false;
    openMegaId = id;
    document.querySelectorAll(`[data-mega="${id}"]`).forEach((b) => b.setAttribute("aria-expanded", "true"));
    if (MOBILE.matches) SHEETS.forEach((s) => !document.getElementById(s).hidden && setPanel(s, false));
  }
  function closeMega(returnFocus) {
    if (!openMegaId) return;
    const id = openMegaId;
    document.getElementById(id).hidden = true;
    openMegaId = null;
    document.querySelectorAll(`[data-mega="${id}"]`).forEach((b) => b.setAttribute("aria-expanded", "false"));
    if (returnFocus) document.querySelector(`[data-mega="${id}"]`).focus();
  }
  document.addEventListener("click", (e) => {
    const m = e.target.closest("[data-mega]");
    if (m) {
      const id = m.dataset.mega;
      if (openMegaId === id) closeMega(); else { openMega(id); const f = document.getElementById(id).querySelector("button, a, input"); if (f && e.detail === 0) f.focus(); }
      return;
    }
    if (openMegaId && e.target.isConnected && !e.target.closest(".mega")) closeMega();
  });

  // --- Breite von Liste und Vorgang per Ziehgriff ---------------------------------------------------
  const WIDTH = { list: { v: "--list-w", min: 320, max: () => Math.min(720, innerWidth * 0.45), def: 400 },
    detail: { v: "--detail-w", min: 360, max: () => Math.min(800, innerWidth * 0.5), def: 460 } };
  const widthOf = (k) => parseFloat(getComputedStyle(document.documentElement).getPropertyValue(WIDTH[k].v)) || WIDTH[k].def;
  function setWidth(k, px, save) {
    const w = WIDTH[k], v = Math.round(Math.max(w.min, Math.min(w.max(), px)));
    document.documentElement.style.setProperty(w.v, v + "px");
    const r = document.querySelector(`.resizer[data-resize="${k}"]`);
    r.setAttribute("aria-valuemin", String(w.min)); r.setAttribute("aria-valuemax", String(Math.round(w.max())));
    r.setAttribute("aria-valuenow", String(v)); r.setAttribute("aria-valuetext", `${v} Pixel breit`);
    if (save) { try { localStorage.setItem("sm-breite-" + k, String(v)); } catch (e) { /* ohne Speicher */ } }
  }
  function clampWidths() { for (const k of Object.keys(WIDTH)) setWidth(k, widthOf(k)); }
  for (const k of Object.keys(WIDTH)) {
    try { const v = Number(localStorage.getItem("sm-breite-" + k)); if (v) document.documentElement.style.setProperty(WIDTH[k].v, v + "px"); } catch (e) { /* ohne Speicher */ }
  }
  document.querySelectorAll(".resizer").forEach((r) => {
    const k = r.dataset.resize, sign = k === "list" ? 1 : -1;
    r.addEventListener("pointerdown", (e) => {
      e.preventDefault();
      r.setPointerCapture(e.pointerId);
      const x0 = e.clientX, w0 = widthOf(k);
      r.classList.add("active"); document.body.classList.add("resizing");
      const move = (ev) => setWidth(k, w0 + sign * (ev.clientX - x0));
      const up = () => { r.removeEventListener("pointermove", move); r.classList.remove("active"); document.body.classList.remove("resizing"); setWidth(k, widthOf(k), true); };
      r.addEventListener("pointermove", move);
      r.addEventListener("pointerup", up, { once: true });
      r.addEventListener("pointercancel", up, { once: true });
    });
    r.addEventListener("keydown", (e) => {
      const step = e.shiftKey ? 64 : 16;
      const keys = { ArrowRight: sign * step, ArrowLeft: -sign * step };
      if (keys[e.key] !== undefined) { e.preventDefault(); setWidth(k, widthOf(k) + keys[e.key], true); }
      if (e.key === "Home") { e.preventDefault(); setWidth(k, WIDTH[k].def, true); }
    });
    r.addEventListener("dblclick", () => setWidth(k, WIDTH[k].def, true));
  });

  // --- Über ----------------------------------------------------------------------------------------
  $("#about-open").addEventListener("click", () => { closeMega(); $("#about").showModal(); });
  $("#about-close").addEventListener("click", () => $("#about").close());
  $("#about").addEventListener("click", (e) => { if (e.target === e.currentTarget) e.currentTarget.close(); });

  // --- Gebiet ----------------------------------------------------------------------------------------
  // stadt:alle (alle Vorgänge), ortsteil:<slug> (Ortsbezug im Ortsteil), ohne:alle (ohne Ortsbezug)
  function parseArea(value) {
    const [kind, key] = (value || "").split(":");
    if (kind === "ortsteil") {
      const o = ortsteile().find((x) => x.slug === key);
      if (o) return { kind, key, name: o.name };
    }
    if (kind === "ohne") return { kind, key: "alle", name: "ohne Ortsbezug" };
    return { kind: "stadt", key: "alle", name: `ganz ${cfg.stadt.name}` };
  }
  const hasPlace = (p) => p.locations.length > 0;
  const inArea = (p) => area.kind === "stadt" || (area.kind === "ohne" ? !hasPlace(p) : p.locations.some((l) => l.ortsteil === area.name));
  function countIn(o) { return all.filter((p) => !p.verfahrenspunkt && p.locations.some((l) => l.ortsteil === o.name)).length; }
  function fillAreaSelect() {
    const sel = $("#f-area");
    const opt = (o) => `<option value="ortsteil:${esc(o.slug)}">${esc(o.name)}${all.length ? ` (${countIn(o)})` : ""}</option>`;
    sel.innerHTML = `<option value="stadt:alle">${esc(`Ganz ${cfg.stadt.name}`)}</option>`
      + ortsteile().filter((o) => !o.ortsbezirk).map(opt).join("")
      + `<optgroup label="Ortsbezirke">${ortsteile().filter((o) => o.ortsbezirk).sort((a, b) => a.name.localeCompare(b.name, "de")).map(opt).join("")}</optgroup>`
      + '<option value="ohne:alle">ohne Ortsbezug (stadtweit)</option>';
  }
  function areaLocs(p) {
    if (area.kind === "ortsteil") return p.locations.filter((l) => l.ortsteil === area.name);
    return p.locations;
  }
  const bestConfidence = (p) => areaLocs(p).reduce((b, l) => (RANK[l.confidence] > RANK[b] ? l.confidence : b), "niedrig");

  function loadArea(value, keepState) {
    area = parseArea(value);
    $("#f-area").value = `${area.kind}:${area.key}`;
    papers = all.filter(inArea);
    document.title = area.kind === "stadt" ? `${cfg.stadt.titel} – Sitzungsinformationen auf Karte und Zeitleiste`
      : `${cfg.stadt.titel} – Vorgänge ${area.kind === "ohne" ? "ohne Ortsbezug" : "in " + area.name}`;
    $("#f-conf").hidden = area.kind === "ohne";
    fillFilters();
    drawOutline();
    selected = null;
    shown = LIST_STEP;
    if (!keepState) showIntro();
    if (tl && zeit) { tl.setData(zeit); tl.select(null); }
    if (!$("#panel-termine").hidden) showTermine();
    if (!$("#panel-auswertung").hidden) showStats();
    render();
    syncUrl();
  }

  // --- Karte -----------------------------------------------------------------------------------------
  const MARKER = { radius: 8, weight: 2, color: "#fff", fillOpacity: 0.95 };
  const color = (c) => getComputedStyle(document.documentElement).getPropertyValue("--" + c).trim();
  let baseLayer = null, colored = false;
  function setBase() {
    const h = cfg.karte.hintergrund;
    if (baseLayer) baseLayer.remove();
    baseLayer = L.tileLayer(colored ? h.farbig : h.grau, { maxZoom: h.max_zoom, attribution: h.attribution }).addTo(map);
  }
  function initMap() {
    map = L.map("map", { zoomControl: false, scrollWheelZoom: true, zoomAnimation: !REDUCED, fadeAnimation: !REDUCED, markerZoomAnimation: !REDUCED });
    L.control.zoom({ position: "bottomright" }).addTo(map);
    map.attributionControl.setPrefix(false);
    // basemap.de grau (Standard) oder farbig; die Wahl merkt sich der Browser
    try { colored = localStorage.getItem("sm-karte-farbig") === "1"; } catch (e) { /* ohne Speicher: grau */ }
    setBase();
    const button = (cls, text, onClick, pressed) => L.Control.extend({
      options: { position: "bottomright" },
      onAdd() {
        const b = L.DomUtil.create("button", `map-style ${cls}`);
        b.type = "button";
        b.textContent = text;
        if (pressed) b.setAttribute("aria-pressed", String(pressed()));
        b.addEventListener("click", () => { onClick(b); if (pressed) b.setAttribute("aria-pressed", String(pressed())); });
        L.DomEvent.disableClickPropagation(b);
        return b;
      },
    });
    new (button("map-colored", "Farbige Karte", () => {
      colored = !colored;
      try { localStorage.setItem("sm-karte-farbig", colored ? "1" : "0"); } catch (e) { /* nicht speicherbar */ }
      setBase();
    }, () => colored))().addTo(map);
    planOn = new URLSearchParams(location.search).get("plaene") === "1";
    new (button("map-plans", "Bauleitplanung", () => { planOn = !planOn; drawPlans(); syncUrl(); }, () => planOn))().addTo(map);
    new (button("map-whole", `Ganz ${cfg.stadt.name} ansehen`, () => map.fitBounds(cityBounds(), mapPadding())))().addTo(map);
    // mobil: die Schaltflächen unten rechts hinter „Kartenoptionen“, damit sie die Karte nicht verdecken
    const MapMenu = L.Control.extend({
      options: { position: "bottomright" },
      onAdd() {
        const b = L.DomUtil.create("button", "map-style map-menu");
        b.type = "button";
        b.textContent = "Kartenoptionen";
        b.setAttribute("aria-expanded", "false");
        const set = (open) => { map.getContainer().classList.toggle("map-menu-open", open); b.setAttribute("aria-expanded", String(open)); };
        b.addEventListener("click", () => set(b.getAttribute("aria-expanded") !== "true"));
        map.on("click", () => set(false));
        L.DomEvent.disableClickPropagation(b);
        return b;
      },
    });
    new MapMenu().addTo(map);
    const Legend = L.Control.extend({
      options: { position: "bottomleft" },
      onAdd() {
        const d = L.DomUtil.create("details", "map-legend");
        d.open = !MOBILE.matches;
        L.DomEvent.disableClickPropagation(d);
        L.DomEvent.disableScrollPropagation(d);
        return d;
      },
    });
    legendEl = new Legend().addTo(map).getContainer();
    cluster = L.markerClusterGroup({ showCoverageOnHover: false, maxClusterRadius: 40, animate: !REDUCED }).addTo(map);
    map.fitBounds(cityBounds());
  }
  function cityBounds() {
    if (navLayer) return navLayer.getBounds();
    const [w, s, e, n] = cfg.karte.bbox;
    return L.latLngBounds([s, w], [n, e]);
  }
  function mapPadding() {
    const desktop = !MOBILE.matches;
    const left = desktop && !$("#panel-list").hidden ? widthOf("list") + 32 : 16;
    const right = desktop && !$("#panel-detail").hidden ? widthOf("detail") + 32 : 16;
    const top = desktop && !$("#timeline-wrap").hidden ? 86 + $("#timeline-wrap").offsetHeight + 12 : 90;
    return { paddingTopLeft: [left, top], paddingBottomRight: [right, desktop ? 70 : 150], animate: !REDUCED };
  }
  // Ortsbezirke als anklickbare Flächen, sobald die Pipeline sie liefert (Gemarkungen, HVBG)
  function initNav() {
    if (!flaechen) return;
    map.createPane("gebiete").style.zIndex = 350;
    navLayer = L.geoJSON(flaechen, {
      pane: "gebiete", style: () => ({ color: color("accent-ink"), weight: 1, opacity: 0.5, fillColor: color("accent"), fillOpacity: 0.06 }),
      onEachFeature(f, layer) {
        const o = ortsteile().find((x) => x.slug === f.properties.slug);
        if (!o) return;
        layer.bindTooltip(() => `<strong>${esc(o.name)}</strong><br>${de(countIn(o))} Vorgänge mit Ortsbezug`, { sticky: true, className: "nav-tip" });
        layer.on("click", () => { if (!(area.kind === "ortsteil" && area.key === o.slug)) chooseArea(`ortsteil:${o.slug}`); });
      },
    }).addTo(map);
  }
  function chooseArea(value) {
    range = null;
    if (tl) tl.reset();
    loadArea(value);
  }
  function drawOutline() {
    if (outline) outline.remove();
    outline = null;
    const feature = area.kind === "ortsteil" && flaechen ? flaechen.features.find((f) => f.properties.slug === area.key) : null;
    if (!feature) { map.fitBounds(cityBounds(), mapPadding()); return; }
    outline = L.geoJSON(feature, { style: { color: color("accent-ink"), weight: 2.5, fillColor: color("accent"), fillOpacity: 0.12 }, interactive: false }).addTo(map);
    map.fitBounds(outline.getBounds(), mapPadding());
  }
  function drawLegend() {
    const rows = [[color("hoch"), "Ort gesichert (Gremium des Ortsteils oder eindeutiger Plan)"], [color("mittel"), "Ort erschlossen (Name im Titel)"], [color("niedrig"), "Ort unsicher (mehrdeutig oder Sprachmodell)"]];
    legendEl.innerHTML = `<summary>Legende: Sicherheit des Orts</summary><ul>${rows
      .map(([c, t]) => `<li><span class="swatch" style="background:${c}" aria-hidden="true"></span>${esc(t)}</li>`).join("")}</ul>
      <p class="hint">Vorgänge, die nur einem Ortsteil zugeordnet sind, stehen in der Liste, nicht als Punkt.</p>
      ${planOn ? `<ul><li><span class="swatch swatch-plan" aria-hidden="true"></span>Geltungsbereich eines Bebauungsplans</li>
        <li><span class="swatch swatch-fplan" aria-hidden="true"></span>Änderung des Flächennutzungsplans</li></ul>
        <p class="hint">${esc(cfg.bauleitplanung.attribution)}. Nicht rechtsverbindlich.</p>` : ""}`;
  }
  // Kartenebene Bauleitplanung: erst beim Einschalten geladen; Hinweis zur Nutzung in Legende und Namensnennung
  const loadPlans = () => (planData ||= fetch(PLAENE_URL).then((r) => (r.ok ? r.json() : null)).catch(() => null));
  const planStyle = (f) => ({ color: f.properties.art === "fplan" ? color("niedrig") : color("accent-ink"), weight: 1.5,
    dashArray: f.properties.art === "fplan" ? "5 4" : null, fillColor: f.properties.art === "fplan" ? color("niedrig") : color("accent"), fillOpacity: 0.1 });
  async function drawPlans() {
    if (legendEl) drawLegend();
    if (!planOn) { if (planLayer) { planLayer.remove(); planLayer = null; } return; }
    const d = await loadPlans();
    if (!planOn || planLayer || !d) return;
    planLayer = L.geoJSON(d, {
      style: planStyle, attribution: esc(d.attribution),
      onEachFeature: (f, layer) => layer.bindTooltip(`${esc(planName(f.properties))}${f.properties.gueltig_ab ? `<br>rechtskräftig seit ${fmtDate(f.properties.gueltig_ab)}` : ""}`, { sticky: true })
        .on("click", () => showPlan(f.properties.key)),
    }).addTo(map);
    planLayer.bringToBack();
    if (legendEl) drawLegend();
  }
  const planName = (p) => `${p.art === "fplan" ? "" : "Bebauungsplan "}${p.titel}`;
  async function showPlan(key) {
    const d = await loadPlans();
    const f = d && d.features.find((x) => x.properties.key === key);
    if (!f) return;
    selected = null;
    planShown = key;
    highlight();
    const list = all.filter((v) => (v.plans || []).some((p) => p.key === key));
    const docs = (f.properties.dokumente || []).map((u) => link(u, esc(decodeURIComponent(u.split("/").pop())))).filter(Boolean);
    $("#detail-heading").textContent = f.properties.art === "fplan" ? "Flächennutzungsplan" : "Bebauungsplan";
    $("#detail").innerHTML = `<h3 tabindex="-1">${esc(planName(f.properties))}</h3>
      <dl class="facts">${f.properties.gueltig_ab ? `<dt>Rechtskräftig seit</dt><dd>${fmtDate(f.properties.gueltig_ab)}</dd>` : ""}
        ${f.properties.nr ? `<dt>Plannummer</dt><dd>${esc(f.properties.nr)}${f.properties.aenderung ? `, ${f.properties.aenderung}. Änderung` : ""}</dd>` : ""}</dl>
      ${docs.length ? `<h4>Plandokumente der Stadt</h4><ul class="related">${docs.map((x) => `<li>${x}</li>`).join("")}</ul>` : ""}
      <h4>Vorgänge mit dieser Plannummer (${list.length})</h4>
      ${list.length ? `<ul class="related">${list.map((v) => `<li><button type="button" class="link-btn" data-open-ref="${esc(v.reference)}">${esc(v.name)}</button> · ${fmtDate(v.date)}</li>`).join("")}</ul>`
        : "<p>Kein Tagesordnungspunkt seit Juli 2024 nennt diesen Plan.</p>"}
      <p class="hint">${esc(cfg.bauleitplanung.attribution)}. Nicht rechtsverbindlich; maßgeblich sind die Unterlagen der Stadt.</p>`;
    if (MOBILE.matches || $("#panel-detail").hidden) setPanel("panel-detail", true);
    $("#detail").scrollTop = 0;
    syncUrl();
  }

  function drawMarkers(list) {
    if (legendEl) drawLegend();
    cluster.clearLayers();
    markers.clear();
    for (const p of list) {
      const ms = areaLocs(p).filter((l) => l.level !== "ortsteil" && l.lon != null).map((l) => {
        const m = L.circleMarker([l.lat, l.lon], { ...MARKER, fillColor: color(l.confidence) })
          .bindTooltip(`${esc(p.reference)} · ${esc(l.name)}`).on("click", () => select(p, true));
        return m;
      });
      ms.forEach((m) => cluster.addLayer(m));
      markers.set(p.reference, ms);
    }
    highlight();
  }
  function highlight() {
    for (const [ref, ms] of markers) {
      const on = selected && ref === selected.reference;
      ms.forEach((m) => { m.setStyle(on ? { radius: 12, weight: 3, color: color("text") } : { radius: MARKER.radius, weight: MARKER.weight, color: MARKER.color }); if (on) m.bringToFront(); });
    }
  }

  // --- Liste und Filter ------------------------------------------------------------------------------
  function fillFilters() {
    const sel = $("#f-gremium"), cur = sel.value;
    const names = [...new Set(papers.flatMap((p) => p.process.map((s) => s.gremium)))].sort((a, b) => a.localeCompare(b, "de"));
    sel.innerHTML = '<option value="">alle</option>' + names.map((v) => `<option value="${esc(v)}">${esc(v)}</option>`).join("");
    if (names.includes(cur)) sel.value = cur;
  }
  function inRange(p) {
    if (!range) return true;
    const [a, b] = range, dim = tl ? tl.dimension() : "vorlage";
    if (dim === "vorlage") return p.date >= a && p.date <= b;
    return p.process.some((s) => s.date && s.date >= a && s.date <= b);
  }
  function filtered(withRange = true) {
    const text = $("#f-text").value.trim().toLowerCase(), gremium = $("#f-gremium").value, art = $("#f-art").value;
    const proc = $("#f-verfahren").checked;
    const confs = new Set([...document.querySelectorAll("#f-conf input:checked")].map((i) => i.value));
    return papers.filter((p) => (proc || !p.verfahrenspunkt) && (!gremium || p.process.some((s) => s.gremium === gremium)) &&
      (!art || (art === "vorlage") === Boolean(p.vorlage)) &&
      (area.kind !== "ortsteil" || confs.has(bestConfidence(p))) && (!withRange || inRange(p)) &&
      (!text || (p.name + " " + p.reference).toLowerCase().includes(text)));
  }
  function resetFilters() {
    $("#filters").reset();
    $("#q").value = "";
    range = null;
    if (tl) tl.reset();
    shown = LIST_STEP;
    render();
    syncUrl();
  }
  function itemHtml(p) {
    const c = bestConfidence(p);
    const conf = hasPlace(p) && area.kind !== "ohne" ? `<span class="conf conf-${c}">${CONF[c]}</span>` : "";
    const gremien = [...new Set(p.process.map((s) => gremiumShort(s.gremium)))].join(", ");
    return `<li><button type="button" data-ref="${esc(p.reference)}" aria-current="${selected === p}">
      <span class="title">${esc(p.name)}</span>
      <span class="meta"><span>${esc(p.vorlage || "ohne Vorlagennummer")}</span><span>${fmtDate(p.date)}</span><span>${esc(gremien)}</span>
      ${p.process.length > 1 ? `<span>${p.process.length} Beratungen</span>` : ""}${conf}</span></button></li>`;
  }
  function render() {
    const base = filtered(false);
    const list = range ? base.filter(inRange) : base;
    const where = area.kind === "stadt" ? area.name : area.kind === "ohne" ? "ohne Ortsbezug" : area.name;
    const span = range ? ` · ${fmtDate(range[0])}–${fmtDate(range[1])}` : "";
    $("#count").textContent = all.length ? `${list.length} von ${papers.length} Vorgängen · ${where}${span}` : "Noch keine Daten veröffentlicht.";
    const active = [$("#f-verfahren").checked].filter(Boolean).length + (area.kind === "ortsteil" ? document.querySelectorAll("#f-conf input:not(:checked)").length : 0);
    $("#active-filters").textContent = active ? ` (${active} aktiv)` : "";
    let html = list.slice(0, shown).map(itemHtml).join("");
    if (list.length > shown) html += `<li class="more"><button type="button" class="btn btn-secondary" id="more">Weitere ${Math.min(LIST_STEP, list.length - shown)} von ${list.length - shown} anzeigen</button></li>`;
    if (!all.length) html = '<li class="empty-list"><p>Die Datenpipeline ist noch im Aufbau. Sobald die ersten Einladungen ausgewertet sind, erscheinen hier die Vorgänge.</p></li>';
    else if (!list.length) html = `<li class="empty-list"><p>Kein Vorgang passt zu Gebiet, Filtern und Zeitraum.</p><button type="button" class="btn btn-secondary" id="reset-filters">Filter und Zeitraum zurücksetzen</button></li>`;
    $("#papers").innerHTML = html;
    drawMarkers(list);
    if (tl) tl.setPapers(base);
  }
  const renderSoon = debounce(() => { shown = LIST_STEP; render(); }, 200);

  // --- Detail: Prozesslinie mit Evidenzstatus -------------------------------------------------------
  const link = (url, text, cls) => { const u = safeUrl(url); return u ? `<a ${cls ? `class="${cls}" ` : ""}href="${u}" target="_blank" rel="noopener">${text}</a>` : ""; };
  // Station = Sitzung, in deren Tagesordnung der Vorgang steht (belegt); Ergebnis bleibt sichtbar als Lücke
  function stepHtml(s) {
    const status = s.oeffentlich === false ? "nicht_öffentlich" : "belegt";
    const body = [`TOP ${esc(s.top)}${s.ort ? ` · ${esc(s.ort)}` : ""}`, fmtDate(s.date) + (s.time ? `, ${esc(s.time)} Uhr` : "")];
    body.push(`Fundstelle: ${link(s.pdf, `Bekanntmachung Nr. ${esc(s.bekanntmachung)} (PDF)`) || `Bekanntmachung Nr. ${esc(s.bekanntmachung)}`}`);
    if (s.titel && s.titel !== selected?.name) body.push(`Titel in dieser Tagesordnung: <q>${esc(s.titel)}</q>`);
    body.push(`<button type="button" class="jump" data-date="${esc(s.date)}">in der Zeitleiste zeigen</button>`);
    const result = s.result ? `<div>Ergebnis: <q>${esc(s.result)}</q></div>`
      : `<div class="blackbox"><span class="mark-inline mark-unklar" aria-hidden="true">?</span> ${esc(RESULT_GAP)} ${link(cfg.stadt.sessionnet, "Bürgerinformationssystem")}</div>`;
    return `<li class="step" data-status="${status}">
      <span class="mark mark-${status}" aria-hidden="true"></span>
      <div class="step-head">Beratung: ${esc(s.gremium)}<span class="step-status">${esc(STATUS[status])}</span></div>
      <div class="step-body">${body.join("<br>")}${result}</div></li>`;
  }
  function legend() {
    return `<details class="acc"><summary>Legende Evidenzstatus</summary><div class="legend">${["belegt", "abgeleitet", "nicht_öffentlich", "unklar"]
      .map((s) => `<span><span class="mark mark-${s}" aria-hidden="true">${s === "unklar" ? "?" : ""}</span><strong>${STATUS[s]}</strong> – ${STATUS_TEXT[s]}</span>`).join("")}
      <span class="hint">Linie: durchgezogen = belegt, gestrichelt = abgeleitet, gepunktet = nicht öffentlich oder unklar.</span></div></details>`;
  }
  function reportLink(p) {
    const q = new URLSearchParams({ title: `Verortung prüfen: ${p.reference}`, body: `Vorgang: ${p.reference}\nTitel: ${p.name}\nGebiet: ${area.name}\n\nWas ist falsch?\n` });
    return `${cfg.projekt.repo}/issues/new?${q}`;
  }
  function methodText(l) {
    const m = METHOD[l.method] || l.method;
    return `${esc(m)}${l.stage === "C" ? ' <span class="derived">Sprachmodell</span>' : ""}${l.evidence ? ` · Fundstelle: „${esc(l.evidence)}“` : ""}`;
  }
  function select(p, fromMap) {
    selected = p;
    planShown = null;
    document.querySelectorAll(".papers button[data-ref]").forEach((b) => b.setAttribute("aria-current", String(b.dataset.ref === p.reference)));
    syncUrl();
    if (tl) tl.select(p);
    highlight();
    const outside = (l) => area.kind === "ortsteil" && l.ortsteil && l.ortsteil !== area.name;
    const locItem = (l) => `<li><strong>${esc(l.name || l.ortsteil)}</strong>
      ${l.ortsteil && l.level !== "ortsteil" ? `(${esc(l.ortsteil)})` : ""} – <span class="conf conf-${esc(l.confidence)}">${CONF[l.confidence] || esc(l.confidence)}</span>, Stufe ${esc(l.stage)}${outside(l) ? ' <span class="hint">außerhalb des gewählten Gebiets</span>' : ""}<br>
      <span class="meta">${methodText(l)}</span></li>`;
    const locs = p.locations.length ? p.locations.map(locItem).join("") : "<li>stadtweit / ohne Ortsbezug</li>";
    const sources = (data.meta.sources || []).map((s) => `<li>${esc(s.name)}: ${esc(s.license)}${s.retrieved_at ? ` · Abruf ${esc(String(s.retrieved_at).slice(0, 10))}` : ""}</li>`).join("");
    const gremien = [...new Set(p.process.map((s) => s.gremium))];
    $("#detail-heading").textContent = "Vorgang";
    $("#detail").innerHTML = `
      <h3 tabindex="-1">${esc(p.name)}</h3>
      <dl class="facts">
        <dt>Vorlage</dt><dd>${p.vorlage ? esc(p.vorlage) : "ohne Vorlagennummer"}</dd>
        <dt>Erste Beratung</dt><dd>${fmtDate(p.date)}</dd>
        <dt>Gremien</dt><dd>${esc(gremien.join(", "))}</dd>
        ${p.verfahrenspunkt ? '<dt>Art</dt><dd>Verfahrenspunkt <span class="derived">abgeleitet</span></dd>' : ""}
      </dl>
      <div class="links">${link(p.process[0] && p.process[0].pdf, "Einladung (PDF)", "btn btn-primary")}
        ${link(cfg.stadt.sessionnet, "Bürgerinformationssystem", "btn btn-secondary")}</div>
      <h4>Prozesslinie</h4>
      ${p.vorlage ? `<p class="hint">Stationen sind die Sitzungen, in deren Tagesordnung die Vorlage ${esc(p.vorlage)} steht, chronologisch.</p>`
        : '<p class="hint">Ohne Vorlagennummer: eine einzelne Station. Tagesordnungspunkte werden nicht über ähnliche Titel verknüpft.</p>'}
      <ol class="steps">${p.process.map(stepHtml).join("")}</ol>
      ${legend()}
      <h4>Ortsbezug</h4><ul class="locs">${locs}</ul>
      ${(p.plans || []).length ? `<h4>Bauleitplanung</h4><ul class="locs">${p.plans.map((x) => `<li><button type="button" class="link-btn" data-open-plan="${esc(x.key)}">${esc(x.titel)}</button>
        <br><span class="meta">${esc(x.treffer)} · Fundstelle: „${esc(x.evidence)}“</span></li>`).join("")}</ul>
        <p class="hint">${esc(cfg.bauleitplanung.attribution)}.</p>` : ""}
      ${(p.bezuege || []).length ? `<p class="hint">Im Titel genannt: ${p.bezuege.map(esc).join(", ")} <span class="derived">Verweis, nicht verknüpft</span></p>` : ""}
      <p class="links">${link(reportLink(p), "Verortung falsch? Hinweis geben", "btn btn-secondary")}</p>
      <details class="acc"><summary>Quellen dieses Vorgangs</summary><ul>
        ${p.process.map((s) => `<li>${link(s.pdf, `Bekanntmachung Nr. ${esc(s.bekanntmachung)}`) || esc(s.bekanntmachung)} · ${esc(s.gremium)}, ${fmtDate(s.date)}, TOP ${esc(s.top)}</li>`).join("")}
        ${sources}</ul></details>
      ${LIMITS}`;
    $("#announce").textContent = `Vorgang ${p.reference} geöffnet: ${p.name}`;
    if (MOBILE.matches || $("#panel-detail").hidden) setPanel("panel-detail", true);
    $("#detail").scrollTop = 0;
    const ms = markers.get(p.reference) || [];
    if (fromMap) {
      const b = document.querySelector(`.papers button[data-ref="${CSS.escape(p.reference)}"]`);
      if (b) b.scrollIntoView({ block: "nearest" });
    } else {
      if (ms.length) cluster.zoomToShowLayer(ms[0], () => { highlight(); map.panTo(ms[0].getLatLng(), { animate: !REDUCED }); });
      if (MOBILE.matches) $("#detail h3").focus();
    }
  }
  $("#detail").addEventListener("click", (e) => {
    const pl = e.target.closest("[data-open-plan]");
    if (pl) { if (!planOn) { planOn = true; document.querySelector(".map-plans")?.setAttribute("aria-pressed", "true"); drawPlans(); } showPlan(pl.dataset.openPlan); return; }
    const r = e.target.closest("[data-open-ref]");
    if (r) { const v = all.find((x) => x.reference === r.dataset.openRef); if (v) { if (!papers.includes(v)) loadArea(DEFAULT_AREA, true); select(v); } return; }
    const b = e.target.closest(".jump");
    if (b && tl) { if ($("#timeline-wrap").hidden) setPanel("timeline-wrap", true); tl.center(b.dataset.date); }
  });

  // --- Termine: kommende Sitzungen -------------------------------------------------------------------
  function showTermine() {
    const box = $("#termine");
    const scope = box.querySelector("#termine-scope") ? box.querySelector("#termine-scope").value : "gebiet";
    const today = new Date().toISOString().slice(0, 10);
    // im Gebiet: stadtweite Gremien und Beiräte des gewählten Ortsteils
    const relevant = (m) => scope === "alle" || area.kind !== "ortsteil" || !m.ortsteil || m.ortsteil === area.name;
    const list = (data.sitzungen || []).filter((m) => m.date >= today && relevant(m)).sort((a, b) => a.date.localeCompare(b.date));
    const onAgenda = (m) => papers.filter((p) => !p.verfahrenspunkt && p.process.some((s) => s.sitzung === m.id));
    let month = "";
    const items = list.map((m) => {
      const head = m.date.slice(0, 7) !== month ? `<h3 class="month">${new Date(m.date + "T12:00:00Z").toLocaleDateString("de-DE", { month: "long", year: "numeric" })}</h3>` : "";
      month = m.date.slice(0, 7);
      const ps = onAgenda(m);
      return `${head}<div class="meeting">
        <div class="meeting-head"><span class="meeting-date">${(m.termine || [{ date: m.date, time: m.time }]).map((t) => `${fmtDay(t.date)}${t.time ? `, ${esc(t.time)} Uhr` : ""}`).join(" und ")}</span>
          <strong>${esc(m.gremium)}</strong>${m.oeffentlich === false ? ' <span class="badge">nicht öffentlich</span>' : ""}</div>
        <div class="meta">${esc(m.ort || "")}${m.ort ? " · " : ""}${link(m.pdf, "Einladung (PDF)") || "Einladung"}</div>
        ${ps.length ? `<div class="agenda"><span>Auf der Tagesordnung${area.kind === "ortsteil" ? ` (${esc(area.name)})` : ""}:</span><ul>${ps.map((p) => `<li><button type="button" class="linkish" data-ref="${esc(p.reference)}">${esc(p.name)}</button></li>`).join("")}</ul></div>` : ""}
      </div>`;
    }).join("");
    box.innerHTML = `<p class="hint">Sitzungen laut Einladungen in den amtlichen Bekanntmachungen. Sie sind in der Regel öffentlich; die Einladung erscheint etwa ein bis zwei Wochen vorher.</p>
      <div class="filters termine-filters"><label>Gremien
        <select id="termine-scope"><option value="gebiet"${scope === "gebiet" ? " selected" : ""}>${area.kind === "ortsteil" ? `stadtweite Gremien und ${esc(area.name)}` : "alle Gremien"}</option>
        <option value="alle"${scope === "alle" ? " selected" : ""}>alle Gremien</option></select></label></div>
      <p class="count">${list.length} kommende Sitzungen</p>
      ${items || "<p>Keine kommenden Sitzungen im Datenbestand.</p>"}`;
    box.querySelector("#termine-scope").addEventListener("change", showTermine);
  }
  $("#termine").addEventListener("click", (e) => {
    const b = e.target.closest("button[data-ref]");
    if (b) { const p = papers.find((x) => x.reference === b.dataset.ref); if (p) { closePanel("panel-termine"); select(p); } }
  });

  // --- Kennzahlen zum Gebiet ---------------------------------------------------------------------------
  function bars(title, rows, attr) {
    const max = Math.max(1, ...rows.map((r) => r.n));
    return `<section class="stat-block"><h3>${esc(title)}</h3><ul class="bars">${rows.map((r) => `<li><button type="button" class="bar" ${attr}="${esc(r.key)}" aria-label="${esc(r.label)}: ${r.n} Vorgänge – Liste danach filtern">
      <span>${esc(r.label)}</span><span class="bar-track" aria-hidden="true"><span class="bar-fill" style="width:${(100 * r.n / max).toFixed(1)}%"></span></span><span class="bar-n">${r.n}</span></button></li>`).join("")}</ul></section>`;
  }
  function showStats() {
    const list = papers.filter((p) => !p.verfahrenspunkt);
    const count = (f) => { const c = new Map(); for (const p of list) for (const k of f(p)) c.set(k, (c.get(k) || 0) + 1); return c; };
    const gr = count((p) => [...new Set(p.process.map((s) => s.gremium))]);
    const yr = count((p) => (p.date ? [p.date.slice(0, 4)] : []));
    const st = count((p) => [p.locations.length ? `Stufe ${[...new Set(p.locations.map((l) => l.stage))].sort().join("/")}` : "ohne Ortsbezug"]);
    $("#stats").innerHTML = list.length ? `<p class="hint">${list.length} Vorgänge (ohne Verfahrenspunkte) · ${esc(area.name)}. Ein Klick auf einen Balken filtert die Liste. Ortsbezüge sind abgeleitet.</p>
      ${bars("Nach Gremium", [...gr].map(([k, n]) => ({ key: k, label: k, n })).sort((a, b) => b.n - a.n), "data-stat-gremium")}
      ${bars("Nach Jahr (erste Beratung)", [...yr].map(([k, n]) => ({ key: k, label: k, n })).sort((a, b) => a.key.localeCompare(b.key)), "data-stat-year")}
      ${bars("Nach Art des Ortsbezugs", [...st].map(([k, n]) => ({ key: k, label: k, n })).sort((a, b) => b.n - a.n), "data-stat-none")}`
      : '<p class="hint">Noch keine Daten.</p>';
  }
  $("#stats").addEventListener("click", (e) => {
    const b = e.target.closest(".bar");
    if (!b || b.dataset.statNone !== undefined) return;
    $("#filters").reset();
    range = null;
    if (tl) tl.reset();
    if (b.dataset.statGremium) $("#f-gremium").value = b.dataset.statGremium;
    if (b.dataset.statYear && tl) { const y = b.dataset.statYear; tl.setRange(`${y}-01-01`, `${y}-12-31`); range = [`${y}-01-01`, `${y}-12-31`]; }
    shown = LIST_STEP;
    render();
    syncUrl();
    closePanel("panel-auswertung");
    setPanel("panel-list", true);
    focusPanel("panel-list");
  });

  // --- Zeitleiste: Monatswerte aus den Daten ------------------------------------------------------------
  function buildZeit() {
    const start = (data.meta.data_start || cfg.quelle.datenbeginn).slice(0, 7);
    const last = [...all.map((p) => p.date), ...(data.sitzungen || []).map((m) => m.date), dataStand].filter(Boolean).sort().pop();
    const months = [];
    for (let [y, m] = start.split("-").map(Number); `${y}-${String(m).padStart(2, "0")}` <= last.slice(0, 7); m === 12 ? (y++, m = 1) : m++) months.push(`${y}-${String(m).padStart(2, "0")}`);
    const idx = new Map(months.map((m, i) => [m, i]));
    const typ = (name) => (cfg.gremien.find((g) => g.name === name) || {}).typ || (/^Ortsbeirat/.test(name) ? "ortsbeirat" : /^Stadtteilbeirat/.test(name) ? "stadtteilbeirat" : "beirat");
    const categories = Object.keys(cfg.gremientypen);
    const vorlage = Object.fromEntries(categories.map((c) => [cfg.gremientypen[c], months.map(() => 0)]));
    const sitzung = months.map(() => 0);
    for (const p of all) {
      if (p.verfahrenspunkt) continue;
      const i = idx.get(p.date.slice(0, 7));
      if (i != null) vorlage[cfg.gremientypen[typ(p.process[0].gremium)]][i]++;
      for (const s of p.process) { const j = idx.get(s.date.slice(0, 7)); if (j != null) sitzung[j]++; }
    }
    const ids = new Map(cfg.gremien.map((g) => [g.name, g.id]));
    return { months, categories: Object.keys(vorlage), density: { vorlage, sitzung },
      meetings: (data.sitzungen || []).map((m) => ({ date: m.date, gremium: m.gremium, gremium_id: m.gremium_id || ids.get(m.gremium) })),
      terms: cfg.wahlperioden, dataStart: `${start}-01`, dataStand };
  }

  // --- URL-Zustand -----------------------------------------------------------------------------------
  function syncUrl() {
    if (!area) return;
    const url = new URL(location.href);
    if (area.kind === "stadt") url.searchParams.delete("gebiet"); else url.searchParams.set("gebiet", `${area.kind}:${area.key}`);
    if (tl && range) { const s = tl.getState(); for (const k of ["von", "bis", "zoom", "achse"]) url.searchParams.set(k, s[k]); }
    else for (const k of ["von", "bis", "zoom", "achse"]) url.searchParams.delete(k);
    const g = $("#f-gremium").value;
    if (g) url.searchParams.set("gremium", g); else url.searchParams.delete("gremium");
    if (planOn) url.searchParams.set("plaene", "1"); else url.searchParams.delete("plaene");
    if (!selected && planShown) url.searchParams.set("plan", planShown); else url.searchParams.delete("plan");
    url.hash = selected ? encodeURIComponent(selected.reference) : "";
    history.replaceState(null, "", url);
  }

  // --- Start -----------------------------------------------------------------------------------------
  async function start() {
    const json = (url) => fetch(url).then((r) => (r.ok ? r.json() : null)).catch(() => null);
    const [c, d, f] = await Promise.all([json(CONFIG_URL), json(DATA_URL), json(FLAECHEN_URL)]);
    if (!c) throw new Error("Konfiguration (stadt.json) fehlt");
    cfg = c;
    data = d || { meta: { sources: [] }, sitzungen: [], vorgaenge: [] };
    flaechen = f && f.features && f.features.length ? f : null;
    all = data.vorgaenge || [];
    dataStand = (data.meta.generated_at || new Date().toISOString()).slice(0, 10);
    applyConfig();
    $("#stand").textContent = data.meta.generated_at ? `Datenstand: ${fmtDate(data.meta.generated_at)}` : "Datenstand: noch keine Daten";
    initMap();
    initNav();
    fillAreaSelect();
    if (all.length) {
      zeit = buildZeit();
      tl = Timeline.create($("#timeline-wrap"), {
        rows: cfg.zeitleiste_gremien.map((r) => ({ id: r.label, ids: r.ids, label: r.label })),
        limits: ["Sitzungen vor dem Beginn des Datenbestands (Einladungen erst ab Juli 2024 veröffentlicht).", "Beschlussergebnisse: Sie sind in den Bekanntmachungen nicht enthalten.", "Nichtöffentliche Beratungen."],
        unit: "Vorgänge",
        onRange(a, b) { range = [a, b]; shown = LIST_STEP; render(); syncUrl(); },
        onDate(dd) { tl.center(dd); },
      });
    } else {
      setPanel("timeline-wrap", false);
      toggleFor("timeline-wrap").hidden = true;
    }
    applyLayout();
    MOBILE.addEventListener("change", applyLayout);
    NARROW.addEventListener("change", applyLayout);
    $("#filters").addEventListener("submit", (e) => e.preventDefault());
    $("#filters").addEventListener("input", (e) => {
      if (e.target.id === "f-text") { $("#q").value = e.target.value; return renderSoon(); }
      shown = LIST_STEP;
      render();
      syncUrl();
    });
    $("#q").addEventListener("input", debounce(() => { $("#f-text").value = $("#q").value; shown = LIST_STEP; render(); }, 200));
    $("#nav-search").addEventListener("submit", (e) => { e.preventDefault(); setPanel("panel-list", true); $("#papers").focus(); });
    $("#f-area").addEventListener("change", (e) => chooseArea(e.target.value));
    $("#papers").addEventListener("click", (e) => {
      if (e.target.closest("#more")) { shown += LIST_STEP; render(); return; }
      if (e.target.closest("#reset-filters")) { resetFilters(); return; }
      const b = e.target.closest("button[data-ref]");
      if (b) select(papers.find((p) => p.reference === b.dataset.ref));
    });
    $("#papers").addEventListener("mouseover", (e) => {
      const b = e.target.closest("button[data-ref]");
      if (b && tl) tl.select(papers.find((p) => p.reference === b.dataset.ref), true);
    });
    $("#papers").addEventListener("mouseleave", () => tl && tl.select(selected));
    $("#cta-termine").addEventListener("click", () => { setPanel("panel-termine", true); showTermine(); focusPanel("panel-termine"); });
    $("#cta-stats").addEventListener("click", () => { setPanel("panel-auswertung", true); showStats(); focusPanel("panel-auswertung"); });
    const params = new URLSearchParams(location.search);
    const ref = decodeURIComponent(location.hash.slice(1));
    loadArea(params.get("gebiet") || DEFAULT_AREA, true);
    if (params.get("gremium")) { $("#f-gremium").value = params.get("gremium"); setPanel("panel-list", true); render(); }
    const von = params.get("von"), bis = params.get("bis");
    if (tl && ISO_DAY.test(von || "") && ISO_DAY.test(bis || "")) {
      setPanel("timeline-wrap", true);
      tl.setState({ von, bis, zoom: params.get("zoom"), achse: params.get("achse") });
      range = [von, bis];
      render();
    }
    if (planOn) drawPlans();
    const initial = papers.find((p) => p.reference === ref);
    if (initial) select(initial); else if (params.get("plan")) await showPlan(params.get("plan")); else showIntro();
    syncUrl();
  }

  start().catch((err) => { $("#detail").innerHTML = `<p>Die Seite konnte nicht geladen werden (${esc(err.message)}).</p>`; });
})();
