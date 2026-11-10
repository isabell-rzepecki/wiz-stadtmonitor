# Strukturdaten Witzenhausen – Bericht Phase 0

> Stand 10.11.2026 · Prompt `wiz-stadtmonitor_strukturdaten` v0.1 · Erkundung ohne Produktionscode · Quellen: `audit_quellen.tsv`

## 1. Ergebnis in Kürze

- **Zensus-Gitterdaten:** nutzbar unter dl-de/by-2-0. Die Geheimhaltung erfolgt durch die Cell-Key-Methode, die Unschärfe in kleinen Ortsbezirken ist erheblich. Einwohnerzahlen lassen sich übertragen. Altersanteile brauchen eine zusätzliche Schwelle.
- **Wegweiser Kommune:** erreichbar, CC0, Daten bis 2023. Witzenhausen gehört zu Demografietyp 2. Unten stehen vier Vergleichskommunen und zwölf Indikatoren zur Bestätigung.
- **Raumeinheiten:** Die 17 Gemarkungen (Kernstadt mit Bischhausen und 16 Ortsbezirke) liegen bereits mit geklärter Lizenz im Repository.
- **Lücken:** Sozial- und Arbeitsmarktdaten (SGB II, Arbeitslosigkeit, Kinderarmut, Wanderung) gibt es nur für die Gemeinde. Kleinräumig gibt es nur den Stichtag 15.05.2022, also keine Zeitreihe.

## 2. Stand im Repository

| Punkt | Befund |
|---|---|
| Raumebene der Vorgänge | Verortung als Punkt (Straße, Flurstück, Plan) oder als Ortsteilfläche (`pipeline/verortung.py`). Die Flächen sind die 17 Gemarkungen aus `data/geo/dl-de-zero/ortsbezirke.geojson`. |
| Herkunft der Flächen | Digitale Verwaltungsgrenzen Hessen (HVBG), dl-de/zero-2.0. Abgleich mit dem früheren GeoJSON: mindestens 99,9 % Flächenübereinstimmung. Bischhausen liegt in der Gemarkung Witzenhausen (Kernstadt), Hübenthal in Berlepsch-Ellerode (LAGIS). |
| Zensus bereits eingebunden | Nettokaltmiete je Ortsbezirk als gewichtetes Mittel (Gewicht: Wohnungen; vertragskonform). Eigentümerquote je Ortsbezirk als **Median der Zellwerte**; das ist nach Datenvertrag keine zulässige Aggregation und wird in Phase 1 auf Zähler und Nenner umgestellt, sofern die Tabelle sie enthält (ungeprüft). |
| Weitere Kontextdaten | Wanderung, Wahlen, Bodenrichtwerte, Angebotsmieten (Kreis). Diese liegen auf Gemeinde- oder Gemarkungsebene vor und haben eigene Formate außerhalb des Datenvertrags. |
| Betrieb | Der Prompt nennt GitHub Pages. Seit 09.11.2026 läuft die Seite auf `stadtmonitor-witzenhausen.de` (Plesk); GitHub Pages leitet nur weiter. Für den Datenvertrag ändert das nichts. |

## 3. Zensus 2022 im 100-m-Gitter

**Lizenz und Geheimhaltung** (aus den Datensatzbeschreibungen):
- Lizenz dl-de/by-2-0, Namensnennung „© Statistische Ämter des Bundes und der Länder“ mit Jahr.
- Geheimhaltung nach § 16 BStatG durch stochastische Überlagerung nach der Cell-Key-Methode. „–“ bedeutet „genau Null oder auf Null geändert“.
- Zellen ohne Personen oder Wohnungen fehlen in den Dateien.
- Summen weichen ab, und die Teilgruppen ergeben nicht die Gesamtzahl.

**Abweichungen von der Beschreibung:**
- Die Werte-Spalte heißt `Einwohner`, nicht `Bevoelkerungszahl`.
- Die Kennungsspalte heißt in der Alterstabelle `GITTER_ID_100M`.
- Der Adapter muss beide Schreibweisen lesen.

