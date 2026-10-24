"""Geltungsbereiche der Bauleitplanung (Umringe der Bebauungspläne und der FNP-Änderungen) der Stadt.

Nutzungsbedingung des Dienstes (Wortlaut in config/stadt.json, bauleitplanung.nutzung): ohne vertragliche
Vereinbarung mit der Stadt nur für nicht kommerzielle Zwecke. Deshalb:
- Rohdaten nur im Build, abgelegt in data/geo/restricted/ (nicht im Repository, siehe .gitignore);
- ausgeliefert nur als Kartenebene der Seite (data/export/karte/bauleitplanung.json) mit Nutzungshinweis,
  nicht im Datenpaket und nicht als Download;
- im Repository und im Datenpaket bleibt nur die Zuordnung Vorgang → Plannummer (ohne Geometrie).
"""
import hashlib
import json
import re
from html import unescape

from shapely.geometry import Polygon, MultiPolygon, mapping

from . import audit, config, net

RESTRICTED = config.GEO / "restricted"
KARTE = config.EXPORT / "karte" / "bauleitplanung.json"
BL = config.STADT["bauleitplanung"]
# Plannummer in Titeln und Bekanntmachungen: „Nr. 18“, „Nr. 7A“, „Nr. 4-1“, „Nr. 13-1a“, „Nr. 1.1“ (wie in den Kennungen)
PLAN_NR = r"Nr\.\s*(\d+(?:[A-Za-z](?![A-Za-zäöüß]))?(?:[-.]\d+[a-z]?(?![A-Za-zäöüß]))?)"


def plan_nr(text):
    """Plannummer ohne führende Nullen („08“ → „8“), Vergleich ohne Groß- und Kleinschreibung."""
    return re.sub(r"^0+(?=\d)", "", text).lower()


def verfahren_id(art, aenderung, nr=None, gemarkung_nr=None):
    """Kennung eines Planverfahrens, unabhängig davon, ob der Umring schon im Datensatz der Stadt steht."""
    return f"fplan:{aenderung}" if art == "fplan" else f"bplan:{gemarkung_nr or '?'}:{nr}:{aenderung}"


def _feld(f, k):
    m = re.search(rf"<lyr:{k}>(.*?)</lyr:{k}>", f, re.S)
    return unescape(re.sub(r"\s+", " ", m.group(1)).strip()) if m else None


def _ring(text):
    nums = [float(x) for x in text.split()]
    return list(zip(nums[0::2], nums[1::2]))  # Achsenfolge laut Dienst: Länge, Breite


def geometrie(f):
    polys = []
    for p in re.findall(r"<gml:Polygon.*?</gml:Polygon>", f, re.S):
        ext = re.search(r"<gml:exterior>.*?<gml:posList[^>]*>(.*?)</gml:posList>", p, re.S)
        ints = re.findall(r"<gml:interior>.*?<gml:posList[^>]*>(.*?)</gml:posList>", p, re.S)
        if ext:
            polys.append(Polygon(_ring(ext.group(1)), [_ring(i) for i in ints]))
    if not polys:
        return None
    g = polys[0] if len(polys) == 1 else MultiPolygon(polys)
    return g if g.is_valid else g.buffer(0)


def schluessel_bplan(inspireid):
    """gdihom:636016_2246_008_029 → („bplan“, Gemarkungsnr., Plannr., Änderung) mit Zahlen ohne führende Nullen."""
    m = re.search(r"\d{6}_(\d{4})_([^_]+)_(\d+)$", inspireid or "")
    if not m:
        return None
    nr = m.group(2).lstrip("0") or "0"
    return {"art": "bplan", "gemarkung_nr": m.group(1), "nr": nr, "aenderung": int(m.group(3))}


def schluessel_fplan(titel, inspireid):
    """Änderung laut Titel (die Kennung weicht teils ab), Gemarkung laut Kennung (0000 = Blatt ohne Gemarkung)."""
    m = re.search(r"(\d+)\.\s*Änderung", titel or "")
    g = re.search(r"FNP_\d{6}_(\d{4})_", inspireid or "")
    return {"art": "fplan", "aenderung": int(m.group(1)) if m else 0,
            "gemarkung_nr": g.group(1) if g and g.group(1) != "0000" else None}


