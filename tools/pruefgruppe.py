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


# --- Sicherung auf Papier ----------------------------------------------------------------------------------------
# Die Schlüsseldatei bleibt dabei mit der Passphrase geschützt; der Ausdruck allein öffnet nichts. Format: nummerierte
# Zeilen „NNN TEXT PRÜF“ (Base64 in Stücken zu 60 Zeichen, PRÜF = 4 Hexziffern aus SHA-256), Zeile 000 mit Anzahl und
# Prüfsumme. Dieselben Zeilen stehen in den QR-Codes (je bis zu 5), damit Scannen und Abtippen dasselbe ergeben.
ZEILE = re.compile(r"^\s*(\d{3})\s+(\S+)\s+([0-9a-f]{4})\s*$")


def _pruef(nr, text):
    return hashlib.sha256(f"{nr:03d}{text}".encode()).hexdigest()[:4]


def ausdruck_zeilen(datei):
    d = json.loads(ausserhalb_git(datei).read_text(encoding="utf-8"))
    if any("secret_key" in e for e in [d, *d.get("frueher", [])]):
        raise Abbruch("Die Datei enthält einen Schlüssel ohne Passphrase; zuerst schluessel-wechsel --neue-passphrase.")
    roh = base64.b64encode(json.dumps(d, separators=(",", ":")).encode()).decode()
    stuecke = [roh[i:i + 60] for i in range(0, len(roh), 60)]
    kopf = f"WIZPG1:{len(stuecke)}:{hashlib.sha256(roh.encode()).hexdigest()[:16]}"
    return [f"{i:03d} {t} {_pruef(i, t)}" for i, t in enumerate([kopf, *stuecke])], d


def ausdruck(datei, ziel):
    """Druckbare HTML-Seite (QR-Codes und Zeilen zum Abtippen) außerhalb jedes Git-Repositorys; nach dem Druck löschen."""
    import segno  # noqa: PLC0415 – nur für den Ausdruck gebraucht
    zeilen, d = ausdruck_zeilen(datei)
    ziel = ausserhalb_git(ziel)
    if ziel.exists():
        raise Abbruch(f"{ziel} gibt es schon.")
    bloecke = [zeilen[i:i + 5] for i in range(0, len(zeilen), 5)]
    qr = "".join(f'<figure>{segno.make(chr(10).join(b), error="m").svg_inline(scale=4)}<figcaption>Zeilen {b[0][:3]}–{b[-1][:3]}</figcaption></figure>'
                 for b in bloecke)
    ids = ", ".join(e["key_id"] for e in [d, *d.get("frueher", [])])
    html = f"""<!doctype html><meta charset="utf-8"><title>Sicherung Schlüssel Prüfgruppe</title>
<style>body{{font:12px/1.4 monospace;margin:16mm}}figure{{display:inline-block;margin:0 12px 12px 0}}pre{{font-size:11px}}</style>
<h1>Sicherung der Schlüsseldatei der Prüfgruppe</h1>
<p>Erstellt {datetime.now():%d.%m.%Y}. Schlüssel: {ids}. Aktuell: {d["key_id"]}.</p>
<p>Nur mit der Passphrase nutzbar; die Passphrase liegt getrennt. Wiederherstellen: QR-Codes scannen oder Zeilen abtippen,
als Textdatei speichern, dann <code>python tools/pruefen.py schluessel-zurueck TEXTDATEI ZIEL</code>.</p>
{qr}<pre>{chr(10).join(zeilen)}</pre>"""
    ziel.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(ziel, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(html)
    return ziel


def aus_ausdruck(text, ziel):
    """Schlüsseldatei aus gescannten oder abgetippten Zeilen; jede Zeile und das Ganze werden geprüft, nichts überschrieben."""
    gelesen = {}
    for z in text.splitlines():
        m = ZEILE.match(z)
        if not m:
            continue
        nr, t, p = int(m[1]), m[2], m[3]
        if _pruef(nr, t) != p:
            raise Abbruch(f"Zeile {nr:03d}: Prüfziffern passen nicht (Tippfehler?).")
        gelesen[nr] = t
    kopf = gelesen.get(0, "").split(":")
    if len(kopf) != 3 or kopf[0] != "WIZPG1":
        raise Abbruch("Zeile 000 fehlt oder ist keine Sicherung der Prüfgruppe.")
    fehlen = [f"{i:03d}" for i in range(1, int(kopf[1]) + 1) if i not in gelesen]
    if fehlen:
        raise Abbruch(f"Es fehlen Zeilen: {', '.join(fehlen)}.")
    roh = "".join(gelesen[i] for i in range(1, int(kopf[1]) + 1))
    if hashlib.sha256(roh.encode()).hexdigest()[:16] != kopf[2]:
        raise Abbruch("Prüfsumme der Sicherung passt nicht.")
    ziel = ausserhalb_git(ziel)
    if ziel.exists():
        raise Abbruch(f"{ziel} gibt es schon; ein Schlüssel wird nie überschrieben.")
    ziel.parent.mkdir(parents=True, exist_ok=True)
    _schreiben(ziel, json.loads(base64.b64decode(roh)))
    return ziel


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
