"""Strukturdaten nach dem gemeinsamen Datenvertrag „Strukturdaten v1“ (data/strukturdaten/).

Quellen (config/stadt.json, Abschnitt strukturdaten):
- Zensus 2022, 100-m-Gitter (Statistische Ämter, dl-de/by-2-0): Die bundesweiten ZIP-Dateien werden geladen, auf die
  Zellen im Stadtgebiet (mit einer Zelle Puffer) gefiltert und verworfen. Im Zwischenspeicher (data/raw/strukturdaten/,
  nicht im Repository) liegt nur der Auszug.
- Wegweiser Kommune (Bertelsmann Stiftung, CC0 1.0): Werte der Stadt, des Kreises und der Vergleichskommunen gleichen
  Demografietyps über die friendlyUrls. Die Schnittstelle ist nicht versioniert; weicht info.version der OpenAPI-
  Beschreibung von wegweiser.api_version ab, bricht der Abruf ab.

Übertragung auf die Ortsbezirke (Gemarkungen): Zellmittelpunkt in der Fläche; Grenzzellen mit Flächenanteil in
zuordnung.tsv und audit_raumabgleich.tsv. Alle Werte je Ortsbezirk und für die Stadt aus den Zellen tragen
status=abgeleitet. Anzahlen werden summiert („–“ = genau null oder durch die Geheimhaltung auf null gesetzt, zählt als
null); Anteile und Quoten nur aus summierten Zählern und Nennern; Mittelwerte nur gewichtet mit einem Gewicht je Zelle.
Anteile und Quoten erscheinen nur, wenn der Nenner mindestens schwelle.nenner_min beträgt und die Summe der Teilgruppen
höchstens schwelle.abweichung_max von der Gesamtzahl derselben Tabelle abweicht; sonst status=fehlt (Grund im Audit).
"""
import csv
import hashlib
import io
import json
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from pyproj import Transformer
from shapely.geometry import Point, box, mapping, shape
from shapely.ops import transform, unary_union

from . import config, net

S = config.STADT["strukturdaten"]
Z, WW = S["zensus"], S["wegweiser"]
RAW = config.RAW / "strukturdaten"
OUT = config.ROOT / "data" / "strukturdaten"
GEMEINDE = config.STADT["stadt"]["gemeindeschluessel"]
ZENSUS_ALTER = 365 * 86400
WEGWEISER_ALTER = 30 * 86400
ZELLE = 100

# Altersklassen: Die Tabelle mit 5 Klassen verliert durch die Geheimhaltung am wenigsten (Stadt 2,2 %, 5er-Jahresgruppen
# 18 %); ihre Grenzen erlauben Anteile unter 18 und ab 65, aber keine Quotienten mit der Grenze 20 Jahre (Wegweiser).
ALTER_U18 = ("Unter18",)
ALTER_18_64 = ("a18bis29", "a30bis49", "a50bis64")
ALTER_AB65 = ("a65undaelter",)
EFH_ZFH = ("FreiEFH", "EFH_DHH", "EFH_Reihenhaus", "Freist_ZFH", "ZFH_DHH", "ZFH_Reihenhaus")
MFH_ANDERE = ("MFH_3bis6Wohnungen", "MFH_7bis12Wohnungen", "MFH_13undmehrWohnungen", "AndererGebaeudetyp")


def jetzt():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


# --- Raumeinheiten -----------------------------------------------------------------------------------------------
def flaechen(datei=None):
    """[(raum_id, name, Fläche in EPSG:3035, Fläche in WGS84)] der Ortsbezirke (Gemarkungen)."""
    to = Transformer.from_crs("EPSG:4326", "EPSG:3035", always_xy=True).transform
    fl = json.loads(Path(datei or config.ORTSBEZIRKE).read_text(encoding="utf-8"))["features"]
    return [(f["properties"]["slug"], f["properties"]["name"], transform(to, shape(f["geometry"])), shape(f["geometry"])) for f in fl]


def _kennung(r):
    return r.get("GITTER_ID_100m") or r.get("GITTER_ID_100M")  # die Tabellen schreiben die Spalte unterschiedlich


