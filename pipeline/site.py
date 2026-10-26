"""Seite zusammenstellen: site/ und config/stadt.json nach _site/, dazu die Exporte aus data/export/."""
import csv
import html
import json
import re
import shutil
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
    datenschutz_ausfuellen(out / "datenschutz.html")
    # Fehlerseite: GitHub Pages liefert sie für jeden Pfad aus, ein relativer Link führte dort ins Leere
    p404 = out / "404.html"
    if p404.exists() and config.SITE_URL:
        p404.write_text(p404.read_text(encoding="utf-8").replace('href="./"', f'href="{config.SITE_URL}"'), encoding="utf-8")
    data = out / "data"
    (data / "export").mkdir(parents=True)
    if mit_daten and config.EXPORT.exists():
        shutil.copytree(config.EXPORT, data / "export", dirs_exist_ok=True)
    lic = config.ROOT / "data" / "LICENSE-DATA.md"
    if lic.exists():
        shutil.copy2(lic, data / "LICENSE-DATA.md")
    print(f"Seite in {out}")
    return out


def datenschutz_ausfuellen(seite):
    """Verantwortliche Stelle und Kontakt aus stadt.json (eine Quelle für Seite und Erfassungs-App); solange sie fehlen,
    bleiben die Leerstellen stehen."""
    D = config.STADT["wohnen_eigentum"]["erfassung"]["datenschutz"]
    if not seite.exists():
        return
    text = seite.read_text(encoding="utf-8")
    for feld in ("verantwortlich", "kontakt_widerspruch"):
        if D.get(feld):
            wert = "<br>".join(html.escape(z) for z in D[feld].splitlines())
            text = re.sub(rf'<p class="offen" data-feld="{feld}">.*?</p>', f'<p data-feld="{feld}">{wert}</p>', text, flags=re.S)
    seite.write_text(text, encoding="utf-8")


def namensnennungen(ziel):
    """Namensnennungen der Quellen, die die Seite nutzt (data/attribution.tsv, Spalte auf_seite), mit Jahr."""
    rows = csv.DictReader((config.ROOT / "data" / "attribution.tsv").open(encoding="utf-8"), delimiter="\t")
    liste = [{"quellen": r["quellen"].split(","), "lizenz": r["lizenz"], "text": r["text"].replace("(Jahr)", str(date.today().year)),
              "link": r["link"]} for r in rows if r["auf_seite"] == "ja"]
    ziel.write_text(json.dumps(liste, ensure_ascii=False, indent=1), encoding="utf-8")
