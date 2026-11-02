"""Quellwache (pipeline/quellwache.py) und Text des Issues (tools/quellwache_issue.py); Sitzungen erfunden."""
import importlib.util
import unittest
from pathlib import Path

from pipeline import quellwache as qw

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("quellwache_issue", ROOT / "tools" / "quellwache_issue.py")
issue = importlib.util.module_from_spec(spec)
spec.loader.exec_module(issue)


def sitzung(i, gremium, typ, datum, ortsteil=None, gid=None, veroeff=None):
    return {"id": i, "bekanntmachung": i, "gremium": gremium, "gremium_typ": typ, "ortsteil": ortsteil, "gremium_id": gid,
            "date": datum, "pdf": f"https://example.org/{i.replace('/', '-')}.pdf", "veroeffentlicht": veroeff or datum}


def daten():
    s = [sitzung("051/2026", "Stadtverordnetenversammlung", "stvv", "2026-04-21"),
         sitzung("030/2026", "Stadtverordnetenversammlung", "stvv", "2026-03-10"),
         sitzung("175/2025", "Stadtteilbeirat Albshausen", "stadtteilbeirat", "2025-11-26", "Albshausen"),
         sitzung("010/2026", "Ortsbeirat Albshausen", "ortsbeirat", "2026-01-20", "Albshausen"),
         sitzung("060/2026", "Ortsbeirat Roßbach", "ortsbeirat", "2026-05-04", "Roßbach")]
    t = lambda sid, titel: {"sitzung": sid, "top": "2", "titel": titel}
    v = [{"reference": "a", "process": [t("051/2026", "Genehmigung der Niederschrift über die Sitzung der Stadtverordnetenversammlung am 10.02.2026"),
                                        t("030/2026", "Genehmigung der Niederschrift über die Sitzung der Stadtverordnetenversammlung am 10.03.2026")]},
         {"reference": "b", "process": [t("010/2026", "Genehmigung der Niederschrift vom 26.11.2025")]},
         {"reference": "c", "process": [t("060/2026", "Genehmigung der Niederschrift der Sitzung vom 26.02.2026"),
                                        t("060/2026", "Genehmigung der Niederschrift vom 07.11.2023")]}]
    return {"sitzungen": s, "vorgaenge": v}


class Pruefen(unittest.TestCase):
    def test_luecken(self):
        q = qw.pruefen(daten(), [], "2026-05-05T10:00:00Z", heute="2026-05-05", bekannt=set())
        self.assertEqual([(x["datum"], x["gremium"], x["fundstelle"]) for x in q["luecken"]],
                         [("2026-02-10", "Stadtverordnetenversammlung", "051/2026"), ("2026-02-26", "Ortsbeirat Roßbach", "060/2026")])
        # 10.03.2026 vorhanden; Stadtteilbeirat und Ortsbeirat Albshausen sind ein Gremium; 2023 vor Datenbeginn
        self.assertEqual(q["warnungen"], [])
        self.assertEqual(q["neu"], 2)

    def test_bekannt_und_rechtsakte(self):
        z = [{"nr": "029/2026", "pdf": "https://example.org/029.pdf", "grund": "keine Einladung zum Sitzungstag 2026-02-10 in den Quellen"}]
        q = qw.pruefen(daten(), z, "2026-05-05T10:00:00Z", heute="2026-05-05", bekannt={("2026-02-10", "Stadtverordnetenversammlung")})
        self.assertEqual(len(q["luecken"]), 2, "dieselbe Sitzung nur einmal")
        self.assertEqual([x["neu"] for x in q["luecken"]], [False, True])
        self.assertEqual(q["neu"], 1)

    def test_stillstand(self):
        q = qw.pruefen(daten(), [], "2026-06-01T10:00:00Z", heute="2026-07-01", bekannt=set())
        self.assertEqual(len(q["warnungen"]), 2, "neueste Einladung 04.05.2026 und Abruf am 01.06.2026 zu alt")


class IssueText(unittest.TestCase):
    def test_text(self):
        q = qw.pruefen(daten(), [], "2026-05-05T10:00:00Z", heute="2026-05-05", bekannt={("2026-02-10", "Stadtverordnetenversammlung")})
        t = issue.text(q)
        self.assertTrue(t.startswith(issue.MARKE))
        self.assertIn("- 2026-02-26 · Ortsbeirat Roßbach", t)
        self.assertNotIn("2026-02-10", t, "bekannte Lücken nicht im Issue")


if __name__ == "__main__":
    unittest.main()
