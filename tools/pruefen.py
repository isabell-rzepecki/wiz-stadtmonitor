"""Prüfung der Erfassungen durch die Prüfgruppe (Übergabe v0.4.2, W5). Läuft nur lokal, nie im Browser oder in GitHub Actions.

Zweck: Für die Stadt gibt es keinen Mietspiegel. Aus Exportdateien der Erfassungs-App (erfassen.html) entsteht ein geprüfter
Bestand, aus dem tools/veroeffentlichen.py nur zusammengefasste, zulässige Dateien erzeugt (Regeln R1–R9).

Aufruf (ARBEIT und SCHLUESSEL außerhalb jedes Git-Repositorys):
  python tools/pruefen.py schluessel SCHLUESSEL                        neues Schlüsselpaar; öffentlichen Teil in stadt.json
  python tools/pruefen.py einlesen   -a ARBEIT -s SCHLUESSEL -p P-1 DATEI…   Exportdateien entschlüsseln, prüfen, aufnehmen
  python tools/pruefen.py pruefen    -a ARBEIT -s SCHLUESSEL -p P-1    Vermieter-Schlüssel, Dubletten, Konflikte, Prüfliste
  python tools/pruefen.py freigeben  -a ARBEIT -s SCHLUESSEL -p P-1 [ID…|--alle]   Freigabe (je Eintrag zwei Prüfer-IDs)
  python tools/pruefen.py verwerfen  -a ARBEIT -s SCHLUESSEL -p P-1 ID --grund TEXT
  python tools/pruefen.py name       -a ARBEIT -s SCHLUESSEL -p P-1 ID --oeffentlich|--nur-kategorie
  python tools/pruefen.py zusammenfuehren -a … V-003 V-007             zwei Vermieter-Schlüssel als dieselbe Person führen
  python tools/pruefen.py loeschen   -a ARBEIT -s SCHLUESSEL -p P-1 (ID|--code XXXX-XXXX) --grund TEXT   Widerruf: ganz entfernen
  python tools/pruefen.py widerspruch -a ARBEIT -s SCHLUESSEL -p P-1 GEBAEUDE… --grund TEXT   Eigentum zu den Gebäuden
                                     (und allen Gebäuden derselben Person) löschen, Gebäude auf die Sperrliste
  python tools/pruefen.py fristen    -a ARBEIT -s SCHLUESSEL -p P-1 [--loeschen]   Einträge nach der Speicherdauer

Ausgabe: ARBEIT/audit/pruefung_<datum>.tsv, ohne Namen von Privatpersonen und ohne Mietbeträge.
"""
import argparse
import json
import sys
from datetime import date
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

import pruefgruppe as pg

SPEICHERDAUER = pg.STADT["wohnen_eigentum"]["erfassung"]["speicherdauer_monate"]

FORMAT = "wiz-stadtmonitor-erfassung"
JP_KATEGORIEN = {k["code"] for k in pg.STADT["wohnen_eigentum"]["kategorien"]} - {"privat", "unklar"}


def validator(typ):
    return Draft202012Validator(json.loads(pg.SCHEMAS[typ].read_text(encoding="utf-8")), format_checker=FormatChecker())


