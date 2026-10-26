"""3D-Gebäudemodelle LoD2 der HVBG (CityGML): Abruf und Lesen der Rohdaten.

Gebäude („LoD2“) und Bauwerke („BW“) der Gemeinde lädt fetch() über die Schnittstelle des Download-Centers der HVBG;
die Adresse einer Datei trägt ein Tagesdatum und wird deshalb jedes Mal erfragt. Die gemessenen Höhen übernimmt
gebaeude.py für die ALKIS-Grundrisse (Seite „Wohnen und Eigentum“, 2D und 3D).
"""
import io
import json
import re
import time
import urllib.parse
import zipfile

from . import audit, config, net

G = config.STADT["gebaeude3d"]
RAW = config.RAW / "lod2"


def fetch():
    """Gebäude und Bauwerke der Gemeinde laden; aus dem Zwischenspeicher, solange sie jünger als 180 Tage sind."""
    RAW.mkdir(parents=True, exist_ok=True)
    for d in G["dateien"]:
        ziel = RAW / f"{d['datei']}.zip"
        if ziel.exists() and time.time() - ziel.stat().st_mtime < 180 * 86400:
            continue
        try:
            liste, _ = net.get(d["rest"], tries=2)
            eintrag = next(x for x in json.loads(liste)["searchresult"]["downloads"] if x["name"] == d["datei"])
            url = G["download_basis"] + urllib.parse.quote(eintrag["downloadLink"]["uri"])
            body, _ = net.get(url, tries=2)
            if not body.startswith(b"PK"):
                raise ValueError("keine ZIP-Datei")
            ziel.write_bytes(body)
            audit.abruf("lod2_dlc", url, 200, len(body), "", "", f"Stand {eintrag.get('creationDate', '')}")
        except Exception as e:  # Stand im Repository bleibt
            audit.abruf("lod2_dlc", d["rest"], getattr(e, "code", ""), "", "", "", str(e)[:200])
            print(f"3D-Gebäude: {d['datei']} nicht abrufbar ({e}); Stand im Repository bleibt")


def _ringe(block):
    """[[(x, y, z), …]] der Polygone eines Blocks."""
    out = []
    for pl in re.findall(r"<gml:posList[^>]*>(.*?)</gml:posList>", block, re.S):
        z = [float(v) for v in pl.split()]
        out.append(list(zip(z[0::3], z[1::3], z[2::3])))
    return out


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
