# Mietmonitor Witzenhausen (wiz-stadtmonitor)

> Früherer Inhalt des Repositorys `wiz-stadtmonitor`, seit Phase 1 des Stadtmonitors in diesem Unterordner. Unverändert lauffähig (`mietmonitor/index.html`).

Kleines Werkzeug zum **Sammeln und Auswerten von Mietdaten** zu Wohnungen und Häusern
in Witzenhausen (Kernstadt und Ortsteile).

## Nutzung

`index.html` im Browser öffnen, per Doppelklick oder über GitHub Pages. Es braucht keine Installation und keinen Server.

- **Erfassen:** Objektart, Ortsteil, Wohnfläche und Kaltmiete sind Pflicht. Dazu kommen optional Straße,
  Zimmer, Nebenkosten, Baujahr, Datum, Quelle, Link, Merkmale und Notiz. Der €/m²-Preis wird live berechnet.
- **Auswertung:** Median und Durchschnitt €/m² (kalt), Median-Kaltmiete und -Wohnfläche,
  aufgeschlüsselt nach Ortsteil und Größenklasse. Filterbar nach Objektart, Ortsteil und Datum.
- **Liste:** sortierbar (Klick auf Spaltenkopf), durchsuchbar, Einträge bearbeiten und löschen.
- **Export/Import:**
  - CSV (Semikolon, Dezimalkomma) öffnet sich direkt in Excel/LibreOffice. Exportiert wird die aktuell gefilterte Auswahl.
  - JSON ist die vollständige Sicherung.
  - Beim Import werden CSV- oder JSON-Dateien eingelesen. Bereits vorhandene IDs werden übersprungen. Eigene Tabellen
    lassen sich importieren, wenn die Spaltenüberschriften den Exportnamen entsprechen
    (z. B. `Ortsteil`, `Wohnfläche (m²)`, `Kaltmiete (€)`) oder den Feldschlüsseln (`ortsteil`, `flaeche`, `kaltmiete` …).

## Wichtig zur Datenspeicherung

Die Daten liegen **nur im `localStorage` des jeweiligen Browsers**. Sie werden nicht automatisch
geteilt und gehen verloren, wenn die Browserdaten gelöscht werden. Deshalb regelmäßig
„Sicherung (JSON)“ nutzen. Um mit mehreren Personen zu sammeln, kann jede Person exportieren,
die Dateien werden dann in einem Browser zusammen importiert.

## Datenschutz

Nur Objektdaten erfassen, **keine personenbezogenen Daten** (keine Namen von Mietenden oder Vermietenden,
keine Telefonnummern, keine Hausnummern). Inseratsdaten bitte manuell übernehmen. Automatisches Auslesen
von Immobilienportalen ist laut deren Nutzungsbedingungen in der Regel nicht erlaubt.

## Entwicklung

```
lib.js      Reine Logik (Validierung, Kennzahlen, CSV) – auch in Node testbar
app.js      Oberfläche
index.html  Seite
style.css   Gestaltung (inkl. Dark Mode)
test/       Tests (node:test)
```

Tests: `npm test` (Node ≥ 18, keine Abhängigkeiten).

Die Ortsteil-Vorschlagsliste steht in `lib.js` (`ORTSTEILE`). Freitext ist ebenfalls möglich.
