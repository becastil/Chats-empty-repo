from __future__ import annotations

from contextlib import redirect_stderr
import hashlib
import importlib.util
from io import StringIO
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from tempfile import TemporaryDirectory
import textwrap
import tomllib
import unittest
import zipfile


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "prepare_release.py"
SPEC = importlib.util.spec_from_file_location("prepare_release", SCRIPT_PATH)
assert SPEC is not None and SPEC.loader is not None
prepare_release = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = prepare_release
SPEC.loader.exec_module(prepare_release)

ZIPAPP_SCRIPT_PATH = ROOT / "scripts" / "build_zipapp.py"
ZIPAPP_SPEC = importlib.util.spec_from_file_location(
    "build_zipapp", ZIPAPP_SCRIPT_PATH
)
assert ZIPAPP_SPEC is not None and ZIPAPP_SPEC.loader is not None
build_zipapp = importlib.util.module_from_spec(ZIPAPP_SPEC)
sys.modules[ZIPAPP_SPEC.name] = build_zipapp
ZIPAPP_SPEC.loader.exec_module(build_zipapp)

ACTIVATION_SMOKE_SCRIPT_PATH = ROOT / "scripts" / "smoke_test_policy_activation.py"
ACTIVATION_SMOKE_SPEC = importlib.util.spec_from_file_location(
    "smoke_test_policy_activation", ACTIVATION_SMOKE_SCRIPT_PATH
)
assert (
    ACTIVATION_SMOKE_SPEC is not None
    and ACTIVATION_SMOKE_SPEC.loader is not None
)
smoke_test_policy_activation = importlib.util.module_from_spec(
    ACTIVATION_SMOKE_SPEC
)
sys.modules[ACTIVATION_SMOKE_SPEC.name] = smoke_test_policy_activation
ACTIVATION_SMOKE_SPEC.loader.exec_module(smoke_test_policy_activation)

OUTREACH_SMOKE_SCRIPT_PATH = (
    ROOT / "scripts" / "smoke_test_outreach_lifecycle.py"
)
OUTREACH_SMOKE_SPEC = importlib.util.spec_from_file_location(
    "smoke_test_outreach_lifecycle", OUTREACH_SMOKE_SCRIPT_PATH
)
assert OUTREACH_SMOKE_SPEC is not None and OUTREACH_SMOKE_SPEC.loader is not None
smoke_test_outreach_lifecycle = importlib.util.module_from_spec(
    OUTREACH_SMOKE_SPEC
)
sys.modules[OUTREACH_SMOKE_SPEC.name] = smoke_test_outreach_lifecycle
OUTREACH_SMOKE_SPEC.loader.exec_module(smoke_test_outreach_lifecycle)

PILOT_SMOKE_SCRIPT_PATH = ROOT / "scripts" / "smoke_test_pilot_funnel.py"
PILOT_SMOKE_SPEC = importlib.util.spec_from_file_location(
    "smoke_test_pilot_funnel", PILOT_SMOKE_SCRIPT_PATH
)
assert PILOT_SMOKE_SPEC is not None and PILOT_SMOKE_SPEC.loader is not None
smoke_test_pilot_funnel = importlib.util.module_from_spec(PILOT_SMOKE_SPEC)
sys.modules[PILOT_SMOKE_SPEC.name] = smoke_test_pilot_funnel
PILOT_SMOKE_SPEC.loader.exec_module(smoke_test_pilot_funnel)

ROLLOUT_SMOKE_SCRIPT_PATH = ROOT / "scripts" / "smoke_test_rollout_summary.py"
ROLLOUT_SMOKE_SPEC = importlib.util.spec_from_file_location(
    "smoke_test_rollout_summary", ROLLOUT_SMOKE_SCRIPT_PATH
)
assert ROLLOUT_SMOKE_SPEC is not None and ROLLOUT_SMOKE_SPEC.loader is not None
smoke_test_rollout_summary = importlib.util.module_from_spec(ROLLOUT_SMOKE_SPEC)
sys.modules[ROLLOUT_SMOKE_SPEC.name] = smoke_test_rollout_summary
ROLLOUT_SMOKE_SPEC.loader.exec_module(smoke_test_rollout_summary)

WHEEL_COMPARE_SCRIPT_PATH = ROOT / "scripts" / "compare_wheel_contents.py"
WHEEL_COMPARE_SPEC = importlib.util.spec_from_file_location(
    "compare_wheel_contents", WHEEL_COMPARE_SCRIPT_PATH
)
assert WHEEL_COMPARE_SPEC is not None and WHEEL_COMPARE_SPEC.loader is not None
compare_wheel_contents = importlib.util.module_from_spec(WHEEL_COMPARE_SPEC)
sys.modules[WHEEL_COMPARE_SPEC.name] = compare_wheel_contents
WHEEL_COMPARE_SPEC.loader.exec_module(compare_wheel_contents)


