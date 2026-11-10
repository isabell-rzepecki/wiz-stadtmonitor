"""Seiten je Ortsteil: Inhalt aus dem Export (Testdaten), Verweise, Sitemap, keine Verfahrenspunkte, kein Skript."""
import json
import re
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from pipeline import config, ortsteilseiten, site

FIX = Path(__file__).parent / "fixtures" / "vorgaenge.json"


class Ortsteilseiten(unittest.TestCase):
    def test_seiten_aus_testdaten(self):
        with tempfile.TemporaryDirectory() as d:
            export = Path(d) / "export"
            export.mkdir()
            shutil.copy(FIX, export / "vorgaenge.json")
            out = Path(d) / "_site"
            out.mkdir()
            with mock.patch.object(config, "EXPORT", export):
                pfade = ortsteilseiten.erzeugen(out)
            self.assertEqual(len(pfade), len(config.STADT["ortsteile"]) + 1)
            daten = json.loads(FIX.read_text(encoding="utf-8"))
            seite = (out / "ortsteil" / "gertenbach" / "index.html").read_text(encoding="utf-8")
            self.assertIn("<h1>Gertenbach</h1>", seite)
            self.assertIn('href="../../?gebiet=ortsteil:gertenbach#STV/066/2026"', seite)  # Vorgang auf der Karte
            for v in daten["vorgaenge"]:
                if v["verfahrenspunkt"]:
                    self.assertNotIn(v["name"], seite)
            self.assertNotIn("<script", seite)
            self.assertIn("Zahlen zum Ortsteil", seite)  # Strukturdaten aus dem Repository
            uebersicht = (out / "ortsteile" / "index.html").read_text(encoding="utf-8")
            self.assertEqual(len(re.findall(r'href="\.\./ortsteil/[^/]+/"', uebersicht)), len(config.STADT["ortsteile"]))

    def test_im_seitenbau_sitemap_und_verweise(self):
        with tempfile.TemporaryDirectory() as d:
            out = site.build(Path(d) / "_site", mit_daten=False)
            karte = (out / "sitemap.xml").read_text(encoding="utf-8")
            self.assertIn("/ortsteile/</loc>", karte)
            self.assertIn("/ortsteil/gertenbach/</loc>", karte)
            seite = (out / "ortsteil" / "kernstadt" / "index.html").read_text(encoding="utf-8")
            self.assertIn('<link rel="canonical" href="https://stadtmonitor-witzenhausen.de/ortsteil/kernstadt/">', seite)
            self.assertIn(f"Stadtmonitor {config.STADT['stadt']['name']}</title>", seite)
            self.assertIn('href="ortsteile/"', (out / "index.html").read_text(encoding="utf-8"))
            self.assertIn("ortsteil/${encodeURIComponent(area.key)}/", (out / "app.js").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
