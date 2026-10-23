# Offene Datenquellen für „wiz-stadtmonitor“ (Stadt Witzenhausen) – Recherchebericht, Stand Oktober 2026

Für die räumliche Verortung der Sitzungsinhalte reicht ein schlanker Kern aus vier frei nutzbaren Quellen: die Verwaltungsgrenzen Hessen (Gemarkungen/Fluren, dl-de/zero-2.0), die Hauskoordinaten bzw. ALKIS-Lagebezeichnungen der HVBG (dl-de/zero-2.0), der WFS „Bebauungspläne Stadt Witzenhausen“ und OpenStreetMap (ODbL). Darstellen lässt sich das mit basemap.de Web Vektor (CC BY 4.0).\[1\] Die Ortsbezirksgrenzen müssen aus den amtlichen Gemarkungen abgeleitet werden; einen eigenen amtlichen Ortsbezirks-Layer gibt es nach dieser Recherche nicht.

## TL;DR

- **Geobasisdaten Hessen sind seit 1. Februar 2022 Open Data unter dl-de/zero-2.0.** Verwaltungsgrenzen bis zur Gemarkung und Flur, ALKIS, Basis-DLM, Hauskoordinaten, DOP und DGM sind per WMS, WFS, OGC API Features oder Shapefile direkt und ohne Anmeldung abrufbar. Damit lassen sich Stadtgrenze, Gemarkungen (≈ Ortsbezirke) und Adressen für Witzenhausen vollständig und ohne Namensnennungspflicht abbilden.
- **Für die Bauleitplanung gibt es einen eigenen WFS der Stadt Witzenhausen** (Geltungsbereiche der B-Pläne und des FNP), aber mit eingeschränkter Nutzungsbedingung: „Die Nutzung ohne vertragliche Vereinbarung mit der Stadt Witzenhausen ist nur für nicht kommerzielle Zwecke erlaubt“. Für Umweltthemen (Überschwemmungsgebiete, Wasserschutzgebiete, Schutzgebiete) stellt das HLNUG WFS-Dienste unter CC BY 4.0 mit festem Quellenvermerk bereit.
- **Die Ortsbezirke entsprechen laut der Hauptsatzung (§ 6, zitiert nach Wikipedia) den Gemarkungen der eingegliederten ehemaligen Gemeinden.** Die Grenzen sollten daher aus dem Gemarkungs-Layer abgeleitet und mit der Hauptsatzung geprüft werden. OSM hat die Stadtgrenze (Relation 549412, admin_level=8), Ortsteil-Grenzrelationen ließen sich dagegen nicht belegen.

## Key Findings

1. **Hessisches Open-Data-Recht und Lizenz.** Laut HZD stehen „seit dem 1. Februar 2022 … Geodaten vom Land Hessen zur freien Nutzung online zur Verfügung“.\[2\] Grundlage ist § 16 HVGG: „Jede Nutzung der Geobasisdaten und zugehörigen Metadaten ist ohne Einschränkung oder Bedingung erlaubt.“\[3\] Die Metadaten der Dienste nennen durchgängig „Lizenz: dl-zero-de/2.0 – Datenlizenz Deutschland – Zero – Version 2.0“.\[4\]\[5\] Eine Namensnennung ist rechtlich nicht vorgeschrieben, wird hier aber empfohlen.
2. **Verwaltungsgrenzen (amtlich, bis Flur).** Die ZKFG/GDI-Hessen betreibt den Dienst „Verwaltungsgrenzen Hessen“ mit den Collections Fluren, Gemarkungen, Gemeinden, Landkreise, Regierungsbezirke und Land. Er ist als OGC API Features und als WFS (`https://basisdienste.geoportal.hessen.de/ogc/borders?`) erreichbar.\[6\] Quelle ist das Shapefile `https://gds-srv.hessen.de/atomfeed/DigVGr-epsg25832-shp.zip`, das die Metadaten mit Stand 27.02.2024 führen.\[7\]
3. **Adressen.** Die Hauskoordinaten Hessen (ETRS89/UTM32, Textformat, Download im Downloadcenter) sind auch als INSPIRE-WFS „Adressen Hauskoordinaten“ (dl-de/zero-2.0) verfügbar.\[8\]\[9\] Der Suchdienst `ogc-free-data.ows` bietet zusätzlich die Layer WFS-lage (Straße und Hausnummer, täglich aktualisiert) und WFS-hako (halbjährlich).\[10\] Für die Geokodierung von Straßennamen in Tagesordnungen ist das die zentrale amtliche Quelle.
4. **Bauleitplanung.** Der WFS der Stadt Witzenhausen liefert den Featuretype `lyr:witzenhausen_bplaene_umringe_feature` (EPSG:25832/4326, BBOX 9.736–9.922 °E / 51.289–51.395 °N) und `lyr:witzenhausen_fplaene_umringe_feature` (FNP).\[11\]\[12\] Die Geltungsbereiche enthalten Verknüpfungen zu Plänen und Dokumenten.\[13\] Die Lizenz ist nicht offen (siehe oben).\[14\]
5. **Umwelt.** Das HLNUG stellt ArcGIS-WFS unter `geodienste-umwelt.hessen.de` bereit: gesetzliche Überschwemmungsgebiete HQ100 und HWRM-Überflutungsflächen HQ10/HQ100/HQextrem, Trinkwasser- und Heilquellenschutzgebiete (TWS_HQS_ALK, TWS_HQS_TK25) sowie das Gewässernetz, jeweils unter CC BY 4.0 mit vorgegebenem Quellenvermerk.\[15\]\[16\]\[17\] Die Schutzgebiete (FFH, VSG, NSG, LSG, Naturparke) kommen als INSPIRE-WFS vom HMLU.\[18\]
6. **Statistik.** Die Stadt hatte laut Zensus 2022 15.162 Einwohner, die Fortschreibung zum 31.12.2024 ergibt 15.132.\[19\]\[20\] Gitterzellen (100 m/1 km/10 km) gibt es als CSV-ZIP unter dl-de/by-2.0.\[21\]\[22\] Bevölkerungszahlen nach Ortsteilen veröffentlicht die Stadt nur als Fließtext (Stand 09/2022), nicht als maschinenlesbaren Datensatz.\[23\]\[24\]
7. **Wahlen.** Die Kommunalwahl vom 15.03.2026 ist im votemanager der ekom21 veröffentlicht: 21 allgemeine Wahlbezirke und 5 Briefwahlbezirke, Trend Stadtverordnetenversammlung SPD 25,69 %, CDU 23,57 %, Grüne 15,88 %.\[25\]\[26\]\[27\]
8. **ÖPNV.** NVV-Soll-Fahrplandaten (GTFS) und der DELFI-Datensatz liegen auf opendata-oepnv.de.\[28\] Für das zentrale Haltestellenverzeichnis (zHV, CC BY) ist eine Registrierung nötig.\[29\]\[30\] Bei den NVV-GTFS-Daten nennt der Mobilithek-Eintrag „Soll-Fahrplandaten NVV“ als Nutzungsbedingungen nur „Lizenz, freie Nutzung/Open Data“, ohne konkrete Lizenzbezeichnung. Nach einer Angabe von 2020 galt CC-BY-NC-ND-4.0; vor der Nutzung ist das auf opendata-oepnv.de nachzuprüfen.
9. **Hintergrundkarte.** basemap.de Web Vektor (CC BY 4.0, EPSG:3857, monatlich aktualisiert) darf laut BKG ausdrücklich in eigene Webseiten eingebunden werden.\[31\]\[32\]\[33\] Die Style-JSON-URLs sind öffentlich, der Dienst eignet sich daher für GitHub Pages.

