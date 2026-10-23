"""Datenpaket (Zip): Vorgänge, Audit-Protokolle, Quellenregister und Lizenzen. Ohne Flächen der Bauleitplanung
(Nutzung nur nicht kommerziell, nicht weitergeben); die Zuordnung Vorgang → Plannummer ist enthalten."""
import zipfile

from . import config

PAKET = config.EXPORT / "stadtmonitor-daten.zip"


def package():
    with zipfile.ZipFile(PAKET, "w", zipfile.ZIP_DEFLATED) as z:
        z.write(config.VORGAENGE, "vorgaenge.json")
        if (config.EXPORT / "eigentum.json").exists():  # städtische Gesellschaften und Eigenbetriebe
            z.write(config.EXPORT / "eigentum.json", "eigentum.json")
        if (config.EXPORT / "beteiligung.json").exists():  # Beteiligungsverfahren (Plan, Stufen, Fristen)
            z.write(config.EXPORT / "beteiligung.json", "beteiligung.json")
        if (config.EXPORT / "wahlen.json").exists():  # Wahlergebnisse ohne Personennamen
            z.write(config.EXPORT / "wahlen.json", "wahlen.json")
        if (config.EXPORT / "wohnen.json").exists():  # Bodenrichtwert-Spannen und Zensuswerte (ohne Geometrie)
            z.write(config.EXPORT / "wohnen.json", "wohnen.json")
        for p in sorted((config.EXPORT / "audit").glob("*.tsv")):
            z.write(p, f"audit/{p.name}")
        for p in (config.ROOT / "data" / "LICENSE-DATA.md", config.ROOT / "data" / "quellen_register.tsv"):
            if p.exists():
                z.write(p, p.name)
    print(f"Datenpaket {PAKET.name}: {PAKET.stat().st_size // 1024} KB")
