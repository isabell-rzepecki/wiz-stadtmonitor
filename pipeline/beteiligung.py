"""Beteiligungsverfahren der Bauleitplanung aus den amtlichen Bekanntmachungen.

Quellen: der Inhaltstyp „bekanntmachungen“ (Titel und PDF, ab 10/2025) und die PDF-Liste der Mediathek (ältere
Bekanntmachungen, erkannt am Dateinamen). Je Bekanntmachung werden Plan (Art, Nummer, Änderung, Gemarkung), Stufen
(Aufstellungsbeschluss, frühzeitige Beteiligung, Beteiligung am Entwurf, Satzungsbeschluss, Genehmigung) und Fristen
erkannt; Muster in config/stadt.json (beteiligung). Ansprechpersonen und E-Mail-Adressen werden nicht übernommen.
Die Zuordnung zum Plan folgt dem Plan-Abgleich der Vorgänge (build.plan_treffer).
"""
import hashlib
import json
import re
import subprocess
from datetime import date
from html import unescape

from . import audit, bauleitplanung, config, net
from .build import ortsteil_zu, plan_treffer

B = config.STADT["beteiligung"]
RAW = config.RAW / "beteiligung"
OUT = config.EXPORT / "beteiligung.json"
MONATE = {m: i + 1 for i, m in enumerate(["Januar", "Februar", "März", "April", "Mai", "Juni", "Juli", "August", "September",
                                          "Oktober", "November", "Dezember"])}
DATUM = r"(\d{1,2}\.\s*(?:\d{1,2}\.|[A-ZÄÖÜa-zäöü]+)\s*\d{4})"
FRIST = re.compile(rf"(?:vom|in der Zeit vom)\s+{DATUM}\s+bis\s+(?:einschließlich\s+|zum\s+)?{DATUM}")
NR = re.compile(r"Nr\.\s*(\d{1,3})\s*/\s*(\d{4})")
BPLAN = re.compile(r"(?:(\d+)\.\s*Änderung\s+(?:und\s+Erweiterung\s+)?des\s+)?Bebauungsplan(?:es|s)?\s+" + bauleitplanung.PLAN_NR)
FPLAN = re.compile(r"(\d+)\.\s*Änderung\s+des\s+Flächennutzungsplan(?:es|s)?")
GEMARKUNG = re.compile(r"Gemarkung\s+([A-ZÄÖÜ][\wäöüß-]+)")
NAME = re.compile(r"[„\"]([^“\"]{3,80})[“\"]")


def iso(text):
    t = re.sub(r"\s+", " ", text.strip())
    m = re.match(r"(\d{1,2})\.\s?(\d{1,2})\.\s?(\d{4})", t)
    if m:
        return f"{m.group(3)}-{int(m.group(2)):02d}-{int(m.group(1)):02d}"
    m = re.match(r"(\d{1,2})\.\s?([A-ZÄÖÜa-zäöü]+)\s?(\d{4})", t)
    if m and m.group(2) in MONATE:
        return f"{m.group(3)}-{MONATE[m.group(2)]:02d}-{int(m.group(1)):02d}"
    return None


def _seiten(url):
    """Alle Seiten der Liste oder None, wenn eine Seite fehlt (eine halbe Liste soll den letzten Stand nicht ersetzen)."""
    out, page = [], 1
    while True:
        try:
            body, h = net.get(url.format(page=page), tries=2)
            out += json.loads(body)
        except Exception as e:
            audit.abruf("wp_bekanntmachungen", url.format(page=page), getattr(e, "code", ""), "", "", "", str(e)[:200])
            return None
        if page >= int(h.get("X-WP-TotalPages") or h.get("x-wp-totalpages") or 1):
            break
        page += 1
    return out


def kandidaten():
    """[{pdf, titel, datum}] aus Bekanntmachungen (Titel) und Mediathek (Dateiname); None, wenn eine Liste fehlt."""
    out = {}
    bekanntmachungen, medien = _seiten(B["bekanntmachungen"]), _seiten(B["medien"])
    if bekanntmachungen is None or medien is None:
        return None
    for b in bekanntmachungen:
        meta = b.get("meta") or {}
        titel = unescape(b["title"]["rendered"])
        if re.search(B["titel_muster"], titel, re.I) and meta.get("dateilink_b"):
            out[meta["dateilink_b"]] = {"pdf": meta["dateilink_b"], "titel": titel, "datum": meta.get("veroeffentlichung") or b["date"][:10]}
    for m in medien:
        name = m["source_url"].rsplit("/", 1)[-1]
        if re.search(B["datei_muster"], name) and m["source_url"] not in out:
            out[m["source_url"]] = {"pdf": m["source_url"], "titel": None, "datum": m["date"][:10]}
    return list(out.values())


