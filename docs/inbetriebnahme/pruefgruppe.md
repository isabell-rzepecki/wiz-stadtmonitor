# Ablaufkarte Prüfgruppe

**Wer:** eine oder mehrere Personen, die das Passwort der Prüfgruppe kennen. Eine Freigabe je Eintrag genügt (`freigaben_noetig: 1`).
**Wo:** Prüfseite im internen Bereich (`/intern/pruefen.html`). Sie rechnet nur im Browser und sendet nichts.

## Einmal zu Beginn

1. Prüfseite öffnen, „Erstmals einrichten“ aufklappen, ein Passwort wählen (mindestens 10 Zeichen, gut: vier Wörter).
2. **Arbeitsdatei** speichern (`arbeitsdatei.json`): auf einen USB-Stick und als Sicherung auf einen zweiten. Sie enthält Schlüssel, Bestand, Kartenliste und Zugriffsprotokoll, verschlüsselt mit dem Passwort.
3. **Kartenliste** speichern und der Ausgabestelle schicken. Sie enthält nur den öffentlichen Schlüssel.

## Immer wenn neue Dateien da sind

1. Arbeitsdatei wählen, Passwort eingeben, „Öffnen“.
2. Exportdateien der Erfassenden (und eine neue Kartenliste der Ausgabestelle) auswählen, „Einlesen und prüfen“. Die Seite weist ab, was nicht passt (fremder Schlüssel, Schema, Freitext, Karte unbekannt, gesperrt oder abgelaufen), vergibt Vermieter-Schlüssel und markiert Dubletten und abweichende Angaben.
3. „Alle Einträge ohne Hinweis freigeben“; Einträge mit Hinweis ansehen und gegebenenfalls mit Grund verwerfen.
4. Bei Bedarf „Vorschau erzeugen“ und die Veröffentlichungsdatei an die verantwortliche Stelle geben. Sie wird mit `python tools/veroeffentlichen.py uebernehmen DATEI` erneut geprüft und nach `data/wohnen/` übernommen.
5. Arbeitsdatei speichern und auf beiden Sticks ersetzen. Nie per E-Mail, Messenger oder Cloud weitergeben.

Unter „Löschen auf Anfrage und Speicherfristen“: Widerruf per Widerrufscode, Widerspruch je Gebäude (mit Sperrliste), Auskunft zu einem Gebäude, Löschen nach der Speicherdauer. „Ohne echte Daten ausprobieren“ spielt den Ablauf mit erfundenen Einträgen durch.

## Mit Python (technischer Weg)

- `python tools/pruefen.py arbeitsdatei-auspacken arbeitsdatei.json ZIEL` ergibt `ZIEL/schluessel.json` und `ZIEL/arbeit/` (Bestand, Register, Protokoll) für alle Befehle von `tools/pruefen.py`; `arbeitsdatei-einpacken -a ZIEL/arbeit -s ZIEL/schluessel.json arbeitsdatei.json` führt zurück.
- Generalprobe: `python tools/generalprobe.py`.
