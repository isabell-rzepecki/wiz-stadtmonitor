# Phase 0: Bestandsaufnahme (23.10.2026)

## Korpus

Abgerufen wurde die Liste der PDF-Medien über die WP-REST-API von witzenhausen.eu (935 Einträge).

- **Einladungen:** 239 Dateien enthalten „Einladung“ im Namen, Zeitraum 07/2024 bis 10/2026.
- **Fremdobjekte:** rund 15, darunter Jagdgenossenschaft, Feuerwehr und Neujahrsempfang.

| Gremium | Einladungen |
|---|---|
| Seniorenrat | 20 |
| Stadtverordnetenversammlung | 14 |
| HFR-Ausschuss | 13 |
| BV-Ausschuss | 13, dazu Varianten „BuV“ und „StUUE“ |
| Sozialausschuss | 9 |
| Ausländerbeirat | 6 |
| STE-Ausschuss | 6 |
| Jugendrat | 5 |
| Ortsbeiräte | rund 125 |

Bei den Ortsbeiräten reicht die Spanne von 11 Einladungen (Hundelshausen, Ziegenhagen) bis zu einer (Berlepsch-Ellerode).

Weitere Befunde:

- **Stadtteilbeiräte** (Albshausen, Hubenrode) treten als eigener Gremientyp auf.
- **Dateinamen von 2024** folgen einem anderen Muster (`ob_ermschwerd_…`).
- Eine Datei mit dem Präfix „OB-“ ist der Ausländerbeirat. Das Gremium muss deshalb aus dem PDF-Kopf gelesen werden, nicht aus dem Dateinamen.

## Stichprobe: 20 Einladungen, 188 Tagesordnungspunkte

Datei: `stichprobe_20_einladungen.tsv`

**Kopfdaten:** Nr., Gremium, Datum und Uhrzeit sowie der Sitzungsort wurden in allen 20 Einladungen erkannt. Zwei Sonderfälle:

- eine Stadtverordnetenversammlung über zwei Tage (16. und 18.12.2025);
- Nr. 142/2026 im Kopf gegenüber 141 im Dateinamen.

**Vorlagennummer `STV/…`:**

| Gremien | Anteil der TOPs |
|---|---|
| StVV und Ausschüsse | 65 % (73 von 112) |
| Ortsbeiräte und Beiräte | 0 % |

**Verfahrens-TOPs** (Eröffnung, Niederschrift, Verschiedenes usw.): 80 von 188, also 43 %.

**Verortung der 108 inhaltlichen TOPs:**

| Stufe | TOPs | Anmerkung |
|---|---|---|
| A (Ortsbeirat) | 27 | |
| B (vorläufige Regel) | 16 | etwa 5 Fehltreffer |
| ohne Ortsbezug | 65 | überwiegend Haushalt und Satzungen |

Beispiele für die Fehltreffer: „Ermschwerder Straße“ liegt in der Kernstadt, „Fahrradweg“ und „Festplatz“ sind keine Straßennamen.

**Anker für Stufe B in Phase 3:**

- Flurstücksangaben („Gem. X, Fl. Y, Flst. Z“), auflösbar über ALKIS;
- Bebauungsplan mit Nummer und Gemarkung;
- Flurnamen (Rabensberg, Werra-Ufer), auflösbar über OSM oder ALKIS;
- Straßennamen, abgeglichen mit dem Straßenverzeichnis aus den Hauskoordinaten.

## Übernahme aus allris-test

| Urteil | Teile |
|---|---|
| Unverändert | `net.py`, `geo.py`, `sprachmodell.py`, Leaflet und Markercluster |
| Angepasst | Seite (`index.html`, `app.js`, `timeline.js`, `style.css`) und `config.py` |
| Später angepasst (Phase 2 bis 4) | Normalisierung, Stufe B/C, Export und Prüfung |
| Nicht übernommen | Soll-Modell, Prozesse, Beteiligung, Baustellen, Assistent, Evaluierung, Tour und alle Bonner Daten |
