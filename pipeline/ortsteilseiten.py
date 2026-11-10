"""Seiten je Ortsteil (/ortsteil/<slug>/) und Übersicht (/ortsteile/): reiner Text ohne JavaScript, damit Menschen und
Suchmaschinen finden, was in einem Ortsteil beraten wird. Inhalt: nächste Sitzungen mit Ortsbezug (wie das Kalender-Abo,
pipeline/abo.py), Vorgänge mit Ortsbezug der letzten zwölf Monate (wie die Karte: Ortsbezug über locations.ortsteil, ohne
Verfahrenspunkte) und Strukturdaten des Ortsbezirks (Datenvertrag „Strukturdaten v1“). Die Seiten zeigen nur, was die
Karte ohnehin öffentlich zeigt; sie entstehen bei jedem Seitenbau neu.
"""
import csv
import html
import json
from datetime import date, timedelta
from urllib.parse import quote

from . import abo, config

TAGE = 365          # Vorgänge der letzten zwölf Monate
SITZUNGEN_MAX = 6   # nächste Sitzungen je Ortsteil
STRUKTUR = ("zensus_einwohner", "zensus_anteil_unter18", "zensus_anteil_ab65", "zensus_durchschnittsalter",
            "zensus_wohnungen", "zensus_anteil_wohnungen_efh_zfh")
MONATE = ("Januar", "Februar", "März", "April", "Mai", "Juni", "Juli", "August", "September", "Oktober", "November", "Dezember")

e = html.escape


def datum(iso):
    d = date.fromisoformat(iso[:10])
    return f"{d.day}. {MONATE[d.month - 1]} {d.year}"


def zahl(wert, einheit):
    try:
        x = float(wert)
    except (TypeError, ValueError):
        return "nicht ausgewiesen"
    if einheit in ("Personen", "Wohnungen"):
        return f"{round(x):,}".replace(",", ".")
    s = f"{x:.1f}".replace(".", ",")
    return {"%": f"{s} %", "Jahre": f"{s} Jahre"}.get(einheit, s)


def _strukturdaten():
    """{slug: [(Name, Wert als Text)]} und die Namensnennung des Zensus."""
    ordner = config.ROOT / "data" / "strukturdaten"
    if not (ordner / "werte.tsv").exists():
        return {}, ""
    with open(ordner / "indikatoren.tsv", encoding="utf-8") as f:
        ind = {r["indikator_id"]: r for r in csv.DictReader(f, delimiter="\t")}
    out = {}
    with open(ordner / "werte.tsv", encoding="utf-8") as f:
        for r in csv.DictReader(f, delimiter="\t"):
            if r["raumebene"] == "ortsbezirk" and r["indikator_id"] in STRUKTUR:
                out.setdefault(r["raum_id"], {})[r["indikator_id"]] = r["wert"]
    tabelle = {slug: [(ind[i]["name"], zahl(werte.get(i), ind[i]["einheit"])) for i in STRUKTUR if i in ind]
               for slug, werte in out.items()}
    quelle = ind.get("zensus_einwohner", {}).get("namensnennung", "")
    return tabelle, quelle


def _daten():
    datei = config.EXPORT / "vorgaenge.json"
    if not datei.exists():
        return {"sitzungen": [], "vorgaenge": [], "meta": {}}
    return json.loads(datei.read_text(encoding="utf-8"))


def _stand(daten):
    g = (daten.get("meta") or {}).get("generated_at") or date.today().isoformat()
    return date.fromisoformat(g[:10])


def _vorgaenge(daten, name, heute):
    grenze = (heute - timedelta(days=TAGE)).isoformat()
    treffer = []
    for v in daten["vorgaenge"]:
        if v.get("verfahrenspunkt") or not any(l.get("ortsteil") == name for l in v.get("locations", [])):
            continue
        schritte = sorted(v.get("process", []), key=lambda s: s.get("date") or "")
        letzter = schritte[-1] if schritte else {}
        if (letzter.get("date") or v.get("date") or "") >= grenze:
            treffer.append((letzter.get("date") or v.get("date") or "", v, letzter))
    return sorted(treffer, key=lambda t: t[0], reverse=True)


