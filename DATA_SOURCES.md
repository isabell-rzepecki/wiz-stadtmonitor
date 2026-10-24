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

## Beteiligung

| Quelle | Anbieter | Lizenz | Namensnennung | Status | Test | Nutzung |
|---|---|---|---|---|---|---|
| [Seite Öffentlichkeitsbeteiligung (Bauleitplanung § 3 BauGB)](https://www.witzenhausen.eu/offentlichkeitsbeteiligung/) (`oeffentlichkeitsbeteiligung`) | Stadt Witzenhausen | amtliche Bekanntmachung | – | verifiziert, verlinkt | geprüft 23.10.2026 | Link „Planunterlagen der Stadt“ bei laufender Beteiligung |
| [UVP-Portal der Länder (Hessen)](https://www.uvp-verbund.de) (`uvp_portal`) | UVP-Verbund | zu prüfen | – | zu prüfen | nicht geprüft | Planfeststellungen/Genehmigungen mit Öffentlichkeitsbeteiligung (aus Ergänzung v0.3, eigene Prüfung bei Nutzung) |

## Beteiligung/Planung

| Quelle | Anbieter | Lizenz | Namensnennung | Status | Test | Nutzung |
|---|---|---|---|---|---|---|
| [Stadtumbau ISEK Kernstadt](https://www.witzenhausen.eu/stadtumbau-isek/) (`isek_stadtumbau`) | Stadt Witzenhausen | amtliche Dokumente | – | verifiziert | geprüft 23.10.2026 | Beteiligungschronik; Untersuchungsgebiet nur als PDF (Digitalisierung nötig) (aus Ergänzung v0.3, eigene Prüfung bei Nutzung) |

## Beteiligung/Sitzungen

| Quelle | Anbieter | Lizenz | Namensnennung | Status | Test | Nutzung |
|---|---|---|---|---|---|---|
| [Amtliche Bekanntmachungen (eigener Inhaltstyp)](https://www.witzenhausen.eu/wp-json/wp/v2/bekanntmachungen?per_page=100&page=1&_fields=id,date,title,link) (`wp_bekanntmachungen`) | Stadt Witzenhausen | amtliche Bekanntmachungen | – | verifiziert, eingebunden | 160 Einträge (ab 10/2025), meta.dateilink_b = PDF; zusammen mit PDF-Dateinamen ab 2024: 9 Bekanntmachungen zur Bauleitplanung erkannt | Beteiligungsverfahren der Bauleitplanung (pipeline/beteiligung.py) |

## Bevölkerung

| Quelle | Anbieter | Lizenz | Namensnennung | Status | Test | Nutzung |
|---|---|---|---|---|---|---|
| [Zensus 2022 Alter in 10er-Jahresgruppen in Gitterzellen](https://www.destatis.de/DE/Themen/Gesellschaft-Umwelt/Bevoelkerung/Zensus2022/_publikationen.html) (`zensus_alter_gitter`) | Statistische Ämter | DL-DE BY 2.0 | – | teilweise | nicht geprüft | Altersstruktur (aus Ergänzungsregister 10/2026, eigene Prüfung bei Nutzung) |

## Denkmal

| Quelle | Anbieter | Lizenz | Namensnennung | Status | Test | Nutzung |
|---|---|---|---|---|---|---|
| [Kulturdenkmäler Hessen (DenkXweb)](https://geodienste.denkx.de/geoserver/denkx/wfs?SERVICE=WFS&VERSION=2.0.0&REQUEST=GetCapabilities) (`denkmal_wfs`) | Landesamt für Denkmalpflege Hessen | dl-de/by-2.0 (laut Ergänzung v0.3; im Capabilities-Dokument nicht genannt) | Kulturdenkmäler: Landesamt für Denkmalpflege Hessen (DenkXweb), dl-de/by-2-0 | verifiziert, eingebunden | GetFeature JSON HTTP 200; im Stadtgebiet 383 Baudenkmäler und 19 Gesamtanlagen; Erfassung laut Dienst nicht flächendeckend | nur Kartenebene (keine Verortung von TOPs); Bodendenkmäler nicht gezeigt |

## Eigentum

| Quelle | Anbieter | Lizenz | Namensnennung | Status | Test | Nutzung |
|---|---|---|---|---|---|---|
| [Beteiligungsbericht der Stadt (2021–2024)](https://www.witzenhausen.eu/wp-content/uploads/2025/11/167-2025-Beteiligungsbericht-2024.pdf) (`beteiligungsbericht`) | Stadt Witzenhausen | amtliches Dokument | Beteiligungsbericht der Stadt Witzenhausen 2024 | verifiziert, eingebunden | Bericht 2024 (PDF, HTTP 200): 7 Pflichtangaben, 14 freiwillige Angaben | Liste der Unternehmen mit Rechtsform, Gegenstand und Gesellschaftern; ohne Personen |

## Finanzen

| Quelle | Anbieter | Lizenz | Namensnennung | Status | Test | Nutzung |
|---|---|---|---|---|---|---|
| [Pläne/Berichte/Abschlüsse](https://www.witzenhausen.eu/plane-berichte-abschlusse/) (`haushalt_stadt`) | Stadt Witzenhausen | amtliche Dokumente | – | verifiziert | nicht geprüft | Haushaltskennzahlen (aus Ergänzungsregister 10/2026, eigene Prüfung bei Nutzung) |

## Förderung

| Quelle | Anbieter | Lizenz | Namensnennung | Status | Test | Nutzung |
|---|---|---|---|---|---|---|
| [Kohesio – EU-geförderte Projekte](https://kohesio.ec.europa.eu) (`kohesio`) | Europäische Kommission | zu prüfen | – | zu prüfen | nicht geprüft | Fördermittel mit Ortsbezug (aus Ergänzung v0.3, eigene Prüfung bei Nutzung) |

## Gebäude

| Quelle | Anbieter | Lizenz | Namensnennung | Status | Test | Nutzung |
|---|---|---|---|---|---|---|
| [ALKIS vereinfacht – GebaeudeBauwerk](https://www.gds.hessen.de/wfs2/aaa-suite/cgi-bin/alkis/vereinf/wfs?SERVICE=WFS&VERSION=2.0.0&REQUEST=GetCapabilities) (`alkis_gebaeude`) | HVBG | Nutzung ohne Einschränkung (§ 18 HVGG, AccessConstraints) | Gebäude: © Hessische Verwaltung für Bodenmanagement und Geoinformation (HVBG), ALKIS vereinfacht; Darstellung verändert | verifiziert, eingebunden | GET liefert 10 Objekte bzw. bei Filter eine Sperrseite (HTTP 403); POST mit Filter gmdschl + funktion: 545 Gebäude für öffentliche Zwecke (von 21.924 Gebäuden der Gemeinde) | Kartenebene Gebäude für öffentliche Zwecke (Nutzung, nicht Eigentum) |
| [INSPIRE HE Gebäude 3D LoD2 (Atom-Download)](https://hvbg.hessen.de/registry/spatial/dataset/06184092-4b18-48e5-aa23-fb3a3ef572f7) (`lod2_he`) | HVBG | dl-de/zero-2.0 | – | teilweise | nicht geprüft | 3D-Ansicht: Daten nicht über diesen Dienst, sondern aus dem Download-Center (lod2_dlc) |
| [3D-Gebäudemodelle LoD2 (Download-Center, Gemeinde Witzenhausen)](https://gds.hessen.de/INTERSHOP/web/WFS/HLBG-Geodaten-Site/de_DE/-/EUR/ViewDownloadcenter-Start?path=3D-Daten/3D-Geb%C3%A4udemodelle/3D-Geb%C3%A4udemodelle%20LoD2) (`lod2_dlc`) | HVBG | Nutzung ohne Einschränkung (§ 18 HVGG); im Download-Center nicht gesondert ausgewiesen | 3D-Gebäudemodelle LoD2: © Hessische Verwaltung für Bodenmanagement und Geoinformation (HVBG); Darstellung vereinfacht | teilweise | BW: 484 Objekte, Lieferdatum 12.01.2022, Aktualität 10.04.2021; 495 Gebäude(teile) mit gemessener Höhe übernommen | 3D-Ansicht (site/3d.html): Grundriss und gemessene Höhe je Ortsteil, data/geo/hvgg/gebaeude3d/ |

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

## Planung

| Quelle | Anbieter | Lizenz | Namensnennung | Status | Test | Nutzung |
|---|---|---|---|---|---|---|
| [Regionalplan Nordhessen (WFS)](https://geodatendienste-landesplanung-hessen.de/ows/services/org.3.fd8337b7-de57-4cc3-9393-e7c1d74120a4_wfs?SERVICE=WFS&VERSION=2.0.0&REQUEST=GetCapabilities) (`rp_nordhessen_wfs`) | HMWVW | dl-de/by-2.0 | Regionalplan Nordhessen: Hessisches Ministerium für Wirtschaft, Energie, Verkehr, Wohnen und ländlichen Raum (HMWVW), dl-de/by-2-0 | verifiziert, eingebunden | GetFeature JSON HTTP 200 mit BBOX EPSG:4326 (Breite zuerst); 4 Vorranggebiete im Stadtgebiet (ESW 03, 05, 07, 12b), Abstimmungsstand „2. Offenlegung“ | Kartenebene Windvorranggebiete; räumliche Überschneidung mit Flurstücken und Geltungsbereichen; planung/bestand nicht ausgewertet |
| [Regionalplan Nordhessen (WMS)](https://geodatendienste-landesplanung-hessen.de/ows/services/org.3.fd8337b7-de57-4cc3-9393-e7c1d74120a4_wms?SERVICE=WMS&REQUEST=GetCapabilities) (`rp_nordhessen_wms`) | HMWVW | dl-de/by-2.0 | – | verifiziert | geprüft 23.10.2026 | Darstellung (aus Ergänzung v0.3, eigene Prüfung bei Nutzung) |
| [Regionalversammlung Nordhessen – Drucksachen](https://rim.ekom21.de/rp-kassel/) (`rp_kassel_rim`) | RP Kassel (ekom21 RIM) | amtliche Dokumente | – | zu prüfen | nicht geprüft | Neuaufstellung Regionalplan; OParl-Schnittstelle prüfen (aus Ergänzung v0.3, eigene Prüfung bei Nutzung) |

## Planung/Energie

| Quelle | Anbieter | Lizenz | Namensnennung | Status | Test | Nutzung |
|---|---|---|---|---|---|---|
| [Ermittlung von Solar-Potentialflächen (2022)](https://www.witzenhausen.eu/wp-content/uploads/2024/07/witzenhausen_-_ermittlung_von_solar-potentialflaechen_ueberarbeitung_20072022.pdf) (`solar_potential`) | Stadt Witzenhausen | amtliches Dokument | – | teilweise | nicht geprüft | Kontext zu PV-Anträgen; Karten nur als PDF (aus Ergänzung v0.3, eigene Prüfung bei Nutzung) |

## Referenz

| Quelle | Anbieter | Lizenz | Namensnennung | Status | Test | Nutzung |
|---|---|---|---|---|---|---|
| [Wikidata Stadt und Ortsteile](https://www.wikidata.org/wiki/Special:EntityData/Q564827.json) (`wikidata`) | Wikimedia | CC0 | Daten: Wikidata (CC0) (freiwillig) | verifiziert | HTTP 200 | Namensnormalisierung, stabile IDs |

## Sitzungen

| Quelle | Anbieter | Lizenz | Namensnennung | Status | Test | Nutzung |
|---|---|---|---|---|---|---|
| [Einreicher von Anträgen und Anfragen (TOP-Titel)](https://www.witzenhausen.eu/amtliche-bekanntmachungen/) (`einreicher_top`) | Stadt Witzenhausen (Einladungen) | wie Einladungen | – | eingebunden | 97 TOPs mit Muster, 0 ohne Zuordnung (23.10.2026) | Angabe und Filter, ohne Zählung je Fraktion |

## Sitzungsdaten

| Quelle | Anbieter | Lizenz | Namensnennung | Status | Test | Nutzung |
|---|---|---|---|---|---|---|
| [Amtliche Bekanntmachungen (PDF)](https://www.witzenhausen.eu/wp-json/wp/v2/media?mime_type=application/pdf&per_page=100&search=Einladung) (`wp_media`) | Stadt Witzenhausen | amtliche Werke (§ 5 UrhG, Bestätigung ausstehend) | Quelle: Amtliche Bekanntmachungen der Stadt Witzenhausen, witzenhausen.eu | verifiziert | HTTP 200; 935 PDF-Medien, 211 Einladungen nach Ausschluss von Fremdobjekten; 210 von 211 ohne Parserfehler | Primärquelle (aus v0.1) |

## Statistik

| Quelle | Anbieter | Lizenz | Namensnennung | Status | Test | Nutzung |
|---|---|---|---|---|---|---|
| [Gemeindedatenblatt Witzenhausen (636016)](https://www.hessen-gemeindelexikon.de/gemeindelexikon_PDF/636016.pdf) (`gemeindelexikon`) | Hessen Agentur/HSL | zu prüfen | – | teilweise | Abruf fehlgeschlagen 23.10.2026 | Bevölkerung/Prognose (aus Ergänzungsregister 10/2026, eigene Prüfung bei Nutzung) |
| [Gemeindeverzeichnis 06636016](https://www.statistikportal.de/de/gemeindeverzeichnis/06636016) (`gv_statistikportal`) | Statistische Ämter | zu prüfen | – | verifiziert | nicht geprüft | Fläche/Einwohner (aus Ergänzungsregister 10/2026, eigene Prüfung bei Nutzung) |

## Trassen

| Quelle | Anbieter | Lizenz | Namensnennung | Status | Test | Nutzung |
|---|---|---|---|---|---|---|
| [SuedLink Planfeststellungsabschnitt C2 (Neu-Eichenberg – Herleshausen)](https://www.netzausbau.de) (`suedlink_c2`) | Bundesnetzagentur / TransnetBW | zu prüfen | – | zu prüfen | nicht geprüft | Trassenverlauf durch das Stadtgebiet (Werratal); Bauinfo Witzenhausen (aus Ergänzung v0.3, eigene Prüfung bei Nutzung) |
| [SuedLink – Information Baustart Stadt Witzenhausen](https://www.witzenhausen.eu/wp-content/uploads/2025/06/Witzenhausen_Anzeige_Baustart_C2.pdf) (`suedlink_baustart_wiz`) | TransnetBW (veröffentlicht über Stadt) | zu prüfen | – | verifiziert (URL) | nicht geprüft | Bauinfomärkte (z. B. Unterrieden 30.06.2025) (aus Ergänzung v0.3, eigene Prüfung bei Nutzung) |
| [BVWP 2030 Projektinformationssystem (PRINS)](https://www.bvwp-projekte.de) (`bvwp_prins`) | BMDV | zu prüfen | – | zu prüfen | nicht geprüft | Straßenbauvorhaben im Stadtgebiet (Betroffenheit unbelegt) (aus Ergänzung v0.3, eigene Prüfung bei Nutzung) |

## Umwelt

| Quelle | Anbieter | Lizenz | Namensnennung | Status | Test | Nutzung |
|---|---|---|---|---|---|---|
| [Gebiete naturbedingter Risiken (ÜSG, HWRM)](https://geodienste-umwelt.hessen.de/arcgis/services/inspire/gebiete_naturbedingter_risiken/MapServer/WFSServer?SERVICE=WFS&REQUEST=GetCapabilities) (`uesg`) | HLNUG | CC BY 4.0 (HLNUG-Quellenvermerk) | Darstellung auf der Grundlage von Daten des Hessischen Landesamtes für Naturschutz, Umwelt und Geologie (HLNUG) | verifiziert, eingebunden | GetFeature HTTP 200 nur mit BBOX in urn:ogc:def:crs:EPSG::4326 (Breite zuerst); mit EPSG:25832 0 Objekte. Im Stadtgebiet: ÜSG 2, HQ häufig 20, HQ100 29, HQ extrem 16 Flächen | Kartenebene Hochwasser (pipeline/umwelt.py), räumliche Überschneidung mit Flurstücken und Geltungsbereichen |
| [Trinkwasser- und Heilquellenschutzgebiete](https://geodienste-umwelt.hessen.de/arcgis/services/inspire/bewirtschaftungsgebiete/MapServer/WFSServer?SERVICE=WFS&REQUEST=GetCapabilities) (`tws`) | HLNUG | CC BY 4.0 (HLNUG-Quellenvermerk) | Darstellung auf der Grundlage von Daten des Hessischen Landesamtes für Naturschutz, Umwelt und Geologie (HLNUG) | verifiziert, eingebunden (Kartengrundlage zu klären) | GetFeature HTTP 200; im Stadtgebiet 62 Zonenflächen (ALK-Fassung). Nutzungsbedingung: keine Darstellung auf nicht zugeordneter Kartengrundlage (ALK bzw. TK25), siehe Issue #12 | Kartenebene Wasserschutz (nicht rechtsverbindlich), räumliche Überschneidung |
| [Schutzgebiete Hessen](https://geodienste-umwelt.hessen.de/arcgis/services/inspire/schutzgebiete/MapServer/WFSServer?SERVICE=WFS&REQUEST=GetCapabilities) (`schutzgeb`) | HMLU / Natureg | frei für private, kommerzielle und Planungszwecke; keine Weiterveräußerung der Daten (Fees im Capabilities-Dokument) | Darstellung auf der Grundlage von Daten des Hessischen Ministeriums für Landwirtschaft und Umwelt, Weinbau, Forsten, Jagd und Heimat (HMLU); Naturparke: Landesbetrieb HessenForst | verifiziert, eingebunden | GetFeature HTTP 200; im Stadtgebiet NSG 6, FFH 5, LSG 4, Naturpark 1 (ganzes Stadtgebiet), Vogelschutzgebiet 0 | Kartenebene Schutzgebiete Natur, räumliche Überschneidung (ohne Naturpark) |
| [Umgebungslärmkartierung Hessen 2022](https://geodienste-umwelt.hessen.de/arcgis/services/laerm/laerm_oden/MapServer/WMSServer?SERVICE=WMS&REQUEST=GetCapabilities) (`laerm_wms`) | HLNUG | CC BY 4.0 | – | teilweise | nicht geprüft (Metadaten Geoportal) | Kontextlayer Lärm; WFS nicht gefunden (aus Ergänzung v0.3, eigene Prüfung bei Nutzung) |

## Verwaltung

| Quelle | Anbieter | Lizenz | Namensnennung | Status | Test | Nutzung |
|---|---|---|---|---|---|---|
| [Ortsbeiräte](https://www.witzenhausen.eu/ortsbeirate/) (`ortsbeiraete_seite`) | Stadt Witzenhausen | – | – | verifiziert | nicht geprüft | Verlinkung (aus Ergänzungsregister 10/2026, eigene Prüfung bei Nutzung) |
| [Satzungen und Formulare (eigener Inhaltstyp)](https://www.witzenhausen.eu/wp-json/wp/v2/satzungen-formulare?per_page=100) (`wp_satzungen`) | Stadt Witzenhausen | amtliche Werke | – | verifiziert | geprüft 23.10.2026 | Ortsrecht mit Raumbezug (Hauptsatzung, Gebühren, Gestaltung) (aus Ergänzung v0.3, eigene Prüfung bei Nutzung) |
| [Hauptsatzung 2014 mit 1.–7. Änderung](https://www.witzenhausen.eu/satzungen-formulare/hauptsatzung/) (`hauptsatzung`) | Stadt Witzenhausen | amtliches Werk | – | verifiziert, eingebunden | Scan selbst eingesehen 23.10.2026: § 6 Abs. 2 „Gebiet der ehemaligen Gemeinde“ je Ortsbezirk; Änderungssatzungen nicht selbst geprüft | § 6: Ortsbezirke = Gebiete der ehemaligen Gemeinden; StVV 31 Sitze (2014), 37 ab 3. Änderung (2020) (aus Ergänzung v0.3, eigene Prüfung bei Nutzung) |

## Verwaltungsgrenzen

| Quelle | Anbieter | Lizenz | Namensnennung | Status | Test | Nutzung |
|---|---|---|---|---|---|---|
| [Digitale Verwaltungsgrenzen Hessen](https://gds-srv.hessen.de/atomfeed/DigVGr-epsg25832-shp.zip) (`vg_shp`) | HVBG | dl-de/zero-2.0 | Geobasisdaten: © Hessische Verwaltung für Bodenmanagement und Geoinformation (HVBG), dl-de/zero-2.0 (freiwillig) | verifiziert | HTTP 200, 67,7 MB, ERZEUGT_AM 17.06.2026; GMDE_NR 636016: 17 Gemarkungen; Abgleich mit Material-GeoJSON: Flächenübereinstimmung ≥ 99,9 % | Ortsbezirksflächen (data/geo/dl-de-zero/ortsbezirke.geojson), Lage von Plänen ohne Gemarkungskennung |
| [WFS Verwaltungsgrenzen Hessen](https://basisdienste.geoportal.hessen.de/ogc/borders?SERVICE=WFS&VERSION=2.0.0&REQUEST=GetCapabilities) (`vg_wfs`) | ZKFG/GDI-Hessen | dl-de/zero-2.0 | – | verifiziert | Capabilities HTTP 200, Layer bestätigt | Alternative zum Shapefile |
| [OGC API Verwaltungsgrenzen Hessen](https://www.geoportal.hessen.de/spatial-objects/885/collections?f=json) (`vg_ogcapi`) | GDI-Hessen | dl-de/zero-2.0 | – | teilweise | HTTP 200 (Collections-Liste), items-Abruf nicht getestet | GeoJSON-Direktabruf |
| [VG250 Gemeinden](https://sgx.geodatenzentrum.de/wfs_vg250?SERVICE=WFS&REQUEST=GetCapabilities) (`vg250`) | BKG | dl-de/by-2.0 | © BKG (Jahr) dl-de/by-2-0 | verifiziert | Capabilities HTTP 200 | Nachbargemeinden (inkl. NI/TH) für Vergleichskarte |
| [Historisches Ortslexikon Hessen (LAGIS)](https://lagis.hessen.de/de/orte/historisches-ortslexikon) (`lagis_ol`) | Hessisches Institut für Landesgeschichte (HIL) | Metadaten CC BY-SA 4.0 | – | verifiziert | 24.10.2026 im Browser geprüft (Seite lädt nur mit JavaScript): Bischhausen Gemarkung Witzenhausen, eingemeindet 30.09.1928; Hübenthal Gemarkung Berlepsch-Ellerode | Beleg für die Zuordnung Bischhausen → Kernstadt und Hübenthal → Berlepsch-Ellerode (nur zitiert, keine Daten übernommen) |

## Wahlen

| Quelle | Anbieter | Lizenz | Namensnennung | Status | Test | Nutzung |
|---|---|---|---|---|---|---|
| [votemanager Kommunalwahl 15.03.2026](https://votemanager-ks.ekom21cdn.de/2026-03-15/06636016/praesentation/index.html) (`wahl_kw2026_vm`) | Stadt Witzenhausen/ekom21 | zu prüfen | – | teilweise | Abruf verweigert 23.10.2026 | Ortsbeiratsergebnisse (aus Ergänzungsregister 10/2026, eigene Prüfung bei Nutzung) |
| [Wahlbekanntmachung Nr. 013/2026](https://www.witzenhausen.eu/wp-content/uploads/2026/01/013-2026-Wahlbekanntmachung-Kommunalwahl-15-03-2026.pdf) (`wahl_kw2026_bek`) | Stadt Witzenhausen | amtliche Bekanntmachung | – | verifiziert | nicht geprüft | Wahlbezirkseinteilung (aus Ergänzungsregister 10/2026, eigene Prüfung bei Nutzung) |
| [Stadtverordnetenwahl 14.03.2021 (votemanager)](https://votemanager-ks.ekom21cdn.de/2021-03-14/06636016/html5/Gemeindewahl_Hessen_363_Gemeinde_Stadt_Witzenhausen.html) (`wahl_kw2021_vm`) | Gemeindewahlleitung / ekom21 | amtliche Ergebnispräsentation; Lizenz der Open-Data-CSV nicht angegeben | Wahlergebnisse: Stadt Witzenhausen (Bekanntmachungen Nr. 043 und 044/2026; Ergebnispräsentation 2016 und 2021) | verifiziert, eingebunden (Stufe Schnellmeldung) | HTTP 200; „Alle Schnellmeldungen eingegangen“; Summen und 37 Sitze geprüft; robots.txt nicht vorhanden (303) | Anteile und Sitze 2021; ein Abruf je 30 Tage |
| [Ergebnisseite Kommunalwahl 2026 Witzenhausen](https://www.hessenschau.de/politik/kommunalwahlen/ergebnisse/ergebnisse-witzenhausen---kommunalwahl-2026-v3,kw26-gemeinde-g06636016-100.html) (`wahl_hessenschau`) | hessenschau/HSL | keine offene Lizenz | – | teilweise | nicht geprüft | Plausibilisierung (aus Ergänzungsregister 10/2026, eigene Prüfung bei Nutzung) |
| [Ergebnis der Stadtverordnetenwahl 15.03.2026 (Bekanntmachung Nr. 043/2026)](https://www.witzenhausen.eu/wp-content/uploads/2026/03/043-2026-Bekanntmachung-Ergebnis-Stavo-15-03-2026.pdf) (`wahl_stvv2026_bm`) | Stadt Witzenhausen (Wahlausschuss) | amtliches Werk (§ 5 UrhG) | Wahlergebnisse: Stadt Witzenhausen (Bekanntmachungen Nr. 043 und 044/2026; Ergebnispräsentation 2016 und 2021) | verifiziert, eingebunden | HTTP 200; endgültig, festgestellt 25.03.2026; Summen geprüft | Stimmen, Anteile, Sitze; keine Personennamen |
| [Ergebnis der Ortsbeiratswahlen 15.03.2026 (Bekanntmachung Nr. 044/2026)](https://www.witzenhausen.eu/wp-content/uploads/2026/03/044-2026-Bekanntmachung-Ergebnis-OB-15-03-2026.pdf) (`wahl_ob2026_bm`) | Stadt Witzenhausen (Wahlausschuss) | amtliches Werk (§ 5 UrhG) | Wahlergebnisse: Stadt Witzenhausen (Bekanntmachungen Nr. 043 und 044/2026; Ergebnispräsentation 2016 und 2021) | verifiziert, eingebunden | HTTP 200; 16 Ortsbezirke, Summen geprüft | Sitze je Wahlvorschlag, Wahlbeteiligung; keine Personennamen |
| [Stadtverordnetenwahl 06.03.2016 (votemanager)](https://votemanager-ks.ekom21cdn.de/20160306/06636016/html5/Gemeindewahl_Hessen_66_Gemeinde_Stadt_Witzenhausen.html) (`wahl_kw2016_vm`) | Gemeindewahlleitung / ekom21 | amtliche Ergebnispräsentation; Lizenz der Open-Data-CSV nicht angegeben | Wahlergebnisse: Stadt Witzenhausen (Bekanntmachungen Nr. 043 und 044/2026; Ergebnispräsentation 2016 und 2021) | verifiziert, eingebunden (Stufe Schnellmeldung) | HTTP 200; „Alle Schnellmeldungen eingegangen“; 31 Sitze (Hauptsatzung 2014, Ergänzung v0.3) und Summen geprüft | Anteile und Sitze 2016 |
| [KW 2026 Gemeinde- und Kreiswahl Ergebnisse (HSL)](https://statistik.hessen.de/unsere-zahlen/wahlen/datenangebot-fuer-presse) (`wahl_kw2026_hsl_csv`) | Hessisches Statistisches Landesamt | zu prüfen | – | nicht genutzt | Seite HTTP 200; nur Muster-CSV verlinkt | Bekanntmachung der Stadt ist Primärquelle |
| [Bundestagswahl 23.02.2025, Wahlbezirksstatistik](https://www.bundeswahlleiterin.de/bundestagswahlen/2025/ergebnisse/weitere-ergebnisse.html) (`wahl_btw2025_bwl_wbz`) | Die Bundeswahlleiterin | „Vervielfältigung und Verbreitung, auch auszugsweise, mit Quellenangabe gestattet“ | © Die Bundeswahlleiterin (im Auftrag der Herausgebergemeinschaft), Wahlbezirksstatistik | verifiziert, eingebunden | HTTP 200; Wahlbezirke der Gemeinde inkl. Briefwahl summiert, Summe der Parteien = gültige Stimmen | Ergebnisse für die Gemeinde |
| [Bundestagswahl 26.09.2021, Wahlbezirksstatistik](https://www.bundeswahlleiterin.de/bundestagswahlen/2021/ergebnisse/weitere-ergebnisse.html) (`wahl_btw2021_bwl_wbz`) | Die Bundeswahlleiterin | „Vervielfältigung und Verbreitung, auch auszugsweise, mit Quellenangabe gestattet“ | © Die Bundeswahlleiterin (im Auftrag der Herausgebergemeinschaft), Wahlbezirksstatistik | verifiziert, eingebunden | HTTP 200; Wahlbezirke der Gemeinde inkl. Briefwahl summiert, Summe der Parteien = gültige Stimmen | Ergebnisse für die Gemeinde |
| [Bundestagswahl 24.09.2017, Wahlbezirksstatistik](https://www.bundeswahlleiterin.de/bundestagswahlen/2017/ergebnisse/weitere-ergebnisse.html) (`wahl_btw2017_bwl_wbz`) | Die Bundeswahlleiterin | „Vervielfältigung und Verbreitung, auch auszugsweise, mit Quellenangabe gestattet“ | © Die Bundeswahlleiterin (im Auftrag der Herausgebergemeinschaft), Wahlbezirksstatistik | verifiziert, eingebunden | HTTP 200; Wahlbezirke der Gemeinde inkl. Briefwahl summiert, Summe der Parteien = gültige Stimmen | Ergebnisse für die Gemeinde |
| [Europawahl 09.06.2024, Wahlbezirksstatistik](https://www.bundeswahlleiterin.de/europawahlen/2024/ergebnisse/weitere-ergebnisse.html) (`wahl_ew2024_bwl_wbz`) | Die Bundeswahlleiterin | „Vervielfältigung und Verbreitung, auch auszugsweise, mit Quellenangabe gestattet“ | © Die Bundeswahlleiterin (im Auftrag der Herausgebergemeinschaft), Wahlbezirksstatistik | verifiziert, eingebunden | HTTP 200; Wahlbezirke der Gemeinde inkl. Briefwahl summiert, Summe der Parteien = gültige Stimmen | Ergebnisse für die Gemeinde |
| [Europawahl 26.05.2019, Wahlbezirksstatistik](https://www.bundeswahlleiterin.de/europawahlen/2019/ergebnisse/weitere-ergebnisse.html) (`wahl_ew2019_bwl_wbz`) | Die Bundeswahlleiterin | „Vervielfältigung und Verbreitung, auch auszugsweise, mit Quellenangabe gestattet“ | © Die Bundeswahlleiterin (im Auftrag der Herausgebergemeinschaft), Wahlbezirksstatistik | verifiziert, eingebunden | HTTP 200; Wahlbezirke der Gemeinde inkl. Briefwahl summiert, Summe der Parteien = gültige Stimmen | Ergebnisse für die Gemeinde |

## Wahlen/Orte

| Quelle | Anbieter | Lizenz | Namensnennung | Status | Test | Nutzung |
|---|---|---|---|---|---|---|
| [Wahlraumübersicht 2016](https://votemanager-ks.ekom21cdn.de/20160306/06636016/html5/Wahllokaluebersicht.html) (`wahl_wahlraeume2016`) | Stadt Witzenhausen/ekom21 | zu prüfen | – | teilweise | nicht geprüft | Sitzungsorte (aus Ergänzungsregister 10/2026, eigene Prüfung bei Nutzung) |

## Wohnen

| Quelle | Anbieter | Lizenz | Namensnennung | Status | Test | Nutzung |
|---|---|---|---|---|---|---|
| [Zensus 2022 Durchschnittliche Nettokaltmiete in Gitterzellen](https://www.destatis.de/DE/Themen/Gesellschaft-Umwelt/Bevoelkerung/Zensus2022/_publikationen.html) (`zensus_miete_gitter`) | Statistische Ämter des Bundes und der Länder | DL-DE BY 2.0 | © Statistische Ämter des Bundes und der Länder, 2024, dl-de/by-2-0 | verifiziert, eingebunden | Durchschnittliche_Nettokaltmiete_und_Anzahl_der_Wohnungen.zip HTTP 200 (mit Zahl vermieteter Wohnungen) | gewichtete Bestandsmiete je Ortsbezirk |
| [Datensatzbeschreibung Nettokaltmiete Gitter](https://www.zensus2022.de/static/Zensus_Veroeffentlichung/Datensatzbeschreibung_Durchschn_Nettokaltmiete_Gitterzellen.xlsx) (`zensus_miete_doku`) | Statistische Ämter | DL-DE BY 2.0 | – | verifiziert | nicht geprüft | Spaltennamen (aus Ergänzungsregister 10/2026, eigene Prüfung bei Nutzung) |
| [Zensus 2022 Eigentümerquote in Gitterzellen](https://www.destatis.de/DE/Themen/Gesellschaft-Umwelt/Bevoelkerung/Zensus2022/_publikationen.html) (`zensus_eigentum_gitter`) | Statistische Ämter | DL-DE BY 2.0 | © Statistische Ämter des Bundes und der Länder, 2024, dl-de/by-2-0 | verifiziert, eingebunden | Eigentuemerquote_in_Gitterzellen.zip HTTP 200 | Median der Zellwerte je Ortsbezirk |
| [Zensus 2022 Leerstandsquote/marktaktive Leerstandsquote in Gitterzellen](https://www.destatis.de/DE/Themen/Gesellschaft-Umwelt/Bevoelkerung/Zensus2022/_publikationen.html) (`zensus_leerstand_gitter`) | Statistische Ämter | DL-DE BY 2.0 | © Statistische Ämter des Bundes und der Länder, 2024, dl-de/by-2-0 | geprüft, nicht genutzt | Leerstandsquote_in_Gitterzellen.zip HTTP 200; „–“ fasst Null und Geheimhaltung zusammen | Quote je Ortsbezirk wäre verzerrt; nur Gemeindewert |
| [Anlage zu § 1 Abs. 3 WoGV – Mietenstufen](https://www.gesetze-im-internet.de/wogv/anlage.html) (`wogv_anlage`) | BMJ | amtliches Werk (§ 5 UrhG) | – | verifiziert | gesetze-im-internet.de/wogv/anlage.html HTTP 200 (24.10.2026): Hessen, Witzenhausen, Stadt – I | datierter Kontext im Panel |
| [GEWOS Ergebnisbericht 2026](https://hessen.de/sites/hessen.hessen.de/files/damlocalcopy/infop_document/2026_gewos_hessen_angespannte_wohnungsmaerkte_ergebnisbericht_final.pdf) (`gewos_2026`) | HMWVW/GEWOS | zu prüfen | – | verifiziert | nicht geprüft | Indikatoren (aus Ergänzungsregister 10/2026, eigene Prüfung bei Nutzung) |

## Wohnen und Boden

| Quelle | Anbieter | Lizenz | Namensnennung | Status | Test | Nutzung |
|---|---|---|---|---|---|---|
| [Bodenrichtwerte Hessen (BORIS) Stichtag 01.01.2024](https://www.gds.hessen.de/wfs2/boris/cgi-bin/brw/2024/wfs?SERVICE=WFS&VERSION=2.0.0&REQUEST=GetCapabilities) (`boris`) | ZGGH / HVBG | Nutzung ohne Einschränkung (AccessConstraints) | Bodenrichtwerte: Gutachterausschüsse für Immobilienwerte des Landes Hessen / ZGGH, Stichtag 01.01.2024 | verifiziert, eingebunden | GetFeature HTTP 200; 294 Zonen der Gemeinde, 107 baureifes Land; Spannen je Gemarkung gleich der Referenztabelle (17/17) | Spannen je Ortsbezirk, Kartenebene Bodenrichtwerte (pipeline/wohnen.py) |
| [Bodenrichtwerte Hessen Stichtag 01.01.2022](https://www.gds.hessen.de/wfs2/boris/cgi-bin/brw/2022/wfs?SERVICE=WFS&VERSION=2.0.0&REQUEST=GetCapabilities) (`boris2022`) | ZGGH / HVBG | wie boris | – | verifiziert | Capabilities HTTP 200 | Zeitvergleich |
| Bodenrichtwerte Hessen Stichtag 01.01.2026 (`boris2026`) | ZGGH / HVBG | vermutlich wie boris | – | nicht auffindbar | …/brw/2026/wfs und …/2025/wfs HTTP 404 (23.10.2026) | Stichtag 2024 ausgewiesen; Hinweis im Panel |
| [Immobilienmarktberichte GAA Hersfeld-Rotenburg/Schwalm-Eder/Werra-Meißner und Land Hessen](https://gds.hessen.de (Downloadcenter)) (`immo_bericht`) | Gutachterausschuss beim AfB Homberg (Efze); ZGGH | Nutzungsbedingungen im Bericht prüfen | – | nur verlinkt | nicht getestet | Liste im Panel; tabellarische Übernahme erst nach Prüfung der Nutzungsbedingungen |
| [Zensus 2022 Gebäude und Wohnungen (Gemeinde)](https://ergebnisse.zensus2022.de) (`zensus_gem`) | Statistische Ämter des Bundes und der Länder | dl-de/by-2.0 | © Statistische Ämter des Bundes und der Länder, 2024, dl-de/by-2-0 | verifiziert, eingebunden | Primärquelle Regionaltabelle Gebäude und Wohnungen (destatis, HTTP 200): Witzenhausen 5,09 €/m², LEQ 4,57 %, ETQ 54,40 %; Sekundärwerte bestätigt | Gemeindewerte und Vergleich der Nachbargemeinden |
| [Zensus 2022 Gitterzellen (100 m)](https://www.destatis.de/DE/Themen/Gesellschaft-Umwelt/Bevoelkerung/Zensus2022/_publikationen.html) (`zensus_gitter`) | Statistische Ämter des Bundes und der Länder | dl-de/by-2.0 | © Statistische Ämter des Bundes und der Länder, 2024, dl-de/by-2-0 | verifiziert, eingebunden | Downloads HTTP 200; 100-m-CSV mit GITTER_ID_100m, x/y_mp_100m (EPSG:3035) | Bestandsmiete und Eigentümerquote je Ortsbezirk als Näherung |
| [Wohngeld-Mietenstufe](https://www.gesetze-im-internet.de/wogv/) (`wohngeld`) | BMWSB / Wohngeldverordnung (Anlage) | amtliches Werk | – | verifiziert | gesetze-im-internet.de/wogv/anlage.html HTTP 200 (24.10.2026): Hessen, Witzenhausen, Stadt – I | datierter Kontext im Panel |
| [Angemessenheitsgrenzen KdU Werra-Meißner-Kreis](https://media.frag-den-staat.de/files/foi/97213/2018VerffentlichungVerwaltungsinterneHandlungsanweisung.pdf) (`kdu`) | Kreisausschuss WMK / Jobcenter | amtliches Dokument, Stand 01.05.2018 | – | veraltet, aktuellen Stand anfragen | nicht getestet | nur mit Stand; nicht als aktuelle Grenze darstellen |
| [Hessische Mieterschutzverordnung](https://verkuendung.hessen.de/sites/verkuendung.hessen.de/files/veroeffentlichungsplattform_plugin/published/1174/GVBl_2025_Nr_74_Regelungstext.pdf) (`mietpreisbremse`) | Land Hessen | amtliches Werk | – | verifiziert, eingebunden | GVBl. 2025 Nr. 74 (HTTP 200): Witzenhausen nicht genannt | datierter Kontext: nicht erfasst |

## Wohnen/Bevölkerung

| Quelle | Anbieter | Lizenz | Namensnennung | Status | Test | Nutzung |
|---|---|---|---|---|---|---|
| [Zensus2022_grid_final (FeatureServer)](https://services2.arcgis.com/jUpNdisbWqRpMo35/arcgis/rest/services/Zensus2022_grid_final/FeatureServer) (`zensus_esri_fs`) | Esri Deutschland (Drittanbieter) | DL-DE BY 2.0 (laut Esri-Item) | – | zu prüfen | nicht geprüft | Fallback (aus Ergänzungsregister 10/2026, eigene Prüfung bei Nutzung) |

## Wohnen/Boden

| Quelle | Anbieter | Lizenz | Namensnennung | Status | Test | Nutzung |
|---|---|---|---|---|---|---|
| [BORIS Hessen 2026 – INSPIRE Download Feed](https://www.geoportal.hessen.de/mapbender/php/mod_inspireDownloadFeed.php?id=c1afe4df-1290-42b3-9399-6bfd00652c13&type=SERVICE&generateFrom=wfs&wfsid=732) (`boris2026_feed`) | HVBG | DL-DE Zero 2.0 | – | widerlegt: kein Stichtag 2026 | Feed HTTP 200, verweist aber auf …/brw/2020/wfs (Stichtag 01.01.2020) | nicht genutzt |
| [BORIS Hessen 2026 – Geoportal-Kartenprojekt](https://www.geoportal.hessen.de/map?WMC=8243) (`boris2026_wmc`) | HVBG | DL-DE Zero 2.0 | – | verifiziert | nicht geprüft | Link/Viewer (aus Ergänzungsregister 10/2026, eigene Prüfung bei Nutzung) |
| [WFS HE BORIS 2024 als OGC API](https://www.geoportal.hessen.de/spatial-objects/864) (`boris2024_api`) | HVBG/Geoportal Hessen | DL-DE Zero 2.0 | – | verifiziert | nicht geprüft | Zeitvergleich (aus Ergänzungsregister 10/2026, eigene Prüfung bei Nutzung) |
| [WFS HE BORIS 2022 als OGC API](https://www.geoportal.hessen.de/spatial-objects/731) (`boris2022_api`) | HVBG/Geoportal Hessen | DL-DE Zero 2.0 | – | verifiziert | nicht geprüft | Zeitreihe (aus Ergänzungsregister 10/2026, eigene Prüfung bei Nutzung) |
| [Bestandsdatenausgabe Bodenrichtwerte (BRM 3.0.1)](https://hvbg.hessen.de/immobilienwertermittlung/bodenrichtwerte) (`boris_xml`) | HVBG | zu prüfen | – | zu prüfen | nicht geprüft | Vollattribute (aus Ergänzungsregister 10/2026, eigene Prüfung bei Nutzung) |
| [Immobilienmarktbericht 2023 GAA Homberg (Efze) – Pressemitteilung](https://hvbg.hessen.de/presse/immobilienmarktbericht-2023-online-verfuegbar-weniger-transaktionen) (`immo_wmk_2023`) | HVBG | zu prüfen | – | teilweise | nicht geprüft | Umsätze WMK (aus Ergänzungsregister 10/2026, eigene Prüfung bei Nutzung) |

## Wohnen/Recht

| Quelle | Anbieter | Lizenz | Namensnennung | Status | Test | Nutzung |
|---|---|---|---|---|---|---|
| [Entwurf Hessische Mieterschutzverordnung 2026](https://hessen.de/presse/mieterschutz-soll-auf-71-kommunen-wachsen) (`mischuv_2026`) | HMWVW | amtliche Pressemitteilung | – | verifiziert, eingebunden | Pressemitteilung 24.09.2026 (HTTP 200): Witzenhausen nicht in der Gebietskulisse | datierter Kontext: nicht erfasst |

## Wohnen/Soziales

| Quelle | Anbieter | Lizenz | Namensnennung | Status | Test | Nutzung |
|---|---|---|---|---|---|---|
| [KdU-Angemessenheitsrichtwerte WMK (Stand 01.01.2023)](https://harald-thome.de/files/pdf/KdU%20New/KdU%20Werra-Mei%C3%9Fner%20Kreis%20-%2001.01.2023.pdf) (`kdu_wmk_2023`) | Jobcenter Werra-Meißner (Kopie harald-thome.de) | keine offene Lizenz | – | nicht prüfbar | Kopie bei harald-thome.de HTTP 404 (23.10.2026) | keine Beträge im Stadtmonitor |
| [Jobcenter Werra-Meißner – Unterkunftskosten](https://jobcenter-werra-meissner.de/geldleistungen/unterkunftskosten/) (`kdu_jobcenter`) | Jobcenter Werra-Meißner | keine offene Lizenz | – | verlinkt | nicht geprüft | Auskunftsstelle im Panel |
| [Merkblatt Anmietung von Wohnraum](https://www.werra-meissner-kreis.de/fileadmin/01_Homepage_Kreisverwaltung/Fachbereiche_und_Einrichtungen/FB6_Soziales_und_Senioren/6.1_Sicherung_Aktivierung_der_Lebensgrundlagen/Merkblatt_KdU.pdf) (`kdu_merkblatt_wmk`) | Kreisausschuss WMK | keine offene Lizenz | – | teilweise | nicht geprüft | Verfahren (aus Ergänzungsregister 10/2026, eigene Prüfung bei Nutzung) |

## ÖPNV

| Quelle | Anbieter | Lizenz | Namensnennung | Status | Test | Nutzung |
|---|---|---|---|---|---|---|
| [Soll-Fahrplandaten NVV (GTFS)](https://mobilithek.info/offers/-1983289435982938851) (`nvv_gtfs`) | NVV via OpenData ÖPNV/Mobilithek | freie Nutzung/Open Data (genau zu prüfen) | – | teilweise | nicht lesbar ohne JS 23.10.2026 | Haltestellen/Linien (aus Ergänzungsregister 10/2026, eigene Prüfung bei Nutzung) |
| [OpenData ÖPNV – Datensätze](https://www.opendata-oepnv.de/ht/de/datensaetze) (`oepnv_portal`) | OpenData ÖPNV | je Datensatz | – | teilweise | nicht geprüft | Haltepositionen (aus Ergänzungsregister 10/2026, eigene Prüfung bei Nutzung) |
