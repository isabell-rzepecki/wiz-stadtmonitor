"""Seiten je Vorgang (out/vorgang/<slug>/index.html): Stationen durch die Gremien, Ortsbezug, Ergebnis laut Bekanntmachung,
Stellungnahmen der Ortsbeiräte und Quellen. Text ohne JavaScript, für Menschen, zum Teilen und für Suchmaschinen.

Inhalt nur aus data/export/vorgaenge.json, also dasselbe wie auf der Karte: Titel sind bereits durch den Namensfilter
gelaufen (pipeline/parse.py), Einreicher nur als Fraktion, Einzelpersonen ohne Namen. Verfahrenspunkte (Eröffnung,
Niederschrift usw.) erhalten keine Seite. Die Adresse leitet sich aus der Vorgangsnummer ab (STV/073/2026 → stv-073-2026).
"""
import re
from urllib.parse import quote

from . import config
from .ortsteilseiten import _daten, _seite, datum, e

ERGEBNIS_ART = {"satzung": "Satzung", "aenderung": "Änderungssatzung", "aufhebung": "Aufhebungssatzung",
                "haushalt": "Haushaltssatzung", "nachtragshaushalt": "Nachtragshaushalt", "jahresabschluss": "Jahresabschluss",
                "hinweis": "Satzung (Bereitstellung)", "bauleitplan": "Bauleitplan"}
ORT = {"hoch": "Ort gesichert", "mittel": "Ort erschlossen", "niedrig": "Ort unsicher"}
EBENE = {"ortsteil": "Ortsteil", "strasse": "Straße", "flurstueck": "Flurstück", "bebauungsplan": "Bebauungsplan"}


def slug(reference):
    """Adresse eines Vorgangs: Kleinbuchstaben, alles außer Buchstaben und Ziffern wird zu einem Bindestrich."""
    return re.sub(r"[^a-z0-9]+", "-", reference.lower()).strip("-")


def pfad(reference, vor=""):
    return f"{vor}vorgang/{slug(reference)}/"


def _einreicher(i):
    cfg = config.STADT.get("einreicher") or {}
    namen = {f["id"]: f["name"] for f in [*cfg.get("fraktionen", []), cfg.get("einzelperson") or {}] if f}
    einzel = (cfg.get("einzelperson") or {}).get("id")
    liste = [namen.get(x, x) for x in i.get("einreicher", [])]
    if not liste:
        return e(i.get("typ", ""))
    wer = liste[0] if i["einreicher"][0] == einzel else f'{"Fraktionen" if len(liste) > 1 else "Fraktion"} {", ".join(liste)}'
    von = "von" if i["einreicher"][0] == einzel else "der"
    return f'{e(i.get("typ", ""))} {von} {e(wer)}' + (f" vom {e(datum(i['datum']))}" if i.get("datum") else "")


def _gremium_links(daten):
    """{Sitzungsnummer: relativer Link zur Gremien- bzw. Ortsteilseite} aus den Sitzungen."""
    ids = {g["id"] for g in config.STADT["gremien"]}
    ortsteile = {o["name"]: o["slug"] for o in config.STADT["ortsteile"]}
    out = {}
    for s in daten["sitzungen"]:
        if s.get("gremium_id") in ids:
            out[s["id"]] = f"gremium/{s['gremium_id'].lower()}/"
        elif s.get("ortsteil") in ortsteile:
            out[s["id"]] = f"ortsteil/{ortsteile[s['ortsteil']]}/"
    return out


