"""Angebotsmieten je Kreis aus der Datentabelle des Deutschlandatlas (pipeline/wohnen.angebotsmieten); Tabelle erfunden
im Aufbau der echten Datei (Titelblatt mit Stand, Kreisblätter mit Indikatorkürzel in der Kopfzeile)."""
import tempfile
import unittest
from pathlib import Path

import openpyxl

from pipeline import wohnen


def mappe(pfad, mit_indikator=True):
    wb = openpyxl.Workbook()
    wb.active.title = "Titel"
    wb["Titel"].append(["Datentabellen"])
    wb["Titel"].append(["Stand: 25.09.2026"])
    for blatt, wert in (("Deutschlandatlas_KRS1222", 6.1), ("Deutschlandatlas_KRS1224", 6.968)):
        ws = wb.create_sheet(blatt)
        ws.append([f"{blatt}: Beschreibung"])
        ws.append(["zur Inhaltsübersicht"])
        kopf = "Indikatorkürzel: preis_miet\n\nWiedervermietungsmieten inserierter Wohnungen (Angebotsmieten nettokalt) im Jahr 2025 in € je m²"
        ws.append(["KRS", "Kreisname", "Indikatorkürzel: fl_suv\n\nFläche", kopf if mit_indikator else "Indikatorkürzel: x\n\ny"])
        ws.append([6636000, "Werra-Meißner-Kreis", 10.0, wert])
        ws.append([6633000, "Kassel", 12.0, 8.861])
        ws.append([9162000, "München", 40.0, 21.5])
    wb.save(pfad)


class Angebotsmieten(unittest.TestCase):
    def test_neuestes_blatt_und_vergleichskreise(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "da.xlsx"
            mappe(p)
            a = wohnen.angebotsmieten(p)
        self.assertEqual((a["jahr"], a["blatt"], a["stand"]), (2025, "Deutschlandatlas_KRS1224", "25.09.2026"))
        self.assertEqual([(k["name"], k["wert"]) for k in a["kreise"]], [("Werra-Meißner-Kreis", 6.97), ("Landkreis Kassel", 8.86)])
        self.assertTrue(a["indikator"].startswith("Wiedervermietungsmieten"))

    def test_ohne_indikator_oder_datei(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "da.xlsx"
            mappe(p, mit_indikator=False)
            self.assertIsNone(wohnen.angebotsmieten(p))
            self.assertIsNone(wohnen.angebotsmieten(Path(d) / "fehlt.xlsx"))


if __name__ == "__main__":
    unittest.main()
