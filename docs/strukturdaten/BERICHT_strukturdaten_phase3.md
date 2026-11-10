# Strukturdaten Witzenhausen – Bericht Phase 3 (Anzeige)

> Stand 10.11.2026 · liest ausschließlich `data/strukturdaten/` (Datenvertrag „Strukturdaten v1“)

## Umgesetzt

- **Fenster „Strukturdaten“** (Menü „Sitzungen“, Karte „Strukturdaten“):
  - Werte des gewählten Ortsteils neben dem Wert der Stadt aus derselben Quelle, mit Stichtag und der Marke „abgeleitet“ im Spaltenkopf.
  - Je Merkmal eine aufklappbare Erläuterung mit Metatext, Quelle, Jahr und Lizenz.
  - Unter der Schwelle steht „nicht ausgewiesen (zu wenige Angaben oder Geheimhaltung)“, bei Geheimhaltung „nicht veröffentlicht (statistische Geheimhaltung)“.
  - Sortierbare Tabelle aller Ortsbezirke (`aria-sort`, Fokus bleibt beim Sortieren erhalten). Voreingestellt ist die Sortierung nach Namen, damit keine Rangfolge entsteht.
  - Vergleich mit den Kommunen des Demografietyps: zwölf Kennzahlen im jüngsten Jahr, der Verlauf der Stadt als kleine Linie, Hinweis auf abweichende Definitionen und Stichtage.
  - Unter „Methode und Quellen“: Übertragung, Schwelle, keine Rangfolge, Datenstand, Quellen mit Lizenz.
- **Kartenebene** „Strukturdaten der Ortsbezirke (Zensus 2022)“ unter „Weitere Ebenen“:
  - Standardmäßig aus, liegt unter den Vorgängen. Nur Anteile und Mittelwerte; absolute Zahlen nur im Fenster.
  - Fünf Quantilklassen als Voreinstellung, umschaltbar auf feste Grenzen über alle Jahre. Farben ColorBrewer BuPu (sequenziell, für Farbfehlsichtige unterscheidbar).
  - Nicht ausgewiesene Flächen neutral mit gestricheltem Rand.
  - Die Legende enthält die Auswahl von Merkmal und Klassen, das Jahr, die Raumeinheit, den Hinweis zum ökologischen Fehlschluss und den Knopf „Als Tabelle“.
  - Ein Klick auf eine Fläche wählt den Ortsteil. Die Ebene lässt sich verlinken (`ebenen=strukturdaten`).
- **Vorgang:** Bei Vorgängen mit Ortsbezug steht ein kurzer Kasten mit Einwohnern und dem Anteil ab 65 je Ortsteil, dazu der Hinweis, dass kein Bezug zum Inhalt besteht, und ein Verweis auf das Fenster.
- **Fußzeile:**
  - Unter „Quellen, Lizenzen und Datenstand“ stehen der Datenstand der Strukturdaten und die Namensnennung des Wegweisers.
  - Die Karte „Wohnen und Boden“ nennt die Eigentümerquote nur noch für die Stadt.
- **Tests:** ein neuer Browsertest (Fenster, Sortierung, Erläuterung, Karte, Legende, Klassen, Tabelle, Vorgang, Barrierefreiheit mit axe). Außerdem ist ein Wettlauf im Test der Kartenseite behoben: Er las die Statusmeldung, bevor die Datei gelesen war.

## Offen (Phase 4, Verifikation)

- Stichprobe von 20 Werten gegen die Originalquellen (`audit_verifikation.tsv`).
- Anteil der Wohnungen in Ein- und Zweifamilienhäusern: Abweichung zwischen Zensus 2022 (59,2 %) und Wegweiser (72,4 %) klären.
- Berlepsch-Ellerode vor Ort plausibilisieren.
- Lizenzhinweise in README, Fußzeile und `data/LICENSE-DATA.md` auf Vollständigkeit prüfen.
