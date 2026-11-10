# Prüfgruppe und Schlüsselverfahren

> Fassung vom 10.11.2026, keine Rechtsberatung (Issue 29). Normale Schutzstufe nach Entscheidung der Projektverantwortlichen vom 10.11.2026; die frühere Fassung (Vier Augen, Papiersicherung, jährlicher Wechsel) steht in der Versionsgeschichte. Namen gehören nicht ins Repository.

## Rollen

- **Prüfgruppe:** eine oder mehrere Personen, die das Passwort der Prüfgruppe kennen. Je Eintrag genügt eine Freigabe (`freigaben_noetig: 1`; mit 2 gilt wieder das Vier-Augen-Prinzip).
- **Ausgabestelle:** gehört nicht zur Prüfgruppe (`einladungsverfahren.md`).

## Arbeitsdatei

- Die Prüfseite (`/intern/pruefen.html`) erzeugt beim Einrichten ein Schlüsselpaar (X25519, libsodium sealed box). Schlüssel, Bestand, Kartenliste und Zugriffsprotokoll liegen zusammen in der **Arbeitsdatei**, verschlüsselt mit dem Passwort (Argon2id „moderat“, XSalsa20-Poly1305). Ohne Passwort ist sie nicht lesbar.
- Das Passwort hat mindestens 10 Zeichen. Es wird nicht gespeichert und nicht übertragen.
- Die Arbeitsdatei liegt auf einem USB-Stick, eine Kopie auf einem zweiten (Sicherung). Nie per E-Mail, Messenger oder Cloud; nie in einem Git-Repository.
- Der öffentliche Schlüssel steht in der Kartenliste und in den QR-Codes der Karten; die Konfiguration braucht ihn nicht mehr.
- Das **Zugriffsprotokoll** vermerkt jede Entschlüsselung eines Namens einer Privatperson (Zeit, Datensatz, Zweck). Es liegt in der Arbeitsdatei und lässt sich als Tabelle speichern.

## Verlust

- **Ein Stick verloren:** Die Datei ist ohne Passwort nicht lesbar. Mit der Kopie weiterarbeiten und das Passwort wechseln. Das geht derzeit nur mit Python: auspacken, mit neuem Passwort einpacken (`pruefen.py arbeitsdatei-auspacken`, `arbeitsdatei-einpacken`).
- **Beide Sticks oder das Passwort verloren:** Bestand und noch nicht eingelesene Exporte sind nicht mehr lesbar. Neu einrichten, neue Kartenliste an die Ausgabestelle, neue Karten ausgeben. Nach Art. 33 DSGVO prüfen, ob eine Meldung nötig ist (Verlust der Verfügbarkeit).

## Kompromittierung (Datei und Passwort könnten in fremde Hände gelangt sein)

1. Neu einrichten; die alten Karten in der Kartenliste sperren und neue ausgeben. Alles, was mit dem alten Schlüssel verschlüsselt ist, gilt als offengelegt.
2. Innerhalb von 72 Stunden prüfen, ob eine Meldung an die Aufsichtsbehörde (Art. 33 DSGVO) und eine Benachrichtigung der Betroffenen (Art. 34) nötig ist. Bei Namen und Mietangaben ist davon auszugehen.
3. Den Vorgang mit Datum, Ursache und Maßnahmen dokumentieren (Art. 33 Abs. 5).

## Python

`tools/pruefen.py` arbeitet mit getrennten Dateien (Schlüsseldatei mit Passphrase, `bestand.sealed`, Register, Protokoll) und kennt weiter Papiersicherung und Schlüsselwechsel. `arbeitsdatei-auspacken` und `arbeitsdatei-einpacken` verbinden beide Wege.