**Probe** mit zwei Tabellen (Zellmittelpunkt im Polygon, 812 Zellen):
- Summe der Zellen: 15.202 Einwohner, Gemeinde laut Regionaltabelle 15.162 (+0,26 %).
- 14 Zellen schneiden eine Grenze zwischen Ortsbezirken.
- Eine Zelle hat ihren Mittelpunkt außerhalb, aber Fläche im Stadtgebiet.

| Ortsbezirk | Zellen | Einwohner (Zellsumme) | Summe der Altersgruppen | Abweichung |
|---|---:|---:|---:|---:|
| Kernstadt | 276 | 7.022 | 6.786 | −3,4 % |
| Hundelshausen | 49 | 1.036 | 1.046 | +1,0 % |
| Ermschwerd | 55 | 966 | 878 | −9,1 % |
| Gertenbach | 60 | 922 | 893 | −3,1 % |
| Unterrieden | 45 | 807 | 760 | −5,8 % |
| Kleinalmerode | 54 | 730 | 663 | −9,2 % |
| Wendershausen | 34 | 671 | 636 | −5,2 % |
| Roßbach | 40 | 599 | 551 | −8,0 % |
| Ziegenhagen | 53 | 584 | 516 | −11,6 % |
| Dohrenbach | 37 | 542 | 464 | −14,4 % |
| Werleshausen | 29 | 388 | 343 | −11,6 % |
| Ellingerode | 19 | 294 | 237 | −19,4 % |
| Blickershausen | 18 | 226 | 202 | −10,6 % |
| Hubenrode | 16 | 181 | 172 | −5,0 % |
| Berlepsch-Ellerode | 10 | 112 | 79 | −29,5 % |
| Neuseesen | 9 | 69 | 64 | −7,2 % |
| Albshausen | 8 | 53 | 32 | −39,6 % |

**Folgerungen:**
- **Einwohnerzahl je Ortsbezirk:** übertragbar (`status=abgeleitet`). Die Unschärfe liegt im Metatext.
- **Anteile aus Teilgruppen** (etwa ab 67 Jahren): In kleinen Ortsbezirken setzt die Cell-Key-Methode viele kleine Zellwerte auf Null, die Zähler sind also systematisch zu klein. Die Schwelle „Nenner ≥ 50“ allein reicht nicht.
  - Vorschlag: Anteil nur, wenn der Nenner ≥ 50 ist **und** die Summe der Teilgruppen höchstens 10 % von der Gesamtzahl abweicht. Der Nenner ist dabei die Summe der Teilgruppen. Sonst `status=fehlt` mit Hinweis.
  - Mit den infrastrukturellen Altersgruppen bestünden 10 von 17 Ortsbezirken diese Regel.
  - In Phase 1 sind gröbere Tabellen zu prüfen (5 Altersklassen, 10er-Jahresgruppen); sie haben vermutlich weniger „–“.
- **Jugend- und Altenquotient** brauchen die Grenzen 20 und 65 Jahre. Die infrastrukturellen Gruppen passen nicht (19–24, 60–66); nötig sind 5er-Jahresgruppen.
- **Mittelwerte** (Durchschnittsalter, Haushaltsgröße, Wohnfläche je Bewohner): nur gewichtet aggregieren, wenn das Gewicht je Zelle vorliegt. Sonst nur Gemeindewert.
- **Gitterebene:** wird nicht angezeigt (wie im Prompt vorgesehen). In den kleinsten Ortsbezirken liegen im Mittel 7 bis 11 Einwohner in einer Zelle.

## 4. Wegweiser Kommune

- OpenAPI `info.version` 3.12.0; Datenstand laut `/rest/statistics/version`: 2026-10-15T08:45:18Z.
- Lizenz CC0 1.0 laut Fußzeile jedes Exports. Jüngstes Jahr 2023; wie weit die Zeitreihen zurückreichen, steht je Indikator im Feld `years` (in Phase 1 dokumentieren).
- Witzenhausen: `witzenhausen` (AGS 06636016), Demografietyp 2 „Alternde Städte und Gemeinden mit sozioökonomischen Herausforderungen“.

