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
  assert.equal(await page.locator('#detail a[href="vorgang/stv-066-2026/"]').count(), 1, "Link zur Seite des Vorgangs");
  assert.deepEqual(await axe(page), []);
  assert.deepEqual(page.errors, []);
  await page.close();
});

test("Ergebnis aus einer Bekanntmachung: Satzung als letzte Station, Beschluss an der Sitzung, Raute in der Zeitleiste, ohne Verstöße", async () => {
  const page = await open(SITE, "#STV%2F488%2F2025");
  await page.waitForFunction(() => document.querySelector("#detail-heading").textContent === "Vorgang");
  const d = page.locator("#detail");
  assert.equal(await d.locator(".steps .step-ergebnis").count(), 1);
  assert.match(await d.locator(".step-ergebnis").textContent(), /Bekanntgemacht: Satzung.*abgeschlossen.*Hundesteuer.*Bekanntmachung Nr\. 186\/2025.*Beschluss vom 16\.12\.2025/s);
  assert.equal(await d.locator(".blackbox").count(), 0, "die beschließende Sitzung zeigt das Ergebnis statt der Lücke");
  assert.match(await d.locator(".steps li").first().textContent(), /beschlossen – belegt durch die Bekanntmachung Nr\. 186\/2025/);
  assert.equal(await d.locator('.step-ergebnis a[href$="186-2025-Satzung-Hundesteuer-OR-9.1.pdf"]').count(), 1);
  await d.locator(".step-ergebnis .jump").click();
  await page.waitForSelector(".tl-ergebnis");
  assert.deepEqual(await axe(page), []);
  assert.deepEqual(page.errors, []);
  await page.close();
});

test("Stellungnahme eines Ortsbeirats: Station im Beschlussvorgang, Zählung mit Grenze, Rückweg über „Gehört zu“, ohne Verstöße", async () => {
  const page = await open(SITE, "#STV%2F485%2F2025");
  await page.waitForFunction(() => document.querySelector("#detail-heading").textContent === "Vorgang");
  const d = page.locator("#detail");
  const stationen = d.locator(".steps li");
  assert.equal(await stationen.count(), 2);
  assert.match(await stationen.first().textContent(), /Stellungnahme: Ortsbeirat Neuseesen.*17\.11\.2025.*zugeordnet über: Haushalt 2026/s, "zeitlich vor der Stadtverordnetenversammlung");
  assert.match(await d.locator(".facts").textContent(), /1 von 16 hatten die Angelegenheit auf der Tagesordnung.*nicht veröffentlicht/s);
  await d.locator('.step-stellungnahme [data-open-ref="160/2025-TOP4"]').click();
  await page.waitForFunction(() => /Stellungnahme zur Haushaltssatzung/.test(document.querySelector("#detail h3")?.textContent || ""));
  assert.match(await d.locator(".facts").textContent(), /Gehört zu.*Haushaltsjahr 2026.*zugeordnet über: Haushalt 2026/s);
  await d.locator('.facts [data-open-ref="STV/485/2025"]').click();
  await page.waitForFunction(() => /^Beratung und Beschlussfassung über die Haushaltssatzung/.test(document.querySelector("#detail h3")?.textContent || ""));
  await d.locator(".step-stellungnahme .jump").click();
  await page.waitForSelector(".tl-stellungnahme");
  assert.deepEqual(await axe(page), []);
  assert.deepEqual(page.errors, []);
  await page.close();
});

