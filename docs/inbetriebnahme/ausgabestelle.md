# Ablaufkarte Ausgabestelle (Einladungskarten)

**Wer:** eine Person der verantwortlichen Stelle, **nicht** in der Prüfgruppe. Nur sie weiß, wer welche Karte hat.
**Wo:** Seite „Einladungskarten drucken“ im internen Bereich (`/intern/karten.html`), Schritt für Schritt. Sie rechnet nur im Browser und sendet nichts.

1. Liste der Karten öffnen (`kartenliste.json`). Beim ersten Mal kommt sie von der Prüfgruppe, danach die zuletzt gesicherte.
2. Karten drucken: Anzahl eingeben, „Karten drucken“. Jede Karte trägt einen QR-Code, die Gültigkeit (12 Monate) und eine Kartennummer (Erfasser-ID). Mit den Karten druckt die Seite ein Blatt, auf dem von Hand eingetragen wird, wer welche Karte erhält. Dieses Blatt bleibt bei der Ausgabestelle. Karten persönlich übergeben.
3. „Liste sichern“, die alte ersetzen und der Prüfgruppe eine Kopie schicken (E-Mail genügt; die Datei enthält keine Codes und keine Namen).

**Sperren** (Verlust, Ausscheiden, Missbrauch): im Schritt „Karten drucken“ unter „Eine Karte ist verloren gegangen?“ die Karte sperren, dann die Liste sichern und der Prüfgruppe schicken. Was danach mit der Karte erfasst wird, nimmt die Prüfgruppe nicht an.

Mit Python (technischer Weg): `tools/einrichten.py codes` und `widerrufen` arbeiten weiter mit dem Register `einladungen.tsv`; solche Codes werden abgetippt und müssen in `config/stadt.json` stehen.
