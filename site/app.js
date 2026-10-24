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
  // Umweltebenen (Hochwasser, Wasserschutz, Schutzgebiete Natur) je Gruppe aus stadt.json (umwelt.gruppen)
  const UMWELT_URL = (id) => `data/export/karte/umwelt_${id}.json`;
  // Wohnen und Boden: Kennzahlen (Bodenrichtwerte, Zensus 2022) und Zonen der Bodenrichtwerte als Kartenebene
  const WOHNEN_URL = "data/export/wohnen.json";
  const WANDERUNG_URL = "data/export/wanderung.json";
  // Wahlen: nur amtliche Ergebnisse, ohne Personennamen (stadt.json, wahlen._hinweis)
  const WAHLEN_URL = "data/export/wahlen.json";
  // Beteiligungsverfahren der Bauleitplanung (Stufen und Fristen aus den Bekanntmachungen)
  const BETEILIGUNG_URL = "data/export/beteiligung.json";
  // Gebäude und Eigentum: städtische Gesellschaften (Beteiligungsbericht), ohne Personen
  const EIGENTUM_URL = "data/export/eigentum.json";
  const BRW_URL = "data/export/karte/bodenrichtwerte.json";
  const DEFAULT_AREA = "stadt:alle";
  const RANK = { hoch: 3, mittel: 2, niedrig: 1 };
  const LIST_STEP = 200;
  const MOBILE = matchMedia("(max-width: 900px)");
  const NARROW = matchMedia("(max-width: 1279px)");
  const REDUCED = matchMedia("(prefers-reduced-motion: reduce)").matches;
  // JSON abrufen, null bei Fehler; vergessen() leert dann den Zwischenspeicher, damit das nächste Einschalten neu versucht
  const holen = (url, vergessen) => fetch(url).then((r) => (r.ok ? r.json() : null)).catch(() => null)
    .then((d) => { if (!d) vergessen(); return d; });
  const CONF = { hoch: "Ort gesichert", mittel: "Ort erschlossen", niedrig: "Ort unsicher" };
  // Methoden der Verortung (Stufe A: Gremium, B: Regeln, C: Sprachmodell); Schlüssel wie pipeline/verortung.py
  const METHOD = {
    gremium_ortsbeirat: "Ortsbeirat des Ortsteils (Ortsbezug des Gremiums, nicht zwingend des Gegenstands)",
    gremium_stadtteilbeirat: "Stadtteilbeirat des Ortsteils (Ortsbezug des Gremiums, nicht zwingend des Gegenstands)",
    ortsteil_name: "Ortsteilname im Titel", strasse: "Straßen- oder Lagename im Titel, Lage laut Hauskoordinaten und Lagebezeichnungen (HVBG)", "strasse+ortsteil": "Straßenname im Titel, in mehreren Ortsteilen vorhanden; eingegrenzt über Gremium, Ortsteil, Gemarkung oder eine weitere Straße im Titel",
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
  // Methode, Prüfangaben und Quellen eines Panels: einmal, aufklappbar am Ende; im Lesetext bleiben Wert, Stichtag und Gebiet
  const methode = (teile, titel = "Methode und Quellen") => {
    const t = teile.filter(Boolean);
    return t.length ? `<details class="acc methode"><summary>${titel}</summary>${t.map((x) => (x.startsWith("<") ? x : `<p>${x}</p>`)).join("")}</details>` : "";
  };
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
  const isoTag = (v) => {  // gültiges Datum JJJJ-MM-TT (auch 2025-13-01 oder 2025-02-30 ausschließen)
    const d = ISO_DAY.test(v || "") && new Date(v + "T12:00:00Z");
    return Boolean(d) && !isNaN(d) && d.toISOString().slice(0, 10) === v;
  };
  const fmtDate = (iso) => iso ? new Date(iso.length === 10 ? iso + "T12:00:00Z" : iso)
    .toLocaleDateString("de-DE", { timeZone: "Europe/Berlin", day: "2-digit", month: "2-digit", year: "numeric" }) : "";
  const fmtDay = (iso) => new Date(iso + "T12:00:00Z").toLocaleDateString("de-DE", { weekday: "short", day: "2-digit", month: "2-digit", year: "numeric", timeZone: "Europe/Berlin" });
  const debounce = (fn, ms) => { let h; return (...a) => { clearTimeout(h); h = setTimeout(() => fn(...a), ms); }; };
  const de = (n) => Number(n || 0).toLocaleString("de-DE");
  const get = (obj, path) => path.split(".").reduce((o, k) => (o == null ? o : o[k]), obj);

  let wohnen = null, brwData = null, brwLayer = null, brw26Layer = null, wanderungData = null, wanderungLayer = {}, wanderungJahr = null, wahlen = null, beteiligung = null, eigentum = null;
  let cfg = null, data = null, flaechen = null, zeit = null, all = [], papers = [], area = null, selected = null, dataStand = null;
  let planData = null, planLayer = null, planOn = false, planShown = null, planFolge = 0, planListe = [];
  const umweltOn = new Set(), umweltData = {}, umweltLayers = {};
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
  const SHEETS = ["panel-list", "panel-detail", "panel-auswertung", "panel-termine", "panel-wohnen", "panel-wahlen", "panel-wanderung", "timeline-wrap"];
  const OVERLAYS = ["panel-auswertung", "panel-termine", "panel-wohnen", "panel-wahlen", "panel-wanderung"];
  const toggleFor = (id) => document.querySelector(`.toggle[data-panel="${id}"]`);
  const opener = {};  // Element, das eine Fläche geöffnet hat (für den Fokus beim Schließen)
  function setPanel(id, open) {
    const el = document.getElementById(id);
    if (open && el.hidden && document.activeElement && !el.contains(document.activeElement)) opener[id] = document.activeElement;
    el.hidden = !open;
    document.querySelectorAll(`.toggle[data-panel="${id}"]`).forEach((b) => b.setAttribute("aria-pressed", String(open)));
    if (id === "panel-list") { document.body.classList.toggle("list-open", open); document.body.classList.toggle("list-closed", !open); }
    if (id === "panel-detail") { document.body.classList.toggle("detail-open", open); document.body.classList.toggle("detail-closed", !open); }
    if (id === "timeline-wrap") {  // mobil: Kartenknöpfe über die offene Zeitleiste heben (style.css)
      document.body.classList.toggle("timeline-open", open);
      if (open) requestAnimationFrame(() => document.documentElement.style.setProperty("--tl-h", `${el.offsetHeight}px`));
    }
    if (!open) return;
    el.classList.remove("full");
    const sz = el.querySelector(".sheet-size");
    if (sz) { sz.setAttribute("aria-expanded", "false"); sz.setAttribute("aria-label", "Vergrößern"); }
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
      <button type="button" class="btn btn-cta tour-cta" data-tour><span class="tour-cta-dot" aria-hidden="true"></span>Tour durch alle Funktionen</button>
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
    // Fokus zurück: Schalter der Fläche, sonst das öffnende Element, sonst der Knopf seines (nun geschlossenen) Menüs
    const t = toggleFor(id), o = opener[id], mega = o && o.closest && o.closest(".mega");
    const ziel = [t, o, mega && document.querySelector(`[data-mega="${mega.id}"]`)].find((x) => x && x.isConnected && x.offsetParent);
    if (ziel) ziel.focus();
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
  // Fenstergröße geändert: Breiten auf die neuen Grenzen ziehen (verzögert, nicht bei jedem Zwischenschritt)
  let breiteZeit = 0;
  addEventListener("resize", () => { clearTimeout(breiteZeit); breiteZeit = setTimeout(clampWidths, 150); });
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
      const up = () => {  // beide Endereignisse abmelden, sonst sammeln sich Zuhörer über viele Ziehvorgänge
        r.removeEventListener("pointermove", move); r.removeEventListener("pointerup", up); r.removeEventListener("pointercancel", up);
        r.classList.remove("active"); document.body.classList.remove("resizing"); setWidth(k, widthOf(k), true);
      };
      r.addEventListener("pointermove", move);
      r.addEventListener("pointerup", up);
      r.addEventListener("pointercancel", up);
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
  // mobil: Blätter starten auf halber Höhe; die Schaltfläche im Kopf zeigt sie ganz (auf breiten Bildschirmen ausgeblendet)
  for (const id of SHEETS.filter((x) => x !== "timeline-wrap")) {
    const head = document.querySelector(`#${id} .panel-head`), close = head && head.querySelector("[data-close]");
    if (!close) continue;
    const b = document.createElement("button");
    b.type = "button";
    b.className = "icon-btn sheet-size";
    b.setAttribute("aria-expanded", "false");
    b.setAttribute("aria-label", "Vergrößern");
    b.innerHTML = '<svg class="icon" aria-hidden="true"><use href="#i-chevron"/></svg>';
    b.addEventListener("click", () => {
      const full = document.getElementById(id).classList.toggle("full");
      b.setAttribute("aria-expanded", String(full));
      b.setAttribute("aria-label", full ? "Verkleinern" : "Vergrößern");
    });
    head.insertBefore(b, close);
  }
  $("#about-close").addEventListener("click", () => $("#about").close());
  document.addEventListener("click", (e) => {
    const b = e.target.closest("[data-about]");
    if (!b) return;
    closeMega();
    $("#about").showModal();
    const h = document.getElementById(b.dataset.about);
    if (h) { h.scrollIntoView({ block: "start" }); h.focus(); }
  });
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
    const opt = (o) => `<option value="ortsteil:${esc(o.slug)}">${esc(o.name)}</option>`;  // Zahl der Vorgänge steht in der Liste
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

  // 3D-Ansicht mit dem gewählten Ortsteil (auch für „Link kopieren“ und neuen Tab, daher im Attribut)
  const link3d = () => `3d.html${area && area.kind === "ortsteil" ? `?gebiet=ortsteil:${encodeURIComponent(area.key)}` : ""}`;
  function loadArea(value, keepState) {
    area = parseArea(value);
    $("#f-area").value = `${area.kind}:${area.key}`;
    const a3 = document.querySelector(".map-3d");
    if (a3) a3.href = link3d();
    papers = all.filter(inArea);
    document.title = area.kind === "stadt" ? `${cfg.stadt.titel} – Sitzungsinformationen auf Karte und Zeitleiste`
      : `${cfg.stadt.titel} – Vorgänge ${area.kind === "ohne" ? "ohne Ortsbezug" : "in " + area.name}`;
    $("#f-conf").hidden = area.kind !== "ortsteil";  // wirkt nur innerhalb eines Ortsteils (siehe filtered)
    fillFilters();
    drawOutline();
    selected = null;
    planShown = null;
    shown = LIST_STEP;
    if (!keepState) showIntro();
    if (tl && zeit) { tl.setData(zeit); tl.select(null); }
    if (!$("#panel-termine").hidden) showTermine();
    if (!$("#panel-auswertung").hidden) showStats();
    if (!$("#panel-wohnen").hidden) showWohnen(null);
    if (!$("#panel-wahlen").hidden) showWahlen();
    render();
    syncUrl();
  }

  // --- Karte -----------------------------------------------------------------------------------------
  const MARKER = { radius: 8, weight: 2, color: "#fff", fillOpacity: 0.95 };
  // Farben aus den CSS-Variablen; gemerkt (sonst je Marker eine Stilberechnung), neu gelesen beim Wechsel hell/dunkel
  const farben = new Map();
  const color = (c) => { if (!farben.has(c)) farben.set(c, getComputedStyle(document.documentElement).getPropertyValue("--" + c).trim()); return farben.get(c); };
  matchMedia("(prefers-color-scheme: dark)").addEventListener("change", () => farben.clear());
  let baseLayer = null, colored = false;
  function setBase() {
    // neuer Hintergrund zuerst, dann der alte weg: sonst bestimmt kurz eine Ebene mit Mindestzoom (BORIS 2026) die Zoomstufe;
    // zIndex 0 hält den Hintergrund unter den Bildebenen
    const h = cfg.karte.hintergrund, alt = baseLayer;
    baseLayer = L.tileLayer(colored ? h.farbig : h.grau, { maxZoom: h.max_zoom, attribution: h.attribution, zIndex: 0 }).addTo(map);
    if (alt) alt.remove();
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
    if (cfg.umwelt) {
      const wanted = (new URLSearchParams(location.search).get("ebenen") || "").split(",");
      for (const g of cfg.umwelt.gruppen) if (wanted.includes(g.id)) umweltOn.add(g.id);
      // Bodenrichtwerte 2026 (Kartendienst der HVBG) nicht aus dem Link: Bilder eines fremden Servers erst nach Einschalten
      // (Datenschutzhinweis); alle anderen Ebenen liegen auf dem Server der Seite
      for (const id of ["bodenrichtwerte", ...WANDERUNG_EBENEN.map((e) => e.id)]) if (wanted.includes(id)) umweltOn.add(id);
      const Layers = L.Control.extend({
        options: { position: "bottomright" },
        onAdd() {
          const d = L.DomUtil.create("details", "map-style map-layers");
          const ebenen = [{ id: "bauleitplanung", titel: "Bauleitplanung" }, ...cfg.umwelt.gruppen, ...(cfg.wohnen ? [{ id: "bodenrichtwerte", titel: `Bodenrichtwerte ${cfg.wohnen.boris.stichtag.slice(0, 4)}` }] : []),
            ...(cfg.wohnen?.boris2026 ? [{ id: "bodenrichtwerte2026", titel: "Bodenrichtwerte 2026 (Karte der HVBG)" }] : []),
            ...(cfg.wanderung ? WANDERUNG_EBENEN : [])];
          d.innerHTML = `<summary>Weitere Ebenen</summary><fieldset aria-label="Weitere Kartenebenen einblenden">${ebenen.map((g) =>
            `<label><input type="checkbox" value="${esc(g.id)}"${(g.id === "bauleitplanung" ? planOn : umweltOn.has(g.id)) ? " checked" : ""}> ${esc(g.titel)}</label>`).join("")}</fieldset>`;
          d.addEventListener("change", (e) => {
            const id = e.target.value;
            // Nutzungshinweis (nur nicht kommerziell) sichtbar machen: Legende beim Einschalten aufklappen
            if (id === "bauleitplanung") { planOn = e.target.checked; if (planOn && legendEl) legendEl.open = true; drawPlans(); syncUrl(); return; }
            if (e.target.checked) umweltOn.add(id); else umweltOn.delete(id);
            drawEbene(id);
            syncUrl();
          });
          L.DomEvent.disableClickPropagation(d);
          L.DomEvent.disableScrollPropagation(d);
          return d;
        },
      });
      new Layers().addTo(map);
    }
    new (button("map-whole", `Ganz ${cfg.stadt.name} ansehen`, () => map.fitBounds(cityBounds(), mapPadding())))().addTo(map);
    // 3D-Ansicht (eigene Seite, MapLibre) für das gewählte Gebiet
    if (cfg.gebaeude3d) {
      const Ansicht3d = L.Control.extend({
        options: { position: "bottomright" },
        onAdd() {
          const a = L.DomUtil.create("a", "map-style map-3d");
          a.href = link3d();
          a.textContent = "3D-Ansicht";
          L.DomEvent.disableClickPropagation(a);
          return a;
        },
      });
      new Ansicht3d().addTo(map);
    }
    // die Schaltflächen unten rechts hinter „Kartenoptionen“, damit sie die Karte nicht verdecken (mobil als Kasten über der Leiste)
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
    // Namensnennungen hinter „© Quellen“, aufgeklappt als Kasten
    const Sources = L.Control.extend({
      options: { position: "bottomleft" },
      onAdd() {
        const b = L.DomUtil.create("button", "map-style map-sources");
        b.type = "button";
        b.textContent = "© Quellen";
        b.setAttribute("aria-expanded", "false");
        b.setAttribute("aria-controls", "map-attribution");
        const set = (open) => { map.getContainer().classList.toggle("attr-open", open); b.setAttribute("aria-expanded", String(open)); };
        b.addEventListener("click", () => set(b.getAttribute("aria-expanded") !== "true"));
        map.on("click", () => set(false));
        L.DomEvent.disableClickPropagation(b);
        return b;
      },
    });
    new Sources().addTo(map);
    map.attributionControl.getContainer().id = "map-attribution";
    const Legend = L.Control.extend({
      options: { position: "bottomleft" },
      onAdd() {
        const d = L.DomUtil.create("details", "map-legend");
        d.open = false;
        L.DomEvent.disableClickPropagation(d);
        L.DomEvent.disableScrollPropagation(d);
        return d;
      },
    });
    legendEl = new Legend().addTo(map).getContainer();
    // Pläne auch ohne Maus erreichbar: Auswahl in der Legende
    legendEl.addEventListener("change", (e) => { if (e.target.matches("[data-plan-wahl]") && e.target.value) showPlan(e.target.value); });
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
  // Ortsbezirke als anklickbare Flächen, abgeleitet aus den Gemarkungen (HVBG); Zuordnung mit Prüfstatus
  function initNav() {
    if (!flaechen) return;
    map.createPane("gebiete").style.zIndex = 350;
    navLayer = L.geoJSON(flaechen, {
      pane: "gebiete", attribution: esc(flaechen.attribution || ""),
      style: () => ({ color: color("accent-ink"), weight: 1.5, opacity: 0.85, fillColor: color("accent"), fillOpacity: 0.05 }),
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
    const ebenen = planOn || umweltOn.size;
    legendEl.innerHTML = `<summary>Legende</summary><p class="legend-group">Ort eines Vorgangs</p><ul>${rows
      .map(([c, t]) => `<li><span class="swatch" style="background:${c}" aria-hidden="true"></span>${esc(t)}</li>`).join("")}</ul>
      ${planOn ? `<p class="legend-group">Bauleitplanung</p><ul><li><span class="swatch swatch-plan" aria-hidden="true"></span>Geltungsbereich eines Bebauungsplans</li>
        <li><span class="swatch swatch-fplan" aria-hidden="true"></span>Änderung des Flächennutzungsplans</li></ul>
        ${planListe.length ? `<label class="legend-plan">Plan anzeigen <select data-plan-wahl><option value="">auswählen …</option>${planListe
          .map((p) => `<option value="${esc(p.key)}"${p.key === planShown ? " selected" : ""}>${esc(planName(p))}</option>`).join("")}</select></label>` : ""}
        <p class="hint">${esc(cfg.bauleitplanung.attribution)}.</p>` : ""}
      ${umweltLegend()}${brwLegend()}${brw26Legend()}${wanderungLegend()}
      ${ebenen ? '<p class="hint">Kartenebenen sind nicht rechtsverbindlich; maßgeblich sind die Quellen.</p>' : ""}
      <p><button type="button" class="link-btn" data-about="about-verortung">Mehr zur Verortung</button></p>`;
  }
  // Bodenrichtwerte: Zonen für baureifes Land, Klassen laut stadt.json (wohnen.boris.klassen), Stichtag immer sichtbar
  const BRW_FILL = [0.08, 0.18, 0.3, 0.44, 0.6];
  const brwStichtag = () => fmtDate(cfg.wohnen.boris.stichtag);
  const eur = (v, d = 0) => `${Number(v).toLocaleString("de-DE", { minimumFractionDigits: d, maximumFractionDigits: d })} €/m²`;
  function brwKlassen() {
    const k = cfg.wohnen.boris.klassen;
    return k.map((v, i) => (i === 0 ? `unter ${v}` : `${k[i - 1]} bis unter ${v}`)).concat(`ab ${k[k.length - 1]}`);
  }
  async function drawBrw() {
    if (!umweltOn.has("bodenrichtwerte")) { if (brwLayer) { brwLayer.remove(); brwLayer = null; } if (legendEl) drawLegend(); return; }
    brwData ||= holen(BRW_URL, () => { brwData = null; });
    const d = await brwData;
    if (!umweltOn.has("bodenrichtwerte") || brwLayer || !d) { if (legendEl) drawLegend(); return; }
    brwLayer = L.geoJSON(d, {
      style: (f) => ({ color: color("accent-ink"), weight: 1, opacity: 0.8, fillColor: color("accent-ink"), fillOpacity: BRW_FILL[f.properties.klasse] ?? 0.1 }),
      attribution: esc(cfg.wohnen.boris.attribution),
      onEachFeature: (f, layer) => layer.bindTooltip(`<strong>Bodenrichtwert ${esc(eur(f.properties.wert))}</strong><br>${esc(f.properties.art || "")} · Gemarkung ${esc(f.properties.gemarkung || "")}
        <br><span class="nav-dim">Stichtag ${brwStichtag()}</span>`, { sticky: true }),
    }).addTo(map);
    brwLayer.bringToBack();
    if (legendEl) drawLegend();
  }
  // Bodenrichtwerte 2026: nur als Kartenbild der HVBG (kein Datendienst); eigene Ebene, nicht mit 2024 vermischt
  const drawEbene = (id) => (id === "bodenrichtwerte" ? drawBrw() : id === "bodenrichtwerte2026" ? drawBrw26()
    : id.startsWith("wanderung_") ? drawWanderung(id) : drawUmwelt(id));
  // Beschriftung des Kartendienstes (grauer Kasten, schwarze Schrift, Schatten) im Browser umfärben:
  // Kasten in Textfarbe, Schrift weiß, Schatten entfernt. Der Dienst erlaubt den Abruf von anderen Seiten (CORS).
  const WmsBeschriftung = L.TileLayer.WMS.extend({
    createTile(coords, done) {
      const c = document.createElement("canvas"), s = this.getTileSize();
      c.width = s.x; c.height = s.y;
      const img = new Image();
      img.crossOrigin = "anonymous";
      img.onload = () => {
        const g = c.getContext("2d");
        g.drawImage(img, 0, 0);
        try {
          const d = g.getImageData(0, 0, s.x, s.y), p = d.data;
          for (let i = 0; i < p.length; i += 4) {
            if (!p[i + 3]) continue;
            const l = p[i];  // Graustufen: 150 Kasten, 50 Schatten, 0 bis 150 Schrift mit Kantenglättung
            if (l === 50 && p[i + 1] === 50) { p[i + 3] = 0; continue; }
            const t = Math.max(0, Math.min(1, 1 - l / 150));
            p[i] = p[i + 1] = p[i + 2] = Math.round(26 + (255 - 26) * t);
            p[i + 3] = Math.max(p[i + 3], 235);
          }
          g.putImageData(d, 0, 0);
        } catch (e) { /* ohne CORS bleibt die Darstellung des Dienstes */ }
        done(null, c);
      };
      img.onerror = (e) => done(e, c);
      img.src = this.getTileUrl(coords);
      return c;
    },
  });
  const brw26Zoom = () => { if (legendEl) drawLegend(); };  // Hinweis „näher heranzoomen“ aktuell halten
  function drawBrw26() {
    const B = cfg.wohnen.boris2026;
    if (!umweltOn.has("bodenrichtwerte2026")) { if (brw26Layer) { brw26Layer.remove(); brw26Layer = null; map.off("zoomend", brw26Zoom); } }
    else if (!brw26Layer) {
      const wms = { format: "image/png", transparent: true, version: "1.3.0", minZoom: B.min_zoom };
      brw26Layer = L.layerGroup([L.tileLayer.wms(B.wms, { ...wms, layers: B.layers, opacity: 0.8, attribution: esc(B.attribution) }),
        new WmsBeschriftung(B.wms, { ...wms, layers: B.beschriftung })]).addTo(map);
      map.on("zoomend", brw26Zoom);
    }
    if (legendEl) drawLegend();
  }
  function brw26Legend() {
    if (!brw26Layer) return "";
    const B = cfg.wohnen.boris2026;
    const nah = map.getZoom() >= B.min_zoom;
    return `<p class="legend-group">Bodenrichtwerte, Stichtag ${fmtDate(B.stichtag)}</p>
      ${nah ? "" : '<p class="hint"><strong>Zum Anzeigen näher heranzoomen.</strong></p>'}<p class="hint">${esc(B.hinweis)}</p>`;
  }
  function brwLegend() {
    if (!brwLayer) return "";
    return `<p class="legend-group">Bodenrichtwerte, Stichtag ${brwStichtag()}</p><ul>${brwKlassen().map((t, i) => `<li><span class="swatch swatch-area" aria-hidden="true"
      style="border-color:${color("accent-ink")};background:color-mix(in srgb, ${color("accent-ink")} ${Math.round(BRW_FILL[i] * 100)}%, transparent)"></span>${esc(t)} €/m²</li>`).join("")}</ul>
      <p class="hint">Baureifes Land.</p>`;
  }
  // Umweltebenen: erst beim Einschalten geladen; Flächen ohne Klickziel, nur mit Hinweis beim Überfahren
  const umweltGruppe = (id) => cfg.umwelt.gruppen.find((g) => g.id === id);
  const umweltEbene = (g, id) => g.ebenen.find((e) => e.id === id) || { stil: {} };
  const umweltStyle = (g, e) => ({ color: g.farbe, weight: e.stil.weight || 1.5, opacity: 0.9, dashArray: e.stil.dash || null,
    fill: Boolean(e.stil.fill), fillColor: g.farbe, fillOpacity: e.stil.fill || 0 });
  const loadUmwelt = (id) => (umweltData[id] ||= holen(UMWELT_URL(id), () => { delete umweltData[id]; }));
  async function drawUmwelt(id) {
    const g = umweltGruppe(id);
    if (!g) return;
    if (!umweltOn.has(id)) { if (umweltLayers[id]) { umweltLayers[id].remove(); delete umweltLayers[id]; } if (legendEl) drawLegend(); return; }
    const d = await loadUmwelt(id);
    if (!umweltOn.has(id) || umweltLayers[id] || !d) { if (legendEl) drawLegend(); return; }
    umweltLayers[id] = L.geoJSON(d, {
      // Punkte (etwa Einzeldenkmäler) als kleine Kreise statt der Standardmarke
      pointToLayer: (f, ll) => L.circleMarker(ll),
      style: (f) => ({ ...umweltStyle(g, umweltEbene(g, f.properties.ebene)),
        ...(/Point/.test(f.geometry.type) ? { radius: 4, fill: true, fillOpacity: 0.7 } : {}) }),
      attribution: esc(g.attribution_kurz || d.attribution),
      onEachFeature: (f, layer) => layer.bindTooltip(umweltText(g, f.properties), { sticky: true }),
    }).addTo(map);
    umweltLayers[id].bringToBack();
    if (legendEl) drawLegend();
  }
  const umweltText = (g, p) => `<strong>${esc(umweltEbene(g, p.ebene).titel)}</strong>${p.name ? `<br>${esc(p.name)}` : ""}${p.zone ? `, ${esc(p.zone)}` : ""}
    ${p.status ? `<br>Status: ${esc(p.status)}` : ""}${p.vo_gueltig ? `<br>Verordnung: ${esc(p.vo_gueltig)}` : ""}<br><span class="nav-dim">Nicht rechtsverbindlich</span>`;
  function umweltLegend() {
    if (!cfg.umwelt || !umweltOn.size) return "";
    return cfg.umwelt.gruppen.filter((g) => umweltOn.has(g.id) && umweltData[g.id]).map((g) => {
      const vorhanden = new Set(((umweltLayers[g.id] && umweltLayers[g.id].toGeoJSON().features) || []).map((f) => f.properties.ebene));
      const rows = g.ebenen.filter((e) => vorhanden.has(e.id)).map((e) => `<li><span class="swatch swatch-area" aria-hidden="true"
        style="border-color:${g.farbe};border-style:${e.stil.dash ? (e.stil.dash.startsWith("1 ") || e.stil.dash.startsWith("2 ") ? "dotted" : "dashed") : "solid"};background:${e.stil.fill ? `color-mix(in srgb, ${g.farbe} ${Math.round(e.stil.fill * 100)}%, transparent)` : "transparent"}"></span>${esc(e.titel)}</li>`).join("");
      return `<p class="legend-group">${esc(g.titel)}</p><ul>${rows || "<li>keine Fläche im Stadtgebiet</li>"}</ul>${g.hinweis ? `<p class="hint">${esc(g.hinweis)}</p>` : ""}`;
    }).join("");
  }
  // Kartenebene Bauleitplanung: erst beim Einschalten geladen; Hinweis zur Nutzung in Legende und Namensnennung
  const loadPlans = () => (planData ||= holen(PLAENE_URL, () => { planData = null; }));
  const planStyle = (f) => ({ color: f.properties.art === "fplan" ? color("niedrig") : color("accent-ink"), weight: 1.5,
    dashArray: f.properties.art === "fplan" ? "5 4" : null, fillColor: f.properties.art === "fplan" ? color("niedrig") : color("accent"), fillOpacity: 0.1 });
  async function drawPlans() {
    if (legendEl) drawLegend();
    if (!planOn) { if (planLayer) { planLayer.remove(); planLayer = null; } return; }
    const d = await loadPlans();
    if (!planOn || planLayer || !d) return;
    planListe = d.features.map((f) => f.properties).sort((a, b) => planName(a).localeCompare(planName(b), "de", { numeric: true }));
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
    const nr = ++planFolge;  // eine spätere Auswahl (Vorgang oder anderer Plan) hat Vorrang
    const d = await loadPlans();
    const f = d && d.features.find((x) => x.properties.key === key);
    if (!f || nr !== planFolge) return;
    selected = null;
    planShown = key;
    document.querySelectorAll(".papers button[data-ref]").forEach((b) => b.setAttribute("aria-current", "false"));
    if (tl) tl.select(null);
    highlight();
    const list = all.filter((v) => (v.plans || []).some((p) => p.key === key));
    const docs = (f.properties.dokumente || []).map((u) => link(u, esc(decodeURIComponent(u.split("/").pop())))).filter(Boolean);
    $("#detail-heading").textContent = f.properties.art === "fplan" ? "Flächennutzungsplan" : "Bebauungsplan";
    $("#detail").innerHTML = `<h3 tabindex="-1">${esc(planName(f.properties))}</h3>
      <dl class="facts">${f.properties.gueltig_ab ? `<dt>Rechtskräftig seit</dt><dd>${fmtDate(f.properties.gueltig_ab)}</dd>` : ""}
        ${f.properties.nr ? `<dt>Plannummer</dt><dd>${esc(f.properties.nr)}${f.properties.aenderung ? `, ${f.properties.aenderung}. Änderung` : ""}</dd>` : ""}</dl>
      ${docs.length ? `<h4>Plandokumente der Stadt</h4><ul class="related">${docs.map((x) => `<li>${x}</li>`).join("")}</ul>` : ""}
      ${(() => { const bs = ((beteiligung && beteiligung.verfahren) || []).filter((b) => b.plan.key === key);
        return bs.length ? `<h4>Beteiligung und Verfahrensschritte</h4>${beteiligungHtml(bs)}` : ""; })()}
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
          .bindTooltip(`${esc(p.reference)} · ${esc(l.name)}<br>${CONF[l.confidence] || esc(l.confidence)}`).on("click", () => select(p, true));
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
    fillEinreicher();
  }
  // Einreicher: nur als Angabe und Filter, ohne Zählung je Fraktion (stadt.json, einreicher._hinweis)
  const einreicherListe = () => (cfg.einreicher ? [...cfg.einreicher.fraktionen, cfg.einreicher.einzelperson] : []);
  const einreicherName = (id) => (einreicherListe().find((f) => f.id === id) || { name: id }).name;
  function fillEinreicher() {
    const sel = $("#f-einreicher"), cur = sel.value;
    const da = new Set(all.flatMap((p) => (p.initiative ? p.initiative.einreicher : [])));
    const opts = einreicherListe().filter((f) => da.has(f.id));
    sel.innerHTML = '<option value="">alle</option>' + opts.map((f) => `<option value="${esc(f.id)}">${esc(f.name)}</option>`).join("");
    if (opts.some((f) => f.id === cur)) sel.value = cur;
  }
  function initiativeText(i) {
    const namen = i.einreicher.map(einreicherName);
    const wer = i.einreicher[0] === cfg.einreicher.einzelperson.id ? namen[0]
      : `${namen.length > 1 ? "Fraktionen" : "Fraktion"} ${namen.join(", ")}`;
    return `${esc(i.typ)} ${i.einreicher[0] === cfg.einreicher.einzelperson.id ? "von" : "der"} ${esc(wer)} vom ${fmtDate(i.datum)}`;
  }
  function inRange(p) {
    if (!range) return true;
    const [a, b] = range, dim = tl ? tl.dimension() : "vorlage";
    if (dim === "vorlage") return p.date >= a && p.date <= b;
    return p.process.some((s) => s.date && s.date >= a && s.date <= b);
  }
  function filtered(withRange = true) {
    const text = $("#f-text").value.trim().toLowerCase(), gremium = $("#f-gremium").value, art = $("#f-art").value;
    const proc = $("#f-verfahren").checked, einr = $("#f-einreicher").value;
    const confs = new Set([...document.querySelectorAll("#f-conf input:checked")].map((i) => i.value));
    return papers.filter((p) => (proc || !p.verfahrenspunkt) && (!gremium || p.process.some((s) => s.gremium === gremium)) &&
      (!art || (art === "vorlage") === Boolean(p.vorlage)) && (!einr || (p.initiative && p.initiative.einreicher.includes(einr))) &&
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
    const active = [$("#f-verfahren").checked, $("#f-einreicher").value].filter(Boolean).length + (area.kind === "ortsteil" ? document.querySelectorAll("#f-conf input:not(:checked)").length : 0);
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
  function legendInhalt() {
    return `<div class="legend">${["belegt", "abgeleitet", "nicht_öffentlich", "unklar"]
      .map((s) => `<span><span class="mark mark-${s}" aria-hidden="true">${s === "unklar" ? "?" : ""}</span><strong>${STATUS[s]}</strong> – ${STATUS_TEXT[s]}</span>`).join("")}
      <span class="hint">Linie: durchgezogen = belegt, gestrichelt = abgeleitet, gepunktet = nicht öffentlich oder unklar.</span></div>`;
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
    const ausListe = $("#panel-list").contains(document.activeElement);
    selected = p;
    planShown = null;
    planFolge++;  // noch ladende Plananzeige verwerfen
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
        ${p.initiative && cfg.einreicher ? `<dt>Eingebracht</dt><dd>${initiativeText(p.initiative)} <span class="derived">laut TOP-Titel</span></dd>` : ""}
      </dl>
      <div class="links">${link(p.process[0] && p.process[0].pdf, "Einladung (PDF)", "btn btn-primary")}
        ${link(cfg.stadt.sessionnet, "Bürgerinformationssystem", "btn btn-secondary")}</div>
      <h4>Prozesslinie</h4>
      <ol class="steps">${p.process.map(stepHtml).join("")}</ol>
      ${(p.beteiligung || []).length ? `<h4>Beteiligung der Öffentlichkeit (Bauleitplanung)</h4>${beteiligungHtml(p.beteiligung)}` : ""}
      <h4>Ortsbezug</h4><ul class="locs">${locs}</ul>
      ${(p.plans || []).length ? `<h4>Bauleitplanung</h4><ul class="locs">${p.plans.map((x) => `<li><button type="button" class="link-btn" data-open-plan="${esc(x.key)}">${esc(x.titel)}</button>
        <br><span class="meta">${esc(x.treffer)} · Fundstelle: „${esc(x.evidence)}“</span></li>`).join("")}</ul>` : ""}
      ${wohnenKasten(p)}
      ${(p.overlaps || []).length && cfg.umwelt ? `<h4>Räumliche Überschneidung</h4><ul class="locs">${p.overlaps.map((u) => `<li>${esc(u.titel)}${u.name ? `: ${esc(u.name)}` : ""}${u.zone ? `, ${esc(u.zone)}` : ""}
        <br><span class="meta">Ort: ${esc(u.ort)}</span></li>`).join("")}</ul>
        <p class="hint">${esc(cfg.umwelt.ueberschneidung_hinweis)}</p>` : ""}
      ${(p.bezuege || []).length ? `<p class="hint">Im Titel genannt: ${p.bezuege.map(esc).join(", ")} <span class="derived">Verweis, nicht verknüpft</span></p>` : ""}
      <p class="links">${link(reportLink(p), "Verortung falsch? Hinweis geben", "btn btn-secondary")}</p>
      ${methode([p.vorlage ? `Stationen der Prozesslinie sind die Sitzungen, in deren Tagesordnung die Vorlage ${esc(p.vorlage)} steht, chronologisch.`
          : "Ohne Vorlagennummer: eine einzelne Station. Tagesordnungspunkte werden nicht über ähnliche Titel verknüpft.",
        legendInhalt(),
        (p.beteiligung || []).length ? "Beteiligung: Verfahrensschritte laut amtlichen Bekanntmachungen zu diesem Plan; zugeordnet über Plannummer und Gemarkung." : "",
        (p.plans || []).length ? `${esc(cfg.bauleitplanung.attribution)}.` : "",
        (p.overlaps || []).length && cfg.umwelt ? esc(cfg.umwelt.hinweis) : "",
        `<ul>${p.process.map((s) => `<li>${link(s.pdf, `Bekanntmachung Nr. ${esc(s.bekanntmachung)}`) || esc(s.bekanntmachung)} · ${esc(s.gremium)}, ${fmtDate(s.date)}, TOP ${esc(s.top)}</li>`).join("")}
        ${sources}</ul>`])}
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
      // schmal oder mittlere Breite: die Liste schließt sich, der Fokus folgt in den Vorgang
      if (MOBILE.matches || (ausListe && $("#panel-list").hidden)) $("#detail h3").focus();
    }
  }
  $("#detail").addEventListener("click", (e) => {
    const ow = e.target.closest("[data-open-wohnen]");
    if (ow) { setPanel("panel-wohnen", true); showWohnen(ow.dataset.openWohnen); focusPanel("panel-wohnen"); return; }
    const pl = e.target.closest("[data-open-plan]");
    if (pl) { if (!planOn) { planOn = true; const cb = document.querySelector('.map-layers input[value="bauleitplanung"]'); if (cb) cb.checked = true; drawPlans(); } showPlan(pl.dataset.openPlan); return; }
    const r = e.target.closest("[data-open-ref]");
    if (r) { const v = all.find((x) => x.reference === r.dataset.openRef); if (v) { if (!papers.includes(v)) loadArea(DEFAULT_AREA, true); select(v); } return; }
    const b = e.target.closest(".jump");
    if (b && tl) { if ($("#timeline-wrap").hidden) setPanel("timeline-wrap", true); tl.center(b.dataset.date); }
  });

  // --- Termine: kommende Sitzungen -------------------------------------------------------------------
  // --- Beteiligung: Stufen mit Frist; laufend, solange das Fristende nicht überschritten ist ---------------
  const heute = () => new Date().toLocaleDateString("sv-SE", { timeZone: "Europe/Berlin" });
  const laeuft = (st) => st.bis && st.bis >= heute();
  function stufeHtml(st) {
    const frist = st.von ? `${fmtDate(st.von)} bis ${fmtDate(st.bis)}` : st.beschluss ? `Beschluss vom ${fmtDate(st.beschluss)}` : "";
    return `<li>${esc(st.titel)}${frist ? ` · ${frist}` : ""}${laeuft(st) ? ' <span class="badge badge-live">läuft</span>' : ""}</li>`;
  }
  function beteiligungHtml(schritte) {
    return `<ol class="beteiligung">${schritte.map((b) => `<li><span class="meta">${fmtDate(b.veroeffentlicht)} · ${link(b.pdf, `Bekanntmachung Nr. ${esc(b.nr)} (PDF)`)}</span>
      <ul>${b.stufen.map(stufeHtml).join("")}</ul></li>`).join("")}</ol>`;
  }
  const planLabel = (pl) => `${pl.art === "fplan" ? `${pl.aenderung}. Änderung des Flächennutzungsplans` : `${pl.aenderung ? `${pl.aenderung}. Änderung des ` : ""}Bebauungsplan${pl.aenderung ? "s" : ""} Nr. ${pl.nr}`}${pl.name ? ` „${pl.name}“` : ""}`;
  function laufendeBeteiligung() {
    const liste = ((beteiligung && beteiligung.verfahren) || []).filter((b) => b.stufen.some(laeuft) &&
      (area.kind !== "ortsteil" || !b.plan.ortsteil || b.plan.ortsteil === area.name));
    if (!liste.length) return "";
    return `<section class="stat-block beteiligung-live"><h3>Laufende Beteiligung der Öffentlichkeit</h3><ul class="locs">${liste.map((b) => {
      const st = b.stufen.find(laeuft);
      return `<li><strong>${esc(planLabel(b.plan))}</strong>${b.plan.ortsteil ? `, ${esc(b.plan.ortsteil)}` : ""}<br>${esc(st.titel)}: ${fmtDate(st.von)} bis ${fmtDate(st.bis)}
        <br>${link(b.pdf, `Bekanntmachung Nr. ${esc(b.nr)} (PDF)`)}${beteiligung.seite ? ` · ${link(beteiligung.seite, "Planunterlagen der Stadt")}` : ""}</li>`;
    }).join("")}</ul><p class="hint">Stellungnahmen sind innerhalb der Frist bei der Stadt möglich; Einzelheiten in der Bekanntmachung.</p></section>`;
  }
  function showTermine() {
    const box = $("#termine");
    const scope = box.querySelector("#termine-scope") ? box.querySelector("#termine-scope").value : "gebiet";
    const today = heute();  // Datum in Berlin, nicht in UTC (sonst fehlt kurz nach Mitternacht die Sitzung des Tages)
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
    box.innerHTML = `${laufendeBeteiligung()}<p class="hint">Sitzungen laut Einladungen in den amtlichen Bekanntmachungen. Sie sind in der Regel öffentlich; die Einladung erscheint etwa ein bis zwei Wochen vorher.</p>
      <div class="filters termine-filters"><label>Gremien
        <select id="termine-scope"><option value="gebiet"${scope === "gebiet" ? " selected" : ""}>${area.kind === "ortsteil" ? `stadtweite Gremien und ${esc(area.name)}` : "alle Gremien"}</option>
        <option value="alle"${scope === "alle" ? " selected" : ""}>alle Gremien</option></select></label></div>
      <p class="count">${list.length} kommende Sitzungen</p>
      ${items || "<p>Keine kommenden Sitzungen im Datenbestand.</p>"}`;
    box.querySelector("#termine-scope").addEventListener("change", () => { showTermine(); $("#termine-scope").focus(); });
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
  // --- Wahlen und Gremien: amtliche Ergebnisse mit Ergebnisstufe und Quelle; fehlende Wahlen als Lücke -----------
  const STUFE = { "endgültig": "endgültig", schnellmeldung: "Schnellmeldung", luecke: "Lücke" };
  const pct = (v) => `${num(v, 2)} %`;
  function kommunalTabelle(r, caption) {
    const rows = [...r.vorschlaege].sort((a, b) => b.stimmen - a.stimmen);
    return `<div class="table-wrap"><table class="compare"><caption class="visually-hidden">${esc(caption)}</caption>
      <thead><tr><th scope="col">Wahlvorschlag</th><th scope="col">Stimmen&shy;anteil</th><th scope="col">Sitze</th></tr></thead>
      <tbody>${rows.map((v) => `<tr><th scope="row">${esc(v.name)}</th><td>${pct(v.anteil)}</td><td>${esc(v.sitze)}</td></tr>`).join("")}
      <tr class="own"><th scope="row">zusammen</th><td></td><td>${esc(r.sitze)}</td></tr></tbody></table></div>`;
  }
  function wahlKopf(e) {
    const s = e.stufe === "endgültig" ? "" : ` <span class="derived">${esc(STUFE[e.stufe] || e.stufe)}</span>`;
    return `<h4>${esc(e.titel)} ${fmtDate(e.datum)}${s}</h4>`;
  }
  function bundTabelle(liste) {
    const da = liste.filter((b) => b.ergebnis);
    if (!da.length) return "";
    const key = (n) => n.toUpperCase();
    const anteil = (b, k) => { const e = Object.entries(b.ergebnis.parteien).find(([n]) => key(n) === k); return e ? 100 * e[1] / b.ergebnis.gueltig : 0; };
    const namen = new Map();
    for (const b of [...da].reverse()) for (const n of Object.keys(b.ergebnis.parteien)) namen.set(key(n), n);
    const zeilen = [...namen.keys()].filter((k) => da.some((b) => anteil(b, k) >= 2)).sort((a, b) => anteil(da[0], b) - anteil(da[0], a));
    const sonst = (b) => 100 - zeilen.reduce((s, k) => s + anteil(b, k), 0);
    return `<div class="table-wrap"><table class="compare"><caption class="visually-hidden">Zweitstimmen bzw. Stimmen in Prozent je Wahl</caption>
      <thead><tr><th scope="col">Partei</th>${da.map((b) => `<th scope="col">${esc(b.titel === "Bundestagswahl" ? "BTW" : "EW")} ${b.datum.slice(0, 4)}</th>`).join("")}</tr></thead>
      <tbody>${zeilen.map((k) => `<tr><th scope="row">${esc(namen.get(k))}</th>${da.map((b) => `<td>${anteil(b, k) ? num(anteil(b, k), 1) : "–"}</td>`).join("")}</tr>`).join("")}
      <tr><th scope="row">Sonstige</th>${da.map((b) => `<td>${num(sonst(b), 1)}</td>`).join("")}</tr>
      <tr class="own"><th scope="row">Wahlbeteiligung</th>${da.map((b) => `<td>${num(b.ergebnis.beteiligung, 1)}</td>`).join("")}</tr></tbody></table></div>`;
  }
  function showWahlen() {
    const box = $("#wahlen");
    const W = cfg.wahlen;
    if (!W || !wahlen) { box.innerHTML = '<p class="hint">Noch keine Wahldaten.</p>'; return; }
    const stvv = wahlen.kommunal.filter((e) => e.art === "stvv");
    const ob = wahlen.kommunal.find((e) => e.art === "ortsbeirat");
    const slug = area.kind === "ortsteil" ? area.key : null;
    const obListe = ob && ob.ergebnisse ? (slug ? ob.ergebnisse.filter((r) => r.ortsteil === slug) : ob.ergebnisse) : [];
    const obName = (r) => (cfg.ortsteile.find((o) => o.slug === r.ortsteil) || { name: r.gebiet }).name;
    box.innerHTML = `<p class="hint">Nur amtliche Ergebnisse, ohne Namen von Personen.</p>
      <section class="stat-block"><h3>Stadtverordnetenversammlung</h3>
        ${stvv.map((e) => `${wahlKopf(e)}
          ${e.ergebnisse ? `${kommunalTabelle(e.ergebnisse[0], `${e.titel} ${fmtDate(e.datum)}: Stimmenanteile und Sitze`)}
            <p class="hint">Wahlbeteiligung ${num(e.ergebnisse[0].beteiligung, 2)} %.</p>`
            : `<p class="blackbox">${esc(e.stufe_text)}.</p>`}`).join("")}</section>
      ${ob ? `<section class="stat-block"><h3>Ortsbeiräte</h3>${wahlKopf(ob)}
        ${obListe.length ? `<div class="table-wrap"><table class="compare"><caption class="visually-hidden">Ortsbeiratswahlen ${fmtDate(ob.datum)}: Sitze je Wahlvorschlag und Wahlbeteiligung</caption>
          <thead><tr><th scope="col">Ortsbezirk</th><th scope="col">Wahlvorschläge (Sitze)</th><th scope="col">Beteiligung</th></tr></thead>
          <tbody>${obListe.map((r) => `<tr><th scope="row">${esc(obName(r))}</th><td class="text">${[...r.vorschlaege].sort((a, b) => b.sitze - a.sitze).map((v) => `${esc(v.name)} (${v.sitze})`).join("; ")}</td><td>${pct(r.beteiligung)}</td></tr>`).join("")}</tbody></table></div>`
          : '<p>Für dieses Gebiet gibt es keinen Ortsbeirat.</p>'}
        </section>` : ""}
      <section class="stat-block"><h3>Bundestags- und Europawahlen in ${esc(cfg.stadt.name)}</h3>
        <p class="hint">Bundestagswahl: Zweitstimmen; Europawahl: Stimmen; in Prozent der gültigen Stimmen.</p>
        ${bundTabelle(wahlen.bund)}</section>
      ${methode([`Namen von Kandidierenden und Gewählten werden nicht übernommen; maßgeblich sind die verlinkten Quellen. ${esc(W.gremien_hinweis)}`,
        `<ul>${[...stvv, ...(ob ? [ob] : [])].map((e) => `<li>${esc(e.titel)} ${fmtDate(e.datum)}: ${esc(e.stufe_text)}${e.quelle_url ? ` · ${link(e.quelle_url, "Quelle")}` : ""}</li>`).join("")}</ul>`,
        `${esc(W.bund_hinweis)} ${esc(wahlen.bund_attribution)}.`])}`;
  }

  // --- Wohnen und Boden: Kennzahlen mit Stichtag und Quelle; Bestands-, Angebots- und Vergleichsmiete getrennt ------
  const num = (v, d) => Number(v).toLocaleString("de-DE", { minimumFractionDigits: d, maximumFractionDigits: d });
  const slugOf = (name) => (cfg.ortsteile.find((o) => o.name === name) || {}).slug;
  let wohnenGebiet = null;  // Ortsteil-Slug, wenn das Panel aus einem Vorgang heraus geöffnet wurde
  function zensusWert(e, d, einheit) {
    if (!e) return "–";
    if (e.wert == null) return `nicht ausgewiesen <span class="meta">(${esc(e.grund || "keine Zelle mit Wert")})</span>`;
    return `${num(e.wert, d)} ${einheit} <span class="derived">Näherung</span>`;
  }
  function showWohnen(slug) {
    const box = $("#wohnen");
    const W = cfg.wohnen;
    if (!W || !wohnen) { box.innerHTML = '<p class="hint">Noch keine Daten zu Wohnen und Boden.</p>'; return; }
    if (slug !== undefined) wohnenGebiet = slug;
    const key = wohnenGebiet || (area.kind === "ortsteil" ? area.key : null);
    const o = key && cfg.ortsteile.find((x) => x.slug === key);
    const name = o ? o.name : cfg.stadt.name;
    const sp = wohnen.boris.spannen[key || "stadt"];
    const z = wohnen.zensus;
    const gem = z && z.gemeinden.find((g) => g.ars === cfg.stadt.ars);
    const ob = key && z && z.ortsbezirke[key];
    const eing = (g, k) => (g.eingeschraenkt || []).includes(k);
    const zelle = (g, k, d) => (g[k] == null ? "–" : eing(g, k) ? `(${num(g[k], d)})` : num(g[k], d));
    box.innerHTML = `<p class="hint">Gebiet: <strong>${esc(name)}</strong>${o ? ` (Gemarkung ${esc(o.gemarkung)})` : ""}. Die Werte beschreiben den Ort, nicht einzelne Vorgänge.</p>
      <section class="stat-block"><h3>Bodenrichtwerte</h3>
        <p class="stichtag">Stichtag ${brwStichtag()}</p>
        ${sp ? `<dl class="facts"><dt>Spanne</dt><dd>${num(sp.min, 0)} bis ${num(sp.max, 0)} €/m²</dd><dt>Zonen</dt><dd>${de(sp.zonen)} (${esc(sp.arten.join(", "))})</dd></dl>`
          : "<p>Keine Bodenrichtwertzone für baureifes Wohn- oder Mischbauland.</p>"}
        <p><button type="button" class="btn btn-soft" data-brw-on>Zonen auf der Karte zeigen</button></p></section>
      <section class="stat-block"><h3>Bestandsmiete und Eigentum (Zensus 2022)</h3>
        <p class="stichtag">Stichtag ${fmtDate(z.stichtag)}</p>
        ${o ? `<dl class="facts"><dt>Bestandsmiete ${esc(o.name)}</dt><dd>${zensusWert(ob && ob.miete, 2, "€/m²")}</dd>
          <dt>Eigentümerquote ${esc(o.name)}</dt><dd>${zensusWert(ob && ob.eigentuemerquote, 1, "%")}</dd></dl>` : ""}
        ${gem ? `<dl class="facts"><dt>Bestandsmiete ${esc(cfg.stadt.name)}</dt><dd>${num(gem.nettokaltmiete_eur_m2, 2)} €/m²</dd>
          <dt>Leerstandsquote</dt><dd>${num(gem.leerstandsquote_pct, 1)} %</dd><dt>Eigentümerquote</dt><dd>${num(gem.eigentuemerquote_pct, 1)} %</dd></dl>` : ""}
        <p class="hint">Angebotsmieten und eine ortsübliche Vergleichsmiete stehen hier nicht: siehe Begriffe.</p></section>
      ${z.gemeinden.length ? `<section class="stat-block"><h3>Vergleich mit Nachbargemeinden (Zensus 2022)</h3>
        <div class="table-wrap"><table class="compare"><caption class="visually-hidden">Bestandsmiete, Leerstands- und Eigentümerquote je Gemeinde, Stichtag 15.05.2022</caption>
        <thead><tr><th scope="col">Gemeinde</th><th scope="col">Bestands&shy;miete €/m²</th><th scope="col">Leer&shy;stand %</th><th scope="col">Eigen&shy;tümer %</th></tr></thead>
        <tbody>${z.gemeinden.map((g) => `<tr${g.ars === cfg.stadt.ars ? ' class="own"' : ""}><th scope="row">${esc(g.name)}</th><td>${zelle(g, "nettokaltmiete_eur_m2", 2)}</td>
          <td>${zelle(g, "leerstandsquote_pct", 1)}</td><td>${zelle(g, "eigentuemerquote_pct", 1)}</td></tr>`).join("")}</tbody></table></div>
        <p class="hint">Werte in Klammern: Aussagewert eingeschränkt. Gemeinden in Hessen, Niedersachsen und Thüringen.</p></section>` : ""}
      <section class="stat-block"><h3>Rechtlicher Rahmen</h3><ul class="locs">${W.kontext.map((k) => `<li><strong>${esc(k.thema)}:</strong> ${esc(k.aussage)}
        <br><span class="meta">Stand: ${esc(k.stand)}${k.link ? ` · ${link(k.link, "Quelle")}` : ""}</span></li>`).join("")}</ul></section>
      <section class="stat-block"><h3>Begriffe</h3><dl class="glossar">${W.begriffe.map((b) => `<dt>${esc(b.begriff)}</dt><dd>${esc(b.text)}</dd>`).join("")}</dl></section>
      <section class="stat-block"><h3>Immobilienmarktberichte</h3><ul class="locs">${W.berichte.map((b) => `<li>${link(b.link, esc(b.titel)) || esc(b.titel)}<br><span class="meta">${esc(b.herausgeber)}</span></li>`).join("")}</ul>
        <p class="hint">${esc(W.berichte_hinweis)}</p></section>
      ${eigentumHtml()}
      ${methode([`<strong>Bodenrichtwerte:</strong> ${esc(W.boris.filter)}. ${esc(W.boris.stichtag_hinweis)} ${esc(W.boris.attribution)}.`,
        `<strong>Zensus:</strong> ${esc(z.naeherung)} Gemeindewerte aus der Regionaltabelle Gebäude und Wohnungen des Zensus 2022. ${esc(z.attribution)}.`,
        eigentum ? `<p><strong>Gebäude und Eigentum:</strong> ${link(eigentum.bericht.url, `Beteiligungsbericht ${esc(String(eigentum.bericht.jahr))}`)}, ${esc(eigentum.bericht.stand)}. Personen (Geschäftsführung, Aufsichtsrat) werden nicht übernommen.</p><ul>${eigentum.grenzen.map((t) => `<li>${esc(t)}</li>`).join("")}</ul>` : ""])}`;
  }
  function eigentumHtml() {
    if (!eigentum) return "";
    const zeile = (g) => `<tr><th scope="row">${esc(g.name)}${g.gegenstand ? `<br><span class="meta">${esc(g.gegenstand)}</span>` : ""}</th>
      <td class="text">${esc(g.rechtsform || "–")}</td><td class="text">${esc(g.gesellschafter || "–")}</td></tr>`;
    const tab = (liste, cap) => `<div class="table-wrap"><table class="compare"><caption class="visually-hidden">${esc(cap)}</caption>
      <thead><tr><th scope="col">Unternehmen</th><th scope="col">Rechtsform</th><th scope="col">Gesellschafter laut Bericht</th></tr></thead>
      <tbody>${liste.map(zeile).join("")}</tbody></table></div>`;
    const pf = eigentum.gesellschaften.filter((g) => g.pflicht), fr = eigentum.gesellschaften.filter((g) => !g.pflicht);
    return `<section class="stat-block"><h3>Gebäude und Eigentum</h3>
      <p><button type="button" class="btn btn-soft" data-ebene-on="gebaeude">Gebäude für öffentliche Zwecke auf der Karte</button></p>
      <p class="hint">Gebäudefunktion laut Liegenschaftskataster; sie beschreibt die Nutzung, nicht das Eigentum.</p>
      ${pf.length ? `<h4>Beteiligungen und Eigenbetriebe der Stadt (Pflichtangaben, § 123a HGO)</h4>${tab(pf, "Beteiligungen und Eigenbetriebe")}` : ""}
      ${fr.length ? `<details class="acc"><summary>Weitere Beteiligungen (freiwillige Angaben, ${fr.length})</summary>${tab(fr, "Weitere Beteiligungen")}</details>` : ""}
      </section>`;
  }
  // --- Zuzug und Wegzug (amtliche Wanderungsstatistik, HSL) --------------------------------------------
  // Je Gemeinde nur Zu- und Fortzüge über die Gemeindegrenze; Herkunft und Ziel nur je Kreis. Keine Schätzung je Ortsteil.
  const WANDERUNG_EBENEN = [{ id: "wanderung_gemeinden", titel: "Wanderungssaldo der Gemeinden im Kreis" },
    { id: "wanderung_kreise", titel: "Wanderung über die Kreisgrenze" }];
  const loadWanderung = () => (wanderungData ||= holen(WANDERUNG_URL, () => { wanderungData = null; }));
  const mittel = (j) => (j.bev_anfang + j.bev_ende) / 2;
  const saldo = (j) => j.zuzuege - j.fortzuege;
  const rate = (j) => (saldo(j) / mittel(j)) * 1000;
  const vz = (v, d = 0) => `${v > 0 ? "+" : v < 0 ? "−" : ""}${num(Math.abs(v), d)}`;
  const wJahre = (d) => Object.keys(d.gemeinden[cfg.stadt.gemeindeschluessel]?.jahre || {}).sort();
  function saldoKlasse(r) { const k = cfg.wanderung.klassen; let i = 0; while (i < k.length && r >= k[i]) i++; return i; }
  const SALDO_FARBE = (i) => (i < 3 ? color("abzug") : color("accent-ink"));
  const SALDO_DECK = [0.6, 0.38, 0.16, 0.16, 0.38, 0.6];
  function saldoKlassenText() {
    const k = cfg.wanderung.klassen, f = (v) => vz(v);
    return [`unter ${f(k[0])}`, ...k.slice(1).map((v, i) => `${f(k[i])} bis unter ${f(v)}`), `${f(k[k.length - 1])} und mehr`];
  }
  function zeitreiheSvg(reihe) {
    const W = 560, H = 190, l = 44, r = 8, t = 10, b = 26, max = Math.max(...reihe.flatMap(([, j]) => [j.zuzuege, j.fortzuege])) * 1.08;
    const x = (i) => l + ((W - l - r) / reihe.length) * (i + 0.5), bw = ((W - l - r) / reihe.length) * 0.36;
    const y = (v) => t + (H - t - b) * (1 - v / max);
    const ticks = [0, 250, 500, 750, 1000, 1250].filter((v) => v <= max);
    return `<svg class="chart" viewBox="0 0 ${W} ${H}" role="img" aria-labelledby="wz-titel"><title id="wz-titel">Zu- und Fortzüge ${esc(cfg.stadt.name)} ${reihe[0][0]} bis ${reihe[reihe.length - 1][0]}; Werte in der Tabelle darunter</title>
      ${ticks.map((v) => `<line x1="${l}" x2="${W - r}" y1="${y(v)}" y2="${y(v)}" class="grid"/><text x="${l - 6}" y="${y(v) + 4}" text-anchor="end">${de(v)}</text>`).join("")}
      ${reihe.map(([jahr, j], i) => `<rect x="${x(i) - bw}" y="${y(j.zuzuege)}" width="${bw}" height="${y(0) - y(j.zuzuege)}" fill="${color("accent-ink")}"/>
        <rect x="${x(i)}" y="${y(j.fortzuege)}" width="${bw}" height="${y(0) - y(j.fortzuege)}" fill="${color("abzug")}"/>
        <text x="${x(i)}" y="${H - 8}" text-anchor="middle">${esc(jahr)}</text>`).join("")}</svg>`;
  }
  async function showWanderung() {
    const box = $("#wanderung");
    const d = cfg.wanderung && await loadWanderung();
    if (!d) { box.innerHTML = '<p class="hint">Noch keine Daten zu Zuzug und Wegzug.</p>'; return; }
    const W = cfg.wanderung, jahre = wJahre(d), g = d.gemeinden[cfg.stadt.gemeindeschluessel];
    wanderungJahr ||= jahre[jahre.length - 1];
    const reihe = jahre.map((y) => [y, g.jahre[y]]);
    const lj = g.jahre[jahre[jahre.length - 1]];
    const gem = Object.entries(d.gemeinden).map(([ags, x]) => ({ ags, name: wName(d, ags, x.name), j: x.jahre[wanderungJahr] })).filter((x) => x.j)
      .sort((a, b) => rate(b.j) - rate(a.j));
    const k = d.kreis;
    const balken = (t, zu, fort) => { const m = Math.max(zu || 0, fort || 0, 1); return `<tr><th scope="row">${esc(t)}</th>
      <td><span class="bar bar-zu" style="width:${(100 * (zu || 0)) / m}%"></span>${zu == null ? "•" : de(zu)}</td>
      <td><span class="bar bar-fort" style="width:${(100 * (fort || 0)) / m}%"></span>${fort == null ? "•" : de(fort)}</td><td>${zu == null || fort == null ? "•" : vz(zu - fort)}</td></tr>`; };
    const kreiseTop = k ? Object.keys(W.kreise).filter((n) => n !== W.kreis_name)
      .map((n) => ({ n, zu: k.zuzuege[n], fort: k.fortzuege[n] })).sort((a, b) => ((b.zu || 0) + (b.fort || 0)) - ((a.zu || 0) + (a.fort || 0))) : [];
    box.innerHTML = `<p class="hint">Zu- und Fortzüge über die Gemeindegrenze (amtliche Statistik); Zahlen je Ortsteil sind nicht veröffentlicht.</p>
      <section class="stat-block"><h3>${esc(cfg.stadt.name)} ${jahre[0]} bis ${jahre[jahre.length - 1]}</h3>
        <dl class="facts"><dt>Zuzüge ${jahre[jahre.length - 1]}</dt><dd>${de(lj.zuzuege)}</dd><dt>Fortzüge</dt><dd>${de(lj.fortzuege)}</dd>
          <dt>Wanderungssaldo</dt><dd>${vz(saldo(lj))}</dd><dt>je 1 000 Einwohner</dt><dd>${vz(rate(lj), 1)}</dd>
          <dt>Geburten minus Sterbefälle</dt><dd>${vz(lj.geborene - lj.gestorbene)}</dd></dl>
        ${zeitreiheSvg(reihe)}
        <p class="chart-key"><span class="swatch" style="background:${color("accent-ink")}" aria-hidden="true"></span>Zuzüge <span class="swatch" style="background:${color("abzug")}" aria-hidden="true"></span>Fortzüge</p>
        <details class="acc"><summary>Tabelle ${jahre[0]} bis ${jahre[jahre.length - 1]}</summary><div class="table-wrap"><table class="compare">
          <caption class="visually-hidden">Zu- und Fortzüge, Saldo und natürliche Bilanz je Jahr</caption>
          <thead><tr><th scope="col">Jahr</th><th scope="col">Zuzüge</th><th scope="col">Fortzüge</th><th scope="col">Saldo</th><th scope="col">je 1 000</th><th scope="col">Geburten − Sterbefälle</th></tr></thead>
          <tbody>${reihe.map(([y, j]) => `<tr><th scope="row">${esc(y)}</th><td>${de(j.zuzuege)}</td><td>${de(j.fortzuege)}</td><td>${vz(saldo(j))}</td><td>${vz(rate(j), 1)}</td><td>${vz(j.geborene - j.gestorbene)}</td></tr>`).join("")}</tbody></table></div></details></section>
      <section class="stat-block"><h3>Gemeinden im ${esc(W.kreis_name)}</h3>
        <label class="inline">Jahr <select id="wanderung-jahr">${jahre.map((y) => `<option${y === wanderungJahr ? " selected" : ""}>${esc(y)}</option>`).join("")}</select></label>
        <p><button type="button" class="btn btn-soft" data-wanderung-on="wanderung_gemeinden">Saldo auf der Karte zeigen</button></p>
        <div class="table-wrap"><table class="compare"><caption class="visually-hidden">Wanderungssaldo je 1 000 Einwohner der Gemeinden im Kreis, ${esc(wanderungJahr)}</caption>
          <thead><tr><th scope="col">Gemeinde</th><th scope="col">Zuzüge</th><th scope="col">Fortzüge</th><th scope="col">Saldo je 1 000</th></tr></thead>
          <tbody>${gem.map((x) => `<tr${x.ags === cfg.stadt.gemeindeschluessel ? ' class="own"' : ""}><th scope="row">${esc(x.name)}</th><td>${de(x.j.zuzuege)}</td><td>${de(x.j.fortzuege)}</td><td>${vz(rate(x.j), 1)}</td></tr>`).join("")}</tbody></table></div>
        <p class="hint">In kleinen Gemeinden schwankt der Saldo von Jahr zu Jahr stark.</p></section>
      ${k ? `<section class="stat-block"><h3>Über die Kreisgrenze (${esc(W.kreis_name)}, ${k.jahr})</h3>
        <p class="hint">Diese Zahlen gelten für den ganzen Kreis, nicht für ${esc(cfg.stadt.name)} allein.</p>
        <div class="table-wrap"><table class="compare bars"><caption class="visually-hidden">Zu- und Fortzüge des Kreises nach Herkunfts- und Zielgebiet</caption>
          <thead><tr><th scope="col">Gebiet</th><th scope="col">Zuzüge aus</th><th scope="col">Fortzüge nach</th><th scope="col">Saldo</th></tr></thead>
          <tbody>${balken("übriges Hessen", k.zuzuege["Land Hessen"], k.fortzuege["Land Hessen"])}${balken("andere Bundesländer", k.zuzuege["Andere Bundesländer"], k.fortzuege["Andere Bundesländer"])}
            ${balken("Ausland", k.zuzuege.Ausland, k.fortzuege.Ausland)}</tbody></table></div>
        <p><button type="button" class="btn btn-soft" data-wanderung-on="wanderung_kreise">Hessische Kreise auf der Karte zeigen</button></p>
        <details class="acc"><summary>Hessische Kreise (${kreiseTop.length})</summary><div class="table-wrap"><table class="compare">
          <caption class="visually-hidden">Zu- und Fortzüge des Kreises je hessischem Kreis</caption>
          <thead><tr><th scope="col">Kreis</th><th scope="col">Zuzüge aus</th><th scope="col">Fortzüge nach</th><th scope="col">Saldo</th></tr></thead>
          <tbody>${kreiseTop.map((x) => `<tr><th scope="row">${esc(x.n)}</th><td>${x.zu == null ? "•" : de(x.zu)}</td><td>${x.fort == null ? "•" : de(x.fort)}</td><td>${x.zu == null || x.fort == null ? "•" : vz(x.zu - x.fort)}</td></tr>`).join("")}</tbody></table></div>
          <p class="hint">• = geheim gehalten. ${esc(W.kreise_hinweis)}</p></details></section>` : ""}
      ${methode([`<ul>${W.hinweise.map((t) => `<li>${esc(t)}</li>`).join("")}</ul>`,
        `${esc(W.attribution)}. ${esc(W.lizenz)}. Berichte: ${jahre.map((y) => link(d.quellen[y], y)).join(", ")}${k ? `; Kreismatrix ${link(k.quelle, String(k.jahr))}` : ""}.`],
        "Wie die Zahlen zu lesen sind")}`;
    $("#wanderung-jahr").addEventListener("change", (e) => { wanderungJahr = e.target.value; showWanderung(); $("#wanderung-jahr").focus(); if (wanderungLayer.wanderung_gemeinden) { wanderungLayer.wanderung_gemeinden.remove(); delete wanderungLayer.wanderung_gemeinden; drawWanderung("wanderung_gemeinden"); } });
  }
  const wName = (d, ags, fallback) => (d.geo?.gemeinden.features.find((f) => f.properties.ags === ags)?.properties.name) || fallback;
  function kuerzen(a, b, km) {
    // beide Enden um km zurücknehmen, damit sich die Pfeilspitzen am Kreismittelpunkt nicht stapeln
    const c = Math.cos((a[1] * Math.PI) / 180), dx = (b[0] - a[0]) * c * 111, dy = (b[1] - a[1]) * 111, len = Math.hypot(dx, dy);
    if (len <= 3 * km) return [a, b];
    const f = km / len;
    return [[a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f], [b[0] - (b[0] - a[0]) * f, b[1] - (b[1] - a[1]) * f]];
  }
  function pfeil(von, nach, km) {
    // Pfeilspitze am Ziel, in Kilometern bemessen (lokal eben genähert)
    const [x1, y1] = von, [x2, y2] = nach, c = Math.cos((y2 * Math.PI) / 180);
    const dx = (x2 - x1) * c, dy = y2 - y1, len = Math.hypot(dx, dy) || 1, ux = dx / len, uy = dy / len, s = km / 111;
    const bx = x2 - (ux * s * 1.0) / c, by = y2 - uy * s * 1.0;
    return [[y2, x2], [by + ux * s * 0.5, bx - (uy * s * 0.5) / c], [by - ux * s * 0.5, bx + (uy * s * 0.5) / c]];
  }
  async function drawWanderung(id) {
    const an = umweltOn.has(id);
    if (!an) { if (wanderungLayer[id]) { wanderungLayer[id].remove(); delete wanderungLayer[id]; } if (legendEl) drawLegend(); return; }
    const d = await loadWanderung();
    if (!d || !d.geo || wanderungLayer[id] || !umweltOn.has(id)) { if (legendEl) drawLegend(); return; }
    const W = cfg.wanderung;
    if (id === "wanderung_gemeinden") {
      const jahr = wanderungJahr ||= wJahre(d).slice(-1)[0];
      wanderungLayer[id] = L.geoJSON(d.geo.gemeinden, {
        style: (f) => { const j = d.gemeinden[f.properties.ags]?.jahre[jahr]; const i = j ? saldoKlasse(rate(j)) : null;
          return { color: color("text-muted"), weight: f.properties.ags === cfg.stadt.gemeindeschluessel ? 2.5 : 1, opacity: 0.9,
            fillColor: i == null ? "transparent" : SALDO_FARBE(i), fillOpacity: i == null ? 0 : SALDO_DECK[i] }; },
        attribution: esc(`${W.attribution}; ${d.geo.attribution}`),
        onEachFeature: (f, layer) => { const j = d.gemeinden[f.properties.ags]?.jahre[jahr];
          layer.bindTooltip(j ? `<strong>${esc(f.properties.name)} ${esc(jahr)}</strong><br>Zuzüge ${de(j.zuzuege)}, Fortzüge ${de(j.fortzuege)}<br>Saldo ${vz(saldo(j))} (${vz(rate(j), 1)} je 1 000 Einwohner)`
            : `<strong>${esc(f.properties.name)}</strong><br>gemeindefreies Gebiet, keine Angabe`, { sticky: true }); },
      }).addTo(map);
    } else {
      const k = d.kreis, ziel = d.geo.kreise[W.kreis_name];
      const liste = Object.keys(W.kreise).filter((n) => n !== W.kreis_name && d.geo.kreise[n])
        .map((n) => ({ n, zu: k.zuzuege[n], fort: k.fortzuege[n] })).filter((x) => (x.zu || 0) + (x.fort || 0) >= W.karte_mindestens);
      const max = Math.max(...liste.map((x) => (x.zu || 0) + (x.fort || 0)));
      const g = L.layerGroup();
      L.geoJSON(d.geo.kreis_umriss, { style: { color: color("accent-ink"), weight: 2, fill: false }, interactive: false }).addTo(g);
      for (const x of liste) {
        const s = (x.zu || 0) - (x.fort || 0);
        const [von, nach] = kuerzen(s >= 0 ? d.geo.kreise[x.n] : ziel, s >= 0 ? ziel : d.geo.kreise[x.n], 7);
        const farbe = s >= 0 ? color("accent-ink") : color("abzug"), weight = 1.5 + (9 * ((x.zu || 0) + (x.fort || 0))) / max;
        const tip = `<strong>${esc(x.n)} ↔ ${esc(W.kreis_name)}, ${k.jahr}</strong><br>Zuzüge in den Kreis ${x.zu == null ? "geheim" : de(x.zu)}, Fortzüge ${x.fort == null ? "geheim" : de(x.fort)}<br>Saldo ${x.zu == null || x.fort == null ? "nicht berechenbar" : vz(s)}`;
        L.polyline([[von[1], von[0]], [nach[1], nach[0]]], { color: farbe, weight, opacity: 0.75 }).bindTooltip(tip, { sticky: true }).addTo(g);
        L.polygon(pfeil(von, nach, 3 + weight * 0.6), { color: farbe, weight: 1, fillColor: farbe, fillOpacity: 0.9 }).bindTooltip(tip, { sticky: true }).addTo(g);
      }
      g.getAttribution = () => esc(`${W.attribution}; ${d.geo.attribution}`);  // Leaflet nimmt sie beim Hinzufügen auf
      wanderungLayer[id] = g.addTo(map);
    }
    if (legendEl) drawLegend();
  }
  function wanderungLegend() {
    if (!cfg.wanderung) return "";
    let h = "";
    if (wanderungLayer.wanderung_gemeinden) {
      h += `<p class="legend-group">Wanderungssaldo je 1 000 Einwohner, ${esc(wanderungJahr)}</p><ul>${saldoKlassenText().map((t, i) => `<li><span class="swatch swatch-area" aria-hidden="true"
        style="border-color:${color("text-muted")};background:color-mix(in srgb, ${SALDO_FARBE(i)} ${Math.round(SALDO_DECK[i] * 100)}%, transparent)"></span>${esc(t)}</li>`).join("")}</ul>
        <p class="hint">Gemeinden im ${esc(cfg.wanderung.kreis_name)}; Wanderungen über die Gemeindegrenze.</p>`;
    }
    if (wanderungLayer.wanderung_kreise) {
      h += `<p class="legend-group">Wanderung über die Kreisgrenze, ${esc(cfg.wanderung.kreis_name)}</p><ul>
        <li><span class="swatch" style="background:${color("accent-ink")}" aria-hidden="true"></span>mehr Zuzüge aus dem Kreis als Fortzüge dorthin</li>
        <li><span class="swatch" style="background:${color("abzug")}" aria-hidden="true"></span>mehr Fortzüge in den Kreis als Zuzüge von dort</li></ul>
        <p class="hint">Linienstärke: Zu- und Fortzüge zusammen; gezeigt sind hessische Kreise mit mindestens ${de(cfg.wanderung.karte_mindestens)} Zu- und Fortzügen, alle Kreise stehen in der Tabelle. Nur der Kreis insgesamt, nicht ${esc(cfg.stadt.name)} allein; andere Bundesländer und Ausland im Panel.</p>`;
    }
    return h;
  }

  $("#wanderung").addEventListener("click", async (e) => {
    const b = e.target.closest("[data-wanderung-on]");
    if (!b) return;
    const id = b.dataset.wanderungOn;
    umweltOn.add(id);
    const box = document.querySelector(`.map-layers input[value="${CSS.escape(id)}"]`);
    if (box) box.checked = true;
    await drawWanderung(id);
    if (wanderungLayer[id]) map.fitBounds(id === "wanderung_kreise" ? L.latLngBounds(Object.values((await loadWanderung()).geo.kreise).map(([x, y]) => [y, x])) : wanderungLayer[id].getBounds(), mapPadding());
    syncUrl();
    closePanel("panel-wanderung");
  });
  $("#wohnen").addEventListener("click", (e) => {
    const eb = e.target.closest("[data-ebene-on]");
    if (eb) {
      umweltOn.add(eb.dataset.ebeneOn);
      const box = document.querySelector(`.map-layers input[value="${CSS.escape(eb.dataset.ebeneOn)}"]`);
      if (box) box.checked = true;
      drawUmwelt(eb.dataset.ebeneOn);
      syncUrl();
      closePanel("panel-wohnen");
      return;
    }
    if (!e.target.closest("[data-brw-on]")) return;
    umweltOn.add("bodenrichtwerte");
    const cb = document.querySelector('.map-layers input[value="bodenrichtwerte"]');
    if (cb) cb.checked = true;
    drawBrw();
    syncUrl();
    closePanel("panel-wohnen");
  });
  // Kasten im Vorgang: nur bei Titeln mit Bezug zu Bauen und Wohnen (wohnen.bezug_titel) und mit Ortsbezug
  function wohnenKasten(p) {
    if (!cfg.wohnen || !wohnen || !new RegExp(cfg.wohnen.bezug_titel, "i").test(p.name)) return "";
    const slugs = [...new Set(p.locations.map((l) => slugOf(l.ortsteil)).filter(Boolean))];
    if (!slugs.length) return "";
    const z = wohnen.zensus;
    const rows = slugs.map((s) => {
      const o = cfg.ortsteile.find((x) => x.slug === s);
      const sp = wohnen.boris.spannen[s];
      const m = z && z.ortsbezirke[s] && z.ortsbezirke[s].miete;
      return `<li><strong>${esc(o.name)}</strong>: Bodenrichtwerte ${sp ? `${num(sp.min, 0)} bis ${num(sp.max, 0)} €/m²` : "–"} (Stichtag ${brwStichtag()})
        · Bestandsmiete ${m && m.wert != null ? `${num(m.wert, 2)} €/m² <span class="derived">Näherung</span>` : "nicht ausgewiesen"} (Zensus 2022)
        <br><button type="button" class="link-btn" data-open-wohnen="${esc(s)}">Mehr zu Wohnen und Boden in ${esc(o.name)}</button></li>`;
    }).join("");
    return `<h4>Wohnen und Boden</h4><ul class="locs">${rows}</ul><p class="hint">Kontext zum Ort, kein Bezug zum Inhalt des Vorgangs.</p>`;
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
    $("#q").value = "";  // Suchfeld der Leiste gehört zum Filter (wie in resetFilters)
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
    const ei = $("#f-einreicher").value;
    if (ei) url.searchParams.set("einreicher", ei); else url.searchParams.delete("einreicher");
    if (planOn) url.searchParams.set("plaene", "1"); else url.searchParams.delete("plaene");
    const imLink = [...umweltOn].filter((id) => id !== "bodenrichtwerte2026");
    if (imLink.length) url.searchParams.set("ebenen", imLink.join(",")); else url.searchParams.delete("ebenen");
    if (!selected && planShown) url.searchParams.set("plan", planShown); else url.searchParams.delete("plan");
    url.hash = selected ? encodeURIComponent(selected.reference) : "";
    history.replaceState(null, "", url);
  }

  // --- Start -----------------------------------------------------------------------------------------
  async function start() {
    const json = (url) => fetch(url).then((r) => (r.ok ? r.json() : null)).catch(() => null);
    const [c, d, f, credits, w, wa, be, ei] = await Promise.all([json(CONFIG_URL), json(DATA_URL), json(FLAECHEN_URL), json("namensnennungen.json"),
      json(WOHNEN_URL), json(WAHLEN_URL), json(BETEILIGUNG_URL), json(EIGENTUM_URL)]);
    beteiligung = be;
    eigentum = ei;
    wohnen = w;
    wahlen = wa;
    if (credits && credits.length) $("#credits").innerHTML = credits.map((a) => `<li>${link(a.link, esc(a.text)) || esc(a.text)} <span class="hint">(${esc(a.lizenz)})</span></li>`).join("");
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
      if (e.target.closest("#more")) {  // weitere Einträge; Fokus auf den ersten neuen, statt ihn mit dem Knopf zu verlieren
        const bisher = shown;
        shown += LIST_STEP;
        render();
        const b = document.querySelectorAll("#papers button[data-ref]")[bisher];
        if (b) b.focus();
        return;
      }
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
    $("#cta-wahlen").addEventListener("click", () => { setPanel("panel-wahlen", true); showWahlen(); focusPanel("panel-wahlen"); });
    $("#cta-wanderung").addEventListener("click", () => { setPanel("panel-wanderung", true); showWanderung(); focusPanel("panel-wanderung"); });
    $("#cta-wohnen").addEventListener("click", () => { setPanel("panel-wohnen", true); showWohnen(null); focusPanel("panel-wohnen"); });
    const params = new URLSearchParams(location.search);
    let ref = "";
    try { ref = decodeURIComponent(location.hash.slice(1)); } catch (e) { /* fehlerhafter Anker: ohne Vorgang starten */ }
    loadArea(params.get("gebiet") || DEFAULT_AREA, true);
    if (params.get("gremium")) { $("#f-gremium").value = params.get("gremium"); setPanel("panel-list", true); render(); }
    if (params.get("einreicher")) { $("#f-einreicher").value = params.get("einreicher"); setPanel("panel-list", true); render(); }
    const von = params.get("von"), bis = params.get("bis");
    if (tl && isoTag(von) && isoTag(bis)) {
      setPanel("timeline-wrap", true);
      tl.setState({ von, bis, zoom: params.get("zoom"), achse: params.get("achse") });
      const st = tl.getState();  // von der Zeitleiste geordnet und auf den Bestand begrenzt
      range = [st.von, st.bis];
      render();
    }
    if (planOn) drawPlans();
    for (const id of umweltOn) drawEbene(id);
    // Vorgang aus dem Anker; liegt er nicht im gewählten Gebiet, die ganze Stadt laden
    const initial = ref && all.find((p) => p.reference === ref);
    if (initial && !papers.includes(initial)) loadArea(DEFAULT_AREA, true);
    if (initial) select(initial); else if (params.get("plan")) await showPlan(params.get("plan")); else showIntro();
    syncUrl();
  }

  // für die Tour (site/tour.js): Flächen und Menüs öffnen, ein Beispiel zeigen, Lage des Gebiets auf der Karte
  window.stadtmonitor = {
    get stadt() { return cfg && cfg.stadt.name; },
    ui: {
      panel(id, open) { if (!toggleFor(id) || !toggleFor(id).hidden) setPanel(id, open); },
      mapMenu(open) { const b = document.querySelector(".map-menu"); if (b && (b.getAttribute("aria-expanded") === "true") !== open) b.click(); },
      layers(open) { const d = document.querySelector(".map-layers"); if (d) d.open = open; },
      menu(id) { if (id) openMega(id); else closeMega(); },
      async example() {
        if (selected) return true;
        // jüngster Vorgang mit Punkt auf der Karte und mehreren Stationen, sonst der erste der Liste
        const list = filtered();
        const p = list.filter((x) => x.process.length > 1 && (markers.get(x.reference) || []).length)
          .sort((a, b) => String(b.date).localeCompare(String(a.date)))[0] || list[0];
        if (p) select(p);
        return Boolean(p);
      },
      areaRect() {
        if (!outline) return null;
        const b = outline.getBounds(), r = map.getContainer().getBoundingClientRect();
        const nw = map.latLngToContainerPoint(b.getNorthWest()), se = map.latLngToContainerPoint(b.getSouthEast());
        return { left: r.left + nw.x, top: r.top + nw.y, right: r.left + se.x, bottom: r.top + se.y };
      },
    },
  };

  start().catch((err) => { $("#detail").innerHTML = `<p>Die Seite konnte nicht geladen werden (${esc(err.message)}).</p>`; });
})();
