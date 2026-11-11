import json
import tempfile
import unittest
from pathlib import Path

from pipeline import site


class Seite(unittest.TestCase):
    def test_zusammenstellen(self):
        with tempfile.TemporaryDirectory() as d:
            out = site.build(Path(d) / "_site")
            for f in ("index.html", "app.js", "timeline.js", "style.css", "stadt.json", "fonts/LICENSE-LilitaOne.txt",
                      "fonts/LICENSE-SpaceMono.txt", "vendor/leaflet/LICENSE"):
                self.assertTrue((out / f).exists(), f)
            self.assertIn("ortsteile", json.loads((out / "stadt.json").read_text(encoding="utf-8")))

    def test_fusszeile_auf_allen_unterseiten(self):
        # eine gemeinsame Fußzeile mit Wegen relativ zur Tiefe der Seite; die eigene Seite ist markiert
        with tempfile.TemporaryDirectory() as d:
            out = site.build(Path(d) / "_site", mit_daten=False)
            for pfad, vor, hier in (("impressum.html", "", "impressum.html"), ("teilen/index.html", "../", "teilen/"),
                                    ("ortsteil/gertenbach/index.html", "../../", None), ("quellen.html", "", "quellen.html")):
                seite = (out / pfad).read_text(encoding="utf-8")
                self.assertEqual(seite.count('<footer class="page-foot">'), 1, pfad)
                self.assertIn('class="fuss-raster"', seite, pfad)
                self.assertIn(f'href="{vor}gremien/"', seite, pfad)
                self.assertIn(f'href="{vor}barrierefreiheit.html"', seite, pfad)
                self.assertIn('href="mailto:', seite, pfad)
                for abzeichen in ("Nichtkommerziell", "Open Source", "Trackingfrei"):
                    self.assertIn(f"</svg>{abzeichen}</li>", seite, pfad)
                self.assertIn('<span data-cfg="stadt.name">Witzenhausen</span>', seite.split('class="fuss-brand"')[1], pfad)
                if hier:
                    self.assertIn(f'href="{vor}{hier}" aria-current="page"', seite, pfad)
                self.assertEqual(seite.count('aria-current="page"'), 1 if hier else 0, pfad)
            self.assertNotIn("fuss-raster", (out / "intern" / "index.html").read_text(encoding="utf-8"))

    def test_wortmarke_und_vorschau_beim_teilen(self):
        # Wortmarke „Stadtmonitor <Stadt>“ mit Link zur Startseite auf allen Seiten; Vorschau nur auf öffentlichen Seiten
        with tempfile.TemporaryDirectory() as d:
            out = site.build(Path(d) / "_site", mit_daten=False)
            name = site.config.STADT["stadt"]["name"]
            for seite in ("datenschutz.html", "wohnen.html", "quellen.html", "intern/index.html", "intern/pruefen.html"):
                text = (out / seite).read_text(encoding="utf-8")
                self.assertRegex(text, rf'class="page-brand" href="(\.\./|\./)"><img [^>]+>Stadtmonitor <span data-cfg="stadt\.name">{name}</span>', seite)
            index = (out / "index.html").read_text(encoding="utf-8")
            self.assertIn(f'<meta property="og:image" content="{site.config.SITE_URL.rstrip("/")}/og-bild.png">', index)
            self.assertIn('<meta name="twitter:card" content="summary_large_image">', index)
            self.assertIn(f'<meta property="og:title" content="Stadtmonitor {name}">', index)
            self.assertIn('property="og:url" content="https://', (out / "wohnen.html").read_text(encoding="utf-8"))
            for seite in ("intern/index.html", "intern/karten.html", "intern/pruefen.html"):
                self.assertNotIn("og:image", (out / seite).read_text(encoding="utf-8"), seite)
            kopf = (out / "og-bild.png").read_bytes()[:24]
            self.assertEqual(kopf[:8], b"\x89PNG\r\n\x1a\n")
            self.assertEqual((int.from_bytes(kopf[16:20], "big"), int.from_bytes(kopf[20:24], "big")), (1200, 630))

    def test_suchmaschinen(self):
        # robots.txt ohne internen Bereich, sitemap.xml der öffentlichen Seiten, Titel mit Stadtname, Canonical, JSON-LD
        import re
        with tempfile.TemporaryDirectory() as d:
            out = site.build(Path(d) / "_site", mit_daten=False)
            name = site.config.STADT["stadt"]["name"]
            basis = site.config.SITE_URL.rstrip("/") + "/"
            robots = (out / "robots.txt").read_text(encoding="utf-8")
            self.assertIn("Disallow: /intern/", robots)
            self.assertIn(f"Sitemap: {basis}sitemap.xml", robots)
            karte = (out / "sitemap.xml").read_text(encoding="utf-8")
            for u in ("", "wohnen.html", "quellen.html", "teilen/"):
                self.assertIn(f"<loc>{basis}{u}</loc>", karte)
            self.assertNotIn("intern", karte)
            self.assertNotIn("erfassen", karte)
            for seite in ("index.html", "wohnen.html", "quellen.html", "teilen/index.html", "impressum.html"):
                text = (out / seite).read_text(encoding="utf-8")
                self.assertIn(f"Stadtmonitor {name}", re.search(r"<title>(.*?)</title>", text).group(1), seite)
                self.assertIn('<link rel="canonical" href="https://', text, seite)
            index = (out / "index.html").read_text(encoding="utf-8")
            self.assertNotIn("%STADT%", index)
            ld = json.loads(re.search(r'<script type="application/ld\+json">(.*?)</script>', index, re.S).group(1).replace("<\\/", "</"))
            self.assertEqual([x["@type"] for x in ld], ["WebSite", "Dataset"])
            self.assertEqual(ld[0]["url"], basis)

    def test_seite_teilen(self):
        # /teilen/: alle Bilder und Downloads liegen auf der eigenen Domain, Vorschau gesetzt, von anderen Seiten verlinkt
        import re
        with tempfile.TemporaryDirectory() as d:
            out = site.build(Path(d) / "_site", mit_daten=False)
            seite = out / "teilen" / "index.html"
            text = seite.read_text(encoding="utf-8")
            ziele = re.findall(r'(?:src|href)="([^"#:]+)"', text)
            self.assertGreater(len(ziele), 20)
            for z in ziele:
                pfad = (seite.parent / z)
                if z.endswith("/"):
                    pfad = pfad / "index.html"
                self.assertTrue(pfad.resolve().exists(), z)
            for n in ("teilen-quer", "teilen-quadrat", "teilen-story", "teilen-banner"):
                for endung in (".png", ".jpg", "@2x.jpg"):
                    self.assertIn(f'href="{n}{endung}" download', text)
            self.assertIn('property="og:url" content="https://stadtmonitor-witzenhausen.de/teilen/"', text)
            self.assertNotIn("<script", text)
            for andere in ("index.html", "impressum.html", "datenschutz.html"):
                self.assertIn('href="teilen/"', (out / andere).read_text(encoding="utf-8"), andere)

    def test_verantwortliche_stelle_aus_konfiguration(self):
        # eine Quelle (stadt.json) für Datenschutzseite und App; ohne Angabe bleibt die Leerstelle sichtbar
        with tempfile.TemporaryDirectory() as d:
            seite = Path(d) / "datenschutz.html"
            vorlage = (site.config.SITE_SRC / "datenschutz.html").read_text(encoding="utf-8")
            seite.write_text(vorlage, encoding="utf-8")
            D = site.config.STADT["wohnen_eigentum"]["erfassung"]["datenschutz"]
            H = site.config.STADT["projekt"]["hosting"]
            alt, alt_h = dict(D), dict(H)
            try:
                D.update(verantwortlich=None, kontakt_widerspruch=None)
                H.update(anbieter="")
                site.datenschutz_ausfuellen(seite)
                self.assertEqual(seite.read_text(encoding="utf-8").count("[Leerstelle"), vorlage.count("[Leerstelle"))
                D.update(verantwortlich="Testverein e. V.\nMusterweg 1, 00000 Teststadt", kontakt_widerspruch="datenschutz@example.org <b>")
                site.datenschutz_ausfuellen(seite)
                text = seite.read_text(encoding="utf-8")
                self.assertIn('<p data-feld="verantwortlich">Testverein e. V.<br>Musterweg 1, 00000 Teststadt</p>', text)
                self.assertIn("datenschutz@example.org &lt;b&gt;", text)
                self.assertNotIn("verantwortlichen Stelle folgen", text)
            finally:
                D.clear()
                H.clear()
                H.update(alt_h)
                D.update(alt)

    def test_impressum_aus_konfiguration(self):
        # Impressum (§ 5 DDG, § 18 Abs. 2 MStV): Stelle und Kontakt aus stadt.json, keine Leerstelle, wenn benannt
        with tempfile.TemporaryDirectory() as d:
            out = site.build(Path(d) / "_site", mit_daten=False)
            text = (out / "impressum.html").read_text(encoding="utf-8")
            D = site.config.STADT["wohnen_eigentum"]["erfassung"]["datenschutz"]
            if D["verantwortlich"]:
                self.assertNotIn("[Leerstelle", text)
                self.assertEqual(text.count(D["verantwortlich"].splitlines()[0]), 2)
                self.assertIn(D["kontakt_widerspruch"], text)
            if D["verantwortlich"]:  # auch im Abschnitt „Über“ der Startseite
                self.assertIn(f'<span data-feld="verantwortlich_name">{D["verantwortlich"].splitlines()[0]}</span>',
                              (out / "index.html").read_text(encoding="utf-8"))
            for seite in ("index.html", "datenschutz.html", "erfassen.html"):
                self.assertIn('href="impressum.html"', (out / seite).read_text(encoding="utf-8"), seite)

    def test_aushang_art14(self):
        # Aushang nach Art. 14 Abs. 5 lit. b: Stadt, Hinweis zu Namen passend zum Schalter, QR-Code zur Datenschutzseite
        with tempfile.TemporaryDirectory() as d:
            seite = Path(d) / "aushang.html"
            seite.write_text((site.config.SITE_SRC / "aushang.html").read_text(encoding="utf-8"), encoding="utf-8")
            site.datenschutz_ausfuellen(seite)
            text = seite.read_text(encoding="utf-8")
            self.assertIn(f'<span data-feld="stadt">{site.config.STADT["stadt"]["name"]}</span>', text)
            if not site.config.STADT["wohnen_eigentum"]["privat_namen_aktiv"]:
                self.assertIn("Namen von Privatpersonen werden derzeit nicht erfasst.", text)
            self.assertIn("<svg", text)
            self.assertIn("datenschutz.html", text)
            self.assertIn("Art. 14", text)


