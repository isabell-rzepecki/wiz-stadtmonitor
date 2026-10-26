"""Wohnen und Boden: Bodenrichtwerte (BORIS Hessen) und Zensus 2022 je Ortsbezirk und Gemeinde.

- Bodenrichtwerte: Zonen der Gemeinde mit Wert, Art und Entwicklungszustand (Stichtag laut config/stadt.json,
  wohnen.boris); Spanne je Gemarkung für baureifes Land (B) mit Art W… oder M…. Abgleich mit der Referenztabelle der
  Übergabe v0.2 im Audit (bodenrichtwerte_abgleich.tsv). Lizenz: Nutzung ohne Einschränkung, daher im Repository.
- Zensus 2022, Gemeinde: Regionaltabelle Gebäude und Wohnungen (Primärquelle) für die Stadt und ihre Nachbargemeinden.
- Zensus 2022, Ortsbezirk: 100-m-Gitterzellen über ihren Mittelpunkt einer Gemarkung zugeordnet. „–“ (genau null
  oder auf null gesetzt) zählt als „ohne Wert“, nicht als null; KLAMMERN (Aussagewert eingeschränkt) wird gezählt.
  Miete gewichtet mit der Zahl vermieteter Wohnungen, Eigentümerquote als ungewichteter Median der Zellwerte; unter
  `mindestzellen` Zellen mit Wert kein Ausweis. Leerstandsquote nur je Gemeinde (siehe zensus.naeherung).

Abgeleitete Ergebnisse liegen im Repository (data/geo/dl-de-zero/, data/wohnen/); scheitert ein Abruf, bleiben sie
auf dem letzten Stand. Bestandsmiete, Angebotsmiete und Vergleichsmiete werden nie zusammengeführt.
"""
import csv
import hashlib
import io
import json
import re
import statistics
import zipfile
from datetime import date

from pyproj import Transformer
from shapely.geometry import MultiPolygon, Point, Polygon, mapping, shape
from shapely.ops import transform, unary_union

from . import audit, config, kacheln, net

W = config.STADT["wohnen"]
RAW = config.RAW / "wohnen"
BRW_GEO = config.GEO / "dl-de-zero" / "bodenrichtwerte_2024.geojson"
BRW_GEO_JAHR = lambda jahr: config.GEO / "dl-de-zero" / f"bodenrichtwerte_{jahr}.geojson"  # noqa: E731
ZENSUS = config.ROOT / "data" / "wohnen" / "zensus2022.json"  # Gemeinde und Nachbargemeinden (Regionaltabelle)
ZENSUS_OB = config.ROOT / "data" / "wohnen" / "zensus_ortsbezirk.json"  # Ortsbezirke aus dem Gitter (Näherung)
REFERENZ = config.ROOT / "docs" / "uebergabe-v0.2" / "material" / "bodenrichtwerte_2024_spannen_gemarkung.tsv"
OUT = config.EXPORT / "wohnen.json"
KARTE = config.EXPORT / "karte" / "bodenrichtwerte.json"
ZONEN_KACHELN = config.EXPORT / "karte" / "bodenrichtwerte_zonen.pmtiles"  # alle Stichtage mit Datendienst, Attribut stichtag
GMDE = config.STADT["stadt"]["gemeindeschluessel"]  # 06636016
ARS = config.STADT["stadt"]["ars"]
ALTER = 365 * 86400


def _gemarkungen():
    fl = json.loads(config.ORTSBEZIRKE.read_text(encoding="utf-8"))
    return [(f["properties"], shape(f["geometry"])) for f in fl["features"]]


def _laden(ziel, url, quelle):
    if net.gueltig(ziel, ALTER):
        return True
    try:
        body, _ = net.get(url, tries=2)
    except Exception as e:
        audit.abruf(quelle, url, getattr(e, "code", ""), "", "", "", str(e)[:200])
        print(f"{quelle}: Abruf gescheitert ({e}); Ergebnisse bleiben auf dem letzten Stand")
        return False
    grund = net.pruefen(ziel, body)
    if grund:
        audit.abruf(quelle, url, 200, len(body), hashlib.sha256(body).hexdigest(), "", grund)
        print(f"{quelle}: {grund}; Ergebnisse bleiben auf dem letzten Stand")
        return False
    net.speichern(ziel, body)
    audit.abruf(quelle, url, 200, len(body), hashlib.sha256(body).hexdigest(), "", "")
    return True


