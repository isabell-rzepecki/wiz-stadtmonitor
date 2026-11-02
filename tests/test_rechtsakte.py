"""Bekanntgemachte Rechtsakte: Lesen der Bekanntmachung und Zuordnung zu Vorgängen (pipeline/rechtsakte.py).
Texte nach dem Muster der amtlichen Bekanntmachungen gekürzt; Tagesordnungspunkte erfunden."""
import unittest

from pipeline import rechtsakte as ra

SATZUNG = """Amtliche Bekanntmachung
der Stadt Witzenhausen
Nr. 113/2026
OR 4.3
Zweite Änderungssatzung
zur Gebührensatzung über die Benutzung der Kindertageseinrichtungen der Stadt Witzenhausen
Aufgrund der §§ 5, 19 der Hessischen Gemeindeordnung hat die
Stadtverordnetenversammlung der Stadt Witzenhausen in ihrer Sitzung am 23.06.2026 die folgende
Satzung beschlossen:
Artikel 1 ... Diese Satzung tritt am 01.08.2026 in Kraft.
Witzenhausen, den 24.06.2026 Der Magistrat (Muster) Bürgermeister"""

OHNE_KOPF = """Amtliche Bekanntmachung der Stadt Witzenhausen Nr. 187/2025
OR 7.2
Aufgrund der §§ 5, 19 HGO hat die Stadtverordnetenversammlung der Stadt Witzenhausen in der Sitzung am 16.12.2025
folgende Satzung zur 7. Änderung der Wasserversorgungssatzung [WVS] beschlossen: Artikel 1"""

HAUSHALT = """Amtliche Bekanntmachung der Stadt Witzenhausen Nr. 039/2026
Bekanntmachung der Haushaltssatzung der Stadt Witzenhausen für das Haushaltsjahr 2026
Die vorstehende Haushaltssatzung für das Haushaltsjahr 2026 wird hiermit öffentlich bekannt gemacht."""

HINWEIS = """Amtliche Bekanntmachung der Stadt Witzenhausen Nr. 164/2025
Die Stadt Witzenhausen weist nachrichtlich darauf hin, dass durch eine Bereitstellung unter https://example.org/x.pdf
am Donnerstag, dem 11.12.2025 die Satzung über die Straßenreinigung (Straßenreinigungssatzung) der Stadt
Witzenhausen öffentlich bekannt gemacht wurde."""

PARK = """Amtliche Bekanntmachung der Stadt Witzenhausen Nr. 029/2026 Gebührenordnung OR 1.3 zur Erhebung von Parkgebühren
Aufgrund § 6 a StVG hat die Stadtverordnetenversammlung der Stadt Witzenhausen am 10. Februar 2026 folgende
Parkgebührenordnung beschlossen:"""


def vorgang(ref, *stationen, punkt=False):
    return {"reference": ref, "verfahrenspunkt": punkt,
            "process": [{"sitzung": s, "top": "1", "date": d, "gremium": g, "titel": t} for s, d, g, t in stationen]}


STVV, HFA, OB = "Stadtverordnetenversammlung", "Haupt-, Finanz- und Rechtsausschuss", "Ortsbeirat Unterrieden"


class Lesen(unittest.TestCase):
    def test_satzung(self):
        r = ra.lesen(SATZUNG)
        self.assertEqual((r["nr"], r["art"], r["aenderung"], r["aufhebung"]), ("113/2026", "aenderung", 2, False))
        self.assertEqual(r["gegenstand"], "Zweite Änderungssatzung zur Gebührensatzung über die Benutzung der Kindertageseinrichtungen der Stadt Witzenhausen")
        self.assertEqual((r["beschluss"], r["inkraft"]), ("2026-06-23", "2026-08-01"))
        self.assertNotIn("Muster", r["gegenstand"])

    def test_gegenstand_aus_dem_beschluss(self):
        r = ra.lesen(OHNE_KOPF)
        self.assertEqual(r["gegenstand"], "Satzung zur 7. Änderung der Wasserversorgungssatzung [WVS]")
        self.assertEqual((r["aenderung"], r["beschluss"]), (7, "2025-12-16"))

    def test_haushalt_ohne_beschlussdatum(self):
        r = ra.lesen(HAUSHALT)
        self.assertEqual((r["art"], r["jahr"], r["beschluss"]), ("haushalt", "2026", None))

    def test_hinweis_und_monatsname(self):
        r = ra.lesen(HINWEIS)
        self.assertEqual(r["art"], "hinweis")
        self.assertTrue(r["gegenstand"].startswith("Satzung über die Straßenreinigung"))
        self.assertEqual(ra.lesen(PARK)["beschluss"], "2026-02-10")


