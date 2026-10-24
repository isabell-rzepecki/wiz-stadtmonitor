# Lizenzen der Daten

Die Daten stehen nicht unter der MIT-Lizenz des Codes.

| Datei | Quelle | Lizenz |
|---|---|---|
| `export/vorgaenge.json`, `export/audit/*.tsv`, `export/stadtmonitor-daten.zip` (im Workflow erzeugt) | Einladungen in den amtlichen Bekanntmachungen der Stadt Witzenhausen, https://www.witzenhausen.eu/amtliche-bekanntmachungen/ | vermutlich amtliche Werke nach § 5 Abs. 1 UrhG; Bestätigung durch die Stadt offen |
| `geo/dl-de-zero/ortsbezirke.geojson`, `export/flaechen.json` | Gemarkungen aus den Digitalen Verwaltungsgrenzen Hessen (HVBG), https://gds-srv.hessen.de/atomfeed/DigVGr-epsg25832-shp.zip; Zuordnung zu Ortsbezirken laut `config/stadt.json` | dl-de/zero-2.0; „Geobasisdaten: © HVBG“ (freiwillig) |
| `geo/dl-de-zero/lagebezeichnungen.json` | Straßen und Lagebezeichnungen je Gemarkung aus dem Suchdienst der HVBG (Ebenen hako und lage), Bezugspunkt = Median; ohne Hausnummern | dl-de/zero-2.0 |
| `geo/dl-de-zero/flurstuecke.json` | Flurstückspunkte aus dem Suchdienst der HVBG (Ebene flst), nur für in Titeln genannte Flurstücke | dl-de/zero-2.0 |
| `geo/dl-de-zero/bodenrichtwerte_2024.geojson`, `export/karte/bodenrichtwerte.json`, `export/wohnen.json` (Bodenrichtwerte) | BORIS Hessen, Stichtag 01.01.2024, Gutachterausschüsse für Immobilienwerte des Landes Hessen / ZGGH | Nutzung ohne Einschränkung oder Bedingung (AccessConstraints des Dienstes) |
| `wohnen/zensus2022.json`, `export/wohnen.json` (Zensus) | Zensus 2022: Regionaltabelle Gebäude und Wohnungen; 100-m-Gitter Nettokaltmiete und Eigentümerquote, je Gemarkung aggregiert | dl-de/by-2.0; „© Statistische Ämter des Bundes und der Länder, 2024“ |
| `export/karte/umwelt_*.json` | Hochwasser und Wasserschutzgebiete (HLNUG); Schutzgebiete (HMLU, Naturparke: HessenForst) | HLNUG: CC BY 4.0; HMLU: frei nutzbar, keine Weiterveräußerung |
| `export/karte/umwelt_wind.json`, `export/karte/umwelt_denkmal.json` | Windvorranggebiete (Regionalplan Nordhessen, HMWVW); Bau- und Flächendenkmäler (LfDH, DenkXweb) | dl-de/by-2.0 |
| `wahlen/wahlen.json`, `export/wahlen.json` (Kommunalwahlen) | Amtliche Bekanntmachungen der Ergebnisse (Nr. 043/2026, 044/2026) und amtliche Ergebnispräsentation 2021 (votemanager); nur Wahlvorschläge, Stimmen und Sitze, keine Personennamen | amtliche Werke (§ 5 Abs. 1 UrhG); Quelle angeben |
| `wahlen/wahlen.json`, `export/wahlen.json` (Bundestags- und Europawahlen) | Wahlbezirksstatistik der Bundeswahlleiterin, summiert für die Gemeinde | „Vervielfältigung und Verbreitung, auch auszugsweise, mit Quellenangabe gestattet“; © Die Bundeswahlleiterin |
| `export/beteiligung.json` | Amtliche Bekanntmachungen zur Bauleitplanung: Plan, Stufen, Fristen; ohne Ansprechpersonen | wie Einladungen (amtliche Werke) |
| `export/karte/umwelt_gebaeude.json` | Gebäude für öffentliche Zwecke, ALKIS vereinfacht (HVBG) | Nutzung ohne Einschränkung (§ 18 HVGG); Quellenvermerk mit Hinweis auf Veränderung |
| `geo/hvgg/gebaeude3d/*.json`, `export/gebaeude3d/*.json` | 3D-Gebäudemodelle LoD2 (HVBG, Download-Center), je Ortsteil auf Grundriss und gemessene Höhe vereinfacht; derzeit nur Bauwerke (BW) | Nutzung ohne Einschränkung (§ 18 HVGG); Quellenvermerk mit Hinweis auf Veränderung |
| `wanderung/wanderung.json`, `export/wanderung.json` | Zu- und Fortzüge, Geburten, Sterbefälle und Bevölkerung je Gemeinde des Werra-Meißner-Kreises 2015–2024; Wanderung des Kreises über die Kreisgrenze 2024 (Hessisches Statistisches Landesamt) | „Vervielfältigung und Verbreitung, auch auszugsweise, mit Quellenangabe gestattet“; © Hessisches Statistisches Landesamt, Wiesbaden |
| `geo/dl-de-zero/wanderung_geo.json` | Gemeindegrenzen des Werra-Meißner-Kreises (vereinfacht) und Mittelpunkte der hessischen Kreise aus den Digitalen Verwaltungsgrenzen (HVBG) | dl-de/zero-2.0 |
| `export/eigentum.json` | Beteiligungsbericht der Stadt (§ 123a HGO): Unternehmen, Rechtsform, Gegenstand, Gesellschafter; ohne Personen | amtliche Veröffentlichung der Stadt; Quelle angeben |
| Kartenhintergrund (nur angezeigt, nicht gespeichert) | basemap.de Web Raster, BKG | CC BY 4.0; „© basemap.de / BKG \| Datenquellen: © GeoBasis-DE“ |
| `../phase0/stichprobe_20_einladungen.tsv` | 20 Einladungen (wie oben), Stufen vorläufig abgeleitet | wie oben |
| `../tests/fixtures/vorgaenge.json`, `../tests/fixtures/einladungen/` | Einladungen (wie oben), nur für Tests | wie oben |
| `export/karte/bauleitplanung.json` (nur Kartenebene der Seite, nicht im Repository, nicht im Datenpaket) | Umringe der Bebauungspläne und FNP-Änderungen, Magistrat der Stadt Witzenhausen (WFS der GDI Nordosthessen) | Nutzung ohne vertragliche Vereinbarung nur für nicht kommerzielle Zwecke; nicht weitergeben |
| `export/audit/verortung_bauleitplanung.tsv` | Zuordnung Vorgang → Plannummer, abgeleitet aus Titeln und Plankennungen; keine Geometrie | wie Einladungen |

Weitere Quellen (Gemarkungen und Hauskoordinaten der HVBG unter dl-de/zero-2.0, OpenStreetMap unter ODbL) folgen; das Register steht in `quellen_register.tsv`. Ihr Stand ist in `docs/Datenquellen_Geodaten_Witzenhausen.md` beschrieben.
