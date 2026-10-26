"""Öffentliche Dateien aus dem geprüften Bestand der Prüfgruppe (Übergabe v0.4.2, W5). Läuft nur lokal.

Zweck: Für die Stadt gibt es keinen Mietspiegel. Veröffentlicht wird nur, was die Veröffentlichungsregeln
(docs/uebergabe-v0.4.2/veroeffentlichungsregeln.tsv) zulassen, und nur aus Einträgen mit zwei Freigaben:
- data/wohnen/eigentum_gebaeude.geojson: Gebäude juristischer Personen mit Kategorie, Name nur nach Regel R3
  (sonstige juristische Personen nur nach ausdrücklicher Prüfung, ob der Name eine natürliche Person erkennbar macht)
- data/wohnen/eigentum_anteile_ortsbezirk.json: Erfassungsstand und Kategorien je Ortsbezirk; „privat“ nur als Anzahl ab
  der Mindestzahl (R2)
- data/wohnen/mieten_aggregiert.json: €/m² je Ortsbezirk und Baujahrklasse (Median, P25–P75) ab 5 Angaben (R4), je
  juristischer Person ab 5 Angaben aus 2 Gebäuden (R5); nie je privater Vermieter:in (R6), nie einzeln (R7); darunter
  „zu wenige Angaben“ (R8)
Bricht ab, ohne etwas zu schreiben, wenn eine Ausgabe sensible Felder, Namen von Privatpersonen, Kennungen einzelner Angaben,
Einzelbeträge, Vermieter-Schlüssel von Privatpersonen oder Zellen unter der Mindestzahl enthält.

Aufruf: python tools/veroeffentlichen.py -a ARBEIT -s SCHLUESSEL -p P-1 [--ziel REPOSITORY]
"""
import argparse
import json
import re
import statistics
from datetime import date
from pathlib import Path

import pruefgruppe as pg

E = pg.STADT["wohnen_eigentum"]
R = E["regeln"]
KAT = {k["code"]: k for k in E["kategorien"]}
GEBAEUDE = pg.ROOT / "data" / "geo" / "hvgg" / "gebaeude.geojson"
VERBOTEN = {"name_privat_enc", "name_privat", "angabe_id", "erfassung_id", "nettokalt_eur", "wohnflaeche_m2", "einwilligung", "erfasser",
            "vermieter_schluessel", "bemerkung", "lage_hinweis", "beleg_url", "letzte_erhoehung_jahr", "ausstattung"}


class Verstoss(pg.Abbruch):
    pass


def gebaeude():
    d = json.loads(GEBAEUDE.read_text(encoding="utf-8"))
    return {f["properties"]["id"]: f for f in d["features"]}


def eigentum(freigegeben, geb):
    """Je Gebäude der jüngste freigegebene Eintrag."""
    je = {}
    for e in sorted(freigegeben, key=lambda e: e["datensatz"]["erfasst_am"]):
        if e["typ"] == "eigentum" and e["datensatz"]["objekt"]["id"] in geb:
            je[e["datensatz"]["objekt"]["id"]] = e
    return je


def karte(je, geb, stand):
    feats = []
    for gid, e in sorted(je.items()):
        r = e["datensatz"]
        k = KAT[r["kategorie"]]
        if r["kategorie"] in ("privat", "unklar"):
            continue  # R2: privat nie je Gebäude; unklar nicht dargestellt
        name = r.get("name_juristische_person") if k["name_veroeffentlichen"] else None
        if r["kategorie"] == "jp_sonst" and not e.get("name_oeffentlich"):
            name = None
        props = {"id": gid, "kategorie": r["kategorie"], "kategorie_titel": k["titel"], "sicherheit": r["sicherheit"], "beleg": r["beleg_art"]}
        if name:
            props["name"] = " ".join(name.split())
        feats.append({"type": "Feature", "geometry": geb[gid]["geometry"], "properties": props})
    return {"type": "FeatureCollection", "stand": stand, "hinweis": "Nur geprüfte Erfassungen mit zwei Freigaben; unvollständig.",
            "attribution": f"{pg.STADT['gebaeude']['attribution']}; Eigentum: eigene Erfassung, geprüft",
            "features": feats}