def einlesen(arbeit, dateien):
    """Exportdateien entschlüsseln, gegen Schema und Freitextregeln prüfen; gültige Einträge in den Bestand, sonst abgewiesen."""
    v = {t: validator(t) for t in pg.SCHEMAS}
    zeilen, neu = [], 0
    for datei in dateien:
        d = json.loads(Path(datei).read_text(encoding="utf-8"))
        if d.get("format") != FORMAT or d.get("version") != 1 or d.get("typ") not in pg.SCHEMAS or d.get("alg") != pg.ALG:
            raise pg.Abbruch(f"{Path(datei).name}: keine Exportdatei der Erfassung (Format, Version, Typ oder Verfahren unbekannt).")
        for e in d["eintraege"]:
            grund = None
            if e.get("key_id") != arbeit.schl.key_id:
                grund = f"anderer Schlüssel ({e.get('key_id')})"
            else:
                try:
                    rec = json.loads(arbeit.schl.oeffnen(e["ciphertext"]))
                except Exception:  # noqa: BLE001 – Inhalt nie ausgeben
                    rec, grund = None, "nicht entschlüsselbar"
            if not grund:
                fehler = sorted(v[d["typ"]].iter_errors(rec), key=lambda x: list(x.path))
                if fehler:
                    grund = "Schema: " + "; ".join(f"{'.'.join(map(str, f.path)) or '–'}: {f.validator}" for f in fehler[:3])
                elif (rec.get("erfassung_id") or rec.get("angabe_id")) != e["id"]:
                    grund = "Kennung passt nicht zum Eintrag"
            if not grund and d["typ"] == "eigentum":
                grund = (pg.freitext(rec["objekt"].get("lage_hinweis"), ohne_ziffern=True) or pg.freitext(rec.get("bemerkung")))
            if not grund and d["typ"] == "miete" and rec.get("vermieter_schluessel", "").startswith("V-"):
                grund = "Vermieter-Schlüssel V-… darf in Mietangaben nicht stehen"
            if not grund and d["typ"] == "eigentum" and rec["objekt"]["id"] in arbeit.d.get("sperrliste", []):
                grund = "Widerspruch zu diesem Gebäude (Sperrliste)"
            if not grund and e["id"] in arbeit.eintraege:
                zeilen.append([e["id"], d["typ"], "schon im Bestand", Path(datei).name])
                continue
            if grund:
                zeilen.append([e["id"], d["typ"], f"abgewiesen: {grund}", Path(datei).name])
                continue
            arbeit.eintraege[e["id"]] = {"typ": d["typ"], "datensatz": rec, "quelle": Path(datei).name, "erfasser": d.get("erfasser"),
                                         "eingelesen": pg.jetzt(), "status": "offen", "konflikt": None, "freigaben": [], "vermieter": None}
            arbeit.verlauf("eingelesen", e["id"])
            neu += 1
            zeilen.append([e["id"], d["typ"], "aufgenommen", Path(datei).name])
    arbeit.speichern()
    arbeit.audit(f"einlesen_{date.today()}.tsv", ["id", "typ", "ergebnis", "datei"], zeilen)
    return neu, zeilen


def _aendern(e, feld, wert):
    """Änderung am Eintrag: bisherige Freigaben gelten nicht mehr."""
    if e.get(feld) != wert:
        e[feld] = wert
        e["freigaben"] = []


