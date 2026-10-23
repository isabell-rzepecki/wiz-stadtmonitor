"""Einladungen → Sitzungen, Tagesordnungspunkte und Vorgänge mit Ortsbezug (Stufe A und Plan-Abgleich).

- Sitzung: eine Einladung (Bekanntmachungsnummer); Gremium aus dem Kopf.
- Vorgang: alle TOPs mit derselben Vorlagennummer, chronologisch; TOPs ohne Nummer bleiben einzelne Vorgänge
  (keine Verknüpfung über ähnliche Titel).
- Verfahrenspunkte (Eröffnung, Niederschrift, Verschiedenes, Gliederungspunkte wie „Anträge“) sind markiert und
  erscheinen nicht auf der Karte.
- Ortsbezug Stufe A: Ortsbeirat bzw. Stadtteilbeirat X → Ortsteil X (Ortsbezug des Gremiums).
- Ortsbezug Stufe B, Plan-Abgleich: „Bebauungsplan Nr. N Gemarkung G“ bzw. „N. Änderung des Flächennutzungsplanes“
  im Titel → Geltungsbereich der Stadt. Ergebnis ist die Plannummer; die Lage auf der Karte ist ein Punkt im
  Geltungsbereich. Stufe B für Straßen, Gemarkungen und Flurstücke: siehe verortung.py.
- Einreicher (einreicher.py): Antrag oder Anfrage einer Fraktion laut TOP-Titel, ohne Zählung je Fraktion.
- Räumliche Überschneidung mit Umweltebenen (umwelt.py): nur für Flurstückspunkte und Geltungsbereiche von Plänen,
  ohne inhaltliche Aussage; im Export nur Name und Ebene, keine Geometrie.
"""
import json
import re
from datetime import datetime, timezone

from . import audit, bauleitplanung, config, einreicher, fetch, geo, parse, umwelt, verortung

VERFAHREN = re.compile(
    r"^(Eröffnung|Begrüßung|Feststellung (der|des)|Genehmigung (der|des) (Tagesordnung|Niederschrift|Protokoll)|"
    r"(Verlesen und )?Genehmigung der Niederschrift|Verlesen|Niederschrift|Protokoll der letzten Sitzung|Mitteilungen|"
    r"Berichte? (des|der) (Bürgermeister|Ortsvorsteher|Vorsitzend|Stadtverordnetenvorsteher)|"
    r"Berichte? (aus|von) der (letzten )?Ortsvorstehersitzung|Bericht Ortsvorstehersitzung|Verschiedenes|Sonstiges|Aktuelles$|"
    r"Aussprache$|Beschlüsse soweit notwendig|Anfragen( an den Magistrat)?$|Aktuelle Stunde|"
    r"(Die )?(Gäste|Bürger\*?innen|Bürgerinnen und Bürger|Bürger)( / [\w-]+)? haben das Wort|"
    r"(Einwohner|Bürger)?[Ff]ragestunde|Verpflichtung|Verabschiedung|Wahl (der|des) (Vorsitz|Stellvertret|Schriftführ)|"
    r"Festlegung der Reihenfolge der Vertretung)", re.I)
# Gliederungspunkte: Überschriften, deren Inhalt in Unterpunkten steht (z. B. „19 Anträge“ mit 19.1, 19.2) oder die
# als Platzhalter ohne Unterpunkt stehen („Darlehensangelegenheiten“)
GLIEDERUNG = re.compile(r"^(Anträge|Anfragen|Grundstücksangelegenheiten|Über- und außerplanmäßige Ausgaben|"
                        r"Darlehensangelegenheiten|Personalangelegenheiten|Mitteilungen|Berichte)$", re.I)
BPLAN = re.compile(r"(?:(\d+)\.\s*Änderung\s+(?:und\s+Erweiterung\s+)?des\s+)?Bebauungsplan(?:es|s)?\s+Nr\.\s*(\d+)"
                   r"(?:\s*,?\s*Gemarkung\s+([A-ZÄÖÜ][\wäöüß-]+))?")
