"""Wahlen: Bekanntmachung lesen (nur Wahlvorschläge, keine Personen), Prüfung der Summen, Lücken."""
import json
import unittest

from pipeline import config, wahlen

TEXT = """Bekanntmachung des Ergebnisses der Ortsbeiratswahl der Stadt Musterstadt am 15.03.2026
Der Wahlausschuss hat in seiner Sitzung am 25.03.2026 das Ergebnis der Ortsbeiratswahl wie folgt festge-
stellt:

Dohrenbach:
Zur Ortsbeiratswahl waren 415 Personen wahlberechtigt, davon haben 300 Personen gewählt.
Die Wahlbeteiligung betrug 72,29 %
Von den insgesamt abgegebenen Stimmzetteln waren 298 Stimmzettel gültig und 2 Stimmzettel ungültig.
Hieraus resultieren 2.036 gültige Stimmen, die sich folgendermaßen verteilen:

Wahlvorschlag                                                            Stimmen        Stimmen- Sitze
                                                                                        anteil
BÜNDNIS 90/DIE GRÜNEN (GRÜNE)                                                    569      27,95 %          2
Gemeinsam für Dohrenbach (GfDo)                                                 1.467     72,05 %          5
Wahlgebiet insgesamt                                                            2.036                      7

Nr.       Bewerberin/Bewerber                                                              Stimmen
        1 Muster, Erika                                                                        300
PERSON                                                 PARTEI
Muster, Erika                                          GfDo
"""


class Wahlen(unittest.TestCase):
    def test_bekanntmachung(self):
        r = wahlen.bekanntmachung(TEXT)
        self.assertEqual(len(r), 1)
        e = r[0]
        self.assertEqual((e["gebiet"], e["wahlberechtigte"], e["waehlende"], e["beteiligung"], e["stimmen_gueltig"], e["sitze"]),
                         ("Dohrenbach", 415, 300, 72.29, 2036, 7))
        self.assertEqual([(v["name"], v["stimmen"], v["anteil"], v["sitze"]) for v in e["vorschlaege"]],
                         [("BÜNDNIS 90/DIE GRÜNEN (GRÜNE)", 569, 27.95, 2), ("Gemeinsam für Dohrenbach (GfDo)", 1467, 72.05, 5)])
        self.assertNotIn("Muster", json.dumps(r, ensure_ascii=False))

    def test_daten_im_repository(self):
        d = json.loads(wahlen.OUT_REPO.read_text(encoding="utf-8"))
        for e in d["kommunal"]:
            for r in e.get("ergebnisse", []):
                self.assertEqual(r["pruefung"], "ok", (e["id"], r.get("gebiet")))
        for b in d["bund"]:
            self.assertEqual(b["ergebnis"]["pruefung"], "ok", b["id"])
        luecke = [e for e in d["kommunal"] if e["stufe"] == "luecke"]
        self.assertTrue(all("ergebnisse" not in e for e in luecke))

    def test_jede_wahl_mit_stufe(self):
        for w in config.STADT["wahlen"]["kommunal"]:
            self.assertIn(w["stufe"], ("endgültig", "schnellmeldung", "luecke"))
            self.assertTrue(w["stufe_text"])


if __name__ == "__main__":
    unittest.main()
