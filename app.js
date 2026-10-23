(function () {
  "use strict";

  const L = window.Mietlib;
  const SPEICHER_SCHLUESSEL = "mietmonitor-witzenhausen-v1";
  const $ = (sel) => document.querySelector(sel);

  const euro = new Intl.NumberFormat("de-DE", { style: "currency", currency: "EUR", maximumFractionDigits: 0 });
  const euro2 = new Intl.NumberFormat("de-DE", { style: "currency", currency: "EUR", minimumFractionDigits: 2, maximumFractionDigits: 2 });
  const zahl = new Intl.NumberFormat("de-DE", { maximumFractionDigits: 1 });
  const fmt = (f, v) => (v === null || v === undefined ? "–" : f.format(v));

  let eintraege = laden();
  let sortierung = { key: "erfasstAm", absteigend: true };

  // --- Speicher ---

  function laden() {
    try {
      const roh = localStorage.getItem(SPEICHER_SCHLUESSEL);
      return roh ? JSON.parse(roh).map(L.normalisiere) : [];
    } catch (err) {
      console.warn("Gespeicherte Daten konnten nicht gelesen werden:", err);
      return [];
    }
  }

  function speichern() {
    try {
      localStorage.setItem(SPEICHER_SCHLUESSEL, JSON.stringify(eintraege));
    } catch (err) {
      alert("Speichern im Browser nicht möglich (z. B. privates Fenster). Bitte Daten exportieren, bevor die Seite geschlossen wird.");
    }
  }

  function neueId() {
    return (crypto.randomUUID ? crypto.randomUUID() : Date.now().toString(36) + Math.random().toString(36).slice(2)).slice(0, 8);
  }

  // --- Formular ---

  const form = $("#formular");

  function optionen(select, werte, leer) {
    select.innerHTML = (leer !== undefined ? `<option value="">${leer}</option>` : "") +
      werte.map((w) => `<option>${esc(w)}</option>`).join("");
  }

  function esc(s) {
    return String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  }

  optionen(form.elements.objektart, L.OBJEKTARTEN);
  optionen(form.elements.quelle, L.QUELLEN);
  $("#ortsteilListe").innerHTML = L.ORTSTEILE.map((o) => `<option value="${esc(o)}">`).join("");
  $("#merkmale").innerHTML = L.MERKMALE.map(
    (m) => `<label><input type="checkbox" name="merkmal" value="${esc(m)}"> ${esc(m)}</label>`
  ).join("");
  optionen($("#filterArt"), L.OBJEKTARTEN, "alle");

  function formularWerte() {
    const d = new FormData(form);
    const roh = Object.fromEntries(d.entries());
    roh.merkmale = d.getAll("merkmal");
    return L.normalisiere(roh);
  }

  function vorschau() {
    const e = formularWerte();
    const qm = L.qmPreis(e);
    const wm = L.warmmiete(e);
    $("#vorschau").textContent = qm ? `${euro2.format(qm)} / m² kalt · Warmmiete ${fmt(euro, wm)}` : "";
  }

  function formularLeeren() {
    form.reset();
    form.elements.id.value = "";
    $("#formTitel").textContent = "Neuen Eintrag erfassen";
    $("#speichern").textContent = "Speichern";
    $("#abbrechen").hidden = true;
    $("#fehler").innerHTML = "";
    vorschau();
  }

  function bearbeiten(id) {
    const e = eintraege.find((x) => x.id === id);
    if (!e) return;
    formularLeeren();
    for (const f of L.FELDER) {
      const feld = form.elements[f.key];
      if (f.liste || !feld) continue;
      const v = e[f.key];
      feld.value = v === null ? "" : f.zahl ? String(v).replace(".", ",") : v;
    }
    form.querySelectorAll('input[name="merkmal"]').forEach((cb) => (cb.checked = e.merkmale.includes(cb.value)));
    $("#formTitel").textContent = "Eintrag bearbeiten";
    $("#speichern").textContent = "Änderungen speichern";
    $("#abbrechen").hidden = false;
    vorschau();
    $("#erfassung").scrollIntoView({ behavior: "smooth" });
  }

  form.addEventListener("input", vorschau);
  $("#abbrechen").addEventListener("click", formularLeeren);

  form.addEventListener("submit", (ev) => {
    ev.preventDefault();
    const e = formularWerte();
    const fehler = L.validiere(e);
    $("#fehler").innerHTML = fehler.map((f) => `<li>${esc(f)}</li>`).join("");
    if (fehler.length) return;

    const vorhanden = e.id && eintraege.findIndex((x) => x.id === e.id);
    if (e.id && vorhanden >= 0) {
      e.erfasstAm = eintraege[vorhanden].erfasstAm;
      eintraege[vorhanden] = e;
    } else {
      e.id = neueId();
      e.erfasstAm = new Date().toISOString().slice(0, 10);
      eintraege.push(e);
    }
    speichern();
    formularLeeren();
    alles();
  });

  // --- Auswertung ---

  function gefiltert() {
    const art = $("#filterArt").value;
    const ort = $("#filterOrt").value;
    const von = $("#filterVon").value;
    return eintraege.filter((e) =>
      (!art || e.objektart === art) &&
      (!ort || e.ortsteil === ort) &&
      (!von || (e.angebotsdatum || e.erfasstAm) >= von)
    );
  }

  function ortsteilFilterAktualisieren() {
    const sel = $("#filterOrt");
    const aktuell = sel.value;
    const orte = [...new Set(eintraege.map((e) => e.ortsteil).filter(Boolean))].sort((a, b) => a.localeCompare(b, "de"));
    optionen(sel, orte, "alle");
    sel.value = orte.includes(aktuell) ? aktuell : "";
  }

  function kennzahlTabelle(tabelle, zeilen, spaltenTitel) {
    if (!zeilen.length) {
      tabelle.innerHTML = '<tr class="leer"><td>Noch keine Daten</td></tr>';
      return;
    }
    tabelle.innerHTML =
      `<thead><tr><th>${spaltenTitel}</th><th class="zahl">Anzahl</th><th class="zahl">Median €/m²</th>` +
      `<th class="zahl">Spanne €/m²</th><th class="zahl">Median Kaltmiete</th></tr></thead><tbody>` +
      zeilen.map((z) =>
        `<tr><td>${esc(z.gruppe)}</td><td class="zahl">${z.anzahl}</td><td class="zahl">${fmt(euro2, z.medianQm)}</td>` +
        `<td class="zahl">${fmt(euro2, z.minQm)} – ${fmt(euro2, z.maxQm)}</td><td class="zahl">${fmt(euro, z.medianKalt)}</td></tr>`
      ).join("") + "</tbody>";
  }

  function auswertung() {
    const daten = gefiltert();
    const k = L.kennzahlen(daten);
    const kacheln = [
      ["Einträge", k.anzahl],
      ["Median €/m² kalt", fmt(euro2, k.medianQm)],
      ["Ø €/m² kalt", fmt(euro2, k.mittelQm)],
      ["Median Kaltmiete", fmt(euro, k.medianKalt)],
      ["Median Wohnfläche", k.medianFlaeche === null ? "–" : zahl.format(k.medianFlaeche) + " m²"],
    ];
    $("#kacheln").innerHTML = kacheln
      .map(([t, w]) => `<div class="kachel"><div class="wert">${w}</div><div class="titel">${t}</div></div>`)
      .join("");

    kennzahlTabelle($("#tabOrt"), L.gruppiert(daten, "ortsteil"), "Ortsteil");
    const reihenfolge = ["unter 40 m²", "40–59 m²", "60–79 m²", "80–99 m²", "ab 100 m²", "unbekannt"];
    const groessen = L.gruppiert(daten, L.groessenklasse)
      .sort((a, b) => reihenfolge.indexOf(a.gruppe) - reihenfolge.indexOf(b.gruppe));
    kennzahlTabelle($("#tabGroesse"), groessen, "Wohnfläche");
  }

  ["#filterArt", "#filterOrt", "#filterVon"].forEach((s) => $(s).addEventListener("input", auswertung));

  // --- Eintragsliste ---

  const SPALTEN = [
    { key: "erfasstAm", titel: "Erfasst" },
    { key: "objektart", titel: "Art" },
    { key: "ortsteil", titel: "Ortsteil" },
    { key: "strasse", titel: "Straße" },
    { key: "flaeche", titel: "m²", zahl: true, f: (v) => fmt(zahl, v) },
    { key: "zimmer", titel: "Zi.", zahl: true, f: (v) => fmt(zahl, v) },
    { key: "kaltmiete", titel: "Kalt", zahl: true, f: (v) => fmt(euro, v) },
    { key: "warm", titel: "Warm", zahl: true, wert: L.warmmiete, f: (v) => fmt(euro, v) },
    { key: "qm", titel: "€/m²", zahl: true, wert: L.qmPreis, f: (v) => fmt(euro2, v) },
    { key: "quelle", titel: "Quelle" },
    { key: "notiz", titel: "Notiz", klasse: "notiz" },
  ];

  function spaltenWert(s, e) {
    return s.wert ? s.wert(e) : e[s.key];
  }

  function liste() {
    const q = $("#suche").value.trim().toLowerCase();
    const s = SPALTEN.find((x) => x.key === sortierung.key) || SPALTEN[0];
    const daten = eintraege
      .filter((e) => !q || [e.ortsteil, e.strasse, e.notiz, e.objektart, e.quelle, e.merkmale.join(" ")].join(" ").toLowerCase().includes(q))
      .sort((a, b) => {
        const va = spaltenWert(s, a), vb = spaltenWert(s, b);
        let r;
        if (va === null || va === "") r = 1;
        else if (vb === null || vb === "") r = -1;
        else r = typeof va === "number" ? va - vb : String(va).localeCompare(String(vb), "de");
        return sortierung.absteigend ? -r : r;
      });

    $("#anzahl").textContent = `(${eintraege.length})`;
    const pfeil = (key) => (sortierung.key === key ? (sortierung.absteigend ? " ▼" : " ▲") : "");
    const kopf = SPALTEN.map((x) => `<th data-sort="${x.key}" class="${x.zahl ? "zahl" : ""}">${x.titel}${pfeil(x.key)}</th>`).join("") + "<th></th>";
    const koerper = daten.length
      ? daten.map((e) =>
          "<tr>" +
          SPALTEN.map((x) => {
            const v = spaltenWert(x, e);
            const inhalt = x.f ? x.f(v) : esc(v);
            const zelle = x.key === "strasse" && e.link ? `<a href="${esc(e.link)}" target="_blank" rel="noopener">${inhalt || "Inserat"}</a>` : inhalt;
            return `<td class="${x.zahl ? "zahl" : ""} ${x.klasse || ""}">${zelle}</td>`;
          }).join("") +
          `<td><button class="klein sekundaer" data-bearbeiten="${esc(e.id)}">Bearbeiten</button> ` +
          `<button class="klein gefahr" data-loeschen="${esc(e.id)}">Löschen</button></td></tr>`
        ).join("")
      : `<tr class="leer"><td colspan="${SPALTEN.length + 1}">${eintraege.length ? "Keine Treffer" : "Noch keine Einträge erfasst"}</td></tr>`;
    $("#tabEintraege").innerHTML = `<thead><tr>${kopf}</tr></thead><tbody>${koerper}</tbody>`;
  }

  $("#suche").addEventListener("input", liste);
  $("#tabEintraege").addEventListener("click", (ev) => {
    const th = ev.target.closest("th[data-sort]");
    if (th) {
      const key = th.dataset.sort;
      sortierung = { key, absteigend: sortierung.key === key ? !sortierung.absteigend : false };
      return liste();
    }
    const b = ev.target.closest("button");
    if (!b) return;
    if (b.dataset.bearbeiten) bearbeiten(b.dataset.bearbeiten);
    if (b.dataset.loeschen && confirm("Diesen Eintrag wirklich löschen?")) {
      eintraege = eintraege.filter((e) => e.id !== b.dataset.loeschen);
      speichern();
      alles();
    }
  });

  // --- Export / Import ---

  function herunterladen(name, inhalt, typ) {
    const url = URL.createObjectURL(new Blob([inhalt], { type: typ }));
    const a = Object.assign(document.createElement("a"), { href: url, download: name });
    document.body.appendChild(a);
    a.click();
    a.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }

  const heute = () => new Date().toISOString().slice(0, 10);
  $("#exportCsv").addEventListener("click", () =>
    herunterladen(`mietdaten-witzenhausen-${heute()}.csv`, L.zuCsv(gefiltert()), "text/csv;charset=utf-8"));
  $("#exportJson").addEventListener("click", () =>
    herunterladen(`mietdaten-witzenhausen-${heute()}.json`, JSON.stringify(eintraege, null, 2), "application/json"));

  $("#import").addEventListener("change", async (ev) => {
    const datei = ev.target.files[0];
    ev.target.value = "";
    if (!datei) return;
    try {
      const text = await datei.text();
      const neu = /\.json$/i.test(datei.name) ? JSON.parse(text).map(L.normalisiere) : L.vonCsv(text);
      const gueltig = neu.filter((e) => L.validiere(e).length === 0);
      const bekannt = new Set(eintraege.map((e) => e.id));
      let hinzugefuegt = 0;
      for (const e of gueltig) {
        if (e.id && bekannt.has(e.id)) continue;
        e.id = e.id || neueId();
        e.erfasstAm = e.erfasstAm || heute();
        eintraege.push(e);
        bekannt.add(e.id);
        hinzugefuegt++;
      }
      speichern();
      alles();
      alert(`${hinzugefuegt} Einträge importiert.` +
        (neu.length - gueltig.length ? ` ${neu.length - gueltig.length} ungültige Zeilen übersprungen.` : "") +
        (gueltig.length - hinzugefuegt ? ` ${gueltig.length - hinzugefuegt} bereits vorhanden.` : ""));
    } catch (err) {
      alert("Import fehlgeschlagen: " + err.message);
    }
  });

  function alles() {
    ortsteilFilterAktualisieren();
    auswertung();
    liste();
  }

  formularLeeren();
  alles();
})();
