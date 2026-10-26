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

import nacl.exceptions
import nacl.pwhash
import nacl.utils
from nacl.public import PrivateKey, PublicKey, SealedBox
from nacl.secret import SecretBox

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
STUFEN = {"moderat": (nacl.pwhash.argon2id.OPSLIMIT_MODERATE, nacl.pwhash.argon2id.MEMLIMIT_MODERATE),
          "interaktiv": (nacl.pwhash.argon2id.OPSLIMIT_INTERACTIVE, nacl.pwhash.argon2id.MEMLIMIT_INTERACTIVE)}  # interaktiv nur für Tests


def _schuetzen(geheim: bytes, passphrase, stufe="moderat"):
    """Privaten Schlüssel mit der Passphrase verschlüsseln (Argon2id, XSalsa20-Poly1305)."""
    if not passphrase or len(passphrase) < 12:
        raise Abbruch("Passphrase mit mindestens 12 Zeichen angeben.")
    ops, mem = STUFEN[stufe]
    salz = nacl.utils.random(nacl.pwhash.argon2id.SALTBYTES)
    k = nacl.pwhash.argon2id.kdf(SecretBox.KEY_SIZE, passphrase.encode(), salz, opslimit=ops, memlimit=mem)
    return {"kdf": "argon2id", "opslimit": ops, "memlimit": mem, "salt": b64(salz), "ciphertext": b64(SecretBox(k).encrypt(geheim))}


def _entsperren(enc, passphrase):
    if passphrase is None:
        raise Abbruch("Die Schlüsseldatei ist mit einer Passphrase geschützt; bitte angeben.")
    k = nacl.pwhash.argon2id.kdf(SecretBox.KEY_SIZE, passphrase.encode(), base64.b64decode(enc["salt"]),
                                 opslimit=enc["opslimit"], memlimit=enc["memlimit"])
    try:
        return SecretBox(k).decrypt(base64.b64decode(enc["ciphertext"]))
    except nacl.exceptions.CryptoError:
        raise Abbruch("Passphrase falsch oder Schlüsseldatei beschädigt.") from None


def _neues_paar(passphrase, stufe):
    k = PrivateKey.generate()
    pub = bytes(k.public_key)
    oeffentlich = {"key_id": f"pg-{datetime.now():%Y%m%d}-{hashlib.sha256(pub).hexdigest()[:8]}", "alg": ALG, "public_key": b64(pub)}
    return oeffentlich, {**oeffentlich, "secret_enc": _schuetzen(bytes(k), passphrase, stufe)}


def _schreiben(datei, inhalt, neu=True):
    tmp = datei.with_suffix(".tmp")
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(inhalt, f)
    if neu and datei.exists():
        tmp.unlink()
        raise Abbruch(f"{datei} gibt es schon; ein Schlüssel wird nie überschrieben.")
    tmp.replace(datei)


def schluessel_erzeugen(datei, passphrase, stufe="moderat"):
    """Neues Schlüsselpaar; der private Teil liegt nur mit der Passphrase verschlüsselt in der Datei.
    Datei und Passphrase nur bei den Schlüsselinhaber:innen. Gibt den öffentlichen Teil für stadt.json zurück."""
    datei = ausserhalb_git(datei)
    if datei.exists():
        raise Abbruch(f"{datei} gibt es schon; ein Schlüssel wird nie überschrieben.")
    oeffentlich, eintrag = _neues_paar(passphrase, stufe)
    datei.parent.mkdir(parents=True, exist_ok=True)
    _schreiben(datei, {"version": 2, **eintrag, "frueher": [], "gesperrt": []})
    return oeffentlich


class Schluessel:
    """Aktueller Schlüssel der Prüfgruppe und frühere (für ältere Exporte und Bestände); gesperrte Kennungen nach einer
    Kompromittierung. Frühere Dateien ohne Passphrase (Feld secret_key) werden noch gelesen."""

    def __init__(self, datei, passphrase=None):
        self.datei = ausserhalb_git(datei)
        self.d = json.loads(self.datei.read_text(encoding="utf-8"))
        self.passphrase = passphrase
        self.key_id, self.alg = self.d["key_id"], self.d["alg"]
        self.paare = {}
        for e in [self.d, *self.d.get("frueher", [])]:
            geheim = base64.b64decode(e["secret_key"]) if "secret_key" in e else _entsperren(e["secret_enc"], passphrase)
            k = PrivateKey(geheim)
            if b64(bytes(k.public_key)) != e["public_key"]:
                raise Abbruch("Schlüsseldatei beschädigt: öffentlicher und privater Teil passen nicht zusammen.")
            self.paare[e["key_id"]] = k
        self.privat = self.paare[self.key_id]
        self.oeffentlich = self.privat.public_key
        self.gesperrt = set(self.d.get("gesperrt", []))

    def kennt(self, key_id):
        return key_id in self.paare and key_id not in self.gesperrt

    def oeffnen(self, ciphertext_b64, key_id=None):
        """Mit dem Schlüssel der Kennung entschlüsseln; ohne Kennung zuerst mit dem aktuellen, dann mit früheren."""
        ct = base64.b64decode(ciphertext_b64)
        kandidaten = [self.paare[key_id]] if key_id else [self.privat, *(k for i, k in self.paare.items() if i != self.key_id)]
        for k in kandidaten:
            try:
                return SealedBox(k).decrypt(ct)
            except nacl.exceptions.CryptoError:
                continue
        raise nacl.exceptions.CryptoError("mit keinem Schlüssel der Prüfgruppe zu öffnen")

    def wechseln(self, kompromittiert=False, neue_passphrase=None, stufe="moderat"):
        """Neues aktuelles Paar; das bisherige bleibt als früheres (zum Öffnen alter Exporte), bei Kompromittierung gesperrt."""
        pw = neue_passphrase or self.passphrase
        oeffentlich, eintrag = _neues_paar(pw, stufe)
        alt = {k: v for k, v in self.d.items() if k not in ("version", "frueher", "gesperrt")}
        if "secret_key" in alt:  # frühere Datei ohne Passphrase: jetzt geschützt ablegen
            alt["secret_enc"] = _schuetzen(base64.b64decode(alt.pop("secret_key")), pw, stufe)
        frueher = [alt, *self.d.get("frueher", [])]
        if neue_passphrase:  # alle früheren Schlüssel unter der neuen Passphrase
            frueher = [{**f, "secret_enc": _schuetzen(bytes(self.paare[f["key_id"]]), pw, stufe)} for f in frueher]
            frueher = [{k: v for k, v in f.items() if k != "secret_key"} for f in frueher]
        gesperrt = sorted(self.gesperrt | ({self.key_id} if kompromittiert else set()))
        _schreiben(self.datei, {"version": 2, **eintrag, "frueher": frueher, "gesperrt": gesperrt}, neu=False)
        self.__init__(self.datei, pw)
        return oeffentlich


def passphrase_abfragen(datei, neu=False):
    """Passphrase für die Kommandozeile (nie als Argument, damit sie nicht in der Shell-Historie landet)."""
    import getpass
    if neu:
        a, b = getpass.getpass("Neue Passphrase (mindestens 12 Zeichen): "), getpass.getpass("Wiederholen: ")
        if a != b:
            raise Abbruch("Passphrasen stimmen nicht überein.")
        return a
    d = json.loads(Path(datei).read_text(encoding="utf-8"))
    return getpass.getpass("Passphrase: ") if "secret_enc" in d else None


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
        return self.schl.oeffnen(enc["ciphertext"], enc.get("key_id") if enc.get("key_id") in self.schl.paare else None).decode()

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
