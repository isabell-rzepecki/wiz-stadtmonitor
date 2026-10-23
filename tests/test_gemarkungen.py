import json
import unittest

from shapely.geometry import box

from pipeline import config, gemarkungen


class Gemarkungen(unittest.TestCase):
    def test_features_mit_zuordnung(self):
        gem = [{"gmk_nr": "2246", "gemarkung": "Witzenhausen", "erzeugt_am": "17.06.2026", "geometry": box(9.8, 51.3, 9.9, 51.4)},
               {"gmk_nr": "9999", "gemarkung": "Unbekannt", "erzeugt_am": "17.06.2026", "geometry": box(0, 0, 1, 1)}]
        f = gemarkungen.features(gem)
        self.assertEqual(f[0]["properties"]["slug"], "kernstadt")
        self.assertFalse(f[0]["properties"]["ortsbezirk"])
        self.assertIn("zuordnung_status", f[0]["properties"])
        self.assertNotIn("slug", f[1]["properties"])

    def test_datei_im_repository(self):
        d = json.loads(config.ORTSBEZIRKE.read_text(encoding="utf-8"))
        self.assertEqual(d["license"], "dl-de/zero-2.0")
        for k in ("attribution", "source", "retrieved"):
            self.assertIn(k, d)
        self.assertEqual(len(d["features"]), 17)
        self.assertEqual({f["properties"]["slug"] for f in d["features"]}, {o["slug"] for o in config.STADT["ortsteile"]})


if __name__ == "__main__":
    unittest.main()
