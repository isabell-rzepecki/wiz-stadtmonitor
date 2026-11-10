# Strukturdaten Witzenhausen – Bericht Phase 4 (Verifikation)

> Stand 10.11.2026 · Werkzeug `tools/strukturdaten_verifikation.py` · Ergebnis `data/strukturdaten/audit_verifikation.tsv`

## Stichprobe von 20 Werten

Die Prüfung ist unabhängig vom Adapter: Die Quellen werden neu geladen und mit eigenem Code ausgewertet.

| Prüfweg | Werte | Ergebnis |
|---|---:|---|
| Zensus je Ortsbezirk: Originaldateien neu geladen, eigene Zuordnung über den Zellmittelpunkt (räumlicher Index), eigene Summen | 7 | alle übereinstimmend; Ellingerode zu Recht nicht ausgewiesen (Teilgruppen 11,6 % unter der Gesamtzahl) |
| Zensus für die Stadt gegen die amtlichen Regionaltabellen | 3 | erwartete Abweichungen, siehe unten |
| Wegweiser über den zweiten Endpunkt der Schnittstelle (JSON statt CSV) | 10 | alle übereinstimmend, auch „keine Angabe“ (Hann. Münden, Ausländeranteil 2023) |

**Erwartete Abweichungen zur amtlichen Gemeindetabelle**

| Merkmal | Stadtmonitor | Regionaltabelle | Abweichung | Grund |
|---|---:|---:|---:|---|
| Einwohner | 15.202 | 15.162 | +0,26 % | Geheimhaltung (Cell-Key-Methode) und Zuordnung der Zellen |
| Wohnungen | 7.865 | 7.989 | −1,6 % | wie oben |
| Wohnungen in Ein- und Zweifamilienhäusern | 59,2 % | 62,2 % | −3,0 Punkte | andere Zählweise: Gitter nach Bauart, Regionaltabelle nach Zahl der Wohnungen im Gebäude |

## Geklärte Auffälligkeiten

- **Ein- und Zweifamilienhäuser, Zensus gegenüber Wegweiser:**
  - Der Wegweiser (72,4 % für 2023) beruht auf der Fortschreibung des Zensus 2011. Sein Wert springt zwischen 2020 und 2023 (72,3 → 68,4 → 72,4).
  - Zensus 2022: 59,2 % nach Bauart, 62,2 % nach Zahl der Wohnungen.
  - Die Differenz liegt in den Quellen, nicht in der Aggregation. Die Erläuterung des Merkmals nennt jetzt die Zählweise.
- **Berlepsch-Ellerode (15,8 %):** In drei benachbarten Zellen liegen Mehrfamilienhäuser und Gebäude anderer Bauart mit zusammen rund 50 Wohnungen. Ein- und Zweifamilienhäuser gibt es nur in vier kleinen Zellen mit je 3 Wohnungen. Der Wert entspricht der Quelle; wer die Gebäudegruppe kennt, kann sie benennen.
- **Durchschnittsalter:** Die Stadt liegt bei 45,7 Jahren (Zensus, 15.05.2022), der Wegweiser nennt für 2022 und 2023 45,7 und 45,8 Jahre.

## Lizenzhinweise und Datenstand

- Namensnennungen auf der Seite (Fußzeile „Quellen, Lizenzen und Datenstand“): Zensus (dl-de/by-2-0), Wegweiser Kommune (CC0 1.0, freiwillig) und HVBG (dl-de/zero-2.0).
- Lizenzen stehen außerdem in `data/LICENSE-DATA.md` (drei Einträge für `strukturdaten/`), in der README und je Merkmal in `indikatoren.tsv` sowie in der Erläuterung im Fenster.
- Datenstand: `meta.json` (Zensus 15.05.2022, Wegweiser bis 2023, Abrufdatum) erscheint im Fenster und in der Fußzeile.

## Auslieferung

- Die Strukturdaten mit allen Audits liegen im Datenpaket der Seite (`data/export/stadtmonitor-daten.zip`, Ordner `strukturdaten/`).
- Ein eigenes Zip-Paket mit Ergebnissen, Audits und Berichten wurde übergeben.
