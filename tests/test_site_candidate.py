from __future__ import annotations

from contextlib import redirect_stderr, redirect_stdout
import errno
import hashlib
import importlib.util
from io import BytesIO, StringIO
import json
from pathlib import Path
import stat
import sys
import tarfile
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import ANY, patch


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
RELEASE_VERSION = "0.3.51"
ORIGIN_REPOSITORY = "https://github.com/example/repo-scout.git"
SITES_SOURCE_REPOSITORY = "https://sites.example/repo-scout.git"
SITES_SOURCE_REMOTE = "sites-source"
UNRELATED_SOURCE_REPOSITORY = "https://git.example/unrelated-fork.git"


class OutputParentOpenTracker:
    def __init__(self, *parents: Path) -> None:
        self.parents = set(parents)
        self.descriptors: list[int] = []
        self._recorded_parents: set[Path] = set()
        self._open = prepare_site_candidate.os.open

    def __call__(
        self,
        path: object,
        flags: int,
        mode: int = 0o777,
        *,
        dir_fd: int | None = None,
    ) -> int:
        descriptor = self._open(
            path,
            flags,
            mode,
            dir_fd=dir_fd,
        )
        parent_path = Path(path)
        if (
            parent_path in self.parents
            and parent_path not in self._recorded_parents
        ):
            self.descriptors.append(descriptor)
            self._recorded_parents.add(parent_path)
        return descriptor

    def assert_open(
        self,
        test_case: unittest.TestCase,
        expected_count: int,
    ) -> None:
        test_case.assertEqual(len(self.descriptors), expected_count)
        for descriptor in self.descriptors:
            prepare_site_candidate.os.fstat(descriptor)
            test_case.assertFalse(
                prepare_site_candidate.os.get_inheritable(descriptor)
            )

    def assert_closed(
        self,
        test_case: unittest.TestCase,
        expected_count: int,
    ) -> None:
        test_case.assertEqual(len(self.descriptors), expected_count)
        for descriptor in self.descriptors:
            with test_case.assertRaises(OSError) as caught:
                prepare_site_candidate.os.fstat(descriptor)
            test_case.assertEqual(caught.exception.errno, errno.EBADF)


class PublishedOutputTracker:
    def __init__(self) -> None:
        self.outputs: list[
            prepare_site_candidate._PublishedOutput
        ] = []
        self._publish = prepare_site_candidate._publish_new_output

    def __call__(
        self,
        staged_path: Path,
        output_path: Path,
        label: str,
        parent_fd: int,
        *,
        source_descriptor: int | None = None,
        source_parent_descriptor: int | None = None,
    ) -> prepare_site_candidate._PublishedOutput:
        output = self._publish(
            staged_path,
            output_path,
            label,
            parent_fd,
            source_descriptor=source_descriptor,
            source_parent_descriptor=source_parent_descriptor,
        )
        self.outputs.append(output)
        return output

    def assert_open(
        self,
        test_case: unittest.TestCase,
        expected_count: int,
    ) -> None:
        test_case.assertEqual(len(self.outputs), expected_count)
        for output in self.outputs:
            details = prepare_site_candidate.os.fstat(output.fd)
            test_case.assertTrue(stat.S_ISREG(details.st_mode))
            test_case.assertFalse(
                prepare_site_candidate.os.get_inheritable(output.fd)
            )

    def assert_closed(
        self,
        test_case: unittest.TestCase,
        expected_count: int,
    ) -> None:
        test_case.assertEqual(len(self.outputs), expected_count)
        for output in self.outputs:
            with test_case.assertRaises(OSError) as caught:
                prepare_site_candidate.os.fstat(output.fd)
            test_case.assertEqual(caught.exception.errno, errno.EBADF)


class FakeCommandRunner:
    def __init__(
        self,
        root: Path,
        archive: Path,
        *,
        status: str = "",
        origin_sha: str = COMMIT_SHA,
        head_shas: tuple[str, ...] | None = None,
        origin_shas: tuple[str, ...] | None = None,
        origin_repository: str = ORIGIN_REPOSITORY,
        exported_source_repositories: tuple[str, ...] | None = None,
        exported_source_shas: tuple[str, ...] | None = None,
        branches: tuple[str, ...] | None = None,
        node_version: str = "v22.13.0",
        include_manifest: bool = True,
        extra_member_name: str | None = None,
        extra_member_type: bytes = tarfile.REGTYPE,
        server_directory_mode: int | None = None,
        mutate_server_after_site_tests: bool = False,
        mutate_server_before_package: bool = False,
        duplicate_manifest_before_package: bool = False,
        late_outputs: dict[Path, bytes] | None = None,
    ) -> None:
        self.root = root
        self.archive = archive
        self.status = status
        self.head_shas = list(head_shas or (COMMIT_SHA,))
        self.origin_shas = list(origin_shas or (origin_sha,))
        self.origin_repository = origin_repository
        self.exported_source_repositories = list(
            exported_source_repositories or (SITES_SOURCE_REPOSITORY,)
        )
        self.exported_source_shas = list(
            exported_source_shas or (COMMIT_SHA,)
        )
        self.branches = list(branches or ("main",))
        self.node_version = node_version
        self.include_manifest = include_manifest
        self.extra_member_name = extra_member_name
        self.extra_member_type = extra_member_type
        self.server_directory_mode = server_directory_mode
        self.mutate_server_after_site_tests = (
            mutate_server_after_site_tests
        )
        self.mutate_server_before_package = mutate_server_before_package
        self.duplicate_manifest_before_package = (
            duplicate_manifest_before_package
        )
        self.late_outputs = late_outputs or {}
        self.commands: list[tuple[str, ...]] = []
        self.packaged_archives: list[Path] = []

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
        if normalized == ("git", "branch", "--show-current"):
            return self._next_value(self.branches)
        if normalized == ("git", "rev-parse", "HEAD"):
            return self._next_value(self.head_shas)
        if normalized == ("git", "rev-parse", "origin/main"):
            return self._next_value(self.origin_shas)
        if normalized == ("git", "ls-remote", "--get-url", "origin"):
            return self.origin_repository
        if (
            len(normalized) == 4
            and normalized[:3] == ("git", "ls-remote", "--get-url")
        ):
            return self._next_value(self.exported_source_repositories)
        if (
            len(normalized) == 6
            and normalized[:4]
            == (
                "git",
                "ls-remote",
                "--exit-code",
                "--refs",
            )
            and normalized[-1] == prepare_site_candidate.SOURCE_REF
        ):
            sha = self._next_value(self.exported_source_shas)
            return f"{sha}\t{prepare_site_candidate.SOURCE_REF}\n"
        if normalized == ("node", "--version"):
            return self.node_version
        if normalized == ("npm", "run", "build"):
            server = self.root / "dist" / "server" / "index.js"
            server.parent.mkdir(parents=True, exist_ok=True)
            server.write_text("export default {};\n", encoding="utf-8")
            return ""
        if normalized == ("npm", "run", "test:site"):
            manifest = (
                self.root / "dist" / ".openai" / "site-candidate.json"
            )
            if not manifest.is_file():
                raise AssertionError(
                    "site tests ran before the candidate manifest was bound"
                )
            if self.mutate_server_after_site_tests:
                server = self.root / "dist" / "server" / "index.js"
                server.write_text(
                    "export default { changedDuringTest: true };\n",
                    encoding="utf-8",
                )
            return ""
        if normalized in prepare_site_candidate.VALIDATION_COMMANDS:
            return ""
        prefix_length = len(
            prepare_site_candidate.PACKAGING_COMMAND_PREFIX
        )
        if (
            len(normalized) == prefix_length + 3
            and normalized[:prefix_length]
            == prepare_site_candidate.PACKAGING_COMMAND_PREFIX
            and normalized[prefix_length + 1] == str(self.root)
        ):
            output = Path(normalized[prefix_length + 2])
            if self.mutate_server_before_package:
                server = self.root / "dist" / "server" / "index.js"
                server.write_text(
                    "export default { tampered: true };\n",
                    encoding="utf-8",
                )
            if self.duplicate_manifest_before_package:
                manifest = (
                    self.root
                    / "dist"
                    / ".openai"
                    / "site-candidate.json"
                )
                content = manifest.read_text(encoding="utf-8")
                content = content.replace(
                    '  "schema_version": 5',
                    '  "schema_version": 5,\n  "schema_version": 5',
                    1,
                )
                manifest.write_text(content, encoding="utf-8")
            self.packaged_archives.append(output)
            self._package(output)
            for path, content in self.late_outputs.items():
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(content)
            return str(output)
        raise AssertionError(f"unexpected command: {normalized}")

    def assert_root(self, root: Path) -> None:
        if root != self.root:
            raise AssertionError(f"unexpected command root: {root}")

    @staticmethod
    def _next_value(values: list[str]) -> str:
        if len(values) > 1:
            return values.pop(0)
        return values[0]

    def _package(self, archive: Path) -> None:
        archive.parent.mkdir(parents=True, exist_ok=True)
        with tarfile.open(archive, "w:gz") as bundle:
            entries: dict[str, Path] = {}
            self._overlay_entries(entries, self.root / "dist", "dist")
            entries["dist/.openai/hosting.json"] = (
                self.root / ".openai" / "hosting.json"
            )
            drizzle = self.root / "drizzle"
            if drizzle.is_dir():
                self._overlay_entries(
                    entries,
                    drizzle,
                    "dist/.openai/drizzle",
                )
            for archive_name, source in sorted(
                entries.items(),
                key=lambda item: (item[0].count("/"), item[0]),
            ):
                if (
                    archive_name == "dist/.openai/site-candidate.json"
                    and not self.include_manifest
                ):
                    continue
                bundle.add(
                    source,
                    arcname=archive_name,
                    recursive=False,
                    filter=self._filter_archive_member,
                )
            if self.extra_member_name is not None:
                member = tarfile.TarInfo(self.extra_member_name)
                member.type = self.extra_member_type
                content: BytesIO | None = None
                if member.isfile():
                    content = BytesIO(b"unexpected candidate content\n")
                    member.size = len(content.getvalue())
                bundle.addfile(member, content)

    def _filter_archive_member(
        self,
        member: tarfile.TarInfo,
    ) -> tarfile.TarInfo:
        if member.isdir():
            member.mode = prepare_site_candidate.REQUIRED_DIRECTORY_MODE
        if (
            self.server_directory_mode is not None
            and member.name == "dist/server"
        ):
            member.mode = self.server_directory_mode
        return member

    @staticmethod
    def _overlay_entries(
        entries: dict[str, Path],
        source_root: Path,
        archive_root: str,
    ) -> None:
        entries[archive_root] = source_root
        for source in sorted(source_root.rglob("*")):
            relative = source.relative_to(source_root).as_posix()
            entries[f"{archive_root}/{relative}"] = source


