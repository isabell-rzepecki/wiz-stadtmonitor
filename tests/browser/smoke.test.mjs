// Browser-Prüfung der zusammengestellten Seite (Playwright, Chromium; aufgebaut wie in der RIS-Karte Bonn):
// Start ohne Daten, 3D-Ansicht, Gebiet mit Vorgang und Prozesslinie, Termine, Zeitleiste, mobil, Dunkelmodus.
// Barrierefreiheit mit axe-core (WCAG 2.1 A und AA). Aufruf über tests/browser/run.sh.
import { test, before, after } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { createRequire } from "node:module";
import { chromium } from "playwright";

const SITE = process.env.SITE || "http://127.0.0.1:8766/";
const SITE_LEER = process.env.SITE_LEER || "http://127.0.0.1:8765/";
const AXE = readFileSync(createRequire(import.meta.url).resolve("axe-core/axe.min.js"), "utf8");
let browser;

// Kartenkacheln werden im Test nicht geladen (kein Netz nötig); ein leeres Bild genügt
const PNG = Buffer.from("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII=", "base64");

// WebGL für die 3D-Ansicht (MapLibre) über die Software-Darstellung
const ARGS = ["--use-gl=swiftshader", "--enable-unsafe-swiftshader"];
before(async () => { browser = await chromium.launch({ args: ARGS, ...(process.env.CHROMIUM ? { executablePath: process.env.CHROMIUM } : {}) }); });
after(async () => { await browser?.close(); });

async function open(base, path = "", { width = 1440, height = 900, dark = false } = {}) {
  const page = await browser.newPage({ viewport: { width, height }, colorScheme: dark ? "dark" : "light", bypassCSP: true });
  page.errors = [];
  page.on("pageerror", (e) => page.errors.push(String(e)));
  page.on("console", (m) => { if (m.type() === "error" && !/404|Failed to load resource/.test(m.text())) page.errors.push(m.text()); });
  await page.route("https://sgx.geodatenzentrum.de/**", (r) => r.fulfill({ contentType: "image/png", body: PNG }));
  await page.route("https://www.gds-srv.hessen.de/**", (r) => r.fulfill({ contentType: "image/png", body: PNG }));
  await page.goto(base + path, { waitUntil: "networkidle" });
  await page.waitForFunction(() => document.querySelector("#f-area")?.value);
  return page;
}

// Kartenoptionen (unten rechts) aufklappen, falls noch zu
async function kartenoptionen(page) {
  if ((await page.locator(".map-menu").getAttribute("aria-expanded")) !== "true") await page.locator(".map-menu").click();
}
async function weitereEbenen(page) {
  await kartenoptionen(page);
  const d = page.locator(".map-layers");
  if (!(await d.evaluate((e) => e.open))) await d.locator("summary").click();
}

async function axe(page) {
  if (!(await page.evaluate(() => "axe" in window))) await page.addScriptTag({ content: AXE });
  return page.evaluate(async () => (await window.axe.run(document, { runOnly: ["wcag2a", "wcag2aa"] }))
    .violations.map((v) => `${v.id}: ${v.nodes.map((n) => n.html.slice(0, 120)).join(" | ")}`));
}

test("ohne Daten: Startfenster mit Hinweis, Stadtname aus der Konfiguration, ohne Verstöße", async () => {
  const page = await open(SITE_LEER);
  assert.equal(await page.locator("#detail-heading").textContent(), "Los geht's");
  assert.match(await page.locator("#detail").textContent(), /Noch keine Daten/);
  assert.match(await page.locator(".brand").textContent(), /Witzenhausen/);
  assert.equal(await page.locator("#f-area").inputValue(), "stadt:alle");
  assert.equal(await page.locator("#f-area option").count(), 19, "ganze Stadt, Kernstadt, 16 Ortsbezirke, ohne Ortsbezug");
  assert.ok(await page.locator('.toggle[data-panel="timeline-wrap"]').isHidden(), "ohne Daten keine Zeitleiste");
  assert.deepEqual(await axe(page), []);
  assert.deepEqual(page.errors, []);
  await page.close();
});

