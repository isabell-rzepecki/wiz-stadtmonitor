# Material zum Teilen

Bilder für Beiträge, Storys, Präsentationen und Profilbanner. Sie zeigen echte Ansichten der veröffentlichten Seite
(nur öffentliche Inhalte), die sich auf dem Korallgrund mit den Umrissen der Ortsbezirke überlagern.

| Datei | Größe | Gedacht für |
|---|---|---|
| `teilen-quer.png` | 1600 × 900 | Beiträge quer (Mastodon, LinkedIn, Facebook), Präsentationen |
| `teilen-quadrat.png` | 1080 × 1080 | Beiträge quadratisch (Instagram, Mastodon) |
| `teilen-story.png` | 1080 × 1920 | Storys und Status (Instagram, WhatsApp) |
| `teilen-banner.png` | 1500 × 500 | Profilbanner |
| `../../site/og-bild.png` | 1200 × 630 | Vorschau beim Teilen eines Links (Open Graph); die Seite bindet es selbst ein |

**Bildbeschreibung (Alt-Text), zum Mitkopieren:**
Stadtmonitor Witzenhausen: Ansichten der Seite auf Computer und Handy, mit der Karte der Ortsbezirke, der Zeitleiste
der Beratungen und den Gebäuden der Kernstadt in 3D.

**Quellen:** Die Quellenzeile steht in jedem Bild und soll beim Zuschneiden erhalten bleiben: Karten © basemap.de /
BKG (CC BY 4.0), © GeoBasis-DE; Gebäude © HVBG, ALKIS vereinfacht, LoD2; Ortsbezirke HVBG (dl-de/zero-2.0).

**Neu erzeugen** (zum Beispiel nach Änderungen an der Seite): `NODE_PATH=tests/browser/node_modules node tools/teilmaterial.mjs`.
Das Vorschaubild entsteht aus `tools/vorschaubild.py`.
