# Stadtmonitor Witzenhausen (wiz-stadtmonitor)

Der Stadtmonitor erschließt die Sitzungsinformationen der Stadt Witzenhausen in drei Dimensionen: **räumlich** (Karte und Liste nach Ortsbezirk), **zeitlich** (Sitzungskalender, Zeitleiste, Prozesslinie über die Vorlagennummer) und **nach Gremien**. Jede Angabe ist auf ein Quelldokument rückführbar.

**Stand: Phase 1 (Übernahme und Entkopplung).** Die Seite steht, die Datenpipeline folgt in Phase 2. Ohne Daten zeigt die Seite einen Hinweis.

## Quellen und Grenzen

- **Grundlage** sind die Einladungen (PDF) in den [amtlichen Bekanntmachungen](https://www.witzenhausen.eu/amtliche-bekanntmachungen/), veröffentlicht ab Juli 2024.
- **Was fehlt:** Beschlussergebnisse, Niederschriften und Vorlagentexte sind dort nicht veröffentlicht. Die Prozesslinie kennzeichnet sie als Lücke und leitet nichts ab.
- **SessionNet** wird nicht automatisiert abgerufen, nur verlinkt.
- **Ortsbezüge** sind abgeleitet. Jeder trägt Stufe (A Gremium, B Regel, C Sprachmodell), Methode, Konfidenz und Fundstelle.
- **Kartenhintergrund:** basemap.de (BKG, CC BY 4.0).
- **Lizenzen:** siehe [`data/LICENSE-DATA.md`](data/LICENSE-DATA.md), Recherche in [`docs/Datenquellen_Geodaten_Witzenhausen.md`](docs/Datenquellen_Geodaten_Witzenhausen.md).

## Aufbau

```
config/stadt.json   Alle stadtspezifischen Werte (Name, Gremien, Ortsbezirke, Karte, Farben, Texte)
site/               Seite (Leaflet, Zeitleiste, Liste, Prozesslinie), ohne Build-Schritt
pipeline/           Python-Pipeline; jetzt: Seite zusammenstellen (python -m pipeline site → _site/)
tools/kontrast.py   WCAG-Kontrastprüfung der Farb-Tokens aus config/stadt.json
tests/              Python-Tests, Browser-Tests (Playwright, axe-core), Testdaten
phase0/             Bestandsaufnahme: Bericht, Stichprobe (TSV), Explorationsskripte
docs/               Projektprompt, Recherche zu Datenquellen
mietmonitor/        Früherer Inhalt des Repositorys (Mietdaten-Erfassung), unverändert lauffähig
```

## Prüfen

```
python3 -m unittest discover -s tests -t .     # Konfiguration, Kontrast, Zusammenstellen
python3 tools/kontrast.py                       # Kontraste hell und dunkel
npm install --prefix tests/browser && bash tests/browser/run.sh   # Browser und Barrierefreiheit
```

## Gestaltung

Die Grundfarbe ist `#f4726b`. Auf ihr steht nur dunkler Text (6,2:1). Für Text und Links dient die Ableitung `#b8352e` (5,9:1 auf Weiß), im Dunkelmodus `#f8a29d`.

Schriften: Lilita One für Überschriften (ohne künstliches Fetten), Space Mono für den Text, beide selbst gehostet mit OFL-Lizenz (`site/fonts/`).

## Herkunft und Lizenz

Code unter MIT ([`LICENSE`](LICENSE)). Seite, Zeitleiste und Pipeline-Grundmodule stammen aus der [RIS-Karte Bonn](https://github.com/daimpad/allris-test) von Damian Paderta (MIT). Es handelt sich um eine unabhängige Kopie ohne gemeinsame Codebasis.

Weitere Lizenzen:

- Leaflet: BSD-2
- Leaflet.markercluster: MIT
- Schriften: SIL OFL 1.1
