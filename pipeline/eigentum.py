"""Gebäude und Eigentum: was öffentlich darstellbar ist.

- Gebäude für öffentliche Zwecke aus ALKIS vereinfacht (HVBG, Nutzung ohne Einschränkung). Der Dienst liefert per
  GET mit Filter nur eine Sperrseite, deshalb GetFeature als POST mit Filter auf Gemeinde und Gebäudefunktion. Das
  Ergebnis wird als GeoJSON (EPSG:4326) in den Zwischenspeicher der weiteren Kartenebenen gelegt (umwelt.py).
- Städtische Gesellschaften und Eigenbetriebe aus dem Beteiligungsbericht (§ 123a HGO): Name, Rechtsform,
  Gegenstand, Anteil der Stadt; Pflicht- oder freiwillige Angabe. Personen (Geschäftsführung, Aufsichtsrat),
  Anschriften und Kontaktdaten werden nicht übernommen.
Privateigentum und kommunale Liegenschaften werden nicht dargestellt (config/stadt.json, eigentum.grenzen).
"""
import hashlib
import json
import re
import subprocess
import time
from datetime import date

from pyproj import Transformer

from . import audit, config, net, umwelt

E = config.STADT["eigentum"]
RAW = config.RAW / "eigentum"
OUT = config.EXPORT / "eigentum.json"
GEBAEUDE = umwelt.RAW / "gebaeude_oeffentlich.geojson"
ALTER = 30 * 86400

ANFRAGE = """<wfs:GetFeature service="WFS" version="2.0.0" count="5000" xmlns:wfs="http://www.opengis.net/wfs/2.0"
 xmlns:fes="http://www.opengis.net/fes/2.0" xmlns:ave="http://repository.gdi-de.org/schemas/adv/produkt/alkis-vereinfacht/2.0">
 <wfs:Query typeNames="ave:GebaeudeBauwerk"><fes:Filter><fes:And>
  <fes:PropertyIsEqualTo><fes:ValueReference>ave:gmdschl</fes:ValueReference><fes:Literal>{gmde}</fes:Literal></fes:PropertyIsEqualTo>
  <fes:PropertyIsEqualTo><fes:ValueReference>ave:funktion</fes:ValueReference><fes:Literal>{funktion}</fes:Literal></fes:PropertyIsEqualTo>
 </fes:And></fes:Filter></wfs:Query></wfs:GetFeature>"""


def _ringe(poly, utm):
    def ring(t):
        z = [float(x) for x in t.split()]
        return [[round(c, 6) for c in utm(x, y)] for x, y in zip(z[0::2], z[1::2])]
    ext = re.search(r"<gml:exterior>.*?<gml:posList[^>]*>(.*?)</gml:posList>", poly, re.S)
    return [ring(ext.group(1))] + [ring(i) for i in re.findall(r"<gml:interior>.*?<gml:posList[^>]*>(.*?)</gml:posList>", poly, re.S)] if ext else None


def gebaeude_geojson(gml):
    """GeoJSON (EPSG:4326) aus der GML-Antwort; Eigenschaften: Funktion und Aktualität."""
    utm = Transformer.from_crs("EPSG:25832", "EPSG:4326", always_xy=True).transform
    feats = []
    for f in re.findall(r"<GebaeudeBauwerk\b.*?</GebaeudeBauwerk>", gml, re.S):
        polys = [r for r in (_ringe(p, utm) for p in re.findall(r"<gml:Polygon\b.*?</gml:Polygon>", f, re.S)) if r]
        if not polys:
            continue
        funktion = re.search(r"<funktion>([^<]*)</funktion>", f)
        feats.append({"type": "Feature", "properties": {"funktion": funktion.group(1) if funktion else None},
                      "geometry": {"type": "MultiPolygon", "coordinates": polys}})
    return {"type": "FeatureCollection", "features": feats}