def _seite(titel, beschreibung, vor, inhalt):
    return f"""<!doctype html>
<html lang="de">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta http-equiv="Content-Security-Policy" content="default-src 'self'; style-src 'self' 'unsafe-inline'; font-src 'self'; img-src 'self'; object-src 'none'; base-uri 'self'; form-action 'none'">
  <title>{e(titel)} – Stadtmonitor</title>
  <meta name="description" content="{e(beschreibung)}">
  <link rel="icon" href="{vor}favicon.svg" type="image/svg+xml">
  <link rel="apple-touch-icon" href="{vor}apple-touch-icon.png">
  <link rel="stylesheet" href="{vor}page.css">
  <link rel="stylesheet" href="{vor}ortsteil.css">
</head>
<body>
  <header class="page-head">
    <a class="page-brand" href="{vor}"><img src="{vor}favicon.svg" width="32" height="32" alt="">Stadtmonitor <span data-cfg="stadt.name"></span></a>
    <a class="page-back" href="{vor}">Zur Karte</a>
  </header>
  <main class="page" id="inhalt">
{inhalt}
  </main>
  <footer class="page-foot"><a href="{vor}ortsteile/">Alle Ortsteile</a> · <a href="{vor}quellen.html">Datenquellen</a> · <a href="{vor}impressum.html">Impressum</a> · <a href="{vor}datenschutz.html">Datenschutz</a></footer>
</body>
</html>
"""


