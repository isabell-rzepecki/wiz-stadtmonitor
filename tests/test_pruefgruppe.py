"""Prüf- und Veröffentlichungsskripte (W5) mit synthetischen Daten: Einlesen, Vermieter-Schlüssel, Dubletten, Konflikte,
Vier-Augen-Freigabe, Veröffentlichung nach R1–R8 und Sperre gegen sensible Ausgaben. Alle Namen und Beträge sind erfunden."""
import json
import shutil
import sys
import tempfile
import unittest
import uuid
from pathlib import Path

from pipeline import config

sys.path.insert(0, str(config.ROOT / "tools"))
import pruefen  # noqa: E402
import pruefgruppe as pg  # noqa: E402
import veroeffentlichen as vo  # noqa: E402

GEB = json.loads((config.ROOT / "data" / "geo" / "hvgg" / "gebaeude.geojson").read_text(encoding="utf-8"))["features"]
G = [f["properties"]["id"] for f in GEB if f["properties"]["o"] == "gertenbach"][:12]
W = [f["properties"]["id"] for f in GEB if f["properties"]["o"] == "wendershausen"][:2]
PW = "Testpassphrase 2026"  # nur im Test
ZEIT = iter(f"2026-10-26T08:{m:02d}:00.000Z" for m in range(60))


def eigentum(gid, kategorie, **x):
    r = {"erfassung_id": str(uuid.uuid4()), "objekt": {"typ": "gebaeude", "id": gid, "gemarkung": "Gertenbach"}, "kategorie": kategorie,
         "beleg_art": "ortskenntnis", "sicherheit": "wahrscheinlich", "vermietet": "ja", "erfasst_am": next(ZEIT), "erfasser": "E-0000test",
         "app_version": "test"}
    if kategorie == "privat":
        r["vermieter_schluessel"] = "V-neu"
    if "name" in x:
        r["name_juristische_person"] = x.pop("name")
        r["vermieter_schluessel"] = f"JP:{r['name_juristische_person']}"
    r.update(x)
    return r


def miete(gid, eur, m2=60.0, bj="1949-1978", **x):
    r = {"angabe_id": str(uuid.uuid4()), "gebaeude_id": gid, "nettokalt_eur": eur, "wohnflaeche_klasse": "60-79", "baujahr_klasse": bj,
         "vertragsbeginn_jahr": 2015 + int(eur) % 9, "einwilligung": {"erteilt": True, "textversion": "test", "zeitpunkt": "2026-10-26T08:00:00Z"},
         "erfasst_am": next(ZEIT), "erfassungsweg": "selbst"}
    if m2:
        r["wohnflaeche_m2"] = m2
    r.update(x)
    return r