## (a) Übersichtstabelle der Quellen

Legende Priorität: **H** = hoch (direkte Verortung von TOPs), **M** = mittel (Kontextlayer), **N** = niedrig (Ergänzung). „Prüfen“ heißt: In dieser Recherche nicht vollständig verifiziert.

### 1. Verwaltungsgrenzen

| Prio | Name | Anbieter | Dienst-/Download-URL, Layer | Format | KBS | Abdeckung / Ortsteilebene | Stand | Lizenz | Zugang | Nutzen |
|---|---|---|---|---|---|---|---|---|---|---|
| H | Verwaltungsgrenzen Hessen (Gemarkungen, Fluren, Gemeinden …) | ZKFG / GDI-Hessen (HVBG) | OGC API: `https://www.geoportal.hessen.de/spatial-objects/885` – Collections `borders:gemarkungenHE_wfs`, `borders:flurenHE_wfs`, `borders:gemeindenHE_wfs`; WFS: `https://basisdienste.geoportal.hessen.de/ogc/borders?` | GeoJSON (OGC API), GML (WFS) | EPSG:25832 (WFS), WGS84 (OGC API GeoJSON – prüfen) | Hessen komplett, inkl. Witzenhausen; Gemarkungsebene ≈ Ortsbezirke | Layer-Aktualität 08.06.2026 | dl-de/zero-2.0 | frei, ohne Anmeldung | Stadtgrenze, Ortsbezirksflächen (aus Gemarkungen), Flur-Zuordnung von Flurstücksangaben |
| H | Digitale Verwaltungsgrenzen (Shapefile) | HVBG | `https://gds-srv.hessen.de/atomfeed/DigVGr-epsg25832-shp.zip` | Shapefile (ZIP) | EPSG:25832 | Hessen komplett | Datei vom 27.02.2024 (laut Metadaten) | dl-de/zero-2.0 | Direktdownload | Offline-Grundlage für Build-Skript |
| M | WMS HE Verwaltungseinheiten | HVBG | `https://www.gds-srv.hessen.de/cgi-bin/verweinh/he-verwaltungseinheiten.ows?language=ger&VERSION=1.3.0&REQUEST=GetCapabilities&SERVICE=WMS` | WMS (Bild) | mehrere | Land bis Gemarkung | laufend | dl-de/zero-2.0 | frei | Nur Darstellung |
| M | VG250 (Gemeindegrenzen) | BKG | WFS `https://sgx.geodatenzentrum.de/wfs_vg250`, Typename `vg250_gem`; WMS `https://sgx.geodatenzentrum.de/wms_vg250` | GML/Shape | EPSG:25832 u. a. | Deutschland; nur Gemeindeebene, keine Ortsteile | Stand 01.01.2025 | dl-de/by-2.0 | frei | Gemeindegrenze, Nachbargemeinden, ARS-Schlüssel |
| M | OSM-Grenzrelation Witzenhausen | OpenStreetMap | Relation 549412 (admin_level=8, AGS 06636016, wikidata=Q564827) | OSM/GeoJSON via Overpass | WGS84 | Stadt; Ortsteilrelationen nicht belegt | laufend | ODbL 1.0 | Overpass-API | Fallback, Abgleich |

### 2. Adressen und Straßen

| Prio | Name | Anbieter | URL / Layer | Format | KBS | Abdeckung | Stand | Lizenz | Zugang | Nutzen |
|---|---|---|---|---|---|---|---|---|---|---|
| H | Hauskoordinaten Hessen | HVBG | Download im Downloadcenter `https://gds.hessen.de/INTERSHOP/web/WFS/HLBG-Geodaten-Site/de_DE/-/EUR/ViewDownloadcenter-Start` (Direkt-URL der Datei: prüfen); INSPIRE-WFS `https://inspire-hessen.de/ows/services/org.2.19698713-4b13-4938-a9db-96bfdc996451_wfs?` | TXT (hessenweit), GML | ETRS89/UTM32 (EPSG:25832) | Hessen; Gemeinde, Straße, Hausnummer; ohne PLZ/postalischen Ort | jährlich/halbjährlich | dl-de/zero-2.0 | frei | Geokodierung von Adressen in TOPs |
| H | Suchdienst Lage/Hauskoordinaten | HVBG | `https://www.gds-srv.hessen.de/cgi-bin/lika-services/ogc-free-data.ows?` – Layer WFS-flst, WFS-lage, WFS-hako (WFS 1.1.0) | GML | EPSG:25832 | Hessen | lage: täglich; hako: halbjährlich | dl-de/zero-2.0 | frei | Straßennamen → Koordinate (auch ohne Hausnummer); Flurstückssuche |
| H | WFS HE ALKIS Vereinfacht | HVBG | `https://www.gds.hessen.de/wfs2/aaa-suite/cgi-bin/alkis/vereinf/wfs?SERVICE=WFS&VERSION=2.0.0&REQUEST=GetCapabilities` | GML | EPSG:25832 | Flurstücke, Gebäude, Tatsächliche Nutzung, Verwaltungseinheiten, Katasterbezirke | laufend | dl-de/zero-2.0 | frei | Flurstücksangaben aus TOPs (z. B. „Gemarkung X, Flur Y, Flurstück Z“) verorten |
| M | WFS HE Basis-DLM | HVBG | `https://www.gds.hessen.de/wfs2/aaa-suite/cgi-bin/atkis-bdlm/sf/wfs?SERVICE=WFS&VERSION=2.0.0&REQUEST=GetCapabilities` | GML | EPSG:25832 | Hessen; Straßenachsen, Gewässer, Siedlung | laufend | dl-de/zero-2.0 | frei | Straßengeometrien mit Namen |
| H | OSM-Straßen/POI | OSM-Mitwirkende | Overpass-API (siehe Teil b); Hessen-Extrakt Geofabrik (URL nicht verifiziert) | OSM/PBF/GeoJSON | WGS84 | vollständig | laufend | ODbL 1.0 | frei | Straßennamen mit Linien, Sitzungsorte (DGH), Schulen, Feuerwehr |

### 3. Bauleitplanung

