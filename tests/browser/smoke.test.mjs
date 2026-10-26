// Browser-Prüfung der zusammengestellten Seite (Playwright, Chromium; aufgebaut wie in der RIS-Karte Bonn):
// Start ohne Daten, Gebäude 2D/3D, Gebiet mit Vorgang und Prozesslinie, Termine, Zeitleiste, mobil, Dunkelmodus.
// Barrierefreiheit mit axe-core (WCAG 2.1 A und AA). Aufruf über tests/browser/run.sh.
import { test, before, after } from "node:test";
import assert from "node:assert/strict";
import { readFileSync, writeFileSync, mkdtempSync, rmSync } from "node:fs";
import { execFileSync } from "node:child_process";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { createRequire } from "node:module";
import { createHash } from "node:crypto";
import { chromium } from "playwright";
import sodium from "libsodium-wrappers";

const SITE = process.env.SITE || "http://127.0.0.1:8766/";
const SITE_LEER = process.env.SITE_LEER || "http://127.0.0.1:8765/";
const AXE = readFileSync(createRequire(import.meta.url).resolve("axe-core/axe.min.js"), "utf8");
let browser;

// Kartenkacheln werden im Test nicht geladen (kein Netz nötig); ein leeres Bild genügt
// Feste Startzeit (die Uhr läuft weiter): Die Testdaten enthalten Sitzungen im November 2026
const JETZT = new Date("2026-10-24T10:00:00Z");
const PNG = Buffer.from("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII=", "base64");

// WebGL für die Gebäude in 2D/3D (MapLibre) über die Software-Darstellung
const ARGS = ["--use-gl=swiftshader", "--enable-unsafe-swiftshader"];
before(async () => { browser = await chromium.launch({ args: ARGS, ...(process.env.CHROMIUM ? { executablePath: process.env.CHROMIUM } : {}) }); });
after(async () => { await browser?.close(); });

