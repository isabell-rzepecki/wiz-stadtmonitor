"""Zuzug und Wegzug aus der amtlichen Wanderungsstatistik (Hessisches Statistisches Landesamt).

- Je Gemeinde des Kreises: Bevölkerung am Jahresanfang und -ende, Geborene, Gestorbene, Zu- und Fortzüge über die
  Gemeindegrenze, aus den Jahresberichten „Bevölkerung in Hessen … nach Gemeinden“ (Tabelle der
  Bevölkerungsvorgänge). Ältere Berichte führen Männer, Frauen und insgesamt (Zeile „I“); übernommen wird „I“.
  Der Bericht 2018 ist mit verschobener Zeichenkodierung gesetzt; der Text wird zurückgerechnet.
- Kreis: Wanderung über die Kreisgrenze nach Herkunfts- und Zielgebieten (Matrix je Kreis, andere Bundesländer,
  Ausland). „•“ (Geheimhaltung) wird als fehlender Wert übernommen, nicht als null.
Geometrien (Gemeinden des Kreises, Kreismittelpunkte) aus den Digitalen Verwaltungsgrenzen (gemarkungen.py).
Ergebnisse liegen im Repository (data/wanderung/, data/geo/dl-de-zero/); scheitert ein Abruf, bleibt dieser Stand.
Zahlen je Ortsteil und Ströme zwischen einzelnen Gemeinden sind nicht veröffentlicht und werden nicht geschätzt.
"""
import json
import re
import subprocess
import zipfile
from datetime import date

from pyproj import Transformer
from shapely.geometry import mapping, shape
from shapely.ops import transform, unary_union

from . import audit, config, gemarkungen, net

W = config.STADT["wanderung"]
RAW = config.RAW / "wanderung"
OUT_REPO = config.ROOT / "data" / "wanderung" / "wanderung.json"
GEO = config.GEO / "dl-de-zero" / "wanderung_geo.json"
OUT = config.EXPORT / "wanderung.json"
FELDER = ["bev_anfang", "geborene", "gestorbene", "zuzuege", "fortzuege", "veraenderung", "bev_ende"]


def fetch():
    """Berichte einmalig laden (sie ändern sich nicht); fehlende bleiben fehlend, der Stand im Repository gilt."""
    RAW.mkdir(parents=True, exist_ok=True)
    ziele = [(RAW / f"{j}.pdf", u) for j, u in W["berichte"].items()] + [(RAW / f"matrix_{W['matrix']['jahr']}.pdf", W["matrix"]["url"])]
    for ziel, url in ziele:
        if ziel.exists():
            continue
        try:
            body, _ = net.get(url, tries=2)
            if not body.startswith(b"%PDF"):
                raise ValueError("keine PDF-Datei")
            ziel.write_bytes(body)
            audit.abruf("hsl_wanderung", url, 200, len(body), "", "", "")
        except Exception as e:
            audit.abruf("hsl_wanderung", url, getattr(e, "code", ""), "", "", "", str(e)[:200])
            print(f"Wanderung: {url} nicht abrufbar ({e})")


def text(pdf):
    return subprocess.run(["pdftotext", "-layout", str(pdf), "-"], capture_output=True, text=True).stdout


def dekodieren(t):
    """Bericht 2018: Glyphen um 29 Stellen verschoben, „±“ steht für den Gedankenstrich."""
    return "".join(chr(ord(c) + 29) if 3 <= ord(c) <= 93 and c not in " \n\f" else c for c in t).replace("±", "–")


ZAHL = r"[–-]?\s?\d{1,3}(?: \d{3})*|•|—"


def zahl(s):
    """'15 219' → 15219, '– 87' → -87, '—' (genau null) → 0, '•' (unbekannt oder geheim) → None."""
    s = s.strip()
    if s == "—":
        return 0
    d = re.sub(r"\D", "", s)
    if not d:
        return None
    return -int(d) if s.startswith(("–", "-")) else int(d)


def _teile(zeile):
    return [t for t in re.split(r"\s{2,}", zeile.strip()) if t]


def _werte(zeile):
    """Die sieben Zahlen am Ende einer Zeile der Tabelle der Bevölkerungsvorgänge."""
    w = [zahl(t) for t in _teile(zeile) if re.fullmatch(ZAHL, t)]
    return w[-7:] if len(w) >= 7 else None


