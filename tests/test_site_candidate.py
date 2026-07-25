from __future__ import annotations

from contextlib import redirect_stdout
import hashlib
import importlib.util
from io import BytesIO, StringIO
import json
from pathlib import Path
import sys
import tarfile
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch


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
        extra_member_name: str | None = None,
        extra_member_type: bytes = tarfile.REGTYPE,
        mutate_server_before_package: bool = False,
    ) -> None:
        self.root = root
        self.archive = archive
        self.status = status
        self.origin_sha = origin_sha
        self.node_version = node_version
        self.include_manifest = include_manifest
        self.extra_member_name = extra_member_name
        self.extra_member_type = extra_member_type
        self.mutate_server_before_package = mutate_server_before_package
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
        if (
            len(normalized) == 5
            and normalized[:2] == prepare_site_candidate.PACKAGING_ENV
            and normalized[3] == str(self.root)
        ):
            if self.mutate_server_before_package:
                server = self.root / "dist" / "server" / "index.js"
                server.write_text(
                    "export default { tampered: true };\n",
                    encoding="utf-8",
                )
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
            drizzle = self.root / "drizzle"
            if drizzle.is_dir():
                for source in sorted(drizzle.rglob("*")):
                    if source.is_file():
                        relative = source.relative_to(drizzle).as_posix()
                        bundle.add(
                            source,
                            arcname=f"dist/.openai/drizzle/{relative}",
                        )
            if self.extra_member_name is not None:
                member = tarfile.TarInfo(self.extra_member_name)
                member.type = self.extra_member_type
                content: BytesIO | None = None
                if member.isfile():
                    content = BytesIO(b"unexpected candidate content\n")
                    member.size = len(content.getvalue())
                bundle.addfile(member, content)


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
            self.assertEqual(receipt_payload["schema_version"], 2)
            self.assertEqual(
                receipt_payload["candidate"],
                {
                    "schema_version": 2,
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
            self.assertRegex(
                receipt_payload["archive"]["payload_sha256"],
                r"^[0-9a-f]{64}$",
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
                        *prepare_site_candidate.PACKAGING_ENV,
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

    def test_independently_verifies_without_build_or_package_commands(
        self,
    ) -> None:
        with TemporaryDirectory() as tmp:
            root, archive, receipt, package_script = self._fixture(Path(tmp))
            prepare_runner = FakeCommandRunner(root, archive)
            prepare_site_candidate.prepare_site_candidate(
                root,
                archive,
                receipt,
                package_script,
                run_command=prepare_runner,
            )
            verify_runner = FakeCommandRunner(root, archive)

            result = prepare_site_candidate.verify_site_candidate(
                root,
                archive,
                receipt,
                run_command=verify_runner,
            )

            self.assertEqual(result.commit_sha, COMMIT_SHA)
            self.assertEqual(
                verify_runner.commands,
                [
                    (
                        "git",
                        "status",
                        "--porcelain",
                        "--untracked-files=all",
                    ),
                    ("git", "rev-parse", "HEAD"),
                    ("git", "rev-parse", "origin/main"),
                ],
            )

    def test_payload_binding_includes_the_drizzle_overlay(self) -> None:
        with TemporaryDirectory() as tmp:
            root, archive, receipt, package_script = self._fixture(Path(tmp))
            migration = root / "drizzle" / "0001_policy.sql"
            migration.parent.mkdir()
            migration.write_text(
                "CREATE TABLE policies (id INTEGER PRIMARY KEY);\n",
                encoding="utf-8",
            )

            prepare_site_candidate.prepare_site_candidate(
                root,
                archive,
                receipt,
                package_script,
                run_command=FakeCommandRunner(root, archive),
            )
            result = prepare_site_candidate.verify_site_candidate(
                root,
                archive,
                receipt,
                run_command=FakeCommandRunner(root, archive),
            )

            self.assertEqual(result.commit_sha, COMMIT_SHA)

    def test_verification_rejects_archive_bytes_changed_after_preparation(
        self,
    ) -> None:
        with TemporaryDirectory() as tmp:
            root, archive, receipt, package_script = self._fixture(Path(tmp))
            runner = FakeCommandRunner(root, archive)
            prepare_site_candidate.prepare_site_candidate(
                root,
                archive,
                receipt,
                package_script,
                run_command=runner,
            )
            with archive.open("ab") as target:
                target.write(b"changed after receipt\n")

            with self.assertRaisesRegex(
                prepare_site_candidate.SiteCandidateError,
                "archive digest does not match receipt",
            ):
                prepare_site_candidate.verify_site_candidate(
                    root,
                    archive,
                    receipt,
                    run_command=FakeCommandRunner(root, archive),
                )

    def test_verification_rejects_payload_digest_drift(self) -> None:
        with TemporaryDirectory() as tmp:
            root, archive, receipt, package_script = self._fixture(Path(tmp))
            runner = FakeCommandRunner(root, archive)
            prepare_site_candidate.prepare_site_candidate(
                root,
                archive,
                receipt,
                package_script,
                run_command=runner,
            )
            payload = json.loads(receipt.read_text(encoding="utf-8"))
            payload["archive"]["payload_sha256"] = "b" * 64
            receipt.write_text(json.dumps(payload), encoding="utf-8")

            with self.assertRaisesRegex(
                prepare_site_candidate.SiteCandidateError,
                "archive payload does not match tested build",
            ):
                prepare_site_candidate.verify_site_candidate(
                    root,
                    archive,
                    receipt,
                    run_command=FakeCommandRunner(root, archive),
                )

    def test_verification_rejects_changed_payload_with_updated_archive_digest(
        self,
    ) -> None:
        with TemporaryDirectory() as tmp:
            root, archive, receipt, package_script = self._fixture(Path(tmp))
            prepare_site_candidate.prepare_site_candidate(
                root,
                archive,
                receipt,
                package_script,
                run_command=FakeCommandRunner(root, archive),
            )
            repack = FakeCommandRunner(
                root,
                archive,
                mutate_server_before_package=True,
            )
            repack(
                (
                    *prepare_site_candidate.PACKAGING_ENV,
                    str(package_script),
                    str(root),
                    str(archive),
                ),
                root,
            )
            payload = json.loads(receipt.read_text(encoding="utf-8"))
            payload["archive"]["sha256"] = hashlib.sha256(
                archive.read_bytes()
            ).hexdigest()
            receipt.write_text(json.dumps(payload), encoding="utf-8")

            with self.assertRaisesRegex(
                prepare_site_candidate.SiteCandidateError,
                "archive payload does not match tested build",
            ):
                prepare_site_candidate.verify_site_candidate(
                    root,
                    archive,
                    receipt,
                    run_command=FakeCommandRunner(root, archive),
                )

    def test_verification_rejects_malformed_payload_digest(self) -> None:
        with TemporaryDirectory() as tmp:
            root, archive, receipt, package_script = self._fixture(Path(tmp))
            prepare_site_candidate.prepare_site_candidate(
                root,
                archive,
                receipt,
                package_script,
                run_command=FakeCommandRunner(root, archive),
            )
            payload = json.loads(receipt.read_text(encoding="utf-8"))
            payload["archive"]["payload_sha256"] = "not-a-digest"
            receipt.write_text(json.dumps(payload), encoding="utf-8")

            with self.assertRaisesRegex(
                prepare_site_candidate.SiteCandidateError,
                "receipt archive payload_sha256 must be a lowercase "
                "SHA-256 digest",
            ):
                prepare_site_candidate.verify_site_candidate(
                    root,
                    archive,
                    receipt,
                    run_command=FakeCommandRunner(root, archive),
                )

    def test_verification_rejects_receipt_commit_drift(self) -> None:
        with TemporaryDirectory() as tmp:
            root, archive, receipt, package_script = self._fixture(Path(tmp))
            runner = FakeCommandRunner(root, archive)
            prepare_site_candidate.prepare_site_candidate(
                root,
                archive,
                receipt,
                package_script,
                run_command=runner,
            )
            payload = json.loads(receipt.read_text(encoding="utf-8"))
            payload["candidate"]["commit_sha"] = "b" * 40
            receipt.write_text(json.dumps(payload), encoding="utf-8")

            with self.assertRaisesRegex(
                prepare_site_candidate.SiteCandidateError,
                "receipt candidate commit_sha does not match checkout",
            ):
                prepare_site_candidate.verify_site_candidate(
                    root,
                    archive,
                    receipt,
                    run_command=FakeCommandRunner(root, archive),
                )

    def test_verification_rejects_checkout_lock_drift(self) -> None:
        with TemporaryDirectory() as tmp:
            root, archive, receipt, package_script = self._fixture(Path(tmp))
            runner = FakeCommandRunner(root, archive)
            prepare_site_candidate.prepare_site_candidate(
                root,
                archive,
                receipt,
                package_script,
                run_command=runner,
            )
            (root / "package-lock.json").write_text(
                '{"lockfileVersion": 4}\n',
                encoding="utf-8",
            )

            with self.assertRaisesRegex(
                prepare_site_candidate.SiteCandidateError,
                "receipt candidate package_lock_sha256 does not match checkout",
            ):
                prepare_site_candidate.verify_site_candidate(
                    root,
                    archive,
                    receipt,
                    run_command=FakeCommandRunner(root, archive),
                )

    def test_verification_rejects_checkout_project_drift(self) -> None:
        with TemporaryDirectory() as tmp:
            root, archive, receipt, package_script = self._fixture(Path(tmp))
            runner = FakeCommandRunner(root, archive)
            prepare_site_candidate.prepare_site_candidate(
                root,
                archive,
                receipt,
                package_script,
                run_command=runner,
            )
            hosting = root / ".openai" / "hosting.json"
            hosting.write_text(
                json.dumps({"project_id": "appgprj_other"}) + "\n",
                encoding="utf-8",
            )

            with self.assertRaisesRegex(
                prepare_site_candidate.SiteCandidateError,
                "receipt candidate project_id does not match checkout",
            ):
                prepare_site_candidate.verify_site_candidate(
                    root,
                    archive,
                    receipt,
                    run_command=FakeCommandRunner(root, archive),
                )

    def test_verification_rejects_receipt_schema_extensions(self) -> None:
        with TemporaryDirectory() as tmp:
            root, archive, receipt, package_script = self._fixture(Path(tmp))
            runner = FakeCommandRunner(root, archive)
            prepare_site_candidate.prepare_site_candidate(
                root,
                archive,
                receipt,
                package_script,
                run_command=runner,
            )
            payload = json.loads(receipt.read_text(encoding="utf-8"))
            payload["approval"] = True
            receipt.write_text(json.dumps(payload), encoding="utf-8")

            with self.assertRaisesRegex(
                prepare_site_candidate.SiteCandidateError,
                "receipt must contain exactly",
            ):
                prepare_site_candidate.verify_site_candidate(
                    root,
                    archive,
                    receipt,
                    run_command=FakeCommandRunner(root, archive),
                )

    def test_verification_rejects_receipts_before_payload_binding(self) -> None:
        with TemporaryDirectory() as tmp:
            root, archive, receipt, package_script = self._fixture(Path(tmp))
            runner = FakeCommandRunner(root, archive)
            prepare_site_candidate.prepare_site_candidate(
                root,
                archive,
                receipt,
                package_script,
                run_command=runner,
            )
            payload = json.loads(receipt.read_text(encoding="utf-8"))
            payload["schema_version"] = 1
            receipt.write_text(json.dumps(payload), encoding="utf-8")

            with self.assertRaisesRegex(
                prepare_site_candidate.SiteCandidateError,
                "receipt schema_version must be 2",
            ):
                prepare_site_candidate.verify_site_candidate(
                    root,
                    archive,
                    receipt,
                    run_command=FakeCommandRunner(root, archive),
                )

    def test_verify_only_cli_does_not_require_a_packaging_helper(self) -> None:
        result = prepare_site_candidate.SiteCandidateResult(
            commit_sha=COMMIT_SHA,
            archive_sha256="c" * 64,
            archive=Path("/tmp/candidate.tar.gz"),
            receipt=Path("/tmp/candidate.json"),
        )

        with patch.object(
            prepare_site_candidate,
            "verify_site_candidate",
            return_value=result,
        ) as verify:
            stdout = StringIO()
            with redirect_stdout(stdout):
                status = prepare_site_candidate.main(
                    [
                        "--verify-only",
                        "--root",
                        "/tmp/project",
                        "--archive",
                        "/tmp/candidate.tar.gz",
                        "--receipt",
                        "/tmp/candidate.json",
                    ]
                )

        self.assertEqual(status, 0)
        self.assertEqual(
            stdout.getvalue().strip(),
            "site candidate verified: "
            f"commit={COMMIT_SHA} "
            "archive=candidate.tar.gz "
            f"sha256={'c' * 64} "
            "receipt=candidate.json",
        )
        verify.assert_called_once_with(
            Path("/tmp/project"),
            Path("/tmp/candidate.tar.gz"),
            Path("/tmp/candidate.json"),
        )

    def test_prepare_cli_still_routes_through_the_packaging_helper(self) -> None:
        result = prepare_site_candidate.SiteCandidateResult(
            commit_sha=COMMIT_SHA,
            archive_sha256="d" * 64,
            archive=Path("/tmp/candidate.tar.gz"),
            receipt=Path("/tmp/candidate.json"),
        )

        with patch.object(
            prepare_site_candidate,
            "prepare_site_candidate",
            return_value=result,
        ) as prepare:
            stdout = StringIO()
            with redirect_stdout(stdout):
                status = prepare_site_candidate.main(
                    [
                        "--root",
                        "/tmp/project",
                        "--package-script",
                        "/tmp/package-site.sh",
                        "--archive",
                        "/tmp/candidate.tar.gz",
                        "--receipt",
                        "/tmp/candidate.json",
                    ]
                )

        self.assertEqual(status, 0)
        self.assertEqual(
            stdout.getvalue().strip(),
            "site candidate ready: "
            f"commit={COMMIT_SHA} "
            "archive=candidate.tar.gz "
            f"sha256={'d' * 64} "
            "receipt=candidate.json",
        )
        prepare.assert_called_once_with(
            Path("/tmp/project"),
            Path("/tmp/candidate.tar.gz"),
            Path("/tmp/candidate.json"),
            Path("/tmp/package-site.sh"),
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

    def test_rejects_an_archive_member_outside_dist(self) -> None:
        with TemporaryDirectory() as tmp:
            root, archive, receipt, package_script = self._fixture(Path(tmp))
            runner = FakeCommandRunner(
                root,
                archive,
                extra_member_name="README.md",
            )

            with self.assertRaisesRegex(
                prepare_site_candidate.SiteCandidateError,
                r"archive member must stay within dist/: README\.md",
            ):
                prepare_site_candidate.prepare_site_candidate(
                    root,
                    archive,
                    receipt,
                    package_script,
                    run_command=runner,
                )

            self.assertFalse(receipt.exists())

    def test_rejects_a_special_file_archive_member(self) -> None:
        with TemporaryDirectory() as tmp:
            root, archive, receipt, package_script = self._fixture(Path(tmp))
            runner = FakeCommandRunner(
                root,
                archive,
                extra_member_name="dist/runtime.pipe",
                extra_member_type=tarfile.FIFOTYPE,
            )

            with self.assertRaisesRegex(
                prepare_site_candidate.SiteCandidateError,
                "archive member must be a regular file or directory: "
                r"dist/runtime\.pipe",
            ):
                prepare_site_candidate.prepare_site_candidate(
                    root,
                    archive,
                    receipt,
                    package_script,
                    run_command=runner,
                )

            self.assertFalse(receipt.exists())

    def test_rejects_a_packaging_helper_that_changes_tested_bytes(self) -> None:
        with TemporaryDirectory() as tmp:
            root, archive, receipt, package_script = self._fixture(Path(tmp))
            runner = FakeCommandRunner(
                root,
                archive,
                mutate_server_before_package=True,
            )

            with self.assertRaisesRegex(
                prepare_site_candidate.SiteCandidateError,
                "archive payload does not match tested build",
            ):
                prepare_site_candidate.prepare_site_candidate(
                    root,
                    archive,
                    receipt,
                    package_script,
                    run_command=runner,
                )

            self.assertFalse(receipt.exists())

    def test_rejects_extra_deployable_bytes_added_during_packaging(self) -> None:
        with TemporaryDirectory() as tmp:
            root, archive, receipt, package_script = self._fixture(Path(tmp))
            runner = FakeCommandRunner(
                root,
                archive,
                extra_member_name="dist/injected.js",
            )

            with self.assertRaisesRegex(
                prepare_site_candidate.SiteCandidateError,
                "archive payload does not match tested build",
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

    def test_runtime_pin_matches_candidate_hosted_and_package_contracts(
        self,
    ) -> None:
        workflow = (
            ROOT / ".github" / "workflows" / "site-dependencies.yml"
        ).read_text(encoding="utf-8")
        package = json.loads(
            (ROOT / "package.json").read_text(encoding="utf-8")
        )
        lock = json.loads(
            (ROOT / "package-lock.json").read_text(encoding="utf-8")
        )
        runtime_pin = (ROOT / ".nvmrc").read_text(encoding="ascii").strip()

        self.assertEqual(
            prepare_site_candidate.read_node_runtime_pin(ROOT),
            "22.13.0",
        )
        self.assertEqual(runtime_pin, "22.13.0")
        self.assertEqual(package["engines"]["node"], f">={runtime_pin}")
        self.assertEqual(
            lock["packages"][""]["engines"]["node"],
            f">={runtime_pin}",
        )
        self.assertIn(
            'node-version-file: ".nvmrc"',
            workflow,
        )

    def test_rejects_a_malformed_runtime_pin_before_commands(self) -> None:
        with TemporaryDirectory() as tmp:
            root, archive, receipt, package_script = self._fixture(Path(tmp))
            (root / ".nvmrc").write_text("22.13\nextra\n", encoding="ascii")
            runner = FakeCommandRunner(root, archive)

            with self.assertRaisesRegex(
                prepare_site_candidate.SiteCandidateError,
                "Node runtime pin must contain one semantic version",
            ):
                prepare_site_candidate.prepare_site_candidate(
                    root,
                    archive,
                    receipt,
                    package_script,
                    run_command=runner,
                )

            self.assertEqual(runner.commands, [])

    @staticmethod
    def _fixture(tmp: Path) -> tuple[Path, Path, Path, Path]:
        root = tmp / "project"
        root.mkdir()
        (root / ".nvmrc").write_text("22.13.0\n", encoding="ascii")
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
