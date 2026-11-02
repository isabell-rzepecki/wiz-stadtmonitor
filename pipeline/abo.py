"""Sitzungstermine zum Abonnieren: Kalender (iCalendar, RFC 5545) und Feed (Atom, RFC 4287) je Ortsteil und für die Stadt.

- alle:   alle Sitzungen
- stadt:  Stadtverordnetenversammlung, Ausschüsse und stadtweite Beiräte
- <slug>: Ortsbeirat bzw. Stadtteilbeirat des Ortsteils mit ganzer Tagesordnung, dazu Sitzungen der Stadtgremien mit
          Tagesordnungspunkten, die diesen Ortsteil betreffen (nur diese Punkte)
Inhalt nur aus den Einladungen (Gremium, Termin, Ort, Tagesordnung ohne Verfahrenspunkte); Titel sind bereits durch den
Namensfilter gelaufen, Privatanschriften als Sitzungsort schon ersetzt. Der Kalender reicht ein Jahr zurück, der Feed
nennt die letzten Einladungen.
"""
from datetime import date, datetime, timedelta, timezone
from xml.sax.saxutils import escape

from . import config

OUT = config.EXPORT / "abo"
ORTSGREMIEN = ("ortsbeirat", "stadtteilbeirat")
TAGE_ZURUECK = 365
FEED_EINTRAEGE = 40
DAUER_STUNDEN = 2
# Zeitzone für Termine mit Uhrzeit: Mitteleuropa mit Sommerzeit (Regeln der EU seit 1996)
VTIMEZONE = """BEGIN:VTIMEZONE
TZID:Europe/Berlin
BEGIN:DAYLIGHT
TZOFFSETFROM:+0100
TZOFFSETTO:+0200
TZNAME:CEST
DTSTART:19700329T020000
RRULE:FREQ=YEARLY;BYMONTH=3;BYDAY=-1SU
END:DAYLIGHT
BEGIN:STANDARD
TZOFFSETFROM:+0200
TZOFFSETTO:+0100
TZNAME:CET
DTSTART:19701025T030000
RRULE:FREQ=YEARLY;BYMONTH=10;BYDAY=-1SU
END:STANDARD
END:VTIMEZONE"""


def _ics_text(s):
    return str(s).replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\r", "").replace("\n", "\\n")


def _falten(zeile):
    """Zeilen nach RFC 5545 bei 75 Oktetten umbrechen (Fortsetzung mit Leerzeichen), ohne UTF-8-Zeichen zu teilen."""
    out, teil, laenge = [], "", 0
    for z in zeile:
        n = len(z.encode("utf-8"))
        if laenge + n > (75 if not out else 74):
            out.append(teil)
            teil, laenge = "", 0
        teil += z
        laenge += n
    out.append(teil)
    return "\r\n ".join(out)


def _host():
    from urllib.parse import urlparse
    return urlparse(config.SITE_URL or "https://stadtmonitor.invalid/").hostname


def tagesordnung(sitzung, vorgaenge, ortsteil=None):
    """[(top, titel)] einer Sitzung ohne Verfahrenspunkte; mit ortsteil nur Punkte mit Ortsbezug dorthin."""
    out = []
    for v in vorgaenge:
        if v["verfahrenspunkt"]:
            continue
        if ortsteil and not any(l.get("ortsteil") == ortsteil for l in v["locations"]):
            continue
        out += [(s["top"], s.get("titel") or v["name"]) for s in v["process"] if s["sitzung"] == sitzung["id"]]
    return sorted(out, key=lambda t: [int(x) if x.isdigit() else 0 for x in t[0].split(".")])


def _ortsgremium(s):
    typ = s.get("gremium_typ") or ("ortsbeirat" if s["gremium"].startswith(("Ortsbeirat", "Stadtteilbeirat")) else "")
    return typ in ORTSGREMIEN


def auswahl(daten):
    """{slug: (Titel, [(sitzung, ortsteil-Filter oder None)])}"""
    sitzungen, vorgaenge = daten["sitzungen"], daten["vorgaenge"]
    je_sitzung = {}
    for v in vorgaenge:
        for s in v["process"]:
            je_sitzung.setdefault(s["sitzung"], []).append(v)
    stadt = [s for s in sitzungen if not _ortsgremium(s)]
    out = {"alle": ("Alle Gremien", [(s, None) for s in sitzungen]),
           "stadt": ("Stadtverordnetenversammlung, Ausschüsse und Beiräte", [(s, None) for s in stadt])}
    for o in config.STADT["ortsteile"]:
        eigene = [(s, None) for s in sitzungen if _ortsgremium(s) and s.get("ortsteil") == o["name"]]
        bezug = [(s, o["name"]) for s in stadt if tagesordnung(s, je_sitzung.get(s["id"], []), o["name"])]
        out[o["slug"]] = (o["name"], sorted(eigene + bezug, key=lambda x: x[0]["date"]))
    return out, je_sitzung


