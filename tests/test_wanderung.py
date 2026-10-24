"""Zuzug und Wegzug: Tabellen der Jahresberichte (drei Satzformen), Kodierung 2018, Kreismatrix nach Spaltenlage."""
import unittest

from pipeline import wanderung

AB_2024 = """
  636 015     Weißenborn                                                     1 003            4          15           63          41            10           1 013
  636 016     Witzenhausen, Stadt                                           15 219           93         209          950         917          – 87          15 132
  636 000     Werra-Meißner-Kreis                                           98 055          694       1 550        5 956       5 475         – 360          97 695
"""
BIS_2023 = """
636 016
Witzenhausen, Stadt                               15 005             118             209           1 131             949              92         15 097
"""
BIS_2017 = """
636 016                           M               7 075         72         101           669       475        168          7 243
Witzenhausen, Stadt               W               7 626         50          94           545       423         80          7 706
                                  I              14 701        122         195         1 214       898        248         14 949
"""
ZEILEN = [("Kreis A", "", "12"), ("Kreis B", "7", ""), ("Land Hessen", "7", "12"), ("Andere Bundesländer", "3", "—"),
          ("Ausland2)", "•", "5"), ("Fortgezogene insgesamt", "10", "17")]
MATRIX = "Herkunfts-\n gebiet\n" + "".join(f"{n:<24}{a:>8}{b:>8}\n" for n, a, b in ZEILEN) + "\f"



class Wanderung(unittest.TestCase):
    def test_satzform_ab_2024(self):
        g = wanderung.gemeinden(AB_2024, "636")
        self.assertEqual(set(g), {"636015", "636016"}, "Kreissumme 000 nicht als Gemeinde")
        self.assertEqual(g["636016"]["zuzuege"], 950)
        self.assertEqual(g["636016"]["veraenderung"], -87)
        self.assertEqual(g["636016"]["bev_anfang"], 15219)

    def test_satzform_2018_bis_2023(self):
        g = wanderung.gemeinden(BIS_2023, "636")["636016"]
        self.assertEqual((g["name"], g["zuzuege"], g["fortzuege"], g["bev_ende"]), ("Witzenhausen, Stadt", 1131, 949, 15097))

    def test_satzform_bis_2017_nimmt_insgesamt(self):
        g = wanderung.gemeinden(BIS_2017, "636")["636016"]
        self.assertEqual((g["bev_anfang"], g["zuzuege"], g["fortzuege"]), (14701, 1214, 898))

    def test_kodierung_2018(self):
        kodiert = "".join(chr(ord(c) - 29) if c not in " \n" else c for c in "Witzenhausen")
        self.assertEqual(wanderung.dekodieren(kodiert), "Witzenhausen")
        self.assertEqual(wanderung.dekodieren("±"), "–")

    def test_zahlen_und_zeichen(self):
        self.assertEqual(wanderung.zahl("1 382"), 1382)
        self.assertEqual(wanderung.zahl("– 87"), -87)
        self.assertEqual(wanderung.zahl("—"), 0, "genau null")
        self.assertIsNone(wanderung.zahl("•"), "geheim, nicht null")

    def test_matrix_nach_spaltenlage(self):
        zu, fort = wanderung.matrix(MATRIX, "Kreis A", {"Kreis A": [], "Kreis B": []})
        self.assertEqual(zu["Kreis B"], 12)
        self.assertEqual(fort["Kreis B"], 7)
        self.assertEqual(fort["Andere Bundesländer"], 3)
        self.assertIsNone(fort["Ausland"])
        self.assertEqual(fort["insgesamt"], 10)


if __name__ == "__main__":
    unittest.main()
