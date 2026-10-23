#!/usr/bin/env bash
# Browser-Prüfung: Seite zweimal zusammenstellen (ohne Daten und mit den Testdaten aus tests/fixtures),
# je einen lokalen Server starten und die Tests ausführen. Aufruf aus dem Wurzelverzeichnis:
#   bash tests/browser/run.sh      (einmalig vorher: npm install --prefix tests/browser)
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
python3 -m http.server 8765 --bind 127.0.0.1 --directory "$TMP/leer" >/dev/null 2>&1 &
python3 -m http.server 8766 --bind 127.0.0.1 --directory "$TMP/test" >/dev/null 2>&1 &
sleep 1
SITE_LEER=http://127.0.0.1:8765/ SITE=http://127.0.0.1:8766/ node --test tests/browser/smoke.test.mjs
