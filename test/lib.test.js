const test = require("node:test");
const assert = require("node:assert/strict");
const L = require("../lib.js");

const beispiel = (x = {}) => L.normalisiere({
  id: "a1", erfasstAm: "2026-10-01", objektart: "Wohnung", ortsteil: "Kernstadt",
  flaeche: "62,5", kaltmiete: "500", nebenkosten: "150", merkmale: ["Balkon/Terrasse"], ...x,
});

test("zahlOderNull versteht deutsches Zahlenformat", () => {
  assert.equal(L.zahlOderNull("1.234,56"), 1234.56);
  assert.equal(L.zahlOderNull("650,5 €"), 650.5);
  assert.equal(L.zahlOderNull("72.5"), 72.5);
  assert.equal(L.zahlOderNull(""), null);
  assert.equal(L.zahlOderNull("abc"), null);
});

test("validiere erkennt Pflichtfelder und Unplausibles", () => {
  assert.deepEqual(L.validiere(beispiel()), []);
  const fehler = L.validiere(beispiel({ ortsteil: "", flaeche: "0", link: "www.x.de" }));
  assert.equal(fehler.length, 3);
});

test("qm-Preis, Warmmiete, Median", () => {
  const e = beispiel();
  assert.equal(L.qmPreis(e), 8);
  assert.equal(L.warmmiete(e), 650);
  assert.equal(L.median([3, 1, 2]), 2);
  assert.equal(L.median([4, 1, 2, 3]), 2.5);
  assert.equal(L.median([]), null);
});

test("gruppiert nach Ortsteil", () => {
  const daten = [beispiel(), beispiel({ id: "a2", kaltmiete: "625" }), beispiel({ id: "a3", ortsteil: "Gertenbach" })];
  const g = L.gruppiert(daten, "ortsteil");
  assert.equal(g[0].gruppe, "Kernstadt");
  assert.equal(g[0].anzahl, 2);
  assert.equal(g[0].medianQm, 9);
});

test("CSV-Export und -Import ergeben dieselben Daten", () => {
  const daten = [beispiel({ notiz: 'Altbau; "ruhig"\nHinterhaus', merkmale: ["Garten", "Keller"] })];
  const zurueck = L.vonCsv(L.zuCsv(daten));
  assert.deepEqual(zurueck, daten);
});

test("CSV-Import mit Komma-Trenner und Feldschlüsseln", () => {
  const csv = "ortsteil,objektart,flaeche,kaltmiete\nErmschwerd,Haus,120,950\n";
  const [e] = L.vonCsv(csv);
  assert.equal(e.ortsteil, "Ermschwerd");
  assert.equal(e.flaeche, 120);
  assert.deepEqual(L.validiere(e), []);
});