class Zuordnen(unittest.TestCase):
    def setUp(self):
        self.rk = dict(ra.lesen(SATZUNG), veroeffentlicht="2026-06-27", pdf="https://example.org/113.pdf")
        self.vs = [vorgang("STV/031", ("096/2026", "2026-06-23", STVV, "Beratung und Beschlussfassung über die Aufhebungssatzung der ersten Änderungssatzung zur Gebührensatzung über die Benutzung der Kindertageseinrichtungen")),
                   vorgang("STV/032", ("090/2026", "2026-06-17", HFA, "Beratung und Beschlussfassung über die zweite Änderungssatzung zur Gebührensatzung über die Benutzung der Kindertageseinrichtungen"),
                           ("096/2026", "2026-06-23", STVV, "Beratung und Beschlussfassung über die zweite Änderungssatzung zur Gebührensatzung über die Benutzung der Kindertageseinrichtungen")),
                   vorgang("096-TOP2", ("096/2026", "2026-06-23", STVV, "Genehmigung der Niederschrift"), punkt=True)]

    def test_sicher_ueber_beschlussdatum_aenderung_und_aufhebung(self):
        zeilen = ra.zuordnen(self.vs, [self.rk], geprueft={})
        self.assertEqual((zeilen[0]["vorgang"], zeilen[0]["sicherheit"]), ("STV/032", "sicher"))
        e = self.vs[1]["ergebnisse"][0]
        self.assertEqual(e["station"], {"sitzung": "096/2026", "top": "1"}, "Station ist die Stadtverordnetenversammlung am Beschlusstag")
        self.assertNotIn("ergebnisse", self.vs[0], "Aufhebungssatzung passt nicht zur zweiten Änderung")

    def test_ohne_beschlussdatum_nur_moeglicherweise(self):
        rk = dict(self.rk, beschluss=None)
        zeilen = ra.zuordnen(self.vs, [rk], geprueft={})
        self.assertEqual(zeilen[0]["sicherheit"], "möglicherweise")

    def test_gleich_gute_kandidaten_bleiben_offen(self):
        vs = self.vs + [vorgang("STV/099", ("096/2026", "2026-06-23", STVV, "Beratung und Beschlussfassung über die 2. Änderungssatzung zur Gebührensatzung Kindertageseinrichtungen Benutzung"))]
        z = ra.zuordnen(vs, [self.rk], geprueft={})[0]
        self.assertEqual((z["vorgang"], z["sicherheit"], z["grund"]), ("", "keine", "mehrere gleich gute Kandidaten"))

    def test_geprueft_hat_vorrang(self):
        z = ra.zuordnen(self.vs, [self.rk], geprueft={"113/2026": {"vorgang": "STV/031", "geprueft_am": "2026-11-02"}})[0]
        self.assertEqual((z["vorgang"], z["sicherheit"]), ("STV/031", "geprüft"))
        self.assertEqual(self.vs[0]["ergebnisse"][0]["geprueft"], "2026-11-02")

    def test_haushalt_ueber_jahr_ohne_stellungnahmen_der_ortsbeiraete(self):
        rk = dict(ra.lesen(HAUSHALT), veroeffentlicht="2026-03-19", pdf="https://example.org/039.pdf")
        vs = [vorgang("STV/485", ("170/2025", "2025-12-10", HFA, "Beratung und Beschlussfassung über die Haushaltssatzung mit Haushaltsplan für das Haushaltsjahr 2026"),
                      ("177/2025", "2025-12-16", STVV, "Beratung und Beschlussfassung über die Haushaltssatzung mit Haushaltsplan für das Haushaltsjahr 2026")),
              vorgang("145-TOP9", ("145/2025", "2025-11-04", STVV, "Einbringung der Haushaltssatzung mit Haushaltsplan für das Haushaltsjahr 2026")),
              vorgang("171-TOP3", ("171/2025", "2025-11-27", OB, "Beratung und Beschlussfassung über den Entwurf der Haushaltssatzung für das Haushaltsjahr 2026")),
              vorgang("STV/385", ("177/2024", "2024-12-17", STVV, "Beratung und Beschlussfassung über die Haushaltssatzung mit Haushaltsplan für das Haushaltsjahr 2025"))]
        z = ra.zuordnen(vs, [rk], geprueft={})[0]
        self.assertEqual((z["vorgang"], z["sicherheit"]), ("STV/485", "sicher"))
        self.assertEqual(vs[0]["ergebnisse"][0]["station"]["sitzung"], "177/2025", "letzte Beratung: Beschluss der Stadtverordnetenversammlung")

    def test_grund_ohne_einladung_zum_sitzungstag(self):
        rk = dict(ra.lesen(PARK), veroeffentlicht="2026-03-07", pdf="https://example.org/029.pdf")
        self.assertEqual(ra.zuordnen(self.vs, [rk], geprueft={})[0]["grund"], "keine Einladung zum Sitzungstag 2026-02-10 in den Quellen")


if __name__ == "__main__":
    unittest.main()
