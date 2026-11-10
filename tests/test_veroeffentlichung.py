"""Veröffentlichen aus der Prüfseite: PHP-Annahme auf dem Server und Übernahme im täglichen Lauf."""
import io
import json
import shutil
import socket
import subprocess
import tempfile
import time
import unittest
import urllib.error
import urllib.request
from pathlib import Path
from unittest import mock

from pipeline import config, veroeffentlichung

L = config.STADT["wohnen_eigentum"]["lizenz"]


def datei(**mehr):
    lz = {"lizenz": L["name"], "lizenz_url": L["url"], "namensnennung": L["namensnennung"]}
    d = {"format": "wiz-veroeffentlichung-1", "stand": "2026-11-10", "dateien": {
        "eigentum_gebaeude.geojson": {"type": "FeatureCollection", "stand": "2026-11-10", "features": [], **lz},
        "eigentum_anteile_ortsbezirk.json": {"stand": "2026-11-10", "mindestzahl_privat": 5, "ortsbezirke": {}, **lz},
        "mieten_aggregiert.json": {"stand": "2026-11-10", "zellen": [], "juristische_personen": [], "angaben_ohne_flaeche": 0, **lz}}}
    d.update(mehr)
    return d


@unittest.skipUnless(shutil.which("php"), "PHP nicht installiert")
class PhpAnnahme(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp())
        (cls.tmp / "intern").mkdir()
        shutil.copy(config.SITE_SRC / "intern" / "veroeffentlichen.php", cls.tmp / "intern" / "veroeffentlichen.php")
        s = socket.socket()
        s.bind(("127.0.0.1", 0))
        cls.port = s.getsockname()[1]
        s.close()
        cls.server = subprocess.Popen(["php", "-S", f"127.0.0.1:{cls.port}", "-t", str(cls.tmp)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        for _ in range(50):
            try:
                socket.create_connection(("127.0.0.1", cls.port), timeout=0.2).close()
                break
            except OSError:
                time.sleep(0.1)

    @classmethod
    def tearDownClass(cls):
        cls.server.terminate()
        cls.server.wait()
        shutil.rmtree(cls.tmp)

    def post(self, body, origin=True, methode="POST", art="application/json"):
        kopf = {"Content-Type": art}
        if origin:
            kopf["Origin"] = f"http://127.0.0.1:{self.port}"
        req = urllib.request.Request(f"http://127.0.0.1:{self.port}/intern/veroeffentlichen.php", method=methode,
                                     data=json.dumps(body).encode() if body is not None else None, headers=kopf)
        try:
            with urllib.request.urlopen(req, timeout=10) as r:
                return r.status, json.loads(r.read())
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read())

    def test_annahme_fassungen_und_abweisungen(self):
        ordner = self.tmp / "veroeffentlicht"
        self.assertEqual(self.post(None, methode="GET")[0], 405)
        self.assertEqual(self.post(datei(), origin=False)[0], 403)  # fremde Seite (ohne Herkunft)
        self.assertEqual(self.post(datei(), art="text/plain")[0], 415)
        self.assertEqual(self.post(datei(probe=True))[0], 422)
        self.assertEqual(self.post({"format": "anders", "dateien": {}})[0], 422)
        schlecht = datei()
        schlecht["dateien"]["mieten_aggregiert.json"]["zellen"] = [{"nettokalt_eur": 450}]
        self.assertEqual(self.post(schlecht)[0], 422)
        privat = datei()
        privat["dateien"]["eigentum_gebaeude.geojson"]["features"] = [{"properties": {"vermieter": "V-012"}}]
        self.assertEqual(self.post(privat)[0], 422)
        self.assertEqual(self.post({"aktion": "zurueck"})[0], 409)  # noch keine vorige Fassung
        self.assertFalse((ordner / "aktuell.json").exists())
        # zwei Veröffentlichungen: die erste wird zur vorigen Fassung, Zurückholen tauscht
        code, d = self.post(datei(stand="2026-11-01"))
        self.assertEqual((code, d["stand"]), (200, "2026-11-01"))
        code, d = self.post(datei(stand="2026-11-10"))
        self.assertEqual((d["stand"], d["vorher"]), ("2026-11-10", "2026-11-01"))
        self.assertEqual(json.loads((ordner / "aktuell.json").read_text())["stand"], "2026-11-10")
        code, d = self.post({"aktion": "zurueck"})
        self.assertEqual((code, d["stand"], d["vorher"]), (200, "2026-11-01", "2026-11-10"))
        self.assertEqual(sorted(p.name for p in ordner.iterdir()), ["aktuell.json", "vorher.json"])


class Uebernahme(unittest.TestCase):
    def test_ohne_datei_bleibt_der_stand(self):
        fehler = urllib.error.HTTPError("u", 404, "nicht da", {}, io.BytesIO(b""))
        with mock.patch.object(veroeffentlichung.net, "get", side_effect=fehler):
            self.assertIsNone(veroeffentlichung.fetch())

    def test_gueltige_datei_wird_geschrieben_probe_abgewiesen(self):
        with tempfile.TemporaryDirectory() as d, mock.patch.object(veroeffentlichung, "RAW", Path(d) / "raw"), \
                mock.patch.object(veroeffentlichung.audit, "abruf"):
            with mock.patch.object(veroeffentlichung.net, "get", return_value=(json.dumps(datei()).encode(), {})):
                aus = veroeffentlichung.fetch(Path(d))
            self.assertEqual(set(aus), {"eigentum_gebaeude.geojson", "eigentum_anteile_ortsbezirk.json", "mieten_aggregiert.json"})
            self.assertTrue((Path(d) / "data" / "wohnen" / "eigentum_anteile_ortsbezirk.json").exists())
            with mock.patch.object(veroeffentlichung.net, "get", return_value=(json.dumps(datei(probe=True)).encode(), {})):
                with self.assertRaises(SystemExit) as e:
                    veroeffentlichung.fetch(Path(d))
            self.assertIn("Probe", str(e.exception))

    def test_hochladen_laesst_veroeffentlichte_dateien_stehen(self):
        skript = (config.ROOT / "tools" / "plesk_hochladen.sh").read_text(encoding="utf-8")
        self.assertIn("--exclude-glob 'veroeffentlicht/*.json'", skript)
        self.assertTrue((config.SITE_SRC / "veroeffentlicht" / ".htaccess").exists())


if __name__ == "__main__":
    unittest.main()
