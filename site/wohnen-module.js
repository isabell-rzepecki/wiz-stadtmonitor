// Module der Seite „Wohnen und Eigentum“: Zweck und Grenzen, Mietniveau, Verlauf der Bodenrichtwerte, Eigentum,
// Mietvergleich, Bezug zu Tagesordnungspunkten, Erfassungsstand, Begriffe, Methode.
// Eigentum und Mieten erscheinen nur aus geprüften Dateien (wohnen.json: eigentum_anteile, mieten) und nur nach den
// Veröffentlichungsregeln (stadt.json, wohnen_eigentum.regeln): Mieten je Zelle ab 5 Angaben, je juristischer Person ab
// 5 Angaben aus 2 Gebäuden, nie je privater Vermieter:in und nie einzeln. Ohne geprüfte Dateien zeigt die Seite den
// Stand der Erfassung, keine Platzhalterwerte.
window.WohnenModule = (function () {
  "use strict";
  const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const zahl = (v, d = 0) => Number(v).toLocaleString("de-DE", { minimumFractionDigits: d, maximumFractionDigits: d });
  const datum = (iso) => (iso ? new Date(`${iso.slice(0, 10)}T12:00:00Z`).toLocaleDateString("de-DE", { day: "2-digit", month: "2-digit", year: "numeric" }) : "–");
  const link = (u, t) => (/^https:\/\//.test(u || "") ? `<a href="${esc(u)}" rel="noopener">${t}</a>` : t);
  const ZU_WENIG = "zu wenige Angaben";

  function abschnitt(id, titel, inhalt, offen = true) {
    return `<details class="modul" id="modul-${id}"${offen ? " open" : ""}><summary><h3>${esc(titel)}</h3></summary><div class="modul-inhalt">${inhalt}</div></details>`;
  }
  const zensusWert = (e, d, einheit) => (!e ? "–" : e.wert == null ? `<span class="luecke">keine Angabe</span> <span class="meta">(${esc(e.grund || "ohne Wert")})</span>`
    : `${zahl(e.wert, d)} ${einheit} <span class="meta">(Näherung, ${zahl(e.zellen)} Gitterzellen)</span>`);

  function zweck(cfg) {
    const E = cfg.wohnen_eigentum;
    return `<p class="lead">${esc(E.zweck)}</p><h4>Grenzen</h4><ul>${E.grenzen.map((g) => `<li>${esc(g)}</li>`).join("")}</ul>`;
  }

  function mietniveau(cfg, w, slug) {
    const W = cfg.wohnen, z = w && w.zensus;
    if (!z) return '<p class="luecke">Noch keine Zensusdaten.</p>';
    const gem = z.gemeinden.find((g) => g.ars === cfg.stadt.ars);
    const o = slug && cfg.ortsteile.find((x) => x.slug === slug);
    const ob = o && z.ortsbezirke[slug];
    const zeilen = cfg.ortsteile.filter((x) => z.ortsbezirke[x.slug]).map((x) => {
      const e = z.ortsbezirke[x.slug];
      return `<tr${x.slug === slug ? ' class="own"' : ""}><th scope="row">${esc(x.name)}</th><td>${e.miete && e.miete.wert != null ? zahl(e.miete.wert, 2) : "–"}</td>
        <td>${e.eigentuemerquote && e.eigentuemerquote.wert != null ? zahl(e.eigentuemerquote.wert, 1) : "–"}</td></tr>`;
    }).join("");
    const eing = (g, k) => (g.eingeschraenkt || []).includes(k);
    const zelle = (g, k, d) => (g[k] == null ? "–" : eing(g, k) ? `(${zahl(g[k], d)})` : zahl(g[k], d));
    return `<p class="hinweis-kasten"><strong>Kein Mietspiegel.</strong> Für ${esc(cfg.stadt.name)} gibt es keinen Mietspiegel. Die Zahlen hier sind Bestandsmieten aus dem Zensus, keine ortsübliche Vergleichsmiete.</p>
      <p class="stichtag">Zensus 2022, Stichtag ${datum(z.stichtag)}</p>
      <dl class="fakten">${gem ? `<dt>Bestandsmiete ${esc(cfg.stadt.name)}</dt><dd>${zahl(gem.nettokaltmiete_eur_m2, 2)} €/m²</dd>
        <dt>Leerstandsquote ${esc(cfg.stadt.name)}</dt><dd>${zahl(gem.leerstandsquote_pct, 1)} % <span class="meta">(nur für die Gemeinde)</span></dd>
        <dt>Eigentümerquote ${esc(cfg.stadt.name)}</dt><dd>${zahl(gem.eigentuemerquote_pct, 1)} %</dd>` : ""}
        ${o ? `<dt>Bestandsmiete ${esc(o.name)}</dt><dd>${zensusWert(ob && ob.miete, 2, "€/m²")}</dd>
          <dt>Eigentümerquote ${esc(o.name)}</dt><dd>${zensusWert(ob && ob.eigentuemerquote, 1, "%")}</dd>` : ""}</dl>
      <details class="unter"><summary>Alle Ortsbezirke (Näherung aus dem Gitter)</summary><div class="tabelle"><table>
        <caption class="visually-hidden">Bestandsmiete und Eigentümerquote je Ortsbezirk, Näherung, Stichtag ${datum(z.stichtag)}</caption>
        <thead><tr><th scope="col">Ortsbezirk</th><th scope="col">Miete €/m²</th><th scope="col">Eigentümer %</th></tr></thead><tbody>${zeilen}</tbody></table></div>
        <p class="meta">„–“: weniger als ${zahl(W.zensus.mindestzellen)} Gitterzellen mit Wert, kein Ausweis.</p></details>
      <details class="unter"><summary>Vergleich mit Nachbargemeinden</summary><div class="tabelle"><table>
        <caption class="visually-hidden">Bestandsmiete, Leerstands- und Eigentümerquote je Gemeinde</caption>
        <thead><tr><th scope="col">Gemeinde</th><th scope="col">Miete €/m²</th><th scope="col">Leerstand %</th><th scope="col">Eigentümer %</th></tr></thead>
        <tbody>${z.gemeinden.map((g) => `<tr${g.ars === cfg.stadt.ars ? ' class="own"' : ""}><th scope="row">${esc(g.name)}</th><td>${zelle(g, "nettokaltmiete_eur_m2", 2)}</td>
          <td>${zelle(g, "leerstandsquote_pct", 1)}</td><td>${zelle(g, "eigentuemerquote_pct", 1)}</td></tr>`).join("")}</tbody></table></div>
        <p class="meta">Werte in Klammern: Aussagewert eingeschränkt.</p></details>
      <h4>Rechtlicher Rahmen</h4><ul class="liste">${W.kontext.map((k) => `<li><strong>${esc(k.thema)}:</strong> ${esc(k.aussage)}
        <br><span class="meta">Stand: ${esc(k.stand)}${k.link ? ` · ${link(k.link, "Quelle")}` : ""}</span></li>`).join("")}</ul>`;
  }

  function verlauf(cfg, w, slug) {
    const v = w && w.boris_verlauf;
    if (!v || !v.stichtage.length) return '<p class="luecke">Noch keine Bodenrichtwerte.</p>';
    const sp = (e) => (e ? `${zahl(e.min)}–${zahl(e.max)}` : "–");
    const reihen = [...cfg.ortsteile.filter((o) => v.spannen[o.slug]).map((o) => [o.slug, o.name]), ["stadt", `ganz ${cfg.stadt.name}`]];
    return `<p>Spannen für baureifes Wohn- und Mischbauland in €/m², je Stichtag mit Datendienst. ${esc(v.hinweis)}</p>
      <div class="tabelle"><table><caption class="visually-hidden">Spannen der Bodenrichtwerte je Ortsbezirk und Stichtag</caption>
        <thead><tr><th scope="col">Ortsbezirk</th>${v.stichtage.map((s) => `<th scope="col">${datum(s)}</th>`).join("")}</tr></thead>
        <tbody>${reihen.map(([k, n]) => `<tr${k === slug ? ' class="own"' : ""}><th scope="row">${esc(n)}</th>${v.stichtage.map((s) => `<td>${sp((v.spannen[k] || {})[s])}</td>`).join("")}</tr>`).join("")}</tbody></table></div>
      <p><button type="button" class="knopf" data-ebene="bodenrichtwerte">Zonen auf der Karte zeigen</button></p>
      <p class="meta">Stichtag 01.01.2026: nur als Karte der HVBG, in der Hauptkarte unter „Weitere Ebenen“ (Bilder eines fremden Servers erst nach dem Einschalten).</p>
      <h4>Angebotsmieten</h4><p><span class="luecke">keine Angabe</span>. Angebotsmieten gibt es frei nur auf Kreisebene (INKAR, BBSR); deren Lizenz und Herkunft sind noch nicht geprüft. Angebotsmieten privater Portale übernimmt die Seite nicht.</p>`;
  }

  function eigentum(cfg, w, eig) {
    const E = cfg.wohnen_eigentum, a = w && w.eigentum_anteile;
    const kat = E.kategorien.filter((k) => k.code !== "unklar").map((k) => `<li><span class="sw" style="background:${k.farbe || "transparent"}" aria-hidden="true"></span>
      ${esc(k.titel)}<span class="meta"> – ${esc(k.code === "privat" ? "nur als Anteil je Ortsbezirk, ohne Namen" : k.name_veroeffentlichen ? "mit Namen je Gebäude" : k.darstellung)}</span></li>`).join("");
    const stand = a ? `<p>Geprüfte Erfassung, Stand ${datum(a.stand)}. Auf der Karte unter „Eigentum (geprüfte Erfassung)“, sofern Gebäude juristischer Personen erfasst sind; Anzahl je Ortsbezirk unter „Erfassungsstand“.</p>`
      : `<p class="hinweis-kasten"><strong>Noch keine geprüfte Erfassung.</strong> Die Karte zeigt deshalb noch keine Eigentümer. Erfasst wird nur, was belegt ist; Privatpersonen erscheinen nie mit Namen.</p>`;
    const g = eig && eig.gesellschaften || [];
    const tab = (liste) => `<div class="tabelle"><table><thead><tr><th scope="col">Unternehmen</th><th scope="col">Rechtsform</th><th scope="col">Gesellschafter laut Bericht</th></tr></thead>
      <tbody>${liste.map((x) => `<tr><th scope="row">${esc(x.name)}</th><td class="text">${esc(x.rechtsform || "–")}</td><td class="text">${esc(x.gesellschafter || "–")}</td></tr>`).join("")}</tbody></table></div>`;
    return `${stand}<h4>Kategorien</h4><ul class="legende-kat">${kat}</ul>
      ${g.length ? `<details class="unter"><summary>Beteiligungen der Stadt (Beteiligungsbericht ${esc(String(eig.bericht.jahr))})</summary>
        ${tab(g.filter((x) => x.pflicht))}<p class="meta">${link(eig.bericht.url, "Beteiligungsbericht")}, ${esc(eig.bericht.stand)}. Ohne Personen.</p></details>` : ""}
      <p class="meta">Gebäude für öffentliche Zwecke (Gebäudefunktion laut Kataster, nicht Eigentum) zeigt die Hauptkarte unter „Weitere Ebenen“.</p>`;
  }

  function mietvergleich(cfg, w) {
    const R = cfg.wohnen_eigentum.regeln, m = w && w.mieten;
    const regeln = `<ul><li>Je Ortsbezirk und Baujahrklasse: Median und Spanne ab ${zahl(R.mieten_zelle_min)} Angaben.</li>
      <li>Je Unternehmen, Genossenschaft oder öffentlicher Hand: ab ${zahl(R.juristische_person_min_angaben)} Angaben aus mindestens ${zahl(R.juristische_person_min_gebaeude)} Gebäuden.</li>
      <li>Je privater Vermieter:in: nie, auch nicht unter einem Kürzel.</li><li>Einzelne Angaben: nie.</li></ul>`;
    if (!m || !m.zellen || !m.zellen.length) {
      return `<p class="hinweis-kasten"><strong>Noch keine geprüften Mietangaben.</strong> ${cfg.wohnen_eigentum.mietangaben_aktiv ? "" : "Die Erfassung ist noch nicht freigegeben."}</p>${regeln}`;
    }
    const zeile = (c) => `<tr><th scope="row">${esc(c.ortsbezirk_name || c.ortsbezirk)}</th><td>${esc(c.baujahr_klasse)}</td>
      <td>${c.n >= R.mieten_zelle_min && c.median != null ? `${zahl(c.median, 2)} (${zahl(c.p25, 2)}–${zahl(c.p75, 2)})` : `<span class="luecke">${ZU_WENIG}</span>`}</td></tr>`;
    return `<p class="stichtag">Stand ${datum(m.stand)}</p><div class="tabelle"><table><caption class="visually-hidden">Nettokaltmiete je Ortsbezirk und Baujahrklasse</caption>
      <thead><tr><th scope="col">Ortsbezirk</th><th scope="col">Baujahr</th><th scope="col">€/m² Median (Spanne)</th></tr></thead><tbody>${m.zellen.map(zeile).join("")}</tbody></table></div>${regeln}`;
  }

  function erfassungsstand(cfg, w, index) {
    const a = (w && w.eigentum_anteile && w.eigentum_anteile.ortsbezirke) || {};
    const o = (index && index.ortsteile) || {};
    const zeilen = cfg.ortsteile.filter((x) => o[x.slug]).map((x) => {
      const n = o[x.slug].gebaeude, ax = a[x.slug] || {}, e = ax.erfasst || 0;
      const privat = ax.privat != null ? zahl(ax.privat) : ax.privat_hinweis ? `<span class="luecke">${ZU_WENIG}</span>` : "–";
      return `<tr><th scope="row">${esc(x.name)}</th><td>${zahl(n)}</td><td>${zahl(e)}</td><td>${zahl((100 * e) / n, 1)} %</td><td>${privat}</td></tr>`;
    }).join("");
    return `<p>Anteil der Gebäude mit belegter Kategorie. Die Eigentumskarte zeigt nur, was erfasst ist; ein niedriger Anteil heißt nicht, dass es wenig Eigentum einer Art gibt.</p>
      <div class="tabelle"><table><caption class="visually-hidden">Erfassungsstand je Ortsbezirk</caption>
      <thead><tr><th scope="col">Ortsbezirk</th><th scope="col">Gebäude</th><th scope="col">mit Kategorie</th><th scope="col">Anteil</th><th scope="col">davon privat</th></tr></thead><tbody>${zeilen}</tbody></table></div>
      <p class="meta">Privat: nur als Anzahl ab ${zahl(cfg.wohnen_eigentum.regeln.privat_anteil_min)} Gebäuden; darunter auch nicht in „mit Kategorie“ enthalten.</p>`;
  }

  function tagesordnung() {
    return `<p>Vorgänge, deren Titel Wohnen, Bauleitplanung oder Grundstücke nennen (Suchbegriffe in der Konfiguration).</p>
      <div id="top-liste" aria-live="polite"><p class="meta">Wird beim Öffnen geladen.</p></div>`;
  }
  async function tagesordnungLaden(cfg, slug, ziel) {
    const d = await fetch("data/export/vorgaenge.json").then((r) => (r.ok ? r.json() : null)).catch(() => null);
    if (!d) { ziel.innerHTML = '<p class="luecke">Vorgänge nicht verfügbar.</p>'; return; }
    const rx = new RegExp(cfg.wohnen.bezug_titel, "i");
    const o = slug && cfg.ortsteile.find((x) => x.slug === slug);
    const liste = d.vorgaenge.filter((v) => !v.verfahrenspunkt && rx.test(v.name) && (!o || v.locations.some((l) => l.ortsteil === o.name)))
      .sort((a, b) => b.date.localeCompare(a.date)).slice(0, 15);
    ziel.innerHTML = liste.length ? `<ul class="liste">${liste.map((v) => `<li><a href="./?${o ? `gebiet=ortsteil:${encodeURIComponent(slug)}` : ""}#${encodeURIComponent(v.reference)}">${esc(v.name)}</a>
      <br><span class="meta">${datum(v.date)} · ${esc(v.process[0] ? v.process[0].gremium : "")}</span></li>`).join("")}</ul>
      <p class="meta">Die 15 jüngsten; alle in der Hauptkarte über die Suche.</p>` : '<p>Keine passenden Vorgänge im Gebiet.</p>';
  }

  function begriffe(cfg) {
    const alle = [...cfg.wohnen.begriffe, ...cfg.wohnen_eigentum.glossar];
    return `<dl class="glossar">${alle.map((b) => `<dt>${esc(b.begriff)}</dt><dd>${esc(b.text)}</dd>`).join("")}</dl>`;
  }

  function methode(cfg, w) {
    const W = cfg.wohnen, z = w && w.zensus;
    return `<ul class="liste"><li><strong>Zensus:</strong> ${esc(z ? z.naeherung : "")} ${esc(W.zensus.attribution)}.</li>
      <li><strong>Bodenrichtwerte:</strong> ${esc(W.boris.filter)}. ${esc(W.boris.attribution)}.</li>
      <li><strong>Gebäude:</strong> ${esc(cfg.gebaeude.attribution)}.</li>
      <li><strong>Veröffentlichungsregeln:</strong> ${esc(cfg.wohnen_eigentum.regeln.quelle)}.</li></ul>
      <h4>Marktberichte</h4><ul class="liste">${W.berichte.map((b) => `<li>${link(b.link, esc(b.titel))}<br><span class="meta">${esc(b.herausgeber)}</span></li>`).join("")}</ul>
      <p class="meta">${esc(W.berichte_hinweis)}</p>`;
  }

  function render(ziel, { cfg, wohnen, eigentum: eig, index, slug }) {
    const offen = ziel.querySelectorAll("details.modul[open]");
    const war = offen.length ? new Set([...offen].map((d) => d.id)) : null;
    ziel.innerHTML = [
      abschnitt("zweck", "Zweck und Grenzen", zweck(cfg)),
      abschnitt("miete", "Mietniveau", mietniveau(cfg, wohnen, slug)),
      abschnitt("boden", "Verlauf: Bodenrichtwerte", verlauf(cfg, wohnen, slug), false),
      abschnitt("eigentum", "Eigentum", eigentum(cfg, wohnen, eig), false),
      abschnitt("vergleich", "Mietvergleich", mietvergleich(cfg, wohnen), false),
      abschnitt("tagesordnung", "Bezug zur Tagesordnung", tagesordnung(), false),
      abschnitt("stand", "Erfassungsstand je Ortsbezirk", erfassungsstand(cfg, wohnen, index), false),
      abschnitt("begriffe", "Begriffe", begriffe(cfg), false),
      abschnitt("methode", "Methode und Quellen", methode(cfg, wohnen), false),
    ].join("");
    if (war) ziel.querySelectorAll("details.modul").forEach((d) => { d.open = war.has(d.id); });
    const top = ziel.querySelector("#modul-tagesordnung");
    const laden = () => { if (top.open && !top.dataset.geladen) { top.dataset.geladen = "1"; tagesordnungLaden(cfg, slug, ziel.querySelector("#top-liste")); } };
    top.addEventListener("toggle", laden);
    laden();
  }
  return { render, ZU_WENIG };
})();
