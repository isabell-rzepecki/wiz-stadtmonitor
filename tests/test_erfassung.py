"""Erfassungs-App (W4): Einladungscodes wie in der App, sichere Voreinstellungen, kein öffentlicher Link, Offline-Liste vollständig."""
import json
import re
import sys
import unittest

from pipeline import config

sys.path.insert(0, str(config.ROOT / "tools"))
import einladung  # noqa: E402

SITE = config.ROOT / "site"
F = config.STADT["wohnen_eigentum"]["erfassung"]


class Erfassung(unittest.TestCase):
    def test_einladungscode_wie_in_der_app(self):
        # gleicher Testcode wie im Browsertest; dort leitet erfassen.js dieselbe Erfasser-ID ab
        self.assertEqual(einladung.erfasser_id("abcd efgh jkmn pqrs"), "E-227c7469")
        self.assertEqual(einladung.code_hash("ABCD-EFGH-JKMN-PQRS"), einladung.code_hash("abcd-efgh-jkmn-pqrs"))
        self.assertEqual(einladung.normieren("o1L0-ABCD-EFGH-JKMN"), "0110ABCDEFGHJKMN")
        c = einladung.neu()
        self.assertTrue(einladung.gueltig(c))
        self.assertRegex(c, r"^[0-9A-HJKMNP-TV-Z]{4}(-[0-9A-HJKMNP-TV-Z]{4}){3}$")
        self.assertFalse(einladung.gueltig("ABCD-EFGH"))

    def test_konfiguration_ohne_geheimnisse(self):
        # nur Hashes und höchstens ein öffentlicher Schlüssel; nie ein privater Schlüssel oder ein Klartextcode
        for h in F["einladungen"]:
            self.assertRegex(h, r"^[0-9a-f]{64}$")
        if F["schluessel"]:
            self.assertEqual(set(F["schluessel"]), {"key_id", "alg", "public_key"})
        text = json.dumps(config.STADT["wohnen_eigentum"])
        self.assertNotRegex(text, r"(?i)secret|private_key|privat_schluessel")
        self.assertTrue(F["einwilligung"]["version"])

    def test_nicht_oeffentlich_verlinkt(self):
        for name in ("index.html", "app.js", "wohnen.html", "wohnen.js", "wohnen-module.js"):
            self.assertNotIn("erfassen", (SITE / name).read_text(encoding="utf-8"), name)
        self.assertIn('content="noindex', (SITE / "erfassen.html").read_text(encoding="utf-8"))

    def test_offline_liste_vollstaendig(self):
        sw = (SITE / "erfassen-sw.js").read_text(encoding="utf-8")
        dateien = re.findall(r'"([\w./-]+\.(?:html|js|css|svg|json|webmanifest))"', sw.split("const KACHELN")[0])
        erzeugt = {"stadt.json", "schemas/erfassung_eigentum.json", "schemas/mietangabe.json", "data/export/karte/gebaeude_index.json"}
        for d in dateien:
            if d not in erzeugt:
                self.assertTrue((SITE / d).exists(), d)
        # alles, was erfassen.html lädt, steht in der Liste
        html = (SITE / "erfassen.html").read_text(encoding="utf-8")
        for d in re.findall(r'(?:src|href)="([\w./-]+)"', html):
            self.assertIn(d, dateien, d)

    def test_schema_mit_vorlaeufigem_vermieterschluessel(self):
        s = json.loads((config.ROOT / "docs" / "uebergabe-v0.4.2" / "schema_erfassung_eigentum.json").read_text(encoding="utf-8"))
        muster = re.compile(s["properties"]["vermieter_schluessel"]["pattern"])
        for ok in ("V-neu", "V-017", "JP:Wohnbau GmbH"):
            self.assertTrue(muster.search(ok), ok)
        self.assertFalse(muster.search("Erika Muster"))


if __name__ == "__main__":
    unittest.main()
