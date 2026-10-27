"""Testdaten für den Vergleich Prüfseite (site/pruefen.js) ↔ tools/pruefen.py; alle Namen und Beträge erfunden.

  python3 tests/browser/pruef_fixture.py erzeugen ORDNER     Schlüssel, Register, Exportdateien; Referenzlauf mit Python
  python3 tests/browser/pruef_fixture.py veroeffentlichen ORDNER DATEI   Veröffentlichung der Prüfseite gegen Python
  python3 tests/browser/pruef_fixture.py vergleichen ORDNER BESTAND
      Bestand der Prüfseite mit Python öffnen und mit dem Referenzlauf vergleichen (gleiche Einträge, Hinweise,
      Vermieter-Schlüssel, Freigaben und Abfolge im Verlauf); gibt „gleich“ oder die Unterschiede aus
"""
import json
import shutil
from datetime import date
import sys
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import einladung  # noqa: E402
import pruefen  # noqa: E402
import pruefgruppe as pg  # noqa: E402

PW = "Vergleich nur zum Testen"


def zeit(i):
    return f"2026-10-2{i // 10}T10:{i % 10:02d}:00.000Z"


def erzeugen(o):
    o = Path(o)
    pub = pg.schluessel_erzeugen(o / "pg.json", PW, stufe="interaktiv")
    aus = einladung.ausgeben(1, o / "einladungen.tsv", 12, heute=date(2026, 10, 1))
    eid = aus[0][1]
    geb = [f["properties"]["id"] for f in json.loads((ROOT / "data" / "geo" / "hvgg" / "gebaeude.geojson").read_text(encoding="utf-8"))["features"][:12]]
    n = iter(range(100))

    def eig(g, kat, name=None, privat=None, **mehr):
        r = {"erfassung_id": str(uuid.uuid4()), "objekt": {"typ": "gebaeude", "id": g}, "kategorie": kat, "beleg_art": "ortskenntnis",
             "sicherheit": "wahrscheinlich", "vermietet": "ja", "erfasst_am": zeit(next(n)), "erfasser": eid, "app_version": "test", **mehr}
        if name:
            r["name_juristische_person"] = name
        if kat == "privat":
            r["vermieter_schluessel"] = "V-neu"
            if privat:
                r["name_privat_enc"] = {"alg": pg.ALG, "key_id": pub["key_id"], "ciphertext": pg.versiegeln(pub["public_key"], privat.encode())}
        return r

    def miete(g, eur, m2=80.0, **mehr):
        return {"angabe_id": str(uuid.uuid4()), "gebaeude_id": g, "nettokalt_eur": eur, "wohnflaeche_klasse": "80-99", "wohnflaeche_m2": m2,
                "baujahr_klasse": "1949-1978", "vertragsbeginn_jahr": 2018,
                "einwilligung": {"erteilt": True, "textversion": pg.STADT["wohnen_eigentum"]["erfassung"]["einwilligung"]["version"],
                                 "zeitpunkt": zeit(next(n))}, "erfasst_am": zeit(next(n)), "erfassungsweg": "selbst", **mehr}

    a = [eig(geb[0], "geno", "Probe-Wohnbau eG"), eig(geb[1], "geno", "probe-wohnbau  EG"), eig(geb[2], "kom", "Stadt (Probe)"),
         eig(geb[3], "privat", privat="Erika Probe"), eig(geb[4], "privat", privat="erika  probe"), eig(geb[5], "privat"), eig(geb[6], "unklar"),
         eig(geb[7], "kom", "Stadt (Probe)"), eig(geb[7], "kom", "Stadt (Probe)"),           # Dublette
         eig(geb[8], "kom", "Stadt (Probe)"), eig(geb[8], "geno", "Probe-Wohnbau eG"),      # abweichende Angaben
         eig(geb[9], "kom", "Stadt (Probe)", objekt={"typ": "gebaeude", "id": geb[9], "lage_hinweis": "Hof 3"})]  # Ziffer: abgewiesen
    b = [miete(geb[0], 650), miete(geb[0], 650), miete(geb[1], 512.5, 61.0, vermieter_schluessel="JP:Probe-Wohnbau eG"),
         miete(geb[2], 720, 75.0), miete(geb[3], 400, vermieter_schluessel="V-001")]                     # V-…: abgewiesen
    # genug Angaben für Median, Spanne und den Vergleich je juristischer Person (Veröffentlichen)
    b += [miete(geb[i % 4], 400 + 37 * i + 0.5, 70.0 + i, **({"vermieter_schluessel": "JP:Probe-Wohnbau eG"} if i < 6 else {}))
          for i in range(11)]
    kaputt = miete(geb[10], 500)
    kaputt["vertragsbeginn_jahr"] = "2018"                                                                 # Schema: abgewiesen
    fremd = eig(geb[11], "bund", "Bund (Probe)")

    def export(typ, recs, erfasser, name):
        e = [{"id": r.get("erfassung_id") or r.get("angabe_id"), "erstellt": r["erfasst_am"], "key_id": pub["key_id"],
              "ciphertext": pg.versiegeln(pub["public_key"], json.dumps(r).encode())} for r in recs]
        p = o / "exporte" / name
        p.parent.mkdir(exist_ok=True)
        p.write_text(json.dumps({"format": "wiz-stadtmonitor-erfassung", "version": 1, "typ": typ, "alg": pg.ALG, "erfasser": erfasser,
                                 "erstellt": zeit(99), "anzahl": len(e), "eintraege": e}), encoding="utf-8")
        return p

    dateien = [export("eigentum", a, eid, "eigentum_1.json"), export("miete", [*b, kaputt], eid, "mieten_1.json"),
               export("eigentum", [fremd], "E-00000000", "eigentum_fremd.json")]
    # Referenzlauf: einlesen, prüfen, zwei Freigaben
    ref = o / "ref"
    ar = pg.Arbeit(ref, pg.Schluessel(o / "pg.json", PW), "P-1")
    pruefen.einlesen(ar, dateien, o / "einladungen.tsv")
    pruefen.pruefen(ar)
    pruefen.freigeben(ar, alle=True)
    pruefen.freigeben(pg.Arbeit(ref, pg.Schluessel(o / "pg.json", PW), "P-2"), alle=True)
    print(json.dumps({"passphrase": PW, "dateien": [str(p) for p in dateien], "aufgenommen": 26, "abgewiesen": 4}))


