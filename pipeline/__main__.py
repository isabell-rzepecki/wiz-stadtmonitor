"""Aufruf: python -m pipeline {fetch|fetch-plaene|fetch-gemarkungen|gemarkungen|fetch-lage|lage|fetch-umwelt|umwelt|build|check|package|site|all}"""
import sys

from . import bauleitplanung, build, check, fetch, gemarkungen, lage, package, site, umwelt

STEPS = {
    "fetch": fetch.fetch,  # Einladungen (PDF) laden und in Text umwandeln, mit Zwischenspeicher
    "fetch-plaene": bauleitplanung.fetch,  # Umringe der Bauleitplanung nach data/geo/restricted/ (nicht im Repository)
    "fetch-gemarkungen": gemarkungen.fetch,  # Digitale Verwaltungsgrenzen Hessen (HVBG), alle 30 Tage neu
    "gemarkungen": gemarkungen.build,  # Ortsbezirksflächen aus den Gemarkungen
    "fetch-lage": lambda: (lage.fetch_hako(), lage.fetch()),  # Hauskoordinaten und Lagebezeichnungen (HVBG), alle 30 Tage neu
    "lage": lage.build,  # Straßen- und Lageverzeichnis je Gemarkung
    "fetch-umwelt": umwelt.fetch,  # Hochwasser, Wasserschutz, Schutzgebiete (HLNUG, HMLU), alle 7 Tage neu
    "umwelt": umwelt.build,  # Umweltebenen auf das Stadtgebiet zugeschnitten, Kartenebenen
    "build": build.build,  # Sitzungen, Vorgänge, Ortsbezüge, Kartenebene, Audit
    "check": check.check,  # Rückführbarkeit, Fehlerquote, Datenschutz, Lizenzgrenze
    "package": package.package,  # Datenpaket (Zip) ohne Flächen der Bauleitplanung
    "site": site.build,  # Seite in _site/ zusammenstellen
}
ALL = ["fetch", "fetch-plaene", "fetch-gemarkungen", "gemarkungen", "fetch-lage", "lage", "fetch-umwelt", "umwelt", "build", "check", "package", "site"]


def main(argv):
    if len(argv) != 1 or argv[0] not in (*STEPS, "all"):
        raise SystemExit(__doc__)
    for step in ALL if argv[0] == "all" else argv:
        print(f"== {step}", flush=True)
        STEPS[step]()


main(sys.argv[1:])
