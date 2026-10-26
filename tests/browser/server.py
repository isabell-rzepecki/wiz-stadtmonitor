"""Statischer Testserver mit HTTP-Range-Abfragen (wie GitHub Pages), damit PMTiles-Kacheln im Browsertest laden.

Aufruf: python3 tests/browser/server.py PORT VERZEICHNIS
"""
import functools
import http.server
import os
import re
import sys


class RangeHandler(http.server.SimpleHTTPRequestHandler):
    def send_head(self):
        bereich = self.headers.get("Range")
        pfad = self.translate_path(self.path)
        m = re.fullmatch(r"bytes=(\d+)-(\d*)", bereich or "")
        if not m or not os.path.isfile(pfad):
            return super().send_head()
        groesse = os.path.getsize(pfad)
        start, ende = int(m.group(1)), min(int(m.group(2) or groesse - 1), groesse - 1)
        if start >= groesse:
            self.send_error(416)
            return None
        f = open(pfad, "rb")
        f.seek(start)
        self.send_response(206)
        self.send_header("Content-Type", self.guess_type(pfad))
        self.send_header("Content-Range", f"bytes {start}-{ende}/{groesse}")
        self.send_header("Content-Length", str(ende - start + 1))
        self.send_header("Accept-Ranges", "bytes")
        self.end_headers()
        self._rest = ende - start + 1
        return f

    def copyfile(self, source, outputfile):
        rest = getattr(self, "_rest", None)
        if rest is None:
            return super().copyfile(source, outputfile)
        outputfile.write(source.read(rest))
        self._rest = None


if __name__ == "__main__":
    port, verzeichnis = int(sys.argv[1]), sys.argv[2]
    handler = functools.partial(RangeHandler, directory=verzeichnis)
    http.server.ThreadingHTTPServer(("127.0.0.1", port), handler).serve_forever()
