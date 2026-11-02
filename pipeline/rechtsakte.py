"""Bekanntgemachte Rechtsakte als Ergebnis von Vorgängen: Satzungen, Gebührenordnungen, Haushalt, Jahresabschluss.

Die Stadt veröffentlicht keine Niederschriften. Was die Stadtverordnetenversammlung als Satzung oder Haushalt
beschließt, muss sie aber öffentlich bekannt machen; die Bekanntmachung ist damit ein indirekter Beleg des Beschlusses.
Quellen wie in beteiligung.py: Inhaltstyp „bekanntmachungen“ (Titel) und Mediathek (Dateiname); Muster in
config/stadt.json (rechtsakte). Bebauungs- und Flächennutzungspläne liest beteiligung.py; deren Stufen
„Satzungsbeschluss“ und „Genehmigung“ werden hier mit übernommen.

Gelesen werden Nummer, Gegenstand, Art (Satzung, Änderung mit Nummer, Aufhebung, Haushalt, Nachtrag,
Jahresabschluss, Hinweis auf eine Bereitstellung), Haushaltsjahr, Datum des Beschlusses und des Inkrafttretens.
Namen (Unterschriften) werden nicht übernommen; der Gegenstand läuft durch den Namensfilter.

Zuordnung (zuordnen): Tagesordnungspunkte am Tag des Beschlusses, sonst bis 400 Tage vor der Bekanntmachung;
Übereinstimmung der Schlagwörter des Gegenstands, Änderungsnummer, Aufhebung und Haushaltsjahr.
- sicher: Beschlussdatum aus dem Text, ein einziger bester Tagesordnungspunkt an diesem Tag
- möglicherweise: ohne Beschlussdatum, aber ein einziger bester Treffer
- geprüft: von Hand bestätigt (config/rechtsakte_geprueft.tsv)
Alles andere bleibt ohne Zuordnung und steht in audit/rechtsakte.tsv (Prüfliste).
"""
import csv
import hashlib
import json
import re
import subprocess
from datetime import date, timedelta
from html import unescape

from . import audit, beteiligung, config, net, parse

R = config.STADT["rechtsakte"]
RAW = config.RAW / "rechtsakte"
OUT = config.EXPORT / "rechtsakte.json"
GEPRUEFT = config.ROOT / "config" / "rechtsakte_geprueft.tsv"
NR = re.compile(r"Nr\.\s*(\d{1,3})\s*/\s*(\d{4})")
DATUM = beteiligung.DATUM
ORDINAL = {"erste": 1, "zweite": 2, "dritte": 3, "vierte": 4, "fünfte": 5, "sechste": 6, "siebte": 7, "achte": 8,
           "neunte": 9, "zehnte": 10}
AENDERUNG = re.compile(r"\b(?:(\d{1,2})\.|(" + "|".join(ORDINAL) + r")[nrs]?)\s*Änderung", re.I)
JAHR = re.compile(r"(?:Haushaltsjahr|Wirtschaftsjahr|Nachtragshaushalts?|Jahresabschluss(?:es)?(?:\s+(?:zum\s+)?31\.\s?12\.)?)\s*(20\d\d)")
KOPF_ENDE = re.compile(r"\s(?:Aufgrund|Auf Grund|Die vorstehende|Die Stadtverordnetenversammlung|Die Stadt [A-ZÄÖÜ][\w-]+ weist|"
                       r"Gemäß|Aus Gründen|Präambel|§\s*1\b)")
BESCHLUSS = re.compile(rf"Stadtverordnetenversammlung[^.]{{0,160}}?\bam\s+{DATUM}")
INKRAFT = re.compile(rf"tritt\s+(?:am|zum|mit Wirkung vom)\s+{DATUM}\s+in\s+Kraft")


def _norm(s):
    s = s.lower()
    for a, b in (("ä", "ae"), ("ö", "oe"), ("ü", "ue"), ("ß", "ss")):
        s = s.replace(a, b)
    return s


STOPP = {_norm(w) for w in R["stoppwoerter"]}


