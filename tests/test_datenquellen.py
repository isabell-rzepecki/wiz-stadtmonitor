import csv
import json
import tempfile
import unittest
from pathlib import Path

from pipeline import site
from tools import datenquellen

ROOT = Path(__file__).resolve().parent.parent


class Datenquellen(unittest.TestCase):
    def test_data_sources_aktuell(self):
        self.assertEqual((ROOT / "DATA_SOURCES.md").read_text(encoding="utf-8"), datenquellen.markdown(),
                         "DATA_SOURCES.md veraltet: python tools/datenquellen.py ausführen")

    def test_attribution_verweist_auf_register(self):
        ids = {r["id"] for r in csv.DictReader((ROOT / "data" / "quellen_register.tsv").open(encoding="utf-8"), delimiter="\t")}
        for a in datenquellen.lesen(datenquellen.ATTRIBUTION):
            for q in a["quellen"].split(","):
                self.assertIn(q, ids, q)

    def test_namensnennungen_der_seite(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "n.json"
            site.namensnennungen(p)
            liste = json.loads(p.read_text(encoding="utf-8"))
        texte = " ".join(a["text"] for a in liste)
        self.assertIn("nicht kommerzielle", texte)
        self.assertIn("basemap.de", texte)
        self.assertNotIn("(Jahr)", texte)
        self.assertNotIn("Zensus", texte, "nur genutzte Quellen")


if __name__ == "__main__":
    unittest.main()
