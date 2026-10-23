"""Wahlergebnisse und Sitzverteilung (nur amtliche Quellen, ohne Personennamen).

- Kommunalwahlen: amtliche Bekanntmachungen des Ergebnisses (PDF) bzw. die amtliche Ergebnispräsentation der
  Gemeindewahlleitung (votemanager). Übernommen werden nur die Tabellen der Wahlvorschläge bis „Wahlgebiet
  insgesamt“ (Stimmen, Anteil, Sitze) und die Kopfzahlen; Bewerberlisten und Gewählte nicht.
- Bundestags- und Europawahlen: Wahlbezirksstatistik der Bundeswahlleiterin, summiert über die Wahlbezirke der
  Gemeinde einschließlich der Briefwahlbezirke.
Fehlt eine amtliche Quelle, bleibt die Wahl mit Stufe „luecke“ stehen. Ergebnisse liegen im Repository
(data/wahlen/wahlen.json); scheitert ein Abruf, bleibt dieser Stand.
"""
import hashlib
import html
import json
import re
import subprocess
import time
import zipfile
from datetime import date

from . import audit, config, net

W = config.STADT["wahlen"]
RAW = config.RAW / "wahlen"
OUT_REPO = config.ROOT / "data" / "wahlen" / "wahlen.json"
OUT = config.EXPORT / "wahlen.json"
GMDE = config.STADT["stadt"]["gemeindeschluessel"]  # 06636016: Land 06, RB 6, Kreis 36, Gemeinde 016
ALTER = 30 * 86400


def _laden(ziel, url, quelle):
    if ziel.exists() and time.time() - ziel.stat().st_mtime < ALTER:
        return
    try:
        body, _ = net.get(url, tries=2)
    except Exception as e:
        audit.abruf(quelle, url, getattr(e, "code", ""), "", "", "", str(e)[:200])
        print(f"{quelle}: Abruf gescheitert ({e}); Stand im Repository bleibt")
        return
    ziel.write_bytes(body)
    audit.abruf(quelle, url, 200, len(body), hashlib.sha256(body).hexdigest(), "", "")


def fetch():
    RAW.mkdir(parents=True, exist_ok=True)
    for w in W["kommunal"]:
        if w.get("url"):
            _laden(RAW / (w["id"] + (".pdf" if w["quelle"] == "bekanntmachung" else ".html")), w["url"], "wahl_" + w["id"])
    for w in W["bund"]:
        _laden(RAW / f"{w['id']}.zip", w["url"], "wahl_" + w["id"])


# --- Kommunalwahlen -------------------------------------------------------------------------------------------

def _int(s):
    return int(s.replace(".", ""))


def _pct(s):
    return float(s.replace(",", "."))


def bekanntmachung(text):
    """[{gebiet, wahlberechtigte, waehlende, beteiligung, stimmzettel_gueltig, stimmzettel_ungueltig, stimmen_gueltig,
    vorschlaege: [{name, stimmen, anteil, sitze}], sitze}] aus der Bekanntmachung (Text von pdftotext -layout)."""
    out, cur, in_tab = [], None, False
    vorher = ""
    for line in text.split("\n"):
        s = line.strip()
        m = re.match(r"Zur \S+wahl waren ([\d.]+) Personen wahlberechtigt, davon haben ([\d.]+) Personen gewählt", s)
        if m:
            gebiet = re.match(r"^(.+?):$", vorher)
            cur = {"gebiet": gebiet.group(1) if gebiet else None, "wahlberechtigte": _int(m.group(1)), "waehlende": _int(m.group(2)),
                   "vorschlaege": []}
            out.append(cur)
            continue
        if s:
            vorher = s
        if not cur:
            continue
        if m := re.match(r"Die Wahlbeteiligung betrug ([\d,]+) %", s):
            cur["beteiligung"] = _pct(m.group(1))
        elif m := re.match(r"Von den insgesamt abgegebenen Stimmzetteln waren ([\d.]+) Stimmzettel gültig und ([\d.]+) Stimmzettel ungültig", s):
            cur["stimmzettel_gueltig"], cur["stimmzettel_ungueltig"] = _int(m.group(1)), _int(m.group(2))
        elif m := re.match(r"Hieraus resultieren ([\d.]+) gültige Stimmen", s):
            cur["stimmen_gueltig"] = _int(m.group(1))
        elif s.startswith("Wahlvorschlag"):
            in_tab = True
        elif in_tab and (m := re.match(r"Wahlgebiet insgesamt\s+([\d.]+)\s+(\d+)$", s)):
            cur["sitze"] = int(m.group(2))
            in_tab = False
        elif in_tab and (m := re.match(r"(.+?)\s{2,}([\d.]+)\s+([\d,]+)\s*%\s+(\d+)$", s)):
            cur["vorschlaege"].append({"name": m.group(1).strip(), "stimmen": _int(m.group(2)), "anteil": _pct(m.group(3)), "sitze": int(m.group(4))})
    return out


