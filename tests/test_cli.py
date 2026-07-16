from __future__ import annotations

from contextlib import redirect_stderr, redirect_stdout
import io
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from repo_scout.cli import main
from repo_scout.rollout import parse_rollout_metadata


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
            self.assertEqual(snapshot["schema_version"], 1)
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

    def test_cli_can_fail_on_attention_for_ci(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            for document in (
                "README.md",
                "PROJECT_STATE.md",
                "ROADMAP.md",
                "CHANGELOG.md",
                "DECISIONS.md",
            ):
                (root / document).write_text("ok\n", encoding="utf-8")

            clear_stdout = io.StringIO()
            with redirect_stdout(clear_stdout):
                clear_exit_code = main(["--fail-on-attention", str(root)])

            self.assertEqual(clear_exit_code, 0)
            self.assertIn("Attention: none", clear_stdout.getvalue())

            (root / "ROADMAP.md").unlink()
            attention_stdout = io.StringIO()
            with redirect_stdout(attention_stdout):
                attention_exit_code = main(["--fail-on-attention", str(root)])

            self.assertEqual(attention_exit_code, 5)
            self.assertIn("Missing project documents: ROADMAP.md", attention_stdout.getvalue())

            output = root / "ci-report.json"
            with redirect_stderr(io.StringIO()):
                output_exit_code = main(
                    [
                        "--format",
                        "json",
                        "--output",
                        str(output),
                        "--fail-on-attention",
                        str(root),
                    ]
                )

            self.assertEqual(output_exit_code, 5)
            self.assertEqual(
                json.loads(output.read_text(encoding="utf-8"))["attention"]["status"],
                "needs-attention",
            )

    def test_cli_applies_team_policy_and_exits_six_on_violations(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "README.md").write_text("# Example\n", encoding="utf-8")
            (root / ".env").write_text("SECRET=unsafe\n", encoding="utf-8")
            policy_path = root / "team-policy.toml"
            policy_path.write_text(
                """version = 2
[repository]
required_files = ["README.md", "SECURITY.md"]
forbidden_files = [".env"]
""",
                encoding="utf-8",
            )

            stdout = io.StringIO()
            with redirect_stdout(stdout):
                exit_code = main(
                    ["--format", "json", "--policy", str(policy_path), str(root)]
                )

            snapshot = json.loads(stdout.getvalue())
            self.assertEqual(exit_code, 6)
            self.assertEqual(snapshot["policy"]["status"], "fail")
            self.assertEqual(
                snapshot["policy"]["violations"][0]["path"], "SECURITY.md"
            )
            self.assertEqual(
                snapshot["policy"]["violations"][1]["path"], ".env"
            )

            (root / "SECURITY.md").write_text("# Security\n", encoding="utf-8")
            (root / ".env").unlink()
            passing_stdout = io.StringIO()
            with redirect_stdout(passing_stdout):
                passing_exit_code = main(
                    ["--format", "markdown", "--policy", str(policy_path), str(root)]
                )

            self.assertEqual(passing_exit_code, 0)
            self.assertIn("## Team Policy", passing_stdout.getvalue())
            self.assertIn("- Status: `pass`", passing_stdout.getvalue())

    def test_cli_enforces_required_file_group_alternatives(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            policy_path = root / "team-policy.toml"
            policy_path.write_text(
                """version = 4
[repository]
required_file_groups = [["package-lock.json", "pnpm-lock.yaml", "yarn.lock"]]
""",
                encoding="utf-8",
            )

            failing_stdout = io.StringIO()
            with redirect_stdout(failing_stdout):
                failing_exit_code = main(
                    ["--format", "json", "--policy", str(policy_path), str(root)]
                )

            failing = json.loads(failing_stdout.getvalue())
            self.assertEqual(failing_exit_code, 6)
            self.assertEqual(
                failing["policy"]["violations"][0]["paths"],
                ["package-lock.json", "pnpm-lock.yaml", "yarn.lock"],
            )

            (root / "yarn.lock").write_text("# yarn lockfile v1\n", encoding="utf-8")
            passing_stdout = io.StringIO()
            with redirect_stdout(passing_stdout):
                passing_exit_code = main(
                    ["--format", "json", "--policy", str(policy_path), str(root)]
                )

            self.assertEqual(passing_exit_code, 0)
            self.assertEqual(
                json.loads(passing_stdout.getvalue())["policy"]["status"], "pass"
            )

    def test_cli_appends_ready_first_repository_rollout_evidence(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            for document in (
                "README.md",
                "PROJECT_STATE.md",
                "ROADMAP.md",
                "CHANGELOG.md",
                "DECISIONS.md",
            ):
                (root / document).write_text("ok\n", encoding="utf-8")
            policy_path = root / "repo-scout-policy.toml"
            policy_path.write_text(
                """version = 1
[repository]
required_files = ["README.md"]
require_clean_git = true
""",
                encoding="utf-8",
            )
            self._commit_repository(root)

            stdout = io.StringIO()
            with redirect_stdout(stdout):
                exit_code = main(
                    [
                        "--format",
                        "markdown",
                        "--policy",
                        str(policy_path),
                        "--rollout-checklist",
                        "--repository-id",
                        "platform/api",
                        str(root),
                    ]
                )

            report = stdout.getvalue()
            self.assertEqual(exit_code, 0)
            self.assertIn("## First-Repository Rollout", report)
            self.assertIn("- **Repository ID:** `platform/api`", report)
            self.assertIn("- **Readiness:** `ready-for-ci`", report)
            self.assertIn(
                "- [x] Team policy version 1 was loaded and evaluated across 2 rules.",
                report,
            )
            self.assertIn(
                "- [x] Repository baseline passes every configured policy rule.",
                report,
            )
            self.assertIn("- [x] Git worktree was clean at scan time.", report)
            self.assertIn("- [x] Git commit identity recorded as", report)
            self.assertIn(
                "- [x] No additional attention findings were detected.", report
            )
            self.assertIn("### Team Handoff", report)
            self.assertIn(
                "- [ ] Record one week of CI evidence before enrolling another repository.",
                report,
            )
            metadata = parse_rollout_metadata(report)
            self.assertEqual(metadata["schema_version"], 2)
            self.assertEqual(metadata["repository_id"], "platform/api")
            self.assertEqual(metadata["readiness"], "ready-for-ci")
            self.assertEqual(metadata["policy"]["status"], "pass")
            self.assertRegex(
                metadata["policy"]["fingerprint"], r"^sha256:[0-9a-f]{64}$"
            )
            self.assertTrue(metadata["git"]["clean"])
            self.assertRegex(
                metadata["git"]["commit"], r"^(?:[0-9a-f]{40}|[0-9a-f]{64})$"
            )

    def test_rollout_requires_an_initial_commit_for_ci_readiness(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp) / "repository"
            root.mkdir()
            subprocess.run(
                ["git", "init", "-q", str(root)], check=True, capture_output=True
            )
            policy_path = Path(tmp) / "policy.toml"
            policy_path.write_text(
                "version = 1\n[repository]\nmax_files = 10\n",
                encoding="utf-8",
            )

            stdout = io.StringIO()
            with redirect_stdout(stdout):
                exit_code = main(
                    [
                        "--format",
                        "markdown",
                        "--policy",
                        str(policy_path),
                        "--rollout-checklist",
                        "--repository-id",
                        "platform/new",
                        str(root),
                    ]
                )

            report = stdout.getvalue()
            metadata = parse_rollout_metadata(report)
            self.assertEqual(exit_code, 0)
            self.assertIn("- **Readiness:** `remediation-required`", report)
            self.assertIn("Create an initial Git commit", report)
            self.assertIsNone(metadata["git"]["commit"])

    def test_rollout_evidence_is_written_before_policy_exit_six(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "README.md").write_text("# Example\n", encoding="utf-8")
            policy_path = root / "repo-scout-policy.toml"
            policy_path.write_text(
                """version = 1
[repository]
required_files = ["README.md", "SECURITY.md"]
""",
                encoding="utf-8",
            )
            output = root / "rollout-evidence.md"

            with redirect_stderr(io.StringIO()):
                exit_code = main(
                    [
                        "--format",
                        "markdown",
                        "--policy",
                        str(policy_path),
                        "--rollout-checklist",
                        "--repository-id",
                        "platform/api",
                        "--output",
                        str(output),
                        str(root),
                    ]
                )

            report = output.read_text(encoding="utf-8")
            self.assertEqual(exit_code, 6)
            self.assertIn("- **Readiness:** `remediation-required`", report)
            self.assertIn(
                "- [ ] Resolve 1 policy violation before enabling required CI.",
                report,
            )
            self.assertIn("- [ ] Initialize Git before starting the rollout.", report)
            self.assertIn("### Team Handoff", report)

    def test_rollout_checklist_requires_policy_markdown_scan(self) -> None:
        stderr = io.StringIO()
        with redirect_stderr(stderr):
            missing_policy = main(
                ["--format", "markdown", "--rollout-checklist", "."]
            )
        self.assertEqual(missing_policy, 2)
        self.assertIn("requires --policy", stderr.getvalue())

        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            policy_path = root / "policy.toml"
            policy_path.write_text(
                "version = 1\n[repository]\nmax_files = 10\n",
                encoding="utf-8",
            )
            stderr = io.StringIO()
            with redirect_stderr(stderr):
                wrong_format = main(
                    [
                        "--policy",
                        str(policy_path),
                        "--rollout-checklist",
                        str(root),
                    ]
                )
            self.assertEqual(wrong_format, 2)
            self.assertIn("requires --format markdown", stderr.getvalue())

            stderr = io.StringIO()
            with redirect_stderr(stderr):
                missing_repository_id = main(
                    [
                        "--format",
                        "markdown",
                        "--policy",
                        str(policy_path),
                        "--rollout-checklist",
                        str(root),
                    ]
                )
            self.assertEqual(missing_repository_id, 2)
            self.assertIn("requires --repository-id", stderr.getvalue())

            stderr = io.StringIO()
            with redirect_stderr(stderr):
                comparison_mode = main(
                    [
                        "--compare",
                        "before.json",
                        "after.json",
                        "--format",
                        "markdown",
                        "--policy",
                        str(policy_path),
                        "--rollout-checklist",
                    ]
                )
            self.assertEqual(comparison_mode, 2)
            self.assertIn("cannot be used with --compare", stderr.getvalue())

            stderr = io.StringIO()
            with redirect_stderr(stderr):
                orphan_repository_id = main(
                    ["--repository-id", "platform/api", str(root)]
                )
            self.assertEqual(orphan_repository_id, 2)
            self.assertIn("requires --rollout-checklist", stderr.getvalue())

            stderr = io.StringIO()
            with redirect_stderr(stderr):
                invalid_repository_id = main(
                    [
                        "--format",
                        "markdown",
                        "--policy",
                        str(policy_path),
                        "--rollout-checklist",
                        "--repository-id",
                        " platform/api",
                        str(root),
                    ]
                )
            self.assertEqual(invalid_repository_id, 2)
            self.assertIn("surrounding whitespace", stderr.getvalue())

    def test_cli_rejects_invalid_team_policy(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            policy_path = root / "team-policy.toml"
            policy_path.write_text(
                """version = 5
[repository]
max_files = 10
""",
                encoding="utf-8",
            )

            stderr = io.StringIO()
            with redirect_stderr(stderr):
                exit_code = main(["--policy", str(policy_path), str(root)])

            self.assertEqual(exit_code, 2)
            self.assertIn(
                "policy version must be 1, 2, 3, or 4", stderr.getvalue()
            )

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

    @unittest.skipUnless(
        os.name == "posix", "POSIX permission semantics required"
    )
    def test_forced_report_replacement_preserves_permissions(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "README.md").write_text("# Example\n", encoding="utf-8")
            output = root / "report.json"
            output.write_text("old report\n", encoding="utf-8")
            output.chmod(0o640)

            with redirect_stderr(io.StringIO()):
                exit_code = main(
                    [
                        "--format",
                        "json",
                        "--output",
                        str(output),
                        "--force",
                        str(root),
                    ]
                )

            self.assertEqual(exit_code, 0)
            self.assertEqual(
                json.loads(output.read_text(encoding="utf-8"))["root"],
                str(root.resolve()),
            )
            self.assertEqual(stat.S_IMODE(output.stat().st_mode), 0o640)

    @unittest.skipUnless(
        os.name == "posix", "POSIX permission semantics required"
    )
    def test_forced_report_replace_failure_keeps_original(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "README.md").write_text("# Example\n", encoding="utf-8")
            output = root / "report.json"
            output.write_text("old report\n", encoding="utf-8")
            output.chmod(0o640)
            stderr = io.StringIO()

            with patch(
                "repo_scout.cli.os.replace",
                side_effect=OSError("disk full"),
            ), redirect_stderr(stderr):
                exit_code = main(
                    [
                        "--format",
                        "json",
                        "--output",
                        str(output),
                        "--force",
                        str(root),
                    ]
                )

            self.assertEqual(exit_code, 4)
            self.assertIn("disk full", stderr.getvalue())
            self.assertEqual(output.read_text(encoding="utf-8"), "old report\n")
            self.assertEqual(stat.S_IMODE(output.stat().st_mode), 0o640)
            self.assertEqual(list(root.glob(f".{output.name}.*")), [])

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

    @staticmethod
    def _commit_repository(root: Path) -> None:
        commands = [
            ("init", "--quiet"),
            ("config", "user.name", "Repo Scout Tests"),
            ("config", "user.email", "tests@example.invalid"),
            ("add", "."),
            ("commit", "--quiet", "-m", "Initial commit"),
        ]
        for command in commands:
            subprocess.run(
                ["git", "-C", str(root), *command],
                check=True,
                capture_output=True,
                text=True,
            )


if __name__ == "__main__":
    unittest.main()
