"""Generalprobe der Erfassung Wohnen und Eigentum (Issue 53): die ganze Kette einmal lokal, mit Wegwerf-Schlüssel und
erfundenen Testdaten, bevor der echte Schlüssel entsteht.

Zweck: Für die Stadt gibt es keinen Mietspiegel. Bevor echte Angaben erfasst werden, soll die Prüfgruppe sehen, dass jeder
Schritt auf ihrem Rechner funktioniert: Einrichten, Erfassen (wie die App), Einlesen, Freigabe zu zweit, Veröffentlichen,
Widerruf, Widerspruch, Schlüsselwechsel, Papiersicherung.

Aufruf aus dem Wurzelverzeichnis des Repositorys:
  python tools/generalprobe.py [--schnell] [--behalten]
Alles entsteht in einem temporären Ordner außerhalb des Repositorys und wird danach gelöscht (mit --behalten nicht).
config/stadt.json bleibt unverändert; die Probe arbeitet mit einer Kopie. Alle Namen und Beträge sind erfunden.
"""
import argparse
import json
import shutil
import sys
import tempfile
import traceback
import uuid
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

PW = "Generalprobe nur zum Testen"  # Wegwerf-Passphrase, nie für den echten Schlüssel


class Probe:
    def __init__(self, ordner, stufe):
        import pruefgruppe as pg  # noqa: PLC0415 – erst nach der Paketprüfung
        self.pg, self.ordner, self.stufe = pg, Path(ordner), stufe
        self.stadt = self.ordner / "stadt.json"
        shutil.copy2(pg.ROOT / "config" / "stadt.json", self.stadt)
        self.schl_datei = self.ordner / "schluessel" / "pg.json"
        self.register = self.ordner / "einladungen.tsv"
        self.druck = self.ordner / "druck"
        geb = json.loads((pg.ROOT / "data" / "geo" / "hvgg" / "gebaeude.geojson").read_text(encoding="utf-8"))["features"]
        je = {}
        for f in geb:
            je.setdefault(f["properties"].get("o"), []).append(f["properties"]["id"])
        self.ortsteil, self.geb = next((o, ids) for o, ids in je.items() if o and len(ids) >= 10)

    def jetzt(self):
        return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")

    def export(self, typ, recs, erfasser):
        """Exportdatei wie aus erfassen.js (Format wiz-stadtmonitor-erfassung, Version 1), versiegelt mit dem Probeschlüssel."""
        pg = self.pg
        eintraege = [{"id": r.get("erfassung_id") or r.get("angabe_id"), "erstellt": r["erfasst_am"], "key_id": self.pub["key_id"],
                      "ciphertext": pg.versiegeln(self.pub["public_key"], json.dumps(r).encode())} for r in recs]
        p = self.ordner / "exporte" / f"{typ}_{erfasser}_{uuid.uuid4().hex[:6]}.bin"
        p.parent.mkdir(exist_ok=True)
        p.write_text(json.dumps({"format": "wiz-stadtmonitor-erfassung", "version": 1, "typ": typ, "alg": pg.ALG, "erfasser": erfasser,
                                 "erstellt": self.jetzt(), "anzahl": len(eintraege), "eintraege": eintraege}), encoding="utf-8")
        return p

    def eigentum(self, gid, kategorie, name=None):
        r = {"erfassung_id": str(uuid.uuid4()), "objekt": {"typ": "gebaeude", "id": gid}, "kategorie": kategorie, "beleg_art": "ortskenntnis",
             "sicherheit": "wahrscheinlich", "vermietet": "ja", "erfasst_am": self.jetzt(), "erfasser": self.eid, "app_version": "generalprobe"}
        if kategorie == "privat":
            r["vermieter_schluessel"] = "V-neu"
        if name:
            r["name_juristische_person"], r["vermieter_schluessel"] = name, f"JP:{name}"
        return r

    def miete(self, gid, eur):
        F = json.loads(self.stadt.read_text(encoding="utf-8"))["wohnen_eigentum"]["erfassung"]
        return {"angabe_id": str(uuid.uuid4()), "gebaeude_id": gid, "nettokalt_eur": eur, "wohnflaeche_klasse": "60-79", "wohnflaeche_m2": 65.0,
                "baujahr_klasse": "1949-1978", "vertragsbeginn_jahr": 2018,
                "einwilligung": {"erteilt": True, "textversion": F["einwilligung"]["version"], "zeitpunkt": self.jetzt()},
                "erfasst_am": self.jetzt(), "erfassungsweg": "selbst"}

    # --- Schritte: je ein kurzer Satz, was geprüft wird; ein Fehler bricht nur den Schritt ab ------------------------
    def s1_schluessel(self):
        import einrichten  # noqa: PLC0415
        self.pub, blatt = einrichten.schluessel(self.schl_datei, self.druck, PW, self.stadt, stufe=self.stufe)
        F = json.loads(self.stadt.read_text(encoding="utf-8"))["wohnen_eigentum"]["erfassung"]
        assert F["schluessel"] == self.pub and blatt.exists()
        return f"Schlüssel {self.pub['key_id']} erzeugt, öffentlicher Teil in der Kopie von stadt.json, Druckblatt erstellt"

    def s2_papiersicherung(self):
        zeilen, _ = self.pg.ausdruck_zeilen(self.schl_datei)
        ziel = self.pg.aus_ausdruck("\n".join(zeilen), self.ordner / "zurueck" / "pg.json")
        assert self.pg.Schluessel(ziel, PW).key_id == self.pub["key_id"]
        return f"{len(zeilen)} Zeilen gedruckt und wiederhergestellt; mit der Passphrase lesbar"

    def s3_codes(self):
        import einrichten  # noqa: PLC0415
        aus, _ = einrichten.codes(2, self.register, self.druck, self.stadt)
        (self.code, self.eid, _), (_, self.eid2, _) = aus
        F = json.loads(self.stadt.read_text(encoding="utf-8"))["wohnen_eigentum"]["erfassung"]
        assert len(F["einladungen"]) == 2 and self.code not in self.register.read_text(encoding="utf-8")
        return f"2 Codes ausgegeben ({self.eid}, {self.eid2}); im Register nur ID und Hash"

    def s4_erfassen(self):
        g = self.geb
        self.a = [self.eigentum(g[0], "geno", "Probe-Wohnbau eG"), self.eigentum(g[1], "geno", "Probe-Wohnbau eG"),
                  self.eigentum(g[2], "kom", "Stadt (Probe)"), self.eigentum(g[3], "privat"), self.eigentum(g[4], "privat"),
                  self.eigentum(g[5], "unklar")]
        self.b = [self.miete(g[i % 2], 420 + 15 * i) for i in range(6)]
        self.exporte = [self.export("eigentum", self.a, self.eid), self.export("miete", self.b, self.eid)]
        return f"{len(self.a)} Eigentumseinträge und {len(self.b)} Mietangaben in {self.ortsteil} versiegelt exportiert"

    def arbeit(self, pruefer):
        return self.pg.Arbeit(self.ordner / "arbeit", self.pg.Schluessel(self.schl_datei, PW), pruefer)

    def s5_einlesen(self):
        import pruefen  # noqa: PLC0415
        fremd = self.export("eigentum", [self.eigentum(self.geb[6], "bund")], "E-00000000")
        neu, zeilen = pruefen.einlesen(self.arbeit("P-1"), [*self.exporte, fremd], self.register)
        ab = [z for z in zeilen if z[2].startswith("abgewiesen")]
        assert neu == len(self.a) + len(self.b), zeilen
        assert len(ab) == 1 and "Einladungsregister" in ab[0][2], ab
        return f"{neu} aufgenommen; Export einer unbekannten Erfasser-ID abgewiesen"

    def s6_pruefen_freigeben(self):
        import pruefen  # noqa: PLC0415
        pfad, _ = pruefen.pruefen(self.arbeit("P-1"))
        n1 = pruefen.freigeben(self.arbeit("P-1"), alle=True)
        ar = self.arbeit("P-2")
        n2 = pruefen.freigeben(ar, alle=True)
        frei = sum(1 for e in ar.eintraege.values() if ar.freigegeben(e))
        assert frei == len(self.a) + len(self.b) and n1 == n2 == frei
        return f"Prüfliste {pfad.name}; {frei} Einträge von P-1 und P-2 freigegeben"

    def s7_veroeffentlichen(self):
        import veroeffentlichen as vo  # noqa: PLC0415
        aus = vo.veroeffentlichen(self.arbeit("P-1"), self.ordner / "repo", cfg={"mietangaben_aktiv": True})
        karte = aus["eigentum_gebaeude.geojson"]
        ids = {f["properties"]["id"] for f in karte["features"]}
        assert self.geb[3] not in ids and self.geb[4] not in ids  # privat nie je Gebäude
        assert all(d["lizenz"] == "CC BY 4.0" for d in aus.values())
        zellen = [z for z in aus["mieten_aggregiert.json"].get("zellen", []) if z.get("n")]
        return f"{len(aus)} Dateien; {len(ids)} Gebäude mit Kategorie, privat nur als Anzahl; {len(zellen)} Mietzelle(n) ab 5 Angaben"

    def s8_widerruf_widerspruch(self):
        import pruefen  # noqa: PLC0415
        ar = self.arbeit("P-1")
        c = self.b[0]["angabe_id"].replace("-", "")[:8].upper()
        i = pruefen.code_zu_id(ar, f"{c[:4]}-{c[4:]}")
        pruefen.loeschen(ar, i, "Widerruf (Generalprobe)")
        weg, _ = pruefen.widerspruch(self.arbeit("P-1"), [self.geb[3]], "Widerspruch (Generalprobe)")
        neu, zeilen = pruefen.einlesen(self.arbeit("P-1"), [self.export("eigentum", [self.eigentum(self.geb[3], "privat")], self.eid)], self.register)
        assert i not in self.arbeit("P-1").eintraege and neu == 0, zeilen
        return f"Mietangabe per Widerrufscode gelöscht; Widerspruch: {len(weg)} Eintrag gelöscht, Gebäude gesperrt"

    def s9_code_widerrufen(self):
        import einrichten  # noqa: PLC0415
        n = einrichten.widerrufen(self.eid2, self.register, self.stadt)
        F = json.loads(self.stadt.read_text(encoding="utf-8"))["wohnen_eigentum"]["erfassung"]
        assert n == 1 and len(F["einladungen"]) == 1
        return f"Code {self.eid2} widerrufen, Hash aus der Kopie von stadt.json entfernt"

    def s10_schluesselwechsel(self):
        import pruefen  # noqa: PLC0415
        neu = pruefen.schluessel_wechsel(self.arbeit("P-1"), stufe=self.stufe)
        ar = self.arbeit("P-1")
        assert ar.schl.key_id == neu["key_id"] and ar.eintraege
        return f"neuer Schlüssel {neu['key_id']}; Bestand neu versiegelt und lesbar; Wechsel fällig: {pruefen.wechsel_faellig(ar.schl)}"