def fetch():
    RAW.mkdir(parents=True, exist_ok=True)
    w, s, o, n = unary_union([g for _, g in _gemarkungen()]).bounds
    bbox = f"&BBOX={s - 0.005},{w - 0.005},{n + 0.005},{o + 0.005},urn:ogc:def:crs:EPSG::4326"
    _laden(RAW / f"boris_{W['boris']['stichtag'][:4]}.gml", W["boris"]["url"] + bbox, "boris")
    for v in W["boris_verlauf"]["stichtage"]:  # frühere Stichtage, gleicher Ausschnitt
        _laden(RAW / f"boris_{v['stichtag'][:4]}.gml", v["url"] + bbox, "boris")
    _laden(RAW / "regionaltabelle.xlsx", W["zensus"]["regionaltabelle"], "zensus_gem")
    for k, g in W["zensus"]["gitter"].items():
        _laden(RAW / f"{k}.zip", g["url"], "zensus_gitter")


# --- Bodenrichtwerte ------------------------------------------------------------------------------------------

def _feld(f, pfad):
    m = re.search(r"".join(rf"<boris:{p}>.*?" for p in pfad[:-1]) + rf"<boris:{pfad[-1]}>(.*?)</boris:{pfad[-1]}>", f, re.S)
    return m.group(1).strip() if m else None


def _polygon(text, utm):
    def ring(t):
        z = [float(x) for x in t.split()]
        return [utm(x, y) for x, y in zip(z[0::2], z[1::2])]
    polys = []
    for p in re.findall(r"<gml:Polygon.*?</gml:Polygon>", text, re.S):
        ext = re.search(r"<gml:exterior>.*?<gml:posList[^>]*>(.*?)</gml:posList>", p, re.S)
        ints = re.findall(r"<gml:interior>.*?<gml:posList[^>]*>(.*?)</gml:posList>", p, re.S)
        if ext:
            polys.append(Polygon(ring(ext.group(1)), [ring(i) for i in ints]))
    if not polys:
        return None
    g = polys[0] if len(polys) == 1 else MultiPolygon(polys)
    return g if g.is_valid else g.buffer(0)


def zonen(stichtag=None):
    """Zonen der Gemeinde zum Stichtag (Standard: wohnen.boris.stichtag) aus den Rohdaten; None ohne Rohdaten."""
    p = RAW / f"boris_{(stichtag or W['boris']['stichtag'])[:4]}.gml"
    if not p.exists():
        return None
    utm = Transformer.from_crs("EPSG:25832", "EPSG:4326", always_xy=True).transform
    out = []
    for f in re.findall(r"<boris:BR_BodenrichtwertZonal\b.*?</boris:BR_BodenrichtwertZonal>", p.read_text(encoding="utf-8"), re.S):
        if (_feld(f, ["kreis"]), _feld(f, ["BR_Gemeindekennzeichen", "gemeinde"])) != (GMDE[3:5], GMDE[5:]):
            continue
        g = _polygon(f, utm)
        wert = _feld(f, ["bodenrichtwert"])
        if g is None or wert is None:
            continue
        nr = _feld(f, ["BR_Gemarkung", "nummer"]) or ""
        out.append({"nummer": _feld(f, ["bodenrichtwertNummer"]), "wert": float(wert), "stichtag": _feld(f, ["stichtag"]),
                    "entwicklungszustand": _feld(f, ["entwicklungszustand"]), "art": _feld(f, ["BR_Nutzung", "art"]),
                    "gemarkung_nr": nr[-4:], "gemarkung": _feld(f, ["BR_Gemarkung", "name"]), "geometry": g})
    return out


def _wohnbauland(z):
    return z["entwicklungszustand"] == "B" and (z["art"] or "")[:1] in ("W", "M")


def spannen(liste):
    """{gemarkung_nr: {min, max, zonen, arten}} für baureifes Land mit Art W…/M…, dazu „stadt“."""
    out = {}
    for z in filter(_wohnbauland, liste):
        for k in (z["gemarkung_nr"], "stadt"):
            e = out.setdefault(k, {"min": z["wert"], "max": z["wert"], "zonen": 0, "arten": set()})
            e["min"], e["max"] = min(e["min"], z["wert"]), max(e["max"], z["wert"])
            e["zonen"] += 1
            e["arten"].add(z["art"])
    return {k: {**v, "arten": sorted(v["arten"])} for k, v in out.items()}


