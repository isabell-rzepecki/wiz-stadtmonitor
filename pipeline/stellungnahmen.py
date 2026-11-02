"""Beteiligung der Ortsbeiräte: Tagesordnungspunkte eines Ortsbeirats, die eine Angelegenheit der Stadtverordneten-
versammlung betreffen, als abgeleitete Station an deren Vorgang.

Ortsbeiräte beraten Haushalt, Nachtrag, Investitionsprogramm und Bauleitpläne, bevor die Stadtverordnetenversammlung
beschließt (Anhörung nach § 82 Abs. 3 HGO). Ihre Tagesordnungspunkte tragen keine Vorlagennummer und stehen deshalb
als eigene Vorgänge. Verknüpft wird nur über eindeutige Schlüssel, nicht über ähnliche Titel:
- Haushalt und Nachtrag: Art und Haushaltsjahr aus dem Titel
- Investitionsprogramm: Jahr der Beratung (das Programm wird im Sommer eingebracht und beraten)
- Bauleitpläne: Planverfahren (Art, Nummer, Änderung, Gemarkung) wie beim Plan-Abgleich
Ziel ist der Vorgang der Stadtverordnetenversammlung zum selben Schlüssel, vorzugsweise der mit „Beschlussfassung“.
Gezählt wird, wie viele Ortsbezirke die Angelegenheit auf der Tagesordnung hatten, nicht, ob oder was sie beschlossen.
"""
import re
from datetime import date, timedelta

from . import config

BEIRAT = ("ortsbeirat", "stadtteilbeirat")
TOLERANZ_TAGE = 90
JAHR = r"(20\d\d)"


def schluessel(titel, datum):
    """Schlüssel der Angelegenheit aus einem Titel: {("haushalt", "2026"), ("nachtrag", "2025"), ("invest", "2026")}."""
    out = set()
    rest = titel
    m = re.search(rf"Nachtrag\w*\b[^.;]*?(?:Haushalt\w*[^.;]*?)?{JAHR}", rest, re.I)
    if m and not re.search(r"Haushaltssicherung", titel, re.I) and re.search(r"Haushalt|Nachtragshaushalt|Nachtrag (?:für|zum) (?:das )?Haushaltsjahr", m.group(0) + titel, re.I):
        out.add(("nachtrag", m.group(1)))
        rest = rest[:m.start()] + rest[m.end():]
    m = re.search(rf"Haushalt(?:ssatzung|splan|sentwurf|s)?\b[^.;]*?(?:Haushaltsjahr|Jahr|für)?\s*{JAHR}", rest, re.I)
    if m and not re.search(r"Haushaltssicherung|Haushaltssituation\b(?![^.;]*Haushaltsplan)", m.group(0), re.I):
        out.add(("haushalt", m.group(1)))
    if re.search(r"Investitionsprogramm|I-Programm", titel, re.I):
        out.add(("invest", datum[:4]))
    return out


TEXT = {"haushalt": "Haushalt {}", "nachtrag": "Nachtrag zum Haushalt {}", "invest": "Investitionsprogramm (beraten {})",
        "plan": "Planverfahren"}


def _text(k):
    return TEXT[k[0]].format(k[1]) if k[0] != "plan" else TEXT["plan"]