def fetch():
    GEBAEUDE.parent.mkdir(parents=True, exist_ok=True)
    if not (GEBAEUDE.exists() and time.time() - GEBAEUDE.stat().st_mtime < ALTER):
        body = ANFRAGE.format(gmde=config.STADT["stadt"]["gemeindeschluessel"], funktion=E["alkis_funktion"]).encode("utf-8")
        try:
            gml = net.post(E["alkis_wfs"], body)
            gj = gebaeude_geojson(gml.decode("utf-8"))
            GEBAEUDE.write_text(json.dumps(gj, ensure_ascii=False), encoding="utf-8")
            audit.abruf("alkis_gebaeude", E["alkis_wfs"] + " (POST)", 200, len(gml), hashlib.sha256(gml).hexdigest(), len(gj["features"]), "")
        except Exception as e:
            audit.abruf("alkis_gebaeude", E["alkis_wfs"] + " (POST)", getattr(e, "code", ""), "", "", "", str(e)[:200])
    RAW.mkdir(parents=True, exist_ok=True)
    ziel = RAW / "beteiligungsbericht.pdf"
    if not (ziel.exists() and time.time() - ziel.stat().st_mtime < ALTER):
        try:
            body, _ = net.get(E["beteiligungsbericht"]["url"], tries=2)
            ziel.write_bytes(body)
            audit.abruf("beteiligungsbericht", E["beteiligungsbericht"]["url"], 200, len(body), hashlib.sha256(body).hexdigest(), "", "")
        except Exception as e:
            audit.abruf("beteiligungsbericht", E["beteiligungsbericht"]["url"], getattr(e, "code", ""), "", "", "", str(e)[:200])


def _feld(block, name, naechste):
    """Text eines Felds der Steckbrief-Tabelle bis zum nächsten bekannten Feld (rechte Spalte)."""
    m = re.search(rf"^\s*{name}\s{{2,}}(.*?)(?=^\s*(?:{naechste})|\Z)", block, re.S | re.M)
    if not m:
        return None
    zeilen = [re.sub(r"^\s{20,}", "", z).strip() for z in m.group(1).split("\n")]
    return re.sub(r"\s+", " ", " ".join(z for z in zeilen if z)).strip()


def gesellschaften(text):
    """[{abschnitt, name, rechtsform, gegenstand, gesellschafter, pflicht}] aus dem Beteiligungsbericht (pdftotext -layout)."""
    teile = re.split(r"^\s*(\d)\.(\d{1,2})\.\s+(.+?)\s*$", text, flags=re.M)
    out = []
    for i in range(1, len(teile) - 3, 4):
        kap, nr, titel, block = teile[i], teile[i + 1], teile[i + 2], teile[i + 3]
        if kap not in ("3", "4") or "Anschrift" not in block[:3000] or "...." in titel:
            continue
        felder = "Rechtsform|Gegenstand des Unternehmens|Beurkundung|Handels|Stammkapital|Geschäftsjahr|Gesellschafter|Mitglieder|Aufsichtsrat|Geschäftsführung|Jahresabschluss|Organe|Verbandsversammlung|Vorstand|Gründung"
        rechtsform = _feld(block, "Rechtsform", felder)
        gegenstand = _feld(block, "Gegenstand des Unternehmens", felder)
        gesell = _feld(block, "Gesellschafter", felder + "|Abschlussprüfer|Beteiligungen")
        # nur Gesellschafter (Institutionen); Organe und Personen danach abschneiden
        gesell = re.split(r"\s*(?:Aufsichtsrat\w*|Vors\.|Betriebsleit\w*|Geschäftsführ\w*|Prokura|\*\))", gesell or "")[0].strip() or None
        satz = re.split(r"(?<=[a-zäöüß)])\.\s", gegenstand or "")[0].strip().rstrip(".")
        out.append({"abschnitt": f"{kap}.{nr}", "name": re.sub(r"\s+", " ", titel), "rechtsform": rechtsform,
                    "gegenstand": satz + "." if satz else None, "gesellschafter": gesell, "pflicht": kap == "3"})
    return out


def build():
    pdf = RAW / "beteiligungsbericht.pdf"
    liste = []
    if pdf.exists():
        text = subprocess.run(["pdftotext", "-layout", str(pdf), "-"], capture_output=True, text=True).stdout
        liste = gesellschaften(text)
    elif OUT.exists():
        liste = json.loads(OUT.read_text(encoding="utf-8")).get("gesellschaften", [])
    daten = {"generated_at": date.today().isoformat(), "bericht": E["beteiligungsbericht"], "gesellschaften": liste, "grenzen": E["grenzen"]}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(daten, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    audit.tabelle("beteiligungsbericht.tsv", ["abschnitt", "name", "rechtsform", "gesellschafter", "pflicht"], liste)
    n_geb = len(json.loads(GEBAEUDE.read_text(encoding="utf-8"))["features"]) if GEBAEUDE.exists() else 0
    print(f"Eigentum: {len(liste)} Gesellschaften und Eigenbetriebe, {n_geb} Gebäude für öffentliche Zwecke")
    return daten
