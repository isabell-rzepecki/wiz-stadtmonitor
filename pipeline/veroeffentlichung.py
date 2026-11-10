"""Veröffentlichte Erfassungsergebnisse vom Server übernehmen (Schritt fetch-veroeffentlichung, vor wohnen).

Die Prüfgruppe veröffentlicht aus der Prüfseite; intern/veroeffentlichen.php legt die Datei als
<Domain>/veroeffentlicht/aktuell.json ab (öffentlich lesbar: nur zusammengefasste Zahlen). Dieser Schritt lädt sie, prüft
sie mit derselben Sperre wie tools/veroeffentlichen.py (Mindestzahlen, Rundung, keine Einzelangaben, keine Namen),
ergänzt die Umrisse der Gebäude und schreibt data/wohnen/. Fehlt die Datei, bleibt der Stand im Repository; verletzt
sie die Sperre, bricht der Schritt ab (Warnung im Lauf) und der bisherige Stand bleibt.
"""
import hashlib
import sys
import urllib.error

from . import audit, config, net

RAW = config.RAW / "veroeffentlichung"
PFAD = "veroeffentlicht/aktuell.json"


def _werkzeug():
    sys.path.insert(0, str(config.ROOT / "tools"))
    import veroeffentlichen  # noqa: PLC0415
    return veroeffentlichen


def fetch(ziel=None):
    if not config.SITE_URL:
        print("Veröffentlichung: keine Adresse der Seite (projekt.site_url)")
        return None
    url = config.SITE_URL.rstrip("/") + "/" + PFAD
    try:
        body, _ = net.get(url, tries=2)
    except urllib.error.HTTPError as e:
        if e.code == 404:
            print("Veröffentlichung: noch keine Datei auf dem Server; data/wohnen/ bleibt")
            return None
        raise
    RAW.mkdir(parents=True, exist_ok=True)
    datei = RAW / "aktuell.json"
    net.speichern(datei, body)
    vo = _werkzeug()
    try:
        aus = vo.uebernehmen(datei, ziel or config.ROOT)
    except vo.Verstoss as e:
        audit.abruf("veroeffentlichung", url, 200, len(body), hashlib.sha256(body).hexdigest(), "", f"Sperre: {e}")
        raise SystemExit(f"Veröffentlichung vom Server nicht übernommen (Sperre): {e}") from None
    audit.abruf("veroeffentlichung", url, 200, len(body), hashlib.sha256(body).hexdigest(), len(aus), "")
    print(f"Veröffentlichung übernommen: {', '.join(aus)}")
    return aus
