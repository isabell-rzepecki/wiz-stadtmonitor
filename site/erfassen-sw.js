// Offline für die Erfassung (erfassen.html): Programm, Konfiguration, Schemata und alle Gebäude der Stadt (eine PMTiles-Datei,
// ca. 3 MB) werden beim Installieren gespeichert. Abrufe aus dem Netz zuerst, bei fehlendem Netz aus dem Speicher.
// Die Gebäudedatei kommt immer aus dem Speicher; Bereichsabfragen (Range) beantwortet der Worker aus der ganzen Datei.
// Gespeichert werden nur öffentliche Dateien; Einträge liegen versiegelt in IndexedDB, nie in diesem Speicher.
const SPEICHER = "wiz-erfassung-v2";
const DATEIEN = ["erfassen.html", "erfassen.js", "erfassen-pruefung.js", "erfassen.css", "wohnen.css", "page.css", "favicon.svg", "erfassen.webmanifest",
  "datenschutz.html", "impressum.html",
  "stadt.json", "schemas/erfassung_eigentum.json", "schemas/mietangabe.json", "data/export/karte/gebaeude_index.json",
  "vendor/maplibre/maplibre-gl-csp.js", "vendor/maplibre/maplibre-gl-csp-worker.js", "vendor/maplibre/maplibre-gl.css", "vendor/pmtiles/pmtiles.js",
  "vendor/libsodium/libsodium.js", "vendor/libsodium/libsodium-wrappers.js"];
const KACHELN = "data/export/karte/gebaeude.pmtiles";
const url = (p) => new URL(p, self.registration.scope.replace(/[^/]*$/, "")).href;

self.addEventListener("install", (e) => {
  e.waitUntil((async () => {
    const c = await caches.open(SPEICHER);
    // einzeln, damit eine fehlende Datei (etwa ohne Daten) nicht die ganze Installation abbricht
    await Promise.all([...DATEIEN, KACHELN].map((p) => c.add(new Request(url(p), { cache: "reload" })).catch(() => {})));
    await self.skipWaiting();
  })());
});
self.addEventListener("activate", (e) => {
  e.waitUntil((async () => {
    for (const k of await caches.keys()) if (k !== SPEICHER) await caches.delete(k);
    await self.clients.claim();
  })());
});

let ganz = null;  // Gebäudedatei im Arbeitsspeicher, für Bereichsabfragen
async function bereich(req) {
  const c = await caches.open(SPEICHER);
  let r = await c.match(url(KACHELN));
  if (!r) {
    r = await fetch(url(KACHELN), { cache: "reload" });
    if (!r.ok) return r;
    await c.put(url(KACHELN), r.clone());
  }
  ganz ||= await r.arrayBuffer();
  const m = /bytes=(\d+)-(\d*)/.exec(req.headers.get("Range") || "");
  if (!m) return new Response(ganz, { status: 200, headers: { "Content-Type": "application/octet-stream", "Content-Length": String(ganz.byteLength) } });
  const start = Number(m[1]), ende = Math.min(m[2] ? Number(m[2]) : ganz.byteLength - 1, ganz.byteLength - 1);
  return new Response(ganz.slice(start, ende + 1), { status: 206, headers: { "Content-Type": "application/octet-stream",
    "Content-Range": `bytes ${start}-${ende}/${ganz.byteLength}`, "Content-Length": String(ende - start + 1) } });
}

self.addEventListener("fetch", (e) => {
  const req = e.request;
  if (req.method !== "GET" || new URL(req.url).origin !== self.location.origin) return;
  if (req.url.split("?")[0] === url(KACHELN)) { e.respondWith(bereich(req)); return; }
  e.respondWith((async () => {
    try {
      const r = await fetch(req);
      if (r.ok && r.status === 200) (await caches.open(SPEICHER)).put(req, r.clone()).catch(() => {});
      return r;
    } catch (err) {
      const c = await caches.match(req, { ignoreSearch: true });
      if (c) return c;
      throw err;
    }
  })());
});
