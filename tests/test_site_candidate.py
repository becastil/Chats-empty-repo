from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tarfile
from tempfile import TemporaryDirectory
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "prepare_site_candidate.py"
SPEC = importlib.util.spec_from_file_location(
    "prepare_site_candidate",
    SCRIPT_PATH,
)
assert SPEC is not None
assert SPEC.loader is not None
prepare_site_candidate = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = prepare_site_candidate
SPEC.loader.exec_module(prepare_site_candidate)

COMMIT_SHA = "a" * 40
PROJECT_ID = "appgprj_test"


class FakeCommandRunner:
    def __init__(
        self,
        root: Path,
        archive: Path,
        *,
        status: str = "",
        origin_sha: str = COMMIT_SHA,
        node_version: str = "v22.13.0",
        include_manifest: bool = True,
    ) -> None:
        self.root = root
        self.archive = archive
        self.status = status
        self.origin_sha = origin_sha
        self.node_version = node_version
        self.include_manifest = include_manifest
        self.commands: list[tuple[str, ...]] = []

    def __call__(self, command: list[str] | tuple[str, ...], root: Path) -> str:
        normalized = tuple(command)
        self.commands.append(normalized)
        self.assert_root(root)
        if normalized == (
            "git",
            "status",
            "--porcelain",
            "--untracked-files=all",
        ):
            return self.status
        if normalized == ("git", "rev-parse", "HEAD"):
            return COMMIT_SHA
        if normalized == ("git", "rev-parse", "origin/main"):
            return self.origin_sha
        if normalized == ("node", "--version"):
            return self.node_version
        if normalized == ("npm", "test"):
            server = self.root / "dist" / "server" / "index.js"
            server.parent.mkdir(parents=True, exist_ok=True)
            server.write_text("export default {};\n", encoding="utf-8")
            return ""
        if normalized in prepare_site_candidate.VALIDATION_COMMANDS:
            return ""
        if len(normalized) == 3 and normalized[1] == str(self.root):
            self._package()
            return str(self.archive)
        raise AssertionError(f"unexpected command: {normalized}")

    def assert_root(self, root: Path) -> None:
        if root != self.root:
            raise AssertionError(f"unexpected command root: {root}")

    def _package(self) -> None:
        self.archive.parent.mkdir(parents=True, exist_ok=True)
        with tarfile.open(self.archive, "w:gz") as bundle:
            paths = (
                (
                    self.root / "dist" / "server" / "index.js",
                    "dist/server/index.js",
                ),
                (
                    self.root / ".openai" / "hosting.json",
                    "dist/.openai/hosting.json",
                ),
                (
                    self.root
                    / "dist"
                    / ".openai"
                    / "site-candidate.json",
                    "dist/.openai/site-candidate.json",
                ),
            )
            for source, archive_name in paths:
                if (
                    archive_name == "dist/.openai/site-candidate.json"
                    and not self.include_manifest
                ):
                    continue
                bundle.add(source, arcname=archive_name)


