"""Quellwache: Lücken und Stillstand in den amtlichen Bekanntmachungen erkennen.

- Sitzungen, die erwähnt werden, deren Einladung aber fehlt: „Genehmigung der Niederschrift über die Sitzung … am
  TT.MM.JJJJ“ in einer Tagesordnung, und Beschlussdaten aus bekanntgemachten Satzungen (rechtsakte.py), zu denen keine
  Sitzung des Gremiums im Datenbestand ist. Ortsbeirat und Stadtteilbeirat desselben Ortsteils gelten als ein Gremium.
- Stillstand: die neueste Einladung ist älter als quellwache.tage_ohne_einladung, oder die Liste der Stadt wurde
  länger als quellwache.tage_ohne_abruf nicht abgerufen.
Bekannte Lücken (config/quellwache_bekannt.tsv) bleiben sichtbar, zählen aber nicht als neu; nur neue Lücken und
Warnungen öffnen im Workflow ein Issue (tools/quellwache_issue.py).
"""
import csv
import re
from datetime import date, timedelta

from . import config

Q = config.STADT["quellwache"]
BEKANNT = config.ROOT / "config" / "quellwache_bekannt.tsv"
BEIRAT = ("ortsbeirat", "stadtteilbeirat")
NIEDERSCHRIFT = re.compile(r"Niederschrift[^.;]*?(?:Sitzung|vom)[^.;]*?(\d{1,2})\.\s?(\d{1,2})\.\s?(20\d\d)")


def _gremium_schluessel(typ, ortsteil, gremium_id):
    if typ == "stvv":
        return ("stvv", "")
    if typ in BEIRAT:
        return ("ortsbezirk", ortsteil or "")
    return ("gremium", gremium_id or "")


def bekannt_laden(datei=None):
    datei = datei or BEKANNT
    if not datei.exists():
        return set()
    with datei.open(encoding="utf-8", newline="") as f:
        return {(z["datum"], z["gremium"]) for z in csv.DictReader((x for x in f if not x.startswith("#")), delimiter="\t")}


def pruefen(daten, rechtsakte_zeilen, abruf, heute=None, bekannt=None):
    heute = heute or date.today().isoformat()
    bekannt = bekannt_laden() if bekannt is None else bekannt
    sitzungen = {s["id"]: s for s in daten["sitzungen"]}
    vorhanden = set()
    for s in daten["sitzungen"]:
        for t in s.get("termine") or [{"date": s["date"]}]:
            vorhanden.add((_gremium_schluessel(s.get("gremium_typ"), s.get("ortsteil"), s.get("gremium_id")), t.get("date")))
    luecken = {}

    def melden(schluessel, datum, gremium, grund, nr, pdf):
        if datum < config.STADT["quelle"]["datenbeginn"] or datum >= heute or (schluessel, datum) in vorhanden:
            return
        luecken.setdefault((schluessel, datum), {"datum": datum, "gremium": gremium, "grund": grund, "fundstelle": nr, "pdf": pdf})

    for v in daten["vorgaenge"]:
        for st in v["process"]:
            m = NIEDERSCHRIFT.search(st.get("titel") or "")
            if not m:
                continue
            s = sitzungen[st["sitzung"]]
            datum = f"{m[3]}-{int(m[2]):02d}-{int(m[1]):02d}"
            if "Stadtverordnetenversammlung" in st["titel"]:
                k, gremium = ("stvv", ""), "Stadtverordnetenversammlung"
            else:
                k, gremium = _gremium_schluessel(s.get("gremium_typ"), s.get("ortsteil"), s.get("gremium_id")), s["gremium"]
            melden(k, datum, gremium, "Niederschrift dieser Sitzung steht auf einer späteren Tagesordnung", s["bekanntmachung"], s["pdf"])
    for z in rechtsakte_zeilen:
        m = re.match(r"keine Einladung zum Sitzungstag (\d{4}-\d\d-\d\d)", z.get("grund", ""))
        if m:
            melden(("stvv", ""), m[1], "Stadtverordnetenversammlung", f"Beschlussdatum laut Bekanntmachung Nr. {z['nr']}", z["nr"], z["pdf"])

    liste = sorted(luecken.values(), key=lambda x: (x["datum"], x["gremium"]))
    for x in liste:
        x["neu"] = (x["datum"], x["gremium"]) not in bekannt
    warnungen = []
    neueste = max((s.get("veroeffentlicht") or s["date"] for s in daten["sitzungen"]), default=None)
    if neueste and neueste < (date.fromisoformat(heute) - timedelta(days=Q["tage_ohne_einladung"])).isoformat():
        warnungen.append(f"Seit {neueste} keine neue Einladung in den Bekanntmachungen (Grenze {Q['tage_ohne_einladung']} Tage). "
                         "Hat die Stadt Dateinamen oder Ablage geändert?")
    if abruf and abruf[:10] < (date.fromisoformat(heute) - timedelta(days=Q["tage_ohne_abruf"])).isoformat():
        warnungen.append(f"Liste der Bekanntmachungen zuletzt am {abruf[:10]} abgerufen (Grenze {Q['tage_ohne_abruf']} Tage).")
    return {"stand": heute, "luecken": liste, "warnungen": warnungen,
            "neu": sum(1 for x in liste if x["neu"]) + len(warnungen)}
