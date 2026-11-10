"""Seiten je Ortsteil: Inhalt aus dem Export (Testdaten), Verweise, Sitemap, keine Verfahrenspunkte, kein Skript."""
import html
import json
import re
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from pipeline import config, ortsteilseiten, site

FIX = Path(__file__).parent / "fixtures" / "vorgaenge.json"


class Ortsteilseiten(unittest.TestCase):
    def test_seiten_aus_testdaten(self):
        with tempfile.TemporaryDirectory() as d:
            export = Path(d) / "export"
            export.mkdir()
            shutil.copy(FIX, export / "vorgaenge.json")
            out = Path(d) / "_site"
            out.mkdir()
            with mock.patch.object(config, "EXPORT", export):
                pfade = ortsteilseiten.erzeugen(out)
            self.assertEqual(len(pfade), len(config.STADT["ortsteile"]) + 1)
            daten = json.loads(FIX.read_text(encoding="utf-8"))
            seite = (out / "ortsteil" / "gertenbach" / "index.html").read_text(encoding="utf-8")
            self.assertIn("<h1>Gertenbach</h1>", seite)
            self.assertIn('href="../../vorgang/stv-066-2026/"', seite)  # Vorgang mit eigener Seite
            for v in daten["vorgaenge"]:
                if v["verfahrenspunkt"]:
                    self.assertNotIn(v["name"], seite)
            self.assertNotIn("<script", seite)
            self.assertIn("Zahlen zum Ortsteil", seite)  # Strukturdaten aus dem Repository
            uebersicht = (out / "ortsteile" / "index.html").read_text(encoding="utf-8")
            self.assertEqual(len(re.findall(r'href="\.\./ortsteil/[^/]+/"', uebersicht)), len(config.STADT["ortsteile"]))

    def test_sitzungsseite(self):
        with tempfile.TemporaryDirectory() as d:
            export = Path(d) / "export"
            export.mkdir()
            shutil.copy(FIX, export / "vorgaenge.json")
            out = Path(d) / "_site"
            out.mkdir()
            with mock.patch.object(config, "EXPORT", export):
                ortsteilseiten.sitzungen_erzeugen(out)
            seite = (out / "sitzungen" / "index.html").read_text(encoding="utf-8")
            daten = json.loads(FIX.read_text(encoding="utf-8"))
            stand = daten["meta"]["generated_at"][:10]
            kommend = [s for s in daten["sitzungen"] if s["date"] >= stand]
            self.assertIn(f"Kommende Sitzungen ({len(kommend)})", seite)
            self.assertEqual(seite.count('<details class="sitzung" open>'), 1 if kommend else 0)
            self.assertIn('href="../vorgang/stv-066-2026/"', seite)  # Punkt öffnet die Seite des Vorgangs
            for v in daten["vorgaenge"]:
                if v["verfahrenspunkt"]:
                    self.assertNotIn(f">{v['name']}<", seite)
            self.assertNotIn("<script", seite)

    def test_gremienseiten(self):
        with tempfile.TemporaryDirectory() as d:
            export = Path(d) / "export"
            export.mkdir()
            shutil.copy(FIX, export / "vorgaenge.json")
            out = Path(d) / "_site"
            out.mkdir()
            with mock.patch.object(config, "EXPORT", export):
                pfade = ortsteilseiten.gremien_erzeugen(out)
            self.assertEqual(len(pfade), len(config.STADT["gremien"]) + 1)
            daten = json.loads(FIX.read_text(encoding="utf-8"))
            stand = daten["meta"]["generated_at"][:10]
            seite = (out / "gremium" / "stvv" / "index.html").read_text(encoding="utf-8")
            kommend = [s for s in daten["sitzungen"] if s.get("gremium_id") == "STVV" and s["date"] >= stand]
            self.assertIn(f"Nächste Sitzungen ({len(kommend)})", seite)
            self.assertIn('href="../../?gremium=Stadtverordnetenversammlung"', seite)
            self.assertNotIn("<script", seite)
            uebersicht = (out / "gremien" / "index.html").read_text(encoding="utf-8")
            self.assertIn('href="../gremium/stvv/"', uebersicht)
            self.assertIn("Frühere Ausschüsse", uebersicht)
            self.assertIn('href="../ortsteil/gertenbach/"', uebersicht)  # Ortsbeiräte über die Ortsteilseiten
            self.assertNotIn('href="../ortsteil/kernstadt/"', uebersicht)  # Kernstadt hat keinen Ortsbeirat

    def test_vorgangsseiten(self):
        from pipeline import vorgangsseiten
        self.assertEqual(vorgangsseiten.slug("STV/073/2026"), "stv-073-2026")
        self.assertEqual(vorgangsseiten.slug("160/2025-TOP4.1"), "160-2025-top4-1")
        with tempfile.TemporaryDirectory() as d:
            export = Path(d) / "export"
            export.mkdir()
            shutil.copy(FIX, export / "vorgaenge.json")
            out = Path(d) / "_site"
            out.mkdir()
            with mock.patch.object(config, "EXPORT", export):
                pfade = vorgangsseiten.erzeugen(out)
                ortsteilseiten.sitzungen_erzeugen(out)
            daten = json.loads(FIX.read_text(encoding="utf-8"))
            ohne = [v for v in daten["vorgaenge"] if not v["verfahrenspunkt"]]
            self.assertEqual(len(pfade), len(ohne))  # Verfahrenspunkte ohne eigene Seite
            v = next(x for x in ohne if x["reference"] == "STV/066/2026")
            seite = (out / "vorgang" / "stv-066-2026" / "index.html").read_text(encoding="utf-8")
            self.assertIn(html.escape(v["name"]), seite)
            self.assertIn('href="../../#STV/066/2026"', seite)  # zurück zur Karte
            self.assertIn(f"Beratungen ({len(v['process'])})", seite)
            self.assertIn("Das Ergebnis ist nicht veröffentlicht", seite)
            self.assertNotIn("<script", seite)
            self.assertIn('href="../vorgang/stv-066-2026/"', (out / "sitzungen" / "index.html").read_text(encoding="utf-8"))

    def test_im_seitenbau_sitemap_und_verweise(self):
        with tempfile.TemporaryDirectory() as d:
            out = site.build(Path(d) / "_site", mit_daten=False)
            karte = (out / "sitemap.xml").read_text(encoding="utf-8")
            self.assertIn("/ortsteile/</loc>", karte)
            self.assertIn("/ortsteil/gertenbach/</loc>", karte)
            self.assertIn("/sitzungen/</loc>", karte)
            self.assertIn("/gremien/</loc>", karte)
            self.assertIn("/gremium/stvv/</loc>", karte)
            self.assertIn("/barrierefreiheit.html</loc>", karte)
            self.assertIn("/einfache-sprache.html</loc>", karte)
            for name in ("barrierefreiheit.html", "einfache-sprache.html"):
                seite = (out / name).read_text(encoding="utf-8")
                self.assertIn('href="mailto:', seite)  # Kontakt aus der Konfiguration
                self.assertNotIn("<script", seite)
                self.assertIn(f'href="{name}"', (out / "index.html").read_text(encoding="utf-8"))
            self.assertIn('href="sitzungen/"', (out / "index.html").read_text(encoding="utf-8"))
            seite = (out / "ortsteil" / "kernstadt" / "index.html").read_text(encoding="utf-8")
            self.assertIn('<link rel="canonical" href="https://stadtmonitor-witzenhausen.de/ortsteil/kernstadt/">', seite)
            self.assertIn(f"Stadtmonitor {config.STADT['stadt']['name']}</title>", seite)
            self.assertIn('href="ortsteile/"', (out / "index.html").read_text(encoding="utf-8"))
            self.assertIn("ortsteil/${encodeURIComponent(area.key)}/", (out / "app.js").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
