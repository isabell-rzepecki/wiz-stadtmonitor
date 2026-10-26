"""Gebäude der Gemeinde für die 2D- und 3D-Karte der Seite „Wohnen und Eigentum“.

- Grundrisse: alle Gebäude aus ALKIS vereinfacht (HVBG, WFS ave:GebaeudeBauwerk, Filter auf die Gemeinde, seitenweise per
  POST). Schlüssel ist die ALKIS-OID; sie ist in 2D und 3D dieselbe und dient später der Erfassung (W4).
- Höhe: gemessene Höhe aus den 3D-Gebäudemodellen LoD2 und den Bauwerken (gebaeude3d, Download-Center der HVBG), je
  Gebäude der höchste Wert des Gebäudes und seiner Teile. Zuordnung zuerst über die OID (LoD2: 16 Zeichen, ALKIS
  vereinfacht: dieselben 16 Zeichen und „BL“), sonst räumlich (Punkt im LoD2-Grundriss liegt im ALKIS-Grundriss).
  Ohne Treffer gilt die Standardhöhe aus config/stadt.json (gebaeude.standardhoehe_m), gekennzeichnet als „geschätzt“.
- Ausgabe: data/geo/hvgg/gebaeude.geojson (im Repository, Geobasisdaten nach § 18 HVGG ohne Einschränkung), daraus die
  Vektorkacheln data/export/karte/gebaeude.pmtiles; Protokoll der Zuordnung in audit/lod2_alkis_zuordnung.tsv.
Keine Eigentumsangaben: Eigentum und Vermietung kommen nur aus der geprüften Erfassung (W5), nicht aus ALKIS.
"""
import hashlib
import json
import re
import time

from pyproj import Transformer
from shapely import STRtree
from shapely.geometry import MultiPolygon, Polygon, mapping, shape

from . import audit, config, gebaeude3d, geo, kacheln, net

G = config.STADT["gebaeude"]
RAW = config.RAW / "gebaeude"
OUT = config.GEO / "hvgg" / "gebaeude.geojson"
KACHELN = config.EXPORT / "karte" / "gebaeude.pmtiles"
ALTER = 30 * 86400
GMDE = config.STADT["stadt"]["gemeindeschluessel"]

ANFRAGE = """<wfs:GetFeature service="WFS" version="2.0.0" count="{n}" startIndex="{start}" xmlns:wfs="http://www.opengis.net/wfs/2.0"
 xmlns:fes="http://www.opengis.net/fes/2.0" xmlns:ave="http://repository.gdi-de.org/schemas/adv/produkt/alkis-vereinfacht/2.0">
 <wfs:Query typeNames="ave:GebaeudeBauwerk"><fes:Filter>
  <fes:PropertyIsEqualTo><fes:ValueReference>ave:gmdschl</fes:ValueReference><fes:Literal>{gmde}</fes:Literal></fes:PropertyIsEqualTo>
 </fes:Filter></wfs:Query></wfs:GetFeature>"""


def _seiten():
    return sorted(RAW.glob("alkis_*.gml"), key=lambda p: int(p.stem.split("_")[1]))


def fetch():
    """Alle Seiten neu laden, wenn der Stand älter als 30 Tage ist; nur vollständig übernehmen (sonst letzter Stand)."""
    RAW.mkdir(parents=True, exist_ok=True)
    seiten = _seiten()
    if seiten and all(net.gueltig(p, ALTER) for p in seiten):
        return
    url = config.STADT["eigentum"]["alkis_wfs"]
    neu, start = [], 0
    try:
        while True:
            body = net.post(url, ANFRAGE.format(n=G["seite"], start=start, gmde=GMDE).encode("utf-8"))
            grund = net.pruefen("seite.gml", body)
            if grund:
                raise ValueError(grund)
            n = body.count(b"<GebaeudeBauwerk ")
            neu.append((start, body))
            audit.abruf("alkis_gebaeude_alle", f"{url} (POST, startIndex {start})", 200, len(body), hashlib.sha256(body).hexdigest(), n, "")
            if n < G["seite"]:
                break
            start += G["seite"]
            time.sleep(1)
    except Exception as e:  # Abruf unvollständig: letzter Stand bleibt
        audit.abruf("alkis_gebaeude_alle", url, getattr(e, "code", ""), "", "", "", str(e)[:200])
        print(f"Gebäude (ALKIS): Abruf gescheitert ({e}); letzter Stand bleibt")
        return
    for p in seiten:
        p.unlink()
    for start, body in neu:
        net.speichern(RAW / f"alkis_{start}.gml", body)


