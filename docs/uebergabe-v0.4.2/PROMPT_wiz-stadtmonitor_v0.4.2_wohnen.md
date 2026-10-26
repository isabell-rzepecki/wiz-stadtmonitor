# Übergabe v0.4.2: Unterseite „Wohnen und Eigentum“ – 2D/3D-Karte, Erfassung ohne Server, Mietvergleich

> Stand 26.10.2026.
> - **Ersetzt** die Prompts v0.4 und v0.4.1.
> - **Ergänzt** v0.1–v0.3.
> - Material aus `material/` nach `docs/uebergabe-v0.4.2/` kopieren.

## 0. Vorgehen

1. Berichte kurz den Stand im Repository:
   - Frontend: Kartenbibliothek, Routing, Build;
   - Datenpipeline: welche Quellen aus v0.2/v0.3 schon eingebunden sind;
   - PWA-Grundlage: Service Worker, Manifest.
2. Lege einen Plan für die Phasen W1–W6 vor und warte auf Freigabe. Nach jeder Phase fragst du nach.
3. Weiter gelten:
   - Quellentreue;
   - Kennzeichnung abgeleiteter Daten;
   - Audit-TSV;
   - WCAG 2.1 AA;
   - Grundfarbe `#f4726b` mit abgedunkelter Textvariante;
   - Lilita One für Überschriften, Space Mono für alles andere;
   - kein Abruf aus dem SessionNet.

## 1. Zweck und Begründung

Das Folgende muss sich in README, Datenschutzhinweis und Code-Kommentaren der betroffenen Module wiederfinden.

**Zweck.** Für Witzenhausen gibt es keinen Mietspiegel. Die Seite schafft eine Vergleichsgrundlage für tatsächlich gezahlte Mieten. Dafür braucht es:
- Mietangaben von Mietenden;
- das Wissen, wer welche Gebäude vermietet. Damit kann man Mietende gezielt ansprechen und Mieten je Vermieter vergleichen.

**Warum zwei getrennte Erfassungen.**

*Eigentum/Vermietung* erfasst das Team: Wer besitzt bzw. vermietet ein Gebäude?

*Mietangaben* machen Mietende freiwillig und mit Einwilligung (Art. 6 Abs. 1 lit. a DSGVO): Nettokaltmiete, Wohnflächenklasse, Baujahrklasse, Jahr des Vertragsbeginns, Gebäude.

Beide Datenarten haben unterschiedliche Betroffene und Rechtsgrundlagen. Sie werden deshalb getrennt erhoben, gespeichert und geprüft.

**Warum ein Vermieter-Schlüssel statt des Namens.** Für den Vergleich müssen Gebäude derselben vermietenden Person gebündelt werden. Dafür genügt ein interner Schlüssel (`V-017`); den Namen braucht es nicht.
- Der Name einer Privatperson wird nur verschlüsselt gespeichert. Er dient allein dazu, Dubletten zu erkennen und Angaben zu prüfen.
- Bei juristischen Personen (Unternehmen, Genossenschaften, öffentliche Hand, Kirchen) ist der Name selbst der Schlüssel (`JP:<Name>`) und darf veröffentlicht werden.
- GbR und Einzelkaufleute gelten als Privatpersonen.

**Warum nur aggregierte Veröffentlichung mit Mindestzahlen** (`material/veroeffentlichungsregeln.tsv`).
- Einzelne Mietangaben machen über das Gebäude die Mietenden erkennbar.
- Ein Mietvergleich je privater Vermieter:in wäre ein Finanzprofil einer Person (Mieteinnahmen). Bei kleinen Vermietern wären zudem die Mietenden identifizierbar.

Daher gilt:
- Mieten je Ortsbezirk und Baujahrklasse: Median und Spanne ab 5 Angaben.
- Vergleiche je Vermieter nur bei juristischen Personen: ab 5 Angaben aus mindestens 2 Gebäuden.
- Für private Vermieter:innen gibt es keinen öffentlichen Vergleich, auch nicht pseudonym.

**Warum die Mietenden über das Gebäude angesprochen werden.** Für die Ansprache genügt das Gebäude: Hausaushang, Flyer, Kontakt über Initiativen. Der Vermieter-Schlüssel hilft, alle Häuser derselben vermietenden Person zu erreichen, ohne den Namen offenzulegen.