def gemeinden(t, kreis):
    """{ags: {name, bev_anfang, …}} für die Gemeinden des Kreises. Drei Satzformen kommen vor:
    Schlüssel und Name in einer Zeile (ab 2024), Schlüssel über der Namenszeile (2018 bis 2023) und Zeilen für
    Männer, Frauen und insgesamt (bis 2017; übernommen wird „I“)."""
    zeilen = t.split("\n")
    out = {}
    for i, z in enumerate(zeilen):
        m = re.match(rf"\s*{kreis} (\d{{3}})(.*)$", z)
        if not m or m.group(1) in ("000", "200") or kreis + m.group(1) in out:
            continue  # Kreissumme, gemeindefreies Gebiet; nur das erste Vorkommen (Tabelle der Bevölkerungsvorgänge)
        rest = m.group(2)
        if re.match(r"\s+M\s{2,}", rest):
            if i + 2 >= len(zeilen) or not re.match(r"\s+I\s{2,}", zeilen[i + 2]):
                continue
            name, werte = _teile(zeilen[i + 1])[0], _werte(zeilen[i + 2])
        elif rest.strip():
            name, werte = _teile(rest)[0], _werte(rest)
        else:
            nz = zeilen[i + 1] if i + 1 < len(zeilen) else ""
            name, werte = (_teile(nz) or [""])[0], _werte(nz)
        if werte and re.match(r"[A-ZÄÖÜ]", name):
            out[kreis + m.group(1)] = {"name": name, **dict(zip(FELDER, werte))}
    return out


def matrix(t, kreis_name, kreise):
    """Zu- und Fortzüge des Kreises über die Kreisgrenze, aus der Matrix „Wanderung über die Kreisgrenze nach Herkunfts-
    und Zielgebieten“. Zeilen sind Zielgebiete, Spalten Herkunftsgebiete in der Reihenfolge der Kreise; die Tabelle
    steht auf zwei Seiten. Spaltengrenzen: rechte Ränder der Zahlen in der Zeile mit den meisten Werten der Seite.
    Ergebnis: ({herkunft: zuzüge}, {ziel: fortzüge}); „Land Hessen“, „Andere Bundesländer“, „Ausland“ und
    „insgesamt“ als eigene Schlüssel."""
    spalten = list(kreise) + ["Land Hessen", "Andere Bundesländer", "Ausland", "insgesamt"]
    zeilennamen = {**{k: k for k in kreise}, "Land Hessen": "Land Hessen", "Andere Bundesländer": "Andere Bundesländer",
                   "Ausland2)": "Ausland", "Fortgezogene insgesamt": "insgesamt"}
    zu, fort, pos = {}, {}, 0
    for seite in (s for s in t.split("\f") if "Herkunfts-" in s and "Fortgezogene insgesamt" in s):
        daten = []
        for z in seite.split("\n"):
            name = next((n for n in zeilennamen if z.strip().startswith(n + " ")), None)
            if name:
                versatz = z.index(name) + len(name)
                daten.append((zeilennamen[name], [(m.end() + versatz, m.group(0)) for m in re.finditer(ZAHL, z[versatz:])]))
        raender = [e for e, _ in max((d for _, d in daten), key=len)]
        cols = spalten[pos:pos + len(raender)]
        pos += len(raender)
        for name, zellen in daten:
            werte = {}
            for ende, roh in zellen:
                j = min(range(len(raender)), key=lambda k: abs(raender[k] - ende))
                if abs(raender[j] - ende) <= 5:
                    werte[cols[j]] = zahl(roh)
            if name == kreis_name:
                zu.update(werte)
            if kreis_name in cols and name != kreis_name:
                fort[name] = werte.get(kreis_name)
    return zu, fort