def _stamm(w):
    """grobe Grundform: Baubetriebshofs, Baubetriebshofes → baubetriebshof"""
    return re.sub(r"(?:es|en|s|e|n)$", "", w) if len(w) > 6 else w


def schlagwoerter(text):
    return {_stamm(w) for w in re.findall(r"[a-z]{5,}", _norm(text)) if w not in STOPP}


def aenderung_nr(text):
    m = AENDERUNG.search(text)
    if not m:
        return None
    return int(m.group(1)) if m.group(1) else ORDINAL[m.group(2).lower()]


def merkmale(text):
    """Merkmale eines Gegenstands oder TOP-Titels für den Abgleich."""
    j = JAHR.search(text)
    return {"woerter": schlagwoerter(text), "aenderung": aenderung_nr(text), "aufhebung": bool(re.search(r"Aufhebung", text, re.I)),
            "nachtrag": bool(re.search(r"Nachtrag", text, re.I)), "jahr": j.group(1) if j else None}


def art(gegenstand, hinweis):
    if hinweis:
        return "hinweis"
    if re.search(r"Nachtrag", gegenstand, re.I) and re.search(r"Haushalt", gegenstand, re.I):
        return "nachtragshaushalt"
    if re.search(r"Haushaltssatzung", gegenstand, re.I):
        return "haushalt"
    if re.search(r"Jahresabschluss", gegenstand, re.I):
        return "jahresabschluss"
    if re.search(r"Aufhebung", gegenstand, re.I):
        return "aufhebung"
    if aenderung_nr(gegenstand) or re.search(r"Änderungssatzung", gegenstand, re.I):
        return "aenderung"
    return "satzung"


def _kurz(s, n=220):
    s = re.sub(r"\s+", " ", s).strip(" ,;:-–")
    return s if len(s) <= n else s[:n].rsplit(" ", 1)[0] + " …"


def lesen(text):
    """Nummer, Gegenstand, Art, Merkmale und Daten aus dem Text einer Bekanntmachung."""
    flach = re.sub(r"\s+", " ", text)
    nr = NR.search(flach[:400])
    rest = flach[nr.end():] if nr else flach
    kopf = KOPF_ENDE.split(rest[:700], maxsplit=1)[0]
    kopf = re.sub(r"\bOR\s*\d+(?:\.\d+)?\b|^\s*\d+\.\d+\s|KORREKTUR DER VERÖFFENTLICHUNG VOM [\d.]+|^\s*Bekanntmachung (?:der|des)\s",
                  " ", kopf).strip()
    hinweis = bool(re.search(r"weist nachrichtlich darauf hin", flach))
    if hinweis:
        m = re.search(r"(?:\d{4}|dem \d{1,2}\.\d{1,2}\.\d{4})\s+(?:die|der|das)\s+(.{5,240}?)\s+öffentlich bekannt gemacht", flach)
        gegenstand = m.group(1) if m else kopf
    elif len(kopf) >= 12:
        gegenstand = kopf
    else:
        m = re.search(r"folgende\s+(.{5,240}?)\s+beschlossen", flach)
        gegenstand = m.group(1) if m else kopf
    gegenstand = _kurz(parse.ohne_namen(gegenstand))
    b = BESCHLUSS.search(flach)
    k = INKRAFT.search(flach)
    m = merkmale(flach[:1500] if not gegenstand else gegenstand)
    if not m["jahr"]:
        j = JAHR.search(flach[:1500])
        m["jahr"] = j.group(1) if j else None
    return {"nr": f"{int(nr.group(1)):03d}/{nr.group(2)}" if nr else None, "art": art(gegenstand, hinweis), "gegenstand": gegenstand,
            "aenderung": m["aenderung"], "aufhebung": m["aufhebung"], "jahr": m["jahr"],
            "beschluss": beteiligung.iso(b.group(1)) if b else None, "inkraft": beteiligung.iso(k.group(1)) if k else None}


