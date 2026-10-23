"""Kontrastprüfung (WCAG 2.1) der Farb-Tokens aus config/stadt.json, hell und dunkel.

Aufruf: python tools/kontrast.py  – gibt je Paar das Verhältnis aus; Rückgabewert 1, wenn ein Paar die Schwelle verfehlt.
"""
import json
import sys
from pathlib import Path

STADT = Path(__file__).resolve().parent.parent / "config" / "stadt.json"


def luminanz(hexfarbe):
    h = hexfarbe.lstrip("#")
    def lin(c):
        c /= 255
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b)


def verhaeltnis(a, b):
    x, y = sorted((luminanz(a), luminanz(b)), reverse=True)
    return (x + 0.05) / (y + 0.05)


def pruefen(gestaltung):
    """[(Modus, Vordergrund, Hintergrund, Verhältnis, Schwelle, bestanden)]"""
    out = []
    for modus, farben in gestaltung["farben"].items():
        for vg, hg, schwelle in gestaltung["kontrast_paare"]:
            v = verhaeltnis(farben[vg], farben[hg])
            out.append((modus, vg, hg, round(v, 2), schwelle, v >= schwelle))
    return out


def main():
    ergebnis = pruefen(json.loads(STADT.read_text(encoding="utf-8"))["gestaltung"])
    for modus, vg, hg, v, schwelle, ok in ergebnis:
        print(f"{modus:7} {vg:15} auf {hg:12} {v:5.2f}:1  (min. {schwelle})  {'ok' if ok else 'ZU NIEDRIG'}")
    return 0 if all(r[-1] for r in ergebnis) else 1


if __name__ == "__main__":
    sys.exit(main())
