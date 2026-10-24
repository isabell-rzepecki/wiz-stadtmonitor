"""3D-Gebäude aus den 3D-Gebäudemodellen LoD2 der HVBG (CityGML) für die 3D-Ansicht.

Das Download-Center der HVBG ist nur interaktiv nutzbar; die CityGML-Dateien je Gemeinde („GB“ Gebäude, „BW“
Bauwerke) werden deshalb von Hand nach data/raw/lod2/ gelegt (auch als ZIP). Je Gebäude bzw. Gebäudeteil werden
Grundriss (GroundSurface, sonst der tiefste Ring des Körpers) und gemessene Höhe übernommen; Dachformen nicht.
Ausgabe je Ortsteil (Lage des Grundrissmittelpunkts in der Gemarkung) nach data/geo/hvgg/gebaeude3d/ (Geobasisdaten,
§ 18 HVGG: Nutzung ohne Einschränkung, Quellenvermerk), damit
die Seite auch ohne Rohdaten im Workflow gebaut werden kann.
"""
import io
import json
import re
import zipfile
from datetime import date

from pyproj import Transformer
from shapely.geometry import Point, Polygon, shape

from . import config

G = config.STADT["gebaeude3d"]
RAW = config.RAW / "lod2"
OUT = config.GEO / "hvgg" / "gebaeude3d"
EXPORT = config.EXPORT / "gebaeude3d"


def dateien():
    """[(name, text)] aller CityGML-Dateien in data/raw/lod2/ (auch in ZIP-Archiven)."""
    out = []
    for p in sorted(RAW.glob("**/*")):
        if p.suffix.lower() == ".gml":
            out.append((p.name, p.read_text(encoding="utf-8", errors="replace")))
        elif p.suffix.lower() == ".zip":
            with zipfile.ZipFile(p) as z:
                for n in z.namelist():
                    if n.lower().endswith(".gml"):
                        out.append((n, io.TextIOWrapper(z.open(n), encoding="utf-8", errors="replace").read()))
    return out


def _ringe(block):
    """[[(x, y, z), …]] der Polygone eines Blocks."""
    out = []
    for pl in re.findall(r"<gml:posList[^>]*>(.*?)</gml:posList>", block, re.S):
        z = [float(v) for v in pl.split()]
        out.append(list(zip(z[0::3], z[1::3], z[2::3])))
    return out


def gebaeude(text):
    """[{id, art, hoehe, grundriss: [[(x, y)]]}] je Gebäude bzw. Gebäudeteil (EPSG:25832)."""
    out = []
    # je Elementart ein eigener Durchlauf: Gebäudeteile stehen innerhalb ihres Gebäudes
    treffer = (m for art in ("Building", "BuildingPart")
               for m in re.finditer(rf"<bldg:({art}) gml:id=\"([^\"]+)\">(.*?)</bldg:{art}>", text, re.S))
    for m in treffer:
        art, gid, block = m.groups()
        # Teile werden einzeln ausgewertet; für das Gebäude selbst nur der Teil vor den Gebäudeteilen
        eigen = re.split(r"<bldg:consistsOfBuildingPart>", block)[0]
        h = re.search(r"<bldg:measuredHeight[^>]*>([\d.]+)</bldg:measuredHeight>", eigen)
        if not h:
            continue
        boden = re.findall(r"<bldg:GroundSurface\b.*?</bldg:GroundSurface>", eigen, re.S)
        ringe = [r for b in boden for r in _ringe(b)]
        if not ringe:  # ohne Bodenfläche: tiefster Ring des Körpers
            alle = _ringe(eigen)
            if not alle:
                continue
            ringe = [min(alle, key=lambda r: sum(p[2] for p in r) / len(r))]
        fkt = re.search(r"<bldg:function>([^<]+)</bldg:function>", eigen)
        out.append({"id": gid, "art": art, "hoehe": round(float(h.group(1)), 1), "funktion": fkt.group(1) if fkt else None,
                    "grundriss": [[(x, y) for x, y, _ in r] for r in ringe]})
    return out


def build():
    liste = dateien()
    if not liste:
        print("3D-Gebäude: keine CityGML-Dateien in data/raw/lod2/; Stand im Repository bleibt")
        _export()
        return
    to_wgs = Transformer.from_crs("EPSG:25832", "EPSG:4326", always_xy=True).transform
    fl = json.loads(config.ORTSBEZIRKE.read_text(encoding="utf-8"))
    flaechen = [(f["properties"].get("slug"), shape(f["geometry"])) for f in fl["features"]]
    je = {}
    for name, text in liste:
        for g in gebaeude(text):
            polys = [[[round(c, 6) for c in to_wgs(x, y)] for x, y in r] for r in g["grundriss"] if len(r) >= 4]
            if not polys:
                continue
            mitte = Polygon(polys[0]).representative_point()
            slug = next((s for s, f in flaechen if f.contains(Point(mitte.x, mitte.y))), None) or "ausserhalb"
            je.setdefault(slug, []).append({"type": "Feature", "properties": {"h": g["hoehe"], "f": g["funktion"], "q": name.rsplit("/", 1)[-1]},
                                            "geometry": {"type": "MultiPolygon", "coordinates": [[p] for p in polys]}})
    OUT.mkdir(parents=True, exist_ok=True)
    for alt in OUT.glob("*.json"):
        alt.unlink()
    for slug, feats in je.items():
        if slug == "ausserhalb":
            continue
        (OUT / f"{slug}.json").write_text(json.dumps({"type": "FeatureCollection", "license": G["lizenz"], "attribution": G["attribution"],
                                                      "stand": date.today().isoformat(), "features": feats},
                                                     ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    index = {"attribution": G["attribution"], "hinweis": G["hinweis"], "dateien": sorted({n.rsplit("/", 1)[-1] for n, _ in liste}),
             "ortsteile": {s: len(f) for s, f in sorted(je.items()) if s != "ausserhalb"}}
    (OUT / "index.json").write_text(json.dumps(index, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"3D-Gebäude: {sum(index['ortsteile'].values())} Gebäude(teile) in {len(index['ortsteile'])} Ortsteilen aus {len(liste)} Dateien")
    _export()


def _export():
    """Kopie in den Export der Seite (lädt je Ortsteil nach)."""
    if not OUT.exists():
        return
    EXPORT.mkdir(parents=True, exist_ok=True)
    for p in OUT.glob("*.json"):
        (EXPORT / p.name).write_bytes(p.read_bytes())
