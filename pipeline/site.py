"""Seite zusammenstellen: site/ und config/stadt.json nach _site/, dazu die Exporte aus data/export/."""
import csv
import html
import json
import os
import re
import shutil
import urllib.parse
from datetime import date

from . import config


def build(out=config.SITE_OUT, mit_daten=True):
    if out.exists():
        shutil.rmtree(out)
    shutil.copytree(config.SITE_SRC, out)
    shutil.copy2(config.STADT_JSON, out / "stadt.json")
    namensnennungen(out / "namensnennungen.json")
    # Schemata der Erfassung (Übergabe v0.4.2): eine Quelle für die Prüfung im Gerät und die Prüfskripte
    (out / "schemas").mkdir()
    for name, quelle in (("erfassung_eigentum.json", "schema_erfassung_eigentum.json"), ("mietangabe.json", "schema_mietangabe.json")):
        shutil.copy2(config.ROOT / "docs" / "uebergabe-v0.4.2" / quelle, out / "schemas" / name)
    for seite in ("datenschutz.html", "impressum.html", "aushang.html", "index.html"):
        datenschutz_ausfuellen(out / seite)
    karten_ausfuellen(out / "intern" / "karten.html")
    pruefen_ausfuellen(out / "intern" / "pruefen.html")
    # Datenquellen als Seite der eigenen Domain (aus DATA_SOURCES.md, die tools/datenquellen.py aus dem Register erzeugt)
    markdown_seite(config.ROOT / "DATA_SOURCES.md", out / "quellen.html", "Datenquellen")
    # Fehlerseite: GitHub Pages liefert sie für jeden Pfad aus, ein relativer Link führte dort ins Leere
    p404 = out / "404.html"
    if p404.exists() and config.SITE_URL:
        p404.write_text(p404.read_text(encoding="utf-8").replace('href="./"', f'href="{config.SITE_URL}"'), encoding="utf-8")
    data = out / "data"
    (data / "export").mkdir(parents=True)
    if mit_daten and config.EXPORT.exists():
        shutil.copytree(config.EXPORT, data / "export", dirs_exist_ok=True)
    # Strukturdaten im Format des Datenvertrags (data/strukturdaten/, offene Lizenzen); die Seite liest nur diese Dateien
    struktur = config.ROOT / "data" / "strukturdaten"
    if mit_daten and struktur.exists():
        shutil.copytree(struktur, data / "strukturdaten", dirs_exist_ok=True)
    lic = config.ROOT / "data" / "LICENSE-DATA.md"
    if lic.exists():
        shutil.copy2(lic, data / "LICENSE-DATA.md")
    print(f"Seite in {out}")
    return out


def datenschutz_ausfuellen(seite):
    """Verantwortliche Stelle und Kontakt aus stadt.json (eine Quelle für Datenschutzseite, Aushang nach Art. 14 und
    Erfassungs-App); solange sie fehlen, bleiben die Leerstellen stehen. Im Aushang zusätzlich Stadt, Hinweis zu Namen,
    Adresse und QR-Code der Datenschutzseite."""
    E = config.STADT["wohnen_eigentum"]
    D = E["erfassung"]["datenschutz"]
    if not seite.exists():
        return
    text = seite.read_text(encoding="utf-8")
    for feld in ("verantwortlich", "kontakt_widerspruch"):
        if D.get(feld):
            wert = "<br>".join(html.escape(z) for z in D[feld].splitlines())
            text = re.sub(rf'<p class="offen" data-feld="{feld}">.*?</p>', f'<p data-feld="{feld}">{wert}</p>', text, flags=re.S)
    adresse = (config.SITE_URL or "").rstrip("/") + "/datenschutz.html" if config.SITE_URL else ""
    namen = ("Bei Privatpersonen kann der Name erfasst sein; er ist nur verschlüsselt gespeichert und dient allein der Prüfung."
             if E["privat_namen_aktiv"] else "Namen von Privatpersonen werden derzeit nicht erfasst.")
    H = config.STADT["projekt"].get("hosting", {})
    if H.get("anbieter"):
        text = re.sub(r'<span class="offen" data-feld="hosting">.*?</span>', f'<span data-feld="hosting">{html.escape(H["anbieter"])}</span>', text, flags=re.S)
    name = (D.get("verantwortlich") or "").splitlines()[0] if D.get("verantwortlich") else None
    spans = {"stadt": html.escape(config.STADT["stadt"]["name"]), "namen": namen, "adresse": html.escape(adresse) if adresse else None,
             "verantwortlich_name": html.escape(name) if name else None, "hosting_ort": html.escape(H["ort"]) if H.get("ort") else None,
             "kontakt_hinweise": (lambda m: f'<a href="mailto:{html.escape(m)}">{html.escape(m)}</a>')(config.STADT["projekt"]["kontakt"])
             if config.STADT["projekt"].get("kontakt") else None}
    for feld, wert in spans.items():
        if wert:
            text = re.sub(rf'<span data-feld="{feld}">.*?</span>', f'<span data-feld="{feld}">{wert}</span>', text, flags=re.S)
    if adresse and 'data-feld="qr"' in text:
        try:
            import segno  # noqa: PLC0415 – nur für den QR-Code im Aushang
            svg = segno.make(adresse, error="m").svg_inline(scale=4, title="QR-Code zur Datenschutzseite")
            text = text.replace('<div data-feld="qr"></div>', f'<div data-feld="qr">{svg}</div>')
        except ImportError:
            pass
    seite.write_text(text, encoding="utf-8")


