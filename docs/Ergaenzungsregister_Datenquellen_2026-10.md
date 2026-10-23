# Offene Datenquellen für die Stadt Witzenhausen (AGS 06636016): Ergänzungsregister für „wiz-stadtmonitor“, Stand Oktober 2026

Der größte neue Gewinn für die Pipeline sind die BORIS-Hessen-Bodenrichtwerte zum Stichtag 01.01.2026. Sie sind seit 01.04.2026 unter der Lizenz Datenlizenz Deutschland – Zero 2.0 veröffentlicht, aber nicht unter dem Pfad `/brw/2026/wfs`.\[1\]\[2\] Abrufbar sind sie über das Geoportal-Kartenprojekt WMC 8243 und einen INSPIRE-Download-Feed (WFS-ID 732).\[2\]\[3\] Die Gemeindewerte aus dem Zensus 2022 (Nettokaltmiete 5,09 €/m², Eigentümerquote 54,4 %, Leerstand 4,6 %) sind konsistent belegt, bisher aber nur über Sekundärauswertungen und noch nicht direkt aus der Zensusdatenbank.\[4\]\[5\] Für die Ortsbeirats- und Wahlebene ist die votemanager-Präsentation die wichtigste Quelle. Sie ist jedoch, wie SessionNet, für automatisierten Abruf voraussichtlich gesperrt. Wahlbekanntmachungen als PDF über die WordPress-Media-API der Stadt sind deshalb der robustere Weg.

## TL;DR

- **Wohnen/Boden:** Für BORIS 2026 liegen ein Geoportal-Kartenprojekt (WMC 8243) und ein INSPIRE-Download-Feed (WFS-ID 732) mit den Objektarten `boris:BR_BodenrichtwertZonal` u. a. vor (Lizenz DL-DE Zero 2.0). Die Wohngeld-Mietenstufe ist amtlich **I**. Witzenhausen gehört **nicht** zu den 71 Kommunen des Entwurfs der neuen Hessischen Mieterschutzverordnung vom 24.09.2026. Die KdU-Grenzen gelten für den Vergleichsraum I (Bad Sooden-Allendorf, Neu-Eichenberg, Witzenhausen); der zuletzt belegte Stand ist der 01.01.2023.
- **Wahlen/Verwaltung:** Die Kommunalwahl vom 15.03.2026 ergab nach (vorläufigen, parteiseitig berichteten) Zahlen SPD 10, CDU 8, GRÜNE 7, Linke 5, FWG 4, FDP 3 von 37 Sitzen bei 61,97 % Wahlbeteiligung. Es gab 21 Urnen- und 5 Briefwahlbezirke.\[6\] Seit 14.04.2026 koalieren SPD, CDU und FDP. Die votemanager-Open-Data-CSVs sind für 2026 nicht verifiziert, und der Host blockiert automatisierten Zugriff.
- **Lücken:** Wortlaut der Hauptsatzung § 6, aktuelle KdU-Werte (Neufassung durch DOMUS Consult in Arbeit), Immobilienmarktbericht mit Witzenhausen-Kennzahlen, Bodenrichtwert-Spannen, Hebesätze sowie die meisten Fachdienste der Blöcke B–D (Lärm, Denkmal, Starkregen, Ladesäulen, Radnetz). Sie konnten in diesem Durchgang nicht belegt werden und stehen unten als „zu prüfen“ mit zuständiger Stelle.

## Key Findings

1. **BORIS 2026 ist offen, aber unter neuer Dienstadresse.** HVBG und Geoportal melden die Veröffentlichung der Bodenrichtwerte 2026 am 01.04.2026 (34.336 Bodenrichtwerte hessenweit, Wohnbauland im Mittel +2,5 %).\[1\]\[7\]\[8\] Das Geoportal-Kartenprojekt „BORIS Hessen 2026“ (WMC-ID 8243) ist mit DL-DE Zero 2.0 und EPSG:25832 ausgewiesen.\[2\] Der INSPIRE-Download-Feed des Datensatzes `c1afe4df-1290-42b3-9399-6bfd00652c13` (zeitliche Ausdehnung 01.01.2026–31.12.2027, Metadaten vom 06.10.2026) erzeugt seine Daten aus dem WFS mit der Geoportal-ID 732.\[3\]\[9\] Er listet die Objektarten `adv:AP_PTO` (featuretypeid 5403), `boris:BR_BodenrichtwertLagetypisch` (5404), `boris:BR_BodenrichtwertZonal` (5405), `boris:BR_UmrechnungstabelleWerte` (5407) und `boris:BR_Verfahren` (5408).\[3\] Eine öffentliche OGC-API-Seite („spatial-objects“) ist für 2024 (ID 864) und 2022 (ID 731) belegt, für 2026 nicht.\[10\]\[11\] Die Bestandsdatenausgabe im XML-Format (BRM 3.0.1) für die Stichtage 2022, 2024 und 2026 bietet das HVBG über gds.hessen.de an.\[12\]
2. **Zensus-2022-Gemeindewerte sind plausibel, aber noch sekundär belegt.** Zwei unabhängige Sekundärauswertungen nennen übereinstimmend für Witzenhausen (ARS 066360016016): 15.162 Einwohner, Nettokaltmiete 5,09 €/m², Eigentümerquote 54,4 %, Leerstandsquote 4,6 % (369 leere Wohnungen), 3.551 vermietete Wohnungen und eine durchschnittliche Wohnfläche von 104,1 m².\[4\]\[5\] Die Werte entsprechen den im Auftrag genannten Sekundärwerten. Eine Primärprüfung in der Zensusdatenbank steht aus.
3. **Witzenhausen bleibt außerhalb der Mietpreisbremse.** Der Verordnungsentwurf vom 24.09.2026 (Gutachten GEWOS, Juli 2026) umfasst 71 Kommunen. Witzenhausen und keine andere Kommune des Werra-Meißner-Kreises erscheint in den Listen „neu aufgenommen“ und „verbleiben“.\[13\] Die geltende Verordnung läuft am 25.11.2026 aus, ein Kabinettsbeschluss ist für Mitte November 2026 erwartet.\[13\]\[14\] Die Kappungsgrenze von 15 % gilt in Witzenhausen damit weiterhin nicht; es bleiben die bundesrechtlichen 20 %.\[13\]
4. **Mittelzentrum.** Laut Gemeindedatenblatt der Hessen Agentur ist Witzenhausen ein „Mittelzentrum im ländlichen Raum mit Verdichtungsansätzen“ (rund 15.100 Einwohner am 31.12.2024; Zensuskorrektur +0,8 % bzw. +122 Einwohner).\[15\]
5. **Wahl-Rohdaten:** Die Stadt veröffentlicht Wahlbekanntmachungen als PDF unter `/wp-content/uploads/` (z. B. Nr. 013/2026).\[6\]\[16\] Damit sind sie über die bekannte Quelle `wp_media` erreichbar. Die votemanager-Seiten der Wahlen 2011, 2016 und 2021 existieren für AGS 06636016.\[17\]\[18\]\[19\]\[20\] Andere Hessen-Instanzen zeigen das Open-Data-Schema (`opendata-wahllokale.csv`, `opendata-strassen.csv`, Ergebnis-CSV je Wahl und Ebene).\[21\]\[22\] Für Witzenhausen 2026 ist dieses Schema nicht verifiziert.

## Register (Markdown)

