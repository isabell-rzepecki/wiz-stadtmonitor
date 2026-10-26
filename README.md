# Stadtmonitor Witzenhausen (wiz-stadtmonitor)

Der Stadtmonitor erschließt die Sitzungsinformationen der Stadt Witzenhausen in drei Dimensionen: **räumlich** (Karte und Liste nach Ortsbezirk), **zeitlich** (Sitzungskalender, Zeitleiste, Prozesslinie über die Vorlagennummer) und **nach Gremien**. Jede Angabe ist auf ein Quelldokument rückführbar.

**Stand:** Die Pipeline ruft täglich alle Einladungen ab, liest Kopf und Tagesordnung, fasst TOPs über die Vorlagennummer zu Vorgängen zusammen und verortet nach Stufe A (Ortsbeirat → Ortsteil) sowie über Plannummern der Bauleitplanung. Stufe B gleicht die Titel mit Straßen- und Lagenamen (Hauskoordinaten und Lagebezeichnungen der HVBG), Gemarkungen, Ortsteilnamen und Flurstücksangaben ab.

## Quellen und Grenzen

- **Grundlage** sind die Einladungen (PDF) in den [amtlichen Bekanntmachungen](https://www.witzenhausen.eu/amtliche-bekanntmachungen/), veröffentlicht ab Juli 2024.
- **Was fehlt:** Beschlussergebnisse, Niederschriften und Vorlagentexte sind dort nicht veröffentlicht. Die Prozesslinie kennzeichnet sie als Lücke und leitet nichts ab.
- **SessionNet** wird nicht automatisiert abgerufen, nur verlinkt.
- **Ortsbezüge** sind abgeleitet. Jeder trägt Stufe (A Gremium, B Regel), Methode, Konfidenz und Fundstelle. Stufe C (Sprachmodell, `pipeline/sprachmodell.py`) ist vorbereitet, aber nicht im Ablauf.
- **Kartenhintergrund:** basemap.de (BKG, CC BY 4.0).
- **Lizenzen:** siehe [`data/LICENSE-DATA.md`](data/LICENSE-DATA.md), Recherche in [`docs/Datenquellen_Geodaten_Witzenhausen.md`](docs/Datenquellen_Geodaten_Witzenhausen.md).

## Grenzen der Daten

- **Zeitraum:** Einladungen sind ab Juli 2024 veröffentlicht; ältere Sitzungen fehlen.
- **Ergebnisse:** Beschlüsse, Niederschriften und Vorlagentexte stehen nicht in den Bekanntmachungen. Die Prozesslinie zeigt je Station „Ergebnis nicht veröffentlicht“.
- **Nichtöffentliche Sitzungen** erscheinen ohne Tagesordnung.
- **Ortsbezirke:** Die Flächen sind aus den 17 Gemarkungen abgeleitet (HVBG, dl-de/zero-2.0, `data/geo/dl-de-zero/ortsbezirke.geojson`). § 6 der Hauptsatzung (2014, selbst eingesehen) bestimmt für jeden der 16 Ortsbezirke „das Gebiet der ehemaligen Gemeinde“; die Kernstadt ist kein Ortsbezirk. Bischhausen gehört zur Kernstadt (Gemarkung Witzenhausen, 1928 eingemeindet), Hübenthal zu Berlepsch-Ellerode (Gemarkung Berlepsch-Ellerode); Beleg: Historisches Ortslexikon Hessen (LAGIS). Dass die Gemarkungsgrenzen überall den Grenzen der ehemaligen Gemeinden entsprechen, ist eine Annahme; die Seite kennzeichnet sie als solche.
- **Stufe B:** Straßennamen, die in mehreren Ortsteilen vorkommen, werden nur über das beratende Gremium, einen genannten Ortsteil, eine Gemarkung oder eine weitere eindeutige Straße im Titel eingegrenzt; sonst bleiben sie ohne Ort und stehen im Audit `verortung_stufe_b.tsv` als „mehrdeutig“. Hausnummern werden nicht ausgewertet.
- **Verortung:** Stufe A ordnet den Ortsbezug des Gremiums zu, nicht zwingend den des Gegenstands. Plan-Abgleiche, deren Änderung noch nicht im Datensatz der Stadt steht, zeigen auf den Ursprungsplan und sind als „mittel“ gekennzeichnet.
- **Bauleitplanung (Bebauungspläne, Flächennutzungsplan):**
  - Die Umringe der Stadt stehen unter der Nutzungsbedingung „Die Nutzung ohne vertragliche Vereinbarung mit der Stadt Witzenhausen ist nur für nicht kommerzielle Zwecke erlaubt.“ Eine gesonderte Freigabe gibt es nicht.
  - Der Stadtmonitor nutzt sie deshalb nur im Build. Die Rohgeometrien liegen in `data/geo/restricted/`; der Ordner ist von der Versionierung ausgeschlossen.
  - Ausgeliefert werden sie nur als Kartenebene mit dem Hinweis „Geltungsbereiche Bauleitplanung: Magistrat der Stadt Witzenhausen – Nutzung nur für nicht kommerzielle Zwecke“; die Datei der Ebene trägt denselben Hinweis. Es gibt keinen Download in der Oberfläche und keine Flächen im Datenpaket.
  - Punkte im Geltungsbereich, Plantitel und Überschneidungen von Planflächen mit Umweltebenen nutzt nur die Seite. Im Repository und im Datenpaket bleibt nur die Zuordnung Vorgang → Plannummer (`audit/verortung_bauleitplanung.tsv`, ohne Plantitel).
- **Umweltebenen (Hochwasser, Wasserschutz, Schutzgebiete):**
  - Zuschaltbare Kartenebenen aus den INSPIRE-Diensten des Landes (HLNUG, CC BY 4.0; HMLU, frei nutzbar ohne Weiterveräußerung), zugeschnitten auf das Stadtgebiet. Sie sind nicht rechtsverbindlich.
  - Eine „räumliche Überschneidung“ wird nur für Flurstückspunkte und Geltungsbereiche von Plänen (mindestens 1 % der Fläche) angegeben, nicht für Straßen oder Ortsteile. Sie sagt nichts über den Inhalt eines Vorgangs aus (`audit/ueberschneidung_umwelt.tsv`).
  - Der Naturpark umfasst das ganze Stadtgebiet und wird daher nicht als Überschneidung ausgewiesen.
- **Wohnen und Boden:**
  - Es gibt keinen Mietspiegel für Witzenhausen, also keine ortsübliche Vergleichsmiete. Angebotsmieten privater Portale werden nicht übernommen. Die drei Begriffe stehen getrennt im Glossar und nie in einer Zahl.
  - Mietwerte stammen nur aus dem Zensus 2022 (Bestandsmiete, Stichtag 15.05.2022).
  - Bodenrichtwerte stehen immer mit ihrem Stichtag. Zonen und Spannen beruhen auf dem Stichtag 01.01.2024 (Datendienst); für den Verlauf kommen die Spannen zum 01.01.2022 hinzu (`bodenrichtwerte_2022.geojson`). Zonengrenzen können sich zwischen Stichtagen ändern, verglichen werden nur Spannen je Gemarkung. Den Stichtag 01.01.2026 gibt es nur als Kartendienst der HVBG; er erscheint als eigene Bildebene ohne Spannen und wird nicht mit 2024 vermischt.
  - Werte je Ortsbezirk aus Gitterzellen sind Näherungen. Die Zellen werden über ihren Mittelpunkt einer Gemarkung zugeordnet; geheim gehaltene Zellen zählen nicht als null; unter 5 Zellen mit Wert wird nichts ausgewiesen. Die Leerstandsquote steht nur für die Gemeinde.
  - Rechtlicher Kontext (Mietenstufe, Mieterschutzverordnung, KdU) ist datierter Text mit Quelle, kein Datensatz. KdU-Beträge werden nicht genannt, weil kein aktueller Stand belegt ist.
- **Wahlen und Gremien:**
  - Nur amtliche Ergebnisse: 2026 aus den Bekanntmachungen Nr. 043 und 044/2026; 2016 und 2021 aus der Ergebnispräsentation der Gemeindewahlleitung (Stufe „Schnellmeldung“; 2016 mit 31 Sitzen, seit 2020 37); Bundestags- und Europawahlen aus der Wahlbezirksstatistik der Bundeswahlleiterin.
  - Keine Personennamen. Die Sitzverteilung folgt dem Wahlergebnis; Fraktionswechsel und Koalitionen sind nicht abgebildet.
- **Beteiligung der Öffentlichkeit:** Stufen und Fristen der Bauleitplanung stammen aus den amtlichen Bekanntmachungen (ab 2024 als PDF, ab 10/2025 als eigener Inhaltstyp). Verknüpft wird über Plannummer, Änderung und Gemarkung; Ansprechpersonen und E-Mail-Adressen werden nicht übernommen.
- **Gebäude und Eigentum:** Gezeigt werden nur die Gebäudefunktion „öffentliche Zwecke“ (ALKIS, Nutzung statt Eigentum) und die Unternehmen des Beteiligungsberichts. Kommunale Liegenschaften sind nicht online veröffentlicht; Privateigentum wird nicht dargestellt.
- **Weitere Kartenebenen:** Windvorranggebiete (Regionalplan Nordhessen) und Kulturdenkmäler (DenkXweb, nicht flächendeckend erfasst) nur als Kartenebene; Bodendenkmäler nicht.
- **Gebäude 2D/3D** (`wohnen.html`, Seite „Wohnen und Eigentum“): alle 21 924 Gebäude der Stadt als Grundriss aus ALKIS vereinfacht, mit gemessener Höhe aus den 3D-Gebäudemodellen LoD2 und den Bauwerken der HVBG, ohne Dachformen und Geländehöhe. Schlüssel ist die ALKIS-OID; LoD2 trägt dieselbe Kennung ohne den Zusatz „BL“. Ohne passendes Modell gilt eine Standardhöhe von 4 m, schraffiert als „Höhe geschätzt“; die Zuordnung steht im Audit `lod2_alkis_zuordnung.tsv`. Ausgeliefert als Vektorkacheln in einer Datei (`gebaeude.pmtiles`), die der Browser über HTTP-Range-Abfragen lädt. `3d.html` leitet dorthin weiter.
- **Zuzug und Wegzug:**
  - Amtliche Zahlen des Hessischen Statistischen Landesamts: je Gemeinde nur Zu- und Fortzüge über die Gemeindegrenze (2015–2024); Herkunft und Ziel nur für den Werra-Meißner-Kreis insgesamt und nur über die Kreisgrenze (2024).
  - Zahlen je Ortsteil und Ströme zwischen einzelnen Gemeinden sind nicht veröffentlicht und werden nicht geschätzt. Umzüge innerhalb der Stadt fehlen.
  - Witzenhausen ist Hochschulstandort; Zu- und Fortzüge von Studierenden erhöhen beide Ströme. Raten je 1 000 Einwohner beziehen sich auf den Mittelwert aus Jahresanfang und -ende; bis 2023 Bevölkerung auf Basis Zensus 2011, ab 2024 Zensus 2022.
- **Einreicher:** Antrag oder Anfrage einer Fraktion wird aus dem TOP-Titel erkannt und als Angabe und Filter gezeigt, ohne Zählung je Fraktion. Eine fehlende Nennung im Titel sagt nichts über die Aktivität einer Fraktion.
- **Quellen:**
  - Das Quellenregister mit Prüfstatus steht in [`data/quellen_register.tsv`](data/quellen_register.tsv), lesbar in [`DATA_SOURCES.md`](DATA_SOURCES.md), erzeugt mit `python tools/datenquellen.py`.
  - Die Namensnennungen auf der Seite kommen aus [`data/attribution.tsv`](data/attribution.tsv), nur für die tatsächlich genutzten Quellen.

## Wohnen und Eigentum: Zweck, Methode, Datenschutz, Grenzen

**Zweck.** Für die Stadt gibt es keinen Mietspiegel. Die Seite `wohnen.html` schafft eine Vergleichsgrundlage für tatsächlich gezahlte Mieten. Dafür braucht es Mietangaben von Mietenden und das Wissen, wer welche Gebäude vermietet: So lassen sich Mietende über das Gebäude ansprechen und Mieten je Vermieter vergleichen.

**Methode.**
- Öffentliche Grundlage (Pipeline): alle Gebäude aus ALKIS mit Höhe aus LoD2 (2D und 3D), Zensus 2022 (Gemeinde; Ortsbezirke als Näherung aus dem Gitter), Bodenrichtwerte 2022 und 2024, rechtlicher Rahmen als datierte Textbausteine.
- Zwei getrennte Erfassungen in `erfassen.html` (nicht öffentlich verlinkt, Zugang über Einladungscode): Eigentum und Vermietung durch das Team; Mietangaben freiwillig mit Einwilligung. Getrennt wegen unterschiedlicher Betroffener und Rechtsgrundlagen.
- Prüfung lokal bei der Prüfgruppe (`tools/pruefen.py`): entschlüsseln, gegen die Schemata prüfen, Dubletten, Vermieter-Schlüssel (`V-017` statt Namen; juristische Personen `JP:<Name>`), Freigabe nach dem Vier-Augen-Prinzip. Veröffentlichung (`tools/veroeffentlichen.py`) nur zusammengefasst nach `docs/uebergabe-v0.4.2/veroeffentlichungsregeln.tsv`.

**Datenschutz.**
- Kein Server, keine Datenbank. Jeder Eintrag wird im Gerät mit dem öffentlichen Schlüssel der Prüfgruppe versiegelt (libsodium sealed box); kein automatischer Upload, nur verschlüsselte Exportdateien.
- Namen von Privatpersonen nur verschlüsselt, nie veröffentlicht; jede Entschlüsselung protokolliert.
- Keine Rohdaten in ein Git-Repository: `.gitignore`, Pre-Commit-Hook und CI-Prüfung (`tools/sperre.py`) lehnen Exportdateien und Felder einzelner Erfassungen ab. Hook einrichten: `git config core.hooksPath .githooks`.
- Sensible Felder bleiben per Konfiguration aus (`privat_namen_aktiv`, `mietangaben_aktiv`), bis verantwortliche Stelle, Einwilligungstext, Informationspflicht, Interessenabwägung, Verarbeitungsverzeichnis und Löschverfahren geklärt sind (Issue 28). Ohne öffentlichen Schlüssel (Issue 29) speichert die App nichts.

**Grenzen.**
- Kein Mietspiegel: Die Angaben ersetzen keine ortsübliche Vergleichsmiete nach § 558 BGB.
- Mietangaben sind freiwillig und nicht repräsentativ.
- Zensus-Werte haben den Stichtag 15.05.2022.
- Die Eigentumskarte ist unvollständig: Sie zeigt nur, was belegt erfasst und geprüft wurde; der Erfassungsstand steht je Ortsbezirk dabei.

Entwürfe zur Datenschutz-Klärung (Interessenabwägung und DSFA-Vorprüfung, Verarbeitungsverzeichnis, Löschverfahren, Information für Vermieter:innen, Prüfgruppe und Schlüsselverfahren; keine Rechtsberatung): [`docs/datenschutz/`](docs/datenschutz/).

Prüfschritte auf Geräten (Android, iOS, Screenreader): [`docs/pruefung-wohnen.md`](docs/pruefung-wohnen.md).

## Aktualisierung

Der Workflow `.github/workflows/pages.yml` läuft täglich um 04:17 UTC und bei jedem Push. Er führt `python -m pipeline all` aus (Schritte: `python -m pipeline` ohne Angabe):

1. Abruf und Ableitung je Quelle: Einladungen, Bauleitplanung, Gemarkungen, Lagebezeichnungen, Gebäude und Gesellschaften, Umwelt, Wohnen, Wahlen, Beteiligung, Wanderung, 3D-Gebäude. Scheitert ein Abruf oder liefert er einen Fehlerbericht, bleibt der letzte Stand;
2. Aufbau der Vorgänge;
3. Prüfung (Rückführbarkeit, Datenschutz, Lizenzgrenzen);
4. Datenpaket;
5. Seite.

Nur vom Hauptzweig veröffentlicht er die Seite auf GitHub Pages; auf anderen Zweigen ist der Lauf eine Probe. Die Rohdaten liegen nur im Zwischenspeicher des Workflows. Voraussetzung: In den Repository-Einstellungen unter „Pages“ ist als Quelle „GitHub Actions“ gewählt.

Pull Requests und den Hauptzweig prüft `.github/workflows/tests.yml` mit Python-Tests, Kontrastprüfung und Browser-Tests mit axe-core.

## Aufbau

```
config/stadt.json   Alle stadtspezifischen Werte (Name, Gremien, Ortsbezirke, Karte, Farben, Texte)
site/               Seite (Leaflet, Zeitleiste, Liste, Prozesslinie; Tour in tour.js; Wohnen und Eigentum mit MapLibre GL und PMTiles), ohne Build-Schritt
pipeline/           Python-Pipeline, je Quelle Abruf und Ableitung, dann build, check, package, site (python -m pipeline all)
tools/kontrast.py   WCAG-Kontrastprüfung der Farb-Tokens aus config/stadt.json
tools/einladung.py, pruefen.py, veroeffentlichen.py   Erfassung Wohnen und Eigentum: Einladungscodes, Prüfung und Veröffentlichung (nur lokal)
tools/sperre.py     Sperre gegen personenbezogene Rohdaten (Pre-Commit-Hook .githooks/pre-commit, CI)
tests/              Python-Tests, Browser-Tests (Playwright, axe-core), Testdaten
phase0/             Bestandsaufnahme: Bericht, Stichprobe (TSV), Explorationsskripte
docs/               Projektprompts (v0.1, Übergabe v0.2 mit Material), Recherche zu Datenquellen
data/quellen_register.tsv   Quellenregister mit Prüfstatus
mietmonitor/        Früherer Inhalt des Repositorys (Mietdaten-Erfassung), unverändert lauffähig
```

## Prüfen

```
python3 -m unittest discover -s tests -t .     # Konfiguration, Kontrast, Zusammenstellen
python3 tools/kontrast.py                       # Kontraste der Farbwerte (nur heller Modus)
python3 tools/kontrast_karte.py                 # Nicht-Text-Kontrast der Kartengrafik (Pillow nötig)
npm install --prefix tests/browser && (cd tests/browser && npx playwright install chromium)
bash tests/browser/run.sh                       # Browser und Barrierefreiheit (oder CHROMIUM=<Pfad> für ein vorhandenes Chromium)
```

## Gestaltung

Die Grundfarbe ist `#f4726b`. Auf ihr steht nur dunkler Text (6,2:1). Für Text und Links dient die Ableitung `#b8352e` (5,9:1 auf Weiß), im Dunkelmodus `#f8a29d`.

Schriften: Lilita One für Überschriften (ohne künstliches Fetten), Space Mono für den Text, beide selbst gehostet mit OFL-Lizenz (`site/fonts/`).

## Herkunft und Lizenz

Code unter MIT ([`LICENSE`](LICENSE)). Seite, Zeitleiste und Pipeline-Grundmodule stammen aus der [RIS-Karte Bonn](https://github.com/daimpad/allris-test) von Damian Paderta (MIT). Es handelt sich um eine unabhängige Kopie ohne gemeinsame Codebasis.

Weitere Lizenzen:

- Leaflet: BSD-2
- Leaflet.markercluster: MIT
- MapLibre GL JS 4.7.1 (CSP-Fassung, `site/vendor/maplibre/`): BSD-3
- PMTiles 4.4.1 (`site/vendor/pmtiles/`): BSD-3
- libsodium.js 0.8.4 (`site/vendor/libsodium/`, Verschlüsselung in der Erfassung): ISC
- Schriften: SIL OFL 1.1
