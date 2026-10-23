"""Nicht-Text-Kontrast (WCAG 2.1, 1.4.11: mindestens 3:1) der Kartengrafik auf der grauen Hintergrundkarte.

Lädt einige Kacheln von basemap.de (grau) über dem Stadtgebiet (Zwischenspeicher data/raw/kacheln/), wendet den
CSS-Filter der Seite an (grayscale(1) contrast(.9) brightness(1.08)) und misst die Grauwerte als Perzentile:
p50/p90 sind die Fläche der Karte, p10/p2 Straßen, Beschriftung und Waldsignaturen. Verglichen werden die
Marker (Füllung gegen den weißen Ring und gegen die Karte), die Grenzen der Ortsbezirke, die Umweltebenen und
die Cluster. Maßstab ist die vorherrschende Kartenfläche (p50, p90); p10 und p2 werden zur Einordnung gezeigt.

Aufruf: python tools/kontrast_karte.py   (benötigt Pillow, nicht Teil von requirements.txt)
"""
import io
import json
import math
import statistics
import sys
import urllib.request
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from kontrast import verhaeltnis  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
STADT = json.loads((ROOT / "config" / "stadt.json").read_text(encoding="utf-8"))
CACHE = ROOT / "data" / "raw" / "kacheln"
ZOOM = (12, 13, 14, 15, 16)


def kacheln():
    w, s, o, n = STADT["karte"]["bbox"]
    url = STADT["karte"]["hintergrund"]["grau"]
    CACHE.mkdir(parents=True, exist_ok=True)
    for z in ZOOM:
        for lat, lon in ((s + n) / 2, (w + o) / 2), (s + (n - s) * 0.2, w + (o - w) * 0.3), (s + (n - s) * 0.8, w + (o - w) * 0.7):
            x = int((lon + 180) / 360 * 2 ** z)
            y = int((1 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2 * 2 ** z)
            p = CACHE / f"{z}_{x}_{y}.png"
            if not p.exists():
                req = urllib.request.Request(url.format(z=z, x=x, y=y), headers={"User-Agent": STADT["projekt"]["user_agent"]})
                p.write_bytes(urllib.request.urlopen(req, timeout=30).read())
            yield p


def grauwerte():
    out = []
    for p in kacheln():
        px = Image.open(io.BytesIO(p.read_bytes())).convert("RGB").tobytes()
        for r, g, b in zip(px[0::3], px[1::3], px[2::3]):
            v = (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255   # grayscale(1)
            v = min(1, max(0, (v - 0.5) * 0.9 + 0.5) * 1.08)    # contrast(.9) brightness(1.08)
            out.append(v)
    return out


def hexgrau(v):
    return "#" + f"{round(v * 255):02x}" * 3


def mischen(vg, hg, alpha):
    f = [int(vg[i:i + 2], 16) for i in (1, 3, 5)]
    b = [int(hg[i:i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(alpha * x + (1 - alpha) * y):02x}" for x, y in zip(f, b))


def main():
    v = sorted(grauwerte())
    q = statistics.quantiles(v, n=100)
    hg = {f"p{k}": hexgrau(q[k - 1]) for k in (2, 10, 50, 90)}
    print("Kartenfläche (Grauwerte):", ", ".join(f"{k} {c}" for k, c in hg.items()))
    hell = STADT["gestaltung"]["farben"]["hell"]
    zeilen = [(f"Marker {k} gegen weißen Ring", hell[k], "#ffffff", 1) for k in ("hoch", "mittel", "niedrig")]
    zeilen += [(f"Marker {k}", hell[k], None, 0.95) for k in ("hoch", "mittel", "niedrig")]
    zeilen += [("Grenze Ortsbezirk", hell["accent_ink"], None, 0.85), ("Ring der Cluster", "#b8352e", None, 1)]
    zeilen += [(f"Umweltebene {g['titel']}", g["farbe"], None, 0.9) for g in STADT["umwelt"]["gruppen"]]
    fehlt = 0
    for name, farbe, gegen, alpha in zeilen:
        werte = {k: verhaeltnis(mischen(farbe, gegen or c, alpha), gegen or c) for k, c in (hg.items() if not gegen else [("", gegen)])}
        massgeblich = [w for k, w in werte.items() if k in ("", "p50", "p90")]
        ok = min(massgeblich) >= 3
        fehlt += not ok
        print(f"{name:52} " + "  ".join(f"{k or 'Ring'} {w:4.2f}" for k, w in werte.items()) + f"  {'ok' if ok else 'UNTER 3:1'}")
    return 1 if fehlt else 0


if __name__ == "__main__":
    sys.exit(main())
