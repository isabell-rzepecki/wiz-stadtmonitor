"""HTTP-Abruf mit Wiederholung; nur Standardbibliothek."""
import time
import urllib.error
import urllib.request
from datetime import date
from pathlib import Path

from .config import USER_AGENT


def post(url, body, content_type="text/xml; charset=UTF-8", tries=3):
    """Bytes einer POST-Anfrage (etwa WFS GetFeature mit Filter im Rumpf)."""
    req = urllib.request.Request(url, data=body, headers={"User-Agent": USER_AGENT, "Content-Type": content_type})
    for i in range(tries):
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                return r.read()
        except Exception:
            if i == tries - 1:
                raise
            time.sleep(2 ** (i + 1))


def kopf(pfad, n=4096):
    """Die ersten Bytes einer Datei (für pruefen)."""
    with open(pfad, "rb") as f:
        return f.read(n)


def pruefen(ziel, body):
    """None, wenn der Inhalt zur Dateiart passt, sonst der Grund. Dienste antworten auch bei Fehlern oft mit Status 200
    (WFS-Fehlerbericht, HTML-Fehlerseite); solche Antworten sollen den letzten Stand nicht ersetzen."""
    k = body[:4096]
    endung = Path(ziel).suffix.lower()
    if not k.strip():
        return "leere Antwort"
    if endung == ".pdf" and not k.startswith(b"%PDF"):
        return "kein PDF"
    if endung in (".zip", ".xlsx") and not k.startswith(b"PK"):
        return "kein Zip-Archiv"
    if endung in (".gml", ".xml") and (b"ExceptionReport" in k or b"FeatureCollection" not in k):
        return "keine FeatureCollection (Fehlerbericht des Dienstes)"
    return None


def gueltig(ziel, alter_s):
    """Datei im Zwischenspeicher, jünger als alter_s und mit passendem Inhalt."""
    p = Path(ziel)
    return p.exists() and time.time() - p.stat().st_mtime < alter_s and pruefen(p, kopf(p)) is None


def abrufdatum(*pfade):
    """Datum des Abrufs: Änderungszeit der jüngsten vorhandenen Rohdatei (nicht das Datum des Laufs), sonst heute."""
    zeiten = [Path(p).stat().st_mtime for p in pfade if Path(p).exists()]
    return (date.fromtimestamp(max(zeiten)) if zeiten else date.today()).isoformat()


def speichern(ziel, body):
    """Erst vollständig schreiben, dann ersetzen: ein Abbruch hinterlässt keine halbe Datei."""
    ziel = Path(ziel)
    teil = ziel.with_name(ziel.name + ".teil")
    teil.write_bytes(body)
    teil.replace(ziel)


def get(url, tries=5):
    """(Bytes, Header) einer Adresse; wiederholt bei Netzfehlern."""
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    for i in range(tries):
        try:
            with urllib.request.urlopen(req, timeout=90) as r:
                return r.read(), dict(r.headers)
        except urllib.error.HTTPError as e:
            if e.code < 500 or i == tries - 1:
                raise
            time.sleep(2 ** (i + 1))
        except Exception:
            if i == tries - 1:
                raise
            time.sleep(2 ** (i + 1))