def votemanager(seite):
    """Gemeindeergebnis aus der votemanager-Seite: Wahlberechtigte, Wählende, Summen je Liste, Sitze je Liste."""
    s = html.unescape(re.sub(r"<script.*?</script>|<style.*?</style>", "", seite, flags=re.S))
    s = re.sub(r"(\s*\|\s*)+", " | ", re.sub(r"<[^>]+>", " | ", s))
    kopf = re.search(r"Wahlberechtigte \| ([\d.]+) \| Wähler/innen \| ([\d.]+) \| ([\d.,]+) %", s)
    summen = re.findall(r"\| ([^|]+?) - Summe Kandidaten-Stimmen \| ([\d.]+) \| ([\d.]+) % ", s)
    gesamt = re.search(r"Es wurden (\d+)\s+Sitze vergeben", s)
    teil = s[gesamt.end():] if gesamt else ""
    parteien = [p.strip() for p, _, _ in summen]
    sitze = {}
    # Mandatsliste „Partei | Kandidat | Mandat“: nur die Partei wird gezählt, Namen werden nicht übernommen
    tok, i = [t.strip() for t in teil.split(" | ")], 0
    while i < len(tok):
        if tok[i] in parteien:
            sitze[tok[i]] = sitze.get(tok[i], 0) + 1
            i += 3
        elif sitze:  # Ende der Mandatsliste
            break
        else:
            i += 1
    if not kopf or not summen:
        return None
    gueltig = sum(_int(n) for _, n, _ in summen)
    return [{"gebiet": None, "wahlberechtigte": _int(kopf.group(1)), "waehlende": _int(kopf.group(2)), "beteiligung": _pct(kopf.group(3)),
             "stimmen_gueltig": gueltig, "sitze": int(gesamt.group(1)) if gesamt else sum(sitze.values()),
             "vorschlaege": [{"name": p.strip(), "stimmen": _int(n), "anteil": float(a), "sitze": sitze.get(p.strip(), 0)} for p, n, a in summen]}]


def _slug(gebiet):
    o = next((o for o in config.STADT["ortsteile"] if gebiet and gebiet in [o["name"], o.get("gemarkung"), *o.get("varianten", [])]), None)
    if not o and gebiet:  # „Berlepsch-Ellerode-Hübenthal“ u. ä.: Anfang des Namens
        o = next((o for o in config.STADT["ortsteile"] if gebiet.startswith(o["name"])), None)
    return o["slug"] if o else None


def kommunal():
    out = []
    for w in W["kommunal"]:
        e = {k: w[k] for k in ("id", "art", "titel", "datum", "stufe", "stufe_text")}
        e["quelle_url"] = w.get("url")
        ergebnisse = None
        if w["quelle"] == "bekanntmachung" and (RAW / f"{w['id']}.pdf").exists():
            text = subprocess.run(["pdftotext", "-layout", str(RAW / f"{w['id']}.pdf"), "-"], capture_output=True, text=True, check=True).stdout
            ergebnisse = bekanntmachung(text)
        elif w["quelle"] == "votemanager" and (RAW / f"{w['id']}.html").exists():
            ergebnisse = votemanager((RAW / f"{w['id']}.html").read_text(encoding="utf-8", errors="replace"))
        if ergebnisse is not None:
            for r in ergebnisse:
                if w["art"] == "ortsbeirat":
                    r["ortsteil"] = _slug(r["gebiet"])
                else:
                    r["gebiet"] = None
                # Plausibilität: Summe der Stimmen und Sitze
                r["pruefung"] = ("ok" if sum(v["stimmen"] for v in r["vorschlaege"]) == r.get("stimmen_gueltig")
                                 and sum(v["sitze"] for v in r["vorschlaege"]) == r.get("sitze") else "abweichend")
            e["ergebnisse"] = ergebnisse
        out.append(e)
    return out


# --- Bundestags- und Europawahlen -----------------------------------------------------------------------------