def _seite_vorgang(v, links, vorhanden):
    vor = "../../"
    ref = v["reference"]
    stationen = []
    for s in sorted(v["process"], key=lambda s: (s.get("date") or "", s.get("time") or "")):
        zeit = f", {e(s['time'])} Uhr" if s.get("time") else ""
        gremium = e(s["gremium"])
        if links.get(s["sitzung"]):
            gremium = f'<a href="{vor}{links[s["sitzung"]]}">{gremium}</a>'
        titel = f"<br>{e(s['titel'])}" if s.get("titel") and s["titel"] != v["name"] else ""
        nicht = " · nichtöffentlich" if s.get("oeffentlich") is False else ""
        info = " · ".join(x for x in (e(s["ort"]) if s.get("ort") else "",
                                      f'<a href="{e(s["pdf"])}" rel="noopener">Einladung Nr. {e(s["bekanntmachung"])} (PDF)</a>'
                                      if s.get("pdf") else "") if x)
        stationen.append((s.get("date") or "", f'<li><strong>{e(datum(s["date"]))}{zeit}</strong> · {gremium}, TOP {e(str(s["top"]))}'
                                               f'{nicht}{titel}<br><span class="klein">{info}</span></li>'))
    for x in v.get("stellungnahmen") or []:
        pdf = f' · <a href="{e(x["pdf"])}" rel="noopener">Einladung (PDF)</a>' if x.get("pdf") else ""
        stationen.append((x.get("date") or "", f'<li><strong>{e(datum(x["date"]))}</strong> · {e(x["gremium"])}, TOP {e(str(x["top"]))}'
                                               f'<br>{e(x["titel"])}<br><span class="klein">Stellungnahme, zugeordnet über einen '
                                               f'eindeutigen Schlüssel{pdf}</span></li>'))
    teile = [f'    <h1 class="vorgang-titel">{e(v["name"])}</h1>',
             f'    <p class="einleitung">Vorgang {e(ref)}: wann und wo er beraten wurde, mit Fundstellen. Maßgeblich sind die '
             f'verlinkten Bekanntmachungen der Stadt.</p>',
             f'    <p><a class="mehr-link" href="{vor}#{quote(ref)}">Auf der Karte zeigen</a></p>']
    angaben = []
    if v.get("vorlage"):
        angaben.append(("Vorlage", e(v["vorlage"])))
    if v.get("initiative") and config.STADT.get("einreicher"):
        angaben.append(("Eingebracht", _einreicher(v["initiative"]) + ' <span class="klein">(laut Titel)</span>'))
    for g in v.get("gehoert_zu") or []:
        ziel = e(g.get("name") or g["reference"])
        if g["reference"] in vorhanden:
            ziel = f'<a href="{vor}{pfad(g["reference"])}">{ziel}</a>'
        angaben.append(("Gehört zu", f'{ziel} <span class="klein">({e(g.get("ueber", ""))})</span>'))
    if angaben:
        teile.append('    <dl class="zahlen">' + "".join(f"<dt>{k}</dt><dd>{w}</dd>" for k, w in angaben) + "</dl>")
    teile.append(f"    <h2>Beratungen ({len(stationen)})</h2>")
    teile.append('    <ol class="vorgaenge">' + "".join(h for _, h in sorted(stationen, key=lambda t: t[0])) + "</ol>")
    teile.append("    <h2>Ergebnis</h2>")
    if v.get("ergebnisse"):
        zeilen = []
        for x in v["ergebnisse"]:
            sicher = "" if x.get("sicherheit") != "möglicherweise" else " (möglicherweise zugehörig)"
            beschluss = f", Beschluss vom {e(datum(x['beschluss']))}" if x.get("beschluss") else ""
            zeilen.append(f'<li>{e(ERGEBNIS_ART.get(x.get("art"), x.get("art", "")))} bekanntgemacht am '
                          f'{e(datum(x["veroeffentlicht"]))}{beschluss}{sicher}<br>{e(x.get("gegenstand", ""))}<br>'
                          f'<span class="klein"><a href="{e(x["pdf"])}" rel="noopener">Bekanntmachung Nr. {e(x["nr"])} (PDF)</a></span></li>')
        teile.append('    <ul class="vorgaenge">' + "".join(zeilen) + "</ul>")
        teile.append('    <p class="klein">Die Stadt veröffentlicht keine Beschlüsse. Eine bekanntgemachte Satzung, ein Haushalt oder '
                     "ein Plan belegt aber, dass beschlossen wurde.</p>")
    else:
        teile.append("    <p>Das Ergebnis ist nicht veröffentlicht. Die Einladungen nennen nur die Tagesordnung; der Stadtmonitor "
                     "leitet keine Ergebnisse ab.</p>")
    for b in v.get("beteiligung") or []:
        stufen = "".join(f'<li>{e(st.get("titel", ""))}'
                         + (f", Beschluss {e(datum(st['beschluss']))}" if st.get("beschluss") else "")
                         + (f", {e(datum(st['von']))} bis {e(datum(st['bis']))}" if st.get("von") and st.get("bis") else "")
                         + "</li>" for st in b.get("stufen", []))
        teile.append("    <h2>Beteiligung der Öffentlichkeit</h2>")
        teile.append(f'    <ul class="vorgaenge">{stufen}</ul><p class="klein"><a href="{e(b["pdf"])}" rel="noopener">'
                     f'Bekanntmachung Nr. {e(b["nr"])} (PDF)</a></p>')
    if v.get("locations") or v.get("plans"):
        ortsteile = {o["name"]: o["slug"] for o in config.STADT["ortsteile"]}
        orte = []
        for l in v.get("locations", []):
            name = e(l["name"])
            if l.get("level") == "ortsteil" and l.get("ortsteil") in ortsteile:
                name = f'<a href="{vor}ortsteil/{ortsteile[l["ortsteil"]]}/">{name}</a>'
            elif l.get("ortsteil") in ortsteile:
                name += f' (<a href="{vor}ortsteil/{ortsteile[l["ortsteil"]]}/">{e(l["ortsteil"])}</a>)'
            orte.append(f'<li>{EBENE.get(l.get("level"), "")}: {name} <span class="klein">{ORT.get(l.get("confidence"), "")}</span></li>')
        orte += [f'<li>Bauleitplan: {e(p["titel"])}</li>' for p in v.get("plans", [])]
        teile.append("    <h2>Ortsbezug</h2>")
        teile.append('    <ul class="vorgaenge">' + "".join(orte) + "</ul>")
        teile.append('    <p class="klein">Abgeleitet: gesichert über das Gremium des Ortsteils oder einen eindeutigen Plan, '
                     "erschlossen über einen Orts- oder Straßennamen im Titel.</p>")
    erste = min((s.get("date") or "" for s in v["process"]), default="")
    beschreibung = f"{v['name'][:140]} – Beratungen in den Gremien der Stadt {config.STADT['stadt']['name']}" + \
                   (f" seit {datum(erste)}" if erste else "") + ", mit Fundstellen."
    titel = v["name"] if len(v["name"]) <= 90 else v["name"][:90].rsplit(" ", 1)[0] + " …"
    return _seite(titel, beschreibung, vor, "\n".join(teile))


def erzeugen(out, mit_daten=True):
    """Schreibt out/vorgang/<slug>/index.html für jeden Vorgang ohne Verfahrenspunkt; gibt die Pfade zurück."""
    if not mit_daten:
        return []
    daten = _daten()
    vorgaenge = [v for v in daten["vorgaenge"] if not v.get("verfahrenspunkt") and v.get("reference")]
    vorhanden = {v["reference"] for v in vorgaenge}
    links = _gremium_links(daten)
    pfade = []
    for v in vorgaenge:
        ziel = out / pfad(v["reference"]) / "index.html"
        ziel.parent.mkdir(parents=True, exist_ok=True)
        ziel.write_text(_seite_vorgang(v, links, vorhanden), encoding="utf-8")
        pfade.append(f"{pfad(v['reference'])}index.html")
    return pfade