| id | thema | prioritaet | name | anbieter | url | typ | layer_oder_datei | format | crs | ebene | lizenz | attribution_pflicht | test_status | status | nutzung |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| boris2026_feed | Wohnen/Boden | hoch | BORIS Hessen 2026 – INSPIRE Download Feed | HVBG | https://www.geoportal.hessen.de/mapbender/php/mod_inspireDownloadFeed.php?id=c1afe4df-1290-42b3-9399-6bfd00652c13&type=SERVICE&generateFrom=wfs&wfsid=732 | Download | boris:BR_BodenrichtwertZonal (featuretypeid 5405); 5403, 5404, 5407, 5408 | Atom/GML | EPSG:25832 | Zone | DL-DE Zero 2.0 | nein (Quellenangabe empfohlen) | geprüft 23.10.2026 (Feed abgerufen, Stand 22.09.2026) | teilweise (Stichtagsbezug des WFS 732 zu bestätigen) | Bodenrichtwertzonen 2026 als Flächenlayer |
| boris2026_wmc | Wohnen/Boden | mittel | BORIS Hessen 2026 – Geoportal-Kartenprojekt | HVBG | https://www.geoportal.hessen.de/map?WMC=8243 | Webseite | WMC 8243 | WMC/WMS | EPSG:25832 | Zone | DL-DE Zero 2.0 | nein | nicht geprüft | verifiziert (Metadaten) | Link „Bodenrichtwert nachschlagen“; WMS-Layer aus WMC ableiten |
| boris2024_api | Wohnen/Boden | mittel | WFS HE BORIS 2024 als OGC API | HVBG/Geoportal Hessen | https://www.geoportal.hessen.de/spatial-objects/864 | OGC API | boris_BR_BodenrichtwertZonal | GeoJSON/XML | EPSG:25832/WGS84 | Zone | DL-DE Zero 2.0 | nein | nicht geprüft | verifiziert | Zeitvergleich 2024→2026 |
| boris2022_api | Wohnen/Boden | niedrig | WFS HE BORIS 2022 als OGC API | HVBG/Geoportal Hessen | https://www.geoportal.hessen.de/spatial-objects/731 | OGC API | boris_BR_BodenrichtwertZonal | GeoJSON/XML | EPSG:25832/WGS84 | Zone | DL-DE Zero 2.0 | nein | nicht geprüft | verifiziert | Zeitreihe |
| boris_xml | Wohnen/Boden | niedrig | Bestandsdatenausgabe Bodenrichtwerte (BRM 3.0.1) | HVBG | https://hvbg.hessen.de/immobilienwertermittlung/bodenrichtwerte | Download | XML 2022/2024/2026 | XML | EPSG:25832 | Zone | zu prüfen (Shop gds.hessen.de) | zu prüfen | nicht geprüft | zu prüfen | Vollattribute, falls WFS limitiert |
| zensus_miete_gitter | Wohnen | hoch | Zensus 2022 Durchschnittliche Nettokaltmiete in Gitterzellen | Statistische Ämter des Bundes und der Länder | https://www.destatis.de/DE/Themen/Gesellschaft-Umwelt/Bevoelkerung/Zensus2022/_publikationen.html | Download | ZIP mit 10-km-, 1-km- und 100-m-CSV (9 MB) | CSV | EPSG:3035 (INSPIRE-Gitter) | 100-m-Gitter | DL-DE BY 2.0 | ja | nicht geprüft | teilweise (Direkt-URL der ZIP offen) | Mietniveau-Raster |
| zensus_miete_doku | Wohnen | mittel | Datensatzbeschreibung Nettokaltmiete Gitter | Statistische Ämter | https://www.zensus2022.de/static/Zensus_Veroeffentlichung/Datensatzbeschreibung_Durchschn_Nettokaltmiete_Gitterzellen.xlsx | Download | XLSX | XLSX | – | – | DL-DE BY 2.0 | – | nicht geprüft | verifiziert (URL) | Spaltennamen/Geheimhaltung |
| zensus_eigentum_gitter | Wohnen | hoch | Zensus 2022 Eigentümerquote in Gitterzellen | Statistische Ämter | https://www.destatis.de/DE/Themen/Gesellschaft-Umwelt/Bevoelkerung/Zensus2022/_publikationen.html | Download | ZIP (15,55 MB) | CSV | EPSG:3035 | 100-m-Gitter | DL-DE BY 2.0 | ja | nicht geprüft | teilweise | Eigentum vs. Miete je Ortsteil |
| zensus_leerstand_gitter | Wohnen | hoch | Zensus 2022 Leerstandsquote und marktaktive Leerstandsquote in Gitterzellen | Statistische Ämter | https://www.destatis.de/DE/Themen/Gesellschaft-Umwelt/Bevoelkerung/Zensus2022/_publikationen.html | Download | 2 ZIPs (12,37 MB / 13,18 MB) | CSV | EPSG:3035 | 100-m-Gitter | DL-DE BY 2.0 | ja | nicht geprüft | teilweise | Leerstandskarte |
| zensus_alter_gitter | Bevölkerung | mittel | Zensus 2022 Alter in 10er-Jahresgruppen in Gitterzellen | Statistische Ämter | https://www.destatis.de/DE/Themen/Gesellschaft-Umwelt/Bevoelkerung/Zensus2022/_publikationen.html | Download | ZIP (ca. 35,93 MB) | CSV | EPSG:3035 | 100-m-Gitter | DL-DE BY 2.0 | ja | nicht geprüft | teilweise | Altersstruktur je Ortsteil |
| zensus_esri_fs | Wohnen/Bevölkerung | niedrig | Zensus2022_grid_final (FeatureServer, Esri-Aufbereitung) | Esri Deutschland (Drittanbieter) | https://services2.arcgis.com/jUpNdisbWqRpMo35/arcgis/rest/services/Zensus2022_grid_final/FeatureServer | API | Layer 0 Zensus2022_100mGitter | JSON/GeoJSON | zu prüfen | 100-m-Gitter | DL-DE BY 2.0 (laut Esri-Item) | ja | nicht geprüft | zu prüfen | nur Fallback/Prototyping |
| wogv_anlage | Wohnen | mittel | Anlage zu § 1 Abs. 3 WoGV – Mietenstufen | BMJ (gesetze-im-internet) | https://www.gesetze-im-internet.de/wogv/anlage.html | Webseite | Land Hessen: „Witzenhausen, Stadt – I“ | HTML | – | Gemeinde | amtliches Werk (§ 5 UrhG) | nein | nicht geprüft | verifiziert | Kennzahl Mietenstufe |
| kdu_wmk_2023 | Wohnen/Soziales | mittel | KdU-Angemessenheitsrichtwerte WMK (Flyer, Stand 01.01.2023) | Jobcenter Werra-Meißner (Kopie harald-thome.de) | https://harald-thome.de/files/pdf/KdU%20New/KdU%20Werra-Mei%C3%9Fner%20Kreis%20-%2001.01.2023.pdf | PDF | Vergleichsraum I | PDF | – | Vergleichsraum | keine offene Lizenz | ja (Quelle) | nicht geprüft | teilweise (veraltet möglich) | KdU-Grenzen (nur Text) |
| kdu_jobcenter | Wohnen/Soziales | mittel | Jobcenter Werra-Meißner – Unterkunftskosten | Jobcenter Werra-Meißner | https://jobcenter-werra-meissner.de/geldleistungen/unterkunftskosten/ | Webseite | Flyer „KDU“ | HTML/PDF | – | Vergleichsraum | keine offene Lizenz | ja | nicht geprüft | zu prüfen | aktuellen Flyer beziehen |
| kdu_merkblatt_wmk | Wohnen/Soziales | niedrig | Merkblatt Anmietung von Wohnraum (SGB XII/II) | Kreisausschuss WMK | https://www.werra-meissner-kreis.de/fileadmin/01_Homepage_Kreisverwaltung/Fachbereiche_und_Einrichtungen/FB6_Soziales_und_Senioren/6.1_Sicherung_Aktivierung_der_Lebensgrundlagen/Merkblatt_KdU.pdf | PDF | – | PDF | – | Kreis | keine offene Lizenz | ja | nicht geprüft | teilweise | Verfahrenshinweise |
| mischuv_2026 | Wohnen/Recht | mittel | Entwurf Hessische Mieterschutzverordnung 2026 (71 Kommunen) | HMWVW | https://hessen.de/presse/mieterschutz-soll-auf-71-kommunen-wachsen | Webseite | Gebietskulisse (Liste) | HTML | – | Gemeinde | amtliche Pressemitteilung | ja (Quelle) | geprüft 23.10.2026 | verifiziert | Status „nicht erfasst“ |
| gewos_2026 | Wohnen | niedrig | GEWOS: Angespannte Wohnungsmärkte Hessen, Ergebnisbericht 2026 | HMWVW/GEWOS | https://hessen.de/sites/hessen.hessen.de/files/damlocalcopy/infop_document/2026_gewos_hessen_angespannte_wohnungsmaerkte_ergebnisbericht_final.pdf | PDF | – | PDF | – | Gemeinde | zu prüfen | ja | nicht geprüft | verifiziert (URL) | Indikatoren für Witzenhausen nachlesen |
| immo_wmk_2023 | Wohnen/Boden | mittel | Immobilienmarktbericht 2023 GAA AfB Homberg (Efze) – Pressemitteilung | HVBG | https://hvbg.hessen.de/presse/immobilienmarktbericht-2023-online-verfuegbar-weniger-transaktionen | Webseite | – | HTML | – | Kreis | zu prüfen | ja | nicht geprüft | teilweise (aktuellere Ausgabe offen) | Umsatzkennzahlen WMK |
| gemeindelexikon | Statistik | mittel | Gemeindedatenblatt Witzenhausen (636016) | Hessen Agentur / HSL | https://www.hessen-gemeindelexikon.de/gemeindelexikon_PDF/636016.pdf | PDF | – | PDF | – | Gemeinde | zu prüfen | ja | Abruf fehlgeschlagen 23.10.2026 | teilweise | Bevölkerung, Prognose 2040, zentralörtliche Einstufung |
| gv_statistikportal | Statistik | mittel | Gemeindeverzeichnis-Eintrag 06636016 | Statistische Ämter | https://www.statistikportal.de/de/gemeindeverzeichnis/06636016 | Webseite | – | HTML | – | Gemeinde | zu prüfen (vermutl. DL-DE BY 2.0) | ja | nicht geprüft | verifiziert | Fläche, Einwohner |
| wahl_kw2026_vm | Wahlen | hoch | votemanager Kommunalwahl 15.03.2026 Witzenhausen | Stadt Witzenhausen / ekom21 | https://votemanager-ks.ekom21cdn.de/2026-03-15/06636016/praesentation/index.html | Webseite | Gemeindewahl, Ortsbeiratswahl, Kreiswahl | HTML (CSV-Export zu prüfen) | – | Wahlbezirk/Ortsbezirk | zu prüfen | zu prüfen | Abruf verweigert 23.10.2026 | teilweise | Ortsbeirats-Ergebnisse je Ortsbezirk |
| wahl_kw2026_bek | Wahlen | hoch | Wahlbekanntmachung Nr. 013/2026 | Stadt Witzenhausen | https://www.witzenhausen.eu/wp-content/uploads/2026/01/013-2026-Wahlbekanntmachung-Kommunalwahl-15-03-2026.pdf | PDF | – | PDF | – | Wahlbezirk | amtliche Bekanntmachung | nein | nicht geprüft (Inhalt via Subagent) | verifiziert | 21 Wahl- und 5 Briefwahlbezirke |
| wahl_kw2021_vm | Wahlen | niedrig | votemanager Kommunalwahl 14.03.2021 | Stadt Witzenhausen / ekom21 | https://votemanager-ks.ekom21cdn.de/2021-03-14/06636016/html5/Kreiswahl_Hessen_362_Gemeinde_Stadt_Witzenhausen.html | Webseite | Kreiswahl, Bezirke 1–21, B99100–B99500 | HTML | – | Wahlbezirk | zu prüfen | zu prüfen | nicht geprüft | verifiziert (Existenz) | Vergleichswahl |
| wahl_wahlraeume2016 | Wahlen/Orte | mittel | Wahlraumübersicht 2016 | Stadt Witzenhausen / ekom21 | https://votemanager-ks.ekom21cdn.de/20160306/06636016/html5/Wahllokaluebersicht.html | Webseite | Wahlraum → Wahlbezirk → Ortsbezirk | HTML | – | Wahlbezirk | zu prüfen | zu prüfen | nicht geprüft | teilweise | Sitzungsorte der Ortsbeiräte (DGH/Bürgerhäuser) |
| wahl_hessenschau | Wahlen | niedrig | Ergebnisseite Kommunalwahl 2026 Witzenhausen | hessenschau/HSL | https://www.hessenschau.de/politik/kommunalwahlen/ergebnisse/ergebnisse-witzenhausen---kommunalwahl-2026-v3,kw26-gemeinde-g06636016-100.html | Webseite | – | HTML (Grafiken) | – | Gemeinde | keine offene Lizenz | ja | nicht geprüft | teilweise | Plausibilisierung |
| haushalt_stadt | Finanzen | mittel | Pläne/Berichte/Abschlüsse (Haushaltsplan 2026 u. a.) | Stadt Witzenhausen | https://www.witzenhausen.eu/plane-berichte-abschlusse/ | PDF | Haushaltsplan 2026, Haushaltssatzung 2026, Jahresabschluss 2025, Beteiligungsbericht | PDF | – | Gemeinde | amtliche Dokumente | nein | nicht geprüft | verifiziert | Haushaltskennzahlen (PDF-Extraktion) |
| ortsbeiraete_seite | Verwaltung | mittel | Ortsbeiräte (Übersichtsseite) | Stadt Witzenhausen | https://www.witzenhausen.eu/ortsbeirate/ | Webseite | – | HTML | – | Ortsbezirk | – | – | nicht geprüft | verifiziert | Verlinkung; Mitglieder nur im Bürgerinfoportal (ausgeschlossen) |
| nvv_gtfs | ÖPNV | hoch | Soll-Fahrplandaten NVV (GTFS) | NVV via OpenData ÖPNV / Mobilithek | https://mobilithek.info/offers/-1983289435982938851 | Download | GTFS-ZIP | GTFS | WGS84 | Haltestelle | „Lizenz, freie Nutzung/Open Data“ (genaue Lizenz zu prüfen) | zu prüfen | Seite ohne JS nicht lesbar 23.10.2026 | teilweise | Haltestellen/Linien in Witzenhausen |
| oepnv_portal | ÖPNV | mittel | OpenData ÖPNV – Datensätze (u. a. NVV-Haltepositionen) | OpenData ÖPNV | https://www.opendata-oepnv.de/ht/de/datensaetze | Download | „Soll-Fahrplandaten NVV“, NVV-Haltepositionen | GTFS/CSV | WGS84 | Haltestelle | je Datensatz | je Datensatz | nicht geprüft | teilweise (Registrierung nötig) | Haltepositionen (Masten) |
| schutzgeb_ogcapi | Natur | niedrig | Schutzgebiete Hessen als OGC API | HMLU/Geoportal Hessen | https://www.geoportal.hessen.de/spatial-objects/266 | OGC API | Naturschutzgebiete, Landschaftsschutzgebiete, Fauna-Flora-Habitate, Vogelschutzgebiete, Naturparke u. a. | GeoJSON | WGS84 | Gebiet | zu prüfen | zu prüfen | nicht geprüft | verifiziert | GeoJSON-Alternative zum bekannten `schutzgeb` |

