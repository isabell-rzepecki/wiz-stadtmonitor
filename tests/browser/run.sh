#!/usr/bin/env bash
# Browser-Prüfung: Seite zweimal zusammenstellen (ohne Daten und mit den Testdaten aus tests/fixtures),
# je einen lokalen Server starten und die Tests ausführen. Aufruf aus dem Wurzelverzeichnis:
#   bash tests/browser/run.sh      (einmalig vorher: npm install --prefix tests/browser und
#                                   cd tests/browser && npx playwright install chromium, oder CHROMIUM=<Pfad> setzen)
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
TMP="$(mktemp -d)"
trap 'kill $(jobs -p) 2>/dev/null || true; rm -rf "$TMP"' EXIT
cd "$ROOT"
python3 -c "from pathlib import Path; from pipeline import site; site.build(Path('$TMP/leer'), mit_daten=False)"
python3 -c "from pathlib import Path; from pipeline import site; site.build(Path('$TMP/test'), mit_daten=False)"
cp tests/fixtures/vorgaenge.json "$TMP/test/data/export/vorgaenge.json"
# Kartenebene Bauleitplanung: eine erfundene Testfläche (keine Daten der Stadt; deren Umringe liegen nicht im Repository)
# Ortsbezirksflächen (Gemarkungen, HVBG, dl-de/zero-2.0; im Repository)
cp data/geo/dl-de-zero/ortsbezirke.geojson "$TMP/test/data/export/flaechen.json"
mkdir -p "$TMP/test/data/export/karte" && cp tests/fixtures/bauleitplanung_test.json "$TMP/test/data/export/karte/bauleitplanung.json"
# Umweltebene Schutzgebiete Natur: erfundene Testflächen
cp tests/fixtures/umwelt_natur_test.json "$TMP/test/data/export/karte/umwelt_natur.json"
# Wohnen und Boden: Kennzahlen aus dem Export (Bodenrichtwerte 2024, Zensus 2022; öffentliche Daten)
cp tests/fixtures/wohnen.json "$TMP/test/data/export/wohnen.json"
# Wahlen: amtliche Ergebnisse aus dem Export (ohne Personennamen)
cp tests/fixtures/wahlen.json "$TMP/test/data/export/wahlen.json"
# Beteiligung: erfundenes Testverfahren mit laufender Frist
cp tests/fixtures/beteiligung_test.json "$TMP/test/data/export/beteiligung.json"
# Eigentum: Unternehmen aus dem Beteiligungsbericht (ohne Personen)
cp tests/fixtures/eigentum.json "$TMP/test/data/export/eigentum.json"
# 3D-Ansicht: abgeleitete Grundrisse mit Höhe (HVBG, Geobasisdaten; im Repository)
cp -r data/geo/hvgg/gebaeude3d "$TMP/test/data/export/gebaeude3d"
# Zuzug und Wegzug: amtliche Zahlen (HSL) und Gemeindegrenzen (HVBG) aus dem Repository, wie im Export zusammengeführt
python3 -c "import json; d=json.load(open('data/wanderung/wanderung.json')); d['geo']=json.load(open('data/geo/dl-de-zero/wanderung_geo.json')); json.dump(d, open('$TMP/test/data/export/wanderung.json','w'), ensure_ascii=False)"
# freie Ports (ein belegter Port hätte sonst einen fremden Server getestet), dann warten, bis beide Server antworten
frei() { python3 -c "import socket; s=socket.socket(); s.bind(('127.0.0.1', 0)); print(s.getsockname()[1])"; }
P_LEER="$(frei)"; P_TEST="$(frei)"
while [ "$P_TEST" = "$P_LEER" ]; do P_TEST="$(frei)"; done
python3 -m http.server "$P_LEER" --bind 127.0.0.1 --directory "$TMP/leer" >"$TMP/server_leer.log" 2>&1 &
python3 -m http.server "$P_TEST" --bind 127.0.0.1 --directory "$TMP/test" >"$TMP/server_test.log" 2>&1 &
for p in "$P_LEER" "$P_TEST"; do
  for _ in $(seq 50); do curl -sf -o /dev/null "http://127.0.0.1:$p/stadt.json" && break; sleep 0.1; done
  curl -sf -o /dev/null "http://127.0.0.1:$p/stadt.json" || { echo "Testserver auf Port $p antwortet nicht"; cat "$TMP"/server_*.log; exit 1; }
done
SITE_LEER="http://127.0.0.1:$P_LEER/" SITE="http://127.0.0.1:$P_TEST/" node --test tests/browser/smoke.test.mjs
