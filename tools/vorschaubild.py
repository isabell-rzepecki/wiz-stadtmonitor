"""Vorschaubild für geteilte Links (Open Graph, 1200 × 630): site/og-bild.png.

Das Bild zeigt Bildmarke, Wortmarke, einen Satz zum Zweck der Seite und die Umrisse der Ortsbezirke
(data/geo/dl-de-zero/ortsbezirke.geojson, HVBG, dl-de/zero-2.0). Dieses Skript schreibt die Vorlage als HTML;
das Bild entsteht mit Chromium, zum Beispiel:

    python tools/vorschaubild.py /tmp/og.html
    npx playwright screenshot --viewport-size=1200,630 file:///tmp/og.html site/og-bild.png
"""
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SATZ = "Was Stadtverordnete, Ausschüsse und Ortsbeiräte beraten – auf Karte, Zeitleiste und Liste."


def _ringe(g):
    polys = [g["coordinates"]] if g["type"] == "Polygon" else g["coordinates"]
    return [r for poly in polys for r in poly]


def umrisse(x0, y0, w, h):
    """SVG-Pfad aller Ortsbezirke, flächentreu genug für eine Vorschau (Längen mit cos(Breite) gestaucht)."""
    d = json.loads((ROOT / "data/geo/dl-de-zero/ortsbezirke.geojson").read_text(encoding="utf-8"))
    alle = [r for f in d["features"] for r in _ringe(f["geometry"])]
    pts = [p for r in alle for p in r]
    k = math.cos(math.radians(sum(p[1] for p in pts) / len(pts)))
    xs = [p[0] * k for p in pts]
    ys = [-p[1] for p in pts]
    s = min(w / (max(xs) - min(xs)), h / (max(ys) - min(ys)))
    ox = x0 + (w - (max(xs) - min(xs)) * s) / 2
    oy = y0 + (h - (max(ys) - min(ys)) * s) / 2
    return "".join("M" + "L".join(f"{ox + (p[0] * k - min(xs)) * s:.1f} {oy + (-p[1] - min(ys)) * s:.1f}" for p in r[::2]) + "Z"
                   for r in alle)


def vorlage():
    stadt = json.loads((ROOT / "config/stadt.json").read_text(encoding="utf-8"))
    name = stadt["stadt"]["name"]
    adresse = stadt["projekt"]["site_url"].split("//")[-1].strip("/")
    marke = (ROOT / "site/favicon.svg").read_text(encoding="utf-8")
    marke = marke[marke.index("<rect"):marke.index("</svg>")]
    schrift = (ROOT / "site/fonts").as_uri()
    return f"""<!doctype html><meta charset="utf-8"><style>
@font-face{{font-family:L;src:url('{schrift}/lilita-one-latin-400-normal.woff2')}}
@font-face{{font-family:M;src:url('{schrift}/space-mono-latin-400-normal.woff2')}}
@font-face{{font-family:M;font-weight:700;src:url('{schrift}/space-mono-latin-700-normal.woff2')}}
html,body{{margin:0;width:1200px;height:630px;overflow:hidden}}
body{{background:#f4726b;font-family:M;color:#1a1a1a;position:relative}}
svg.k{{position:absolute;right:-30px;top:-20px}} .t{{position:absolute;left:80px;top:80px;width:620px}}
h1{{font:400 92px/0.98 L;color:#fdf6f4;margin:30px 0 24px;letter-spacing:-1px}} h1 span{{color:#1a1a1a;display:block}}
p{{font-size:26px;line-height:1.45;margin:0 0 28px}} .u{{font-weight:700;font-size:22px}}
</style>
<svg class="k" width="600" height="670" viewBox="0 0 600 670"><path d="{umrisse(20, 20, 560, 630)}" fill="#fdf6f4" fill-opacity=".14" stroke="#fdf6f4" stroke-opacity=".8" stroke-width="2" stroke-linejoin="round"/></svg>
<div class="t"><svg viewBox="0 0 64 64" width="120" height="120" style="display:block">{marke}</svg>
<h1>Stadtmonitor<span>{name}</span></h1><p>{SATZ}</p><div class="u">{adresse}</div></div>"""


if __name__ == "__main__":
    ziel = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("og-bild.html")
    ziel.write_text(vorlage(), encoding="utf-8")
    print(ziel)
