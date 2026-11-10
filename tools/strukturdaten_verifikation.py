"""Verifikation der Strukturdaten (Phase 4): Stichprobe von 20 Werten gegen die Originalquellen.

Unabhängig vom Adapter (pipeline/strukturdaten.py):
- Zensus je Ortsbezirk: die bundesweiten Gitterdateien neu laden und mit eigenem Code (räumlicher Index, eigene
  Zuordnung über den Zellmittelpunkt) neu summieren.
- Zensus für die Stadt: amtliche Regionaltabellen (Bevölkerung, Gebäude und Wohnungen); Abweichungen durch die
  Geheimhaltung und die Zuordnung der Zellen sind erwartet und werden ausgewiesen.
- Wegweiser Kommune: zweiter Endpunkt der Schnittstelle (/rest/statistics/data, JSON) statt des CSV-Exports.
Rohdateien bleiben im Arbeitsspeicher. Ergebnis: data/strukturdaten/audit_verifikation.tsv.

Aufruf: python tools/strukturdaten_verifikation.py
"""
import csv
import io
import json
import sys
import urllib.request
import zipfile
from pathlib import Path

import openpyxl
from pyproj import Transformer
from shapely import STRtree
from shapely.geometry import Point, shape
from shapely.ops import transform

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "strukturdaten"
STADT = json.loads((ROOT / "config" / "stadt.json").read_text(encoding="utf-8"))
S = STADT["strukturdaten"]
ARS = STADT["stadt"]["ars"]
GEMEINDE = STADT["stadt"]["gemeindeschluessel"]
UA = {"User-Agent": STADT["projekt"]["user_agent"]}


def holen(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=300) as r:
        return r.read()


def zahl(v):
    v = (v or "").strip()
    return 0 if v in ("", "–", "-") else int(v.replace(".", ""))


# --- Zensus: unabhängige Neuberechnung aus dem Gitter ------------------------------------------------------------
def gitter_neu(key, spalten):
    """{raum_id: {spalte: Summe}} aus der Originaldatei, Zuordnung über den Zellmittelpunkt (räumlicher Index)."""
    to = Transformer.from_crs("EPSG:4326", "EPSG:3035", always_xy=True).transform
    fl = json.loads((ROOT / "data" / "geo" / "dl-de-zero" / "ortsbezirke.geojson").read_text(encoding="utf-8"))["features"]
    ids = [f["properties"]["slug"] for f in fl]
    geoms = [transform(to, shape(f["geometry"])) for f in fl]
    baum = STRtree(geoms)
    t = S["zensus"]["tabellen"][key]
    roh = holen(S["zensus"]["basis"] + t["zip"])
    summen = {}
    with zipfile.ZipFile(io.BytesIO(roh)) as z:
        name = next(n for n in z.namelist() if n.endswith(t["datei"]))
        for r in csv.DictReader(io.TextIOWrapper(z.open(name), encoding="utf-8-sig"), delimiter=";"):
            p = Point(float(r["x_mp_100m"]), float(r["y_mp_100m"]))
            treffer = [i for i in baum.query(p) if geoms[i].contains(p)]
            if not treffer:
                continue
            for raum in (ids[treffer[0]], GEMEINDE):
                s = summen.setdefault(raum, {})
                for c in spalten:
                    s[c] = s.get(c, 0) + zahl(r[c])
                s["_zellen"] = s.get("_zellen", 0) + 1
    return summen


