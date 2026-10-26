// Wohnen und Eigentum: alle Gebäude der Stadt in 2D (Grundriss) und 3D (Grundriss mit gemessener Höhe, fill-extrusion).
// Zweck der Seite (Übergabe v0.4.2): Für die Stadt gibt es keinen Mietspiegel; die Seite soll eine Vergleichsgrundlage
// für tatsächlich gezahlte Mieten schaffen. Grundlage dafür sind die Gebäude mit ihrer ALKIS-OID als Schlüssel; dieselbe
// Kennung gilt in 2D, in 3D und später in der Erfassung. Eigentum und Mieten zeigt die Seite erst nach der Prüfung und
// nur nach den Veröffentlichungsregeln (docs/uebergabe-v0.4.2/veroeffentlichungsregeln.tsv).
// Daten: data/export/karte/gebaeude.pmtiles (Vektorkacheln, pipeline/gebaeude.py) und gebaeude_index.json; Bodenrichtwertzonen aller
// Stichtage mit Datendienst in bodenrichtwerte_zonen.pmtiles (pipeline/wohnen.py). Die Module rechts stehen in wohnen-module.js.
(function () {
  "use strict";
  const $ = (s) => document.querySelector(s);
  const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const json = (u) => fetch(u).then((r) => (r.ok ? r.json() : null)).catch(() => null);
  const zahl = (v, d = 0) => Number(v).toLocaleString("de-DE", { minimumFractionDigits: d, maximumFractionDigits: d });
  const REDUZIERT = matchMedia("(prefers-reduced-motion: reduce)").matches;
  const SCHMAL = matchMedia("(max-width: 700px)");

  // Gebäudefunktion (ALKIS) in vier Gruppen; Farben mit mindestens 3:1 gegen den grauen Hintergrund
  const GRUPPEN = [
    { id: "wohnen", titel: "Wohngebäude", farbe: "#c8463d", werte: ["Wohngebäude"] },
    { id: "wirtschaft", titel: "Wirtschaft oder Gewerbe", farbe: "#4f6487", werte: ["Gebäude für Wirtschaft oder Gewerbe", "Treibhaus, Gewächshaus"] },
    { id: "oeffentlich", titel: "Öffentliche Zwecke, Kirche", farbe: "#2c7652",
      werte: ["Gebäude für öffentliche Zwecke", "Kirche", "Kapelle", "Burg, Festung", "Schloss"] },
    { id: "sonstige", titel: "Nebengebäude und Sonstiges", farbe: "#857a70", werte: [] },
  ];
  const farbe = ["match", ["get", "f"], ...GRUPPEN.slice(0, 3).flatMap((g) => [g.werte, g.farbe]), GRUPPEN[3].farbe];
  const geschaetzt = ["==", ["get", "hq"], "geschätzt"];
  // Bodenrichtwerte: gleicher Filter wie in der Hauptkarte (baureifes Wohn- und Mischbauland), Klassen laut stadt.json
  const BRW_FARBEN = ["#f6e7cf", "#ecc58f", "#dd9a5a", "#bf6a34", "#86401f"];
  const brwFilter = (st) => ["all", ["==", ["get", "stichtag"], st], ["==", ["get", "ez"], "B"],
    ["in", ["slice", ["coalesce", ["get", "art"], ""], 0, 1], ["literal", ["W", "M"]]]];
  const datum = (iso) => new Date(`${iso.slice(0, 10)}T12:00:00Z`).toLocaleDateString("de-DE", { day: "2-digit", month: "2-digit", year: "numeric" });

  async function start() {
    const [cfg, index, flaechen, wohnen, eigentum] = await Promise.all([json("stadt.json"), json("data/export/karte/gebaeude_index.json"),
      json("data/export/flaechen.json"), json("data/export/wohnen.json"), json("data/export/eigentum.json")]);
    const G = cfg.gebaeude, K = cfg.wohnen.boris.klassen;
    // Eigentum: nur die geprüfte Datei aus tools/veroeffentlichen.py (juristische Personen je Gebäude; privat nie je Gebäude)
    const eigDaten = wohnen && wohnen.eigentum_karte ? await json("data/export/karte/eigentum_gebaeude.json") : null;
    const eigIndex = new Map(((eigDaten && eigDaten.features) || []).map((f) => [f.properties.id, f.properties]));
    const KATS = cfg.wohnen_eigentum.kategorien.filter((k) => k.farbe && [...eigIndex.values()].some((p) => p.kategorie === k.code));
    const eigFarbe = KATS.length ? ["match", ["get", "id"], ...KATS.flatMap((k) => [[...eigIndex.values()].filter((p) => p.kategorie === k.code).map((p) => p.id), k.farbe]), "#e3ded9"] : null;
    const params = new URLSearchParams(location.search);
    let ansicht = params.get("ansicht") === "3d" ? "3d" : "2d";
    let gewaehlt = params.get("gebaeude") || null;
    const stichtage = ((wohnen && wohnen.boris_verlauf && wohnen.boris_verlauf.stichtage) || []).slice().sort().reverse();
    const ebeneSel = $("#ebene");
    if (eigFarbe) ebeneSel.innerHTML += '<option value="eigentum">Eigentum (geprüfte Erfassung)</option>';
    ebeneSel.innerHTML += stichtage.map((st) => `<option value="bodenrichtwerte:${esc(st)}">Bodenrichtwerte ${esc(datum(st))}</option>`).join("");
    ebeneSel.value = [...ebeneSel.options].some((o) => o.value === params.get("ebene")) ? params.get("ebene") : "funktion";
    const vorhanden = (index && index.ortsteile) || {};
    const liste = cfg.ortsteile.filter((o) => vorhanden[o.slug]);
    const sel = $("#ortsteil");
    sel.innerHTML = `<option value="">ganze Stadt</option>` + liste.map((o) => `<option value="${esc(o.slug)}">${esc(o.name)}</option>`).join("");
    const gebiet = (params.get("gebiet") || "").replace(/^ortsteil:/, "");
    sel.value = liste.some((o) => o.slug === gebiet) ? gebiet : "";

    // Module rechts (auf schmalen Bildschirmen über „Angaben“ ein- und ausblenden)
    const knopf = $("#angaben-knopf"), aside = $("#module");
    function angaben(offen) { aside.hidden = !offen; knopf.setAttribute("aria-expanded", String(offen)); }
    angaben(!SCHMAL.matches);
    knopf.addEventListener("click", () => { const offen = aside.hidden; angaben(offen); if (offen) $("#module-titel").focus(); });
    $("#module-titel").tabIndex = -1;
    function module() {
      const o = cfg.ortsteile.find((x) => x.slug === sel.value);
      $("#module-gebiet").textContent = `– ${o ? o.name : `ganz ${cfg.stadt.name}`}`;
      WohnenModule.render($("#module-inhalt"), { cfg, wohnen, eigentum, index, slug: sel.value || null });
    }
    module();

    function legende() {
      const st = ebeneSel.value.startsWith("bodenrichtwerte:") ? ebeneSel.value.slice(16) : null;
      const sw = (f, t, k = "") => `<li><span class="sw${k}" style="${f ? `background:${f}` : ""}" aria-hidden="true"></span>${t}</li>`;
      $("#legende").innerHTML = ebeneSel.value === "eigentum"
        ? KATS.map((k) => sw(k.farbe, esc(k.titel))).join("") + sw("#e3ded9", "nicht erfasst, unklar oder Privatperson")
        : st
        ? BRW_FARBEN.map((f, i) => sw(f, `${i === 0 ? `unter ${K[0]}` : i === K.length ? `ab ${K[K.length - 1]}` : `${K[i - 1]} bis unter ${K[i]}`} €/m²`)).join("")
          + sw("#6b625b", "Gebäude")
        : GRUPPEN.map((g) => sw(g.farbe, esc(g.titel))).join("") + sw("", `Höhe geschätzt (${zahl(G.standardhoehe_m)} m, ohne 3D-Modell)`, " sw-geschaetzt");
      $("#hinweis").textContent = ebeneSel.value === "eigentum"
        ? `Eigentum nach geprüfter Erfassung (zwei Freigaben), Stand ${datum(eigDaten.stand)}; unvollständig. Gebäude von Privatpersonen erscheinen nie einzeln, nur als Anzahl je Ortsbezirk (Erfassungsstand).`
        : st
        ? `Bodenrichtwerte, Stichtag ${datum(st)}: ${cfg.wohnen.boris.filter}. Zonengrenzen können sich zwischen Stichtagen ändern. ${cfg.wohnen.boris.attribution}.`
        : `${cfg.gebaeude3d.hinweis} Grundrisse aus ALKIS, Höhe aus den 3D-Gebäudemodellen LoD2; ohne passendes Modell gilt eine Standardhöhe. Eigentum zeigt eine eigene Ebene, sobald geprüfte Erfassungen vorliegen.`;
    }
    legende();
    $("#mehr").open = !SCHMAL.matches;
    if (!index) { $("#stand").textContent = "Noch keine Gebäudedaten."; return; }

    maplibregl.setWorkerUrl("vendor/maplibre/maplibre-gl-csp-worker.js");
    const protokoll = new pmtiles.Protocol();
    maplibregl.addProtocol("pmtiles", protokoll.tile);
    const kacheln = new URL("data/export/karte/gebaeude.pmtiles", location.href).href;
    const zonen = new URL("data/export/karte/bodenrichtwerte_zonen.pmtiles", location.href).href;
    const brwFarbe = ["step", ["get", "wert"], BRW_FARBEN[0], ...K.flatMap((k, i) => [k, BRW_FARBEN[i + 1]])];
    const map = new maplibregl.Map({
      container: "karte", center: [cfg.karte.zentrum[1], cfg.karte.zentrum[0]], zoom: 14, maxPitch: 70,
      style: { version: 8, sources: {
        basis: { type: "raster", tiles: [cfg.karte.hintergrund.grau], tileSize: 256, maxzoom: cfg.karte.hintergrund.max_zoom, attribution: cfg.karte.hintergrund.attribution },
        gebaeude: { type: "vector", url: `pmtiles://${kacheln}`, attribution: esc(G.attribution) },
        zonen: { type: "vector", url: `pmtiles://${zonen}`, attribution: esc(cfg.wohnen.boris.attribution) },
        grenze: { type: "geojson", data: { type: "FeatureCollection", features: [] } } },
      layers: [
        { id: "hintergrund", type: "background", paint: { "background-color": "#f2f2f2" } },
        { id: "basis", type: "raster", source: "basis", paint: { "raster-saturation": -1, "raster-opacity": 0.9 } },
        { id: "zonen", type: "fill", source: "zonen", "source-layer": "bodenrichtwerte", layout: { visibility: "none" }, filter: brwFilter(""),
          paint: { "fill-color": brwFarbe, "fill-opacity": 0.8 } },
        { id: "zonen-linie", type: "line", source: "zonen", "source-layer": "bodenrichtwerte", layout: { visibility: "none" }, filter: brwFilter(""),
          paint: { "line-color": "#5c534c", "line-width": 1 } },
        { id: "flaeche", type: "fill", source: "gebaeude", "source-layer": "gebaeude", filter: ["!", geschaetzt],
          paint: { "fill-color": farbe, "fill-opacity": 0.85 } },
        { id: "umriss", type: "line", source: "gebaeude", "source-layer": "gebaeude", minzoom: 15, paint: { "line-color": "#1a1a1a", "line-width": 0.4, "line-opacity": 0.5 } },
        { id: "koerper", type: "fill-extrusion", source: "gebaeude", "source-layer": "gebaeude", filter: ["!", geschaetzt], layout: { visibility: "none" },
          paint: { "fill-extrusion-color": farbe, "fill-extrusion-height": ["get", "h"], "fill-extrusion-base": 0, "fill-extrusion-opacity": 0.9 } },
        { id: "auswahl", type: "line", source: "gebaeude", "source-layer": "gebaeude", filter: ["==", ["get", "id"], ""], paint: { "line-color": "#1a1a1a", "line-width": 3 } },
        { id: "grenze", type: "line", source: "grenze", paint: { "line-color": "#b8352e", "line-width": 2 } },
      ] },
      attributionControl: { compact: SCHMAL.matches },
    });
    map.addControl(new maplibregl.NavigationControl({ visualizePitch: true }), "top-right");
    window.stadtmonitorWohnen = { map };  // für Prüfungen im Browser
    const dauer = REDUZIERT ? 0 : 700;

    // Gebäude mit geschätzter Höhe: schraffiert (Farbe allein trägt die Information nicht), in 2D und 3D
    function schraffurEbenen() {
      const c = document.createElement("canvas");
      c.width = c.height = 8;
      const g = c.getContext("2d");
      g.fillStyle = "rgba(255, 255, 255, 0.85)"; g.fillRect(0, 0, 8, 8);
      g.strokeStyle = "#5c534c"; g.lineWidth = 2;
      g.beginPath(); g.moveTo(-2, 10); g.lineTo(10, -2); g.moveTo(-2, 2); g.lineTo(2, -2); g.moveTo(6, 10); g.lineTo(10, 6); g.stroke();
      map.addImage("schraffur", g.getImageData(0, 0, 8, 8));
      map.addLayer({ id: "flaeche-geschaetzt", type: "fill", source: "gebaeude", "source-layer": "gebaeude", filter: geschaetzt,
        paint: { "fill-pattern": "schraffur" } }, "umriss");
      map.addLayer({ id: "koerper-geschaetzt", type: "fill-extrusion", source: "gebaeude", "source-layer": "gebaeude", filter: geschaetzt,
        layout: { visibility: "none" }, paint: { "fill-extrusion-pattern": "schraffur", "fill-extrusion-height": ["get", "h"], "fill-extrusion-opacity": 0.9 } }, "auswahl");
    }
    const EBENEN_2D = ["flaeche", "flaeche-geschaetzt", "umriss"], EBENEN_3D = ["koerper", "koerper-geschaetzt"];
    function setAnsicht(a, bewegen = true) {
      ansicht = a;
      $("#ansicht-2d").setAttribute("aria-pressed", String(a === "2d"));
      $("#ansicht-3d").setAttribute("aria-pressed", String(a === "3d"));
      EBENEN_3D.forEach((id) => map.setLayoutProperty(id, "visibility", a === "3d" ? "visible" : "none"));
      EBENEN_2D.forEach((id) => map.setLayoutProperty(id, "visibility", a === "3d" ? "none" : "visible"));
      if (bewegen) map.easeTo({ pitch: a === "3d" ? 55 : 0, bearing: a === "3d" ? -20 : 0, duration: dauer });
      zustand();
    }
    // Kartenebene: Gebäude nach Funktion oder Bodenrichtwertzonen eines Stichtags (Gebäude dann einheitlich grau)
    function setEbene() {
      const st = ebeneSel.value.startsWith("bodenrichtwerte:") ? ebeneSel.value.slice(16) : null;
      const eig = ebeneSel.value === "eigentum";
      for (const id of ["zonen", "zonen-linie"]) {
        map.setLayoutProperty(id, "visibility", st ? "visible" : "none");
        map.setFilter(id, brwFilter(st || ""));
      }
      map.setPaintProperty("flaeche", "fill-color", st ? "#6b625b" : eig ? eigFarbe : farbe);
      map.setPaintProperty("flaeche", "fill-opacity", st ? 0.6 : eig ? 0.95 : 0.85);
      map.setPaintProperty("koerper", "fill-extrusion-color", st ? "#bdb6ae" : eig ? eigFarbe : farbe);
      legende();
      zustand();
    }
    function zustand() {
      const u = new URL(location.href);
      u.searchParams.set("ansicht", ansicht);
      if (ebeneSel.value !== "funktion") u.searchParams.set("ebene", ebeneSel.value); else u.searchParams.delete("ebene");
      if (sel.value) u.searchParams.set("gebiet", `ortsteil:${sel.value}`); else u.searchParams.delete("gebiet");
      if (gewaehlt) u.searchParams.set("gebaeude", gewaehlt); else u.searchParams.delete("gebaeude");
      history.replaceState(null, "", u);
      $("#zurueck").href = sel.value ? `./?gebiet=ortsteil:${encodeURIComponent(sel.value)}` : "./";
    }
    function stand() {
      const e = sel.value ? vorhanden[sel.value] : Object.values(vorhanden).reduce((s, x) => ({ gebaeude: s.gebaeude + x.gebaeude, hoehe_geschaetzt: s.hoehe_geschaetzt + x.hoehe_geschaetzt }), { gebaeude: 0, hoehe_geschaetzt: 0 });
      const name = sel.value ? (cfg.ortsteile.find((o) => o.slug === sel.value) || {}).name : `ganz ${cfg.stadt.name}`;
      $("#stand").textContent = `${name}: ${zahl(e.gebaeude)} Gebäude, davon ${zahl(e.hoehe_geschaetzt)} mit geschätzter Höhe.`
        + (map.getZoom() < G.zoom[0] ? " Zum Anzeigen der Gebäude heranzoomen." : "");
    }
    function zeigeGebiet(bewegen = true) {
      const slug = sel.value;
      const f = slug && flaechen && flaechen.features.find((x) => x.properties.slug === slug);
      map.getSource("grenze").setData(f ? { type: "FeatureCollection", features: [f] } : { type: "FeatureCollection", features: [] });
      const b = slug ? vorhanden[slug].kern : cfg.karte.bbox;
      if (bewegen) map.fitBounds([[b[0], b[1]], [b[2], b[3]]], { padding: SCHMAL.matches ? { top: 150, bottom: 140, left: 20, right: 20 } : { top: 90, bottom: 60, left: 400, right: aside.hidden ? 60 : 460 }, duration: dauer, maxZoom: 17 });
      stand();
      zustand();
    }
    const zoneHtml = (z) => `<dt>Bodenrichtwert</dt><dd>${zahl(z.wert)} €/m² <span class="meta">(${esc(z.art || "–")}, Gemarkung ${esc(z.gemarkung || "–")}, Stichtag ${esc(datum(z.stichtag))})</span></dd>`;
    const eigHtml = (id) => {
      const e = eigIndex.get(id);
      return e ? `<dt>Eigentum</dt><dd>${esc(e.kategorie_titel)}${e.name ? `: ${esc(e.name)}` : ""} <span class="meta">(${esc(e.sicherheit)}, geprüfte Erfassung)</span></dd>` : "";
    };
    function zeigeGebaeude(p, zone = null) {
      gewaehlt = p ? p.id : null;
      map.setFilter("auswahl", ["==", ["get", "id"], gewaehlt || ""]);
      const box = $("#gebaeude");
      box.hidden = !p && !zone;
      if (!p && zone) {
        box.innerHTML = `<h3>Bodenrichtwertzone</h3><dl>${zoneHtml(zone)}</dl><button type="button" class="link-btn" id="auswahl-weg">Auswahl aufheben</button>`;
        $("#auswahl-weg").addEventListener("click", () => { zeigeGebaeude(null); map.getCanvas().focus(); });
      }
      if (p) {
        const herkunft = p.hq === "geschätzt" ? `geschätzt (Standardhöhe, kein 3D-Modell gefunden)`
          : `gemessen (${p.hq === "Bauwerk" ? "Bauwerk" : "3D-Gebäudemodell LoD2"}, ${p.z === "gleich" ? "über die Kennung" : "über die Lage"} zugeordnet)`;
        const ot = (cfg.ortsteile.find((o) => o.slug === p.o) || {}).name;
        box.innerHTML = `<h3>Gebäude</h3><dl>
          <dt>Funktion (ALKIS)</dt><dd>${esc(p.f || "nicht angegeben")}</dd>
          <dt>Höhe</dt><dd>${zahl(p.h, 1)} m, ${esc(herkunft)}</dd>
          ${ot ? `<dt>Ortsteil</dt><dd>${esc(ot)}</dd>` : ""}
          <dt>Kennung (ALKIS-OID)</dt><dd><code>${esc(p.id)}</code></dd>${zone ? zoneHtml(zone) : ""}${eigHtml(p.id)}</dl>
          <button type="button" class="link-btn" id="auswahl-weg">Auswahl aufheben</button>`;
        $("#auswahl-weg").addEventListener("click", () => { zeigeGebaeude(null); map.getCanvas().focus(); });
      }
      zustand();
    }

    map.on("load", () => {
      document.querySelectorAll(".maplibregl-compact-show").forEach((e) => e.classList.remove("maplibregl-compact-show"));
      schraffurEbenen();
      setAnsicht(ansicht, false);
      if (ansicht === "3d") map.jumpTo({ pitch: 55, bearing: -20 });
      zeigeGebiet(true);
      setEbene();
      sel.addEventListener("change", () => { zeigeGebaeude(null); zeigeGebiet(true); module(); });
      ebeneSel.addEventListener("change", () => { zeigeGebaeude(null); setEbene(); });
      $("#module-inhalt").addEventListener("click", (e) => {
        if (!e.target.closest("[data-ebene]") || !stichtage.length) return;
        ebeneSel.value = `bodenrichtwerte:${stichtage[0]}`;
        setEbene();
        if (SCHMAL.matches) angaben(false);
        ebeneSel.focus();
      });
      $("#ansicht-2d").addEventListener("click", () => setAnsicht("2d"));
      $("#ansicht-3d").addEventListener("click", () => setAnsicht("3d"));
      const KLICK = [...EBENEN_2D.slice(0, 2), ...EBENEN_3D];
      map.on("click", (e) => {
        const ebenen = [...KLICK, ...(ebeneSel.value === "funktion" ? [] : ["zonen"])].filter((id) => map.getLayoutProperty(id, "visibility") !== "none");
        const fs = map.queryRenderedFeatures(e.point, { layers: ebenen });
        const g = fs.find((f) => f.layer.id !== "zonen"), z = fs.find((f) => f.layer.id === "zonen");
        if (g || z) zeigeGebaeude(g ? g.properties : null, z ? z.properties : null);
      });
      for (const ebene of [...KLICK, "zonen"]) {
        map.on("mouseenter", ebene, () => { map.getCanvas().style.cursor = "pointer"; });
        map.on("mouseleave", ebene, () => { map.getCanvas().style.cursor = ""; });
      }
      map.on("zoomend", stand);
      // Gebäude aus dem Link: auswählen, sobald seine Kachel geladen ist
      if (gewaehlt) {
        const suche = () => {
          const f = map.querySourceFeatures("gebaeude", { sourceLayer: "gebaeude", filter: ["==", ["get", "id"], gewaehlt] })[0];
          if (f) { zeigeGebaeude(f.properties); map.off("idle", suche); }
        };
        map.on("idle", suche);
      }
    });
  }
  start().catch((e) => { $("#stand").textContent = `Die Karte konnte nicht geladen werden (${e.message}).`; });
})();
