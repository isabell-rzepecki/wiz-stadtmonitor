"""Wohnen und Boden: Zensusangaben, Spannen der Bodenrichtwerte, getrennte Mietbegriffe."""
import json
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
        for e in d["ortsbezirke"].values():  # unter der Mindestzahl an Zellen kein Wert
            for m in e.values():
                if m["zellen"] < config.STADT["wohnen"]["zensus"]["mindestzellen"]:
                    self.assertIsNone(m["wert"])


if __name__ == "__main__":
    unittest.main()
