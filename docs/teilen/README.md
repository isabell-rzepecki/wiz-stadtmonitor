# Material zum Teilen

Die Bilder liegen auf der Seite selbst unter **/teilen/** (`site/teilen/`): Motive quer, quadratisch, Story und Banner
als PNG, JPG und JPG in doppelter Auflösung, dazu Wort- und Bildmarke, das Vorschaubild für Links, ein kurzer Text,
ein Alt-Text und die Quellenangaben.

Neu erzeugen (zum Beispiel nach Änderungen an der Seite):
`NODE_PATH=tests/browser/node_modules node tools/teilmaterial.mjs`. Die Rohaufnahmen landen in `docs/teilen/.roh/`
und werden nicht eingecheckt. Das Vorschaubild entsteht aus `tools/vorschaubild.py`.
