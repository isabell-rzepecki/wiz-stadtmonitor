"""Weitere Kartenebenen: Hochwasser (ÜSG, HWRM), Trinkwasser- und Heilquellenschutz (HLNUG, CC BY 4.0), Schutzgebiete
Natur (HMLU, Naturparke HessenForst; frei nutzbar, keine Weiterveräußerung), Windvorranggebiete (Regionalplan
Nordhessen) und Kulturdenkmäler (DenkXweb), beide dl-de/by-2.0.

Ebenen und Quellenvermerke stehen in config/stadt.json (umwelt). Abruf über die INSPIRE-WFS des Landes; der Dienst
liefert nur mit einer BBOX in EPSG:4326 (Breite, Länge) Objekte. Die Flächen werden auf das Stadtgebiet
zugeschnitten und als Kartenebenen je Gruppe ausgeliefert (data/export/karte/umwelt_<gruppe>.json).

Überschneidungen mit verorteten Vorgängen sind rein räumlich (Flurstückspunkt in der Fläche oder Geltungsbereich eines
Plans zu mindestens ANTEIL in der Fläche). Straßen und Ortsteile werden nicht verschnitten: ihr Bezugspunkt bzw. ihre
Fläche sagt über die Lage eines Vorhabens zu wenig aus.
"""
import hashlib
import json
import re
import time
import urllib.parse
from datetime import date

from shapely.geometry import Point, mapping, shape
from shapely.ops import unary_union

from . import audit, config, net

RAW = config.RAW / "umwelt"
KARTE = config.EXPORT / "karte"
U = config.STADT["umwelt"]
ANTEIL = 0.01
TOLERANZ = 0.00002  # etwa 2 m


def stadtgebiet():
    fl = json.loads(config.ORTSBEZIRKE.read_text(encoding="utf-8"))
    return unary_union([shape(f["geometry"]) for f in fl["features"]])


def ebenen():
    for g in U["gruppen"]:
        for e in g["ebenen"]:
            yield g, e


def url(e, bbox):
    w, s, o, n = bbox
    if e.get("url"):  # andere Dienste mit eigener Adresse (BBOX in EPSG:4326, Breite zuerst)
        return e["url"].format(w=w, s=s, o=o, n=n)
    q = {"SERVICE": "WFS", "VERSION": "2.0.0", "REQUEST": "GetFeature", "TYPENAMES": f"inspire_{e['dienst']}:{e['typ']}",
         "BBOX": f"{s},{w},{n},{o},urn:ogc:def:crs:EPSG::4326", "OUTPUTFORMAT": "GEOJSON"}
    return U["dienst"].format(dienst=e["dienst"]) + "?" + urllib.parse.urlencode(q)


def fetch():
    """Alle Ebenen im Rechteck um das Stadtgebiet laden; Zwischenspeicher sieben Tage."""
    RAW.mkdir(parents=True, exist_ok=True)
    w, s, o, n = stadtgebiet().bounds
    bbox = (w - 0.005, s - 0.005, o + 0.005, n + 0.005)
    for g, e in ebenen():
        if e.get("abruf"):  # eigener Abruf in einem anderen Modul (z. B. gebaeude.py)
            continue
        ziel = RAW / f"{e['id']}.geojson"
        if ziel.exists() and time.time() - ziel.stat().st_mtime < 7 * 86400:
            continue
        u = url(e, bbox)
        try:
            body, _ = net.get(u, tries=2)
            n_obj = len(json.loads(body)["features"])
            ziel.write_bytes(body)
            audit.abruf(g["quelle"], u, 200, len(body), hashlib.sha256(body).hexdigest(), n_obj, "")
        except Exception as ex:  # letzter Stand bleibt, Fehler steht im Protokoll
            audit.abruf(g["quelle"], u, getattr(ex, "code", ""), "", "", "", str(ex)[:200])


def _wert(props, feld):
    v = props.get(feld) if feld else None
    return str(v).strip() if v not in (None, "", " ") else None


def flaechen(stadt=None):
    """[{gruppe, ebene, titel, name, zone, status, vo_gueltig, link, ueberschneidung, geometry}] im Stadtgebiet."""
    stadt = stadt or stadtgebiet()
    out = []
    for g, e in ebenen():
        p = RAW / f"{e['id']}.geojson"
        if not p.exists():
            continue
        for f in json.loads(p.read_text(encoding="utf-8"))["features"]:
            geom = shape(f["geometry"])
            geom = (geom if geom.is_valid else geom.buffer(0)).intersection(stadt)
            if geom.is_empty or geom.area == 0:
                continue
            pr = f["properties"]
            link = _wert(pr, e.get("link"))
            name = _wert(pr, e.get("name"))
            if name and e.get("name_praefix"):  # „Kreis_Gemeinde_Ortsteil_Adresse“ → „Ortsteil, Adresse“
                name = re.sub(e["name_praefix"], "", name).replace("_", ", ")
            out.append({"gruppe": g["id"], "ebene": e["id"], "titel": e["titel"], "name": name,
                        "zone": _wert(pr, e.get("zone")), "status": _wert(pr, e.get("status")),
                        "vo_gueltig": _wert(pr, e.get("vo_gueltig")), "link": link if link and link.startswith("https://") else None,
                        "ueberschneidung": e.get("ueberschneidung", True), "geometry": geom})
    return out


def build():
    """Kartenebenen je Gruppe; gibt die Flächen für die Überschneidung zurück."""
    liste = flaechen()
    KARTE.mkdir(parents=True, exist_ok=True)
    for g in U["gruppen"]:
        feats = []
        for f in (x for x in liste if x["gruppe"] == g["id"]):
            geom = json.loads(json.dumps(mapping(f["geometry"].simplify(TOLERANZ, preserve_topology=True))),
                              parse_float=lambda x: round(float(x), 6))
            props = {k: f[k] for k in ("ebene", "name", "zone", "status", "vo_gueltig", "link") if f[k]}
            feats.append({"type": "Feature", "properties": props, "geometry": geom})
        quelle = next(e for e in g["ebenen"])
        data = {"type": "FeatureCollection", "attribution": g["attribution"], "hinweis": g.get("hinweis", U["hinweis"]),
                "source": quelle["url"].split("?")[0] if quelle.get("url") else g.get("quelle_url") or U["dienst"].format(dienst=quelle["dienst"]), "retrieved": date.today().isoformat(),
                "ebenen": {e["id"]: e["titel"] for e in g["ebenen"]}, "features": feats}
        (KARTE / f"umwelt_{g['id']}.json").write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"Umweltebenen: {len(liste)} Flächen im Stadtgebiet")
    return liste


def ueberschneidungen(liste, punkt=None, flaeche=None):
    """[{gruppe, ebene, titel, name, zone}] der Flächen, die ein Punkt (lon, lat) trifft oder eine Fläche zu ANTEIL deckt."""
    out = []
    p = Point(*punkt) if punkt else None
    for f in liste:
        if not f["ueberschneidung"]:
            continue
        g = f["geometry"]
        if (p is not None and g.contains(p)) or (flaeche is not None and flaeche.area and g.intersection(flaeche).area >= ANTEIL * flaeche.area):
            e = {k: f[k] for k in ("gruppe", "ebene", "titel", "name", "zone") if f[k]}
            if e not in out:
                out.append(e)
    return out