test("Gebiet aus dem Link: Vorgang mit zwei Stationen, Ergebnis als Lücke, ohne Verstöße", async () => {
  const page = await open(SITE, "?gebiet=ortsteil:gertenbach");
  await page.locator('.toggle[data-panel="panel-list"]').click();
  const items = page.locator("#papers button[data-ref]");
  assert.equal(await items.count(), 1);
  await items.first().click();
  await page.waitForFunction(() => document.querySelector("#detail-heading").textContent === "Vorgang");
  assert.equal(await page.locator("#detail .steps li").count(), 2, "HFR und StVV");
  assert.equal(await page.locator("#detail .blackbox").count(), 2, "je Station „Ergebnis nicht veröffentlicht“");
  assert.match(await page.locator("#detail").textContent(), /Stufe B/);
  assert.match(await page.locator("#detail").textContent(), /Räumliche Überschneidung.*kein inhaltlicher Bezug/s);
  assert.ok(page.url().endsWith("#STV%2F066%2F2026"), page.url());
  assert.deepEqual(await axe(page), []);
  assert.deepEqual(page.errors, []);
  await page.close();
});

test("Karte: Ortsbezirk anklicken lädt das Gebiet, Hinweis zur Zuordnung", async () => {
  const page = await open(SITE);
  const pts = await page.evaluate(() => {
    const o = [];
    for (let y = 120; y < innerHeight - 60; y += 20) for (let x = 40; x < innerWidth - 500; x += 20) {
      const el = document.elementFromPoint(x, y);
      if (el && el.closest(".leaflet-gebiete-pane path")) o.push({ x, y });
    }
    return o;
  });
  assert.ok(pts.length, "keine anklickbare Fläche");
  await page.mouse.click(pts[Math.floor(pts.length / 2)].x, pts[Math.floor(pts.length / 2)].y);
  await page.waitForFunction(() => document.querySelector("#f-area").value.startsWith("ortsteil:"));
  assert.match(page.url(), /gebiet=ortsteil/);
  assert.equal(await page.locator(".map-legend").evaluate((e) => e.open), false, "Legende startet eingeklappt");
  await page.locator(".map-legend summary").click();
  await page.locator('.map-legend [data-about="about-verortung"]').click();
  assert.ok(await page.locator("#about").evaluate((e) => e.open));
  assert.match(await page.locator("#about").textContent(), /§ 6 der Hauptsatzung/);
  await page.locator("#about-close").click();
  assert.match(await page.locator(".leaflet-control-attribution").textContent(), /HVBG/);
  assert.deepEqual(await axe(page), []);
  assert.deepEqual(page.errors, []);
  await page.close();
});

test("Verfahrenspunkte sind standardmäßig ausgeblendet", async () => {
  const page = await open(SITE, "?gebiet=ortsteil:neuseesen");
  await page.locator('.toggle[data-panel="panel-list"]').click();
  assert.equal(await page.locator("#papers button[data-ref]").count(), 1);
  await page.locator("#more-filters summary").click();
  await page.locator("#f-verfahren").check();
  assert.equal(await page.locator("#papers button[data-ref]").count(), 2);
  assert.deepEqual(page.errors, []);
  await page.close();
});

test("Termine: kommende Sitzungen mit Tagesordnung", async () => {
  const page = await open(SITE);
  await page.locator('[data-mega="mega-mitmachen"]').click();
  await page.locator("#cta-termine").click();
  await page.waitForFunction(() => document.querySelectorAll("#termine .meeting").length > 0);
  // Sitzungen ab heute; die Testdaten enthalten zwei im November 2026
  const n = await page.locator("#termine .meeting").count();
  assert.ok(n <= 2);
  assert.match(await page.locator("#termine").textContent(), /Laufende Beteiligung der Öffentlichkeit.*Testplan/s);
  assert.deepEqual(await axe(page), []);
  assert.deepEqual(page.errors, []);
  await page.close();
});

test("Zeitleiste und Kennzahlen, ohne Verstöße", async () => {
  const page = await open(SITE);
  await page.locator('.toggle[data-panel="timeline-wrap"]').click();
  assert.ok(await page.locator("#timeline-wrap .tl-svg rect").count() > 0);
  assert.deepEqual(await axe(page), []);
  await page.locator('[data-mega="mega-mitmachen"]').click();
  await page.locator("#cta-stats").click();
  assert.ok(await page.locator("#stats .bar").count() > 0);
  assert.deepEqual(await axe(page), []);
  assert.deepEqual(page.errors, []);
  await page.close();
});

