// Wohnen und Eigentum: alle Gebäude der Stadt in 2D (Grundriss) und 3D (Grundriss mit gemessener Höhe, fill-extrusion).
// Zweck der Seite (Übergabe v0.4.2): Für die Stadt gibt es keinen Mietspiegel; die Seite soll eine Vergleichsgrundlage
// für tatsächlich gezahlte Mieten schaffen. Grundlage dafür sind die Gebäude mit ihrer ALKIS-OID als Schlüssel; dieselbe
// Kennung gilt in 2D, in 3D und später in der Erfassung. Eigentum und Mieten zeigt die Seite erst nach der Prüfung und
// nur nach den Veröffentlichungsregeln (docs/uebergabe-v0.4.2/veroeffentlichungsregeln.tsv).
// Daten: data/export/karte/gebaeude.pmtiles (Vektorkacheln, pipeline/gebaeude.py) und gebaeude_index.json.
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

  async function start() {
    const [cfg, index, flaechen] = await Promise.all([json("stadt.json"), json("data/export/karte/gebaeude_index.json"), json("data/export/flaechen.json")]);
    const G = cfg.gebaeude;
    const params = new URLSearchParams(location.search);
    let ansicht = params.get("ansicht") === "3d" ? "3d" : "2d";
    let gewaehlt = params.get("gebaeude") || null;
    const vorhanden = (index && index.ortsteile) || {};
    const liste = cfg.ortsteile.filter((o) => vorhanden[o.slug]);
    const sel = $("#ortsteil");
    sel.innerHTML = `<option value="">ganze Stadt</option>` + liste.map((o) => `<option value="${esc(o.slug)}">${esc(o.name)}</option>`).join("");
    const gebiet = (params.get("gebiet") || "").replace(/^ortsteil:/, "");
    sel.value = liste.some((o) => o.slug === gebiet) ? gebiet : "";
    $("#legende").innerHTML = GRUPPEN.map((g) => `<li><span class="sw" style="background:${g.farbe}" aria-hidden="true"></span>${esc(g.titel)}</li>`).join("")
      + `<li><span class="sw sw-geschaetzt" aria-hidden="true"></span>Höhe geschätzt (${zahl(G.standardhoehe_m)} m, ohne 3D-Modell)</li>`;
    $("#hinweis").textContent = `${cfg.gebaeude3d.hinweis} Grundrisse aus ALKIS, Höhe aus den 3D-Gebäudemodellen LoD2; ohne passendes Modell gilt eine Standardhöhe. Eigentum und Vermietung zeigt die Karte nicht.`;
    $("#mehr").open = !SCHMAL.matches;
    if (!index) { $("#stand").textContent = "Noch keine Gebäudedaten."; return; }

    maplibregl.setWorkerUrl("vendor/maplibre/maplibre-gl-csp-worker.js");
    const protokoll = new pmtiles.Protocol();
    maplibregl.addProtocol("pmtiles", protokoll.tile);
    const kacheln = new URL("data/export/karte/gebaeude.pmtiles", location.href).href;
    const map = new maplibregl.Map({
      container: "karte", center: [cfg.karte.zentrum[1], cfg.karte.zentrum[0]], zoom: 14, maxPitch: 70,
      style: { version: 8, sources: {
        basis: { type: "raster", tiles: [cfg.karte.hintergrund.grau], tileSize: 256, maxzoom: cfg.karte.hintergrund.max_zoom, attribution: cfg.karte.hintergrund.attribution },
        gebaeude: { type: "vector", url: `pmtiles://${kacheln}`, attribution: esc(G.attribution) },
        grenze: { type: "geojson", data: { type: "FeatureCollection", features: [] } } },
      layers: [
        { id: "hintergrund", type: "background", paint: { "background-color": "#f2f2f2" } },
        { id: "basis", type: "raster", source: "basis", paint: { "raster-saturation": -1, "raster-opacity": 0.9 } },
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
    function zustand() {
      const u = new URL(location.href);
      u.searchParams.set("ansicht", ansicht);
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
      if (bewegen) map.fitBounds([[b[0], b[1]], [b[2], b[3]]], { padding: SCHMAL.matches ? { top: 150, bottom: 140, left: 20, right: 20 } : { top: 90, bottom: 60, left: 400, right: 60 }, duration: dauer, maxZoom: 17 });
      stand();
      zustand();
    }
    function zeigeGebaeude(p) {
      gewaehlt = p ? p.id : null;
      map.setFilter("auswahl", ["==", ["get", "id"], gewaehlt || ""]);
      const box = $("#gebaeude");
      box.hidden = !p;
      if (p) {
        const herkunft = p.hq === "geschätzt" ? `geschätzt (Standardhöhe, kein 3D-Modell gefunden)`
          : `gemessen (${p.hq === "Bauwerk" ? "Bauwerk" : "3D-Gebäudemodell LoD2"}, ${p.z === "gleich" ? "über die Kennung" : "über die Lage"} zugeordnet)`;
        const ot = (cfg.ortsteile.find((o) => o.slug === p.o) || {}).name;
        box.innerHTML = `<h3>Gebäude</h3><dl>
          <dt>Funktion (ALKIS)</dt><dd>${esc(p.f || "nicht angegeben")}</dd>
          <dt>Höhe</dt><dd>${zahl(p.h, 1)} m, ${esc(herkunft)}</dd>
          ${ot ? `<dt>Ortsteil</dt><dd>${esc(ot)}</dd>` : ""}
          <dt>Kennung (ALKIS-OID)</dt><dd><code>${esc(p.id)}</code></dd></dl>
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
      sel.addEventListener("change", () => { zeigeGebaeude(null); zeigeGebiet(true); });
      $("#ansicht-2d").addEventListener("click", () => setAnsicht("2d"));
      $("#ansicht-3d").addEventListener("click", () => setAnsicht("3d"));
      for (const ebene of [...EBENEN_2D.slice(0, 2), ...EBENEN_3D]) {
        map.on("click", ebene, (e) => { if (e.features && e.features[0]) zeigeGebaeude(e.features[0].properties); });
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
