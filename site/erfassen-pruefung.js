// Prüfung der Erfassung im Gerät: JSON-Schema (nur die in schemas/*.json genutzten Schlüsselwörter) und Freitextregeln.
// Freitext darf keine Hausnummern, Kontaktdaten oder Namen enthalten (Übergabe v0.4.2, W4); Hausnummern und Kontaktdaten
// werden erkannt und abgewiesen, Namen lassen sich nicht sicher erkennen, darauf weist das Formular hin.
window.ErfassenPruefung = (function () {
  "use strict";
  const typ = (v) => (Array.isArray(v) ? "array" : v === null ? "null" : Number.isInteger(v) ? "integer" : typeof v);
  const passt = (t, v) => t === typ(v) || (t === "number" && typeof v === "number");
  const gleich = (a, b) => JSON.stringify(a) === JSON.stringify(b);
  const ISO = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:\d{2})$/;

  // Fehler als Liste [{pfad, text}]
  function schema(s, v, pfad = "", fehler = []) {
    const f = (text) => fehler.push({ pfad, text });
    if (s.type && !passt(s.type, v)) { f(`erwartet ${s.type}`); return fehler; }
    if (s.enum && !s.enum.some((e) => gleich(e, v))) f("kein zulässiger Wert");
    if ("const" in s && !gleich(s.const, v)) f("kein zulässiger Wert");
    if (typeof v === "string") {
      if (s.maxLength != null && [...v].length > s.maxLength) f(`höchstens ${s.maxLength} Zeichen`);
      if (s.pattern && !new RegExp(s.pattern, "u").test(v)) f("Format ungültig");
      if (s.format === "date-time" && !(ISO.test(v) && !Number.isNaN(Date.parse(v)))) f("kein Zeitpunkt");
      if (s.format === "uri" && !/^https?:\/\/[^\s]+$/.test(v)) f("keine Adresse (https://…)");
    }
    if (typeof v === "number") {
      if (s.minimum != null && v < s.minimum) f(`mindestens ${s.minimum}`);
      if (s.maximum != null && v > s.maximum) f(`höchstens ${s.maximum}`);
    }
    if (Array.isArray(v)) {
      if (s.items) v.forEach((x, i) => schema(s.items, x, `${pfad}[${i}]`, fehler));
      if (s.uniqueItems && new Set(v.map((x) => JSON.stringify(x))).size !== v.length) f("doppelte Einträge");
    }
    if (typ(v) === "object") {
      for (const r of s.required || []) if (!(r in v)) fehler.push({ pfad: pfad ? `${pfad}.${r}` : r, text: "fehlt" });
      for (const [k, x] of Object.entries(v)) {
        const p = pfad ? `${pfad}.${k}` : k;
        if (s.properties && k in s.properties) schema(s.properties[k], x, p, fehler);
        else if (s.additionalProperties === false) fehler.push({ pfad: p, text: "nicht vorgesehen" });
      }
    }
    for (const t of s.allOf || []) schema(t, v, pfad, fehler);
    if (s.if && schema(s.if, v).length === 0 && s.then) schema(s.then, v, pfad, fehler);
    if (s.not && schema(s.not, v).length === 0) f("nicht zulässig");
    return fehler;
  }

  // Hausnummern: Straßenname mit Nummer, „Nr. 5“, „Hausnummer“; Kontaktdaten: E-Mail, Telefonnummer
  const STRASSE = /(str(a(ß|ss)e)?\.?|weg|gasse|platz|allee|ring|damm|ufer|markt|berg|hof|tor|graben|feld|pfad|steig|anger|siedlung|chaussee)\s*\d+\s*[a-z]?\b/i;
  const REGELN = [
    [STRASSE, "keine Hausnummern"],
    [/\b(nr|no|hausnr|hausnummer)\.?\s*\d/i, "keine Hausnummern"],
    [/\bhausnummer\b/i, "keine Hausnummern"],
    [/[^\s@]+@[^\s@]+\.[a-z]{2,}/i, "keine E-Mail-Adressen"],
    [/(\+|\b0)\d[\d\s/()-]{6,}\d/, "keine Telefonnummern"],
  ];
  function freitext(text, { ohneZiffern = false } = {}) {
    if (!text) return null;
    if (ohneZiffern && /\d/.test(text)) return "keine Ziffern (also keine Hausnummern)";
    const r = REGELN.find(([rx]) => rx.test(text));
    return r ? r[1] : null;
  }
  return { schema, freitext };
})();
