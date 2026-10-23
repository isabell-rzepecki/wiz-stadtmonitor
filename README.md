# Stadtmonitor Witzenhausen (wiz-stadtmonitor)

Der Stadtmonitor erschließt die Sitzungsinformationen der Stadt Witzenhausen in drei Dimensionen: **räumlich** (Karte und Liste nach Ortsbezirk), **zeitlich** (Sitzungskalender, Zeitleiste, Prozesslinie über die Vorlagennummer) und **nach Gremien**. Jede Angabe ist auf ein Quelldokument rückführbar.

**Stand: Phase 2 (Datenpipeline).** Die Pipeline ruft täglich alle Einladungen ab, liest Kopf und Tagesordnung, fasst TOPs über die Vorlagennummer zu Vorgängen zusammen und verortet nach Stufe A (Ortsbeirat → Ortsteil) sowie über Plannummern der Bauleitplanung. Straßen und Flurstücke (Stufe B) folgen mit den Gemarkungsflächen in Phase 3.

## Quellen und Grenzen

- **Grundlage** sind die Einladungen (PDF) in den [amtlichen Bekanntmachungen](https://www.witzenhausen.eu/amtliche-bekanntmachungen/), veröffentlicht ab Juli 2024.
- **Was fehlt:** Beschlussergebnisse, Niederschriften und Vorlagentexte sind dort nicht veröffentlicht. Die Prozesslinie kennzeichnet sie als Lücke und leitet nichts ab.
- **SessionNet** wird nicht automatisiert abgerufen, nur verlinkt.
- **Ortsbezüge** sind abgeleitet. Jeder trägt Stufe (A Gremium, B Regel, C Sprachmodell), Methode, Konfidenz und Fundstelle.
- **Kartenhintergrund:** basemap.de (BKG, CC BY 4.0).
- **Lizenzen:** siehe [`data/LICENSE-DATA.md`](data/LICENSE-DATA.md), Recherche in [`docs/Datenquellen_Geodaten_Witzenhausen.md`](docs/Datenquellen_Geodaten_Witzenhausen.md).

## Grenzen der Daten

- **Zeitraum:** Einladungen sind ab Juli 2024 veröffentlicht; ältere Sitzungen fehlen.
- **Ergebnisse:** Beschlüsse, Niederschriften und Vorlagentexte stehen nicht in den Bekanntmachungen. Die Prozesslinie zeigt je Station „Ergebnis nicht veröffentlicht“.
- **Nichtöffentliche Sitzungen** erscheinen ohne Tagesordnung.
- **Ortsbezirke:** Die Flächen sind aus den 17 Gemarkungen abgeleitet (HVBG, dl-de/zero-2.0, `data/geo/dl-de-zero/ortsbezirke.geojson`). Die Gleichsetzung Gemarkung = Ortsbezirk ist plausibel, aber noch nicht mit § 6 der Hauptsatzung abgeglichen; Bischhausen und Hübenthal sind offen (Issue #3).
- **Verortung:** Stufe A ordnet den Ortsbezug des Gremiums zu, nicht zwingend den des Gegenstands. Plan-Abgleiche, deren Änderung noch nicht im Datensatz der Stadt steht, zeigen auf den Ursprungsplan und sind als „mittel“ gekennzeichnet.
- **Bauleitplanung (Bebauungspläne, Flächennutzungsplan):**
  - Die Umringe der Stadt stehen unter der Nutzungsbedingung „Die Nutzung ohne vertragliche Vereinbarung mit der Stadt Witzenhausen ist nur für nicht kommerzielle Zwecke erlaubt.“ Eine gesonderte Freigabe gibt es nicht.
  - Der Stadtmonitor nutzt sie deshalb nur im Build. Die Rohgeometrien liegen in `data/geo/restricted/`; der Ordner ist von der Versionierung ausgeschlossen.
  - Ausgeliefert werden sie nur als Kartenebene mit dem Hinweis „Geltungsbereiche Bauleitplanung: Magistrat der Stadt Witzenhausen – Nutzung nur für nicht kommerzielle Zwecke“. Es gibt keinen GeoJSON-Export, keinen Download in der Oberfläche und keine Flächen im Datenpaket.
  - Im Repository und im Datenpaket bleibt nur die Zuordnung Vorgang → Plannummer (`audit/verortung_bauleitplanung.tsv`). Sie enthält keine Geometrie der Stadt.
- **Quellen:** Das Quellenregister mit Prüfstatus steht in [`data/quellen_register.tsv`](data/quellen_register.tsv).

## Aktualisierung

Der Workflow `.github/workflows/pages.yml` läuft täglich um 04:17 UTC und bei jedem Push. Er führt `python -m pipeline all` aus:

1. Abruf der Einladungen und Umringe;
2. Aufbau der Vorgänge;
3. Prüfung;
4. Datenpaket;
5. Seite.

Danach veröffentlicht er die Seite auf GitHub Pages. Die Rohdaten liegen nur im Zwischenspeicher des Workflows. Voraussetzung: In den Repository-Einstellungen unter „Pages“ ist als Quelle „GitHub Actions“ gewählt.

Pull Requests prüft `.github/workflows/tests.yml` mit Python-Tests, Kontrastprüfung und Browser-Tests mit axe-core.

## Aufbau

```
config/stadt.json   Alle stadtspezifischen Werte (Name, Gremien, Ortsbezirke, Karte, Farben, Texte)
site/               Seite (Leaflet, Zeitleiste, Liste, Prozesslinie), ohne Build-Schritt
pipeline/           Python-Pipeline: fetch, fetch-plaene, build, check, package, site (python -m pipeline all)
tools/kontrast.py   WCAG-Kontrastprüfung der Farb-Tokens aus config/stadt.json
tests/              Python-Tests, Browser-Tests (Playwright, axe-core), Testdaten
phase0/             Bestandsaufnahme: Bericht, Stichprobe (TSV), Explorationsskripte
docs/               Projektprompts (v0.1, Übergabe v0.2 mit Material), Recherche zu Datenquellen
data/quellen_register.tsv   Quellenregister mit Prüfstatus
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