def kandidaten():
    """[{pdf, titel, datum}] aus Bekanntmachungen (Titel) und Mediathek (Dateiname); None, wenn eine Liste fehlt."""
    out = {}
    bekanntmachungen = beteiligung._seiten(config.STADT["beteiligung"]["bekanntmachungen"])
    medien = beteiligung._seiten(config.STADT["beteiligung"]["medien"])
    if bekanntmachungen is None or medien is None:
        return None
    for b in bekanntmachungen:
        meta = b.get("meta") or {}
        titel = unescape(b["title"]["rendered"])
        if re.search(R["titel_muster"], titel, re.I) and not re.search(R["ausschliessen"], titel) and meta.get("dateilink_b"):
            out[meta["dateilink_b"]] = {"pdf": meta["dateilink_b"], "titel": titel, "datum": meta.get("veroeffentlichung") or b["date"][:10]}
    for m in medien:
        name = m["source_url"].rsplit("/", 1)[-1]
        if re.search(R["datei_muster"], name) and not re.search(R["ausschliessen"], name) and m["source_url"] not in out:
            out[m["source_url"]] = {"pdf": m["source_url"], "titel": None, "datum": m["date"][:10]}
    return list(out.values())


def fetch():
    RAW.mkdir(parents=True, exist_ok=True)
    liste = kandidaten()
    if liste is None:
        print("Bekanntmachungen nicht vollständig abrufbar; Rechtsakte bleiben auf dem letzten Stand")
        return
    for k in liste:
        ziel = RAW / k["pdf"].rsplit("/", 1)[-1]
        if ziel.exists():
            continue
        try:
            body, _ = net.get(k["pdf"], tries=2)
            grund = net.pruefen(ziel, body)
            if grund:
                raise ValueError(grund)
            net.speichern(ziel, body)
            audit.abruf("wp_rechtsakte", k["pdf"], 200, len(body), hashlib.sha256(body).hexdigest(), "", "")
        except Exception as e:
            audit.abruf("wp_rechtsakte", k["pdf"], getattr(e, "code", ""), "", "", "", str(e)[:200])
    (RAW / "kandidaten.json").write_text(json.dumps(liste, ensure_ascii=False, indent=1), encoding="utf-8")


def _bauleitplaene():
    """Satzungsbeschluss und Genehmigung aus beteiligung.json als Rechtsakte (Zuordnung über die Bekanntmachungsnummer)."""
    p = config.EXPORT / "beteiligung.json"
    out = []
    for b in json.loads(p.read_text(encoding="utf-8"))["verfahren"] if p.exists() else []:
        st = next((s for s in b["stufen"] if s["stufe"] in ("satzung", "genehmigung")), None)
        if not st:
            continue
        pl = b["plan"]
        name = (f"{pl['aenderung']}. Änderung des Flächennutzungsplans" if pl["art"] == "fplan"
                else f"{str(pl['aenderung']) + '. Änderung des ' if pl['aenderung'] else ''}Bebauungsplan{'s' if pl['aenderung'] else ''} Nr. {pl['nr']}")
        name += f" „{pl['name']}“" if pl.get("name") else ""
        name += f", Gemarkung {pl['gemarkung']}" if pl.get("gemarkung") else ""
        out.append({"nr": b["nr"], "art": "bauleitplan", "gegenstand": _kurz(parse.ohne_namen(name)), "stufe": st["titel"],
                    "aenderung": pl["aenderung"] or None, "aufhebung": False, "jahr": None, "beschluss": st.get("beschluss"),
                    "inkraft": b["veroeffentlicht"], "pdf": b["pdf"], "veroeffentlicht": b["veroeffentlicht"]})
    return out


