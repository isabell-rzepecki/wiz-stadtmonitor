# Datenquellen

Erzeugt aus `data/quellen_register.tsv` und `data/attribution.tsv` mit `python tools/datenquellen.py`; nicht von Hand bearbeiten.

Status laut Register: `verifiziert`, `teilweise`, `zu prüfen`, `zu verifizieren`. Einträge aus Recherchen gelten als ungeprüft, bis eine Quelle im Projekt genutzt und abgerufen wurde (Spalte Test).

## Adressen

| Quelle | Anbieter | Lizenz | Namensnennung | Status | Test | Nutzung |
|---|---|---|---|---|---|---|
| [Suchdienst Hauskoordinaten/Lage/Flurstücke](https://www.gds-srv.hessen.de/cgi-bin/lika-services/ogc-free-data.ows?SERVICE=WFS&VERSION=1.1.0&REQUEST=GetCapabilities) (`hako_lage`) | HVBG | dl-de/zero-2.0 | Geobasisdaten: © Hessische Verwaltung für Bodenmanagement und Geoinformation (HVBG), dl-de/zero-2.0 (freiwillig) | verifiziert | hako: GetFeature mit Filter HA_KREIS=36, HA_GEMEINDE=016 → 5.233 Adressen, 378 Straßen (Namen mit Ortsteilzusatz bei Doppelungen); lage: 2-km-Kacheln, 5.052 Flurstücke; flst: Abfrage je Flurstück; Punkt-in-Gemarkung ohne Abweichung | Straßen- und Lageverzeichnis je Gemarkung (data/geo/dl-de-zero/lagebezeichnungen.json), Flurstückspunkte für Stufe B |
| [Hauskoordinaten Hessen (Gesamtdatei)](https://gds.hessen.de/INTERSHOP/web/WFS/HLBG-Geodaten-Site/de_DE/-/EUR/ViewDownloadcenter-Start) (`hako_txt`) | HVBG | dl-de/zero-2.0 | – | zu prüfen | nicht getestet | Offline-Alternative zum WFS |

## Bauleitplanung

| Quelle | Anbieter | Lizenz | Namensnennung | Status | Test | Nutzung |
|---|---|---|---|---|---|---|
| [Bebauungspläne Stadt Witzenhausen (Umringe)](https://www.gdi-nordosthessen.de/ws/wfs/ds_plu_bplan_whs/ows.wfs?SERVICE=WFS&VERSION=2.0.0&REQUEST=GetFeature&TYPENAMES=lyr:witzenhausen_bplaene_umringe_feature&SRSNAME=EPSG:4326) (`bplan`) | Magistrat der Stadt Witzenhausen / GDI Nordosthessen | Nutzung ohne Vertrag nur nicht kommerziell | Geltungsbereiche Bauleitplanung: Magistrat der Stadt Witzenhausen – Nutzung nur für nicht kommerzielle Zwecke | verifiziert, Nutzung nicht kommerziell, nicht weitergeben | GetFeature HTTP 200, 184 Umringe (EPSG:4326, Achsen Länge/Breite), Feld nutzungsrecht bestätigt | Abgleich Plannummer → Vorgang; Kartenebene der Seite mit Nutzungshinweis; Rohdaten nur im Build (data/geo/restricted/), nicht im Repository und nicht im Datenpaket |
| [Flächennutzungspläne Stadt Witzenhausen](https://www.gdi-nordosthessen.de/ws/wfs/2f2bfc47-027f-051b/ds_lu_fplan_whs/ows.wfs?SERVICE=WFS&VERSION=2.0.0&REQUEST=GetFeature&TYPENAMES=lyr:witzenhausen_fplaene_umringe_feature&SRSNAME=EPSG:4326) (`fplan`) | Magistrat der Stadt Witzenhausen | Nutzung ohne Vertrag nur nicht kommerziell | Geltungsbereiche Bauleitplanung: Magistrat der Stadt Witzenhausen – Nutzung nur für nicht kommerzielle Zwecke | verifiziert, Nutzung nicht kommerziell, nicht weitergeben | Proxy-URL des Geoportals liefert bei GetFeature einen Fehler; Dienst-URL aus den Capabilities: GetFeature HTTP 200, 45 Umringe mit Plandokumenten (PDF) | wie bplan; FNP-Änderungen im Titel abgleichen |

## Bevölkerung

| Quelle | Anbieter | Lizenz | Namensnennung | Status | Test | Nutzung |
|---|---|---|---|---|---|---|
| [Zensus 2022 Alter in 10er-Jahresgruppen in Gitterzellen](https://www.destatis.de/DE/Themen/Gesellschaft-Umwelt/Bevoelkerung/Zensus2022/_publikationen.html) (`zensus_alter_gitter`) | Statistische Ämter | DL-DE BY 2.0 | – | teilweise | nicht geprüft | Altersstruktur (aus Ergänzungsregister 10/2026, eigene Prüfung bei Nutzung) |

## Finanzen

| Quelle | Anbieter | Lizenz | Namensnennung | Status | Test | Nutzung |
|---|---|---|---|---|---|---|
| [Pläne/Berichte/Abschlüsse](https://www.witzenhausen.eu/plane-berichte-abschlusse/) (`haushalt_stadt`) | Stadt Witzenhausen | amtliche Dokumente | – | verifiziert | nicht geprüft | Haushaltskennzahlen (aus Ergänzungsregister 10/2026, eigene Prüfung bei Nutzung) |

## Hintergrundkarte

| Quelle | Anbieter | Lizenz | Namensnennung | Status | Test | Nutzung |
|---|---|---|---|---|---|---|
| [basemap.de Web Vektor (grau)](https://sgx.geodatenzentrum.de/gdz_basemapde_vektor/styles/bm_web_gry.json) (`basemap`) | BKG / AdV | CC BY 4.0 | © basemap.de / BKG (Jahr) – Datenquellen: © GeoBasis-DE | verifiziert | HTTP 200, Style-Version 5.1.0 | Hintergrund für MapLibre GL JS |

## Infrastruktur

| Quelle | Anbieter | Lizenz | Namensnennung | Status | Test | Nutzung |
|---|---|---|---|---|---|---|
| [OpenStreetMap (Overpass)](https://overpass-api.de/api/interpreter) (`osm`) | OSM-Mitwirkende | ODbL 1.0 | © OpenStreetMap-Mitwirkende, ODbL | zu prüfen | nicht getestet | Sitzungsorte, POIs; ODbL-Daten getrennt ablegen |

## Kataster

| Quelle | Anbieter | Lizenz | Namensnennung | Status | Test | Nutzung |
|---|---|---|---|---|---|---|
| [WFS HE ALKIS vereinfacht](https://www.gds.hessen.de/wfs2/aaa-suite/cgi-bin/alkis/vereinf/wfs?SERVICE=WFS&VERSION=2.0.0&REQUEST=GetCapabilities) (`alkis`) | HVBG | dl-de/zero-2.0 | – | verifiziert | Capabilities HTTP 200 | Flurstücksangaben in TOPs verorten (nur kleinräumige Abrufe) |

## Natur

| Quelle | Anbieter | Lizenz | Namensnennung | Status | Test | Nutzung |
|---|---|---|---|---|---|---|
| [Schutzgebiete Hessen als OGC API](https://www.geoportal.hessen.de/spatial-objects/266) (`schutzgeb_ogcapi`) | HMLU/Geoportal Hessen | zu prüfen | – | verifiziert | nicht geprüft | GeoJSON-Alternative (aus Ergänzungsregister 10/2026, eigene Prüfung bei Nutzung) |

## Referenz

| Quelle | Anbieter | Lizenz | Namensnennung | Status | Test | Nutzung |
|---|---|---|---|---|---|---|
| [Wikidata Stadt und Ortsteile](https://www.wikidata.org/wiki/Special:EntityData/Q564827.json) (`wikidata`) | Wikimedia | CC0 | Daten: Wikidata (CC0) (freiwillig) | verifiziert | HTTP 200 | Namensnormalisierung, stabile IDs |

## Sitzungsdaten

| Quelle | Anbieter | Lizenz | Namensnennung | Status | Test | Nutzung |
|---|---|---|---|---|---|---|
| [Amtliche Bekanntmachungen (PDF)](https://www.witzenhausen.eu/wp-json/wp/v2/media?mime_type=application/pdf&per_page=100&search=Einladung) (`wp_media`) | Stadt Witzenhausen | amtliche Werke (§ 5 UrhG, Bestätigung ausstehend) | Quelle: Amtliche Bekanntmachungen der Stadt Witzenhausen, witzenhausen.eu | verifiziert | HTTP 200; 935 PDF-Medien, 211 Einladungen nach Ausschluss von Fremdobjekten; 210 von 211 ohne Parserfehler | Primärquelle (aus v0.1) |

## Statistik

| Quelle | Anbieter | Lizenz | Namensnennung | Status | Test | Nutzung |
|---|---|---|---|---|---|---|
| [Gemeindedatenblatt Witzenhausen (636016)](https://www.hessen-gemeindelexikon.de/gemeindelexikon_PDF/636016.pdf) (`gemeindelexikon`) | Hessen Agentur/HSL | zu prüfen | – | teilweise | Abruf fehlgeschlagen 23.10.2026 | Bevölkerung/Prognose (aus Ergänzungsregister 10/2026, eigene Prüfung bei Nutzung) |
| [Gemeindeverzeichnis 06636016](https://www.statistikportal.de/de/gemeindeverzeichnis/06636016) (`gv_statistikportal`) | Statistische Ämter | zu prüfen | – | verifiziert | nicht geprüft | Fläche/Einwohner (aus Ergänzungsregister 10/2026, eigene Prüfung bei Nutzung) |

## Umwelt

| Quelle | Anbieter | Lizenz | Namensnennung | Status | Test | Nutzung |
|---|---|---|---|---|---|---|
| [Gebiete naturbedingter Risiken (ÜSG, HWRM)](https://geodienste-umwelt.hessen.de/arcgis/services/inspire/gebiete_naturbedingter_risiken/MapServer/WFSServer?SERVICE=WFS&REQUEST=GetCapabilities) (`uesg`) | HLNUG | CC BY 4.0 (HLNUG-Quellenvermerk) | Darstellung auf der Grundlage von Daten des Hessischen Landesamtes für Naturschutz, Umwelt und Geologie (HLNUG) | verifiziert, eingebunden | GetFeature HTTP 200 nur mit BBOX in urn:ogc:def:crs:EPSG::4326 (Breite zuerst); mit EPSG:25832 0 Objekte. Im Stadtgebiet: ÜSG 2, HQ häufig 20, HQ100 29, HQ extrem 16 Flächen | Kartenebene Hochwasser (pipeline/umwelt.py), räumliche Überschneidung mit Flurstücken und Geltungsbereichen |
| [Trinkwasser- und Heilquellenschutzgebiete](https://geodienste-umwelt.hessen.de/arcgis/services/inspire/bewirtschaftungsgebiete/MapServer/WFSServer?SERVICE=WFS&REQUEST=GetCapabilities) (`tws`) | HLNUG | CC BY 4.0 (HLNUG-Quellenvermerk) | Darstellung auf der Grundlage von Daten des Hessischen Landesamtes für Naturschutz, Umwelt und Geologie (HLNUG) | verifiziert, eingebunden (Kartengrundlage zu klären) | GetFeature HTTP 200; im Stadtgebiet 62 Zonenflächen (ALK-Fassung). Nutzungsbedingung: keine Darstellung auf nicht zugeordneter Kartengrundlage (ALK bzw. TK25), siehe Issue #12 | Kartenebene Wasserschutz (nicht rechtsverbindlich), räumliche Überschneidung |
| [Schutzgebiete Hessen](https://geodienste-umwelt.hessen.de/arcgis/services/inspire/schutzgebiete/MapServer/WFSServer?SERVICE=WFS&REQUEST=GetCapabilities) (`schutzgeb`) | HMLU / Natureg | frei für private, kommerzielle und Planungszwecke; keine Weiterveräußerung der Daten (Fees im Capabilities-Dokument) | Darstellung auf der Grundlage von Daten des Hessischen Ministeriums für Landwirtschaft und Umwelt, Weinbau, Forsten, Jagd und Heimat (HMLU); Naturparke: Landesbetrieb HessenForst | verifiziert, eingebunden | GetFeature HTTP 200; im Stadtgebiet NSG 6, FFH 5, LSG 4, Naturpark 1 (ganzes Stadtgebiet), Vogelschutzgebiet 0 | Kartenebene Schutzgebiete Natur, räumliche Überschneidung (ohne Naturpark) |

## Verwaltung

| Quelle | Anbieter | Lizenz | Namensnennung | Status | Test | Nutzung |
|---|---|---|---|---|---|---|
| [Ortsbeiräte](https://www.witzenhausen.eu/ortsbeirate/) (`ortsbeiraete_seite`) | Stadt Witzenhausen | – | – | verifiziert | nicht geprüft | Verlinkung (aus Ergänzungsregister 10/2026, eigene Prüfung bei Nutzung) |

## Verwaltungsgrenzen

| Quelle | Anbieter | Lizenz | Namensnennung | Status | Test | Nutzung |
|---|---|---|---|---|---|---|
| [Digitale Verwaltungsgrenzen Hessen](https://gds-srv.hessen.de/atomfeed/DigVGr-epsg25832-shp.zip) (`vg_shp`) | HVBG | dl-de/zero-2.0 | Geobasisdaten: © Hessische Verwaltung für Bodenmanagement und Geoinformation (HVBG), dl-de/zero-2.0 (freiwillig) | verifiziert | HTTP 200, 67,7 MB, ERZEUGT_AM 17.06.2026; GMDE_NR 636016: 17 Gemarkungen; Abgleich mit Material-GeoJSON: Flächenübereinstimmung ≥ 99,9 % | Ortsbezirksflächen (data/geo/dl-de-zero/ortsbezirke.geojson), Lage von Plänen ohne Gemarkungskennung |
| [WFS Verwaltungsgrenzen Hessen](https://basisdienste.geoportal.hessen.de/ogc/borders?SERVICE=WFS&VERSION=2.0.0&REQUEST=GetCapabilities) (`vg_wfs`) | ZKFG/GDI-Hessen | dl-de/zero-2.0 | – | verifiziert | Capabilities HTTP 200, Layer bestätigt | Alternative zum Shapefile |
| [OGC API Verwaltungsgrenzen Hessen](https://www.geoportal.hessen.de/spatial-objects/885/collections?f=json) (`vg_ogcapi`) | GDI-Hessen | dl-de/zero-2.0 | – | teilweise | HTTP 200 (Collections-Liste), items-Abruf nicht getestet | GeoJSON-Direktabruf |
| [VG250 Gemeinden](https://sgx.geodatenzentrum.de/wfs_vg250?SERVICE=WFS&REQUEST=GetCapabilities) (`vg250`) | BKG | dl-de/by-2.0 | © BKG (Jahr) dl-de/by-2-0 | verifiziert | Capabilities HTTP 200 | Nachbargemeinden (inkl. NI/TH) für Vergleichskarte |

## Wahlen

| Quelle | Anbieter | Lizenz | Namensnennung | Status | Test | Nutzung |
|---|---|---|---|---|---|---|
| [votemanager Kommunalwahl 15.03.2026](https://votemanager-ks.ekom21cdn.de/2026-03-15/06636016/praesentation/index.html) (`wahl_kw2026_vm`) | Stadt Witzenhausen/ekom21 | zu prüfen | – | teilweise | Abruf verweigert 23.10.2026 | Ortsbeiratsergebnisse (aus Ergänzungsregister 10/2026, eigene Prüfung bei Nutzung) |
| [Wahlbekanntmachung Nr. 013/2026](https://www.witzenhausen.eu/wp-content/uploads/2026/01/013-2026-Wahlbekanntmachung-Kommunalwahl-15-03-2026.pdf) (`wahl_kw2026_bek`) | Stadt Witzenhausen | amtliche Bekanntmachung | – | verifiziert | nicht geprüft | Wahlbezirkseinteilung (aus Ergänzungsregister 10/2026, eigene Prüfung bei Nutzung) |
| [votemanager Kommunalwahl 14.03.2021](https://votemanager-ks.ekom21cdn.de/2021-03-14/06636016/html5/Kreiswahl_Hessen_362_Gemeinde_Stadt_Witzenhausen.html) (`wahl_kw2021_vm`) | Stadt Witzenhausen/ekom21 | zu prüfen | – | verifiziert | nicht geprüft | Vergleichswahl (aus Ergänzungsregister 10/2026, eigene Prüfung bei Nutzung) |
| [Ergebnisseite Kommunalwahl 2026 Witzenhausen](https://www.hessenschau.de/politik/kommunalwahlen/ergebnisse/ergebnisse-witzenhausen---kommunalwahl-2026-v3,kw26-gemeinde-g06636016-100.html) (`wahl_hessenschau`) | hessenschau/HSL | keine offene Lizenz | – | teilweise | nicht geprüft | Plausibilisierung (aus Ergänzungsregister 10/2026, eigene Prüfung bei Nutzung) |

## Wahlen/Orte

| Quelle | Anbieter | Lizenz | Namensnennung | Status | Test | Nutzung |
|---|---|---|---|---|---|---|
| [Wahlraumübersicht 2016](https://votemanager-ks.ekom21cdn.de/20160306/06636016/html5/Wahllokaluebersicht.html) (`wahl_wahlraeume2016`) | Stadt Witzenhausen/ekom21 | zu prüfen | – | teilweise | nicht geprüft | Sitzungsorte (aus Ergänzungsregister 10/2026, eigene Prüfung bei Nutzung) |

## Wohnen

| Quelle | Anbieter | Lizenz | Namensnennung | Status | Test | Nutzung |
|---|---|---|---|---|---|---|
| [Zensus 2022 Durchschnittliche Nettokaltmiete in Gitterzellen](https://www.destatis.de/DE/Themen/Gesellschaft-Umwelt/Bevoelkerung/Zensus2022/_publikationen.html) (`zensus_miete_gitter`) | Statistische Ämter des Bundes und der Länder | DL-DE BY 2.0 | © Statistische Ämter des Bundes und der Länder, (Jahr), dl-de/by-2-0 | teilweise | nicht geprüft | Mietniveau-Raster (aus Ergänzungsregister 10/2026, eigene Prüfung bei Nutzung) |
| [Datensatzbeschreibung Nettokaltmiete Gitter](https://www.zensus2022.de/static/Zensus_Veroeffentlichung/Datensatzbeschreibung_Durchschn_Nettokaltmiete_Gitterzellen.xlsx) (`zensus_miete_doku`) | Statistische Ämter | DL-DE BY 2.0 | – | verifiziert | nicht geprüft | Spaltennamen (aus Ergänzungsregister 10/2026, eigene Prüfung bei Nutzung) |
| [Zensus 2022 Eigentümerquote in Gitterzellen](https://www.destatis.de/DE/Themen/Gesellschaft-Umwelt/Bevoelkerung/Zensus2022/_publikationen.html) (`zensus_eigentum_gitter`) | Statistische Ämter | DL-DE BY 2.0 | © Statistische Ämter des Bundes und der Länder, (Jahr), dl-de/by-2-0 | teilweise | nicht geprüft | Eigentumsquote (aus Ergänzungsregister 10/2026, eigene Prüfung bei Nutzung) |
| [Zensus 2022 Leerstandsquote/marktaktive Leerstandsquote in Gitterzellen](https://www.destatis.de/DE/Themen/Gesellschaft-Umwelt/Bevoelkerung/Zensus2022/_publikationen.html) (`zensus_leerstand_gitter`) | Statistische Ämter | DL-DE BY 2.0 | © Statistische Ämter des Bundes und der Länder, (Jahr), dl-de/by-2-0 | teilweise | nicht geprüft | Leerstandskarte (aus Ergänzungsregister 10/2026, eigene Prüfung bei Nutzung) |
| [Anlage zu § 1 Abs. 3 WoGV – Mietenstufen](https://www.gesetze-im-internet.de/wogv/anlage.html) (`wogv_anlage`) | BMJ | amtliches Werk (§ 5 UrhG) | – | verifiziert | nicht geprüft | Mietenstufe (aus Ergänzungsregister 10/2026, eigene Prüfung bei Nutzung) |
| [GEWOS Ergebnisbericht 2026](https://hessen.de/sites/hessen.hessen.de/files/damlocalcopy/infop_document/2026_gewos_hessen_angespannte_wohnungsmaerkte_ergebnisbericht_final.pdf) (`gewos_2026`) | HMWVW/GEWOS | zu prüfen | – | verifiziert | nicht geprüft | Indikatoren (aus Ergänzungsregister 10/2026, eigene Prüfung bei Nutzung) |

## Wohnen und Boden

| Quelle | Anbieter | Lizenz | Namensnennung | Status | Test | Nutzung |
|---|---|---|---|---|---|---|
| [Bodenrichtwerte Hessen (BORIS) Stichtag 01.01.2024](https://www.gds.hessen.de/wfs2/boris/cgi-bin/brw/2024/wfs?SERVICE=WFS&VERSION=2.0.0&REQUEST=GetCapabilities) (`boris`) | ZGGH / HVBG | Nutzung ohne Einschränkung (AccessConstraints) | Bodenrichtwerte: Gutachterausschüsse für Immobilienwerte des Landes Hessen / ZGGH, Stichtag angeben | verifiziert | GetFeature HTTP 200, 395 Zonen in BBOX, 294 in Witzenhausen | Bodenrichtwerte je Gemarkung/Ortsbezirk; Material: bodenrichtwerte_2024_spannen_gemarkung.tsv |
| [Bodenrichtwerte Hessen Stichtag 01.01.2022](https://www.gds.hessen.de/wfs2/boris/cgi-bin/brw/2022/wfs?SERVICE=WFS&VERSION=2.0.0&REQUEST=GetCapabilities) (`boris2022`) | ZGGH / HVBG | wie boris | – | verifiziert | Capabilities HTTP 200 | Zeitvergleich |
| Bodenrichtwerte Hessen Stichtag 01.01.2026 (`boris2026`) | ZGGH / HVBG | vermutlich wie boris | – | ersetzt durch boris2026_feed (Ergänzungsregister 10/2026) | 404 unter analogem Pfad | aktuellen Stichtag ermitteln (boris.hessen.de, gds.hessen.de) |
| [Immobilienmarktberichte GAA Hersfeld-Rotenburg/Schwalm-Eder/Werra-Meißner und Land Hessen](https://gds.hessen.de (Downloadcenter)) (`immo_bericht`) | Gutachterausschuss beim AfB Homberg (Efze); ZGGH | Nutzungsbedingungen im Bericht prüfen | – | zu prüfen | nicht getestet | Kaufpreise, Umsätze; manuell tabellarisch erfassen |
| [Zensus 2022 Gebäude und Wohnungen (Gemeinde)](https://ergebnisse.zensus2022.de) (`zensus_gem`) | Statistische Ämter des Bundes und der Länder | dl-de/by-2.0 | © Statistische Ämter des Bundes und der Länder, (Jahr), dl-de/by-2-0 | zu verifizieren | Werte sekundär über wahlatlas.net abgerufen | Kennzahlen Witzenhausen und Nachbarn; Material: zensus2022_wohnen_nachbargemeinden.tsv |
| [Zensus 2022 Gitterzellen (100 m)](https://www.destatis.de/DE/Themen/Gesellschaft-Umwelt/Bevoelkerung/Zensus2022/_publikationen.html) (`zensus_gitter`) | Statistische Ämter des Bundes und der Länder | dl-de/by-2.0 | © Statistische Ämter des Bundes und der Länder, (Jahr), dl-de/by-2-0 | zu prüfen | nicht getestet | Näherungswerte je Ortsbezirk (Gitter × Gemarkung) |
| [Wohngeld-Mietenstufe](https://www.gesetze-im-internet.de/wogv/) (`wohngeld`) | BMWSB / Wohngeldverordnung (Anlage) | amtliches Werk | – | zu prüfen | Sekundärquelle nennt Mietenstufe I | Kontextangabe mit Stand |
| [Angemessenheitsgrenzen KdU Werra-Meißner-Kreis](https://media.frag-den-staat.de/files/foi/97213/2018VerffentlichungVerwaltungsinterneHandlungsanweisung.pdf) (`kdu`) | Kreisausschuss WMK / Jobcenter | amtliches Dokument, Stand 01.05.2018 | – | veraltet, aktuellen Stand anfragen | nicht getestet | nur mit Stand; nicht als aktuelle Grenze darstellen |
| [Hessische Mieterschutzverordnung](https://verkuendung.hessen.de/sites/verkuendung.hessen.de/files/veroeffentlichungsplattform_plugin/published/1174/GVBl_2025_Nr_74_Regelungstext.pdf) (`mietpreisbremse`) | Land Hessen | amtliches Werk | – | Rechtslage im Fluss | nicht getestet | nur als datierter Hinweis; Zugehörigkeit Witzenhausens prüfen |

## Wohnen/Bevölkerung

| Quelle | Anbieter | Lizenz | Namensnennung | Status | Test | Nutzung |
|---|---|---|---|---|---|---|
| [Zensus2022_grid_final (FeatureServer)](https://services2.arcgis.com/jUpNdisbWqRpMo35/arcgis/rest/services/Zensus2022_grid_final/FeatureServer) (`zensus_esri_fs`) | Esri Deutschland (Drittanbieter) | DL-DE BY 2.0 (laut Esri-Item) | – | zu prüfen | nicht geprüft | Fallback (aus Ergänzungsregister 10/2026, eigene Prüfung bei Nutzung) |

## Wohnen/Boden

| Quelle | Anbieter | Lizenz | Namensnennung | Status | Test | Nutzung |
|---|---|---|---|---|---|---|
| [BORIS Hessen 2026 – INSPIRE Download Feed](https://www.geoportal.hessen.de/mapbender/php/mod_inspireDownloadFeed.php?id=c1afe4df-1290-42b3-9399-6bfd00652c13&type=SERVICE&generateFrom=wfs&wfsid=732) (`boris2026_feed`) | HVBG | DL-DE Zero 2.0 | Bodenrichtwerte: Gutachterausschüsse für Immobilienwerte des Landes Hessen / ZGGH, Stichtag angeben | teilweise | geprüft 23.10.2026 | Bodenrichtwertzonen 2026 (aus Ergänzungsregister 10/2026, eigene Prüfung bei Nutzung) |
| [BORIS Hessen 2026 – Geoportal-Kartenprojekt](https://www.geoportal.hessen.de/map?WMC=8243) (`boris2026_wmc`) | HVBG | DL-DE Zero 2.0 | – | verifiziert | nicht geprüft | Link/Viewer (aus Ergänzungsregister 10/2026, eigene Prüfung bei Nutzung) |
| [WFS HE BORIS 2024 als OGC API](https://www.geoportal.hessen.de/spatial-objects/864) (`boris2024_api`) | HVBG/Geoportal Hessen | DL-DE Zero 2.0 | – | verifiziert | nicht geprüft | Zeitvergleich (aus Ergänzungsregister 10/2026, eigene Prüfung bei Nutzung) |
| [WFS HE BORIS 2022 als OGC API](https://www.geoportal.hessen.de/spatial-objects/731) (`boris2022_api`) | HVBG/Geoportal Hessen | DL-DE Zero 2.0 | – | verifiziert | nicht geprüft | Zeitreihe (aus Ergänzungsregister 10/2026, eigene Prüfung bei Nutzung) |
| [Bestandsdatenausgabe Bodenrichtwerte (BRM 3.0.1)](https://hvbg.hessen.de/immobilienwertermittlung/bodenrichtwerte) (`boris_xml`) | HVBG | zu prüfen | – | zu prüfen | nicht geprüft | Vollattribute (aus Ergänzungsregister 10/2026, eigene Prüfung bei Nutzung) |
| [Immobilienmarktbericht 2023 GAA Homberg (Efze) – Pressemitteilung](https://hvbg.hessen.de/presse/immobilienmarktbericht-2023-online-verfuegbar-weniger-transaktionen) (`immo_wmk_2023`) | HVBG | zu prüfen | – | teilweise | nicht geprüft | Umsätze WMK (aus Ergänzungsregister 10/2026, eigene Prüfung bei Nutzung) |

## Wohnen/Recht

| Quelle | Anbieter | Lizenz | Namensnennung | Status | Test | Nutzung |
|---|---|---|---|---|---|---|
| [Entwurf Hessische Mieterschutzverordnung 2026](https://hessen.de/presse/mieterschutz-soll-auf-71-kommunen-wachsen) (`mischuv_2026`) | HMWVW | amtliche Pressemitteilung | – | verifiziert | geprüft 23.10.2026 | nicht erfasst (aus Ergänzungsregister 10/2026, eigene Prüfung bei Nutzung) |

## Wohnen/Soziales

| Quelle | Anbieter | Lizenz | Namensnennung | Status | Test | Nutzung |
|---|---|---|---|---|---|---|
| [KdU-Angemessenheitsrichtwerte WMK (Stand 01.01.2023)](https://harald-thome.de/files/pdf/KdU%20New/KdU%20Werra-Mei%C3%9Fner%20Kreis%20-%2001.01.2023.pdf) (`kdu_wmk_2023`) | Jobcenter Werra-Meißner (Kopie harald-thome.de) | keine offene Lizenz | – | teilweise | nicht geprüft | KdU-Grenzen (aus Ergänzungsregister 10/2026, eigene Prüfung bei Nutzung) |
| [Jobcenter Werra-Meißner – Unterkunftskosten](https://jobcenter-werra-meissner.de/geldleistungen/unterkunftskosten/) (`kdu_jobcenter`) | Jobcenter Werra-Meißner | keine offene Lizenz | – | zu prüfen | nicht geprüft | aktueller Flyer (aus Ergänzungsregister 10/2026, eigene Prüfung bei Nutzung) |
| [Merkblatt Anmietung von Wohnraum](https://www.werra-meissner-kreis.de/fileadmin/01_Homepage_Kreisverwaltung/Fachbereiche_und_Einrichtungen/FB6_Soziales_und_Senioren/6.1_Sicherung_Aktivierung_der_Lebensgrundlagen/Merkblatt_KdU.pdf) (`kdu_merkblatt_wmk`) | Kreisausschuss WMK | keine offene Lizenz | – | teilweise | nicht geprüft | Verfahren (aus Ergänzungsregister 10/2026, eigene Prüfung bei Nutzung) |

## ÖPNV

| Quelle | Anbieter | Lizenz | Namensnennung | Status | Test | Nutzung |
|---|---|---|---|---|---|---|
| [Soll-Fahrplandaten NVV (GTFS)](https://mobilithek.info/offers/-1983289435982938851) (`nvv_gtfs`) | NVV via OpenData ÖPNV/Mobilithek | freie Nutzung/Open Data (genau zu prüfen) | – | teilweise | nicht lesbar ohne JS 23.10.2026 | Haltestellen/Linien (aus Ergänzungsregister 10/2026, eigene Prüfung bei Nutzung) |
| [OpenData ÖPNV – Datensätze](https://www.opendata-oepnv.de/ht/de/datensaetze) (`oepnv_portal`) | OpenData ÖPNV | je Datensatz | – | teilweise | nicht geprüft | Haltepositionen (aus Ergänzungsregister 10/2026, eigene Prüfung bei Nutzung) |
