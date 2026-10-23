# Lizenzen der Daten

Die Daten stehen nicht unter der MIT-Lizenz des Codes.

| Datei | Quelle | Lizenz |
|---|---|---|
| `export/vorgaenge.json`, `export/audit/*.tsv`, `export/stadtmonitor-daten.zip` (im Workflow erzeugt) | Einladungen in den amtlichen Bekanntmachungen der Stadt Witzenhausen, https://www.witzenhausen.eu/amtliche-bekanntmachungen/ | vermutlich amtliche Werke nach § 5 Abs. 1 UrhG; Bestätigung durch die Stadt offen |
| Kartenhintergrund (nur angezeigt, nicht gespeichert) | basemap.de Web Raster, BKG | CC BY 4.0; „© basemap.de / BKG \| Datenquellen: © GeoBasis-DE“ |
| `../phase0/stichprobe_20_einladungen.tsv` | 20 Einladungen (wie oben), Stufen vorläufig abgeleitet | wie oben |
| `../tests/fixtures/vorgaenge.json`, `../tests/fixtures/einladungen/` | Einladungen (wie oben), nur für Tests | wie oben |
| `export/karte/bauleitplanung.json` (nur Kartenebene der Seite, nicht im Repository, nicht im Datenpaket) | Umringe der Bebauungspläne und FNP-Änderungen, Magistrat der Stadt Witzenhausen (WFS der GDI Nordosthessen) | Nutzung ohne vertragliche Vereinbarung nur für nicht kommerzielle Zwecke; nicht weitergeben |
| `export/audit/verortung_bauleitplanung.tsv` | Zuordnung Vorgang → Plannummer, abgeleitet aus Titeln und Plankennungen; keine Geometrie | wie Einladungen |

Weitere Quellen (Gemarkungen und Hauskoordinaten der HVBG unter dl-de/zero-2.0, OpenStreetMap unter ODbL) folgen; das Register steht in `quellen_register.tsv`. Ihr Stand ist in `docs/Datenquellen_Geodaten_Witzenhausen.md` beschrieben.
