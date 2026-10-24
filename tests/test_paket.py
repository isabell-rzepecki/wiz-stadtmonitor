"""Datenpaket: keine Angaben aus den Umringen der Bauleitplanung (nur nicht kommerziell), nur die Plannummer."""
import csv
import tempfile
import unittest
from pathlib import Path

from pipeline import package


def vorgang():
    return {"vorgaenge": [{
        "plans": [{"key": "bplan:2246:18:0", "titel": "Muster-Plangebiet", "treffer": "eindeutig", "evidence": "Bebauungsplan Nr. 18"}],
        "locations": [
            {"level": "ortsteil", "name": "Kernstadt"},
            {"level": "bebauungsplan", "name": "Muster-Plangebiet", "plan": "bplan:2246:18:0", "lon": 9.8, "lat": 51.3},
            {"level": "flurstueck", "name": "Gemarkung Witzenhausen, Flur 2, Flurstück 169", "lon": 9.85, "lat": 51.34}],
        "overlaps": [{"ebene": "tws", "ort": "Muster-Plangebiet"}, {"ebene": "tws", "ort": "Gemarkung Witzenhausen, Flur 2, Flurstück 169"}],
    }]}


class Paket(unittest.TestCase):
    def test_ohne_planumringe(self):
        v = package.ohne_planumringe(vorgang())["vorgaenge"][0]
        self.assertNotIn("Muster-Plangebiet", str(v))
        self.assertEqual(v["plans"], [{"key": "bplan:2246:18:0", "treffer": "eindeutig", "evidence": "Bebauungsplan Nr. 18"}])
        plan = next(l for l in v["locations"] if l["level"] == "bebauungsplan")
        self.assertNotIn("lon", plan)
        self.assertEqual(plan["name"], "bplan:2246:18:0")
        flst = next(l for l in v["locations"] if l["level"] == "flurstueck")  # Flurstückspunkte (dl-de/zero) bleiben
        self.assertEqual((flst["lon"], flst["lat"]), (9.85, 51.34))
        self.assertEqual([o["ort"] for o in v["overlaps"]], ["Gemarkung Witzenhausen, Flur 2, Flurstück 169"])

    def test_audit_ohne_plantitel(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "verortung_bauleitplanung.tsv"
            with p.open("w", encoding="utf-8", newline="") as f:
                w = csv.writer(f, delimiter="\t", lineterminator="\n")
                w.writerows([["vorgang", "plan_key", "plan_titel"], ["STV/1/2026", "bplan:2246:18:0", "Muster-Plangebiet"]])
            text = package._tsv(p, **package.AUDIT_FILTER[p.name])
        self.assertEqual(text, "vorgang\tplan_key\nSTV/1/2026\tbplan:2246:18:0\n")


if __name__ == "__main__":
    unittest.main()
