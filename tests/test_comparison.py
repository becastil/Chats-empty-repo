from __future__ import annotations

import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from repo_scout.cli import main


def snapshot(
    *,
    total: int,
    total_bytes: int,
    extensions: dict[str, int],
    present: list[str],
    missing: list[str],
    branch: str,
    dirty_files: int,
    attention_status: str,
    attention_items: int,
) -> dict[str, object]:
    return {
        "root": "/workspace/project",
        "git": {
            "is_repo": True,
            "branch": branch,
            "dirty_files": dirty_files,
        },
        "docs": {"present": present, "missing": missing},
        "attention": {
            "status": attention_status,
            "items": [{} for _ in range(attention_items)],
        },
        "files": {
            "total": total,
            "total_bytes": total_bytes,
            "by_extension": extensions,
            "largest": [],
        },
    }


class ComparisonCliTests(unittest.TestCase):
    def test_cli_can_compare_saved_snapshots_as_json(self) -> None:
        with TemporaryDirectory() as tmp:
            before_path = Path(tmp) / "before.json"
            after_path = Path(tmp) / "after.json"
            before_path.write_text(
                json.dumps(
                    snapshot(
                        total=2,
                        total_bytes=20,
                        extensions={".md": 1, ".py": 1},
                        present=["README.md"],
                        missing=["ROADMAP.md"],
                        branch="main",
                        dirty_files=0,
                        attention_status="clear",
                        attention_items=0,
                    )
                ),
                encoding="utf-8",
            )
            after_path.write_text(
                json.dumps(
                    snapshot(
                        total=3,
                        total_bytes=35,
                        extensions={".md": 1, ".py": 2},
                        present=["README.md", "ROADMAP.md"],
                        missing=[],
                        branch="feature",
                        dirty_files=2,
                        attention_status="needs-attention",
                        attention_items=2,
                    )
                ),
                encoding="utf-8",
            )

            from contextlib import redirect_stdout
            import io

            stdout = io.StringIO()
            with redirect_stdout(stdout):
                exit_code = main(
                    ["--format", "json", "--compare", str(before_path), str(after_path)]
                )

            comparison = json.loads(stdout.getvalue())
            self.assertEqual(exit_code, 0)
            self.assertEqual(comparison["status"], "changed")
            self.assertEqual(comparison["files"]["total"]["delta"], 1)
            self.assertEqual(
                comparison["files"]["by_extension"]["changed"][".py"]["delta"],
                1,
            )
            self.assertEqual(comparison["docs"]["missing"]["removed"], ["ROADMAP.md"])
            self.assertTrue(comparison["git"]["branch"]["changed"])

    def test_cli_can_render_unchanged_comparison_as_markdown(self) -> None:
        with TemporaryDirectory() as tmp:
            snapshot_path = Path(tmp) / "snapshot.json"
            snapshot_path.write_text(
                json.dumps(
                    snapshot(
                        total=1,
                        total_bytes=10,
                        extensions={".md": 1},
                        present=["README.md"],
                        missing=[],
                        branch="main",
                        dirty_files=0,
                        attention_status="clear",
                        attention_items=0,
                    )
                ),
                encoding="utf-8",
            )

            from contextlib import redirect_stdout
            import io

            stdout = io.StringIO()
            with redirect_stdout(stdout):
                exit_code = main(
                    [
                        "--format",
                        "markdown",
                        "--compare",
                        str(snapshot_path),
                        str(snapshot_path),
                    ]
                )

            report = stdout.getvalue()
            self.assertEqual(exit_code, 0)
            self.assertIn("# Repo Scout Comparison", report)
            self.assertIn("- **Status:** `unchanged`", report)
            self.assertIn("No changes detected.", report)

    def test_cli_can_write_comparison_report_to_output(self) -> None:
        with TemporaryDirectory() as tmp:
            snapshot_path = Path(tmp) / "snapshot.json"
            output_path = Path(tmp) / "comparison.json"
            snapshot_path.write_text(
                json.dumps(
                    snapshot(
                        total=1,
                        total_bytes=10,
                        extensions={".md": 1},
                        present=["README.md"],
                        missing=[],
                        branch="main",
                        dirty_files=0,
                        attention_status="clear",
                        attention_items=0,
                    )
                ),
                encoding="utf-8",
            )

            from contextlib import redirect_stderr
            import io

            with redirect_stderr(io.StringIO()):
                exit_code = main(
                    [
                        "--format",
                        "json",
                        "--compare",
                        str(snapshot_path),
                        str(snapshot_path),
                        "--output",
                        str(output_path),
                    ]
                )

            self.assertEqual(exit_code, 0)
            self.assertEqual(
                json.loads(output_path.read_text(encoding="utf-8"))["status"],
                "unchanged",
            )


if __name__ == "__main__":
    unittest.main()