| Prio | Name | Anbieter | URL / Layer | Format | KBS | Abdeckung | Stand | Lizenz | Zugang | Nutzen |
|---|---|---|---|---|---|---|---|---|---|---|
| H | Bebauungspläne Stadt Witzenhausen | Magistrat der Stadt Witzenhausen (über GDI Nordosthessen) | WFS `https://www.gdi-nordosthessen.de/ws/wfs/ds_plu_bplan_whs/ows.wfs?`, Featuretype `lyr:witzenhausen_bplaene_umringe_feature`; Proxy: `https://www.geoportal.hessen.de/mapbender/php/wfs.php?INSPIRE=1&FEATURETYPE_ID=1245&request=GetCapabilities&VERSION=1.1.0&SERVICE=WFS`; OGC API `https://www.geoportal.hessen.de/spatial-objects/337` | GML 3.2.1/3.1.1/2.1.2 | EPSG:25832, EPSG:4326 | Stadtgebiet (BBOX 9.736/51.289–9.922/51.395) | WMS-Layer-Aktualität 20.03.2026 | **nicht offen**: nur nicht kommerziell ohne Vertrag | frei abrufbar | TOPs zu B-Plan-Verfahren verorten, Link auf Plandokumente |
| H | Flächennutzungspläne Stadt Witzenhausen | Magistrat der Stadt Witzenhausen | WFS über Geoportal: `https://www.geoportal.hessen.de/mapbender/php/wfs.php?INSPIRE=1&FEATURETYPE_ID=4140&request=GetCapabilities&VERSION=2.0.0&SERVICE=WFS`, Featuretype `lyr:witzenhausen_fplaene_umringe_feature` | GML | EPSG:25832, EPSG:4326 | Stadtgebiet | prüfen | prüfen (vermutlich wie B-Pläne) | frei abrufbar | FNP-Änderungsverfahren |
| M | Bebauungspläne Werra-Meißner-Kreis | Kreisausschuss WMK | WMS-Layer `vs_plu_LKWM_BPlaene` (Geoportal-Layer-ID 47056) | WMS | EPSG:4258, CRS:84 u. a. | 14 Kommunen des Kreises | 19.01.2024 | prüfen | frei | Nachbarkommunen, Abgleich |
| N | Geoportal Nordhessen (B-Plan-Übersicht) | GDI Nordhessen | `https://www.geoportalnordhessen.de/de/bplaene-werra-meissner.html` | Web-Viewer | – | WMK | – | – | Viewer | Manuelle Prüfung |
| N | Regionalplan Nordhessen | RP Kassel | nicht recherchiert | – | – | – | – | – | – | Prüfbedarf |

### 4. Umwelt und Naturschutz

| Prio | Name | Anbieter | URL / Layer | Format | KBS | Abdeckung | Stand | Lizenz | Zugang | Nutzen |
|---|---|---|---|---|---|---|---|---|---|---|
| M | Gebiete naturbedingter Risiken (Überschwemmungsgebiete) | HLNUG | WFS `https://geodienste-umwelt.hessen.de/arcgis/services/inspire/gebiete_naturbedingter_risiken/MapServer/WFSServer?`; Layer `Ueberschwemmungsgebiete_HQ100_nach_HWG`, `Abflussgebiete_HQ100_nach_HWG`, `Hochwasser_mit_hoher_Wahrscheinlichkeit`, `…_mittlerer_…`, `…_niedriger_…`; OGC API `https://www.geoportal.hessen.de/spatial-objects/264`; Shape-ZIP über `https://www.hlnug.de/themen/geografische-informationssysteme/geodienste/wasser` | GML32, GeoJSON (laut Capabilities) | EPSG:25832 | Hessen inkl. Werra/Gelster | laufend | CC BY 4.0 | frei | TOPs zu Hochwasserschutz, Bauen im ÜSG |
| M | Trinkwasser- und Heilquellenschutzgebiete | HLNUG | WFS `https://geodienste-umwelt.hessen.de/arcgis/services/inspire/bewirtschaftungsgebiete/MapServer/WFSServer?`; Layer `inspire_bewirtschaftungsgebiete:TWS_HQS_ALK`, `…:TWS_HQS_TK25`; auch auf opendata.hessen.de | GML/ATOM | EPSG:25832 | Hessen | Metadaten 09.10.2026 | CC BY 4.0 | frei | Trinkwasserthemen; nicht rechtsverbindlich |
| M | Schutzgebiete Hessen (FFH, VSG, NSG, LSG, Naturparke, NNM, BR) | HMLU (Natureg) | WFS `https://geodienste-umwelt.hessen.de/arcgis/services/inspire/schutzgebiete/MapServer/WFSServer?`; OGC API `https://www.geoportal.hessen.de/spatial-objects/266`; Shape-Download im Natureg-Viewer | GML, Shape | EPSG:25832 | Hessen | laufend | prüfen (auf der OGC-API-Seite nicht angezeigt) | frei | Naturschutzbelange in TOPs, Naturpark Frau-Holle-Land |
| N | Gewässernetz Hessen (DLM25, Kilometrierung) | HLNUG | WFS `https://geodienste-umwelt.hessen.de/arcgis/services/inspire/gewaessernetz/MapServer/WFSServer?`; OGC API `…/spatial-objects/262` | GML | EPSG:25832 | Hessen | laufend | Quellenvermerk HLNUG (Lizenz prüfen) | frei | Bäche/Gräben in TOPs |
| N | HWRM-Viewer, Lärmkartierung | HLNUG/Land | `https://hwrm.hessen.de/`; Lärmkartierung als Themenkarte im Geoportal Nordhessen | Viewer | – | Hessen | – | – | Viewer | Manuelle Recherche |

### 5. Infrastruktur und Daseinsvorsorge

| Prio | Name | Anbieter | URL | Format | KBS | Abdeckung | Stand | Lizenz | Zugang | Nutzen |
|---|---|---|---|---|---|---|---|---|---|---|
| H | Sitzungsorte, Schulen, Kitas, Feuerwehr, DGH, Friedhöfe, Sportplätze | OSM | Overpass-Abfrage (Teil b) | GeoJSON | WGS84 | Vollständigkeit prüfen | laufend | ODbL 1.0 | frei | Sitzungsorte der Ortsbeiräte verorten; POIs in TOPs |
| M | Soll-Fahrplandaten NVV (GTFS) | NVV über opendata-oepnv.de | `https://www.opendata-oepnv.de/ht/de/datensaetze` (Datensatz „Soll-Fahrplandaten NVV“; Direkt-URL prüfen) | GTFS (ZIP) | WGS84 | NVV-Gebiet inkl. Witzenhausen | laufend | Mobilithek: „Lizenz, freie Nutzung/Open Data“, ohne Lizenzbezeichnung; 2020: CC-BY-NC-ND-4.0 für GTFS – prüfen | ggf. Registrierung | Haltestellen, Linien |
| M | DELFI GTFS / zHV Haltestellen | DELFI e. V. | opendata-oepnv.de (DELFI-Organisation); zHV-Webanwendung `https://zhv.wvigmbh.de/` | GTFS, CSV | WGS84 | Deutschland | zHV: 19.10.2026 | CC BY | Registrierung erforderlich | Haltestellen mit DHID |
| N | Ladesäulen, Breitband | BNetzA / Bund | nicht recherchiert | – | – | – | – | – | – | Prüfbedarf |

### 6. Statistik und Wahlen

