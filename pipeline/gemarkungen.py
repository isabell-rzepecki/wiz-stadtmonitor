"""Ortsbezirke aus den Gemarkungen (Digitale Verwaltungsgrenzen Hessen, HVBG, dl-de/zero-2.0).

Quelle `vg_shp` im Quellenregister: Shapefile in EPSG:25832, Filter auf die Gemeinde (GMDE_NR). Die Zuordnung
Gemarkung → Ortsbezirk steht in config/stadt.json (ortsteile[].gemarkung_nr, zuordnung_status); offene Punkte
(§ 6 Hauptsatzung, Bischhausen, Hübenthal) bleiben dort sichtbar markiert und werden hier nicht aufgelöst.

Ausgabe:
- data/geo/dl-de-zero/ortsbezirke.geojson: volle Auflösung (6 Nachkommastellen), im Repository;
- data/export/flaechen.json: vereinfacht (etwa 2 m) für die Seite, mit Gemeindegrenze.
"""
import hashlib
import io
import json
import zipfile

import shapefile
from pyproj import Transformer
from shapely.geometry import mapping, shape
from shapely.ops import transform, unary_union

from . import audit, config, net

URL = "https://gds-srv.hessen.de/atomfeed/DigVGr-epsg25832-shp.zip"
ZIP = config.RAW / "vg" / "DigVGr.zip"
LIZENZ = "dl-de/zero-2.0"
NAMENSNENNUNG = "Geobasisdaten: © Hessische Verwaltung für Bodenmanagement und Geoinformation (HVBG), dl-de/zero-2.0"
OUT_SITE = config.EXPORT / "flaechen.json"
GMDE_NR = config.STADT["stadt"]["gemeindeschluessel"][-6:]


def fetch():
    """Shapefile-Archiv laden (rund 68 MB); aus dem Zwischenspeicher, solange es jünger als 30 Tage ist. Scheitert der
    Abruf, bleiben die Ortsbezirksflächen im Repository auf dem letzten Stand."""
    if net.gueltig(ZIP, 30 * 86400):
        return
    ZIP.parent.mkdir(parents=True, exist_ok=True)
    try:
        body, _ = net.get(URL)
    except Exception as e:
        audit.abruf("vg_shp", URL, getattr(e, "code", ""), "", "", "", str(e)[:200])
        print(f"Verwaltungsgrenzen nicht abrufbar ({e}); Ortsbezirksflächen bleiben auf dem letzten Stand")
        return
    grund = net.pruefen(ZIP, body)
    if grund:
        audit.abruf("vg_shp", URL, 200, len(body), "", "", grund)
        print(f"Verwaltungsgrenzen: {grund}; Ortsbezirksflächen bleiben auf dem letzten Stand")
        return
    net.speichern(ZIP, body)
    audit.abruf("vg_shp", URL, 200, len(body), hashlib.sha256(body).hexdigest(), "", "")


def _reader(z, name):
    return shapefile.Reader(shp=io.BytesIO(z.read(f"{name}.shp")), dbf=io.BytesIO(z.read(f"{name}.dbf")),
                            shx=io.BytesIO(z.read(f"{name}.shx")), encoding="utf-8")


def _runden(geom, stellen=6):
    return json.loads(json.dumps(mapping(geom)), parse_float=lambda x: round(float(x), stellen))


def lesen():
    """(Gemarkungen [{gmk_nr, gemarkung, erzeugt_am, geometry}], Gemeindefläche) in EPSG:4326."""
    utm = Transformer.from_crs("EPSG:25832", "EPSG:4326", always_xy=True).transform
    with zipfile.ZipFile(ZIP) as z:
        gem = []
        for sr in _reader(z, "GEMARKUNG_LA").iterShapeRecords():
            if sr.record["GMDE_NR"] == GMDE_NR:
                gem.append({"gmk_nr": sr.record["GMK_NR"], "gemarkung": sr.record["GMK_BZ"], "erzeugt_am": sr.record["ERZEUGT_AM"],
                            "geometry": transform(utm, shape(sr.shape.__geo_interface__))})
        stadt = [transform(utm, shape(sr.shape.__geo_interface__)) for sr in _reader(z, "GEMEINDE_LA").iterShapeRecords()
                 if sr.record["GMDE_NR"] == GMDE_NR]
    return sorted(gem, key=lambda g: g["gmk_nr"]), unary_union(stadt) if stadt else None


def features(gem, toleranz=None):
    by_nr = {o["gemarkung_nr"]: o for o in config.STADT["ortsteile"]}
    out = []
    for g in gem:
        o = by_nr.get(g["gmk_nr"])
        geom = g["geometry"].simplify(toleranz, preserve_topology=True) if toleranz else g["geometry"]
        props = {"gmk_nr": g["gmk_nr"], "gemarkung": g["gemarkung"]}
        if o:
            props.update(slug=o["slug"], name=o["name"], ortsbezirk=o["ortsbezirk"], zuordnung_status=o.get("zuordnung_status", ""))
        else:
            props.update(zuordnung_status="keine Zuordnung in der Konfiguration")
        out.append({"type": "Feature", "properties": props, "geometry": _runden(geom)})
    return out


def kopf(erzeugt_am):
    return {"license": LIZENZ, "attribution": NAMENSNENNUNG, "source": URL, "retrieved": net.abrufdatum(ZIP),
            "erzeugt_am_quelle": erzeugt_am}


def build():
    if not ZIP.exists():
        print("Kein Shapefile-Archiv; Ortsbezirksflächen aus dem Repository, Seitenflächen daraus abgeleitet")
        voll = json.loads(config.ORTSBEZIRKE.read_text(encoding="utf-8"))
        gem = [{"gmk_nr": f["properties"]["gmk_nr"], "gemarkung": f["properties"]["gemarkung"], "geometry": shape(f["geometry"])}
               for f in voll["features"]]
        stadt = unary_union([g["geometry"] for g in gem])
        site = {"type": "FeatureCollection", **{k: voll[k] for k in ("license", "attribution", "source", "retrieved", "erzeugt_am_quelle")},
                "features": features(gem, 0.00002), "stadtgrenze": _runden(stadt.simplify(0.00002, preserve_topology=True))}
        OUT_SITE.parent.mkdir(parents=True, exist_ok=True)
        OUT_SITE.write_text(json.dumps(site, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
        return
    gem, stadt = lesen()
    if len(gem) != len(config.STADT["ortsteile"]):
        raise SystemExit(f"{len(gem)} Gemarkungen, erwartet {len(config.STADT['ortsteile'])} (Konfiguration prüfen)")
    erzeugt = gem[0]["erzeugt_am"] if gem else ""
    voll = {"type": "FeatureCollection", **kopf(erzeugt), "features": features(gem)}
    config.ORTSBEZIRKE.parent.mkdir(parents=True, exist_ok=True)
    config.ORTSBEZIRKE.write_text(json.dumps(voll, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    site = {"type": "FeatureCollection", **kopf(erzeugt), "features": features(gem, 0.00002)}
    if stadt is not None:
        site["stadtgrenze"] = _runden(stadt.simplify(0.00002, preserve_topology=True))
    OUT_SITE.parent.mkdir(parents=True, exist_ok=True)
    OUT_SITE.write_text(json.dumps(site, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"{len(gem)} Gemarkungen (Stand der Quelle {erzeugt}), {sum(1 for f in voll['features'] if 'slug' in f['properties'])} zugeordnet")