def karten_ausfuellen(seite):
    """Seite der Einladungskarten: Adresse der Erfassungsseite (für die QR-Codes) aus stadt.json; die Seite selbst lädt
    nichts nach (connect-src 'none'). Die Gültigkeit der Karten steht in der Kartenliste (von der Prüfgruppe)."""
    if not seite.exists():
        return
    text = seite.read_text(encoding="utf-8")
    text = text.replace('<meta name="wiz-site-url" content="">', f'<meta name="wiz-site-url" content="{html.escape(config.SITE_URL or "")}">')
    seite.write_text(text, encoding="utf-8")


def pruefen_ausfuellen(seite):
    """Prüfseite: Schemata und Kategorien der Erfassung aus Übergabe und stadt.json in die Seite (sie lädt nichts nach,
    connect-src 'none'); dieselben Quellen wie tools/pruefen.py."""
    if not seite.exists():
        return
    E = config.STADT["wohnen_eigentum"]
    U = config.ROOT / "docs" / "uebergabe-v0.4.2"
    k = {"kategorien": [{x: kat[x] for x in ("code", "titel", "name_veroeffentlichen")} for kat in E["kategorien"]],
         "speicherdauer_monate": E["erfassung"]["speicherdauer_monate"], "freigaben_noetig": E["erfassung"]["freigaben_noetig"],
         "einladung_gueltig_monate": E["erfassung"]["einladung_gueltig_monate"],
         "regeln": E["regeln"], "lizenz": E["lizenz"], "mietangaben_aktiv": E["mietangaben_aktiv"],
         "einwilligung_version": E["erfassung"]["einwilligung"]["version"],
         "gebaeude_attribution": config.STADT["gebaeude"]["attribution"],
         "ortsteile": {o["slug"]: o["name"] for o in config.STADT["ortsteile"]},
         "schemas": {"eigentum": json.loads((U / "schema_erfassung_eigentum.json").read_text(encoding="utf-8")),
                     "miete": json.loads((U / "schema_mietangabe.json").read_text(encoding="utf-8"))}}
    daten = json.dumps(k, ensure_ascii=False).replace("</", "<\\/")
    text = seite.read_text(encoding="utf-8").replace('<script type="application/json" id="konfig">{}</script>',
                                                     f'<script type="application/json" id="konfig">{daten}</script>')
    seite.write_text(text, encoding="utf-8")
    # Gebäude je Ortsbezirk (wie tools/veroeffentlichen.py aus gebaeude.geojson) als Skriptdatei neben der Seite;
    # Kennungen ohne gemeinsamen Anfang, Gebäude außerhalb der Ortsbezirksflächen unter ""
    geb = config.ROOT / "data" / "geo" / "hvgg" / "gebaeude.geojson"
    je, praefix = {}, ""
    if geb.exists():
        feats = json.loads(geb.read_text(encoding="utf-8"))["features"]
        praefix = os.path.commonprefix([f["properties"]["id"] for f in feats])
        for f in feats:
            je.setdefault(f["properties"].get("o") or "", []).append(f["properties"]["id"][len(praefix):])
    daten = json.dumps({"praefix": praefix, "o": {o: ",".join(ids) for o, ids in sorted(je.items())}}, separators=(",", ":"))
    (seite.parent / "pruefen-gebaeude.js").write_text(f"window.PRUEFEN_GEBAEUDE = {daten};\n", encoding="utf-8")


def weiterleitung(ziel, nach=None):
    """Kleine Seite für die frühere Adresse (GitHub Pages): leitet mit Pfad, Abfrage und Anker auf die eigene Domain weiter.
    GitHub Pages liefert 404.html für jeden unbekannten Pfad aus, daher dieselbe Seite als index.html und 404.html."""
    nach = (nach or config.SITE_URL).rstrip("/") + "/"
    alt = config.STADT["projekt"].get("fruehere_url") or ""
    basis = urllib.parse.urlparse(alt).path or "/"
    ziel.mkdir(parents=True, exist_ok=True)
    seite = f"""<!doctype html>
<html lang="de">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="robots" content="noindex">
  <title>Stadtmonitor ist umgezogen</title>
  <meta http-equiv="refresh" content="0; url={html.escape(nach)}">
  <link rel="canonical" href="{html.escape(nach)}">
  <script>
    (function () {{
      var basis = {json.dumps(basis)}, pfad = location.pathname;
      if (pfad.indexOf(basis) === 0) pfad = pfad.slice(basis.length);
      location.replace({json.dumps(nach)} + pfad.replace(/^\//, "") + location.search + location.hash);
    }})();
  </script>
</head>
<body style="font: 16px/1.6 system-ui, sans-serif; margin: 2rem;">
  <p>Der Stadtmonitor ist umgezogen: <a href="{html.escape(nach)}">{html.escape(nach)}</a></p>
</body>
</html>
"""
    for name in ("index.html", "404.html"):
        (ziel / name).write_text(seite, encoding="utf-8")
    return ziel


