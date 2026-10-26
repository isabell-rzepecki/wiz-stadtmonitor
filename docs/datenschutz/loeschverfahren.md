# Lösch- und Widerspruchsverfahren

> Stand 26.10.2026, bestätigt durch die verantwortliche Stelle (Issue 28). Keine Rechtsberatung. Kontakt: post@wiz-o-mat.de (Funktionsadresse, benannt am 26.10.2026). Eintrag in `config/stadt.json` (`wohnen_eigentum.erfassung.datenschutz.kontakt_widerspruch`); Datenschutzseite und App übernehmen ihn beim nächsten Veröffentlichen.

## Speicherdauer

- **Rohdaten bei der Prüfgruppe** (versiegelter Bestand): 24 Monate nach Eingang (`wohnen_eigentum.erfassung.speicherdauer_monate`).
  - Fällige Einträge zeigt `python tools/pruefen.py fristen -a ARBEIT -s SCHLUESSEL -p P-1`; mit `--loeschen` werden sie gelöscht.
  - Die Prüfgruppe prüft das mindestens vierteljährlich.
- **Exportdateien (.bin):** Nach dem Einlesen löscht die Prüfgruppe sie sofort; der Inhalt liegt dann nur noch im versiegelten Bestand.
- **Im Gerät der erfassenden Person:** Exportierte Einträge löschen, sobald die Prüfgruppe den Eingang bestätigt hat („Exportierte löschen“).
- **Miete und Wohnfläche in m²:** beim Einlesen zu €/m² verrechnet und verworfen; im Bestand bleibt nur der Preis je m².
- **Zugriffsprotokoll** (`namenzugriff.tsv`): 24 Monate wie die Rohdaten (festgelegt am 26.10.2026); `fristen --loeschen` entfernt ältere Zeilen.

## Widerruf einer Mietangabe (Art. 7 Abs. 3 DSGVO)

1. Die mietende Person nennt ihren **Widerrufscode**. Die App zeigt ihn nach dem Speichern an (`XXXX-XXXX`).
2. Die Prüfgruppe löscht mit `python tools/pruefen.py loeschen -a ARBEIT -s SCHLUESSEL -p P-1 --code XXXX-XXXX --grund "Widerruf"`. Im Verlauf bleiben nur Kennung, Zeitpunkt und Grund.
3. Ist die Angabe noch nicht eingegangen: Hinweis an das Team, die Exportdatei beim Eingang zu prüfen. Eine bereits eingelesene Kennung wird gelöscht.
4. Mit `python tools/veroeffentlichen.py` werden die öffentlichen Werte neu berechnet und veröffentlicht.
5. Bestätigung an die mietende Person innerhalb eines Monats (Art. 12 Abs. 3 DSGVO).

Ohne Code: Suche über Gebäude, Vertragsbeginn und Preis je m² (Miete geteilt durch Wohnfläche). Ist das nicht eindeutig, werden alle in Frage kommenden Angaben gelöscht.

## Widerspruch von Vermieter:innen (Art. 21 DSGVO)

1. Die Person nennt das Gebäude oder die Gebäude, die sie betreffen.
2. Die Prüfgruppe löscht mit `python tools/pruefen.py widerspruch -a ARBEIT -s SCHLUESSEL -p P-1 GEBAEUDE… --grund "Widerspruch"`. Gelöscht werden die Einträge zu diesen Gebäuden und, über den Vermieter-Schlüssel, zu allen Gebäuden derselben Person.
3. Alle betroffenen Gebäudekennungen kommen auf eine Sperrliste im versiegelten Bestand. Neue Erfassungen zu diesen Gebäuden weist `einlesen` ab.
4. Danach werden die öffentlichen Werte neu berechnet.
5. Bestätigung innerhalb eines Monats.

## Auskunft (Art. 15 DSGVO)

Auskunft gibt die Prüfgruppe aus dem versiegelten Bestand. Name und Daten werden dazu entschlüsselt; der Zugriff wird mit dem Zweck „Auskunft“ protokolliert.
