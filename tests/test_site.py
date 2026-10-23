import json
import tempfile
import unittest
from pathlib import Path

from pipeline import site


class Seite(unittest.TestCase):
    def test_zusammenstellen(self):
        with tempfile.TemporaryDirectory() as d:
            out = site.build(Path(d) / "_site")
            for f in ("index.html", "app.js", "timeline.js", "style.css", "stadt.json", "fonts/LICENSE-LilitaOne.txt",
                      "fonts/LICENSE-SpaceMono.txt", "vendor/leaflet/LICENSE"):
                self.assertTrue((out / f).exists(), f)
            self.assertIn("ortsteile", json.loads((out / "stadt.json").read_text(encoding="utf-8")))


if __name__ == "__main__":
    unittest.main()