| Prio | Name | Anbieter | URL | Format | Abdeckung | Stand | Lizenz | Zugang | Nutzen |
|---|---|---|---|---|---|---|---|---|---|
| M | Zensus 2022 Gitterzellen | Statistische Ämter des Bundes und der Länder | `https://www.destatis.de/DE/Themen/Gesellschaft-Umwelt/Bevoelkerung/Zensus2022/_publikationen.html` (z. B. „Bevölkerungszahlen in Gitterzellen“, ZIP 18 MB; Direkt-URL prüfen) | CSV in ZIP (10 km/1 km/100 m) | Deutschland; über Gitter auf Ortsteile aggregierbar | Stichtag 15.05.2022 | dl-de/by-2.0 | Direktdownload | Einwohner je Ortsbezirk (Gitter × Gemarkung) |
| M | Gemeindedatenblatt Witzenhausen | Hessen Agentur (Gemeindelexikon) | `https://www.hessen-gemeindelexikon.de/gemeindelexikon_PDF/636016.pdf` | PDF | Gemeinde | 31.12.2024 | prüfen | frei | Kennzahlen, Prognose bis 2040 |
| M | Einwohner Stadtteile | Stadt Witzenhausen | `https://www.witzenhausen.eu/lage/` | HTML-Text | Ortsteile | 09/2022 | keine Angabe | frei | Einwohner je Ortsteil (manuell übernehmen) |
| M | Kommunalwahl 15.03.2026 | Stadt / ekom21 votemanager | `https://votemanager-ks.ekom21cdn.de/2026-03-15/06636016/praesentation/index.html` | HTML; Open-Data-Exporte prüfen | 21 Wahlbezirke + 5 Briefwahlbezirke | 2026 | keine Angabe | frei | Ergebnisse je Wahlbezirk; Wahlbezirk ↔ Ortsteil prüfen |
| N | Haushalt der Stadt | Stadt Witzenhausen | Rubrik „Haushalt“ auf witzenhausen.eu | PDF | Stadt | – | – | frei | Haushaltsbezüge in TOPs |

### 7. Weitere Portale und Referenzdaten

| Prio | Name | Anbieter | URL | Format | Lizenz | Nutzen |
|---|---|---|---|---|---|---|
| H | Wikidata (Stadt und 16 Ortsteile) | Wikimedia | `https://www.wikidata.org/wiki/Q564827` u. a. (siehe Teil b) | JSON/SPARQL | CC0 | Stabile IDs, Koordinaten, Normalisierung der Ortsteilnamen |
| M | opendata.hessen.de | HMDI | `https://opendata.hessen.de/` | DCAT/CKAN, SPARQL | je Datensatz | Landesportal nach HODaG, gestartet am 03.11.2025 laut Technologieland Hessen (Hessen Trade & Invest); reines Metadatenportal ohne eigene Datenspeicherung; Weiterleitung an GovData |
| M | Geoportal Hessen „Offene Geodaten“ (OGC API) | GDI-Hessen | `https://www.geoportal.hessen.de/spatial-objects/` | OGC API Features (GeoJSON) | je Datensatz | Einheitlicher GeoJSON-Zugang zu vielen WFS |
| N | GovData, Mobilithek, Uni Kassel, DenkXweb, LAGIS | diverse | nicht recherchiert | – | – | Prüfbedarf |

### 8. Hintergrundkarten

| Prio | Name | Anbieter | URL | Format | KBS | Lizenz | Eignung GitHub Pages |
|---|---|---|---|---|---|---|---|
| H | basemap.de Web Vektor (Farbe/Grau/Relief) | BKG / AdV | Styles: `https://sgx.geodatenzentrum.de/gdz_basemapde_vektor/styles/bm_web_col.json`, `…/bm_web_gry.json`, `…/bm_web_top.json` | Vector Tiles (PBF), Style-JSON | EPSG:3857 | CC BY 4.0 | ja – Einbindung in eigene Webseiten laut BKG erlaubt; MapLibre GL JS |
| M | basemap.de Web Raster (WMS/WMTS) | BKG / ZSGT | über basemap.de | WMS/WMTS | mehrere | CC BY 4.0 | ja, für Leaflet |
| M | Hessen DOP (WMS/WMTS) | HVBG | WMS `https://www.gds-srv.hessen.de/cgi-bin/lika-services/ogc-free-images.ows?…` (Layer `he_dop_rgb`; im OSM-Wiki als `he_dop20_rgb` – Capabilities prüfen); WMTS `https://www.gds-srv.hessen.de/wmts-dop/wmts/1.0.0/WMTSCapabilities.xml` | WMS/WMTS | u. a. EPSG:25832 | dl-de/zero-2.0 | technisch ja; Last und Verfügbarkeit prüfen |
| M | Hessen Karten-WMS (ALK, DTK, PG, Hauskoordinaten) | HVBG | `https://www.gds-srv.hessen.de/cgi-bin/lika-services/ogc-free-maps.ows?language=ger&VERSION=1.3.0&REQUEST=GetCapabilities&SERVICE=WMS`; Layer `he_alk`, `he_alk_grau`, `he_dtk25`, `he_pg`, `he_hako` | WMS | mehrere | dl-de/zero-2.0 | ja, als Overlay (z. B. Liegenschaftskarte bei Zoom ≥ 16) |
| N | OSM-Standardkacheln | OSMF | `https://tile.openstreetmap.org/{z}/{x}/{y}.png` | Raster | EPSG:3857 | ODbL / Tile Usage Policy | nur eingeschränkt – laut OSMF-Tile-Usage-Policy Pflicht: sichtbare Attribution, gültiger Referer, Caching „at least 7 days“; Bulk-Download verboten, „Offline use is not permitted“, „there is no SLA or guarantee“, Sperrung ohne Vorwarnung möglich |

## (b) Abrufbeispiele für die hoch priorisierten Quellen

Die BBOX der Stadt laut WFS-Capabilities der B-Pläne lautet in WGS84: lon 9.736–9.922, lat 51.289–51.395.\[11\] Zur Sicherheit wird unten etwas gepuffert. Die UTM-Werte sind **näherungsweise gerechnet** und sollten nach dem ersten Abruf an der realen Stadtgrenze nachjustiert werden.

```bash
# Gemeinsame Konstanten
BBOX_WGS84="9.72,51.28,9.94,51.41"                 # lon_min,lat_min,lon_max,lat_max
BBOX_UTM32="549000,5680000,566000,5698000"         # x_min,y_min,x_max,y_max (EPSG:25832, Näherung)
```

**1. Gemarkungen (Ortsbezirke) und Gemeindegrenze – OGC API Features (GeoJSON)**

```bash
# Collections laut Geoportal: borders:gemarkungenHE_wfs, borders:gemeindenHE_wfs, borders:flurenHE_wfs
curl -L "https://www.geoportal.hessen.de/spatial-objects/885/collections/borders:gemarkungenHE_wfs/items?f=json&bbox=${BBOX_WGS84}&limit=500" -o gemarkungen_raw.geojson
curl -L "https://www.geoportal.hessen.de/spatial-objects/885/collections/borders:gemeindenHE_wfs/items?f=json&bbox=${BBOX_WGS84}&limit=50" -o gemeinden_raw.geojson
# Danach lokal auf Gemeinde Witzenhausen filtern (Attributnamen nach erstem Abruf prüfen, z. B. Gemeindeschlüssel 06636016)
```
Hinweis: `f=json`, `bbox` und `limit` sind Standardparameter von OGC API Features. Die HTML-Variante `?&f=html` ist im Geoportal belegt,\[6\] die JSON-Variante sollte einmal getestet werden.

