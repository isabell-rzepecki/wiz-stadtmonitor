"""Fundstellen prüfen (Schritt fundstellen, nach build): Sind die verlinkten PDFs der Stadt noch erreichbar?

Je Lauf werden höchstens PRO_LAUF Adressen geprüft, die am längsten nicht geprüften zuerst; so verteilt sich die Last
auf den Server der Stadt über mehrere Nächte. Geprüft wird mit HEAD (bei 405 mit GET der ersten Bytes). Der Server der
Stadt leitet fehlende Dateien auf seine Startseite um (301, danach 200 mit HTML); darum zählt auch eine Antwort, die kein
PDF ist, als nicht erreichbar. Als tot gilt eine Adresse erst, wenn sie zweimal hintereinander so antwortet (404, 410
oder kein PDF); Netzfehler und 5xx gelten als unklar und werden beim nächsten Mal wiederholt. Der Stand liegt in data/raw/fundstellen/stand.json (Zwischenspeicher des
Workflows); das Ergebnis ergänzt data/export/quellwache.json um „tote_links“, die im Issue der Quellwache erscheinen.
"""
import json
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone

from . import config

PRO_LAUF = 40
PAUSE_S = 0.5
KEIN_PDF = "kein PDF"
TOT = {404, 410, KEIN_PDF}
STAND = config.RAW / "fundstellen" / "stand.json"


def adressen(daten):
    """{PDF-Adresse: Fundstelle (Nummer der Bekanntmachung)} aus Sitzungen und Vorgängen."""
    out = {}
    for s in daten.get("sitzungen", []):
        if s.get("pdf"):
            out.setdefault(s["pdf"], s.get("bekanntmachung") or s.get("id") or "")
    for v in daten.get("vorgaenge", []):
        for s in v.get("process", []):
            if s.get("pdf"):
                out.setdefault(s["pdf"], s.get("bekanntmachung") or s.get("sitzung") or "")
    return out


def status(url):
    """HTTP-Status der Adresse, KEIN_PDF bei einer PDF-Adresse, die etwas anderes liefert (Umleitung auf eine Seite),
    None bei Netzfehlern."""
    for methode, kopf in (("HEAD", {}), ("GET", {"Range": "bytes=0-1023"})):
        req = urllib.request.Request(url, method=methode, headers={"User-Agent": config.USER_AGENT, **kopf})
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                if url.lower().endswith(".pdf") and "pdf" not in (r.headers.get("Content-Type") or "").lower():
                    return KEIN_PDF
                return r.status
        except urllib.error.HTTPError as e:
            if e.code == 405 and methode == "HEAD":
                continue
            return e.code
        except Exception:
            return None
    return None


def pruefen(daten, stand, jetzt, abfrage=status, pro_lauf=PRO_LAUF, pause=PAUSE_S):
    """Aktualisiert stand {url: {geprueft, status, fehl}} und gibt die nicht erreichbaren Fundstellen zurück."""
    alle = adressen(daten)
    for url in list(stand):
        if url not in alle:
            del stand[url]
    reihe = sorted(alle, key=lambda u: (stand.get(u, {}).get("geprueft") or "", u))[:pro_lauf]
    for i, url in enumerate(reihe):
        if i and pause:
            time.sleep(pause)
        code = abfrage(url)
        e = stand.setdefault(url, {"fehl": 0})
        e.update(geprueft=jetzt, status=code)
        if code in TOT:
            e["fehl"] = e.get("fehl", 0) + 1
            e.setdefault("seit", jetzt[:10])
        elif isinstance(code, int) and code < 400:
            e["fehl"] = 0
            e.pop("seit", None)
    return [{"url": u, "fundstelle": alle[u], "status": e["status"], "seit": e.get("seit", "")}
            for u, e in sorted(stand.items()) if e.get("fehl", 0) >= 2]


def run():
    datei = config.EXPORT / "vorgaenge.json"
    if not datei.exists():
        print("Fundstellen: kein Export (vorgaenge.json), nichts zu prüfen")
        return
    daten = json.loads(datei.read_text(encoding="utf-8"))
    stand = json.loads(STAND.read_text(encoding="utf-8")) if STAND.exists() else {}
    jetzt = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    tote = pruefen(daten, stand, jetzt)
    STAND.parent.mkdir(parents=True, exist_ok=True)
    STAND.write_text(json.dumps(stand, ensure_ascii=False, indent=1), encoding="utf-8")
    qw_datei = config.EXPORT / "quellwache.json"
    qw = json.loads(qw_datei.read_text(encoding="utf-8")) if qw_datei.exists() else {"luecken": [], "warnungen": [], "neu": 0}
    qw["neu"] = qw.get("neu", 0) - len(qw.get("tote_links", [])) + len(tote)
    qw["tote_links"] = tote
    qw_datei.write_text(json.dumps(qw, ensure_ascii=False, indent=1), encoding="utf-8")
    geprueft = sum(1 for e in stand.values() if e.get("geprueft") == jetzt)
    print(f"Fundstellen: {geprueft} von {len(stand)} geprüft, {len(tote)} nicht erreichbar")