class SiteCandidateTests(unittest.TestCase):
    def test_prepares_a_provenance_bound_archive_and_receipt(self) -> None:
        with TemporaryDirectory() as tmp:
            root, archive, receipt, package_script = self._fixture(Path(tmp))
            runner = FakeCommandRunner(root, archive)

            result = prepare_site_candidate.prepare_site_candidate(
                root,
                archive,
                receipt,
                package_script,
                run_command=runner,
            )

            expected_lock_sha = hashlib.sha256(
                (root / "package-lock.json").read_bytes()
            ).hexdigest()
            receipt_payload = json.loads(receipt.read_text(encoding="utf-8"))
            self.assertEqual(result.commit_sha, COMMIT_SHA)
            self.assertEqual(
                receipt_payload["candidate"],
                {
                    "schema_version": 1,
                    "commit_sha": COMMIT_SHA,
                    "source_ref": "refs/heads/main",
                    "node_version": "22.13.0",
                    "package_lock_sha256": expected_lock_sha,
                    "project_id": PROJECT_ID,
                },
            )
            self.assertEqual(
                receipt_payload["archive"]["sha256"],
                hashlib.sha256(archive.read_bytes()).hexdigest(),
            )
            self.assertEqual(
                runner.commands,
                [
                    (
                        "git",
                        "status",
                        "--porcelain",
                        "--untracked-files=all",
                    ),
                    ("git", "rev-parse", "HEAD"),
                    ("git", "rev-parse", "origin/main"),
                    ("node", "--version"),
                    *prepare_site_candidate.VALIDATION_COMMANDS,
                    (
                        "git",
                        "status",
                        "--porcelain",
                        "--untracked-files=all",
                    ),
                    (
                        str(package_script),
                        str(root),
                        str(archive),
                    ),
                    (
                        "git",
                        "status",
                        "--porcelain",
                        "--untracked-files=all",
                    ),
                ],
            )

    def test_rejects_a_dirty_checkout_before_validation(self) -> None:
        with TemporaryDirectory() as tmp:
            root, archive, receipt, package_script = self._fixture(Path(tmp))
            runner = FakeCommandRunner(
                root,
                archive,
                status=" M package-lock.json",
            )

            with self.assertRaisesRegex(
                prepare_site_candidate.SiteCandidateError,
                "worktree must be clean",
            ):
                prepare_site_candidate.prepare_site_candidate(
                    root,
                    archive,
                    receipt,
                    package_script,
                    run_command=runner,
                )

            self.assertEqual(
                runner.commands,
                [
                    (
                        "git",
                        "status",
                        "--porcelain",
                        "--untracked-files=all",
                    )
                ],
            )

    def test_rejects_source_that_is_not_origin_main(self) -> None:
        with TemporaryDirectory() as tmp:
            root, archive, receipt, package_script = self._fixture(Path(tmp))
            runner = FakeCommandRunner(
                root,
                archive,
                origin_sha="b" * 40,
            )

            with self.assertRaisesRegex(
                prepare_site_candidate.SiteCandidateError,
                "does not match origin/main",
            ):
                prepare_site_candidate.prepare_site_candidate(
                    root,
                    archive,
                    receipt,
                    package_script,
                    run_command=runner,
                )

    def test_rejects_runtime_drift_from_hosted_validation(self) -> None:
        with TemporaryDirectory() as tmp:
            root, archive, receipt, package_script = self._fixture(Path(tmp))
            runner = FakeCommandRunner(
                root,
                archive,
                node_version="v26.0.0",
            )

            with self.assertRaisesRegex(
                prepare_site_candidate.SiteCandidateError,
                "requires Node 22.13.0; found v26.0.0",
            ):
                prepare_site_candidate.prepare_site_candidate(
                    root,
                    archive,
                    receipt,
                    package_script,
                    run_command=runner,
                )

    def test_rejects_an_archive_without_the_bound_manifest(self) -> None:
        with TemporaryDirectory() as tmp:
            root, archive, receipt, package_script = self._fixture(Path(tmp))
            runner = FakeCommandRunner(
                root,
                archive,
                include_manifest=False,
            )

            with self.assertRaisesRegex(
                prepare_site_candidate.SiteCandidateError,
                "archive is missing regular file "
                "dist/.openai/site-candidate.json",
            ):
                prepare_site_candidate.prepare_site_candidate(
                    root,
                    archive,
                    receipt,
                    package_script,
                    run_command=runner,
                )

            self.assertFalse(receipt.exists())

    def test_rejects_a_colliding_archive_and_receipt_path(self) -> None:
        with TemporaryDirectory() as tmp:
            root, archive, _, package_script = self._fixture(Path(tmp))
            runner = FakeCommandRunner(root, archive)

            with self.assertRaisesRegex(
                prepare_site_candidate.SiteCandidateError,
                "archive and receipt must use different output paths",
            ):
                prepare_site_candidate.prepare_site_candidate(
                    root,
                    archive,
                    archive,
                    package_script,
                    run_command=runner,
                )

            self.assertEqual(runner.commands, [])

    def test_expected_node_matches_the_hosted_dependency_contract(self) -> None:
        workflow = (
            ROOT / ".github" / "workflows" / "site-dependencies.yml"
        ).read_text(encoding="utf-8")

        self.assertEqual(
            prepare_site_candidate.EXPECTED_NODE_VERSION,
            "22.13.0",
        )
        self.assertIn(
            f'node-version: "{prepare_site_candidate.EXPECTED_NODE_VERSION}"',
            workflow,
        )

    @staticmethod
    def _fixture(tmp: Path) -> tuple[Path, Path, Path, Path]:
        root = tmp / "project"
        root.mkdir()
        (root / "package-lock.json").write_text(
            '{"lockfileVersion": 3}\n',
            encoding="utf-8",
        )
        hosting = root / ".openai" / "hosting.json"
        hosting.parent.mkdir()
        hosting.write_text(
            json.dumps({"project_id": PROJECT_ID}) + "\n",
            encoding="utf-8",
        )
        package_script = tmp / "package-site.sh"
        package_script.write_text("#!/usr/bin/env bash\n", encoding="utf-8")
        package_script.chmod(0o755)
        return (
            root.resolve(),
            (tmp / "candidate.tar.gz").resolve(),
            (tmp / "candidate-receipt.json").resolve(),
            package_script.resolve(),
        )


if __name__ == "__main__":
    unittest.main()
