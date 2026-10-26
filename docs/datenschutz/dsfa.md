# Datenschutz-Folgenabschätzung (Art. 35 DSGVO): Erfassung Wohnen und Eigentum

> Inhaltlich abgeschlossen am 26.10.2026 (Issue 28). Keine Rechtsberatung. Wirksam erst mit der Freigabe durch die verantwortliche Stelle (Abschnitt 7).
> Vorprüfung: `interessenabwaegung_dsfa.md`, Abschnitt 2. Verarbeitungen: `verarbeitungsverzeichnis.md` (V1, V2).

## 1. Gegenstand und Methode

- **Gegenstand:** V1, die Erfassung von Eigentum und Vermietung durch das Team (Art. 6 Abs. 1 lit. f DSGVO), und V2, freiwillige Mietangaben von Mietenden (Art. 6 Abs. 1 lit. a DSGVO).
- **Zweck:** Für die Stadt gibt es keinen Mietspiegel. Die Erfassung soll eine Vergleichsgrundlage für tatsächlich gezahlte Mieten schaffen.
- **Methode:** DSK-Kurzpapier Nr. 18. Ein Risiko ergibt sich aus Eintrittswahrscheinlichkeit und Schwere, je auf vier Stufen (geringfügig, überschaubar, substanziell, groß). Bewertet wird zuerst ohne, dann mit den Maßnahmen. Ergebnisstufen: geringes Risiko, Risiko, hohes Risiko.

## 2. Beschreibung der Verarbeitung

| Schritt | Ort | Daten | Schutz |
|---|---|---|---|
| Erfassen | Gerät der erfassenden Person (App `erfassen.html`, ohne Server) | V1: Gebäude, Kategorie, vermietet, Beleg, Sicherheit. V2: Gebäude, Miete, Fläche, Baujahr, Vertragsbeginn, Ausstattung, Einwilligung | Jeder Eintrag wird beim Speichern versiegelt (libsodium sealed box); das Gerät kann ihn danach nicht mehr lesen. Zugang nur mit Einladungscode |
| Export | Datei, die die erfassende Person übergibt | versiegelte Einträge, pseudonyme Erfasser-ID | Kein Upload. Nur die Prüfgruppe kann die Datei öffnen |
| Einlesen und Prüfen | Rechner der Prüfgruppe, außerhalb von Git | entschlüsselt nur im Arbeitsspeicher; Bestand versiegelt; Miete und Fläche werden zu €/m² | Schema- und Freitextprüfung, Einladungsregister, Sperrliste, Freigabe durch zwei Personen, Zugriffsprotokoll |
| Veröffentlichen | Repository und Website | Kategorien juristischer Personen je Gebäude; Anzahlen je Ortsbezirk; Median €/m² ab 5 Angaben, Spanne ab 10, gerundet auf 0,10 € | Regeln R1–R9 und eine automatische Sperre vor dem Schreiben |
| Löschen | Prüfgruppe | alle Rohdaten nach 24 Monaten; bei Widerruf oder Widerspruch sofort | `pruefen.py fristen`, `loeschen`, `widerspruch` |

Namen von Privatpersonen sind derzeit abgeschaltet (`privat_namen_aktiv: false`). Wer sie einschaltet, muss diese DSFA vorher erneut prüfen (Risiko R4).

## 3. Notwendigkeit und Verhältnismäßigkeit

- **Zweckbindung:** Die Daten dienen nur der Vergleichsgrundlage. Es gibt keinen Mietvergleich je privater Vermieter:in und keine Weitergabe.
- **Datenminimierung:**
  - Keine Namen von Mietenden, keine Wohnungsnummer, kein Stockwerk, keine Fotos.
  - Miete und Fläche werden beim Einlesen zum Preis je m² verrechnet und verworfen.
  - Erfasser:innen sind nur pseudonym erfasst.
- **Speicherbegrenzung:** 24 Monate; Exportdateien werden nach dem Einlesen gelöscht.
- **Richtigkeit:** Belegart und Sicherheit werden mit erfasst. Jeder Eintrag braucht zwei Freigaben; Konflikte und Dubletten werden markiert.
- **Rechte der Betroffenen:**
  - Mietende können ihre Einwilligung jederzeit mit dem Widerrufscode widerrufen.
  - Vermieter:innen können widersprechen (Art. 21); ihre Gebäude kommen dann auf eine Sperrliste.
  - Auskunft gibt die Prüfgruppe aus dem Bestand; der Zugriff wird protokolliert.
- **Transparenz:** Die App zeigt einen Datenschutzhinweis und einen versionierten Einwilligungstext. Die Information nach Art. 14 steht auf der Datenschutzseite. Ohne benannte verantwortliche Stelle speichert die App nichts.

## 4. Risiken und Maßnahmen

E = Eintrittswahrscheinlichkeit, S = Schwere; jeweils vor den Maßnahmen, danach das Restrisiko.

