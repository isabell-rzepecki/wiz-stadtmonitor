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
    subprocess.run(["pdftotext", "-layout", "-enc", "UTF-8", str(pdf), str(txt)], check=True, timeout=120)


def fetch():
    PDF.mkdir(parents=True, exist_ok=True)
    TXT.mkdir(parents=True, exist_ok=True)
    medien = [m for m in liste() if ist_einladung(m["source_url"])]
    neu = 0
    for m in medien:
        name = dateiname(m["source_url"])
        pdf = PDF / name
        if not pdf.exists():
            body, _ = net.get(m["source_url"])
            pdf.write_bytes(body)
            audit.abruf("wp_media_pdf", m["source_url"], 200, len(body), hashlib.sha256(body).hexdigest(), "", "")
            neu += 1
            time.sleep(config.STADT["quelle"]["pause_s"])
        txt = TXT / (pdf.stem + ".txt")
        if not txt.exists():
            text(pdf, txt)
    stand = {"abruf": datetime.now(timezone.utc).isoformat(timespec="seconds"), "anzahl": len(medien), "medien": medien}
    MEDIEN.write_text(json.dumps(stand, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{len(medien)} Einladungen, davon {neu} neu geladen")