def _ortsteil(o, daten, je_sitzung, auswahl, struktur, quelle, heute, mit_abo):
    slug, name, vor = o["slug"], o["name"], "../../"
    karte = f"{vor}?gebiet=ortsteil:{quote(slug)}"
    teile = [f"    <h1>{e(name)}</h1>",
             f'    <p class="einleitung">Was in {e(name)} beraten wird: die nächsten Sitzungen, die Vorgänge mit Bezug zu {e(name)} '
             f'aus den letzten zwölf Monaten und Zahlen zum Ortsteil. Alles mit Quellenangabe; die ganze Übersicht steht auf der '
             f'<a href="{karte}">Karte von {e(name)}</a>.</p>']
    # Nächste Sitzungen (eigenes Gremium mit ganzer Tagesordnung, Stadtgremien nur mit Punkten zu diesem Ortsteil)
    kommend = [(s, f) for s, f in auswahl if s["date"] >= heute.isoformat()][:SITZUNGEN_MAX]
    teile.append("    <h2>Nächste Sitzungen</h2>")
    if kommend:
        # je Sitzung ein Akkordeon (details/summary, ohne JavaScript): Kopfzeile mit Datum, Gremium und Zahl der Punkte,
        # aufgeklappt Ort, Einladung und die Tagesordnungspunkte; die nächste Sitzung ist geöffnet
        for i, (s, filt) in enumerate(kommend):
            punkte = abo.tagesordnung(s, je_sitzung.get(s["id"], []), filt)
            zeit = f", {e(s['time'])} Uhr" if s.get("time") else ""
            anzahl = f'<span class="anzahl">{len(punkte)} {"Punkt" if len(punkte) == 1 else "Punkte"}</span>' if punkte else ""
            ort = e(s["ort"]) if s.get("ort") else ""
            pdf = f'<a href="{e(s["pdf"])}" rel="noopener">Einladung (PDF)</a>' if s.get("pdf") else ""
            info = " · ".join(x for x in (ort, pdf) if x)
            tops = "".join(f'<li><span class="top">TOP {e(t)}</span> {e(x)}</li>' for t, x in punkte)
            teile.append(f'    <details class="sitzung"{" open" if i == 0 else ""}><summary><strong>{e(datum(s["date"]))}{zeit}</strong> '
                         f'<span class="gremium">{e(s["gremium"])}</span>{anzahl}</summary>'
                         f'{f"<p class=klein>{info}</p>" if info else ""}{f"<ol class=tops>{tops}</ol>" if tops else ""}</details>')
    else:
        teile.append("    <p>Zurzeit sind keine Sitzungen mit Bezug zu diesem Ortsteil angekündigt.</p>")
    if mit_abo:
        teile.append(f'    <p class="klein">Termine abonnieren: <a href="{vor}data/export/abo/{quote(slug)}.ics">Kalender (.ics)</a> · '
                     f'<a href="{vor}data/export/abo/{quote(slug)}.atom">Feed (Atom)</a></p>')
    # Vorgänge der letzten zwölf Monate
    vorgaenge = _vorgaenge(daten, name, heute)
    teile.append(f"    <h2>Vorgänge der letzten zwölf Monate ({len(vorgaenge)})</h2>")
    if vorgaenge:
        # nach Monaten gruppiert (Akkordeon), der jüngste Monat geöffnet
        monate = {}
        for d, v, s in vorgaenge:
            monate.setdefault(d[:7], []).append((d, v, s))
        for i, (monat, eintraege) in enumerate(monate.items()):
            zeilen = []
            for d, v, s in eintraege:
                ref = v.get("reference") or ""
                link = f"{karte}#{quote(ref)}" if ref else karte
                nr = f'<span class="nr">{e(v["vorlage"])}</span> ' if v.get("vorlage") else ""
                ergebnis = f" · {e(s['result'])}" if s.get("result") else ""
                pdf = f' · <a href="{e(s["pdf"])}" rel="noopener">Fundstelle (PDF)</a>' if s.get("pdf") else ""
                zeilen.append(f'<li><a href="{e(link)}">{e(v["name"])}</a><br>'
                              f'<span class="klein">{nr}{e(s.get("gremium", ""))}, {e(datum(d)) if d else ""}{ergebnis}{pdf}</span></li>')
            titel = f"{MONATE[int(monat[5:7]) - 1]} {monat[:4]}" if len(monat) == 7 else "ohne Datum"
            teile.append(f'    <details class="monat"{" open" if i == 0 else ""}><summary><strong>{e(titel)}</strong>'
                         f'<span class="anzahl">{len(eintraege)}</span></summary><ul class="vorgaenge">{"".join(zeilen)}</ul></details>')
    else:
        teile.append("    <p>In den letzten zwölf Monaten gab es keine Vorgänge mit Bezug zu diesem Ortsteil.</p>")
    teile.append(f'    <p><a class="mehr-link" href="{karte}">Alle Vorgänge zu {e(name)} auf der Karte</a></p>')
    # Strukturdaten
    werte = struktur.get(slug)
    if werte:
        teile.append("    <h2>Zahlen zum Ortsteil</h2>")
        teile.append('    <dl class="zahlen">' + "".join(f"<dt>{e(k)}</dt><dd>{e(w)}</dd>" for k, w in werte) + "</dl>")
        teile.append(f'    <p class="klein">Stichtag 15. Mai 2022. {e(quelle.rstrip('.'))}. Werte aus dem 100-Meter-Gitter, dem Ortsbezirk zugeordnet; '
                     f'kleine Zahlen sind geheim gehalten. Mehr dazu unter „Strukturdaten“ auf der <a href="{karte}">Karte</a>.</p>')
    teile.append(f'    <p>Gebäude, Mieten und Bodenrichtwerte in {e(name)}: '
                 f'<a href="{vor}wohnen.html?gebiet=ortsteil:{quote(slug)}">Wohnen und Eigentum</a></p>')
    beschreibung = (f"{name}: nächste Sitzungen, Vorgänge der letzten zwölf Monate und Zahlen zum Ortsteil – "
                    f"Stadtverordnete, Ausschüsse und Ortsbeirat, mit Quellenangabe.")
    return _seite(f"{name}: Sitzungen, Vorgänge und Zahlen", beschreibung, vor, "\n".join(teile))