## Register (TSV)

```tsv
id	thema	prioritaet	name	anbieter	url	typ	layer_oder_datei	format	crs	ebene	lizenz	attribution_pflicht	test_status	status	nutzung
boris2026_feed	Wohnen/Boden	hoch	BORIS Hessen 2026 – INSPIRE Download Feed	HVBG	https://www.geoportal.hessen.de/mapbender/php/mod_inspireDownloadFeed.php?id=c1afe4df-1290-42b3-9399-6bfd00652c13&type=SERVICE&generateFrom=wfs&wfsid=732	Download	boris:BR_BodenrichtwertZonal (featuretypeid 5405); 5403,5404,5407,5408	Atom/GML	EPSG:25832	Zone	DL-DE Zero 2.0	nein	geprüft 23.10.2026	teilweise	Bodenrichtwertzonen 2026
boris2026_wmc	Wohnen/Boden	mittel	BORIS Hessen 2026 – Geoportal-Kartenprojekt	HVBG	https://www.geoportal.hessen.de/map?WMC=8243	Webseite	WMC 8243	WMC/WMS	EPSG:25832	Zone	DL-DE Zero 2.0	nein	nicht geprüft	verifiziert	Link/Viewer
boris2024_api	Wohnen/Boden	mittel	WFS HE BORIS 2024 als OGC API	HVBG/Geoportal Hessen	https://www.geoportal.hessen.de/spatial-objects/864	OGC API	boris_BR_BodenrichtwertZonal	GeoJSON/XML	EPSG:25832/WGS84	Zone	DL-DE Zero 2.0	nein	nicht geprüft	verifiziert	Zeitvergleich
boris2022_api	Wohnen/Boden	niedrig	WFS HE BORIS 2022 als OGC API	HVBG/Geoportal Hessen	https://www.geoportal.hessen.de/spatial-objects/731	OGC API	boris_BR_BodenrichtwertZonal	GeoJSON/XML	EPSG:25832/WGS84	Zone	DL-DE Zero 2.0	nein	nicht geprüft	verifiziert	Zeitreihe
boris_xml	Wohnen/Boden	niedrig	Bestandsdatenausgabe Bodenrichtwerte (BRM 3.0.1)	HVBG	https://hvbg.hessen.de/immobilienwertermittlung/bodenrichtwerte	Download	XML 2022/2024/2026	XML	EPSG:25832	Zone	zu prüfen	zu prüfen	nicht geprüft	zu prüfen	Vollattribute
zensus_miete_gitter	Wohnen	hoch	Zensus 2022 Durchschnittliche Nettokaltmiete in Gitterzellen	Statistische Ämter des Bundes und der Länder	https://www.destatis.de/DE/Themen/Gesellschaft-Umwelt/Bevoelkerung/Zensus2022/_publikationen.html	Download	ZIP 10km/1km/100m CSV (9 MB)	CSV	EPSG:3035	100-m-Gitter	DL-DE BY 2.0	ja	nicht geprüft	teilweise	Mietniveau-Raster
zensus_miete_doku	Wohnen	mittel	Datensatzbeschreibung Nettokaltmiete Gitter	Statistische Ämter	https://www.zensus2022.de/static/Zensus_Veroeffentlichung/Datensatzbeschreibung_Durchschn_Nettokaltmiete_Gitterzellen.xlsx	Download	XLSX	XLSX	–	–	DL-DE BY 2.0	–	nicht geprüft	verifiziert	Spaltennamen
zensus_eigentum_gitter	Wohnen	hoch	Zensus 2022 Eigentümerquote in Gitterzellen	Statistische Ämter	https://www.destatis.de/DE/Themen/Gesellschaft-Umwelt/Bevoelkerung/Zensus2022/_publikationen.html	Download	ZIP (15,55 MB)	CSV	EPSG:3035	100-m-Gitter	DL-DE BY 2.0	ja	nicht geprüft	teilweise	Eigentumsquote
zensus_leerstand_gitter	Wohnen	hoch	Zensus 2022 Leerstandsquote/marktaktive Leerstandsquote in Gitterzellen	Statistische Ämter	https://www.destatis.de/DE/Themen/Gesellschaft-Umwelt/Bevoelkerung/Zensus2022/_publikationen.html	Download	2 ZIP (12,37 MB / 13,18 MB)	CSV	EPSG:3035	100-m-Gitter	DL-DE BY 2.0	ja	nicht geprüft	teilweise	Leerstandskarte
zensus_alter_gitter	Bevölkerung	mittel	Zensus 2022 Alter in 10er-Jahresgruppen in Gitterzellen	Statistische Ämter	https://www.destatis.de/DE/Themen/Gesellschaft-Umwelt/Bevoelkerung/Zensus2022/_publikationen.html	Download	ZIP	CSV	EPSG:3035	100-m-Gitter	DL-DE BY 2.0	ja	nicht geprüft	teilweise	Altersstruktur
zensus_esri_fs	Wohnen/Bevölkerung	niedrig	Zensus2022_grid_final (FeatureServer)	Esri Deutschland (Drittanbieter)	https://services2.arcgis.com/jUpNdisbWqRpMo35/arcgis/rest/services/Zensus2022_grid_final/FeatureServer	API	Layer 0 Zensus2022_100mGitter	JSON/GeoJSON	zu prüfen	100-m-Gitter	DL-DE BY 2.0 (laut Esri-Item)	ja	nicht geprüft	zu prüfen	Fallback
wogv_anlage	Wohnen	mittel	Anlage zu § 1 Abs. 3 WoGV – Mietenstufen	BMJ	https://www.gesetze-im-internet.de/wogv/anlage.html	Webseite	Hessen: Witzenhausen, Stadt – I	HTML	–	Gemeinde	amtliches Werk (§ 5 UrhG)	nein	nicht geprüft	verifiziert	Mietenstufe
kdu_wmk_2023	Wohnen/Soziales	mittel	KdU-Angemessenheitsrichtwerte WMK (Stand 01.01.2023)	Jobcenter Werra-Meißner (Kopie harald-thome.de)	https://harald-thome.de/files/pdf/KdU%20New/KdU%20Werra-Mei%C3%9Fner%20Kreis%20-%2001.01.2023.pdf	PDF	Vergleichsraum I	PDF	–	Vergleichsraum	keine offene Lizenz	ja	nicht geprüft	teilweise	KdU-Grenzen
kdu_jobcenter	Wohnen/Soziales	mittel	Jobcenter Werra-Meißner – Unterkunftskosten	Jobcenter Werra-Meißner	https://jobcenter-werra-meissner.de/geldleistungen/unterkunftskosten/	Webseite	Flyer KDU	HTML/PDF	–	Vergleichsraum	keine offene Lizenz	ja	nicht geprüft	zu prüfen	aktueller Flyer
kdu_merkblatt_wmk	Wohnen/Soziales	niedrig	Merkblatt Anmietung von Wohnraum	Kreisausschuss WMK	https://www.werra-meissner-kreis.de/fileadmin/01_Homepage_Kreisverwaltung/Fachbereiche_und_Einrichtungen/FB6_Soziales_und_Senioren/6.1_Sicherung_Aktivierung_der_Lebensgrundlagen/Merkblatt_KdU.pdf	PDF	–	PDF	–	Kreis	keine offene Lizenz	ja	nicht geprüft	teilweise	Verfahren
mischuv_2026	Wohnen/Recht	mittel	Entwurf Hessische Mieterschutzverordnung 2026	HMWVW	https://hessen.de/presse/mieterschutz-soll-auf-71-kommunen-wachsen	Webseite	Gebietskulisse	HTML	–	Gemeinde	amtliche Pressemitteilung	ja	geprüft 23.10.2026	verifiziert	nicht erfasst
gewos_2026	Wohnen	niedrig	GEWOS Ergebnisbericht 2026	HMWVW/GEWOS	https://hessen.de/sites/hessen.hessen.de/files/damlocalcopy/infop_document/2026_gewos_hessen_angespannte_wohnungsmaerkte_ergebnisbericht_final.pdf	PDF	–	PDF	–	Gemeinde	zu prüfen	ja	nicht geprüft	verifiziert	Indikatoren
immo_wmk_2023	Wohnen/Boden	mittel	Immobilienmarktbericht 2023 GAA Homberg (Efze) – Pressemitteilung	HVBG	https://hvbg.hessen.de/presse/immobilienmarktbericht-2023-online-verfuegbar-weniger-transaktionen	Webseite	–	HTML	–	Kreis	zu prüfen	ja	nicht geprüft	teilweise	Umsätze WMK
gemeindelexikon	Statistik	mittel	Gemeindedatenblatt Witzenhausen (636016)	Hessen Agentur/HSL	https://www.hessen-gemeindelexikon.de/gemeindelexikon_PDF/636016.pdf	PDF	–	PDF	–	Gemeinde	zu prüfen	ja	Abruf fehlgeschlagen 23.10.2026	teilweise	Bevölkerung/Prognose
gv_statistikportal	Statistik	mittel	Gemeindeverzeichnis 06636016	Statistische Ämter	https://www.statistikportal.de/de/gemeindeverzeichnis/06636016	Webseite	–	HTML	–	Gemeinde	zu prüfen	ja	nicht geprüft	verifiziert	Fläche/Einwohner
wahl_kw2026_vm	Wahlen	hoch	votemanager Kommunalwahl 15.03.2026	Stadt Witzenhausen/ekom21	https://votemanager-ks.ekom21cdn.de/2026-03-15/06636016/praesentation/index.html	Webseite	Gemeindewahl/Ortsbeiratswahl/Kreiswahl	HTML	–	Wahlbezirk/Ortsbezirk	zu prüfen	zu prüfen	Abruf verweigert 23.10.2026	teilweise	Ortsbeiratsergebnisse
wahl_kw2026_bek	Wahlen	hoch	Wahlbekanntmachung Nr. 013/2026	Stadt Witzenhausen	https://www.witzenhausen.eu/wp-content/uploads/2026/01/013-2026-Wahlbekanntmachung-Kommunalwahl-15-03-2026.pdf	PDF	–	PDF	–	Wahlbezirk	amtliche Bekanntmachung	nein	nicht geprüft	verifiziert	Wahlbezirkseinteilung
wahl_kw2021_vm	Wahlen	niedrig	votemanager Kommunalwahl 14.03.2021	Stadt Witzenhausen/ekom21	https://votemanager-ks.ekom21cdn.de/2021-03-14/06636016/html5/Kreiswahl_Hessen_362_Gemeinde_Stadt_Witzenhausen.html	Webseite	Bezirke 1–21, B99100–B99500	HTML	–	Wahlbezirk	zu prüfen	zu prüfen	nicht geprüft	verifiziert	Vergleichswahl
wahl_wahlraeume2016	Wahlen/Orte	mittel	Wahlraumübersicht 2016	Stadt Witzenhausen/ekom21	https://votemanager-ks.ekom21cdn.de/20160306/06636016/html5/Wahllokaluebersicht.html	Webseite	Wahlraum→Wahlbezirk→Ortsbezirk	HTML	–	Wahlbezirk	zu prüfen	zu prüfen	nicht geprüft	teilweise	Sitzungsorte
wahl_hessenschau	Wahlen	niedrig	Ergebnisseite Kommunalwahl 2026 Witzenhausen	hessenschau/HSL	https://www.hessenschau.de/politik/kommunalwahlen/ergebnisse/ergebnisse-witzenhausen---kommunalwahl-2026-v3,kw26-gemeinde-g06636016-100.html	Webseite	–	HTML	–	Gemeinde	keine offene Lizenz	ja	nicht geprüft	teilweise	Plausibilisierung
haushalt_stadt	Finanzen	mittel	Pläne/Berichte/Abschlüsse	Stadt Witzenhausen	https://www.witzenhausen.eu/plane-berichte-abschlusse/	PDF	Haushaltsplan 2026 u. a.	PDF	–	Gemeinde	amtliche Dokumente	nein	nicht geprüft	verifiziert	Haushaltskennzahlen
ortsbeiraete_seite	Verwaltung	mittel	Ortsbeiräte	Stadt Witzenhausen	https://www.witzenhausen.eu/ortsbeirate/	Webseite	–	HTML	–	Ortsbezirk	–	–	nicht geprüft	verifiziert	Verlinkung
nvv_gtfs	ÖPNV	hoch	Soll-Fahrplandaten NVV (GTFS)	NVV via OpenData ÖPNV/Mobilithek	https://mobilithek.info/offers/-1983289435982938851	Download	GTFS-ZIP	GTFS	WGS84	Haltestelle	freie Nutzung/Open Data (genau zu prüfen)	zu prüfen	nicht lesbar ohne JS 23.10.2026	teilweise	Haltestellen/Linien
oepnv_portal	ÖPNV	mittel	OpenData ÖPNV – Datensätze	OpenData ÖPNV	https://www.opendata-oepnv.de/ht/de/datensaetze	Download	Soll-Fahrplandaten NVV; NVV-Haltepositionen	GTFS/CSV	WGS84	Haltestelle	je Datensatz	je Datensatz	nicht geprüft	teilweise	Haltepositionen
schutzgeb_ogcapi	Natur	niedrig	Schutzgebiete Hessen als OGC API	HMLU/Geoportal Hessen	https://www.geoportal.hessen.de/spatial-objects/266	OGC API	Naturschutzgebiete u. a.	GeoJSON	WGS84	Gebiet	zu prüfen	zu prüfen	nicht geprüft	verifiziert	GeoJSON-Alternative
```