def namensnennungen(ziel):
    """Namensnennungen der Quellen, die die Seite nutzt (data/attribution.tsv, Spalte auf_seite), mit Jahr."""
    rows = csv.DictReader((config.ROOT / "data" / "attribution.tsv").open(encoding="utf-8"), delimiter="\t")
    liste = [{"quellen": r["quellen"].split(","), "lizenz": r["lizenz"], "text": r["text"].replace("(Jahr)", str(date.today().year)),
              "link": r["link"]} for r in rows if r["auf_seite"] == "ja"]
    ziel.write_text(json.dumps(liste, ensure_ascii=False, indent=1), encoding="utf-8")


def _inline(s):
    """Markdown in einer Zeile: Code, Fett, Links (nur http, https, mailto oder relativ)."""
    s = html.escape(s, quote=False)
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    s = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", s)

    def link(m):
        url = m.group(2).replace('"', "%22")
        if re.match(r"(https?:|mailto:)", url) or not re.match(r"[a-z]+:", url):
            return f'<a href="{url}">{m.group(1)}</a>'
        return m.group(1)
    return re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", link, s)


def markdown_html(text):
    """Kleiner Umsetzer für die eigenen Markdown-Dateien: Überschriften, Absätze, Listen, Tabellen."""
    out, absatz, liste, tabelle = [], [], None, []

    def schliessen():
        nonlocal absatz, liste, tabelle
        if absatz:
            out.append(f"<p>{_inline(' '.join(absatz))}</p>")
        if liste:
            out.append(f"<{liste[0]}>" + "".join(f"<li>{_inline(x)}</li>" for x in liste[1]) + f"</{liste[0]}>")
        if tabelle:
            zeilen = [[_inline(z.strip().replace("\\|", "|")) for z in re.split(r"(?<!\\)\|", r.strip().strip("|"))] for r in tabelle
                      if not re.fullmatch(r"\|?[\s:|-]+\|?", r.strip())]
            kopf, rumpf = zeilen[0], zeilen[1:]
            out.append('<div class="tabelle-rahmen"><table><thead><tr>' + "".join(f'<th scope="col">{z}</th>' for z in kopf) +
                       "</tr></thead><tbody>" + "".join("<tr>" + "".join(f"<td>{z}</td>" for z in r) + "</tr>" for r in rumpf) +
                       "</tbody></table></div>")
        absatz, liste, tabelle = [], None, []

    for zeile in text.splitlines():
        s = zeile.rstrip()
        if not s.strip():
            schliessen()
        elif m := re.match(r"(#{1,4})\s+(.*)", s):
            schliessen()
            n = len(m.group(1))
            out.append(f"<h{n}>{_inline(m.group(2))}</h{n}>")
        elif s.lstrip().startswith("|"):
            if absatz or liste:
                schliessen()
            tabelle.append(s)
        elif m := re.match(r"\s*(?:([-*])|\d+\.)\s+(.*)", s):
            art = "ul" if m.group(1) else "ol"
            if absatz or tabelle or (liste and liste[0] != art):
                schliessen()
            liste = liste or (art, [])
            liste[1].append(m.group(2))
        elif liste and zeile.startswith("   "):
            liste[1][-1] += " " + s.strip()
        else:
            if liste or tabelle:
                schliessen()
            absatz.append(s.strip())
    schliessen()
    return "\n".join(out)


def markdown_seite(quelle, ziel, titel, tiefe=0, robots=None):
    """Eine Markdown-Datei als einfache Seite im Stil der Unterseiten (page.css)."""
    if not quelle.exists():
        return
    vor = "../" * tiefe
    ziel.parent.mkdir(parents=True, exist_ok=True)
    ziel.write_text(f"""<!doctype html>
<html lang="de">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta http-equiv="Content-Security-Policy" content="default-src 'self'; style-src 'self' 'unsafe-inline'; font-src 'self'; img-src 'self'; object-src 'none'; base-uri 'self'; form-action 'none'">
  {f'<meta name="robots" content="{robots}">' if robots else ""}
  <title>{html.escape(titel)} – Stadtmonitor</title>
  <link rel="icon" href="{vor}favicon.svg" type="image/svg+xml">
  <link rel="stylesheet" href="{vor}page.css">
</head>
<body>
  <header class="page-head">
    <a class="page-brand" href="{vor}./"><img src="{vor}favicon.svg" width="32" height="32" alt="">Stadtmonitor</a>
    <a class="page-back" href="{vor}./">Zur Karte</a>
  </header>
  <main class="page breit" id="inhalt">
{markdown_html(quelle.read_text(encoding="utf-8"))}
  </main>
  <footer class="page-foot"><a href="{vor}./">Zur Karte</a> · <a href="{vor}impressum.html">Impressum</a> · <a href="{vor}datenschutz.html">Datenschutz</a></footer>
</body>
</html>
""", encoding="utf-8")