def build():
    k = RAW / "kandidaten.json"
    liste = json.loads(k.read_text(encoding="utf-8")) if k.exists() else []
    out, zeilen, gesehen = [], [], set()
    for c in sorted(liste, key=lambda c: c["datum"]):
        p = RAW / c["pdf"].rsplit("/", 1)[-1]
        if not p.exists():
            continue
        r = lesen(subprocess.run(["pdftotext", str(p), "-"], capture_output=True, text=True).stdout)
        if not r["nr"] or r["nr"] in gesehen:  # dieselbe Bekanntmachung als zweite Datei
            zeilen.append({"nr": r["nr"] or "", "pdf": c["pdf"], "ergebnis": "doppelt oder ohne Nummer, übersprungen"})
            continue
        gesehen.add(r["nr"])
        out.append({**r, "pdf": c["pdf"], "veroeffentlicht": c["datum"]})
    out += [b for b in _bauleitplaene() if b["nr"] not in gesehen]
    out.sort(key=lambda r: r["veroeffentlicht"], reverse=True)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"generated_at": date.today().isoformat(), "rechtsakte": out}, ensure_ascii=False, separators=(",", ":")),
                   encoding="utf-8")
    audit.tabelle("rechtsakte_gelesen.tsv", ["nr", "pdf", "ergebnis"],
                  zeilen + [{"nr": r["nr"], "pdf": r["pdf"], "ergebnis": f"{r['art']}; {r['gegenstand']}; Beschluss {r['beschluss'] or '-'}"} for r in out])
    print(f"Rechtsakte: {len(out)} Bekanntmachungen (Satzungen, Haushalt, Pläne)")
    return out


# --- Zuordnung zu den Vorgängen (aus build.build aufgerufen) --------------------------------------------------------

def geprueft_laden(datei=None):
    """{nr: vorgang oder "" (keiner), …} aus config/rechtsakte_geprueft.tsv"""
    datei = datei or GEPRUEFT
    if not datei.exists():
        return {}
    with datei.open(encoding="utf-8", newline="") as f:
        return {z["nr"]: {"vorgang": z["vorgang"].strip(), "geprueft_am": z["geprueft_am"]}
                for z in csv.DictReader((x for x in f if not x.startswith("#")), delimiter="\t")}


JAHRESAKTE = ("haushalt", "nachtragshaushalt", "jahresabschluss")


def _passt(ra, m):
    """Ausschlüsse: Änderungsnummer, Aufhebung, Nachtrag und Jahr müssen zusammenpassen."""
    if ra["aenderung"] and m["aenderung"] and ra["aenderung"] != m["aenderung"]:
        return False
    if ra["art"] != "bauleitplan" and ra["aufhebung"] != m["aufhebung"]:
        return False
    if ra["art"] in JAHRESAKTE:
        return bool(m["jahr"]) and m["jahr"] == ra["jahr"] and m["nachtrag"] == (ra["art"] == "nachtragshaushalt")
    return True


def kandidaten_fuer(ra, vorgaenge):
    """[(punkte, vorgang, station)] in absteigender Folge; Einbringungen und Berichte zählen nicht als Beschluss."""
    mr = merkmale(ra["gegenstand"]) | {"aenderung": ra["aenderung"], "aufhebung": ra["aufhebung"]}
    bis = ra["veroeffentlicht"]
    von = ra["beschluss"] or (date.fromisoformat(bis) - timedelta(days=R["tage_vorher"])).isoformat()
    # beschließt die Stadtverordnetenversammlung; Ortsbeiräte geben nur Stellungnahmen ab. Eine Geschäftsordnung gibt
    # sich ein Beirat selbst.
    gremium = next((g for g in R["eigene_gremien"] if g in ra["gegenstand"]), "Stadtverordnetenversammlung")
    out = []
    for v in vorgaenge:
        if v["verfahrenspunkt"]:
            continue
        if ra["art"] == "bauleitplan" and ra["nr"] not in {b["nr"] for b in v.get("beteiligung", [])}:
            continue
        for s in v["process"]:
            if not s["date"] or not (von <= s["date"] <= bis) or (ra["beschluss"] and s["date"] != ra["beschluss"]):
                continue
            if gremium not in s["gremium"]:
                continue
            if re.match(r"(Einbringung|Bericht|Bekanntgabe|Kenntnisgabe|Stellungnahme)", s["titel"]) and "Beschlussfassung" not in s["titel"]:
                continue
            if ra["art"] in JAHRESAKTE and "Beschlussfassung" not in s["titel"]:
                continue
            m = merkmale(s["titel"])
            if not _passt(ra, m):
                continue
            # Plan über die Bekanntmachungsnummer, Haushalt und Abschluss über das Jahr schon belegt
            punkte = len(mr["woerter"] & m["woerter"]) + (2 if ra["art"] == "bauleitplan" or ra["art"] in JAHRESAKTE else 0)
            # mit Beschlussdatum genügt ein gemeinsames Schlagwort (etwa „Hauptsatzung“), sonst zwei
            if punkte >= (1 if ra["beschluss"] else R["mindestpunkte"]):
                out.append((punkte, v, s))
    # beste Punkte zuerst, bei Gleichstand die letzte Beratung (Beschluss der Stadtverordnetenversammlung)
    out.sort(key=lambda x: x[2]["date"], reverse=True)
    out.sort(key=lambda x: -x[0])
    return out


