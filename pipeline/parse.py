"""Einladungen lesen: Kopf (Nr., Gremium, Termine, Ort, Öffentlichkeit) und Tagesordnung (TOP, Titel, Vorlage).

Eingabe ist die Ausgabe von `pdftotext -layout`. Das Gremium kommt aus dem Kopf der Einladung, nicht aus dem
Dateinamen (dort gibt es abweichende Muster und Fehlbezeichnungen, siehe phase0/BERICHT.md).
"""
import re
from datetime import date

from . import config

VORLAGE = re.compile(r"\b([A-ZÄÖÜ][A-Za-zÄÖÜ]{1,5}/\d{1,4}/\d{4})\b")
TOP = re.compile(r"^\s{0,6}(\d{1,2}(?:\.\d{1,2})*)\.?(?:\s{2,}|\t)(\S.*)$")
DATUM = re.compile(r"\b(\d{1,2})\.(\d{1,2})\.(\d{4})\b")
ENDE = re.compile(rf"^\s*(gez\.|{re.escape(config.STADT['stadt']['name'])}, (den )?\d)", re.I)
SEITE = re.compile(r"^\s*(-\s*\d+\s*-|Seite \d+( von \d+)?)\s*$")
# Namen natürlicher Personen in TOP-Titeln (Gäste, Vortragende, einzelne Stadtverordnete) werden nicht übernommen:
# Anrede oder Funktion, gefolgt von ein bis drei Namensteilen („Frau Muster“, „Herrn Max Muster“)
ROLLE = (r"Herrn?|Frau|Familie|Ortsvorsteher(?:in)?|Bürgermeister(?:in)?|Stadtverordnetenvorsteher(?:in)?|"
         r"Stadtverordnete[nr]?|Stadträtin|Stadtrat|Referent(?:in)?|eingeladen:")
_NAME = r"(?:Dr\.\s+)?(?:[A-ZÄÖÜ]\.\s*)?[A-ZÄÖÜ][a-zäöüß]+(?:-[A-ZÄÖÜ][a-zäöüß]+)?"
_KEIN = rf"(?:{ROLLE}|Vorsitzende|Magistrat|Holle)\b"  # Funktionen statt Namen; „Frau Holle“ ist eine Sagengestalt
PERSON = re.compile(rf"\b({ROLLE})\s+(?!{_KEIN}){_NAME}(?:\s+(?!{_KEIN}){_NAME}){{0,2}}"
                    rf"(?:\s+und\s+{_NAME}(?:\s+{_NAME}){{0,2}})?")
# mehrere Personen ohne Anrede in Klammern: „(Vorname Name/Vorname Name)“
_VOLL = r"[A-ZÄÖÜ][a-zäöüß]+\s[A-ZÄÖÜ][a-zäöüß]+"
PERSONEN = re.compile(rf"\({_VOLL}(?:\s*/\s*{_VOLL})+\)")
NAME_ERSATZ = "[Name entfernt]"
# Hinweise auf eine Privatwohnung im Sitzungsort
PRIVAT = re.compile(r"\b(bei|Familie|Fam\.|Herrn?|Frau|Wohnung|privat\w*)\b", re.I)


def ohne_namen(titel):
    """Personennamen im Titel durch einen Platzhalter ersetzen; Anrede oder Funktion bleibt stehen."""
    return PERSONEN.sub(f"({NAME_ERSATZ})", PERSON.sub(lambda m: f"{m.group(1)} {NAME_ERSATZ}", titel))


class ParseFehler(ValueError):
    pass


def kopf_text(text):
    i = text.find("Tagesordnung")
    return re.sub(r"\s+", " ", text[: i if i >= 0 else 1500]).strip()


def gremium_name(roh):
    """Name ohne Zusätze wie „– Konstituierung –“; Schreibfehler „Stadtentwicklung,Tourismus“ bereinigt."""
    name = re.sub(r"\s*[–-]\s*(Konstituierung|Wahl der Gremien)\s*[–-]?\s*$", "", roh).strip()
    name = re.sub(r",(?=\S)", ", ", name)
    return name


def nominativ(phrase):
    """„des Ortsbeirates Neuseesen“ → „Ortsbeirat Neuseesen“, „der Stadtverordnetenversammlung“ → …"""
    p = re.sub(r"^(des|der)\s+", "", phrase)
    return re.sub(r"(rat|ausschuss|Ausschuss)es\b", r"\1", p)


