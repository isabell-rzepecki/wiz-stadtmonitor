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

    def test_verantwortliche_stelle_aus_konfiguration(self):
        # eine Quelle (stadt.json) für Datenschutzseite und App; ohne Angabe bleibt die Leerstelle sichtbar
        with tempfile.TemporaryDirectory() as d:
            seite = Path(d) / "datenschutz.html"
            vorlage = (site.config.SITE_SRC / "datenschutz.html").read_text(encoding="utf-8")
            seite.write_text(vorlage, encoding="utf-8")
            D = site.config.STADT["wohnen_eigentum"]["erfassung"]["datenschutz"]
            alt = dict(D)
            try:
                D.update(verantwortlich=None, kontakt_widerspruch=None)
                site.datenschutz_ausfuellen(seite)
                self.assertEqual(seite.read_text(encoding="utf-8").count("[Leerstelle"), vorlage.count("[Leerstelle"))
                D.update(verantwortlich="Testverein e. V.\nMusterweg 1, 00000 Teststadt", kontakt_widerspruch="datenschutz@example.org <b>")
                site.datenschutz_ausfuellen(seite)
                text = seite.read_text(encoding="utf-8")
                self.assertIn('<p data-feld="verantwortlich">Testverein e. V.<br>Musterweg 1, 00000 Teststadt</p>', text)
                self.assertIn("datenschutz@example.org &lt;b&gt;", text)
                self.assertNotIn("verantwortlichen Stelle folgen", text)
            finally:
                D.clear()
                D.update(alt)


if __name__ == "__main__":
    unittest.main()
