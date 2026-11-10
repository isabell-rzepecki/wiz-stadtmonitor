"""Strukturdaten v1: Gitterauszug, Zuordnung der Zellen, Aggregation mit Schwelle, Wegweiser-Export, Versionsprüfung."""
import io
import json
import unittest
import zipfile
from unittest import mock

from shapely.geometry import box

from pipeline import strukturdaten as sd

G = sd.GEMEINDE


def _zip(name, kopf, zeilen):
    b = io.BytesIO()
    with zipfile.ZipFile(b, "w") as z:
        z.writestr(f"Ordner/{name}", "﻿" + ";".join(kopf) + "\n" + "\n".join(";".join(r) for r in zeilen) + "\n")
    return b.getvalue()


class Gitter(unittest.TestCase):
    def test_filtern_mit_puffer_und_einheitlicher_kennung(self):
        stadt = box(0, 0, 1000, 1000)
        roh = _zip("Zensus_100m-Gitter.csv", ["GITTER_ID_100M", "x_mp_100m", "y_mp_100m", "Einwohner"],
                   [["innen", "450", "450", "12"], ["puffer", "1050", "450", "3"], ["fern", "5050", "450", "7"]])
        kopf, zeilen = sd.filtern(roh, "Zensus_100m-Gitter.csv", stadt)
        self.assertEqual(kopf[0], "GITTER_ID_100m")
        self.assertEqual([z["GITTER_ID_100m"] for z in zeilen], ["innen", "puffer"])  # eine Zelle Puffer, ferne Zellen nicht

    def test_zuordnung_nach_mittelpunkt_mit_flaechenanteil(self):
        fl = [("a", "A", box(0, 0, 1000, 1000), None), ("b", "B", box(1000, 0, 2000, 1000), None)]
        zu = sd.zuordnen({"mitte": (450, 450), "grenze": (980, 450), "aussen": (2040, 450)}, fl)
        self.assertEqual(zu["mitte"][0], "a")
        self.assertAlmostEqual(zu["mitte"][1], 1.0)
        self.assertEqual(zu["grenze"][0], "a")
        self.assertAlmostEqual(zu["grenze"][1], 0.7)  # 70 m der 100 m liegen in a
        self.assertEqual(sd.konfidenz(zu["grenze"][1]), "mittel")
        self.assertIsNone(zu["aussen"][0])  # Mittelpunkt außerhalb: nicht zugeordnet, Fläche im Gebiet gemeldet
        self.assertAlmostEqual(zu["aussen"][2], 0.1)


