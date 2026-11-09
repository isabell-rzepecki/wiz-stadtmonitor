# Betrieb auf der eigenen Domain (Plesk)

Die Seite läuft unter **https://stadtmonitor-witzenhausen.de/**. GitHub Actions baut sie täglich (04:17 UTC) und bei
jeder Änderung und lädt die fertige Seite per SFTP auf den Plesk-Server (`tools/plesk_hochladen.sh`). Danach zeigt
GitHub Pages nur noch eine Weiterleitung auf die Domain. Nichts mit Nutzungsbeschränkung (Flächen der Bauleitplanung)
liegt dafür im Repository.

## Einmalig beim Anbieter und in Plesk

1. **Domain registrieren** `stadtmonitor-witzenhausen.de` beim Hosting-Anbieter (Kundenbereich, Bestellung einer
   Domain zum vorhandenen Webhosting). Danach zeigt der DNS-Eintrag auf den Plesk-Server; bei einer Domain im selben
   Paket legt Plesk die Einträge selbst an.
2. **Domain in Plesk hinzufügen** („Websites & Domains“ → „Domain hinzufügen“, nicht Subdomain); den Dokumentstamm
   notieren (meist `stadtmonitor-witzenhausen.de` oder `httpdocs`). `www.stadtmonitor-witzenhausen.de` leitet die
   mitgelieferte `.htaccess` auf die Adresse ohne `www` um.
3. **SSL/TLS-Zertifikat** von Let's Encrypt für die Domain und `www` ausstellen und „Permanente SEO-sichere
   301-Weiterleitung von HTTP zu HTTPS“ einschalten. Geht erst, wenn der DNS-Eintrag weltweit sichtbar ist.
4. **Zugang für SFTP:** unter „Webhosting-Zugang“ der Systembenutzer mit **SSH-Zugang** („/bin/sh (chrooted)“
   genügt) und einem langen, nur dafür genutzten Passwort. Zusätzliche FTP-Konten können meist kein SFTP.
5. **Apache** muss aktiv sein (Standard in Plesk), damit `.htaccess` gilt (Fehlerseite, Medientypen, `www`-Umleitung,
   keine Verzeichnislisten).
6. **Auftragsverarbeitung:** den Vertrag nach Art. 28 DSGVO mit dem Hosting-Anbieter abschließen (meist im
   Kundenbereich) und Name und Sitz des Anbieters in `config/stadt.json` unter `projekt.hosting.anbieter` eintragen
   (oder mitteilen); die Datenschutzseite übernimmt sie.

## Einmalig in GitHub

Im Repository unter *Settings → Secrets and variables → Actions → New repository secret* eintragen (nie in Dateien,
Chat oder E-Mail):

| Secret | Inhalt |
|---|---|
| `PLESK_HOST` | Servername für SSH/SFTP (Plesk-Adresse ohne `https://` und `:8443`, oder laut Anbieter) |
| `PLESK_USER` | Systembenutzer aus Schritt 4 |
| `PLESK_PASSWORT` | Passwort dazu |
| `PLESK_PFAD` | Dokumentstamm aus Schritt 2, relativ zum Startordner des Benutzers |
| `PLESK_PORT` | nur falls nicht 22 |
| `PLESK_KNOWN_HOSTS` | empfohlen: Hostschlüssel des Servers; der erste Lauf zeigt die Fingerabdrücke im Protokoll |

Danach unter *Actions → Daten und Seite → Run workflow* einmal starten. Der erste Lauf lädt hoch, ohne etwas zu
löschen, und legt die Markierung `.stadtmonitor` an; spätere Läufe entfernen auf dem Server, was es nicht mehr gibt
(außer `.well-known`).

## Wenn etwas nicht klappt

- **Ohne Secrets** lädt der Lauf nichts hoch und GitHub Pages zeigt weiter die ganze Seite.
- **Falscher Pfad, falsches Passwort oder fremder Hostschlüssel:** der Lauf bricht ab, GitHub Pages bleibt beim
  letzten Stand.
- **Zertifikat scheitert:** meist ist die Domain noch nicht im DNS sichtbar; eine Stunde warten, erneut versuchen.
- **Erfassung:** Die App speichert Einträge je Adresse. Codekarten und QR-Codes zeigen auf die Domain; Einträge, die
  noch unter der GitHub-Adresse liegen, vor dem Umzug dort exportieren.
