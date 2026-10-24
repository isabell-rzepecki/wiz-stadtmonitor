"""Gebäude und Eigentum: Beteiligungsbericht ohne Personen, Gebäude aus GML."""
import unittest

from pipeline import eigentum

BERICHT = """3. Die Beteiligungen der Stadt Musterstadt
3.1. Muster Bäder GmbH (MB)

    Anschrift / Sitz                    Muster Bäder GmbH
                                        Hinter dem Deich 9

    Rechtsform                          Gesellschaft mit beschränkter Haftung ( GmbH )

    Gegenstand des Unternehmens         Gegenstand des Unternehmens ist der Betrieb von öffentlichen
                                        Bädern. Die Gesellschaft ist zu allen Maßnahmen berechtigt.

    Stammkapital                        260.000,00 €

    Gesellschafter                      Stadt Musterstadt ( 100 % )

    Aufsichtsratsvorsitz                Bürgermeisterin Erika Muster
    Geschäftsführung1                   Max Beispiel
"""

GML = """<GebaeudeBauwerk gml:id="X"><geometrie><gml:MultiSurface><gml:surfaceMember><gml:Polygon gml:id="p">
<gml:exterior><gml:LinearRing><gml:posList>559841 5689512 559851 5689512 559851 5689522 559841 5689512</gml:posList></gml:LinearRing></gml:exterior>
</gml:Polygon></gml:surfaceMember></gml:MultiSurface></geometrie><funktion>Gebäude für öffentliche Zwecke</funktion></GebaeudeBauwerk>"""


class Eigentum(unittest.TestCase):
    def test_bericht_ohne_personen(self):
        g = eigentum.gesellschaften(BERICHT)
        self.assertEqual(len(g), 1)
        e = g[0]
        self.assertEqual((e["name"], e["gesellschafter"], e["pflicht"]), ("Muster Bäder GmbH (MB)", "Stadt Musterstadt ( 100 % )", True))
        self.assertEqual(e["gegenstand"], "Gegenstand des Unternehmens ist der Betrieb von öffentlichen Bädern.")
        self.assertNotIn("Erika", str(g))  # Aufsichtsratsvorsitz (Person) nicht übernommen
        self.assertNotIn("Erika", str(g))
        self.assertNotIn("Beispiel", str(g))

    def test_gebaeude(self):
        gj = eigentum.gebaeude_geojson(GML)
        self.assertEqual(len(gj["features"]), 1)
        lon, lat = gj["features"][0]["geometry"]["coordinates"][0][0][0]
        self.assertTrue(9.5 < lon < 10.2 and 51.2 < lat < 51.5)


if __name__ == "__main__":
    unittest.main()