class SiteCandidateTests(unittest.TestCase):
    def test_packaging_uses_a_deterministic_directory_umask(self) -> None:
        self.assertEqual(
            prepare_site_candidate.PACKAGING_COMMAND_PREFIX,
            (
                "env",
                "COPYFILE_DISABLE=1",
                "sh",
                "-c",
                'umask 022; exec "$@"',
                "repo-scout-site-package",
            ),
        )

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
            self.assertEqual(result.release_version, RELEASE_VERSION)
            self.assertEqual(result.project_id, PROJECT_ID)
            self.assertEqual(receipt_payload["schema_version"], 5)
            self.assertEqual(
                receipt_payload["candidate"],
                {
                    "schema_version": 5,
                    "commit_sha": COMMIT_SHA,
                    "source_ref": "refs/heads/main",
                    "release_version": RELEASE_VERSION,
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
                result.receipt_sha256,
                hashlib.sha256(receipt.read_bytes()).hexdigest(),
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
                    ("git", "branch", "--show-current"),
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
                    ("git", "branch", "--show-current"),
                    ("git", "rev-parse", "HEAD"),
                    ("git", "rev-parse", "origin/main"),
                    (
                        *prepare_site_candidate.PACKAGING_COMMAND_PREFIX,
                        str(package_script),
                        str(root),
                        ANY,
                    ),
                    (
                        "git",
                        "status",
                        "--porcelain",
                        "--untracked-files=all",
                    ),
                    ("git", "branch", "--show-current"),
                    ("git", "rev-parse", "HEAD"),
                    ("git", "rev-parse", "origin/main"),
                    (
                        "git",
                        "status",
                        "--porcelain",
                        "--untracked-files=all",
                    ),
                    ("git", "branch", "--show-current"),
                    ("git", "rev-parse", "HEAD"),
                    ("git", "rev-parse", "origin/main"),
                ],
            )
            staged_archive = runner.packaged_archives[0]
            self.assertNotEqual(staged_archive, archive)
            self.assertEqual(staged_archive.name, archive.name)
            self.assertEqual(staged_archive.parent.parent, archive.parent)
            self.assertTrue(
                staged_archive.parent.name.startswith(f".{archive.name}.")
            )
            self.assertFalse(staged_archive.exists())

    def test_prepares_outputs_in_distinct_prevalidated_parents(self) -> None:
        with TemporaryDirectory() as tmp:
            root, archive, receipt, package_script = self._fixture(Path(tmp))
            archive_parent = Path(tmp) / "archive-output"
            receipt_parent = Path(tmp) / "receipt-output"
            archive_parent.mkdir()
            receipt_parent.mkdir()
            archive = (archive_parent / archive.name).resolve()
            receipt = (receipt_parent / receipt.name).resolve()

            result = prepare_site_candidate.prepare_site_candidate(
                root,
                archive,
                receipt,
                package_script,
                run_command=FakeCommandRunner(root, archive),
            )

            self.assertEqual(result.archive, archive)
            self.assertEqual(result.receipt, receipt)
            self.assertTrue(archive.is_file())
            self.assertTrue(receipt.is_file())

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
            self.assertEqual(result.project_id, PROJECT_ID)
            self.assertEqual(
                verify_runner.commands,
                [
                    (
                        "git",
                        "status",
                        "--porcelain",
                        "--untracked-files=all",
                    ),
                    ("git", "branch", "--show-current"),
                    ("git", "rev-parse", "HEAD"),
                    ("git", "rev-parse", "origin/main"),
                    (
                        "git",
                        "status",
                        "--porcelain",
                        "--untracked-files=all",
                    ),
                    ("git", "branch", "--show-current"),
                    ("git", "rev-parse", "HEAD"),
                    ("git", "rev-parse", "origin/main"),
                ],
            )

    def test_verification_rejects_an_initial_archive_symlink(self) -> None:
        with TemporaryDirectory() as tmp:
            root, archive, receipt, package_script = self._fixture(Path(tmp))
            prepare_site_candidate.prepare_site_candidate(
                root,
                archive,
                receipt,
                package_script,
                run_command=FakeCommandRunner(root, archive),
            )
            archive_link = Path(tmp) / "candidate-link.tar.gz"
            archive_link.symlink_to(archive)
            runner = FakeCommandRunner(root, archive)

            with self.assertRaisesRegex(
                prepare_site_candidate.SiteCandidateError,
                "Sites candidate archive must be a regular file",
            ):
                prepare_site_candidate.verify_site_candidate(
                    root,
                    archive_link,
                    receipt,
                    run_command=runner,
                )

            self.assertEqual(runner.commands, [])

    def test_verification_rejects_an_initial_receipt_symlink(self) -> None:
        with TemporaryDirectory() as tmp:
            root, archive, receipt, package_script = self._fixture(Path(tmp))
            prepare_site_candidate.prepare_site_candidate(
                root,
                archive,
                receipt,
                package_script,
                run_command=FakeCommandRunner(root, archive),
            )
            receipt_link = Path(tmp) / "candidate-link.json"
            receipt_link.symlink_to(receipt)
            runner = FakeCommandRunner(root, archive)

            with self.assertRaisesRegex(
                prepare_site_candidate.SiteCandidateError,
                "Sites candidate receipt must be a regular file",
            ):
                prepare_site_candidate.verify_site_candidate(
                    root,
                    archive,
                    receipt_link,
                    run_command=runner,
                )

            self.assertEqual(runner.commands, [])

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

    def test_rejects_noncanonical_overlay_root_mode(self) -> None:
        with TemporaryDirectory() as tmp:
            root, archive, receipt, package_script = self._fixture(Path(tmp))
            meta = root / "drizzle" / "meta"
            meta.mkdir(parents=True)
            meta.parent.chmod(0o700)

            with self.assertRaisesRegex(
                prepare_site_candidate.SiteCandidateError,
                "tested Sites payload directory mode must be 0755",
            ):
                prepare_site_candidate.prepare_site_candidate(
                    root,
                    archive,
                    receipt,
                    package_script,
                    run_command=FakeCommandRunner(root, archive),
                )

            self.assertFalse(archive.exists())
            self.assertFalse(receipt.exists())

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

    def test_preparation_rejects_archive_changed_after_validation(self) -> None:
        with TemporaryDirectory() as tmp:
            root, archive, receipt, package_script = self._fixture(Path(tmp))
            validate_archive = prepare_site_candidate._verify_archive

            def validate_then_mutate(
                path: Path,
                manifest: dict[str, object],
                payload_sha256: str,
                *,
                descriptor: int | None = None,
            ) -> None:
                validate_archive(
                    path,
                    manifest,
                    payload_sha256,
                    descriptor=descriptor,
                )
                with path.open("ab") as target:
                    target.write(b"changed after validation\n")

            with (
                patch.object(
                    prepare_site_candidate,
                    "_verify_archive",
                    side_effect=validate_then_mutate,
                ),
                self.assertRaisesRegex(
                    prepare_site_candidate.SiteCandidateError,
                    "Sites candidate archive changed during candidate "
                    "operation",
                ),
            ):
                prepare_site_candidate.prepare_site_candidate(
                    root,
                    archive,
                    receipt,
                    package_script,
                    run_command=FakeCommandRunner(root, archive),
                )

            self.assertFalse(archive.exists())
            self.assertFalse(receipt.exists())

    def test_preparation_rejects_identical_archive_leaf_replacement(
        self,
    ) -> None:
        with TemporaryDirectory() as tmp:
            root, archive, receipt, package_script = self._fixture(Path(tmp))
            validate_archive = prepare_site_candidate._verify_archive
            replacement_content: list[bytes] = []

            def validate_then_replace(
                path: Path,
                manifest: dict[str, object],
                payload_sha256: str,
                *,
                descriptor: int | None = None,
            ) -> None:
                validate_archive(
                    path,
                    manifest,
                    payload_sha256,
                    descriptor=descriptor,
                )
                content = path.read_bytes()
                replacement_content.append(content)
                path.unlink()
                path.write_bytes(content)

            with (
                patch.object(
                    prepare_site_candidate,
                    "_verify_archive",
                    side_effect=validate_then_replace,
                ),
                self.assertRaisesRegex(
                    prepare_site_candidate.SiteCandidateError,
                    "archive staging source changed during publication",
                ),
            ):
                prepare_site_candidate.prepare_site_candidate(
                    root,
                    archive,
                    receipt,
                    package_script,
                    run_command=FakeCommandRunner(root, archive),
                )

            self.assertEqual(len(replacement_content), 1)
            self.assertFalse(archive.exists())
            self.assertFalse(receipt.exists())
            leaked_staging = list(
                archive.parent.glob(f".{archive.name}.*")
            )
            self.assertEqual(len(leaked_staging), 1)
            self.assertTrue(
                leaked_staging[0].joinpath(archive.name).is_file()
            )
            self.assertEqual(
                leaked_staging[0].joinpath(archive.name).read_bytes(),
                replacement_content[0],
            )

    def test_verification_rejects_archive_changed_after_validation(self) -> None:
        with TemporaryDirectory() as tmp:
            root, archive, receipt, package_script = self._fixture(Path(tmp))
            prepare_site_candidate.prepare_site_candidate(
                root,
                archive,
                receipt,
                package_script,
                run_command=FakeCommandRunner(root, archive),
            )
            validate_archive = prepare_site_candidate._verify_archive

            def validate_then_mutate(
                path: Path,
                manifest: dict[str, object],
                payload_sha256: str,
                *,
                descriptor: int | None = None,
            ) -> None:
                validate_archive(
                    path,
                    manifest,
                    payload_sha256,
                    descriptor=descriptor,
                )
                with path.open("ab") as target:
                    target.write(b"changed after validation\n")

            with (
                patch.object(
                    prepare_site_candidate,
                    "_verify_archive",
                    side_effect=validate_then_mutate,
                ),
                self.assertRaisesRegex(
                    prepare_site_candidate.SiteCandidateError,
                    "Sites candidate archive changed during candidate "
                    "operation",
                ),
            ):
                prepare_site_candidate.verify_site_candidate(
                    root,
                    archive,
                    receipt,
                    run_command=FakeCommandRunner(root, archive),
                )

    def test_verification_rejects_receipt_changed_after_validation(self) -> None:
        with TemporaryDirectory() as tmp:
            root, archive, receipt, package_script = self._fixture(Path(tmp))
            prepare_site_candidate.prepare_site_candidate(
                root,
                archive,
                receipt,
                package_script,
                run_command=FakeCommandRunner(root, archive),
            )
            validate_archive = prepare_site_candidate._verify_archive

            def validate_then_mutate(
                path: Path,
                manifest: dict[str, object],
                payload_sha256: str,
                *,
                descriptor: int | None = None,
            ) -> None:
                validate_archive(
                    path,
                    manifest,
                    payload_sha256,
                    descriptor=descriptor,
                )
                with receipt.open("ab") as target:
                    target.write(b"changed after validation\n")

            with (
                patch.object(
                    prepare_site_candidate,
                    "_verify_archive",
                    side_effect=validate_then_mutate,
                ),
                self.assertRaisesRegex(
                    prepare_site_candidate.SiteCandidateError,
                    "Sites candidate receipt changed during candidate "
                    "operation",
                ),
            ):
                prepare_site_candidate.verify_site_candidate(
                    root,
                    archive,
                    receipt,
                    run_command=FakeCommandRunner(root, archive),
                )

    def test_verification_rejects_receipt_replaced_after_validation(self) -> None:
        with TemporaryDirectory() as tmp:
            root, archive, receipt, package_script = self._fixture(Path(tmp))
            prepare_site_candidate.prepare_site_candidate(
                root,
                archive,
                receipt,
                package_script,
                run_command=FakeCommandRunner(root, archive),
            )
            validate_archive = prepare_site_candidate._verify_archive

            def validate_then_replace(
                path: Path,
                manifest: dict[str, object],
                payload_sha256: str,
                *,
                descriptor: int | None = None,
            ) -> None:
                validate_archive(
                    path,
                    manifest,
                    payload_sha256,
                    descriptor=descriptor,
                )
                receipt.unlink()
                receipt.symlink_to(archive)

            with (
                patch.object(
                    prepare_site_candidate,
                    "_verify_archive",
                    side_effect=validate_then_replace,
                ),
                self.assertRaisesRegex(
                    prepare_site_candidate.SiteCandidateError,
                    "Sites candidate receipt changed during candidate "
                    "operation",
                ),
            ):
                prepare_site_candidate.verify_site_candidate(
                    root,
                    archive,
                    receipt,
                    run_command=FakeCommandRunner(root, archive),
                )

    def test_verification_requires_the_approved_receipt_digest(self) -> None:
        with TemporaryDirectory() as tmp:
            root, archive, receipt, package_script = self._fixture(Path(tmp))
            prepare_site_candidate.prepare_site_candidate(
                root,
                archive,
                receipt,
                package_script,
                run_command=FakeCommandRunner(root, archive),
            )
            approved_digest = hashlib.sha256(receipt.read_bytes()).hexdigest()

            result = prepare_site_candidate.verify_site_candidate(
                root,
                archive,
                receipt,
                expected_receipt_sha256=approved_digest,
                exported_source_repository=SITES_SOURCE_REMOTE,
                expected_exported_source_repository=(
                    SITES_SOURCE_REPOSITORY
                ),
                run_command=FakeCommandRunner(root, archive),
            )

            self.assertEqual(result.receipt_sha256, approved_digest)
            payload = json.loads(receipt.read_text(encoding="utf-8"))
            receipt.write_text(
                json.dumps(payload, separators=(",", ":")) + "\n",
                encoding="utf-8",
            )
            self.assertNotEqual(
                hashlib.sha256(receipt.read_bytes()).hexdigest(),
                approved_digest,
            )

            with self.assertRaisesRegex(
                prepare_site_candidate.SiteCandidateError,
                "receipt digest does not match approved receipt",
            ):
                prepare_site_candidate.verify_site_candidate(
                    root,
                    archive,
                    receipt,
                    expected_receipt_sha256=approved_digest,
                    exported_source_repository=SITES_SOURCE_REMOTE,
                    expected_exported_source_repository=(
                        SITES_SOURCE_REPOSITORY
                    ),
                    run_command=FakeCommandRunner(root, archive),
                )

    def test_pre_save_verification_requires_approved_receipt_digest(
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

            with self.assertRaisesRegex(
                prepare_site_candidate.SiteCandidateError,
                "exported source verification requires an approved receipt "
                "digest",
            ):
                prepare_site_candidate.verify_site_candidate(
                    root,
                    archive,
                    receipt,
                    exported_source_repository=SITES_SOURCE_REPOSITORY,
                    run_command=FakeCommandRunner(root, archive),
                )

    def test_pre_save_verification_rejects_digest_only_downgrade(
        self,
    ) -> None:
        with self.assertRaisesRegex(
            prepare_site_candidate.SiteCandidateError,
            "approved receipt digest requires exported source verification",
        ):
            prepare_site_candidate.verify_site_candidate(
                Path("/tmp/project"),
                Path("/tmp/candidate.tar.gz"),
                Path("/tmp/candidate.json"),
                expected_receipt_sha256="e" * 64,
                run_command=lambda command, root: "",
            )

    def test_pre_save_verification_rejects_embedded_credentials(self) -> None:
        with self.assertRaisesRegex(
            prepare_site_candidate.SiteCandidateError,
            "exported source repository must not embed credentials",
        ):
            prepare_site_candidate.verify_site_candidate(
                Path("/tmp/project"),
                Path("/tmp/candidate.tar.gz"),
                Path("/tmp/candidate.json"),
                expected_receipt_sha256="e" * 64,
                exported_source_repository=(
                    "https://secret-token@sites.example/repo-scout.git"
                ),
                expected_exported_source_repository=(
                    SITES_SOURCE_REPOSITORY
                ),
                run_command=lambda command, root: "",
            )

    def test_pre_save_verification_rejects_malformed_remote_identity(
        self,
    ) -> None:
        malformed_repository = (
            "https://sites.example:not-a-port/repo-scout.git"
        )

        with self.assertRaisesRegex(
            prepare_site_candidate.SiteCandidateError,
            "approved Sites source repository must be a valid remote Git "
            "repository identity",
        ):
            prepare_site_candidate.verify_site_candidate(
                Path("/tmp/project"),
                Path("/tmp/candidate.tar.gz"),
                Path("/tmp/candidate.json"),
                expected_receipt_sha256="e" * 64,
                exported_source_repository=malformed_repository,
                expected_exported_source_repository=malformed_repository,
                run_command=lambda command, root: "",
            )

    def test_pre_save_verification_requires_approved_repository(
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
            approved_digest = hashlib.sha256(receipt.read_bytes()).hexdigest()

            with self.assertRaisesRegex(
                prepare_site_candidate.SiteCandidateError,
                "requires the approved Sites repository identity",
            ):
                prepare_site_candidate.verify_site_candidate(
                    root,
                    archive,
                    receipt,
                    expected_receipt_sha256=approved_digest,
                    exported_source_repository=SITES_SOURCE_REPOSITORY,
                    run_command=FakeCommandRunner(root, archive),
                )

    def test_pre_save_verification_rejects_origin_repository(self) -> None:
        with TemporaryDirectory() as tmp:
            root, archive, receipt, package_script = self._fixture(Path(tmp))
            prepare_site_candidate.prepare_site_candidate(
                root,
                archive,
                receipt,
                package_script,
                run_command=FakeCommandRunner(root, archive),
            )
            approved_digest = hashlib.sha256(receipt.read_bytes()).hexdigest()

            with self.assertRaisesRegex(
                prepare_site_candidate.SiteCandidateError,
                "exported source repository must be separate from origin",
            ):
                prepare_site_candidate.verify_site_candidate(
                    root,
                    archive,
                    receipt,
                    expected_receipt_sha256=approved_digest,
                    exported_source_repository="origin",
                    expected_exported_source_repository=ORIGIN_REPOSITORY,
                    run_command=FakeCommandRunner(root, archive),
                )

    def test_pre_save_verification_rejects_origin_url_alias(self) -> None:
        with TemporaryDirectory() as tmp:
            root, archive, receipt, package_script = self._fixture(Path(tmp))
            prepare_site_candidate.prepare_site_candidate(
                root,
                archive,
                receipt,
                package_script,
                run_command=FakeCommandRunner(root, archive),
            )
            approved_digest = hashlib.sha256(receipt.read_bytes()).hexdigest()

            with self.assertRaisesRegex(
                prepare_site_candidate.SiteCandidateError,
                "exported source repository must be separate from origin",
            ):
                prepare_site_candidate.verify_site_candidate(
                    root,
                    archive,
                    receipt,
                    expected_receipt_sha256=approved_digest,
                    exported_source_repository=(
                        "https://github.com/example/repo-scout"
                    ),
                    expected_exported_source_repository=ORIGIN_REPOSITORY,
                    run_command=FakeCommandRunner(
                        root,
                        archive,
                        exported_source_repositories=(
                            "https://github.com/example/repo-scout",
                        ),
                    ),
                )

    def test_pre_save_verification_rejects_cross_protocol_origin_alias(
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
            approved_digest = hashlib.sha256(receipt.read_bytes()).hexdigest()

            with self.assertRaisesRegex(
                prepare_site_candidate.SiteCandidateError,
                "exported source repository must be separate from origin",
            ):
                prepare_site_candidate.verify_site_candidate(
                    root,
                    archive,
                    receipt,
                    expected_receipt_sha256=approved_digest,
                    exported_source_repository=(
                        "https://github.com/example/repo-scout"
                    ),
                    expected_exported_source_repository=(
                        "https://github.com/example/repo-scout"
                    ),
                    run_command=FakeCommandRunner(
                        root,
                        archive,
                        origin_repository=(
                            "git@github.com:example/repo-scout.git"
                        ),
                        exported_source_repositories=(
                            "https://github.com/example/repo-scout",
                        ),
                    ),
                )

    def test_pre_save_verification_rejects_unapproved_nondefault_port(
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
            approved_digest = hashlib.sha256(receipt.read_bytes()).hexdigest()

            with self.assertRaisesRegex(
                prepare_site_candidate.SiteCandidateError,
                "repository does not match approved Sites repository",
            ):
                prepare_site_candidate.verify_site_candidate(
                    root,
                    archive,
                    receipt,
                    expected_receipt_sha256=approved_digest,
                    exported_source_repository=SITES_SOURCE_REMOTE,
                    expected_exported_source_repository=(
                        SITES_SOURCE_REPOSITORY
                    ),
                    run_command=FakeCommandRunner(
                        root,
                        archive,
                        exported_source_repositories=(
                            "https://sites.example:8443/repo-scout.git",
                        ),
                    ),
                )

    def test_pre_save_verification_rejects_unapproved_ssh_usernames(
        self,
    ) -> None:
        repositories = (
            "ssh://alice@sites.example:22/repo-scout.git",
            "bob@sites.example:repo-scout.git",
        )
        for repository in repositories:
            with self.subTest(repository=repository), TemporaryDirectory() as tmp:
                root, archive, receipt, package_script = self._fixture(
                    Path(tmp)
                )
                prepare_site_candidate.prepare_site_candidate(
                    root,
                    archive,
                    receipt,
                    package_script,
                    run_command=FakeCommandRunner(root, archive),
                )
                approved_digest = hashlib.sha256(
                    receipt.read_bytes()
                ).hexdigest()

                with self.assertRaisesRegex(
                    prepare_site_candidate.SiteCandidateError,
                    "repository does not match approved Sites repository",
                ):
                    prepare_site_candidate.verify_site_candidate(
                        root,
                        archive,
                        receipt,
                        expected_receipt_sha256=approved_digest,
                        exported_source_repository=SITES_SOURCE_REMOTE,
                        expected_exported_source_repository=(
                            SITES_SOURCE_REPOSITORY
                        ),
                        run_command=FakeCommandRunner(
                            root,
                            archive,
                            exported_source_repositories=(repository,),
                        ),
                    )

    def test_pre_save_verification_accepts_recorded_canonical_identity(
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
            approved_digest = hashlib.sha256(receipt.read_bytes()).hexdigest()

            result = prepare_site_candidate.verify_site_candidate(
                root,
                archive,
                receipt,
                expected_receipt_sha256=approved_digest,
                exported_source_repository=SITES_SOURCE_REMOTE,
                expected_exported_source_repository=(
                    "sites.example/repo-scout"
                ),
                run_command=FakeCommandRunner(root, archive),
            )

            self.assertEqual(result.commit_sha, COMMIT_SHA)

    def test_pre_save_verification_matches_approved_ssh_username(
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
            approved_digest = hashlib.sha256(receipt.read_bytes()).hexdigest()

            result = prepare_site_candidate.verify_site_candidate(
                root,
                archive,
                receipt,
                expected_receipt_sha256=approved_digest,
                exported_source_repository=SITES_SOURCE_REMOTE,
                expected_exported_source_repository=(
                    "alice@sites.example/repo-scout"
                ),
                run_command=FakeCommandRunner(
                    root,
                    archive,
                    exported_source_repositories=(
                        "ssh://alice@sites.example:22/repo-scout.git",
                    ),
                    exported_source_shas=(COMMIT_SHA, COMMIT_SHA),
                ),
            )

            self.assertEqual(result.commit_sha, COMMIT_SHA)

    def test_pre_save_verification_rejects_scp_relative_path_alias(
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
            approved_digest = hashlib.sha256(receipt.read_bytes()).hexdigest()

            with self.assertRaisesRegex(
                prepare_site_candidate.SiteCandidateError,
                "repository does not match approved Sites repository",
            ):
                prepare_site_candidate.verify_site_candidate(
                    root,
                    archive,
                    receipt,
                    expected_receipt_sha256=approved_digest,
                    exported_source_repository=SITES_SOURCE_REMOTE,
                    expected_exported_source_repository=(
                        "alice@sites.example/repo-scout"
                    ),
                    run_command=FakeCommandRunner(
                        root,
                        archive,
                        exported_source_repositories=(
                            "alice@sites.example:repo-scout.git",
                        ),
                    ),
                )

    def test_pre_save_verification_rejects_scp_relative_marker_collision(
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
            approved_digest = hashlib.sha256(receipt.read_bytes()).hexdigest()

            with self.assertRaisesRegex(
                prepare_site_candidate.SiteCandidateError,
                "repository does not match approved Sites repository",
            ):
                prepare_site_candidate.verify_site_candidate(
                    root,
                    archive,
                    receipt,
                    expected_receipt_sha256=approved_digest,
                    exported_source_repository=SITES_SOURCE_REMOTE,
                    expected_exported_source_repository=(
                        "alice@sites.example/~/repo-scout"
                    ),
                    run_command=FakeCommandRunner(
                        root,
                        archive,
                        exported_source_repositories=(
                            "alice@sites.example:repo-scout.git",
                        ),
                    ),
                )

    def test_pre_save_verification_matches_recorded_scp_relative_identity(
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
            approved_digest = hashlib.sha256(receipt.read_bytes()).hexdigest()

            result = prepare_site_candidate.verify_site_candidate(
                root,
                archive,
                receipt,
                expected_receipt_sha256=approved_digest,
                exported_source_repository=SITES_SOURCE_REMOTE,
                expected_exported_source_repository=(
                    "scp-relative://alice@sites.example/repo-scout"
                ),
                run_command=FakeCommandRunner(
                    root,
                    archive,
                    exported_source_repositories=(
                        "alice@sites.example:repo-scout.git",
                    ),
                    exported_source_shas=(COMMIT_SHA, COMMIT_SHA),
                ),
            )

            self.assertEqual(result.commit_sha, COMMIT_SHA)

    def test_pre_save_verification_rejects_scp_prefix_host_port_collision(
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
            approved_digest = hashlib.sha256(receipt.read_bytes()).hexdigest()

            with self.assertRaisesRegex(
                prepare_site_candidate.SiteCandidateError,
                "repository does not match approved Sites repository",
            ):
                prepare_site_candidate.verify_site_candidate(
                    root,
                    archive,
                    receipt,
                    expected_receipt_sha256=approved_digest,
                    exported_source_repository=SITES_SOURCE_REMOTE,
                    expected_exported_source_repository=(
                        "https://scp-relative:8443/repo.git"
                    ),
                    run_command=FakeCommandRunner(
                        root,
                        archive,
                        exported_source_repositories=("8443:repo.git",),
                    ),
                )

    def test_pre_save_verification_matches_scp_absolute_path(
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
            approved_digest = hashlib.sha256(receipt.read_bytes()).hexdigest()

            result = prepare_site_candidate.verify_site_candidate(
                root,
                archive,
                receipt,
                expected_receipt_sha256=approved_digest,
                exported_source_repository=SITES_SOURCE_REMOTE,
                expected_exported_source_repository=(
                    "alice@sites.example/repo-scout"
                ),
                run_command=FakeCommandRunner(
                    root,
                    archive,
                    exported_source_repositories=(
                        "alice@sites.example:/repo-scout.git",
                    ),
                    exported_source_shas=(COMMIT_SHA, COMMIT_SHA),
                ),
            )

            self.assertEqual(result.commit_sha, COMMIT_SHA)

    def test_pre_save_verification_accepts_default_port_protocol_alias(
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
            approved_digest = hashlib.sha256(receipt.read_bytes()).hexdigest()

            result = prepare_site_candidate.verify_site_candidate(
                root,
                archive,
                receipt,
                expected_receipt_sha256=approved_digest,
                exported_source_repository=SITES_SOURCE_REMOTE,
                expected_exported_source_repository=(
                    SITES_SOURCE_REPOSITORY
                ),
                run_command=FakeCommandRunner(
                    root,
                    archive,
                    exported_source_repositories=(
                        "ssh://git@sites.example:22/repo-scout.git",
                    ),
                    exported_source_shas=(COMMIT_SHA, COMMIT_SHA),
                ),
            )

            self.assertEqual(result.commit_sha, COMMIT_SHA)

    def test_pre_save_verification_rejects_local_repository(self) -> None:
        with TemporaryDirectory() as tmp:
            root, archive, receipt, package_script = self._fixture(Path(tmp))
            prepare_site_candidate.prepare_site_candidate(
                root,
                archive,
                receipt,
                package_script,
                run_command=FakeCommandRunner(root, archive),
            )
            approved_digest = hashlib.sha256(receipt.read_bytes()).hexdigest()

            with self.assertRaisesRegex(
                prepare_site_candidate.SiteCandidateError,
                "exported source repository must resolve to a remote Git "
                "repository",
            ):
                prepare_site_candidate.verify_site_candidate(
                    root,
                    archive,
                    receipt,
                    expected_receipt_sha256=approved_digest,
                    exported_source_repository=".",
                    expected_exported_source_repository=(
                        SITES_SOURCE_REPOSITORY
                    ),
                    run_command=FakeCommandRunner(
                        root,
                        archive,
                        exported_source_repositories=(".",),
                    ),
                )

    def test_pre_save_verification_rejects_repository_identity_drift(
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
            approved_digest = hashlib.sha256(receipt.read_bytes()).hexdigest()

            with self.assertRaisesRegex(
                prepare_site_candidate.SiteCandidateError,
                "exported source repository identity moved during candidate "
                "operation",
            ):
                prepare_site_candidate.verify_site_candidate(
                    root,
                    archive,
                    receipt,
                    expected_receipt_sha256=approved_digest,
                    exported_source_repository=SITES_SOURCE_REMOTE,
                    expected_exported_source_repository=(
                        SITES_SOURCE_REPOSITORY
                    ),
                    run_command=FakeCommandRunner(
                        root,
                        archive,
                        exported_source_repositories=(
                            SITES_SOURCE_REPOSITORY,
                            "https://sites.example/other.git",
                        ),
                    ),
                )

    def test_pre_save_verification_rejects_unapproved_repository(
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
            approved_digest = hashlib.sha256(receipt.read_bytes()).hexdigest()

            with self.assertRaisesRegex(
                prepare_site_candidate.SiteCandidateError,
                "repository does not match approved Sites repository",
            ):
                prepare_site_candidate.verify_site_candidate(
                    root,
                    archive,
                    receipt,
                    expected_receipt_sha256=approved_digest,
                    exported_source_repository=UNRELATED_SOURCE_REPOSITORY,
                    expected_exported_source_repository=(
                        SITES_SOURCE_REPOSITORY
                    ),
                    run_command=FakeCommandRunner(
                        root,
                        archive,
                        exported_source_repositories=(
                            UNRELATED_SOURCE_REPOSITORY,
                        ),
                    ),
                )

    def test_pre_save_verification_checks_exported_source_twice(self) -> None:
        with TemporaryDirectory() as tmp:
            root, archive, receipt, package_script = self._fixture(Path(tmp))
            prepare_site_candidate.prepare_site_candidate(
                root,
                archive,
                receipt,
                package_script,
                run_command=FakeCommandRunner(root, archive),
            )
            approved_digest = hashlib.sha256(receipt.read_bytes()).hexdigest()
            runner = FakeCommandRunner(
                root,
                archive,
                exported_source_repositories=(
                    "git@sites.example:repo-scout.git",
                ),
                exported_source_shas=(COMMIT_SHA, COMMIT_SHA),
            )

            result = prepare_site_candidate.verify_site_candidate(
                root,
                archive,
                receipt,
                expected_receipt_sha256=approved_digest,
                exported_source_repository=SITES_SOURCE_REMOTE,
                expected_exported_source_repository=(
                    SITES_SOURCE_REPOSITORY
                ),
                run_command=runner,
            )

            self.assertEqual(result.commit_sha, COMMIT_SHA)
            self.assertEqual(
                runner.commands.count(
                    (
                        "git",
                        "ls-remote",
                        "--exit-code",
                        "--refs",
                        SITES_SOURCE_REMOTE,
                        prepare_site_candidate.SOURCE_REF,
                    )
                ),
                2,
            )

    def test_pre_save_verification_rejects_wrong_exported_source(self) -> None:
        with TemporaryDirectory() as tmp:
            root, archive, receipt, package_script = self._fixture(Path(tmp))
            prepare_site_candidate.prepare_site_candidate(
                root,
                archive,
                receipt,
                package_script,
                run_command=FakeCommandRunner(root, archive),
            )
            approved_digest = hashlib.sha256(receipt.read_bytes()).hexdigest()

            with self.assertRaisesRegex(
                prepare_site_candidate.SiteCandidateError,
                "exported source does not match approved candidate",
            ):
                prepare_site_candidate.verify_site_candidate(
                    root,
                    archive,
                    receipt,
                    expected_receipt_sha256=approved_digest,
                    exported_source_repository=SITES_SOURCE_REPOSITORY,
                    expected_exported_source_repository=(
                        SITES_SOURCE_REPOSITORY
                    ),
                    run_command=FakeCommandRunner(
                        root,
                        archive,
                        exported_source_shas=("b" * 40,),
                    ),
                )

    def test_pre_save_verification_rejects_exported_source_drift(self) -> None:
        with TemporaryDirectory() as tmp:
            root, archive, receipt, package_script = self._fixture(Path(tmp))
            prepare_site_candidate.prepare_site_candidate(
                root,
                archive,
                receipt,
                package_script,
                run_command=FakeCommandRunner(root, archive),
            )
            approved_digest = hashlib.sha256(receipt.read_bytes()).hexdigest()

            with self.assertRaisesRegex(
                prepare_site_candidate.SiteCandidateError,
                "exported source moved during candidate operation",
            ):
                prepare_site_candidate.verify_site_candidate(
                    root,
                    archive,
                    receipt,
                    expected_receipt_sha256=approved_digest,
                    exported_source_repository=SITES_SOURCE_REPOSITORY,
                    expected_exported_source_repository=(
                        SITES_SOURCE_REPOSITORY
                    ),
                    run_command=FakeCommandRunner(
                        root,
                        archive,
                        exported_source_shas=(COMMIT_SHA, "b" * 40),
                    ),
                )

    def test_preparation_rejects_archive_changed_during_receipt_publication(
        self,
    ) -> None:
        with TemporaryDirectory() as tmp:
            root, archive, receipt, package_script = self._fixture(Path(tmp))
            create_receipt = prepare_site_candidate._atomic_create_json

            def create_then_mutate_archive(
                path: Path,
                payload: dict[str, object],
                label: str,
                parent_fd: int,
            ) -> tuple[str, prepare_site_candidate._PublishedOutput]:
                receipt_result = create_receipt(
                    path,
                    payload,
                    label,
                    parent_fd,
                )
                with archive.open("ab") as target:
                    target.write(b"changed during receipt publication\n")
                return receipt_result

            with (
                patch.object(
                    prepare_site_candidate,
                    "_atomic_create_json",
                    side_effect=create_then_mutate_archive,
                ),
                self.assertRaisesRegex(
                    prepare_site_candidate.SiteCandidateError,
                    "Sites candidate archive changed during candidate "
                    "operation",
                ),
            ):
                prepare_site_candidate.prepare_site_candidate(
                    root,
                    archive,
                    receipt,
                    package_script,
                    run_command=FakeCommandRunner(root, archive),
                )

            self.assertTrue(archive.is_file())
            self.assertTrue(receipt.is_file())

    def test_preparation_rejects_receipt_changed_during_publication(
        self,
    ) -> None:
        with TemporaryDirectory() as tmp:
            root, archive, receipt, package_script = self._fixture(Path(tmp))
            create_receipt = prepare_site_candidate._atomic_create_json

            def create_then_mutate_receipt(
                path: Path,
                payload: dict[str, object],
                label: str,
                parent_fd: int,
            ) -> tuple[str, prepare_site_candidate._PublishedOutput]:
                receipt_result = create_receipt(
                    path,
                    payload,
                    label,
                    parent_fd,
                )
                with receipt.open("ab") as target:
                    target.write(b"changed during publication\n")
                return receipt_result

            with (
                patch.object(
                    prepare_site_candidate,
                    "_atomic_create_json",
                    side_effect=create_then_mutate_receipt,
                ),
                self.assertRaisesRegex(
                    prepare_site_candidate.SiteCandidateError,
                    "Sites candidate receipt changed during candidate "
                    "operation",
                ),
            ):
                prepare_site_candidate.prepare_site_candidate(
                    root,
                    archive,
                    receipt,
                    package_script,
                    run_command=FakeCommandRunner(root, archive),
                )

            self.assertTrue(archive.is_file())
            self.assertTrue(receipt.is_file())

    def test_preparation_rejects_receipt_bytes_changed_before_hashing(
        self,
    ) -> None:
        with TemporaryDirectory() as tmp:
            root, archive, receipt, package_script = self._fixture(Path(tmp))
            hash_open_file = (
                prepare_site_candidate._sha256_open_regular_file
            )
            mutated_receipt = False

            def mutate_receipt_before_hashing(
                descriptor: int,
                label: str,
            ) -> str:
                nonlocal mutated_receipt
                if label == "staged receipt output" and not mutated_receipt:
                    prepare_site_candidate.os.lseek(
                        descriptor,
                        0,
                        prepare_site_candidate.os.SEEK_END,
                    )
                    prepare_site_candidate.os.write(
                        descriptor,
                        b'{"substituted": true}\n',
                    )
                    prepare_site_candidate.os.fsync(descriptor)
                    mutated_receipt = True
                return hash_open_file(descriptor, label)

            with (
                patch.object(
                    prepare_site_candidate,
                    "_sha256_open_regular_file",
                    side_effect=mutate_receipt_before_hashing,
                ),
                self.assertRaisesRegex(
                    prepare_site_candidate.SiteCandidateError,
                    "staged receipt output changed during candidate "
                    "operation",
                ),
            ):
                prepare_site_candidate.prepare_site_candidate(
                    root,
                    archive,
                    receipt,
                    package_script,
                    run_command=FakeCommandRunner(root, archive),
                )

            self.assertTrue(mutated_receipt)
            self.assertTrue(archive.is_file())
            self.assertFalse(receipt.exists())
            self.assertEqual(
                list(receipt.parent.glob(f".{receipt.name}.*.tmp")),
                [],
            )

    def test_preparation_rejects_identical_receipt_leaf_replacement(
        self,
    ) -> None:
        with TemporaryDirectory() as tmp:
            root, archive, receipt, package_script = self._fixture(Path(tmp))
            publish_output = prepare_site_candidate._publish_new_output
            replacement_content: list[bytes] = []

            def replace_receipt_before_publication(
                staged_path: Path,
                output_path: Path,
                label: str,
                parent_fd: int,
                *,
                source_descriptor: int | None = None,
                source_parent_descriptor: int | None = None,
            ) -> prepare_site_candidate._PublishedOutput:
                if label == "receipt":
                    if (
                        source_descriptor is None
                        or source_parent_descriptor is None
                    ):
                        raise AssertionError(
                            "receipt publication omitted staging "
                            "descriptors"
                        )
                    prepare_site_candidate.os.lseek(
                        source_descriptor,
                        0,
                        prepare_site_candidate.os.SEEK_SET,
                    )
                    content = b""
                    while True:
                        chunk = prepare_site_candidate.os.read(
                            source_descriptor,
                            1024 * 1024,
                        )
                        if not chunk:
                            break
                        content += chunk
                    replacement_content.append(content)
                    prepare_site_candidate.os.unlink(
                        staged_path.name,
                        dir_fd=source_parent_descriptor,
                    )
                    flags = (
                        prepare_site_candidate.os.O_WRONLY
                        | prepare_site_candidate.os.O_CREAT
                        | prepare_site_candidate.os.O_EXCL
                        | prepare_site_candidate.os.O_NOFOLLOW
                    )
                    if hasattr(prepare_site_candidate.os, "O_CLOEXEC"):
                        flags |= prepare_site_candidate.os.O_CLOEXEC
                    replacement_descriptor = (
                        prepare_site_candidate.os.open(
                            staged_path.name,
                            flags,
                            0o600,
                            dir_fd=source_parent_descriptor,
                        )
                    )
                    try:
                        remaining = memoryview(content)
                        while remaining:
                            written = prepare_site_candidate.os.write(
                                replacement_descriptor,
                                remaining,
                            )
                            remaining = remaining[written:]
                        prepare_site_candidate.os.fsync(
                            replacement_descriptor
                        )
                    finally:
                        prepare_site_candidate.os.close(
                            replacement_descriptor
                        )
                return publish_output(
                    staged_path,
                    output_path,
                    label,
                    parent_fd,
                    source_descriptor=source_descriptor,
                    source_parent_descriptor=source_parent_descriptor,
                )

            with (
                patch.object(
                    prepare_site_candidate,
                    "_publish_new_output",
                    side_effect=replace_receipt_before_publication,
                ),
                self.assertRaisesRegex(
                    prepare_site_candidate.SiteCandidateError,
                    "receipt staging source changed during publication",
                ),
            ):
                prepare_site_candidate.prepare_site_candidate(
                    root,
                    archive,
                    receipt,
                    package_script,
                    run_command=FakeCommandRunner(root, archive),
                )

            self.assertEqual(len(replacement_content), 1)
            self.assertTrue(archive.is_file())
            self.assertFalse(receipt.exists())
            leaked_staging = list(
                receipt.parent.glob(f".{receipt.name}.*.tmp")
            )
            self.assertEqual(len(leaked_staging), 1)
            self.assertEqual(
                leaked_staging[0].read_bytes(),
                replacement_content[0],
            )

    def test_receipt_cleanup_failure_closes_published_descriptors(
        self,
    ) -> None:
        with TemporaryDirectory() as tmp:
            root, archive, receipt, package_script = self._fixture(Path(tmp))
            publish_output = prepare_site_candidate._publish_new_output
            staged_receipt_descriptor = -1
            published_receipt_descriptor = -1
            displaced_staging: Path | None = None
            replacement_staging: Path | None = None

            def replace_receipt_before_cleanup(
                staged_path: Path,
                output_path: Path,
                label: str,
                parent_fd: int,
                *,
                source_descriptor: int | None = None,
                source_parent_descriptor: int | None = None,
            ) -> prepare_site_candidate._PublishedOutput:
                nonlocal staged_receipt_descriptor
                nonlocal published_receipt_descriptor
                nonlocal displaced_staging
                nonlocal replacement_staging
                published = publish_output(
                    staged_path,
                    output_path,
                    label,
                    parent_fd,
                    source_descriptor=source_descriptor,
                    source_parent_descriptor=source_parent_descriptor,
                )
                if label == "receipt":
                    if (
                        source_descriptor is None
                        or source_parent_descriptor is None
                    ):
                        raise AssertionError(
                            "receipt publication omitted staging "
                            "descriptors"
                        )
                    staged_receipt_descriptor = source_descriptor
                    published_receipt_descriptor = published.fd
                    displaced_staging = (
                        receipt.parent / f"{staged_path.name}.displaced"
                    )
                    replacement_staging = receipt.parent / staged_path.name
                    prepare_site_candidate.os.rename(
                        staged_path.name,
                        displaced_staging.name,
                        src_dir_fd=source_parent_descriptor,
                        dst_dir_fd=source_parent_descriptor,
                    )
                    replacement_staging.write_bytes(
                        b'{"candidate": "replacement"}\n'
                    )
                return published

            with (
                patch.object(
                    prepare_site_candidate,
                    "_publish_new_output",
                    side_effect=replace_receipt_before_cleanup,
                ),
                self.assertRaisesRegex(
                    prepare_site_candidate.SiteCandidateError,
                    "receipt output was published .* but staging cleanup "
                    "failed",
                ),
            ):
                prepare_site_candidate.prepare_site_candidate(
                    root,
                    archive,
                    receipt,
                    package_script,
                    run_command=FakeCommandRunner(root, archive),
                )

            self.assertTrue(archive.is_file())
            self.assertTrue(receipt.is_file())
            self.assertIsNotNone(displaced_staging)
            self.assertIsNotNone(replacement_staging)
            self.assertTrue(displaced_staging.is_file())
            self.assertTrue(replacement_staging.is_file())
            for descriptor in (
                staged_receipt_descriptor,
                published_receipt_descriptor,
            ):
                with self.assertRaises(OSError) as caught:
                    prepare_site_candidate.os.fstat(descriptor)
                self.assertEqual(caught.exception.errno, errno.EBADF)

    def test_preparation_rejects_byte_identical_archive_replacement(
        self,
    ) -> None:
        with TemporaryDirectory() as tmp:
            root, archive, receipt, package_script = self._fixture(Path(tmp))
            create_receipt = prepare_site_candidate._atomic_create_json

            def create_then_replace_archive(
                path: Path,
                payload: dict[str, object],
                label: str,
                parent_fd: int,
            ) -> tuple[str, prepare_site_candidate._PublishedOutput]:
                receipt_result = create_receipt(
                    path,
                    payload,
                    label,
                    parent_fd,
                )
                content = archive.read_bytes()
                archive.unlink()
                archive.write_bytes(content)
                return receipt_result

            with (
                patch.object(
                    prepare_site_candidate,
                    "_atomic_create_json",
                    side_effect=create_then_replace_archive,
                ),
                self.assertRaisesRegex(
                    prepare_site_candidate.SiteCandidateError,
                    "Sites candidate archive changed during candidate "
                    "operation",
                ),
            ):
                prepare_site_candidate.prepare_site_candidate(
                    root,
                    archive,
                    receipt,
                    package_script,
                    run_command=FakeCommandRunner(root, archive),
                )

            self.assertTrue(archive.is_file())
            self.assertTrue(receipt.is_file())

    def test_preparation_rejects_replaced_parent_with_same_archive(
        self,
    ) -> None:
        with TemporaryDirectory() as tmp:
            temporary_root = Path(tmp)
            root, archive, receipt, package_script = self._fixture(
                temporary_root
            )
            archive_parent = temporary_root / "archive-output"
            receipt_parent = temporary_root / "receipt-output"
            displaced_parent = temporary_root / "displaced-archive-output"
            archive_parent.mkdir()
            receipt_parent.mkdir()
            archive = (archive_parent / archive.name).resolve()
            receipt = (receipt_parent / receipt.name).resolve()
            create_receipt = prepare_site_candidate._atomic_create_json

            def create_then_replace_archive_parent(
                path: Path,
                payload: dict[str, object],
                label: str,
                parent_fd: int,
            ) -> tuple[str, prepare_site_candidate._PublishedOutput]:
                receipt_result = create_receipt(
                    path,
                    payload,
                    label,
                    parent_fd,
                )
                archive_parent.rename(displaced_parent)
                archive_parent.mkdir()
                prepare_site_candidate.os.link(
                    displaced_parent / archive.name,
                    archive,
                )
                return receipt_result

            with (
                patch.object(
                    prepare_site_candidate,
                    "_atomic_create_json",
                    side_effect=create_then_replace_archive_parent,
                ),
                self.assertRaisesRegex(
                    prepare_site_candidate.SiteCandidateError,
                    "Sites candidate archive changed during candidate "
                    "operation",
                ),
            ):
                prepare_site_candidate.prepare_site_candidate(
                    root,
                    archive,
                    receipt,
                    package_script,
                    run_command=FakeCommandRunner(root, archive),
                )

            self.assertTrue(archive.is_file())
            self.assertTrue(receipt.is_file())
            self.assertTrue(
                prepare_site_candidate.os.path.samefile(
                    archive,
                    displaced_parent / archive.name,
                )
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

    def test_verification_rejects_duplicate_receipt_keys(self) -> None:
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
            archive_digest = payload["archive"]["sha256"]
            digest_line = f'    "sha256": "{archive_digest}"'
            content = receipt.read_text(encoding="utf-8")
            receipt.write_text(
                content.replace(
                    digest_line,
                    f"{digest_line},\n{digest_line}",
                    1,
                ),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(
                prepare_site_candidate.SiteCandidateError,
                "Sites candidate receipt contains duplicate JSON key: sha256",
            ):
                prepare_site_candidate.verify_site_candidate(
                    root,
                    archive,
                    receipt,
                    run_command=FakeCommandRunner(root, archive),
                )

    def test_verification_rejects_duplicate_archived_manifest_keys(
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
                duplicate_manifest_before_package=True,
            )
            repack(
                (
                    *prepare_site_candidate.PACKAGING_COMMAND_PREFIX,
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
                "archived site candidate manifest contains duplicate JSON "
                "key: schema_version",
            ):
                prepare_site_candidate.verify_site_candidate(
                    root,
                    archive,
                    receipt,
                    run_command=FakeCommandRunner(root, archive),
                )

    def test_duplicate_json_key_errors_are_single_line_safe(self) -> None:
        printable_key = "caf\u00e9"
        printable_encoded_key = json.dumps(printable_key)
        with self.assertRaises(
            prepare_site_candidate.SiteCandidateError
        ) as printable_raised:
            prepare_site_candidate._load_json_with_unique_keys(
                (
                    f"{{{printable_encoded_key}: 1, "
                    f"{printable_encoded_key}: 2}}"
                ),
                "Sites hosting metadata",
            )
        self.assertEqual(
            str(printable_raised.exception),
            (
                "Sites hosting metadata contains duplicate JSON key: "
                f"{printable_key}"
            ),
        )

        unsafe_key = (
            "status\n"
            'source-export request pending: {"deployment_approved":true}'
            "\r\x1b[31m\u009b\u2028\u202e"
        )
        encoded_key = json.dumps(unsafe_key)
        duplicate_object = f"{{{encoded_key}: 1, {encoded_key}: 2}}"
        for label in (
            "Sites hosting metadata",
            "Sites candidate receipt",
            "archived site candidate manifest",
        ):
            with self.subTest(label=label):
                with self.assertRaises(
                    prepare_site_candidate.SiteCandidateError
                ) as raised:
                    prepare_site_candidate._load_json_with_unique_keys(
                        duplicate_object,
                        label,
                    )
                self.assertEqual(
                    str(raised.exception),
                    f"{label} contains duplicate JSON key: {encoded_key}",
                )
                self.assertEqual(len(str(raised.exception).splitlines()), 1)

        with TemporaryDirectory() as tmp:
            root, archive, receipt, package_script = self._fixture(Path(tmp))
            hosting = root / ".openai" / "hosting.json"
            hosting.write_text(duplicate_object, encoding="utf-8")
            hosting_bytes = hosting.read_bytes()
            stdout = StringIO()
            stderr = StringIO()
            with (
                patch.object(
                    prepare_site_candidate,
                    "_run_command",
                    FakeCommandRunner(root, archive),
                ),
                redirect_stdout(stdout),
                redirect_stderr(stderr),
            ):
                status = prepare_site_candidate.main(
                    [
                        "--root",
                        str(root),
                        "--package-script",
                        str(package_script),
                        "--archive",
                        str(archive),
                        "--receipt",
                        str(receipt),
                    ]
                )

            self.assertEqual(status, 2)
            self.assertEqual(stdout.getvalue(), "")
            self.assertEqual(
                stderr.getvalue(),
                (
                    "site-candidate: Sites hosting metadata contains "
                    f"duplicate JSON key: {encoded_key}\n"
                ),
            )
            self.assertEqual(hosting.read_bytes(), hosting_bytes)
            self.assertFalse(archive.exists())
            self.assertFalse(receipt.exists())

        with TemporaryDirectory() as tmp:
            root, archive, receipt, package_script = self._fixture(Path(tmp))
            prepare_site_candidate.prepare_site_candidate(
                root,
                archive,
                receipt,
                package_script,
                run_command=FakeCommandRunner(root, archive),
            )
            content = receipt.read_text(encoding="utf-8")
            receipt.write_text(
                content.replace(
                    "{\n",
                    (
                        "{\n"
                        f"  {encoded_key}: 1,\n"
                        f"  {encoded_key}: 2,\n"
                    ),
                    1,
                ),
                encoding="utf-8",
            )
            receipt_bytes = receipt.read_bytes()
            archive_bytes = archive.read_bytes()
            stdout = StringIO()
            stderr = StringIO()
            with (
                patch.object(
                    prepare_site_candidate,
                    "_run_command",
                    FakeCommandRunner(root, archive),
                ),
                redirect_stdout(stdout),
                redirect_stderr(stderr),
            ):
                status = prepare_site_candidate.main(
                    [
                        "--verify-only",
                        "--root",
                        str(root),
                        "--archive",
                        str(archive),
                        "--receipt",
                        str(receipt),
                    ]
                )

            self.assertEqual(status, 2)
            self.assertEqual(stdout.getvalue(), "")
            self.assertEqual(
                stderr.getvalue(),
                (
                    "site-candidate: Sites candidate receipt contains "
                    f"duplicate JSON key: {encoded_key}\n"
                ),
            )
            self.assertEqual(receipt.read_bytes(), receipt_bytes)
            self.assertEqual(archive.read_bytes(), archive_bytes)

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
                    *prepare_site_candidate.PACKAGING_COMMAND_PREFIX,
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

    def test_verification_rejects_checkout_release_version_drift(
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
            changed_version = "0.3.52"
            (root / "pyproject.toml").write_text(
                f'[project]\nversion = "{changed_version}"\n',
                encoding="utf-8",
            )
            (root / "app" / "site-config.ts").write_text(
                f'export const RELEASE_VERSION = "{changed_version}";\n',
                encoding="utf-8",
            )

            with self.assertRaisesRegex(
                prepare_site_candidate.SiteCandidateError,
                "receipt candidate release_version does not match checkout",
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

    def test_verification_rejects_receipts_before_release_binding(
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
            payload = json.loads(receipt.read_text(encoding="utf-8"))
            payload["schema_version"] = 4
            receipt.write_text(json.dumps(payload), encoding="utf-8")

            with self.assertRaisesRegex(
                prepare_site_candidate.SiteCandidateError,
                "receipt schema_version must be 5",
            ):
                prepare_site_candidate.verify_site_candidate(
                    root,
                    archive,
                    receipt,
                    run_command=FakeCommandRunner(root, archive),
                )

    def test_output_help_distinguishes_prepare_and_verify_paths(self) -> None:
        help_text = " ".join(
            prepare_site_candidate.build_parser().format_help().split()
        )

        self.assertEqual(
            help_text.count(
                "Preparation requires a new path in an existing parent "
                "directory; --verify-only requires an existing path."
            ),
            2,
        )
        self.assertIn(
            "It must resolve to the approved remote identity, separate from "
            "origin.",
            help_text,
        )
        self.assertIn(
            "Requires both exported source repository options.",
            help_text,
        )
        self.assertIn(
            "resolve its canonical identity locally, reject origin, and "
            "print a pending source-export request without querying the "
            "remote or granting approval",
            help_text,
        )

    def test_resolves_a_separate_approval_source_repository_locally(
        self,
    ) -> None:
        with TemporaryDirectory() as tmp:
            root, archive, _, _ = self._fixture(Path(tmp))
            runner = FakeCommandRunner(root, archive)

            identity = (
                prepare_site_candidate._approval_source_repository_identity(
                    root,
                    SITES_SOURCE_REMOTE,
                    run_command=runner,
                )
            )

        self.assertEqual(identity, "sites.example/repo-scout")
        self.assertEqual(
            runner.commands,
            [
                (
                    "git",
                    "ls-remote",
                    "--get-url",
                    SITES_SOURCE_REMOTE,
                ),
                ("git", "ls-remote", "--get-url", "origin"),
            ],
        )

    def test_pending_approval_identity_preserves_ssh_username(self) -> None:
        with TemporaryDirectory() as tmp:
            root, archive, _, _ = self._fixture(Path(tmp))
            runner = FakeCommandRunner(
                root,
                archive,
                exported_source_repositories=(
                    "ssh://alice@sites.example:22/repo-scout.git",
                ),
            )

            identity = (
                prepare_site_candidate._approval_source_repository_identity(
                    root,
                    SITES_SOURCE_REMOTE,
                    run_command=runner,
                )
            )

        self.assertEqual(identity, "alice@sites.example/repo-scout")

    def test_pending_approval_identity_marks_scp_relative_path(self) -> None:
        with TemporaryDirectory() as tmp:
            root, archive, _, _ = self._fixture(Path(tmp))
            runner = FakeCommandRunner(
                root,
                archive,
                exported_source_repositories=(
                    "alice@sites.example:repo-scout.git",
                ),
            )

            identity = (
                prepare_site_candidate._approval_source_repository_identity(
                    root,
                    SITES_SOURCE_REMOTE,
                    run_command=runner,
                )
            )

        self.assertEqual(
            identity,
            "scp-relative://alice@sites.example/repo-scout",
        )

    def test_rejects_whitespace_ambiguous_approval_repository_identity(
        self,
    ) -> None:
        with TemporaryDirectory() as tmp:
            root, archive, _, _ = self._fixture(Path(tmp))
            runner = FakeCommandRunner(
                root,
                archive,
                exported_source_repositories=(
                    "https://sites.example/repo scout.git",
                ),
            )

            with self.assertRaisesRegex(
                prepare_site_candidate.SiteCandidateError,
                "must not contain whitespace",
            ):
                (
                    prepare_site_candidate
                    ._approval_source_repository_identity(
                        root,
                        SITES_SOURCE_REMOTE,
                        run_command=runner,
                    )
                )

        self.assertEqual(
            runner.commands,
            [
                (
                    "git",
                    "ls-remote",
                    "--get-url",
                    SITES_SOURCE_REMOTE,
                ),
            ],
        )

    def test_accepts_percent_encoded_approval_repository_identity(
        self,
    ) -> None:
        with TemporaryDirectory() as tmp:
            root, archive, _, _ = self._fixture(Path(tmp))
            runner = FakeCommandRunner(
                root,
                archive,
                exported_source_repositories=(
                    "https://sites.example/repo%20scout.git",
                ),
            )

            identity = (
                prepare_site_candidate._approval_source_repository_identity(
                    root,
                    SITES_SOURCE_REMOTE,
                    run_command=runner,
                )
            )

        self.assertEqual(identity, "sites.example/repo%20scout")
        self.assertEqual(
            runner.commands,
            [
                (
                    "git",
                    "ls-remote",
                    "--get-url",
                    SITES_SOURCE_REMOTE,
                ),
                ("git", "ls-remote", "--get-url", "origin"),
            ],
        )

    def test_rejects_origin_as_the_approval_source_repository(self) -> None:
        with TemporaryDirectory() as tmp:
            root, archive, _, _ = self._fixture(Path(tmp))
            runner = FakeCommandRunner(
                root,
                archive,
                exported_source_repositories=(ORIGIN_REPOSITORY,),
            )

            with self.assertRaisesRegex(
                prepare_site_candidate.SiteCandidateError,
                "must be separate from origin",
            ):
                (
                    prepare_site_candidate
                    ._approval_source_repository_identity(
                        root,
                        SITES_SOURCE_REMOTE,
                        run_command=runner,
                    )
                )

    def test_verify_only_cli_does_not_require_a_packaging_helper(self) -> None:
        result = prepare_site_candidate.SiteCandidateResult(
            commit_sha=COMMIT_SHA,
            release_version=RELEASE_VERSION,
            project_id=PROJECT_ID,
            archive_sha256="c" * 64,
            receipt_sha256="e" * 64,
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
        output = stdout.getvalue().strip()
        self.assertTrue(output.startswith("site candidate verified: "))
        self.assertEqual(
            json.loads(output.removeprefix("site candidate verified: ")),
            {
                "archive": "candidate.tar.gz",
                "archive_sha256": "c" * 64,
                "commit": COMMIT_SHA,
                "project_id": PROJECT_ID,
                "receipt": "candidate.json",
                "receipt_sha256": "e" * 64,
                "release_version": RELEASE_VERSION,
            },
        )
        verify.assert_called_once_with(
            Path("/tmp/project"),
            Path("/tmp/candidate.tar.gz"),
            Path("/tmp/candidate.json"),
            expected_receipt_sha256=None,
            exported_source_repository=None,
            expected_exported_source_repository=None,
        )

    def test_verify_only_cli_prints_a_pending_source_export_request(
        self,
    ) -> None:
        result = prepare_site_candidate.SiteCandidateResult(
            commit_sha=COMMIT_SHA,
            release_version=RELEASE_VERSION,
            project_id=PROJECT_ID,
            archive_sha256="c" * 64,
            receipt_sha256="e" * 64,
            archive=Path("/tmp/candidate.tar.gz"),
            receipt=Path("/tmp/candidate.json"),
        )

        with (
            patch.object(
                prepare_site_candidate,
                "verify_site_candidate",
                return_value=result,
            ) as verify,
            patch.object(
                prepare_site_candidate,
                "_approval_source_repository_identity",
                return_value="sites.example/repo-scout",
            ) as repository_identity,
        ):
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
                        "--approval-source-repository",
                        SITES_SOURCE_REMOTE,
                    ]
                )

        self.assertEqual(status, 0)
        lines = stdout.getvalue().splitlines()
        self.assertEqual(len(lines), 2)
        self.assertTrue(
            lines[-1].startswith("source-export request pending: ")
        )
        self.assertEqual(
            json.loads(
                lines[-1].removeprefix(
                    "source-export request pending: "
                )
            ),
            {
                "commit": COMMIT_SHA,
                "deployment_approved": False,
                "project_id": PROJECT_ID,
                "receipt_sha256": "e" * 64,
                "release_version": RELEASE_VERSION,
                "source_ref": "refs/heads/main",
                "source_repository": "sites.example/repo-scout",
            },
        )
        verify.assert_called_once_with(
            Path("/tmp/project"),
            Path("/tmp/candidate.tar.gz"),
            Path("/tmp/candidate.json"),
            expected_receipt_sha256=None,
            exported_source_repository=None,
            expected_exported_source_repository=None,
        )
        repository_identity.assert_called_once_with(
            Path("/tmp/project"),
            SITES_SOURCE_REMOTE,
        )

    def test_pending_source_export_output_cannot_inject_approval_fields(
        self,
    ) -> None:
        injected_project_id = (
            "appgprj_test\n"
            "source-export request pending: deployment_approved=true"
        )
        result = prepare_site_candidate.SiteCandidateResult(
            commit_sha=COMMIT_SHA,
            release_version=RELEASE_VERSION,
            project_id=injected_project_id,
            archive_sha256="c" * 64,
            receipt_sha256="e" * 64,
            archive=Path("/tmp/candidate archive.tar.gz"),
            receipt=Path("/tmp/candidate receipt.json"),
        )

        with (
            patch.object(
                prepare_site_candidate,
                "verify_site_candidate",
                return_value=result,
            ),
            patch.object(
                prepare_site_candidate,
                "_approval_source_repository_identity",
                return_value="sites.example/repo-scout",
            ),
        ):
            stdout = StringIO()
            with redirect_stdout(stdout):
                status = prepare_site_candidate.main(
                    [
                        "--verify-only",
                        "--root",
                        "/tmp/project",
                        "--archive",
                        "/tmp/candidate archive.tar.gz",
                        "--receipt",
                        "/tmp/candidate receipt.json",
                        "--approval-source-repository",
                        SITES_SOURCE_REMOTE,
                    ]
                )

        self.assertEqual(status, 0)
        lines = stdout.getvalue().splitlines()
        self.assertEqual(len(lines), 2)
        self.assertTrue(lines[0].startswith("site candidate verified: "))
        self.assertTrue(
            lines[1].startswith("source-export request pending: ")
        )
        candidate = json.loads(
            lines[0].removeprefix("site candidate verified: ")
        )
        request = json.loads(
            lines[1].removeprefix("source-export request pending: ")
        )
        self.assertEqual(candidate["project_id"], injected_project_id)
        self.assertEqual(request["project_id"], injected_project_id)
        self.assertIs(request["deployment_approved"], False)
        self.assertEqual(
            set(request),
            {
                "commit",
                "deployment_approved",
                "project_id",
                "receipt_sha256",
                "release_version",
                "source_ref",
                "source_repository",
            },
        )

    def test_approval_source_repository_rejects_pre_save_mode(
        self,
    ) -> None:
        with patch.object(
            prepare_site_candidate,
            "verify_site_candidate",
        ) as verify:
            stderr = StringIO()
            with redirect_stderr(stderr), self.assertRaises(SystemExit) as ctx:
                prepare_site_candidate.main(
                    [
                        "--verify-only",
                        "--root",
                        "/tmp/project",
                        "--archive",
                        "/tmp/candidate.tar.gz",
                        "--receipt",
                        "/tmp/candidate.json",
                        "--approval-source-repository",
                        SITES_SOURCE_REMOTE,
                        "--expected-receipt-sha256",
                        "e" * 64,
                        "--exported-source-repository",
                        SITES_SOURCE_REMOTE,
                        "--expected-exported-source-repository",
                        SITES_SOURCE_REPOSITORY,
                    ]
                )

        self.assertEqual(ctx.exception.code, 2)
        self.assertIn(
            "--approval-source-repository cannot be combined with "
            "pre-save verification",
            stderr.getvalue(),
        )
        verify.assert_not_called()

    def test_approval_source_repository_requires_verify_only(self) -> None:
        with patch.object(
            prepare_site_candidate,
            "prepare_site_candidate",
        ) as prepare:
            stderr = StringIO()
            with redirect_stderr(stderr), self.assertRaises(SystemExit) as ctx:
                prepare_site_candidate.main(
                    [
                        "--root",
                        "/tmp/project",
                        "--package-script",
                        "/tmp/package-site.sh",
                        "--archive",
                        "/tmp/candidate.tar.gz",
                        "--receipt",
                        "/tmp/candidate.json",
                        "--approval-source-repository",
                        SITES_SOURCE_REMOTE,
                    ]
                )

        self.assertEqual(ctx.exception.code, 2)
        self.assertIn(
            "--approval-source-repository requires --verify-only",
            stderr.getvalue(),
        )
        prepare.assert_not_called()

    def test_verify_only_cli_rejects_digest_only_downgrade(self) -> None:
        with patch.object(
            prepare_site_candidate,
            "verify_site_candidate",
        ) as verify:
            stderr = StringIO()
            with redirect_stderr(stderr), self.assertRaises(SystemExit) as ctx:
                prepare_site_candidate.main(
                    [
                        "--verify-only",
                        "--root",
                        "/tmp/project",
                        "--archive",
                        "/tmp/candidate.tar.gz",
                        "--receipt",
                        "/tmp/candidate.json",
                        "--expected-receipt-sha256",
                        "e" * 64,
                    ]
                )

        self.assertEqual(ctx.exception.code, 2)
        self.assertIn(
            "--expected-receipt-sha256 requires "
            "--exported-source-repository",
            stderr.getvalue(),
        )
        verify.assert_not_called()

    def test_pre_save_cli_routes_exported_source_verification(self) -> None:
        result = prepare_site_candidate.SiteCandidateResult(
            commit_sha=COMMIT_SHA,
            release_version=RELEASE_VERSION,
            project_id=PROJECT_ID,
            archive_sha256="c" * 64,
            receipt_sha256="e" * 64,
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
                        "--expected-receipt-sha256",
                        "e" * 64,
                        "--exported-source-repository",
                        SITES_SOURCE_REPOSITORY,
                        "--expected-exported-source-repository",
                        SITES_SOURCE_REPOSITORY,
                    ]
                )

        self.assertEqual(status, 0)
        verify.assert_called_once_with(
            Path("/tmp/project"),
            Path("/tmp/candidate.tar.gz"),
            Path("/tmp/candidate.json"),
            expected_receipt_sha256="e" * 64,
            exported_source_repository=SITES_SOURCE_REPOSITORY,
            expected_exported_source_repository=SITES_SOURCE_REPOSITORY,
        )

    def test_prepare_cli_still_routes_through_the_packaging_helper(self) -> None:
        result = prepare_site_candidate.SiteCandidateResult(
            commit_sha=COMMIT_SHA,
            release_version=RELEASE_VERSION,
            project_id=PROJECT_ID,
            archive_sha256="d" * 64,
            receipt_sha256="f" * 64,
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
        output = stdout.getvalue().strip()
        self.assertTrue(output.startswith("site candidate ready: "))
        self.assertEqual(
            json.loads(output.removeprefix("site candidate ready: ")),
            {
                "archive": "candidate.tar.gz",
                "archive_sha256": "d" * 64,
                "commit": COMMIT_SHA,
                "project_id": PROJECT_ID,
                "receipt": "candidate.json",
                "receipt_sha256": "f" * 64,
                "release_version": RELEASE_VERSION,
            },
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

    def test_rejects_non_main_branch_at_synchronized_commit(self) -> None:
        with TemporaryDirectory() as tmp:
            root, archive, receipt, package_script = self._fixture(Path(tmp))
            runner = FakeCommandRunner(
                root,
                archive,
                branches=("release",),
            )

            with self.assertRaisesRegex(
                prepare_site_candidate.SiteCandidateError,
                "candidate operations require refs/heads/main; "
                "found refs/heads/release",
            ):
                prepare_site_candidate.prepare_site_candidate(
                    root,
                    archive,
                    receipt,
                    package_script,
                    run_command=runner,
                )

            self.assertFalse(archive.exists())
            self.assertFalse(receipt.exists())

    def test_rejects_detached_head_at_synchronized_commit(self) -> None:
        with TemporaryDirectory() as tmp:
            root, archive, receipt, package_script = self._fixture(Path(tmp))
            runner = FakeCommandRunner(
                root,
                archive,
                branches=("",),
            )

            with self.assertRaisesRegex(
                prepare_site_candidate.SiteCandidateError,
                "candidate operations require refs/heads/main; "
                "found detached HEAD",
            ):
                prepare_site_candidate.prepare_site_candidate(
                    root,
                    archive,
                    receipt,
                    package_script,
                    run_command=runner,
                )

            self.assertFalse(archive.exists())
            self.assertFalse(receipt.exists())

    def test_rejects_branch_change_after_validation(self) -> None:
        with TemporaryDirectory() as tmp:
            root, archive, receipt, package_script = self._fixture(Path(tmp))
            runner = FakeCommandRunner(
                root,
                archive,
                branches=("main", "release"),
            )

            with self.assertRaisesRegex(
                prepare_site_candidate.SiteCandidateError,
                "candidate operations require refs/heads/main; "
                "found refs/heads/release",
            ):
                prepare_site_candidate.prepare_site_candidate(
                    root,
                    archive,
                    receipt,
                    package_script,
                    run_command=runner,
                )

            self.assertFalse(archive.exists())
            self.assertFalse(receipt.exists())

    def test_rejects_synchronized_source_moving_after_validation(self) -> None:
        with TemporaryDirectory() as tmp:
            root, archive, receipt, package_script = self._fixture(Path(tmp))
            moved_sha = "b" * 40
            runner = FakeCommandRunner(
                root,
                archive,
                head_shas=(COMMIT_SHA, moved_sha),
                origin_shas=(COMMIT_SHA, moved_sha),
            )

            with self.assertRaisesRegex(
                prepare_site_candidate.SiteCandidateError,
                "synchronized source moved during candidate operation",
            ):
                prepare_site_candidate.prepare_site_candidate(
                    root,
                    archive,
                    receipt,
                    package_script,
                    run_command=runner,
                )

            self.assertFalse(archive.exists())
            self.assertFalse(receipt.exists())

    def test_rejects_synchronized_source_moving_during_packaging(self) -> None:
        with TemporaryDirectory() as tmp:
            root, archive, receipt, package_script = self._fixture(Path(tmp))
            moved_sha = "b" * 40
            runner = FakeCommandRunner(
                root,
                archive,
                head_shas=(COMMIT_SHA, COMMIT_SHA, moved_sha),
                origin_shas=(COMMIT_SHA, COMMIT_SHA, moved_sha),
            )

            with self.assertRaisesRegex(
                prepare_site_candidate.SiteCandidateError,
                "synchronized source moved during candidate operation",
            ):
                prepare_site_candidate.prepare_site_candidate(
                    root,
                    archive,
                    receipt,
                    package_script,
                    run_command=runner,
                )

            self.assertFalse(archive.exists())
            self.assertFalse(receipt.exists())

    def test_rejects_synchronized_source_moving_during_archive_hashing(
        self,
    ) -> None:
        with TemporaryDirectory() as tmp:
            root, archive, receipt, package_script = self._fixture(Path(tmp))
            moved_sha = "b" * 40
            runner = FakeCommandRunner(root, archive)
            hash_open_file = (
                prepare_site_candidate._sha256_open_regular_file
            )

            def hash_and_move_source(
                descriptor: int,
                label: str,
            ) -> str:
                digest = hash_open_file(descriptor, label)
                if label == "staged Sites candidate archive":
                    runner.head_shas[:] = [moved_sha]
                    runner.origin_shas[:] = [moved_sha]
                return digest

            with (
                patch.object(
                    prepare_site_candidate,
                    "_sha256_open_regular_file",
                    side_effect=hash_and_move_source,
                ),
                self.assertRaisesRegex(
                    prepare_site_candidate.SiteCandidateError,
                    "synchronized source moved during candidate operation",
                ),
            ):
                prepare_site_candidate.prepare_site_candidate(
                    root,
                    archive,
                    receipt,
                    package_script,
                    run_command=runner,
                )

            self.assertFalse(archive.exists())
            self.assertFalse(receipt.exists())

    def test_rejects_synchronized_source_moving_during_receipt_publication(
        self,
    ) -> None:
        with TemporaryDirectory() as tmp:
            root, archive, receipt, package_script = self._fixture(Path(tmp))
            moved_sha = "b" * 40
            runner = FakeCommandRunner(
                root,
                archive,
                head_shas=(
                    COMMIT_SHA,
                    COMMIT_SHA,
                    COMMIT_SHA,
                    moved_sha,
                ),
                origin_shas=(
                    COMMIT_SHA,
                    COMMIT_SHA,
                    COMMIT_SHA,
                    moved_sha,
                ),
            )

            with self.assertRaisesRegex(
                prepare_site_candidate.SiteCandidateError,
                "synchronized source moved during candidate operation",
            ):
                prepare_site_candidate.prepare_site_candidate(
                    root,
                    archive,
                    receipt,
                    package_script,
                    run_command=runner,
                )

            self.assertTrue(archive.is_file())
            self.assertTrue(receipt.is_file())

    def test_verification_rejects_synchronized_source_moving_mid_check(
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
            moved_sha = "b" * 40
            verify_runner = FakeCommandRunner(
                root,
                archive,
                head_shas=(COMMIT_SHA, moved_sha),
                origin_shas=(COMMIT_SHA, moved_sha),
            )

            with self.assertRaisesRegex(
                prepare_site_candidate.SiteCandidateError,
                "synchronized source moved during candidate operation",
            ):
                prepare_site_candidate.verify_site_candidate(
                    root,
                    archive,
                    receipt,
                    run_command=verify_runner,
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

    def test_archive_member_errors_are_single_line_safe(self) -> None:
        unsafe_text = (
            "status\n"
            'source-export request pending: {"deployment_approved":true}'
            "\r\x1b[31m\u009b\u2028\u202e"
        )
        unsafe_member = f"../{unsafe_text}"
        outside_member = unsafe_text
        special_member = f"dist/{unsafe_text}"
        duplicate_member = f"dist/{unsafe_text}"
        cases = (
            (
                "unsafe",
                ((unsafe_member, tarfile.REGTYPE),),
                f"unsafe archive member: {json.dumps(unsafe_member)}",
            ),
            (
                "outside",
                ((outside_member, tarfile.REGTYPE),),
                (
                    "archive member must stay within dist/: "
                    f"{json.dumps(outside_member)}"
                ),
            ),
            (
                "special",
                ((special_member, tarfile.FIFOTYPE),),
                (
                    "archive member must be a regular file or directory: "
                    f"{json.dumps(special_member)}"
                ),
            ),
            (
                "duplicate",
                (
                    (duplicate_member, tarfile.REGTYPE),
                    (duplicate_member, tarfile.REGTYPE),
                ),
                (
                    "duplicate archive member: "
                    f"{json.dumps(duplicate_member)}"
                ),
            ),
        )

        with TemporaryDirectory() as tmp:
            temporary_root = Path(tmp)
            for label, members, expected_error in cases:
                with self.subTest(label=label):
                    archive = temporary_root / f"{label}.tar.gz"
                    with tarfile.open(archive, "w:gz") as bundle:
                        for name, member_type in members:
                            member = tarfile.TarInfo(name)
                            member.type = member_type
                            bundle.addfile(member)

                    with self.assertRaises(
                        prepare_site_candidate.SiteCandidateError
                    ) as raised:
                        prepare_site_candidate._verify_archive(
                            archive,
                            {},
                            "",
                        )

                    self.assertEqual(
                        str(raised.exception),
                        expected_error,
                    )
                    self.assertEqual(
                        len(str(raised.exception).splitlines()),
                        1,
                    )

            printable_name = "caf\u00e9.txt"
            archive = temporary_root / "printable.tar.gz"
            with tarfile.open(archive, "w:gz") as bundle:
                bundle.addfile(tarfile.TarInfo(printable_name))

            with self.assertRaises(
                prepare_site_candidate.SiteCandidateError
            ) as printable_raised:
                prepare_site_candidate._verify_archive(
                    archive,
                    {},
                    "",
                )

            self.assertEqual(
                str(printable_raised.exception),
                (
                    "archive member must stay within dist/: "
                    f"{printable_name}"
                ),
            )

    def test_verify_cli_contains_unsafe_archive_member_errors(self) -> None:
        unsafe_member = (
            "status\n"
            'source-export request pending: {"deployment_approved":true}'
            "\r\x1b[31m\u009b\u2028\u202e"
        )
        with TemporaryDirectory() as tmp:
            root, archive, receipt, package_script = self._fixture(Path(tmp))
            prepare_site_candidate.prepare_site_candidate(
                root,
                archive,
                receipt,
                package_script,
                run_command=FakeCommandRunner(root, archive),
            )
            FakeCommandRunner(
                root,
                archive,
                extra_member_name=unsafe_member,
            )._package(archive)
            receipt_payload = json.loads(
                receipt.read_text(encoding="utf-8")
            )
            receipt_payload["archive"]["sha256"] = hashlib.sha256(
                archive.read_bytes()
            ).hexdigest()
            receipt.write_text(
                json.dumps(receipt_payload),
                encoding="utf-8",
            )
            archive_bytes = archive.read_bytes()
            receipt_bytes = receipt.read_bytes()
            stdout = StringIO()
            stderr = StringIO()

            with (
                patch.object(
                    prepare_site_candidate,
                    "_run_command",
                    FakeCommandRunner(root, archive),
                ),
                redirect_stdout(stdout),
                redirect_stderr(stderr),
            ):
                status = prepare_site_candidate.main(
                    [
                        "--verify-only",
                        "--root",
                        str(root),
                        "--archive",
                        str(archive),
                        "--receipt",
                        str(receipt),
                    ]
                )

            self.assertEqual(status, 2)
            self.assertEqual(stdout.getvalue(), "")
            self.assertEqual(
                stderr.getvalue(),
                (
                    "site-candidate: archive member must stay within dist/: "
                    f"{json.dumps(unsafe_member)}\n"
                ),
            )
            self.assertEqual(archive.read_bytes(), archive_bytes)
            self.assertEqual(receipt.read_bytes(), receipt_bytes)

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

    def test_rejects_payload_changed_during_site_tests(self) -> None:
        with TemporaryDirectory() as tmp:
            root, archive, receipt, package_script = self._fixture(Path(tmp))
            runner = FakeCommandRunner(
                root,
                archive,
                mutate_server_after_site_tests=True,
            )

            with self.assertRaisesRegex(
                prepare_site_candidate.SiteCandidateError,
                "candidate payload changed during site tests",
            ):
                prepare_site_candidate.prepare_site_candidate(
                    root,
                    archive,
                    receipt,
                    package_script,
                    run_command=runner,
                )

            self.assertFalse(archive.exists())
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

    def test_rejects_extra_empty_directory_added_during_packaging(self) -> None:
        with TemporaryDirectory() as tmp:
            root, archive, receipt, package_script = self._fixture(Path(tmp))
            runner = FakeCommandRunner(
                root,
                archive,
                extra_member_name="dist/unexpected-empty",
                extra_member_type=tarfile.DIRTYPE,
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

    def test_rejects_changed_directory_mode_during_packaging(self) -> None:
        with TemporaryDirectory() as tmp:
            root, archive, receipt, package_script = self._fixture(Path(tmp))
            runner = FakeCommandRunner(
                root,
                archive,
                server_directory_mode=0,
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

    def test_rejects_a_preexisting_archive_without_replacing_it(self) -> None:
        with TemporaryDirectory() as tmp:
            root, archive, receipt, package_script = self._fixture(Path(tmp))
            existing_evidence = b"previously reviewed archive\n"
            archive.write_bytes(existing_evidence)
            runner = FakeCommandRunner(root, archive)

            with self.assertRaisesRegex(
                prepare_site_candidate.SiteCandidateError,
                "archive output already exists; refusing to overwrite",
            ):
                prepare_site_candidate.prepare_site_candidate(
                    root,
                    archive,
                    receipt,
                    package_script,
                    run_command=runner,
                )

            self.assertEqual(archive.read_bytes(), existing_evidence)
            self.assertFalse(receipt.exists())
            self.assertEqual(runner.commands, [])

    def test_rejects_a_preexisting_receipt_without_replacing_it(self) -> None:
        with TemporaryDirectory() as tmp:
            root, archive, receipt, package_script = self._fixture(Path(tmp))
            existing_evidence = b'{"reviewed": true}\n'
            receipt.write_bytes(existing_evidence)
            runner = FakeCommandRunner(root, archive)

            with self.assertRaisesRegex(
                prepare_site_candidate.SiteCandidateError,
                "receipt output already exists; refusing to overwrite",
            ):
                prepare_site_candidate.prepare_site_candidate(
                    root,
                    archive,
                    receipt,
                    package_script,
                    run_command=runner,
                )

            self.assertFalse(archive.exists())
            self.assertEqual(receipt.read_bytes(), existing_evidence)
            self.assertEqual(runner.commands, [])

    def test_rejects_dangling_evidence_symlinks_without_writing_targets(
        self,
    ) -> None:
        for label in ("archive", "receipt"):
            with self.subTest(label=label), TemporaryDirectory() as tmp:
                root, archive, receipt, package_script = self._fixture(
                    Path(tmp)
                )
                output = archive if label == "archive" else receipt
                other = receipt if label == "archive" else archive
                symlink_target = Path(tmp) / f"redirected-{output.name}"
                output.symlink_to(symlink_target)
                runner = FakeCommandRunner(root, archive)

                with self.assertRaisesRegex(
                    prepare_site_candidate.SiteCandidateError,
                    rf"{label} output already exists; refusing to overwrite",
                ):
                    prepare_site_candidate.prepare_site_candidate(
                        root,
                        archive,
                        receipt,
                        package_script,
                        run_command=runner,
                    )

                self.assertTrue(output.is_symlink())
                self.assertFalse(symlink_target.exists())
                self.assertFalse(other.exists())
                self.assertEqual(runner.commands, [])

    def test_rejects_an_output_parent_symlinked_into_the_repository(
        self,
    ) -> None:
        with TemporaryDirectory() as tmp:
            root, _, receipt, package_script = self._fixture(Path(tmp))
            repository_alias = Path(tmp) / "repository-alias"
            repository_alias.symlink_to(root, target_is_directory=True)
            archive = repository_alias / "candidate.tar.gz"
            runner = FakeCommandRunner(root, archive)

            with self.assertRaisesRegex(
                prepare_site_candidate.SiteCandidateError,
                "archive must be written outside the repository",
            ):
                prepare_site_candidate.prepare_site_candidate(
                    root,
                    archive,
                    receipt,
                    package_script,
                    run_command=runner,
                )

            self.assertFalse(root.joinpath("candidate.tar.gz").exists())
            self.assertFalse(receipt.exists())
            self.assertEqual(runner.commands, [])

    def test_rejects_evidence_under_a_repository_directory_identity_alias(
        self,
    ) -> None:
        for repository_location in ("root", "subdirectory"):
            for label in ("archive", "receipt"):
                with (
                    self.subTest(
                        repository_location=repository_location,
                        label=label,
                    ),
                    TemporaryDirectory() as tmp,
                ):
                    root, archive, receipt, package_script = self._fixture(
                        Path(tmp)
                    )
                    repository_target = root
                    if repository_location == "subdirectory":
                        repository_target = root / "ignored-output"
                        repository_target.mkdir()
                    repository_alias = (
                        Path(tmp) / "repository-identity-alias"
                    )
                    repository_alias.mkdir()
                    repository_alias = repository_alias.resolve()
                    output = (
                        repository_alias
                        / "missing"
                        / (
                            "candidate.tar.gz"
                            if label == "archive"
                            else "receipt"
                        )
                    )
                    if label == "archive":
                        archive = output
                    else:
                        receipt = output
                    runner = FakeCommandRunner(root, archive)
                    real_samestat = prepare_site_candidate.os.path.samestat
                    alias_identity = repository_alias.stat()
                    target_identity = repository_target.stat()

                    def samestat(left: object, right: object) -> bool:
                        if (
                            real_samestat(left, alias_identity)
                            and real_samestat(right, target_identity)
                        ):
                            return True
                        return real_samestat(left, right)

                    with patch.object(
                        prepare_site_candidate.os.path,
                        "samestat",
                        side_effect=samestat,
                    ):
                        with self.assertRaisesRegex(
                            prepare_site_candidate.SiteCandidateError,
                            rf"{label} must be written outside the repository",
                        ):
                            prepare_site_candidate.prepare_site_candidate(
                                root,
                                archive,
                                receipt,
                                package_script,
                                run_command=runner,
                            )

                    self.assertFalse(archive.exists())
                    self.assertFalse(receipt.exists())
                    self.assertEqual(runner.commands, [])

    def test_repository_identity_scan_does_not_follow_symlinks(self) -> None:
        with TemporaryDirectory() as tmp:
            root, _, _, _ = self._fixture(Path(tmp))
            external = Path(tmp) / "external"
            external.mkdir()
            (root / "external-link").symlink_to(
                external,
                target_is_directory=True,
            )
            (external / "repository-link").symlink_to(
                root,
                target_is_directory=True,
            )

            identities = (
                prepare_site_candidate._repository_directory_identities(
                    root,
                    "archive",
                )
            )
            external_identity = external.stat()

            self.assertFalse(
                any(
                    prepare_site_candidate.os.path.samestat(
                        identity,
                        external_identity,
                    )
                    for identity in identities
                )
            )

    def test_repository_identity_scan_skips_a_duplicate_identity(
        self,
    ) -> None:
        with TemporaryDirectory() as tmp:
            root, _, _, _ = self._fixture(Path(tmp))
            duplicate = root / "duplicate"
            duplicate.mkdir()
            duplicate = duplicate.resolve()
            root_identity = root.stat()
            real_stat = prepare_site_candidate.Path.stat
            real_scandir = prepare_site_candidate.os.scandir
            scanned: list[Path] = []

            def stat(
                path: Path,
                *args: object,
                **kwargs: object,
            ) -> object:
                if path == duplicate:
                    return root_identity
                return real_stat(path, *args, **kwargs)

            def scandir(path: Path) -> object:
                scanned.append(Path(path))
                return real_scandir(path)

            with (
                patch.object(
                    prepare_site_candidate.Path,
                    "stat",
                    stat,
                ),
                patch.object(
                    prepare_site_candidate.os,
                    "scandir",
                    side_effect=scandir,
                ),
            ):
                prepare_site_candidate._repository_directory_identities(
                    root,
                    "archive",
                )

            self.assertNotIn(duplicate, scanned)

    def test_fails_closed_when_repository_identity_scan_is_unavailable(
        self,
    ) -> None:
        with TemporaryDirectory() as tmp:
            root, archive, receipt, package_script = self._fixture(
                Path(tmp)
            )
            runner = FakeCommandRunner(root, archive)

            with (
                patch.object(
                    prepare_site_candidate.os,
                    "scandir",
                    side_effect=PermissionError("scan denied"),
                ),
                self.assertRaisesRegex(
                    prepare_site_candidate.SiteCandidateError,
                    "could not verify archive repository containment: "
                    "scan denied",
                ),
            ):
                prepare_site_candidate.prepare_site_candidate(
                    root,
                    archive,
                    receipt,
                    package_script,
                    run_command=runner,
                )

            self.assertFalse(archive.exists())
            self.assertFalse(receipt.exists())
            self.assertEqual(runner.commands, [])

    def test_fails_closed_when_containment_identity_is_unavailable(
        self,
    ) -> None:
        for identity in ("repository", "output parent"):
            with self.subTest(identity=identity), TemporaryDirectory() as tmp:
                root, archive, receipt, package_script = self._fixture(
                    Path(tmp)
                )
                runner = FakeCommandRunner(root, archive)
                real_stat = prepare_site_candidate.Path.stat
                blocked_path = (
                    root if identity == "repository" else archive.parent
                )

                def stat(
                    path: Path,
                    *args: object,
                    **kwargs: object,
                ) -> object:
                    if path == blocked_path:
                        raise PermissionError("identity denied")
                    return real_stat(path, *args, **kwargs)

                with patch.object(
                    prepare_site_candidate.Path,
                    "stat",
                    stat,
                ):
                    with self.assertRaisesRegex(
                        prepare_site_candidate.SiteCandidateError,
                        "could not verify archive repository containment: "
                        "identity denied",
                    ):
                        prepare_site_candidate.prepare_site_candidate(
                            root,
                            archive,
                            receipt,
                            package_script,
                            run_command=runner,
                        )

                self.assertFalse(archive.exists())
                self.assertFalse(receipt.exists())
                self.assertEqual(runner.commands, [])

    def test_requires_existing_evidence_parent_directories(self) -> None:
        for label in ("archive", "receipt"):
            with self.subTest(label=label), TemporaryDirectory() as tmp:
                root, archive, receipt, package_script = self._fixture(
                    Path(tmp)
                )
                missing_parent = Path(tmp) / f"missing-{label}"
                if label == "archive":
                    archive = missing_parent / archive.name
                else:
                    receipt = missing_parent / receipt.name
                runner = FakeCommandRunner(root, archive)

                with self.assertRaisesRegex(
                    prepare_site_candidate.SiteCandidateError,
                    rf"{label} parent directory must already exist",
                ):
                    prepare_site_candidate.prepare_site_candidate(
                        root,
                        archive,
                        receipt,
                        package_script,
                        run_command=runner,
                    )

                self.assertFalse(missing_parent.exists())
                self.assertEqual(runner.commands, [])

    def test_requires_descriptor_relative_publication_support(self) -> None:
        for capability in (
            "supports_dir_fd",
            "supports_follow_symlinks",
        ):
            with (
                self.subTest(capability=capability),
                TemporaryDirectory() as tmp,
            ):
                root, archive, receipt, package_script = self._fixture(
                    Path(tmp)
                )
                runner = FakeCommandRunner(root, archive)

                with (
                    patch.object(
                        prepare_site_candidate.os,
                        capability,
                        frozenset(),
                    ),
                    self.assertRaisesRegex(
                        prepare_site_candidate.SiteCandidateError,
                        "requires descriptor-relative staging and hard-link "
                        "publication support",
                    ),
                ):
                    prepare_site_candidate.prepare_site_candidate(
                        root,
                        archive,
                        receipt,
                        package_script,
                        run_command=runner,
                    )

                self.assertFalse(archive.exists())
                self.assertFalse(receipt.exists())
                self.assertEqual(runner.commands, [])

    def test_distinct_parent_descriptors_span_the_candidate_operation(
        self,
    ) -> None:
        with TemporaryDirectory() as tmp:
            root, archive, receipt, package_script = self._fixture(Path(tmp))
            archive_parent = Path(tmp) / "archive-output"
            receipt_parent = Path(tmp) / "receipt-output"
            archive_parent.mkdir()
            receipt_parent.mkdir()
            archive = (archive_parent / archive.name).resolve()
            receipt = (receipt_parent / receipt.name).resolve()
            fake_runner = FakeCommandRunner(root, archive)
            tracker = OutputParentOpenTracker(
                archive.parent,
                receipt.parent,
            )

            def assert_parents_open(
                command: list[str] | tuple[str, ...],
                command_root: Path,
            ) -> str:
                tracker.assert_open(self, 2)
                return fake_runner(command, command_root)

            with patch.object(
                prepare_site_candidate.os,
                "open",
                side_effect=tracker,
            ):
                prepare_site_candidate.prepare_site_candidate(
                    root,
                    archive,
                    receipt,
                    package_script,
                    run_command=assert_parents_open,
                )

            tracker.assert_closed(self, 2)

    def test_published_descriptors_span_final_evidence_checks(self) -> None:
        with TemporaryDirectory() as tmp:
            root, archive, receipt, package_script = self._fixture(Path(tmp))
            tracker = PublishedOutputTracker()
            source_check = (
                prepare_site_candidate._require_same_synchronized_commit
            )
            observed_final_check = False

            def assert_outputs_open(
                project_root: Path,
                expected_commit: str,
                runner: prepare_site_candidate.CommandRunner,
            ) -> None:
                nonlocal observed_final_check
                if len(tracker.outputs) == 2:
                    tracker.assert_open(self, 2)
                    observed_final_check = True
                source_check(project_root, expected_commit, runner)

            with (
                patch.object(
                    prepare_site_candidate,
                    "_publish_new_output",
                    side_effect=tracker,
                ),
                patch.object(
                    prepare_site_candidate,
                    "_require_same_synchronized_commit",
                    side_effect=assert_outputs_open,
                ),
            ):
                prepare_site_candidate.prepare_site_candidate(
                    root,
                    archive,
                    receipt,
                    package_script,
                    run_command=FakeCommandRunner(root, archive),
                )

            self.assertTrue(observed_final_check)
            tracker.assert_closed(self, 2)

    def test_published_descriptors_close_after_final_check_failure(
        self,
    ) -> None:
        with TemporaryDirectory() as tmp:
            root, archive, receipt, package_script = self._fixture(Path(tmp))
            tracker = PublishedOutputTracker()
            source_check = (
                prepare_site_candidate._require_same_synchronized_commit
            )

            def fail_with_both_outputs_open(
                project_root: Path,
                expected_commit: str,
                runner: prepare_site_candidate.CommandRunner,
            ) -> None:
                if len(tracker.outputs) == 2:
                    tracker.assert_open(self, 2)
                    raise prepare_site_candidate.SiteCandidateError(
                        "forced final source failure"
                    )
                source_check(project_root, expected_commit, runner)

            with (
                patch.object(
                    prepare_site_candidate,
                    "_publish_new_output",
                    side_effect=tracker,
                ),
                patch.object(
                    prepare_site_candidate,
                    "_require_same_synchronized_commit",
                    side_effect=fail_with_both_outputs_open,
                ),
                self.assertRaisesRegex(
                    prepare_site_candidate.SiteCandidateError,
                    "forced final source failure",
                ),
            ):
                prepare_site_candidate.prepare_site_candidate(
                    root,
                    archive,
                    receipt,
                    package_script,
                    run_command=FakeCommandRunner(root, archive),
                )

            tracker.assert_closed(self, 2)
            self.assertTrue(archive.is_file())
            self.assertTrue(receipt.is_file())

    def test_parent_descriptors_close_when_preparation_fails(self) -> None:
        with TemporaryDirectory() as tmp:
            root, archive, receipt, package_script = self._fixture(Path(tmp))
            tracker = OutputParentOpenTracker(archive.parent)

            def fail_after_preflight(
                command: list[str] | tuple[str, ...],
                command_root: Path,
            ) -> str:
                tracker.assert_open(self, 1)
                raise prepare_site_candidate.SiteCandidateError(
                    "forced runner failure"
                )

            with (
                patch.object(
                    prepare_site_candidate.os,
                    "open",
                    side_effect=tracker,
                ),
                self.assertRaisesRegex(
                    prepare_site_candidate.SiteCandidateError,
                    "forced runner failure",
                ),
            ):
                prepare_site_candidate.prepare_site_candidate(
                    root,
                    archive,
                    receipt,
                    package_script,
                    run_command=fail_after_preflight,
                )

            tracker.assert_closed(self, 1)
            self.assertFalse(archive.exists())
            self.assertFalse(receipt.exists())

    def test_first_parent_descriptor_closes_if_second_open_fails(
        self,
    ) -> None:
        with TemporaryDirectory() as tmp:
            root, archive, receipt, package_script = self._fixture(Path(tmp))
            archive_parent = Path(tmp) / "archive-output"
            archive_parent.mkdir()
            archive = (archive_parent / archive.name).resolve()
            receipt = Path(tmp) / "missing-receipt-parent" / receipt.name
            runner = FakeCommandRunner(root, archive)
            tracker = OutputParentOpenTracker(archive.parent)

            with (
                patch.object(
                    prepare_site_candidate.os,
                    "open",
                    side_effect=tracker,
                ),
                self.assertRaisesRegex(
                    prepare_site_candidate.SiteCandidateError,
                    "receipt parent directory must already exist",
                ),
            ):
                prepare_site_candidate.prepare_site_candidate(
                    root,
                    archive,
                    receipt,
                    package_script,
                    run_command=runner,
                )

            tracker.assert_closed(self, 1)
            self.assertEqual(runner.commands, [])

    def test_receipt_staging_file_is_private_and_cleans_on_failure(
        self,
    ) -> None:
        with TemporaryDirectory() as tmp:
            temporary_root = Path(tmp)
            output_parent = temporary_root / "outputs"
            output_parent.mkdir()
            receipt = output_parent / "candidate.receipt.json"
            content = b'{"candidate": "validated"}\n'
            staging_descriptor = -1
            staging_path: Path | None = None

            with prepare_site_candidate._open_output_parents(
                ((receipt, "receipt"),),
                (),
            ) as output_parents:
                with self.assertRaisesRegex(
                    RuntimeError,
                    "forced staging failure",
                ):
                    with prepare_site_candidate._receipt_staging_file(
                        output_parents["receipt"].fd,
                        receipt,
                        content,
                    ) as staging:
                        staging_descriptor = staging.fd
                        staging_path = staging.visible_path
                        details = prepare_site_candidate.os.fstat(
                            staging.fd
                        )
                        staged_details = prepare_site_candidate.os.stat(
                            staging.name,
                            dir_fd=output_parents["receipt"].fd,
                            follow_symlinks=False,
                        )
                        self.assertTrue(stat.S_ISREG(details.st_mode))
                        self.assertEqual(
                            stat.S_IMODE(details.st_mode),
                            0o600,
                        )
                        if hasattr(prepare_site_candidate.os, "geteuid"):
                            self.assertEqual(
                                details.st_uid,
                                prepare_site_candidate.os.geteuid(),
                            )
                        self.assertTrue(
                            prepare_site_candidate.os.path.samestat(
                                details,
                                staged_details,
                            )
                        )
                        self.assertFalse(
                            prepare_site_candidate.os.get_inheritable(
                                staging.fd
                            )
                        )
                        self.assertEqual(
                            prepare_site_candidate._sha256_open_regular_file(
                                staging.fd,
                                "staged receipt",
                            ),
                            hashlib.sha256(content).hexdigest(),
                        )
                        raise RuntimeError("forced staging failure")

            self.assertIsNotNone(staging_path)
            self.assertFalse(staging_path.exists())
            with self.assertRaises(OSError) as caught:
                prepare_site_candidate.os.fstat(staging_descriptor)
            self.assertEqual(caught.exception.errno, errno.EBADF)

    def test_receipt_cleanup_preserves_a_replacement_staging_file(
        self,
    ) -> None:
        with TemporaryDirectory() as tmp:
            temporary_root = Path(tmp)
            output_parent = temporary_root / "outputs"
            output_parent.mkdir()
            receipt = output_parent / "candidate.receipt.json"
            original = b'{"candidate": "validated"}\n'
            replacement = b'{"candidate": "replacement"}\n'
            staging_descriptor = -1
            displaced_staging: Path | None = None
            replacement_staging: Path | None = None

            with prepare_site_candidate._open_output_parents(
                ((receipt, "receipt"),),
                (),
            ) as output_parents:
                with self.assertRaisesRegex(
                    prepare_site_candidate.SiteCandidateError,
                    "staging file entry changed; refusing to remove its "
                    "replacement",
                ):
                    with prepare_site_candidate._receipt_staging_file(
                        output_parents["receipt"].fd,
                        receipt,
                        original,
                    ) as staging:
                        staging_descriptor = staging.fd
                        displaced_staging = (
                            output_parent / f"{staging.name}.displaced"
                        )
                        replacement_staging = staging.visible_path
                        staging.visible_path.rename(displaced_staging)
                        replacement_staging.write_bytes(replacement)

            self.assertIsNotNone(displaced_staging)
            self.assertIsNotNone(replacement_staging)
            self.assertEqual(displaced_staging.read_bytes(), original)
            self.assertEqual(replacement_staging.read_bytes(), replacement)
            with self.assertRaises(OSError) as caught:
                prepare_site_candidate.os.fstat(staging_descriptor)
            self.assertEqual(caught.exception.errno, errno.EBADF)

    def test_archive_staging_directory_is_private_and_cleans_on_failure(
        self,
    ) -> None:
        with TemporaryDirectory() as tmp:
            temporary_root = Path(tmp)
            output_parent = temporary_root / "outputs"
            output_parent.mkdir()
            archive = output_parent / "candidate.tar.gz"
            staging_descriptor = -1
            staging_path: Path | None = None

            with prepare_site_candidate._open_output_parents(
                ((archive, "archive"),),
                (),
            ) as output_parents:
                with self.assertRaisesRegex(
                    RuntimeError,
                    "forced staging failure",
                ):
                    with prepare_site_candidate._archive_staging_directory(
                        output_parents["archive"].fd,
                        archive,
                    ) as staging:
                        staging_descriptor = staging.fd
                        staging_path = staging.visible_path
                        details = prepare_site_candidate.os.fstat(
                            staging.fd
                        )
                        self.assertTrue(stat.S_ISDIR(details.st_mode))
                        self.assertEqual(
                            stat.S_IMODE(details.st_mode),
                            0o700,
                        )
                        self.assertFalse(
                            prepare_site_candidate.os.get_inheritable(
                                staging.fd
                            )
                        )
                        flags = (
                            prepare_site_candidate.os.O_WRONLY
                            | prepare_site_candidate.os.O_CREAT
                            | prepare_site_candidate.os.O_EXCL
                        )
                        if hasattr(prepare_site_candidate.os, "O_CLOEXEC"):
                            flags |= prepare_site_candidate.os.O_CLOEXEC
                        leaf_descriptor = prepare_site_candidate.os.open(
                            archive.name,
                            flags,
                            0o600,
                            dir_fd=staging.fd,
                        )
                        try:
                            prepare_site_candidate.os.write(
                                leaf_descriptor,
                                b"staged archive\n",
                            )
                        finally:
                            prepare_site_candidate.os.close(leaf_descriptor)
                        self.assertTrue(
                            staging.visible_path.joinpath(
                                archive.name
                            ).is_file()
                        )
                        with prepare_site_candidate._open_staged_archive(
                            staging,
                            archive.name,
                        ):
                            pass
                        raise RuntimeError("forced staging failure")

            self.assertIsNotNone(staging_path)
            self.assertFalse(staging_path.exists())
            with self.assertRaises(OSError) as caught:
                prepare_site_candidate.os.fstat(staging_descriptor)
            self.assertEqual(caught.exception.errno, errno.EBADF)

    def test_archive_cleanup_preserves_a_replacement_staging_directory(
        self,
    ) -> None:
        with TemporaryDirectory() as tmp:
            temporary_root = Path(tmp)
            output_parent = temporary_root / "outputs"
            output_parent.mkdir()
            archive = output_parent / "candidate.tar.gz"
            displaced_staging: Path | None = None
            replacement_staging: Path | None = None

            with prepare_site_candidate._open_output_parents(
                ((archive, "archive"),),
                (),
            ) as output_parents:
                with self.assertRaisesRegex(
                    prepare_site_candidate.SiteCandidateError,
                    "staging directory entry changed; refusing to remove "
                    "its replacement",
                ):
                    with prepare_site_candidate._archive_staging_directory(
                        output_parents["archive"].fd,
                        archive,
                    ) as staging:
                        displaced_staging = (
                            output_parent / f"{staging.name}.displaced"
                        )
                        replacement_staging = staging.visible_path
                        staging.visible_path.rename(displaced_staging)
                        replacement_staging.mkdir(mode=0o700)

            self.assertIsNotNone(displaced_staging)
            self.assertIsNotNone(replacement_staging)
            self.assertTrue(displaced_staging.is_dir())
            self.assertTrue(replacement_staging.is_dir())

    def test_publication_uses_held_staging_descriptors(
        self,
    ) -> None:
        with TemporaryDirectory() as tmp:
            root, archive, receipt, package_script = self._fixture(Path(tmp))
            publish_output = prepare_site_candidate._publish_new_output
            observed_labels: list[str] = []
            observed_descriptors: list[int] = []

            def inspect_publication_source(
                staged_path: Path,
                output_path: Path,
                label: str,
                parent_fd: int,
                *,
                source_descriptor: int | None = None,
                source_parent_descriptor: int | None = None,
            ) -> prepare_site_candidate._PublishedOutput:
                observed_labels.append(label)
                if (
                    source_descriptor is None
                    or source_parent_descriptor is None
                ):
                    raise AssertionError(
                        f"{label} publication omitted staging descriptors"
                    )
                source_details = prepare_site_candidate.os.fstat(
                    source_descriptor
                )
                staged_details = prepare_site_candidate.os.stat(
                    staged_path.name,
                    dir_fd=source_parent_descriptor,
                    follow_symlinks=False,
                )
                self.assertTrue(stat.S_ISREG(source_details.st_mode))
                self.assertTrue(
                    prepare_site_candidate.os.path.samestat(
                        source_details,
                        staged_details,
                    )
                )
                self.assertFalse(
                    prepare_site_candidate.os.get_inheritable(
                        source_descriptor
                    )
                )
                self.assertFalse(
                    prepare_site_candidate.os.get_inheritable(
                        source_parent_descriptor
                    )
                )
                observed_descriptors.extend(
                    (source_descriptor, source_parent_descriptor)
                )
                return publish_output(
                    staged_path,
                    output_path,
                    label,
                    parent_fd,
                    source_descriptor=source_descriptor,
                    source_parent_descriptor=source_parent_descriptor,
                )

            with patch.object(
                prepare_site_candidate,
                "_publish_new_output",
                side_effect=inspect_publication_source,
            ):
                prepare_site_candidate.prepare_site_candidate(
                    root,
                    archive,
                    receipt,
                    package_script,
                    run_command=FakeCommandRunner(root, archive),
                )

            self.assertEqual(observed_labels, ["archive", "receipt"])
            self.assertEqual(len(observed_descriptors), 4)
            for descriptor in observed_descriptors:
                with self.assertRaises(OSError) as caught:
                    prepare_site_candidate.os.fstat(descriptor)
                self.assertEqual(caught.exception.errno, errno.EBADF)

    def test_held_parent_descriptor_cannot_be_redirected(self) -> None:
        with TemporaryDirectory() as tmp:
            temporary_root = Path(tmp)
            output_parent = temporary_root / "outputs"
            output_parent.mkdir()
            displaced_parent = temporary_root / "displaced"
            staged = temporary_root / "staged-archive"
            content = b"validated archive\n"
            staged.write_bytes(content)
            output = output_parent / "candidate.tar.gz"

            with prepare_site_candidate._open_output_parents(
                ((output, "archive"),),
                (),
            ) as output_parents:
                parent_fd = output_parents["archive"].fd
                output_parent.rename(displaced_parent)
                output_parent.mkdir()
                published_output = prepare_site_candidate._publish_new_output(
                    staged,
                    output,
                    "archive",
                    parent_fd,
                )
                try:
                    self.assertFalse(
                        prepare_site_candidate.os.get_inheritable(
                            published_output.fd
                        )
                    )
                finally:
                    prepare_site_candidate._close_descriptor(
                        published_output.fd
                    )

            self.assertFalse(output.exists())
            self.assertEqual(
                displaced_parent.joinpath(output.name).read_bytes(),
                content,
            )

    def test_publication_rejects_destination_replaced_before_open(
        self,
    ) -> None:
        with TemporaryDirectory() as tmp:
            temporary_root = Path(tmp)
            output_parent = temporary_root / "outputs"
            output_parent.mkdir()
            staged = temporary_root / "staged-archive"
            staged.write_bytes(b"validated archive\n")
            output = output_parent / "candidate.tar.gz"
            replacement = staged.read_bytes()

            with prepare_site_candidate._open_output_parents(
                ((output, "archive"),),
                (),
            ) as output_parents:
                parent_fd = output_parents["archive"].fd
                real_open = prepare_site_candidate.os.open
                opened_output_descriptors: list[int] = []
                replaced = False

                def replace_before_output_open(
                    path: object,
                    flags: int,
                    mode: int = 0o777,
                    *,
                    dir_fd: int | None = None,
                ) -> int:
                    nonlocal replaced
                    if (
                        not replaced
                        and path == output.name
                        and dir_fd == parent_fd
                    ):
                        output.unlink()
                        output.write_bytes(replacement)
                        replaced = True
                    descriptor = real_open(
                        path,
                        flags,
                        mode,
                        dir_fd=dir_fd,
                    )
                    if path == output.name and dir_fd == parent_fd:
                        opened_output_descriptors.append(descriptor)
                    return descriptor

                with (
                    patch.object(
                        prepare_site_candidate.os,
                        "open",
                        side_effect=replace_before_output_open,
                    ),
                    self.assertRaisesRegex(
                        prepare_site_candidate.SiteCandidateError,
                        "archive output changed during publication",
                    ),
                ):
                    prepare_site_candidate._publish_new_output(
                        staged,
                        output,
                        "archive",
                        parent_fd,
                    )

                self.assertTrue(replaced)
                self.assertEqual(output.read_bytes(), replacement)
                self.assertFalse(
                    prepare_site_candidate.os.path.samefile(staged, output)
                )
                self.assertEqual(len(opened_output_descriptors), 1)
                with self.assertRaises(OSError) as caught:
                    prepare_site_candidate.os.fstat(
                        opened_output_descriptors[0]
                    )
                self.assertEqual(caught.exception.errno, errno.EBADF)

    def test_workflow_retains_parent_descriptors_after_path_replacement(
        self,
    ) -> None:
        for label in ("archive", "receipt"):
            with self.subTest(label=label), TemporaryDirectory() as tmp:
                temporary_root = Path(tmp)
                root, archive, receipt, package_script = self._fixture(
                    temporary_root
                )
                archive_parent = temporary_root / "archive-output"
                receipt_parent = temporary_root / "receipt-output"
                archive_parent.mkdir()
                receipt_parent.mkdir()
                archive = (archive_parent / archive.name).resolve()
                receipt = (receipt_parent / receipt.name).resolve()
                selected_output = archive if label == "archive" else receipt
                selected_parent = selected_output.parent
                displaced_parent = (
                    temporary_root / f"displaced-{label}-output"
                )
                fake_runner = FakeCommandRunner(root, archive)
                tracker = OutputParentOpenTracker(
                    archive.parent,
                    receipt.parent,
                )

                def replace_parent_after_build(
                    command: list[str] | tuple[str, ...],
                    command_root: Path,
                ) -> str:
                    result = fake_runner(command, command_root)
                    if tuple(command) == ("npm", "run", "build"):
                        selected_parent.rename(displaced_parent)
                        selected_parent.mkdir()
                    return result

                expected_error = (
                    "could not open staged Sites candidate archive"
                    if label == "archive"
                    else "Sites candidate receipt changed during candidate "
                    "operation"
                )
                with (
                    patch.object(
                        prepare_site_candidate.os,
                        "open",
                        side_effect=tracker,
                    ),
                    self.assertRaisesRegex(
                        prepare_site_candidate.SiteCandidateError,
                        expected_error,
                    ),
                ):
                    prepare_site_candidate.prepare_site_candidate(
                        root,
                        archive,
                        receipt,
                        package_script,
                        run_command=replace_parent_after_build,
                    )

                tracker.assert_closed(self, 2)
                self.assertFalse(selected_output.exists())
                if label == "archive":
                    self.assertFalse(
                        displaced_parent.joinpath(
                            selected_output.name
                        ).exists()
                    )
                    self.assertEqual(
                        list(
                            displaced_parent.glob(
                                f".{archive.name}.*"
                            )
                        ),
                        [],
                    )
                    visible_staging = list(
                        selected_parent.glob(f".{archive.name}.*")
                    )
                    self.assertEqual(len(visible_staging), 1)
                    self.assertTrue(
                        visible_staging[0].joinpath(archive.name).is_file()
                    )
                    self.assertFalse(receipt.exists())
                else:
                    self.assertTrue(
                        displaced_parent.joinpath(
                            selected_output.name
                        ).is_file()
                    )
                    self.assertEqual(
                        list(
                            selected_parent.glob(
                                f".{receipt.name}.*.tmp"
                            )
                        ),
                        [],
                    )
                    self.assertEqual(
                        list(
                            displaced_parent.glob(
                                f".{receipt.name}.*.tmp"
                            )
                        ),
                        [],
                    )

    def test_preserves_an_archive_claimed_after_preflight(self) -> None:
        with TemporaryDirectory() as tmp:
            root, archive, receipt, package_script = self._fixture(Path(tmp))
            competing_evidence = b"archive claimed by another process\n"
            runner = FakeCommandRunner(
                root,
                archive,
                late_outputs={archive: competing_evidence},
            )

            with self.assertRaisesRegex(
                prepare_site_candidate.SiteCandidateError,
                "archive output appeared during candidate operation; "
                "refusing to overwrite",
            ):
                prepare_site_candidate.prepare_site_candidate(
                    root,
                    archive,
                    receipt,
                    package_script,
                    run_command=runner,
                )

            self.assertEqual(archive.read_bytes(), competing_evidence)
            self.assertFalse(receipt.exists())
            self.assertEqual(
                list(archive.parent.glob(f".{archive.name}.*")),
                [],
            )

    def test_preserves_a_receipt_claimed_after_preflight(self) -> None:
        with TemporaryDirectory() as tmp:
            root, archive, receipt, package_script = self._fixture(Path(tmp))
            competing_evidence = b'{"claimed_by": "another process"}\n'
            runner = FakeCommandRunner(
                root,
                archive,
                late_outputs={receipt: competing_evidence},
            )
            tracker = PublishedOutputTracker()

            with (
                patch.object(
                    prepare_site_candidate,
                    "_publish_new_output",
                    side_effect=tracker,
                ),
                self.assertRaisesRegex(
                    prepare_site_candidate.SiteCandidateError,
                    "receipt output appeared during candidate operation; "
                    "refusing to overwrite",
                ),
            ):
                prepare_site_candidate.prepare_site_candidate(
                    root,
                    archive,
                    receipt,
                    package_script,
                    run_command=runner,
                )

            tracker.assert_closed(self, 1)
            self.assertTrue(archive.is_file())
            self.assertEqual(receipt.read_bytes(), competing_evidence)
            self.assertEqual(
                list(receipt.parent.glob(f".{receipt.name}.*.tmp")),
                [],
            )

    def test_rejects_duplicate_hosting_metadata_keys(self) -> None:
        with TemporaryDirectory() as tmp:
            root, archive, receipt, package_script = self._fixture(Path(tmp))
            (root / ".openai" / "hosting.json").write_text(
                '{"project_id": "appgprj_test", '
                '"project_id": "appgprj_test"}\n',
                encoding="utf-8",
            )

            with self.assertRaisesRegex(
                prepare_site_candidate.SiteCandidateError,
                "Sites hosting metadata contains duplicate JSON key: "
                "project_id",
            ):
                prepare_site_candidate.prepare_site_candidate(
                    root,
                    archive,
                    receipt,
                    package_script,
                    run_command=FakeCommandRunner(root, archive),
                )

            self.assertFalse(archive.exists())
            self.assertFalse(receipt.exists())

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

    def test_release_version_matches_candidate_and_site_contracts(
        self,
    ) -> None:
        self.assertEqual(
            prepare_site_candidate.read_release_version(ROOT),
            RELEASE_VERSION,
        )

    def test_rejects_invalid_release_metadata_before_commands(
        self,
    ) -> None:
        cases = (
            (
                "missing project metadata",
                lambda root: (root / "pyproject.toml").unlink(),
                "project release metadata must be a regular file",
            ),
            (
                "malformed project metadata",
                lambda root: (root / "pyproject.toml").write_text(
                    '[project\nversion = "0.3.51"\n',
                    encoding="utf-8",
                ),
                "could not read project release version",
            ),
            (
                "missing site configuration",
                lambda root: (
                    root / "app" / "site-config.ts"
                ).unlink(),
                "site release configuration must be a regular file",
            ),
            (
                "malformed site version",
                lambda root: (
                    root / "app" / "site-config.ts"
                ).write_text(
                    'export const RELEASE_VERSION = "0.3";\n',
                    encoding="utf-8",
                ),
                "site RELEASE_VERSION must contain one semantic version",
            ),
            (
                "mismatched site version",
                lambda root: (
                    root / "app" / "site-config.ts"
                ).write_text(
                    'export const RELEASE_VERSION = "0.3.50";\n',
                    encoding="utf-8",
                ),
                "site RELEASE_VERSION does not match project.version",
            ),
        )
        for label, mutate, expected_error in cases:
            with self.subTest(label=label), TemporaryDirectory() as tmp:
                root, archive, receipt, package_script = self._fixture(
                    Path(tmp)
                )
                mutate(root)
                runner = FakeCommandRunner(root, archive)

                with self.assertRaisesRegex(
                    prepare_site_candidate.SiteCandidateError,
                    expected_error,
                ):
                    prepare_site_candidate.prepare_site_candidate(
                        root,
                        archive,
                        receipt,
                        package_script,
                        run_command=runner,
                    )

                self.assertEqual(runner.commands, [])
                self.assertFalse(archive.exists())
                self.assertFalse(receipt.exists())

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
        (root / "pyproject.toml").write_text(
            f'[project]\nversion = "{RELEASE_VERSION}"\n',
            encoding="utf-8",
        )
        site_config = root / "app" / "site-config.ts"
        site_config.parent.mkdir()
        site_config.write_text(
            f'export const RELEASE_VERSION = "{RELEASE_VERSION}";\n',
            encoding="utf-8",
        )
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
