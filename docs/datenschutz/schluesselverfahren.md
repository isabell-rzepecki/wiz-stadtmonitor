# Prüfgruppe und Schlüsselverfahren

> Entwurf vom 26.10.2026, keine Rechtsberatung (Issue 29). Rollen und Rhythmus sind festgelegt (26.10.2026). Namen gehören nicht ins Repository, sondern in die Unterlagen der verantwortlichen Stelle.

## Rollen

- **Prüfgruppe:** mindestens zwei Personen mit pseudonymen Prüfer-IDs (`P-1`, `P-2` …). Jeder Eintrag braucht die Freigabe von zwei verschiedenen IDs (Vier-Augen-Prinzip). [Leerstelle: Zuordnung der IDs, geführt bei der verantwortlichen Stelle]
- **Schlüsselinhaber:innen:** zwei Personen der Prüfgruppe, die auch Einträge prüfen. Nur sie kennen die Passphrase und verwahren die Schlüsseldatei; so bleibt der Kreis mit Zugriff klein.
- **Zugriffsprotokoll** (`namenzugriff.tsv`): Das Prüfskript schreibt es bei jeder Entschlüsselung eines Namens automatisch ins Arbeitsverzeichnis. Vierteljährlich sieht es eine Person durch, die **keinen Schlüssel** hat (aus der Prüfgruppe oder der verantwortlichen Stelle). So prüft niemand die eigenen Zugriffe. Ergebnis mit Datum festhalten.

## Schlüssel erzeugen und verwahren

1. `python tools/pruefen.py schluessel PFAD/pg.json` auf einem Rechner der Prüfgruppe, außerhalb jedes Git-Repositorys.
   - Das Skript fragt eine Passphrase ab (mindestens 12 Zeichen).
   - Der private Schlüssel liegt nur mit ihr verschlüsselt in der Datei (Argon2id, XSalsa20-Poly1305); die Datei erhält Rechte 0600.
2. Den ausgegebenen öffentlichen Teil (`key_id`, `alg`, `public_key`) unter `wohnen_eigentum.erfassung.schluessel` in `config/stadt.json` eintragen und veröffentlichen. Die App kennt nur diesen Teil.
3. Sicherung **auf Papier im Tresor** der verantwortlichen Stelle (siehe unten). Die Passphrase wird getrennt verwahrt (versiegelter Umschlag, nicht im selben Tresorfach). Nie per E-Mail, Messenger oder Cloud-Speicher.

## Sicherung auf Papier

1. `python tools/pruefen.py schluessel-ausdruck PFAD/pg.json PFAD/sicherung.html` erzeugt eine Druckseite außerhalb jedes Git-Repositorys:
   - QR-Codes (je fünf Zeilen) und dieselben Zeilen als Text zum Abtippen, jede Zeile mit vier Prüfziffern;
   - die Schlüsseldatei bleibt dabei mit der Passphrase verschlüsselt; der Ausdruck allein öffnet nichts.
2. An einem lokalen Drucker drucken, nicht an einem Netzwerkdrucker mit Speicher. Danach die HTML-Datei löschen.
3. Wiederherstellung einmal probehalber prüfen: QR-Codes scannen oder Zeilen abtippen, als Textdatei speichern, `python tools/pruefen.py schluessel-zurueck TEXTDATEI PFAD/test.json`, dann mit der Passphrase öffnen (etwa `fristen`). Test- und Textdatei löschen.
4. Ausdruck in einen Umschlag, Datum und aktuelle Schlüsselkennung außen vermerken, in den Tresor. Den alten Ausdruck vernichten (Aktenvernichter).

## Schlüsselwechsel (jährlich; außerdem beim Wechsel einer Schlüsselinhaber:in und bei Verdacht)

Der Rhythmus steht in `config/stadt.json` (`schluessel_wechsel_monate: 12`). `pruefen.py fristen` meldet, wenn der Wechsel fällig ist; das Datum steht in der Schlüsselkennung (`pg-JJJJMMTT-…`).

1. `python tools/pruefen.py schluessel-wechsel -a ARBEIT -s PFAD/pg.json -p P-1 [--neue-passphrase]`.
   - Es entsteht ein neues Paar.
   - Namen von Privatpersonen und der Bestand werden mit dem neuen Schlüssel neu versiegelt.
   - Der alte Schlüssel bleibt in der Datei, damit ältere Exporte lesbar bleiben.
2. Den neuen öffentlichen Teil in `stadt.json` eintragen und veröffentlichen. Geräte holen ihn beim nächsten Start mit Netz; Einträge, die vorher gespeichert wurden, bleiben mit dem alten Schlüssel lesbar.
3. Die Papiersicherung erneuern (neuer Ausdruck, alter wird vernichtet).

## Verlust

- **Verlust der Datei, Papiersicherung vorhanden:** mit `schluessel-zurueck` wiederherstellen, danach Schlüsselwechsel mit neuer Passphrase.
- **Verlust von Datei und Sicherung oder der Passphrase:**
  - Der Bestand und alle noch nicht eingelesenen Exporte sind nicht mehr lesbar.
  - Auch Einträge, die noch in Geräten liegen, sind mit dem alten Schlüssel versiegelt und damit verloren; sie müssen neu erfasst werden.
  - Neues Paar erzeugen und veröffentlichen.
  - Nach Art. 33 DSGVO prüfen, ob eine Meldung nötig ist (Verlust der Verfügbarkeit).

## Kompromittierung (Datei und Passphrase könnten in fremde Hände gelangt sein)

Kommt nur der Ausdruck oder nur die Datei abhanden, schützt die Passphrase sie weiter. Trotzdem sofort einen Schlüsselwechsel mit neuer Passphrase machen und einen neuen Ausdruck anlegen.

1. Sofort `schluessel-wechsel … --kompromittiert --neue-passphrase`.
   - Der alte Schlüssel wird gesperrt; `einlesen` weist Exporte mit ihm ab.
   - Der Bestand liegt danach unter dem neuen Schlüssel.
2. Den neuen öffentlichen Teil sofort veröffentlichen. Alles, was mit dem alten Schlüssel versiegelt ist, gilt als offengelegt. Das betrifft auch noch nicht exportierte Einträge in Geräten: Erfassende löschen sie dort, und sie werden mit dem neuen Schlüssel neu erfasst.
3. Innerhalb von 72 Stunden prüfen, ob eine Meldung an die Aufsichtsbehörde (Art. 33 DSGVO) und eine Benachrichtigung der Betroffenen (Art. 34) nötig ist. Bei Namen und Mietangaben ist davon auszugehen.
4. Den Vorgang mit Datum, Ursache und Maßnahmen dokumentieren (Art. 33 Abs. 5).
