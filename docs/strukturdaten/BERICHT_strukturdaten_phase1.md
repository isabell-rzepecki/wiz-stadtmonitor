# Strukturdaten Witzenhausen – Bericht Phase 1 und 2 (Adapter und Raumabgleich)

> Stand 10.11.2026 · umgesetzt nach den Entscheidungen zu Phase 0 (alle fünf Punkte wie empfohlen) · noch keine Anzeige auf der Seite

## Umgesetzt

- **Adapter** `pipeline/strukturdaten.py`, Schritte `fetch-strukturdaten` und `strukturdaten` (im Gesamtlauf nach `wohnen`).
  - Zensus: ZIP laden, auf das Stadtgebiet mit einer Zelle Puffer filtern, verwerfen. Der Auszug liegt nur im Zwischenspeicher, je Tabelle 40–100 KB.
  - Wegweiser: `info.version` prüfen; weicht sie von 3.12.0 ab, bricht der Abruf ab.
- **Ausgabe** nach Datenvertrag „Strukturdaten v1“ in `data/strukturdaten/`:
  - Datenvertrag: `indikatoren.tsv`, `werte.tsv`, `raum/ortsbezirk.geojson`, `raum/gemeinde.geojson`, `zuordnung.tsv`, `gesamtstadt.tsv`, `meta.json`.
  - Protokolle: `audit_abruf.tsv`, `audit_raumabgleich.tsv`, `audit_schwelle.tsv`.
- **Raumabgleich:** 820 Zellen über den Mittelpunkt zugeordnet; Grenzzellen mit Flächenanteil und Konfidenz im Audit. Eine Zelle liegt mit dem Mittelpunkt außerhalb, aber teilweise im Stadtgebiet; sie ist gemeldet und nicht zugeordnet.
- **Entscheidungen:**
  - Vergleichskommunen und zwölf Indikatoren in `config/stadt.json` (`strukturdaten`).
  - Schwelle: Nenner ≥ 50 und Abweichung der Teilgruppen ≤ 10 %.
  - Eigentümerquote je Ortsbezirk entfernt (Pipeline, Daten, Fenster und Seite „Wohnen und Eigentum“); sie bleibt für die Gemeinde.
  - Entwurf der Anfrage an die Stadt: `anfrage_einwohner_stadtteile.md`.
- **Tests:** `tests/test_strukturdaten.py` prüft Auszug, Zuordnung, Summen, Schwelle, gewichtetes Mittel, Wegweiser-Export und Versionsabbruch. Alle Python- und Browsertests sind grün.

## Abweichungen vom Plan (Methode)

1. **Altersgruppen:** Bei den 5er-Jahresgruppen lag selbst die ganze Stadt 18 % unter der Gesamtzahl, die Schwelle hätte jeden Anteil verworfen. Genutzt wird deshalb die Tabelle mit 5 Altersklassen (Verlust der Stadt 2,2 %). Daraus entstehen die Anteile **unter 18** und **ab 65 Jahren**. Jugend- und Altenquotient (Grenze 20 Jahre) gibt es nur für die Gemeinde aus dem Wegweiser.
2. **Ausländeranteil, Haushaltsgröße, Wohnfläche je Person** gibt es nur für die Gemeinde (Wegweiser). Das Gitter liefert dafür nur Zellwerte, ohne Zähler und Nenner und ohne passendes Gewicht.

## Ergebnis (Zensus 2022, Stichtag 15.05.2022, abgeleitet)

| Ortsbezirk | Einwohner | unter 18 % | ab 65 % | Ø Alter | Wohnungen in EFH/ZFH % |
|---|---:|---:|---:|---:|---:|
| Stadt (Zellsumme) | 15.202 | 15,7 | 24,8 | 45,7 | 59,2 |
| Kernstadt | 7.022 | 15,9 | 23,9 | 44,6 | 41,5 |
| Hundelshausen | 1.036 | 15,1 | 28,9 | 47,3 | 78,9 |
| Ermschwerd | 966 | 13,7 | 26,5 | 46,4 | 68,6 |
| Gertenbach | 922 | 16,7 | 24,0 | 44,8 | 70,4 |
| Unterrieden | 807 | 16,5 | 21,1 | 44,5 | 89,0 |
| Kleinalmerode | 730 | 12,8 | 28,7 | 48,8 | 83,7 |
| Wendershausen | 671 | 20,0 | 21,1 | 43,8 | 83,3 |
| Roßbach | 599 | – | – | 47,8 | 88,3 |
| Ziegenhagen | 584 | 17,4 | 27,4 | 46,9 | 68,0 |
| Dohrenbach | 542 | 13,2 | 25,4 | 48,6 | 73,5 |
| Werleshausen | 388 | 17,9 | 20,8 | 45,3 | 81,2 |
| Ellingerode | 294 | – | – | 46,8 | 61,8 |
| Blickershausen | 226 | 14,5 | 27,2 | 48,3 | 79,3 |
| Hubenrode | 181 | 13,6 | 23,6 | 47,5 | 80,2 |
| Berlepsch-Ellerode | 112 | 12,7 | 25,5 | 51,5 | 15,8 |
| Neuseesen | 69 | 18,6 | 24,3 | 44,6 | 70,0 |
| Albshausen | 53 | – | – | 50,7 | – |

„–“ heißt: unter der Schwelle, Grund in `audit_schwelle.tsv`. Roßbach und Ellingerode scheitern an der Abweichung (10,0 % bzw. 11,6 %), Albshausen am Nenner.

## Auffällig, für die Verifikation (Phase 4)

- **Durchschnittsalter:** Die Stadt liegt bei 45,7 (Zensus 2022), der Wegweiser nennt für 2023 45,8. Das passt.
- **Wohnungen in Ein- und Zweifamilienhäusern:** 59,2 % im Zensus 2022 gegenüber 72,4 % im Wegweiser 2023. Der Wegweiser beruht bis 2023 auf der Fortschreibung des Zensus 2011; vermutlich unterscheiden sich auch Abgrenzung und Grundgesamtheit. Bis zur Klärung werden beide Werte nur getrennt und mit Quelle gezeigt.
- **Berlepsch-Ellerode:** 15,8 % Wohnungen in Ein- und Zweifamilienhäusern bei 112 Einwohnern. Bitte vor Ort plausibilisieren.

## Nächster Schritt (Phase 3, nach Freigabe)

Kontext-Panel im Fenster eines Ortsteils und zuschaltbare Kartenebene (Choroplethen, nur Anteile und Mittelwerte, fünf Quantilklassen, Tabellenansicht, Hinweis zum ökologischen Fehlschluss), ausschließlich aus `data/strukturdaten/`.
