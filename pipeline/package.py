"""Datenpaket (Zip): Vorgänge, Audit-Protokolle, Quellenregister und Lizenzen. Ohne Flächen der Bauleitplanung
(Nutzung nur nicht kommerziell, nicht weitergeben); die Zuordnung Vorgang → Plannummer ist enthalten."""
import zipfile

from . import config

PAKET = config.EXPORT / "stadtmonitor-daten.zip"


def package():
    with zipfile.ZipFile(PAKET, "w", zipfile.ZIP_DEFLATED) as z:
        z.write(config.VORGAENGE, "vorgaenge.json")
        for p in sorted((config.EXPORT / "audit").glob("*.tsv")):
            z.write(p, f"audit/{p.name}")
        for p in (config.ROOT / "data" / "LICENSE-DATA.md", config.ROOT / "data" / "quellen_register.tsv"):
            if p.exists():
                z.write(p, p.name)
    print(f"Datenpaket {PAKET.name}: {PAKET.stat().st_size // 1024} KB")