**Warum es keine Rohdaten auf GitHub gibt.** Die Seite läuft vorerst nur auf GitHub Pages, ohne eigenen Server. Personenbezogene Rohdaten (verschlüsselte Namen, Mietangaben) werden deshalb weder in ein öffentliches noch in ein privates Repository übernommen.
- Sie existieren nur als **verschlüsselte Exportdateien zum Download** aus der App.
- Verwahrt und verarbeitet werden sie lokal durch die Prüfgruppe.
- So entsteht keine Speicherung bei einem US-Anbieter, und die Kontrolle bleibt bei der verantwortlichen Stelle.

**Grenzen, die auf der Seite stehen müssen:**
- kein Mietspiegel;
- die Angaben sind freiwillig und nicht repräsentativ;
- Zensus-Werte haben den Stichtag 15.05.2022;
- die Eigentumskarte ist unvollständig: Sie zeigt nur, was belegt erfasst wurde, mit dem Erfassungsstand je Ortsbezirk.

**Vor der ersten echten Erfassung zu klären** (als Issues anlegen; ich bin keine Rechtsberatung):
- verantwortliche Stelle nach Art. 4 Nr. 7 DSGVO (Initiative oder Verein, benannt);
- dokumentierte Interessenabwägung für die Eigentumserfassung;
- Einwilligungstext für Mietangaben (versioniert);
- Informationspflicht nach Art. 14 DSGVO gegenüber Vermieter:innen;
- Prüfung einer Datenschutz-Folgenabschätzung;
- Verarbeitungsverzeichnis;
- Lösch- und Widerspruchsverfahren.

Bis dahin sind die sensiblen Felder per Konfiguration deaktiviert: `privat_namen_aktiv: false`, `mietangaben_aktiv: false`.

## 2. Architektur (nur GitHub Pages, nur Flat Files)

- **Öffentliche Seite und Erfassungs-PWA:** statisch auf GitHub Pages. Keine Datenbank, kein Server, keine serverlose Funktion.
- **Kartendaten:**
  - Gebäude und Bodenrichtwertzonen als **PMTiles**. Zu prüfen ist, ob GitHub Pages die HTTP-Range-Abfragen zuverlässig bedient. Fallback: Kachelverzeichnis `{z}/{x}/{y}.pbf`.
  - Kleine Ebenen als GeoJSON.
  - Grenzwerte: Dateien unter 100 MB, Site unter ca. 1 GB.
- **Sensible Daten:** nur im Gerät, verschlüsselt (IndexedDB), und als verschlüsselte Exportdatei.
  - Verschlüsselung mit dem öffentlichen Schlüssel der Prüfgruppe: libsodium sealed box oder age. Eine gepflegte Bibliothek verwenden, nichts selbst bauen.
  - Die PWA kennt keinen privaten Schlüssel.
- **Prüfung und Veröffentlichung:** lokale Skripte bei der Prüfgruppe (Abschnitt W5). Ins öffentliche Repository gelangen nur aggregierte bzw. zulässige Ausgabedateien.

## 3. Phasen

**W1 – Datenbasis Wohnen (Build-Pipeline, öffentlich)**
- **Zensus 2022:** Gemeindewerte gegen die Zensusdatenbank verifizieren. Das 100-m-Gitter (Nettokaltmiete, Leerstand, Eigentümerquote) mit den Gemarkungen verschneiden; Zuordnung über den Zellmittelpunkt. Ausgabe: `data/wohnen/zensus_ortsbezirk.json` mit Kennzeichnung „Näherung“. Unterdrückte Werte nicht als 0 behandeln.
- **Bodenrichtwerte 2022/2024/2026:** Spannen je Gemarkung und Zonen als PMTiles mit Stichtagsattribut.
- **Rechtlicher Rahmen** als datierte Textbausteine mit Quelle: Wohngeld-Mietenstufe, KdU-Grenzen mit Stand, Mieterschutzverordnung.
- **INKAR/BBSR-Angebotsmieten** (Kreis) nur nach Lizenzprüfung.
- **Audit:** `audit/wohnen_<datum>.tsv`.

