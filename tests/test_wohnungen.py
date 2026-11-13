"""Mehrfamilienhäuser: Gebäudeart, Zahl der Wohnungen und Eigentümer-Liste (Schema, Zusammenfassung je Ortsbezirk nach
Regel R10, Karte mit Namen ohne Zahlen, Auswertung je Eigentümer, Sperre). Gebäude-Kennungen, Namen und Zahlen sind erfunden."""
import sys
import unittest

from pipeline import config

sys.path.insert(0, str(config.ROOT / "tools"))
import pruefen  # noqa: E402
import veroeffentlichen as vo  # noqa: E402

MIN = vo.R["privat_anteil_min"]


def rec(gid, **x):
    return {"erfassung_id": f"id-{gid}", "objekt": {"typ": "gebaeude", "id": gid}, "kategorie": x.pop("kategorie", "wu_priv"),
            "beleg_art": "ortskenntnis", "sicherheit": "wahrscheinlich", "erfasst_am": "2026-11-13T10:00:00Z", "erfasser": "E-0000test", **x}


def bestand(*recs, o="gertenbach"):
    je = {r["objekt"]["id"]: {"typ": "eigentum", "datensatz": r} for r in recs}
    geb = {r["objekt"]["id"]: {"properties": {"o": o}} for r in recs}
    return je, geb


class Schema(unittest.TestCase):
    def test_nur_beim_mehrfamilienhaus(self):
        v = pruefen.validator("eigentum")
        gut = [{}, {"gebaeudeart": "efh"}, {"gebaeudeart": "unbekannt"}, {"gebaeudeart": "mfh"},
               {"gebaeudeart": "mfh", "wohnungen_gesamt": 12, "wohnungen_je_kategorie": {"wu_priv": 8, "privat": 4}}]
        schlecht = [{"gebaeudeart": "efh", "wohnungen_gesamt": 4}, {"wohnungen_je_kategorie": {"privat": 2}},
                    {"gebaeudeart": "mfh", "wohnungen_gesamt": 2}, {"gebaeudeart": "mfh", "wohnungen_je_kategorie": {"unklar": 3}},
                    {"gebaeudeart": "mfh", "wohnungen_je_kategorie": {"privat": 0}}, {"gebaeudeart": "reihenhaus"}]
        for z in gut:
            self.assertEqual(list(v.iter_errors(rec("G1", **z))), [], z)
        for z in schlecht:
            self.assertTrue(list(v.iter_errors(rec("G1", **z))), z)


def ez(kategorie, wohnungen, name=None):
    return {"kategorie": kategorie, "wohnungen": wohnungen, **({"name_juristische_person": name} if name else {})}


class EigentuemerListe(unittest.TestCase):
    def test_schema(self):
        v = pruefen.validator("eigentum")
        gut = {"gebaeudeart": "mfh", "wohnungen_gesamt": 12, "eigentuemer": [ez("geno", 5, "Stinkycat eG (Test)"), ez("geno", 3, "Hasenohr eG (Test)"), ez("privat", 2)]}
        self.assertEqual(list(v.iter_errors(rec("G1", kategorie="geno", **gut))), [])
        for schlecht in ({"gebaeudeart": "mfh", "eigentuemer": [ez("privat", 2, "Name")]}, {"gebaeudeart": "efh", "eigentuemer": [ez("geno", 2)]},
                         {"gebaeudeart": "mfh", "eigentuemer": []}, {"gebaeudeart": "mfh", "eigentuemer": [ez("kom", 0)]}):
            self.assertTrue(list(v.iter_errors(rec("G1", **schlecht))), schlecht)

    def test_summen_karte_und_auswertung(self):
        je, geb = bestand(rec("G1", kategorie="geno", name_juristische_person="Stinkycat eG (Test)", gebaeudeart="mfh", wohnungen_gesamt=12,
                              eigentuemer=[ez("geno", 5, "Stinkycat eG (Test)"), ez("geno", 3, "Hasenohr eG (Test)"), ez("privat", 2)]),
                          rec("G2", kategorie="privat", gebaeudeart="mfh", eigentuemer=[ez("privat", 6), ez("geno", 2, "stinkycat  EG (test)")]),
                          rec("G3", kategorie="geno", name_juristische_person="Hasenohr eG (Test)", gebaeudeart="efh"))
        for f in geb.values():
            f["geometry"] = None
        w = vo.wohnungen(je, geb)["gertenbach"]
        self.assertEqual(w["je_kategorie"], {"geno": 10})
        self.assertIsNone(w["privat"])  # 2 Häuser mit privaten Wohnungen < Mindestzahl
        self.assertIsNone(w["wohnungen"])
        props = {f["properties"]["id"]: f["properties"] for f in vo.karte(je, geb, "2026-11-13")["features"]}
        self.assertEqual([x.get("name") for x in props["G1"]["eigentuemer"]], ["Hasenohr eG (Test)", "Stinkycat eG (Test)"])
        self.assertTrue(all("wohnungen" not in x for x in props["G1"]["eigentuemer"]))  # Namen ohne Zahlen
        self.assertEqual(props["G2"]["kategorie"], "geno")  # Haus mit privater Mehrheit erscheint nur mit der Genossenschaft
        self.assertNotIn("privat", str(props["G2"]))
        auswertung = {x["name"]: (x["haeuser"], x["wohnungen"]) for x in vo.je_eigentuemer(je)}
        self.assertEqual(auswertung, {"Stinkycat eG (Test)": (2, 7), "Hasenohr eG (Test)": (2, 3)})

    def test_sperre(self):
        f = {"properties": {"id": "G1", "kategorie": "geno", "eigentuemer": [{"kategorie": "privat"}]}}
        with self.assertRaises(vo.Verstoss):
            vo.pruefe_ausgabe({"eigentum_gebaeude.geojson": {"features": [f]}}, [])
        f["properties"]["eigentuemer"] = [{"kategorie": "geno", "name": "X eG", "wohnungen": 5}]
        with self.assertRaises(vo.Verstoss):
            vo.pruefe_ausgabe({"eigentum_gebaeude.geojson": {"features": [f]}}, [])
        with self.assertRaises(vo.Verstoss):
            vo.pruefe_ausgabe({"eigentum_anteile_ortsbezirk.json": {"ortsbezirke": {}, "je_eigentuemer": [{"name": "Erika", "kategorie": "privat"}]}}, [])