def anteile(je, geb, stand):
    gesamt, erfasst = {}, {}
    for f in geb.values():
        if f["properties"]["o"]:  # Gebäude außerhalb der Ortsbezirksflächen zählen nicht
            gesamt[f["properties"]["o"]] = gesamt.get(f["properties"]["o"], 0) + 1
    for gid, e in je.items():
        k = e["datensatz"]["kategorie"]
        if k != "unklar" and geb[gid]["properties"]["o"]:
            erfasst.setdefault(geb[gid]["properties"]["o"], {}).setdefault(k, 0)
            erfasst[geb[gid]["properties"]["o"]][k] += 1
    ob = {}
    for slug, n in sorted(gesamt.items()):
        kat = erfasst.get(slug, {})
        privat = kat.pop("privat", 0)
        zeigen = privat >= R["privat_anteil_min"]
        # unter der Mindestzahl zählt „privat“ auch nicht zu „erfasst“, sonst ließe es sich als Differenz zurückrechnen
        ob[slug] = {"gebaeude": n, "erfasst": sum(kat.values()) + (privat if zeigen else 0), "kategorien": dict(sorted(kat.items())),
                    "privat": privat if zeigen else None}
        if 0 < privat and not zeigen:
            ob[slug]["privat_hinweis"] = "zu wenige Angaben; nicht in „erfasst“ enthalten"
    return {"stand": stand, "mindestzahl_privat": R["privat_anteil_min"], "ortsbezirke": ob}


def kennzahlen(werte):
    q = statistics.quantiles(werte, n=4, method="inclusive")
    return {"median": round(statistics.median(werte), 2), "p25": round(q[0], 2), "p75": round(q[2], 2)}


def mieten(freigegeben, geb, stand):
    namen = {o["slug"]: o["name"] for o in pg.STADT["ortsteile"]}
    zellen, jp, ohne = {}, {}, 0
    for e in freigegeben:
        if e["typ"] != "miete":
            continue
        r = e["datensatz"]
        if not r.get("wohnflaeche_m2") or r["gebaeude_id"] not in geb:
            ohne += 1
            continue
        qm = r["nettokalt_eur"] / r["wohnflaeche_m2"]
        zellen.setdefault((geb[r["gebaeude_id"]]["properties"]["o"], r.get("baujahr_klasse", "unbekannt")), []).append(qm)
        v = e.get("vermieter") or ""
        if v.startswith("JP:"):
            jp.setdefault(v, []).append((r["gebaeude_id"], qm))
    liste = []
    for (slug, bj), werte in sorted(zellen.items()):
        z = {"ortsbezirk": slug, "ortsbezirk_name": namen.get(slug, slug), "baujahr_klasse": bj}
        z.update({"n": len(werte), **kennzahlen(werte)} if len(werte) >= R["mieten_zelle_min"] else {"n": None, "hinweis": "zu wenige Angaben"})
        liste.append(z)
    vermieter = []
    for v, x in sorted(jp.items()):
        werte, gebs = [q for _, q in x], {g for g, _ in x}
        if len(werte) >= R["juristische_person_min_angaben"] and len(gebs) >= R["juristische_person_min_gebaeude"]:
            vermieter.append({"name": v[3:], "n": len(werte), "gebaeude": len(gebs), **kennzahlen(werte)})
    return {"stand": stand, "einheit": "€ je m² Wohnfläche, nettokalt", "methode": "Median und Spanne P25–P75 (Quantile, inklusive Methode)",
            "regeln": {k: R[k] for k in ("mieten_zelle_min", "juristische_person_min_angaben", "juristische_person_min_gebaeude")},
            "angaben_ohne_flaeche": ohne, "zellen": liste, "juristische_personen": vermieter}


def schluessel_rekursiv(x):
    if isinstance(x, dict):
        for k, v in x.items():
            yield k
            yield from schluessel_rekursiv(v)
    elif isinstance(x, list):
        for v in x:
            yield from schluessel_rekursiv(v)


