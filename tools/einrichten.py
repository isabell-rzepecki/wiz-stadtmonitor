"""Einrichtung der Erfassung (Issues 29 und 30): lokal, in zwei Schritten für zwei Rollen.

Zweck: Für die Stadt gibt es keinen Mietspiegel. Damit die Erfassungs-App (erfassen.html) speichern kann, braucht sie den
öffentlichen Schlüssel der Prüfgruppe; damit Personen hineinkommen, braucht sie Einladungscodes. Beides entsteht nur
lokal: Der private Schlüssel und die Codes laufen nie durch ein Repository, einen Chat oder GitHub Actions. In
config/stadt.json landen nur der öffentliche Schlüssel und die Hashes der Codes mit Ablaufdatum.

Aufruf aus dem Wurzelverzeichnis des Repositorys; PFADE für Schlüssel, Register und Druckblätter außerhalb jedes
Git-Repositorys (wird geprüft):
  1. Prüfgruppe (Schlüsselinhaber:in):
     python tools/einrichten.py schluessel PFAD/pg.json --druck PFAD/druck
       neues Schlüsselpaar (Passphrase wird abgefragt), Papiersicherung als Druckblatt, öffentlicher Teil in stadt.json
  2. Ausgabestelle (Person der verantwortlichen Stelle, nicht in der Prüfgruppe):
     python tools/einrichten.py codes ANZAHL --register PFAD/einladungen.tsv --druck PFAD/druck
       Codes erzeugen, Register ergänzen, Druckblatt mit den Codes zum Ausschneiden, Hashes in stadt.json
     python tools/einrichten.py widerrufen E-XXXXXXXX --register PFAD/einladungen.tsv
       im Register widerrufen und den Hash aus stadt.json entfernen
  Ohne Python: dieselben Schritte auf der Einrichtungsseite site/einrichten.html (im Browser, ohne Netz). Sie erzeugt
  „öffentliche Dateien“ (nur öffentlicher Schlüssel bzw. Hashes mit Ablaufdatum); übernommen werden sie mit
     python tools/einrichten.py uebernehmen DATEI…
Danach config/stadt.json committen; die Seite holt die neue Konfiguration beim nächsten Start mit Netz.
Druckblätter nach dem Druck löschen. Dem Register entsprechend erhält die Prüfgruppe eine Kopie (ohne Namen).
"""
import argparse
import base64
import hashlib
import json
import os
import re
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import einladung  # noqa: E402
import pruefgruppe as pg  # noqa: E402

STADT_JSON = pg.ROOT / "config" / "stadt.json"


def _wert_ersetzen(text, schluessel, neu):
    """Wert eines Felds im Block wohnen_eigentum.erfassung ersetzen; der Rest der Datei bleibt Zeichen für Zeichen gleich."""
    start = text.index('"erfassung": {', text.index('"wohnen_eigentum"'))
    pos = text.index(f'"{schluessel}":', start) + len(schluessel) + 3
    while text[pos] == " ":
        pos += 1
    _, ende = json.JSONDecoder().raw_decode(text, pos)
    einzug = " " * (pos - text.rfind("\n", 0, pos) - len(schluessel) - 5)
    if isinstance(neu, list) and neu:
        wert = "[\n" + ",\n".join(f"{einzug}  {json.dumps(x, ensure_ascii=False)}" for x in neu) + f"\n{einzug}]"
    else:
        wert = json.dumps(neu, ensure_ascii=False)
    return text[:pos] + wert + text[ende:]


def stadt_setzen(stadt_json=STADT_JSON, **felder):
    p = Path(stadt_json)
    text = p.read_text(encoding="utf-8")
    for k, v in felder.items():
        text = _wert_ersetzen(text, k, v)
    erfassung = json.loads(text)["wohnen_eigentum"]["erfassung"]
    assert all(erfassung[k] == v for k, v in felder.items())
    p.write_text(text, encoding="utf-8")
    return erfassung


