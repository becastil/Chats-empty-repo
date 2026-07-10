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


ROOT = Path(__file__).resolve().parents[1]
ACTION_PINS = {
    "actions/checkout@9c091bb21b7c1c1d1991bb908d89e4e9dddfe3e0",
    "actions/setup-python@ece7cb06caefa5fff74198d8649806c4678c61a1",
    "actions/upload-artifact@043fb46d1a93c77aae656e7c1c64a875d1fc6a0a",
}
REPO_SCOUT_VERSION = "0.2.8"
REPO_SCOUT_SOURCE_SHA = "3519a842b0b24662d40d395f81ff29bba9eddcff"
REPO_SCOUT_WHEEL_SHA256 = (
    "38efdc5d8b0a1e232037e3d9215ae72640af592df6f1e00d7bf03e6b0b13bd66"
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
            self.assertIn("if: ${{ always() }}", workflow)
            self.assertIn("$RUNNER_TEMP/repo-scout-policy-report.md", workflow)
            self.assertIn("${{ runner.temp }}/repo-scout-policy-report.md", workflow)
            self.assertIn("--force", workflow)
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

        self.assertEqual(raw_policy["version"], 1)
        self.assertEqual(
            policy["repository"]["required_files"],
            ["README.md", "SECURITY.md"],
        )
        self.assertTrue(policy["repository"]["require_clean_git"])

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
            report_path = workspace / "repo-scout-policy-report.md"

            for _ in range(2):
                completed = self._run_policy(
                    workspace, target, policy_path, report_path
                )
                self.assertEqual(completed.returncode, 0, completed.stderr)

            passing_report = report_path.read_text(encoding="utf-8")
            self.assertIn("## Team Policy", passing_report)
            self.assertIn("- Status: `pass`", passing_report)
            self.assertIn("- Violations: none.", passing_report)

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

    def test_example_command_rejects_malformed_policy(self) -> None:
        with TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            target = workspace / "target"
            target.mkdir()
            shutil.copytree(ROOT / "src", workspace / "repo-scout" / "src")
            policy_path = target / "repo-scout-policy.toml"
            policy_path.write_text("version = [\n", encoding="utf-8")
            report_path = workspace / "repo-scout-policy-report.md"

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


if __name__ == "__main__":
    unittest.main()