def pruefe_ausgabe(ausgaben, private_namen):
    """Sperre vor dem Schreiben: wirft Verstoss, wenn eine Ausgabe gegen die Regeln verstößt."""
    for name, d in ausgaben.items():
        text = json.dumps(d, ensure_ascii=False)
        felder = VERBOTEN & set(schluessel_rekursiv(d))
        if felder:
            raise Verstoss(f"{name}: verbotene Felder {sorted(felder)}")
        if re.search(r"\bV-(\d{3,5}|neu)\b", text):
            raise Verstoss(f"{name}: Vermieter-Schlüssel einer Privatperson")
        if re.search(r"[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}", text):
            raise Verstoss(f"{name}: Kennung einer einzelnen Angabe")
        low = text.casefold()
        for n in private_namen:
            if n and n.strip().casefold() in low:
                raise Verstoss(f"{name}: Name einer Privatperson")
        for f in d.get("features", []):
            if f["properties"]["kategorie"] in ("privat", "unklar") or ("name" in f["properties"] and not KAT[f["properties"]["kategorie"]]["name_veroeffentlichen"]):
                raise Verstoss(f"{name}: Gebäude mit Kategorie {f['properties']['kategorie']} oder Name, der nicht veröffentlicht werden darf")
        for z in d.get("zellen", []):
            if z.get("median") is not None and (z.get("n") or 0) < R["mieten_zelle_min"]:
                raise Verstoss(f"{name}: Zelle unter der Mindestzahl")
            if z.get("n") is None and z.get("hinweis") != "zu wenige Angaben":
                raise Verstoss(f"{name}: Zelle ohne Hinweis „zu wenige Angaben“")
        for j in d.get("juristische_personen", []):
            if j["n"] < R["juristische_person_min_angaben"] or j["gebaeude"] < R["juristische_person_min_gebaeude"]:
                raise Verstoss(f"{name}: Vergleich je juristischer Person unter der Mindestzahl")
        for o in d.get("ortsbezirke", {}).values() if isinstance(d.get("ortsbezirke"), dict) else []:
            if o.get("privat") is not None and o["privat"] < R["privat_anteil_min"]:
                raise Verstoss(f"{name}: Anteil privat unter der Mindestzahl")
            if o.get("privat") is None and o["erfasst"] != sum(o.get("kategorien", {}).values()):
                raise Verstoss(f"{name}: Anteil privat als Differenz rückrechenbar")


def veroeffentlichen(arbeit, ziel=pg.ROOT, cfg=E):
    stand = date.today().isoformat()
    frei = [e for e in arbeit.eintraege.values() if arbeit.freigegeben(e)]
    geb = gebaeude()
    je = eigentum(frei, geb)
    ausgaben = {"eigentum_gebaeude.geojson": karte(je, geb, stand), "eigentum_anteile_ortsbezirk.json": anteile(je, geb, stand)}
    if cfg["mietangaben_aktiv"]:
        ausgaben["mieten_aggregiert.json"] = mieten(frei, geb, stand)
    namen = [arbeit.name_oeffnen(i, "Veröffentlichungsprüfung") for i, e in arbeit.eintraege.items()
             if e["typ"] == "eigentum" and e["datensatz"].get("name_privat_enc")]
    pruefe_ausgabe(ausgaben, namen)
    ordner = Path(ziel) / "data" / "wohnen"
    ordner.mkdir(parents=True, exist_ok=True)
    for name, d in ausgaben.items():
        (ordner / name).write_text(json.dumps(d, ensure_ascii=False, indent=1 if name.endswith(".json") else None,
                                              separators=None if name.endswith(".json") else (",", ":")), encoding="utf-8")
    arbeit.verlauf(f"veröffentlicht ({', '.join(ausgaben)})")
    arbeit.speichern()
    arbeit.audit(f"veroeffentlichung_{stand}.tsv", ["datei", "eintraege"],
                 [[n, len(d.get("features", d.get("zellen", d.get("ortsbezirke", []))))] for n, d in ausgaben.items()])
    return ausgaben


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("-a", "--arbeit", required=True)
    ap.add_argument("-s", "--schluessel", required=True)
    ap.add_argument("-p", "--pruefer", required=True)
    ap.add_argument("--ziel", default=str(pg.ROOT))
    a = ap.parse_args(argv)
    aus = veroeffentlichen(pg.Arbeit(a.arbeit, pg.Schluessel(a.schluessel), a.pruefer), a.ziel)
    print("geschrieben:", ", ".join(aus), "– danach: python -m pipeline wohnen")


if __name__ == "__main__":
    main()
