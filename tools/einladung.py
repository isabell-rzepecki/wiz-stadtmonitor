"""Einladungscodes für die Erfassungs-App (erfassen.html), lokal bei der Prüfgruppe erzeugt.

Aufruf (REGISTER außerhalb jedes Git-Repositorys, etwa ARBEIT/einladungen.tsv der Prüfgruppe):
  python tools/einladung.py neu [ANZAHL] --register REGISTER    Codes erzeugen, gültig 12 Monate (stadt.json)
  python tools/einladung.py widerrufen ERFASSER-ID --register REGISTER

Der Code geht persönlich auf Papier an die erfassende Person und wird nirgends gespeichert. In config/stadt.json
(wohnen_eigentum.erfassung.einladungen) kommen nur Hash und Ablaufdatum; Widerruf durch Entfernen des Eintrags dort und
im Register. Das Register (Erfasser-ID, Hash, Ausgabe, gültig bis, widerrufen; ohne Namen und ohne Code) nutzt
tools/pruefen.py, um Exporte nach Widerruf oder Ablauf abzuweisen. Die Zuordnung von ID zu Person führt allein die
Prüfgruppe, außerhalb jedes Git-Repositorys (docs/datenschutz/einladungsverfahren.md).

Hinweis: Ohne Server ist der Code nur eine Schwelle gegen zufällige Nutzung, kein harter Zugangsschutz.
Lesbar sind die Einträge trotzdem nur für die Prüfgruppe (Verschlüsselung mit ihrem öffentlichen Schlüssel).
"""
import argparse
import csv
import hashlib
import json
import secrets
from datetime import date
from pathlib import Path

KOPF = ["erfasser_id", "hash", "ausgegeben", "gueltig_bis", "widerrufen"]

# Crockford-Base32 ohne leicht verwechselbare Zeichen (I, L, O, U); 16 Zeichen = 80 Bit
ZEICHEN = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"


def normieren(code):
    """Großschreibung, ohne Leer- und Bindestriche; O als 0, I und L als 1 (Tippfehler beim Abschreiben)."""
    c = "".join(code.upper().split()).replace("-", "")
    return c.translate(str.maketrans({"O": "0", "I": "1", "L": "1"}))


def neu():
    roh = "".join(secrets.choice(ZEICHEN) for _ in range(16))
    return "-".join(roh[i:i + 4] for i in range(0, 16, 4))


def code_hash(code):
    return hashlib.sha256(f"wiz-einladung:{normieren(code)}".encode()).hexdigest()


def erfasser_id(code):
    return "E-" + hashlib.sha256(f"wiz-erfasser:{normieren(code)}".encode()).hexdigest()[:8]


def gueltig(code):
    c = normieren(code)
    return len(c) == 16 and all(z in ZEICHEN for z in c)


def bis_datum(ab: date, monate: int) -> str:
    j, m = divmod(ab.year * 12 + ab.month - 1 + monate, 12)
    return date(j, m + 1, min(ab.day, 28)).isoformat()


def register_lesen(pfad):
    p = Path(pfad)
    if not p.exists():
        return []
    with p.open(encoding="utf-8") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def register_schreiben(pfad, zeilen):
    import pruefgruppe  # noqa: PLC0415 – nur hier gebraucht (Prüfung: nicht in einem Git-Repository)
    p = pruefgruppe.ausserhalb_git(pfad)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(".tmp")
    with tmp.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, KOPF, delimiter="\t", lineterminator="\n")
        w.writeheader()
        w.writerows(zeilen)
    tmp.replace(p)


def ausgeben(anzahl, register, monate, heute=None):
    """Neue Codes; Register ergänzt. Gibt [(code, erfasser_id, eintrag_für_stadt_json)] zurück."""
    heute = heute or date.today()
    zeilen, out = register_lesen(register), []
    for _ in range(anzahl):
        c = neu()
        e = {"hash": code_hash(c), "bis": bis_datum(heute, monate)}
        zeilen.append({"erfasser_id": erfasser_id(c), "hash": e["hash"], "ausgegeben": heute.isoformat(), "gueltig_bis": e["bis"], "widerrufen": ""})
        out.append((c, erfasser_id(c), e))
    register_schreiben(register, zeilen)
    return out


def widerrufen(erfasser, register, heute=None):
    zeilen = register_lesen(register)
    treffer = [z for z in zeilen if z["erfasser_id"] == erfasser]
    if not treffer:
        raise SystemExit(f"{erfasser} steht nicht im Register.")
    for z in treffer:
        z["widerrufen"] = z["widerrufen"] or (heute or date.today()).isoformat()
    register_schreiben(register, zeilen)
    return [z["hash"] for z in treffer]


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Einladungscodes für die Erfassungs-App")
    sub = ap.add_subparsers(dest="befehl", required=True)
    p = sub.add_parser("neu")
    p.add_argument("anzahl", nargs="?", type=int, default=1)
    p.add_argument("--register", required=True)
    p = sub.add_parser("widerrufen")
    p.add_argument("erfasser_id")
    p.add_argument("--register", required=True)
    a = ap.parse_args()
    stadt = json.loads((Path(__file__).resolve().parent.parent / "config" / "stadt.json").read_text(encoding="utf-8"))
    monate = stadt["wohnen_eigentum"]["erfassung"]["einladung_gueltig_monate"]
    if a.befehl == "neu":
        for c, eid, e in ausgeben(a.anzahl, a.register, monate):
            print(f"Code {c}\tErfasser-ID {eid}\tfür stadt.json: {json.dumps(e)}")
        print("Code nur persönlich auf Papier weitergeben; nicht speichern, nicht per E-Mail oder Messenger.")
    else:
        for h in widerrufen(a.erfasser_id, a.register):
            print(f"Im Register widerrufen. In config/stadt.json den Eintrag mit hash {h} entfernen und veröffentlichen.")