test("Systemeinstellung dunkel: Seite bleibt hell, Vorgang ohne Verstöße", async () => {
  const page = await open(SITE, "#STV%2F066%2F2026", { dark: true });
  await page.waitForFunction(() => document.querySelector("#detail-heading").textContent === "Vorgang");
  assert.equal(await page.evaluate(() => getComputedStyle(document.body).color), "rgb(26, 26, 26)");
  assert.deepEqual(await axe(page), []);
  await page.locator('.toggle[data-panel="panel-list"]').click();
  assert.deepEqual(await axe(page), []);
  assert.deepEqual(page.errors, []);
  await page.close();
});

test("Kartenebene Bauleitplanung: Nutzungshinweis in Legende und Namensnennung, ohne Verstöße", async () => {
  const page = await open(SITE);
  await weitereEbenen(page);
  await page.getByLabel("Bauleitplanung").check();
  await page.waitForFunction(() => document.querySelectorAll(".leaflet-overlay-pane path").length > 0);
  assert.match(await page.locator(".map-legend").textContent(), /nur für nicht kommerzielle Zwecke/);
  assert.match(await page.locator(".leaflet-control-attribution").textContent(), /Magistrat der Stadt Witzenhausen/);
  assert.match(page.url(), /plaene=1/);
  assert.deepEqual(await axe(page), []);
  assert.deepEqual(page.errors, []);
  await page.close();
});

test("Umweltebenen: zuschaltbar, Legende mit Hinweis, Quelle unter © Quellen, Zustand im Link, ohne Verstöße", async () => {
  const page = await open(SITE);
  await weitereEbenen(page);
  await page.getByLabel("Schutzgebiete Natur").check();
  await page.waitForFunction(() => document.querySelectorAll(".leaflet-overlay-pane path").length >= 2);
  const legende = await page.locator(".map-legend").textContent();
  assert.match(legende, /Naturschutzgebiet/);
  assert.match(legende, /nicht rechtsverbindlich/i);
  assert.match(await page.locator(".leaflet-control-attribution").textContent(), /Schutzgebiete: HMLU/);
  assert.match(page.url(), /ebenen=natur/);
  assert.deepEqual(await axe(page), []);
  await page.getByLabel("Hochwasser").check();  // ohne Datei: keine Fläche, kein Fehler
  assert.deepEqual(page.errors, []);
  await page.close();
});

test("Wohnen und Boden: Stichtage, getrennte Mietbegriffe, Vergleich, Ortsbezirk als Näherung, ohne Verstöße", async () => {
  const page = await open(SITE, "?gebiet=ortsteil:gertenbach");
  await page.locator('[data-mega="mega-mitmachen"]').click();
  await page.locator("#cta-wohnen").click();
  const text = await page.locator("#wohnen").textContent();
  assert.match(text, /Stichtag 01\.01\.2024/);
  assert.match(text, /Stichtag 15\.05\.2022/);
  assert.match(text, /Bestandsmiete Gertenbach/);
  assert.match(text, /Näherung/);
  assert.match(text, /Angebotsmiete/);
  assert.match(text, /Ortsübliche Vergleichsmiete/);
  assert.ok(await page.locator("#wohnen table.compare tbody tr").count() >= 5);
  assert.match(text, /Gebäude und Eigentum/);
  assert.match(text, /Pflichtangaben/);
  assert.deepEqual(await axe(page), []);
  await page.locator("[data-brw-on]").click();
  assert.match(page.url(), /ebenen=bodenrichtwerte/);
  assert.deepEqual(page.errors, []);
  await page.close();
});

