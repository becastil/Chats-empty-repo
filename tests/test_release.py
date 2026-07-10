from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
import re
import sys
from tempfile import TemporaryDirectory
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "prepare_release.py"
SPEC = importlib.util.spec_from_file_location("prepare_release", SCRIPT_PATH)
assert SPEC is not None and SPEC.loader is not None
prepare_release = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = prepare_release
SPEC.loader.exec_module(prepare_release)


class ReleaseManifestTests(unittest.TestCase):
    def test_current_project_versions_match(self) -> None:
        self.assertEqual(prepare_release.load_project_version(ROOT), "0.3.0")

    def test_writes_deterministic_checksums_for_exact_artifacts(self) -> None:
        with TemporaryDirectory() as tmp:
            root, dist = self._project(Path(tmp), version="1.2.3")
            wheel = dist / "repo_scout-1.2.3-py3-none-any.whl"
            source = dist / "repo_scout-1.2.3.tar.gz"
            wheel.write_bytes(b"wheel contents")
            source.write_bytes(b"source contents")

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
        self.assertIn("subject-checksums: dist/SHA256SUMS", workflow)
        self.assertIn(
            '"$RUNNER_TEMP/repo-scout-release/bin/repo-scout-rollout" --help',
            workflow,
        )
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