**2. Dasselbe per WFS 2.0 (GML, EPSG:25832)**

```bash
curl -L "https://basisdienste.geoportal.hessen.de/ogc/borders?SERVICE=WFS&VERSION=2.0.0&REQUEST=GetCapabilities" -o borders_caps.xml
curl -L "https://basisdienste.geoportal.hessen.de/ogc/borders?SERVICE=WFS&VERSION=2.0.0&REQUEST=GetFeature&TYPENAMES=borders:gemarkungenHE_wfs&SRSNAME=EPSG:25832&BBOX=${BBOX_UTM32},EPSG:25832" -o gemarkungen.gml
ogr2ogr -f GeoJSON -t_srs EPSG:4326 gemarkungen.geojson gemarkungen.gml
```

**3. Shapefile-Komplettdownload (Fallback, offline-fähig)**

```bash
curl -L "https://gds-srv.hessen.de/atomfeed/DigVGr-epsg25832-shp.zip" -o DigVGr.zip && unzip -o DigVGr.zip -d digvgr
# Layer mit Gemarkungen auswählen, auf Witzenhausen clippen:
ogr2ogr -f GeoJSON -t_srs EPSG:4326 -spat 549000 5680000 566000 5698000 gemarkungen_wiz.geojson digvgr/<Gemarkungs-Layer>.shp
```

**4. Bebauungspläne und FNP Witzenhausen (WFS)**

```bash
curl -L "https://www.gdi-nordosthessen.de/ws/wfs/ds_plu_bplan_whs/ows.wfs?SERVICE=WFS&VERSION=2.0.0&REQUEST=GetFeature&TYPENAMES=lyr:witzenhausen_bplaene_umringe_feature&SRSNAME=EPSG:4326" -o bplaene.gml
ogr2ogr -f GeoJSON bplaene.geojson bplaene.gml
# FNP über den Geoportal-Proxy (Capabilities zuerst prüfen):
curl -L "https://www.geoportal.hessen.de/mapbender/php/wfs.php?INSPIRE=1&FEATURETYPE_ID=4140&SERVICE=WFS&VERSION=2.0.0&REQUEST=GetFeature&TYPENAMES=lyr:witzenhausen_fplaene_umringe_feature" -o fplaene.gml
```

**5. Hauskoordinaten und Lagebezeichnungen**

```bash
# Capabilities des Suchdienstes (Layernamen WFS-lage / WFS-hako dort verifizieren):
curl -L "https://www.gds-srv.hessen.de/cgi-bin/lika-services/ogc-free-data.ows?SERVICE=WFS&VERSION=1.1.0&REQUEST=GetCapabilities" -o hako_caps.xml
# INSPIRE-Adressen-WFS:
curl -L "https://inspire-hessen.de/ows/services/org.2.19698713-4b13-4938-a9db-96bfdc996451_wfs?SERVICE=WFS&VERSION=2.0.0&REQUEST=GetCapabilities" -o inspire_ad_caps.xml
# Empfehlung: hessenweite TXT-Datei einmalig aus dem Downloadcenter laden und lokal auf Gemeindeschlüssel 06636016 filtern;
# daraus ein Straßenverzeichnis (Straße → Ortsteil per Punkt-in-Gemarkung) für die Geokodierung der TOPs erzeugen.
```

**6. ALKIS vereinfacht (Flurstücke zu Flurstücksangaben in TOPs)**

```bash
curl -L "https://www.gds.hessen.de/wfs2/aaa-suite/cgi-bin/alkis/vereinf/wfs?SERVICE=WFS&VERSION=2.0.0&REQUEST=GetCapabilities" -o alkis_caps.xml
# GetFeature nur kleinräumig (Feature-Limits beachten), z. B. per BBOX um ein Plangebiet; Typename aus den Capabilities übernehmen.
```

**7. HLNUG Überschwemmungsgebiete und Wasserschutzgebiete**

```bash
curl -L "https://geodienste-umwelt.hessen.de/arcgis/services/inspire/gebiete_naturbedingter_risiken/MapServer/WFSServer?SERVICE=WFS&VERSION=2.0.0&REQUEST=GetFeature&TYPENAMES=inspire_gebiete_naturbedingter_risiken:Ueberschwemmungsgebiete_HQ100_nach_HWG&BBOX=${BBOX_UTM32},urn:ogc:def:crs:EPSG::25832&OUTPUTFORMAT=GEOJSON" -o uesg_hq100.geojson
curl -L "https://geodienste-umwelt.hessen.de/arcgis/services/inspire/bewirtschaftungsgebiete/MapServer/WFSServer?SERVICE=WFS&VERSION=2.0.0&REQUEST=GetFeature&TYPENAMES=inspire_bewirtschaftungsgebiete:TWS_HQS_ALK&BBOX=${BBOX_UTM32},urn:ogc:def:crs:EPSG::25832&OUTPUTFORMAT=GEOJSON" -o tws.geojson
```
Hinweis des HLNUG: Die Zahl der pro GetFeature zurückgelieferten Features ist begrenzt.\[15\] Bei großen BBOXen muss gekachelt oder die Shape-ZIP genutzt werden.

**8. OSM per Overpass (Stadtgrenze, mögliche Ortsteilgrenzen, Sitzungsorte, POIs)**

```
[out:json][timeout:120];
area(id:3600549412)->.wiz;            // Relation 549412 = Stadt Witzenhausen
(
  relation(area.wiz)["boundary"="administrative"]["admin_level"~"^(9|10)$"];
  node(area.wiz)["place"~"village|hamlet|suburb|town"];
  nwr(area.wiz)["amenity"~"community_centre|townhall|school|kindergarten|fire_station|grave_yard"];
  nwr(area.wiz)["landuse"="cemetery"];
  nwr(area.wiz)["leisure"~"sports_centre|pitch|stadium"];
  nwr(area.wiz)["railway"="station"];
  nwr(area.wiz)["highway"="bus_stop"];
  way(area.wiz)["highway"]["name"];
);
out tags center;
```
Absenden mit `curl -X POST --data-urlencode data@query.overpassql https://overpass-api.de/api/interpreter` (Fair-Use-Regeln des Overpass-Betreibers beachten, Ergebnis cachen statt bei jedem Seitenaufruf abfragen).

**9. Wikidata (Stadt und Ortsteile)**

