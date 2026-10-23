#!/usr/bin/env bash
# Browser-Prüfung: Seite zweimal zusammenstellen (ohne Daten und mit den Testdaten aus tests/fixtures),
# je einen lokalen Server starten und die Tests ausführen. Aufruf aus dem Wurzelverzeichnis:
#   bash tests/browser/run.sh      (einmalig vorher: npm install --prefix tests/browser)
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
TMP="$(mktemp -d)"
trap 'kill $(jobs -p) 2>/dev/null || true; rm -rf "$TMP"' EXIT
cd "$ROOT"
python3 -c "from pathlib import Path; from pipeline import site; site.build(Path('$TMP/leer'))"
python3 -c "from pathlib import Path; from pipeline import site; site.build(Path('$TMP/test'))"
cp tests/fixtures/vorgaenge.json "$TMP/test/data/export/vorgaenge.json"
python3 -m http.server 8765 --bind 127.0.0.1 --directory "$TMP/leer" >/dev/null 2>&1 &
python3 -m http.server 8766 --bind 127.0.0.1 --directory "$TMP/test" >/dev/null 2>&1 &
sleep 1
SITE_LEER=http://127.0.0.1:8765/ SITE=http://127.0.0.1:8766/ node --test tests/browser/smoke.test.mjs
