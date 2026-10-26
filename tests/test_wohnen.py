"""Wohnen und Boden: Zensusangaben, Spannen der Bodenrichtwerte, getrennte Mietbegriffe."""
import json
import sys
import unittest

from pipeline import config, wohnen


class Wohnen(unittest.TestCase):
    def test_zensuszahlen(self):
        self.assertEqual(wohnen._zahl("5,09"), (5.09, False))
        self.assertEqual(wohnen._zahl("(5,50)"), (5.5, True))
        self.assertEqual(wohnen._zahl("–"), (None, False))  # null oder geheim gehalten: ohne Wert, nicht 0
        self.assertEqual(wohnen._zahl(54.4), (54.4, False))

    def test_spanne_nur_wohn_und_mischbauland(self):
        z = lambda wert, ez, art, gk="2151": {"wert": wert, "entwicklungszustand": ez, "art": art, "gemarkung_nr": gk}
        sp = wohnen.spannen([z(30, "B", "WA"), z(45, "B", "MI"), z(80, "B", "GE"), z(1.2, "LF", "A"), z(20, "B", "WR", "2152")])
        self.assertEqual((sp["2151"]["min"], sp["2151"]["max"], sp["2151"]["zonen"]), (30, 45, 2))
        self.assertEqual((sp["stadt"]["min"], sp["stadt"]["max"], sp["stadt"]["zonen"]), (20, 45, 3))

    def test_mietbegriffe_getrennt(self):
        b = [x["begriff"] for x in config.STADT["wohnen"]["begriffe"]]
        self.assertEqual(b, ["Bestandsmiete", "Angebotsmiete", "Ortsübliche Vergleichsmiete"])

    def test_zensus_im_repository(self):
        d = json.loads(wohnen.ZENSUS.read_text(encoding="utf-8"))
        self.assertEqual(d["license"], "dl-de/by-2.0")
        wiz = next(g for g in d["gemeinden"] if g["ars"] == config.STADT["stadt"]["ars"])
        self.assertAlmostEqual(wiz["nettokaltmiete_eur_m2"], 5.09)
        ob = json.loads(wohnen.ZENSUS_OB.read_text(encoding="utf-8"))
        self.assertEqual(ob["kennzeichnung"], "Näherung")
        self.assertEqual(len(ob["ortsbezirke"]), len(config.STADT["ortsteile"]))
        for e in ob["ortsbezirke"].values():  # unter der Mindestzahl an Zellen kein Wert; „–“ nie als 0
            for m in e.values():
                if m["zellen"] < ob["mindestzellen"]:
                    self.assertIsNone(m["wert"])
                self.assertNotEqual(m["wert"], 0)

    def test_bodenrichtwerte_verlauf(self):
        # beide Stichtage mit Datendienst im Repository; 2026 gibt es nur als Kartendienst
        for jahr in ("2022", "2024"):
            d = json.loads(wohnen.BRW_GEO_JAHR(jahr).read_text(encoding="utf-8"))
            self.assertEqual(d["stichtag"][:4], jahr)
            self.assertIn(f"01.01.{jahr}", d["attribution"])
            self.assertTrue(d["features"])
        stichtage = [v["stichtag"] for v in config.STADT["wohnen"]["boris_verlauf"]["stichtage"]]
        self.assertNotIn("2026-01-01", stichtage)

    def test_wohnen_eigentum_sicher_voreingestellt(self):
        # sensible Felder aus, bis die Datenschutzfragen geklärt sind; Schwellen wie in den Veröffentlichungsregeln (R4, R5)
        E = config.STADT["wohnen_eigentum"]
        self.assertIs(E["privat_namen_aktiv"], False)
        self.assertIs(E["mietangaben_aktiv"], False)
        regeln = {z.split("\t")[0]: z.split("\t")[2] for z in (config.ROOT / E["regeln"]["quelle"]).read_text(encoding="utf-8").splitlines()[1:] if z}
        self.assertIn(f"ab {E['regeln']['mieten_zelle_min']} Angaben", regeln["R4"])
        self.assertIn(f"ab {E['regeln']['juristische_person_min_angaben']} Angaben aus mindestens {E['regeln']['juristische_person_min_gebaeude']} Gebäuden", regeln["R5"])
        kat = {k["code"]: k for k in E["kategorien"]}
        self.assertFalse(kat["privat"]["name_veroeffentlichen"])  # R1, R2: privat nie mit Namen, nur als Anteil
        self.assertIsNone(kat["privat"]["farbe"])

    def test_eigentumsfarben_kontrast(self):
        # Kartenebene Eigentum: Nicht-Text-Kontrast mindestens 3:1 gegen Hintergrund und nicht erfasste Gebäude (WCAG 1.4.11)
        sys.path.insert(0, str(config.ROOT / "tools"))
        import kontrast
        verh = lambda a, b: (max(kontrast.luminanz(a), kontrast.luminanz(b)) + 0.05) / (min(kontrast.luminanz(a), kontrast.luminanz(b)) + 0.05)  # noqa: E731
        for k in config.STADT["wohnen_eigentum"]["kategorien"]:
            if k["farbe"]:
                for grund in ("#f2f2f2", "#e3ded9"):
                    self.assertGreaterEqual(verh(k["farbe"], grund), 3, (k["code"], grund))

    def test_ohne_gepruefte_dateien_keine_werte(self):
        d = json.loads(wohnen.OUT.read_text(encoding="utf-8")) if wohnen.OUT.exists() else None
        if d is None:
            self.skipTest("wohnen.json noch nicht erzeugt")
        for k, p in (("eigentum_anteile", wohnen.EIGENTUM_ANTEILE), ("mieten", wohnen.MIETEN)):
            self.assertIn(k, d)
            if not p.exists():
                self.assertIsNone(d[k])


if __name__ == "__main__":
    unittest.main()
