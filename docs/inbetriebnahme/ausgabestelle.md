# Ablaufkarte Ausgabestelle (Einladungscodes)

**Wer:** eine Person der verantwortlichen Stelle, **nicht** in der Prüfgruppe. Nur sie weiß, wer welche Erfasser-ID hat.
**Wo:** eigener Rechner, im Wurzelverzeichnis des Repositorys; Register und Druckblatt liegen außerhalb jedes Git-Repositorys.

1. Codes erzeugen: `python tools/einrichten.py codes ANZAHL --register PFAD/einladungen.tsv --druck PFAD/druck`
2. Das Druckblatt drucken und die Karten ausschneiden. Jede Karte enthält Code, Gültigkeit (12 Monate), Erfasser-ID und die Adresse der Erfassungsseite. Danach das Druckblatt löschen.
3. Die Zuordnung Erfasser-ID ↔ Person nur in den eigenen Unterlagen notieren, nie im Repository.
4. `config/stadt.json` committen und veröffentlichen; erst dann gelten die Codes.
5. Die Karte **persönlich** übergeben, nicht per E-Mail oder Messenger.
6. Eine Kopie des Registers (ohne Namen) geht an die Prüfgruppe (`ARBEIT/einladungen.tsv`).

**Widerruf** (Verlust, Ausscheiden, Missbrauch): `python tools/einrichten.py widerrufen E-XXXXXXXX --register PFAD/einladungen.tsv`, dann `stadt.json` committen und die Register-Kopie der Prüfgruppe erneuern.
