"""Gemeinsame Grundlagen der Prüfgruppe (Übergabe v0.4.2, W5): Schlüssel, versiegelter Bestand, Zugriffsprotokoll.

Zweck: Für die Stadt gibt es keinen Mietspiegel. Die Prüfgruppe prüft die Erfassungen (Eigentum und Vermietung durch das
Team, freiwillige Mietangaben mit Einwilligung) und gibt daraus nur zusammengefasste, zulässige Dateien frei.

Datenschutz:
- Läuft nur lokal bei der Prüfgruppe, nie im Browser und nie in GitHub Actions.
- Arbeitsverzeichnis und Schlüsseldatei müssen außerhalb jedes Git-Repositorys liegen (wird geprüft).
- Der Bestand liegt nur versiegelt vor (libsodium sealed box mit dem Schlüssel der Prüfgruppe); entschlüsselt wird er
  nur im Arbeitsspeicher.
- Jede Entschlüsselung eines Namens einer Privatperson wird in namenzugriff.tsv protokolliert (wer, wann, Datensatz, Zweck).
"""
import base64
import csv
import hashlib
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path

from nacl.public import PrivateKey, PublicKey, SealedBox

ROOT = Path(__file__).resolve().parent.parent
ALG = "libsodium-sealedbox-x25519"
SCHEMAS = {"eigentum": ROOT / "docs" / "uebergabe-v0.4.2" / "schema_erfassung_eigentum.json",
           "miete": ROOT / "docs" / "uebergabe-v0.4.2" / "schema_mietangabe.json"}
STADT = json.loads((ROOT / "config" / "stadt.json").read_text(encoding="utf-8"))

jetzt = lambda: datetime.now(timezone.utc).isoformat(timespec="seconds")  # noqa: E731
b64 = lambda b: base64.b64encode(b).decode()  # noqa: E731


class Abbruch(SystemExit):
    """Fehler mit verständlicher Meldung (ohne Inhalte von Datensätzen)."""


def ausserhalb_git(pfad):
    p = Path(pfad).resolve()
    for d in (p, *p.parents):
        if (d / ".git").exists():
            raise Abbruch(f"{p} liegt in einem Git-Repository ({d}). Rohdaten und Schlüssel gehören nie in ein Repository.")
    return p


