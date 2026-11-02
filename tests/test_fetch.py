"""Auswahl der Einladungen aus der Mediathek: auch ohne das Wort im Dateinamen, dann nur nach Prüfung des Texts."""
import tempfile
import unittest
from pathlib import Path

from pipeline import fetch

U = "https://www.witzenhausen.eu/wp-content/uploads/2024/11/"


class Auswahl(unittest.TestCase):
    def test_dateinamen(self):
        self.assertTrue(fetch.ist_einladung(U + "167-2026-Einladung-STVV-10-11-2026.pdf"))
        for f in ("168-2024-Amtl-Bekanntm-STVV-17-12-2024.pdf", "043-2025-OB-Kleinalmerode-20-03-2025.pdf",
                  "070-2025-Seniorenrat-07-05-25.pdf", "164-2024-Amtl-Bekanntm-STeUE-Ausschuss-03-12-2024.pdf",
                  "Nr.-101-2025-OB-Blickershausen-08-07-2025.pdf", "Amtliche-Bekanntmachung-OB-Gertenbach-14-01-2026.pdf",
                  "Amtliche-Bekanntmachung-Nr.028_2025.pdf", "Amtliche-Bekanntmachung.pdf"):
            self.assertTrue(fetch.vielleicht_einladung(U + f), f)
        for f in ("167-2026-Einladung-STVV-10-11-2026.pdf", "050-2025-1-Aenderg-BPl-22-Gem-Wiz-Am-Stieg.pdf",
                  "066-2025-Amtl-Jagdgenossenschaft-Wendershsn-02-05-2025.pdf", "Nr.-085-2025-Kirmes-Hundelshausen.pdf",
                  "Amtliche-Bekanntmachung-BPlan_Unter-den-Weinbergen_Gem.Ermschwerd.pdf"):
            self.assertFalse(fetch.vielleicht_einladung(U + f), f)

    def test_text_entscheidet(self):
        # dem Dateinamen nach möglich (Wahlergebnis Stadtverordnetenversammlung), der Text entscheidet
        self.assertTrue(fetch.vielleicht_einladung(U + "043-2026-Bekanntmachung-Ergebnis-Stavo-15-03-2026.pdf"))
        with tempfile.TemporaryDirectory() as d:
            ja, nein = Path(d) / "ja.txt", Path(d) / "nein.txt"
            ja.write_text("Amtliche Bekanntmachung\nNr. 168/2024\n\nEINLADUNG\nzur Sitzung …\n\nTagesordnung:\n1 Eröffnung", encoding="utf-8")
            nein.write_text("Amtliche Bekanntmachung\nMandatsniederlegung im Ortsbeirat …", encoding="utf-8")
            self.assertTrue(fetch.text_ist_einladung(ja))
            self.assertFalse(fetch.text_ist_einladung(nein))


if __name__ == "__main__":
    unittest.main()
