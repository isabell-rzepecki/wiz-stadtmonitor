import json
import unittest
from pathlib import Path

from tools import kontrast

STADT = json.loads((Path(__file__).resolve().parent.parent / "config" / "stadt.json").read_text(encoding="utf-8"))


class Kontrast(unittest.TestCase):
    def test_bekannte_werte(self):
        self.assertAlmostEqual(kontrast.verhaeltnis("#ffffff", "#000000"), 21.0, places=2)
        # Grundfarbe: mit Weiß für Text unzulässig, mit dunklem Text zulässig
        self.assertLess(kontrast.verhaeltnis("#f4726b", "#ffffff"), 3.0)
        self.assertGreater(kontrast.verhaeltnis("#f4726b", "#1a1a1a"), 4.5)

    def test_alle_paare_bestehen(self):
        fails = [r for r in kontrast.pruefen(STADT["gestaltung"]) if not r[-1]]
        self.assertEqual(fails, [])

    def test_css_nutzt_die_werte_der_konfiguration(self):
        css = (Path(__file__).resolve().parent.parent / "site" / "style.css").read_text(encoding="utf-8")
        for k in ("accent_ink", "accent_fill", "text", "text_muted", "hoch", "mittel", "niedrig"):
            self.assertIn(f"--{k.replace('_', '-')}: {STADT['gestaltung']['farben']['hell'][k]};", css, k)

    def test_nur_heller_modus(self):
        for name in ("style.css", "page.css", "404.html"):
            text = (Path(__file__).resolve().parent.parent / "site" / name).read_text(encoding="utf-8")
            self.assertNotIn("prefers-color-scheme: dark", text, name)


if __name__ == "__main__":
    unittest.main()