class Zusammenfassung(unittest.TestCase):
    def test_wohnungen_je_kategorie(self):
        je, geb = bestand(rec("G1", gebaeudeart="mfh", wohnungen_gesamt=12, wohnungen_je_kategorie={"wu_priv": 12}),
                          rec("G2", gebaeudeart="mfh", wohnungen_je_kategorie={"geno": 6}),
                          rec("G3", gebaeudeart="efh"), rec("G4"))
        w = vo.wohnungen(je, geb)["gertenbach"]
        self.assertEqual(w, {"mehrfamilienhaeuser": 2, "mit_wohnungszahl": 1, "wohnungen": 12, "je_kategorie": {"geno": 6, "wu_priv": 12},
                             "privat": None, "privat_haeuser": None})

    def test_privat_erst_ab_der_mindestzahl_und_ohne_rueckrechnung(self):
        wenige = [rec(f"P{i}", kategorie="privat", gebaeudeart="mfh", wohnungen_gesamt=4, wohnungen_je_kategorie={"privat": 4})
                  for i in range(MIN - 1)]
        je, geb = bestand(rec("G1", gebaeudeart="mfh", wohnungen_gesamt=10, wohnungen_je_kategorie={"wu_priv": 10}), *wenige)
        w = vo.wohnungen(je, geb)["gertenbach"]
        self.assertIsNone(w["privat"])
        self.assertIsNone(w["wohnungen"])  # sonst ließe sich „privat“ als Differenz zurückrechnen
        self.assertIn("privat_hinweis", w)
        genug = wenige + [rec("PX", kategorie="privat", gebaeudeart="mfh", wohnungen_gesamt=3, wohnungen_je_kategorie={"privat": 3})]
        je, geb = bestand(*genug)
        w = vo.wohnungen(je, geb)["gertenbach"]
        self.assertEqual((w["privat"], w["privat_haeuser"], w["wohnungen"]), (4 * (MIN - 1) + 3, MIN, 4 * (MIN - 1) + 3))

    def test_karte_nur_art_und_gesamtzahl(self):
        je, geb = bestand(rec("G1", gebaeudeart="mfh", wohnungen_gesamt=12, wohnungen_je_kategorie={"wu_priv": 8, "privat": 4}),
                          rec("G2", kategorie="geno", gebaeudeart="efh"), rec("G3", kategorie="privat", gebaeudeart="mfh", wohnungen_gesamt=6))
        for f in geb.values():
            f["geometry"] = None
        props = {f["properties"]["id"]: f["properties"] for f in vo.karte(je, geb, "2026-11-13")["features"]}
        self.assertEqual((props["G1"]["gebaeudeart"], props["G1"]["wohnungen"]), ("mfh", 12))
        self.assertNotIn("wohnungen_je_kategorie", props["G1"])
        self.assertEqual(props["G2"]["gebaeudeart"], "efh")
        self.assertNotIn("G3", props)  # privat nie je Gebäude (R2)
        with self.assertRaises(vo.Verstoss):
            vo.pruefe_ausgabe({"eigentum_gebaeude.geojson": {"features": [{"properties": {
                "id": "G1", "kategorie": "wu_priv", "wohnungen_je_kategorie": {"privat": 4}}}]}}, [])

    def test_sperre(self):
        def ausgabe(w):
            return {"eigentum_anteile_ortsbezirk.json": {"ortsbezirke": {"gertenbach": {
                "gebaeude": 10, "erfasst": 1, "kategorien": {"kom": 1}, "privat": None, "wohnungen": w}}}}
        vo.pruefe_ausgabe(ausgabe({"mehrfamilienhaeuser": 1, "wohnungen": 10, "je_kategorie": {"kom": 10}, "privat": None}), [])
        with self.assertRaises(vo.Verstoss):
            vo.pruefe_ausgabe(ausgabe({"mehrfamilienhaeuser": 2, "wohnungen": 8, "je_kategorie": {}, "privat": 8, "privat_haeuser": 2}), [])
        with self.assertRaises(vo.Verstoss):
            vo.pruefe_ausgabe(ausgabe({"mehrfamilienhaeuser": 2, "wohnungen": 8, "je_kategorie": {"kom": 5}, "privat": None,
                                       "privat_hinweis": "zu wenige Angaben"}), [])


if __name__ == "__main__":
    unittest.main()
