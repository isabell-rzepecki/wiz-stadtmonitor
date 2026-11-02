"""Prüfung des Exports: Rückführbarkeit, Parserfehler, Datenschutz, Lizenzgrenzen. Bricht bei Verstößen ab."""
import collections
import json

from . import config, parse

MAX_FEHLERQUOTE = 0.05


def check():
    d = json.loads(config.VORGAENGE.read_text(encoding="utf-8"))
    probleme = []
    quote = d["meta"]["parserfehler"] / max(1, d["meta"]["einladungen"])
    if not d["meta"]["einladungen"] or not d["sitzungen"]:  # leere Liste der Quelle: nicht als neuen Stand veröffentlichen
        probleme.append("keine Einladungen oder Sitzungen im Export")
    if quote > MAX_FEHLERQUOTE:
        probleme.append(f"Parserfehler {quote:.1%} über {MAX_FEHLERQUOTE:.0%}")
    ids = {s["id"] for s in d["sitzungen"]}
    refs = {v["reference"] for v in d["vorgaenge"]}
    for v in d["vorgaenge"]:
        if not v["process"] or any(not s.get("pdf") or s["sitzung"] not in ids for s in v["process"]):
            probleme.append(f"{v['reference']}: Station ohne Quelle")
        for x in v.get("stellungnahmen", []):  # Station eines Ortsbeirats nur mit Einladung und bestehendem Vorgang
            if not x.get("pdf") or x.get("sitzung") not in ids or x.get("reference") not in refs:
                probleme.append(f"{v['reference']}: Stellungnahme ohne Quelle oder Vorgang")
            if parse.ohne_namen(x.get("titel", "")) != x.get("titel", ""):
                probleme.append(f"{v['reference']}: Personenname im Titel einer Stellungnahme")
        for e in v.get("ergebnisse", []):  # Ergebnis nur mit amtlicher Bekanntmachung und Sicherheitsstufe
            if not (e.get("pdf") and e.get("nr") and e.get("sicherheit") in ("sicher", "geprüft", "möglicherweise")):
                probleme.append(f"{v['reference']}: Ergebnis ohne Bekanntmachung oder Sicherheit")
            if parse.ohne_namen(e.get("gegenstand", "")) != e.get("gegenstand", ""):
                probleme.append(f"{v['reference']}: Personenname im Gegenstand eines Ergebnisses")
        for l in v["locations"]:
            if not (l.get("method") and l.get("confidence") and l.get("evidence") and l.get("source_pdf")):
                probleme.append(f"{v['reference']}: Ortsbezug ohne Methode, Konfidenz oder Fundstelle")
    # keine Wohnadressen natürlicher Personen als Sitzungsort, keine Personennamen in Titeln
    for s in d["sitzungen"]:
        if s.get("ort") and not s["ort"].startswith("Privatanschrift") and parse.PRIVAT.search(s["ort"]):
            probleme.append(f"Sitzung {s['id']}: Privatanschrift als Ort")
    for v in d["vorgaenge"]:
        for txt in [v.get("name", ""), *(st.get("titel", "") for st in v["process"])]:
            if parse.ohne_namen(txt) != txt:
                probleme.append(f"{v['reference']}: Personenname im Titel")
    # Lizenzgrenze: im Export nur Plannummer und ein Punkt, keine Flächen der Bauleitplanung
    if '"coordinates"' in config.VORGAENGE.read_text(encoding="utf-8"):
        probleme.append("vorgaenge.json enthält Geometrien")
    # Kartenebenen ohne Objekte: Hinweis im Protokoll (die Seite zeigt dann eine Lücke)
    for p in sorted((config.EXPORT / "karte").glob("*.json")):
        ebene = json.loads(p.read_text(encoding="utf-8"))
        if ebene.get("type") == "FeatureCollection" and not ebene.get("features"):
            print(f"Hinweis: Kartenebene {p.name} ohne Objekte")
    je = collections.Counter(s["gremium"] for s in d["sitzungen"])
    print(f"{len(d['sitzungen'])} Sitzungen, {len(d['vorgaenge'])} Vorgänge, Parserfehler {quote:.1%}")
    for g, n in je.most_common():
        print(f"  {n:4} {g}")
    if probleme:
        raise SystemExit("Prüfung fehlgeschlagen:\n" + "\n".join(probleme[:50]))