def pruefen(arbeit):
    """Vermieter-Schlüssel vergeben, Dubletten und Konflikte je Gebäude bestimmen, Prüfliste schreiben."""
    aktiv = {i: e for i, e in arbeit.eintraege.items() if e["status"] == "offen"}
    eig = {i: e for i, e in aktiv.items() if e["typ"] == "eigentum"}
    # 1. Vermieter-Schlüssel: juristische Personen über den normierten Namen, Privatpersonen über den (entschlüsselten) Namen
    jp_namen = {}
    for i, e in sorted(eig.items(), key=lambda x: x[1]["datensatz"]["erfasst_am"]):
        r = e["datensatz"]
        if r["kategorie"] in JP_KATEGORIEN and r.get("name_juristische_person"):
            n = pg.name_normieren(r["name_juristische_person"])
            _aendern(e, "vermieter", jp_namen.setdefault(n, f"JP:{' '.join(r['name_juristische_person'].split())}"))
        elif r["kategorie"] != "privat":
            _aendern(e, "vermieter", None)
    bekannt = {}  # normierter Name -> V-Schlüssel
    for i, e in eig.items():
        if e["datensatz"]["kategorie"] == "privat" and (e.get("vermieter") or "").startswith("V-") and e["datensatz"].get("name_privat_enc"):
            bekannt.setdefault(pg.name_normieren(arbeit.name_oeffnen(i, "Abgleich Vermieter-Schlüssel")), e["vermieter"])
    for i, e in sorted(eig.items(), key=lambda x: x[1]["datensatz"]["erfasst_am"]):
        if e["datensatz"]["kategorie"] != "privat" or (e.get("vermieter") or "").startswith("V-"):
            continue
        name = arbeit.name_oeffnen(i, "Abgleich Vermieter-Schlüssel")
        n = pg.name_normieren(name) if name else None
        if n and n in bekannt:
            _aendern(e, "vermieter", bekannt[n])
        else:
            _aendern(e, "vermieter", f"V-{arbeit.d['vermieter_naechste']:03d}")
            arbeit.d["vermieter_naechste"] += 1
            if n:
                bekannt[n] = e["vermieter"]
    # 2. Eigentum je Gebäude: gleiche Angaben = Dublette (ältere verworfen), abweichende = Konflikt
    je_geb = {}
    for i, e in eig.items():
        je_geb.setdefault(e["datensatz"]["objekt"]["id"], []).append(i)
    for ids in je_geb.values():
        ids.sort(key=lambda i: eig[i]["datensatz"]["erfasst_am"])
        merkmal = lambda i: (eig[i]["datensatz"]["kategorie"], eig[i]["vermieter"], eig[i]["datensatz"].get("vermietet"))  # noqa: E731
        if len({merkmal(i) for i in ids}) == 1:
            for i in ids[:-1]:
                eig[i]["status"], eig[i]["konflikt"] = "verworfen", f"Dublette von {ids[-1]}"
                arbeit.verlauf("Dublette verworfen", i)
            _aendern(eig[ids[-1]], "konflikt", None)
        else:
            for i in ids:
                _aendern(eig[i], "konflikt", f"abweichende Angaben zum Gebäude ({len(ids)} Einträge)")
    # 3. Mietangaben: Vermieter über das Gebäude (nur juristische Person, geprüfter Eintrag), mögliche Dubletten
    jp_je_geb = {e["datensatz"]["objekt"]["id"]: e["vermieter"] for e in eig.values()
                 if e["status"] == "offen" and not e.get("konflikt") and (e.get("vermieter") or "").startswith("JP:")}
    gruppen = {}
    for i, e in aktiv.items():
        if e["typ"] != "miete":
            continue
        r = e["datensatz"]
        eigen = r.get("vermieter_schluessel")
        eigen = jp_namen.get(pg.name_normieren(eigen[3:]), eigen) if eigen else None
        _aendern(e, "vermieter", eigen or jp_je_geb.get(r["gebaeude_id"]))
        gruppen.setdefault((r["gebaeude_id"], r["nettokalt_eur"], r["vertragsbeginn_jahr"], r["wohnflaeche_klasse"]), []).append(i)
    for ids in gruppen.values():
        for i in ids:
            _aendern(arbeit.eintraege[i], "konflikt", f"mögliche Dublette ({len(ids)} gleiche Angaben)" if len(ids) > 1 else None)
    arbeit.verlauf("geprüft")
    arbeit.speichern()
    # Prüfliste ohne Namen von Privatpersonen und ohne Mietbeträge
    zeilen = []
    for i, e in sorted(arbeit.eintraege.items(), key=lambda x: (x[1]["typ"], x[1]["datensatz"].get("erfasst_am", ""))):
        r = e["datensatz"]
        zeilen.append([i, e["typ"], r["objekt"]["id"] if e["typ"] == "eigentum" else r["gebaeude_id"], r.get("kategorie", ""),
                       e.get("vermieter") or "", e["status"], e.get("konflikt") or "", len(set(e["freigaben"])),
                       "ja" if arbeit.freigegeben(e) else "nein", e.get("name_oeffentlich", "")])
    p = arbeit.audit(f"pruefung_{date.today()}.tsv", ["id", "typ", "gebaeude", "kategorie", "vermieter", "status", "konflikt", "freigaben",
                                                     "freigegeben", "name_oeffentlich"], zeilen)
    return p, zeilen


