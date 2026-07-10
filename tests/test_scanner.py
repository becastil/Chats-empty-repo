from __future__ import annotations

from pathlib import Path
import sys
import subprocess
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
            self.assertIsNone(snapshot["git"]["commit"])
            self.assertEqual(snapshot["schema_version"], 1)
            self.assertEqual(snapshot["files"]["paths"], [
                "LICENSE",
                "README.md",
                "pyproject.toml",
                "src/app.py",
            ])
            self.assertFalse(snapshot["files"]["paths_truncated"])
            self.assertEqual(snapshot["files"]["total"], 4)
            self.assertEqual(snapshot["files"]["by_extension"][".md"], 1)
            self.assertEqual(snapshot["files"]["by_extension"][".py"], 1)
            self.assertEqual(snapshot["files"]["by_extension"][".toml"], 1)
            self.assertEqual(snapshot["files"]["by_extension"]["[no extension]"], 1)
            self.assertNotIn("by_language", snapshot["files"])
            self.assertEqual(snapshot["attention"]["status"], "needs-attention")
            self.assertEqual(
                snapshot["attention"]["items"][0]["kind"], "missing_docs"
            )
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

    def test_scan_project_reports_large_files_at_threshold(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "small.txt").write_text("small", encoding="utf-8")
            (root / "large.txt").write_text("large file", encoding="utf-8")

            snapshot = scan_project(root, large_file_bytes=6)

            large_items = [
                item
                for item in snapshot["attention"]["items"]
                if item["kind"] == "large_file"
            ]
            self.assertEqual([item["path"] for item in large_items], ["large.txt"])
            self.assertEqual(large_items[0]["threshold_bytes"], 6)

    def test_scan_project_reports_dirty_git_state(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            subprocess.run(
                ["git", "init", "-q", str(root)], check=True, capture_output=True
            )
            (root / "README.md").write_text("# Example\n", encoding="utf-8")

            snapshot = scan_project(root)

            self.assertEqual(snapshot["git"]["dirty_files"], 1)
            self.assertIsNone(snapshot["git"]["commit"])
            self.assertEqual(snapshot["attention"]["items"][0]["kind"], "dirty_git")

    def test_scan_project_records_exact_git_commit(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            subprocess.run(
                ["git", "init", "-q", str(root)], check=True, capture_output=True
            )
            subprocess.run(
                ["git", "-C", str(root), "config", "user.name", "Repo Scout Tests"],
                check=True,
                capture_output=True,
            )
            subprocess.run(
                ["git", "-C", str(root), "config", "user.email", "tests@example.com"],
                check=True,
                capture_output=True,
            )
            (root / "README.md").write_text("# Example\n", encoding="utf-8")
            subprocess.run(
                ["git", "-C", str(root), "add", "README.md"],
                check=True,
                capture_output=True,
            )
            subprocess.run(
                ["git", "-C", str(root), "commit", "-q", "-m", "Initial"],
                check=True,
                capture_output=True,
            )
            expected = subprocess.run(
                ["git", "-C", str(root), "rev-parse", "HEAD"],
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()

            snapshot = scan_project(root)

            self.assertEqual(snapshot["git"]["commit"], expected)
            self.assertEqual(snapshot["git"]["dirty_files"], 0)


if __name__ == "__main__":
    unittest.main()
