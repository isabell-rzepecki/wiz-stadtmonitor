// Tour durch die Funktionen des Stadtmonitors (übernommen aus der RIS-Karte Bonn, MIT-Lizenz): hebt nacheinander
// Bedienelemente hervor (abgedunkelte Umgebung, pulsierender Rahmen, pulsierende Punkte an erwähnten Einzelheiten)
// und erklärt sie in einer Karte. Start über Schaltflächen mit data-tour (Fenster „Los geht's“, Dialog „Über“).
// Bedienung: Weiter/Zurück, Pfeiltasten, Esc beendet. Bei reduzierter Bewegung ohne Animation (style.css). Kein Inline-Skript (CSP).
(function () {
  "use strict";
  const MOBILE = matchMedia("(max-width: 900px)");
  const $ = (s) => document.querySelector(s);
  const stadt = () => (window.stadtmonitor && window.stadtmonitor.stadt) || "der Stadt";

  // Schritte: target (Selektor) oder rect (Fläche aus app.js), before (Flächen öffnen), menu (Mega-Menü),
  // beacons (Selektoren für pulsierende Punkte), clip (sichtbarer Ausschnitt), when (Schritt nur, wenn verfügbar)
  const STEPS = [
    { title: "Willkommen zur Tour",
      text: () => `Der Stadtmonitor zeigt, womit sich Stadtverordnetenversammlung, Ausschüsse, Ortsbeiräte und Beiräte in ${stadt()} befassen: wo (Karte), wann (Zeitleiste) und in welchen Sitzungen. Dazu kommen Daten zu Wahlen, Wohnen und Boden sowie Zuzug und Wegzug. Die Tour stellt die Funktionen der Reihe nach vor. Weiter mit der Pfeiltaste nach rechts, beenden mit Esc.` },
    { target: "#nav-search", beacons: ["#q"],
      title: "Suche",
      text: "Ein Stichwort oder eine Vorlagennummer eingeben, etwa „Bebauungsplan“, „Kita“ oder „STV/488/2025“. Gesucht wird in allen Tagesordnungspunkten." },
    { target: "#f-area",
      title: "Gebiet wählen",
      text: () => `Ganz ${stadt()}, die Kernstadt, einer der 16 Ortsbezirke oder Vorgänge ohne Ortsbezug. Auf der Karte lassen sich die Ortsteile auch direkt anklicken. Karte, Liste, Zeitleiste und die Panels zeigen jeweils das gewählte Gebiet.` },
    { before: (ui) => { ui.mapMenu(false); if (MOBILE.matches) ui.panel("panel-detail", false); }, rect: (ui) => ui.areaRect(), fallback: "#map",
      beacons: [".marker-cluster, .leaflet-marker-pane .leaflet-interactive", ".map-legend > summary", ".map-sources"],
      title: "Die Karte",
      text: "Jeder Punkt ist ein Vorgang mit Ortsbezug; Zahlen fassen nahe Punkte zusammen, ein Klick zoomt hinein. Die Farbe zeigt, wie sicher der Ort ist: grün gesichert (Gremium des Ortsteils oder eindeutiger Plan), braun erschlossen (Name im Titel), blau unsicher. Die Legende erklärt die Farben; unter „© Quellen“ stehen die Namensnennungen." },
    { before: (ui) => { ui.mapMenu(true); ui.layers(true); }, target: ".leaflet-bottom.leaflet-right", beacons: [".map-layers > summary", ".map-3d", ".map-colored"],
      title: "Kartenoptionen und Ebenen",
      text: "Unter „Weitere Ebenen“ lassen sich Bauleitplanung, Hochwasser, Wasserschutz, Schutzgebiete, Windvorranggebiete, Kulturdenkmäler, Gebäude für öffentliche Zwecke, Bodenrichtwerte sowie Zuzug und Wegzug einblenden. Die Ebenen sind nicht rechtsverbindlich. „Gebäude 2D/3D“ öffnet die Seite Wohnen und Eigentum mit allen Gebäuden als Grundriss und mit ihrer Höhe, „Farbige Karte“ wechselt den Hintergrund." },
    { before: (ui) => { ui.layers(false); ui.mapMenu(false); ui.panel("panel-list", true); }, target: "#panel-list", beacons: ["#f-text", "#more-filters > summary"],
      title: "Die Liste",
      text: () => "Alle Vorgänge des Gebiets – gleichwertig zur Karte und mit der Tastatur bedienbar. Filter nach Stichwort, Gremium und Art; unter „Weitere Filter“ nach Fraktion, die einen Antrag eingebracht hat, und nach Sicherheit der Ortsangabe."
        + (MOBILE.matches ? "" : " Die Breite lässt sich am Rand ziehen.") },
    { when: () => !document.querySelector('.toggle[data-panel="timeline-wrap"]').hidden,
      before: (ui) => ui.panel("timeline-wrap", true), target: "#timeline-wrap",
      title: "Die Zeitleiste",
      text: "Die Balken zeigen, wie viele Vorgänge je Monat beraten wurden; dazu Sitzungen und Wahlperioden. Mit den Griffen oder einer Voreinstellung wählen Sie einen Zeitraum – Liste und Karte folgen." },
    { before: async (ui) => { await ui.example(); ui.panel("panel-detail", true); }, target: "#panel-detail", requires: "#detail .steps",
      beacons: ["#detail .links .btn-primary"],
      title: "Der Vorgang",
      text: "Ein Beispiel aus dem Gebiet: Vorlagennummer, erste Beratung, Gremien und, wenn im Titel genannt, die Fraktion, die den Antrag eingebracht hat. Dazu der Link zur Einladung (PDF) und zum Bürgerinformationssystem. Maßgeblich ist immer das Original." },
    { target: "#detail .steps", clip: "#detail", scroll: true,
      title: "Die Prozesslinie",
      text: "Die Stationen des Vorgangs: die Sitzungen, in deren Tagesordnung er stand, mit Datum, TOP und Fundstelle. Beschlussergebnisse sind nicht veröffentlicht; die Prozesslinie zeigt sie als Lücke und leitet nichts ab. Unter „Methode und Quellen“ stehen Evidenzstatus und Bekanntmachungen." },
    { menu: "mega-mitmachen", target: "#mega-mitmachen", beacons: ["#cta-termine", "#cta-wahlen", "#cta-wohnen", "#cta-wanderung"],
      title: "Sitzungen und Themen",
      text: "Kommende Sitzungen mit Tagesordnung und laufender Beteiligung an der Bauleitplanung; Kennzahlen zum Gebiet; amtliche Wahlergebnisse und Sitzverteilung; Wohnen und Boden mit Bodenrichtwerten und Zensus; Zuzug und Wegzug seit 2015. Dazu der Weg ins Bürgerinformationssystem und ein Hinweis, wenn etwas falsch zugeordnet ist." },
    { menu: "mega-daten", target: "#mega-daten",
      title: "Offene Daten",
      text: "Alle Daten zum Herunterladen: das Datenpaket mit Prüfprotokollen, dazu Quellen, Lizenzen und Datenstand." },
    { target: ".nav-group.seg",
      title: "Flächen ein- und ausklappen",
      text: () => "Liste, Zeitleiste und Vorgang lassen sich hier öffnen und schließen; die Karte bleibt darunter sichtbar. Esc schließt die Fläche, in der Sie gerade sind."
        + (MOBILE.matches ? " Auf dem Handy starten die Flächen auf halber Höhe; der Pfeil im Kopf vergrößert sie." : "") },
    { target: "#about-open",
      title: "Über den Stadtmonitor",
      text: "Hier steht, woher die Daten stammen, wie verortet wird, wie sicher die Angaben sind und was der Stadtmonitor nicht zeigen kann. Viel Freude beim Erkunden." },
  ];

  let steps = [], i = 0, root = null, card = null, spot = null, raf = 0, prevFocus = null, ui = null;

  const shown = (el) => el && el.getClientRects().length > 0 && getComputedStyle(el).visibility !== "hidden";
  const first = (sel) => sel ? [...document.querySelectorAll(sel)].find((el) => shown(el) && inView(el.getBoundingClientRect())) : null;
  const inView = (r) => r.bottom > 0 && r.right > 0 && r.top < innerHeight && r.left < innerWidth;

  function build() {
    root = document.createElement("div");
    root.className = "tour";
    root.innerHTML = `<div class="tour-block"></div><div class="tour-spot" aria-hidden="true"></div><div class="tour-beacons" aria-hidden="true"></div>
      <div class="tour-card glass" role="dialog" aria-modal="true" aria-labelledby="tour-title" aria-describedby="tour-text">
        <div class="tour-top"><span class="tour-count" id="tour-count"></span>
          <button type="button" class="icon-btn tour-x" data-tour-act="end" aria-label="Tour beenden"><svg class="icon" aria-hidden="true"><use href="#i-close"/></svg></button></div>
        <div class="tour-bar" aria-hidden="true"><span></span></div>
        <h2 class="tour-title" id="tour-title"></h2>
        <p class="tour-text" id="tour-text"></p>
        <div class="tour-nav">
          <button type="button" class="btn btn-soft" data-tour-act="prev">Zurück</button>
          <button type="button" class="btn btn-cta" data-tour-act="next"></button>
        </div>
        <p class="visually-hidden" id="tour-live" aria-live="polite"></p>
      </div>`;
    document.body.appendChild(root);
    card = root.querySelector(".tour-card");
    spot = root.querySelector(".tour-spot");
    // Klicks bleiben in der Tour (sonst schlösse app.js das gerade geöffnete Menü)
    root.addEventListener("click", (e) => {
      e.stopPropagation();
      const b = e.target.closest("[data-tour-act]");
      if (!b) return;
      if (busy && b.dataset.tourAct !== "end") return;
      if (b.dataset.tourAct === "next") go(i + 1, 1);
      else if (b.dataset.tourAct === "prev") go(i - 1, -1);
      else end();
    });
  }

  function start() {
    ui = window.stadtmonitor && window.stadtmonitor.ui;
    if (!ui || root) return;
    const about = $("#about");
    if (about && about.open) about.close();
    prevFocus = document.activeElement;
    steps = STEPS.filter((s) => !s.when || s.when());
    ui.menu(null);
    build();
    // Rest der Seite für Tastatur und Screenreader sperren, solange die Tour läuft
    document.querySelectorAll("body > header, body > main").forEach((el) => { el.inert = true; });
    document.body.classList.add("touring");
    addEventListener("keydown", onKey, true);
    addEventListener("resize", layout);
    go(0, 1);
  }

  function end() {
    if (!root) return;
    cancelAnimationFrame(raf);
    removeEventListener("keydown", onKey, true);
    removeEventListener("resize", layout);
    document.querySelectorAll("body > header, body > main").forEach((el) => { el.inert = false; });
    document.body.classList.remove("touring");
    ui.menu(null);
    root.remove();
    root = null;
    // Fokus zurück: zuletzt fokussiertes Element, sonst Überschrift des Vorgangs, sonst die Gebietsauswahl
    const back = [prevFocus, $("#detail-heading"), $("#f-area")].find((el) => el && el.isConnected && shown(el));
    if (back) back.focus();
  }

  let goSeq = 0, busy = false;
  async function go(n, dir) {
    if (n >= steps.length) return end();
    if (n < 0) return;
    const s = steps[n], seq = ++goSeq;
    const pending = s.before && s.before(ui);
    if (pending && typeof pending.then === "function") {
      // Vorbereitung dauert (Beispiel wird geladen): Hinweis zeigen, Blättern sperren
      const next = root.querySelector('[data-tour-act="next"]');
      root.querySelector("#tour-text").textContent = "Einen Moment, das Beispiel wird geladen …";
      busy = true;
      next.setAttribute("aria-disabled", "true");
      try { await pending; } finally { busy = false; next.removeAttribute("aria-disabled"); }
    }
    // während des Wartens (Beispiel wird geladen) weitergeblättert oder beendet
    if (seq !== goSeq || !root) return;
    ui.menu(s.menu || null);
    if (s.scroll) { const el = $(s.target); if (el) el.scrollIntoView({ block: "start" }); }
    // fehlt das Element (etwa ohne Vorlagen im Gebiet), in Laufrichtung überspringen
    if ((s.requires && !$(s.requires)) || (s.target && !s.fallback && !$(s.target))) {
      if (n + dir >= 0 && n + dir < steps.length) return go(n + dir, dir);
    }
    i = n;
    root.querySelector("#tour-count").textContent = `Schritt ${n + 1} von ${steps.length}`;
    root.querySelector(".tour-bar span").style.width = `${((n + 1) / steps.length) * 100}%`;
    root.querySelector("#tour-title").textContent = s.title;
    const text = typeof s.text === "function" ? s.text() : s.text;
    root.querySelector("#tour-text").textContent = text;
    const prev = root.querySelector('[data-tour-act="prev"]'), next = root.querySelector('[data-tour-act="next"]');
    prev.hidden = n === 0;
    next.textContent = n === 0 ? "Los geht's" : n === steps.length - 1 ? "Fertig" : "Weiter";
    root.querySelector("#tour-live").textContent = `Schritt ${n + 1} von ${steps.length}: ${s.title}. ${text}`;
    card.classList.remove("enter");
    void card.offsetWidth;  // Einblendung neu starten
    card.classList.add("enter");
    root.querySelector(".tour-beacons").innerHTML = (s.beacons || []).map(() => '<span class="tour-beacon"></span>').join("");
    next.focus();
    // Flächen gleiten herein: Lage einige Bilder lang nachführen
    cancelAnimationFrame(raf);
    const until = performance.now() + 700;
    const tick = () => { layout(); if (performance.now() < until) raf = requestAnimationFrame(tick); };
    tick();
  }

  function targetRect(s) {
    let r = null;
    if (s.rect) r = s.rect(ui);
    if (!r && (s.target || s.fallback)) {
      const el = first(s.target) || first(s.fallback);
      if (el) r = el.getBoundingClientRect();
    }
    if (!r) return null;
    let { left, top, right, bottom } = r;
    if (s.clip) {
      const c = $(s.clip).getBoundingClientRect();
      left = Math.max(left, c.left); top = Math.max(top, c.top); right = Math.min(right, c.right); bottom = Math.min(bottom, c.bottom);
    }
    const pad = 6;
    left = Math.max(4, left - pad); top = Math.max(4, top - pad);
    right = Math.min(innerWidth - 4, right + pad); bottom = Math.min(innerHeight - 4, bottom + pad);
    if (right - left < 12 || bottom - top < 12) return null;
    return { left, top, right, bottom, width: right - left, height: bottom - top };
  }

  function layout() {
    if (!root) return;
    const s = steps[i], r = targetRect(s);
    spot.classList.toggle("none", !r);
    const box = r || { left: innerWidth / 2, top: innerHeight / 2, width: 0, height: 0 };
    Object.assign(spot.style, { left: box.left + "px", top: box.top + "px", width: box.width + "px", height: box.height + "px" });
    // pulsierende Punkte: Mitte kleiner Elemente, sonst rechte obere Ecke
    const beacons = root.querySelectorAll(".tour-beacon");
    (s.beacons || []).forEach((sel, k) => {
      const el = first(sel), b = beacons[k];
      if (!b) return;
      b.hidden = !el;
      if (!el) return;
      const e = el.getBoundingClientRect(), small = e.width < 40 && e.height < 40;
      b.style.left = (small ? e.left + e.width / 2 : e.right - 8) + "px";
      b.style.top = (small ? e.top + e.height / 2 : e.top + 8) + "px";
    });
    placeCard(r);
  }

  function placeCard(r) {
    const vw = innerWidth, vh = innerHeight, gap = 16, m = 10;
    const cw = card.offsetWidth, ch = card.offsetHeight;
    const clampX = (x) => Math.max(m, Math.min(vw - cw - m, x));
    const clampY = (y) => Math.max(m, Math.min(vh - ch - m, y));
    let x, y;
    if (!r) { x = (vw - cw) / 2; y = (vh - ch) / 2; }
    else if (MOBILE.matches) { x = (vw - cw) / 2; y = (r.top + r.bottom) / 2 > vh / 2 ? m : vh - ch - m; }
    else if (r.bottom + gap + ch <= vh - m && r.height < vh * 0.6) { x = clampX(r.left + r.width / 2 - cw / 2); y = r.bottom + gap; }
    else if (r.right + gap + cw <= vw - m) { x = r.right + gap; y = clampY(r.top); }
    else if (r.left - gap - cw >= m) { x = r.left - gap - cw; y = clampY(r.top); }
    else if (r.top - gap - ch >= m) { x = clampX(r.left + r.width / 2 - cw / 2); y = r.top - gap - ch; }
    else { x = clampX(r.left + r.width / 2 - cw / 2); y = vh - ch - m; }
    card.style.left = Math.round(x) + "px";
    card.style.top = Math.round(y) + "px";
  }

  function onKey(e) {
    if (!root) return;
    const keys = { Escape: end, ArrowRight: () => go(i + 1, 1), ArrowLeft: () => go(i - 1, -1) };
    if (keys[e.key]) { e.preventDefault(); e.stopPropagation(); if (!busy || e.key === "Escape") keys[e.key](); return; }
    if (e.key === "Tab") {  // Fokus bleibt in der Karte
      const f = [...card.querySelectorAll("button")].filter(shown);
      const k = f.indexOf(document.activeElement);
      e.preventDefault();
      f[(k + (e.shiftKey ? -1 : 1) + f.length) % f.length].focus();
    }
  }

  document.addEventListener("click", (e) => { if (e.target.closest("[data-tour]")) start(); });
})();