def freigeben(arbeit, ids=None, alle=False):
    n = 0
    for i, e in arbeit.eintraege.items():
        if (alle or i in (ids or [])) and e["status"] == "offen" and not e.get("konflikt") and arbeit.pruefer not in e["freigaben"]:
            e["freigaben"].append(arbeit.pruefer)
            arbeit.verlauf("freigegeben", i)
            n += 1
    arbeit.speichern()
    return n


def verwerfen(arbeit, i, grund):
    e = arbeit.eintraege[i]
    e["status"], e["konflikt"], e["freigaben"] = "verworfen", f"verworfen: {grund}", []
    arbeit.verlauf(f"verworfen ({grund})", i)
    arbeit.speichern()


def name_entscheiden(arbeit, i, oeffentlich):
    """Sonstige juristische Personen: Name nur veröffentlichen, wenn er keine natürliche Person erkennbar macht."""
    _aendern(arbeit.eintraege[i], "name_oeffentlich", bool(oeffentlich))
    arbeit.verlauf(f"Name {'öffentlich' if oeffentlich else 'nur Kategorie'}", i)
    arbeit.speichern()


def zusammenfuehren(arbeit, behalten, aufgeben):
    for e in arbeit.eintraege.values():
        if e.get("vermieter") == aufgeben:
            _aendern(e, "vermieter", behalten)
    arbeit.verlauf(f"{aufgeben} zu {behalten} zusammengeführt")
    arbeit.speichern()


def code_zu_id(arbeit, code):
    """Widerrufscode aus der App (die ersten 8 Zeichen der Kennung, als XXXX-XXXX) zur Kennung."""
    c = code.replace("-", "").strip().lower()
    treffer = [i for i in arbeit.eintraege if i.replace("-", "")[:8] == c]
    if len(treffer) != 1:
        raise pg.Abbruch(f"Widerrufscode {code}: {len(treffer)} Einträge gefunden.")
    return treffer[0]


def loeschen(arbeit, i, grund):
    """Widerruf oder Widerspruch: Eintrag ganz entfernen; im Verlauf bleibt nur Kennung, Zeit und Grund."""
    arbeit.eintraege.pop(i)
    arbeit.verlauf(f"gelöscht ({grund})", i)
    arbeit.speichern()


def widerspruch(arbeit, gebaeude, grund):
    """Widerspruch von Vermieter:innen (Art. 21 DSGVO): Eigentumseinträge zu den Gebäuden und zu allen Gebäuden mit demselben
    privaten Vermieter-Schlüssel löschen; die Gebäude kommen auf die Sperrliste und werden nicht erneut aufgenommen."""
    eig = {i: e for i, e in arbeit.eintraege.items() if e["typ"] == "eigentum"}
    ziele = set(gebaeude)
    schluessel = {e["vermieter"] for e in eig.values() if e["datensatz"]["objekt"]["id"] in ziele and (e.get("vermieter") or "").startswith("V-")}
    ziele |= {e["datensatz"]["objekt"]["id"] for e in eig.values() if e.get("vermieter") in schluessel}
    weg = [i for i, e in eig.items() if e["datensatz"]["objekt"]["id"] in ziele]
    for i in weg:
        arbeit.eintraege.pop(i)
        arbeit.verlauf(f"gelöscht ({grund})", i)
    arbeit.d["sperrliste"] = sorted(set(arbeit.d.get("sperrliste", [])) | ziele)
    arbeit.speichern()
    return weg, ziele