## Abrufbefehle (Priorität hoch)

**BORIS 2026 – Feed auflösen, dann GetFeature.** Der Feed verweist pro Objektart auf einen Dataset-Feed. Dessen `link`-Elemente enthalten die tatsächlichen GetFeature-URLs; die Basis-URL des WFS 732 ist daraus zu übernehmen und nicht zu raten.
```bash
curl -s "https://www.geoportal.hessen.de/mapbender/php/mod_inspireDownloadFeed.php?id=c1afe4df-1290-42b3-9399-6bfd00652c13&type=DATASET&generateFrom=wfs&wfsid=732&featuretypeid=5405" -o boris2026_zonal_feed.xml
grep -o 'href="[^"]*GetFeature[^"]*"' boris2026_zonal_feed.xml | head
# danach mit der ermittelten Basis-URL (WFS 2.0):
# ogr2ogr -f GeoJSON boris2026_wiz.geojson "WFS:<BASIS-URL>?SERVICE=WFS&VERSION=2.0.0" boris:BR_BodenrichtwertZonal \
#   -spat 548000 5680000 567000 5699000 -spat_srs EPSG:25832 -t_srs EPSG:4326
```
Danach mit der Gemeindegrenze aus `vg_shp` clippen (`-clipsrc`), denn die BBOX enthält Teile von Bad Sooden-Allendorf, Neu-Eichenberg und Niedersachsen/Thüringen.