class Pruefgruppe(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.schl_datei = self.tmp / "schluessel" / "pg.json"
        self.pub = pg.schluessel_erzeugen(self.schl_datei, PW, stufe="interaktiv")
        self.schl = pg.Schluessel(self.schl_datei, PW)

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def export(self, typ, recs, key_id=None):
        """Exportdatei wie aus erfassen.js (Format wiz-stadtmonitor-erfassung, Version 1)."""
        eintraege = []
        for r in recs:
            if r.get("name_privat"):
                r["name_privat_enc"] = {"alg": pg.ALG, "key_id": self.pub["key_id"],
                                        "ciphertext": pg.versiegeln(self.pub["public_key"], r.pop("name_privat").encode())}
            eintraege.append({"id": r.get("erfassung_id") or r.get("angabe_id"), "erstellt": r["erfasst_am"], "key_id": key_id or self.pub["key_id"],
                              "ciphertext": pg.versiegeln(self.pub["public_key"], json.dumps(r).encode())})
        p = self.tmp / f"{typ}_{uuid.uuid4().hex[:6]}.bin"
        p.write_text(json.dumps({"format": "wiz-stadtmonitor-erfassung", "version": 1, "typ": typ, "alg": pg.ALG, "erfasser": "E-0000test",
                                 "erstellt": "2026-10-26T09:00:00Z", "anzahl": len(eintraege), "eintraege": eintraege}), encoding="utf-8")
        return p

    def arbeit(self, pruefer="P-1"):
        return pg.Arbeit(self.tmp / "arbeit", self.schl, pruefer)

    def test_ablauf_bis_zur_veroeffentlichung(self):
        konflikt_a, konflikt_b = eigentum(G[9], "kom", name="Stadt"), eigentum(G[9], "privat", name_privat="Hans Beispiel")
        dublette = [eigentum(G[10], "kirche", name="Kirchengemeinde Test"), eigentum(G[10], "kirche", name="Kirchengemeinde Test")]
        a = [eigentum(G[0], "geno", name="Wohnbau Test eG"), eigentum(G[1], "geno", name="wohnbau  test EG"), eigentum(G[2], "geno", name="Wohnbau Test eG"),
             eigentum(G[3], "privat", name_privat="Erika Testname"), eigentum(G[4], "privat", name_privat="erika testname"),
             eigentum(G[5], "privat", name_privat="Otto Probe"), eigentum(G[6], "jp_sonst", name="Müller Immobilien GmbH"),
             eigentum(G[7], "unklar"), konflikt_a, konflikt_b, *dublette,
             eigentum(G[8], "privat", objekt={"typ": "gebaeude", "id": G[8], "lage_hinweis": "Hauptstraße 12"}),  # Hausnummer: abgewiesen
             {**eigentum(G[8], "privat"), "name_juristische_person": "x"}]                                              # Schema: abgewiesen
        b = [miete(G[i % 3], 400 + 10 * i) for i in range(6)] + [miete(W[0], 500), miete(W[1], 520), miete(G[0], 450, m2=None)]
        ar = self.arbeit()
        neu, zeilen = pruefen.einlesen(ar, [self.export("eigentum", a), self.export("miete", b), self.export("eigentum", [eigentum(G[11], "bund")], key_id="fremd")])
        self.assertEqual(neu, len(a) - 2 + len(b))
        abgewiesen = [z[2] for z in zeilen if z[2].startswith("abgewiesen")]
        self.assertEqual(len(abgewiesen), 3, abgewiesen)
        self.assertTrue(any("Hausnummern" in g or "Ziffern" in g for g in abgewiesen))
        self.assertTrue(any("anderer Schlüssel" in g for g in abgewiesen))
        # nochmals einlesen: nichts doppelt
        self.assertEqual(pruefen.einlesen(ar, [self.export("miete", [b[0]])])[0], 0)
        # Prüfen: Vermieter-Schlüssel, Dublette, Konflikt
        pfad, _ = pruefen.pruefen(ar)
        e = ar.eintraege
        self.assertEqual(e[a[3]["erfassung_id"]]["vermieter"], e[a[4]["erfassung_id"]]["vermieter"])  # gleiche Person, andere Schreibweise
        self.assertRegex(e[a[3]["erfassung_id"]]["vermieter"], r"^V-\d{3}$")
        self.assertNotEqual(e[a[3]["erfassung_id"]]["vermieter"], e[a[5]["erfassung_id"]]["vermieter"])
        self.assertEqual({e[x["erfassung_id"]]["vermieter"] for x in a[:3]}, {"JP:Wohnbau Test eG"})
        self.assertEqual(e[dublette[0]["erfassung_id"]]["status"], "verworfen")
        self.assertIn("abweichende Angaben", e[konflikt_a["erfassung_id"]]["konflikt"])
        self.assertEqual(e[b[0]["angabe_id"]]["vermieter"], "JP:Wohnbau Test eG")  # über das Gebäude zugeordnet
        # Prüfliste und Bestand ohne Klartextnamen und ohne Beträge
        liste = pfad.read_text(encoding="utf-8")
        for verboten in ("Erika", "Otto", "Hans", "nettokalt"):
            self.assertNotIn(verboten, liste)
        self.assertNotIn("Erika", (self.tmp / "arbeit" / "bestand.sealed").read_text(encoding="ascii"))
        self.assertIn("Abgleich Vermieter-Schlüssel", (self.tmp / "arbeit" / "namenzugriff.tsv").read_text(encoding="utf-8"))
        # Vier Augen: eine Freigabe genügt nicht; Konflikt nicht freigebbar
        pruefen.freigeben(ar, alle=True)
        self.assertFalse(any(ar.freigegeben(x) for x in e.values()))
        pruefen.freigeben(ar, alle=True)  # dieselbe Person zählt nicht doppelt
        self.assertFalse(any(ar.freigegeben(x) for x in e.values()))
        ar2 = self.arbeit("P-2")
        pruefen.verwerfen(ar2, konflikt_b["erfassung_id"], "Beleg widerspricht")
        pruefen.pruefen(ar2)
        pruefen.freigeben(ar2, alle=True)
        ar1 = self.arbeit("P-1")
        pruefen.freigeben(ar1, [konflikt_a["erfassung_id"]])
        self.assertTrue(ar1.freigegeben(ar1.eintraege[konflikt_a["erfassung_id"]]))
        self.assertTrue(ar1.freigegeben(ar1.eintraege[a[0]["erfassung_id"]]))
        # Veröffentlichen (Mietangaben nur, wenn freigeschaltet)
        ziel = self.tmp / "repo"
        ohne = vo.veroeffentlichen(ar1, ziel, cfg={"mietangaben_aktiv": False})
        self.assertNotIn("mieten_aggregiert.json", ohne)
        aus = vo.veroeffentlichen(ar1, ziel, cfg={"mietangaben_aktiv": True})
        karte = json.loads((ziel / "data" / "wohnen" / "eigentum_gebaeude.geojson").read_text(encoding="utf-8"))
        props = {f["properties"]["id"]: f["properties"] for f in karte["features"]}
        self.assertEqual(props[G[0]]["name"], "Wohnbau Test eG")
        self.assertEqual(props[G[9]]["kategorie"], "kom")
        self.assertNotIn("name", props[G[6]])  # sonstige juristische Person: Name erst nach Prüfung
        for g in (G[3], G[4], G[5], G[7]):
            self.assertNotIn(g, props)  # privat und unklar nie je Gebäude
        ant = aus["eigentum_anteile_ortsbezirk.json"]["ortsbezirke"]["gertenbach"]
        self.assertIsNone(ant["privat"])  # 3 < 5
        self.assertEqual(ant["erfasst"], sum(ant["kategorien"].values()))
        m = aus["mieten_aggregiert.json"]
        zelle = next(z for z in m["zellen"] if z["ortsbezirk"] == "gertenbach")
        self.assertEqual(zelle["n"], 6)
        self.assertAlmostEqual(zelle["median"], round(425 / 60, 2))  # 400 … 450 € auf 60 m²
        klein = next(z for z in m["zellen"] if z["ortsbezirk"] == "wendershausen")
        self.assertEqual((klein["n"], klein["hinweis"]), (None, "zu wenige Angaben"))
        self.assertNotIn("median", klein)
        self.assertEqual(m["angaben_ohne_flaeche"], 1)
        self.assertEqual([j["name"] for j in m["juristische_personen"]], ["Wohnbau Test eG"])  # 6 Angaben aus 3 Gebäuden
        text = "".join(p.read_text(encoding="utf-8") for p in (ziel / "data" / "wohnen").iterdir())
        for verboten in ("Erika", "Otto", "Hans", "V-0", "angabe_id", "nettokalt_eur"):
            self.assertNotIn(verboten, text)
        # Name der sonstigen juristischen Person nach ausdrücklicher Prüfung; Änderung verlangt neue Freigaben
        pruefen.name_entscheiden(ar1, a[6]["erfassung_id"], True)
        self.assertEqual(ar1.eintraege[a[6]["erfassung_id"]]["freigaben"], [])
        pruefen.freigeben(ar1, [a[6]["erfassung_id"]])
        pruefen.freigeben(self.arbeit("P-2"), [a[6]["erfassung_id"]])
        aus = vo.veroeffentlichen(self.arbeit("P-1"), ziel, cfg={"mietangaben_aktiv": True})
        self.assertIn("Müller Immobilien GmbH", json.dumps(aus["eigentum_gebaeude.geojson"], ensure_ascii=False))
        # Widerruf: Eintrag ganz entfernen
        ar = self.arbeit()
        pruefen.loeschen(ar, b[0]["angabe_id"], "Einwilligung widerrufen")
        self.assertNotIn(b[0]["angabe_id"], self.arbeit().eintraege)

    def test_einladungsregister_beim_einlesen(self):
        import einladung
        reg = self.tmp / "arbeit" / "einladungen.tsv"
        zeile = {"erfasser_id": "E-0000test", "hash": "0" * 64, "ausgegeben": "2026-10-01", "gueltig_bis": "2027-10-01", "widerrufen": ""}
        einladung.register_schreiben(reg, [zeile])
        ar = self.arbeit()
        self.assertEqual(pruefen.einlesen(ar, [self.export("miete", [miete(G[0], 400)])])[0], 1)
        # Widerruf am Vortag: Einträge vom 26.10. werden abgewiesen; unbekannte ID ebenso
        einladung.register_schreiben(reg, [{**zeile, "widerrufen": "2026-10-25"}])
        n, z = pruefen.einlesen(self.arbeit(), [self.export("miete", [miete(G[1], 410)])])
        self.assertEqual(n, 0)
        self.assertIn("nach Widerruf", z[0][2])
        einladung.register_schreiben(reg, [{**zeile, "erfasser_id": "E-anders00"}])
        n, z = pruefen.einlesen(self.arbeit(), [self.export("miete", [miete(G[2], 420)])])
        self.assertIn("nicht im Einladungsregister", z[0][2])
        self.assertIn("nach Ablauf", pruefen.einladung_pruefen({**zeile, "gueltig_bis": "2026-10-20"}, "2026-10-26T08:00:00Z"))
        self.assertIn("vor Ausgabe", pruefen.einladung_pruefen(zeile, "2026-09-30T08:00:00Z"))

    def test_widerruf_widerspruch_fristen(self):
        b = [miete(G[0], 410), miete(G[1], 420)]
        a = [eigentum(G[2], "privat", name_privat="Erika Testname"), eigentum(G[3], "privat", name_privat="erika testname"),
             eigentum(G[4], "privat", name_privat="Otto Probe"), eigentum(G[5], "geno", name="Wohnbau Test eG")]
        ar = self.arbeit()
        pruefen.einlesen(ar, [self.export("miete", b), self.export("eigentum", a)])
        pruefen.pruefen(ar)
        # Widerruf über den Code aus der App (erste 8 Zeichen der Kennung als XXXX-XXXX)
        c = b[0]["angabe_id"].replace("-", "")[:8].upper()
        pruefen.loeschen(ar, pruefen.code_zu_id(ar, f"{c[:4]}-{c[4:]}"), "Widerruf")
        self.assertNotIn(b[0]["angabe_id"], ar.eintraege)
        self.assertIn(b[1]["angabe_id"], ar.eintraege)
        with self.assertRaises(pg.Abbruch):
            pruefen.code_zu_id(ar, "0000-0000")
        # Widerspruch zu einem Gebäude: alle Gebäude derselben Person, Sperrliste, kein erneutes Einlesen
        weg, ziele = pruefen.widerspruch(ar, [G[2]], "Widerspruch")
        self.assertEqual(ziele, {G[2], G[3]})
        self.assertEqual(set(weg), {a[0]["erfassung_id"], a[1]["erfassung_id"]})
        self.assertIn(a[2]["erfassung_id"], ar.eintraege)  # andere Person bleibt
        neu, zeilen = pruefen.einlesen(self.arbeit(), [self.export("eigentum", [eigentum(G[3], "kom", name="Stadt")])])
        self.assertEqual(neu, 0)
        self.assertIn("Sperrliste", zeilen[0][2])
        # Speicherdauer: Einträge älter als 24 Monate
        ar = self.arbeit()
        ar.eintraege[b[1]["angabe_id"]]["eingelesen"] = "2024-09-30T10:00:00+00:00"
        self.assertEqual(pruefen.fristen(ar, heute=pruefen.date(2026, 10, 26)), [b[1]["angabe_id"]])
        pruefen.fristen(ar, True, heute=pruefen.date(2026, 10, 26))
        self.assertNotIn(b[1]["angabe_id"], self.arbeit().eintraege)
        self.assertIn(a[2]["erfassung_id"], self.arbeit().eintraege)

    def test_passphrase_und_schluesselwechsel(self):
        # privater Schlüssel nur verschlüsselt in der Datei; ohne oder mit falscher Passphrase nicht nutzbar
        roh = self.schl_datei.read_text(encoding="utf-8")
        self.assertNotIn("secret_key", roh)
        self.assertIn("argon2id", roh)
        for falsch in (None, "falsche Passphrase 1"):
            with self.assertRaises(pg.Abbruch):
                pg.Schluessel(self.schl_datei, falsch)
        with self.assertRaises(pg.Abbruch):
            pg.schluessel_erzeugen(self.tmp / "kurz.json", "kurz", stufe="interaktiv")
        # Bestand mit Namen anlegen, dann Schlüssel wechseln
        a = [eigentum(G[0], "privat", name_privat="Erika Testname"), eigentum(G[1], "geno", name="Wohnbau Test eG")]
        alt_export = self.export("eigentum", a)
        ar = self.arbeit()
        pruefen.einlesen(ar, [alt_export])
        alt_id = self.schl.key_id
        neu = pruefen.schluessel_wechsel(ar, stufe="interaktiv")
        self.assertNotEqual(neu["key_id"], alt_id)
        schl = pg.Schluessel(self.schl_datei, PW)
        self.assertEqual(schl.key_id, neu["key_id"])
        self.assertTrue(schl.kennt(alt_id))  # alte Exporte bleiben lesbar
        ar2 = pg.Arbeit(self.tmp / "arbeit", schl, "P-1")
        enc = ar2.eintraege[a[0]["erfassung_id"]]["datensatz"]["name_privat_enc"]
        self.assertEqual(enc["key_id"], neu["key_id"])
        self.assertEqual(ar2.name_oeffnen(a[0]["erfassung_id"], "Test"), "Erika Testname")
        # der Bestand ist mit dem neuen Schlüssel versiegelt: ohne den alten Schlüssel lesbar
        nur_neu = self.tmp / "nur_neu.json"
        d = json.loads(self.schl_datei.read_text(encoding="utf-8"))
        nur_neu.write_text(json.dumps({**d, "frueher": []}), encoding="utf-8")
        self.assertIn(a[1]["erfassung_id"], pg.Arbeit(self.tmp / "arbeit", pg.Schluessel(nur_neu, PW), "P-1").eintraege)
        # Kompromittierung: alter Schlüssel gesperrt, Exporte mit ihm werden abgewiesen
        pub_vorher = dict(self.pub, key_id=neu["key_id"], public_key=neu["public_key"])
        self.pub = pub_vorher
        neuer_export = self.export("eigentum", [eigentum(G[2], "kom", name="Stadt")])
        pruefen.schluessel_wechsel(ar2, kompromittiert=True, stufe="interaktiv")
        ar3 = pg.Arbeit(self.tmp / "arbeit", pg.Schluessel(self.schl_datei, PW), "P-1")
        n, zeilen = pruefen.einlesen(ar3, [neuer_export])
        self.assertEqual(n, 0)
        self.assertIn("gesperrter Schlüssel", zeilen[0][2])

    def test_sperre_gegen_sensible_ausgaben(self):
        gut = {"zellen": [{"ortsbezirk": "x", "n": 5, "median": 6.0, "p25": 5.0, "p75": 7.0}, {"ortsbezirk": "y", "n": None, "hinweis": "zu wenige Angaben"}],
               "juristische_personen": [{"name": "A eG", "n": 5, "gebaeude": 2, "median": 6.0}]}
        vo.pruefe_ausgabe({"m": gut}, ["Erika Testname"])
        schlecht = [{"z": [{"nettokalt_eur": 400}]}, {"z": "V-017"}, {"z": "V-neu"}, {"z": str(uuid.uuid4())}, {"z": "Gebäude von Erika Testname"},
                    {"zellen": [{"n": 3, "median": 6.0}]}, {"zellen": [{"n": None}]}, {"juristische_personen": [{"name": "A", "n": 5, "gebaeude": 1}]},
                    {"features": [{"properties": {"id": "x", "kategorie": "privat"}}]},
                    {"ortsbezirke": {"x": {"erfasst": 4, "kategorien": {"geno": 2}, "privat": None}}},
                    {"ortsbezirke": {"x": {"erfasst": 5, "kategorien": {}, "privat": 2}}}, {"a": {"name_privat_enc": {}}}]
        for d in schlecht:
            with self.assertRaises(vo.Verstoss, msg=json.dumps(d)):
                vo.pruefe_ausgabe({"d": d}, ["Erika Testname"])

    def test_nicht_im_repository(self):
        with self.assertRaises(pg.Abbruch):
            pg.Arbeit(config.ROOT / "data" / "pruefung", self.schl, "P-1")
        with self.assertRaises(pg.Abbruch):
            pg.schluessel_erzeugen(config.ROOT / "schluessel.json", PW, stufe="interaktiv")
        with self.assertRaises(pg.Abbruch):
            pg.schluessel_erzeugen(self.schl_datei, PW, stufe="interaktiv")  # nie überschreiben
        with self.assertRaises(pg.Abbruch):
            pg.Arbeit(self.tmp / "arbeit", self.schl, "Erika")  # Prüfer-ID pseudonym
        self.assertEqual(self.schl_datei.stat().st_mode & 0o777, 0o600)

    def test_freitext_wie_in_der_app(self):
        for t, erwartet in (("Hauptstraße 12", "keine Hausnummern"), ("Am Markt 3a", "keine Hausnummern"), ("Nr. 5", "keine Hausnummern"),
                            ("a@b.de", "keine E-Mail-Adressen"), ("0551 1234567", "keine Telefonnummern"), ("seit 2019 vermietet", None)):
            self.assertEqual(pg.freitext(t), erwartet, t)
        self.assertEqual(pg.freitext("B 80", ohne_ziffern=True), "keine Ziffern (also keine Hausnummern)")


if __name__ == "__main__":
    unittest.main()