def geometrien():
    """Gemeinden des Kreises (vereinfacht) und Mittelpunkte der hessischen Kreise aus den Verwaltungsgrenzen."""
    utm = Transformer.from_crs("EPSG:25832", "EPSG:4326", always_xy=True).transform
    with zipfile.ZipFile(gemarkungen.ZIP) as z:
        gem = [(sr.record["GMDE_NR"], sr.record["GMDE_BZ"], transform(utm, shape(sr.shape.__geo_interface__)))
               for sr in gemarkungen._reader(z, "GEMEINDE_LA").iterShapeRecords() if sr.record["KREIS_NR"] == W["kreis"]]
        kreise = {}
        for sr in gemarkungen._reader(z, "KREIS_LA").iterShapeRecords():
            kreise.setdefault(sr.record["KREIS_NR"], []).append(transform(utm, shape(sr.shape.__geo_interface__)))
    feats = [{"type": "Feature", "properties": {"ags": "06" + nr, "name": name, "gemeindefrei": nr.endswith("200")},
              "geometry": gemarkungen._runden(g.simplify(0.0004, preserve_topology=True), 5)} for nr, name, g in sorted(gem)]
    punkte = {}
    for name, nrs in W["kreise"].items():
        p = unary_union([g for nr in nrs for g in kreise.get(nr, [])]).representative_point()
        punkte[name] = [round(p.x, 4), round(p.y, 4)]
    umriss = unary_union([g for _, _, g in gem]).simplify(0.0008, preserve_topology=True)
    return {"license": gemarkungen.LIZENZ, "attribution": gemarkungen.NAMENSNENNUNG, "source": gemarkungen.URL,
            "gemeinden": {"type": "FeatureCollection", "features": feats}, "kreise": punkte, "kreis_umriss": gemarkungen._runden(umriss, 5)}


def build():
    berichte = {j: RAW / f"{j}.pdf" for j in W["berichte"]}
    alt = json.loads(OUT_REPO.read_text(encoding="utf-8")) if OUT_REPO.exists() else {"gemeinden": {}, "kreis": None}
    daten = {"gemeinden": alt.get("gemeinden", {}), "kreis": alt.get("kreis")}
    zeilen = []
    for j, p in berichte.items():
        if not p.exists():
            zeilen.append({"jahr": j, "ergebnis": "Bericht fehlt, Stand im Repository"})
            continue
        t = text(p)
        g = gemeinden(t, W["kreis"])
        if len(g) < 10:  # Tabelle mit verschobener Kodierung (Bericht 2018)
            g = gemeinden(dekodieren(t), W["kreis"])
        for ags, v in g.items():
            daten["gemeinden"].setdefault("06" + ags, {"name": v["name"], "jahre": {}})["jahre"][j] = {k: v[k] for k in FELDER}
        pruef = [ags for ags, v in g.items() if v["bev_anfang"] is not None and v["bev_ende"] is not None and
                 abs(v["bev_anfang"] + v["geborene"] - v["gestorbene"] + v["zuzuege"] - v["fortzuege"] - v["bev_ende"]) > 25]
        zeilen.append({"jahr": j, "ergebnis": f"{len(g)} Gemeinden; Bilanz weicht um mehr als 25 ab: {', '.join(pruef) or 'keine'}"})
    mp = RAW / f"matrix_{W['matrix']['jahr']}.pdf"
    if mp.exists():
        zu, fort = matrix(text(mp), W["kreis_name"], W["kreise"])
        daten["kreis"] = {"jahr": W["matrix"]["jahr"], "quelle": W["matrix"]["url"], "zuzuege": zu, "fortzuege": fort}
        andere = [k for k in W["kreise"] if k != W["kreis_name"]]
        for art, d in (("Zuzüge", zu), ("Fortzüge", fort)):  # Summe der Kreise gegen „Land Hessen“ (geheime Werte fehlen)
            summe, geheim = sum(d.get(k) or 0 for k in andere), [k for k in andere if d.get(k) is None]
            zeilen.append({"jahr": f"Matrix {W['matrix']['jahr']}", "ergebnis": f"{art}: Kreise {summe}, Land Hessen {d.get('Land Hessen')}, "
                           f"ohne Wert (geheim): {', '.join(geheim) or 'keine'}"})
    if gemarkungen.ZIP.exists():
        GEO.write_text(json.dumps(geometrien(), ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    daten.update(generated_at=date.today().isoformat(), quellen=W["berichte"], lizenz=W["lizenz"], attribution=W["attribution"])
    OUT_REPO.parent.mkdir(parents=True, exist_ok=True)
    OUT_REPO.write_text(json.dumps(daten, ensure_ascii=False, indent=1, sort_keys=True), encoding="utf-8")
    geo = json.loads(GEO.read_text(encoding="utf-8")) if GEO.exists() else None
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({**daten, "geo": geo}, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    audit.tabelle("wanderung.tsv", ["jahr", "ergebnis"], zeilen)
    w = daten["gemeinden"].get(config.STADT["stadt"]["gemeindeschluessel"], {}).get("jahre", {})
    print(f"Wanderung: {len(daten['gemeinden'])} Gemeinden, Jahre {', '.join(sorted(w)) or '–'}; Kreismatrix {daten['kreis'] and daten['kreis']['jahr']}")
    return daten