def filtern(roh, datei, stadt3035):
    """Zeilen der 100-m-Tabelle `datei` aus dem ZIP `roh` (Bytes), deren Zelle die Stadtfläche mit einer Zelle Puffer
    schneidet; Kennungsspalte einheitlich GITTER_ID_100m."""
    puffer = stadt3035.buffer(ZELLE)
    x0, y0, x1, y1 = puffer.bounds
    with zipfile.ZipFile(io.BytesIO(roh)) as z:
        name = next(n for n in z.namelist() if n.endswith(datei))
        leser = csv.DictReader(io.TextIOWrapper(z.open(name), encoding="utf-8-sig"), delimiter=";")
        kopf = ["GITTER_ID_100m" if k.upper() == "GITTER_ID_100M" else k for k in leser.fieldnames]
        zeilen = []
        for r in leser:
            x, y = float(r["x_mp_100m"]), float(r["y_mp_100m"])
            if x0 <= x <= x1 and y0 <= y <= y1 and box(x - 50, y - 50, x + 50, y + 50).intersects(puffer):
                zeilen.append({"GITTER_ID_100m": _kennung(r), **{k: v for k, v in r.items() if k.upper() != "GITTER_ID_100M"}})
    return kopf, zeilen


def zuordnen(zellen, fl):
    """{zell_id: (raum_id oder None, Flächenanteil im Ziel, Anteil im Stadtgebiet)} nach dem Zellmittelpunkt."""
    out = {}
    for cid, (x, y) in zellen.items():
        z = box(x - 50, y - 50, x + 50, y + 50)
        ziel = next((rid for rid, _, g, _ in fl if g.contains(Point(x, y))), None)
        anteil = {rid: z.intersection(g).area / z.area for rid, _, g, _ in fl if z.intersects(g)}
        out[cid] = (ziel, anteil.get(ziel, 0.0) if ziel else 0.0, sum(anteil.values()))
    return out


def konfidenz(anteil):
    return "hoch" if anteil >= 0.999 else "mittel" if anteil >= 0.5 else "niedrig"


# --- Abruf -------------------------------------------------------------------------------------------------------
def _protokoll(eintrag):
    p = RAW / "abruf.json"
    alt = json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}
    alt[eintrag["quelle"]] = eintrag
    p.write_text(json.dumps(alt, ensure_ascii=False, indent=1), encoding="utf-8")


def _frisch(p, alter):
    import time
    return p.exists() and time.time() - p.stat().st_mtime < alter


