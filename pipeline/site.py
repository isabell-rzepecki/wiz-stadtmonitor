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
    for seite in ("datenschutz.html", "impressum.html", "aushang.html", "index.html"):
        datenschutz_ausfuellen(out / seite)
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
    name = (D.get("verantwortlich") or "").splitlines()[0] if D.get("verantwortlich") else None
    spans = {"stadt": html.escape(config.STADT["stadt"]["name"]), "namen": namen, "adresse": html.escape(adresse) if adresse else None,
             "verantwortlich_name": html.escape(name) if name else None}
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


def namensnennungen(ziel):
    """Namensnennungen der Quellen, die die Seite nutzt (data/attribution.tsv, Spalte auf_seite), mit Jahr."""
    rows = csv.DictReader((config.ROOT / "data" / "attribution.tsv").open(encoding="utf-8"), delimiter="\t")
    liste = [{"quellen": r["quellen"].split(","), "lizenz": r["lizenz"], "text": r["text"].replace("(Jahr)", str(date.today().year)),
              "link": r["link"]} for r in rows if r["auf_seite"] == "ja"]
    ziel.write_text(json.dumps(liste, ensure_ascii=False, indent=1), encoding="utf-8")