def grund(ra, beste, tage):
    """Warum eine Bekanntmachung ohne Vorgang bleibt (Prüfliste)."""
    if ra["beschluss"] and ra["beschluss"] < config.STADT["quelle"]["datenbeginn"]:
        return "Beschluss vor Datenbeginn"
    if ra["beschluss"] and ra["beschluss"] not in tage:
        return f"keine Einladung zum Sitzungstag {ra['beschluss']} in den Quellen"
    if not beste:
        return "kein passender Tagesordnungspunkt"
    return "mehrere gleich gute Kandidaten"


def zuordnen(vorgaenge, rechtsakte, geprueft=None):
    """Ergebnis-Stationen an die Vorgänge hängen (v["ergebnisse"]); Zeilen der Prüfliste zurück."""
    geprueft = geprueft if geprueft is not None else geprueft_laden()
    nach_ref = {v["reference"]: v for v in vorgaenge}
    tage = {s["date"] for v in vorgaenge for s in v["process"]}
    zeilen = []
    for ra in rechtsakte:
        ks = kandidaten_fuer(ra, vorgaenge)
        # bester Treffer je Vorgang; eindeutig, wenn kein zweiter Vorgang gleich viele Punkte hat
        je_vorgang = {}
        for p, v, s in ks:
            je_vorgang.setdefault(v["reference"], (p, v, s))
        beste = sorted(je_vorgang.values(), key=lambda x: -x[0])
        eindeutig = bool(beste) and (len(beste) == 1 or beste[0][0] > beste[1][0])
        ziel, sicherheit, station = None, None, None
        g = geprueft.get(ra["nr"])
        if g is not None:
            if g["vorgang"] in nach_ref:
                ziel, sicherheit = nach_ref[g["vorgang"]], "geprüft"
                station = next((s for p, v, s in ks if v is ziel), None)
        elif eindeutig:
            _, ziel, station = beste[0]
            # Haushalt und Abschluss: Art und Jahr eindeutig wie eine Nummer
            sicherheit = "sicher" if ra["beschluss"] or ra["art"] in JAHRESAKTE else "möglicherweise"
        if ziel is not None:
            e = {k: ra[k] for k in ("nr", "art", "gegenstand", "veroeffentlicht", "pdf")}
            e.update(sicherheit=sicherheit, **{k: ra[k] for k in ("beschluss", "inkraft", "stufe") if ra.get(k)})
            if g is not None and g.get("geprueft_am"):
                e["geprueft"] = g["geprueft_am"]
            if station:
                e["station"] = {"sitzung": station["sitzung"], "top": station["top"]}
            ziel.setdefault("ergebnisse", []).append(e)
        zeilen.append({"nr": ra["nr"], "art": ra["art"], "gegenstand": ra["gegenstand"], "veroeffentlicht": ra["veroeffentlicht"],
                       "beschluss": ra["beschluss"] or "", "vorgang": ziel["reference"] if ziel else "", "sicherheit": sicherheit or "keine",
                       "grund": "" if ziel else grund(ra, beste, tage),
                       "kandidaten": "; ".join(f"{v['reference']} ({p}) {s['titel'][:80]}" for p, v, s in beste[:3]),
                       "pdf": ra["pdf"]})
    for v in vorgaenge:
        if v.get("ergebnisse"):
            v["ergebnisse"].sort(key=lambda e: e["veroeffentlicht"])
    return zeilen