```sparql
SELECT ?item ?itemLabel ?coord ?pop WHERE {
  ?item wdt:P131 wd:Q564827 .
  OPTIONAL { ?item wdt:P625 ?coord . }
  OPTIONAL { ?item wdt:P1082 ?pop . }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "de". }
}
```
Endpunkt: `https://query.wikidata.org/sparql?format=json&query=…`. Q-IDs (aus Wikidata-Seiten, nicht per SPARQL gegengeprüft): Witzenhausen Q564827; Albshausen Q1660176; Berlepsch-Ellerode(-Hübenthal) Q15107510; Blickershausen Q884011; Dohrenbach Q1234893; Ellingerode Q1332184; Ermschwerd Q1292400; Gertenbach Q1433972; Hubenrode Q1632999; Hundelshausen Q1637452; Kleinalmerode Q1746285; Neuseesen Q1745254; Roßbach Q1753104; Unterrieden Q2498818; Wendershausen Q2559136; Werleshausen Q2560623; Ziegenhagen Q198786.\[34\]\[35\]\[36\]\[37\]\[38\]\[39\]\[40\]\[41\]\[42\]\[43\]\[44\]\[45\]\[46\]\[47\]\[48\]\[49\]\[50\] Weitere Wohnplätze mit eigenem Datensatz, aber ohne eigenen Ortsbezirk: Hübenthal Q1652053, Freudenthal Q21036575.\[51\]\[52\]

**10. Hintergrundkarte (MapLibre GL JS)**

```js
const map = new maplibregl.Map({
  container: 'map',
  style: 'https://sgx.geodatenzentrum.de/gdz_basemapde_vektor/styles/bm_web_col.json',
  center: [9.857, 51.341], zoom: 11
});
```

## (c) Lizenzübersicht und Attributionstexte

