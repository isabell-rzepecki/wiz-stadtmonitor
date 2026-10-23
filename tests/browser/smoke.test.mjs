// Browser-Prüfung der zusammengestellten Seite (Playwright, Chromium; aufgebaut wie in der RIS-Karte Bonn):
// Start ohne Daten, Gebiet mit Vorgang und Prozesslinie, Termine, Zeitleiste, mobil, Dunkelmodus.
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

before(async () => { browser = await chromium.launch(process.env.CHROMIUM ? { executablePath: process.env.CHROMIUM } : {}); });
after(async () => { await browser?.close(); });

async function open(base, path = "", { width = 1440, height = 900, dark = false } = {}) {
  const page = await browser.newPage({ viewport: { width, height }, colorScheme: dark ? "dark" : "light", bypassCSP: true });
  page.errors = [];
  page.on("pageerror", (e) => page.errors.push(String(e)));
  page.on("console", (m) => { if (m.type() === "error" && !/404|Failed to load resource/.test(m.text())) page.errors.push(m.text()); });
  await page.route("https://sgx.geodatenzentrum.de/**", (r) => r.fulfill({ contentType: "image/png", body: PNG }));
  await page.goto(base + path, { waitUntil: "networkidle" });
  await page.waitForFunction(() => document.querySelector("#f-area")?.value);
  return page;
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
  assert.ok(page.url().endsWith("#STV%2F066%2F2026"), page.url());
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

test("Dunkelmodus: Vorgang ohne Verstöße", async () => {
  const page = await open(SITE, "#STV%2F066%2F2026", { dark: true });
  await page.waitForFunction(() => document.querySelector("#detail-heading").textContent === "Vorgang");
  assert.deepEqual(await axe(page), []);
  await page.locator('.toggle[data-panel="panel-list"]').click();
  assert.deepEqual(await axe(page), []);
  assert.deepEqual(page.errors, []);
  await page.close();
});

test("Mobil: Kartenoptionen in einem Menü, ohne Verstöße", async () => {
  const page = await open(SITE, "", { width: 390, height: 844 });
  await page.locator('.toggle[data-panel="panel-detail"]').click();
  const menu = page.locator(".map-menu");
  assert.equal(await page.locator(".map-whole").isVisible(), false);
  await menu.click();
  assert.ok(await page.locator(".map-whole").isVisible());
  assert.deepEqual(await axe(page), []);
  assert.deepEqual(page.errors, []);
  await page.close();
});