def _csv(raw):
    for enc in ("utf-8-sig", "cp1252"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    raise ValueError("Kodierung unbekannt")


def bund_ergebnis(w):
    p = RAW / f"{w['id']}.zip"
    if not p.exists():
        return None
    with zipfile.ZipFile(p) as z:
        zeilen = _csv(z.read(next(n for n in z.namelist() if n.endswith(w["datei"])))).splitlines()
    h = next(i for i, l in enumerate(zeilen[:20]) if "Wahlbezirk" in l and "Gemeinde" in l)
    cols = [c.strip().strip('"') for c in zeilen[h].split(";")]
    idx = {c: i for i, c in enumerate(cols)}
    rb = next(c for c in cols if c.startswith("Reg"))
    a = next(c for c in cols if c.startswith("Wahlberechtigte") and "(A)" in c or c == "Wahlberechtigte")
    b = next(c for c in cols if c.startswith(("Wähler (B)", "Wählende (B)")) or c == "Wählende")
    gueltig_i = max(i for i, c in enumerate(cols) if "gültig" in c.lower() and "ungültig" not in c.lower())
    parteien = []
    for i in range(gueltig_i + 1, len(cols)):
        c = cols[i]
        if not c or "Wahlbezirk" in c:
            break
        parteien.append((i, re.sub(r"^Z_| - Zweitstimmen$", "", c)))
    summe = {"wahlberechtigte": 0, "waehlende": 0, "gueltig": 0, "wahlbezirke": 0}
    stimmen = {n: 0 for _, n in parteien}
    for l in zeilen[h + 1:]:
        f = [x.strip().strip('"') for x in l.split(";")]
        if len(f) < len(parteien) or (f[idx["Land"]], f[idx[rb]], f[idx["Kreis"]], f[idx["Gemeinde"]]) != (GMDE[:2], GMDE[2], GMDE[3:5], GMDE[5:]):
            continue
        num = lambda i: int(f[i] or 0)
        summe["wahlbezirke"] += 1
        summe["wahlberechtigte"] += num(idx[a])
        summe["waehlende"] += num(idx[b])
        summe["gueltig"] += num(gueltig_i)
        for i, n in parteien:
            stimmen[n] += num(i)
    if not summe["wahlbezirke"]:
        return None
    pruef = "ok" if sum(stimmen.values()) == summe["gueltig"] else "abweichend"
    return {**summe, "beteiligung": round(100 * summe["waehlende"] / summe["wahlberechtigte"], 2), "pruefung": pruef,
            "parteien": {n: v for n, v in sorted(stimmen.items(), key=lambda x: -x[1]) if v}}


def build():
    alt = json.loads(OUT_REPO.read_text(encoding="utf-8")) if OUT_REPO.exists() else {}
    kom = kommunal()
    for e in kom:  # ohne Rohdaten: letzten Stand übernehmen
        if "ergebnisse" not in e:
            prev = next((x for x in alt.get("kommunal", []) if x["id"] == e["id"]), None)
            if prev and "ergebnisse" in prev:
                e["ergebnisse"] = prev["ergebnisse"]
    bund = []
    for w in W["bund"]:
        r = bund_ergebnis(w) or next((x.get("ergebnis") for x in alt.get("bund", []) if x["id"] == w["id"]), None)
        bund.append({**{k: w[k] for k in ("id", "titel", "datum", "stimme")}, "quelle_url": w["url"], "ergebnis": r})
    daten = {"generated_at": date.today().isoformat(), "kommunal": kom, "bund": bund,
             "bund_attribution": W["bund_attribution"]}
    OUT_REPO.parent.mkdir(parents=True, exist_ok=True)
    OUT_REPO.write_text(json.dumps(daten, ensure_ascii=False, indent=1), encoding="utf-8")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(daten, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    zeilen = [{"wahl": e["id"], "gebiet": r.get("gebiet") or "Gemeinde", "pruefung": r["pruefung"], "sitze": r.get("sitze", "")}
              for e in kom for r in e.get("ergebnisse", [])]
    zeilen += [{"wahl": b["id"], "gebiet": "Gemeinde", "pruefung": b["ergebnis"]["pruefung"] if b["ergebnis"] else "fehlt", "sitze": ""} for b in bund]
    audit.tabelle("wahlen_pruefung.tsv", ["wahl", "gebiet", "pruefung", "sitze"], zeilen)
    abw = [z for z in zeilen if z["pruefung"] != "ok"]
    print(f"Wahlen: {sum(len(e.get('ergebnisse', [])) for e in kom)} kommunale Ergebnisse, {sum(1 for b in bund if b['ergebnis'])} Bundes-/Europawahlen; "
          f"{len(abw)} Prüfungen nicht ok")
    return daten
