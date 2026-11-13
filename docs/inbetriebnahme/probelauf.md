# Probelauf: einmal die ganze Kette, ohne echte Angaben

**Ziel:** Prüfgruppe, Ausgabestelle und eine erfassende Person gehen den Ablauf einmal gemeinsam durch, bevor echte Angaben erfasst werden. Am Ende wissen alle, wo sie klicken, und nichts davon bleibt bestehen.

**Wer:** mindestens zwei Personen (Prüfgruppe und Ausgabestelle getrennt, wie später auch), dazu ein Handy zum Erfassen. **Dauer:** etwa eine Stunde.

**Wichtig:** Für den Probelauf eine eigene **Übungs-Prüfmappe** mit eigenem Übungs-Passwort anlegen und am Ende löschen. Im Probelauf nie „Jetzt veröffentlichen“ drücken; Schluss ist bei der Vorschau. Nur erfundene Angaben eintragen, keine Namen, keine echten Mieten.

## Ablauf

| Schritt | Wer | Wo | Was |
|---|---|---|---|
| 1 | Prüfgruppe | `/intern/` → „Zum ersten Mal hier?“ | Übungs-Prüfmappe anlegen, sichern als `uebung-pruefmappe.json`, „Liste der Einladungskarten sichern“ |
| 2 | Ausgabestelle | `/intern/` → „Einladungskarten drucken“ | Kartenliste öffnen, **eine** Karte drucken, Liste sichern und der Prüfgruppe schicken |
| 3 | Erfassende Person | Handy, QR-Code der Karte | Ein Gebäude antippen, Formular „Eigentum und Vermietung“: ein Mehrfamilienhaus mit erfundener Wohnungszahl und Wohnungen je Eigentümer-Art; dann eine erfundene Mietangabe mit Einwilligung (Widerrufscode notieren) |
| 4 | Erfassende Person | App → „Einträge“ → „Exportieren“ | Exportdatei an die Prüfgruppe schicken |
| 5 | Prüfgruppe | `/intern/` → „Neue Angaben prüfen“ | Übungs-Prüfmappe öffnen, Exportdatei und Kartenliste einlesen, Hinweise ansehen, freigeben |
| 6 | Prüfgruppe | Schritt „Veröffentlichen“ | **Nur** „Vorschau ansehen“: Stimmen die Tabellen? Steht „zu wenige Angaben“ dort, wo es zu wenige sind? |
| 7 | Prüfgruppe | „Löschen und Auskunft“ | Widerruf mit dem notierten Code ausprobieren; Auskunft zu dem Gebäude ansehen |
| 8 | alle | – | Kurz festhalten, was unklar war (ohne Namen), und an die Kontaktadresse schicken |

## Aufräumen

- Ausgabestelle: die Übungskarte unter „Eine Karte ist verloren gegangen?“ sperren und vernichten; das handschriftliche Blatt vernichten.
- Prüfgruppe: `uebung-pruefmappe.json` und die Übungs-Kartenliste löschen, auch aus Downloads und Papierkorb.
- Erfassende Person: in der App „Exportierte löschen“.
- Danach die echte Prüfmappe mit einem neuen Passwort anlegen (Schritt 1 noch einmal, ohne „Übung“).

## Ohne Treffen üben

- Prüfseite: `/intern/` → „Lieber erst einmal üben?“ spielt den Ablauf mit erfundenen Einträgen durch.
- Erfassung: in der App „Ohne Karte ausprobieren“; dabei wird nichts gespeichert.
- Technisch: `python tools/generalprobe.py` prüft die ganze Kette lokal mit Wegwerf-Schlüssel.