def gremium(name):
    """(id, typ, ortsteil) zu einem Gremiennamen; ids aus config/stadt.json, Ortsbeiräte als OB-<slug>."""
    for g in config.STADT["gremien"]:
        if name == g["name"] or name in g.get("namen", []):
            return g["id"], g["typ"], None
    m = re.match(r"^(Ortsbeirat|Stadtteilbeirat) (.+)$", name)
    if m:
        o = next((o for o in config.STADT["ortsteile"] if m.group(2) in [o["name"], *o.get("varianten", [])]), None)
        if o:
            prefix = "OB" if m.group(1) == "Ortsbeirat" else "STB"
            return f"{prefix}-{o['slug']}", m.group(1).lower(), o["name"]
    return None, None, None


def iso(d, m, y):
    return date(int(y), int(m), int(d)).isoformat()


def kopf(text, jahr=None):
    """Kopf der Einladung; jahr = Jahr der Veröffentlichung, falls die Nummer ohne Jahr steht (sonst Sitzungsjahr)."""
    h = kopf_text(text)
    m = re.search(r"Nr\.\s*(\d+)(?:\s*/\s*(\d{4}))?", h)
    if not m:
        raise ParseFehler("Bekanntmachungsnummer fehlt")
    nr_nummer, nr_jahr = int(m.group(1)), m.group(2)
    m = re.search(r"Sitzung\s+(de[sr]\s.*?)\s+am\b", h)
    if not m:
        raise ParseFehler("Gremium fehlt")
    roh = m.group(1)
    name = gremium_name(nominativ(roh))
    gid, typ, ortsteil = gremium(name)
    kanon = next((g["name"] for g in config.STADT["gremien"] if g["id"] == gid), None)
    if kanon:  # Schreibvarianten auf den Namen laut Konfiguration
        name = kanon
    rest = h[m.end():]
    termine = [(iso(*DATUM.search(d).groups()), t.replace(".", ":"))
               for d, t in re.findall(r"(\d{1,2}\.\d{1,2}\.\d{4}),?\s*um\s+(\d{1,2}[:.]\d{2})", rest)]
    if not termine:
        d = DATUM.search(rest)
        if not d:
            raise ParseFehler("Datum fehlt")
        termine = [(iso(*d.groups()), None)]
    # Ort: nach der letzten Uhrzeit bis zum Ende des Kopfs; doppelte Präpositionen („im in der …“) entfernt
    m = re.search(r"Uhr,?\s+((?:(?:im|in der|in|auf dem|bei)\s+)+)(.+?)\.?\s*(?:gez\..*)?$", rest)
    ort = m.group(2).strip() if m else None
    if ort and " Uhr " in f" {ort} ":
        ort = None
    # Sitzung bei einer Privatperson: Anschrift nicht übernehmen (keine Wohnadressen natürlicher Personen)
    if m and ("bei" in m.group(1).split() or PRIVAT.search(m.group(2))):
        ort = "Privatanschrift (nicht übernommen, siehe Einladung)"
    nr_abgeleitet = nr_jahr is None
    nr = f"{nr_nummer:03d}/{nr_jahr or jahr or termine[0][0][:4]}"
    oeffentlich = not re.search(r"nicht\s*-?\s*öffentlich", h[:h.find("Sitzung") + 10], re.I)
    return {"nr": nr, "nr_abgeleitet": nr_abgeleitet, "gremium": name, "gremium_roh": roh, "gremium_id": gid, "gremium_typ": typ, "ortsteil": ortsteil,
            "date": termine[0][0], "time": termine[0][1], "termine": [{"date": d, "time": t} for d, t in termine],
            "ort": ort, "oeffentlich": oeffentlich}


def tagesordnung(text):
    """[{top, titel, vorlage, bezuege}] in der Reihenfolge der Einladung."""
    i = text.find("Tagesordnung")
    if i < 0:
        return []
    tops, cur, warte_vorlage = [], None, False
    for line in text[i:].split("\n")[1:]:
        if ENDE.match(line):
            break
        if not line.strip() or SEITE.match(line):
            continue
        if warte_vorlage and cur:
            v = VORLAGE.search(line)
            if v:
                cur["vorlage"] = v.group(1)
            warte_vorlage = False
            continue
        v = re.match(r"^\s*Vorlage:?\s*(\S*)\s*$", line)
        if v and cur:
            vm = VORLAGE.search(v.group(1))
            if vm:
                cur["vorlage"] = vm.group(1)
            else:
                warte_vorlage = True
            continue
        m = TOP.match(line)
        if m:
            cur = {"top": m.group(1), "titel": m.group(2).strip(), "vorlage": None}
            tops.append(cur)
            continue
        if cur:
            cur["titel"] += " " + line.strip()
    for t in tops:
        t["titel"] = ohne_namen(re.sub(r"\s+", " ", t["titel"]).strip())
        t["bezuege"] = [v for v in VORLAGE.findall(t["titel"]) if v != t["vorlage"]]
    return tops


def einladung(text, jahr=None):
    k = kopf(text, jahr)
    k["tops"] = tagesordnung(text)
    return k