def _druckblatt(ziel, html):
    ziel = pg.ausserhalb_git(ziel)
    if ziel.exists():
        raise pg.Abbruch(f"{ziel} gibt es schon.")
    ziel.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(ziel, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(html)
    return ziel


def schluessel(datei, druck, passphrase, stadt_json=STADT_JSON, stufe="moderat"):
    oeffentlich = pg.schluessel_erzeugen(datei, passphrase, stufe)
    blatt = pg.ausdruck(datei, Path(druck) / f"schluessel_sicherung_{oeffentlich['key_id']}.html")
    stadt_setzen(stadt_json, schluessel=oeffentlich)
    return oeffentlich, blatt


def codes(anzahl, register, druck, stadt_json=STADT_JSON, heute=None):
    heute = heute or date.today()
    stadt = json.loads(Path(stadt_json).read_text(encoding="utf-8"))
    F = stadt["wohnen_eigentum"]["erfassung"]
    adresse = stadt["projekt"]["site_url"].rstrip("/") + "/erfassen.html"
    aus = einladung.ausgeben(anzahl, register, F["einladung_gueltig_monate"], heute)
    karten = "".join(f"""<div class="karte"><p class="kopf">Einladung zur Erfassung Wohnen und Eigentum</p>
<p class="code">{c}</p><p>Gültig bis {e['bis'][8:10]}.{e['bis'][5:7]}.{e['bis'][:4]}. Erfasser-ID {eid}.</p>
<p>Erfassungsseite: <strong>{adresse}</strong></p>
<p class="klein">Code in der App eingeben, dann diesen Zettel vernichten. Nicht abfotografieren, nicht weitergeben.</p></div>"""
                     for c, eid, e in aus)
    blatt = _druckblatt(Path(druck) / f"einladungscodes_{heute.isoformat()}_{aus[0][1]}.html", f"""<!doctype html><meta charset="utf-8">
<title>Einladungscodes</title><style>body{{font:14px/1.4 sans-serif;margin:12mm}}.karte{{border:1px dashed #555;padding:8mm;margin:0 0 6mm;
break-inside:avoid}}.kopf{{font-weight:700;margin:0}}.code{{font:700 24px/1.2 monospace;letter-spacing:2px;margin:4mm 0}}.klein{{font-size:12px;color:#444}}</style>
<p>Ausschneiden und persönlich übergeben. Wer welche Erfasser-ID erhält, nur in den Unterlagen der Ausgabestelle notieren.
Dieses Blatt nach dem Druck löschen.</p>{karten}""")
    stadt_setzen(stadt_json, einladungen=[*F["einladungen"], *(e for _, _, e in aus)])
    return aus, blatt


def widerrufen(erfasser, register, stadt_json=STADT_JSON, heute=None):
    hashes = set(einladung.widerrufen(erfasser, register, heute))
    F = json.loads(Path(stadt_json).read_text(encoding="utf-8"))["wohnen_eigentum"]["erfassung"]
    bleiben = [e for e in F["einladungen"] if (e if isinstance(e, str) else e["hash"]) not in hashes]
    stadt_setzen(stadt_json, einladungen=bleiben)
    return len(F["einladungen"]) - len(bleiben)


# Öffentliche Dateien der Einrichtungsseite: nur diese Felder, sonst wird nichts übernommen
KEY_ID = re.compile(r"^pg-\d{8}-[0-9a-f]{8}$")
HASH = re.compile(r"^[0-9a-f]{64}$")


def oeffentlich_pruefen(d):
    """Inhalt einer öffentlichen Datei (format wiz-einrichtung-1) prüfen; gibt (schluessel|None, einladungen) zurück."""
    if not isinstance(d, dict) or d.get("format") != "wiz-einrichtung-1":
        raise pg.Abbruch("Keine öffentliche Datei der Einrichtungsseite (format wiz-einrichtung-1).")
    fremd = set(d) - {"format", "erstellt", "schluessel", "einladungen"}
    if fremd:
        raise pg.Abbruch(f"Unerwartete Felder: {', '.join(sorted(fremd))}.")
    s = d.get("schluessel")
    if s is not None:
        if not isinstance(s, dict) or set(s) != {"key_id", "alg", "public_key"} or s["alg"] != pg.ALG or not KEY_ID.match(str(s["key_id"])):
            raise pg.Abbruch("Schlüssel: nur key_id, alg und public_key im erwarteten Format.")
        try:
            pub = base64.b64decode(s["public_key"], validate=True)
        except ValueError:
            raise pg.Abbruch("Schlüssel: public_key ist kein Base64.") from None
        if len(pub) != 32 or hashlib.sha256(pub).hexdigest()[:8] != s["key_id"][-8:]:
            raise pg.Abbruch("Schlüssel: public_key passt nicht zur key_id.")
    e = d.get("einladungen") or []
    if not isinstance(e, list) or any(not isinstance(x, dict) or set(x) != {"hash", "bis"} or not HASH.match(str(x["hash"]))
                                      or not re.match(r"^\d{4}-\d{2}-\d{2}$", str(x["bis"])) for x in e):
        raise pg.Abbruch("Einladungen: nur hash (64 Hexziffern) und bis (JJJJ-MM-TT).")
    if s is None and not e:
        raise pg.Abbruch("Die Datei enthält weder Schlüssel noch Einladungen.")
    return s, e


def uebernehmen(dateien, stadt_json=STADT_JSON):
    """Öffentliche Dateien der Einrichtungsseite in stadt.json übernehmen (Schlüssel ersetzen, Einladungen ergänzen)."""
    F = json.loads(Path(stadt_json).read_text(encoding="utf-8"))["wohnen_eigentum"]["erfassung"]
    schl, einl = F["schluessel"], list(F["einladungen"])
    vorhanden = {x if isinstance(x, str) else x["hash"] for x in einl}
    for datei in dateien:
        s, e = oeffentlich_pruefen(json.loads(Path(datei).read_text(encoding="utf-8")))
        schl = s or schl
        einl += [x for x in e if x["hash"] not in vorhanden]
        vorhanden |= {x["hash"] for x in e}
    return stadt_setzen(stadt_json, schluessel=schl, einladungen=einl)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="befehl", required=True)
    s = sub.add_parser("schluessel")
    s.add_argument("datei")
    s.add_argument("--druck", required=True)
    s = sub.add_parser("codes")
    s.add_argument("anzahl", type=int)
    s.add_argument("--register", required=True)
    s.add_argument("--druck", required=True)
    s = sub.add_parser("widerrufen")
    s.add_argument("erfasser_id")
    s.add_argument("--register", required=True)
    s = sub.add_parser("uebernehmen")
    s.add_argument("dateien", nargs="+")
    a = ap.parse_args(argv)
    if a.befehl == "uebernehmen":
        alt = json.loads(STADT_JSON.read_text(encoding="utf-8"))["wohnen_eigentum"]["erfassung"]
        F = uebernehmen(a.dateien)
        if alt["schluessel"] and alt["schluessel"] != F["schluessel"]:
            print(f"Schlüssel ersetzt: {alt['schluessel']['key_id']} → {F['schluessel']['key_id']} (Schlüsselwechsel).")
        print(f"In config/stadt.json: Schlüssel {(F['schluessel'] or {}).get('key_id', 'keiner')}, {len(F['einladungen'])} Einladungen "
              f"({len(F['einladungen']) - len(alt['einladungen'])} neu). Danach committen und veröffentlichen.")
        return
    if a.befehl == "schluessel":
        oeffentlich, blatt = schluessel(a.datei, a.druck, pg.passphrase_abfragen(a.datei, neu=True))
        print(f"Schlüssel {oeffentlich['key_id']} erzeugt; öffentlicher Teil in config/stadt.json eingetragen.")
        print(f"Papiersicherung {blatt}: lokal drucken, Wiederherstellung probehalber prüfen, Datei löschen (docs/datenschutz/schluesselverfahren.md).")
    elif a.befehl == "codes":
        aus, blatt = codes(a.anzahl, a.register, a.druck)
        print(f"{len(aus)} Codes erzeugt, Register {a.register} ergänzt, Hashes in config/stadt.json eingetragen.")
        print(f"Druckblatt {blatt}: drucken, Codes persönlich auf Papier übergeben, Datei löschen. Register-Kopie an die Prüfgruppe.")
    else:
        n = widerrufen(a.erfasser_id, a.register)
        print(f"Im Register widerrufen; {n} Eintrag aus config/stadt.json entfernt. Committen und veröffentlichen.")
    print("Danach: git add config/stadt.json && git commit, dann veröffentlichen.")


if __name__ == "__main__":
    main()
