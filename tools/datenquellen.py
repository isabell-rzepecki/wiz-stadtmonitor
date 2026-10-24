"""DATA_SOURCES.md aus data/quellen_register.tsv und data/attribution.tsv erzeugen (Namensnennungen der Seite: pipeline/site.py).

Aufruf: python tools/datenquellen.py         – schreibt DATA_SOURCES.md
        python tools/datenquellen.py --pruefen – Rückgabewert 1, wenn DATA_SOURCES.md nicht dem Register entspricht
"""
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REGISTER = ROOT / "data" / "quellen_register.tsv"
ATTRIBUTION = ROOT / "data" / "attribution.tsv"
ZIEL = ROOT / "DATA_SOURCES.md"


def lesen(p):
    return list(csv.DictReader(p.open(encoding="utf-8"), delimiter="\t"))


def _zelle(t):
    return (t or "–").replace("|", "\\|").replace("\n", " ")


def markdown():
    reg = lesen(REGISTER)
    attr = {q: a for a in lesen(ATTRIBUTION) for q in a["quellen"].split(",")}
    out = ["# Datenquellen", "",
           "Erzeugt aus `data/quellen_register.tsv` und `data/attribution.tsv` mit `python tools/datenquellen.py`; nicht von Hand bearbeiten.", "",
           "Status laut Register: `verifiziert`, `teilweise`, `zu prüfen`, `zu verifizieren`. Einträge aus Recherchen gelten als ungeprüft, "
           "bis eine Quelle im Projekt genutzt und abgerufen wurde (Spalte Test).", ""]
    for thema in sorted({r["thema"] for r in reg}):
        out += [f"## {thema}", "", "| Quelle | Anbieter | Lizenz | Namensnennung | Status | Test | Nutzung |", "|---|---|---|---|---|---|---|"]
        for r in [r for r in reg if r["thema"] == thema]:
            a = attr.get(r["id"])
            name = f"[{_zelle(r['name'])}]({r['url']})" if r["url"].startswith("http") else _zelle(r["name"])
            out.append(f"| {name} (`{r['id']}`) | {_zelle(r['anbieter'])} | {_zelle(r['lizenz'])} | {_zelle(a['text'] if a else '')} | "
                       f"{_zelle(r['status'])} | {_zelle(r['test_2026_10_23'])} | {_zelle(r['nutzung'])} |")
        out.append("")
    return "\n".join(out)


def main():
    text = markdown()
    if "--pruefen" in sys.argv:
        ok = ZIEL.exists() and ZIEL.read_text(encoding="utf-8") == text
        print("DATA_SOURCES.md aktuell" if ok else "DATA_SOURCES.md veraltet: python tools/datenquellen.py ausführen")
        return 0 if ok else 1
    ZIEL.write_text(text, encoding="utf-8")
    print(f"{ZIEL.name} geschrieben")
    return 0


if __name__ == "__main__":
    sys.exit(main())
