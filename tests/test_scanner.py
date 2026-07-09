from __future__ import annotations

from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from repo_scout.scanner import ScanLimitExceeded, scan_project


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
            self.assertNotIn("by_language", snapshot["files"])
            self.assertIn("README.md", snapshot["docs"]["present"])
            self.assertIn("CHANGELOG.md", snapshot["docs"]["missing"])

    def test_scan_project_can_group_files_by_language(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "Dockerfile").write_text("FROM scratch\n", encoding="utf-8")
            (root / "LICENSE").write_text("MIT\n", encoding="utf-8")
            (root / "app.py").write_text("print('hi')\n", encoding="utf-8")
            (root / "config.yaml").write_text("enabled: true\n", encoding="utf-8")

            snapshot = scan_project(root, include_languages=True)

            self.assertEqual(
                snapshot["files"]["by_language"],
                {"Dockerfile": 1, "Other": 1, "Python": 1, "YAML": 1},
            )

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

    def test_scan_project_raises_when_max_files_is_exceeded(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "one.py").write_text("", encoding="utf-8")
            (root / "two.py").write_text("", encoding="utf-8")

            with self.assertRaises(ScanLimitExceeded):
                scan_project(root, max_files=1)

    def test_scan_project_records_max_files_filter_when_allowed(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "README.md").write_text("# Example\n", encoding="utf-8")

            snapshot = scan_project(root, max_files=1)

            self.assertEqual(snapshot["files"]["total"], 1)
            self.assertEqual(snapshot["filters"]["max_files"], 1)


if __name__ == "__main__":
    unittest.main()