def verknuepfen(vorgaenge, sitzungen, verfahren):
    """Stationen „Stellungnahme“ an Vorgänge der Stadtverordnetenversammlung hängen (v["stellungnahmen"]) und am
    Ortsbeiratspunkt den Bezug vermerken (v["gehoert_zu"]). verfahren: {reference: {Planverfahren-Kennung}}.
    Gibt die Zeilen des Audits zurück."""
    def beirat(v):
        return all(sitzungen[s["sitzung"]]["gremium_typ"] in BEIRAT for s in v["process"])

    def stvv(v):
        return any(sitzungen[s["sitzung"]]["gremium_typ"] == "stvv" for s in v["process"])

    ziele = {}  # Schlüssel → [Vorgang der Stadtverordnetenversammlung]
    for v in vorgaenge:
        if v["verfahrenspunkt"] or not stvv(v):
            continue
        tops = [s for s in v["process"] if sitzungen[s["sitzung"]]["gremium_typ"] == "stvv"]
        for s in tops:
            for k in schluessel(s["titel"], s["date"]):
                # Haushalt und Nachtrag nur aus Titeln über die Satzung selbst (nicht Sicherungskonzept, Ausgaben)
                if k[0] in ("haushalt", "nachtrag") and not re.search(r"Haushaltssatzung|Nachtrag", s["titel"]):
                    continue
                ziele.setdefault(k, []).append(v)
        for f in verfahren.get(v["reference"], ()):
            ziele.setdefault(("plan", f), []).append(v)

    def letzte_stvv(v):
        return max(s["date"] for s in v["process"] if sitzungen[s["sitzung"]]["gremium_typ"] == "stvv")

    def bester(k, datum):
        alle = list({id(v): v for v in ziele.get(k, [])}.values())
        if k[0] == "plan":  # die nächste Entscheidung nach der Beratung im Ortsbeirat
            nach = [v for v in alle if letzte_stvv(v) >= datum]
            return min(nach, key=lambda v: min(s["date"] for s in v["process"] if s["date"] >= datum)) if nach else None
        # Beschluss nach der Beratung im Ortsbeirat; gibt es noch keinen, die Einbringung (Ortsbeiräte beraten danach,
        # Toleranz in Tagen). Ein Punkt nach dem Beschluss gehört nicht mehr zu diesem Vorgang.
        beschluss = [v for v in alle if any("Beschlussfassung" in s["titel"] for s in v["process"])]
        if beschluss:
            kand = [v for v in beschluss if letzte_stvv(v) >= datum]
        else:
            frueheste = (date.fromisoformat(datum) - timedelta(days=TOLERANZ_TAGE)).isoformat()
            kand = [v for v in alle if letzte_stvv(v) >= frueheste]
        return kand[0] if len(kand) == 1 else None

    zeilen = []
    for v in vorgaenge:
        if v["verfahrenspunkt"] or v["vorlage"] or not beirat(v):
            continue
        s = v["process"][0]
        sz = sitzungen[s["sitzung"]]
        keys = sorted(schluessel(s["titel"], s["date"])) + [("plan", f) for f in sorted(verfahren.get(v["reference"], ()))]
        for k in keys:
            ziel = bester(k, s["date"])
            zeilen.append({"vorgang": v["reference"], "gremium": s["gremium"], "datum": s["date"], "titel": s["titel"],
                           "schluessel": f"{k[0]}:{k[1]}", "ziel": ziel["reference"] if ziel else "",
                           "ziel_titel": ziel["name"] if ziel else ""})
            if not ziel or ziel is v:
                continue
            art = "Stellungnahme" if re.search(r"Stellungnahme", s["titel"], re.I) else "Beratung"
            ziel.setdefault("stellungnahmen", []).append(
                {"reference": v["reference"], "gremium": s["gremium"], "ortsteil": sz["ortsteil"], "sitzung": s["sitzung"],
                 "bekanntmachung": s["bekanntmachung"], "date": s["date"], "top": s["top"], "titel": s["titel"], "pdf": s["pdf"],
                 "art": art, "ueber": _text(k)})
            v.setdefault("gehoert_zu", []).append({"reference": ziel["reference"], "name": ziel["name"], "ueber": _text(k)})
            break  # ein Ziel je Ortsbeiratspunkt
    gesamt = sum(1 for o in config.STADT["ortsteile"] if o.get("ortsbezirk"))
    for v in vorgaenge:
        if v.get("stellungnahmen"):
            v["stellungnahmen"].sort(key=lambda x: (x["date"], x["gremium"]))
            v["ortsbeiraete"] = {"anzahl": len({x["ortsteil"] for x in v["stellungnahmen"]}), "von": gesamt}
    return zeilen