**W2 – Gebäude 2D/3D**
- **2D:** ALKIS-Gebäudegrundrisse (`ave:GebaeudeBauwerk`, Feld `funktion`) als Flächen, klickbar. Schlüssel ist die ALKIS-OID (`DEHE…`).
- **3D, Stufe A (umsetzen):** dieselben Grundrisse als MapLibre-`fill-extrusion`. Die Höhe je Gebäude wird in der Pipeline aus den hessischen LoD2-Daten berechnet (INSPIRE-Atom-Download, dl-de/zero-2.0). Umschalten per Schalter „2D/3D“ und Neigung. Klick und Detailansicht sind identisch zu 2D.
- **3D, Stufe B (nur nach Rückfrage):** echte LoD2-Modelle als 3D Tiles (`tileset.json` + glb), Anzeige über deck.gl `Tile3DLayer`. Vorher Datenvolumen und Performance auf Mobilgeräten messen und berichten.
- **Zuordnung LoD2 ↔ ALKIS:** zuerst prüfen, ob die IDs übereinstimmen. Sonst räumlich zuordnen (Schwerpunkt LoD2 im ALKIS-Grundriss) und als `audit/lod2_alkis_zuordnung.tsv` protokollieren (gleich / räumlich / ohne Treffer).
- **Ohne Höhe:** Gebäude ohne LoD2-Höhe bekommen eine Standardhöhe und das Kennzeichen „Höhe geschätzt“.

**W3 – Unterseite `/wohnen` (öffentlich)**
- **Module:**
  - Mietniveau: Hinweis „kein Mietspiegel“, Zensus-Bestandsmiete, rechtlicher Rahmen.
  - Verlauf: Bodenrichtwerte nach Stichtag, Angebotsmieten nur auf Kreisebene.
  - Eigentum: Karte nach Kategorien; „privat“ nur als Anteil je Ortsbezirk.
  - Mietvergleich: nur nach Regeln R4/R5, sonst „zu wenige Angaben“.
  - Bezug zu Tagesordnungspunkten (Wohnen, Bauleitplanung, Liegenschaften).
- **Glossar:** Bestandsmiete, Angebotsmiete, ortsübliche Vergleichsmiete, Median, Mindestzahl.
- **Erfassungsstand** je Ortsbezirk (Anteil Gebäude mit Kategorie).

**W4 – Erfassungs-PWA `/erfassen` (geschlossener Kreis)**
- **Zugang:** nicht in der öffentlichen Navigation verlinkt. Der Zugang wird über einen Einladungscode freigeschaltet. Daraus entsteht eine pseudonyme Erfasser-ID; Klarnamen werden nicht gespeichert.
- **Offline:** Gebäude-Kacheln je Ortsbezirk vorab laden; Speicherung in IndexedDB.
- **Formular A, Eigentum/Vermietung** (`material/schema_erfassung_eigentum.json`):
  - Gebäude antippen, Kategorie wählen (große Schaltflächen), vermietet ja/nein/teilweise.
  - Name: bei juristischen Personen als Klartext; bei „privat“ als internes Feld mit Hinweis „wird verschlüsselt, nicht veröffentlicht“, sofort verschlüsselt.
  - Außerdem Vermieter-Schlüssel (vorläufig `V-neu`), Belegart und Sicherheit.
- **Formular B, Mietangabe** (`material/schema_mietangabe.json`):
  - Ausfüllbar durch Mietende selbst oder im Gespräch mit dem Team.
  - Pflicht ist die Einwilligung mit Textversion und Zeitpunkt.
  - Keine Wohnungsnummer, kein Stockwerk, keine Namen von Mietenden.
  - Die Wohnfläche in m² dient nur zur Berechnung von €/m²; gespeichert wird die Klasse.
  - Der ganze Datensatz wird im Gerät verschlüsselt.
- **Export:**
  - Schaltfläche „Exportieren“: eine verschlüsselte Datei je Formulartyp (`eigentum_<erfasser>_<datum>.age` bzw. `.bin`) zum Download bzw. Teilen.
  - Danach können die Einträge im Gerät als „exportiert“ markiert oder gelöscht werden.
  - Es gibt keinen automatischen Upload.