def pakete():
    fehlt = []
    for modul, paket in (("nacl", "pynacl"), ("jsonschema", "jsonschema"), ("segno", "segno")):
        try:
            __import__(modul)
        except ImportError:
            fehlt.append(paket)
    if sys.version_info < (3, 10):
        fehlt.append("Python 3.10 oder neuer")
    return fehlt


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--schnell", action="store_true", help="schwächere Schlüsselableitung (nur für die Probe)")
    ap.add_argument("--behalten", action="store_true", help="Probeordner nicht löschen")
    a = ap.parse_args(argv)
    fehlt = pakete()
    if fehlt:
        print(f"FEHLT  {', '.join(fehlt)}: python -m pip install -r requirements.txt -r tools/requirements.txt")
        return 1
    ordner = Path(tempfile.mkdtemp(prefix="wiz-generalprobe-"))
    print(f"Generalprobe in {ordner} (erfundene Testdaten, Wegwerf-Schlüssel)")
    probe, fehler = Probe(ordner, "interaktiv" if a.schnell else "moderat"), 0
    try:
        for name in sorted((n for n in dir(Probe) if n.startswith("s") and n[1:].split("_")[0].isdigit()), key=lambda n: int(n[1:].split("_")[0])):
            titel = name.split("_", 1)[1].replace("_", " ")
            try:
                print(f"ok     {titel}: {getattr(probe, name)()}")
            except Exception as e:  # noqa: BLE001 – jeder Fehler wird gemeldet, die Probe läuft weiter
                fehler += 1
                print(f"FEHLER {titel}: {type(e).__name__}: {e}")
                traceback.print_exc(limit=2, file=sys.stderr)
    finally:
        if a.behalten:
            print(f"Probeordner bleibt: {ordner}")
        else:
            shutil.rmtree(ordner, ignore_errors=True)
    print("Generalprobe bestanden." if not fehler else f"{fehler} Schritt(e) fehlgeschlagen.")
    return 1 if fehler else 0


if __name__ == "__main__":
    sys.exit(main())