def gitter_mittel(raum_ids):
    """Durchschnittsalter je Raum, gewichtet mit Einwohnern, mit eigener Zuordnung."""
    to = Transformer.from_crs("EPSG:4326", "EPSG:3035", always_xy=True).transform
    fl = json.loads((ROOT / "data" / "geo" / "dl-de-zero" / "ortsbezirke.geojson").read_text(encoding="utf-8"))["features"]
    ids = [f["properties"]["slug"] for f in fl]
    geoms = [transform(to, shape(f["geometry"])) for f in fl]
    baum = STRtree(geoms)

    def lesen(key, spalte):
        t = S["zensus"]["tabellen"][key]
        with zipfile.ZipFile(io.BytesIO(holen(S["zensus"]["basis"] + t["zip"]))) as z:
            name = next(n for n in z.namelist() if n.endswith(t["datei"]))
            out = {}
            for r in csv.DictReader(io.TextIOWrapper(z.open(name), encoding="utf-8-sig"), delimiter=";"):
                p = Point(float(r["x_mp_100m"]), float(r["y_mp_100m"]))
                treffer = [i for i in baum.query(p) if geoms[i].contains(p)]
                if treffer:
                    out[r.get("GITTER_ID_100m") or r.get("GITTER_ID_100M")] = (ids[treffer[0]], r[spalte])
            return out
    alter, ew = lesen("durchschnittsalter", "Durchschnittsalter"), lesen("einwohner", "Einwohner")
    out = {}
    for raum in raum_ids:
        paare = [(float(a.replace(",", ".")), zahl(ew.get(c, (None, ""))[1])) for c, (r, a) in alter.items()
                 if (raum == GEMEINDE or r == raum) and a.strip() not in ("", "–", "-")]
        paare = [(a, e) for a, e in paare if e > 0]
        g = sum(e for _, e in paare)
        out[raum] = round(sum(a * e for a, e in paare) / g, 1) if g else None
    return out


def regionaltabelle(datei, blatt):
    wb = openpyxl.load_workbook(io.BytesIO(holen(S["zensus"]["basis"] + datei)), read_only=True)
    rows = wb[blatt].iter_rows(values_only=True)
    kopf = next(rows)
    return next(dict(zip(kopf, r)) for r in rows if r and str(r[1]) == ARS)


# --- Wegweiser: zweiter Endpunkt ---------------------------------------------------------------------------------
def wegweiser_json(indikator, kommune, jahr):
    d = json.loads(holen(f"{S['wegweiser']['api']}statistics/data/{indikator}+{kommune}+{jahr}"))["data"]
    return d["indicators"][0]["regionYearValues"][0][0]