test("Bodenrichtwerte 2026: eigene Bildebene mit Stichtag, Hinweis zum Heranzoomen, Zustand im Link, ohne Verstöße", async () => {
  const page = await open(SITE);
  let wms = 0;
  page.on("request", (r) => { if (r.url().startsWith("https://www.gds-srv.hessen.de/")) wms++; });
  await weitereEbenen(page);
  await page.getByLabel("Bodenrichtwerte 2026 (Karte der HVBG)").check();
  const legende = page.locator(".map-legend");
  await page.waitForFunction(() => /01\.01\.2026/.test(document.querySelector(".map-legend")?.textContent || ""));
  assert.match(await legende.textContent(), /näher heranzoomen/);
  assert.match(await legende.textContent(), /gds-srv\.hessen\.de/);
  assert.match(page.url(), /ebenen=bodenrichtwerte2026/);
  assert.equal(wms, 0, "unterhalb der Mindestzoomstufe keine Abrufe");
  for (let i = 0; i < 3; i++) { await page.locator(".leaflet-control-zoom-in").click(); await page.waitForTimeout(300); }
  await page.waitForFunction(() => !/näher heranzoomen/.test(document.querySelector(".map-legend")?.textContent || ""));
  assert.ok(wms > 0, "ab der Mindestzoomstufe Kartenbilder der HVBG");
  assert.match(await page.locator(".leaflet-control-attribution").textContent(), /Bodenrichtwerte 2026/);
  assert.deepEqual(await axe(page), []);
  assert.deepEqual(page.errors, []);
  await page.close();
});

test("Zuzug und Wegzug: Zeitreihe mit Tabelle, Gemeinden im Kreis, Kreisebene gekennzeichnet, Kartenebenen, ohne Verstöße", async () => {
  const page = await open(SITE);
  await page.locator('[data-mega="mega-mitmachen"]').click();
  await page.locator("#cta-wanderung").click();
  await page.waitForSelector("#wanderung svg.chart");
  const text = await page.locator("#wanderung").textContent();
  assert.match(text, /2015 bis 2024/);
  assert.match(text, /Zuzüge 2024\s*950/);
  assert.match(text, /Zahlen je Ortsteil sind nicht veröffentlicht/);
  assert.match(text, /gelten für den ganzen Kreis, nicht für Witzenhausen allein/);
  assert.match(text, /Hochschulstandort/);
  assert.equal(await page.locator("#wanderung table.compare tbody tr.own").count(), 1, "Witzenhausen in der Gemeindetabelle hervorgehoben");
  assert.deepEqual(await axe(page), []);
  await page.locator("#wanderung-jahr").selectOption("2015");
  await page.waitForFunction(() => /im Kreis, 2015/.test(document.querySelector("#wanderung caption")?.textContent + document.querySelectorAll("#wanderung caption")[1]?.textContent));
  await page.locator('[data-wanderung-on="wanderung_gemeinden"]').click();
  await page.waitForFunction(() => /Wanderungssaldo je 1 000 Einwohner, 2015/.test(document.querySelector(".map-legend")?.textContent || ""));
  assert.match(page.url(), /ebenen=wanderung_gemeinden/);
  assert.match(await page.locator(".leaflet-control-attribution").textContent(), /Hessisches Statistisches Landesamt/);
  await weitereEbenen(page);
  await page.getByLabel("Wanderung über die Kreisgrenze").check();
  await page.waitForFunction(() => /mindestens 30 Zu- und Fortzügen/.test(document.querySelector(".map-legend")?.textContent || ""));
  assert.ok(await page.locator(".leaflet-overlay-pane path").count() > 20);
  assert.deepEqual(await axe(page), []);
  assert.deepEqual(page.errors, []);
  await page.close();
});

test("Wahlen und Gremien: amtliche Ergebnisse, Lücke 2016, Ortsbeirat des Gebiets, ohne Verstöße", async () => {
  const page = await open(SITE, "?gebiet=ortsteil:gertenbach");
  await page.locator('[data-mega="mega-mitmachen"]').click();
  await page.locator("#cta-wahlen").click();
  const text = await page.locator("#wahlen").textContent();
  assert.match(text, /Stadtverordnetenwahl 15\.03\.2026/);
  assert.match(text, /Schnellmeldung/);
  assert.match(text, /Stadtverordnetenwahl 06\.03\.2016/);
  assert.match(text, /Gertenbach/);
  assert.equal(await page.locator("#wahlen h3:has-text('Ortsbeiräte') ~ .table-wrap tbody tr").count(), 1);
  assert.ok(await page.locator("#wahlen table").count() >= 4);
  assert.deepEqual(await axe(page), []);
  assert.deepEqual(page.errors, []);
  await page.close();
});

