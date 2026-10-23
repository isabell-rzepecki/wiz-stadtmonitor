"""Straßen- und Lageverzeichnis aus dem Suchdienst der HVBG (Quelle `hako_lage`, dl-de/zero-2.0):
Name → Gemarkungen (Ortsbezirke) mit einem Bezugspunkt je Gemarkung.

- Ebene `hako` (Hauskoordinaten): Straßen mit Gebäuden; ein Abruf mit Filter auf Kreis und Gemeinde.
- Ebene `lage` (Lagebezeichnungen der Flurstücke ohne Hausnummer): weitere Straßen und Gewannnamen
  („Am Rabensberg“); Abruf in Kacheln von 2 km (höchstens 10.000 Objekte je Anfrage laut Dienst).

Die Gemarkung jedes Punkts wird per Punkt-in-Fläche gegen die Gemarkungen (pipeline/gemarkungen.py) bestimmt und
mit der Angabe des Dienstes abgeglichen; Abweichungen stehen im Audit. Hausnummern werden nicht übernommen.
"""
import hashlib
import json
import re
import statistics
import time
import urllib.parse
from datetime import date

from pyproj import Transformer

from . import audit, config, net

URL = "https://www.gds-srv.hessen.de/cgi-bin/lika-services/ogc-free-data.ows"
RAW = config.RAW / "lage"
VERZEICHNIS = config.GEO / "dl-de-zero" / "lagebezeichnungen.json"
GMDE_NR = config.STADT["stadt"]["gemeindeschluessel"][-6:]
KACHEL = 2000
LIMIT = 10000


def _bbox_utm():
    d = json.loads(config.ORTSBEZIRKE.read_text(encoding="utf-8"))
    to_utm = Transformer.from_crs("EPSG:4326", "EPSG:25832", always_xy=True).transform
    xs, ys = [], []
    for f in d["features"]:
        for ring in (f["geometry"]["coordinates"] if f["geometry"]["type"] == "Polygon" else [r for p in f["geometry"]["coordinates"] for r in p]):
            for lon, lat in ring[::5]:
                x, y = to_utm(lon, lat)
                xs.append(x); ys.append(y)
    return int(min(xs)) // KACHEL * KACHEL, int(min(ys)) // KACHEL * KACHEL, int(max(xs)) + 1, int(max(ys)) + 1


def fetch():
    """Kacheln der Ebene `lage` laden (Zwischenspeicher 30 Tage)."""
    RAW.mkdir(parents=True, exist_ok=True)
    x0, y0, x1, y1 = _bbox_utm()
    for x in range(x0, x1, KACHEL):
        for y in range(y0, y1, KACHEL):
            p = RAW / f"lage_{x}_{y}.gml"
            if p.exists() and time.time() - p.stat().st_mtime < 30 * 86400:
                continue
            url = (f"{URL}?SERVICE=WFS&VERSION=1.1.0&REQUEST=GetFeature&TYPENAME=lage&SRSNAME=EPSG:25832"
                   f"&BBOX={x},{y},{x + KACHEL},{y + KACHEL},EPSG:25832")
            try:
                body, _ = net.get(url)
            except Exception as e:
                audit.abruf("hako_lage", url, getattr(e, "code", ""), "", "", "", str(e)[:200])
                raise
            n = body.count(b"<ms:lage ")
            if n >= LIMIT:
                raise SystemExit(f"Kachel {x},{y}: {n} Objekte, Grenze des Dienstes erreicht – Kachel verkleinern")
            p.write_bytes(body)
            audit.abruf("hako_lage", url, 200, len(body), hashlib.sha256(body).hexdigest(), n, "")
            time.sleep(0.5)


def fetch_hako():
    """Hauskoordinaten der Gemeinde in einem Abruf (Filter auf Kreis und Gemeinde), Zwischenspeicher 30 Tage."""
    RAW.mkdir(parents=True, exist_ok=True)
    p = RAW / "hako.gml"
    if p.exists() and time.time() - p.stat().st_mtime < 30 * 86400:
        return
    kreis, gem = GMDE_NR[1:3], GMDE_NR[3:]
    flt = (f"<Filter><And><PropertyIsEqualTo><PropertyName>HA_KREIS</PropertyName><Literal>{kreis}</Literal></PropertyIsEqualTo>"
           f"<PropertyIsEqualTo><PropertyName>HA_GEMEINDE</PropertyName><Literal>{gem}</Literal></PropertyIsEqualTo></And></Filter>")
    url = f"{URL}?" + urllib.parse.urlencode({"SERVICE": "WFS", "VERSION": "1.1.0", "REQUEST": "GetFeature", "TYPENAME": "hako", "FILTER": flt})
    body, _ = net.get(url)
    n = body.count(b"<ms:hako ")
    if n >= LIMIT or n == 0:
        audit.abruf("hako_lage", url, 200, len(body), "", n, "Anzahl unplausibel")
        raise SystemExit(f"Hauskoordinaten: {n} Objekte – Abruf prüfen")
    p.write_bytes(body)
    audit.abruf("hako_lage", url, 200, len(body), hashlib.sha256(body).hexdigest(), n, "")


