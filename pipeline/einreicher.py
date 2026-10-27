"""Einreicher von Anträgen und Anfragen aus den TOP-Titeln („Antrag der Fraktion X vom TT.MM.JJJJ“).

Muster und Fraktionen stehen in config/stadt.json (einreicher). Gemeinsame Anträge werden allen beteiligten
Fraktionen zugeordnet (gemeinsam = True). Einzelne Stadtverordnete erscheinen ohne Namen. Was dem Muster folgt,
aber keiner Fraktion zugeordnet werden kann, steht im Audit (einreicher.tsv) als „nicht zugeordnet“.
"""
import re

from . import config

E = config.STADT["einreicher"]
MUSTER = re.compile(E["muster"].format(typ=E["muster_typ"]), re.I | re.S)
# ohne Datum („Beantwortung der Anträge der FWG-Fraktion zur …“): nur, wenn eine Fraktion erkannt wird
OHNE_DATUM = re.compile(E["muster_ohne_datum"].format(typ=E["muster_typ"]), re.I | re.S)
FRAKTIONEN = [(f["id"], re.compile(f["muster"], re.I)) for f in E["fraktionen"]]
EINZEL = re.compile(E["einzelperson"]["muster"], re.I)


def erkennen(titel):
    """{typ, einreicher: [ids], datum (ISO oder None), gemeinsam, fundstelle} oder None."""
    m = MUSTER.search(titel)
    if not m:
        m = OHNE_DATUM.search(titel)
        if not m or not any(rx.search(m.group("einr")) for _, rx in FRAKTIONEN):
            return None
    einr = m.group("einr")
    ids = [fid for fid, rx in FRAKTIONEN if rx.search(einr)]
    if not ids and EINZEL.search(einr):
        ids = [E["einzelperson"]["id"]]
    datum = m.groupdict().get("datum")
    iso = None
    if datum:
        d, mo, y = datum.split(".")
        iso = f"{y}-{int(mo):02d}-{int(d):02d}"
    typ = m.group("typ")
    typ = typ[0].upper() + typ[1:].lower() if typ.isupper() else typ
    return {"typ": typ, "einreicher": ids, "datum": iso, "gemeinsam": len(ids) > 1,
            "fundstelle": m.group(0) if ids and ids != [E["einzelperson"]["id"]] else (f"{typ} vom {datum}" if datum else typ)}
