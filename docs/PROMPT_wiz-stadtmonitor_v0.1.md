# Prompt: „wiz-stadtmonitor“ – Sitzungsinformationen der Stadt Witzenhausen räumlich, zeitlich und nach Gremien erschließen

> Entwurf v0.1 (23.10.2026) · Zur Ausführung in Claude Code · Ausgangsbasis: RIS-Karte Bonn (`github.com/daimpad/allris-test`, MIT)

---

## 1. Rolle

Du arbeitest als Webentwickler:in mit Erfahrung in Open-Data-Pipelines, PDF-Extraktion und Geodaten **und** als Beauftragte:r für Bürgerbeteiligung. Du arbeitest quellentreu: Du erfindest keine Inhalte, und jede angezeigte Information ist auf ein Quelldokument rückführbar. Vor jeder Phase (Abschnitt 8) legst du einen kurzen Plan vor und wartest auf Freigabe.

## 2. Festgelegte Rahmenentscheidungen

| Punkt | Entscheidung |
|---|---|
| Repository | `wiz-stadtmonitor` (existiert bereits; Inhalt vor jeder Änderung prüfen, nichts überschreiben ohne Rückfrage) |
| Verhältnis zu `allris-test` | Unabhängige Kopie als Ausgangsbasis; kein Fork, keine gemeinsame Codebasis. Herkunft und MIT-Lizenz des übernommenen Codes in README und LICENSE nennen |
| Code-Lizenz | MIT; Datendateien mit eigener LICENSE-Datei |
| Datenquelle | Amtliche Bekanntmachungen (PDF) auf `witzenhausen.eu` |
| Räumlicher Umfang | Ganze Stadt: Kernstadt und alle 16 Ortsbezirke |
| Prozesslinie | Nur Beratungsstationen; fehlende Beschlussergebnisse sichtbar als Lücke kennzeichnen |
| Sprachmodelle | Zulässig für Ortsextraktion, mit Kennzeichnung, Konfidenz und Link zum Original |
| Auslieferung | Ergebnisse als Zip-Paket; Audit-Protokolle als TSV |

## 3. Übernahme aus `allris-test`

1. **Bestandsaufnahme:** Verzeichnisstruktur, Pipeline-Skripte, Frontend-Komponenten, Visualisierungen (Karte, Liste, Filter, Prozesslinie, Detailansicht), Build- und Deploy-Workflows. Halte für jedes Teil fest, ob es *unverändert* übernommen, *angepasst* oder *ersetzt* wird.
2. **Übernehmen:** Frontend-Architektur, Kartendarstellung, Listenansicht, Filterlogik, Prozesslinien-Komponente, Transparenzkennzeichnung (Methode, Konfidenz, Fundstelle), Audit-TSV-Muster, Barrierefreiheitsmaßnahmen.
3. **Ersetzen:**
   - der OParl-Abruf durch einen PDF-Adapter (Abschnitt 4),
   - Bonner Geodaten, Gremientypen, Glossar und Beteiligungshinweise,
   - sämtliche Bonner Daten (nicht in das neue Repository kopieren).
4. **Entkoppeln:** Stadtspezifische Werte (Name, Farben, Schriften, Gremien und Abkürzungen, Ortsteile, Kartenausschnitt, Glossar) gehören in eine Konfigurationsdatei. Sie stehen nicht im Code.

## 4. Datenquellen (recherchiert, Stand 23.10.2026)

### 4.1 Primärquelle: Amtliche Bekanntmachungen der Stadt Witzenhausen
- Auflistung über die WordPress-REST-API: `https://www.witzenhausen.eu/wp-json/wp/v2/media?mime_type=application/pdf&per_page=100&page=N` (Felder `date`, `source_url`, `title`; Gesamtzahl im Header `X-WP-Total`). Insgesamt 952 PDF-Medien; davon ca. 240 Einladungen (`search=Einladung`), Zeitraum 07/2024 bis heute.
- Dateinamenmuster: `<lfd.Nr>-<Jahr>-Einladung-<Gremium>-<TT>-<MM>-<JJJJ>.pdf`, z. B. `154-2026-Einladung-OB-Hundelshausen-28-09-2026.pdf`.
- Gremienkürzel (beobachtet, Varianten normalisieren):
  - `STVV` – Stadtverordnetenversammlung
  - `HFR` / `HFR-Ausschuss` – Haupt-, Finanz-, Rechts-, Digitalisierungs- und Wirtschaftsausschuss
  - `BV` / `BV-Ausschuss` – Bau-, Verkehr-, Umwelt- und Energieausschuss (**nicht** Bezirksvertretung)
  - `Soz` / `SozA` / `Soz-Ausschuss` – Sozial-, Familien-, Jugend-, Senioren- und Sportausschuss
  - `STE` – Ausschuss für Stadtentwicklung, Tourismus und Kultur
  - `AB` – Ausländerbeirat
  - `Jugendrat`, `Seniorenrat`
  - `OB-<Ortsteil>` – Ortsbeirat
  - Zusätze wie `-Konstituierung` und `nicht-oeffentlich-` erkennen
  - Fremdobjekte (z. B. Jagdgenossenschaft) ausschließen
