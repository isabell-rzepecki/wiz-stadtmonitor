"""Datenpaket (Zip): Vorgänge, Gesellschaften, Beteiligung, Wahlen, Wanderung, Wohnen, Audit-Protokolle,
Quellenregister und Lizenzen (je Datei in LICENSE-DATA.md).

Bauleitplanung (Nutzung nur nicht kommerziell, nicht weitergeben): Das Paket enthält nur die Zuordnung Vorgang →
Plannummer. Punkte im Geltungsbereich, Plantitel und Überschneidungen von Planflächen mit Umweltebenen stammen aus den
Umringen und bleiben der Seite vorbehalten (dort mit Nutzungshinweis)."""
import csv
import io
import json
import zipfile

from . import config

PAKET = config.EXPORT / "stadtmonitor-daten.zip"


def ohne_planumringe(d):
    """Vorgänge ohne Angaben aus den Umringen der Bauleitplanung: Plannummer und Fundstelle bleiben."""
    for v in d["vorgaenge"]:
        plan_orte = {l["name"] for l in v["locations"] if l["level"] == "bebauungsplan"}
        v["plans"] = [{k: p[k] for k in ("key", "treffer", "evidence") if k in p} for p in v.get("plans", [])]
        for l in v["locations"]:
            if l["level"] == "bebauungsplan":
                for k in ("lon", "lat"):
                    l.pop(k, None)
                l["name"] = l.get("plan")
        if "overlaps" in v:
            v["overlaps"] = [o for o in v["overlaps"] if o.get("ort") not in plan_orte]
            if not v["overlaps"]:
                del v["overlaps"]
    return d


def _tsv(pfad, spalten_weg=(), zeile_weg=lambda z: False):
    """Audit-Tabelle als Text, ohne die genannten Spalten und Zeilen."""
    rows = list(csv.DictReader(pfad.open(encoding="utf-8"), delimiter="\t"))
    spalten = [c for c in (rows[0].keys() if rows else []) if c not in spalten_weg]
    out = io.StringIO()
    w = csv.DictWriter(out, spalten, delimiter="\t", lineterminator="\n", extrasaction="ignore")
    w.writeheader()
    w.writerows(r for r in rows if not zeile_weg(r))
    return out.getvalue()


# Audit-Tabellen mit Angaben aus den Umringen: Plantitel und Überschneidungen von Planflächen nicht ins Paket
AUDIT_FILTER = {
    "verortung_bauleitplanung.tsv": {"spalten_weg": ("plan_titel",)},
    "ueberschneidung_umwelt.tsv": {"zeile_weg": lambda z: z.get("ort_ebene") == "bebauungsplan"},
}


def package():
    with zipfile.ZipFile(PAKET, "w", zipfile.ZIP_DEFLATED) as z:
        d = ohne_planumringe(json.loads(config.VORGAENGE.read_text(encoding="utf-8")))
        z.writestr("vorgaenge.json", json.dumps(d, ensure_ascii=False, separators=(",", ":")))
        if (config.EXPORT / "eigentum.json").exists():  # städtische Gesellschaften und Eigenbetriebe
            z.write(config.EXPORT / "eigentum.json", "eigentum.json")
        if (config.EXPORT / "beteiligung.json").exists():  # Beteiligungsverfahren (Plan, Stufen, Fristen)
            z.write(config.EXPORT / "beteiligung.json", "beteiligung.json")
        if (config.EXPORT / "wahlen.json").exists():  # Wahlergebnisse ohne Personennamen
            z.write(config.EXPORT / "wahlen.json", "wahlen.json")
        if (config.ROOT / "data" / "wanderung" / "wanderung.json").exists():  # Zu- und Fortzüge (HSL), ohne Geometrie
            z.write(config.ROOT / "data" / "wanderung" / "wanderung.json", "wanderung.json")
        if (config.EXPORT / "wohnen.json").exists():  # Bodenrichtwert-Spannen und Zensuswerte (ohne Geometrie)
            z.write(config.EXPORT / "wohnen.json", "wohnen.json")
        for p in sorted((config.EXPORT / "audit").glob("*.tsv")):
            if p.name in AUDIT_FILTER:
                z.writestr(f"audit/{p.name}", _tsv(p, **AUDIT_FILTER[p.name]))
            else:
                z.write(p, f"audit/{p.name}")
        for p in (config.ROOT / "data" / "LICENSE-DATA.md", config.ROOT / "data" / "quellen_register.tsv"):
            if p.exists():
                z.write(p, p.name)
    print(f"Datenpaket {PAKET.name}: {PAKET.stat().st_size // 1024} KB")
