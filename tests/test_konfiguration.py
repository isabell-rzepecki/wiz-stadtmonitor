import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STADT = json.loads((ROOT / "config" / "stadt.json").read_text(encoding="utf-8"))


class Konfiguration(unittest.TestCase):
    def test_ortsteile(self):
        ot = STADT["ortsteile"]
        self.assertEqual(sum(o["ortsbezirk"] for o in ot), 16)
        self.assertEqual(len({o["slug"] for o in ot}), len(ot))
        self.assertTrue(all(re.fullmatch(r"[a-z0-9-]+", o["slug"]) for o in ot))

    def test_gemarkungen(self):
        nrs = [o["gemarkung_nr"] for o in STADT["ortsteile"]]
        self.assertEqual(len(set(nrs)), 17)
        self.assertTrue(all(re.fullmatch(r"\d{4}", n) for n in nrs))
        self.assertTrue(all(o.get("zuordnung_status") for o in STADT["ortsteile"]))

    def test_gremien(self):
        ids = {g["id"] for g in STADT["gremien"]}
        self.assertTrue({i for r in STADT["zeitleiste_gremien"] for i in r["ids"]} <= ids)
        self.assertTrue(all(g["typ"] in STADT["gremientypen"] for g in STADT["gremien"]))

    def test_kein_bonn_im_code(self):
        # stadtspezifische Werte gehören in config/stadt.json; Herkunftsvermerke („RIS-Karte Bonn“) sind erlaubt
        for p in [*(ROOT / "site").glob("*.js"), *(ROOT / "site").glob("*.html"), *(ROOT / "site").glob("*.css"), *(ROOT / "pipeline").glob("*.py")]:
            text = re.sub(r"RIS-Karte Bonn", "", p.read_text(encoding="utf-8"))
            self.assertNotRegex(text, r"(?i)\bbonn|endenich|oparl", p.name)

    def test_keine_stadtwerte_im_code(self):
        name = STADT["stadt"]["name"]
        for p in [*(ROOT / "site").glob("*.js"), *(ROOT / "pipeline").glob("*.py")]:
            self.assertNotIn(name, p.read_text(encoding="utf-8"), p.name)


if __name__ == "__main__":
    unittest.main()