def fetch():
    RAW.mkdir(parents=True, exist_ok=True)
    liste = kandidaten()
    if liste is None:
        print("Bekanntmachungen nicht vollständig abrufbar; Liste der Verfahren bleibt auf dem letzten Stand")
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
            audit.abruf("wp_bekanntmachungen", k["pdf"], 200, len(body), hashlib.sha256(body).hexdigest(), "", "")
        except Exception as e:
            audit.abruf("wp_bekanntmachungen", k["pdf"], getattr(e, "code", ""), "", "", "", str(e)[:200])
    (RAW / "kandidaten.json").write_text(json.dumps(liste, ensure_ascii=False, indent=1), encoding="utf-8")


verfahren_id = bauleitplanung.verfahren_id


def lesen(text):
    """Plan, Verfahren, Stufen mit Fristen aus dem Text einer Bekanntmachung."""
    t = re.sub(r"[ \t]+", " ", text)
    flach = re.sub(r"\s+", " ", t)
    nr = NR.search(flach[:300])
    kopf = flach[:600]
    plan = None
    if m := BPLAN.search(kopf):
        plan = {"art": "bplan", "nr": bauleitplanung.plan_nr(m.group(2)), "aenderung": int(m.group(1) or 0)}
    elif m := FPLAN.search(kopf):
        plan = {"art": "fplan", "aenderung": int(m.group(1))}
    if plan:
        g = GEMARKUNG.search(kopf)
        n = NAME.search(kopf)
        plan.update(gemarkung=g.group(1) if g else None, name=n.group(1).strip() if n else None)
    stufen = []
    for s in B["stufen"]:
        m = re.search(s["muster"], flach, re.I)
        if not m:
            continue
        e = {"stufe": s["id"], "titel": s["titel"]}
        if s.get("frist"):
            f = FRIST.search(flach, m.start(), m.start() + 1500)
            if f:
                e.update(von=iso(f.group(1)), bis=iso(f.group(2)))
        if s["id"] == "aufstellung":
            d = re.search(r"Stadtverordnetenversammlung[^.]{0,120}?am\s+(\d{1,2}\.\d{1,2}\.\d{4})", flach)
            if d:
                e["beschluss"] = iso(d.group(1))
        stufen.append(e)
    # Satzung/Genehmigung nur, wenn keine Beteiligungsstufe den Text bestimmt (sonst Erwähnung als Ausblick)
    if any(s["stufe"] in ("frueh_oeff", "veroeff") for s in stufen):
        stufen = [s for s in stufen if s["stufe"] not in ("satzung", "genehmigung")]
    return {"nr": f"{int(nr.group(1)):03d}/{nr.group(2)}" if nr else None, "plan": plan,
            "verfahren": next((v["titel"] for v in B["verfahren"] if re.search(v["muster"], kopf)), None), "stufen": stufen}


def build():
    k = RAW / "kandidaten.json"
    liste = json.loads(k.read_text(encoding="utf-8")) if k.exists() else []
    plaene = bauleitplanung.plaene()
    out, zeilen, gesehen = [], [], set()
    for c in liste:
        p = RAW / c["pdf"].rsplit("/", 1)[-1]
        if not p.exists():
            continue
        text = subprocess.run(["pdftotext", str(p), "-"], capture_output=True, text=True).stdout
        r = lesen(text)
        if r["nr"] and r["nr"] in gesehen:  # dieselbe Bekanntmachung als zweite Datei
            zeilen.append({"pdf": c["pdf"], "nr": r["nr"], "ergebnis": "doppelt, übersprungen"})
            continue
        gesehen.add(r["nr"])
        if not r["plan"] or not r["stufen"]:
            zeilen.append({"pdf": c["pdf"], "nr": r["nr"] or "", "ergebnis": "kein Plan oder keine Stufe erkannt"})
            continue
        o = ortsteil_zu(gemarkung=r["plan"]["gemarkung"]) if r["plan"]["gemarkung"] else None
        v = {**r["plan"], "gemarkung_nr": o["gemarkung_nr"] if o else None}
        plan, treffer = plan_treffer(v, plaene)
        r["plan"].update(ortsteil=o["name"] if o else None, key=plan["key"] if plan else None, treffer=treffer,
                         verfahren=verfahren_id(v["art"], v["aenderung"], v.get("nr"), v["gemarkung_nr"]))
        r.update(pdf=c["pdf"], veroeffentlicht=c["datum"])
        out.append(r)
        zeilen.append({"pdf": c["pdf"], "nr": r["nr"] or "", "ergebnis": f"{r['plan']['art']} {r['plan'].get('nr', '')} Änd. {r['plan']['aenderung']} "
                       f"{r['plan']['gemarkung'] or ''}; {', '.join(s['stufe'] for s in r['stufen'])}; {treffer}"})
    out.sort(key=lambda r: r["veroeffentlicht"], reverse=True)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"generated_at": date.today().isoformat(), "seite": B["seite"], "verfahren": out},
                              ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    audit.tabelle("beteiligung.tsv", ["pdf", "nr", "ergebnis"], zeilen)
    print(f"Beteiligung: {len(out)} Bekanntmachungen zur Bauleitplanung, {len(liste) - len(out)} ohne Plan oder Stufe")
    return out