DETAIL = {"gremium_ortsbeirat": "A-gremium", "gremium_stadtteilbeirat": "A-gremium", "strasse": "B-strasse",
          "strasse+ortsteil": "B-strasse", "gemarkung": "B-gemarkung", "flurstueck": "B-flurstueck", "ortsteil_name": "B-ortsteil",
          "bebauungsplan": "B-bplan", "flaechennutzungsplan": "B-fplan"}
FPLAN = re.compile(r"(\d+)\.\s*Änderung\s+des\s+Flächennutzungsplan(?:es|s)?")


def ortsteil_zu(name=None, gemarkung=None, nr=None):
    for o in config.STADT["ortsteile"]:
        if name and name in (o["name"], *o.get("varianten", [])):
            return o
        if gemarkung and gemarkung == o.get("gemarkung"):
            return o
        if nr and nr == o.get("gemarkung_nr"):
            return o
    return None


def verfahrenspunkt(top):
    titel = top["titel"]
    if VERFAHREN.match(titel):
        return True
    return bool(GLIEDERUNG.match(titel))


def plan_verweise(titel, sitzung):
    """Plannummern im Titel: [{art, nr, aenderung, gemarkung_nr|None, evidence}]"""
    out = []
    for m in BPLAN.finditer(titel):
        o = ortsteil_zu(gemarkung=m.group(3)) if m.group(3) else None
        # ohne Gemarkung: nur eindeutig, wenn ein Ortsbeirat berät (Plannummern zählen je Gemarkung)
        if not o and sitzung["gremium_typ"] in ("ortsbeirat", "stadtteilbeirat"):
            o = ortsteil_zu(name=sitzung["ortsteil"])
        out.append({"art": "bplan", "nr": m.group(2), "aenderung": int(m.group(1) or 0),
                    "gemarkung_nr": o["gemarkung_nr"] if o else None, "evidence": m.group(0)})
    for m in FPLAN.finditer(titel):
        out.append({"art": "fplan", "aenderung": int(m.group(1)), "evidence": m.group(0)})
    return out


def plan_treffer(v, plaene):
    """(Plan, Treffer) – „eindeutig“, „Ursprungsplan“ (Änderung noch nicht im Datensatz) oder (None, Grund)."""
    if v["art"] == "fplan":
        p = next((p for p in plaene if p["art"] == "fplan" and p["aenderung"] == v["aenderung"]), None)
        return (p, "eindeutig") if p else (None, "nicht im Datensatz (im Verfahren)")
    if not v["gemarkung_nr"]:
        return None, "mehrdeutig (ohne Gemarkung)"
    cand = [p for p in plaene if p["art"] == "bplan" and p["gemarkung_nr"] == v["gemarkung_nr"] and p["nr"] == v["nr"]]
    exact = next((p for p in cand if p["aenderung"] == v["aenderung"]), None)
    if exact:
        return exact, "eindeutig"
    base = next((p for p in cand if p["aenderung"] == 0), None)
    if base:
        return base, "Ursprungsplan (Änderung nicht im Datensatz)"
    return None, "nicht im Datensatz (im Verfahren)"