test("Nur eigene Domain: Datenquellen als Seite, interner Bereich, Hinweise per E-Mail, ohne Verstöße", async () => {
  for (const pfad of ["quellen.html", "intern/", "teilen/", "ortsteile/", "ortsteil/gertenbach/", "sitzungen/", "gremien/", "gremium/stvv/", "barrierefreiheit.html", "einfache-sprache.html", "vorgang/stv-066-2026/"]) {
    const page = await browser.newPage({ bypassCSP: true });
    const fehler = [];
    page.on("pageerror", (e) => fehler.push(String(e)));
    page.on("console", (m) => { if (m.type() === "error") fehler.push(m.text()); });
    await page.goto(SITE + pfad, { waitUntil: "networkidle" });
    assert.ok(await page.locator("h1").count(), pfad);
    assert.deepEqual(await axe(page), [], pfad);
    assert.deepEqual(fehler, [], pfad);
    await page.close();
  }
  const page = await open(SITE);
  assert.match(await page.locator("#cta-report").getAttribute("href"), /^mailto:/);
  // Hauptmenü nach Fragen der Nutzenden: Politik, Stadt in Zahlen, Über (mit Hinweis, Daten und Quellen), Teilen
  if (await page.locator('.nav [data-mega="mega-politik"] span').first().isVisible())
    assert.deepEqual((await page.locator(".nav .menu-btn span:not(.visually-hidden)").allTextContents()).map((s) => s.trim()), ["Politik", "Stadt in Zahlen", "Über", "Teilen"]);
  assert.equal(await page.locator("#mega-ueber #cta-report, #mega-ueber #about-open, #mega-ueber #sources").count(), 3);
  // Tastatur und Maus: Menüknöpfe mit Hinweis; Ortsteil auf der Karte mit Tab und Eingabe wählbar, mit Hinweis beim Fokus
  assert.match(await page.locator('.nav [data-mega="mega-stadt"]').getAttribute("title"), /Ortsteile, Wohnen/);
  const flaeche = page.locator('path[role="button"][aria-label^="Ortsteil "]').first();
  await flaeche.waitFor({ state: "attached" });
  const ortsteil = (await flaeche.getAttribute("aria-label")).match(/Ortsteil (.+) auswählen/)[1];
  await flaeche.focus();
  await page.locator(".leaflet-tooltip").first().waitFor();
  await page.keyboard.press("Enter");
  await page.waitForFunction(() => document.querySelector("#f-area").value.startsWith("ortsteil:"));
  assert.match(await page.locator("#f-area option:checked").textContent(), new RegExp(ortsteil));
  assert.equal(await page.locator("#mega-stadt #cta-wohnen, #mega-stadt #cta-struktur, #mega-stadt #cta-wanderung, #mega-stadt a[href='ortsteile/']").count(), 4);
  assert.equal(await page.locator("#mega-politik #cta-termine, #mega-politik #cta-stats, #mega-politik #cta-wahlen, #mega-politik a[href='gremien/']").count(), 4);
  assert.equal(await page.locator('a[href*="github"]').count(), 0);
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

test("Termine im Ortsteil: Abo des Ortsbeirats, Punkte der Stadtgremien mit Ortsbezug, ohne Verstöße", async () => {
  const page = await open(SITE, "?gebiet=ortsteil:gertenbach");
  await page.locator('[data-mega="mega-politik"]').click();
  await page.locator("#cta-termine").click();
  await page.waitForSelector("#termine .abo");
  const abo = page.locator("#termine .abo");
  assert.match(await abo.textContent(), /Gertenbach: Ortsbeirat und Punkte der Stadtgremien zu Gertenbach/);
  const ics = await (await page.request.get(await abo.locator("a", { hasText: "Kalenderadresse" }).first().getAttribute("href"))).text();
  assert.match(ics, /X-WR-CALNAME:Stadtmonitor: Gertenbach/);
  assert.match(ics.replace(/\r\n /g, ""), /Tagesordnungspunkte mit Bezug zu Gertenbach:/, "Stadtgremium nur mit den Punkten zu Gertenbach");
  assert.deepEqual(await axe(page), []);
  assert.deepEqual(page.errors, []);
  await page.close();
});

test("Verfahrenspunkte sind standardmäßig ausgeblendet", async () => {
  const page = await open(SITE, "?gebiet=ortsteil:neuseesen");
  await page.locator('.toggle[data-panel="panel-list"]').click();
  assert.equal(await page.locator("#papers button[data-ref]").count(), 2, "Stromtrasse und Stellungnahme zum Haushalt");
  await page.locator("#more-filters summary").click();
  await page.locator("#f-verfahren").check();
  assert.equal(await page.locator("#papers button[data-ref]").count(), 3);
  assert.deepEqual(page.errors, []);
  await page.close();
});

test("Termine: kommende Sitzungen mit Tagesordnung", async () => {
  const page = await open(SITE);
  await page.locator('[data-mega="mega-politik"]').click();
  await page.locator("#cta-termine").click();
  await page.waitForFunction(() => document.querySelectorAll("#termine .meeting").length > 0);
  // Sitzungen ab heute (24.10.2026); die Testdaten enthalten zwei im November 2026
  assert.equal(await page.locator("#termine .meeting").count(), 2);
  assert.match(await page.locator("#termine").textContent(), /Laufende Beteiligung der Öffentlichkeit.*Testplan/s);
  // Abonnieren: Kalender (webcal und https) und Feed, Dateien gültig und mit der Sitzung vom 10.11.2026
  const abo = page.locator("#termine .abo");
  assert.match(await abo.textContent(), /Termine abonnieren.*Stadtverordnetenversammlung, Ausschüsse und Beiräte.*Alle Gremien/s);
  assert.match(await abo.locator("a", { hasText: "Kalender abonnieren" }).first().getAttribute("href"), /^webcal:\/\/.*\/data\/export\/abo\/stadt\.ics$/);
  const ics = await (await page.request.get(await abo.locator("a", { hasText: "Kalenderadresse" }).nth(1).getAttribute("href"))).text();
  assert.match(ics, /^BEGIN:VCALENDAR\r\n.*SUMMARY:Stadtverordnetenversammlung\r\n.*DTSTART;TZID=Europe\/Berlin:20261110T190000.*END:VCALENDAR\r\n$/s);
  assert.ok(ics.split("\r\n").every((z) => new TextEncoder().encode(z).length <= 75), "Zeilen höchstens 75 Oktette");
  const atom = await (await page.request.get(await abo.locator("a", { hasText: "Feed" }).nth(1).getAttribute("href"))).text();
  assert.match(atom, /<feed xmlns="http:\/\/www.w3.org\/2005\/Atom".*<title>Stadtverordnetenversammlung am 10\.11\.2026<\/title>/s);
  assert.deepEqual(await axe(page), []);
  assert.deepEqual(page.errors, []);
  await page.close();
});

test("Zeitleiste und Kennzahlen, ohne Verstöße", async () => {
  const page = await open(SITE);
  await page.locator('.toggle[data-panel="timeline-wrap"]').click();
  assert.ok(await page.locator("#timeline-wrap .tl-svg rect").count() > 0);
  assert.deepEqual(await axe(page), []);
  await page.locator('[data-mega="mega-politik"]').click();
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
  await page.locator('[data-mega="mega-stadt"]').click();
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

test("Strukturdaten: Werte des Ortsteils und der Stadt, Vergleich mit Verlauf, sortierbare Tabelle, Kartenebene mit Legende, Hinweis im Vorgang, ohne Verstöße", async () => {
  const page = await open(SITE, "?gebiet=ortsteil:gertenbach");
  await page.locator('[data-mega="mega-stadt"]').click();
  await page.locator("#cta-struktur").click();
  await page.waitForSelector("#struktur table");
  const text = await page.locator("#struktur").textContent();
  assert.match(text, /Gebiet: Gertenbach/);
  assert.match(text, /Stichtag 15\.05\.2022/);
  assert.match(text, /ökologischer Fehlschluss/);
  assert.match(text, /Einwohner\s*Erläuterung.*922.*15\.202/s);  // Gertenbach und Stadt aus derselben Quelle
  assert.match(text, /abgeleitet/);
  assert.match(text, /Eschwege.*Hannoversch Münden.*Bad Wildungen.*Schwalmstadt/s);
  assert.ok(await page.locator("#struktur svg.spark").count() >= 10, "Verlauf je Kennzahl als kleine Linie");
  assert.match(text, /Fortschreibung des Zensus 2011/);
  // Albshausen: unter der Schwelle nicht ausgewiesen, nicht als Zahl
  const albs = page.locator("#struktur-tabelle tbody tr", { hasText: "Albshausen" });
  assert.match(await albs.textContent(), /nicht ausgewiesen/);
  // Sortieren: Spaltenkopf mit aria-sort, Fokus bleibt auf dem Knopf
  await page.locator('#struktur [data-struktur-sort="wert"]').click();
  assert.equal(await page.locator('#struktur-tabelle th[aria-sort="ascending"]').count(), 1);
  assert.equal(await page.evaluate(() => document.activeElement.dataset.strukturSort), "wert");
  await page.locator('#struktur [data-struktur-sort="wert"]').click();
  assert.equal(await page.locator('#struktur-tabelle th[aria-sort="descending"]').count(), 1);
  const erste = await page.locator("#struktur-tabelle tbody tr").first().textContent();
  assert.doesNotMatch(erste, /nicht ausgewiesen/);  // Lücken stehen beim Sortieren am Ende
  await page.locator("#struktur details.erl summary").first().click();
  assert.match(await page.locator("#struktur details.erl[open]").first().textContent(), /dl-de\/by-2-0/);
  assert.deepEqual(await axe(page), []);
  // Karte: Ebene mit Legende (Klassen, nicht ausgewiesen, Hinweis), Auswahl des Merkmals, Link
  await page.locator('#struktur [data-struktur-karte="zensus_anteil_ab65"]').click();
  await page.waitForFunction(() => /Strukturdaten der Ortsbezirke/.test(document.querySelector(".map-legend")?.textContent || ""));
  const leg = page.locator(".map-legend");
  assert.match(await leg.textContent(), /nicht ausgewiesen/);
  assert.match(await leg.textContent(), /ökologischer Fehlschluss/);
  assert.match(await leg.textContent(), /Jahr 2022/);
  assert.equal(await page.locator(".leaflet-struktur-pane path").count(), 17);
  assert.match(page.url(), /ebenen=strukturdaten/);
  assert.equal(await leg.locator("[data-struktur-ind]").inputValue(), "zensus_anteil_ab65");
  await leg.locator("[data-struktur-klassen]").selectOption("fest");
  await leg.locator("[data-struktur-ind]").selectOption("zensus_durchschnittsalter");
  await page.waitForFunction(() => /Jahre/.test(document.querySelector(".map-legend")?.textContent || ""));
  assert.match(await page.locator(".leaflet-control-attribution").textContent(), /Statistische Ämter/);
  assert.deepEqual(await axe(page), []);
  await leg.locator("[data-struktur-tabelle]").click();
  await page.waitForSelector("#panel-struktur:not([hidden]) #struktur-tabelle");
  assert.match(await page.locator("#struktur-tabelle caption").textContent(), /Durchschnittsalter je Ortsbezirk/);
  assert.deepEqual(page.errors, []);
  await page.close();
  // Vorgang mit Ortsbezug: kurzer Kasten mit Verweis auf das Fenster
  const v = await open(SITE, "?gebiet=ortsteil:gertenbach");
  await v.locator('.toggle[data-panel="panel-list"]').click();
  await v.locator("#papers button[data-ref]").first().click();
  await v.waitForSelector("#detail [data-open-struktur]");
  assert.match(await v.locator("#detail").textContent(), /Strukturdaten.*Einwohner.*kein Bezug zum Inhalt des Vorgangs/s);
  await v.locator("#detail [data-open-struktur]").first().click();
  await v.waitForSelector("#panel-struktur:not([hidden]) #struktur table");
  assert.deepEqual(v.errors, []);
  await v.close();
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
  await page.locator('[data-mega="mega-stadt"]').click();
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
  await page.locator('[data-mega="mega-politik"]').click();
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

test("Quellwache: bekannte Lücken unter Quellen und Datenstand, mit Fundstelle, ohne Verstöße", async () => {
  const page = await open(SITE);
  await page.locator('[data-mega="mega-ueber"]').click();
  await page.locator("#sources > summary").click();
  await page.locator("#luecken summary").click();
  const t = await page.locator("#luecken").textContent();
  assert.match(t, /Bekannte Lücken in den Quellen \(1\).*10\.02\.2026 · Stadtverordnetenversammlung · erwähnt in Bekanntmachung Nr\. 051\/2026/s);
  assert.equal(await page.locator('#luecken a[href$="051-2026-Einladung-STVV-Konstituierung-21-04-2026.pdf"]').count(), 1);
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
  const titel = await page.locator(".brand-mobil").boundingBox();
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
  // Angebotsmiete nur als Kreiswert (BBSR, Deutschlandatlas), eigener Kreis hervorgehoben, getrennt von der Bestandsmiete
  assert.match(await page.locator("#modul-boden").textContent(), /Angebotsmieten 2025 \(Kreiswert\).*nicht für Witzenhausen allein.*Werra-Meißner-Kreis\s*6,97.*BBSR-Wohnungsmarktbeobachtung; IDN ImmoDaten GmbH/s);
  assert.match(await page.locator("#modul-boden tr.own").last().textContent(), /Werra-Meißner-Kreis/);
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
      sicherheit: "gesichert", beleg: "ortskenntnis", ...(i % 2 ? {} : { name: "Wohnbau Test eG", gebaeudeart: "mfh", wohnungen: 12,
        eigentuemer: [{ kategorie: "geno", kategorie_titel: "Wohnungsgenossenschaft", name: "Wohnbau Test eG" }, { kategorie: "geno", kategorie_titel: "Wohnungsgenossenschaft", name: "Hasenohr eG (Test)" }] }) } })) };
  const page = await browser.newPage({ viewport: { width: 1280, height: 800 }, bypassCSP: true });
  const errors = [];
  page.on("pageerror", (e) => errors.push(String(e)));
  page.on("console", (m) => { if (m.type() === "error") errors.push(m.text()); });
  await page.route("https://sgx.geodatenzentrum.de/**", (r) => r.fulfill({ contentType: "image/png", body: PNG }));
  await page.route("**/data/export/wohnen.json", async (r) => {
    const res = await r.fetch(), w = await res.json();
    w.eigentum_karte = true;
    w.eigentum_anteile = { stand: "2026-10-26", ortsbezirke: { gertenbach: { gebaeude: 1295, erfasst: 40, kategorien: { geno: 20, kom: 20 }, privat: null,
      privat_hinweis: "zu wenige Angaben; nicht in „erfasst“ enthalten",
      wohnungen: { mehrfamilienhaeuser: 3, mit_wohnungszahl: 3, wohnungen: 36, je_kategorie: { geno: 24 }, privat: null, privat_haeuser: null } } } };
    w.eigentum_anteile.je_eigentuemer = [{ name: "Wohnbau Test eG", kategorie: "geno", kategorie_titel: "Wohnungsgenossenschaft", haeuser: 3, wohnungen: 24 }];
    w.zensus_mfh = { stichtag: "2022-05-15", attribution: "Zensus (Test)", hinweis: "Näherung (Test).", ortsbezirke: { gertenbach: 147, kernstadt: 2238 } };
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
    assert.match(await page.locator("#gebaeude").textContent(), /Eigentum\s*Wohnungsgenossenschaft: Wohnbau Test eG\s*Wohnungsgenossenschaft: Hasenohr eG \(Test\)/);
    assert.match(await page.locator("#gebaeude").textContent(), /Haus\s*Mehrfamilienhaus mit 12 Wohnungen/);
    getroffen = true;
    break;
  }
  assert.ok(getroffen, "kein erfasstes Gebäude anklickbar");
  await page.locator("#modul-stand > summary").click();
  assert.match(await page.locator("#modul-stand").textContent(), /Gertenbach\s*[\d.]+\s*40\s*[\d,]+ %\s*zu wenige Angaben/);
  // Wohnungen in Mehrfamilienhäusern: erfasst gegen Zensus 2022 (36 von 147 = 24,5 %), Ortsteile ohne Erfassung mit Bezugsgröße
  const stand = await page.locator("#modul-stand").textContent();
  assert.match(stand, /Wohnungen in Mehrfamilienhäusern.*Gertenbach\s*147\s*3\s*36\s*24,5 %\s*Wohnungsgenossenschaft: 24/s);
  assert.match(stand, /Kernstadt\s*2\.238\s*0/);
  assert.match(stand, /Wohnungen je Unternehmen und Genossenschaft.*Wohnbau Test eG\s*Wohnungsgenossenschaft\s*3\s*24/s);
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
  page.kartenlink = (bis = "2099-12-31", code = TESTCODE) => `${SITE}erfassen.html?karte=${Math.random().toString(36).slice(2)}#code=${code}&bis=${bis}&schluessel=test-1~${sodium.to_base64(kp.publicKey, sodium.base64_variants.URLSAFE_NO_PADDING)}`;
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
async function karteScannen(page, link) {
  await page.goto(link, { waitUntil: "networkidle" });
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

test("Erfassung über die Einladungskarte: QR-Link meldet an, Adresse bereinigt, ohne benannte Stelle kein Speichern, Mietangaben aus, ohne Verstöße", async () => {
  const page = await erfassenSeite({ aktiv: false });
  assert.equal(await page.locator("#tafel-titel").textContent(), "Zugang");
  assert.equal(await page.locator("#ortsteil-wahl").isVisible(), false);
  assert.match(await page.locator("#tafel-inhalt").textContent(), /QR-Code auf Ihrer Einladungskarte/);
  assert.equal(await page.locator("#code").count(), 0);  // ohne Codeliste in der Konfiguration kein Abtippen
  assert.deepEqual(await axe(page), []);
  await page.goto(`${SITE}erfassen.html?a#code=ABCD`, { waitUntil: "networkidle" });
  assert.match(await page.locator("#tafel-inhalt").textContent(), /Link der Einladungskarte ist unvollständig/);
  await page.goto(page.kartenlink("2020-01-01"), { waitUntil: "networkidle" });
  assert.match(await page.locator("#tafel-inhalt").textContent(), /abgelaufen \(gültig bis 01\.01\.2020\)/);
  assert.equal(new URL(page.url()).hash, "");
  await karteScannen(page, page.kartenlink());
  assert.equal(new URL(page.url()).hash, "");  // Code nicht in Adresse und Verlauf
  const z = await page.evaluate(async () => {
    const d = await new Promise((ok) => { const r = indexedDB.open("wiz-erfassung"); r.onsuccess = () => ok(r.result); });
    return new Promise((ok) => { const g = d.transaction("meta").objectStore("meta").get("zugang"); g.onsuccess = () => ok(g.result); });
  });
  assert.deepEqual([z.erfasser, z.bis, z.schluessel.key_id], ["E-227c7469", "2099-12-31", "test-1"]);
  assert.match(await page.locator("#tafel-inhalt").textContent(), /verantwortliche Stelle ist noch nicht benannt.*Erfasser-ID E-227c7469/s);
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
  // Mehrfamilienhaus mit zwei Genossenschaften und privaten Wohnungen: gültig, nichts gespeichert
  await page.locator("#weiter").click();
  await gebaeudeAntippen(page);
  await page.locator("#zu-a").click();
  await page.getByRole("radio", { name: /Mehrfamilienhaus/ }).check();
  await page.fill('input[name="wohnungen_gesamt"]', "12");
  const zeile = (i) => page.locator(".ez-zeile").nth(i);
  await zeile(0).locator(".ez-art").selectOption("geno");
  await zeile(0).locator(".ez-name-feld").fill("Stinkycat eG (Probe)");
  await zeile(0).locator(".ez-zahl").fill("5");
  await page.locator("#ez-neu").click();
  await zeile(1).locator(".ez-art").selectOption("geno");
  await zeile(1).locator(".ez-name-feld").fill("Hasenohr eG (Probe)");
  await zeile(1).locator(".ez-zahl").fill("3");
  await page.locator("#ez-neu").click();
  await zeile(2).locator(".ez-art").selectOption("privat");
  await zeile(2).locator(".ez-zahl").fill("2");
  assert.match(await page.locator("#ez-summe").textContent(), /Zusammen 10 von 12 Wohnungen zugeordnet/);
  await page.selectOption('select[name="beleg_art"]', "ortskenntnis");
  assert.deepEqual(await axe(page), []);
  await page.locator('#form-a button[type="submit"]').click();
  assert.match(await page.locator(".erfolg").textContent(), /Probe: Die Angaben sind gültig/);
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
  for (const g of ["Wem gehört das Gebäude?", "Was für ein Haus ist das?", "Werden Wohnungen vermietet?", "Wie sicher ist die Angabe?"]) await page.getByRole("group", { name: g }).waitFor();
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
  // Mehrfamilienhaus: Zahl der Wohnungen oder „Zahl unbekannt“; Wohnungen je Eigentümer-Art zusammen höchstens die Gesamtzahl
  // Mehrfamilienhaus: statt „Wem gehört das Gebäude?“ die Eigentümer-Liste; Zahl der Wohnungen oder „Zahl unbekannt“;
  // je Zeile Art und Zahl, zusammen höchstens die Gesamtzahl
  await page.getByRole("radio", { name: /Mehrfamilienhaus/ }).check();
  await page.locator("#feld-mfh").waitFor();
  assert.equal(await page.locator("#feld-kategorie").isHidden(), true);
  assert.equal(await page.locator(".ez-zeile").count(), 1);
  await page.locator('#form-a button[type="submit"]').click();
  assert.match(await page.locator(".fehlerliste").textContent(), /Zahl der Wohnungen: Zahl eingeben/);
  await page.fill('input[name="wohnungen_gesamt"]', "4");
  await page.locator(".ez-zeile .ez-art").first().selectOption("privat");
  assert.equal(await page.locator(".ez-zeile .ez-name").first().isHidden(), true);  // bei Privatpersonen nie ein Name
  await page.locator(".ez-zeile .ez-zahl").first().fill("6");
  await page.locator('#form-a button[type="submit"]').click();
  assert.match(await page.locator(".fehlerliste").textContent(), /zusammen 6, mehr als die 4 Wohnungen/);
  assert.equal(await page.evaluate(() => [...document.querySelectorAll("#form-a input, #form-a select")].filter((x) => !x.closest("[hidden]") && !(x.labels && x.labels.length)).length), 0);
  assert.deepEqual(await axe(page), []);
  // zurück zum Ein- oder Zweifamilienhaus: die Frage „Wem gehört das Gebäude?“ mit der Auswahl von vorher
  await page.getByRole("radio", { name: /Ein- oder Zweifamilienhaus/ }).check();
  assert.equal(await page.locator("#feld-kategorie").isVisible(), true);
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
  // Sperre eines älteren, abgetippten Codes: Hash nicht mehr in der Konfiguration
  page.konfig.zugang = false;
  await page.reload({ waitUntil: "networkidle" });
  assert.match(await page.locator("#tafel-inhalt").textContent(), /gesperrt/);
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
  await page.locator("#probe").waitFor();
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
  for (const t of ["Suche", "Gebiet wählen", "Die Karte", "Kartenoptionen und Ebenen", "Die Liste", "Der Vorgang", "Die Prozesslinie", "Politik", "Stadt in Zahlen", "Über den Stadtmonitor"])
    assert.ok(titel.includes(t), `Schritt „${t}“ fehlt: ${titel.join(", ")}`);
  assert.equal(await page.locator("#detail-heading").textContent(), "Vorgang", "Beispielvorgang geöffnet");
  await page.keyboard.press("Escape");
  assert.equal(await page.locator(".tour").count(), 0);
  assert.deepEqual(page.errors, []);
  await page.close();
});

test("Einrichten und Einladungskarten: Prüfgruppe richtet ein, Ausgabestelle druckt und sperrt Karten, QR-Link meldet in der App an, Export kommt an, nichts gesendet, ohne Verstöße", async () => {
  // ohne bypassCSP: Die Seiten müssen mit ihrer eigenen Richtlinie (connect-src 'none' bzw. 'self' auf der Prüfseite, WebAssembly) funktionieren
  const ctx = await browser.newContext({ acceptDownloads: true });
  const page = await ctx.newPage();
  const fehler = [], abrufe = [];
  page.on("pageerror", (e) => fehler.push(String(e)));
  page.on("console", (m) => { if (m.type() === "error") fehler.push(m.text()); });
  page.on("request", (r) => abrufe.push(r.url()));
  const dir = mkdtempSync(join(tmpdir(), "karten-"));
  const laden = async (knopf, p = page) => {
    const [dl] = await Promise.all([p.waitForEvent("download"), p.locator(knopf).click()]);
    const ziel = join(dir, `${Date.now()}_${dl.suggestedFilename()}`);
    await dl.saveAs(ziel);
    return ziel;
  };
  try {
    // Prüfgruppe: einrichten (zu kurz, ungleich, dann richtig), Arbeitsdatei und Kartenliste speichern
    await page.goto(SITE + "intern/pruefen.html?aufgabe=einrichten");
    await page.waitForFunction(() => !document.querySelector("#knopf-einrichten").disabled);
    assert.match(await page.locator('meta[http-equiv="Content-Security-Policy"]').getAttribute("content"), /connect-src 'self'/);
    assert.equal(await page.locator(".fortschritt").textContent(), "Schritt 1 von 2");
    assert.equal(await page.locator("[data-weiter]").isDisabled(), true);  // erst nach dem Anlegen
    await page.fill("#pass1", "zu kurz");
    await page.locator("#knopf-einrichten").click();
    assert.match(await page.locator("#einrichten-status").textContent(), /mindestens 10 Zeichen/);
    const PASS = "vier Wörter zum Testen";
    await page.fill("#pass1", PASS);
    await page.fill("#pass2", PASS + "x");
    await page.locator("#knopf-einrichten").click();
    assert.match(await page.locator("#einrichten-status").textContent(), /stimmen nicht überein/);
    await page.fill("#pass2", PASS);
    await page.locator("#knopf-einrichten").click();
    await page.waitForFunction(() => /Angelegt/.test(document.querySelector("#einrichten-status").textContent), null, { timeout: 60000 });
    assert.equal(await page.locator("#pass1").inputValue(), "");
    assert.equal(await page.locator(".fortschritt").textContent(), "Schritt 2 von 2");  // geht von selbst weiter
    const arbeitsdatei = await laden("#speichern-arbeitsdatei-neu");
    const kartenliste = await laden("#speichern-kartenliste-neu");
    const roh = readFileSync(arbeitsdatei, "utf8");
    assert.deepEqual(Object.keys(JSON.parse(roh)).sort(), ["ciphertext", "format", "gespeichert", "kdf", "key_id"]);
    const kl = JSON.parse(readFileSync(kartenliste, "utf8"));
    assert.deepEqual([kl.format, kl.karten.length, kl.key_id], ["wiz-kartenliste-1", 0, JSON.parse(roh).key_id]);
    assert.doesNotMatch(readFileSync(kartenliste, "utf8"), /secret/);
    // Python packt die Arbeitsdatei der Seite aus (gleicher öffentlicher Schlüssel, leerer Bestand)
    const py = execFileSync("python3", ["-c", `
import sys
sys.path.insert(0, "tools")
import pruefgruppe as pg
i = pg.arbeitsdatei_lesen(sys.argv[1], sys.argv[2])
assert i["bestand"]["eintraege"] == {} and i["karten"]["karten"] == []
z = pg.arbeitsdatei_auspacken(sys.argv[1], sys.argv[2], sys.argv[3])
print("ok", pg.Schluessel(z / "schluessel.json", sys.argv[2]).key_id)
`, arbeitsdatei, PASS, join(dir, "aus")], { encoding: "utf8" });
    assert.equal(py.trim(), `ok ${kl.key_id}`);
    // Ausgabestelle: falsche Datei abgewiesen, Kartenliste öffnen, zwei Karten drucken, eine sperren, speichern
    await page.goto(SITE + "intern/karten.html");
    assert.match(await page.locator('meta[http-equiv="Content-Security-Policy"]').getAttribute("content"), /connect-src 'none'/);
    await page.evaluate(() => { window.print = () => { window.gedruckt = document.querySelector("#druck").innerHTML; }; });
    await page.setInputFiles("#f-liste", arbeitsdatei);
    await page.waitForFunction(() => /nicht die Liste der Einladungskarten/.test(document.querySelector("#oeffnen-status").textContent));  // Datei wird asynchron gelesen
    await page.setInputFiles("#f-liste", kartenliste);
    await page.waitForFunction(() => /0 Karten/.test(document.querySelector("#oeffnen-status").textContent));
    await page.fill("#anzahl", "2");
    await page.locator("#form-neu button").click();
    await page.waitForFunction(() => window.gedruckt);
    const blatt = await page.evaluate(() => window.gedruckt);
    const links = [...blatt.matchAll(/data-link="([^"]+)"/g)].map((m) => m[1].replaceAll("&amp;", "&"));
    assert.equal(links.length, 2);
    assert.equal((blatt.match(/<svg/g) || []).length, 2);
    assert.match(blatt, /Erhalten von \(Name\)/);
    assert.match(links[0], new RegExp(`^https://stadtmonitor-witzenhausen\\.de/erfassen\\.html#code=[0-9A-Z-]{19}&bis=\\d{4}-\\d\\d-\\d\\d&schluessel=${kl.key_id}~[A-Za-z0-9_-]{43}$`));
    assert.match(await page.locator("#ungespeichert").textContent(), /sichere die Liste/);
    await page.locator("details.mehr summary", { hasText: "verloren" }).click();
    page.once("dialog", (d) => d.accept());
    await page.locator("#karten [data-sperren]").first().click();
    assert.match(await page.locator("#karten tbody").textContent(), /gesperrt seit/);
    await page.locator("[data-weiter]").click();
    assert.equal(await page.locator(".fortschritt").textContent(), "Schritt 3 von 3");
    const liste2 = await laden("#speichern");
    const k2 = JSON.parse(readFileSync(liste2, "utf8"));
    assert.equal(k2.karten.length, 2);
    assert.equal(k2.karten.filter((k) => k.widerrufen).length, 1);
    for (const l of links) assert.doesNotMatch(readFileSync(liste2, "utf8"), new RegExp(new URLSearchParams(l.split("#")[1]).get("code")));
    // Barrierefreiheit der Kartenseite (axe braucht ein eingefügtes Skript; daher eine zweite Ansicht ohne Richtlinie)
    const pruef = await browser.newPage({ bypassCSP: true });
    await pruef.goto(SITE + "intern/karten.html");
    await pruef.setInputFiles("#f-liste", liste2);
    await pruef.locator("#anzahl").waitFor();
    assert.deepEqual(await axe(pruef), []);
    await pruef.goto(SITE + "intern/index.html");
    assert.deepEqual(await axe(pruef), []);
    await pruef.close();
    // Erfassende: QR-Link der zweiten (gültigen) Karte öffnet die App angemeldet; Eintrag speichern und exportieren
    const app = await erfassenSeite();
    await karteScannen(app, SITE + "erfassen.html?karte" + links[1].slice(links[1].indexOf("#")));
    const eid = k2.karten[1].erfasser_id;
    assert.match(await app.locator("#tafel-inhalt").textContent(), new RegExp(`Erfasser-ID ${eid}`));
    await app.reload({ waitUntil: "networkidle" });  // ohne Link weiter angemeldet
    await app.waitForFunction(() => window.stadtmonitorErfassen && window.stadtmonitorErfassen.map.loaded());
    await app.selectOption("#ortsteil", "gertenbach");
    await app.waitForFunction(() => window.stadtmonitorErfassen.map.queryRenderedFeatures({ layers: ["flaeche"] }).length > 0);
    app.errors.length = 0;  // vom Neuladen abgebrochene Kartenabrufe zählen nicht
    await gebaeudeAntippen(app);
    await app.locator("#zu-a").click();
    await app.locator('input[name="kategorie"][value="kom"]').check();
    await app.fill('input[name="name_juristische_person"]', "Stadt (Test)");
    await app.selectOption('select[name="beleg_art"]', "ortskenntnis");
    await app.locator('#form-a button[type="submit"]').click();
    await app.locator(".erfolg").waitFor();
    await app.locator("#zu-eintraege").click();
    const exp = await exportDatei(app, "eigentum");
    assert.equal(exp.inhalt.eintraege[0].key_id, kl.key_id);  // mit dem Schlüssel aus dem Link versiegelt
    const expDatei = join(dir, exp.name);
    writeFileSync(expDatei, JSON.stringify(exp.inhalt));
    assert.deepEqual(app.errors, []);
    await app.context().close();
    // Prüfgruppe: Arbeitsdatei öffnen, Export und neue Kartenliste in einem Zug einlesen, freigeben, speichern
    await page.goto(SITE + "intern/pruefen.html");
    await page.waitForFunction(() => !document.querySelector("#knopf-oeffnen").disabled);
    const nachLaden = abrufe.length;
    await page.setInputFiles("#f-arbeitsdatei", arbeitsdatei);
    await page.fill("#f-pass", PASS);
    await page.locator("#knopf-oeffnen").click();
    await page.locator("#f-exporte").waitFor({ timeout: 60000 });  // nach dem Öffnen gleich der nächste Schritt
    assert.match(await page.locator("#stand").textContent(), /Einladungskarten0, davon 0 gültig/);
    await page.setInputFiles("#f-exporte", [expDatei, liste2]);
    await page.locator("#form-eingang button").click();
    await page.waitForFunction(() => /aufgenommen/.test(document.querySelector("#eingang-status").textContent));
    assert.match(await page.locator("#eingang-status").textContent(), /Liste der Einladungskarten übernommen \(2 Karten\)\. 1 aufgenommen, 0 abgewiesen/);
    assert.match(await page.locator("#stand").textContent(), /Einladungskarten2, davon 1 gültig/);
    await page.locator("[data-weiter]").click();
    await page.locator("#knopf-alle").click();
    assert.match(await page.locator("#stand").textContent(), /Freigegeben1/);
    await page.locator("[data-weiter]").click();  // veröffentlichen überspringen
    await page.locator("[data-weiter]").click();
    assert.equal(await page.locator(".fortschritt").textContent(), "Schritt 5 von 5");
    const neu = await laden("#speichern-arbeitsdatei");
    assert.notEqual(readFileSync(neu, "utf8"), roh);
    assert.deepEqual(abrufe.slice(nachLaden), []);
    assert.deepEqual(await page.evaluate(() => [localStorage.length, sessionStorage.length]), [0, 0]);
    assert.deepEqual(fehler, []);
  } finally {
    rmSync(dir, { recursive: true, force: true });
    await ctx.close();
  }
});

test("Prüfseite: Arbeitsdatei mit Passwort, Einlesen und Prüfen wie tools/pruefen.py, mit Python austauschbar, Rechte und Fristen, Probe, nichts gesendet, ohne Verstöße", async () => {
  const dir = mkdtempSync(join(tmpdir(), "pruefseite-"));
  const root = new URL("../..", import.meta.url).pathname;
  const fx = JSON.parse(execFileSync("python3", ["tests/browser/pruef_fixture.py", "erzeugen", dir], { cwd: root, encoding: "utf8" }));
  const ctx = await browser.newContext({ acceptDownloads: true });
  const page = await ctx.newPage();
  const fehler = [], abrufe = [];
  page.on("pageerror", (e) => fehler.push(String(e)));
  page.on("console", (m) => { if (m.type() === "error") fehler.push(m.text()); });
  page.on("request", (r) => abrufe.push(r.url()));
  const laden = async (knopf) => {
    const [dl] = await Promise.all([page.waitForEvent("download"), page.locator(knopf).click()]);
    const ziel = join(dir, `dl_${Date.now()}_${dl.suggestedFilename()}`);
    await dl.saveAs(ziel);
    return ziel;
  };
  const oeffnen = async (datei, pass = fx.passphrase, aufgabe = "pruefen") => {
    await page.goto(SITE + `intern/pruefen.html?aufgabe=${aufgabe}`);
    await page.waitForFunction(() => !document.querySelector("#knopf-oeffnen").disabled);
    await page.setInputFiles("#f-arbeitsdatei", datei);
    await page.fill("#f-pass", pass);
    await page.locator("#knopf-oeffnen").click();
  };
  const offen = async (datei, aufgabe = "pruefen") => {
    await oeffnen(datei, fx.passphrase, aufgabe);
    await page.waitForFunction(() => window.Schritte.aktuell !== "oeffnen");
  };
  const schritt = (name) => page.evaluate((n) => window.Schritte.gehe(n), name);
  const mehr = async (text) => { const d = page.locator("details.mehr", { hasText: text }); if (!(await d.getAttribute("open") !== null)) await d.locator("summary").click(); };
  try {
    // falsches Passwort: nicht geöffnet
    await oeffnen(fx.start, "falsches Passwort");
    await page.waitForFunction(() => /Passwort ist falsch/.test(document.querySelector("#oeffnen-status").textContent));
    assert.equal(await page.locator("#f-exporte").isVisible(), false);
    await offen(fx.start);
    assert.match(await page.locator('meta[http-equiv="Content-Security-Policy"]').getAttribute("content"), /connect-src 'self'/);
    const nachLaden = abrufe.length;
    assert.match(await page.locator("#stand").textContent(), /Einladungskarten1, davon 1 gültig/);
    // Eingang: dieselben Fälle wie im Python-Referenzlauf; geprüft wird gleich mit
    await page.setInputFiles("#f-exporte", fx.dateien);
    await page.locator("#form-eingang button").click();
    await page.waitForFunction(() => /aufgenommen/.test(document.querySelector("#eingang-status").textContent));
    assert.match(await page.locator("#eingang-status").textContent(), new RegExp(`^${fx.aufgenommen} aufgenommen, ${fx.abgewiesen} abgewiesen`));
    assert.match(await page.locator("#eingang-tabelle").textContent(), /Karte nicht in der Kartenliste/);
    assert.match(await page.locator("#stand").textContent(), /Mit Hinweis, bitte ansehen4/);
    await schritt("pruefen");
    await page.locator("#knopf-alle").click();
    assert.match(await page.locator("#stand").textContent(), /Freigegeben21/);
    assert.match(await page.locator("#liste").textContent(), /8,12 €\/m²/);  // 650 / 80 = 8,125 → 8,12 wie Python round()
    assert.match(await page.locator("#ungespeichert").textContent(), /sichere die Prüfmappe/);
    await schritt("speichern");
    const arbeitsdatei = await laden("#speichern-arbeitsdatei");
    assert.equal(await page.locator("#ungespeichert").textContent(), "");
    // Python packt die Arbeitsdatei der Seite aus: Bestand gleich dem Referenzlauf
    const vergleich = execFileSync("python3", ["tests/browser/pruef_fixture.py", "vergleichen", dir, arbeitsdatei], { cwd: root, encoding: "utf8" });
    assert.equal(vergleich.trim(), "gleich");
    // Veröffentlichen: Vorschau, Sperre bestanden, eine Datei; Python übernimmt sie und erhält dasselbe wie mit veroeffentlichen.py
    await schritt("veroeffentlichen");
    await page.locator("#knopf-veroeffentlichen").click();
    await page.waitForFunction(() => /nichts Persönliches/.test(document.querySelector("#veroeffentlichen-status").textContent));
    const vorschau = await page.locator("#vorschau").textContent();
    assert.match(vorschau, /Kernstadt, 1949-1978/);
    assert.match(vorschau, /Probe-Wohnbau eG/);
    assert.match(vorschau, /zu wenige/);  // privat unter der Mindestzahl
    assert.match(vorschau, /Wohnungen in Mehrfamilienhäusern/);  // R10: Wohnungen je Kategorie, „privat“ aus einem Haus verdeckt
    const veroeff = await laden("#speichern-veroeffentlichung");
    const vtext = readFileSync(veroeff, "utf8");
    assert.doesNotMatch(vtext, /Erika|V-0\d\d|[0-9a-f]{8}-[0-9a-f]{4}-4|eur_je_m2|nettokalt_eur/i);
    assert.match(JSON.stringify(JSON.parse(vtext)), /"wohnungen":\{"mehrfamilienhaeuser":2,"mit_wohnungszahl":1,"wohnungen":null/);
    const pub = execFileSync("python3", ["tests/browser/pruef_fixture.py", "veroeffentlichen", dir, veroeff], { cwd: root, encoding: "utf8" });
    assert.equal(pub.trim(), "gleich");
    assert.match(await page.locator("#ungespeichert").textContent(), /sichere die Prüfmappe/);  // Verlauf vermerkt die Veröffentlichung
    assert.deepEqual(abrufe.slice(nachLaden), []);
    // Auf der Seite veröffentlichen: genau eine Anfrage an veroeffentlichen.php mit der Veröffentlichungsdatei (Server nachgestellt)
    let gesendet = null;
    await page.route("**/intern/veroeffentlichen.php", (r) => { gesendet = r.request(); r.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ ok: true, aktion: "veroeffentlicht", stand: "2026-11-10", vorher: null }) }); });
    page.once("dialog", (d) => d.accept());
    await page.locator("#knopf-senden").click();
    await page.waitForFunction(() => /Veröffentlicht \(Stand 2026-11-10\)/.test(document.querySelector("#senden-status").textContent));
    assert.equal(gesendet.method(), "POST");
    const body = JSON.parse(gesendet.postData());
    assert.equal(body.format, "wiz-veroeffentlichung-1");
    assert.deepEqual(Object.keys(body.dateien).sort(), JSON.parse(vtext).dateien ? Object.keys(JSON.parse(vtext).dateien).sort() : []);
    assert.doesNotMatch(gesendet.postData(), /Erika|V-0\d\d|[0-9a-f]{8}-[0-9a-f]{4}-4|eur_je_m2|nettokalt_eur|secret|ciphertext/i);
    assert.deepEqual(abrufe.slice(nachLaden).filter((u) => !u.endsWith("/intern/veroeffentlichen.php")), [], "sonst nichts gesendet");
    // Server lehnt ab: Meldung, nichts verloren
    await page.unroute("**/intern/veroeffentlichen.php");
    await page.route("**/intern/veroeffentlichen.php", (r) => r.fulfill({ status: 422, contentType: "application/json", body: JSON.stringify({ ok: false, fehler: "Verbotene Felder: x" }) }));
    page.once("dialog", (d) => d.accept());
    await page.locator("#knopf-senden").click();
    await page.waitForFunction(() => /Nicht veröffentlicht: Verbotene Felder/.test(document.querySelector("#senden-status").textContent));
    fehler.splice(fehler.findIndex((f) => /status of 422/.test(f)), 1);  // die abgelehnte Anfrage selbst meldet der Browser
    // umgekehrt: Arbeitsdatei aus Python öffnen, Eintrag mit Hinweis verwerfen
    await offen(fx.ref);
    assert.match(await page.locator("#stand").textContent(), /Einträge26.*Freigegeben21.*Mit Hinweis, bitte ansehen4.*Aussortiert1/s);
    await schritt("pruefen");
    await mehr("Einzelne Angaben");
    const zeile = page.locator("#liste tbody tr", { hasText: "abweichende Angaben" }).first();
    await zeile.locator("input").check();
    await page.locator("#knopf-verwerfen").click();
    assert.match(await page.locator("#pruefen-status").textContent(), /Grund/);
    await page.fill("#f-grund", "im Test geklärt");
    await page.locator("#knopf-verwerfen").click();
    assert.match(await page.locator("#stand").textContent(), /Aussortiert2/);
    // Rechte: Widerruf per Code und Widerspruch je Gebäude; Python macht dasselbe und erhält denselben Bestand
    // Protokoll der Namenszugriffe aus der gespeicherten Prüfmappe: so viele Zeilen wie im Python-Referenzlauf
    await offen(arbeitsdatei, "sonderfall");
    assert.equal(await page.locator(".fortschritt").textContent(), "Schritt 2 von 3");
    await mehr("Unterlagen");
    const protokoll = readFileSync(await laden("#speichern-protokoll"), "utf8").trim().split("\n");
    assert.equal(protokoll.length, readFileSync(join(dir, "ref", "namenzugriff.tsv"), "utf8").trim().split("\n").length);
    await offen(fx.ref, "sonderfall");
    await mehr("Mietangabe zurückziehen");
    await mehr("nicht erfasst werden");
    await mehr("was über ein Haus gespeichert ist");
    await page.fill("#f-widerruf", "ZZZZ-ZZZZ");
    await page.locator("#form-widerruf button").click();
    assert.match(await page.locator("#rechte-status").textContent(), /0 Einträge gefunden/);
    await page.fill("#f-widerruf", `${fx.widerrufscode.slice(0, 4)}-${fx.widerrufscode.slice(4)}`);
    await page.locator("#form-widerruf button").click();
    assert.match(await page.locator("#rechte-status").textContent(), /gelöscht \(Widerruf\)/);
    await page.fill("#f-widerspruch", "DEHE0000UNBEKANNT");
    await page.locator("#form-widerspruch button").click();
    assert.match(await page.locator("#rechte-status").textContent(), /unbekannt/);
    await page.fill("#f-widerspruch", fx.widerspruch);
    await page.locator("#form-widerspruch button").click();
    assert.match(await page.locator("#rechte-status").textContent(), /2 Eigentumseinträge gelöscht, 2 Gebäude auf der Sperrliste/);  // dieselbe Privatperson an zwei Gebäuden
    await page.fill("#f-auskunft", fx.widerspruch);
    await page.locator("#form-auskunft button").click();
    // Mietangaben bleiben (Widerspruch betrifft die Eigentumsangaben), Eigentum zu diesem Gebäude ist gelöscht
    assert.match(await page.locator("#auskunft").textContent(), /2 Einträge, auf der Sperrliste/);
    assert.doesNotMatch(await page.locator("#auskunft tbody").textContent(), /Eigentum/);
    await schritt("speichern");
    const rechte = execFileSync("python3", ["tests/browser/pruef_fixture.py", "rechte", dir, await laden("#speichern-arbeitsdatei"), fx.widerrufscode, fx.widerspruch],
      { cwd: root, encoding: "utf8" });
    assert.equal(rechte.trim(), "gleich");
    // Passwort ändern: die gesicherte Prüfmappe öffnet nur noch mit dem neuen Passwort (Browser und Python)
    const NEU = "neues Passwort zum Testen";
    await schritt("sonderfall");
    await mehr("Passwort der Prüfmappe");
    await page.fill("#pass-neu1", NEU);
    await page.fill("#pass-neu2", NEU + "x");
    await page.locator("#knopf-passwort").click();
    assert.match(await page.locator("#passwort-status").textContent(), /stimmen nicht überein/);
    await page.fill("#pass-neu2", NEU);
    await page.locator("#knopf-passwort").click();
    await page.waitForFunction(() => /Passwort geändert/.test(document.querySelector("#passwort-status").textContent), null, { timeout: 60000 });
    await schritt("speichern");
    const neuGesichert = await laden("#speichern-arbeitsdatei");
    const pyNeu = execFileSync("python3", ["-c", `
import sys
sys.path.insert(0, "tools")
import pruefgruppe as pg
pg.arbeitsdatei_lesen(sys.argv[1], sys.argv[2])
try:
    pg.arbeitsdatei_lesen(sys.argv[1], sys.argv[3]); print("altes geht noch")
except (Exception, SystemExit):
    print("ok")
`, neuGesichert, NEU, fx.passphrase], { cwd: root, encoding: "utf8" });
    assert.equal(pyNeu.trim(), "ok");
    await oeffnen(neuGesichert);  // altes Passwort
    await page.waitForFunction(() => /Passwort ist falsch/.test(document.querySelector("#oeffnen-status").textContent), null, { timeout: 60000 });
    await oeffnen(neuGesichert, NEU);
    await page.waitForFunction(() => window.Schritte.aktuell !== "oeffnen", null, { timeout: 60000 });
    // Fristen: drei Jahre später ist alles fällig und wird gelöscht
    await page.clock.setSystemTime(new Date(Date.now() + 3 * 365 * 86400000));
    await offen(fx.ref, "sonderfall");
    assert.match(await page.locator("#stand").textContent(), /Älter als erlaubt26 Einträge/);
    await mehr("Alte Angaben löschen");
    page.once("dialog", (d) => d.accept());
    await page.locator("#knopf-fristen").click();
    assert.match(await page.locator("#stand").textContent(), /Einträge0 /);
    // Probe: Wegwerf-Schlüssel und Testdaten, ganzer Ablauf; nichts speicherbar, Veröffentlichung als Probe markiert
    await page.goto(SITE + "intern/pruefen.html?aufgabe=probe");
    await page.waitForFunction(() => !document.querySelector("#knopf-probe").disabled);
    await page.locator("#knopf-probe").click();
    assert.match(await page.locator("#pruefen-status").textContent(), /Übung gestartet.*11 erfundene Einträge/);
    assert.equal(await page.locator("#probe-band").isVisible(), true);
    assert.equal(await page.locator("#speichern-arbeitsdatei").isDisabled(), true);
    assert.equal(await page.locator("#knopf-senden").isDisabled(), true);  // Probe: nichts veröffentlichen
    await page.locator("#knopf-alle").click();
    await page.locator("[data-weiter]").click();
    await page.locator("#knopf-veroeffentlichen").click();
    await page.waitForFunction(() => /nichts Persönliches/.test(document.querySelector("#veroeffentlichen-status").textContent));
    const probe = await laden("#speichern-veroeffentlichung");
    assert.match(probe, /probe_veroeffentlichung_/);
    assert.equal(JSON.parse(readFileSync(probe, "utf8")).probe, true);
    assert.deepEqual(await page.evaluate(() => [localStorage.length, sessionStorage.length]), [0, 0]);
    assert.deepEqual(fehler, []);
    // Barrierefreiheit (axe braucht ein eingefügtes Skript, das die Richtlinie der Seite sperrt; daher ohne sie)
    const pruef = await browser.newPage({ bypassCSP: true });
    await pruef.goto(SITE + "intern/pruefen.html");
    await pruef.waitForFunction(() => !document.querySelector("#knopf-oeffnen").disabled);
    await pruef.evaluate(() => { document.querySelectorAll("section.schritt").forEach((s) => { s.hidden = false; }); document.querySelectorAll("details").forEach((d) => { d.open = true; }); });
    assert.deepEqual(await axe(pruef), []);
    await pruef.close();
  } finally {
    rmSync(dir, { recursive: true, force: true });
    await ctx.close();
  }
});