# --- Schlüssel ---------------------------------------------------------------------------------------------------
def schluessel_erzeugen(datei):
    """Neues Schlüsselpaar; die Datei (mit privatem Schlüssel) nur für die Schlüsselinhaber:innen. Gibt den öffentlichen Teil zurück."""
    datei = ausserhalb_git(datei)
    if datei.exists():
        raise Abbruch(f"{datei} gibt es schon; ein Schlüssel wird nie überschrieben.")
    k = PrivateKey.generate()
    pub = bytes(k.public_key)
    oeffentlich = {"key_id": f"pg-{datetime.now():%Y%m%d}-{hashlib.sha256(pub).hexdigest()[:8]}", "alg": ALG, "public_key": b64(pub)}
    datei.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(datei, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump({**oeffentlich, "secret_key": b64(bytes(k))}, f)
    return oeffentlich


class Schluessel:
    def __init__(self, datei):
        d = json.loads(ausserhalb_git(datei).read_text(encoding="utf-8"))
        self.key_id, self.alg = d["key_id"], d["alg"]
        self.privat = PrivateKey(base64.b64decode(d["secret_key"]))
        self.oeffentlich = self.privat.public_key
        if b64(bytes(self.oeffentlich)) != d["public_key"]:
            raise Abbruch("Schlüsseldatei beschädigt: öffentlicher und privater Teil passen nicht zusammen.")

    def oeffnen(self, ciphertext_b64):
        return SealedBox(self.privat).decrypt(base64.b64decode(ciphertext_b64))


def versiegeln(public_key_b64, daten: bytes):
    return b64(SealedBox(PublicKey(base64.b64decode(public_key_b64))).encrypt(daten))


# --- Freitext wie in der App (site/erfassen-pruefung.js) ----------------------------------------------------------
STRASSE = re.compile(r"(str(a(ß|ss)e)?\.?|weg|gasse|platz|allee|ring|damm|ufer|markt|berg|hof|tor|graben|feld|pfad|steig|anger|siedlung|chaussee)"
                     r"\s*\d+\s*[a-z]?\b", re.I)
REGELN = [(STRASSE, "keine Hausnummern"), (re.compile(r"\b(nr|no|hausnr|hausnummer)\.?\s*\d", re.I), "keine Hausnummern"),
          (re.compile(r"\bhausnummer\b", re.I), "keine Hausnummern"), (re.compile(r"[^\s@]+@[^\s@]+\.[a-z]{2,}", re.I), "keine E-Mail-Adressen"),
          (re.compile(r"(\+|\b0)\d[\d\s/()-]{6,}\d"), "keine Telefonnummern")]


def freitext(text, ohne_ziffern=False):
    if not text:
        return None
    if ohne_ziffern and re.search(r"\d", text):
        return "keine Ziffern (also keine Hausnummern)"
    return next((t for rx, t in REGELN if rx.search(text)), None)


# --- Arbeitsverzeichnis: versiegelter Bestand, Protokolle -----------------------------------------------------------
class Arbeit:
    def __init__(self, pfad, schluessel: Schluessel, pruefer):
        if not re.fullmatch(r"P-[\w-]{1,20}", pruefer or ""):
            raise Abbruch("Prüfer-ID im Format P-… angeben (pseudonym, kein Name).")
        self.pfad, self.schl, self.pruefer = ausserhalb_git(pfad), schluessel, pruefer
        self.pfad.mkdir(parents=True, exist_ok=True)
        self.datei = self.pfad / "bestand.sealed"
        self.d = (json.loads(self.schl.oeffnen(self.datei.read_text(encoding="ascii")))
                  if self.datei.exists() else {"version": 1, "eintraege": {}, "vermieter_naechste": 1, "verlauf": []})

    @property
    def eintraege(self):
        return self.d["eintraege"]

    def speichern(self):
        tmp = self.datei.with_suffix(".tmp")
        tmp.write_text(versiegeln(b64(bytes(self.schl.oeffentlich)), json.dumps(self.d, ensure_ascii=False).encode()), encoding="ascii")
        tmp.replace(self.datei)

    def verlauf(self, aktion, datensatz=""):
        self.d["verlauf"].append({"zeit": jetzt(), "pruefer": self.pruefer, "aktion": aktion, "datensatz": datensatz})

    def name_oeffnen(self, eintrag_id, zweck):
        """Name einer Privatperson entschlüsseln, mit Eintrag im Zugriffsprotokoll."""
        enc = self.eintraege[eintrag_id]["datensatz"].get("name_privat_enc")
        if not enc:
            return None
        p = self.pfad / "namenzugriff.tsv"
        neu = not p.exists()
        with p.open("a", encoding="utf-8", newline="") as f:
            w = csv.writer(f, delimiter="\t")
            if neu:
                w.writerow(["zeit", "pruefer", "datensatz", "zweck"])
            w.writerow([jetzt(), self.pruefer, eintrag_id, zweck])
        return self.schl.oeffnen(enc["ciphertext"]).decode()

    def freigegeben(self, e):
        return e["status"] == "offen" and not e.get("konflikt") and len(set(e["freigaben"])) >= 2

    def audit(self, name, kopf, zeilen):
        (self.pfad / "audit").mkdir(exist_ok=True)
        p = self.pfad / "audit" / name
        with p.open("w", encoding="utf-8", newline="") as f:
            w = csv.writer(f, delimiter="\t")
            w.writerow(kopf)
            w.writerows(zeilen)
        return p


def name_normieren(n):
    """Für den Abgleich: Kleinschreibung, ohne Satzzeichen, Leerraum vereinheitlicht."""
    return " ".join(re.sub(r"[^\wäöüß ]", " ", n.casefold()).split())
