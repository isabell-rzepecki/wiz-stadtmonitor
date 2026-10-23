"""Aufruf: python -m pipeline {site}"""
import sys

from . import site

STEPS = {
    "site": site.build,  # Seite in _site/ zusammenstellen (site/, stadt.json, data/export/)
}


def main(argv):
    if len(argv) != 1 or argv[0] not in STEPS:
        raise SystemExit(__doc__)
    print(f"== {argv[0]}", flush=True)
    STEPS[argv[0]]()


main(sys.argv[1:])