class ReleaseManifestTests(unittest.TestCase):
    def test_current_project_versions_match(self) -> None:
        self.assertEqual(prepare_release.load_project_version(ROOT), "0.3.51")

    def test_public_distribution_metadata_and_quick_start_match_release(self) -> None:
        with (ROOT / "pyproject.toml").open("rb") as project_file:
            project = tomllib.load(project_file)["project"]
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        site_config = (ROOT / "app/site-config.ts").read_text(encoding="utf-8")

        self.assertEqual(
            project["description"],
            "Local repository snapshots and policy enforcement for developer teams.",
        )
        self.assertEqual(
            project["urls"]["Homepage"],
            "https://repo-scout.becastil.chatgpt.site",
        )
        self.assertEqual(
            project["urls"]["Source"],
            "https://github.com/becastil/Chats-empty-repo",
        )
        version = project["version"]
        site_version = re.search(
            r'RELEASE_VERSION\s*=\s*"([^"]+)"',
            site_config,
        )
        self.assertIsNotNone(site_version)
        assert site_version is not None
        self.assertEqual(site_version.group(1), version)
        self.assertIn(f"repo-scout-{version}.pyz", readme)
        self.assertIn(f"repo_scout-{version}-py3-none-any.whl", readme)
        self.assertIn(
            "https://repo-scout.becastil.chatgpt.site/?source=github#why-teams-buy",
            readme,
        )
        self.assertIn(
            "discovery_source=GitHub+repository+or+release",
            readme,
        )
        self.assertNotIn("PYTHONPATH=src python3 -m repo_scout", readme)

    def test_site_dependency_security_contract_is_locked(self) -> None:
        package = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))
        lock = json.loads(
            (ROOT / "package-lock.json").read_text(encoding="utf-8")
        )["packages"]

        self.assertEqual(package["dependencies"]["next"], "16.2.11")
        self.assertEqual(package["devDependencies"]["eslint-config-next"], "16.2.11")
        self.assertEqual(
            package["devDependencies"]["@cloudflare/vite-plugin"],
            "1.46.0",
        )
        self.assertEqual(package["devDependencies"]["vite"], "8.1.5")
        self.assertEqual(package["devDependencies"]["wrangler"], "4.113.0")
        self.assertEqual(
            package["scripts"]["audit:dependencies"],
            "npm audit",
        )
        self.assertEqual(
            package["overrides"],
            {"postcss": "8.5.22", "sharp": "0.35.3"},
        )
        self.assertEqual(lock["node_modules/next"]["version"], "16.2.11")
        self.assertEqual(lock["node_modules/postcss"]["version"], "8.5.22")
        self.assertEqual(lock["node_modules/sharp"]["version"], "0.35.3")
        self.assertEqual(
            lock["node_modules/vite"]["dependencies"]["postcss"],
            "^8.5.17",
        )
        self.assertNotIn("node_modules/next/node_modules/postcss", lock)

    def test_release_verification_docs_cover_every_artifact(self) -> None:
        documentation = (ROOT / "docs" / "releases.md").read_text(
            encoding="utf-8"
        )
        _, verification_heading, verification_tail = documentation.partition(
            "## Verify A Release"
        )
        verification, deployment_heading, deployment_tail = verification_tail.partition(
            "## Prepare And Approve A Site Deployment"
        )
        _, audit_heading, _ = deployment_tail.partition(
            "## Audit The Production Download"
        )
        self.assertTrue(verification_heading)
        self.assertTrue(deployment_heading)
        self.assertTrue(audit_heading)

        artifact_count = len(prepare_release.ARTIFACT_TEMPLATE)
        normalized = " ".join(verification.split())
        self.assertIn(
            f"directory containing all {artifact_count + 1} downloaded files",
            normalized,
        )
        self.assertEqual(
            verification.count("gh attestation verify "),
            artifact_count,
        )
        self.assertIn("set -euo pipefail", verification)
        version = prepare_release.load_project_version(ROOT)
        self.assertIn(
            'REPO_SCOUT_REPOSITORY="becastil/Chats-empty-repo"',
            verification,
        )
        self.assertIn(f'REPO_SCOUT_VERSION="{version}"', verification)
        self.assertIn(
            'REPO_SCOUT_TAG="v${REPO_SCOUT_VERSION}"',
            verification,
        )
        self.assertIn(
            'REPO_SCOUT_SIGNER_WORKFLOW="${REPO_SCOUT_REPOSITORY}/'
            '.github/workflows/release.yml"',
            verification,
        )
        self.assertEqual(
            verification.count("git ls-remote --exit-code --tags "),
            1,
        )
        self.assertIn(
            '"refs/tags/${REPO_SCOUT_TAG}^{}"',
            verification,
        )
        self.assertIn(
            '[[ "$REPO_SCOUT_RESOLVED_REF" == '
            '"refs/tags/${REPO_SCOUT_TAG}^{}" ]]',
            verification,
        )
        self.assertIn(
            '[[ "$REPO_SCOUT_SOURCE_SHA" =~ ^[0-9a-f]{40}$ ]]',
            verification,
        )
        self.assertIn("sha256sum --check SHA256SUMS", verification)
        self.assertIn("shasum -a 256 -c SHA256SUMS", verification)
        for template in prepare_release.ARTIFACT_TEMPLATE:
            artifact = template.format(version="${REPO_SCOUT_VERSION}")
            self.assertIn(f'"{artifact}"', verification)
        for requirement in (
            '--repo "$REPO_SCOUT_REPOSITORY"',
            '--signer-workflow "$REPO_SCOUT_SIGNER_WORKFLOW"',
            '--source-ref "refs/tags/${REPO_SCOUT_TAG}"',
            '--source-digest "$REPO_SCOUT_SOURCE_SHA"',
            "--deny-self-hosted-runners",
        ):
            self.assertEqual(
                verification.count(requirement),
                artifact_count,
                requirement,
            )
        self.assertNotRegex(
            verification,
            r"--source-digest [0-9a-f]{40}",
        )
        self.assertIn(
            f"All {artifact_count} checksum lines must report `OK`, and all "
            f"{artifact_count} attestation commands must verify",
            normalized,
        )

    def test_release_verification_snippet_is_valid_bash(self) -> None:
        documentation = (ROOT / "docs" / "releases.md").read_text(
            encoding="utf-8"
        )
        _, verification_heading, verification_tail = documentation.partition(
            "## Verify A Release"
        )
        verification, deployment_heading, deployment_tail = verification_tail.partition(
            "## Prepare And Approve A Site Deployment"
        )
        _, audit_heading, _ = deployment_tail.partition(
            "## Audit The Production Download"
        )
        _, code_heading, code_tail = verification.partition("```bash\n")
        snippet, code_end, _ = code_tail.partition("```\n")
        self.assertTrue(verification_heading)
        self.assertTrue(deployment_heading)
        self.assertTrue(audit_heading)
        self.assertTrue(code_heading)
        self.assertTrue(code_end)

        result = subprocess.run(
            ["bash", "-n"],
            input=snippet,
            text=True,
            capture_output=True,
            check=False,
        )

        self.assertEqual(result.returncode, 0, result.stderr)

    def test_site_deployment_handoff_preserves_publication_boundary(self) -> None:
        documentation = (ROOT / "docs" / "releases.md").read_text(
            encoding="utf-8"
        )
        _, deployment_heading, deployment_tail = documentation.partition(
            "## Prepare And Approve A Site Deployment"
        )
        deployment, audit_heading, audit = deployment_tail.partition(
            "## Audit The Production Download"
        )
        self.assertTrue(deployment_heading)
        self.assertTrue(audit_heading)

        normalized = " ".join(deployment.split())
        for command in (
            "npm ci",
            "npm run audit:dependencies",
            "npm test",
            "npm run lint",
        ):
            self.assertIn(command, deployment)
        for requirement in (
            "exact committed source",
            "existing Sites source repository",
            "existing Sites project",
            "`.openai/hosting.json`",
            "Saving a version does not make that version live",
            "explicit owner approval",
            "Only after the approved deployment succeeds",
            "immediately run the production audit",
            "dependency audit must report zero vulnerabilities",
            "Do not use `npm audit fix --force`",
        ):
            self.assertIn(requirement, normalized, requirement)
        self.assertIn("python3 scripts/audit_production_site.py", audit)

    def test_distribution_path_counts_every_packaged_command(self) -> None:
        with (ROOT / "pyproject.toml").open("rb") as project_file:
            commands = tomllib.load(project_file)["project"]["scripts"]
        distribution = (ROOT / "DISTRIBUTION.md").read_text(encoding="utf-8")

        self.assertIn(
            f"wheel when it needs all {len(commands)} commands",
            " ".join(distribution.split()),
        )

    def test_policy_activation_smoke_contract_passes_against_source(self) -> None:
        environment = os.environ.copy()
        environment["PYTHONPATH"] = str(ROOT / "src")

        checked = smoke_test_policy_activation.verify_policy_activation(
            sys.executable, environment=environment
        )

        self.assertEqual(
            checked,
            (
                "package-lock.json",
                "pnpm-lock.yaml",
                "yarn.lock",
                "python-service",
                "agent-ready-service",
                "service-baseline",
                "polyglot-review",
            ),
        )

    def test_outreach_lifecycle_smoke_contract_passes_against_source(self) -> None:
        environment = os.environ.copy()
        environment["PYTHONPATH"] = str(ROOT / "src")

        checked = smoke_test_outreach_lifecycle.verify_outreach_lifecycle(
            sys.executable, environment=environment
        )

        self.assertEqual(
            checked,
            (
                "utc-date-default",
                "permissive-ledger-rejected",
                "private-review-written",
                "copy-ready-handoffs",
                "draft-declined-without-contact",
                "draft-reviewed",
                "draft-ledger-drift-rejected",
                "private-review-bundle",
                "unconfirmed-approval-rejected",
                "draft-approved",
                "counts-only-publication-guard",
                "contact-recorded",
                "follow-up-recorded",
                "duplicate-follow-up-rejected",
                "unconfirmed-outcome-rejected",
                "pilot-outcome-recorded",
                "missing-approval-rejected",
                "extra-column-rejected",
            ),
        )

    def test_remaining_smokes_reject_missing_installed_commands(self) -> None:
        cases = (
            (
                smoke_test_policy_activation.verify_policy_activation,
                smoke_test_policy_activation.SmokeTestError,
            ),
            (
                smoke_test_outreach_lifecycle.verify_outreach_lifecycle,
                smoke_test_outreach_lifecycle.SmokeTestError,
            ),
            (
                smoke_test_rollout_summary.verify_rollout_summary,
                smoke_test_rollout_summary.SmokeTestError,
            ),
        )
        with TemporaryDirectory() as tmp:
            for verify, error in cases:
                with self.subTest(verify=verify.__name__), self.assertRaisesRegex(
                    error,
                    "installed command is missing or not executable",
                ):
                    verify(sys.executable, command_directory=tmp)

    def test_pilot_funnel_smoke_contract_passes_against_source(self) -> None:
        environment = os.environ.copy()
        environment["PYTHONPATH"] = str(ROOT / "src")

        checked = smoke_test_pilot_funnel.verify_pilot_funnel(
            sys.executable, environment=environment
        )

        self.assertEqual(
            checked,
            (
                "commercial-totals",
                "qualified-segmentation",
                "operator-text",
                "distribution-evidence",
                "joined-growth-review",
                "growth-boundaries",
                "invalid-growth-rejected",
                "invalid-distribution-rejected",
                "invalid-export-rejected",
            ),
        )

    def test_pilot_funnel_smoke_rejects_missing_installed_commands(self) -> None:
        with TemporaryDirectory() as tmp, self.assertRaisesRegex(
            smoke_test_pilot_funnel.SmokeTestError,
            "installed command is missing or not executable",
        ):
            smoke_test_pilot_funnel.verify_pilot_funnel(
                sys.executable,
                command_directory=tmp,
            )

    def test_rollout_summary_smoke_contract_passes_against_source(self) -> None:
        environment = os.environ.copy()
        environment["PYTHONPATH"] = str(ROOT / "src")

        checked = smoke_test_rollout_summary.verify_rollout_summary(
            sys.executable, environment=environment
        )

        self.assertEqual(
            checked,
            (
                "counts-only-summary",
                "shared-policy-remediation",
                "explicit-details",
                "duplicate-rejected",
            ),
        )

    def test_writes_deterministic_checksums_for_exact_artifacts(self) -> None:
        with TemporaryDirectory() as tmp:
            root, dist = self._project(Path(tmp), version="1.2.3")
            wheel = dist / "repo_scout-1.2.3-py3-none-any.whl"
            source = dist / "repo_scout-1.2.3.tar.gz"
            portable = dist / "repo-scout-1.2.3.pyz"
            wheel.write_bytes(b"wheel contents")
            source.write_bytes(b"source contents")
            portable.write_bytes(b"portable contents")

            manifest = prepare_release.prepare_release(root, dist, "v1.2.3")
            first = manifest.read_text(encoding="ascii")
            prepare_release.prepare_release(root, dist, "v1.2.3")

            self.assertEqual(manifest.read_text(encoding="ascii"), first)
            self.assertEqual(
                first,
                "".join(
                    [
                        f"{hashlib.sha256(wheel.read_bytes()).hexdigest()}  {wheel.name}\n",
                        f"{hashlib.sha256(source.read_bytes()).hexdigest()}  {source.name}\n",
                        f"{hashlib.sha256(portable.read_bytes()).hexdigest()}  {portable.name}\n",
                    ]
                ),
            )

    def test_rejects_tag_or_runtime_version_drift(self) -> None:
        with TemporaryDirectory() as tmp:
            root, dist = self._project(Path(tmp), version="1.2.3")
            self._write_artifacts(dist, "1.2.3")

            with self.assertRaisesRegex(prepare_release.ReleaseError, "does not match"):
                prepare_release.prepare_release(root, dist, "v1.2.4")
            with self.assertRaisesRegex(prepare_release.ReleaseError, "vMAJOR"):
                prepare_release.prepare_release(root, dist, "release-1.2.3")

            (root / "src/repo_scout/__init__.py").write_text(
                '__version__ = "1.2.4"\n', encoding="utf-8"
            )
            with self.assertRaisesRegex(prepare_release.ReleaseError, "version mismatch"):
                prepare_release.prepare_release(root, dist, "v1.2.3")

    def test_rejects_missing_or_unexpected_artifacts(self) -> None:
        with TemporaryDirectory() as tmp:
            root, dist = self._project(Path(tmp), version="1.2.3")
            (dist / "repo_scout-1.2.3-py3-none-any.whl").write_bytes(b"wheel")

            with self.assertRaisesRegex(prepare_release.ReleaseError, "missing regular"):
                prepare_release.prepare_release(root, dist, "v1.2.3")

            (dist / "repo_scout-1.2.3.tar.gz").write_bytes(b"source")
            (dist / "repo-scout-1.2.3.pyz").write_bytes(b"portable")
            (dist / "unreviewed.bin").write_bytes(b"extra")
            with self.assertRaisesRegex(prepare_release.ReleaseError, "unexpected"):
                prepare_release.prepare_release(root, dist, "v1.2.3")

    @staticmethod
    def _project(base: Path, *, version: str) -> tuple[Path, Path]:
        root = base / "project"
        package = root / "src" / "repo_scout"
        package.mkdir(parents=True)
        (root / "pyproject.toml").write_text(
            f'[project]\nname = "repo-scout"\nversion = "{version}"\n',
            encoding="utf-8",
        )
        (package / "__init__.py").write_text(
            f'__version__ = "{version}"\n', encoding="utf-8"
        )
        dist = root / "dist"
        dist.mkdir()
        return root, dist

    @staticmethod
    def _write_artifacts(dist: Path, version: str) -> None:
        (dist / f"repo_scout-{version}-py3-none-any.whl").write_bytes(b"wheel")
        (dist / f"repo_scout-{version}.tar.gz").write_bytes(b"source")
        (dist / f"repo-scout-{version}.pyz").write_bytes(b"portable")


