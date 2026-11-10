"""Fundstellen prüfen: Reihenfolge, Grenze je Lauf, erst nach zwei Fehlschlägen tot, Netzfehler unklar, Issue-Text."""
import sys
import unittest

from pipeline import config, fundstellen

sys.path.insert(0, str(config.ROOT / "tools"))
import quellwache_issue  # noqa: E402

DATEN = {"sitzungen": [{"id": "1/2026", "bekanntmachung": "1/2026", "pdf": "https://x/a.pdf"},
                       {"id": "2/2026", "bekanntmachung": "2/2026", "pdf": "https://x/b.pdf"}],
         "vorgaenge": [{"process": [{"sitzung": "2/2026", "bekanntmachung": "2/2026", "pdf": "https://x/b.pdf"},
                                    {"sitzung": "3/2026", "bekanntmachung": "3/2026", "pdf": "https://x/c.pdf"}]}]}


class Fundstellen(unittest.TestCase):
    def test_adressen_einmalig_mit_fundstelle(self):
        self.assertEqual(fundstellen.adressen(DATEN), {"https://x/a.pdf": "1/2026", "https://x/b.pdf": "2/2026", "https://x/c.pdf": "3/2026"})

    def test_zwei_fehlschlaege_grenze_und_reihenfolge(self):
        antworten = {"https://x/a.pdf": 200, "https://x/b.pdf": fundstellen.KEIN_PDF, "https://x/c.pdf": None}
        abgefragt = []
        def abfrage(u):
            abgefragt.append(u)
            return antworten[u]
        stand = {}
        self.assertEqual(fundstellen.pruefen(DATEN, stand, "2026-11-10T01:00:00Z", abfrage, pause=0), [])  # einmal 404: noch nicht tot
        tote = fundstellen.pruefen(DATEN, stand, "2026-11-11T01:00:00Z", abfrage, pause=0)
        self.assertEqual([(t["url"], t["fundstelle"], t["status"], t["seit"]) for t in tote], [("https://x/b.pdf", "2/2026", "kein PDF", "2026-11-10")])
        self.assertEqual(stand["https://x/c.pdf"]["fehl"], 0)  # Netzfehler: unklar, nicht tot
        # Grenze je Lauf: die am längsten nicht geprüfte Adresse zuerst
        abgefragt.clear()
        stand["https://x/a.pdf"]["geprueft"] = "2026-01-01T00:00:00Z"
        fundstellen.pruefen(DATEN, stand, "2026-11-12T01:00:00Z", abfrage, pro_lauf=1, pause=0)
        self.assertEqual(abgefragt, ["https://x/a.pdf"])
        # wieder erreichbar: nicht mehr tot; nicht mehr verlinkt: aus dem Stand entfernt
        antworten["https://x/b.pdf"] = 200
        self.assertEqual(fundstellen.pruefen(DATEN, stand, "2026-11-13T01:00:00Z", abfrage, pause=0), [])
        fundstellen.pruefen({"sitzungen": DATEN["sitzungen"][:1], "vorgaenge": []}, stand, "2026-11-14T01:00:00Z", abfrage, pause=0)
        self.assertEqual(list(stand), ["https://x/a.pdf"])

    def test_issue_text(self):
        q = {"stand": "2026-11-10", "luecken": [], "warnungen": [], "neu": 1,
             "tote_links": [{"url": "https://x/b.pdf", "fundstelle": "2/2026", "status": 404, "seit": "2026-11-10"}]}
        text = quellwache_issue.text(q)
        self.assertIn("Nicht erreichbare Fundstellen", text)
        self.assertIn("Nr. 2/2026 · Status 404 seit 2026-11-10: https://x/b.pdf", text)


if __name__ == "__main__":
    unittest.main()
