# Einladungscodes: Ausgabe, Gültigkeit, Widerruf

> Entwurf vom 26.10.2026 (Issue 30). Personen und Namen gehören nicht ins Repository.

## Ausgabe

1. Eine Person der Prüfgruppe erzeugt die Codes auf ihrem Rechner, außerhalb jedes Git-Repositorys:
   `python tools/einladung.py neu [ANZAHL] --register ARBEIT/einladungen.tsv`
2. Das Werkzeug schreibt je Code eine Zeile ins **Register**: Erfasser-ID, Hash, Ausgabe, gültig bis, widerrufen. Name und Code stehen nicht darin. Wer welche Erfasser-ID hat, notiert die Prüfgruppe getrennt davon, bei der verantwortlichen Stelle.
3. Die ausgegebenen Einträge `{"hash": …, "bis": …}` kommen unter `wohnen_eigentum.erfassung.einladungen` in `config/stadt.json` und werden veröffentlicht.
4. Den **Code persönlich auf Papier** übergeben, nicht per E-Mail oder Messenger. Er wird nirgends gespeichert. Nach der Eingabe in der App kann das Papier vernichtet werden; die App merkt sich nur Erfasser-ID und Hash.

## Gültigkeit

- Ein Code gilt **12 Monate** ab Ausgabe (`einladung_gueltig_monate`).
- Danach sperrt die App beim nächsten Start mit Netz: „Dieser Zugang ist abgelaufen“.
- `tools/pruefen.py einlesen` weist Einträge ab, die nach Ablauf erfasst wurden.
- Wer weiter erfasst, erhält einen neuen Code und damit eine neue Erfasser-ID; bereits erfasste und eingelesene Einträge bleiben.

## Widerruf (etwa bei verlorenem Code, Ausscheiden, Missbrauch)

1. `python tools/einladung.py widerrufen E-XXXXXXXX --register ARBEIT/einladungen.tsv` vermerkt das Datum im Register.
2. Den Eintrag mit dem ausgegebenen Hash aus `stadt.json` entfernen und veröffentlichen. Die App sperrt beim nächsten Start mit Netz.
3. Auch wenn ein Gerät offline bleibt: `einlesen` weist alles ab, was nach dem Widerruftag erfasst wurde. Einträge bis zum Widerruftag nimmt es an.
4. Ist zu befürchten, dass Einträge vor dem Widerruf gefälscht wurden, prüft die Prüfgruppe die Einträge dieser Erfasser-ID einzeln. Gegebenenfalls verwirft sie sie (`pruefen.py verwerfen`).

## Grenze

Ohne Server ist der Code eine Schwelle gegen zufällige Nutzung, kein harter Zugangsschutz: Wer den öffentlichen Schlüssel kennt, kann Exportdateien auch selbst bauen. Deshalb gleicht das Prüfskript jede Erfasser-ID mit dem Register ab, und jeder Eintrag braucht zwei Freigaben.
