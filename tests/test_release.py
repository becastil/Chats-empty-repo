from __future__ import annotations

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from tempfile import TemporaryDirectory
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


class ReleaseManifestTests(unittest.TestCase):
    def test_current_project_versions_match(self) -> None:
        self.assertEqual(prepare_release.load_project_version(ROOT), "0.3.27")

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

            self.assertEqual(artifact.name, "repo-scout-0.3.27.pyz")
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

        self.assertIn('      - "v[0-9]+.[0-9]+.[0-9]+"', workflow)
        self.assertNotIn("workflow_dispatch", workflow)
        self.assertIn("contents: write", workflow)
        self.assertIn("id-token: write", workflow)
        self.assertIn("attestations: write", workflow)
        self.assertIn("persist-credentials: false", workflow)
        self.assertIn("git merge-base --is-ancestor", workflow)
        self.assertIn("python -m unittest discover -s tests", workflow)
        self.assertIn("pip install --require-hashes", workflow)
        self.assertIn("python -m build --no-isolation --sdist --wheel", workflow)
        self.assertIn("python scripts/build_zipapp.py --dist dist", workflow)
        self.assertIn("subject-checksums: dist/SHA256SUMS", workflow)
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
            '"$RUNNER_TEMP/repo-scout-release/bin/repo-scout-rollout" --help',
            workflow,
        )
        self.assertIn('python "dist/repo-scout-${version}.pyz" --help', workflow)
        self.assertIn("dist/repo-scout-*.pyz", workflow)
        self.assertIn('gh release create "$GITHUB_REF_NAME"', workflow)
        self.assertIn("--verify-tag", workflow)
        self.assertNotIn("pull_request_target", workflow)
        self.assertNotIn("continue-on-error", workflow)
        self.assertNotIn("|| true", workflow)

        expected_actions = {
            "actions/checkout@9c091bb21b7c1c1d1991bb908d89e4e9dddfe3e0",
            "actions/setup-python@ece7cb06caefa5fff74198d8649806c4678c61a1",
            "actions/attest-build-provenance@0f67c3f4856b2e3261c31976d6725780e5e4c373",
        }
        actions = set(
            re.findall(r"^\s*uses:\s*([^\s#]+)", workflow, re.MULTILINE)
        )
        self.assertEqual(actions, expected_actions)
        for action in actions:
            self.assertRegex(action, r"^[\w.-]+/[\w.-]+@[0-9a-f]{40}$")

    def test_release_requirements_are_exactly_pinned_and_hashed(self) -> None:
        requirements = (
            ROOT / ".github/release-requirements.txt"
        ).read_text(encoding="utf-8")
        packages = re.findall(r"^([\w-]+)==([^\s\\]+)", requirements, re.MULTILINE)
        hashes = re.findall(r"--hash=sha256:([0-9a-f]{64})", requirements)

        self.assertEqual(
            packages,
            [
                ("build", "1.3.0"),
                ("packaging", "25.0"),
                ("pyproject-hooks", "1.2.0"),
                ("setuptools", "80.9.0"),
            ],
        )
        self.assertEqual(len(hashes), len(packages))


if __name__ == "__main__":
    unittest.main()
