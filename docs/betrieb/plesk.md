# Betrieb auf der Subdomain (Plesk)

Die Seite läuft unter **https://stadtmonitor.wiz-o-mat.de/**. GitHub Actions baut sie täglich (04:17 UTC) und bei jeder
Änderung und lädt die fertige Seite per SFTP auf den Plesk-Server (`tools/plesk_hochladen.sh`). Danach zeigt GitHub Pages nur
noch eine Weiterleitung auf die Subdomain. Nichts mit Nutzungsbeschränkung (Flächen der Bauleitplanung) liegt dafür im
Repository.

## Einmalig in Plesk

1. **Subdomain** `stadtmonitor.wiz-o-mat.de` anlegen; den Dokumentstamm notieren (meist `stadtmonitor.wiz-o-mat.de` oder `httpdocs/stadtmonitor`).
2. **SSL/TLS-Zertifikat** von Let's Encrypt für die Subdomain ausstellen und „Permanente SEO-sichere 301-Weiterleitung von HTTP zu HTTPS“ einschalten.
3. **Zugang für SFTP:** unter „Webhosting-Zugang“ (oder „FTP-Zugang“) einen Benutzer mit **SSH-Zugang** („/bin/sh (chrooted)“ genügt) und einem langen, nur dafür genutzten Passwort. Ohne SSH-Zugang gibt es kein SFTP.
4. **Apache** muss aktiv sein (Standard in Plesk), damit `.htaccess` gilt (Fehlerseite, Medientypen, keine Verzeichnislisten).
5. **Auftragsverarbeitung:** den Vertrag nach Art. 28 DSGVO mit dem Hosting-Anbieter abschließen (meist im Kundenbereich) und Name und Sitz des Anbieters in `config/stadt.json` unter `projekt.hosting.anbieter` eintragen (oder mitteilen); die Datenschutzseite übernimmt sie.

## Einmalig in GitHub

Im Repository unter *Settings → Secrets and variables → Actions → New repository secret* eintragen (nie in Dateien, Chat oder E-Mail):

| Secret | Inhalt |
|---|---|
| `PLESK_HOST` | Servername, etwa der Name aus der Plesk-Adresse |
| `PLESK_USER` | Benutzer aus Schritt 3 |
| `PLESK_PASSWORT` | Passwort dazu |
| `PLESK_PFAD` | Dokumentstamm der Subdomain aus Schritt 1, relativ zum Startordner des Benutzers |
| `PLESK_PORT` | nur falls nicht 22 |
| `PLESK_KNOWN_HOSTS` | empfohlen: Hostschlüssel des Servers; der erste Lauf zeigt die Fingerabdrücke im Protokoll, den Anbieter danach fragen oder in Plesk vergleichen |

Danach unter *Actions → Daten und Seite → Run workflow* einmal starten. Der erste Lauf lädt hoch, ohne etwas zu löschen, und legt
die Markierung `.stadtmonitor` an; spätere Läufe entfernen auf dem Server, was es nicht mehr gibt (außer `.well-known`).

## Wenn etwas nicht klappt

- **Ohne Secrets** lädt der Lauf nichts hoch und GitHub Pages zeigt weiter die ganze Seite.
- **Falscher Pfad, falsches Passwort oder fremder Hostschlüssel:** der Lauf bricht ab, GitHub Pages bleibt beim letzten Stand.
- **Erfassung:** Die App speichert Einträge je Adresse. Codekarten und QR-Codes zeigen auf die Subdomain; Einträge, die noch unter der GitHub-Adresse liegen, vor dem Umzug dort exportieren.
