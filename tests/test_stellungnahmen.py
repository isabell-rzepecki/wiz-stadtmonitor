"""Stellungnahmen der Ortsbeiräte am Vorgang der Stadtverordnetenversammlung (pipeline/stellungnahmen.py).
Titel nach dem Muster der Einladungen; Sitzungen und Kennungen erfunden."""
import unittest

from pipeline import stellungnahmen as st


def sitzung(i, typ, datum, ortsteil=None):
    return i, {"id": i, "gremium_typ": typ, "date": datum, "ortsteil": ortsteil}


SITZUNGEN = dict([sitzung("S1", "stvv", "2025-11-04"), sitzung("S2", "stvv", "2025-12-16"), sitzung("S3", "stvv", "2026-09-15"),
                  sitzung("A1", "ausschuss", "2025-12-10"),
                  sitzung("O1", "ortsbeirat", "2025-11-17", "Neuseesen"), sitzung("O2", "ortsbeirat", "2025-11-20", "Werleshausen"),
                  sitzung("O3", "ortsbeirat", "2026-03-05", "Werleshausen"), sitzung("O4", "ortsbeirat", "2026-07-06", "Roßbach"),
                  sitzung("O5", "stadtteilbeirat", "2025-11-26", "Neuseesen")])


def vorgang(ref, vorlage, *stationen, punkt=False):
    return {"reference": ref, "vorlage": vorlage, "name": stationen[0][2], "verfahrenspunkt": punkt,
            "process": [{"sitzung": s, "bekanntmachung": s, "gremium": g, "date": SITZUNGEN[s]["date"], "top": "1", "titel": t,
                         "pdf": f"https://example.org/{s}.pdf"} for s, g, t in stationen]}


def vorgaenge():
    return [
        vorgang("EIN", None, ("S1", "Stadtverordnetenversammlung", "Einbringung der Haushaltssatzung mit Haushaltsplan für das Haushaltsjahr 2026")),
        vorgang("HH26", "STV/485", ("A1", "Ausschuss", "Beratung und Beschlussfassung über die Haushaltssatzung mit Haushaltsplan für das Haushaltsjahr 2026"),
                ("S2", "Stadtverordnetenversammlung", "Beratung und Beschlussfassung über die Haushaltssatzung mit Haushaltsplan für das Haushaltsjahr 2026")),
        vorgang("NT25", "STV/483", ("S2", "Stadtverordnetenversammlung", "Beratung und Beschlussfassung über den 1. Nachtrag zur Haushaltssatzung mit Haushaltsplan für das Haushaltsjahr 2025")),
        vorgang("HSK", "STV/484", ("S2", "Stadtverordnetenversammlung", "Beratung und Beschlussfassung über das Haushaltssicherungskonzept Nachtrag 2025")),
        vorgang("INV", "STV/039", ("S3", "Stadtverordnetenversammlung", "Beratung und Beschlussfassung über das Investitionsprogramm 2026 bis 2030")),
        vorgang("O1-4", None, ("O1", "Ortsbeirat Neuseesen", "Stellungnahme zur Haushaltssatzung mit Haushaltsplan und Anlagen für das Haushaltsjahr 2026")),
        vorgang("O1-5", None, ("O1", "Ortsbeirat Neuseesen", "Stellungnahme zum 1. Nachtrag zur Haushaltssatzung mit Haushaltsplan und Anlagen für das Haushaltsjahr 2025")),
        vorgang("O2-4", None, ("O2", "Ortsbeirat Werleshausen", "Stellungnahme zum Haushaltsentwurf der Stadt 2026")),
        vorgang("O3-4", None, ("O3", "Ortsbeirat Werleshausen", "Stellungnahme zum 1. Nachtrag für das Haushaltsjahr 2025")),
        vorgang("O4-3", None, ("O4", "Ortsbeirat Roßbach", "Stellungnahme zum I-Programm 2026 - 2030")),
        vorgang("O5-3", None, ("O5", "Stadtteilbeirat Neuseesen", "Information zum Haushaltsplan 2026")),
        vorgang("O2-1", None, ("O2", "Ortsbeirat Werleshausen", "Genehmigung der Niederschrift"), punkt=True),
    ]


