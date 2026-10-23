"""Beteiligungsverfahren: Plan, Stufen und Fristen aus dem Text einer Bekanntmachung; keine Personenangaben."""
import json
import unittest

from pipeline import beteiligung

TEXT = """Amtliche Bekanntmachung der Stadt Musterstadt Nr. 044/2025
Bauleitplanung der Stadt Musterstadt Bebauungsplan Nr. 9 „Unter dem Weingarten“, Gemarkung Ermschwerd
Beteiligung der Öffentlichkeit gemäß § 3 Abs. 2 BauGB
Gemäß § 3 (2) BauGB wird bekannt gemacht, dass der Entwurf in der Zeit vom 17. März 2025 bis einschließlich
18. April 2025 eingesehen werden kann. Stellungnahmen an erika.muster@example.org."""


class Beteiligung(unittest.TestCase):
    def test_lesen(self):
        r = beteiligung.lesen(TEXT)
        self.assertEqual(r["nr"], "044/2025")
        self.assertEqual((r["plan"]["art"], r["plan"]["nr"], r["plan"]["aenderung"], r["plan"]["gemarkung"], r["plan"]["name"]),
                         ("bplan", "9", 0, "Ermschwerd", "Unter dem Weingarten"))
        self.assertEqual([(s["stufe"], s.get("von"), s.get("bis")) for s in r["stufen"]], [("veroeff", "2025-03-17", "2025-04-18")])
        self.assertNotIn("muster", json.dumps(r).lower())

    def test_datum(self):
        self.assertEqual(beteiligung.iso("16. Dezember 2024"), "2024-12-16")
        self.assertEqual(beteiligung.iso("07.04.2025"), "2025-04-07")

    def test_verfahren_id(self):
        self.assertEqual(beteiligung.verfahren_id("fplan", 45), "fplan:45")
        self.assertEqual(beteiligung.verfahren_id("bplan", 5, "18", "2246"), "bplan:2246:18:5")


if __name__ == "__main__":
    unittest.main()
