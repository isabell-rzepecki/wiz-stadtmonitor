"""Einladungscodes für die Erfassungs-App (erfassen.html), lokal bei der Prüfgruppe erzeugt.

Aufruf: python tools/einladung.py [ANZAHL]  – gibt je Code den Code, seinen Hash und die Erfasser-ID aus.

Der Code geht an die erfassende Person und wird nirgends gespeichert. In config/stadt.json
(wohnen_eigentum.erfassung.einladungen) kommt nur der Hash; Widerruf durch Entfernen des Hashes.
Die Erfasser-ID ist pseudonym und wird aus dem Code abgeleitet; die Zuordnung von ID zu Person
führt allein die Prüfgruppe, außerhalb jedes Git-Repositorys.

Hinweis: Ohne Server ist der Code nur eine Schwelle gegen zufällige Nutzung, kein harter Zugangsschutz.
Lesbar sind die Einträge trotzdem nur für die Prüfgruppe (Verschlüsselung mit ihrem öffentlichen Schlüssel).
"""
import hashlib
import secrets
import sys

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


if __name__ == "__main__":
    for _ in range(int(sys.argv[1]) if len(sys.argv) > 1 else 1):
        c = neu()
        print(f"Code {c}\tHash {code_hash(c)}\tErfasser-ID {erfasser_id(c)}")
