# Prüfgruppe und Schlüsselverfahren

> Entwurf vom 26.10.2026, keine Rechtsberatung (Issue 29). Personen stehen als Leerstellen; ihre Namen gehören nicht ins Repository, sondern in die Unterlagen der verantwortlichen Stelle.

## Rollen

- **Prüfgruppe:** mindestens zwei Personen mit pseudonymen Prüfer-IDs (`P-1`, `P-2` …). Jeder Eintrag braucht die Freigabe von zwei verschiedenen IDs (Vier-Augen-Prinzip). [Leerstelle: Zuordnung der IDs, geführt bei der verantwortlichen Stelle]
- **Schlüsselinhaber:innen:** zwei Personen aus der Prüfgruppe. Sie kennen die Passphrase und verwahren die Schlüsseldatei. [Leerstelle]
- **Zugriffsprotokoll** (`namenzugriff.tsv`): Das Prüfskript schreibt es bei jeder Entschlüsselung eines Namens automatisch, ins Arbeitsverzeichnis. Eine Person der Prüfgruppe sieht es vierteljährlich durch. [Leerstelle]

## Schlüssel erzeugen und verwahren

1. `python tools/pruefen.py schluessel PFAD/pg.json` auf einem Rechner der Prüfgruppe, außerhalb jedes Git-Repositorys.
   - Das Skript fragt eine Passphrase ab (mindestens 12 Zeichen).
   - Der private Schlüssel liegt nur mit ihr verschlüsselt in der Datei (Argon2id, XSalsa20-Poly1305); die Datei erhält Rechte 0600.
2. Den ausgegebenen öffentlichen Teil (`key_id`, `alg`, `public_key`) unter `wohnen_eigentum.erfassung.schluessel` in `config/stadt.json` eintragen und veröffentlichen. Die App kennt nur diesen Teil.
3. Sicherungskopie der Schlüsseldatei auf einem verschlüsselten Datenträger, offline, an einem zweiten Ort. Die Passphrase wird getrennt verwahrt (etwa versiegelter Umschlag). Nie per E-Mail, Messenger oder Cloud-Speicher.

## Schlüsselwechsel (regelmäßig, etwa jährlich, oder beim Wechsel einer Schlüsselinhaber:in)

1. `python tools/pruefen.py schluessel-wechsel -a ARBEIT -s PFAD/pg.json -p P-1 [--neue-passphrase]`.
   - Es entsteht ein neues Paar.
   - Namen von Privatpersonen und der Bestand werden mit dem neuen Schlüssel neu versiegelt.
   - Der alte Schlüssel bleibt in der Datei, damit ältere Exporte lesbar bleiben.
2. Den neuen öffentlichen Teil in `stadt.json` eintragen und veröffentlichen. Geräte holen ihn beim nächsten Start mit Netz; Einträge, die vorher gespeichert wurden, bleiben mit dem alten Schlüssel lesbar.
3. Die Sicherungskopie erneuern.

## Verlust

- **Verlust der Datei, Sicherung vorhanden:** Sicherung einspielen, danach Schlüsselwechsel mit neuer Passphrase.
- **Verlust von Datei und Sicherung oder der Passphrase:**
  - Der Bestand und alle noch nicht eingelesenen Exporte sind nicht mehr lesbar.
  - Auch Einträge, die noch in Geräten liegen, sind mit dem alten Schlüssel versiegelt und damit verloren; sie müssen neu erfasst werden.
  - Neues Paar erzeugen und veröffentlichen.
  - Nach Art. 33 DSGVO prüfen, ob eine Meldung nötig ist (Verlust der Verfügbarkeit).

## Kompromittierung (Datei und Passphrase könnten in fremde Hände gelangt sein)

1. Sofort `schluessel-wechsel … --kompromittiert --neue-passphrase`.
   - Der alte Schlüssel wird gesperrt; `einlesen` weist Exporte mit ihm ab.
   - Der Bestand liegt danach unter dem neuen Schlüssel.
2. Den neuen öffentlichen Teil sofort veröffentlichen. Alles, was mit dem alten Schlüssel versiegelt ist, gilt als offengelegt. Das betrifft auch noch nicht exportierte Einträge in Geräten: Erfassende löschen sie dort, und sie werden mit dem neuen Schlüssel neu erfasst.
3. Innerhalb von 72 Stunden prüfen, ob eine Meldung an die Aufsichtsbehörde (Art. 33 DSGVO) und eine Benachrichtigung der Betroffenen (Art. 34) nötig ist. Bei Namen und Mietangaben ist davon auszugehen.
4. Den Vorgang mit Datum, Ursache und Maßnahmen dokumentieren (Art. 33 Abs. 5).