def lesen(art, gml):
    """[{key, art, titel, gemarkung_nr, nr, aenderung, gueltig_ab, dokumente, geometry}]"""
    out = []
    for f in re.findall(rf"<lyr:{BL['quellen'][art]['element']}\b.*?</lyr:{BL['quellen'][art]['element']}>", gml, re.S):
        titel = _feld(f, "officialtitle")
        k = schluessel_bplan(_feld(f, "inspireid")) if art == "bplan" else schluessel_fplan(titel, _feld(f, "inspireid"))
        g = geometrie(f)
        if not k or g is None:
            continue
        docs = [unescape(u) for u in re.findall(r"<lyr:url>(.*?)</lyr:url>", f, re.S)]
        k.update(titel=titel, gueltig_ab=_feld(f, "validfrom"), dokumente=docs, geometry=g)
        k["key"] = (f"bplan:{k['gemarkung_nr']}:{k['nr']}:{k['aenderung']}" if art == "bplan"
                    else "fplan:" + (_feld(f, "inspireid") or "").rsplit("/", 1)[-1])
        out.append(k)
    return out


def fetch():
    """Umringe abrufen (Zwischenspeicher in data/geo/restricted/), Abruf protokollieren."""
    RESTRICTED.mkdir(parents=True, exist_ok=True)
    for art, q in BL["quellen"].items():
        try:
            body, _ = net.get(q["url"])
            n = body.count(f"<lyr:{q['element']}".encode())
            grund = net.pruefen(f"{art}.gml", body) or ("keine Pläne in der Antwort" if n == 0 else None)
            if grund:  # Fehlerbericht mit Status 200: den einzigen Stand nicht überschreiben
                audit.abruf(art, q["url"], 200, len(body), hashlib.sha256(body).hexdigest(), n, grund)
                print(f"Bauleitplanung ({art}): {grund}; letzter Stand bleibt")
                continue
            net.speichern(RESTRICTED / f"{art}.gml", body)
            audit.abruf(art, q["url"], 200, len(body), hashlib.sha256(body).hexdigest(), n, "")
        except Exception as e:  # Abruf scheitert: letzter Stand bleibt, Fehler steht im Protokoll
            audit.abruf(art, q["url"], getattr(e, "code", ""), "", "", "", str(e)[:200])


def plaene():
    out = []
    for art in BL["quellen"]:
        p = RESTRICTED / f"{art}.gml"
        if p.exists():
            out += lesen(art, p.read_text(encoding="utf-8"))
    return out


def karte(liste):
    """Kartenebene für die Seite: vereinfachte Flächen (etwa 1 m), Koordinaten auf 6 Stellen, mit Nutzungshinweis."""
    feats = []
    for p in liste:
        g = p["geometry"].simplify(0.00001, preserve_topology=True)
        geom = json.loads(json.dumps(mapping(g)), parse_float=lambda x: round(float(x), 6))
        props = {k: p[k] for k in ("key", "art", "titel", "gueltig_ab", "aenderung") if p.get(k) is not None}
        if p["art"] == "bplan":
            props["nr"] = p["nr"]
        if p.get("gemarkung_nr"):
            props["gemarkung_nr"] = p["gemarkung_nr"]
        if p.get("dokumente"):
            props["dokumente"] = p["dokumente"]
        feats.append({"type": "Feature", "properties": props, "geometry": geom})
    data = {"type": "FeatureCollection", "license": BL["nutzung"], "attribution": BL["attribution"],
            "hinweis": "Nur als Kartenebene des Stadtmonitors bereitgestellt, nicht als Datensatz zur Weitergabe. " + BL["nutzung"],
            "source": {a: q["url"] for a, q in BL["quellen"].items()}, "retrieved": net.abrufdatum(*(RESTRICTED / f"{a}.gml" for a in BL["quellen"])),
            "features": feats}
    KARTE.parent.mkdir(parents=True, exist_ok=True)
    KARTE.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    return len(feats)
