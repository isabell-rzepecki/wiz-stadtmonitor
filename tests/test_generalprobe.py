"""Generalprobe (Issue 53): die ganze Kette läuft mit Wegwerf-Schlüssel durch und lässt das Repository unverändert."""
import contextlib
import io
import subprocess
import sys
import unittest

from pipeline import config

sys.path.insert(0, str(config.ROOT / "tools"))
import generalprobe  # noqa: E402


class Generalprobe(unittest.TestCase):
    def test_alle_schritte_bestanden_repository_unveraendert(self):
        vorher = (config.ROOT / "config" / "stadt.json").read_bytes()
        status = lambda: subprocess.run(["git", "status", "--porcelain", "--untracked-files=all"], cwd=config.ROOT,  # noqa: E731
                                        capture_output=True, text=True).stdout
        git_vorher = status()
        aus = io.StringIO()
        with contextlib.redirect_stdout(aus), contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(generalprobe.main(["--schnell"]), 0, aus.getvalue())
        text = aus.getvalue()
        self.assertEqual(text.count("\nok "), 10, text)
        self.assertNotIn("FEHLER", text)
        self.assertEqual((config.ROOT / "config" / "stadt.json").read_bytes(), vorher)
        self.assertEqual(status(), git_vorher)


if __name__ == "__main__":
    unittest.main()
