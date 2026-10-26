# Interessenabwägung und Vorprüfung DSFA: Erfassung von Eigentum und Vermietung

> Entwurf vom 26.10.2026, keine Rechtsberatung. Vor der ersten echten Erfassung von der verantwortlichen Stelle zu prüfen und zu unterzeichnen (Issue 28).

Verantwortliche Stelle: [Leerstelle: Name, Anschrift, Kontakt]

## 1. Interessenabwägung (Art. 6 Abs. 1 lit. f DSGVO)

**Verarbeitung.** Das Team erfasst je Gebäude, wer es besitzt oder vermietet. Grundlage sind Belege: Handelsregister, Beteiligungsbericht, Bekanntmachung, Bauschild, Presse, Website der Eigentümerin, Ortskenntnis, eigener Grundbuchauszug nur für ein eigenes Grundstück. Erfasst werden die Kategorie, ob vermietet wird, die Belegart und wie sicher die Angabe ist. Bei Privatpersonen (auch GbR und Einzelkaufleute) kommt der Name hinzu, nur verschlüsselt.

**Berechtigtes Interesse.** Für die Stadt gibt es keinen Mietspiegel. Eine Vergleichsgrundlage für tatsächlich gezahlte Mieten braucht das Wissen, wer welche Gebäude vermietet: Nur so lassen sich Mietende gezielt ansprechen und Mieten je Vermieter vergleichen. Transparenz über die Eigentumsstruktur des Wohnungsmarkts ist ein öffentliches Interesse.

**Erforderlichkeit.**
- Bei juristischen Personen genügt die Kategorie mit Namen; ein Personenbezug besteht nicht.
- Bei Privatpersonen wird der Name nur gebraucht, um Gebäude derselben Person zu bündeln (Vermieter-Schlüssel `V-017`) und Dubletten zu erkennen. Veröffentlicht wird er nie.
- Mildere Mittel: Ohne Bündelung wäre keine Ansprache aller Mietenden einer Person möglich. Ohne Namen ließe sich die Bündelung nicht prüfen.

**Interessen der Betroffenen.** Private Vermieter:innen erwarten nicht, dass Dritte ihr Eigentum systematisch erfassen. Belastend wäre eine Veröffentlichung je Person oder ein Rückschluss auf Mieteinnahmen.

**Schutzmaßnahmen (umgesetzt, W4–W6).**
- Namen von Privatpersonen nur verschlüsselt im Gerät (libsodium sealed box), entschlüsselbar nur bei der Prüfgruppe; jede Entschlüsselung protokolliert.
- Keine Veröffentlichung je Person; Kategorie „privat“ nie je Gebäude, nur als Anzahl je Ortsbezirk ab 5 Gebäuden.
- Kein Mietvergleich je privater Vermieter:in, auch nicht pseudonym (R6).
- Keine Fotos, keine Klingelschilder, keine Namen aus Grundbuchauszügen Dritter.
- Kein Server, kein Upload; Rohdaten nie in einem Git-Repository (Sperre in Hook und CI).
- Freigabe nach dem Vier-Augen-Prinzip; Speicherdauer 24 Monate (Löschverfahren).
- Widerspruch jederzeit (Art. 21), siehe Löschverfahren.

**Ergebnis (Vorschlag).** Mit diesen Maßnahmen überwiegt das Interesse an einer Vergleichsgrundlage, sofern die Informationspflicht (Art. 14) erfüllt und der Widerspruch einfach möglich ist. Die Entscheidung trifft die verantwortliche Stelle.

## 2. Vorprüfung Datenschutz-Folgenabschätzung (Art. 35 DSGVO)

Kriterien nach den Leitlinien der Datenschutzbehörden (WP 248); eine DSFA gilt in der Regel als nötig, wenn zwei oder mehr zutreffen.

| Kriterium | Eigentum | Mietangaben |
|---|---|---|
| Bewertung oder Scoring | nein | nein |
| Automatisierte Entscheidung mit Rechtswirkung | nein | nein |
| Systematische Überwachung | teilweise (systematische Erfassung aller Gebäude) | nein |
| Vertrauliche oder höchstpersönliche Daten | nein | ja (Miete, Finanzdaten) |
| Umfangreiche Verarbeitung | nein (eine Kleinstadt) | nein |
| Abgleich oder Zusammenführung von Datensätzen | ja (Kataster, Belege, Mietangaben über das Gebäude) | ja |
| Schutzbedürftige Betroffene | nein | teilweise (Abhängigkeit vom Vermieter) |
| Neue Technologien | nein | nein |
| Hindert an Rechtsausübung | nein | nein |

**Ergebnis (Vorschlag).** Zwei oder mehr Kriterien treffen zumindest teilweise zu. Empfohlen wird eine kurze DSFA vor dem Start, mit den Schutzmaßnahmen oben als Kern.

**Durchgeführt:** `dsfa.md` (26.10.2026). Restrisiko gering, keine Konsultation nach Art. 36; Freigabe durch die verantwortliche Stelle offen.
