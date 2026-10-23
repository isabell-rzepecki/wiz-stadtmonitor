# Übergabe v0.2: „wiz-stadtmonitor“ – Ergänzung um offene Geodaten und das Modul „Wohnen und Boden“

> Stand 23.10.2026 · Ergänzt den bereits übergebenen Prompt v0.1. Er ersetzt ihn nicht.
> Das beiliegende Material liegt im Ordner `material/`. Bitte zu Beginn nach `docs/uebergabe-v0.2/` im Repository kopieren.

---

## 0. Ausgangslage und erste Schritte

Der Prompt v0.1 ist bereits in Ausführung. Bevor du etwas änderst:

1. Berichte kurz den aktuellen Stand im Repository `wiz-stadtmonitor`:
   - welche Phasen aus v0.1 abgeschlossen sind,
   - welche Datenstrukturen es gibt, insbesondere zu Ortsbezügen und zur Konfigurationsdatei,
   - welche Geometrien bisher verwendet werden.
2. Lege dann einen Plan für die Arbeitspakete A bis F vor und warte auf Freigabe.
3. Nach jedem Arbeitspaket stellst du eine Rückfrage, wie in v0.1.

Es gelten weiter alle Rahmenentscheidungen aus v0.1:
- Quellentreue,
- Kennzeichnung abgeleiteter Daten,
- Audit-TSV,
- WCAG 2.1 AA,
- Farbe `#f4726b` mit abgedunkelter Textvariante,
- Lilita One für Überschriften, Space Mono für alles andere,
- kein Abruf aus dem SessionNet.

## 1. Material

| Datei | Inhalt | Status |
|---|---|---|
| `quellen_register.tsv` | 25 Quellen: URL, Layer, Format, KBS, Ebene, Lizenz, Attributionspflicht, Testergebnis vom 23.10.2026, Status, Nutzung | Spalte `status` beachten: `verifiziert`, `teilweise`, `zu prüfen`, `zu verifizieren` |
| `gemarkungen_witzenhausen.geojson` | 17 Gemarkungen der Stadt (HVBG, dl-de/zero-2.0), EPSG:4326, leicht vereinfacht | aus Originaldaten erzeugt; im Build neu ableiten |
| `gemarkung_ortsbezirk.tsv` | Zuordnung Gemarkung → Ortsbezirk/Gremium, inkl. Kürzel aus Dateinamen | plausibel, gegen § 6 Hauptsatzung prüfen |
| `bodenrichtwerte_2024_spannen_gemarkung.tsv` | Spannen der Bodenrichtwerte (baureifes Wohn-/Mischbauland) je Gemarkung | abgeleitet, nur Plausibilitätsreferenz |
| `zensus2022_wohnen_nachbargemeinden.tsv` | Nettokaltmiete, vermietete und leerstehende Wohnungen; für Witzenhausen auch Eigentümer- und Leerstandsquote | Sekundärabruf, gegen Zensusdatenbank verifizieren |
| `abrufbeispiele.md` | Abrufbefehle, je Befehl als getestet oder nicht getestet markiert | – |
| `attribution.md` | Attributionstexte für Footer und Datendateien | – |

Das Register ist die verbindliche Quellenliste. Neue Quellen nimmst du nur nach Rückfrage auf und trägst sie dann im Register nach.

## 2. Grundsätze für die Datenintegration

- **Abruf beim Build, nicht im Browser.** Alle Quellen werden in einer Pipeline geladen, gecacht und als statische Dateien ausgeliefert. Die einzige Laufzeitquelle ist die Hintergrundkarte (basemap.de).
- **Nach Lizenz getrennt ablegen.**
  - Je Lizenz ein Unterordner, z. B. `data/geo/dl-de-zero/`, `data/geo/cc-by/`, `data/geo/odbl/`.
  - ODbL-Ableitungen nie mit anderen Daten in einer Datei mischen.
  - Daten mit Nutzungsbeschränkung (Bauleitplanung Witzenhausen) nicht ins Repository übernehmen, bis die Stadt die Nutzung schriftlich bestätigt hat.