def _feld(f, k):
    m = re.search(rf"<ms:{k}>(.*?)</ms:{k}>", f, re.S)
    return m.group(1).strip() if m else ""


def punkte():
    """[(name, quelle, gemarkung_nr laut Dienst, x, y)] in EPSG:25832; je Flurstück bzw. Adresse ein Punkt."""
    out, gesehen = [], set()
    gk_utm = Transformer.from_crs("EPSG:31467", "EPSG:25832", always_xy=True).transform
    hako = RAW / "hako.gml"
    if hako.exists():
        for f in re.findall(r"<ms:hako .*?</ms:hako>", hako.read_text(encoding="utf-8"), re.S):
            name = re.sub(r"\s+", " ", _feld(f, "HA_STR"))
            r, h = _feld(f, "HA_RWERT"), _feld(f, "HA_HWERT")
            if name and r and h:
                x, y = gk_utm(float(r), float(h))
                out.append((name, "hako", _feld(f, "HA_OTEIL"), x, y))
    for p in sorted(RAW.glob("lage_*.gml")):
        for f in re.findall(r"<ms:lage .*?</ms:lage>", p.read_text(encoding="utf-8"), re.S):
            fid = _feld(f, "ID")
            if _feld(f, "GD_GDNR") != GMDE_NR or fid in gesehen:  # an Kachelgrenzen doppelt geliefert
                continue
            gesehen.add(fid)
            name = re.sub(r"\s+", " ", _feld(f, "LA_LABEZ"))
            pos = re.search(r"<gml:pos>([\d.]+) ([\d.]+)</gml:pos>", f)
            if name and pos:
                out.append((name, "lage", _feld(f, "FS_GKNR"), float(pos.group(1)), float(pos.group(2))))
    return out


def build():
    """Verzeichnis {name: {gemarkung_nr: {"n", "lon", "lat", "quelle"}}}; Punkt = Median der Punkte je Gemarkung."""
    from shapely.geometry import Point, shape
    to_wgs = Transformer.from_crs("EPSG:25832", "EPSG:4326", always_xy=True).transform
    flaechen = [(f["properties"]["gmk_nr"], shape(f["geometry"])) for f in json.loads(config.ORTSBEZIRKE.read_text(encoding="utf-8"))["features"]]
    je, abweichungen = {}, []
    for name, quelle, gk_dienst, x, y in punkte():
        lon, lat = to_wgs(x, y)
        gk = next((nr for nr, g in flaechen if g.contains(Point(lon, lat))), None)
        if gk != gk_dienst:
            abweichungen.append({"name": name, "quelle": quelle, "gemarkung_dienst": gk_dienst, "gemarkung_lage": gk or "außerhalb",
                                 "lon": round(lon, 6), "lat": round(lat, 6)})
        if not gk:
            continue
        e = je.setdefault(name, {}).setdefault(gk, {"pts": [], "quellen": set()})
        e["pts"].append((lon, lat))
        e["quellen"].add(quelle)
    verz = {name: {gk: {"n": len(e["pts"]), "lon": round(statistics.median(p[0] for p in e["pts"]), 6),
                        "lat": round(statistics.median(p[1] for p in e["pts"]), 6), "quelle": "+".join(sorted(e["quellen"]))}
                   for gk, e in sorted(g.items())} for name, g in je.items()}
    out = {"license": "dl-de/zero-2.0",
           "attribution": "Geobasisdaten: © Hessische Verwaltung für Bodenmanagement und Geoinformation (HVBG), dl-de/zero-2.0",
           "source": URL + " (Ebenen hako und lage)", "retrieved": date.today().isoformat(),
           "hinweis": "Straßen und Lagebezeichnungen je Gemarkung (Punkt-in-Fläche), Bezugspunkt = Median der Punkte; ohne Hausnummern",
           "namen": dict(sorted(verz.items()))}
    VERZEICHNIS.parent.mkdir(parents=True, exist_ok=True)
    VERZEICHNIS.write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    audit.tabelle("strassen_gemarkung_abweichungen.tsv", ["name", "quelle", "gemarkung_dienst", "gemarkung_lage", "lon", "lat"], abweichungen)
    mehr = sum(1 for v in verz.values() if len(v) > 1)
    print(f"{len(verz)} Namen, davon {mehr} in mehreren Gemarkungen; {len(abweichungen)} Punkte mit abweichender Gemarkungsangabe")