class ZipappDistributionTests(unittest.TestCase):
    def test_builds_executable_primary_cli_with_packaged_templates(self) -> None:
        with TemporaryDirectory() as tmp:
            dist = Path(tmp) / "dist"

            artifact = build_zipapp.build_zipapp(ROOT, dist)

            self.assertEqual(artifact.name, "repo-scout-0.3.51.pyz")
            self.assertTrue(artifact.is_file())
            self.assertTrue(artifact.stat().st_mode & 0o100)
            with zipfile.ZipFile(artifact) as archive:
                names = set(archive.namelist())
            self.assertIn("__main__.py", names)
            self.assertIn("repo_scout/cli.py", names)
            self.assertIn(
                "repo_scout/templates/policies/python-service.toml", names
            )
            self.assertIn(
                "repo_scout/templates/policies/node-service.toml", names
            )
            self.assertFalse(
                any("__pycache__" in name or ".egg-info/" in name for name in names)
            )

            version = subprocess.run(
                [sys.executable, str(artifact), "--version"],
                capture_output=True,
                text=True,
            )
            self.assertEqual(version.returncode, 0, version.stderr)
            self.assertEqual(version.stdout, "repo-scout 0.3.51\n")

            target = Path(tmp) / "target"
            target.mkdir()
            subprocess.run(
                ["git", "init", "--quiet", str(target)],
                check=True,
                capture_output=True,
                text=True,
            )
            completed = subprocess.run(
                [sys.executable, str(artifact), "--format", "json", str(target)],
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            snapshot = json.loads(completed.stdout)
            self.assertEqual(snapshot["schema_version"], 1)
            self.assertEqual(snapshot["git"]["dirty_files"], 0)
            self.assertEqual(snapshot["files"]["total"], 0)

    def test_rejects_a_project_without_package_source(self) -> None:
        with TemporaryDirectory() as tmp, self.assertRaisesRegex(
            ValueError, "package source does not exist"
        ):
            build_zipapp.build_zipapp(Path(tmp), Path(tmp) / "dist")


class WheelContentComparisonTests(unittest.TestCase):
    def _write_wheel(
        self,
        path: Path,
        members: list[tuple[str, bytes, int]],
        *,
        timestamp: tuple[int, int, int, int, int, int],
        compression: int = zipfile.ZIP_STORED,
    ) -> None:
        with zipfile.ZipFile(path, "w") as archive:
            for name, contents, mode in members:
                info = zipfile.ZipInfo(name, timestamp)
                info.compress_type = compression
                info.external_attr = mode << 16
                archive.writestr(info, contents)

    def test_matches_logical_contents_across_archive_metadata(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            reference = root / "reference.whl"
            rebuilt = root / "rebuilt.whl"
            members = [
                ("repo_scout/__init__.py", b'__version__ = "1.2.3"\n', 0o100644),
                (
                    "repo_scout-1.2.3.dist-info/entry_points.txt",
                    b"[console_scripts]\nrepo-scout = repo_scout.cli:main\n",
                    0o100644,
                ),
            ]
            self._write_wheel(
                reference,
                members,
                timestamp=(2026, 1, 1, 0, 0, 0),
            )
            self._write_wheel(
                rebuilt,
                list(reversed(members)),
                timestamp=(2026, 7, 24, 0, 0, 0),
                compression=zipfile.ZIP_DEFLATED,
            )

            self.assertEqual(
                compare_wheel_contents.compare_wheel_contents(
                    reference,
                    rebuilt,
                ),
                2,
            )

    def test_rejects_missing_unexpected_changed_and_mode_drift(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            reference = root / "reference.whl"
            rebuilt = root / "rebuilt.whl"
            timestamp = (2026, 7, 24, 0, 0, 0)
            reference_members = [
                ("repo_scout/cli.py", b"contents\n", 0o100644),
                ("repo_scout/policy.py", b"policy\n", 0o100644),
            ]
            self._write_wheel(
                reference,
                reference_members,
                timestamp=timestamp,
            )

            cases = (
                (
                    [("repo_scout/cli.py", b"contents\n", 0o100644)],
                    "missing members: repo_scout/policy.py",
                ),
                (
                    reference_members
                    + [("repo_scout/extra.py", b"extra\n", 0o100644)],
                    "unexpected members: repo_scout/extra.py",
                ),
                (
                    [
                        ("repo_scout/cli.py", b"changed\n", 0o100644),
                        reference_members[1],
                    ],
                    "member content or mode differs: repo_scout/cli.py",
                ),
                (
                    [
                        ("repo_scout/cli.py", b"contents\n", 0o100600),
                        reference_members[1],
                    ],
                    "member content or mode differs: repo_scout/cli.py",
                ),
            )
            for members, message in cases:
                with self.subTest(message=message):
                    self._write_wheel(
                        rebuilt,
                        members,
                        timestamp=timestamp,
                    )
                    with self.assertRaisesRegex(
                        compare_wheel_contents.WheelComparisonError,
                        re.escape(message),
                    ):
                        compare_wheel_contents.compare_wheel_contents(
                            reference,
                            rebuilt,
                        )

    def test_rejects_duplicate_members_and_invalid_archives(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            reference = root / "reference.whl"
            rebuilt = root / "rebuilt.whl"
            member = ("repo_scout/cli.py", b"contents\n", 0o100644)
            self._write_wheel(
                reference,
                [member],
                timestamp=(2026, 7, 24, 0, 0, 0),
            )
            with (
                self.assertWarns(UserWarning),
                zipfile.ZipFile(rebuilt, "w") as archive,
            ):
                archive.writestr(member[0], member[1])
                archive.writestr(member[0], member[1])

            with self.assertRaisesRegex(
                compare_wheel_contents.WheelComparisonError,
                "rebuilt wheel contains duplicate members: repo_scout/cli.py",
            ):
                compare_wheel_contents.compare_wheel_contents(
                    reference,
                    rebuilt,
                )

            rebuilt.write_text("not a wheel\n", encoding="utf-8")
            stderr = StringIO()
            with redirect_stderr(stderr):
                self.assertEqual(
                    compare_wheel_contents.main([str(reference), str(rebuilt)]),
                    2,
                )
            self.assertIn("cannot read rebuilt wheel", stderr.getvalue())


class ReleaseWorkflowTests(unittest.TestCase):
    def test_declared_mit_license_has_distribution_text(self) -> None:
        pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
        license_text = (ROOT / "LICENSE").read_text(encoding="utf-8")

        self.assertIn('license = "MIT"', pyproject)
        self.assertIn("MIT License", license_text)
        self.assertIn("Permission is hereby granted", license_text)

    def test_release_workflow_is_pinned_and_attested(self) -> None:
        workflow = (ROOT / ".github/workflows/release.yml").read_text(
            encoding="utf-8"
        )
        with (ROOT / "pyproject.toml").open("rb") as project_file:
            packaged_commands = set(
                tomllib.load(project_file)["project"]["scripts"]
            )

        self.assertIn('      - "v[0-9]+.[0-9]+.[0-9]+"', workflow)
        self.assertNotIn("workflow_dispatch", workflow)
        self.assertIn("contents: write", workflow)
        self.assertIn("id-token: write", workflow)
        self.assertIn("attestations: write", workflow)
        self.assertIn("persist-credentials: false", workflow)
        self.assertIn("git merge-base --is-ancestor", workflow)
        self.assertIn("python -m unittest discover -s tests", workflow)
        self.assertIn("subject-checksums: dist/SHA256SUMS", workflow)
        self.assertIn('version="${GITHUB_REF_NAME#v}"', workflow)
        self.assertIn(
            '"$RUNNER_TEMP/repo-scout-release/bin/$command" --version',
            workflow,
        )
        self.assertIn('test "$actual" = "$command $version"', workflow)
        _, loop_heading, command_tail = workflow.partition(
            "          for command in \\\n"
        )
        command_block, loop_end, _ = command_tail.partition("; do")
        self.assertTrue(loop_heading)
        self.assertTrue(loop_end)
        smoke_commands = re.findall(
            r"^            (repo-scout(?:-[a-z]+)*)", command_block, re.MULTILINE
        )
        self.assertEqual(len(smoke_commands), len(set(smoke_commands)))
        self.assertEqual(set(smoke_commands), packaged_commands)
        self.assertIn(
            '"$RUNNER_TEMP/repo-scout-release/bin/repo-scout-distribution" --help',
            workflow,
        )
        self.assertIn(
            '"$RUNNER_TEMP/repo-scout-release/bin/repo-scout-growth" --help',
            workflow,
        )
        self.assertIn(
            "python scripts/smoke_test_policy_activation.py", workflow
        )
        self.assertIn(
            '--python "$RUNNER_TEMP/repo-scout-release/bin/python"', workflow
        )
        self.assertLess(
            workflow.index("python scripts/smoke_test_policy_activation.py"),
            workflow.index("- name: Attest release provenance"),
        )
        self.assertIn(
            '"$RUNNER_TEMP/repo-scout-release/bin/repo-scout-outreach" --help',
            workflow,
        )
        self.assertIn(
            "python scripts/smoke_test_outreach_lifecycle.py", workflow
        )
        self.assertLess(
            workflow.index("python scripts/smoke_test_outreach_lifecycle.py"),
            workflow.index("- name: Attest release provenance"),
        )
        self.assertIn("python scripts/smoke_test_pilot_funnel.py", workflow)
        self.assertIn(
            '--command-directory "$RUNNER_TEMP/repo-scout-release/bin"',
            workflow,
        )
        self.assertEqual(
            workflow.count(
                '--command-directory "$RUNNER_TEMP/repo-scout-release/bin"'
            ),
            4,
        )
        self.assertLess(
            workflow.index("python scripts/smoke_test_pilot_funnel.py"),
            workflow.index("- name: Attest release provenance"),
        )
        self.assertIn(
            '"$RUNNER_TEMP/repo-scout-release/bin/repo-scout-rollout" --help',
            workflow,
        )
        self.assertIn("python scripts/smoke_test_rollout_summary.py", workflow)
        self.assertLess(
            workflow.index("python scripts/smoke_test_rollout_summary.py"),
            workflow.index("- name: Attest release provenance"),
        )
        self.assertIn('python "dist/repo-scout-${version}.pyz" --help', workflow)
        self.assertIn(
            'python "dist/repo-scout-${version}.pyz" --version',
            workflow,
        )
        self.assertIn("dist/repo-scout-*.pyz", workflow)
        self.assertIn('gh release create "$GITHUB_REF_NAME"', workflow)
        self.assertIn("--verify-tag", workflow)
        self.assertNotIn("pull_request_target", workflow)
        self.assertNotIn("continue-on-error", workflow)
        self.assertNotIn("|| true", workflow)

        expected_actions = {
            "actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1",
            "actions/setup-python@5fda3b95a4ea91299a34e894583c3862153e4b97",
            "actions/attest-build-provenance@0f67c3f4856b2e3261c31976d6725780e5e4c373",
        }
        actions = set(
            re.findall(r"^\s*uses:\s*([^\s#]+)", workflow, re.MULTILINE)
        )
        self.assertEqual(actions, expected_actions)
        for action in actions:
            self.assertRegex(action, r"^[\w.-]+/[\w.-]+@[0-9a-f]{40}$")

    def test_release_tag_guard_requires_an_annotated_exact_commit(self) -> None:
        workflow = (ROOT / ".github/workflows/release.yml").read_text(
            encoding="utf-8"
        )
        marker = "      - name: Require an annotated release tag\n"
        next_marker = "      - name: Require a main-branch release commit\n"
        self.assertIn(marker, workflow)
        self.assertIn(next_marker, workflow)
        self.assertLess(workflow.index(marker), workflow.index(next_marker))

        guard_step = workflow[
            workflow.index(marker) : workflow.index(next_marker)
        ]
        self.assertIn("        run: |\n", guard_step)
        guard_script = textwrap.dedent(
            guard_step.split("        run: |\n", 1)[1]
        )
        self.assertIn('git cat-file -t "$tag_ref"', guard_script)
        self.assertIn('git rev-parse "${tag_ref}^{commit}"', guard_script)
        self.assertIn("must be an annotated tag", guard_script)
        self.assertIn("instead of push commit", guard_script)
        self.assertNotIn("|| true", guard_script)

        with TemporaryDirectory() as tmp:
            repository = Path(tmp) / "repository"
            subprocess.run(
                ["git", "init", "--quiet", str(repository)],
                check=True,
                capture_output=True,
                text=True,
            )

            def run_git(*args: str) -> str:
                return subprocess.run(
                    ["git", *args],
                    cwd=repository,
                    check=True,
                    capture_output=True,
                    text=True,
                ).stdout.strip()

            def run_guard(expected_sha: str) -> subprocess.CompletedProcess[str]:
                environment = os.environ.copy()
                environment["GITHUB_REF_NAME"] = "v1.2.3"
                environment["GITHUB_SHA"] = expected_sha
                return subprocess.run(
                    ["bash", "-e"],
                    input=guard_script,
                    cwd=repository,
                    env=environment,
                    capture_output=True,
                    text=True,
                )

            run_git("config", "user.name", "Repo Scout Tests")
            run_git("config", "user.email", "tests@example.com")
            tracked = repository / "tracked.txt"
            tracked.write_text("first\n", encoding="utf-8")
            run_git("add", "tracked.txt")
            run_git("commit", "--quiet", "-m", "first")
            first_commit = run_git("rev-parse", "HEAD")

            tracked.write_text("second\n", encoding="utf-8")
            run_git("commit", "--quiet", "-am", "second")
            second_commit = run_git("rev-parse", "HEAD")
            run_git(
                "tag",
                "--annotate",
                "v1.2.3",
                first_commit,
                "--message",
                "Repo Scout v1.2.3",
            )

            annotated = run_guard(first_commit)
            self.assertEqual(annotated.returncode, 0, annotated.stderr)

            wrong_commit = run_guard(second_commit)
            self.assertNotEqual(wrong_commit.returncode, 0)
            self.assertIn("instead of push commit", wrong_commit.stderr)

            run_git("tag", "--delete", "v1.2.3")
            run_git("tag", "v1.2.3", first_commit)
            lightweight = run_guard(first_commit)
            self.assertNotEqual(lightweight.returncode, 0)
            self.assertIn("must be an annotated tag", lightweight.stderr)

    def test_release_checksums_are_revalidated_after_smoke_tests(self) -> None:
        workflow = (ROOT / ".github/workflows/release.yml").read_text(
            encoding="utf-8"
        )
        smoke_marker = "      - name: Smoke test the portable zipapp\n"
        verify_marker = "      - name: Revalidate release checksums\n"
        attest_marker = "      - name: Attest release provenance\n"
        for marker in (smoke_marker, verify_marker, attest_marker):
            self.assertIn(marker, workflow)
        self.assertLess(
            workflow.index(smoke_marker), workflow.index(verify_marker)
        )
        self.assertLess(
            workflow.index(verify_marker), workflow.index(attest_marker)
        )

        verify_step = workflow[
            workflow.index(verify_marker) : workflow.index(attest_marker)
        ]
        self.assertIn("        working-directory: dist\n", verify_step)
        self.assertIn("        run: |\n", verify_step)
        verify_script = textwrap.dedent(
            verify_step.split("        run: |\n", 1)[1]
        )
        self.assertIn("sha256sum --check SHA256SUMS", verify_script)
        self.assertIn("shasum -a 256 -c SHA256SUMS", verify_script)
        self.assertNotIn("--ignore-missing", verify_script)
        self.assertNotIn("|| true", verify_script)

        with TemporaryDirectory() as tmp:
            dist = Path(tmp)
            artifacts = {
                "repo-scout-1.2.3.pyz": b"portable artifact\n",
                "repo_scout-1.2.3-py3-none-any.whl": b"wheel artifact\n",
                "repo_scout-1.2.3.tar.gz": b"source artifact\n",
            }
            for name, contents in artifacts.items():
                (dist / name).write_bytes(contents)
            manifest = "".join(
                f"{hashlib.sha256(contents).hexdigest()}  {name}\n"
                for name, contents in artifacts.items()
            )
            (dist / "SHA256SUMS").write_text(manifest, encoding="utf-8")

            verified = subprocess.run(
                ["bash", "-e"],
                input=verify_script,
                cwd=dist,
                capture_output=True,
                text=True,
            )
            self.assertEqual(verified.returncode, 0, verified.stderr)

            mutated = dist / "repo_scout-1.2.3-py3-none-any.whl"
            mutated.write_bytes(mutated.read_bytes() + b"post-manifest mutation\n")
            rejected = subprocess.run(
                ["bash", "-e"],
                input=verify_script,
                cwd=dist,
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(rejected.returncode, 0)
            self.assertIn("FAILED", rejected.stdout + rejected.stderr)

    def test_release_smoke_installs_only_the_exact_local_wheel(self) -> None:
        workflow = (ROOT / ".github/workflows/release.yml").read_text(
            encoding="utf-8"
        )
        smoke_marker = "      - name: Smoke test the built wheel\n"
        next_marker = "      - name: Smoke test the portable zipapp\n"
        self.assertIn(smoke_marker, workflow)
        self.assertIn(next_marker, workflow)
        smoke_step = workflow[
            workflow.index(smoke_marker) : workflow.index(next_marker)
        ]
        self.assertIn("        run: |\n", smoke_step)
        smoke_script = textwrap.dedent(
            smoke_step.split("        run: |\n", 1)[1]
        )

        version_marker = 'version="${GITHUB_REF_NAME#v}"'
        install_marker = (
            '"$RUNNER_TEMP/repo-scout-release/bin/python" -m pip install \\\n'
        )
        self.assertIn(version_marker, smoke_script)
        self.assertIn(install_marker, smoke_script)
        self.assertLess(
            smoke_script.index(version_marker),
            smoke_script.index(install_marker),
        )
        self.assertIn("--disable-pip-version-check", smoke_script)
        self.assertIn("--no-index", smoke_script)
        self.assertIn("--no-deps", smoke_script)
        self.assertIn(
            '"dist/repo_scout-${version}-py3-none-any.whl"',
            smoke_script,
        )
        self.assertNotIn("dist/*.whl", smoke_script)
        self.assertNotIn("--index-url", smoke_script)
        self.assertNotIn("--extra-index-url", smoke_script)
        self.assertNotIn("--find-links", smoke_script)
        self.assertEqual(smoke_script.count("pip install"), 1)

    def test_release_rebuilds_exact_source_distribution_offline(self) -> None:
        workflow = (ROOT / ".github/workflows/release.yml").read_text(
            encoding="utf-8"
        )
        validate_marker = "      - name: Validate version and write checksums\n"
        source_marker = "      - name: Verify source distribution rebuild\n"
        smoke_marker = "      - name: Smoke test the built wheel\n"
        for marker in (validate_marker, source_marker, smoke_marker):
            self.assertIn(marker, workflow)
        self.assertLess(workflow.index(validate_marker), workflow.index(source_marker))
        self.assertLess(workflow.index(source_marker), workflow.index(smoke_marker))

        source_step = workflow[
            workflow.index(source_marker) : workflow.index(smoke_marker)
        ]
        self.assertIn("        run: |\n", source_step)
        source_script = textwrap.dedent(
            source_step.split("        run: |\n", 1)[1]
        )
        build_python = '"$RUNNER_TEMP/repo-scout-release-build/bin/python"'
        self.assertIn('version="${GITHUB_REF_NAME#v}"', source_script)
        self.assertIn(
            'rebuilt_wheels="$RUNNER_TEMP/repo-scout-release-sdist-wheels"',
            source_script,
        )
        self.assertIn(f"{build_python} -m pip wheel \\\n", source_script)
        self.assertIn("--disable-pip-version-check", source_script)
        self.assertIn("--no-cache-dir", source_script)
        self.assertIn("--no-index", source_script)
        self.assertIn("--no-deps", source_script)
        self.assertIn("--no-build-isolation", source_script)
        self.assertIn('--wheel-dir "$rebuilt_wheels"', source_script)
        self.assertIn('"dist/repo_scout-${version}.tar.gz"', source_script)
        self.assertIn(
            f"{build_python} \\\n"
            "  scripts/compare_wheel_contents.py \\\n",
            source_script,
        )
        self.assertIn(
            '"dist/repo_scout-${version}-py3-none-any.whl" \\\n',
            source_script,
        )
        self.assertIn(
            '"$rebuilt_wheels/repo_scout-${version}-py3-none-any.whl"',
            source_script,
        )
        self.assertNotIn("*.tar.gz", source_script)
        self.assertNotIn("*.whl", source_script)
        self.assertNotIn("--index-url", source_script)
        self.assertNotIn("--extra-index-url", source_script)
        self.assertNotIn("--find-links", source_script)
        self.assertNotIn("|| true", source_script)

    def test_release_build_uses_a_force_verified_isolated_toolchain(self) -> None:
        workflow = (ROOT / ".github/workflows/release.yml").read_text(
            encoding="utf-8"
        )
        install_marker = "      - name: Verify hash-locked build tools\n"
        zipapp_marker = "      - name: Build portable zipapp\n"
        package_marker = "      - name: Build wheel and source distribution\n"
        validate_marker = "      - name: Validate version and write checksums\n"
        source_marker = "      - name: Verify source distribution rebuild\n"
        smoke_marker = "      - name: Smoke test the built wheel\n"
        for marker in (
            install_marker,
            zipapp_marker,
            package_marker,
            validate_marker,
            source_marker,
            smoke_marker,
        ):
            self.assertIn(marker, workflow)
        self.assertLess(workflow.index(install_marker), workflow.index(zipapp_marker))
        self.assertLess(workflow.index(zipapp_marker), workflow.index(package_marker))
        self.assertLess(workflow.index(package_marker), workflow.index(validate_marker))
        self.assertLess(workflow.index(validate_marker), workflow.index(source_marker))
        self.assertLess(workflow.index(source_marker), workflow.index(smoke_marker))

        install_step = workflow[
            workflow.index(install_marker) : workflow.index(zipapp_marker)
        ]
        self.assertIn("        run: |\n", install_step)
        install_script = textwrap.dedent(
            install_step.split("        run: |\n", 1)[1]
        )
        self.assertIn(
            'build_venv="$RUNNER_TEMP/repo-scout-release-build"',
            install_script,
        )
        self.assertIn('python -m venv "$build_venv"', install_script)
        self.assertIn(
            '"$build_venv/bin/python" -m pip install \\\n',
            install_script,
        )
        self.assertIn("--disable-pip-version-check", install_script)
        self.assertIn("--require-hashes", install_script)
        self.assertIn("--force-reinstall", install_script)
        self.assertIn("-r .github/release-requirements.txt", install_script)
        self.assertIn(
            '"$build_venv/bin/python" -m pip check',
            install_script,
        )
        self.assertEqual(install_script.count("pip install"), 1)
        self.assertNotIn("source ", install_script)

        build_python = (
            '"$RUNNER_TEMP/repo-scout-release-build/bin/python"'
        )
        zipapp_step = workflow[
            workflow.index(zipapp_marker) : workflow.index(package_marker)
        ]
        package_step = workflow[
            workflow.index(package_marker) : workflow.index(validate_marker)
        ]
        validate_step = workflow[
            workflow.index(validate_marker) : workflow.index(source_marker)
        ]
        self.assertIn(
            f"{build_python}\n          scripts/build_zipapp.py --dist dist",
            zipapp_step,
        )
        self.assertIn(
            f"{build_python} -m build\n"
            "          --no-isolation --sdist --wheel --outdir dist",
            package_step,
        )
        self.assertIn(
            f"{build_python}\n          scripts/prepare_release.py",
            validate_step,
        )
        self.assertEqual(workflow.count(build_python), 5)

    def test_release_publication_requires_immutable_release_evidence(self) -> None:
        workflow = (ROOT / ".github/workflows/release.yml").read_text(
            encoding="utf-8"
        )
        marker = "      - name: Publish and verify immutable GitHub release\n"
        self.assertIn(marker, workflow)
        publish_step = workflow[workflow.index(marker) :]
        publish_script = textwrap.dedent(
            publish_step.split("        run: |\n", 1)[1]
        )

        self.assertIn('gh release create "$GITHUB_REF_NAME"', publish_script)
        self.assertIn(
            '"repos/${GITHUB_REPOSITORY}/releases/tags/${GITHUB_REF_NAME}"',
            publish_script,
        )
        self.assertIn("Accept: application/vnd.github+json", publish_script)
        self.assertIn("X-GitHub-Api-Version: 2026-03-10", publish_script)
        self.assertIn("--jq '.immutable'", publish_script)
        self.assertLess(
            publish_script.index("gh release create"),
            publish_script.index("gh api"),
        )

        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            fake_bin = root / "bin"
            fake_bin.mkdir()
            log = root / "gh-log"
            fake_gh = fake_bin / "gh"
            fake_gh.write_text(
                f"#!{sys.executable}\n"
                "import os\n"
                "from pathlib import Path\n"
                "import shlex\n"
                "import sys\n"
                "log = Path(os.environ['FAKE_GH_LOG'])\n"
                "with log.open('a', encoding='utf-8') as output:\n"
                "    output.write(shlex.join(sys.argv[1:]) + '\\n')\n"
                "if sys.argv[1] == 'api':\n"
                "    if os.environ.get('FAKE_GH_API_FAIL') == '1':\n"
                "        raise SystemExit(1)\n"
                "    print(os.environ['FAKE_RELEASE_IMMUTABLE'])\n",
                encoding="utf-8",
            )
            fake_gh.chmod(0o755)

            for immutable, api_fail, expected_success in (
                ("true", "0", True),
                ("false", "0", False),
                ("unexpected", "0", False),
                ("true", "1", False),
            ):
                with self.subTest(immutable=immutable, api_fail=api_fail):
                    log.write_text("", encoding="utf-8")
                    environment = os.environ.copy()
                    environment.update(
                        {
                            "FAKE_GH_API_FAIL": api_fail,
                            "FAKE_GH_LOG": str(log),
                            "FAKE_RELEASE_IMMUTABLE": immutable,
                            "GH_TOKEN": "test-token",
                            "GITHUB_REF_NAME": "v0.3.50",
                            "GITHUB_REPOSITORY": "example/repo-scout",
                            "PATH": f"{fake_bin}{os.pathsep}{environment['PATH']}",
                        }
                    )
                    completed = subprocess.run(
                        ["bash", "-e"],
                        input=publish_script,
                        env=environment,
                        capture_output=True,
                        text=True,
                    )

                    self.assertEqual(completed.returncode == 0, expected_success)
                    calls = log.read_text(encoding="utf-8").splitlines()
                    self.assertEqual(len(calls), 2)
                    self.assertTrue(calls[0].startswith("release create "))
                    self.assertTrue(calls[1].startswith("api "))

    def test_release_requirements_are_exactly_pinned_and_hashed(self) -> None:
        requirements = (
            ROOT / ".github/release-requirements.txt"
        ).read_text(encoding="utf-8")

        self.assertEqual(
            requirements,
            "# Release-only build dependencies. Every downloaded wheel is "
            "hash-verified.\n"
            "build==1.3.0 \\\n"
            "    --hash=sha256:"
            "7145f0b5061ba90a1500d60bd1b13ca0a8a4cebdd0cc16ed8adf1c0e739f43b4\n"
            "packaging==25.0 \\\n"
            "    --hash=sha256:"
            "29572ef2b1f17581046b3a2227d5c611fb25ec70ca1ba8554b24b0e69331a484\n"
            "pyproject-hooks==1.2.0 \\\n"
            "    --hash=sha256:"
            "9e5c6bfa8dcc30091c74b0cf803c81fdd29d94f01992a7707bc97babb1141913\n"
            "setuptools==83.0.0 \\\n"
            "    --hash=sha256:"
            "29b23c360f22f414dc7336bb39178cc7bcbf6021ed2733cde173f09dba19abb3\n",
        )


if __name__ == "__main__":
    unittest.main()