test("Desktop: Kartenoptionen und Quellen eingeklappt, Bauleitplanung unter den Ebenen", async () => {
  const page = await open(SITE);
  assert.equal(await page.locator(".map-whole").isVisible(), false);
  assert.equal(await page.locator(".leaflet-control-attribution").isVisible(), false);
  await page.locator(".map-sources").click();
  assert.ok(await page.locator(".leaflet-control-attribution").isVisible());
  await page.locator(".map-sources").click();
  await weitereEbenen(page);
  assert.ok(await page.locator(".map-whole").isVisible());
  assert.ok(await page.getByLabel("Bauleitplanung").isVisible());
  assert.deepEqual(await axe(page), []);
  assert.deepEqual(page.errors, []);
  await page.close();
});

test("Mobil: Kartenoptionen in einem Menü, ohne Verstöße", async () => {
  const page = await open(SITE, "", { width: 390, height: 844 });
  await page.locator('.toggle[data-panel="panel-detail"]').click();
  const menu = page.locator(".map-menu");
  assert.equal(await page.locator(".map-whole").isVisible(), false);
  assert.equal(await page.locator(".leaflet-control-attribution").isVisible(), false, "Namensnennung zugeklappt");
  await page.locator(".map-sources").click();
  assert.ok(await page.locator(".leaflet-control-attribution").isVisible());
  assert.equal(await page.locator(".map-sources").getAttribute("aria-expanded"), "true");
  await page.locator(".map-sources").click();
  await menu.click();
  assert.ok(await page.locator(".map-whole").isVisible());
  // Kartenoptionen als Kasten über der Leiste: nichts ragt über den Seitentitel
  const kasten = await page.locator(".leaflet-bottom.leaflet-right").boundingBox();
  const titel = await page.locator(".site-title").boundingBox();
  assert.ok(kasten.y >= titel.y + titel.height, `Kasten ${kasten.y} unter Titel ${titel.y + titel.height}`);
  assert.deepEqual(await axe(page), []);
  assert.deepEqual(page.errors, []);
  await page.close();
});

test("3D-Ansicht: Ortsteil aus dem Link, Höhenangaben, Hinweis und Namensnennung, Weg zurück, ohne Verstöße", async () => {
  const karte = await open(SITE, "?gebiet=ortsteil:kernstadt");
  await kartenoptionen(karte);
  const link = karte.locator(".map-3d");
  await link.click();
  await karte.waitForURL(/3d\.html\?gebiet=ortsteil(:|%3A)kernstadt/);
  await karte.close();
  const page = await browser.newPage({ viewport: { width: 1280, height: 800 }, bypassCSP: true });
  const errors = [];
  page.on("pageerror", (e) => errors.push(String(e)));
  await page.route("https://sgx.geodatenzentrum.de/**", (r) => r.fulfill({ contentType: "image/png", body: PNG }));
  await page.goto(SITE + "3d.html?gebiet=ortsteil:kernstadt", { waitUntil: "networkidle" });
  await page.waitForFunction(() => /Objekte/.test(document.querySelector("#stand3d").textContent));
  assert.match(await page.locator("#stand3d").textContent(), /^Kernstadt: \d+ Objekte, Höhe Median [\d,]+ m/);
  assert.equal(await page.locator("#ortsteil3d").inputValue(), "kernstadt");
  assert.match(await page.locator("#hinweis3d").textContent(), /Dachformen und Geländehöhe werden nicht dargestellt/);
  assert.match(await page.locator(".maplibregl-ctrl-attrib").textContent(), /HVBG.*vereinfacht/);
  await page.locator("#ortsteil3d").selectOption("ermschwerd");
  await page.waitForFunction(() => /^Ermschwerd/.test(document.querySelector("#stand3d").textContent));
  assert.match(page.url(), /gebiet=ortsteil%3Aermschwerd/);
  assert.equal(await page.locator("#zurueck").getAttribute("href"), "./?gebiet=ortsteil:ermschwerd");
  assert.deepEqual(await axe(page), []);
  assert.deepEqual(errors, []);
  await page.close();
});
