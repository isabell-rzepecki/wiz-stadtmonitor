"""Abruf der Einladungen aus den amtlichen Bekanntmachungen (WP-REST-API der Stadt) mit Zwischenspeicher.

Liste aller PDF-Medien → Einladungen (Dateiname enthält „einladung“ oder „stadtteilbeirat“, ohne Fremdobjekte laut
config.STADT["quelle"]["ausschliessen"]) → PDF nach data/raw/pdf/ (nur neue Dateien, mit Pause) → Text mit
`pdftotext -layout` nach data/raw/txt/. Das Verzeichnis der Medien steht in data/raw/medien.json.
"""
import hashlib
import json
import re
import subprocess
import time
import urllib.error
from datetime import datetime, timezone

from . import audit, config, net

PDF = config.RAW / "pdf"
TXT = config.RAW / "txt"
MEDIEN = config.RAW / "medien.json"


def dateiname(url):
    return url.rsplit("/", 1)[-1]


def ist_einladung(url):
    f = dateiname(url).lower()
    if not re.search(r"einladung|stadtteilbeirat", f):
        return False
    return not any(x in f for x in config.STADT["quelle"]["ausschliessen"])


def liste():
    """Alle PDF-Medien der Seite: [{id, date, source_url, title}]."""
    out, page = [], 1
    while True:
        url = config.STADT["quelle"]["liste"].format(page=page)
        try:
            body, _ = net.get(url)
        except urllib.error.HTTPError as e:
            if e.code == 400:  # hinter der letzten Seite
                break
            audit.abruf("wp_media", url, e.code, "", "", "", str(e)[:200])
            raise
        audit.abruf("wp_media", url, 200, len(body), hashlib.sha256(body).hexdigest(), len(json.loads(body)), "")
        items = json.loads(body)
        if not items:
            break
        out += [{"id": x["id"], "date": x["date"], "source_url": x["source_url"],
                 "title": (x.get("title") or {}).get("rendered", "")} for x in items]
        page += 1
        time.sleep(config.STADT["quelle"]["pause_s"])
    return out


def text(pdf, txt):
    """Text einer Einladung; False, wenn pdftotext scheitert (die Einladung zählt dann als Parserfehler)."""
    r = subprocess.run(["pdftotext", "-layout", "-enc", "UTF-8", str(pdf), str(txt)], timeout=120, capture_output=True)
    return r.returncode == 0


def fetch():
    """Liste und neue PDF laden. Scheitert die Liste oder ist sie leer, bleibt medien.json auf dem letzten Stand;
    scheitert eine einzelne Datei, fehlt nur sie (sie wird beim nächsten Lauf erneut versucht)."""
    PDF.mkdir(parents=True, exist_ok=True)
    TXT.mkdir(parents=True, exist_ok=True)
    try:
        alle = liste()
    except Exception as e:
        print(f"Liste der Bekanntmachungen nicht abrufbar ({e}); medien.json bleibt auf dem letzten Stand")
        return
    medien = [m for m in alle if ist_einladung(m["source_url"])]
    if not medien:
        audit.abruf("wp_media", config.STADT["quelle"]["liste"], 200, "", "", 0, "keine Einladungen in der Liste")
        print("Keine Einladungen in der Liste; medien.json bleibt auf dem letzten Stand")
        return
    neu, fehlt = 0, []
    for m in medien:
        name = dateiname(m["source_url"])
        pdf = PDF / name
        if pdf.exists() and net.pruefen(pdf, net.kopf(pdf)):
            pdf.unlink()  # kein PDF im Zwischenspeicher (etwa eine Fehlerseite): neu laden
        if not pdf.exists():
            try:
                body, _ = net.get(m["source_url"])
                grund = net.pruefen(pdf, body)
                if grund:
                    raise ValueError(grund)
            except Exception as e:
                audit.abruf("wp_media_pdf", m["source_url"], getattr(e, "code", ""), "", "", "", str(e)[:200])
                fehlt.append(m)
                continue
            net.speichern(pdf, body)
            audit.abruf("wp_media_pdf", m["source_url"], 200, len(body), hashlib.sha256(body).hexdigest(), "", "")
            neu += 1
            time.sleep(config.STADT["quelle"]["pause_s"])
        txt = TXT / (pdf.stem + ".txt")
        if not txt.exists() and not text(pdf, txt):
            txt.unlink(missing_ok=True)  # keine halbe Textdatei; nächster Lauf versucht es erneut
    if fehlt:
        print(f"{len(fehlt)} Einladungen nicht abrufbar (siehe Abrufprotokoll); sie fehlen bis zum nächsten Lauf")
        medien = [m for m in medien if m not in fehlt]
    stand = {"abruf": datetime.now(timezone.utc).isoformat(timespec="seconds"), "anzahl": len(medien), "medien": medien}
    MEDIEN.write_text(json.dumps(stand, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{len(medien)} Einladungen, davon {neu} neu geladen")
