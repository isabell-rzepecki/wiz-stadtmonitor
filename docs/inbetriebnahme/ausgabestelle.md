# Ablaufkarte Ausgabestelle (Einladungskarten)

**Wer:** eine Person der verantwortlichen Stelle, **nicht** in der Prüfgruppe. Nur sie weiß, wer welche Karte hat.
**Wo:** Seite „Einladungskarten“ im internen Bereich (`/intern/karten.html`). Sie rechnet nur im Browser und sendet nichts.

1. Kartenliste öffnen (`kartenliste.json`). Beim ersten Mal kommt sie von der Prüfgruppe, danach die zuletzt gespeicherte.
2. Anzahl eingeben, „Karten erstellen und drucken“. Jede Karte trägt einen QR-Code, die Gültigkeit (12 Monate) und eine Kartennummer (Erfasser-ID). Mit den Karten druckt die Seite eine Liste, auf der von Hand eingetragen wird, wer welche Karte erhält. Diese Liste bleibt bei der Ausgabestelle.
3. Karten persönlich übergeben.
4. Kartenliste speichern, die alte ersetzen und der Prüfgruppe eine Kopie schicken (E-Mail genügt; die Datei enthält keine Codes und keine Namen).

**Sperren** (Verlust, Ausscheiden, Missbrauch): Kartenliste öffnen, in Schritt 3 „Sperren“, speichern, Kopie an die Prüfgruppe. Was danach mit der Karte erfasst wird, nimmt die Prüfgruppe nicht an.

Mit Python (technischer Weg): `tools/einrichten.py codes` und `widerrufen` arbeiten weiter mit dem Register `einladungen.tsv`; solche Codes werden abgetippt und müssen in `config/stadt.json` stehen.
