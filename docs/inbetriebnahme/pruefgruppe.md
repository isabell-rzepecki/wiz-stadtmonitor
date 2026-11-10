# Ablaufkarte Prüfgruppe

**Wer:** eine oder mehrere Personen, die das Passwort der Prüfgruppe kennen. Eine Freigabe je Eintrag genügt (`freigaben_noetig: 1`).
**Wo:** Prüfseite im internen Bereich (`/intern/pruefen.html`). Jede Aufgabe führt Schritt für Schritt, mit „Weiter“ und „Zurück“. Die Seite rechnet nur im Browser und sendet nur beim Veröffentlichen, und dann nur die zusammengefassten Zahlen.

Auf der Seite heißt die Arbeitsdatei **Prüfmappe** (`pruefmappe.json`; ältere `arbeitsdatei.json` lassen sich ebenso öffnen). Sie enthält Schlüssel, Bestand, Liste der Einladungskarten und Zugriffsprotokoll, verschlüsselt mit dem Passwort.

## Einmal zu Beginn (Startseite: „Zum ersten Mal hier?“)

1. Passwort wählen (mindestens 10 Zeichen, gut: vier Wörter), „Prüfmappe anlegen“.
2. „Prüfmappe sichern“: auf einen USB-Stick und eine Kopie auf einen zweiten.
3. „Liste der Einladungskarten sichern“ und der Ausgabestelle schicken. Sie enthält nur den öffentlichen Schlüssel.

## Immer wenn neue Dateien da sind (Startseite: „Neue Angaben prüfen“)

1. Prüfmappe öffnen: Datei wählen, Passwort, „Öffnen“.
2. Neue Dateien einlesen: Exportdateien der Erfassenden (und eine neue Liste der Ausgabestelle) wählen, „Einlesen“. Die Seite weist ab, was nicht passt (fremder Schlüssel, Schema, Freitext, Karte unbekannt, gesperrt oder abgelaufen), vergibt Vermieter-Schlüssel und markiert Dubletten und abweichende Angaben.
3. Ansehen und freigeben: „Alles ohne Hinweis freigeben“; Angaben mit Hinweis ansehen und gegebenenfalls unter „Einzelne Angaben freigeben oder aussortieren“ mit Grund aussortieren.
4. Veröffentlichen, wenn gewünscht: „Vorschau ansehen“, dann „Jetzt veröffentlichen“. Die Zahlen erscheinen nach dem nächsten nächtlichen Lauf auf der Seite „Wohnen und Eigentum“; der Lauf prüft sie dort noch einmal mit derselben Sperre. „Etwas stimmt nicht mit der letzten Veröffentlichung?“ holt die vorige zurück.
5. „Prüfmappe sichern“ und auf beiden Sticks ersetzen. Nie per E-Mail, Messenger oder Cloud weitergeben.

## Seltener (Startseite: „Löschen und Auskunft“)

Nach dem Öffnen der Prüfmappe: Widerruf per Code, Widerspruch je Gebäude (mit Sperrliste, Art. 21 DSGVO), Auskunft zu einem Gebäude (Art. 15 DSGVO), alte Angaben nach der Speicherdauer löschen, Liste der Einladungskarten neu sichern, Unterlagen (Prüfliste, Einlesebericht, Zugriffsprotokoll). Danach die Prüfmappe sichern.

**Üben:** Startseite, „Hier geht es ohne echte Angaben“ spielt den Ablauf mit erfundenen Einträgen durch.

## Mit Python (technischer Weg)

- `python tools/pruefen.py arbeitsdatei-auspacken pruefmappe.json ZIEL` ergibt `ZIEL/schluessel.json` und `ZIEL/arbeit/` (Bestand, Register, Protokoll) für alle Befehle von `tools/pruefen.py`; `arbeitsdatei-einpacken -a ZIEL/arbeit -s ZIEL/schluessel.json pruefmappe.json` führt zurück.
- Generalprobe: `python tools/generalprobe.py`.