def build():
    medien = json.loads(fetch.MEDIEN.read_text(encoding="utf-8"))
    plaene = bauleitplanung.plaene()
    flaechen = geo.Ortsteile() if config.ORTSBEZIRKE.exists() else None
    verz = verortung.Verzeichnis()
    umweltflaechen = umwelt.flaechen() if config.ORTSBEZIRKE.exists() else []
    # Beteiligungsverfahren der Bauleitplanung (pipeline/beteiligung.py), je Planverfahren
    bet_datei = config.EXPORT / "beteiligung.json"
    beteiligung = json.loads(bet_datei.read_text(encoding="utf-8"))["verfahren"] if bet_datei.exists() else []
    sitzungen, tops, fehler = {}, [], []
    for m in medien["medien"]:
        name = fetch.dateiname(m["source_url"])
        txt = fetch.TXT / (name.rsplit(".", 1)[0] + ".txt")
        try:
            e = parse.einladung(txt.read_text(encoding="utf-8"))
        except (parse.ParseFehler, FileNotFoundError, ValueError) as ex:
            fehler.append({"datei": name, "fehler": str(ex), "url": m["source_url"]})
            continue
        if not e["gremium_id"]:
            fehler.append({"datei": name, "fehler": f"Gremium unbekannt: {e['gremium']}", "url": m["source_url"]})
        sid = e["nr"]
        if sid in sitzungen:
            alt = sitzungen[sid]
            if (alt["gremium"], alt["date"]) == (e["gremium"], e["date"]):  # dieselbe Einladung erneut hochgeladen
                fehler.append({"datei": name, "fehler": f"Nr. {sid} doppelt hochgeladen, erste Datei übernommen", "url": m["source_url"]})
                continue
            # Nummer von der Stadt doppelt vergeben (z. B. 142/2026): beide Sitzungen, Kennung um das Gremium ergänzt
            sid = f"{sid}-{e['gremium_id'] or 'X'}"
            fehler.append({"datei": name, "fehler": f"Nr. {e['nr']} doppelt vergeben, übernommen als {sid}", "url": m["source_url"]})
        s = {k: e[k] for k in ("gremium", "gremium_id", "gremium_typ", "ortsteil", "date", "time", "termine", "ort", "oeffentlich")}
        s.update(id=sid, bekanntmachung=e["nr"], nr_abgeleitet=e["nr_abgeleitet"], pdf=m["source_url"], veroeffentlicht=m["date"][:10])
        sitzungen[sid] = s
        for t in e["tops"]:
            tops.append({**t, "sitzung": sid, "verfahrenspunkt": verfahrenspunkt(t)})

    gruppen = {}
    for t in tops:
        key = t["vorlage"] or f"{t['sitzung']}-TOP{t['top']}"
        gruppen.setdefault(key, []).append(t)
    vorgaenge, plan_audit, b_audit, u_audit, e_audit = [], [], [], [], []
    for key, ts in gruppen.items():
        ts.sort(key=lambda t: (sitzungen[t["sitzung"]]["date"], [int(x) for x in t["top"].split(".")]))
        process = []
        for t in ts:
            s = sitzungen[t["sitzung"]]
            process.append({"sitzung": s["id"], "bekanntmachung": s["bekanntmachung"], "gremium": s["gremium"],
                            "date": s["date"], "time": s["time"], "ort": s["ort"], "top": t["top"], "titel": t["titel"],
                            "oeffentlich": s["oeffentlich"], "result": None, "pdf": s["pdf"]})
        locations = []
        for t in ts:
            s = sitzungen[t["sitzung"]]
            if s["ortsteil"] and not any(l["ortsteil"] == s["ortsteil"] and l["stage"] == "A" for l in locations):
                locations.append({"level": "ortsteil", "name": s["ortsteil"], "ortsteil": s["ortsteil"], "stage": "A",
                                  "method": f"gremium_{s['gremium_typ']}", "confidence": "hoch", "evidence": s["gremium"], "source_pdf": s["pdf"]})
        verweise, verfahren_ids = [], set()
        for t in ts:
            for v in plan_verweise(t["titel"], sitzungen[t["sitzung"]]):
                verfahren_ids.add(f"fplan:{v['aenderung']}" if v["art"] == "fplan" else f"bplan:{v['gemarkung_nr'] or '?'}:{v['nr']}:{v['aenderung']}")
                p, treffer = plan_treffer(v, plaene)
                plan_audit.append({"vorgang": key, "sitzung": t["sitzung"], "top": t["top"], "art": v["art"], "nr": v.get("nr", ""),
                                   "aenderung": v["aenderung"], "gemarkung_nr": v.get("gemarkung_nr", ""), "treffer": treffer,
                                   "plan_key": p["key"] if p else "", "plan_titel": p["titel"] if p else "", "fundstelle": v["evidence"]})
                if p and p["key"] not in [x["key"] for x in verweise]:
                    verweise.append({"key": p["key"], "titel": p["titel"], "treffer": treffer, "evidence": v["evidence"]})
                    pt = p["geometry"].representative_point()
                    # Plan ohne Gemarkung in der Kennung (FNP-Blätter 0000): Ortsteil über die Lage in den Gemarkungen
                    o = ortsteil_zu(nr=p.get("gemarkung_nr")) or (flaechen.locate(pt.x, pt.y) if flaechen else None) or {"name": None}
                    locations.append({"level": "bebauungsplan", "name": p["titel"], "ortsteil": o["name"], "stage": "B",
                                      "method": "bebauungsplan" if p["art"] == "bplan" else "flaechennutzungsplan",
                                      "confidence": "hoch" if treffer == "eindeutig" else "mittel",
                                      "evidence": v["evidence"], "plan": p["key"], "lon": round(pt.x, 6), "lat": round(pt.y, 6),
                                      "source_pdf": sitzungen[t["sitzung"]]["pdf"]})
        # Stufe B aus den Titeln (nicht für Verfahrenspunkte)
        for t in ts:
            if t["verfahrenspunkt"]:
                continue
            s = sitzungen[t["sitzung"]]
            locs_b, aud = verortung.stufe_b(t["titel"], s, verz, s["pdf"])
            for l in locs_b:
                if not any(x["level"] == l["level"] and x["name"] == l["name"] for x in locations):
                    locations.append(l)
            b_audit += [{"vorgang": key, "sitzung": t["sitzung"], "top": t["top"], "titel": t["titel"], **a} for a in aud]
        # räumliche Überschneidung mit Umweltebenen: Flurstückspunkte und Geltungsbereiche, nicht Straßen oder Ortsteile
        overlaps = []
        for l in locations:
            if l["level"] == "flurstueck":
                treffer = umwelt.ueberschneidungen(umweltflaechen, punkt=(l["lon"], l["lat"]))
            elif l["level"] == "bebauungsplan":
                p = next((x for x in plaene if x["key"] == l["plan"]), None)
                treffer = umwelt.ueberschneidungen(umweltflaechen, flaeche=p["geometry"]) if p else []
            else:
                continue
            overlaps += [{**u, "ort": l["name"]} for u in treffer]
            u_audit += [{"vorgang": key, "ort": l["name"], "ort_ebene": l["level"], "ebene": u["ebene"], "flaeche": u.get("name", ""),
                         "zone": u.get("zone", "")} for u in treffer]
        first = ts[0]
        # Einreicher (Antrag/Anfrage einer Fraktion) aus dem ersten TOP, der das Muster enthält
        initiative = None
        for t in ts:
            r = einreicher.erkennen(t["titel"])
            if r:
                e_audit.append({"vorgang": key, "sitzung": t["sitzung"], "top": t["top"], "typ": r["typ"], "einreicher": ",".join(r["einreicher"]) or "nicht zugeordnet",
                                "datum": r["datum"], "gemeinsam": "ja" if r["gemeinsam"] else "nein", "fundstelle": r["fundstelle"]})
                initiative = initiative or r
        schritte = [{"nr": b["nr"], "veroeffentlicht": b["veroeffentlicht"], "pdf": b["pdf"], "stufen": b["stufen"]}
                    for b in beteiligung if b["plan"]["verfahren"] in verfahren_ids]
        vorgaenge.append({"reference": key, "vorlage": first["vorlage"], "name": first["titel"], "date": process[0]["date"],
                          "verfahrenspunkt": all(t["verfahrenspunkt"] for t in ts),
                          "bezuege": sorted({b for t in ts for b in t["bezuege"]}),
                          "process": process, "locations": locations, "plans": verweise,
                          **({"overlaps": overlaps} if overlaps else {}), **({"initiative": initiative} if initiative else {}),
                          **({"beteiligung": sorted(schritte, key=lambda b: b["veroeffentlicht"])} if schritte else {})})
    vorgaenge.sort(key=lambda v: (v["date"], v["reference"]), reverse=True)
    stand = datetime.now(timezone.utc).isoformat(timespec="seconds")
    daten = {"meta": {"generated_at": stand, "data_start": config.STADT["quelle"]["datenbeginn"],
                      "license": config.SOURCES["bekanntmachungen"]["license"],
                      "attribution": config.STADT["quelle"]["attribution"],
                      "source": config.SOURCES["bekanntmachungen"]["url"], "retrieved": medien["abruf"],
                      "sources": [{"name": "Amtliche Bekanntmachungen (Einladungen)", "license": config.SOURCES["bekanntmachungen"]["license"],
                                   "retrieved_at": medien["abruf"]},
                                  {"name": "Bauleitplanung (Plannummer und Lage im Geltungsbereich)", "license": config.STADT["bauleitplanung"]["nutzung"]},
                                  *[{"name": f"{g['titel']} (räumliche Überschneidung)", "license": g["attribution"]}
                                    for g in config.STADT["umwelt"]["gruppen"]]],
                      "parserfehler": len(fehler), "einladungen": len(medien["medien"])},
             "sitzungen": sorted(sitzungen.values(), key=lambda s: s["date"]), "vorgaenge": vorgaenge}
    config.EXPORT.mkdir(parents=True, exist_ok=True)
    config.VORGAENGE.write_text(json.dumps(daten, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    n_karte = bauleitplanung.karte(plaene)

    audit.tabelle("parserfehler.tsv", ["datei", "fehler", "url"], fehler)
    audit.tabelle("einreicher.tsv", ["vorgang", "sitzung", "top", "typ", "einreicher", "datum", "gemeinsam", "fundstelle"], e_audit)
    audit.tabelle("verortung_stufe_b.tsv", ["vorgang", "sitzung", "top", "titel", "methode_detail", "mehrdeutig", "treffer",
                                            "ortsteil", "konfidenz", "fundstelle"], b_audit)
    audit.tabelle("ueberschneidung_umwelt.tsv", ["vorgang", "ort", "ort_ebene", "ebene", "flaeche", "zone"], u_audit)
    audit.tabelle("verortung_bauleitplanung.tsv", ["vorgang", "sitzung", "top", "art", "nr", "aenderung", "gemarkung_nr",
                                                   "treffer", "plan_key", "plan_titel", "fundstelle"], plan_audit)
    mehrdeutig = {(a["vorgang"], a["sitzung"], a["top"]) for a in b_audit if a["mehrdeutig"] == "ja"}
    zeilen = []
    for v in vorgaenge:
        for s in v["process"]:
            ls = v["locations"]
            zeilen.append({"bekanntmachung": s["bekanntmachung"], "gremium": s["gremium"], "datum": s["date"], "top": s["top"],
                           "titel": s["titel"], "vorlage": v["vorlage"], "vorgang": v["reference"],
                           "verfahrenspunkt": "ja" if v["verfahrenspunkt"] else "nein",
                           "stufe": "/".join(sorted({l["stage"] for l in ls})) or "-",
                           "treffer": "; ".join(l["name"] for l in ls), "konfidenz": "; ".join(l["confidence"] for l in ls),
                           "methode": "; ".join(l["method"] for l in ls), "fundstelle": "; ".join(l["evidence"] for l in ls),
                           "methode_detail": "; ".join(DETAIL.get(l["method"], l["method"]) for l in ls),
                           "mehrdeutig": "ja" if (v["reference"], s["sitzung"], s["top"]) in mehrdeutig else "nein",
                           "quelle_pdf": s["pdf"], "pruefstatus": "ungeprüft"})
    audit.tabelle("tops.tsv", ["bekanntmachung", "gremium", "datum", "top", "titel", "vorlage", "vorgang", "verfahrenspunkt",
                               "stufe", "treffer", "konfidenz", "methode", "methode_detail", "mehrdeutig", "fundstelle",
                               "quelle_pdf", "pruefstatus"], zeilen)
    print(f"{len(sitzungen)} Sitzungen, {len(tops)} TOPs, {len(vorgaenge)} Vorgänge, {len(fehler)} Parserfehler, "
          f"{len(plan_audit)} Planverweise, {n_karte} Flächen der Bauleitplanung, "
          f"{sum(1 for v in vorgaenge if v.get('overlaps'))} Vorgänge mit räumlicher Überschneidung")
    return daten
