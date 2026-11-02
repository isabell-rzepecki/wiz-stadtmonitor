"""Quellwache im Workflow: neue Lücken oder Warnungen öffnen bzw. aktualisieren ein Issue, ohne neue Funde wird es
geschlossen. Aufruf: python3 tools/quellwache_issue.py data/export/quellwache.json (braucht gh und GH_TOKEN).
Ohne gh oder Token nur Ausgabe des Texts (Probe: --nur-text)."""
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STADT = json.loads((ROOT / "config" / "stadt.json").read_text(encoding="utf-8"))
TITEL = STADT["quellwache"]["issue_titel"]
MARKE = "<!-- quellwache -->"


def text(q):
    zeilen = [MARKE, f"Stand: {q['stand']}. Erzeugt von der täglichen Quellwache (`pipeline/quellwache.py`).", ""]
    if q["warnungen"]:
        zeilen += ["## Warnungen", *[f"- {w}" for w in q["warnungen"]], ""]
    neu = [x for x in q["luecken"] if x["neu"]]
    if neu:
        zeilen += ["## Neue Lücken", "Erwähnte Sitzungen ohne Einladung in den amtlichen Bekanntmachungen:", ""]
        zeilen += [f"- {x['datum']} · {x['gremium']} · {x['grund']} ([Nr. {x['fundstelle']}]({x['pdf']}))" for x in neu]
        zeilen += ["", "Ist die Lücke geklärt oder dauerhaft (die Stadt veröffentlicht die Einladung nicht), Datum und Gremium in "
                   "`config/quellwache_bekannt.tsv` eintragen; dann schließt der nächste Lauf dieses Issue."]
    return "\n".join(zeilen) + "\n"


def gh(*args):
    return subprocess.run(["gh", *args], check=True, capture_output=True, text=True).stdout


def main(argv):
    q = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    body = text(q)
    if "--nur-text" in argv or not shutil.which("gh"):
        print(body)
        return 0
    offen = [i for i in json.loads(gh("issue", "list", "--state", "open", "--search", f"in:title {TITEL}", "--json", "number,title,body"))
             if i["title"] == TITEL]
    if q["neu"]:
        if offen:
            if offen[0]["body"].strip() != body.strip():
                gh("issue", "edit", str(offen[0]["number"]), "--body", body)
                print(f"Issue #{offen[0]['number']} aktualisiert")
        else:
            print(gh("issue", "create", "--title", TITEL, "--body", body).strip())
    elif offen:
        gh("issue", "close", str(offen[0]["number"]), "--comment", "Quellwache: keine neuen Lücken und keine Warnungen mehr.")
        print(f"Issue #{offen[0]['number']} geschlossen")
    else:
        print("Quellwache: nichts Neues")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
