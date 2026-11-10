# Inbetriebnahme der Erfassung Wohnen und Eigentum

Alles läuft im internen Bereich der Domain (`/intern/`, mit Passwort). Die Startseite dort fragt „Wer sind Sie?“ und führt je Rolle Schritt für Schritt. Namen gehören nicht ins Repository.

1. **Verantwortliche Stelle** benannt (26.10.2026, `config/stadt.json`, `wohnen_eigentum.erfassung.datenschutz`).
2. **Prüfgruppe** richtet auf der Prüfseite die Arbeitsdatei ein und gibt die Kartenliste an die Ausgabestelle → [pruefgruppe.md](pruefgruppe.md)
3. **Ausgabestelle** druckt Einladungskarten mit QR-Code und schickt die Kartenliste zurück → [ausgabestelle.md](ausgabestelle.md)
4. **Aushang** (`aushang.html`) drucken und vor Beginn aushängen: Stadtbibliothek und Bürgerbüro, Dorfgemeinschaftshäuser der Ortsteile, Mieterberatung, Initiativen, Universitätsstandort (`docs/datenschutz/information_vermieter.md`).
5. **Erfassende** scannen ihre Karte, erfassen und schicken die Exportdatei → [erfassende.md](erfassende.md)
6. Probelauf: eine Karte, ein Eintrag je Formular, Export, Einlesen, Freigabe, Vorschau der Veröffentlichung.

Seit 10.11.2026 gilt die normale Schutzstufe (Entscheidung der Projektverantwortlichen): kein Netztrennen, keine Papiersicherung, eine Freigabe, Schlüssel und Codes müssen nicht mehr in die Konfiguration. Begründung und Folgen: `docs/datenschutz/schluesselverfahren.md`.