| Quelle | Lizenz | Pflicht | Empfohlener Attributionstext (Footer / Datendatei) |
|---|---|---|---|
| HVBG-Geobasisdaten (Verwaltungsgrenzen, ALKIS, Basis-DLM, Hauskoordinaten, DOP, WMS) | dl-de/zero-2.0 | keine Namensnennung erforderlich | „Geobasisdaten: © Hessische Verwaltung für Bodenmanagement und Geoinformation (HVBG), Datenlizenz Deutschland – Zero – Version 2.0 (https://www.govdata.de/dl-de/zero-2-0)“ (freiwillig, aus Transparenzgründen empfohlen) |
| BKG VG250 | dl-de/by-2.0 | ja | „© BKG (Jahr des letzten Datenbezugs) dl-de/by-2-0, Datenquellen: https://sgx.geodatenzentrum.de/web_public/gdz/datenquellen/datenquellen_vg_nuts.pdf“. Auf Webseiten sind „BKG“ mit https://www.bkg.bund.de und „dl-de/by-2-0“ mit https://www.govdata.de/dl-de/by-2-0 zu verlinken. |
| basemap.de Web Vektor/Raster | CC BY 4.0 | ja | „© basemap.de / BKG (Jahr) \| Datenquellen: © GeoBasis-DE“ (so im Style-JSON hinterlegt; MapLibre zeigt das automatisch an)\[53\] |
| HLNUG (Überschwemmungsgebiete, Wasserschutzgebiete, Gewässernetz) | CC BY 4.0 | ja | Dienst: „Hessisches Landesamt für Naturschutz, Umwelt und Geologie (HLNUG)“; Daten: „Darstellung auf der Grundlage von Daten des Hessischen Landesamtes für Naturschutz, Umwelt und Geologie (HLNUG)“\[16\]\[54\] |
| Schutzgebiete (HMLU/Natureg) | prüfen | vorsorglich ja | „Schutzgebiete: Hessisches Ministerium für Landwirtschaft und Umwelt, Weinbau, Forsten, Jagd und Heimat (NATUREG)“ |
| Bebauungspläne/FNP Stadt Witzenhausen | proprietär, nur nicht kommerziell ohne Vertrag | ja, Nutzungsbedingungen | „Geltungsbereiche Bauleitplanung: Magistrat der Stadt Witzenhausen (Nutzung nur zu nicht kommerziellen Zwecken)“ – vor Veröffentlichung schriftliche Bestätigung der Stadt einholen |
| Zensus 2022 | dl-de/by-2.0 | ja | „© Statistische Ämter des Bundes und der Länder, (Jahr); Gittergeometrien: © GeoBasis-DE / BKG (Jahr); dl-de/by-2-0“\[21\] |
| OpenStreetMap | ODbL 1.0 | ja; abgeleitete Datenbanken unter ODbL | „© OpenStreetMap-Mitwirkende, ODbL (https://www.openstreetmap.org/copyright)“ |
| Wikidata | CC0 | keine | „Daten: Wikidata (CC0)“ freiwillig |
| DELFI zHV / GTFS | CC BY | ja | „Haltestellendaten: DELFI e. V.“\[29\] |
| NVV GTFS | Mobilithek: „Lizenz, freie Nutzung/Open Data“ ohne Lizenzbezeichnung; 2020: CC-BY-NC-ND-4.0 – auf opendata-oepnv.de prüfen | ja | „Fahrplandaten: Nordhessischer VerkehrsVerbund (NVV)“; ND-Klausel kann die Umwandlung in eigene Formate ausschließen – vor Nutzung klären |

Praxis für Datendateien: In jede erzeugte GeoJSON-Datei ein Top-Level-Feld `"attribution"` und `"license"` schreiben und eine `DATA_SOURCES.md` mit Abrufdatum, URL und Lizenz je Datei pflegen. Für ODbL-Daten muss die Ableitung (z. B. `osm_pois.geojson`) ebenfalls unter ODbL stehen. Sie sollte deshalb getrennt von Daten anderer Lizenzen gehalten werden.

## (d) Lücken und Prüfbedarf

1. **Ortsbezirksgrenzen.** Ein eigener amtlicher Layer „Ortsbezirke“ wurde nicht gefunden. Der Wikipedia-Artikel zu Witzenhausen gibt unter Bezug auf § 6 der Hauptsatzung an: „Die Ortsbezirksgrenzen entsprechen den Gemarkungen der eingegliederten ehemaligen Gemeinden.“\[55\] Ob das wörtlich so in der Satzung steht und ob spätere Änderungssatzungen § 6 betreffen, ist **nicht verifiziert**. Die aktuelle Hauptsatzung unter `https://www.witzenhausen.eu/satzungen-ortsrecht/` ist zu prüfen. Auch das OSM-Wiki weist darauf hin: „Die Gemarkungen sind nicht automatisch admin_level=9. Die Ortsbezirke (mit Ortsbeirat) werden in den jeweiligen Hauptsatzungen festgelegt.“\[56\]
2. **Gemarkung ↔ Ortsteil.** Nach dem ersten Abruf ist zu prüfen, ob sich die Gemarkungen eindeutig den 16 Ortsbezirken zuordnen lassen. Kritisch sind (a) Berlepsch-Ellerode-Hübenthal, wo eine oder mehrere Gemarkungen in Frage kommen, und (b) die Kernstadt, zu der laut Wikipedia auch Bischhausen gehört und für die kein Ortsbezirk besteht.\[55\] Die Kernstadt wäre dann vermutlich die Vereinigung der Gemarkungen Witzenhausen und Bischhausen (Annahme). Eine Zuordnungstabelle `gemarkung → ortsbezirk` sollte manuell gepflegt und versioniert werden.
3. **OSM-Ortsteilgrenzen.** Belegt ist nur die Stadtrelation 549412.\[57\] Ob admin_level 9/10-Relationen existieren, klärt die Overpass-Abfrage oben. Es ist eher nicht zu erwarten.
4. **Lizenz B-Pläne Witzenhausen.** Laut Metadaten ist die Nutzung „ohne vertragliche Vereinbarung … nur für nicht kommerzielle Zwecke erlaubt“, eine offene Lizenz ist auf der OGC-API-Seite nicht hinterlegt.\[13\]\[14\] Für eine öffentliche, nicht kommerzielle Bürgeranwendung ist das voraussichtlich zulässig, eine kurze schriftliche Bestätigung bei stadtverwaltung@witzenhausen.de ist dennoch ratsam. Alternativ können Geltungsbereiche nur verlinkt statt gespiegelt werden.
5. **Direkt-URLs.** Für die hessenweite Hauskoordinaten-TXT, die Zensus-Gitter-ZIP und den NVV-GTFS-Datensatz wurden nur die Portalseiten belegt, nicht die Dateilinks. Claude Code sollte die Links einmalig aus den Portalseiten auslesen und im Skript fixieren. Beim Download gilt: Dateiname und Prüfsumme protokollieren.
6. **Layernamen und Parameter.** Die WFS-Typenamen und Ausgabeformate der HVBG-Suchdienste (WFS-lage, WFS-hako) sowie der DOP-Layer (`he_dop_rgb` vs. `he_dop20_rgb`) sind aus den GetCapabilities zu bestätigen.\[10\]\[58\] Die UTM-BBOX ist eine Näherung.
7. **Einwohner nach Ortsteilen.** Maschinenlesbare amtliche Zahlen auf Ortsteilebene wurden nicht gefunden. Es gibt zwei Wege: die Zahlen von witzenhausen.eu/lage (Stand 09/2022) übernehmen, mit Quellenhinweis „Stadt Witzenhausen“, oder Zensus-100-m-Gitter mit den Gemarkungen verschneiden. Letzteres ist reproduzierbar, wegen Geheimhaltung und Zellzuordnung aber nur ein Näherungswert.\[59\]
8. **Wahlbezirke.** Die 21 allgemeinen Wahlbezirke sind nicht automatisch mit den Ortsteilen identisch. Die Zuordnung steht in der Wahlbekanntmachung Nr. 013/2026 bzw. im votemanager.\[26\] Ob der votemanager Open-Data-CSV-Exporte anbietet, ist zu prüfen.
9. **Nicht recherchiert (Budget).** Regionalplan Nordhessen (RP Kassel), Lärmkartierung (WFS), DenkXweb/Kulturdenkmäler, LAGIS Ortslexikon, GovData-Einträge für den Werra-Meißner-Kreis, Mobilithek, Universität Kassel (Witzenhausen), Ladesäulenregister der Bundesnetzagentur, Breitband, Geofabrik-Extrakt sowie die Nutzungsrichtlinien von Nominatim und Photon. Für die OSM-Standardkacheln verbietet die OSMF-Tile-Usage-Policy Bulk-Download und Offline-Nutzung und gibt keine Verfügbarkeitsgarantie. Für die Geokodierung wird ohnehin empfohlen, die amtlichen Hauskoordinaten und Lagebezeichnungen lokal vorzuhalten, statt externe Geocoder im Browser aufzurufen. Das macht die Anwendung unabhängig von Rate-Limits Dritter.
10. **SessionNet** wird gemäß Vorgabe nicht genutzt. Grundlage bleiben die PDF-Bekanntmachungen unter `https://www.witzenhausen.eu/amtliche-bekanntmachungen/`.

## Recommendations

- **Build-Pipeline (einmal pro Woche oder Monat, nicht im Browser):** Gemarkungen und Gemeindegrenze (HVBG), B-Plan- und FNP-Umringe (Stadt), Hauskoordinaten/Lagebezeichnungen (HVBG), ÜSG und TWS (HLNUG) und OSM-POIs laden. Daraus GeoJSON in EPSG:4326 erzeugen (koordinatengenau auf 6 Nachkommastellen gerundet) und statisch im Repository ablegen.
- **Geokodierung der TOPs:** Zuerst Ortsbezirk aus dem Gremium (Ortsbeirat X → Gemarkung X), dann Straßenname gegen ein lokal erzeugtes Straßenverzeichnis aus den Hauskoordinaten (gefiltert auf 06636016, je Straße die Ortsbezirke per Punkt-in-Polygon), dann B-Plan-Namen gegen die WFS-Umringe, zuletzt Flurstücksangaben gegen ALKIS.
- **Frontend:** MapLibre GL JS mit basemap.de Web Vektor (Grau als ruhiger Hintergrund), optional Hessen-DOP-WMTS als Luftbild-Umschalter, Attributions-Footer gemäß Tabelle (c).
- **Vor dem Livegang:** Lizenzbestätigung der Stadt für die B-Plan-Daten einholen, NVV-GTFS-Lizenz klären und § 6 Hauptsatzung gegenlesen.

## Quellen

1. [basemap.de Web Vektor - BKG-MIS](https://mis.bkg.bund.de/trefferanzeige?docuuid=61B9F1A4-0627-4C12-9577-F64F083CFA28)
2. [Offene Geobasisdaten für alle](https://hzd.hessen.de/medienraum/news/open-data-offene-geobasisdaten-fuer-alle)
3. [Open Data Bereitstellung offener Geobasisdaten in Hessen](https://www.bdvi.de/application/files/4716/3914/7002/FORUM_4-2021_Open_Data_Hessen.pdf)
4. [WMS HE Karten - PG](https://www.geoportal.de/info/5feba35f-8c86-7dd1-333e-3e77b10c9c6e)
5. [AdV-MIS - INSPIRE-WMS HE Flurstücke/Grundstücke ALKIS - INSPIRE-WMS HE Flurstücke/Grundstücke ALKIS](https://advmis.geodatenzentrum.de/trefferanzeige?docuuid=2bb109ce-d777-0540-7791-8a18af9b79f2)
6. <https://www.geoportal.hessen.de/spatial-objects/885>
7. [Hessen](https://www.geoportal.hessen.de/mapbender/php/mod_dataISOMetadata.php?outputFormat=iso19139&id=7e3a1bba-1412-acfa-7f49-71040909e113)
8. [Produktblatt Hauskoordinaten - HVBG Hessen](https://hvbg.hessen.de/sites/hvbg.hessen.de/files/2022-09/produktblatt_hauskoordinaten.pdf)
9. [INSPIRE-WFS HE Adressen Hauskoordinaten](https://www.geoportal.hessen.de/spatial-objects/706)
10. <https://hebid.hessen.de/bdd/hlbk/Dokumente/Uebersicht_Geowebdienste_OpenData_V3.pdf>
11. [Bebauungspläne Stadt Witzenhausen](https://www.geoportal.hessen.de/mapbender/php/wfs.php?INSPIRE=1&FEATURETYPE_ID=1245&request=GetCapabilities&VERSION=1.1.0&SERVICE=WFS)
12. [This XML file does not appear to have any ... - Geoportal Hessen](https://www.geoportal.hessen.de/mapbender/php/wfs.php?INSPIRE=1&FEATURETYPE_ID=4140&request=GetCapabilities&VERSION=2.0.0&SERVICE=WFS&INSPIRE=1)
13. [Bebauungspläne Gem. Witzenhausen](https://www.geoportal.hessen.de/spatial-objects/337)
14. [Bebauungspläne Stadt Witzenhausen - Witzenhausen Bebauungspläne Umringe](https://inspire-geoportal.ec.europa.eu/srv/api/records/188f691a-0412-eee5-4186-b22986bf14da)
15. [Geodienste Wasser](https://www.hlnug.de/themen/geografische-informationssysteme/geodienste/wasser)
16. [Gebiete naturbedingter Risiken Hessen](https://www.geoportal.hessen.de/spatial-objects/264)
17. [https://www.geoportal.hessen.de/mapbender/php ...](https://www.geoportal.hessen.de/mapbender/php/mod_featuretypeISOMetadata.php?SERVICE=WFS&outputFormat=iso19139&Id=2737)
18. [Schutzgebiete Hessen - Geoportal Hessen](https://www.geoportal.hessen.de/spatial-objects/266)
19. [Witzenhausen (Werra-Meißner-Kreis, Hessen, Deutschland) - Einwohnerzahlen, Grafiken, Karte, Lage, Wetter und Web-Informationen](https://citypopulation.de/de/germany/hessen/werra_mei%C3%9Fner_kreis/06636016__witzenhausen/)
20. [Witzenhausen : Zensus 2022](https://wahlatlas.net/experimente/zensus2022/gemeinden/066360016016.html)
21. [Zensus2022 100mGitter](https://plattform-npgeo-vfdb.hub.arcgis.com/datasets/esri-de-content::zensus2022-100mgitter/about)
22. [Neue Angebote auf Gitterzellebene: Weitere Auswertungen verfügbar - Statistisches Bundesamt](https://www.destatis.de/DE/Themen/Gesellschaft-Umwelt/Bevoelkerung/Zensus2022/Aktuell/meldung-verfuegbarkeit-weitere-auswertungen.html)
23. [Lage - Stadt Witzenhausen](https://www.witzenhausen.eu/lage/)
24. [DeWiki \> Witzenhausen](https://dewiki.de/Lexikon/Witzenhausen)
25. [Kommunalwahl 2026 - Stadt Witzenhausen](https://www.witzenhausen.eu/kommunalwahl-2026/)
26. [Amtliche Bekanntmachung der Stadt Witzenhausen Nr. 013/2026](https://www.witzenhausen.eu/wp-content/uploads/2026/01/013-2026-Wahlbekanntmachung-Kommunalwahl-15-03-2026.pdf)
27. [Trendwahl Witzenhausen 2026: SPD führt knapp vor CDU](https://meineregion365.de/politik/kirschenstadt-spd-fuehrt-knapp-vor-der-cdu-3114506)
28. [Datensätze - OpenData ÖPNV](https://www.opendata-oepnv.de/ht/de/datensaetze)
29. [Start - OpenData ÖPNV](https://www.opendata-oepnv.de/ht/en/organisation/delfi/start?tx_vrrkit_view%5Baction%5D=details&tx_vrrkit_view%5Bcontroller%5D=View&tx_vrrkit_view%5Bdataset_name%5D=deutschlandweite-haltestellendaten&cHash=02aa95607cd0164111fcf703f749a2ee)
30. [Startseite - OpenData ÖPNV](https://www.opendata-oepnv.de/ht/de/organisation/delfi/startseite?amp%3Btx_vrrkit_view%5Baction%5D=details&amp%3Bamp%3Btx_vrrkit_view%5Bcontroller%5D=View&amp%3Btx_vrrkit_view%5Bdataset_name%5D=deutschlandweite-haltestellendaten&amp%3BcHash=3a0a43be16ca41ebb4b200e9e0be3e95)
31. [WEB VEKTOR - basemap.de](https://basemap.de/produkte-und-dienste/web-vektor/)
32. [Stand: 03.03.2025 Seite 1 von 6 Dokumentation basemap.de Web Vektor](https://sgx.geodatenzentrum.de/web_public/gdz/dokumentation/deu/basemap.de_web_vektor.pdf)
33. [BKG-MIS - Vector Tiles basemap.de Web Vektor](https://mis.bkg.bund.de/trefferanzeige?docuuid=5417CFE8-F0EC-4629-BADB-493864DB466A)
34. [Witzenhausen - Wikidata](https://www.wikidata.org/wiki/Q564827)
35. [Werleshausen - Wikidata](https://www.wikidata.org/wiki/Q2560623)
36. [Blickershausen - Wikidata](https://www.wikidata.org/wiki/Q884011)
37. [Ellingerode - Wikidata](https://www.wikidata.org/wiki/Q1332184)
38. [Gertenbach - Wikidata](https://www.wikidata.org/wiki/Q1433972)
39. [Ziegenhagen - Wikidata](https://www.wikidata.org/wiki/Q198786)
40. [Dohrenbach - Wikidata](https://www.wikidata.org/wiki/Q1234893)
41. [Hundelshausen - Wikidata](https://www.wikidata.org/wiki/Q1637452)
42. [Unterrieden - Wikidata](https://www.wikidata.org/wiki/Q2498818)
43. [Albshausen - Wikidata](https://www.wikidata.org/wiki/Q1660176)
44. [Hubenrode - Wikidata](https://www.wikidata.org/wiki/Q1632999)
45. [Ermschwerd - Wikidata](https://www.wikidata.org/wiki/Q1292400)
46. [Wendershausen - Wikidata](https://www.wikidata.org/wiki/Q2559136)
47. [Neuseesen - Wikidata](https://www.wikidata.org/wiki/Q1745254)
48. [Roßbach - Wikidata](https://www.wikidata.org/wiki/Q1753104)
49. [Berlepsch-Ellerode-Hübenthal - Wikidata](https://www.wikidata.org/wiki/Q15107510)
50. [Kleinalmerode - Wikidata](https://www.wikidata.org/wiki/Q1746285)
51. [Q21036575 - Wikidata](https://www.wikidata.org/wiki/Q21036575)
52. [Hübenthal - Wikidata](https://www.wikidata.org/wiki/Q1652053)
53. [WEB VEKTOR HOSTING - basemap.de](https://basemap.de/produkte-und-dienste/web_vektor_hosting/)
54. [Metadaten](https://www.geoportal.hessen.de/mapbender/php/mod_showMetadata.php?resource=wfs&id=272&layout=tabs&languageCode=de)
55. [Witzenhausen - Wikiwand](https://www.wikiwand.com/de/Witzenhausen?lang=de&title=Witzenhausen)
56. [Hessen/Geodaten online - OpenStreetMap Wiki](https://wiki.openstreetmap.org/wiki/Hessen/Geodaten_online)
57. [Relation: ‪Witzenhausen‬ (‪549412‬)](https://www.openstreetmap.org/relation/549412)
58. [Open Data (Geodata) Hessen ab 01.02.2022](https://community.openstreetmap.org/t/open-data-geodata-hessen-ab-01-02-2022/94571)
59. [Zensus 2022 - Statistisches Bundesamt](https://www.destatis.de/DE/Themen/Gesellschaft-Umwelt/Bevoelkerung/Zensus2022/_inhalt.html)