async function open(base, path = "", { width = 1440, height = 900, dark = false } = {}) {
  const page = await browser.newPage({ viewport: { width, height }, colorScheme: dark ? "dark" : "light", bypassCSP: true });
  await page.clock.setSystemTime(JETZT);
  page.errors = [];
  page.requests = [];  // alle Abrufe ab dem Laden (etwa fremde Kartendienste)
  page.on("request", (r) => page.requests.push(r.url()));
  page.on("pageerror", (e) => page.errors.push(String(e)));
  // fehlende Dateien sind nur in der Seite ohne Daten erwartet; mit Testdaten zählt jede fehlende Datei als Fehler
  const fehlendErlaubt = base === SITE_LEER;
  page.on("console", (m) => { if (m.type() === "error" && !(fehlendErlaubt && /404|Failed to load resource/.test(m.text()))) page.errors.push(m.text()); });
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
  // Sitzungen ab heute (24.10.2026); die Testdaten enthalten zwei im November 2026
  assert.equal(await page.locator("#termine .meeting").count(), 2);
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
  // der Nutzungshinweis ist sichtbar (Legende klappt beim Einschalten auf), nicht nur im Quelltext
  assert.ok(await page.locator(".map-legend .hint", { hasText: "nur für nicht kommerzielle Zwecke" }).isVisible());
  assert.match(await page.locator(".leaflet-control-attribution").textContent(), /Magistrat der Stadt Witzenhausen/);
  assert.match(page.url(), /plaene=1/);
  // Pläne auch per Tastatur: Auswahl in der Legende öffnet den Plan
  const wahl = page.locator(".map-legend select[data-plan-wahl]");
  await wahl.selectOption({ index: 1 });
  await page.waitForFunction(() => /plan$/.test(document.querySelector("#detail-heading")?.textContent || ""));
  assert.match(page.url(), /plan=/);
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

test("Wohnen und Boden (Fenster): Kennzahlen mit Stichtag, Ortsbezirk als Näherung, Verweis auf die Seite, ohne Verstöße", async () => {
  const page = await open(SITE, "?gebiet=ortsteil:gertenbach");
  await page.locator('[data-mega="mega-mitmachen"]').click();
  await page.locator("#cta-wohnen").click();
  const text = await page.locator("#wohnen").textContent();
  assert.match(text, /Stichtag 01\.01\.2024/);
  assert.match(text, /Stichtag 15\.05\.2022/);
  assert.match(text, /Bestandsmiete Gertenbach/);
  assert.match(text, /Näherung/);
  assert.match(text, /Kein Mietspiegel/);
  assert.equal(await page.locator("#wohnen table").count(), 0);  // Tabellen nur auf der Seite
  assert.equal(await page.locator('#wohnen a[href^="wohnen.html"]').getAttribute("href"), "wohnen.html?gebiet=ortsteil:gertenbach");
  assert.deepEqual(await axe(page), []);
  await page.locator("[data-brw-on]").click();
  assert.match(page.url(), /ebenen=bodenrichtwerte/);
  assert.deepEqual(page.errors, []);
  await page.close();
});

test("Bodenrichtwerte 2026: eigene Bildebene mit Stichtag, Hinweis zum Heranzoomen, nicht aus dem Link, ohne Verstöße", async () => {
  const page = await open(SITE);
  let wms = 0;
  page.on("request", (r) => { if (r.url().startsWith("https://www.gds-srv.hessen.de/")) wms++; });
  await weitereEbenen(page);
  await page.getByLabel("Bodenrichtwerte 2026 (Karte der HVBG)").check();
  const legende = page.locator(".map-legend");
  await page.waitForFunction(() => /01\.01\.2026/.test(document.querySelector(".map-legend")?.textContent || ""));
  assert.match(await legende.textContent(), /näher heranzoomen/);
  assert.match(await legende.textContent(), /gds-srv\.hessen\.de/);
  assert.doesNotMatch(page.url(), /bodenrichtwerte2026/, "fremder Kartendienst nur nach Einschalten, nicht über einen Link");
  assert.equal(wms, 0, "unterhalb der Mindestzoomstufe keine Abrufe");
  for (let i = 0; i < 3; i++) { await page.locator(".leaflet-control-zoom-in").click(); await page.waitForTimeout(300); }
  await page.waitForFunction(() => !/näher heranzoomen/.test(document.querySelector(".map-legend")?.textContent || ""));
  assert.ok(wms > 0, "ab der Mindestzoomstufe Kartenbilder der HVBG");
  assert.match(await page.locator(".leaflet-control-attribution").textContent(), /Bodenrichtwerte 2026/);
  assert.deepEqual(await axe(page), []);
  assert.deepEqual(page.errors, []);
  await page.close();
  // ein Link mit der Ebene schaltet sie nicht ein (Datenschutzhinweis: Übertragung nur nach Einschalten)
  const verlinkt = await open(SITE, "?ebenen=bodenrichtwerte2026&zoom=16");
  await weitereEbenen(verlinkt);
  assert.equal(await verlinkt.getByLabel("Bodenrichtwerte 2026 (Karte der HVBG)").isChecked(), false);
  assert.deepEqual(verlinkt.requests.filter((u) => u.startsWith("https://www.gds-srv.hessen.de/")), []);
  await verlinkt.close();
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

test("Wahlen und Gremien: amtliche Ergebnisse mit Stufe (Schnellmeldung), 2016, Ortsbeirat des Gebiets, ohne Verstöße", async () => {
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

test("Gebäude 2D/3D: Ortsteil aus dem Link, Gebäude anklicken, Umschalten, frühere 3D-Seite leitet weiter, ohne Verstöße", async () => {
  const karte = await open(SITE, "?gebiet=ortsteil:gertenbach");
  await kartenoptionen(karte);
  await karte.locator(".map-3d").click();
  await karte.waitForURL(/wohnen\.html\?ansicht=3d&gebiet=ortsteil(:|%3A)gertenbach/);
  await karte.close();
  const page = await browser.newPage({ viewport: { width: 1280, height: 800 }, bypassCSP: true });
  const errors = [];
  page.on("pageerror", (e) => errors.push(String(e)));
  page.on("console", (m) => { if (m.type() === "error") errors.push(m.text()); });
  await page.route("https://sgx.geodatenzentrum.de/**", (r) => r.fulfill({ contentType: "image/png", body: PNG }));
  await page.goto(SITE + "wohnen.html?gebiet=ortsteil:gertenbach", { waitUntil: "networkidle" });
  await page.waitForFunction(() => /^Gertenbach: [\d.]+ Gebäude/.test(document.querySelector("#stand").textContent));
  assert.equal(await page.locator("#ortsteil").inputValue(), "gertenbach");
  assert.match(await page.locator("#legende").textContent(), /Höhe geschätzt/);
  assert.match(await page.locator(".maplibregl-ctrl-attrib").textContent(), /HVBG.*ALKIS/);
  // ein Gebäude anklicken: Angaben mit Funktion, Höhe und Kennung (ALKIS-OID), Kennung im Link
  await page.waitForFunction(() => window.stadtmonitorWohnen && window.stadtmonitorWohnen.map.loaded()
    && window.stadtmonitorWohnen.map.queryRenderedFeatures({ layers: ["flaeche"] }).length > 0);
  const punkt = await page.evaluate(() => {
    const m = window.stadtmonitorWohnen.map, f = m.queryRenderedFeatures({ layers: ["flaeche"] })[0];
    const ring = f.geometry.type === "Polygon" ? f.geometry.coordinates[0] : f.geometry.coordinates[0][0];
    const p = m.project([ring.reduce((s, c) => s + c[0], 0) / ring.length, ring.reduce((s, c) => s + c[1], 0) / ring.length]);
    const r = m.getCanvas().getBoundingClientRect();
    return { x: r.left + p.x, y: r.top + p.y };
  });
  await page.mouse.click(punkt.x, punkt.y);
  await page.locator("#gebaeude").waitFor();
  assert.match(await page.locator("#gebaeude").textContent(), /Funktion \(ALKIS\).*Höhe.*m.*ALKIS-OID.*DEHE/s);
  assert.match(page.url(), /gebaeude=DEHE/);
  assert.deepEqual(await axe(page), []);
  // 3D: Körper statt Flächen, Zustand im Link
  await page.locator("#ansicht-3d").click();
  assert.equal(await page.locator("#ansicht-3d").getAttribute("aria-pressed"), "true");
  assert.equal(await page.evaluate(() => window.stadtmonitorWohnen.map.getLayoutProperty("koerper", "visibility")), "visible");
  assert.match(page.url(), /ansicht=3d/);
  assert.equal(await page.locator("#zurueck").getAttribute("href"), "./?gebiet=ortsteil:gertenbach");
  assert.deepEqual(errors, []);
  // Kartenebene Bodenrichtwerte: Zonen des gewählten Stichtags, Legende mit Klassen, Zustand im Link
  await page.locator("#ebene").selectOption("bodenrichtwerte:2022-01-01");
  assert.match(page.url(), /ebene=bodenrichtwerte(:|%3A)2022-01-01/);
  assert.match(await page.locator("#legende").textContent(), /unter 30 €\/m².*ab 80 €\/m²/s);
  assert.match(await page.locator("#hinweis").textContent(), /Stichtag 01\.01\.2022/);
  await page.waitForFunction(() => window.stadtmonitorWohnen.map.queryRenderedFeatures({ layers: ["zonen"] }).length > 0);
  assert.ok(await page.evaluate(() => window.stadtmonitorWohnen.map.queryRenderedFeatures({ layers: ["zonen"] })
    .every((f) => f.properties.stichtag === "2022-01-01" && f.properties.ez === "B")));
  assert.deepEqual(errors, []);
  // frühere 3D-Ansicht: Weiterleitung mit Ortsteil
  await page.goto(SITE + "3d.html?gebiet=ortsteil:gertenbach");
  await page.waitForURL(/wohnen\.html\?gebiet=ortsteil(:|%3A)gertenbach&ansicht=3d/);
  await page.close();
});

test("Wohnen und Eigentum (Seite): Module mit Zweck, Mietniveau, Verlauf, Eigentum ohne Erfassung, Schwellen, Tagesordnung, ohne Verstöße", async () => {
  const page = await browser.newPage({ viewport: { width: 1280, height: 800 }, bypassCSP: true });
  await page.clock.setSystemTime(JETZT);
  const errors = [];
  page.on("pageerror", (e) => errors.push(String(e)));
  page.on("console", (m) => { if (m.type() === "error") errors.push(m.text()); });
  await page.route("https://sgx.geodatenzentrum.de/**", (r) => r.fulfill({ contentType: "image/png", body: PNG }));
  // erfundener Vorgang mit Bezug zum Wohnen (die Testdaten enthalten keinen)
  const vorgang = { reference: "TEST/001/2026", name: "Bebauungsplan Testgebiet", date: "2026-10-01", verfahrenspunkt: false,
    locations: [{ ortsteil: "Gertenbach" }], process: [{ gremium: "Ortsbeirat Gertenbach" }] };
  await page.route("**/data/export/vorgaenge.json", (r) => r.fulfill({ contentType: "application/json", body: JSON.stringify({ vorgaenge: [vorgang] }) }));
  await page.goto(SITE + "wohnen.html?gebiet=ortsteil:gertenbach", { waitUntil: "networkidle" });
  const module = page.locator("#module");
  assert.equal(await page.locator("#angaben-knopf").getAttribute("aria-expanded"), "true");
  assert.match(await page.locator("#module-titel").textContent(), /Gertenbach/);
  assert.match(await page.locator("#modul-zweck").textContent(), /keinen Mietspiegel.*Grenzen/s);
  const miete = await page.locator("#modul-miete").textContent();
  assert.match(miete, /Kein Mietspiegel/);
  assert.match(miete, /Stichtag 15\.05\.2022/);
  assert.match(miete, /Bestandsmiete Gertenbach/);
  assert.ok(await page.locator("#modul-miete details.unter").nth(1).locator("tbody tr").count() >= 5);  // Nachbargemeinden
  // Module aufklappen und Inhalte prüfen
  for (const id of ["boden", "eigentum", "vergleich", "tagesordnung", "stand", "begriffe", "methode"]) await page.locator(`#modul-${id} > summary`).click();
  assert.match(await page.locator("#modul-boden").textContent(), /01\.01\.2022.*01\.01\.2024.*Angebotsmieten/s);
  const eig = await page.locator("#modul-eigentum").textContent();
  assert.match(eig, /Noch keine geprüfte Erfassung/);
  assert.match(eig, /Privatpersonen.*nur als Anteil je Ortsbezirk, ohne Namen/s);
  assert.match(await page.locator("#modul-vergleich").textContent(), /Noch keine geprüften Mietangaben.*ab 5 Angaben.*Je privater Vermieter:in: nie/s);
  await page.waitForFunction(() => !/Wird beim Öffnen geladen/.test(document.querySelector("#top-liste").textContent));
  assert.equal(await page.locator("#top-liste a").getAttribute("href"), "./?gebiet=ortsteil:gertenbach#TEST%2F001%2F2026");
  assert.match(await page.locator("#modul-stand").textContent(), /Gertenbach\s*[\d.]+\s*0\s*0,0 %/);
  assert.match(await page.locator("#modul-begriffe").textContent(), /Ortsübliche Vergleichsmiete.*Median/s);
  assert.deepEqual(await axe(page), []);
  // Knopf in „Verlauf“ schaltet die Kartenebene auf den jüngsten Stichtag
  await page.locator("#modul-boden [data-ebene]").click();
  assert.equal(await page.locator("#ebene").inputValue(), "bodenrichtwerte:2024-01-01");
  // anderer Ortsteil: Module neu, offene Module bleiben offen
  await page.locator("#ortsteil").selectOption("");
  assert.match(await page.locator("#module-titel").textContent(), /ganz /);
  assert.equal(await page.locator("#modul-eigentum").evaluate((d) => d.open), true);
  // ausblenden über „Angaben“
  await page.locator("#angaben-knopf").click();
  assert.equal(await module.isHidden(), true);
  assert.deepEqual(errors, []);
  await page.close();
  // schmal: Module zuerst zu, „Angaben“ öffnet sie
  const mobil = await browser.newPage({ viewport: { width: 390, height: 844 }, bypassCSP: true });
  await mobil.route("https://sgx.geodatenzentrum.de/**", (r) => r.fulfill({ contentType: "image/png", body: PNG }));
  await mobil.goto(SITE + "wohnen.html", { waitUntil: "networkidle" });
  assert.equal(await mobil.locator("#module").isHidden(), true);
  // Kasten unten links: schmal zunächst eingeklappt, der Knopf klappt ihn auf und wieder zu
  const infoKnopf = mobil.locator("#info-knopf");
  assert.equal(await infoKnopf.getAttribute("aria-expanded"), "false");
  assert.equal(await mobil.locator("#ebene").isHidden(), true);
  await infoKnopf.click();
  assert.equal(await mobil.locator("#ebene").isVisible(), true);
  await infoKnopf.click();
  assert.equal(await mobil.locator("#legende").isHidden(), true);
  await mobil.locator("#angaben-knopf").click();
  assert.equal(await mobil.locator("#module").isVisible(), true);
  assert.deepEqual(await axe(mobil), []);
  await mobil.close();
});

test("Wohnen und Eigentum: Ebene Eigentum aus der geprüften Datei, privat nie je Gebäude, Erfassungsstand, ohne Verstöße", async () => {
  // erfundene geprüfte Erfassungen über echten Gebäuden des Ortsteils (Gebäude: HVBG; Kategorien und Namen erfunden)
  const geb = JSON.parse(readFileSync(new URL("../../data/geo/hvgg/gebaeude.geojson", import.meta.url), "utf8")).features
    .filter((f) => f.properties.o === "gertenbach" && f.geometry.type === "Polygon").slice(0, 40);
  const mitte = (f) => { const r = f.geometry.coordinates[0].slice(0, -1); return [r.reduce((s, c) => s + c[0], 0) / r.length, r.reduce((s, c) => s + c[1], 0) / r.length]; };
  const eig = { type: "FeatureCollection", stand: "2026-10-26", features: geb.map((f, i) => ({ type: "Feature", geometry: f.geometry,
    properties: { id: f.properties.id, kategorie: i % 2 ? "kom" : "geno", kategorie_titel: i % 2 ? "Stadt" : "Wohnungsgenossenschaft",
      sicherheit: "gesichert", beleg: "ortskenntnis", ...(i % 2 ? {} : { name: "Wohnbau Test eG" }) } })) };
  const page = await browser.newPage({ viewport: { width: 1280, height: 800 }, bypassCSP: true });
  const errors = [];
  page.on("pageerror", (e) => errors.push(String(e)));
  page.on("console", (m) => { if (m.type() === "error") errors.push(m.text()); });
  await page.route("https://sgx.geodatenzentrum.de/**", (r) => r.fulfill({ contentType: "image/png", body: PNG }));
  await page.route("**/data/export/wohnen.json", async (r) => {
    const res = await r.fetch(), w = await res.json();
    w.eigentum_karte = true;
    w.eigentum_anteile = { stand: "2026-10-26", ortsbezirke: { gertenbach: { gebaeude: 1295, erfasst: 40, kategorien: { geno: 20, kom: 20 }, privat: null,
      privat_hinweis: "zu wenige Angaben; nicht in „erfasst“ enthalten" } } };
    await r.fulfill({ response: res, json: w });
  });
  await page.route("**/data/export/karte/eigentum_gebaeude.json", (r) => r.fulfill({ json: eig }));
  await page.goto(SITE + "wohnen.html?gebiet=ortsteil:gertenbach&ebene=eigentum", { waitUntil: "networkidle" });
  await page.waitForFunction(() => window.stadtmonitorWohnen && window.stadtmonitorWohnen.map.loaded());
  assert.equal(await page.locator("#ebene").inputValue(), "eigentum");
  const legende = await page.locator("#legende").textContent();
  assert.match(legende, /Stadt.*Wohnungsgenossenschaft|Wohnungsgenossenschaft.*Stadt/s);
  assert.match(legende, /Privatperson/);
  assert.match(await page.locator("#hinweis").textContent(), /nie einzeln/);
  // ein erfasstes Gebäude anklicken: Kategorie und Name der juristischen Person
  let getroffen = false;
  for (const f of geb.filter((x, i) => i % 2 === 0)) {
    const pt = await page.evaluate(async (c) => {
      const m = window.stadtmonitorWohnen.map;
      m.jumpTo({ center: c, zoom: 18 });
      await new Promise((ok) => m.once("idle", ok));
      const p = m.project(c), r = m.getCanvas().getBoundingClientRect();
      return { x: r.left + p.x, y: r.top + p.y, id: (m.queryRenderedFeatures(p, { layers: ["flaeche"] })[0] || { properties: {} }).properties.id };
    }, mitte(f));
    if (pt.id !== f.properties.id) continue;
    await page.mouse.click(pt.x, pt.y);
    await page.locator("#gebaeude").waitFor();
    assert.match(await page.locator("#gebaeude").textContent(), /Eigentum\s*Wohnungsgenossenschaft: Wohnbau Test eG/);
    getroffen = true;
    break;
  }
  assert.ok(getroffen, "kein erfasstes Gebäude anklickbar");
  await page.locator("#modul-stand > summary").click();
  assert.match(await page.locator("#modul-stand").textContent(), /Gertenbach\s*[\d.]+\s*40\s*[\d,]+ %\s*zu wenige Angaben/);
  await page.locator("#modul-eigentum > summary").click();
  assert.match(await page.locator("#modul-eigentum").textContent(), /Geprüfte Erfassung, Stand 26\.10\.2026/);
  assert.deepEqual(await axe(page), []);
  assert.deepEqual(errors, []);
  await page.close();
});

// Erfassung: Testschlüssel und Testcode nur im Test (die Konfiguration im Repository hat weder Schlüssel noch Codes)
const TESTCODE = "ABCD-EFGH-JKMN-PQRS";
async function erfassenSeite({ aktiv = true, zugang = true, ohneStelle = false, viewport = { width: 1280, height: 800 } } = {}) {
  await sodium.ready;
  const kp = sodium.crypto_box_keypair(), V = sodium.base64_variants.ORIGINAL;
  const ctx = await browser.newContext({ viewport, acceptDownloads: true, serviceWorkers: "block", bypassCSP: true });
  const page = await ctx.newPage();
  page.errors = [];
  page.on("pageerror", (e) => page.errors.push(String(e)));
  page.on("console", (m) => { if (m.type() === "error") page.errors.push(m.text()); });
  await page.route("https://sgx.geodatenzentrum.de/**", (r) => r.fulfill({ contentType: "image/png", body: PNG }));
  const hash = createHash("sha256").update(`wiz-einladung:${TESTCODE.replace(/-/g, "")}`).digest("hex");
  page.konfig = { zugang, ohneStelle };
  await page.route("**/stadt.json", async (r) => {
    const res = await r.fetch(), c = await res.json();
    Object.assign(c.wohnen_eigentum, { privat_namen_aktiv: aktiv, mietangaben_aktiv: aktiv });
    c.wohnen_eigentum.erfassung.datenschutz.verantwortlich = aktiv && !page.konfig.ohneStelle ? "Teststelle (erfunden)" : null;
    if (aktiv) c.wohnen_eigentum.erfassung.schluessel = { key_id: "test-1", alg: "libsodium-sealedbox-x25519", public_key: sodium.to_base64(kp.publicKey, V) };
    c.wohnen_eigentum.erfassung.einladungen = !page.konfig.zugang ? [] : page.konfig.bis ? [{ hash, bis: page.konfig.bis }] : [hash];
    await r.fulfill({ response: res, json: c });
  });
  page.schluesseldatei = (dir) => { const p = join(dir, "pg.json"); writeFileSync(p, JSON.stringify({ key_id: "test-1", alg: "libsodium-sealedbox-x25519",
    public_key: sodium.to_base64(kp.publicKey, V), secret_key: sodium.to_base64(kp.privateKey, V) })); return p; };
  page.oeffnen = (ct) => JSON.parse(sodium.to_string(sodium.crypto_box_seal_open(sodium.from_base64(ct, V), kp.publicKey, kp.privateKey)));
  page.oeffnenText = (ct) => sodium.to_string(sodium.crypto_box_seal_open(sodium.from_base64(ct, V), kp.publicKey, kp.privateKey));
  await page.goto(SITE + "erfassen.html", { waitUntil: "networkidle" });
  return page;
}
async function freischalten(page) {
  await page.fill("#code", "abcd efgh jkmn pqrs");
  await page.locator("#zugang button").click();
  await page.waitForFunction(() => window.stadtmonitorErfassen && window.stadtmonitorErfassen.map.loaded());
  await page.selectOption("#ortsteil", "gertenbach");
  await page.waitForFunction(() => window.stadtmonitorErfassen.map.queryRenderedFeatures({ layers: ["flaeche"] }).length > 0);
}
async function gebaeudeAntippen(page) {
  const pt = await page.evaluate(() => {
    const m = window.stadtmonitorErfassen.map, f = m.queryRenderedFeatures({ layers: ["flaeche"] })[0];
    const ring = f.geometry.type === "Polygon" ? f.geometry.coordinates[0] : f.geometry.coordinates[0][0];
    const q = m.project([ring.reduce((s, c) => s + c[0], 0) / ring.length, ring.reduce((s, c) => s + c[1], 0) / ring.length]);
    const r = m.getCanvas().getBoundingClientRect();
    return { x: r.left + q.x, y: r.top + q.y };
  });
  await page.mouse.click(pt.x, pt.y);
  await page.locator("#zu-a").waitFor();
}
const exportDatei = async (page, typ) => {
  const [dl] = await Promise.all([page.waitForEvent("download"), page.locator(`[data-export="${typ}"]`).click()]);
  return { name: dl.suggestedFilename(), inhalt: JSON.parse(readFileSync(await dl.path(), "utf8")) };
};

test("Erfassung ohne Freigaben: Code nötig, ohne Schlüssel kein Speichern, Mietangaben aus, Datenschutzhinweis, ohne Verstöße", async () => {
  const page = await erfassenSeite({ aktiv: false });
  assert.equal(await page.locator("#tafel-titel").textContent(), "Zugang");
  assert.equal(await page.locator("#ortsteil-wahl").isVisible(), false);
  assert.deepEqual(await axe(page), []);
  await page.fill("#code", "1234");
  await page.locator("#zugang button").click();
  assert.match(await page.locator("#code-fehler").textContent(), /16 Zeichen/);
  await page.fill("#code", "ZZZZ-ZZZZ-ZZZZ-ZZZZ");
  await page.locator("#zugang button").click();
  await page.waitForFunction(() => /nicht \(mehr\) gültig/.test(document.querySelector("#code-fehler").textContent));
  await freischalten(page);
  assert.match(await page.locator("#tafel-inhalt").textContent(), /Speichern noch nicht möglich.*Erfasser-ID E-227c7469/s);
  await gebaeudeAntippen(page);
  assert.equal(await page.locator("#zu-b").isDisabled(), true);
  await page.locator("#zu-a").click();
  assert.equal(await page.locator('#form-a button[type="submit"]').isDisabled(), true);
  await page.locator('input[name="kategorie"][value="privat"]').check();
  assert.equal(await page.locator('input[name="name_privat"]').count(), 0);  // Namensfeld nicht freigegeben
  assert.match(await page.locator("#feld-privat").textContent(), /nicht freigegeben/);
  await page.locator("#knopf-datenschutz").click();
  assert.match(await page.locator("#datenschutz").textContent(), /keinen automatischen Upload.*Verantwortlich.*noch nicht benannt/s);
  assert.deepEqual(await axe(page), []);
  assert.deepEqual(page.errors, []);
  await page.context().close();
});

test("Erfassung als Probe: ohne Code und Schlüssel, Formulare prüfen, nichts gespeichert; ohne benannte Stelle nichts speicherbar", async () => {
  const page = await erfassenSeite({ aktiv: false, zugang: false });
  await page.locator("#probe").click();
  await page.waitForFunction(() => window.stadtmonitorErfassen && window.stadtmonitorErfassen.map.loaded());
  await page.selectOption("#ortsteil", "gertenbach");
  await page.waitForFunction(() => window.stadtmonitorErfassen.map.queryRenderedFeatures({ layers: ["flaeche"] }).length > 0);
  assert.equal(await page.locator("#probe-band").isVisible(), true);
  assert.equal(await page.locator("#knopf-eintraege").isVisible(), false);
  await page.locator("#tafel-inhalt").getByText("Erfasser-ID Probe").waitFor();
  await gebaeudeAntippen(page);
  await page.locator("#zu-b").click();  // in der Probe auch Mietangaben
  await page.locator('#form-b button[type="submit"]').click();
  assert.match(await page.locator(".fehlerliste").textContent(), /Einwilligung: fehlt/);
  await page.locator('input[name="einwilligung"]').check();
  await page.fill('input[name="nettokalt_eur"]', "450");
  await page.fill('input[name="wohnflaeche_m2"]', "65");
  await page.fill('input[name="vertragsbeginn_jahr"]', "2019");
  await page.locator('#form-b button[type="submit"]').click();
  assert.match(await page.locator(".erfolg").textContent(), /Probe: Die Angaben sind gültig\. Nichts wurde gespeichert/);
  assert.equal(await page.locator("#widerrufscode").count(), 0);
  const n = await page.evaluate(async () => {
    const d = await new Promise((ok) => { const r = indexedDB.open("wiz-erfassung"); r.onsuccess = () => ok(r.result); });
    const z = (s) => new Promise((ok) => { const g = d.transaction(s).objectStore(s).count(); g.onsuccess = () => ok(g.result); });
    return [await z("eintraege"), await z("meta")];
  });
  assert.deepEqual(n, [0, 0]);
  assert.deepEqual(await axe(page), []);
  assert.deepEqual(page.errors, []);
  await page.context().close();
  // echter Zugang mit Schlüssel, aber ohne benannte verantwortliche Stelle: nichts speicherbar, Hinweis sichtbar
  const p2 = await erfassenSeite({ ohneStelle: true });
  await freischalten(p2);
  assert.match(await p2.locator("#tafel-inhalt").textContent(), /verantwortliche Stelle ist noch nicht benannt/);
  await gebaeudeAntippen(p2);
  await p2.locator("#zu-b").click();
  assert.equal(await p2.locator('#form-b button[type="submit"]').isDisabled(), true);
  assert.match(await p2.locator("#form-b").textContent(), /verantwortliche Stelle ist noch nicht benannt/);
  await p2.locator("#abbrechen").click();
  await p2.locator("#zu-a").click();
  assert.equal(await p2.locator('#form-a button[type="submit"]').isDisabled(), true);
  await p2.context().close();
});

test("Erfassung mit Testschlüssel: Formulare prüfen, versiegelt speichern, Export entschlüsselbar, kein Klartext im Gerät, Widerruf", async () => {
  const page = await erfassenSeite();
  await freischalten(page);
  // Formular A: Hausnummer abgewiesen, Name der Privatperson zusätzlich versiegelt
  await gebaeudeAntippen(page);
  const id = (await page.locator("#tafel-inhalt code").textContent()).trim();
  await page.locator("#zu-a").click();
  await page.locator('#form-a button[type="submit"]').click();
  assert.match(await page.locator(".fehlerliste").textContent(), /Eigentum: fehlt.*Beleg: fehlt/s);
  // Screenreader: Fehlerliste als Meldung mit Fokus, Gruppen mit Legende, jedes Feld mit Namen
  assert.equal(await page.evaluate(() => document.activeElement.classList.contains("fehlerliste")), true);
  assert.equal(await page.locator(".fehlerliste").getAttribute("role"), "alert");
  for (const g of ["Wem gehört das Gebäude?", "Werden Wohnungen vermietet?", "Wie sicher ist die Angabe?"]) await page.getByRole("group", { name: g }).waitFor();
  await page.getByRole("radio", { name: /Privatperson/ }).waitFor();
  await page.getByRole("combobox", { name: "Beleg" }).waitFor();
  assert.equal(await page.evaluate(() => [...document.querySelectorAll("#form-a input, #form-a select, #form-a textarea")]
    .filter((x) => x.type !== "hidden" && !x.closest("[hidden]") && !(x.labels && x.labels.length)).length), 0);
  await page.locator('input[name="kategorie"][value="privat"]').check();
  await page.fill('input[name="name_privat"]', "Erika Testname");
  await page.selectOption('select[name="beleg_art"]', "ortskenntnis");
  await page.fill('input[name="lage_hinweis"]', "Hauptstraße 12");
  await page.fill('textarea[name="bemerkung"]', "Kontakt test@example.org");
  await page.locator('#form-a button[type="submit"]').click();
  const fa = await page.locator(".fehlerliste").textContent();
  assert.match(fa, /Lage: keine Ziffern/);
  assert.match(fa, /Bemerkung: keine E-Mail-Adressen/);
  assert.equal(await page.locator('input[name="lage_hinweis"]').getAttribute("aria-invalid"), "true");
  assert.deepEqual(await axe(page), []);
  await page.fill('input[name="lage_hinweis"]', "Hauptstraße");
  await page.fill('textarea[name="bemerkung"]', "");
  await page.locator('#form-a button[type="submit"]').click();
  await page.locator(".erfolg").waitFor();
  // Formular B: ohne Einwilligung nicht speicherbar; Fläche ergibt die Klasse
  await page.locator("#weiter").click();
  await gebaeudeAntippen(page);
  await page.locator("#zu-b").click();
  await page.fill('input[name="nettokalt_eur"]', "450");
  await page.fill('input[name="wohnflaeche_m2"]', "72");
  await page.fill('input[name="vertragsbeginn_jahr"]', "2019");
  assert.equal(await page.locator('select[name="wohnflaeche_klasse"]').inputValue(), "60-79");
  assert.match(await page.locator("#je-m2").textContent(), /6,25 € je m²/);
  await page.locator('#form-b button[type="submit"]').click();
  assert.match(await page.locator(".fehlerliste").textContent(), /Einwilligung: fehlt/);
  // Fassung v3: Stelle und Kontakt eingesetzt, keine Platzhalter sichtbar, Datenschutzhinweis erreichbar
  const wtext = await page.locator(".einwilligung").textContent();
  assert.match(wtext, /Ich willige ein, dass Teststelle \(erfunden\) meine Angabe/);
  assert.doesNotMatch(wtext, /\{stelle\}|\{kontakt\}/);
  await page.locator("#zu-datenschutz").click();
  assert.equal(await page.locator("#datenschutz").isVisible(), true);
  await page.locator("#datenschutz button").click();
  await page.getByRole("group", { name: "Einwilligung" }).waitFor();
  await page.getByRole("checkbox", { name: "Ich willige ein." }).waitFor();
  await page.getByRole("spinbutton", { name: /Nettokaltmiete im Monat/ }).waitFor();
  assert.equal(await page.evaluate(() => [...document.querySelectorAll("#form-b input, #form-b select")].filter((x) => !(x.labels && x.labels.length)).length), 0);
  assert.deepEqual(await axe(page), []);
  await page.locator('input[name="einwilligung"]').check();
  await page.locator('input[name="erfassungsweg"][value="im_gespraech_mit_team"]').check();
  await page.locator('#form-b button[type="submit"]').click();
  await page.locator(".erfolg").waitFor();
  const widerrufscode = (await page.locator("#widerrufscode").textContent()).trim();
  assert.match(widerrufscode, /^[0-9A-F]{4}-[0-9A-F]{4}$/);
  // im Gerät nur versiegelte Einträge
  const ablage = await page.evaluate(async () => {
    const d = await new Promise((ok) => { const r = indexedDB.open("wiz-erfassung"); r.onsuccess = () => ok(r.result); });
    return new Promise((ok) => { const g = d.transaction("eintraege").objectStore("eintraege").getAll(); g.onsuccess = () => ok(g.result); });
  });
  assert.equal(ablage.length, 2);
  // Klartextmerkmale statt bloßer Ziffern: „450“ kann zufällig in Kennung, Zeitstempel oder Chiffrat vorkommen
  assert.doesNotMatch(JSON.stringify(ablage), /Erika|Testname|nettokalt|wohnflaeche|Hauptstra|60-79/);
  assert.deepEqual(Object.keys(ablage.find((e) => e.typ === "miete")).sort(), ["alg", "ciphertext", "erstellt", "exportiert", "id", "key_id", "typ"]);
  // Export je Formular, mit dem Testschlüssel entschlüsselbar und gegen die Schemata gültig
  await page.locator("#zu-eintraege").click();
  const a = await exportDatei(page, "eigentum");
  assert.equal(a.name, `eigentum_E-227c7469_${new Date().toISOString().slice(0, 10)}.bin`);
  assert.equal(a.inhalt.anzahl, 1);
  const ra = page.oeffnen(a.inhalt.eintraege[0].ciphertext);
  assert.equal(ra.objekt.id, id);
  assert.equal(ra.kategorie, "privat");
  assert.equal(ra.vermieter_schluessel, "V-neu");
  assert.equal(ra.erfasser, "E-227c7469");
  assert.equal(page.oeffnenText(ra.name_privat_enc.ciphertext), "Erika Testname");
  assert.doesNotMatch(JSON.stringify(ra), /Erika/);
  const b = await exportDatei(page, "miete");
  assert.match(b.name, /^mieten_E-227c7469_/);
  const rb = page.oeffnen(b.inhalt.eintraege[0].ciphertext);
  assert.deepEqual([rb.nettokalt_eur, rb.wohnflaeche_m2, rb.wohnflaeche_klasse, rb.vertragsbeginn_jahr, rb.erfassungsweg, rb.erfasser],
    [450, 72, "60-79", 2019, "im_gespraech_mit_team", "E-227c7469"]);
  assert.equal(rb.einwilligung.erteilt, true);
  assert.equal(rb.angabe_id.replace(/-/g, "").slice(0, 8).toUpperCase(), widerrufscode.replace("-", ""));
  assert.equal(rb.einwilligung.textversion, "2026-10-26-v3");
  for (const [schema, rec] of [["erfassung_eigentum", ra], ["mietangabe", rb]]) {
    const s = await (await fetch(SITE + `schemas/${schema}.json`)).json();
    assert.deepEqual(await page.evaluate(([s, r]) => window.ErfassenPruefung.schema(s, r), [s, rec]), []);
  }
  assert.match(await page.locator("#export-meldung").textContent(), /1 Eintrag\)/);
  // Exportdateien der App im Prüfskript der Prüfgruppe (Python, PyNaCl) einlesen
  const dir = mkdtempSync(join(tmpdir(), "pruefung-"));
  try {
    const dateien = [a, b].map((x) => { const p = join(dir, x.name); writeFileSync(p, JSON.stringify(x.inhalt)); return p; });
    const aus = execFileSync("python3", ["tools/pruefen.py", "einlesen", "-a", join(dir, "arbeit"), "-s", page.schluesseldatei(dir), "-p", "P-test", ...dateien],
      { cwd: new URL("../..", import.meta.url).pathname, encoding: "utf8" });
    assert.match(aus, /^2 aufgenommen, 0 abgewiesen/);
  } finally { rmSync(dir, { recursive: true, force: true }); }
  // exportierte löschen
  page.once("dialog", (d) => d.accept());
  await page.locator("#loeschen").click();
  await page.waitForFunction(() => /gelöscht/.test(document.querySelector("#export-meldung").textContent));
  assert.equal(await page.locator("#anzahl").textContent(), "0");
  assert.deepEqual(await axe(page), []);
  assert.deepEqual(page.errors, []);
  // Widerruf: Hash nicht mehr in der Konfiguration
  page.konfig.zugang = false;
  await page.reload({ waitUntil: "networkidle" });
  assert.match(await page.locator("#tafel-inhalt").textContent(), /widerrufen/);
  // abgelaufener Code (Eintrag mit Ablaufdatum): nicht freischaltbar
  Object.assign(page.konfig, { zugang: true, bis: "2020-01-01" });
  await page.reload({ waitUntil: "networkidle" });
  await page.fill("#code", TESTCODE);
  await page.locator("#zugang button").click();
  await page.waitForFunction(() => /abgelaufen \(gültig bis 01\.01\.2020\)/.test(document.querySelector("#code-fehler").textContent));
  await page.context().close();
});

test("Erfassung offline: Service Worker speichert Programm und Gebäude, Bereichsabfragen aus dem Speicher", async () => {
  const ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, bypassCSP: true });
  const page = await ctx.newPage();
  await page.route("https://sgx.geodatenzentrum.de/**", (r) => r.fulfill({ contentType: "image/png", body: PNG }));
  await page.goto(SITE + "erfassen.html", { waitUntil: "networkidle" });
  await page.evaluate(() => navigator.serviceWorker.ready);
  await page.waitForFunction(async () => !!(await caches.match(new URL("data/export/karte/gebaeude.pmtiles", location.href).href)));
  await ctx.setOffline(true);
  await page.reload({ waitUntil: "load" });
  await page.locator("#code").waitFor();
  assert.match(await page.locator("#netz").textContent(), /Offline/);
  const r = await page.evaluate(async () => {
    const x = await fetch("data/export/karte/gebaeude.pmtiles", { headers: { Range: "bytes=0-126" } });
    return { status: x.status, laenge: (await x.arrayBuffer()).byteLength, bereich: x.headers.get("Content-Range") };
  });
  assert.equal(r.status, 206);
  assert.equal(r.laenge, 127);
  assert.match(r.bereich, /^bytes 0-126\/\d+$/);
  await ctx.close();
});

test("Tour: Start aus dem Startfenster, alle Schritte mit Pfeiltaste, Beispielvorgang, Esc beendet, ohne Verstöße", async () => {
  const page = await open(SITE, "?gebiet=ortsteil:gertenbach");
  await page.locator("#detail [data-tour]").click();
  const card = page.locator(".tour-card");
  await card.waitFor();
  assert.match(await page.locator("#tour-title").textContent(), /Willkommen/);
  assert.deepEqual(await axe(page), []);
  const titel = [];
  for (let k = 0; k < 20; k++) {
    const [ist, von] = (await page.locator("#tour-count").textContent()).match(/(\d+) von (\d+)/).slice(1);
    if (ist === von) break;
    await page.keyboard.press("ArrowRight");
    await page.waitForFunction((ist) => !document.querySelector("#tour-count")?.textContent.startsWith(`Schritt ${ist} `), ist);
    titel.push(await page.locator("#tour-title").textContent());
  }
  for (const t of ["Suche", "Gebiet wählen", "Die Karte", "Kartenoptionen und Ebenen", "Die Liste", "Der Vorgang", "Die Prozesslinie", "Sitzungen und Themen", "Über den Stadtmonitor"])
    assert.ok(titel.includes(t), `Schritt „${t}“ fehlt: ${titel.join(", ")}`);
  assert.equal(await page.locator("#detail-heading").textContent(), "Vorgang", "Beispielvorgang geöffnet");
  await page.keyboard.press("Escape");
  assert.equal(await page.locator(".tour").count(), 0);
  assert.deepEqual(page.errors, []);
  await page.close();
});
