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

    def test_impressum_aus_konfiguration(self):
        # Impressum (§ 5 DDG, § 18 Abs. 2 MStV): Stelle und Kontakt aus stadt.json, keine Leerstelle, wenn benannt
        with tempfile.TemporaryDirectory() as d:
            out = site.build(Path(d) / "_site", mit_daten=False)
            text = (out / "impressum.html").read_text(encoding="utf-8")
            D = site.config.STADT["wohnen_eigentum"]["erfassung"]["datenschutz"]
            if D["verantwortlich"]:
                self.assertNotIn("[Leerstelle", text)
                self.assertEqual(text.count(D["verantwortlich"].splitlines()[0]), 2)
                self.assertIn(D["kontakt_widerspruch"], text)
            if D["verantwortlich"]:  # auch im Abschnitt „Über“ der Startseite
                self.assertIn(f'<span data-feld="verantwortlich_name">{D["verantwortlich"].splitlines()[0]}</span>',
                              (out / "index.html").read_text(encoding="utf-8"))
            for seite in ("index.html", "datenschutz.html", "erfassen.html"):
                self.assertIn('href="impressum.html"', (out / seite).read_text(encoding="utf-8"), seite)

    def test_aushang_art14(self):
        # Aushang nach Art. 14 Abs. 5 lit. b: Stadt, Hinweis zu Namen passend zum Schalter, QR-Code zur Datenschutzseite
        with tempfile.TemporaryDirectory() as d:
            seite = Path(d) / "aushang.html"
            seite.write_text((site.config.SITE_SRC / "aushang.html").read_text(encoding="utf-8"), encoding="utf-8")
            site.datenschutz_ausfuellen(seite)
            text = seite.read_text(encoding="utf-8")
            self.assertIn(f'<span data-feld="stadt">{site.config.STADT["stadt"]["name"]}</span>', text)
            if not site.config.STADT["wohnen_eigentum"]["privat_namen_aktiv"]:
                self.assertIn("Namen von Privatpersonen werden derzeit nicht erfasst.", text)
            self.assertIn("<svg", text)
            self.assertIn("datenschutz.html", text)
            self.assertIn("Art. 14", text)


if __name__ == "__main__":
    unittest.main()
