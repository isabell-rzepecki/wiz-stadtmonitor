"""Aufruf: python -m pipeline {fetch|fetch-plaene|fetch-gemarkungen|gemarkungen|fetch-lage|lage|fetch-eigentum|eigentum|fetch-umwelt|umwelt|fetch-wohnen|wohnen|fetch-wahlen|wahlen|fetch-beteiligung|beteiligung|fetch-wanderung|wanderung|gebaeude3d|build|check|package|site|all}"""
import sys

from . import bauleitplanung, beteiligung, build, check, eigentum, fetch, gebaeude3d, gemarkungen, lage, package, site, umwelt, wahlen, wanderung, wohnen

STEPS = {
    "fetch": fetch.fetch,  # Einladungen (PDF) laden und in Text umwandeln, mit Zwischenspeicher
    "fetch-plaene": bauleitplanung.fetch,  # Umringe der Bauleitplanung nach data/geo/restricted/ (nicht im Repository)
    "fetch-gemarkungen": gemarkungen.fetch,  # Digitale Verwaltungsgrenzen Hessen (HVBG), alle 30 Tage neu
    "gemarkungen": gemarkungen.build,  # Ortsbezirksflächen aus den Gemarkungen
    "fetch-lage": lambda: (lage.fetch_hako(), lage.fetch()),  # Hauskoordinaten und Lagebezeichnungen (HVBG), alle 30 Tage neu
    "lage": lage.build,  # Straßen- und Lageverzeichnis je Gemarkung
    "fetch-eigentum": eigentum.fetch,  # Gebäude für öffentliche Zwecke (ALKIS, POST) und Beteiligungsbericht, alle 30 Tage neu
    "eigentum": eigentum.build,  # städtische Gesellschaften und Eigenbetriebe ohne Personen
    "fetch-umwelt": umwelt.fetch,  # Hochwasser, Wasserschutz, Schutzgebiete (HLNUG, HMLU), alle 7 Tage neu
    "umwelt": umwelt.build,  # Umweltebenen auf das Stadtgebiet zugeschnitten, Kartenebenen
    "fetch-wohnen": wohnen.fetch,  # Bodenrichtwerte (BORIS), Zensus 2022 Regionaltabelle und Gitter, alle 365 Tage neu
    "fetch-wanderung": wanderung.fetch,  # Jahresberichte und Kreismatrix des HSL (einmalig, ändern sich nicht)
    "wanderung": wanderung.build,  # Zu- und Fortzüge je Gemeinde des Kreises, Wanderung über die Kreisgrenze
    "gebaeude3d": gebaeude3d.build,  # 3D-Gebäude (LoD2, von Hand nach data/raw/lod2/) je Ortsteil für die 3D-Ansicht
    "wohnen": wohnen.build,  # Bodenrichtwerte und Zensuswerte je Ortsbezirk und Gemeinde, Kartenebene Bodenrichtwerte
    "fetch-wahlen": wahlen.fetch,  # amtliche Wahlergebnisse (Bekanntmachungen, votemanager, Bundeswahlleiterin), alle 30 Tage neu
    "wahlen": wahlen.build,  # Ergebnisse je Wahl ohne Personennamen, Prüfung der Summen
    "fetch-beteiligung": beteiligung.fetch,  # Bekanntmachungen zur Bauleitplanung (PDF), nur neue Dateien
    "beteiligung": beteiligung.build,  # Plan, Stufen und Fristen der Beteiligungsverfahren
    "build": build.build,  # Sitzungen, Vorgänge, Ortsbezüge, Kartenebene, Audit
    "check": check.check,  # Rückführbarkeit, Fehlerquote, Datenschutz, Lizenzgrenze
    "package": package.package,  # Datenpaket (Zip) ohne Flächen der Bauleitplanung
    "site": site.build,  # Seite in _site/ zusammenstellen
}
ALL = ["fetch", "fetch-plaene", "fetch-gemarkungen", "gemarkungen", "fetch-lage", "lage", "fetch-eigentum", "eigentum", "fetch-umwelt", "umwelt", "fetch-wohnen", "wohnen", "fetch-wahlen", "wahlen", "fetch-beteiligung", "beteiligung", "fetch-wanderung", "wanderung", "gebaeude3d", "build", "check", "package", "site"]


def main(argv):
    if len(argv) != 1 or argv[0] not in (*STEPS, "all"):
        raise SystemExit(__doc__)
    for step in ALL if argv[0] == "all" else argv:
        print(f"== {step}", flush=True)
        STEPS[step]()


main(sys.argv[1:])