| Nr. | Risiko (Quelle → Schaden) | E / S vorher | Maßnahmen | Restrisiko |
|---|---|---|---|---|
| R1 | Mietende werden aus veröffentlichten Werten wiedererkannt → Nachteile im Mietverhältnis | substanziell / substanziell → **Risiko** | Mindestzahl 5. Bei weniger als 10 Angaben nur der Median, weil P25 und P75 sonst echte Einzelwerte wären. Rundung auf 0,10 €. Nie Einzelwerte, nie je private Vermieter:in. Die Sperre prüft das vor jeder Veröffentlichung | gering |
| R2 | Private Eigentümer:innen werden bloßgestellt (Gebäude, Name, Einnahmen) → Ansehen, Belästigung | überschaubar / substanziell → **Risiko** | Kategorie „privat“ nie je Gebäude, nur als Anzahl ab 5 je Ortsbezirk. Kein Name in Ausgaben, keine Differenz-Rückrechnung (Sperre). Kein Mietvergleich je Person | gering |
| R3 | Unbefugte greifen auf den Bestand zu (Diebstahl, Schlüssel) → Offenlegung von Mieten und Kategorien | überschaubar / substanziell → **Risiko** | Bestand und Exporte nur versiegelt. Privater Schlüssel nur mit Passphrase nutzbar (Argon2id). Papiersicherung im Tresor, Passphrase getrennt. Jährlicher Wechsel, bei Verdacht sofort. Meldewege nach Art. 33 und 34 (`schluesselverfahren.md`) | gering |
| R4 | Befugte missbrauchen ihren Zugang (Prüfgruppe, Erfassende) → Profilbildung, Zweckentfremdung | überschaubar / substanziell → **Risiko** | Vier-Augen-Freigabe; Zugriffsprotokoll, das eine Person ohne Schlüssel durchsieht. Freitext ohne Namen, Kontaktdaten und Hausnummern (App und Einlesen). Namensfeld abgeschaltet. Codes widerrufbar und befristet | gering |
| R5 | Ein Gerät mit Erfassungen geht verloren → Offenlegung | überschaubar / überschaubar → geringes Risiko | Im Gerät liegt alles versiegelt; lesbar sind nur Gebäudekennungen der Eigentumserfassung und die pseudonyme ID. Nach bestätigtem Eingang „Exportierte löschen“ | gering |
| R6 | Einwilligung unwirksam oder Information fehlt → Rechte nicht ausübbar | substanziell / überschaubar → **Risiko** | Speichern ist gesperrt, solange keine Stelle benannt ist. Einwilligungstext versioniert, Zeitpunkt gespeichert. Datenschutzhinweis in der App, Widerrufscode. Information nach Art. 14 Abs. 5 lit. b: Datenschutzseite, Aushang, Hinweis bei Beginn | gering, sobald Abschnitt 6 erfüllt ist |
| R7 | Eigentum wird falsch zugeordnet → falsche öffentliche Angabe | überschaubar / geringfügig → geringes Risiko | Beleg und Sicherheit, zwei Freigaben, Konfliktprüfung. Öffentlich nur juristische Personen; Widerspruch und Korrektur möglich | gering |
| R8 | Rohdaten gelangen in ein Git-Repository → dauerhafte Veröffentlichung | überschaubar / groß → **Risiko** | Werkzeuge verweigern Pfade in Git. Sperre im Pre-Commit-Hook und in der CI. `.gitignore`. Die Generalprobe arbeitet nur außerhalb des Repositorys | gering |

## 5. Ergebnis

Nach den Maßnahmen ist das Restrisiko für alle Risiken **gering**, sobald die Voraussetzungen in Abschnitt 6 erfüllt sind. Ein hohes Restrisiko bleibt nicht. Eine vorherige Konsultation der Aufsichtsbehörde (Art. 36 DSGVO) ist daher nicht erforderlich.

**Überprüfung:** jährlich mit dem Schlüsselwechsel, außerdem vor jeder wesentlichen Änderung. Dazu zählen das Einschalten von Namen (`privat_namen_aktiv`), ein Upload oder Server (Issue 34), neue Datenfelder und geänderte Veröffentlichungsregeln.

## 6. Voraussetzungen vor der ersten echten Erfassung

- [ ] Verantwortliche Stelle mit Anschrift und Funktionsadresse in `config/stadt.json` (Issue 28)
- [x] Form der Information nach Art. 14 festgelegt: öffentlich nach Abs. 5 lit. b, Datenschutzseite und Aushang (`information_vermieter.md`, `site/aushang.html`); offen sind nur die Orte des Aushangs
- [x] Einwilligungstext abgeschlossen: Fassung 2026-10-26-v3, geprüft gegen Art. 4 Nr. 11, 7 und 13 DSGVO (Zweck, Stelle, Datenkategorien, Speicherdauer, Freiwilligkeit, Widerruf mit Kontakt, Verweis auf Rechte); keine anwaltliche Prüfung
- [ ] Interessenabwägung und Verarbeitungsverzeichnis von der Stelle bestätigen lassen
- [ ] Inbetriebnahme nach Issue 53 (Prüfgruppe, Schlüssel, Ausgabestelle, Codes, Generalprobe)

## 7. Freigabe

| | |
|---|---|
| Verantwortliche Stelle | [Leerstelle] |
| Datenschutzbeauftragte:r angehört (falls benannt, Art. 35 Abs. 2) | [Leerstelle] |
| Ergebnis bestätigt am | [Leerstelle] |
| Unterschrift | [Leerstelle] |