def erzeugen(out, mit_daten=True):
    """Schreibt out/ortsteil/<slug>/index.html und out/ortsteile/index.html; gibt die Pfade relativ zu out zurück."""
    daten = _daten() if mit_daten else {"sitzungen": [], "vorgaenge": [], "meta": {}}
    heute = _stand(daten) if daten.get("meta") else date.today()
    auswahl, je_sitzung = abo.auswahl(daten)
    struktur, quelle = _strukturdaten()
    mit_abo = mit_daten and (config.EXPORT / "abo").exists()
    ortsteile = sorted(config.STADT["ortsteile"], key=lambda o: (o["slug"] != "kernstadt", o["name"]))
    pfade, liste = [], []
    for o in ortsteile:
        ziel = out / "ortsteil" / o["slug"] / "index.html"
        ziel.parent.mkdir(parents=True, exist_ok=True)
        ziel.write_text(_ortsteil(o, daten, je_sitzung, auswahl.get(o["slug"], ("", []))[1], struktur, quelle, heute, mit_abo),
                        encoding="utf-8")
        pfade.append(f"ortsteil/{o['slug']}/index.html")
        n = len(_vorgaenge(daten, o["name"], heute))
        art = "Kernstadt" if not o.get("ortsbezirk") else "Ortsbezirk"
        liste.append(f'      <li><a href="../ortsteil/{quote(o["slug"])}/">{e(o["name"])}</a> '
                     f'<span class="klein">{art} · {n} Vorgänge in zwölf Monaten</span></li>')
    inhalt = ("    <h1>Ortsteile</h1>\n"
              '    <p class="einleitung">Für jeden Ortsteil eine eigene Seite: die nächsten Sitzungen, die Vorgänge mit Ortsbezug '
              "aus den letzten zwölf Monaten und Zahlen aus dem Zensus 2022.</p>\n"
              '    <ul class="ortsteile">\n' + "\n".join(liste) + "\n    </ul>")
    ziel = out / "ortsteile" / "index.html"
    ziel.parent.mkdir(parents=True, exist_ok=True)
    ziel.write_text(_seite("Ortsteile im Überblick", "Seiten zu allen Ortsteilen: nächste Sitzungen, Vorgänge der letzten zwölf "
                           "Monate und Zahlen zum Ortsteil.", "../", inhalt), encoding="utf-8")
    pfade.append("ortsteile/index.html")
    return pfade


def _punkte(sitzung, vorgaenge):
    """[(TOP, Titel, Vorgangsnummer)] einer Sitzung ohne Verfahrenspunkte, nach TOP geordnet."""
    out = []
    for v in vorgaenge:
        if v.get("verfahrenspunkt"):
            continue
        out += [(s["top"], s.get("titel") or v["name"], v.get("reference") or "") for s in v["process"] if s["sitzung"] == sitzung["id"]]
    return sorted(out, key=lambda t: [int(x) if x.isdigit() else 0 for x in str(t[0]).split(".")])


def _sitzung(s, punkte, vor, offen):
    zeit = f", {e(s['time'])} Uhr" if s.get("time") else ""
    anzahl = f'<span class="anzahl">{len(punkte)} {"Punkt" if len(punkte) == 1 else "Punkte"}</span>' if punkte else ""
    info = " · ".join(x for x in (e(s["ort"]) if s.get("ort") else "",
                                  f'<a href="{e(s["pdf"])}" rel="noopener">Einladung (PDF)</a>' if s.get("pdf") else "") if x)
    tops = "".join(f'<li><span class="top">TOP {e(str(t))}</span> '
                   + (f'<a href="{vor}#{quote(ref)}">{e(x)}</a>' if ref else e(x)) + "</li>" for t, x, ref in punkte)
    return (f'    <details class="sitzung"{" open" if offen else ""}><summary><strong>{e(datum(s["date"]))}{zeit}</strong> '
            f'<span class="gremium">{e(s["gremium"])}</span>{anzahl}</summary>'
            f'{f"<p class=klein>{info}</p>" if info else ""}{f"<ol class=tops>{tops}</ol>" if tops else ""}</details>')


