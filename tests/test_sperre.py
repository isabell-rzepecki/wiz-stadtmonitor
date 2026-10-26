"""Sperre gegen personenbezogene Rohdaten (W6): Funde, keine Fehlalarme im Repository, Hook und .gitignore."""
import json
import os
import sys
import unittest
from pathlib import Path

from pipeline import config

sys.path.insert(0, str(config.ROOT / "tools"))
import sperre  # noqa: E402


def befund(name, inhalt):
    return sperre.befund(Path(name), name, inhalt.encode() if isinstance(inhalt, str) else inhalt)


class Sperre(unittest.TestCase):
    def test_funde(self):
        self.assertIn("verschlüsselt", befund("eigentum_E-1234abcd_2026-10-26.bin", b"{}"))
        self.assertIn("verschlüsselt", befund("pruefung/bestand.sealed", b"x"))
        self.assertIn("verschlüsselt", befund("protokoll/namenzugriff.tsv", "zeit\tpruefer\n"))
        self.assertIn("Exportdatei", befund("daten.json", json.dumps({"format": "wiz-stadtmonitor-erfassung", "eintraege": []})))
        self.assertIn("nettokalt_eur", befund("data/mieten.json", json.dumps([{"gebaeude_id": "x", "nettokalt_eur": 450}])))
        self.assertIn("name_privat_enc", befund("data/x.geojson", json.dumps({"features": [{"properties": {"name_privat_enc": {}}}]})))
        self.assertIn("secret_key", befund("pg.json", json.dumps({"key_id": "x", "secret_key": "y"})))
        self.assertIn("angabe_id", befund("liste.tsv", "angabe_id\tgebaeude\n1\tDEHE\n"))
        self.assertIn("einwilligung", befund("x.jsonl", '{"einwilligung": {"erteilt": true}}\n'))

    def test_keine_fehlalarme(self):
        self.assertIsNone(befund("data/wohnen/mieten_aggregiert.json", json.dumps({"zellen": [{"n": 5, "median": 6.1}]})))
        self.assertIsNone(befund("site/erfassen.js", "const x = { nettokalt_eur: 1, name_privat_enc: 2 };"))
        self.assertIsNone(befund("docs/uebergabe-v0.4.2/schema_mietangabe.json", '{"properties": {"nettokalt_eur": {}}}'))
        self.assertEqual(sperre.main(["--alle"]), 0)  # der Stand im Repository ist frei von Rohdaten

    def test_hook_und_gitignore(self):
        hook = config.ROOT / ".githooks" / "pre-commit"
        self.assertTrue(os.access(hook, os.X_OK))
        self.assertIn("sperre.py\" --staged", hook.read_text(encoding="utf-8"))
        ign = (config.ROOT / ".gitignore").read_text(encoding="utf-8").split()
        for muster in ("*.age", "*.bin", "*.sealed", "intern/", "namenzugriff.tsv"):
            self.assertIn(muster, ign)


if __name__ == "__main__":
    unittest.main()
