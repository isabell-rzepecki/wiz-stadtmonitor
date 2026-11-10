// Material zum Teilen (Beiträge, Storys, Präsentationen): echte Ansichten der Seite, übereinander gelegt auf dem
// Korallgrund mit den Umrissen der Ortsbezirke. Ergebnis in docs/teilen/. Aufruf aus dem Wurzelverzeichnis:
//   python tools/vorschaubild.py /tmp/og.html   (liefert auch die Umrisse)
//   NODE_PATH=tests/browser/node_modules node tools/teilmaterial.mjs [Adresse der Seite]
// Die Aufnahmen kommen von der veröffentlichten Seite (nur öffentliche Inhalte); die Kartengrundlagen stehen
// als Quellenzeile in jedem Bild.
import { createRequire } from "node:module";
import { execFileSync } from "node:child_process";
import { mkdirSync, readFileSync } from "node:fs";
import { join, resolve } from "node:path";

const { chromium } = createRequire(import.meta.url)("playwright");
const ROOT = resolve(new URL("..", import.meta.url).pathname);
const SEITE = process.argv[2] || "https://stadtmonitor-witzenhausen.de/";
const ZIEL = join(ROOT, "docs", "teilen");
const ROH = join(ZIEL, ".roh");
mkdirSync(ROH, { recursive: true });
const QUELLEN = "Karten: © basemap.de / BKG (CC BY 4.0), © GeoBasis-DE · Gebäude: © HVBG, ALKIS vereinfacht, LoD2 · Ortsbezirke: HVBG (dl-de/zero-2.0)";
const SATZ = "Was Stadtverordnete, Ausschüsse und Ortsbeiräte beraten – auf Karte, Zeitleiste und Liste.";

const umrisse = (x, y, w, h) => execFileSync("python3", ["-c",
  `import sys; sys.path.insert(0, "tools"); import vorschaubild as v; print(v.umrisse(${x}, ${y}, ${w}, ${h}))`], { cwd: ROOT, encoding: "utf8" }).trim();
const marke = (() => { const s = readFileSync(join(ROOT, "site", "favicon.svg"), "utf8"); return s.slice(s.indexOf("<rect"), s.indexOf("</svg>")); })();
const bild = (n) => `data:image/png;base64,${readFileSync(join(ROH, n + ".png")).toString("base64")}`;
const schrift = (n) => `data:font/woff2;base64,${readFileSync(join(ROOT, "site", "fonts", n)).toString("base64")}`;

const browser = await chromium.launch();
// 1. Aufnahmen der Seite (doppelte Auflösung)
const D = { width: 1440, height: 900 }, M = { width: 390, height: 844 };
async function aufnahme(name, pfad, vp, schritt, warten = 5000) {
  const p = await browser.newPage({ viewport: vp, deviceScaleFactor: 2 });
  await p.goto(SEITE + pfad, { waitUntil: "networkidle", timeout: 90000 }).catch(() => {});
  await p.waitForTimeout(warten);
  if (schritt) { await schritt(p).catch((e) => console.warn(name, e.message)); await p.waitForTimeout(3500); }
  await p.screenshot({ path: join(ROH, name + ".png") });
  await p.close();
}
await aufnahme("d_karte", "", D);
await aufnahme("d_zeitleiste", "", D, (p) => p.getByRole("button", { name: /Zeitleiste/ }).first().click());
await aufnahme("d_wohnen", "wohnen.html?gebiet=ortsteil:kernstadt", D, null, 9000);
await aufnahme("d_wohnen3d", "wohnen.html?gebiet=ortsteil:kernstadt&ansicht=3d", D, null, 12000);
await aufnahme("m_karte", "", M);
await aufnahme("m_wohnen", "wohnen.html?gebiet=ortsteil:kernstadt&ansicht=3d", M, null, 12000);