**BORIS 2024 als OGC API (Vergleich).** Die Collection-ID ist auf der Landingpage zu prüfen:
```bash
curl -s "https://www.geoportal.hessen.de/spatial-objects/864/collections?f=json"
curl -s "https://www.geoportal.hessen.de/spatial-objects/864/collections/boris_BR_BodenrichtwertZonal/items?bbox=9.72,51.28,9.94,51.41&limit=1000&f=json" -o boris2024_wiz.geojson
```

**Zensus-Gitter.** Die ZIPs von der Zensus-Seite laden, dann die 100-m-CSV filtern. Die Spaltennamen der Gitterkoordinaten (Mittelpunkt in EPSG:3035) gemäß Datensatzbeschreibung prüfen. Gebräuchlich sind `GITTER_ID_100m`, `x_mp_100m`, `y_mp_100m`; das ist für 2022 nicht verifiziert.
```bash
ogr2ogr -f GPKG zensus_miete_wiz.gpkg Zensus2022_Durchschn_Nettokaltmiete_100m-Gitter.csv \
  -oo X_POSSIBLE_NAMES=x_mp_100m -oo Y_POSSIBLE_NAMES=y_mp_100m -a_srs EPSG:3035 -s_srs EPSG:3035 -t_srs EPSG:25832 \
  -clipsrc gemeinde_witzenhausen_25832.gpkg -oo SEPARATOR=SEMICOLON
```
(Der Dateiname im ZIP ist zu prüfen; Kennzeichen für Geheimhaltung wie „–“ als Null behandeln.)