**Vorschlag Vergleichsebene** (Typ 2, 17.000–23.000 Einwohner, Nordhessen und Südniedersachsen):

| Kommune | friendlyUrl | Einwohner 2023 |
|---|---|---:|
| Witzenhausen | `witzenhausen` | 15.097 |
| Werra-Meißner-Kreis | `werra-meissner-kreis-lk` | 100.215 |
| Eschwege | `eschwege` | 19.435 |
| Hann. Münden | `hannoversch-muenden` | 23.418 |
| Bad Wildungen | `bad-wildungen` | 17.473 |
| Schwalmstadt | `schwalmstadt` | 18.661 |

**Vorschlag Indikatoren** (alle für Witzenhausen 2023 vorhanden; friendlyUrls aus `/rest/indicator/list`):

| friendlyUrl | Einheit | Witzenhausen 2023 | kleinräumig aus dem Zensus |
|---|---|---:|---|
| `bevoelkerung` | Anzahl | 15.097 | Einwohner (Stichtag 2022) |
| `bevoelkerungsentwicklung-ueber-die-letzten-5-jahre` | % | −0,5 | – |
| `durchschnittsalter` | Jahre | 45,8 | Durchschnittsalter, gewichtet (zu prüfen) |
| `jugendquotient` | je 100 der 20–64-Jährigen | 30,9 | aus 5er-Jahresgruppen (zu prüfen) |
| `altenquotient` | je 100 der 20–64-Jährigen | 43,2 | aus 5er-Jahresgruppen (zu prüfen) |
| `auslaenderanteil` | % | 9,4 | Ausländeranteil (zu prüfen; Hann. Münden: k. A.) |
| `kinderarmut` | % | 15,2 | – |
| `sgb-ii-quote` | % | 9,0 | – |
| `arbeitslose-an-den-svb` | % | 7,8 | – |
| `wanderungssaldo` | je 1.000 EW | 6,4 | – |
| `wohnflaeche-pro-person` | m² | 47,9 | Wohnfläche je Bewohner (zu prüfen) |
| `wohnungen-in-ein-zweifamilienhaeusern` | % | 72,4 | Wohnungen nach Gebäudetyp (zu prüfen) |

Hinweis für die Anzeige: Die Wegweiser-Werte beruhen bis 2023 auf der Fortschreibung des Zensus 2011, die Gitterwerte auf dem Zensus 2022. Beide werden nicht in einer Zahl vermischt.

## 5. Offene Entscheidungen vor Phase 1

1. Vergleichskommunen wie in Abschnitt 4 bestätigen oder ändern.
2. Indikatorauswahl bestätigen (12).
3. Schwellenregel für Anteile: Nenner ≥ 50 **und** Abweichung der Teilsumme höchstens 10 %.
4. Eigentümerquote je Ortsbezirk auf Zähler und Nenner umstellen oder nur auf Gemeindeebene zeigen.
5. Ablage `data/strukturdaten/`: alle Lizenzen sind offen (dl-de/by-2-0, dl-de/zero-2.0, CC0), es gibt keinen Grund für eine abweichende Ablage.
6. Optional: Entwurf einer Anfrage an die Stadt um Einwohnerzahlen je Stadtteil aus dem Melderegister.

## 6. Plan Phase 1 (nach Freigabe)

- Adapter `pipeline/strukturdaten.py` im Stil der übrigen Schritte:
  - lädt die Zensus-ZIPs nach `data/raw/` (nicht im Repository), filtert auf das Stadtgebiet mit einer Zelle Puffer und verwirft die Rohdateien;
  - holt die Wegweiser-Exporte über die friendlyUrls;
  - protokolliert `info.version` und bricht bei einer Änderung ab.
- Ausgabe nach Datenvertrag „Strukturdaten v1“: `indikatoren.tsv`, `werte.tsv`, `raum/ortsbezirk.geojson`, `zuordnung.tsv`, `gesamtstadt.tsv`, `meta.json`, dazu `audit_abruf.tsv`.
- Tests für die Schwellenregel, die Aggregation (Anzahlen summiert, Anteile nur aus Zähler und Nenner) und beide Spaltenschreibweisen.