- Inhalt:
  - Die PDFs haben eine Textebene (`pdftotext -layout` ausreichend).
  - Kopf: Bekanntmachungsnummer, Gremium, Datum, Uhrzeit, Sitzungsort.
  - Tagesordnung: TOP-Nummer, Titel, bei STVV und Ausschüssen meist mit Vorlagennummer `STV/<Nr>/<Jahr>`; in Ortsbeiratseinladungen fehlen Vorlagennummern oft.
- Lücken: Vorlagentexte, Niederschriften und Beschlussergebnisse sind dort nicht oder nur vereinzelt veröffentlicht; Zeitraum vor 07/2024 fehlt.
- Abruf zurückhaltend: Rate-Limit, Cache, eindeutiger User-Agent mit Kontaktadresse.

### 4.2 SessionNet (Somacos, gehostet bei OWL-IT)
- `https://sessionnet.owl-it.de/witzenhausen/bi/`
- Kein OParl-Endpunkt gefunden; `robots.txt` des Hosts untersagt Crawling. **Nicht automatisiert abrufen.** Nur als Linkziel für Bürger:innen verwenden (Startseite bzw. Recherche), solange keine Zustimmung der Stadt vorliegt.

### 4.3 Geodaten (vor Nutzung prüfen)
- Ortsteil- bzw. Gemarkungsgrenzen aus den hessischen Geobasisdaten (Lizenz und Bezugsweg prüfen).
- Alternativ: OSM-Grenzen (`admin_level` für Ortsteile) unter ODbL.
- Straßen und Ortsteilzuordnung über Photon/Nominatim (ODbL, Lizenzhinweis).
- Sitzungsorte (Bürgerhäuser, Dorfgemeinschaftshäuser, Rathaus) als eigene, manuell geprüfte Liste mit Koordinaten.

## 5. Ziel

Eine öffentliche, statisch auslieferbare Webanwendung, die die Sitzungsinformationen der Stadt Witzenhausen in drei Dimensionen erschließt, jeweils mit Quellenangabe:

1. **Räumlich (Wo?)** – Karte und Liste der Tagesordnungspunkte mit Ortsbezug; Filter nach Ortsteil.
2. **Zeitlich (Wann? Wo steht das Verfahren?)** – Sitzungskalender und, wo eine Vorlagennummer vorhanden ist, eine Prozesslinie über alle Tagesordnungen, in denen sie erscheint.
3. **Akteursbezogen (Wer?)** – Gremien (StVV, Ausschüsse, Ortsbeiräte, Beiräte); Magistrat und Fraktionen nur, soweit im Titel genannt (als abgeleitet kennzeichnen).

## 6. Funktionale Anforderungen

### 6.1 Datenmodell
Bekanntmachung (PDF, Nr., Datum) → Sitzung (Gremium, Datum, Ort, öffentlich/nichtöffentlich) → Tagesordnungspunkt (Nr., Titel, Vorlagennummer optional) → Vorlage (über Vorlagennummer zusammengeführt) → Ort (Stufe, Konfidenz, Fundstelle).

### 6.2 Verortung in drei Stufen
| Stufe | Methode | Konfidenz |
|---|---|---|
| A | Gremium ist Ortsbeirat X → Ortsteil X (Ortsbezug des Gremiums, nicht zwingend des Gegenstands) | hoch für den Ortsteil |
| B | Regelbasiert: Ortsteilnamen, Straßennamen, Bebauungsplan- und Gemarkungsangaben in TOP-Titeln; Abgleich gegen Straßenliste mit Ortsteilzuordnung | mittel |
| C | LLM-gestützte Extraktion aus dem TOP-Titel mit strukturiertem Output und Verifikation gegen Stufe B | niedrig bis mittel, stets gekennzeichnet |

- Standard-TOPs ohne Ortsbezug (Eröffnung, Niederschrift, Verschiedenes, „Die Gäste haben das Wort“) als Verfahrens-TOPs klassifizieren und aus der Karte ausschließen.
- Jede Verortung trägt `method`, `confidence`, `evidence` (Zitat/Fundstelle), `source_pdf`.
- Audit-TSV: Bekanntmachungsnr., Gremium, Datum, TOP, Titel, Stufe, Treffer, Konfidenz, Fundstelle, Prüfstatus.
- Datenschutz: keine Verortung von Wohnadressen natürlicher Personen; Namen von Privatpersonen in TOP-Titeln nicht in Karte oder Suche hervorheben.