**Wahlbekanntmachungen über die WordPress-API** (bekannte Quelle `wp_media`):
```bash
curl -s "https://www.witzenhausen.eu/wp-json/wp/v2/media?search=Wahlbekanntmachung&per_page=100" | jq '.[]|{date,source_url}'
curl -s "https://www.witzenhausen.eu/wp-json/wp/v2/media?search=Wahlergebnis&per_page=100" | jq '.[]|{date,source_url}'
```

**NVV-GTFS:** Der Download erfolgt über das Konto auf opendata-oepnv.de (Registrierung). Danach Haltestellen auf Witzenhausen begrenzen:
```bash
unzip nvv_gtfs.zip stops.txt
awk -F',' 'NR==1 || ($5+0>=51.28 && $5+0<=51.41 && $6+0>=9.72 && $6+0<=9.94)' stops.txt > stops_wiz.txt
# Spaltenpositionen stop_lat/stop_lon vorher im Header prüfen
```

**Overpass (OSM, Relation 549412 → area 3600549412):**
```
[out:json][timeout:120];
area(3600549412)->.wiz;
(
  nwr["amenity"~"^(school|kindergarten|pharmacy|doctors|hospital|fire_station|library|community_centre|townhall|grave_yard)$"](area.wiz);
  nwr["leisure"~"^(playground|sports_centre|pitch|swimming_pool)$"](area.wiz);
  nwr["landuse"="cemetery"](area.wiz);
  nwr["amenity"="recycling"](area.wiz);
  nwr["highway"="bus_stop"](area.wiz);
);
out center tags;
```

**Wikidata (Items in Witzenhausen und seinen Ortsteilen, transitiv über P131):**
```sparql
SELECT ?item ?itemLabel ?typLabel ?coord WHERE {
  ?item wdt:P131* wd:Q564827 .
  OPTIONAL { ?item wdt:P31 ?typ . }
  OPTIONAL { ?item wdt:P625 ?coord . }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "de". }
}
```

## Kernzahlen Witzenhausen

| Kennzahl | Wert | Stichtag | Quelle / Belegqualität |
|---|---|---|---|
| Fläche | 126,78 km² | Gemeindeverzeichnis | Statistikportal (amtlich)\[23\] |
| Einwohner (Zensus) | 15.162 | 15.05.2022 | Zensus 2022, über Sekundärauswertungen; Primärprüfung offen\[4\]\[24\] |
| Einwohner (Fortschreibung) | 15.132 (7.539 m / 7.593 w)\[25\] | vermutl. 31.12.2024 (Seite „Stand 31.03.2026“) | Statistikportal; Stichtag zu klären\[23\] |
| Einwohner (HSL) | ca. 15.100 | 31.12.2024 | Gemeindedatenblatt Hessen Agentur\[15\] |
| Nettokaltmiete | 5,09 €/m² | 15.05.2022 | Zensus 2022 (sekundär, zwei übereinstimmende Quellen)\[4\] |
| Eigentümerquote | 54,4 % | 15.05.2022 | wie oben\[4\] |
| Leerstandsquote | 4,6 % (369 Wohnungen)\[5\] | 15.05.2022 | wie oben\[4\] |
| Vermietete Wohnungen | 3.551 | 15.05.2022 | wie oben\[4\] |
| Ø Wohnfläche je Wohnung | 104,1 m² | 15.05.2022 | sekundär (strassenkatalog.de) |
| Wohngeld-Mietenstufe | I | ab 01.01.2023 | Anlage WoGV (amtlich) |
| KdU Vergleichsraum I (1/2/3/4/5 Pers./je weitere) | 357,24 / 399,36 / 497,80 / 551,76 / 616,00 / +73,92 €\[26\] | 01.01.2023 | Jobcenter-Flyer (Kopie); Aktualität offen |
| Mieterschutzverordnung | nicht erfasst (weder geltend noch Entwurf 2026)\[13\] | 24.09.2026 | HMWVW |
| Zentralörtliche Funktion | Mittelzentrum im ländlichen Raum mit Verdichtungsansätzen | 2025 | Hessen Agentur\[15\] |
| Kommunalwahl 2026 StVV (Sitze von 37) | SPD 10 (27,45 %), CDU 8 (21,80 %), GRÜNE 7 (17,58 %), Linke 5 (14,03 %), FWG 4 (10,06 %), FDP 3 (9,08 %); Beteiligung 61,97 %\[27\]\[28\] | 15.03.2026 | SPD Witzenhausen (20.03.2026, vermutl. vorläufig); Sitze SPD/CDU/FDP durch Werra-Rundschau bestätigt |
| Wahlbezirke | 21 Urnen- und 5 Briefwahlbezirke | 15.03.2026 | Wahlbekanntmachung 013/2026 |
| Bodenrichtwert-Spannen, Kaufpreisniveau, Hebesätze | nicht belegt | – | siehe Lücken |

Einordnung: Eine Nettokaltmiete von 5,09 €/m² im Bestand und Mietenstufe I bestätigen ein niedriges Mietniveau. Das ist konsistent mit dem Ausschluss aus der Mieterschutzkulisse. Ein Leerstand von 4,6 % liegt leicht über dem Bundeswert von 4,3 %, den Destatis in der Pressemitteilung Nr. 46 vom 4. Juli 2024 für den Zensus 2022 meldet („Bundesweit standen am 15. Mai 2022 rund 1,9 Millionen Wohnungen leer“), und nahe am Wert von 4,7 %, den die Statistischen Ämter für westdeutsche ländliche Kreise mit Verdichtungsansätzen ausweisen (über Statista, Nov. 2024). Für die Karte ist deshalb die Leerstandsquote im 100-m-Gitter der aussagekräftigste Wohnindikator je Ortsteil.

## Lizenz- und Attributionsübersicht (neue Quellen)