def zonen_mit_stand(stichtag, url):
    """Zonen zum Stichtag: aus den Rohdaten (dann auch ins Repository geschrieben) oder aus dem Stand im Repository."""
    jahr = stichtag[:4]
    ziel = BRW_GEO_JAHR(jahr)
    liste = zonen(stichtag)
    if not liste:  # keine Rohdaten oder keine Zonen gelesen: Stand im Repository
        if not ziel.exists():
            return None
        d = json.loads(ziel.read_text(encoding="utf-8"))
        return [{**f["properties"], "geometry": shape(f["geometry"])} for f in d["features"]]
    feats = [{"type": "Feature", "properties": {k: v for k, v in z.items() if k != "geometry"},
              "geometry": json.loads(json.dumps(mapping(z["geometry"].simplify(0.00001, preserve_topology=True))),
                                     parse_float=lambda x: round(float(x), 6))} for z in liste]
    attribution = re.sub(r"Stichtag \d\d\.\d\d\.\d{4}", f"Stichtag {stichtag[8:10]}.{stichtag[5:7]}.{jahr}", W["boris"]["attribution"])
    ziel.write_text(json.dumps({"type": "FeatureCollection", "license": W["boris"]["lizenz"], "attribution": attribution,
                                "source": url, "stichtag": stichtag, "retrieved": net.abrufdatum(RAW / f"boris_{jahr}.gml"),
                                "features": feats}, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    return liste


def verlauf():
    """{stichtag: {gemarkung_nr: Spanne}} für den aktuellen und die früheren Stichtage (Wohn- und Mischbauland)."""
    out = {}
    for v in [*W["boris_verlauf"]["stichtage"], {"stichtag": W["boris"]["stichtag"], "url": W["boris"]["url"]}]:
        liste = zonen_mit_stand(v["stichtag"], v["url"])
        if liste:
            out[v["stichtag"]] = spannen(liste)
    return dict(sorted(out.items()))


def _boris(gem):
    liste = zonen_mit_stand(W["boris"]["stichtag"], W["boris"]["url"])
    if not liste:
        return None
    sp = spannen(liste)
    # Abgleich mit der Referenztabelle der Übergabe (abgeleitet, ungeprüft)
    namen = {p["gmk_nr"]: p["gemarkung"] for p, _ in gem}
    ref = {r["gemarkung"]: r for r in csv.DictReader(REFERENZ.open(encoding="utf-8"), delimiter="\t")} if REFERENZ.exists() else {}
    zeilen = []
    for nr, name in sorted(namen.items(), key=lambda x: x[1]):
        e, r = sp.get(nr), ref.get(name, {})
        eig = (e["min"], e["max"], e["zonen"]) if e else ("", "", 0)
        rv = (float(r["brw_min_eur_m2"]), float(r["brw_max_eur_m2"]), int(r["anzahl_zonen"])) if r else ("", "", "")
        zeilen.append({"gemarkung": name, "min": eig[0], "max": eig[1], "zonen": eig[2], "ref_min": rv[0], "ref_max": rv[1],
                       "ref_zonen": rv[2], "abgleich": "gleich" if r and eig == rv else ("keine Referenz" if not r else "abweichend")})
    audit.tabelle("bodenrichtwerte_abgleich.tsv", ["gemarkung", "min", "max", "zonen", "ref_min", "ref_max", "ref_zonen", "abgleich"], zeilen)
    # Kartenebene: baureifes Land, alle Arten
    klassen = W["boris"]["klassen"]
    feats = []
    for z in liste:
        if z["entwicklungszustand"] != "B":
            continue
        geom = z["geometry"].simplify(0.00001, preserve_topology=True)
        feats.append({"type": "Feature", "properties": {"wert": z["wert"], "art": z["art"], "gemarkung": z["gemarkung"],
                                                        "klasse": sum(z["wert"] >= k for k in klassen)},
                      "geometry": json.loads(json.dumps(mapping(geom)), parse_float=lambda x: round(float(x), 6))})
    KARTE.parent.mkdir(parents=True, exist_ok=True)
    KARTE.write_text(json.dumps({"type": "FeatureCollection", "attribution": W["boris"]["attribution"], "stichtag": W["boris"]["stichtag"],
                                 "klassen": klassen, "features": feats}, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    abw = sum(1 for z in zeilen if z["abgleich"] == "abweichend")
    print(f"Bodenrichtwerte: {len(liste)} Zonen, {len(feats)} baureifes Land; Abgleich: {abw} Gemarkungen abweichend")
    return {nr: v for nr, v in sp.items()}


# --- Zensus ---------------------------------------------------------------------------------------------------

def _zahl(v):
    """(Wert, eingeschränkt) aus Zensusangaben: „5,09“, „(5,50)“ → eingeschränkt, „–“ → None."""
    if v is None:
        return None, False
    s = str(v).strip()
    eing = s.startswith("(")
    s = s.strip("()").replace(",", ".")
    try:
        return float(s), eing
    except ValueError:
        return None, False


def gemeinden():
    p = RAW / "regionaltabelle.xlsx"
    if not p.exists():
        return None
    import openpyxl
    ws = openpyxl.load_workbook(p, read_only=True)["CSV-Wohnungen"]
    zeilen = ws.iter_rows(values_only=True)
    kopf = {h: i for i, h in enumerate(next(zeilen))}
    out = []
    for r in zeilen:
        if str(r[kopf["_RS"]]) not in W["zensus"]["vergleich"]:
            continue
        e = {"ars": str(r[kopf["_RS"]]), "name": r[kopf["Name"]]}
        for k, sp in (("nettokaltmiete_eur_m2", "QMMIETE"), ("leerstandsquote_pct", "LEQ"), ("eigentuemerquote_pct", "ETQ"),
                      ("leerstehende_wohnungen", "LEERSTAND_INSGESAMT")):
            v, eing = _zahl(r[kopf[sp]])
            e[k] = v
            if eing:
                e.setdefault("eingeschraenkt", []).append(k)
        out.append(e)
    return sorted(out, key=lambda e: W["zensus"]["vergleich"].index(e["ars"]))


def ortsbezirke(gem):
    """Kennzahlen je Gemarkung aus den 100-m-Gitterzellen; None, wenn Rohdaten fehlen."""
    if not all((RAW / f"{k}.zip").exists() for k in W["zensus"]["gitter"]):
        return None
    to3035 = Transformer.from_crs("EPSG:4326", "EPSG:3035", always_xy=True).transform
    flaechen = [(p["gmk_nr"], transform(to3035, g)) for p, g in gem]
    x0, y0, x1, y1 = unary_union([g for _, g in flaechen]).bounds
    zuordnung = {}
    out = {nr: {} for nr, _ in flaechen}
    for k, g in W["zensus"]["gitter"].items():
        with zipfile.ZipFile(RAW / f"{k}.zip") as z:
            name = next(n for n in z.namelist() if n.endswith(g["datei"]))
            werte = {nr: [] for nr, _ in flaechen}
            ohne, eing = {nr: 0 for nr, _ in flaechen}, {nr: 0 for nr, _ in flaechen}
            for r in csv.DictReader(io.TextIOWrapper(z.open(name), encoding="utf-8-sig"), delimiter=";"):
                x, y = float(r["x_mp_100m"]), float(r["y_mp_100m"])
                if not (x0 <= x <= x1 and y0 <= y <= y1):
                    continue
                cid = r["GITTER_ID_100m"]
                if cid not in zuordnung:
                    zuordnung[cid] = next((nr for nr, f in flaechen if f.contains(Point(x, y))), None)
                nr = zuordnung[cid]
                if nr is None:
                    continue
                v, _ = _zahl(r[g["wert"]])
                if v is None:
                    ohne[nr] += 1
                    continue
                eing[nr] += r.get("werterlaeuternde_Zeichen") == "KLAMMERN"
                werte[nr].append((v, float(_zahl(r[g["gewicht"]])[0] or 0) if g.get("gewicht") else 1))
        for nr in out:
            ws = werte[nr]
            e = {"zellen": len(ws), "zellen_ohne_wert": ohne[nr], "zellen_eingeschraenkt": eing[nr]}
            if len(ws) < W["zensus"]["mindestzellen"]:
                e.update(wert=None, grund=f"weniger als {W['zensus']['mindestzellen']} Zellen mit Wert")
            elif g.get("gewicht"):
                summe = sum(w for _, w in ws)
                e.update(wert=round(sum(v * w for v, w in ws) / summe, 2) if summe else None, wohnungen=int(summe), methode="gewichtetes Mittel")
            else:
                e.update(wert=round(statistics.median(v for v, _ in ws), 1), methode="Median der Zellwerte")
            out[nr][k] = e
    return out


def zonen_kacheln(stichtage):
    """Zonen aller Stichtage als Vektorkacheln (Seite „Wohnen und Eigentum“), je Zone mit Stichtag, Wert, Art und Zustand."""
    feats = []
    for st in stichtage:
        p = BRW_GEO_JAHR(st[:4])
        if p.exists():
            for f in json.loads(p.read_text(encoding="utf-8"))["features"]:
                pr = f["properties"]
                feats.append({"type": "Feature", "geometry": f["geometry"],
                              "properties": {"stichtag": st, "wert": pr["wert"], "art": pr.get("art"), "ez": pr.get("entwicklungszustand"),
                                             "gemarkung": pr.get("gemarkung")}})
    if feats:
        kacheln.schreiben(feats, ZONEN_KACHELN, "bodenrichtwerte", 11, 15, attribution=W["boris"]["attribution"])


AUDIT_SPALTEN = ["bereich", "ebene", "schluessel", "name", "kennzahl", "stichtag", "wert", "status", "quelle"]


def pruefprotokoll(zensus, vl, by_nr):
    """audit/wohnen_<datum>.tsv: jede ausgewiesene Zahl mit Ebene, Stichtag, Status (Wert, Lücke mit Grund) und Quelle."""
    zeilen = []
    for g in (zensus or {}).get("gemeinden", []):
        for k in ("nettokaltmiete_eur_m2", "leerstandsquote_pct", "eigentuemerquote_pct"):
            zeilen.append({"bereich": "Zensus", "ebene": "Gemeinde", "schluessel": g["ars"], "name": g["name"], "kennzahl": k,
                           "stichtag": W["zensus"]["stichtag"], "wert": g.get(k),
                           "status": "Lücke (ohne Wert)" if g.get(k) is None else "eingeschränkt" if k in g.get("eingeschraenkt", []) else "Wert",
                           "quelle": "Regionaltabelle Gebäude und Wohnungen"})
    for nr, e in (zensus or {}).get("ortsbezirke", {}).items():
        for k, m in e.items():
            zeilen.append({"bereich": "Zensus", "ebene": "Ortsbezirk (Näherung)", "schluessel": nr, "name": by_nr.get(nr, {}).get("name", nr),
                           "kennzahl": k, "stichtag": W["zensus"]["stichtag"], "wert": m.get("wert"),
                           "status": f"Wert ({m.get('methode')}, {m['zellen']} Zellen, {m['zellen_ohne_wert']} ohne Wert)" if m.get("wert") is not None
                           else f"Lücke ({m.get('grund', 'ohne Wert')})", "quelle": "100-m-Gitter"})
    for st, sp in vl.items():
        for nr, v in sp.items():
            zeilen.append({"bereich": "Bodenrichtwerte", "ebene": "Stadt" if nr == "stadt" else "Gemarkung", "schluessel": nr,
                           "name": by_nr.get(nr, {}).get("name", nr), "kennzahl": "Spanne Wohn- und Mischbauland (€/m²)", "stichtag": st,
                           "wert": f"{v['min']:g}–{v['max']:g}", "status": f"Wert ({v['zonen']} Zonen)", "quelle": "BORIS Hessen (WFS)"})
    for k in W.get("kontext", []):
        zeilen.append({"bereich": "Rechtsrahmen", "ebene": "Stadt", "schluessel": "", "name": k["thema"], "kennzahl": "Text",
                       "stichtag": k["stand"], "wert": "", "status": "datierter Text", "quelle": k["link"]})
    audit.tabelle(f"wohnen_{date.today().isoformat()}.tsv", AUDIT_SPALTEN, zeilen)


def build():
    gem = _gemarkungen()
    sp = _boris(gem)
    alt = json.loads(ZENSUS.read_text(encoding="utf-8")) if ZENSUS.exists() else {}
    # Ortsbezirke: eigene Datei; Übergang aus dem früheren gemeinsamen Stand in zensus2022.json
    alt_ob = json.loads(ZENSUS_OB.read_text(encoding="utf-8")) if ZENSUS_OB.exists() else {"ortsbezirke": alt.pop("ortsbezirke", {})}
    gd, ob = gemeinden(), ortsbezirke(gem)
    kopf = {"license": "dl-de/by-2.0", "attribution": W["zensus"]["attribution"], "stichtag": W["zensus"]["stichtag"]}
    ZENSUS.parent.mkdir(parents=True, exist_ok=True)
    if gd is not None:
        alt = {**kopf, "retrieved": net.abrufdatum(RAW / "regionaltabelle.xlsx"), "gemeinden": gd}
        ZENSUS.write_text(json.dumps(alt, ensure_ascii=False, indent=1), encoding="utf-8")
    if ob is not None:
        namen = {p["gmk_nr"]: p["gemarkung"] for p, _ in gem}
        alt_ob = {**kopf, "retrieved": net.abrufdatum(*(RAW / f"{k}.zip" for k in W["zensus"]["gitter"])),
                  "kennzeichnung": "Näherung", "naeherung": W["zensus"]["naeherung"], "mindestzellen": W["zensus"]["mindestzellen"],
                  "gemarkungen": {nr: namen.get(nr) for nr in ob}, "ortsbezirke": ob}
        ZENSUS_OB.write_text(json.dumps(alt_ob, ensure_ascii=False, indent=1), encoding="utf-8")
    if not alt and not alt_ob.get("ortsbezirke"):
        print("Zensus: keine Rohdaten und kein Stand im Repository")
    if alt:  # für die Ausgabe zusammengeführt (Gemeinde und Ortsbezirke getrennt gekennzeichnet)
        alt = {**alt, "naeherung": W["zensus"]["naeherung"], "ortsbezirke": alt_ob.get("ortsbezirke", {})}
    by_nr = {o["gemarkung_nr"]: o for o in config.STADT["ortsteile"]}
    vl = verlauf()
    daten = {"generated_at": date.today().isoformat(),
             "boris": {"stichtag": W["boris"]["stichtag"], "attribution": W["boris"]["attribution"], "filter": W["boris"]["filter"],
                       "spannen": {by_nr[k]["slug"] if k in by_nr else k: v for k, v in (sp or {}).items()}},
             # Verlauf der Spannen je Ortsbezirk über die Stichtage mit Datendienst (2026 nur als Karte)
             "boris_verlauf": {"stichtage": list(vl), "hinweis": W["boris_verlauf"]["_hinweis"],
                               "spannen": {by_nr[k]["slug"] if k in by_nr else k: {st: sp_[k] for st, sp_ in vl.items() if k in sp_}
                                           for k in sorted({k for sp_ in vl.values() for k in sp_})}},
             "zensus": {k: alt.get(k) for k in ("stichtag", "attribution", "naeherung", "gemeinden")} if alt else None}
    if alt:
        daten["zensus"]["ortsbezirke"] = {by_nr[k]["slug"]: v for k, v in alt.get("ortsbezirke", {}).items() if k in by_nr}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(daten, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    pruefprotokoll(alt, vl, by_nr)
    zonen_kacheln(vl)
    wiz = next((g for g in (alt.get("gemeinden") or []) if g["ars"] == ARS), None) if alt else None
    if wiz and alt.get("ortsbezirke"):  # Plausibilität: gewichtete Gittermiete aller Ortsbezirke gegen den Gemeindewert
        m = [e["miete"] for e in alt["ortsbezirke"].values() if e.get("miete", {}).get("wert")]
        gitter = sum(e["wert"] * e["wohnungen"] for e in m) / max(1, sum(e["wohnungen"] for e in m))
        print(f"Plausibilität Miete: Gitter (ausgewiesene Ortsbezirke) {gitter:.2f} €/m², Gemeinde {wiz['nettokaltmiete_eur_m2']} €/m²")
    print(f"Wohnen und Boden: Zensus-Gemeinde {wiz['nettokaltmiete_eur_m2'] if wiz else '–'} €/m², "
          f"{len((alt or {}).get('ortsbezirke', {}))} Ortsbezirke aus dem Gitter")
    return daten