- **Validierung** gegen die Schemata bereits im Gerät. Hausnummern in Freitextfeldern werden abgewiesen.
- **Datenschutzhinweis** und Kontakt für Widerspruch in der App.

**W5 – Lokale Prüf- und Veröffentlichungsskripte** (laufen bei der Prüfgruppe, nicht im Browser, nicht in GitHub Actions)
- `tools/pruefen.py`:
  - Exportdateien lokal entschlüsseln, gegen die Schemata validieren, Dubletten je Gebäude erkennen.
  - Vermieter-Schlüssel vergeben bzw. zusammenführen.
  - Konfliktliste erstellen; Freigabe nach Vier-Augen-Prinzip (zwei Prüfer-IDs).
  - Ausgabe `audit/pruefung_<datum>.tsv`, ohne Namen und ohne Mietbeträge einzelner Angaben.
- `tools/veroeffentlichen.py`:
  - Erzeugt aus freigegebenen Daten nur die öffentlichen Dateien: `data/eigentum.pmtiles` bzw. `.geojson` (Kategorien und juristische Namen), `data/wohnen/eigentum_anteile_ortsbezirk.json`, `data/wohnen/mieten_aggregiert.json` (Regeln R4/R5/R8).
  - Bricht ab, wenn eine Ausgabedatei Felder wie `name_privat_enc`, Klarnamen zu „privat“, `angabe_id`, Einzelbeträge oder Zellen unter dem Schwellenwert enthält.
  - Tests dafür schreiben.
- **Ablage der Rohdaten:** außerhalb jedes Git-Repositorys, bei der verantwortlichen Stelle, verschlüsselt. Den Ablageort dokumentiert die verantwortliche Stelle, nicht das Repository.
- **Zugriffsprotokoll** für Entschlüsselungen: `namenzugriff.tsv` lokal bei der Prüfgruppe (Wer, Wann, Datensatz, Zweck).

**W6 – Absicherung und Prüfung**
- **Absicherung im Repository:**
  - `.gitignore` für `*.age`, `*.bin`, `export*`, `intern/`.
  - Pre-Commit-Hook und CI-Prüfung, die Commits mit sensiblen Feldnamen oder verschlüsselten Exportdateien ablehnen.
- **Tests:**
  - Offline/online auf Android und iOS;
  - Export und Import mit Testschlüssel;
  - Veröffentlichungsskript mit synthetischen Daten. Echte Daten erst nach Klärung der Punkte in Abschnitt 1.
- **Barrierefreiheit:** Kontrastprüfung, Screenreader-Test beider Formulare.
- **README-Abschnitt** „Wohnen und Eigentum: Zweck, Methode, Datenschutz, Grenzen“ auf Grundlage von Abschnitt 1.

## 4. Nicht tun

- Keine personenbezogenen Rohdaten in irgendein Git-Repository, in Issues, Actions-Logs, Analytics oder Fehlermeldungen.
- Keine Namen von Privatpersonen im Klartext speichern, anzeigen oder übertragen.
- Keine Namen aus Grundbuchauszügen Dritter.
- Keine Fotos von Personen, keine Klingelschilder als Beleg.
- Keine Angebotsmieten privater Portale.
- Keine Darstellung einzelner Mietangaben und kein Mietvergleich je privater Vermieter:in.
- Kein Server, keine Datenbank, keine serverlose Funktion ohne ausdrückliche neue Entscheidung.

## 5. Offene Punkte (als Issues)

- Datenschutz-Klärung laut Abschnitt 1, inkl. Einwilligungstext und Datenschutzhinweis.
- Benennung der Prüfgruppe und der Schlüsselinhaber:innen; Verfahren bei Schlüsselverlust oder -wechsel.
- Ausgabe und Widerruf der Einladungscodes.
- Lizenz der veröffentlichten Daten (CC BY 4.0 oder ODbL).
- Range-Abfragen von PMTiles auf GitHub Pages testen; ggf. Fallback.
- Lizenz der INKAR/BBSR-Angebotsmieten.
- Späterer Umzug auf einen eigenen Server in der EU: derselbe statische Build; ein Upload-Endpunkt mit Flat-File-Ablage wäre dann möglich.