def fetch_zensus():
    RAW.mkdir(parents=True, exist_ok=True)
    stadt = unary_union([g for _, _, g, _ in flaechen()])
    for key, t in Z["tabellen"].items():
        ziel = RAW / f"zensus_{key}.csv"
        if _frisch(ziel, ZENSUS_ALTER):
            continue
        url = Z["basis"] + t["zip"]
        body, _ = net.get(url, tries=2)
        if not body.startswith(b"PK"):
            raise SystemExit(f"Zensus {key}: keine ZIP-Datei unter {url}")
        kopf, zeilen = filtern(body, t["datei"], stadt)
        sha = hashlib.sha256(body).hexdigest()
        del body  # Rohdatei verwerfen; nur der Auszug bleibt
        teil = ziel.with_name(ziel.name + ".teil")
        with teil.open("w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=kopf, delimiter=";", lineterminator="\n")
            w.writeheader()
            w.writerows(zeilen)
        teil.replace(ziel)
        _protokoll({"quelle": f"zensus_{key}", "url": url, "zeit": jetzt(), "http_status": 200, "zeilen": len(zeilen), "sha256": sha})


def _json(url):
    body, _ = net.get(url, tries=3)
    return json.loads(body), body


def fetch_wegweiser():
    RAW.mkdir(parents=True, exist_ok=True)
    api, body = _json(WW["openapi"])
    version = api.get("info", {}).get("version")
    _protokoll({"quelle": "wegweiser_openapi", "url": WW["openapi"], "zeit": jetzt(), "http_status": 200, "zeilen": "",
                "sha256": hashlib.sha256(body).hexdigest(), "info_version": version})
    if version != WW["api_version"]:
        raise SystemExit(f"Wegweiser Kommune: Schnittstelle geändert (info.version {version}, erwartet {WW['api_version']}). "
                         "Abruf abgebrochen; Indikatoren und friendlyUrls prüfen, dann wegweiser.api_version anpassen.")
    ziel = RAW / "wegweiser"
    ziel.mkdir(exist_ok=True)
    if _frisch(ziel / "regionen.json", WEGWEISER_ALTER) and all(_frisch(ziel / f"{i}.csv", WEGWEISER_ALTER) for i in WW["indikatoren"]):
        return
    stand = net.get(WW["api"] + "statistics/version", tries=3)[0].decode("utf-8").strip().strip('"')  # Datenstand als Text
    regionen = {fu: _json(WW["api"] + f"region/get/{fu}")[0] for fu in WW["kommunen"]}
    (ziel / "regionen.json").write_text(json.dumps({"datenstand": stand, "regionen": regionen}, ensure_ascii=False, indent=1), encoding="utf-8")
    for fu in WW["indikatoren"]:
        meta, _ = _json(WW["api"] + f"indicator/get/{fu}")
        jahre = meta.get("years") or []
        url = WW["api"] + f"export/{fu}+{'+'.join(WW['kommunen'])}+{min(jahre)}-{max(jahre)}+tabelle.csv?charset=UTF-8"
        body, _ = net.get(url, tries=3)
        (ziel / f"{fu}.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")
        net.speichern(ziel / f"{fu}.csv", body)
        _protokoll({"quelle": f"wegweiser_{fu}", "url": url, "zeit": jetzt(), "http_status": 200,
                    "zeilen": body.count(b"\n"), "sha256": hashlib.sha256(body).hexdigest()})


def fetch():
    fetch_zensus()
    fetch_wegweiser()


# --- Wegweiser lesen ---------------------------------------------------------------------------------------------
def _zahl_de(s):
    s = (s or "").strip()
    if not s or s in ("k.A.", ".", "-", "–"):
        return None
    return float(s.replace(".", "").replace(",", "."))


def wegweiser_csv(text, namen):
    """[(friendlyUrl der Kommune, Jahr, Wert)] aus einem Export einer Kennzahl. namen: {Name in der Tabelle: friendlyUrl}."""
    zeilen = list(csv.reader(io.StringIO(text), delimiter=";"))
    k = next(i for i, r in enumerate(zeilen) if r and r[0] == "Kommune")
    jahre = [int(c.split("\n")[0].strip()) for c in zeilen[k][1:]]
    out = []
    for r in zeilen[k + 1:]:
        if not r or not r[0] or r[0] not in namen:
            continue
        for j, v in zip(jahre, r[1:]):
            out.append((namen[r[0]], j, _zahl_de(v)))
    return out


# --- Aufbau ------------------------------------------------------------------------------------------------------
def _ganz(v):
    v = (v or "").strip()
    return 0 if v in ("–", "-", "") else int(v.replace(".", ""))


def _dezimal(v):
    v = (v or "").strip()
    return None if v in ("–", "-", "") else float(v.replace(",", "."))


def _lesen(key):
    p = RAW / f"zensus_{key}.csv"
    if not p.exists():
        return None
    with p.open(encoding="utf-8") as f:
        return {r["GITTER_ID_100m"]: r for r in csv.DictReader(f, delimiter=";")}


def zensus_werte(tab, zuo, raeume, schwelle=None):
    """Werte je Raum aus den gefilterten Tabellen. tab: {key: {zell_id: Zeile}}; zuo: {zell_id: raum_id}; raeume: Liste der
    Ziel-IDs, dazu die Gemeinde. Gibt (werte, gruende) zurück: werte {(raum, indikator): (wert, status, quellobjekt)}."""
    schwelle = schwelle or S["schwelle"]
    werte, gruende = {}, []

    def summe(key, spalten, raum):
        zellen = [r for cid, r in tab[key].items() if (zuo.get(cid) == raum if raum != GEMEINDE else zuo.get(cid))]
        return {s: sum(_ganz(r.get(s)) for r in zellen) for s in spalten}, len(zellen)

    def quelle(key, n):
        return f"{Z['tabellen'][key]['datei']}; {n} Zellen"

    def anteil(raum, ind, zaehler, nenner, gesamt, key, n):
        """Anteil in % aus Zähler und Nenner (Summe der Teilgruppen); gesamt: Gesamtzahl derselben Tabelle."""
        abw = abs(nenner - gesamt) / gesamt if gesamt else 0.0
        if nenner < schwelle["nenner_min"]:
            werte[(raum, ind)] = (None, "fehlt", quelle(key, n))
            gruende.append({"raum_id": raum, "indikator_id": ind, "grund": f"Nenner {nenner} unter {schwelle['nenner_min']}"})
        elif abw > schwelle["abweichung_max"]:
            werte[(raum, ind)] = (None, "fehlt", quelle(key, n))
            gruende.append({"raum_id": raum, "indikator_id": ind,
                            "grund": f"Teilgruppen weichen um {abw * 100:.1f} % von der Gesamtzahl ab (Geheimhaltung)"})
        else:
            werte[(raum, ind)] = (round(zaehler / nenner * 100, 1), "abgeleitet", quelle(key, n))

    for raum in [*raeume, GEMEINDE]:
        if tab.get("einwohner") is not None:
            s, n = summe("einwohner", ["Einwohner"], raum)
            werte[(raum, "zensus_einwohner")] = (s["Einwohner"], "abgeleitet", quelle("einwohner", n))
        if tab.get("alter") is not None:
            s, n = summe("alter", ["Insgesamt_Bevoelkerung", *ALTER_U18, *ALTER_18_64, *ALTER_AB65], raum)
            u18, m, a65 = (sum(s[c] for c in g) for g in (ALTER_U18, ALTER_18_64, ALTER_AB65))
            teil, ins = u18 + m + a65, s["Insgesamt_Bevoelkerung"]
            for ind, v in (("zensus_unter18", u18), ("zensus_18bis64", m), ("zensus_ab65", a65)):
                werte[(raum, ind)] = (v, "abgeleitet", quelle("alter", n))
            anteil(raum, "zensus_anteil_unter18", u18, teil, ins, "alter", n)
            anteil(raum, "zensus_anteil_ab65", a65, teil, ins, "alter", n)
        if tab.get("durchschnittsalter") is not None and tab.get("einwohner") is not None:
            paare = [(_dezimal(r.get("Durchschnittsalter")), _ganz(tab["einwohner"].get(cid, {}).get("Einwohner")))
                     for cid, r in tab["durchschnittsalter"].items() if (zuo.get(cid) == raum if raum != GEMEINDE else zuo.get(cid))]
            paare = [(a, e) for a, e in paare if a is not None and e > 0]
            gewicht = sum(e for _, e in paare)
            key = "durchschnittsalter"
            if gewicht < schwelle["nenner_min"]:
                werte[(raum, "zensus_durchschnittsalter")] = (None, "fehlt", quelle(key, len(paare)))
                gruende.append({"raum_id": raum, "indikator_id": "zensus_durchschnittsalter", "grund": f"Gewicht {gewicht} unter {schwelle['nenner_min']}"})
            else:
                werte[(raum, "zensus_durchschnittsalter")] = (round(sum(a * e for a, e in paare) / gewicht, 1), "abgeleitet",
                                                              f"{quelle(key, len(paare))}; gewichtet mit Einwohnern ({Z['tabellen']['einwohner']['datei']})")
        if tab.get("wohnungen_typ") is not None:
            s, n = summe("wohnungen_typ", ["Insgesamt_Wohnungen", *EFH_ZFH, *MFH_ANDERE], raum)
            efh = sum(s[c] for c in EFH_ZFH)
            teil = efh + sum(s[c] for c in MFH_ANDERE)
            werte[(raum, "zensus_wohnungen")] = (s["Insgesamt_Wohnungen"], "abgeleitet", quelle("wohnungen_typ", n))
            werte[(raum, "zensus_wohnungen_efh_zfh")] = (efh, "abgeleitet", quelle("wohnungen_typ", n))
            anteil(raum, "zensus_anteil_wohnungen_efh_zfh", efh, teil, s["Insgesamt_Wohnungen"], "wohnungen_typ", n)
    return werte, gruende


def _schreiben(name, spalten, zeilen):
    with (OUT / name).open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter="\t", lineterminator="\n")
        w.writerow(spalten)
        for z in zeilen:
            w.writerow(["" if z.get(s) is None else str(z.get(s)).replace("\t", " ").replace("\n", " ") for s in spalten])


