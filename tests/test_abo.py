"""Kalender und Feeds der Sitzungstermine (pipeline/abo.py); Sitzungen und Titel erfunden."""
import unittest
from xml.etree import ElementTree as ET

from pipeline import abo

STAND = "2026-10-24T10:00:00Z"


def daten():
    sitzungen = [
        {"id": "150/2026", "gremium": "Ortsbeirat Gertenbach", "gremium_typ": "ortsbeirat", "ortsteil": "Gertenbach", "date": "2026-11-05",
         "time": "19:30", "ort": "Dorfgemeinschaftshaus, Saal 1", "pdf": "https://example.org/150.pdf", "veroeffentlicht": "2026-10-20"},
        {"id": "151/2026", "gremium": "Stadtverordnetenversammlung", "gremium_typ": "stvv", "ortsteil": None, "date": "2026-11-10",
         "time": "19:00", "ort": "Rathaussaal", "pdf": "https://example.org/151.pdf", "veroeffentlicht": "2026-10-22"},
        {"id": "152/2026", "gremium": "Ortsbeirat Roßbach", "gremium_typ": "ortsbeirat", "ortsteil": "Roßbach", "date": "2026-11-12",
         "time": None, "termine": [{"date": "2026-11-12", "time": None}], "ort": "", "oeffentlich": False, "pdf": "https://example.org/152.pdf"},
        {"id": "010/2025", "gremium": "Stadtverordnetenversammlung", "gremium_typ": "stvv", "date": "2025-02-11", "time": "19:00",
         "ort": "Rathaussaal", "pdf": "https://example.org/010.pdf"},
    ]
    def v(ref, sitzung, top, titel, ortsteil=None, punkt=False):
        return {"reference": ref, "name": titel, "verfahrenspunkt": punkt,
                "locations": [{"ortsteil": ortsteil}] if ortsteil else [],
                "process": [{"sitzung": sitzung, "top": top, "titel": titel}]}
    vorgaenge = [v("A", "150/2026", "3", "Bank am Spielplatz; Pflege, Farbe", "Gertenbach"),
                 v("B", "150/2026", "1", "Eröffnung", "Gertenbach", punkt=True),
                 v("C", "151/2026", "10", "Bebauungsplan Nr. 3 Gertenbach", "Gertenbach"),
                 v("D", "151/2026", "11", "Haushaltssatzung 2027 mit einem sehr langen Titel über mehrere Zeilen im Kalender")]
    return {"sitzungen": sitzungen, "vorgaenge": vorgaenge}


class Auswahl(unittest.TestCase):
    def test_ortsteil_mit_punkten_der_stadtgremien(self):
        g, je = abo.auswahl(daten())
        titel, eintraege = g["gertenbach"]
        self.assertEqual([(s["id"], f) for s, f in eintraege], [("150/2026", None), ("151/2026", "Gertenbach")])
        self.assertEqual(abo.tagesordnung(eintraege[1][0], je["151/2026"], "Gertenbach"), [("10", "Bebauungsplan Nr. 3 Gertenbach")])
        self.assertEqual([s["id"] for s, _ in g["stadt"][1]], ["151/2026", "010/2025"])
        self.assertEqual(len(g["alle"][1]), 4)

    def test_gremium_mit_ganzer_tagesordnung(self):
        d = daten()
        for s in d["sitzungen"]:
            if s["gremium_typ"] == "stvv":
                s["gremium_id"] = "STVV"
        g, je = abo.auswahl(d)
        titel, eintraege = g[abo.gremium_slug("STVV")]
        self.assertEqual(titel, "Stadtverordnetenversammlung")
        self.assertEqual([(s["id"], f) for s, f in eintraege], [("151/2026", None), ("010/2025", None)])
        self.assertEqual(len(abo.tagesordnung(eintraege[0][0], je["151/2026"])), 2)
        self.assertNotIn("gertenbach", abo.gremium_slug("STVV"))


class Kalender(unittest.TestCase):
    def setUp(self):
        g, self.je = abo.auswahl(daten())
        self.g = g

    def test_format(self):
        t = abo.ics(*self.g["alle"], self.je, STAND)
        self.assertTrue(t.startswith("BEGIN:VCALENDAR\r\nVERSION:2.0\r\n") and t.endswith("END:VCALENDAR\r\n"))
        self.assertTrue(all(len(z.encode()) <= 75 for z in t.split("\r\n")))
        flach = t.replace("\r\n ", "")
        self.assertIn("DTSTART;TZID=Europe/Berlin:20261105T193000", flach)
        self.assertIn("DTEND;TZID=Europe/Berlin:20261105T213000", flach)
        self.assertIn("LOCATION:Dorfgemeinschaftshaus\\, Saal 1", flach)
        self.assertIn("TOP 3 Bank am Spielplatz\; Pflege\\, Farbe", flach)
        self.assertNotIn("Eröffnung", flach, "ohne Verfahrenspunkte")
        self.assertIn("DTSTART;VALUE=DATE:20261112", flach, "ohne Uhrzeit ganztägig")
        self.assertIn("Nichtöffentliche Sitzung.", flach)
        self.assertNotIn("010-2025", flach, "älter als ein Jahr")
        self.assertEqual(flach.count("BEGIN:VEVENT"), 3)

    def test_feed(self):
        f = abo.atom("gertenbach", *self.g["gertenbach"], self.je, STAND)
        root = ET.fromstring(f)
        ns = {"a": "http://www.w3.org/2005/Atom"}
        titel = [e.find("a:title", ns).text for e in root.findall("a:entry", ns)]
        self.assertEqual(titel, ["Stadtverordnetenversammlung am 10.11.2026", "Ortsbeirat Gertenbach am 05.11.2026"])
        inhalt = root.findall("a:entry", ns)[0].find("a:content", ns).text
        self.assertIn("Tagesordnungspunkte mit Bezug zu Gertenbach:\nTOP 10", inhalt)
        self.assertNotIn("Haushaltssatzung", inhalt)


if __name__ == "__main__":
    unittest.main()