### 6.3 Prozesslinie
- Stationen = Sitzungen, in deren Tagesordnung dieselbe Vorlagennummer erscheint, chronologisch.
- Ergebnisfeld je Station: „Ergebnis nicht veröffentlicht“ mit Erläuterung und Link zum SessionNet. Keine Ergebnisse ableiten oder vermuten.
- TOPs ohne Vorlagennummer: einzelne Station, keine Verknüpfung über Titelähnlichkeit ohne Kennzeichnung.

### 6.4 Glossar und Beteiligung (HGO statt GO NRW)
- Begriffe neu fassen: Stadtverordnetenversammlung, Magistrat, Ortsbeirat, Ausschuss, Ausländerbeirat, Jugend- und Seniorenrat, Bekanntmachung, Vorlage.
- Beteiligungshinweise (Fragestunde, Öffentlichkeit von Sitzungen, Ortsbeiratssitzungen) aus der HGO und der Geschäftsordnung der Stadt belegen; keine Übernahme der Bonner Texte.

## 7. Gestaltung

- **Grundfarbe** `#f4726b`.
  - Kontrast weiß auf `#f4726b` = 2,81:1 → für Text unzulässig (WCAG 2.1 AA).
  - Dunkler Text auf `#f4726b` = 7,47:1 → zulässig.
  - Für Text und Links auf Weiß eine abgedunkelte Ableitung verwenden (rechnerisch z. B. `#e91c11` mit 4,53:1; ggf. weniger gesättigte Variante bestimmen und messen).
  - Alle Farbpaare als Tokens definieren und prüfen, auch im Dunkelmodus und bei Kartensymbolen.
  - Die bisherige Lila-Palette vollständig ersetzen.
- **Schriften:**
  - Lilita One für Überschriften. Es gibt nur einen Schnitt (Regular 400); `font-synthesis: none`, kein künstliches Fetten.
  - Space Mono (400/700) für alles andere. Wegen der Monospace-Laufweite auf Lesbarkeit achten: Grundgröße ≥ 16 px, Zeilenhöhe ≥ 1,5, Zeilenlänge begrenzen, ausreichender Absatzabstand.
  - Fonts selbst hosten (OFL-Lizenzdateien beilegen) und Fallback-Stacks angeben.
- WCAG 2.1 AA; mobil nutzbar; Listenansicht gleichwertig zur Karte.

## 8. Vorgehen (nach jeder Phase Rückfrage)

0. **Bestandsaufnahme und Exploration:**
   - `allris-test` und das bestehende `wiz-stadtmonitor` inventarisieren (Abschnitt 3).
   - Alle Einladungs-PDFs auflisten; Stichprobe von 20 PDFs parsen.
   - Bericht: Anzahl Sitzungen je Gremium, TOPs, Anteil mit Vorlagennummer, Anteil verortbar nach Stufe A/B, Parserfehler.
1. **Übernahme und Entkopplung:** Code kopieren, Bonn-spezifisches entfernen, Konfigurationsdatei einführen, Gestaltung umstellen.
2. **Datenpipeline:** PDF-Abruf mit Cache, Parser, Normalisierung der Gremien, Zusammenführung über Vorlagennummer, Ablage als JSON/GeoJSON.
3. **Verortung** nach 6.2 mit Audit-TSV; manuelle Prüfung einer Stichprobe (z. B. 50 TOPs, alle Ortsbezirke vertreten).
4. **Frontend:** Karte, Liste, Filter (Ortsteil, Gremium, Zeitraum, Stichwort, Konfidenz), Sitzungskalender, Prozesslinie mit Lückenkennzeichnung.
5. **Repository:**
   - README mit Ziel, Quellen, Lizenzen, Grenzen und Datenstand; Hinweis auf fehlende Ergebnisse und den Zeitraum ab 07/2024.
   - LICENSE und CONTRIBUTING.
   - GitHub Actions für Aktualisierung und Deployment.
6. **Verifikation:** Stichprobe gegen die Original-PDFs; Kontrastprüfung; Lizenzhinweise vollständig; Audit-TSV im Zip-Paket.

## 9. Offene Punkte

- Weiterverwendung der Bekanntmachungen: vermutlich amtliche Werke nach § 5 Abs. 1 UrhG; mit der Stadt bestätigen, ebenso die Zustimmung zum regelmäßigen Abruf.
- Anfrage an die Stadt: OParl-Freischaltung im SessionNet bzw. Veröffentlichung von Niederschriften und Beschlüssen (würde Prozesslinie und Ergebnisse vervollständigen).
- Quelle und Lizenz der Ortsteilgrenzen; Straßenliste mit Ortsteilzuordnung.
- Hosting und Domain; Aktualisierungsrhythmus (Bekanntmachungen erscheinen ca. 1–2 Wochen vor der Sitzung).
- GitHub-Account bzw. Organisation von `wiz-stadtmonitor` per `gh repo view` prüfen.
