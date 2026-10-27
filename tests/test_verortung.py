import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from pipeline import verortung

NAMEN = {
    "Brückenstraße": {"2246": {"n": 31, "lon": 9.857, "lat": 51.343}},
    "Ermschwerder Straße (Witzenhausen)": {"2246": {"n": 40, "lon": 9.86, "lat": 51.35}},
    "Ermschwerder Straße (Blickershausen)": {"2125": {"n": 5, "lon": 9.79, "lat": 51.37}},
    "Bahnhofstraße (Gertenbach)": {"2151": {"n": 9, "lon": 9.77, "lat": 51.39}},
    "Bahnhofstraße (Hundelshausen)": {"2173": {"n": 9, "lon": 9.88, "lat": 51.29}},
    "Am Rabensberg": {"2246": {"n": 14, "lon": 9.857, "lat": 51.352}},
    "In der Stadt": {"2246": {"n": 3, "lon": 9.85, "lat": 51.34}},
    "Allenbach": {"2246": {"n": 3, "lon": 9.85, "lat": 51.34}},
}


class StufeB(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        p = Path(cls.tmp.name) / "v.json"
        p.write_text(json.dumps({"namen": NAMEN}), encoding="utf-8")
        cls.v = verortung.Verzeichnis(p)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def b(self, titel, ortsteil=None):
        locs, aud = verortung.stufe_b(titel, {"ortsteil": ortsteil}, self.v, "https://example.org/x.pdf")
        return {(l["level"], l["name"], l["ortsteil"]) for l in locs}, aud

    def test_eindeutige_strasse_und_kein_ortsteil_aus_adjektiv(self):
        locs, _ = self.b("Neugestaltung Brückenstraße und Teilabschnitt Ermschwerder Straße")
        self.assertIn(("strasse", "Brückenstraße", "Kernstadt"), locs)
        # mehrdeutig, eingegrenzt über die eindeutige Brückenstraße; „Ermschwerder“ ist nicht der Ortsteil Ermschwerd
        self.assertIn(("strasse", "Ermschwerder Straße", "Kernstadt"), locs)
        self.assertFalse(any(l[2] == "Ermschwerd" for l in locs))

    def test_mehrdeutig_ohne_kontext_bleibt_offen(self):
        locs, aud = self.b("Sanierung Bahnhofstraße")
        self.assertEqual(locs, set())
        self.assertEqual(aud[0]["mehrdeutig"], "ja")
        self.assertEqual(aud[0]["konfidenz"], "")

    def test_vorrang_nur_ohne_eingrenzenden_hinweis(self):
        # verortung.vorrang: „Ermschwerder Straße“ meint ohne Hinweis die Kernstadt
        with mock.patch.dict(verortung.VORRANG, {"Ermschwerder Straße": "Kernstadt"}, clear=True):
            locs, aud = verortung.stufe_b("Entwurfsplanung Ermschwerder Straße", {"ortsteil": None}, self.v, "x.pdf")
            self.assertEqual([(l["name"], l["ortsteil"], l["method"]) for l in locs], [("Ermschwerder Straße", "Kernstadt", "strasse+vorrang")])
            self.assertEqual(aud[0]["mehrdeutig"], "ja")
            locs, _ = self.b("Entwurfsplanung Ermschwerder Straße", ortsteil="Blickershausen")
            self.assertEqual(locs, {("strasse", "Ermschwerder Straße", "Blickershausen")})
            # Ortsbeirat eines anderen Ortsteils: kein Vorrang, bleibt offen
            locs, _ = self.b("Entwurfsplanung Ermschwerder Straße", ortsteil="Roßbach")
            self.assertEqual(locs, set())

    def test_mehrdeutig_eingegrenzt_ueber_gremium(self):
        locs, _ = self.b("Bank Bahnhofstr.", ortsteil="Gertenbach")
        self.assertIn(("strasse", "Bahnhofstraße", "Gertenbach"), locs)

    def test_gemarkung_und_ortsteil(self):
        locs, _ = self.b("Aufstellung des Bebauungsplanes Nr. 7 Gemarkung Kleinalmerode")
        self.assertIn(("ortsteil", "Kleinalmerode", "Kleinalmerode"), locs)
        locs, _ = self.b("Baumaßnahmen am Bahnhaltepunkt Gertenbach")
        self.assertIn(("ortsteil", "Gertenbach", "Gertenbach"), locs)

    def test_ausschluss_und_einzelwoerter(self):
        locs, _ = self.b("Resilienz kritischer Infrastruktur in der Stadt am Allenbach")
        self.assertEqual(locs, set())
        locs, _ = self.b("Umweltschaugarten am Rabensberg")
        self.assertIn(("strasse", "Am Rabensberg", "Kernstadt"), locs)

    def test_flurstueck(self):
        with mock.patch.object(verortung, "flurstueck", return_value={"lon": 9.8, "lat": 51.38}) as f:
            locs, _ = self.b("Veräußerung des Grundstückes Gem. Ermschwerd, Fl. 11, Flst. 125, in Größe von 6.575 m²")
        f.assert_called_once_with("2140", "11", "125", None)
        self.assertIn(("flurstueck", "Gemarkung Ermschwerd, Flur 11, Flurstück 125", "Ermschwerd"), locs)

    def test_flurstueck_schreibweisen(self):
        for titel in ("Verkauf Gemarkung Witzenhausen, Flur. 2, Flurstück 169", "Gemarkung Witzenhausen, Flur 2, Flurstücke 169 und 171",
                      "Gemarkung Witzenhausen, Flur 2, Flurstück Nr. 169"):
            with mock.patch.object(verortung, "flurstueck", return_value={"lon": 9.85, "lat": 51.34}) as f:
                self.b(titel)
            f.assert_called_once_with("2246", "2", "169", None)


if __name__ == "__main__":
    unittest.main()
