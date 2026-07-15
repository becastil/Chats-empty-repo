from __future__ import annotations

import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
from tempfile import TemporaryDirectory
import tomllib
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from repo_scout.policy import load_policy
from repo_scout.rollout import parse_rollout_metadata


ROOT = Path(__file__).resolve().parents[1]
ACTION_PINS = {
    "actions/checkout@9c091bb21b7c1c1d1991bb908d89e4e9dddfe3e0",
    "actions/setup-python@ece7cb06caefa5fff74198d8649806c4678c61a1",
    "actions/upload-artifact@043fb46d1a93c77aae656e7c1c64a875d1fc6a0a",
}
REPO_SCOUT_VERSION = "0.3.39"
REPO_SCOUT_SOURCE_SHA = "86886448f86dbfdc04f03248cc8017a81e688dbe"
REPO_SCOUT_WHEEL_SHA256 = (
    "9fe9317b0e479e6b874d68c35511785308b373fff10367a76dc3006b5a667e36"
)


class CiExampleTests(unittest.TestCase):
    def test_workflows_are_read_only_and_immutably_pinned(self) -> None:
        dogfood = (ROOT / ".github/workflows/repo-scout-policy.yml").read_text(
            encoding="utf-8"
        )
        external = (
            ROOT / "examples/github-actions/repo-scout-policy.yml"
        ).read_text(encoding="utf-8")

        for workflow in (dogfood, external):
            self.assertIn("permissions:\n  contents: read", workflow)
            self.assertIn("  attestations: read", workflow)
            self.assertIn("persist-credentials: false", workflow)
            self.assertIn("runs-on: ubuntu-24.04", workflow)
            self.assertEqual(workflow.count("if: ${{ always() }}"), 2)
            self.assertIn("$RUNNER_TEMP/repo-scout-rollout.md", workflow)
            self.assertIn("${{ runner.temp }}/repo-scout-rollout.md", workflow)
            self.assertIn("REPO_SCOUT_REPOSITORY_ID: ${{ github.repository }}", workflow)
            self.assertIn("--rollout-checklist", workflow)
            self.assertIn(
                '--repository-id "$REPO_SCOUT_REPOSITORY_ID"', workflow
            )
            self.assertIn("name: repo-scout-rollout-evidence", workflow)
            self.assertIn("retention-days: 14", workflow)
            self.assertIn("--force", workflow)
            self.assertNotIn('--output "$TARGET_ROOT', workflow)
            self.assertNotIn("pull_request_target", workflow)
            self.assertNotIn("continue-on-error", workflow)
            self.assertNotIn("|| true", workflow)
            self.assertNotRegex(workflow, r"permissions:[\s\S]{0,80}\bwrite\b")
            self.assertIn(
                f'REPO_SCOUT_VERSION: "{REPO_SCOUT_VERSION}"', workflow
            )
            self.assertIn(
                f"REPO_SCOUT_WHEEL_SHA256: {REPO_SCOUT_WHEEL_SHA256}",
                workflow,
            )
            self.assertIn(
                f"REPO_SCOUT_SOURCE_SHA: {REPO_SCOUT_SOURCE_SHA}", workflow
            )
            self.assertIn(
                'gh release download "v${REPO_SCOUT_VERSION}"', workflow
            )
            self.assertIn("sha256sum --check --strict -", workflow)
            self.assertIn(
                "sha256sum --check --ignore-missing --strict SHA256SUMS",
                workflow,
            )
            self.assertIn(
                'gh attestation verify "$wheel"',
                workflow,
            )
            self.assertIn(
                '--signer-workflow "$REPO_SCOUT_REPOSITORY/'
                '.github/workflows/release.yml"',
                workflow,
            )
            self.assertIn(
                '--source-ref "refs/tags/v${REPO_SCOUT_VERSION}"', workflow
            )
            self.assertIn('--source-digest "$REPO_SCOUT_SOURCE_SHA"', workflow)
            self.assertIn("--deny-self-hosted-runners", workflow)
            self.assertIn(
                'python -m venv "$RUNNER_TEMP/repo-scout-venv"', workflow
            )
            self.assertIn("-m pip install --no-deps", workflow)
            self.assertIn(
                '"$RUNNER_TEMP/repo-scout-venv/bin/repo-scout"', workflow
            )
            self.assertNotIn("PYTHONPATH", workflow)

            uses = re.findall(r"^\s*uses:\s*([^\s#]+)", workflow, re.MULTILINE)
            self.assertTrue(uses)
            for action in uses:
                self.assertRegex(action, r"^[\w.-]+/[\w.-]+@[0-9a-f]{40}$")
                self.assertIn(action, ACTION_PINS)

        self.assertIn("--policy examples/team-policy.toml", dogfood)

        self.assertIn("path: target", external)
        self.assertNotIn("path: repo-scout", external)
        self.assertNotIn("repository: becastil/Chats-empty-repo", external)
        self.assertIn("$TARGET_ROOT/repo-scout-policy.toml", external)

    def test_example_policy_uses_the_supported_contract(self) -> None:
        policy_path = ROOT / "examples/github-actions/repo-scout-policy.toml"
        with policy_path.open("rb") as policy_file:
            raw_policy = tomllib.load(policy_file)

        policy = load_policy(policy_path)

        self.assertEqual(raw_policy["version"], 3)
        self.assertEqual(
            policy["repository"]["required_files"],
            ["README.md", "SECURITY.md"],
        )
        self.assertEqual(
            policy["repository"]["forbidden_files"],
            [".env", ".env.local"],
        )
        self.assertEqual(
            policy["repository"]["forbidden_file_patterns"],
            ["**/.env", "**/.env.local"],
        )
        self.assertTrue(policy["repository"]["require_clean_git"])

    def test_dogfood_policy_uses_safe_nested_forbidden_patterns(self) -> None:
        policy = load_policy(ROOT / "examples/team-policy.toml")

        self.assertEqual(policy["version"], 3)
        self.assertEqual(
            policy["repository"]["forbidden_file_patterns"],
            ["**/.env", "**/.env.local"],
        )

    def test_example_command_is_repeatable_and_preserves_failure_evidence(self) -> None:
        with TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            target = workspace / "target"
            target.mkdir()
            shutil.copytree(ROOT / "src", workspace / "repo-scout" / "src")
            policy_path = target / "repo-scout-policy.toml"
            shutil.copy(
                ROOT / "examples/github-actions/repo-scout-policy.toml",
                policy_path,
            )
            (target / "README.md").write_text("# Example\n", encoding="utf-8")
            (target / "SECURITY.md").write_text("# Security\n", encoding="utf-8")
            self._commit_repository(target)
            report_path = workspace / "repo-scout-rollout.md"

            for _ in range(2):
                completed = self._run_policy(
                    workspace, target, policy_path, report_path
                )
                self.assertEqual(completed.returncode, 0, completed.stderr)

            passing_report = report_path.read_text(encoding="utf-8")
            self.assertIn("## Team Policy", passing_report)
            self.assertIn("## First-Repository Rollout", passing_report)
            self.assertIn("- Status: `pass`", passing_report)
            self.assertIn("- Violations: none.", passing_report)
            passing_metadata = parse_rollout_metadata(passing_report)
            self.assertEqual(passing_metadata["schema_version"], 2)
            self.assertEqual(
                passing_metadata["repository_id"], "example/service"
            )
            self.assertEqual(passing_metadata["readiness"], "ready-for-ci")
            self.assertRegex(
                passing_metadata["policy"]["fingerprint"],
                r"^sha256:[0-9a-f]{64}$",
            )
            self.assertRegex(
                passing_metadata["git"]["commit"],
                r"^(?:[0-9a-f]{40}|[0-9a-f]{64})$",
            )
            self.assertEqual(
                passing_metadata["git"]["commit"], self._git_commit(target)
            )

            nested_env = target / "services/api/.env"
            nested_env.parent.mkdir(parents=True)
            nested_env.write_text("SECRET=unsafe\n", encoding="utf-8")
            subprocess.run(
                [
                    "git",
                    "-C",
                    str(target),
                    "add",
                    "--force",
                    "services/api/.env",
                ],
                check=True,
            )
            subprocess.run(
                [
                    "git",
                    "-C",
                    str(target),
                    "commit",
                    "--quiet",
                    "-m",
                    "Add forbidden environment file",
                ],
                check=True,
            )
            forbidden = self._run_policy(
                workspace, target, policy_path, report_path
            )

            forbidden_report = report_path.read_text(encoding="utf-8")
            self.assertEqual(forbidden.returncode, 6, forbidden.stderr)
            self.assertIn(
                "Forbidden file pattern **/.env matched 1 file(s): "
                "services/api/.env.",
                forbidden_report,
            )
            forbidden_metadata = parse_rollout_metadata(forbidden_report)
            self.assertEqual(
                forbidden_metadata["readiness"], "remediation-required"
            )

            nested_env.unlink()
            subprocess.run(
                ["git", "-C", str(target), "add", "--all"], check=True
            )
            subprocess.run(
                [
                    "git",
                    "-C",
                    str(target),
                    "commit",
                    "--quiet",
                    "-m",
                    "Remove forbidden environment file",
                ],
                check=True,
            )

            (target / "SECURITY.md").unlink()
            subprocess.run(
                ["git", "-C", str(target), "add", "--all"], check=True
            )
            subprocess.run(
                ["git", "-C", str(target), "commit", "--quiet", "-m", "Remove security policy"],
                check=True,
            )
            failed = self._run_policy(workspace, target, policy_path, report_path)

            failing_report = report_path.read_text(encoding="utf-8")
            self.assertEqual(failed.returncode, 6, failed.stderr)
            self.assertIn("- Status: `fail`", failing_report)
            self.assertIn("Required file is missing: SECURITY.md.", failing_report)
            failing_metadata = parse_rollout_metadata(failing_report)
            self.assertEqual(
                failing_metadata["readiness"], "remediation-required"
            )
            self.assertEqual(failing_metadata["policy"]["status"], "fail")
            self.assertEqual(
                failing_metadata["git"]["commit"], self._git_commit(target)
            )

    def test_example_command_rejects_malformed_policy(self) -> None:
        with TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            target = workspace / "target"
            target.mkdir()
            shutil.copytree(ROOT / "src", workspace / "repo-scout" / "src")
            policy_path = target / "repo-scout-policy.toml"
            policy_path.write_text("version = [\n", encoding="utf-8")
            report_path = workspace / "repo-scout-rollout.md"

            completed = self._run_policy(
                workspace, target, policy_path, report_path
            )

            self.assertEqual(completed.returncode, 2)
            self.assertIn("invalid TOML", completed.stderr)
            self.assertFalse(report_path.exists())

    @staticmethod
    def _run_policy(
        workspace: Path,
        target: Path,
        policy_path: Path,
        report_path: Path,
    ) -> subprocess.CompletedProcess[str]:
        environment = os.environ.copy()
        environment["PYTHONPATH"] = str(workspace / "repo-scout" / "src")
        return subprocess.run(
            [
                sys.executable,
                "-m",
                "repo_scout",
                "--format",
                "markdown",
                "--policy",
                str(policy_path),
                "--rollout-checklist",
                "--repository-id",
                "example/service",
                "--output",
                str(report_path),
                "--force",
                str(target),
            ],
            cwd=workspace,
            env=environment,
            capture_output=True,
            text=True,
        )

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

    @staticmethod
    def _git_commit(root: Path) -> str:
        return subprocess.run(
            ["git", "-C", str(root), "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()


if __name__ == "__main__":
    unittest.main()
