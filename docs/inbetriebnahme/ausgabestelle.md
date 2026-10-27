# Ablaufkarte Ausgabestelle (Einladungscodes)

**Wer:** eine Person der verantwortlichen Stelle, **nicht** in der Prüfgruppe. Nur sie weiß, wer welche Erfasser-ID hat.
**Wo:** eigener Rechner, im Wurzelverzeichnis des Repositorys; Register und Druckblatt liegen außerhalb jedes Git-Repositorys.

**Ohne Python (empfohlen):** die Einrichtungsseite `einrichten.html` (nicht verlinkt) im Browser öffnen, das Netz trennen, Schritt 2. Sie erzeugt die Codekarten zum Drucken, das Register (`.tsv`) und eine „öffentliche Datei“ mit den Hashes; diese Datei an die verantwortliche Stelle geben, die sie mit `python tools/einrichten.py uebernehmen DATEI` in `config/stadt.json` überträgt. Bei weiteren Codes das bisherige Register auf der Seite mit auswählen. Die Codes stehen nur auf den Karten.

1. Codes erzeugen (mit Python): `python tools/einrichten.py codes ANZAHL --register PFAD/einladungen.tsv --druck PFAD/druck`
2. Das Druckblatt drucken und die Karten ausschneiden. Jede Karte enthält Code, Gültigkeit (12 Monate), Erfasser-ID und die Adresse der Erfassungsseite. Danach das Druckblatt löschen.
3. Die Zuordnung Erfasser-ID ↔ Person nur in den eigenen Unterlagen notieren, nie im Repository.
4. `config/stadt.json` committen und veröffentlichen; erst dann gelten die Codes.
5. Die Karte **persönlich** übergeben, nicht per E-Mail oder Messenger.
6. Eine Kopie des Registers (ohne Namen) geht an die Prüfgruppe (`ARBEIT/einladungen.tsv`).

**Widerruf** (Verlust, Ausscheiden, Missbrauch): `python tools/einrichten.py widerrufen E-XXXXXXXX --register PFAD/einladungen.tsv`, dann `stadt.json` committen und die Register-Kopie der Prüfgruppe erneuern.
