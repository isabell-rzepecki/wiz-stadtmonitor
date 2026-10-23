# Abrufbeispiele (getestet am 23.10.2026, sofern nicht anders vermerkt)

Konstanten:

```bash
GMDE=636016                                   # Witzenhausen (AGS 06636016)
BBOX_LATLON="51.28,9.72,51.41,9.94"           # Achsenreihenfolge lat,lon für EPSG:4326 in WFS 2.0
```

## 1. Gemarkungen (= Ortsbezirke) – getestet

```bash
curl -L -o DigVGr.zip https://gds-srv.hessen.de/atomfeed/DigVGr-epsg25832-shp.zip
unzip -o DigVGr.zip -d digvgr                 # enthält GEMARKUNG_LA, GEMEINDE_LA, FLUR_LA …
ogr2ogr -f GeoJSON -t_srs EPSG:4326 -where "GMDE_NR='636016'" gemarkungen.geojson digvgr/GEMARKUNG_LA.shp
```
Felder: `GMK_NR`, `GMK_BZ`, `GMDE_NR`, `GMDE_BZ`, `ERZEUGT_AM`. Ergebnis: 17 Gemarkungen. Ohne GDAL: `pyshp` + `shapely` + `pyproj` (so wurde `gemarkungen_witzenhausen.geojson` erzeugt).

## 2. Bodenrichtwerte 2024 – getestet

```bash
curl -L -o brw2024.gml "https://www.gds.hessen.de/wfs2/boris/cgi-bin/brw/2024/wfs?SERVICE=WFS&VERSION=2.0.0&REQUEST=GetFeature&TYPENAMES=boris:BR_BodenrichtwertZonal&BBOX=${BBOX_LATLON},urn:ogc:def:crs:EPSG::4326&COUNT=5000"
```
- Antwort: 395 Zonen, davon 294 mit `kreis=36`, `gemeinde=016`.
- Relevante Elemente: `boris:bodenrichtwert`, `boris:stichtag`, `boris:entwicklungszustand` (B = baureifes Land, LF = Landwirtschaft, SF = Sonderfläche …), `boris:art` (WA, WR, MI, MD, GE …), Gemarkung unter `boris:BR_Gemarkung/boris:name`.
- Geometrie mit `ogr2ogr` prüfen; das AdV-Schema ist verschachtelt, ggf. eigener Parser.
- Stichtag 2026: `…/brw/2026/wfs` liefert 404 → Pfad über boris.hessen.de bzw. gds.hessen.de ermitteln.

## 3. Hauskoordinaten / Lagebezeichnungen – Capabilities getestet

```bash
curl -L "https://www.gds-srv.hessen.de/cgi-bin/lika-services/ogc-free-data.ows?SERVICE=WFS&VERSION=1.1.0&REQUEST=GetCapabilities" -o hako_caps.xml
# Layer: hako, lage, flst. GetFeature mit BBOX in EPSG:25832 kacheln (Feature-Limits beachten):
curl -L "https://www.gds-srv.hessen.de/cgi-bin/lika-services/ogc-free-data.ows?SERVICE=WFS&VERSION=1.1.0&REQUEST=GetFeature&TYPENAME=hako&BBOX=<xmin>,<ymin>,<xmax>,<ymax>,EPSG:25832" -o hako_tile.gml   # nicht getestet
```
Ziel: Straßenverzeichnis `strasse → [ortsbezirk]` per Punkt-in-Gemarkung.

## 4. Bebauungspläne – Capabilities getestet

```bash
curl -L "https://www.gdi-nordosthessen.de/ws/wfs/ds_plu_bplan_whs/ows.wfs?SERVICE=WFS&VERSION=2.0.0&REQUEST=GetFeature&TYPENAMES=lyr:witzenhausen_bplaene_umringe_feature&SRSNAME=EPSG:4326" -o bplaene.gml   # GetFeature nicht getestet
```
Lizenz: nur nicht kommerziell ohne Vertrag → Daten zunächst nur im Build nutzen, nicht im Repo veröffentlichen.

## 5. HLNUG / Schutzgebiete – Capabilities getestet

```bash
U=https://geodienste-umwelt.hessen.de/arcgis/services/inspire
curl -L "$U/gebiete_naturbedingter_risiken/MapServer/WFSServer?SERVICE=WFS&VERSION=2.0.0&REQUEST=GetFeature&TYPENAMES=inspire_gebiete_naturbedingter_risiken:Ueberschwemmungsgebiete_HQ100_nach_HWG&BBOX=548000,5680000,567000,5699000,urn:ogc:def:crs:EPSG::25832" -o uesg.gml   # GetFeature nicht getestet
curl -L "$U/bewirtschaftungsgebiete/MapServer/WFSServer?SERVICE=WFS&VERSION=2.0.0&REQUEST=GetFeature&TYPENAMES=inspire_bewirtschaftungsgebiete:TWS_HQS_ALK&BBOX=548000,5680000,567000,5699000,urn:ogc:def:crs:EPSG::25832" -o tws.gml
curl -L "$U/schutzgebiete/MapServer/WFSServer?SERVICE=WFS&VERSION=2.0.0&REQUEST=GetFeature&TYPENAMES=inspire_schutzgebiete:Naturschutzgebiete&BBOX=548000,5680000,567000,5699000,urn:ogc:def:crs:EPSG::25832" -o nsg.gml
```
BBOX in UTM ist eine Näherung → nach dem Abruf mit der Stadtgrenze clippen.

## 6. Hintergrundkarte – getestet

```js
new maplibregl.Map({ container: 'map',
  style: 'https://sgx.geodatenzentrum.de/gdz_basemapde_vektor/styles/bm_web_gry.json',
  center: [9.857, 51.341], zoom: 11 });
```

## 7. Wikidata – Entity-Abruf getestet

```bash
curl -L "https://www.wikidata.org/wiki/Special:EntityData/Q564827.json" -o wiz.json
```
Q-IDs (nicht gegengeprüft): Albshausen Q1660176 · Berlepsch-Ellerode(-Hübenthal) Q15107510 · Blickershausen Q884011 · Dohrenbach Q1234893 · Ellingerode Q1332184 · Ermschwerd Q1292400 · Gertenbach Q1433972 · Hubenrode Q1632999 · Hundelshausen Q1637452 · Kleinalmerode Q1746285 · Neuseesen Q1745254 · Roßbach Q1753104 · Unterrieden Q2498818 · Wendershausen Q2559136 · Werleshausen Q2560623 · Ziegenhagen Q198786 · Hübenthal Q1652053.

## 8. OSM (Overpass) – nicht getestet

```
[out:json][timeout:120];
area(id:3600549412)->.wiz;
( nwr(area.wiz)["amenity"~"community_centre|townhall|school|kindergarten|fire_station|grave_yard"];
  node(area.wiz)["place"~"village|hamlet|suburb|town"]; );
out tags center;
```
Ergebnis cachen; ODbL-Ableitungen getrennt ablegen.
