"""Erfassungs-App (W4): Einladungscodes wie in der App, sichere Voreinstellungen, kein öffentlicher Link, Offline-Liste vollständig."""
import json
import re
import shutil
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path

from pipeline import config

sys.path.insert(0, str(config.ROOT / "tools"))
import einladung  # noqa: E402
import einrichten  # noqa: E402

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

    def test_einladungsregister(self):
        tmp = Path(tempfile.mkdtemp())
        try:
            reg = tmp / "einladungen.tsv"
            aus = einladung.ausgeben(2, reg, 12, heute=date(2026, 10, 26))
            self.assertEqual([e["bis"] for _, _, e in aus], ["2027-10-26", "2027-10-26"])
            text = reg.read_text(encoding="utf-8")
            for code, eid, e in aus:  # Register mit ID und Hash, nie mit dem Code
                self.assertIn(eid, text)
                self.assertIn(e["hash"], text)
                self.assertNotIn(code, text)
            einladung.widerrufen(aus[0][1], reg, heute=date(2026, 11, 2))
            z = {r["erfasser_id"]: r for r in einladung.register_lesen(reg)}
            self.assertEqual((z[aus[0][1]]["widerrufen"], z[aus[1][1]]["widerrufen"]), ("2026-11-02", ""))
            self.assertEqual(einladung.bis_datum(date(2026, 1, 31), 1), "2026-02-28")
            with self.assertRaises(SystemExit):
                einladung.ausgeben(1, config.ROOT / "einladungen.tsv", 12)  # nie in einem Git-Repository
        finally:
            shutil.rmtree(tmp)

    def test_einrichten_schreibt_nur_oeffentliches_in_stadt_json(self):
        # Kopie der echten stadt.json: Schlüssel und Codes eintragen, Rest der Datei bleibt Zeichen für Zeichen gleich
        tmp = Path(tempfile.mkdtemp())
        try:
            stadt = tmp / "stadt.json"
            original = (config.ROOT / "config" / "stadt.json").read_text(encoding="utf-8")
            stadt.write_text(original, encoding="utf-8")
            pub, blatt = einrichten.schluessel(tmp / "pg" / "pg.json", tmp / "druck", "Testpassphrase 1", stadt, stufe="interaktiv")
            aus, karten = einrichten.codes(3, tmp / "einladungen.tsv", tmp / "druck", stadt, heute=date(2026, 10, 26))
            F = json.loads(stadt.read_text(encoding="utf-8"))["wohnen_eigentum"]["erfassung"]
            self.assertEqual(F["schluessel"], pub)
            self.assertEqual(F["einladungen"], [e for _, _, e in aus])
            text = stadt.read_text(encoding="utf-8")
            self.assertNotRegex(text, r"secret|argon2id")
            for c, _, _ in aus:
                self.assertNotIn(c, text)
                self.assertIn(c, karten.read_text(encoding="utf-8"))
            self.assertIn("erfassen.html", karten.read_text(encoding="utf-8"))
            self.assertEqual(karten.stat().st_mode & 0o777, 0o600)
            self.assertIn("<svg", blatt.read_text(encoding="utf-8"))
            # außerhalb der beiden Felder unverändert: zurückgesetzt ergibt sich die Datei Zeichen für Zeichen
            alt = json.loads(original)["wohnen_eigentum"]["erfassung"]
            kopie = tmp / "kopie.json"
            kopie.write_text(text, encoding="utf-8")
            einrichten.stadt_setzen(kopie, schluessel=alt["schluessel"], einladungen=alt["einladungen"])
            self.assertEqual(kopie.read_text(encoding="utf-8"), original)
            # Widerruf entfernt genau einen Hash
            self.assertEqual(einrichten.widerrufen(aus[0][1], tmp / "einladungen.tsv", stadt, heute=date(2026, 11, 2)), 1)
            F = json.loads(stadt.read_text(encoding="utf-8"))["wohnen_eigentum"]["erfassung"]
            self.assertEqual([e["hash"] for e in F["einladungen"]], [aus[1][2]["hash"], aus[2][2]["hash"]])
            with self.assertRaises(SystemExit):  # Druckblätter nie im Repository
                einrichten.codes(1, tmp / "einladungen.tsv", config.ROOT / "druck", stadt)
        finally:
            shutil.rmtree(tmp)

    def test_konfiguration_ohne_geheimnisse(self):
        # nur Hashes und höchstens ein öffentlicher Schlüssel; nie ein privater Schlüssel oder ein Klartextcode
        for e in F["einladungen"]:  # {hash, bis} oder (früher) nur der Hash
            h = e if isinstance(e, str) else e["hash"]
            self.assertRegex(h, r"^[0-9a-f]{64}$")
            if isinstance(e, dict):
                self.assertEqual(set(e), {"hash", "bis"})
                self.assertRegex(e["bis"], r"^\d{4}-\d{2}-\d{2}$")
        if F["schluessel"]:
            self.assertEqual(set(F["schluessel"]), {"key_id", "alg", "public_key"})
        text = json.dumps(config.STADT["wohnen_eigentum"])
        self.assertNotRegex(text, r"(?i)secret|private_key|privat_schluessel")
        W = F["einwilligung"]
        self.assertTrue(W["version"])
        # Fassung v3: abgeschlossen, Stelle und Kontakt als Platzhalter (die App setzt sie aus dem Datenschutzblock ein)
        self.assertNotIn("entwurf", W["version"].lower())
        self.assertIn("keine anwaltliche Prüfung", W["status"])
        for teil in ("{stelle}", "{kontakt}", "Zweck", "Widerrufscode", "keine Nachteile", "24 Monate", "Aufsichtsbehörde"):
            self.assertIn(teil, W["text"])

    def test_nicht_oeffentlich_verlinkt(self):
        for name in ("index.html", "app.js", "wohnen.html", "wohnen.js", "wohnen-module.js", "erfassen.html", "erfassen.js",
                     "datenschutz.html", "impressum.html"):
            text = (SITE / name).read_text(encoding="utf-8")
            self.assertNotIn("einrichten.html", text, name)
            self.assertNotIn("pruefen.html", text, name)
            if name in ("index.html", "app.js", "wohnen.html", "wohnen.js", "wohnen-module.js"):
                self.assertNotIn("erfassen", text, name)
        for seite in ("erfassen.html", "einrichten.html", "pruefen.html"):
            self.assertIn('content="noindex', (SITE / seite).read_text(encoding="utf-8"))
        # Einrichtungs- und Prüfseite können technisch nichts senden
        for seite in ("einrichten.html", "pruefen.html"):
            self.assertIn("connect-src 'none'", (SITE / seite).read_text(encoding="utf-8"))

    def test_oeffentliche_datei_der_einrichtungsseite(self):
        from nacl.public import PrivateKey
        import base64
        import hashlib
        pub = bytes(PrivateKey.generate().public_key)
        schl = {"key_id": f"pg-20261027-{hashlib.sha256(pub).hexdigest()[:8]}", "alg": "libsodium-sealedbox-x25519",
                "public_key": base64.b64encode(pub).decode()}
        e = [{"hash": "a" * 64, "bis": "2027-10-27"}]
        tmp = Path(tempfile.mkdtemp())
        try:
            stadt = tmp / "stadt.json"
            original = (config.ROOT / "config" / "stadt.json").read_text(encoding="utf-8")
            stadt.write_text(original, encoding="utf-8")
            dateien = []
            for i, inhalt in enumerate(({"schluessel": schl}, {"einladungen": e}, {"einladungen": e})):
                dateien.append(tmp / f"o{i}.json")
                dateien[-1].write_text(json.dumps({"format": "wiz-einrichtung-1", "erstellt": "2026-10-27T10:00:00Z", **inhalt}), encoding="utf-8")
            F = einrichten.uebernehmen(dateien, stadt)
            self.assertEqual((F["schluessel"], F["einladungen"][-1:]), (schl, e))  # doppelte Hashes nur einmal
            self.assertEqual(len(F["einladungen"]), len(json.loads(original)["wohnen_eigentum"]["erfassung"]["einladungen"]) + 1)
            # alles außer den beiden Feldern bleibt Zeichen für Zeichen gleich
            alt = json.loads(original)["wohnen_eigentum"]["erfassung"]
            einrichten.stadt_setzen(stadt, schluessel=alt["schluessel"], einladungen=alt["einladungen"])
            self.assertEqual(stadt.read_text(encoding="utf-8"), original)
            falsch = [{"format": "anders", "schluessel": schl},
                      {"format": "wiz-einrichtung-1", "schluessel": {**schl, "secret_enc": {}}},
                      {"format": "wiz-einrichtung-1", "schluessel": {**schl, "key_id": "pg-20261027-00000000"}},
                      {"format": "wiz-einrichtung-1", "einladungen": [{"hash": "a" * 64, "bis": "2027-10-27", "code": "ABCD"}]},
                      {"format": "wiz-einrichtung-1", "einladungen": e, "register": []},
                      {"format": "wiz-einrichtung-1"}]
            for d in falsch:
                with self.assertRaises(SystemExit, msg=d):
                    einrichten.oeffentlich_pruefen(d)
        finally:
            shutil.rmtree(tmp)

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
