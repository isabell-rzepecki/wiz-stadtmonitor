# Einladungscodes: Ausgabe, Gültigkeit, Widerruf

> Entwurf vom 26.10.2026 (Issue 30). Wer ausgibt, ist festgelegt (26.10.2026). Personen und Namen gehören nicht ins Repository.

## Wer gibt aus

Die **Ausgabestelle** ist eine Person der verantwortlichen Stelle, die **nicht zur Prüfgruppe** gehört. Sie erzeugt die Codes, führt das Register und übergibt die Codes. Nur sie weiß, wer hinter welcher Erfasser-ID steht. Die Prüfgruppe sieht nur pseudonyme Erfasser-IDs; so bleiben Zugang und Prüfung getrennt.

## Ausgabe

1. Die Ausgabestelle erzeugt die Codes auf ihrem Rechner, im Wurzelverzeichnis des Repositorys; Register und Druckblatt liegen außerhalb jedes Git-Repositorys:
   `python tools/einrichten.py codes ANZAHL --register PFAD/einladungen.tsv --druck PFAD/druck`
2. Das Werkzeug schreibt je Code eine Zeile ins **Register**: Erfasser-ID, Hash, Ausgabe, gültig bis, widerrufen. Name und Code stehen nicht darin. Wer welche Erfasser-ID hat, notiert die Ausgabestelle getrennt davon in ihren Unterlagen.
3. Es trägt die Einträge `{"hash": …, "bis": …}` unter `wohnen_eigentum.erfassung.einladungen` in `config/stadt.json` ein. Die Ausgabestelle committet die Datei; nach dem Veröffentlichen gelten die Codes.
4. Das **Druckblatt** enthält je Code eine Karte zum Ausschneiden. Den Code **persönlich auf Papier** übergeben, nicht per E-Mail oder Messenger. Danach das Druckblatt löschen. Nach der Eingabe in der App kann das Papier vernichtet werden; die App merkt sich nur Erfasser-ID und Hash.
5. Eine Kopie des Registers (ohne Namen) geht nach jeder Änderung an die Prüfgruppe (`ARBEIT/einladungen.tsv`); `pruefen.py einlesen` gleicht damit ab.

## Gültigkeit

- Ein Code gilt **12 Monate** ab Ausgabe (`einladung_gueltig_monate`).
- Danach sperrt die App beim nächsten Start mit Netz: „Dieser Zugang ist abgelaufen“.
- `tools/pruefen.py einlesen` weist Einträge ab, die nach Ablauf erfasst wurden.
- Wer weiter erfasst, erhält einen neuen Code und damit eine neue Erfasser-ID; bereits erfasste und eingelesene Einträge bleiben.

## Widerruf (etwa bei verlorenem Code, Ausscheiden, Missbrauch)

1. `python tools/einrichten.py widerrufen E-XXXXXXXX --register PFAD/einladungen.tsv` vermerkt das Datum im Register und entfernt den Hash aus `stadt.json`.
2. `stadt.json` committen und veröffentlichen; die App sperrt beim nächsten Start mit Netz. Die Register-Kopie der Prüfgruppe erneuern.
3. Auch wenn ein Gerät offline bleibt: `einlesen` weist alles ab, was nach dem Widerruftag erfasst wurde. Einträge bis zum Widerruftag nimmt es an.
4. Ist zu befürchten, dass Einträge vor dem Widerruf gefälscht wurden, prüft die Prüfgruppe die Einträge dieser Erfasser-ID einzeln. Gegebenenfalls verwirft sie sie (`pruefen.py verwerfen`).

## Grenze

Ohne Server ist der Code eine Schwelle gegen zufällige Nutzung, kein harter Zugangsschutz: Wer den öffentlichen Schlüssel kennt, kann Exportdateien auch selbst bauen. Deshalb gleicht das Prüfskript jede Erfasser-ID mit dem Register ab, und jeder Eintrag braucht zwei Freigaben.
