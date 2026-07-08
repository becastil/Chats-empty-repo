from __future__ import annotations

from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from repo_scout.scanner import scan_project


class ScanProjectTests(unittest.TestCase):
    def test_scan_project_counts_files_extensions_and_docs(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "README.md").write_text("# Example\n", encoding="utf-8")
            (root / "LICENSE").write_text("MIT\n", encoding="utf-8")
            (root / "pyproject.toml").write_text("[project]\n", encoding="utf-8")
            (root / "src").mkdir()
            (root / "src" / "app.py").write_text("print('hi')\n", encoding="utf-8")
            (root / ".git").mkdir()
            (root / ".git" / "ignored").write_text("ignore me\n", encoding="utf-8")

            snapshot = scan_project(root)

            self.assertFalse(snapshot["git"]["is_repo"])
            self.assertEqual(snapshot["files"]["total"], 4)
            self.assertEqual(snapshot["files"]["by_extension"][".md"], 1)
            self.assertEqual(snapshot["files"]["by_extension"][".py"], 1)
            self.assertEqual(snapshot["files"]["by_extension"][".toml"], 1)
            self.assertEqual(snapshot["files"]["by_extension"]["[no extension]"], 1)
            self.assertIn("README.md", snapshot["docs"]["present"])
            self.assertIn("CHANGELOG.md", snapshot["docs"]["missing"])

    def test_scan_project_applies_extra_ignore_patterns(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "README.md").write_text("# Example\n", encoding="utf-8")
            (root / "debug.log").write_text("debug\n", encoding="utf-8")
            (root / "private").mkdir()
            (root / "private" / "note.txt").write_text("secret\n", encoding="utf-8")

            snapshot = scan_project(root, ignore_patterns=["*.log", "private"])

            self.assertEqual(snapshot["files"]["total"], 1)
            self.assertEqual(snapshot["files"]["by_extension"], {".md": 1})
            self.assertEqual(snapshot["filters"]["ignored"], ["*.log", "private"])


if __name__ == "__main__":
    unittest.main()
