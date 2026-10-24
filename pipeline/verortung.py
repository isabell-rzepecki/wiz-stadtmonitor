"""Stufe B: regelbasierte Verortung aus dem Titel eines Tagesordnungspunkts.

methode_detail (Audit) und method (Seite):
- B-gemarkung   „Gemarkung X“ / „Gem. X“                         → Ortsteil der Gemarkung (Fläche, kein Punkt)
- B-flurstueck  „Gem. X, Fl. Y, Flst. Z“                          → Flurstückspunkt (Suchdienst HVBG, Ebene flst)
- B-strasse     Straßen- oder Lagename aus dem Verzeichnis        → Bezugspunkt der Straße in ihrer Gemarkung
- B-ortsteil    Ortsteilname als ganzes Wort (nicht „Ermschwerder …“) → Ortsteil (Fläche, kein Punkt)
Mehrdeutige Straßennamen (in mehreren Gemarkungen) werden über das beratende Gremium (Ortsbeirat) oder einen im
Titel genannten Ortsteil bzw. eine Gemarkung eingegrenzt; sonst bleiben sie ohne Ort und stehen im Audit als
„mehrdeutig“. Hausnummern werden nicht ausgewertet (keine Wohnadressen).
"""
import json
import re
import time
import urllib.parse

from pyproj import Transformer

from . import config, lage, net

STRASSENWORT = re.compile(r"(straße|weg|gasse|platz|allee|ring|pfad|steig|stieg|ufer|brücke|tor|markt|hof)$", re.I)
# „Gemarkung X, Flur 2, Flurstück 169/3“, auch „Flur. 2“, „Flurstücke 169 und 171“ (erstes), „Flurstück Nr. 169“
FLST = re.compile(r"Gem(?:arkung|\.)\s+([A-ZÄÖÜ][\wäöüß-]+(?:-[A-ZÄÖÜ][\wäöüß-]+)?),?\s+Fl(?:ur\.?|\.)\s*(\d+),?\s+"
                  r"Fl(?:urstücke?|st\.?)\s*(?:Nr\.\s*)?(\d+)(?:/(\d+))?")
GEMARKUNG = re.compile(r"Gem(?:arkung|\.)\s+([A-ZÄÖÜ][\wäöüß]+(?:-[A-ZÄÖÜ][\wäöüß]+)?)")
# Flurstückspunkte (dl-de/zero-2.0) im Repository, damit die Verortung nicht von der Erreichbarkeit des Dienstes abhängt
FLST_CACHE = config.GEO / "dl-de-zero" / "flurstuecke.json"
_DIENST_AUS = False
AUSSCHLUSS = set(config.STADT.get("verortung", {}).get("ausschluss_namen", []))


def normalisieren(text):
    t = re.sub(r"(?i)str\.(?=\s|/|,|$)", "straße", text)
    t = re.sub(r"(?i)strasse", "straße", t)
    return re.sub(r"\s+", " ", t)


def basisname(name):
    """„Bahnhofstraße (Gertenbach)“ → („Bahnhofstraße“, „Gertenbach“)"""
    m = re.match(r"^(.*?)\s*\(([^)]+)\)$", name)
    return (m.group(1), m.group(2)) if m else (name, None)


class Verzeichnis:
    def __init__(self, path=lage.VERZEICHNIS):
        d = json.loads(path.read_text(encoding="utf-8"))["namen"] if path.exists() else {}
        self.namen = {}
        for name, je in d.items():
            base, _ = basisname(name)
            # einzelne Wörter nur, wenn sie wie ein Straßenname enden (sonst zu viele Fehltreffer: „Allenbach“)
            if base in AUSSCHLUSS or len(base) < 6 or (" " not in base and "-" not in base and not STRASSENWORT.search(base)):
                continue
            ziel = self.namen.setdefault(base, {})
            for gk, v in je.items():
                ziel[gk] = v
        # längste Namen zuerst, damit „Ermschwerder Landstraße“ vor „Ermschwerder Straße“ greift
        self.muster = [(n, re.compile(rf"(?<![\wäöüß]){re.escape(n)}(?![\wäöüß])", re.I)) for n in sorted(self.namen, key=len, reverse=True)]

    def finde(self, titel):
        """[(name, span)] ohne Überlappungen"""
        t, out, belegt = normalisieren(titel), [], []
        for n, rx in self.muster:
            for m in rx.finditer(t):
                if any(a < m.end() and m.start() < b for a, b in belegt):
                    continue
                belegt.append(m.span())
                out.append((n, m.span()))
        return out, t


def _ortsteil(name=None, gk=None):
    for o in config.STADT["ortsteile"]:
        if name and (name == o["name"] or name == o.get("gemarkung") or name in o.get("varianten", [])):
            return o
        if gk and gk == o.get("gemarkung_nr"):
            return o
    return None