if __name__ == "__main__":
    unittest.main()


class NurEigeneDomain(unittest.TestCase):
    def test_keine_links_zu_github_quellen_und_intern_auf_der_domain(self):
        import re
        with tempfile.TemporaryDirectory() as d:
            out = site.build(Path(d) / "_site", mit_daten=False)
            for p in list(out.rglob("*.html")) + [out / "app.js", out / "wohnen-module.js"]:
                text = p.read_text(encoding="utf-8")
                self.assertFalse(re.search(r'href="[^"]*github', text), p.name)
            self.assertNotIn("projekt.repo", (out / "app.js").read_text(encoding="utf-8"))
            q = (out / "quellen.html").read_text(encoding="utf-8")
            self.assertIn("<h1>Datenquellen</h1>", q)
            self.assertIn("<table>", q)
            self.assertNotIn("javascript:", q)
            for name in ("index.html", "karten.html", "pruefen.html", "pruefen-gebaeude.js"):
                self.assertTrue((out / "intern" / name).exists(), name)
            self.assertFalse((out / "einrichten.html").exists())
            self.assertIn('href="mailto:', (out / "impressum.html").read_text(encoding="utf-8"))


class Domain(unittest.TestCase):
    def test_htaccess_und_adresse(self):
        # Plesk (Apache): Fehlerseite, Medientypen, keine Verzeichnislisten; Adresse der Domain in Seiten und Codekarten
        with tempfile.TemporaryDirectory() as d:
            out = site.build(Path(d) / "_site", mit_daten=False)
            h = (out / ".htaccess").read_text(encoding="utf-8")
            for teil in ("ErrorDocument 404 /404.html", "Options -Indexes", ".pmtiles", ".webmanifest"):
                self.assertIn(teil, h)
            self.assertIn('href="https://stadtmonitor-witzenhausen.de/"', (out / "404.html").read_text(encoding="utf-8"))
            self.assertIn('content="https://stadtmonitor-witzenhausen.de/"', (out / "intern" / "karten.html").read_text(encoding="utf-8"))
            self.assertIn("https://stadtmonitor-witzenhausen.de/datenschutz.html", (out / "aushang.html").read_text(encoding="utf-8"))
            self.assertNotIn("über GitHub Pages bereitgestellt", (out / "datenschutz.html").read_text(encoding="utf-8"))

    def test_hosting_auf_der_datenschutzseite(self):
        with tempfile.TemporaryDirectory() as d:
            seite = Path(d) / "datenschutz.html"
            seite.write_text((site.config.SITE_SRC / "datenschutz.html").read_text(encoding="utf-8"), encoding="utf-8")
            H = site.config.STADT["projekt"]["hosting"]
            alt = dict(H)
            try:
                H["anbieter"] = ""
                site.datenschutz_ausfuellen(seite)
                self.assertIn("Name und Sitz des Hosting-Anbieters folgen", seite.read_text(encoding="utf-8"))
                H["anbieter"] = "Beispiel Hosting GmbH, Musterstadt <x>"
                site.datenschutz_ausfuellen(seite)
                text = seite.read_text(encoding="utf-8")
                self.assertIn('<span data-feld="hosting">Beispiel Hosting GmbH, Musterstadt &lt;x&gt;</span>', text)
                self.assertIn('<span data-feld="hosting_ort">Deutschland (EU)</span>', text)
            finally:
                H.clear()
                H.update(alt)

    def test_weiterleitung_fuer_github_pages(self):
        with tempfile.TemporaryDirectory() as d:
            ziel = site.weiterleitung(Path(d) / "w", "https://stadtmonitor.example/")
            for name in ("index.html", "404.html"):
                text = (ziel / name).read_text(encoding="utf-8")
                self.assertIn('content="0; url=https://stadtmonitor.example/"', text)
                self.assertIn('var basis = "/wiz-stadtmonitor/"', text)
                self.assertIn('location.replace("https://stadtmonitor.example/" + pfad', text)