def alkis():
    """[{oid, funktion, geometry (EPSG:25832)}] aus den Rohdaten; [] ohne Rohdaten."""
    out = []
    for p in _seiten():
        for f in re.findall(r"<GebaeudeBauwerk\b.*?</GebaeudeBauwerk>", p.read_text(encoding="utf-8"), re.S):
            oid = re.search(r"<oid>([^<]+)</oid>", f)
            polys = []
            for pl in re.findall(r"<gml:Polygon\b.*?</gml:Polygon>", f, re.S):
                ringe = [[(float(a), float(b)) for a, b in zip(*[iter(t.split())] * 2)]
                         for t in re.findall(r"<gml:posList[^>]*>(.*?)</gml:posList>", pl, re.S)]
                if ringe and len(ringe[0]) >= 4:
                    polys.append(Polygon(ringe[0], ringe[1:]))
            if not oid or not polys:
                continue
            g = polys[0] if len(polys) == 1 else MultiPolygon(polys)
            fkt = re.search(r"<funktion>([^<]*)</funktion>", f)
            out.append({"oid": oid.group(1), "funktion": fkt.group(1) if fkt else None, "geometry": g if g.is_valid else g.buffer(0)})
    return out


def lod2_text(text, art="LoD2"):
    """{oid16: {h, punkt (EPSG:25832), art, id}} je Gebäude einer CityGML-Datei: höchster gemessener Wert von Gebäude
    und Gebäudeteilen; Punkt im Grundriss (Bodenfläche, sonst erster Ring)."""
    out = {}
    for m in re.finditer(r'<bldg:Building gml:id="([^"]+)">(.*?)</bldg:Building>', text, re.S):
        gid, block = m.groups()
        hs = [float(h) for h in re.findall(r"<bldg:measuredHeight[^>]*>([\d.]+)</bldg:measuredHeight>", block)]
        if not hs:
            continue
        boden = [r for b in re.findall(r"<bldg:GroundSurface\b.*?</bldg:GroundSurface>", block, re.S) for r in gebaeude3d._ringe(b)]
        ring = (boden or gebaeude3d._ringe(block) or [[]])[0]
        punkt = Polygon([(x, y) for x, y, _ in ring]).representative_point() if len(ring) >= 4 else None
        out[gid[:16]] = {"h": round(max(hs), 1), "punkt": punkt, "art": art, "id": gid}
    return out


def lod2():
    """lod2_text für alle Dateien in data/raw/lod2/ (Gebäude „LoD2“ und Bauwerke „BW“)."""
    out = {}
    for name, text in gebaeude3d.dateien():
        out.update(lod2_text(text, "Bauwerk" if name.rsplit("/", 1)[-1].startswith("BW_") else "LoD2"))
    return out


def zuordnen(geb, hoehen):
    """Höhe je ALKIS-Gebäude: (Zuordnung, LoD2-ID, Höhe, Herkunft der Höhe). Ändert geb nicht."""
    ergebnis, frei = {}, dict(hoehen)
    for g in geb:
        h = frei.pop(g["oid"][:16], None)
        if h:
            ergebnis[g["oid"]] = ("gleich", h["id"], h["h"], h["art"])
    offen = [g for g in geb if g["oid"] not in ergebnis]
    if offen and frei:
        baum = STRtree([g["geometry"] for g in offen])
        for h in frei.values():
            if h["punkt"] is None:
                continue
            for i in baum.query(h["punkt"], predicate="within"):
                oid = offen[int(i)]["oid"]
                if oid not in ergebnis or ergebnis[oid][2] < h["h"]:  # mehrere Teile im Grundriss: der höchste zählt
                    ergebnis[oid] = ("räumlich", h["id"], h["h"], h["art"])
    for g in geb:
        ergebnis.setdefault(g["oid"], ("ohne Treffer", "", float(G["standardhoehe_m"]), "geschätzt"))
    return ergebnis


def aktuell():
    """True, wenn das Ergebnis jünger ist als alle Rohdaten (ALKIS und LoD2)."""
    roh = [*_seiten(), *(p for p in gebaeude3d.RAW.glob("**/*") if p.suffix.lower() in (".gml", ".zip"))]
    return OUT.exists() and roh and all(p.stat().st_mtime < OUT.stat().st_mtime for p in roh)


