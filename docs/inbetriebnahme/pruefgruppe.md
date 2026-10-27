# Ablaufkarte Prüfgruppe

**Wer:** zwei Schlüsselinhaber:innen; zum Freigeben mindestens zwei Personen mit Prüfer-IDs (`P-1`, `P-2`).
**Wo:** eigener Rechner, im Wurzelverzeichnis des Repositorys. Schlüssel, Arbeitsordner und Druckblätter liegen **außerhalb** jedes Git-Repositorys.

## Einmalig

**Ohne Python (empfohlen für Schlüssel und Sicherung):** die Einrichtungsseite `einrichten.html` (nicht verlinkt) im Browser öffnen, das Netz trennen, Schritt 1 gemeinsam ausführen. Die Seite erzeugt die Schlüsseldatei (mit der Passphrase durch Argon2id geschützt, dasselbe Format wie unten), die Papiersicherung zum Drucken und eine „öffentliche Datei“ mit dem öffentlichen Schlüssel. Danach Schritt 3: die Sicherung einmal probeweise einlesen und die Passphrase prüfen. Die öffentliche Datei überträgt `python tools/einrichten.py uebernehmen DATEI` in `config/stadt.json`. Die Schlüsseldatei funktioniert unverändert mit `tools/pruefen.py`.

Mit Python:

1. Pakete: `python -m pip install -r requirements.txt -r tools/requirements.txt`
2. Generalprobe: `python tools/generalprobe.py`. Weiter erst, wenn sie „bestanden“ meldet.
3. Schlüssel: `python tools/einrichten.py schluessel PFAD/pg.json --druck PFAD/druck`
   - Die Passphrase hat mindestens 12 Zeichen und wird nie notiert, außer im versiegelten Umschlag.
4. Papiersicherung: das Druckblatt an einem lokalen Drucker drucken; die Wiederherstellung einmal prüfen (`pruefen.py schluessel-zurueck`). Danach das Druckblatt löschen; den Ausdruck in den Tresor, den Umschlag mit der Passphrase getrennt davon.
5. `config/stadt.json` committen (enthält nur den öffentlichen Teil).

## Laufend

**Ohne Python:** die Prüfseite `pruefen.html` (nicht verlinkt, rechnet nur im Browser, sendet nichts). Öffnen mit Schlüsseldatei, Passphrase, Prüfer-ID, Bestandsdatei (`bestand.sealed`) und Register; dann Exportdateien einlesen, „Prüfen“, freigeben. Die zweite Freigabe gibt die zweite Person mit eigener Prüfer-ID, nacheinander am selben Gerät oder mit der gespeicherten Bestandsdatei an ihrem Gerät. Am Ende den Bestand und, falls Namen geöffnet wurden, das Zugriffsprotokoll speichern. Die Dateien sind dieselben wie bei Python; man kann zwischen beiden wechseln. Veröffentlichen, Widerruf, Widerspruch und Fristen folgen auf der Seite in den nächsten Schritten; bis dahin mit Python.

Mit Python:

- **Eingang:** `python tools/pruefen.py einlesen -a ARBEIT -s PFAD/pg.json -p P-1 DATEI…`, danach die Exportdatei löschen.
- **Prüfen und Freigeben:** `python tools/pruefen.py pruefen -a ARBEIT -s PFAD/pg.json -p P-1`, dann `python tools/pruefen.py freigeben -a ARBEIT -s PFAD/pg.json -p P-1 --alle` durch P-1 **und** P-2.
- **Veröffentlichen:** `python tools/veroeffentlichen.py -a ARBEIT -s PFAD/pg.json -p P-1`; nur die Dateien unter `data/wohnen/` committen.
- **Widerruf und Widerspruch:** `loeschen --code XXXX-XXXX`, `widerspruch GEBÄUDE…` (siehe `docs/datenschutz/loeschverfahren.md`).
- **Vierteljährlich:** Eine Person **ohne** Schlüssel sieht `namenzugriff.tsv` durch.
- **Jährlich:** `fristen` meldet den Schlüsselwechsel; dann `schluessel-wechsel` und eine neue Papiersicherung.