class Aggregation(unittest.TestCase):
    def tab(self):
        # Raum a: viele Personen; Raum b: klein (Nenner unter 50); Raum c: Teilgruppen weichen stark ab (Geheimhaltung)
        alter = {}
        for i in range(10):
            alter[f"a{i}"] = {"Insgesamt_Bevoelkerung": "20", "Unter18": "4", "a18bis29": "3", "a30bis49": "5", "a50bis64": "4", "a65undaelter": "4"}
        alter["b0"] = {"Insgesamt_Bevoelkerung": "30", "Unter18": "5", "a18bis29": "5", "a30bis49": "10", "a50bis64": "5", "a65undaelter": "5"}
        for i in range(4):
            alter[f"c{i}"] = {"Insgesamt_Bevoelkerung": "20", "Unter18": "–", "a18bis29": "3", "a30bis49": "5", "a50bis64": "4", "a65undaelter": "4"}
        einw = {k: {"Einwohner": v["Insgesamt_Bevoelkerung"]} for k, v in alter.items()}
        dalter = {k: {"Durchschnittsalter": "40,00" if k.startswith("a") else "60,00"} for k in alter}
        dalter["a0"] = {"Durchschnittsalter": "–"}  # ohne Wert: nicht im Mittel
        woh = {k: {"Insgesamt_Wohnungen": "10", "FreiEFH": "6", "EFH_DHH": "–", "EFH_Reihenhaus": "–", "Freist_ZFH": "2", "ZFH_DHH": "–",
                   "ZFH_Reihenhaus": "–", "MFH_3bis6Wohnungen": "2", "MFH_7bis12Wohnungen": "–", "MFH_13undmehrWohnungen": "–",
                   "AndererGebaeudetyp": "–"} for k in alter}
        zuo = {k: k[0] for k in alter}
        return {"einwohner": einw, "alter": alter, "durchschnittsalter": dalter, "wohnungen_typ": woh}, zuo

    def test_summen_anteile_schwelle_und_gewichtetes_mittel(self):
        tab, zuo = self.tab()
        w, gruende = sd.zensus_werte(tab, zuo, ["a", "b", "c"], {"nenner_min": 50, "abweichung_max": 0.10})
        self.assertEqual(w[("a", "zensus_einwohner")][:2], (200, "abgeleitet"))
        self.assertEqual(w[("a", "zensus_anteil_ab65")][:2], (20.0, "abgeleitet"))  # 40 von 200
        self.assertEqual(w[("a", "zensus_anteil_unter18")][0], 20.0)
        # klein: Anzahl ja, Anteil nein
        self.assertEqual(w[("b", "zensus_einwohner")][0], 30)
        self.assertEqual(w[("b", "zensus_anteil_ab65")][:2], (None, "fehlt"))
        # Teilgruppen 16 statt 20 je Zelle (20 % Abweichung): kein Anteil, Grund im Audit
        self.assertEqual(w[("c", "zensus_anteil_ab65")][:2], (None, "fehlt"))
        self.assertTrue(any(g["raum_id"] == "c" and "Geheimhaltung" in g["grund"] for g in gruende))
        # Mittelwert gewichtet mit Einwohnern, Zelle ohne Wert nicht gezählt
        self.assertEqual(w[("a", "zensus_durchschnittsalter")][0], 40.0)
        self.assertIn("gewichtet", w[("a", "zensus_durchschnittsalter")][2])
        # Gemeinde: alle zugeordneten Zellen; Anteil Ein- und Zweifamilienhäuser aus Zähler und Nenner
        self.assertEqual(w[(G, "zensus_einwohner")][0], 200 + 30 + 80)
        self.assertEqual(w[("a", "zensus_anteil_wohnungen_efh_zfh")][0], 80.0)
        self.assertEqual(w[("a", "zensus_wohnungen_efh_zfh")][0], 80)


class Wegweiser(unittest.TestCase):
    TEXT = ('Altenquotient\nWitzenhausen (im Werra-Meißner-Kreis), Eschwege\n\nKommune;"2022\nAltenquotient (x)";"2023\nAltenquotient (x)"\n'
            'Witzenhausen;42,9;43,2\nEschwege;1.047,5;k.A.\n\n"k.A. = keine Angaben"\n')

    def test_export_lesen(self):
        z = sd.wegweiser_csv(self.TEXT, {"Witzenhausen": "witzenhausen", "Eschwege": "eschwege"})
        self.assertIn(("witzenhausen", 2023, 43.2), z)
        self.assertIn(("eschwege", 2022, 1047.5), z)
        self.assertIn(("eschwege", 2023, None), z)

    def test_geaenderte_schnittstelle_bricht_ab(self):
        antwort = json.dumps({"info": {"version": "9.9.9"}}).encode()
        import tempfile
        from pathlib import Path
        with tempfile.TemporaryDirectory() as d, mock.patch.object(sd.net, "get", return_value=(antwort, {})), \
                mock.patch.object(sd, "_protokoll"), mock.patch.object(sd, "RAW", Path(d)):
            with self.assertRaises(SystemExit) as e:
                sd.fetch_wegweiser()
        self.assertIn("9.9.9", str(e.exception))


class Konfiguration(unittest.TestCase):
    def test_vertrag_und_entscheidungen(self):
        S = sd.S
        self.assertEqual(S["vertrag_version"], "1")
        self.assertEqual(S["schwelle"], {"nenner_min": 50, "abweichung_max": 0.10})
        self.assertEqual(S["wegweiser"]["kommunen"][:2], ["witzenhausen", "werra-meissner-kreis-lk"])
        self.assertEqual(len(S["wegweiser"]["indikatoren"]), 12)
        self.assertNotIn("eigentuemerquote", sd.config.STADT["wohnen"]["zensus"]["gitter"])  # nur je Gemeinde


if __name__ == "__main__":
    unittest.main()