def sitzungen_erzeugen(out, mit_daten=True):
    """out/sitzungen/index.html: kommende Sitzungen aller Gremien und die der letzten zwölf Monate, je Sitzung aufklappbar
    mit Tagesordnung (Link auf den Vorgang in der Karte) und Einladung."""
    daten = _daten() if mit_daten else {"sitzungen": [], "vorgaenge": [], "meta": {}}
    heute = _stand(daten) if daten.get("meta") else date.today()
    vor = "../"
    je_sitzung = {}
    for v in daten["vorgaenge"]:
        for s in v["process"]:
            je_sitzung.setdefault(s["sitzung"], []).append(v)
    alle = sorted(daten["sitzungen"], key=lambda s: (s["date"], s.get("time") or ""))
    kommend = [s for s in alle if s["date"] >= heute.isoformat()]
    grenze = (heute - timedelta(days=TAGE)).isoformat()
    vergangen = [s for s in reversed(alle) if grenze <= s["date"] < heute.isoformat()]
    teile = ["    <h1>Sitzungen</h1>",
             '    <p class="einleitung">Alle Sitzungen der Stadtverordnetenversammlung, der Ausschüsse, Ortsbeiräte und Beiräte: '
             "die kommenden und die der letzten zwölf Monate, jeweils mit Tagesordnung und Einladung. Ein Klick auf einen "
             'Punkt öffnet den Vorgang auf der <a href="../">Karte</a>.</p>',
             f"    <h2>Kommende Sitzungen ({len(kommend)})</h2>"]
    if kommend:
        teile += [_sitzung(s, _punkte(s, je_sitzung.get(s["id"], [])), vor, i == 0) for i, s in enumerate(kommend)]
    else:
        teile.append("    <p>Zurzeit sind keine Sitzungen angekündigt.</p>")
    if (config.EXPORT / "abo").exists() and mit_daten:
        teile.append(f'    <p class="klein">Termine abonnieren: <a href="{vor}data/export/abo/alle.ics">Kalender (.ics)</a> · '
                     f'<a href="{vor}data/export/abo/alle.atom">Feed (Atom)</a> · je Ortsteil auf den <a href="{vor}ortsteile/">Seiten der Ortsteile</a></p>')
    teile.append(f"    <h2>Vergangene Sitzungen der letzten zwölf Monate ({len(vergangen)})</h2>")
    monat = None
    for s in vergangen:
        if s["date"][:7] != monat:
            monat = s["date"][:7]
            teile.append(f'    <h3>{MONATE[int(monat[5:7]) - 1]} {monat[:4]}</h3>')
        teile.append(_sitzung(s, _punkte(s, je_sitzung.get(s["id"], [])), vor, False))
    if not vergangen:
        teile.append("    <p>Keine Sitzungen in den letzten zwölf Monaten im Datenbestand.</p>")
    ziel = out / "sitzungen" / "index.html"
    ziel.parent.mkdir(parents=True, exist_ok=True)
    ziel.write_text(_seite("Sitzungen der Stadtverordneten, Ausschüsse und Ortsbeiräte",
                           "Kommende und vergangene Sitzungen der Stadtverordnetenversammlung, der Ausschüsse, Ortsbeiräte und "
                           "Beiräte mit Tagesordnung, Einladung und Quellenangabe.", vor, "\n".join(teile)), encoding="utf-8")
    return ["sitzungen/index.html"]