def normiert(d):
    return {"eintraege": {i: {k: v for k, v in e.items() if k != "eingelesen"} for i, e in d["eintraege"].items()},
            "vermieter_naechste": d["vermieter_naechste"], "sperrliste": d.get("sperrliste", []),
            "verlauf": [(v["pruefer"], v["aktion"], v["datensatz"]) for v in d["verlauf"]]}


def vergleichen(o, bestand):
    o = Path(o)
    schl = pg.Schluessel(o / "pg.json", PW)
    ref = normiert(pg.Arbeit(o / "ref", schl, "P-1").d)
    ziel = o / "browser"
    ziel.mkdir(exist_ok=True)
    shutil.copy(bestand, ziel / "bestand.sealed")
    neu = normiert(pg.Arbeit(ziel, schl, "P-1").d)
    unterschiede = [k for k in ref if ref[k] != neu[k]]
    for i in set(ref["eintraege"]) | set(neu["eintraege"]):
        if ref["eintraege"].get(i) != neu["eintraege"].get(i):
            unterschiede.append(f"{i}: {ref['eintraege'].get(i)} != {neu['eintraege'].get(i)}")
    print("gleich" if not unterschiede else "\n".join(map(str, unterschiede)))


def veroeffentlichen(o, datei):
    """Python veröffentlicht aus einer Kopie des Referenzbestands; die Datei der Prüfseite wird übernommen; beide gleich?"""
    import veroeffentlichen as vo
    o = Path(o)
    shutil.copytree(o / "ref", o / "ref_pub")
    vo.veroeffentlichen(pg.Arbeit(o / "ref_pub", pg.Schluessel(o / "pg.json", PW), "P-1"), o / "py")
    vo.uebernehmen(datei, o / "seite")
    unterschiede = []
    for name in sorted(vo.DATEIEN):
        a, b = (json.loads((o / z / "data" / "wohnen" / name).read_text(encoding="utf-8")) for z in ("py", "seite"))
        if a != b:
            unterschiede.append(f"{name}: {json.dumps(a, ensure_ascii=False)[:600]} != {json.dumps(b, ensure_ascii=False)[:600]}")
    print("gleich" if not unterschiede else "\n".join(unterschiede))


if __name__ == "__main__":
    {"erzeugen": erzeugen, "vergleichen": vergleichen, "veroeffentlichen": veroeffentlichen}[sys.argv[1]](*sys.argv[2:])
