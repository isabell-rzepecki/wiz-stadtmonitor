"""Sperre gegen personenbezogene Rohdaten im Repository (Übergabe v0.4.2, W6, Regeln R1 und R9).

Lehnt ab: verschlüsselte Exportdateien und Bestände (*.age, *.bin, *.sealed), Schlüsseldateien (secret_key),
Zugriffsprotokolle (namenzugriff.tsv) und Datendateien mit Feldern einzelner Erfassungen (Namen von Privatpersonen,
Kennungen und Beträge einzelner Mietangaben, Einwilligungen). Geprüft werden Datendateien (JSON, GeoJSON, TSV, CSV, JSONL);
Quellcode, die Schemata und die Konfiguration dürfen die Feldnamen nennen.

Aufruf:
  python tools/sperre.py --staged   vorgemerkte Dateien (Pre-Commit-Hook .githooks/pre-commit)
  python tools/sperre.py --alle     alle Dateien im Repository (CI)
  python tools/sperre.py DATEI…
Rückgabewert 1 bei einem Fund.
"""
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENDUNGEN_VERBOTEN = {".age", ".bin", ".sealed"}
NAMEN_VERBOTEN = {"namenzugriff.tsv", "bestand.sealed"}
DATEN = {".json", ".geojson", ".tsv", ".csv", ".jsonl", ".ndjson"}
FELDER = {"name_privat_enc", "name_privat", "angabe_id", "nettokalt_eur", "wohnflaeche_m2", "eur_je_m2", "einwilligung", "secret_key", "ciphertext"}
# Schemata und Konfiguration beschreiben die Felder nur; sie enthalten keine Erfassungen
ERLAUBT = {"docs/uebergabe-v0.4.2/schema_erfassung_eigentum.json", "docs/uebergabe-v0.4.2/schema_mietangabe.json", "config/stadt.json"}


def schluessel(x):
    if isinstance(x, dict):
        for k, v in x.items():
            yield k
            yield from schluessel(v)
    elif isinstance(x, list):
        for v in x:
            yield from schluessel(v)


def befund(pfad: Path, rel: str, inhalt: bytes):
    if pfad.suffix.lower() in ENDUNGEN_VERBOTEN or pfad.name.lower() in NAMEN_VERBOTEN:
        return "verschlüsselte Export- oder Bestandsdatei"
    if pfad.suffix.lower() not in DATEN or rel in ERLAUBT:
        return None
    text = inhalt.decode("utf-8", errors="replace")
    if "wiz-stadtmonitor-erfassung" in text:
        return "Exportdatei der Erfassung"
    if pfad.suffix.lower() in (".json", ".geojson"):
        try:
            felder = FELDER & set(schluessel(json.loads(text)))
        except ValueError:
            felder = {f for f in FELDER if f'"{f}"' in text}
    elif pfad.suffix.lower() in (".jsonl", ".ndjson"):
        felder = {f for f in FELDER if f'"{f}"' in text}
    else:
        kopf = re.split(r"[\t,;]", text.split("\n", 1)[0].strip().lower())
        felder = FELDER & set(kopf)
    return f"Felder einzelner Erfassungen: {', '.join(sorted(felder))}" if felder else None


def dateien(modus, args):
    if modus == "--staged":
        out = subprocess.run(["git", "diff", "--cached", "--name-only", "--diff-filter=ACMR", "-z"], cwd=ROOT, capture_output=True, check=True).stdout
        return [(n, subprocess.run(["git", "show", f":{n}"], cwd=ROOT, capture_output=True, check=True).stdout) for n in out.decode().split("\0") if n]
    if modus == "--alle":
        out = subprocess.run(["git", "ls-files", "-z"], cwd=ROOT, capture_output=True, check=True).stdout
        return [(n, (ROOT / n).read_bytes()) for n in out.decode().split("\0") if n and (ROOT / n).is_file()]
    return [(str(Path(a).resolve().relative_to(ROOT)) if Path(a).resolve().is_relative_to(ROOT) else a, Path(a).read_bytes()) for a in args]


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    modus = argv[0] if argv and argv[0] in ("--staged", "--alle") else None
    funde = [(n, b) for n, inhalt in dateien(modus, argv[1:] if modus else argv) if (b := befund(Path(n), n.replace("\\", "/"), inhalt))]
    for n, b in funde:
        print(f"gesperrt: {n}: {b}", file=sys.stderr)
    if funde:
        print("Personenbezogene Rohdaten gehören in kein Git-Repository (Regel R9). Datei entfernen: git rm --cached DATEI", file=sys.stderr)
    return 1 if funde else 0


if __name__ == "__main__":
    sys.exit(main())
