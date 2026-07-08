from __future__ import annotations

from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from repo_scout.cli import main


class CliTests(unittest.TestCase):
    def test_cli_can_emit_json_snapshot(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "README.md").write_text("# Example\n", encoding="utf-8")

            stdout = io.StringIO()
            with redirect_stdout(stdout):
                exit_code = main(["--format", "json", str(root)])

            self.assertEqual(exit_code, 0)
            snapshot = json.loads(stdout.getvalue())
            self.assertEqual(snapshot["root"], str(root.resolve()))
            self.assertEqual(snapshot["files"]["total"], 1)
            self.assertEqual(snapshot["docs"]["present"], ["README.md"])

    def test_cli_applies_repeated_ignore_patterns(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "README.md").write_text("# Example\n", encoding="utf-8")
            (root / "debug.log").write_text("noisy\n", encoding="utf-8")
            (root / "private").mkdir()
            (root / "private" / "note.txt").write_text("secret\n", encoding="utf-8")

            stdout = io.StringIO()
            with redirect_stdout(stdout):
                exit_code = main(
                    [
                        "--format",
                        "json",
                        "--ignore",
                        "*.log",
                        "--ignore",
                        "private",
                        str(root),
                    ]
                )

            self.assertEqual(exit_code, 0)
            snapshot = json.loads(stdout.getvalue())
            self.assertEqual(snapshot["files"]["total"], 1)
            self.assertEqual(snapshot["filters"]["ignored"], ["*.log", "private"])


if __name__ == "__main__":
    unittest.main()
