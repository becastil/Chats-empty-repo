from __future__ import annotations

import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
from tempfile import TemporaryDirectory
import textwrap
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
REPO_SCOUT_VERSION = "0.3.50"
REPO_SCOUT_SOURCE_SHA = "371d6fd8da0dc33f60b5c808ca3a3c516125cd7b"
REPO_SCOUT_WHEEL_SHA256 = (
    "a684e16240c0d50357ba552e8b56fa9024c32e80b9ae7b23bd44a874eec1df24"
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

        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn(
            f"It installs the `v{REPO_SCOUT_VERSION}`\nwheel only after checking",
            readme,
        )

        business_model = (ROOT / "BUSINESS_MODEL.md").read_text(encoding="utf-8")
        self.assertIn(
            "The dogfood and copy-ready gates now install the independently "
            "verified\n"
            f"`v{REPO_SCOUT_VERSION}` wheel, so v4 policies can run locally "
            "and in CI",
            business_model,
        )

        self.assertIn("path: target", external)
        self.assertNotIn("path: repo-scout", external)
        self.assertNotIn("repository: becastil/Chats-empty-repo", external)
        self.assertIn("$TARGET_ROOT/repo-scout-policy.toml", external)

        download_marker = "      - name: Download pinned Repo Scout release\n"
        verify_marker = "      - name: Verify release integrity and provenance\n"
        dogfood_download = dogfood[
            dogfood.index(download_marker) : dogfood.index(verify_marker)
        ]
        external_download = external[
            external.index(download_marker) : external.index(verify_marker)
        ]
        self.assertEqual(dogfood_download, external_download)
        self.assertEqual(dogfood_download.count("gh release download"), 1)
        self.assertIn("for attempt in 1 2 3 4; do", dogfood_download)
        self.assertIn(
            'attempt_dir="$release_dir/attempt-$attempt"', dogfood_download
        )
        self.assertIn(
            'mv "$attempt_dir/$wheel_name" "$attempt_dir/SHA256SUMS" '
            '"$release_dir/"',
            dogfood_download,
        )
        self.assertIn('if [[ "$attempt" -eq 4 ]]', dogfood_download)
        self.assertIn('sleep "$((attempt * 5))"', dogfood_download)
        download_script = textwrap.dedent(
            dogfood_download.split("        run: |\n", 1)[1]
        )
        syntax_check = subprocess.run(
            ["bash", "-n"],
            input=download_script,
            capture_output=True,
            text=True,
        )
        self.assertEqual(syntax_check.returncode, 0, syntax_check.stderr)

        install_marker = "      - name: Install verified Repo Scout release\n"
        dogfood_verify = dogfood[
            dogfood.index(verify_marker) : dogfood.index(install_marker)
        ]
        external_verify = external[
            external.index(verify_marker) : external.index(install_marker)
        ]
        self.assertEqual(dogfood_verify, external_verify)
        self.assertEqual(dogfood_verify.count("gh attestation verify"), 1)
        self.assertIn("for attempt in 1 2 3 4; do", dogfood_verify)
        self.assertIn(
            "Repo Scout provenance verification failed after %s attempts.",
            dogfood_verify,
        )
        self.assertIn('sleep "$((attempt * 5))"', dogfood_verify)
        verify_script = textwrap.dedent(
            dogfood_verify.split("        run: |\n", 1)[1]
        )
        syntax_check = subprocess.run(
            ["bash", "-n"],
            input=verify_script,
            capture_output=True,
            text=True,
        )
        self.assertEqual(syntax_check.returncode, 0, syntax_check.stderr)

    def test_release_download_retries_are_executable_and_bounded(self) -> None:
        workflow = (ROOT / ".github/workflows/repo-scout-policy.yml").read_text(
            encoding="utf-8"
        )
        download_marker = "      - name: Download pinned Repo Scout release\n"
        verify_marker = "      - name: Verify release integrity and provenance\n"
        download_step = workflow[
            workflow.index(download_marker) : workflow.index(verify_marker)
        ]
        download_script = textwrap.dedent(
            download_step.split("        run: |\n", 1)[1]
        )

        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            fake_bin = root / "bin"
            self._write_retry_fakes(fake_bin)

            recovered, recovered_counter, recovered_sleeps = (
                self._run_release_download(
                    download_script,
                    fake_bin,
                    root / "recovered",
                    success_on=3,
                )
            )
            recovered_release = root / "recovered/repo-scout-release"
            self.assertEqual(recovered.returncode, 0, recovered.stderr)
            self.assertEqual(recovered_counter, 3)
            self.assertEqual(recovered_sleeps, ["5", "10"])
            self.assertEqual(
                (
                    recovered_release
                    / f"repo_scout-{REPO_SCOUT_VERSION}-py3-none-any.whl"
                ).read_text(encoding="utf-8"),
                "wheel",
            )
            self.assertEqual(
                (recovered_release / "SHA256SUMS").read_text(encoding="utf-8"),
                "manifest",
            )

            failed, failed_counter, failed_sleeps = self._run_release_download(
                download_script,
                fake_bin,
                root / "failed",
                success_on=5,
            )
            failed_release = root / "failed/repo-scout-release"
            self.assertEqual(failed.returncode, 1)
            self.assertEqual(failed_counter, 4)
            self.assertEqual(failed_sleeps, ["5", "10", "15"])
            self.assertIn("failed after 4 attempts", failed.stderr)
            self.assertFalse((failed_release / "SHA256SUMS").exists())
            self.assertFalse(
                (
                    failed_release
                    / f"repo_scout-{REPO_SCOUT_VERSION}-py3-none-any.whl"
                ).exists()
            )

    def test_provenance_verification_retries_are_executable_and_bounded(
        self,
    ) -> None:
        workflow = (ROOT / ".github/workflows/repo-scout-policy.yml").read_text(
            encoding="utf-8"
        )
        verify_marker = "      - name: Verify release integrity and provenance\n"
        install_marker = "      - name: Install verified Repo Scout release\n"
        verify_step = workflow[
            workflow.index(verify_marker) : workflow.index(install_marker)
        ]
        verify_script = textwrap.dedent(
            verify_step.split("        run: |\n", 1)[1]
        )

        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            fake_bin = root / "bin"
            self._write_retry_fakes(fake_bin)

            recovered, recovered_counter, recovered_sleeps = (
                self._run_provenance_verification(
                    verify_script,
                    fake_bin,
                    root / "recovered",
                    success_on=3,
                )
            )
            self.assertEqual(recovered.returncode, 0, recovered.stderr)
            self.assertEqual(recovered_counter, 3)
            self.assertEqual(recovered_sleeps, ["5", "10"])

            failed, failed_counter, failed_sleeps = (
                self._run_provenance_verification(
                    verify_script,
                    fake_bin,
                    root / "failed",
                    success_on=5,
                )
            )
            self.assertEqual(failed.returncode, 1)
            self.assertEqual(failed_counter, 4)
            self.assertEqual(failed_sleeps, ["5", "10", "15"])
            self.assertIn(
                "provenance verification failed after 4 attempts",
                failed.stderr,
            )

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
    def _write_retry_fakes(fake_bin: Path) -> None:
        fake_bin.mkdir()
        fake_gh = fake_bin / "gh"
        fake_gh.write_text(
            f"#!{sys.executable}\n"
            "import os\n"
            "from pathlib import Path\n"
            "import sys\n"
            "counter = Path(os.environ['FAKE_GH_COUNTER'])\n"
            "attempt = int(counter.read_text()) + 1 if counter.exists() else 1\n"
            "counter.write_text(str(attempt))\n"
            "if attempt < int(os.environ['FAKE_GH_SUCCESS_ON']):\n"
            "    raise SystemExit(1)\n"
            "if sys.argv[1:3] == ['release', 'download']:\n"
            "    destination = Path(sys.argv[sys.argv.index('--dir') + 1])\n"
            "    destination.mkdir(parents=True, exist_ok=True)\n"
            "    version = os.environ['REPO_SCOUT_VERSION']\n"
            "    (destination / f'repo_scout-{version}-py3-none-any.whl').write_text('wheel')\n"
            "    (destination / 'SHA256SUMS').write_text('manifest')\n",
            encoding="utf-8",
        )
        fake_sleep = fake_bin / "sleep"
        fake_sleep.write_text(
            "#!/usr/bin/env sh\n"
            "printf '%s\\n' \"$1\" >> \"$FAKE_SLEEP_LOG\"\n",
            encoding="utf-8",
        )
        fake_sha256sum = fake_bin / "sha256sum"
        fake_sha256sum.write_text("#!/usr/bin/env sh\nexit 0\n", encoding="utf-8")
        fake_gh.chmod(0o755)
        fake_sleep.chmod(0o755)
        fake_sha256sum.chmod(0o755)

    @staticmethod
    def _run_release_download(
        script: str,
        fake_bin: Path,
        runner_temp: Path,
        *,
        success_on: int,
    ) -> tuple[subprocess.CompletedProcess[str], int, list[str]]:
        runner_temp.mkdir()
        counter = runner_temp / "gh-count"
        sleep_log = runner_temp / "sleep-log"
        environment = os.environ.copy()
        environment.update(
            {
                "FAKE_GH_COUNTER": str(counter),
                "FAKE_GH_SUCCESS_ON": str(success_on),
                "FAKE_SLEEP_LOG": str(sleep_log),
                "PATH": f"{fake_bin}{os.pathsep}{environment['PATH']}",
                "REPO_SCOUT_REPOSITORY": "example/repo-scout",
                "REPO_SCOUT_VERSION": REPO_SCOUT_VERSION,
                "RUNNER_TEMP": str(runner_temp),
            }
        )
        completed = subprocess.run(
            ["bash", "-e"],
            input=script,
            env=environment,
            capture_output=True,
            text=True,
        )
        sleeps = (
            sleep_log.read_text(encoding="utf-8").splitlines()
            if sleep_log.exists()
            else []
        )
        return completed, int(counter.read_text(encoding="utf-8")), sleeps

    @staticmethod
    def _run_provenance_verification(
        script: str,
        fake_bin: Path,
        runner_temp: Path,
        *,
        success_on: int,
    ) -> tuple[subprocess.CompletedProcess[str], int, list[str]]:
        runner_temp.mkdir()
        release_dir = runner_temp / "repo-scout-release"
        release_dir.mkdir()
        wheel = release_dir / f"repo_scout-{REPO_SCOUT_VERSION}-py3-none-any.whl"
        wheel.write_text("wheel", encoding="utf-8")
        (release_dir / "SHA256SUMS").write_text("manifest", encoding="utf-8")
        counter = runner_temp / "gh-count"
        sleep_log = runner_temp / "sleep-log"
        environment = os.environ.copy()
        environment.update(
            {
                "FAKE_GH_COUNTER": str(counter),
                "FAKE_GH_SUCCESS_ON": str(success_on),
                "FAKE_SLEEP_LOG": str(sleep_log),
                "PATH": f"{fake_bin}{os.pathsep}{environment['PATH']}",
                "REPO_SCOUT_REPOSITORY": "example/repo-scout",
                "REPO_SCOUT_SOURCE_SHA": REPO_SCOUT_SOURCE_SHA,
                "REPO_SCOUT_VERSION": REPO_SCOUT_VERSION,
                "REPO_SCOUT_WHEEL_SHA256": REPO_SCOUT_WHEEL_SHA256,
                "RUNNER_TEMP": str(runner_temp),
            }
        )
        completed = subprocess.run(
            ["bash", "-e"],
            input=script,
            env=environment,
            capture_output=True,
            text=True,
        )
        sleeps = (
            sleep_log.read_text(encoding="utf-8").splitlines()
            if sleep_log.exists()
            else []
        )
        return completed, int(counter.read_text(encoding="utf-8")), sleeps

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