def flurstueck(gk, flur, zaehler, nenner):
    """Punkt eines Flurstücks (lon, lat) über den Suchdienst; Ergebnisse zwischengespeichert. Ist der Dienst nicht
    erreichbar, bleibt das Flurstück für diesen Lauf ohne Punkt (kein Eintrag im Zwischenspeicher)."""
    global _DIENST_AUS
    key = f"{gk}-{flur}-{zaehler}-{nenner or ''}"
    cache = json.loads(FLST_CACHE.read_text(encoding="utf-8")) if FLST_CACHE.exists() else {}
    if key in cache:
        return cache[key]
    if _DIENST_AUS:
        return None
    teile = [("FS_GKNR", gk), ("FS_FLNR", f"{int(flur):03d}"), ("FS_FSZ", f"{int(zaehler):05d}")]
    if nenner:
        teile.append(("FS_FSN", f"{int(nenner):03d}"))
    flt = "<Filter><And>" + "".join(f"<PropertyIsEqualTo><PropertyName>{k}</PropertyName><Literal>{v}</Literal></PropertyIsEqualTo>" for k, v in teile) + "</And></Filter>"
    url = f"{lage.URL}?" + urllib.parse.urlencode({"SERVICE": "WFS", "VERSION": "1.1.0", "REQUEST": "GetFeature", "TYPENAME": "flst", "FILTER": flt})
    try:
        body, _ = net.get(url, tries=2)
        grund = net.pruefen("flst.gml", body)
        if grund:  # Fehlerbericht: nicht als „Flurstück nicht gefunden“ merken
            raise ValueError(grund)
        pos = re.search(rb"<gml:pos>([\d.]+) ([\d.]+)</gml:pos>", body)  # EPSG:31467, Hochwert zuerst
        res = None
        if pos:
            lon, lat = Transformer.from_crs("EPSG:31467", "EPSG:4326", always_xy=True).transform(float(pos.group(2)), float(pos.group(1)))
            res = {"lon": round(lon, 6), "lat": round(lat, 6)}
        time.sleep(0.3)
    except Exception:
        _DIENST_AUS = True
        return None
    cache[key] = res
    FLST_CACHE.parent.mkdir(parents=True, exist_ok=True)
    FLST_CACHE.write_text(json.dumps(dict(sorted(cache.items())), ensure_ascii=False, indent=0), encoding="utf-8")
    return res


def stufe_b(titel, sitzung, verz, quelle_pdf):
    """(locations, audit_zeilen) für einen Titel; audit_zeilen mit methode_detail, mehrdeutig, treffer, fundstelle."""
    locs, aud = [], []
    gremium_ot = sitzung.get("ortsteil")

    def add(level, name, ortsteil, method, detail, conf, evidence, lon=None, lat=None, mehrdeutig=False):
        if not any(l["name"] == name and l["level"] == level for l in locs):
            loc = {"level": level, "name": name, "ortsteil": ortsteil, "stage": "B", "method": method, "confidence": conf,
                   "evidence": evidence, "source_pdf": quelle_pdf}
            if lon is not None:
                loc.update(lon=lon, lat=lat)
            locs.append(loc)
        aud.append({"methode_detail": detail, "mehrdeutig": "ja" if mehrdeutig else "nein", "treffer": name, "ortsteil": ortsteil or "",
                    "konfidenz": conf, "fundstelle": evidence})

    # Flurstücke und Gemarkungen
    genannte = set()
    for m in FLST.finditer(titel):
        o = _ortsteil(name=m.group(1))
        if not o:
            continue
        genannte.add(o["name"])
        p = flurstueck(o["gemarkung_nr"], m.group(2), m.group(3), m.group(4))
        if p:
            add("flurstueck", f"Gemarkung {o['gemarkung']}, Flur {m.group(2)}, Flurstück {m.group(3)}{'/' + m.group(4) if m.group(4) else ''}",
                o["name"], "flurstueck", "B-flurstueck", "hoch", m.group(0), p["lon"], p["lat"])
    for m in GEMARKUNG.finditer(titel):
        o = _ortsteil(name=m.group(1))
        if o:
            genannte.add(o["name"])
            if not any(l["ortsteil"] == o["name"] for l in locs):
                add("ortsteil", o["name"], o["name"], "gemarkung", "B-gemarkung", "mittel", m.group(0))

    # Straßen- und Lagenamen
    treffer, norm = verz.finde(titel)
    spans = [s for _, s in treffer]
    # Ortsteilnamen als ganze Wörter außerhalb von Straßennamen
    for o in config.STADT["ortsteile"]:
        if not o["ortsbezirk"]:
            continue
        for n in [o["name"], *o.get("varianten", [])]:
            for m in re.finditer(rf"(?<![\wäöüß]){re.escape(n)}(?![\wäöüß])", norm):
                if any(a <= m.start() < b for a, b in spans):
                    continue
                genannte.add(o["name"])
                if not any(l["ortsteil"] == o["name"] for l in locs):
                    add("ortsteil", o["name"], o["name"], "ortsteil_name", "B-ortsteil", "mittel", m.group(0))
    # Gemarkungen eindeutiger Straßen im selben Titel grenzen mehrdeutige ein („Brückenstraße und Ermschwerder Straße“)
    eindeutig_gk = {next(iter(verz.namen[n])) for n, _ in treffer if len(verz.namen[n]) == 1}
    for name, span in treffer:
        je = verz.namen[name]
        kand = {gk: v for gk, v in je.items()}
        mehr = len(kand) > 1
        if mehr:
            eingegrenzt = {gk: v for gk, v in kand.items() if (_ortsteil(gk=gk) or {}).get("name") in (genannte | {gremium_ot})}
            if len(eingegrenzt) != 1:
                eingegrenzt = {gk: v for gk, v in kand.items() if gk in eindeutig_gk}
            if len(eingegrenzt) == 1:
                kand = eingegrenzt
        evidence = norm[span[0]:span[1]]
        if len(kand) == 1:
            gk, v = next(iter(kand.items()))
            o = _ortsteil(gk=gk)
            add("strasse", name, o["name"] if o else None, "strasse" if not mehr else "strasse+ortsteil",
                "B-strasse", "mittel", evidence, v["lon"], v["lat"], mehrdeutig=mehr)
        else:
            aud.append({"methode_detail": "B-strasse", "mehrdeutig": "ja", "treffer": name,
                        "ortsteil": ", ".join(sorted(filter(None, ((_ortsteil(gk=gk) or {}).get("name") for gk in kand)))),
                        "konfidenz": "", "fundstelle": evidence})
    return locs, aud
