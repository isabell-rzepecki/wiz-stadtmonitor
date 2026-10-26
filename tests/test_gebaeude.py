"""Gebäude: Höhe aus LoD2 je ALKIS-Gebäude (über die OID, räumlich, geschätzt) und Vektorkacheln."""
import gzip
import tempfile
import unittest
from pathlib import Path

import mapbox_vector_tile
from pmtiles.reader import MmapSource, Reader
from shapely.geometry import Polygon

from pipeline import gebaeude, kacheln

RING = "559841 5689512 150 559851 5689512 150 559851 5689522 150 559841 5689522 150 559841 5689512 150"
DACH = RING.replace(" 150", " 158")
GML = f"""<core:cityObjectMember><bldg:Building gml:id="DEHE061500000AAA">
<bldg:measuredHeight uom="urn:adv:uom:m">8.42</bldg:measuredHeight>
<bldg:boundedBy><bldg:GroundSurface gml:id="g1"><gml:posList srsDimension="3">{RING}</gml:posList></bldg:GroundSurface></bldg:boundedBy>
<bldg:boundedBy><bldg:RoofSurface gml:id="r1"><gml:posList srsDimension="3">{DACH}</gml:posList></bldg:RoofSurface></bldg:boundedBy>
</bldg:Building></core:cityObjectMember>
<core:cityObjectMember><bldg:Building gml:id="DEHE061500000BBB">
<bldg:consistsOfBuildingPart><bldg:BuildingPart gml:id="B2a"><bldg:measuredHeight uom="urn:adv:uom:m">4</bldg:measuredHeight>
<gml:posList srsDimension="3">{RING}</gml:posList></bldg:BuildingPart></bldg:consistsOfBuildingPart>
<bldg:consistsOfBuildingPart><bldg:BuildingPart gml:id="B2b"><bldg:measuredHeight uom="urn:adv:uom:m">9.5</bldg:measuredHeight>
<gml:posList srsDimension="3">{RING}</gml:posList></bldg:BuildingPart></bldg:consistsOfBuildingPart>
</bldg:Building></core:cityObjectMember>
<core:cityObjectMember><bldg:Building gml:id="DEHE061500000CCC"><gml:posList srsDimension="3">{RING}</gml:posList></bldg:Building></core:cityObjectMember>"""


def quadrat(x, y, a=10):
    return Polygon([(x, y), (x + a, y), (x + a, y + a), (x, y + a)])


class Gebaeude(unittest.TestCase):
    def test_hoehe_aus_lod2(self):
        h = gebaeude.lod2_text(GML)
        self.assertEqual(h["DEHE061500000AAA"]["h"], 8.4)
        self.assertEqual(h["DEHE061500000BBB"]["h"], 9.5, "ohne eigene Höhe: der höchste Gebäudeteil")
        self.assertNotIn("DEHE061500000CCC", h, "ohne gemessene Höhe kein Eintrag")
        self.assertTrue(quadrat(559841, 5689512).contains(h["DEHE061500000AAA"]["punkt"]))

    def test_zuordnung_oid_raeumlich_geschaetzt(self):
        hoehen = gebaeude.lod2_text(GML)
        hoehen["DEHE061500000BBB"]["punkt"] = quadrat(600000, 5700000).representative_point()
        geb = [{"oid": "DEHE061500000AAABL", "geometry": quadrat(559841, 5689512)},  # gleiche OID mit Zusatz „BL“
               {"oid": "DEHE061500000XYZBL", "geometry": quadrat(599995, 5699995, 20)},  # andere OID, Grundriss enthält den Punkt
               {"oid": "DEHE061500000ZZZBL", "geometry": quadrat(0, 0)}]  # ohne Treffer
        z = gebaeude.zuordnen(geb, hoehen)
        self.assertEqual(z["DEHE061500000AAABL"][:3], ("gleich", "DEHE061500000AAA", 8.4))
        self.assertEqual(z["DEHE061500000XYZBL"][:3], ("räumlich", "DEHE061500000BBB", 9.5))
        self.assertEqual(z["DEHE061500000ZZZBL"], ("ohne Treffer", "", float(gebaeude.G["standardhoehe_m"]), "geschätzt"))

    def test_vektorkacheln(self):
        feats = [{"type": "Feature", "properties": {"id": "A", "h": 7.5},
                  "geometry": {"type": "Polygon", "coordinates": [[[9.85, 51.34], [9.851, 51.34], [9.851, 51.341], [9.85, 51.341], [9.85, 51.34]]]}}]
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "t.pmtiles"
            n = kacheln.schreiben(feats, p, "gebaeude", 14, 15)
            with open(p, "rb") as f:
                r = Reader(MmapSource(f))
                self.assertEqual((r.header()["min_zoom"], r.header()["max_zoom"]), (14, 15))
                self.assertEqual(r.metadata()["vector_layers"][0]["fields"], {"h": "Number", "id": "String"})
                kachel = r.get(14, 8640, 5460)
                self.assertIsNotNone(kachel)
                t = mapbox_vector_tile.decode(gzip.decompress(kachel))
        self.assertEqual(n, 2)
        self.assertEqual(t["gebaeude"]["features"][0]["properties"], {"id": "A", "h": 7.5})


if __name__ == "__main__":
    unittest.main()
