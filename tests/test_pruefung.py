"""Prüfung des Exports (check.py) und Inhaltsprüfung der Abrufe (net.pruefen)."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from pipeline import check, config, net


def export(sitzung=None, titel="Haushalt 2026", location=None):
    s = {"id": "001/2026", "gremium": "Stadtverordnetenversammlung", "ort": "Rathaussaal, Am Markt 1", **(sitzung or {})}
    v = {"reference": "001/2026-TOP1", "name": titel, "locations": [location] if location else [],
         "process": [{"sitzung": "001/2026", "pdf": "https://example.org/a.pdf", "titel": titel}]}
    return {"meta": {"parserfehler": 0, "einladungen": 1}, "sitzungen": [s], "vorgaenge": [v]}


class Check(unittest.TestCase):
    def pruefe(self, daten):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "vorgaenge.json"
            p.write_text(json.dumps(daten, ensure_ascii=False), encoding="utf-8")
            with mock.patch.object(config, "VORGAENGE", p), mock.patch.object(config, "EXPORT", Path(tmp)):
                check.check()

    def test_sauberer_export(self):
        self.pruefe(export())

    def test_privatanschrift_als_ort(self):
        with self.assertRaises(SystemExit):
            self.pruefe(export({"ort": "Hause der Familie Muster, Musterweg 1"}))

    def test_personenname_im_titel(self):
        with self.assertRaises(SystemExit):
            self.pruefe(export(titel="Frau Muster stellt sich vor"))
        self.pruefe(export(titel="Frau [Name entfernt] stellt sich vor"))

    def test_geometrie_im_export(self):
        loc = {"method": "x", "confidence": "hoch", "evidence": "x", "source_pdf": "x", "coordinates": [[9.8, 51.3]]}
        with self.assertRaises(SystemExit):
            self.pruefe(export(location=loc))

    def test_leerer_export(self):
        d = export()
        d["sitzungen"], d["vorgaenge"], d["meta"]["einladungen"] = [], [], 0
        with self.assertRaises(SystemExit):
            self.pruefe(d)


class Pruefen(unittest.TestCase):
    def test_dateiarten(self):
        self.assertIsNone(net.pruefen("a.pdf", b"%PDF-1.7 ..."))
        self.assertTrue(net.pruefen("a.pdf", b"<html>Fehler</html>"))
        self.assertIsNone(net.pruefen("a.zip", b"PK\x03\x04"))
        self.assertTrue(net.pruefen("a.xlsx", b"<!DOCTYPE html>"))
        self.assertIsNone(net.pruefen("a.gml", b'<?xml version="1.0"?><wfs:FeatureCollection xmlns:wfs="x">'))
        self.assertTrue(net.pruefen("a.gml", b'<?xml version="1.0"?><ows:ExceptionReport>'))
        self.assertTrue(net.pruefen("a.html", b"  "))


if __name__ == "__main__":
    unittest.main()