def fristen(arbeit, loeschen_=False, heute=None):
    """Einträge, deren Eingang länger als die Speicherdauer zurückliegt; auf Wunsch löschen."""
    heute = heute or date.today()
    j, m = divmod(heute.year * 12 + heute.month - 1 - SPEICHERDAUER, 12)
    grenze = date(j, m + 1, min(heute.day, 28))
    faellig = [i for i, e in arbeit.eintraege.items() if date.fromisoformat(e["eingelesen"][:10]) < grenze]
    if loeschen_:
        for i in faellig:
            arbeit.eintraege.pop(i)
            arbeit.verlauf(f"gelöscht (Speicherdauer {SPEICHERDAUER} Monate)", i)
        arbeit.speichern()
    return faellig


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="befehl", required=True)
    s = sub.add_parser("schluessel")
    s.add_argument("datei")
    for name in ("einlesen", "pruefen", "freigeben", "verwerfen", "name", "zusammenfuehren", "loeschen", "widerspruch", "fristen"):
        p = sub.add_parser(name)
        p.add_argument("-a", "--arbeit", required=True)
        p.add_argument("-s", "--schluessel", required=True)
        p.add_argument("-p", "--pruefer", required=True)
        if name == "einlesen":
            p.add_argument("dateien", nargs="+")
        if name == "freigeben":
            p.add_argument("ids", nargs="*")
            p.add_argument("--alle", action="store_true", help="alle offenen Einträge ohne Konflikt")
        if name in ("verwerfen", "name"):
            p.add_argument("id")
        if name == "loeschen":
            p.add_argument("id", nargs="?")
            p.add_argument("--code", help="Widerrufscode aus der App (XXXX-XXXX)")
        if name == "widerspruch":
            p.add_argument("gebaeude", nargs="+")
        if name == "fristen":
            p.add_argument("--loeschen", action="store_true")
        if name in ("verwerfen", "loeschen", "widerspruch"):
            p.add_argument("--grund", required=True)
        if name == "name":
            g = p.add_mutually_exclusive_group(required=True)
            g.add_argument("--oeffentlich", action="store_true")
            g.add_argument("--nur-kategorie", action="store_true")
        if name == "zusammenfuehren":
            p.add_argument("behalten")
            p.add_argument("aufgeben")
    a = ap.parse_args(argv)
    if a.befehl == "schluessel":
        print(json.dumps(pg.schluessel_erzeugen(a.datei), ensure_ascii=False))
        print("In config/stadt.json unter wohnen_eigentum.erfassung.schluessel eintragen (nur diesen öffentlichen Teil).", file=sys.stderr)
        return
    arbeit = pg.Arbeit(a.arbeit, pg.Schluessel(a.schluessel), a.pruefer)
    if a.befehl == "einlesen":
        neu, zeilen = einlesen(arbeit, a.dateien)
        print(f"{neu} aufgenommen, {sum(1 for z in zeilen if z[2].startswith('abgewiesen'))} abgewiesen")
    elif a.befehl == "pruefen":
        p, zeilen = pruefen(arbeit)
        print(f"{sum(1 for z in zeilen if z[6] and z[5] == 'offen')} Konflikte, {sum(1 for z in zeilen if z[8] == 'ja')} freigegeben; Prüfliste {p}")
    elif a.befehl == "freigeben":
        print(f"{freigeben(arbeit, a.ids, a.alle)} Einträge freigegeben durch {a.pruefer}")
    elif a.befehl == "verwerfen":
        verwerfen(arbeit, a.id, a.grund)
    elif a.befehl == "name":
        name_entscheiden(arbeit, a.id, a.oeffentlich)
    elif a.befehl == "zusammenfuehren":
        zusammenfuehren(arbeit, a.behalten, a.aufgeben)
    elif a.befehl == "loeschen":
        if bool(a.id) == bool(a.code):
            raise pg.Abbruch("Kennung oder --code angeben (nicht beides).")
        loeschen(arbeit, a.id or code_zu_id(arbeit, a.code), a.grund)
    elif a.befehl == "widerspruch":
        weg, ziele = widerspruch(arbeit, a.gebaeude, a.grund)
        print(f"{len(weg)} Einträge gelöscht, {len(ziele)} Gebäude auf der Sperrliste")
    elif a.befehl == "fristen":
        f = fristen(arbeit, a.loeschen)
        print(f"{len(f)} Einträge älter als {SPEICHERDAUER} Monate" + (" gelöscht" if a.loeschen else " (mit --loeschen löschen)"))


if __name__ == "__main__":
    main()
