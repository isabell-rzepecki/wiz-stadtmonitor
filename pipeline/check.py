"""Prüfung des Exports: Rückführbarkeit, Parserfehler, Datenschutz, Lizenzgrenzen. Bricht bei Verstößen ab."""
import collections
import json
import re

from . import config

MAX_FEHLERQUOTE = 0.05


def check():
    d = json.loads(config.VORGAENGE.read_text(encoding="utf-8"))
    probleme = []
    quote = d["meta"]["parserfehler"] / max(1, d["meta"]["einladungen"])
    if quote > MAX_FEHLERQUOTE:
        probleme.append(f"Parserfehler {quote:.1%} über {MAX_FEHLERQUOTE:.0%}")
    ids = {s["id"] for s in d["sitzungen"]}
    for v in d["vorgaenge"]:
        if not v["process"] or any(not s.get("pdf") or s["sitzung"] not in ids for s in v["process"]):
            probleme.append(f"{v['reference']}: Station ohne Quelle")
        for l in v["locations"]:
            if not (l.get("method") and l.get("confidence") and l.get("evidence") and l.get("source_pdf")):
                probleme.append(f"{v['reference']}: Ortsbezug ohne Methode, Konfidenz oder Fundstelle")
    # keine Wohnadressen natürlicher Personen als Sitzungsort
    for s in d["sitzungen"]:
        if s.get("ort") and re.match(r"^bei\s", s["ort"]):
            probleme.append(f"Sitzung {s['id']}: Privatanschrift als Ort")
    # Lizenzgrenze: im Export nur Plannummer und ein Punkt, keine Flächen der Bauleitplanung
    if '"coordinates"' in config.VORGAENGE.read_text(encoding="utf-8"):
        probleme.append("vorgaenge.json enthält Geometrien")
    je = collections.Counter(s["gremium"] for s in d["sitzungen"])
    print(f"{len(d['sitzungen'])} Sitzungen, {len(d['vorgaenge'])} Vorgänge, Parserfehler {quote:.1%}")
    for g, n in je.most_common():
        print(f"  {n:4} {g}")
    if probleme:
        raise SystemExit("Prüfung fehlgeschlagen:\n" + "\n".join(probleme[:50]))
