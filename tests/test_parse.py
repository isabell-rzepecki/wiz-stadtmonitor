import json
import unittest
from pathlib import Path

from pipeline import build, parse

FIX = Path(__file__).resolve().parent / "fixtures" / "einladungen"


def lies(name):
    return parse.einladung((FIX / name).read_text(encoding="utf-8"))


class Kopf(unittest.TestCase):
    def test_stvv_zwei_tage_und_unterpunkte(self):
        e = lies("177-2025-Einladung-STVV-16-12-2025.txt")
        self.assertEqual((e["nr"], e["gremium_id"], e["date"], e["time"]), ("177/2025", "STVV", "2025-12-16", "18:00"))
        self.assertEqual([t["date"] for t in e["termine"]], ["2025-12-16", "2025-12-18"])
        self.assertEqual(e["ort"], "Rathaussaal, Am Markt 1")
        tops = {t["top"]: t for t in e["tops"]}
        self.assertEqual(tops["8"]["vorlage"], "STV/488/2025")
        self.assertIn("Hundesteuer", tops["8"]["titel"])
        self.assertEqual(tops["19.2"]["vorlage"], "STV/473/2025")
        self.assertIsNone(tops["23"]["vorlage"])
        self.assertEqual(e["tops"][-1]["top"], "23", "Ende vor „gez.“")

    def test_nummer_ohne_jahr(self):
        e = lies("149-2026-Einladung-OB-Ermschwerd.txt")
        self.assertEqual((e["nr"], e["nr_abgeleitet"], e["gremium_id"], e["ortsteil"]), ("149/2026", True, "OB-ermschwerd", "Ermschwerd"))

    def test_nicht_oeffentlich_ohne_tagesordnung(self):
        e = lies("011-2025-Amtl-nicht-oeffentl-Einladung-HFR-28-01-2025.txt")
        self.assertFalse(e["oeffentlich"])
        self.assertEqual(e["tops"], [])
        self.assertEqual(e["gremium_id"], "HFR-2021")
        self.assertEqual(e["ort"], "Rathaussaal, Am Markt 1")

    def test_privatanschrift_wird_nicht_uebernommen(self):
        e = lies("160-2024-Stadtteilbeirat-Albshausen-21-11-2024.txt")
        self.assertEqual((e["gremium_id"], e["gremium_typ"], e["ortsteil"]), ("STB-albshausen", "stadtteilbeirat", "Albshausen"))
        self.assertTrue(e["ort"].startswith("Privatanschrift"))
        roh = json.dumps(e, ensure_ascii=False)
        self.assertNotIn("Beispiel", roh)
        self.assertNotIn("Musterweg", roh)

    def test_privatanschrift_auch_ohne_bei_am_ende(self):
        for zeile in ("um 19:00 Uhr, im Hause der Familie Muster, Musterweg 4", "um 19:00 Uhr in der Wohnung von Herrn Muster"):
            k = parse.kopf(f"Amtliche Bekanntmachung Nr. 1/2025 Einladung zur Sitzung des Ortsbeirates Gertenbach am 01.02.2025 {zeile}")
            self.assertTrue(k["ort"].startswith("Privatanschrift"), k["ort"])

    def test_namen_in_titeln_entfernt(self):
        f = parse.ohne_namen
        self.assertEqual(f("Frau Muster (Tourist-Info) stellt sich vor"), "Frau [Name entfernt] (Tourist-Info) stellt sich vor")
        self.assertEqual(f("Ortstermin mit Herrn Max Muster am 02.07.2026"), "Ortstermin mit Herrn [Name entfernt] am 02.07.2026")
        self.assertEqual(f("Antrag der Stadtverordneten Erika Muster vom 13.04.2025 zu X"),
                         "Antrag der Stadtverordneten [Name entfernt] vom 13.04.2025 zu X")
        self.assertEqual(f("Erinnerungen an Ortsvorsteherin Erika Muster"), "Erinnerungen an Ortsvorsteherin [Name entfernt]")
        self.assertEqual(f("Beschilderung L 3302 (eingeladen: M. Muster)"), "Beschilderung L 3302 (eingeladen: [Name entfernt])")
        self.assertEqual(f("Vortrag (Referent Dr. Max Muster, Stiftung)"), "Vortrag (Referent [Name entfernt], Stiftung)")
        self.assertEqual(f("Jugendraum (Erika Muster/Max Beispiel)"), "Jugendraum ([Name entfernt])")
        # ohne Anrede nach „mit“, auch zwei Personen; Orte nach „mit“ bleiben
        self.assertEqual(f("Bericht über Gespräch mit Erika Muster und weiteres Vorgehen"), "Bericht über Gespräch mit [Name entfernt] und weiteres Vorgehen")
        self.assertEqual(f("Gespräch mit Erika Muster, Fachdienst Soziales"), "Gespräch mit [Name entfernt], Fachdienst Soziales")
        self.assertEqual(f("Ortstermine mit Max Muster und Erika Beispiel-Muster an der Brücke"), "Ortstermine mit [Name entfernt] an der Brücke")
        for t in ("Wanderweg mit Schloss Rothestein", "Partnerschaft mit Bad Sooden-Allendorf", "Kooperation mit Neu Eichenberg",
                  "Zusammenarbeit mit dem Deutschen Roten Kreuz", "Gespräch mit Herrn [Name entfernt]"):
            self.assertEqual(f(t), t)
        # Funktionen, Gliederungspunkte und Orte bleiben
        for t in ("Bericht des Herrn Bürgermeister", "Frau [Name entfernt] (Polizei Witzenhausen) stellt sich vor", "Wanderweg Frau Holle", "Frau-Holle-Pfad", "Bericht des Bürgermeisters",
                  "Antrag der Stadtverordnetenfraktion SPD vom 01.02.2025", "Bürgerinnen und Bürger haben das Wort"):
            self.assertEqual(f(t), t)

    def test_antrag_einzelner_stadtverordneter_ohne_namen(self):
        e = lies("074-2025-Einladung-BuV-Ausschuss-13-05-2025.txt")
        roh = json.dumps(e, ensure_ascii=False)
        self.assertNotIn("Muster", roh)
        self.assertIn("Stadtverordneten [Name entfernt] vom 13.04.2025", roh)

    def test_vorlage_ohne_doppelpunkt_und_konstituierung(self):
        e = lies("051-2026-Einladung-STVV-Konstituierung-21-04-2026.txt")
        self.assertEqual(e["gremium"], "Stadtverordnetenversammlung")
        self.assertEqual(e["tops"][0]["vorlage"], "STV/001/2026")

    def test_nummer_laut_kopf_nicht_dateiname(self):
        e = lies("141-2026-Einladung-Soz-09-09-2026.txt")
        self.assertEqual((e["nr"], e["gremium_id"]), ("142/2026", "SozA"))

    def test_bezuege_im_titel(self):
        e = lies("074-2025-Einladung-BuV-Ausschuss-13-05-2025.txt")
        t = e["tops"][0]
        self.assertEqual(t["vorlage"], "STV/416/2025")
        self.assertEqual(t["bezuege"], ["STV/479/2020", "STV/228/2023"])