// 2. Bausteine: Browserfenster, Telefon, Wortmarke
const fenster = (n, b, stil) => `<div class="fenster" style="width:${b}px;${stil}"><div class="leiste"><i></i><i></i><i></i></div><img src="${bild(n)}"></div>`;
const telefon = (n, b, stil) => `<div class="telefon" style="width:${b}px;${stil}"><img src="${bild(n)}"></div>`;
const wortmarke = (gr) => `<div class="wm" style="font-size:${gr}px"><svg viewBox="0 0 64 64" style="width:${gr * 1.25}px;height:${gr * 1.25}px">${marke}</svg><div>Stadtmonitor<span>Witzenhausen</span></div></div>`;
const grund = (w, h) => `<svg class="umriss" width="${w}" height="${h}"><path d="${umrisse(w * 0.35, -h * 0.05, w * 0.75, h * 1.1)}" fill="#fdf6f4" fill-opacity=".10" stroke="#fdf6f4" stroke-opacity=".55" stroke-width="2" stroke-linejoin="round"/></svg>`;
const css = `@font-face{font-family:L;src:url('${schrift("lilita-one-latin-400-normal.woff2")}')}
@font-face{font-family:M;src:url('${schrift("space-mono-latin-400-normal.woff2")}')}
@font-face{font-family:M;font-weight:700;src:url('${schrift("space-mono-latin-700-normal.woff2")}')}
*{box-sizing:border-box} html,body{margin:0;overflow:hidden} body{background:#f4726b;font-family:M;color:#1a1a1a;position:relative}
.umriss{position:absolute;left:0;top:0}
.fenster{position:absolute;border-radius:18px;overflow:hidden;background:#fff;box-shadow:0 30px 70px rgba(80,20,15,.35),0 4px 14px rgba(80,20,15,.18)}
.fenster .leiste{height:34px;background:#fdf6f4;display:flex;gap:9px;align-items:center;padding:0 16px;border-bottom:1px solid #0001}
.fenster .leiste i{width:12px;height:12px;border-radius:50%;background:#f4726b55;display:block}
.fenster img,.telefon img{display:block;width:100%}
.telefon{position:absolute;border-radius:46px;overflow:hidden;border:12px solid #1a1a1a;background:#1a1a1a;box-shadow:0 34px 80px rgba(60,15,10,.45)}
.telefon img{border-radius:34px}
.wm{display:flex;align-items:center;gap:.45em;font-family:L;line-height:.95;color:#fdf6f4;letter-spacing:-.01em}
.wm span{display:block;color:#1a1a1a} .wm svg{flex:none;border-radius:22%}
.satz{font-size:26px;line-height:1.45} .adr{font-weight:700} .quelle{position:absolute;font-size:13px;color:#1a1a1aa6}`;
const formate = {
  "teilen-quer": [1600, 900, (w, h) => `${grund(w, h)}
    <div style="position:absolute;left:80px;top:80px;width:560px">${wortmarke(76)}<p class="satz" style="margin:34px 0 26px">${SATZ}</p><div class="adr" style="font-size:22px">stadtmonitor-witzenhausen.de</div></div>
    ${fenster("d_wohnen3d", 760, "left:760px;top:70px;transform:rotate(3deg)")}
    ${fenster("d_karte", 820, "left:600px;top:380px;transform:rotate(-4deg)")}
    ${telefon("m_karte", 250, "left:1290px;top:300px;transform:rotate(6deg)")}
    <div class="quelle" style="left:80px;bottom:28px;width:480px">${QUELLEN}</div>`],
  "teilen-quadrat": [1080, 1080, (w, h) => `${grund(w, h)}
    <div style="position:absolute;left:70px;top:64px">${wortmarke(66)}<div class="adr" style="font-size:24px;margin-top:22px">stadtmonitor-witzenhausen.de</div></div>
    ${fenster("d_zeitleiste", 740, "left:270px;top:310px;transform:rotate(4deg)")}
    ${fenster("d_karte", 740, "left:60px;top:500px;transform:rotate(-3deg)")}
    ${telefon("m_wohnen", 220, "left:790px;top:500px;transform:rotate(7deg)")}
    <div class="quelle" style="left:70px;bottom:22px;width:940px;font-size:12px;background:#f4726b;padding-top:6px">${QUELLEN}</div>`],
  "teilen-story": [1080, 1920, (w, h) => `${grund(w, h)}
    <div style="position:absolute;left:90px;top:140px;width:900px">${wortmarke(96)}<p class="satz" style="font-size:36px;margin:44px 0 28px">${SATZ}</p><div class="adr" style="font-size:32px">stadtmonitor-witzenhausen.de</div></div>
    ${fenster("d_wohnen", 900, "left:150px;top:690px;transform:rotate(4deg)")}
    ${telefon("m_karte", 380, "left:100px;top:860px;transform:rotate(-6deg)")}
    ${telefon("m_wohnen", 380, "left:570px;top:940px;transform:rotate(5deg)")}
    <div class="quelle" style="left:90px;bottom:40px;width:900px;font-size:16px;background:#f4726b;padding-top:8px">${QUELLEN}</div>`],
  "teilen-banner": [1500, 500, (w, h) => `${grund(w, h)}
    <div style="position:absolute;left:70px;top:150px">${wortmarke(72)}</div>
    ${fenster("d_karte", 560, "left:760px;top:90px;transform:rotate(-4deg)")}
    ${fenster("d_wohnen3d", 520, "left:1010px;top:170px;transform:rotate(4deg)")}
    <div class="quelle" style="left:70px;bottom:24px;width:640px;font-size:12px">${QUELLEN}</div>`],
};
for (const [name, [w, h, inhalt]] of Object.entries(formate)) {
  const p = await browser.newPage({ viewport: { width: w, height: h } });
  await p.setContent(`<!doctype html><meta charset="utf-8"><style>${css} html,body{width:${w}px;height:${h}px}</style>${inhalt(w, h)}`);
  await p.evaluate(() => document.fonts.ready); await p.waitForTimeout(300);
  await p.screenshot({ path: join(ZIEL, name + ".png") });
  await p.close();
  console.log(join("docs", "teilen", name + ".png"));
}
await browser.close();