def main():
    werte = {(r["raum_id"], r["indikator_id"]): r for r in csv.DictReader((OUT / "werte.tsv").open(encoding="utf-8"), delimiter="\t")}
    vergleich = {(r["wegweiser_friendly_url"], r["indikator_id"], r["jahr"]): r for r in
                 csv.DictReader((OUT / "gesamtstadt.tsv").open(encoding="utf-8"), delimiter="\t")}
    zeilen = []

    def zeile(quelle, raum, ind, jahr, sm, pr, weg, ergebnis, bemerkung=""):
        try:
            abw = f"{(float(sm) - float(pr)) / float(pr) * 100:+.2f} %" if sm not in ("", None) and pr not in ("", None) and float(pr) else ""
        except ValueError:
            abw = ""
        zeilen.append({"nr": len(zeilen) + 1, "quelle": quelle, "raum_id": raum, "indikator_id": ind, "jahr": jahr,
                       "wert_stadtmonitor": sm, "wert_pruefung": pr, "abweichung": abw, "pruefweg": weg, "ergebnis": ergebnis, "bemerkung": bemerkung})

    print("Zensus: Neuberechnung aus dem Gitter …", file=sys.stderr)
    ew = gitter_neu("einwohner", ["Einwohner"])
    al = gitter_neu("alter", ["Insgesamt_Bevoelkerung", "Unter18", "a18bis29", "a30bis49", "a50bis64", "a65undaelter"])
    wo = gitter_neu("wohnungen_typ", ["Insgesamt_Wohnungen", "FreiEFH", "EFH_DHH", "EFH_Reihenhaus", "Freist_ZFH", "ZFH_DHH", "ZFH_Reihenhaus",
                                      "MFH_3bis6Wohnungen", "MFH_7bis12Wohnungen", "MFH_13undmehrWohnungen", "AndererGebaeudetyp"])
    da = gitter_mittel(["berlepsch-ellerode"])
    teil = lambda s: s["Unter18"] + s["a18bis29"] + s["a30bis49"] + s["a50bis64"] + s["a65undaelter"]  # noqa: E731
    efh = lambda s: sum(s[c] for c in ("FreiEFH", "EFH_DHH", "EFH_Reihenhaus", "Freist_ZFH", "ZFH_DHH", "ZFH_Reihenhaus"))  # noqa: E731
    wteil = lambda s: efh(s) + sum(s[c] for c in ("MFH_3bis6Wohnungen", "MFH_7bis12Wohnungen", "MFH_13undmehrWohnungen", "AndererGebaeudetyp"))  # noqa: E731
    gleich = lambda a, b: "übereinstimmend" if str(a) == str(b) else "abweichend"  # noqa: E731
    neu = "eigene Neuberechnung aus der Originaldatei (räumlicher Index, Zellmittelpunkt)"
    for raum in ("kernstadt", "albshausen"):
        sm = werte[(raum, "zensus_einwohner")]["wert"]
        zeile("Zensus 2022, Gitter Bevölkerungszahl", raum, "zensus_einwohner", "2022", sm, ew[raum]["Einwohner"], neu, gleich(sm, ew[raum]["Einwohner"]))
    for raum, ind, z in (("hundelshausen", "zensus_anteil_ab65", "a65undaelter"), ("wendershausen", "zensus_anteil_unter18", "Unter18")):
        s = al[raum]
        pr = round(s[z] / teil(s) * 100, 1)
        sm = werte[(raum, ind)]["wert"]
        zeile("Zensus 2022, Gitter 5 Altersklassen", raum, ind, "2022", sm, pr, neu + "; Anteil aus Zähler und Summe der Klassen", gleich(float(sm), pr))
    s = al["ellingerode"]
    abw = abs(teil(s) - s["Insgesamt_Bevoelkerung"]) / s["Insgesamt_Bevoelkerung"]
    sm = werte[("ellingerode", "zensus_anteil_ab65")]
    zeile("Zensus 2022, Gitter 5 Altersklassen", "ellingerode", "zensus_anteil_ab65", "2022", f"{sm['wert']} ({sm['status']})", "",
          neu, "übereinstimmend" if sm["status"] == "fehlt" and abw > S["schwelle"]["abweichung_max"] else "abweichend",
          f"Schwelle: Teilgruppen weichen um {abw * 100:.1f} % ab, nicht ausgewiesen ist richtig")
    for raum in ("berlepsch-ellerode",):
        sm = werte[(raum, "zensus_durchschnittsalter")]["wert"]
        zeile("Zensus 2022, Gitter Durchschnittsalter", raum, "zensus_durchschnittsalter", "2022", sm, da[raum], neu + "; gewichtet mit Einwohnern",
              gleich(float(sm), da[raum]))
    s = wo["unterrieden"]
    pr = round(efh(s) / wteil(s) * 100, 1)
    sm = werte[("unterrieden", "zensus_anteil_wohnungen_efh_zfh")]["wert"]
    zeile("Zensus 2022, Gitter Wohnungen nach Gebäudetyp", "unterrieden", "zensus_anteil_wohnungen_efh_zfh", "2022", sm, pr, neu, gleich(float(sm), pr))

    print("Zensus: Regionaltabellen …", file=sys.stderr)
    bev = regionaltabelle("Regionaltabelle_Bevoelkerung.xlsx", "CSV-Einwohnerzahl")
    gwz = regionaltabelle("Regionaltabelle_Gebaeude_Wohnungen.xlsx", "CSV-Wohnungen")
    amtl = "amtliche Regionaltabelle des Zensus 2022 (Gemeinde)"
    zeile("Zensus 2022, Regionaltabelle Bevölkerung", GEMEINDE, "zensus_einwohner", "2022", werte[(GEMEINDE, "zensus_einwohner")]["wert"], bev["EWZ"], amtl,
          "erwartete Abweichung", "Summe der Zellen: Geheimhaltung (Cell-Key-Methode) und Zuordnung über den Zellmittelpunkt")
    zeile("Zensus 2022, Regionaltabelle Gebäude und Wohnungen", GEMEINDE, "zensus_wohnungen", "2022", werte[(GEMEINDE, "zensus_wohnungen")]["wert"],
          gwz["GEBAEUDEART_SYS_1"], amtl + ", Wohnungen in Gebäuden mit Wohnraum", "erwartete Abweichung", "wie oben")
    ein_zwei = int(gwz["ZAHLWOHNGN_HHG__1"]) + int(gwz["ZAHLWOHNGN_HHG__2"])
    zeile("Zensus 2022, Regionaltabelle Gebäude und Wohnungen", GEMEINDE, "zensus_anteil_wohnungen_efh_zfh", "2022",
          werte[(GEMEINDE, "zensus_anteil_wohnungen_efh_zfh")]["wert"], round(ein_zwei / int(gwz["GEBAEUDEART_SYS_1"]) * 100, 1),
          amtl + ", Wohnungen in Gebäuden mit 1 oder 2 Wohnungen", "Definition abweichend",
          "Gitter zählt nach Bauart (Einfamilien-, Zweifamilienhaus), Gebäude anderer Bauart im Nenner; die Regionaltabelle nach Zahl der Wohnungen im Gebäude")

    print("Wegweiser: zweiter Endpunkt …", file=sys.stderr)
    stichprobe = [("witzenhausen", "bevoelkerung", 2023), ("werra-meissner-kreis-lk", "altenquotient", 2023), ("eschwege", "kinderarmut", 2023),
                  ("hannoversch-muenden", "auslaenderanteil", 2023), ("bad-wildungen", "sgb-ii-quote", 2021), ("schwalmstadt", "wanderungssaldo", 2019),
                  ("witzenhausen", "durchschnittsalter", 2010), ("witzenhausen", "jugendquotient", 2015),
                  ("witzenhausen", "arbeitslose-an-den-svb", 2023), ("witzenhausen", "wohnungen-in-ein-zweifamilienhaeusern", 2021)]
    for kommune, ind, jahr in stichprobe:
        sm = vergleich.get((kommune, f"ww_{ind}", str(jahr)), {}).get("wert", "")
        pr = wegweiser_json(ind, kommune, jahr)
        pr = "" if pr is None else pr
        ok = (sm == "" and pr == "") or (sm != "" and pr != "" and abs(float(sm) - float(pr)) < 1e-9)
        zeile("Wegweiser Kommune", kommune, f"ww_{ind}", str(jahr), sm, pr, "Schnittstelle /rest/statistics/data (JSON), nicht der CSV-Export des Adapters",
              "übereinstimmend" if ok else "abweichend", "keine Angabe in beiden Wegen" if sm == "" and pr == "" else "")

    spalten = ["nr", "quelle", "raum_id", "indikator_id", "jahr", "wert_stadtmonitor", "wert_pruefung", "abweichung", "pruefweg", "ergebnis", "bemerkung"]
    with (OUT / "audit_verifikation.tsv").open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=spalten, delimiter="\t", lineterminator="\n")
        w.writeheader()
        w.writerows(zeilen)
    for z in zeilen:
        print(f"{z['nr']:2} {z['ergebnis']:22} {z['raum_id']:24} {z['indikator_id']:42} {z['wert_stadtmonitor']} | {z['wert_pruefung']} {z['abweichung']}")
    if any(z["ergebnis"] == "abweichend" for z in zeilen):
        sys.exit(1)


if __name__ == "__main__":
    main()
