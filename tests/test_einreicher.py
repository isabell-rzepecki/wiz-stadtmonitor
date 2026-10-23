"""Einreicher aus TOP-Titeln: Fraktionen, gemeinsame Anträge, Einzelpersonen ohne Namen."""
import unittest

from pipeline import einreicher


class Einreicher(unittest.TestCase):
    def test_fraktion(self):
        r = einreicher.erkennen("Anfrage der Fraktion BÜNDNIS 90/DIE GRÜNEN vom 17.08.2026 zur Sicherung der Löschwasserversorgung")
        self.assertEqual((r["typ"], r["einreicher"], r["datum"], r["gemeinsam"]), ("Anfrage", ["GRUENE"], "2026-08-17", False))

    def test_gemeinsam(self):
        r = einreicher.erkennen("Beratung und Beschlussfassung über den Antrag der Fraktionen FWG u BÜNDNIS 90/DIE GRÜNEN vom 16.08.2026 zu X")
        self.assertEqual(sorted(r["einreicher"]), ["FWG", "GRUENE"])
        self.assertTrue(r["gemeinsam"])
        r = einreicher.erkennen("Anfrage der Fraktionen SPD, CDU und FDP vom 24.06.2026 zum Bauvorhaben")
        self.assertEqual(r["einreicher"], ["SPD", "CDU", "FDP"])

    def test_varianten(self):
        self.assertEqual(einreicher.erkennen("Antrag der Fraktion Bunte Liste/Kllimaliste - Alternativen für Witzenhausen vom 01.02.2025 X")["einreicher"], ["AFW"])
        self.assertEqual(einreicher.erkennen("Antrag von Die Partei vom 14.10.2025 über eine Luftmessstation")["einreicher"], ["PARTEI"])
        self.assertEqual(einreicher.erkennen("Anfrage der FDP Fraktion vom 25.10.2024 zu X")["einreicher"], ["FDP"])

    def test_einzelperson_ohne_namen(self):
        r = einreicher.erkennen("Antrag der Stadtverordneten Erika Muster vom 01.02.2025 zu X")
        self.assertEqual(r["einreicher"], ["EINZEL"])
        self.assertNotIn("Muster", r["fundstelle"])

    def test_ohne_muster(self):
        self.assertIsNone(einreicher.erkennen("Beratung und Beschlussfassung über den Haushalt 2025"))


if __name__ == "__main__":
    unittest.main()
