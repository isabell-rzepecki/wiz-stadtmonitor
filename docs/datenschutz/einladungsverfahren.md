# Einladungskarten: Ausgabe, Gültigkeit, Sperre

> Fassung vom 10.11.2026 (Issue 30; normale Schutzstufe nach Entscheidung der Projektverantwortlichen). Personen und Namen gehören nicht ins Repository.

## Wer gibt aus

Die **Ausgabestelle** ist eine Person der verantwortlichen Stelle, die **nicht zur Prüfgruppe** gehört. Nur sie weiß, wer hinter welcher Kartennummer (Erfasser-ID) steht. Die Prüfgruppe sieht nur pseudonyme Erfasser-IDs; so bleiben Zugang und Prüfung getrennt.

## Ausgabe

1. Die Ausgabestelle öffnet auf der Seite „Einladungskarten“ (`/intern/karten.html`) die Kartenliste der Prüfgruppe und druckt Karten.
2. Jede Karte trägt einen QR-Code mit der Adresse der Erfassung. Der Teil nach `#` enthält Code, Ablaufdatum und den öffentlichen Schlüssel der Prüfgruppe; er geht beim Öffnen nicht an den Server. Die App speichert ihn im Gerät und entfernt ihn aus der Adresse.
3. Die **Kartenliste** erhält je Karte: Erfasser-ID, Hash des Codes, Ausgabe, gültig bis, gesperrt. Codes und Namen stehen nicht darin; sie darf per E-Mail an die Prüfgruppe.
4. Wer welche Karte hat, steht nur auf der ausgedruckten Liste der Ausgabestelle. Karten werden persönlich übergeben.

## Gültigkeit und Sperre

- Eine Karte gilt **12 Monate** ab Ausgabe (`einladung_gueltig_monate`). Nach Ablauf meldet die App sich ab.
- Gesperrt wird auf der Kartenseite; die Prüfgruppe übernimmt die neue Kartenliste beim nächsten Einlesen.
- Beim Einlesen weist die Prüfseite ab, was mit einer unbekannten Karte, vor der Ausgabe, nach Ablauf oder nach der Sperre erfasst wurde.

## Grenze

Ohne Server ist die Karte eine Schwelle gegen zufällige Nutzung, kein harter Zugangsschutz. Neue Karten gelten sofort, ohne Eintrag in der Konfiguration; geprüft wird deshalb erst beim Einlesen gegen die Kartenliste. Ein gefälschter QR-Code mit fremdem Schlüssel könnte Erfassende dazu bringen, für Dritte zu verschlüsseln; das Risiko ist gering, weil Exportdateien nur an die bekannte Prüfgruppe gehen. Ältere, abgetippte Codes (`tools/einrichten.py`) prüft die App weiter gegen `wohnen_eigentum.erfassung.einladungen`.
