"""Umweltebenen: Abrufadresse (Achsenfolge) und räumliche Überschneidung."""
import unittest
import urllib.parse

from shapely.geometry import box

from pipeline import config, umwelt


def flaeche(geom, ebene="nsg", ueberschneidung=True):
    return {"gruppe": "natur", "ebene": ebene, "titel": "Naturschutzgebiet", "name": "Test", "zone": None,
            "ueberschneidung": ueberschneidung, "geometry": geom}


class Umwelt(unittest.TestCase):
    def test_bbox_breite_zuerst(self):
        e = config.STADT["umwelt"]["gruppen"][0]["ebenen"][0]
        q = urllib.parse.parse_qs(urllib.parse.urlparse(umwelt.url(e, (9.7, 51.2, 9.9, 51.4))).query)
        self.assertEqual(q["BBOX"][0], "51.2,9.7,51.4,9.9,urn:ogc:def:crs:EPSG::4326")
        self.assertEqual(q["OUTPUTFORMAT"][0], "GEOJSON")

    def test_punkt_in_flaeche(self):
        liste = [flaeche(box(9.8, 51.3, 9.9, 51.4))]
        self.assertEqual(len(umwelt.ueberschneidungen(liste, punkt=(9.85, 51.35))), 1)
        self.assertEqual(umwelt.ueberschneidungen(liste, punkt=(9.95, 51.35)), [])

    def test_flaeche_mindestanteil(self):
        liste = [flaeche(box(9.8, 51.3, 9.9, 51.4))]
        self.assertEqual(len(umwelt.ueberschneidungen(liste, flaeche=box(9.85, 51.35, 9.95, 51.36))), 1)
        # Berührung am Rand bzw. Anteil unter ANTEIL: keine Überschneidung
        self.assertEqual(umwelt.ueberschneidungen(liste, flaeche=box(9.8999, 51.35, 9.99, 51.36)), [])

    def test_naturpark_ohne_ueberschneidung(self):
        liste = [flaeche(box(9.0, 51.0, 10.0, 52.0), "naturpark", ueberschneidung=False)]
        self.assertEqual(umwelt.ueberschneidungen(liste, punkt=(9.85, 51.35)), [])

    def test_konfiguration(self):
        ids = [e["id"] for _, e in umwelt.ebenen()]
        self.assertEqual(len(ids), len(set(ids)))
        for g in config.STADT["umwelt"]["gruppen"]:
            self.assertTrue(g["attribution"] and g["quelle"] and g["farbe"].startswith("#"))


if __name__ == "__main__":
    unittest.main()