INDIKATOR_SPALTEN = ["indikator_id", "name", "thema", "einheit", "typ", "zaehler_id", "nenner_id", "raumebenen", "jahre", "quelle",
                     "datenhalter", "lizenz", "lizenz_url", "namensnennung", "metatext", "geheimhaltung", "quell_url", "abrufdatum"]


def build():
    fl = flaechen()
    tab = {k: _lesen(k) for k in Z["tabellen"]}
    abruf = json.loads((RAW / "abruf.json").read_text(encoding="utf-8")) if (RAW / "abruf.json").exists() else {}
    if all(v is None for v in tab.values()) and not (RAW / "wegweiser").exists():
        print("Strukturdaten: keine Rohdaten; data/strukturdaten/ bleibt auf dem letzten Stand")
        return
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "raum").mkdir(exist_ok=True)
    meta_alt = json.loads((OUT / "meta.json").read_text(encoding="utf-8")) if (OUT / "meta.json").exists() else {}

    # Raumeinheiten (WGS84)
    gq = {"quelle": "Digitale Verwaltungsgrenzen Hessen (HVBG), Gemarkungen", "lizenz": "dl-de/zero-2.0"}
    (OUT / "raum" / "ortsbezirk.geojson").write_text(json.dumps({"type": "FeatureCollection", "features": [
        {"type": "Feature", "geometry": mapping(g4326), "properties": {"raum_id": rid, "name": name, "raumebene": "ortsbezirk",
                                                                       "eltern_id": GEMEINDE, **gq}}
        for rid, name, _, g4326 in fl]}, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    (OUT / "raum" / "gemeinde.geojson").write_text(json.dumps({"type": "FeatureCollection", "features": [
        {"type": "Feature", "geometry": mapping(unary_union([g for *_, g in fl])),
         "properties": {"raum_id": GEMEINDE, "name": config.STADT["stadt"]["name"], "raumebene": "gemeinde", "eltern_id": "", **gq}}]},
        ensure_ascii=False, separators=(",", ":")), encoding="utf-8")

    zeilen_werte, zeilen_zuo, zeilen_raum, gruende = [], [], [], []
    zensus_da = any(v is not None for v in tab.values())
    if zensus_da:
        zellen = {}
        for t in tab.values():
            for cid, r in (t or {}).items():
                zellen[cid] = (float(r["x_mp_100m"]), float(r["y_mp_100m"]))
        zu = zuordnen(zellen, fl)
        zuo = {cid: z[0] for cid, z in zu.items() if z[0]}
        for cid in sorted(zu):
            ziel, anteil, im_gebiet = zu[cid]
            if ziel:
                zeilen_zuo.append({"von_ebene": "gitter_100m", "von_id": cid, "nach_ebene": "ortsbezirk", "nach_id": ziel,
                                   "flaechenanteil": round(anteil, 3), "methode": "zellmittelpunkt", "konfidenz": konfidenz(anteil)})
            if ziel and anteil < 0.999:
                zeilen_raum.append({"einheit": cid, "ziel": ziel, "flaechenanteil": round(anteil, 3), "methode": "zellmittelpunkt",
                                    "konfidenz": konfidenz(anteil), "pruefstatus": "Grenzzelle, ganz dem Ortsbezirk des Mittelpunkts zugeordnet"})
            elif not ziel and im_gebiet > 0:
                zeilen_raum.append({"einheit": cid, "ziel": "", "flaechenanteil": round(im_gebiet, 3), "methode": "zellmittelpunkt",
                                    "konfidenz": "", "pruefstatus": "nicht zugeordnet: Mittelpunkt außerhalb des Stadtgebiets"})
        werte, gruende = zensus_werte(tab, zuo, [rid for rid, *_ in fl])
        for (raum, ind), (wert, status, q) in sorted(werte.items()):
            zeilen_werte.append({"raumebene": "gemeinde" if raum == GEMEINDE else "ortsbezirk", "raum_id": raum, "indikator_id": ind,
                                 "jahr": Z["stichtag"][:4], "wert": wert, "status": status, "quellobjekt": q})
        _schreiben("werte.tsv", ["raumebene", "raum_id", "indikator_id", "jahr", "wert", "status", "quellobjekt"], zeilen_werte)
        _schreiben("zuordnung.tsv", ["von_ebene", "von_id", "nach_ebene", "nach_id", "flaechenanteil", "methode", "konfidenz"], zeilen_zuo)
        _schreiben("audit_raumabgleich.tsv", ["einheit", "ziel", "flaechenanteil", "methode", "konfidenz", "pruefstatus"], zeilen_raum)
        _schreiben("audit_schwelle.tsv", ["raum_id", "indikator_id", "grund"], gruende)

    # Wegweiser: Vergleichswerte (gesamtstadt.tsv)
    ww_meta, ww_zeilen, datenstand_ww = {}, [], meta_alt.get("wegweiser_datenstand")
    wd = RAW / "wegweiser"
    if (wd / "regionen.json").exists():
        reg = json.loads((wd / "regionen.json").read_text(encoding="utf-8"))
        datenstand_ww = reg["datenstand"]
        namen = {r["name"]: fu for fu, r in reg["regionen"].items()}
        for fu in WW["indikatoren"]:
            if not (wd / f"{fu}.csv").exists():
                continue
            ww_meta[fu] = json.loads((wd / f"{fu}.json").read_text(encoding="utf-8"))
            ab = abruf.get(f"wegweiser_{fu}", {}).get("zeit", "")[:10]
            for kfu, j, v in wegweiser_csv((wd / f"{fu}.csv").read_text(encoding="utf-8-sig"), namen):
                ww_zeilen.append({"kommune": reg["regionen"][kfu]["name"], "wegweiser_friendly_url": kfu, "indikator_id": f"ww_{fu}",
                                  "jahr": j, "wert": v, "abrufdatum": ab})
        _schreiben("gesamtstadt.tsv", ["kommune", "wegweiser_friendly_url", "indikator_id", "jahr", "wert", "abrufdatum"], ww_zeilen)

    # Indikatoren
    za = abruf.get("zensus_einwohner", {}).get("zeit", "")[:10]
    zl = {"quelle": "Zensus 2022, eigene Aggregation", "datenhalter": "Statistische Ämter des Bundes und der Länder", "lizenz": Z["lizenz"],
          "lizenz_url": Z["lizenz_url"], "namensnennung": Z["attribution"], "geheimhaltung": Z["geheimhaltung"],
          "quell_url": Z["quell_url"], "jahre": Z["stichtag"][:4], "raumebenen": "ortsbezirk;gemeinde"}
    m = Z["metatext"]
    ind = [
        dict(indikator_id="zensus_einwohner", name="Einwohner", thema="Bevölkerung", einheit="Personen", typ="anzahl", metatext=m["anzahl"], abrufdatum=za),
        dict(indikator_id="zensus_unter18", name="Einwohner unter 18 Jahren", thema="Bevölkerung", einheit="Personen", typ="anzahl", metatext=m["anzahl"]),
        dict(indikator_id="zensus_18bis64", name="Einwohner von 18 bis 64 Jahren", thema="Bevölkerung", einheit="Personen", typ="anzahl", metatext=m["anzahl"]),
        dict(indikator_id="zensus_ab65", name="Einwohner ab 65 Jahren", thema="Bevölkerung", einheit="Personen", typ="anzahl", metatext=m["anzahl"]),
        dict(indikator_id="zensus_anteil_unter18", name="Anteil unter 18 Jahren", thema="Bevölkerung", einheit="%", typ="anteil",
             zaehler_id="zensus_unter18", nenner_id="", metatext=m["anteil"] + " Nenner ist die Summe der fünf Altersklassen."),
        dict(indikator_id="zensus_anteil_ab65", name="Anteil ab 65 Jahren", thema="Bevölkerung", einheit="%", typ="anteil",
             zaehler_id="zensus_ab65", nenner_id="", metatext=m["anteil"] + " Nenner ist die Summe der fünf Altersklassen."),
        dict(indikator_id="zensus_durchschnittsalter", name="Durchschnittsalter", thema="Bevölkerung", einheit="Jahre", typ="mittelwert",
             metatext=m["mittelwert"]),
        dict(indikator_id="zensus_wohnungen", name="Wohnungen", thema="Wohnen", einheit="Wohnungen", typ="anzahl", metatext=m["anzahl"]),
        dict(indikator_id="zensus_wohnungen_efh_zfh", name="Wohnungen in Ein- und Zweifamilienhäusern", thema="Wohnen", einheit="Wohnungen",
             typ="anzahl", metatext=m["anzahl"]),
        dict(indikator_id="zensus_anteil_wohnungen_efh_zfh", name="Anteil der Wohnungen in Ein- und Zweifamilienhäusern", thema="Wohnen",
             einheit="%", typ="anteil", zaehler_id="zensus_wohnungen_efh_zfh", nenner_id="",
             metatext=m["anteil"] + " Gezählt nach der Bauart des Gebäudes (freistehend, Doppelhaushälfte, Reihenhaus); Nenner ist die Summe aller"
             " Gebäudetypen einschließlich Gebäuden anderer Bauart. Die amtliche Gemeindetabelle zählt dagegen nach der Zahl der Wohnungen im"
             " Gebäude, der Wegweiser Kommune nach der Fortschreibung auf Basis des Zensus 2011; die Werte sind deshalb nicht gleich."),
    ] if zensus_da else []
    for i in ind:
        i.setdefault("abrufdatum", za)
        for k, v in zl.items():
            i.setdefault(k, v)
    for fu, x in ww_meta.items():
        jahre = x.get("years") or []
        ind.append({"indikator_id": f"ww_{fu}", "name": x["name"], "thema": "Vergleich (Wegweiser Kommune)", "einheit": x.get("unit"),
                    "typ": WW["typen"].get(fu, "quote"), "raumebenen": "gemeinde;kreis", "jahre": f"{min(jahre)}-{max(jahre)}" if jahre else "",
                    "quelle": "Wegweiser Kommune", "datenhalter": x.get("source"), "lizenz": WW["lizenz"], "lizenz_url": WW["lizenz_url"],
                    "namensnennung": WW["namensnennung"], "metatext": " ".join(t for t in (x.get("explanation"), x.get("calculation") and f"Berechnung: {x['calculation']}") if t),
                    "geheimhaltung": "", "quell_url": f"https://www.wegweiser-kommune.de/data-api/rest/indicator/get/{fu}",
                    "abrufdatum": abruf.get(f"wegweiser_{fu}", {}).get("zeit", "")[:10]})
    if ind:
        _schreiben("indikatoren.tsv", INDIKATOR_SPALTEN, ind)

    # Abrufprotokoll und Datenstand
    _schreiben("audit_abruf.tsv", ["quelle", "url", "zeit", "http_status", "zeilen", "sha256"],
               [abruf[k] for k in sorted(abruf)])
    (OUT / "meta.json").write_text(json.dumps({
        "vertrag_version": S["vertrag_version"],
        "datenstand": {"zensus": Z["stichtag"], "wegweiser": max((z["jahr"] for z in ww_zeilen), default=None)},
        "wegweiser_datenstand": datenstand_ww,
        "abrufdatum": max((e.get("zeit", "")[:10] for e in abruf.values()), default=None),
        "veroeffentlichen": S["veroeffentlichen"],
        "lizenzstatus": "offen (dl-de/by-2-0, dl-de/zero-2.0, CC0 1.0)",
        "quellen": [
            {"name": "Zensus 2022, Gitterdaten", "url": Z["quell_url"], "lizenz": Z["lizenz"], "namensnennung": Z["attribution"]},
            {"name": "Wegweiser Kommune", "url": "https://www.wegweiser-kommune.de/open-data", "lizenz": WW["lizenz"],
             "namensnennung": WW["namensnennung"], "api_version": abruf.get("wegweiser_openapi", {}).get("info_version")},
            {"name": gq["quelle"], "url": "https://gds-srv.hessen.de/atomfeed/DigVGr-epsg25832-shp.zip", "lizenz": gq["lizenz"],
             "namensnennung": "© HVBG"}],
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"Strukturdaten: {len(zeilen_werte)} Werte, {len(ww_zeilen)} Vergleichswerte, {len(zeilen_zuo)} Zellen zugeordnet, "
          f"{sum(1 for z in zeilen_raum if not z['ziel'])} nicht zugeordnet, {len(gruende)} unter der Schwelle")
