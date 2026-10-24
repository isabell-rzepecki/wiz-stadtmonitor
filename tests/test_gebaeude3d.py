"""3D-Gebäude: Grundriss und gemessene Höhe aus CityGML (LoD2), Gebäudeteile einzeln."""
import unittest

from pipeline import gebaeude3d

RING = "559841 5689512 150 559851 5689512 150 559851 5689522 150 559841 5689522 150 559841 5689512 150"
DACH = RING.replace(" 150", " 158")
GML = f"""<core:cityObjectMember><bldg:Building gml:id="B1">
<bldg:function>31001_2000</bldg:function><bldg:measuredHeight uom="urn:adv:uom:m">8.42</bldg:measuredHeight>
<bldg:boundedBy><bldg:GroundSurface gml:id="g1"><gml:posList srsDimension="3">{RING}</gml:posList></bldg:GroundSurface></bldg:boundedBy>
<bldg:boundedBy><bldg:RoofSurface gml:id="r1"><gml:posList srsDimension="3">{DACH}</gml:posList></bldg:RoofSurface></bldg:boundedBy>
</bldg:Building></core:cityObjectMember>
<core:cityObjectMember><bldg:Building gml:id="B2"><bldg:function>51009_1610</bldg:function>
<bldg:consistsOfBuildingPart><bldg:BuildingPart gml:id="B2a"><bldg:measuredHeight uom="urn:adv:uom:m">4</bldg:measuredHeight>
<gml:posList srsDimension="3">{DACH}</gml:posList><gml:posList srsDimension="3">{RING}</gml:posList></bldg:BuildingPart></bldg:consistsOfBuildingPart>
</bldg:Building></core:cityObjectMember>
<core:cityObjectMember><bldg:Building gml:id="B3"><gml:posList srsDimension="3">{RING}</gml:posList></bldg:Building></core:cityObjectMember>"""


class Gebaeude3d(unittest.TestCase):
    def test_grundriss_und_hoehe(self):
        g = {x["id"]: x for x in gebaeude3d.gebaeude(GML)}
        self.assertEqual(g["B1"]["hoehe"], 8.4)
        self.assertEqual(g["B1"]["funktion"], "31001_2000")
        self.assertEqual(g["B1"]["grundriss"][0][0], (559841.0, 5689512.0))
        self.assertEqual(len(g["B1"]["grundriss"]), 1, "nur die Bodenfläche, nicht das Dach")

    def test_gebaeudeteil_ohne_bodenflaeche_nimmt_den_tiefsten_ring(self):
        g = {x["id"]: x for x in gebaeude3d.gebaeude(GML)}
        self.assertEqual(g["B2a"]["hoehe"], 4.0)
        self.assertNotIn("B2", g, "Gebäude ohne eigene Höhe nur über seine Teile")

    def test_ohne_hoehe_kein_gebaeude(self):
        self.assertNotIn("B3", {x["id"] for x in gebaeude3d.gebaeude(GML)})


if __name__ == "__main__":
    unittest.main()