class Verfahren(unittest.TestCase):
    def test_verfahrenspunkte(self):
        e = lies("106-2025-Einladung-OB-Neuseesen-25-07-2025.txt")
        flags = {t["top"]: build.verfahrenspunkt(t) for t in e["tops"]}
        self.assertEqual(flags, {"1": True, "2": True, "3": True, "4": False, "5": False, "6": False, "7": True})

    def test_planverweise(self):
        s = {"gremium_typ": "ausschuss", "ortsteil": None}
        v = build.plan_verweise("Aufstellung der 29. Änderung des Bebauungsplanes Nr. 8 Gemarkung Witzenhausen „Anschluss“", s)
        self.assertEqual((v[0]["nr"], v[0]["aenderung"], v[0]["gemarkung_nr"]), ("8", 29, "2246"))
        ob = {"gremium_typ": "ortsbeirat", "ortsteil": "Roßbach"}
        self.assertEqual(build.plan_verweise("Antrag auf Überplanung des Bebauungsplanes Nr. 5", ob)[0]["gemarkung_nr"], "2214")
        self.assertIsNone(build.plan_verweise("Änderung des Bebauungsplanes Nr. 5", s)[0]["gemarkung_nr"])
        f = build.plan_verweise("Aufstellung der 45. Änderung des Flächennutzungsplanes Gemarkung Witzenhausen", s)
        self.assertEqual((f[0]["art"], f[0]["aenderung"]), ("fplan", 45))


if __name__ == "__main__":
    unittest.main()
