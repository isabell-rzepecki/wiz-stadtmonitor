"""Audit-Protokolle (TSV) unter data/export/audit/."""
import csv
from datetime import date

from . import config

AUDIT = config.EXPORT / "audit"
ABRUF_SPALTEN = ["quelle_id", "url", "http_status", "bytes", "sha256", "anzahl_features", "fehler"]


def abruf(quelle_id, url, status, size, sha, anzahl, fehler):
    """Eine Zeile im Abrufprotokoll des Tages (audit/abruf_<datum>.tsv)."""
    AUDIT.mkdir(parents=True, exist_ok=True)
    p = AUDIT / f"abruf_{date.today().isoformat()}.tsv"
    neu = not p.exists()
    with p.open("a", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter="\t", lineterminator="\n")
        if neu:
            w.writerow(ABRUF_SPALTEN)
        w.writerow([quelle_id, url, status, size, sha, anzahl, fehler])


def tabelle(name, spalten, zeilen):
    AUDIT.mkdir(parents=True, exist_ok=True)
    with (AUDIT / name).open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter="\t", lineterminator="\n")
        w.writerow(spalten)
        for z in zeilen:
            w.writerow([str(z.get(s, "") if z.get(s) is not None else "").replace("\t", " ").replace("\n", " ") for s in spalten])