- **Metadaten je Datei.** Jede erzeugte Datei trägt auf oberster Ebene `license`, `attribution`, `source` und `retrieved`. `DATA_SOURCES.md` führt das Register in lesbarer Form fort.
- **Audit des Abrufs.** Je Lauf eine `audit/abruf_<datum>.tsv` mit den Spalten Quelle-ID, URL, HTTP-Status, Bytes, SHA-256, Anzahl Features und Fehlermeldung.
- **Koordinaten.** Ausgabe in EPSG:4326 mit 6 Nachkommastellen. Die BBOX-Werte in UTM sind Näherungen; nach dem Abruf mit der Stadtgrenze clippen.
- **Datenschutz.** Keine Eigentümerangaben, keine Wohnadressen natürlicher Personen. Flurstücke werden nur als Ortsbezug genutzt, nicht als personenbezogene Information.

## 3. Arbeitspakete

### A. Raumbezug: Ortsbezirke aus Gemarkungen
- Die Stadt hat 17 Gemarkungen. Das entspricht den 16 Ortsbezirken plus der Kernstadt (Gemarkung „Witzenhausen“, ohne Ortsbeirat).
- Ersetze bisherige provisorische Ortsteilgeometrien durch eine im Build abgeleitete Gemarkungsdatei aus `vg_shp` (Filter `GMDE_NR='636016'`).
- Die Zuordnung Gemarkung → Ortsbezirk → Gremium steht in der Konfigurationsdatei. Grundlage ist `gemarkung_ortsbezirk.tsv`, mit `zuordnung_status` je Zeile.
- Prüfpunkte, offen markieren und nicht stillschweigend auflösen:
  - Zugehörigkeit von Bischhausen (Kernstadt?),
  - Zugehörigkeit von Hübenthal (Berlepsch-Ellerode?),
  - Wortlaut § 6 Hauptsatzung.

### B. Geokodierung erweitern (Stufe B aus v0.1)
1. **Straßenverzeichnis:** Aus `hako_lage` (Layer `lage`/`hako`) für die Gemeinde 636016 ein Verzeichnis `strasse → [ortsbezirke]` per Punkt-in-Gemarkung erzeugen. Straßen in mehreren Ortsbezirken als mehrdeutig markieren.
2. **Abgleich der TOP-Titel:** Straßennamen, Gemarkungs- und Ortsteilnamen, B-Plan-Nummern und Flurstücksangaben (`Gemarkung X, Flur Y, Flurstück Z` → `alkis`, nur kleinräumig).
3. **B-Plan-Umringe** (`bplan`) zum Abgleich von Plannummern und -namen nur im Build verwenden. In der Oberfläche vorerst auf das Plandokument verlinken statt die Geometrie auszuliefern, bis die Lizenz geklärt ist.
4. **Audit-TSV:** um die Spalten `methode_detail` (z. B. `B-strasse`, `B-gemarkung`, `B-bplan`, `B-flurstueck`) und `mehrdeutig` erweitern.

### C. Kontextlayer Umwelt (optional, nach Freigabe)
- Überschwemmungsgebiete HQ100 und HWRM-Flächen (`uesg`), Trinkwasserschutzgebiete (`tws`), Schutzgebiete (`schutzgeb`).
- Als zuschaltbare Ebenen mit Legende und Hinweis „nicht rechtsverbindlich“.
- Ein automatischer Bezug zu TOPs entsteht nur, wenn ein bereits verorteter TOP in einer solchen Fläche liegt. Das wird als „räumliche Überschneidung“ gekennzeichnet, nicht als inhaltlicher Zusammenhang.

### D. Modul „Wohnen und Boden“
**Ziel:** Je Ortsbezirk und für die Stadt ein Kontextpanel, das bei verorteten TOPs mit Bezug zu Bauen und Wohnen angezeigt wird. Außerdem eine Vergleichsansicht der Nachbargemeinden.

1. **Bodenrichtwerte**
   - Quelle: `boris`, Stichtag 01.01.2024, Featuretype `boris:BR_BodenrichtwertZonal`.
   - Zonen als Fläche mit Wert, Art und Entwicklungszustand darstellen, zusätzlich eine Spanne je Gemarkung.
   - Mit `bodenrichtwerte_2024_spannen_gemarkung.tsv` plausibilisieren.
   - Den aktuellen Stichtag 2026 ermitteln (Pfad `…/brw/2026/wfs` liefert 404). Bis dahin den Stichtag 2024 deutlich ausweisen.