def ics(titel, eintraege, je_sitzung, stand):
    host, url = _host(), config.SITE_URL or ""
    von = (date.fromisoformat(stand[:10]) - timedelta(days=TAGE_ZURUECK)).isoformat()
    zeilen = ["BEGIN:VCALENDAR", "VERSION:2.0", f"PRODID:-//{host}//Stadtmonitor//DE", "CALSCALE:GREGORIAN", "METHOD:PUBLISH",
              f"X-WR-CALNAME:{_ics_text('Stadtmonitor: ' + titel)}", "X-WR-TIMEZONE:Europe/Berlin",
              "REFRESH-INTERVAL;VALUE=DURATION:PT12H", "X-PUBLISHED-TTL:PT12H", *VTIMEZONE.split("\n")]
    dtstamp = stand[:19].replace("-", "").replace(":", "") + "Z"
    for s, ort_filter in eintraege:
        termine = s.get("termine") or [{"date": s["date"], "time": s.get("time")}]
        for i, t in enumerate(termine):
            if not t.get("date") or t["date"] < von:
                continue
            tops = tagesordnung(s, je_sitzung.get(s["id"], []), ort_filter)
            text = [f"Einladung: {s['pdf']}"]
            if s.get("oeffentlich") is False:
                text.insert(0, "Nichtöffentliche Sitzung.")
            if tops:
                text.append(("Tagesordnungspunkte mit Bezug zu " + ort_filter if ort_filter else "Tagesordnung") + ":")
                text += [f"TOP {n} {ti}" for n, ti in tops]
            text.append(f"Stadtmonitor: {url}")
            tag = t["date"].replace("-", "")
            if t.get("time"):
                beginn = datetime.strptime(f"{t['date']} {t['time']}", "%Y-%m-%d %H:%M")
                zeit = [f"DTSTART;TZID=Europe/Berlin:{beginn:%Y%m%dT%H%M%S}",
                        f"DTEND;TZID=Europe/Berlin:{beginn + timedelta(hours=DAUER_STUNDEN):%Y%m%dT%H%M%S}"]
            else:
                ende = (date.fromisoformat(t["date"]) + timedelta(days=1)).strftime("%Y%m%d")
                zeit = [f"DTSTART;VALUE=DATE:{tag}", f"DTEND;VALUE=DATE:{ende}"]
            uid = f"{s['id'].replace('/', '-')}{'-' + str(i + 1) if len(termine) > 1 else ''}@{host}"
            zeilen += ["BEGIN:VEVENT", f"UID:{uid}", f"DTSTAMP:{dtstamp}", *zeit,
                       f"SUMMARY:{_ics_text(s['gremium'])}",
                       *([f"LOCATION:{_ics_text(s['ort'])}"] if s.get("ort") else []),
                       f"DESCRIPTION:{_ics_text(chr(10).join(text))}", f"URL:{s['pdf']}",
                       "STATUS:CONFIRMED", "TRANSP:OPAQUE", "END:VEVENT"]
    zeilen.append("END:VCALENDAR")
    return "\r\n".join(_falten(z) for z in zeilen) + "\r\n"


def atom(slug, titel, eintraege, je_sitzung, stand):
    host, url = _host(), config.SITE_URL or ""
    neueste = sorted(eintraege, key=lambda x: (x[0].get("veroeffentlicht") or x[0]["date"], x[0]["id"]), reverse=True)[:FEED_EINTRAEGE]
    teile = ['<?xml version="1.0" encoding="utf-8"?>', '<feed xmlns="http://www.w3.org/2005/Atom" xml:lang="de">',
             f"<id>tag:{host},2024:abo:{escape(slug)}</id>", f"<title>{escape('Stadtmonitor: ' + titel)}</title>",
             "<subtitle>Einladungen zu Sitzungen laut amtlichen Bekanntmachungen</subtitle>",
             f'<link rel="self" href="{escape(url)}data/export/abo/{escape(slug)}.atom"/>', f'<link href="{escape(url)}"/>',
             f"<updated>{stand}</updated>", "<author><name>Stadtmonitor</name></author>",
             f"<rights>{escape(config.STADT['quelle']['attribution'])}</rights>"]
    for s, ort_filter in neueste:
        tops = tagesordnung(s, je_sitzung.get(s["id"], []), ort_filter)
        termin = " und ".join(f"{date.fromisoformat(t['date']):%d.%m.%Y}{', ' + t['time'] + ' Uhr' if t.get('time') else ''}"
                              for t in (s.get("termine") or [{"date": s["date"], "time": s.get("time")}]) if t.get("date"))
        text = [f"{s['gremium']}, {termin}" + (f", {s['ort']}" if s.get("ort") else "")]
        if s.get("oeffentlich") is False:
            text.append("Nichtöffentliche Sitzung.")
        if tops:
            text.append(("Tagesordnungspunkte mit Bezug zu " + ort_filter if ort_filter else "Tagesordnung") + ":")
            text += [f"TOP {n} {ti}" for n, ti in tops]
        veroeff = (s.get("veroeffentlicht") or s["date"]) + "T00:00:00Z"
        teile += ["<entry>", f"<id>tag:{host},2024:sitzung:{escape(s['id'])}{':' + escape(slug) if ort_filter else ''}</id>",
                  f"<title>{escape(s['gremium'])} am {date.fromisoformat(s['date']):%d.%m.%Y}</title>",
                  f'<link href="{escape(s["pdf"])}"/>', f"<updated>{veroeff}</updated>", f"<published>{veroeff}</published>",
                  f'<content type="text">{escape(chr(10).join(text))}</content>', "</entry>"]
    teile.append("</feed>")
    return "\n".join(teile) + "\n"


def schreiben(daten, stand=None, ziel=None):
    stand = stand or datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    ziel = ziel or OUT
    ziel.mkdir(parents=True, exist_ok=True)
    gruppen, je_sitzung = auswahl(daten)
    for slug, (titel, eintraege) in gruppen.items():
        (ziel / f"{slug}.ics").write_text(ics(titel, eintraege, je_sitzung, stand), encoding="utf-8", newline="")
        (ziel / f"{slug}.atom").write_text(atom(slug, titel, eintraege, je_sitzung, stand), encoding="utf-8")
    return {slug: len(e) for slug, (_, e) in gruppen.items()}
