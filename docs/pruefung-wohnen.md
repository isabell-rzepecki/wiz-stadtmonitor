# Prüfung Wohnen und Eigentum auf Geräten

Automatisch geprüft (tests/, CI): Formulare und Schemata, Versiegelung und Export, Einlesen der Exporte mit `tools/pruefen.py`, offline mit Service Worker (Chromium), Veröffentlichung mit synthetischen Daten, Sperre gegen Rohdaten, axe-core (WCAG 2.1 A/AA), Namen und Gruppen der Formularfelder im Barrierefreiheitsbaum.

Nicht automatisch prüfbar sind echte Geräte und Screenreader. Vor der ersten echten Erfassung einmal von Hand, mit Testschlüssel und Testcode (`tools/pruefen.py schluessel`, `tools/einladung.py`) in einer Probekonfiguration, nie mit echten Daten:

## Android (Chrome) und iOS (Safari)

1. `erfassen.html` öffnen, Code eingeben, „Zum Startbildschirm hinzufügen“; App vom Startbildschirm starten.
2. Flugmodus an, App neu starten: Gebäude erscheinen, Formular A und B lassen sich speichern; Hinweis „Offline“ sichtbar.
3. Je einen Eintrag A und B speichern; „Einträge“ zeigt 2, Karte markiert Gebäude aus A grün.
4. Flugmodus aus, „Exportieren“: Datei wird gespeichert bzw. „Datei teilen“ öffnet das Teilen-Menü (iOS: in „Dateien“ sichern).
5. Exportdatei mit `tools/pruefen.py einlesen` öffnen: 2 aufgenommen, 0 abgewiesen.
6. „Exportierte löschen“: Zähler 0.
7. iOS: Safari löscht Website-Daten nach längerer Nichtnutzung; Einträge deshalb zeitnah exportieren.

## Screenreader (TalkBack, VoiceOver, NVDA)

1. Zugang: Feld „Einladungscode“ wird mit Hinweis vorgelesen; Fehlermeldung wird angesagt.
2. Formular A: Gruppen „Wem gehört das Gebäude?“, „Werden Wohnungen vermietet?“, „Wie sicher ist die Angabe?“ mit Anzahl der Optionen; nach „Speichern“ ohne Angaben springt der Fokus auf „Bitte prüfen“ und die Liste wird vorgelesen.
3. Formular B: Einwilligungstext vor dem Kontrollkästchen; Hinweis „entspricht … € je m²“ wird angesagt; Fehlerliste wie in A.
4. „Gespeichert“ wird angesagt; Fokus auf der Überschrift.

Ergebnis mit Datum, Gerät und Version im Issue zur Datenschutz-Klärung (Issue 28) festhalten.