2. **Zensus 2022**
   - Gemeindewerte für Witzenhausen und Nachbargemeinden in Hessen, Niedersachsen und Thüringen aus der Zensusdatenbank verifizieren.
   - Gitterzellen (100 m) mit Gemarkungen verschneiden: Nettokaltmiete, Leerstand, Eigentümerquote je Ortsbezirk.
   - Diese Werte als Näherung kennzeichnen, mit Hinweis auf Geheimhaltung und Zellzuordnung (Zellmittelpunkt in Gemarkung). Zellen mit unterdrückten Werten nicht als null behandeln.
3. **Begriffliche Trennung** in Oberfläche und Datenmodell:
   - Bestandsmiete (Zensus, Stichtag 15.05.2022),
   - Angebotsmiete (wird nicht übernommen, private Portale ohne offene Lizenz),
   - ortsübliche Vergleichsmiete (für Witzenhausen nicht verfügbar, kein Mietspiegel).
   Nie in einer Zahl oder Skala zusammenführen. Ein Glossar-Eintrag erklärt den Unterschied.
4. **Rechtlicher Kontext** als datierter Text, nicht als Datensatz:
   - Wohngeld-Mietenstufe (`wohngeld`, prüfen),
   - Status der hessischen Mietpreisbremse (`mietpreisbremse`; Rechtslage im Fluss, nur mit Datum und Quelle),
   - KdU-Angemessenheitsgrenzen nur mit Stand 2018 und dem Hinweis, dass der aktuelle Stand beim Kreis zu erfragen ist.
5. **Immobilienmarktberichte** (`immo_bericht`): Nur auflisten und verlinken. Eine tabellarische Übernahme erfolgt erst nach Rückfrage, weil die Nutzungsbedingungen zu prüfen sind.

### E. Hintergrundkarte
- basemap.de Web Vektor grau (`bm_web_gry.json`) als Standard; Attribution aus dem Style übernehmen.
- Prüfen, ob die Markerfarbe `#f4726b` und die Gemarkungsgrenzen auf dem grauen Hintergrund ausreichend kontrastieren (Nicht-Text-Kontrast ≥ 3:1).

### F. Register und Dokumentation
- `quellen_register.tsv` im Repository fortschreiben: Status je Quelle nach eigener Prüfung aktualisieren, Abrufdatum ergänzen.
- `DATA_SOURCES.md` und Footer aus `attribution.md` erzeugen.
- README-Abschnitt „Grenzen der Daten“ ergänzen:
  - kein Mietspiegel,
  - Zensus-Stichtag 2022,
  - Bodenrichtwert-Stichtag,
  - Lizenzvorbehalt Bauleitplanung,
  - Näherungscharakter der Ortsbezirkswerte.

## 4. Nicht tun
- Kein Abruf aus dem SessionNet.
- Keine OSM-Standardkacheln für den Massenabruf.
- Keine Angebotsmieten privater Portale übernehmen.
- Keine Werte schätzen oder interpolieren, ohne sie als abgeleitet zu kennzeichnen.
- Keine Bauleitplanungsgeometrien ins Repository übernehmen, solange die Bestätigung der Stadt fehlt.

## 5. Offene Punkte (in Issues überführen)
- § 6 Hauptsatzung: Ortsbezirke = Gemarkungen? Bischhausen, Hübenthal?
- Schriftliche Bestätigung der Stadt zur Nutzung der B-Plan- und FNP-Umringe sowie der Bekanntmachungen.
- BORIS-Stichtag 2026: Dienst-URL.
- Zensus-Gemeindewerte gegen die Primärquelle prüfen; Dateinamen der Gitterdownloads ermitteln.
- Wohngeld-Mietenstufe gegen die Anlage der WoGV prüfen.
- Aktuelle KdU-Angemessenheitsgrenzen beim Werra-Meißner-Kreis anfragen.
- Zugehörigkeit Witzenhausens zur neuen hessischen Mieterschutzverordnung prüfen.
- Lizenz der Schutzgebiete (Natureg) im Metadatensatz prüfen.