- **BORIS (alle Stichtage), HVBG:** Datenlizenz Deutschland – Zero 2.0.\[2\] Keine Attributionspflicht; empfohlen: „Bodenrichtwerte: Gutachterausschüsse für Immobilienwerte in Hessen / HVBG, Stichtag 01.01.2026“.
- **Zensus 2022 (Gitter, Gemeindewerte):** Datenlizenz Deutschland – Namensnennung 2.0 (DL-DE BY 2.0), bestätigt durch Destatis („Die hier angebotenen Geodaten stehen gemäß der Open Data Datenlizenz Deutschland – Namensnennung – Version 2.0 zum Download und zur Online-Nutzung zur Verfügung“) und durch die Zensusdatenbank („Datenlizenz DL-DE->BY-2.0“). Attribution erforderlich: „© Statistische Ämter des Bundes und der Länder, Zensus 2022“.
- **WoGV-Anlage, Wahlbekanntmachungen, Haushaltsdokumente, Pressemitteilung HMWVW:** amtliche Werke bzw. amtliche Bekanntmachungen; Quellenangabe empfohlen.
- **KdU-Flyer, Merkblatt WMK, Immobilienmarktbericht, hessenschau:** keine offene Lizenz. Nur Kennzahlen mit Quellenangabe übernehmen, keine Dokumente spiegeln.
- **NVV-GTFS:** Mobilithek nennt „Lizenz, freie Nutzung/Open Data“; der genaue Lizenztext (vermutlich CC BY 4.0 oder DL-DE) ist auf opendata-oepnv.de nach Anmeldung zu verifizieren.\[29\]
- **Esri-Zensus-FeatureServer:** Drittanbieter-Aufbereitung; laut Esri-Deutschland-Item „Zensus2022 100mGitter“ unter DL-DE BY 2.0 mit der Attribution „© Statistische Ämter des Bundes und der Länder, 2024; Gittergeometrien: © GeoBasis-DE / BKG (2024)“. Nur als Fallback.
- **votemanager:** keine Lizenzangabe gefunden. Technisch ist der automatisierte Abruf nach den Erfahrungen dieser Recherche gesperrt.

## Lücken, Widersprüche und Prüfbedarf

1. **votemanager ist für die Pipeline voraussichtlich nicht crawlbar.** Ein automatisierter Abruf auf ekom21cdn.de wurde mit „Site disallows automated access“ abgelehnt. Vor jedem Einsatz `robots.txt` des Hosts prüfen und analog zu SessionNet behandeln. Die Open-Data-CSV-Namen (`opendata-wahllokale.csv`, `opendata-strassen.csv`) sind nur von anderen Kommunen belegt.\[21\]\[22\] Alternative: die amtliche Bekanntmachung des endgültigen Wahlergebnisses (PDF) über `wp_media` oder eine Anfrage beim Wahlamt der Stadt (Rathaus, Am Markt 1).
2. **Wahlergebnis 2026:** Die Stimmenanteile stammen aus einer Parteiquelle vom 20.03.2026 und geben wahrscheinlich das vorläufige Ergebnis wieder.\[28\] Die Sitzzahlen sind teilweise unabhängig bestätigt.\[27\] Endgültige Zahlen per Bekanntmachung verifizieren.\[25\]
3. **Wahlbezirk → Ortsbezirk:** Die Zuordnung ist nur aus 2016 belegt. Damals fehlte Ermschwerd und Hubenrode die Ortsbezirksangabe; Wendershausen wählte im Gemeinschaftshaus Werleshausen.\[30\] Für 2026 ist die Zuordnung offen. Gibt es 21 Urnenbezirke bei 16 Ortsbezirken plus 5 Kernstadtbezirken, ergäbe sich 1:1 je Ortsbezirk. Das ist rechnerisch plausibel, aber unbelegt.
4. **Hauptsatzung § 6 (Ortsbezirke):** Der Wortlaut wurde nicht gefunden. Er ist über die Seite „Satzungen & Ortsrecht“ auf witzenhausen.eu bzw. `wp_media` (Suche „Hauptsatzung“) zu beschaffen. Davon hängen die Abgrenzung Kernstadt/Bischhausen und die Zuordnung Hübenthal zu Berlepsch-Ellerode ab. Ein Abgleich mit den 17 Gemarkungen aus `vg_shp` ist nötig: 16 Ortsbezirke plus Kernstadt ergäben 17, was aufginge, wenn Bischhausen und Hübenthal keine eigenen Gemarkungen sind. Das ist unbestätigt.
5. **KdU:** Der letzte belegte Stand ist der 01.01.2023.\[26\] Der Kreis hat DOMUS Consult (Hamburg) mit der Fortschreibung des schlüssigen Konzepts beauftragt; der Stand ist unbekannt.\[31\] Zuständig sind das Jobcenter Werra-Meißner (Standort Walburger Straße 41, Witzenhausen) bzw. der Fachbereich 6 der Kreisverwaltung.\[26\]
6. **Immobilienmarktbericht:** Nur die Ausgabe 2023 ist belegt (1.787 Kauffälle im WMK).\[32\] Aktuelle Ausgabe und Witzenhausen-Kennzahlen bei der Geschäftsstelle des Gutachterausschusses im AfB Homberg (Efze) anfragen. Das HVBG bietet zusätzlich generalisierte Bodenwert-Übersichten je Landkreis im Downloadcenter von gds.hessen.de an.\[8\]
7. **BORIS 2026:** Ob der WFS mit Geoportal-ID 732 den Stichtag 2026 ausliefert, ist aus dem Feed allein nicht gesichert; die Metadaten (2026–2027) sprechen dafür.\[9\] Die Prüfung erfolgt durch Abruf von `boris:BR_BodenrichtwertZonal` und das Stichtagsattribut. Die Bodenrichtwert-Spannen für Witzenhausen lassen sich danach direkt aus den Daten ableiten.
8. **Hebesätze, GENESIS-Tabellencodes, Baufertigstellungen:** In diesem Durchgang nicht belegt. Nächster Schritt: Regionaldatenbank Deutschland bzw. GENESIS-Online des HSL, Suche nach AGS 06636016.
9. **Nicht recherchierte Fachthemen (Status „zu prüfen“, keine URL ins Register übernommen):** Regionalplan Nordhessen und Teilregionalplan Energie (RP Kassel), Lärmkartierung und Starkregenhinweiskarte (HLNUG), DenkXweb (Landesamt für Denkmalpflege Hessen), Ladesäulen- und Marktstammdatenregister (BNetzA), Radnetz Hessen (Hessen Mobil), Schulen/Kitas, LAGIS-Ortslexikon, Feldblöcke/InVeKoS. Hier dürfen keine URLs aus dem Gedächtnis eingesetzt werden; jede Quelle ist einzeln nachzuweisen.
10. **Bahnhof Eichenberg:** Er liegt in der eigenständigen Gemeinde Neu-Eichenberg, die in der KdU-Vergleichsraumliste getrennt geführt wird.\[26\] Er gehört daher nicht zum Gemeindegebiet; die genaue Lage ist nicht separat geprüft.

## Recommendations

1. **Sofort übernehmen:** `boris2026_feed` (nach Auflösung der GetFeature-URL), `wogv_anlage`, `mischuv_2026` (als Statusfeld „Mieterschutz: nein“), `wahl_kw2026_bek` und `haushalt_stadt`. Alle sind belegt und ohne Anmeldung zugänglich.
2. **Als Nächstes:** die Zensus-Gitter (Miete, Leerstand, Eigentum, Alter). Sie geben den Ortsbeiratsflächen eine echte Binnendifferenzierung. Die Lizenz (DL-DE BY 2.0) ist belegt; vorher nur noch die Spaltennamen anhand der Datensatzbeschreibung festschreiben.
3. **Wahlen nicht über votemanager automatisieren.** Stattdessen die Ergebnisbekanntmachungen als PDF über `wp_media` parsen und die Zuordnung Wahlbezirk → Ortsbezirk einmalig manuell aus der Wahlbekanntmachung bzw. einer Anfrage beim Wahlamt pflegen.
4. **Anfragen bündeln** (eine E-Mail an die Stadt, eine an den Kreis): Hauptsatzung, Wahlbezirkseinteilung 2026, Abgrenzung des Sanierungs- bzw. Stadtumbaugebiets als Geodatum, aktuelle KdU-Werte und den Immobilienmarktbericht.