class Schluessel(unittest.TestCase):
    def test_haushalt_nachtrag_invest(self):
        self.assertEqual(st.schluessel("Stellungnahme zum 1. Nachtrag zur Haushaltssatzung mit Haushaltsplan für das Haushaltsjahr 2025", "2025-11-17"),
                         {("nachtrag", "2025")})
        self.assertEqual(st.schluessel("Stellungnahme zur Haushaltssatzung (Entwurf) für das Jahr 2027", "2026-11-12"), {("haushalt", "2027")})
        self.assertEqual(st.schluessel("Stellungnahme zum städtischen Investitionsprogramm 2026 - 2030", "2026-08-14"), {("invest", "2026")})
        self.assertEqual(st.schluessel("Beratung über das Haushaltssicherungskonzept Nachtrag 2025", "2025-12-16"), set())
        self.assertEqual(st.schluessel("Stellungnahme zur geplanten Stromtrasse", "2025-07-25"), set())


class Verknuepfen(unittest.TestCase):
    def setUp(self):
        self.vs = vorgaenge()
        self.zeilen = st.verknuepfen(self.vs, SITZUNGEN, {})
        self.v = {v["reference"]: v for v in self.vs}

    def test_haushalt_zum_beschluss_nicht_zur_einbringung(self):
        refs = [x["reference"] for x in self.v["HH26"]["stellungnahmen"]]
        self.assertEqual(refs, ["O1-4", "O2-4", "O5-3"], "zeitlich sortiert, auch der Stadtteilbeirat")
        self.assertNotIn("stellungnahmen", self.v["EIN"])
        self.assertEqual(self.v["O1-4"]["gehoert_zu"], [{"reference": "HH26", "name": self.v["HH26"]["name"], "ueber": "Haushalt 2026"}])

    def test_zaehlung_nach_ortsbezirk(self):
        self.assertEqual(self.v["HH26"]["ortsbeiraete"]["anzahl"], 2, "Neuseesen (Ortsbeirat und Stadtteilbeirat) und Werleshausen")
        self.assertEqual(self.v["HH26"]["ortsbeiraete"]["von"], 16)

    def test_nachtrag_ohne_sicherungskonzept_und_nicht_nach_dem_beschluss(self):
        self.assertEqual([x["reference"] for x in self.v["NT25"]["stellungnahmen"]], ["O1-5"])
        self.assertNotIn("stellungnahmen", self.v["HSK"])
        z = next(z for z in self.zeilen if z["vorgang"] == "O3-4")
        self.assertEqual(z["ziel"], "", "Stellungnahme vom März 2026 liegt nach dem Beschluss vom Dezember 2025")

    def test_investitionsprogramm_und_art(self):
        x = self.v["INV"]["stellungnahmen"][0]
        self.assertEqual((x["reference"], x["art"], x["ortsteil"]), ("O4-3", "Stellungnahme", "Roßbach"))
        self.assertEqual(self.v["HH26"]["stellungnahmen"][2]["art"], "Beratung")

    def test_verfahrenspunkte_bleiben_aussen_vor(self):
        self.assertNotIn("gehoert_zu", self.v["O2-1"])
        self.assertFalse(any(z["vorgang"] == "O2-1" for z in self.zeilen))

    def test_planverfahren(self):
        vs = vorgaenge()
        vs.append(vorgang("BP", "STV/366", ("S3", "Stadtverordnetenversammlung", "Beratung und Beschlussfassung über die 1. Änderung des Bebauungsplanes Nr. 22")))
        vs.append(vorgang("O4-5", None, ("O4", "Ortsbeirat Roßbach", "Beratung über die 1. Änderung des Bebauungsplanes Nr. 22")))
        st.verknuepfen(vs, SITZUNGEN, {"BP": {"bplan:2246:22:1"}, "O4-5": {"bplan:2246:22:1"}})
        self.assertEqual(vs[-1]["gehoert_zu"][0]["reference"], "BP")


if __name__ == "__main__":
    unittest.main()
