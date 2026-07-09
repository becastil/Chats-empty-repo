from __future__ import annotations

from contextlib import redirect_stderr, redirect_stdout
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
            self.assertNotIn("by_language", snapshot["files"])

    def test_cli_can_include_language_summary(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "README.md").write_text("# Example\n", encoding="utf-8")
            (root / "app.py").write_text("print('hi')\n", encoding="utf-8")

            stdout = io.StringIO()
            with redirect_stdout(stdout):
                exit_code = main(
                    ["--format", "json", "--languages", str(root)]
                )

            self.assertEqual(exit_code, 0)
            snapshot = json.loads(stdout.getvalue())
            self.assertEqual(
                snapshot["files"]["by_language"],
                {"Markdown": 1, "Python": 1},
            )

    def test_cli_can_emit_markdown_handoff_report(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "README.md").write_text("# Example\n", encoding="utf-8")
            (root / "app.py").write_text("print('hi')\n", encoding="utf-8")
            (root / "debug.log").write_text("noisy\n", encoding="utf-8")

            stdout = io.StringIO()
            with redirect_stdout(stdout):
                exit_code = main(
                    [
                        "--format",
                        "markdown",
                        "--languages",
                        "--ignore",
                        "*.log",
                        str(root),
                    ]
                )

            report = stdout.getvalue()
            self.assertEqual(exit_code, 0)
            self.assertIn(f"- **Root:** `{root.resolve()}`", report)
            self.assertIn("# Repo Scout Snapshot", report)
            self.assertIn("## Project Documents", report)
            self.assertIn("- Missing:", report)
            self.assertIn("## Attention Needed", report)
            self.assertIn("Missing project documents:", report)
            self.assertIn("## Extensions", report)
            self.assertIn("| `.py` | 1 |", report)
            self.assertIn("## Languages", report)
            self.assertIn("| Python | 1 |", report)
            self.assertIn("- Ignored: `*.log`", report)
            self.assertNotIn("debug.log", report)

    def test_cli_can_customize_large_file_attention_threshold(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "README.md").write_text("# Example\n", encoding="utf-8")

            stdout = io.StringIO()
            with redirect_stdout(stdout):
                exit_code = main(
                    ["--large-file-bytes", "1", str(root)]
                )

            self.assertEqual(exit_code, 0)
            self.assertIn("Attention:", stdout.getvalue())
            self.assertIn("README.md is", stdout.getvalue())

    def test_cli_writes_output_and_requires_force_to_replace(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "README.md").write_text("# Example\n", encoding="utf-8")
            output = root / "report.md"

            stderr = io.StringIO()
            with redirect_stderr(stderr):
                first_exit_code = main(
                    ["--format", "markdown", "--output", str(output), str(root)]
                )

            first_report = output.read_text(encoding="utf-8")
            self.assertEqual(first_exit_code, 0)
            self.assertIn("# Repo Scout Snapshot", first_report)
            self.assertIn("wrote", stderr.getvalue())

            overwrite_stderr = io.StringIO()
            with redirect_stderr(overwrite_stderr):
                second_exit_code = main(
                    ["--format", "markdown", "--output", str(output), str(root)]
                )

            self.assertEqual(second_exit_code, 4)
            self.assertIn("--force", overwrite_stderr.getvalue())
            self.assertEqual(output.read_text(encoding="utf-8"), first_report)

            with redirect_stderr(io.StringIO()):
                forced_exit_code = main(
                    [
                        "--format",
                        "json",
                        "--output",
                        str(output),
                        "--force",
                        str(root),
                    ]
                )

            self.assertEqual(forced_exit_code, 0)
            self.assertEqual(json.loads(output.read_text(encoding="utf-8"))["root"], str(root.resolve()))

    def test_markdown_report_shows_custom_attention_threshold(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "README.md").write_text("# Example\n", encoding="utf-8")

            stdout = io.StringIO()
            with redirect_stdout(stdout):
                exit_code = main(
                    ["--format", "markdown", "--large-file-bytes", "1", str(root)]
                )

            self.assertEqual(exit_code, 0)
            self.assertIn("- Large-file threshold: 1 bytes", stdout.getvalue())

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

    def test_cli_returns_error_when_max_files_is_exceeded(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "one.py").write_text("", encoding="utf-8")
            (root / "two.py").write_text("", encoding="utf-8")

            stderr = io.StringIO()
            with redirect_stderr(stderr):
                exit_code = main(["--max-files", "1", str(root)])

            self.assertEqual(exit_code, 3)
            self.assertIn("exceeded --max-files=1", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