## Caveats

- Mehrere Kennzahlen (Zensus-Gemeindewerte, Wahlergebnis 2026) beruhen auf Sekundärquellen. Sie sind im Register als „teilweise“ markiert und vor Veröffentlichung gegen die Primärquellen zu prüfen.
- Der Status „geprüft“ ist nur dort vergeben, wo in dieser Recherche tatsächlich abgerufen wurde (BORIS-Feed, Pressemitteilung HMWVW). Alle übrigen Einträge sind „nicht geprüft“.
- Die Mieterschutzverordnung ist ein Entwurf; die Gebietskulisse kann sich bis zum Kabinettsbeschluss (erwartet Mitte November 2026) noch ändern. Eine Aufnahme Witzenhausens ist nach Datenlage aber unwahrscheinlich.

## Quellen

1. [Geoportal Hessen - Meldungen](https://www.geoportal.hessen.de/article/Meldungen/)
2. [Metadata - Geoportal Hessen](https://www.geoportal.hessen.de/mapbender/php/mod_showMetadata.php?languageCode=en&resource=wmc&layout=tabs&id=8243)
3. [INSPIRE Download Service Feed für BORIS Hessen](https://www.geoportal.hessen.de/mapbender/php/mod_inspireDownloadFeed.php?id=c1afe4df-1290-42b3-9399-6bfd00652c13&amp=&type=SERVICE&amp=&generateFrom=wfs&amp=&wfsid=732)
4. [Witzenhausen : Zensus 2022](https://wahlatlas.net/experimente/zensus2022/gemeinden/066360016016.html)
5. [Witzenhausen - Straßen, PLZ und Wohnqualität](https://strassenkatalog.de/ort/witzenhausen-witzenhausen-stadt.html)
6. <https://www.witzenhausen.eu/wp-content/uploads/2026/01/013-2026-Wahlbekanntmachung-Kommunalwahl-15-03-2026.pdf>
7. [gis.Point - Das Portal für Geoinformation und Geodäsie - News Einzelansicht](https://gispoint.de/news-einzelansicht/200004847-bodenrichtwerte-fuer-hessen-online.html)
8. [Geobranchen.de - Das Portal rund um GIS, GISnews, Geonews, Geoinformatik, Geographie, Geodaten, Geobusiness, Geowissenschaft, CAD - Hessische Bodenrichtwerte 2026 sind online](https://www.geobranchen.de/mediathek/geonews/item/hessische-bodenrichtwerte-2026-sind-online)
9. [AdV-MIS - BORIS Hessen](https://advmis.geodatenzentrum.de/trefferanzeige?docuuid=c1afe4df-1290-42b3-9399-6bfd00652c13)
10. [Offene Geodaten des Landes Hessen](https://www.geoportal.hessen.de/spatial-objects/864)
11. [Offene Geodaten des Landes Hessen](https://www.geoportal.hessen.de/spatial-objects/731)
12. [Basis der Bodenwertermittlung](https://hvbg.hessen.de/immobilienwertermittlung/bodenrichtwerte)
13. [Mieterschutz soll auf 71 Kommunen wachsen](https://hessen.de/presse/mieterschutz-soll-auf-71-kommunen-wachsen)
14. [Hessen Mietpreisbremse: 71 Gemeinden im Entwurf 2026](https://hausbesitzer-news.de/immobilie-eigentum/hessen-mieterschutzverordnung-71-gemeinden-mietpreisbremse/)
15. [Gemeindedatenblatt: Witzenhausen, St. (636016)](https://www.hessen-gemeindelexikon.de/gemeindelexikon_PDF/636016.pdf)
16. [Kommunalwahl 2026 - Stadt Witzenhausen](https://www.witzenhausen.eu/kommunalwahl-2026/)
17. [Kreiswahl - Kommunalwahlen 2016 in der Stadt Witzenhausen - Gesamtergebnis](https://votemanager-ks.ekom21cdn.de/20160306/06636016/html5/Kreiswahl_Hessen_24_Gemeinde_Stadt_Witzenhausen.html)
18. [Kreiswahl - Kommunalwahl 14.03.2021 2021 in der Stadt Witzenhausen - Gesamtergebnis](https://votemanager-ks.ekom21cdn.de/2021-03-14/06636016/html5/Kreiswahl_Hessen_362_Gemeinde_Stadt_Witzenhausen.html)
19. [Ortsbeiratswahl - Kommunalwahlen 2011 in der Stadt Witzenhausen - Gesamtergebnis](https://votemanager-ks.ekom21cdn.de/20110327/06636016/html5/Ortsbeiratswahl_Hessen_87_Gemeinde_Stadt_Witzenhausen.html)
20. [Kreiswahl - Kommunalwahlen 2016 in der Stadt Witzenhausen - Wahlbezirk Wendershausen](https://votemanager-ks.ekom21cdn.de/20160306/06636016/html5/Kreiswahl_Hessen_24_Wahlbezirk_Wendershausen.html)
21. [OpenData CSV-Dateien](https://votemanager-ks.ekom21cdn.de/2021-09-26/06611000/praesentation/opendata.html)
22. [Kommunalwahlen 2021 in der - OpenData CSV-Dateien](https://votemanager-da.ekom21cdn.de/2021-03-14/06440017/html5/OpenDataInfo.html)
23. [06636016](https://www.statistikportal.de/de/gemeindeverzeichnis/06636016)
24. [Witzenhausen (Hessen, Zensusbevölkerung, Deutschland) - Einwohnerzahlen, Grafiken, Karte, Lage, Wetter und Web-Informationen](https://citypopulation.de/de/germany/census/hessen/06636016__witzenhausen/)
25. [Kommunalwahl-Ergebnisse 2026: So hat Witzenhausen gewählt](https://www.hessenschau.de/politik/kommunalwahlen/ergebnisse/ergebnisse-witzenhausen---kommunalwahl-2026-v3,kw26-gemeinde-g06636016-100.html)
26. [Innerhalb des Werra-Meißner-Kreises](https://harald-thome.de/files/pdf/KdU%20New/KdU%20Werra-Mei%C3%9Fner%20Kreis%20-%2001.01.2023.pdf)
27. [Neue Koalition: FDP schließt sich in Witzenhausen Rot-Schwarz an](https://www.werra-rundschau.de/lokales/kreisteil-witzenhausen/neue-koalition-fdp-schliesst-sich-in-witzenhausen-rot-schwarz-an-94264463.html)
28. [SPD Witzenhausen Webseite](https://www.spd-witzenhausen.de/ortsverband.html)
29. [Soll-Fahrplandaten NVV](https://mobilithek.info/offers/-1983289435982938851)
30. [Kommunalwahlen 2016 in der Stadt Witzenhausen - Wahlraumübersicht](https://votemanager-ks.ekom21cdn.de/20160306/06636016/html5/Wahllokaluebersicht.html)
31. [Pressemitteilung des Werra-Meißner-Kreises - Stadt Witzenhausen](https://www.witzenhausen.eu/aktuelle-ereignisse/pressemitteilung-des-werra-meissner-kreises-3/)
32. [Immobilienmarktbericht 2023 online verfügbar](https://hvbg.hessen.de/presse/immobilienmarktbericht-2023-online-verfuegbar-weniger-transaktionen)