def build():
    if not _seiten() or aktuell():
        print("Gebäude: " + ("Rohdaten unverändert" if _seiten() else "keine ALKIS-Rohdaten") + "; Stand im Repository bleibt")
        return export()
    geb = alkis()
    hoehen = lod2()
    if not geb:
        print("Gebäude: keine Gebäude gelesen; Stand im Repository bleibt")
        return export()
    zu = zuordnen(geb, hoehen)
    wgs = Transformer.from_crs("EPSG:25832", "EPSG:4326", always_xy=True).transform
    ot = geo.Ortsteile() if config.ORTSBEZIRKE.exists() else None
    feats, zeilen = [], []
    for g in sorted(geb, key=lambda x: x["oid"]):
        z, lid, h, quelle = zu[g["oid"]]
        g84 = kacheln.projizieren(g["geometry"], wgs)
        p = g84.representative_point()
        o = ot.locate(p.x, p.y) if ot else None
        feats.append({"type": "Feature",
                      "properties": {"id": g["oid"], "f": g["funktion"], "h": h, "hq": quelle, "z": z, "o": (o or {}).get("slug")},
                      "geometry": json.loads(json.dumps(mapping(g84)), parse_float=lambda x: round(float(x), 6))})
        zeilen.append({"alkis_oid": g["oid"], "lod2_id": lid, "zuordnung": z, "hoehe_m": h, "hoehe_quelle": quelle})
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"type": "FeatureCollection", "license": G["lizenz"], "attribution": G["attribution"],
                               "standardhoehe_m": G["standardhoehe_m"], "features": feats},
                              ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    audit.tabelle("lod2_alkis_zuordnung.tsv", ["alkis_oid", "lod2_id", "zuordnung", "hoehe_m", "hoehe_quelle"], zeilen)
    zaehl = {k: sum(1 for z in zeilen if z["zuordnung"] == k) for k in ("gleich", "räumlich", "ohne Treffer")}
    print(f"Gebäude: {len(feats)} aus ALKIS; Höhe aus LoD2 über die OID {zaehl['gleich']}, räumlich {zaehl['räumlich']}, "
          f"geschätzt {zaehl['ohne Treffer']}")
    return export()


def index(features):
    """Je Ortsteil: Zahl der Gebäude, Herkunft der Höhe und Ausschnitt des bebauten Kerns (5- bis 95-Prozent-Bereich der
    Gebäudelagen, damit einzelne entfernte Gebäude den Ausschnitt nicht aufweiten)."""
    je = {}
    for f in features:
        p = f["properties"]
        e = je.setdefault(p.get("o") or "ausserhalb", {"gebaeude": 0, "hoehe_geschaetzt": 0, "punkte": []})
        e["gebaeude"] += 1
        e["hoehe_geschaetzt"] += p["hq"] == "geschätzt"
        e["punkte"].append(shape(f["geometry"]).representative_point())
    for e in je.values():
        xs, ys = sorted(pt.x for pt in e["punkte"]), sorted(pt.y for pt in e["punkte"])
        q = lambda a, t: a[min(len(a) - 1, int(t * len(a)))]  # noqa: E731
        e["kern"] = [round(q(xs, 0.05), 5), round(q(ys, 0.05), 5), round(q(xs, 0.95), 5), round(q(ys, 0.95), 5)]
        del e["punkte"]
    return dict(sorted(je.items()))


def export(ziel=KACHELN, nur=None):
    """Vektorkacheln und Übersicht aus dem Stand im Repository; nur = Ortsteil (für Testdaten)."""
    if not OUT.exists():
        return None
    d = json.loads(OUT.read_text(encoding="utf-8"))
    feats = [f for f in d["features"] if not nur or f["properties"].get("o") == nur]
    n = kacheln.schreiben(feats, ziel, "gebaeude", *G["zoom"], attribution=G["attribution"])
    ziel.with_name("gebaeude_index.json").write_text(json.dumps({
        "attribution": G["attribution"], "lizenz": G["lizenz"], "standardhoehe_m": G["standardhoehe_m"], "zoom": G["zoom"],
        "ortsteile": index(feats)}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"Gebäude: {n} Kacheln in {ziel.name} ({ziel.stat().st_size // 1024} KB)")
    return n
