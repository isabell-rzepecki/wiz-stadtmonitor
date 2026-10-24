"""Pfade, Quellen und Lizenzen der Pipeline; stadtspezifische Werte aus config/stadt.json."""
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STADT_JSON = ROOT / "config" / "stadt.json"
STADT = json.loads(STADT_JSON.read_text(encoding="utf-8"))

RAW = ROOT / "data" / "raw"
GEO = ROOT / "data" / "geo"
EXPORT = ROOT / "data" / "export"
SITE_SRC = ROOT / "site"
SITE_OUT = ROOT / "_site"

# Ortsbezirke als Flächen, abgeleitet aus den Gemarkungen der HVBG (dl-de/zero-2.0, daher im Repository);
# Daten je Lizenz in eigenem Unterordner (dl-de-zero/, restricted/ …)
ORTSBEZIRKE = GEO / "dl-de-zero" / "ortsbezirke.geojson"
VORGAENGE = EXPORT / "vorgaenge.json"

USER_AGENT = STADT["projekt"]["user_agent"]

# Quelle je Datensatz; wird in jeden Export übernommen (meta.sources).
SOURCES = {
    "bekanntmachungen": {
        "url": STADT["stadt"]["bekanntmachungen"],
        "license": "Amtliche Bekanntmachungen der Stadt (amtliche Werke nach § 5 Abs. 1 UrhG – Bestätigung durch die Stadt offen)",
    },
}

# Öffentliche Adresse der Seite (für absolute Links)
SITE_URL = os.environ.get("SITE_URL", STADT["projekt"]["site_url"])
