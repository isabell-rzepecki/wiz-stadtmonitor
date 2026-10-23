// Reine Logik ohne DOM: Validierung, Kennzahlen, CSV. Läuft im Browser und in Node (Tests).
(function (root) {
  "use strict";

  const ORTSTEILE = [
    "Kernstadt",
    "Albshausen",
    "Berlepsch-Ellerode",
    "Blickershausen",
    "Dohrenbach",
    "Ellingerode",
    "Ermschwerd",
    "Gertenbach",
    "Hubenrode",
    "Hundelshausen",
    "Kleinalmerode",
    "Roßbach",
    "Unterrieden",
    "Wendershausen",
    "Ziegenhagen",
  ];

  const OBJEKTARTEN = ["Wohnung", "Haus", "WG-Zimmer", "Sonstiges"];
  const QUELLEN = ["Inserat", "Mietvertrag", "Befragung", "Sonstiges"];
  const MERKMALE = ["Balkon/Terrasse", "Garten", "Einbauküche", "Stellplatz/Garage", "Keller", "Möbliert", "Barrierearm"];

  // Reihenfolge = Spaltenreihenfolge im CSV.
  const FELDER = [
    { key: "id", label: "ID" },
    { key: "erfasstAm", label: "Erfasst am" },
    { key: "angebotsdatum", label: "Angebots-/Vertragsdatum" },
    { key: "objektart", label: "Objektart" },
    { key: "ortsteil", label: "Ortsteil" },
    { key: "strasse", label: "Straße" },
    { key: "flaeche", label: "Wohnfläche (m²)", zahl: true },
    { key: "zimmer", label: "Zimmer", zahl: true },
    { key: "kaltmiete", label: "Kaltmiete (€)", zahl: true },
    { key: "nebenkosten", label: "Nebenkosten (€)", zahl: true },
    { key: "baujahr", label: "Baujahr", zahl: true },
    { key: "merkmale", label: "Merkmale", liste: true },
    { key: "quelle", label: "Quelle" },
    { key: "link", label: "Link" },
    { key: "notiz", label: "Notiz" },
  ];

  function zahlOderNull(wert) {
    if (wert === null || wert === undefined) return null;
    if (typeof wert === "number") return Number.isFinite(wert) ? wert : null;
    let s = String(wert).trim().replace(/\s|€/g, "");
    if (s === "") return null;
    // "1.234,56" -> "1234.56"; "650,5" -> "650.5"
    if (s.includes(",")) s = s.replace(/\./g, "").replace(",", ".");
    const n = Number(s);
    return Number.isFinite(n) ? n : null;
  }

  function normalisiere(eintrag) {
    const e = {};
    for (const f of FELDER) {
      const v = eintrag[f.key];
      if (f.zahl) e[f.key] = zahlOderNull(v);
      else if (f.liste) {
        e[f.key] = Array.isArray(v)
          ? v.map(String).map((s) => s.trim()).filter(Boolean)
          : String(v ?? "").split(/[|,]/).map((s) => s.trim()).filter(Boolean);
      } else e[f.key] = String(v ?? "").trim();
    }
    return e;
  }

  // Gibt eine Liste von Fehlermeldungen zurück (leer = gültig).
  function validiere(e) {
    const fehler = [];
    if (!e.objektart) fehler.push("Objektart fehlt.");
    if (!e.ortsteil) fehler.push("Ortsteil fehlt.");
    if (e.flaeche === null || e.flaeche <= 0) fehler.push("Wohnfläche muss größer als 0 sein.");
    else if (e.flaeche > 1000) fehler.push("Wohnfläche über 1000 m² – bitte prüfen.");
    if (e.kaltmiete === null || e.kaltmiete <= 0) fehler.push("Kaltmiete muss größer als 0 sein.");
    if (e.nebenkosten !== null && e.nebenkosten < 0) fehler.push("Nebenkosten dürfen nicht negativ sein.");
    if (e.zimmer !== null && (e.zimmer <= 0 || e.zimmer > 50)) fehler.push("Zimmeranzahl unplausibel.");
    if (e.baujahr !== null && (e.baujahr < 1200 || e.baujahr > new Date().getFullYear() + 2)) {
      fehler.push("Baujahr unplausibel.");
    }
    if (e.link && !/^https?:\/\//i.test(e.link)) fehler.push("Link muss mit http:// oder https:// beginnen.");
    return fehler;
  }

  function qmPreis(e) {
    if (!e.flaeche || !e.kaltmiete) return null;
    return e.kaltmiete / e.flaeche;
  }

  function warmmiete(e) {
    if (e.kaltmiete === null) return null;
    return e.kaltmiete + (e.nebenkosten ?? 0);
  }

  function median(werte) {
    const s = werte.filter((w) => w !== null && Number.isFinite(w)).sort((a, b) => a - b);
    if (s.length === 0) return null;
    const m = Math.floor(s.length / 2);
    return s.length % 2 ? s[m] : (s[m - 1] + s[m]) / 2;
  }

  function mittelwert(werte) {
    const s = werte.filter((w) => w !== null && Number.isFinite(w));
    return s.length ? s.reduce((a, b) => a + b, 0) / s.length : null;
  }

  function kennzahlen(eintraege) {
    const qm = eintraege.map(qmPreis);
    const gueltig = qm.filter((w) => w !== null);
    return {
      anzahl: eintraege.length,
      medianQm: median(qm),
      mittelQm: mittelwert(qm),
      minQm: gueltig.length ? Math.min(...gueltig) : null,
      maxQm: gueltig.length ? Math.max(...gueltig) : null,
      medianKalt: median(eintraege.map((e) => e.kaltmiete)),
      medianFlaeche: median(eintraege.map((e) => e.flaeche)),
    };
  }

  // Gruppiert nach einem Feld oder einer Funktion und liefert Kennzahlen je Gruppe, absteigend nach Anzahl.
  function gruppiert(eintraege, schluessel) {
    const fn = typeof schluessel === "function" ? schluessel : (e) => e[schluessel] || "–";
    const gruppen = new Map();
    for (const e of eintraege) {
      const k = fn(e);
      if (!gruppen.has(k)) gruppen.set(k, []);
      gruppen.get(k).push(e);
    }
    return [...gruppen.entries()]
      .map(([gruppe, liste]) => ({ gruppe, ...kennzahlen(liste) }))
      .sort((a, b) => b.anzahl - a.anzahl || String(a.gruppe).localeCompare(String(b.gruppe), "de"));
  }

  function groessenklasse(e) {
    const f = e.flaeche;
    if (f === null) return "unbekannt";
    if (f < 40) return "unter 40 m²";
    if (f < 60) return "40–59 m²";
    if (f < 80) return "60–79 m²";
    if (f < 100) return "80–99 m²";
    return "ab 100 m²";
  }

  // --- CSV (Semikolon, Dezimalkomma: öffnet sich direkt in deutschem Excel/LibreOffice) ---

  function csvZelle(v) {
    const s = String(v ?? "");
    return /[";\n\r]/.test(s) ? '"' + s.replace(/"/g, '""') + '"' : s;
  }

  function zuCsv(eintraege) {
    const kopf = FELDER.map((f) => f.label).concat("Warmmiete (€)", "€/m² kalt");
    const zeilen = eintraege.map((e) => {
      const werte = FELDER.map((f) => {
        const v = e[f.key];
        if (f.liste) return (v || []).join(" | ");
        if (f.zahl) return v === null || v === undefined ? "" : String(v).replace(".", ",");
        return v;
      });
      const wm = warmmiete(e);
      const qm = qmPreis(e);
      werte.push(wm === null ? "" : String(wm).replace(".", ","));
      werte.push(qm === null ? "" : qm.toFixed(2).replace(".", ","));
      return werte.map(csvZelle).join(";");
    });
    return "﻿" + [kopf.map(csvZelle).join(";")].concat(zeilen).join("\r\n") + "\r\n";
  }

  function parseCsvZeilen(text) {
    text = text.replace(/^﻿/, "");
    const erste = text.split(/\r?\n/, 1)[0];
    const trenner = (erste.match(/;/g) || []).length >= (erste.match(/,/g) || []).length ? ";" : ",";
    const zeilen = [];
    let zeile = [];
    let zelle = "";
    let inQuotes = false;
    for (let i = 0; i < text.length; i++) {
      const c = text[i];
      if (inQuotes) {
        if (c === '"' && text[i + 1] === '"') { zelle += '"'; i++; }
        else if (c === '"') inQuotes = false;
        else zelle += c;
      } else if (c === '"') inQuotes = true;
      else if (c === trenner) { zeile.push(zelle); zelle = ""; }
      else if (c === "\n" || c === "\r") {
        if (c === "\r" && text[i + 1] === "\n") i++;
        zeile.push(zelle); zeilen.push(zeile); zeile = []; zelle = "";
      } else zelle += c;
    }
    if (zelle !== "" || zeile.length) { zeile.push(zelle); zeilen.push(zeile); }
    return zeilen.filter((z) => z.some((x) => x.trim() !== ""));
  }

  // Ordnet Spalten über die Überschrift zu (Label oder Feldschlüssel), damit auch eigene Tabellen importierbar sind.
  function vonCsv(text) {
    const zeilen = parseCsvZeilen(text);
    if (zeilen.length === 0) return [];
    const norm = (s) => s.trim().toLowerCase();
    const index = {};
    zeilen[0].forEach((titel, i) => {
      const f = FELDER.find((f) => norm(f.label) === norm(titel) || norm(f.key) === norm(titel));
      if (f) index[f.key] = i;
    });
    return zeilen.slice(1).map((z) => {
      const roh = {};
      for (const [key, i] of Object.entries(index)) roh[key] = z[i] ?? "";
      return normalisiere(roh);
    });
  }

  const api = {
    ORTSTEILE, OBJEKTARTEN, QUELLEN, MERKMALE, FELDER,
    zahlOderNull, normalisiere, validiere, qmPreis, warmmiete,
    median, mittelwert, kennzahlen, gruppiert, groessenklasse,
    zuCsv, vonCsv, parseCsvZeilen,
  };

  if (typeof module !== "undefined" && module.exports) module.exports = api;
  else root.Mietlib = api;
})(typeof globalThis !== "undefined" ? globalThis : this);
