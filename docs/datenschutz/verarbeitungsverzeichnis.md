# Verzeichnis von Verarbeitungstätigkeiten (Art. 30 DSGVO)

> Entwurf vom 26.10.2026, keine Rechtsberatung (Issue 28).

Verantwortliche Stelle: [Leerstelle: Name, Anschrift, Kontakt]; Datenschutzbeauftragte:r: [falls benannt]

## V1 Erfassung von Eigentum und Vermietung

- **Zweck:** Vergleichsgrundlage für Mieten, weil es keinen Mietspiegel gibt; Ansprache von Mietenden über das Gebäude.
- **Rechtsgrundlage:** Art. 6 Abs. 1 lit. f DSGVO (Interessenabwägung: `interessenabwaegung_dsfa.md`).
- **Betroffene:** Eigentümer:innen und Vermieter:innen, die natürliche Personen sind (auch GbR, Einzelkaufleute).
- **Daten:** Gebäudekennung (ALKIS), Kategorie, vermietet ja/nein, Belegart und -adresse, Sicherheit, Name (nur verschlüsselt), Vermieter-Schlüssel, pseudonyme Erfasser-ID.
- **Herkunft:** öffentliche Belege und Ortskenntnis des Teams (Art. 14 DSGVO).
- **Empfänger:** Prüfgruppe der verantwortlichen Stelle. Öffentlich nur Kategorien juristischer Personen je Gebäude und Anzahlen je Ortsbezirk.
- **Drittland:** keines. Die Website liegt bei GitHub Pages (USA, EU-US Data Privacy Framework); dort liegen keine Erfassungsdaten.
- **Löschung:** 24 Monate nach Eingang bei der Prüfgruppe; bei Widerspruch sofort (`loeschverfahren.md`).
- **Technische und organisatorische Maßnahmen:** Verschlüsselung im Gerät (libsodium sealed box), kein Server und kein Upload, Schlüssel nur bei Schlüsselinhaber:innen, Vier-Augen-Freigabe, Zugriffsprotokoll für Namen, Sperre gegen Rohdaten in Git, Veröffentlichung nur nach Mindestzahlen.

## V2 Freiwillige Mietangaben

- **Zweck:** wie V1, Vergleich tatsächlich gezahlter Mieten.
- **Rechtsgrundlage:** Einwilligung, Art. 6 Abs. 1 lit. a DSGVO (versionierter Text, Fassung 2026-10-26-v3 in `config/stadt.json`; Version und Zeitpunkt werden gespeichert).
- **Betroffene:** Mietende.
- **Daten:** Gebäudekennung, Nettokaltmiete und Wohnfläche (m²; beim Einlesen zu €/m² verrechnet und verworfen), Flächenklasse, Baujahrklasse, Vertragsbeginn, letzte Erhöhung, Ausstattung, optional Vermieter (nur juristische Person), Einwilligung. Keine Namen, keine Wohnungsnummer, kein Stockwerk.
- **Empfänger:** Prüfgruppe. Öffentlich nur der Median ab 5 Angaben je Ortsbezirk und Baujahrklasse, die Spanne ab 10, gerundet auf 0,10 €; je Unternehmen ab 5 Angaben aus 2 Gebäuden.
- **Drittland:** keines.
- **Löschung:** 24 Monate nach Eingang; bei Widerruf sofort. Miete und Wohnfläche werden beim Einlesen verworfen; im Bestand bleibt der Preis je m² (`pruefen.py`, DSFA).
- **Technische und organisatorische Maßnahmen:** wie V1; zusätzlich ein Widerrufscode für Mietende.

## V3 Bereitstellung der Website

- **Zweck:** Auslieferung der Seite.
- **Rechtsgrundlage:** Art. 6 Abs. 1 lit. f DSGVO.
- **Daten:** Server-Protokolle bei GitHub Pages; Kartenkacheln von basemap.de (BKG).
- **Weitere Angaben:** siehe `site/datenschutz.html`.
