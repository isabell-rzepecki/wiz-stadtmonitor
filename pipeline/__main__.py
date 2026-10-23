"""Aufruf: python -m pipeline {fetch|fetch-plaene|build|check|package|site|all}"""
import sys

from . import bauleitplanung, build, check, fetch, package, site

STEPS = {
    "fetch": fetch.fetch,  # Einladungen (PDF) laden und in Text umwandeln, mit Zwischenspeicher
    "fetch-plaene": bauleitplanung.fetch,  # Umringe der Bauleitplanung nach data/geo/restricted/ (nicht im Repository)
    "build": build.build,  # Sitzungen, Vorgänge, Ortsbezüge, Kartenebene, Audit
    "check": check.check,  # Rückführbarkeit, Fehlerquote, Datenschutz, Lizenzgrenze
    "package": package.package,  # Datenpaket (Zip) ohne Flächen der Bauleitplanung
    "site": site.build,  # Seite in _site/ zusammenstellen
}
ALL = ["fetch", "fetch-plaene", "build", "check", "package", "site"]


def main(argv):
    if len(argv) != 1 or argv[0] not in (*STEPS, "all"):
        raise SystemExit(__doc__)
    for step in ALL if argv[0] == "all" else argv:
        print(f"== {step}", flush=True)
        STEPS[step]()


main(sys.argv[1:])
