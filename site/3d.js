// 3D-Ansicht: Gebäude je Ortsteil als Grundriss mit gemessener Höhe (fill-extrusion), aus data/export/gebaeude3d/.
// Vereinfachte Darstellung ohne Dachformen; Höhenklassen und Hinweise aus stadt.json (gebaeude3d).
(function () {
  "use strict";
  const $ = (s) => document.querySelector(s);
  const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const FARBEN = ["#e88a84", "#d9534a", "#b8352e", "#8f2620", "#5e1814"];
  const json = (u) => fetch(u).then((r) => (r.ok ? r.json() : null)).catch(() => null);

  async function start() {
    const [cfg, index, flaechen] = await Promise.all([json("stadt.json"), json("data/export/gebaeude3d/index.json"), json("data/export/flaechen.json")]);
    const G = cfg.gebaeude3d;
    const params = new URLSearchParams(location.search);
    const gebiet = (params.get("gebiet") || "").replace(/^ortsteil:/, "");
    const vorhanden = index ? index.ortsteile : {};
    const liste = cfg.ortsteile.filter((o) => vorhanden[o.slug]);
    const sel = $("#ortsteil3d");
    sel.innerHTML = liste.map((o) => `<option value="${esc(o.slug)}">${esc(o.name)}</option>`).join("");
    sel.value = liste.some((o) => o.slug === gebiet) ? gebiet : (liste.find((o) => o.slug === "kernstadt") || liste[0] || {}).slug || "";
    $("#hinweis3d").textContent = `${G.hinweis} ${index && index.dateien.every((d) => /^BW_/i.test(d)) ? "Derzeit sind nur Bauwerke (Datei „BW“) eingelesen; die Gebäude (Datei „GB“) fehlen noch." : ""}`;
    const k = G.hoehen;
    $("#legende3d").innerHTML = FARBEN.map((f, i) => `<li><span class="sw" style="background:${f}" aria-hidden="true"></span>${i === 0 ? `unter ${k[0]} m` : i === k.length ? `ab ${k[k.length - 1]} m` : `${k[i - 1]}–${k[i]} m`}</li>`).join("");
    const schmal = matchMedia("(max-width: 700px)").matches;
    $("#mehr3d").open = !schmal;
    if (!liste.length) { $("#stand3d").textContent = "Noch keine 3D-Daten."; return; }

    maplibregl.setWorkerUrl("vendor/maplibre/maplibre-gl-csp-worker.js");
    const tiles = cfg.karte.hintergrund.grau;
    const map = new maplibregl.Map({
      container: "karte3d", center: [cfg.karte.zentrum[1], cfg.karte.zentrum[0]], zoom: 15, pitch: 55, bearing: -20, maxPitch: 70,
      style: { version: 8, sources: { basis: { type: "raster", tiles: [tiles], tileSize: 256, maxzoom: cfg.karte.hintergrund.max_zoom,
        attribution: cfg.karte.hintergrund.attribution } }, layers: [{ id: "hintergrund", type: "background", paint: { "background-color": "#f2f2f2" } }, { id: "basis", type: "raster", source: "basis", paint: { "raster-saturation": -1, "raster-opacity": 0.9 } }] },
      attributionControl: { compact: schmal, customAttribution: esc(G.attribution) },
    });
    map.addControl(new maplibregl.NavigationControl({ visualizePitch: true }), "top-right");
    map.on("load", () => {
      // kompakte Namensnennung (schmal) zunächst eingeklappt, wie „© Quellen“ auf der Karte
      document.querySelectorAll(".maplibregl-compact-show").forEach((e) => e.classList.remove("maplibregl-compact-show"));
      map.addSource("gebaeude", { type: "geojson", data: { type: "FeatureCollection", features: [] } });
      map.addSource("grenze", { type: "geojson", data: { type: "FeatureCollection", features: [] } });
      map.addLayer({ id: "grenze", type: "line", source: "grenze", paint: { "line-color": "#b8352e", "line-width": 2 } });
      map.addLayer({ id: "gebaeude", type: "fill-extrusion", source: "gebaeude", paint: {
        "fill-extrusion-color": ["step", ["get", "h"], FARBEN[0], k[0], FARBEN[1], k[1], FARBEN[2], k[2], FARBEN[3], k[3], FARBEN[4]],
        "fill-extrusion-height": ["get", "h"], "fill-extrusion-base": 0, "fill-extrusion-opacity": 0.9 } });
      laden(sel.value);
      sel.addEventListener("change", () => laden(sel.value));  // erst nach dem Laden der Karte (Quellen vorhanden)
    });
    let folge = 0;  // nur die zuletzt gewählte Antwort zeigen, auch wenn eine frühere später eintrifft
    async function laden(slug) {
      const nr = ++folge;
      const d = await json(`data/export/gebaeude3d/${encodeURIComponent(slug)}.json`);
      if (nr !== folge) return;
      if (!d || !d.features.length) { $("#stand3d").textContent = "Daten für diesen Ortsteil fehlen."; return; }
      map.getSource("gebaeude").setData(d);
      const f = flaechen && flaechen.features.find((x) => x.properties.slug === slug);
      map.getSource("grenze").setData(f ? { type: "FeatureCollection", features: [f] } : { type: "FeatureCollection", features: [] });
      const hs = d.features.map((x) => x.properties.h).sort((a, b) => a - b);
      const name = (cfg.ortsteile.find((o) => o.slug === slug) || {}).name || slug;
      $("#stand3d").textContent = `${name}: ${hs.length.toLocaleString("de-DE")} Objekte, Höhe Median ${hs[Math.floor(hs.length / 2)].toLocaleString("de-DE")} m, höchstes ${hs[hs.length - 1].toLocaleString("de-DE")} m`;
      // auf den bebauten Kern ausrichten: 5- bis 95-Prozent-Bereich der Gebäudelagen, einzelne entfernte Objekte zählen nicht
      const pts = d.features.map((x) => x.geometry.coordinates[0][0][0]);
      const q = (arr, p) => arr[Math.min(arr.length - 1, Math.floor(p * arr.length))];
      const xs = pts.map((c) => c[0]).sort((a, b) => a - b), ys = pts.map((c) => c[1]).sort((a, b) => a - b);
      const b = new maplibregl.LngLatBounds([q(xs, 0.05), q(ys, 0.05)], [q(xs, 0.95), q(ys, 0.95)]);
      map.fitBounds(b, { padding: schmal ? { top: 140, bottom: 120, left: 20, right: 20 } : { top: 90, bottom: 60, left: 420, right: 60 }, pitch: 55, bearing: -20, maxZoom: 17, duration: matchMedia("(prefers-reduced-motion: reduce)").matches ? 0 : 800 });
      $("#zurueck").href = `./?gebiet=ortsteil:${encodeURIComponent(slug)}`;
      const url = new URL(location.href); url.searchParams.set("gebiet", `ortsteil:${slug}`); history.replaceState(null, "", url);
    }
  }
  start().catch((e) => { $("#stand3d").textContent = `Die 3D-Ansicht konnte nicht geladen werden (${e.message}).`; });
})();
