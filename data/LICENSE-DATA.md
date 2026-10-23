# Lizenzen der Daten

Die Daten stehen nicht unter der MIT-Lizenz des Codes.

| Datei | Quelle | Lizenz |
|---|---|---|
| `export/vorgaenge.json`, `export/audit/*.tsv`, `export/stadtmonitor-daten.zip` (im Workflow erzeugt) | Einladungen in den amtlichen Bekanntmachungen der Stadt Witzenhausen, https://www.witzenhausen.eu/amtliche-bekanntmachungen/ | vermutlich amtliche Werke nach § 5 Abs. 1 UrhG; Bestätigung durch die Stadt offen |
| `geo/dl-de-zero/ortsbezirke.geojson`, `export/flaechen.json` | Gemarkungen aus den Digitalen Verwaltungsgrenzen Hessen (HVBG), https://gds-srv.hessen.de/atomfeed/DigVGr-epsg25832-shp.zip; Zuordnung zu Ortsbezirken laut `config/stadt.json` | dl-de/zero-2.0; „Geobasisdaten: © HVBG“ (freiwillig) |
| `geo/dl-de-zero/lagebezeichnungen.json` | Straßen und Lagebezeichnungen je Gemarkung aus dem Suchdienst der HVBG (Ebenen hako und lage), Bezugspunkt = Median; ohne Hausnummern | dl-de/zero-2.0 |
| Kartenhintergrund (nur angezeigt, nicht gespeichert) | basemap.de Web Raster, BKG | CC BY 4.0; „© basemap.de / BKG \| Datenquellen: © GeoBasis-DE“ |
| `../phase0/stichprobe_20_einladungen.tsv` | 20 Einladungen (wie oben), Stufen vorläufig abgeleitet | wie oben |
| `../tests/fixtures/vorgaenge.json`, `../tests/fixtures/einladungen/` | Einladungen (wie oben), nur für Tests | wie oben |
| `export/karte/bauleitplanung.json` (nur Kartenebene der Seite, nicht im Repository, nicht im Datenpaket) | Umringe der Bebauungspläne und FNP-Änderungen, Magistrat der Stadt Witzenhausen (WFS der GDI Nordosthessen) | Nutzung ohne vertragliche Vereinbarung nur für nicht kommerzielle Zwecke; nicht weitergeben |
| `export/audit/verortung_bauleitplanung.tsv` | Zuordnung Vorgang → Plannummer, abgeleitet aus Titeln und Plankennungen; keine Geometrie | wie Einladungen |

Weitere Quellen (Gemarkungen und Hauskoordinaten der HVBG unter dl-de/zero-2.0, OpenStreetMap unter ODbL) folgen; das Register steht in `quellen_register.tsv`. Ihr Stand ist in `docs/Datenquellen_Geodaten_Witzenhausen.md` beschrieben.
