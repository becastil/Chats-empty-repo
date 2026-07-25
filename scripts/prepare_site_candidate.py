#!/usr/bin/env python3
from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import subprocess
import sys
import tarfile
from tempfile import NamedTemporaryFile, TemporaryDirectory
from typing import Callable, Iterable, Protocol, Sequence
from urllib.parse import urlsplit


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SOURCE_REF = "refs/heads/main"
SCHEMA_VERSION = 4
PRE_SITE_TEST_COMMANDS = (
    ("npm", "ci"),
    ("npm", "run", "audit:dependencies"),
    ("npm", "run", "lint"),
    ("npm", "run", "build"),
)
SITE_TEST_COMMAND = ("npm", "run", "test:site")
VALIDATION_COMMANDS = (
    *PRE_SITE_TEST_COMMANDS,
    SITE_TEST_COMMAND,
)
REQUIRED_ARCHIVE_MEMBERS = (
    "dist/server/index.js",
    "dist/.openai/hosting.json",
    "dist/.openai/site-candidate.json",
)
ARCHIVE_ROOT = "dist"
PACKAGING_COMMAND_PREFIX = (
    "env",
    "COPYFILE_DISABLE=1",
    "sh",
    "-c",
    'umask 022; exec "$@"',
    "repo-scout-site-package",
)
REQUIRED_DIRECTORY_MODE = 0o755
SHA_PATTERN = re.compile(r"[0-9a-f]{40}\Z")
DIGEST_PATTERN = re.compile(r"[0-9a-f]{64}\Z")
NODE_VERSION_PATTERN = re.compile(
    r"(?:0|[1-9][0-9]*)\."
    r"(?:0|[1-9][0-9]*)\."
    r"(?:0|[1-9][0-9]*)(?:\n)?\Z"
)
SCP_REPOSITORY_PATTERN = re.compile(
    r"(?:[^/@:\s]+@)?(?P<host>[^/:\s]+):(?P<path>[^\\].+)\Z"
)
REMOTE_REPOSITORY_SCHEMES = frozenset(("git", "http", "https", "ssh"))
DEFAULT_REPOSITORY_PORTS = {
    "git": 9418,
    "http": 80,
    "https": 443,
    "ssh": 22,
}
RECEIPT_KEYS = frozenset(("schema_version", "candidate", "archive"))
CANDIDATE_KEYS = frozenset(
    (
        "schema_version",
        "commit_sha",
        "source_ref",
        "node_version",
        "package_lock_sha256",
        "project_id",
    )
)
ARCHIVE_KEYS = frozenset(("name", "payload_sha256", "sha256"))


class SiteCandidateError(RuntimeError):
    """Raised when a Sites candidate cannot be tied to validated source."""


class _DuplicateJsonKeyError(ValueError):
    def __init__(self, key: str) -> None:
        self.key = key
        super().__init__(key)


class HashDigest(Protocol):
    def update(self, data: bytes, /) -> None: ...


CommandRunner = Callable[[Sequence[str], Path], str]


@dataclass(frozen=True)
class SiteCandidateResult:
    commit_sha: str
    archive_sha256: str
    receipt_sha256: str
    archive: Path
    receipt: Path


def prepare_site_candidate(
    root: Path,
    archive: Path,
    receipt: Path,
    package_script: Path,
    *,
    run_command: CommandRunner | None = None,
) -> SiteCandidateResult:
    project_root = root.expanduser().resolve()
    archive_path = _candidate_evidence_path(archive)
    receipt_path = _candidate_evidence_path(receipt)
    package_path = package_script.expanduser().resolve()
    runner = run_command or _run_command

    if archive_path == receipt_path:
        raise SiteCandidateError(
            "archive and receipt must use different output paths"
        )
    if package_path in (archive_path, receipt_path):
        raise SiteCandidateError(
            "Sites packaging helper cannot also be an output path"
        )
    _require_regular_file(project_root / "package-lock.json", "package lock")
    _require_regular_file(project_root / ".nvmrc", "Node runtime pin")
    expected_node_version = read_node_runtime_pin(project_root)
    hosting_path = project_root / ".openai" / "hosting.json"
    _require_regular_file(hosting_path, "Sites hosting metadata")
    _require_regular_file(package_path, "Sites packaging helper")
    if not os.access(package_path, os.X_OK):
        raise SiteCandidateError(
            f"Sites packaging helper is not executable: {package_path}"
        )
    for output_path, label in (
        (archive_path, "archive"),
        (receipt_path, "receipt"),
    ):
        if output_path == project_root or output_path.is_relative_to(
            project_root
        ):
            raise SiteCandidateError(
                f"{label} must be written outside the repository: {output_path}"
            )
        if os.path.lexists(output_path):
            raise SiteCandidateError(
                f"{label} output already exists; refusing to overwrite: "
                f"{output_path}"
            )

    commit_sha = _synchronized_commit(project_root, runner)

    node_output = runner(("node", "--version"), project_root).strip()
    expected_node_output = f"v{expected_node_version}"
    if node_output != expected_node_output:
        raise SiteCandidateError(
            "site candidate requires Node "
            f"{expected_node_version}; found {node_output or 'no version'}"
        )

    for command in PRE_SITE_TEST_COMMANDS:
        runner(command, project_root)

    server_entry = project_root / "dist" / "server" / "index.js"
    _require_regular_file(server_entry, "built Sites server entry")
    manifest = _candidate_manifest(
        project_root,
        commit_sha,
        expected_node_version,
    )
    manifest_path = (
        project_root / "dist" / ".openai" / "site-candidate.json"
    )
    _atomic_write_json(manifest_path, manifest)
    payload_sha256 = _candidate_payload_sha256(project_root)

    runner(SITE_TEST_COMMAND, project_root)
    _require_same_synchronized_commit(
        project_root,
        commit_sha,
        runner,
    )
    if _candidate_payload_sha256(project_root) != payload_sha256:
        raise SiteCandidateError(
            "candidate payload changed during site tests"
        )

    archive_path.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(
        dir=archive_path.parent,
        prefix=f".{archive_path.name}.",
    ) as staging_directory:
        staged_archive = Path(staging_directory) / archive_path.name
        runner(
            (
                *PACKAGING_COMMAND_PREFIX,
                str(package_path),
                str(project_root),
                str(staged_archive),
            ),
            project_root,
        )
        _require_regular_file(staged_archive, "Sites candidate archive")
        archive_sha256 = _sha256(staged_archive)
        _verify_archive(
            staged_archive,
            manifest,
            payload_sha256,
        )

        _require_same_synchronized_commit(
            project_root,
            commit_sha,
            runner,
        )
        _require_same_archive(
            staged_archive,
            archive_sha256,
        )
        _publish_new_output(
            staged_archive,
            archive_path,
            "archive",
        )
        _require_same_archive(
            archive_path,
            archive_sha256,
        )
    receipt_payload = {
        "schema_version": SCHEMA_VERSION,
        "candidate": manifest,
        "archive": {
            "name": archive_path.name,
            "payload_sha256": payload_sha256,
            "sha256": archive_sha256,
        },
    }
    receipt_sha256 = _atomic_create_json(
        receipt_path,
        receipt_payload,
        "receipt",
    )
    _require_same_synchronized_commit(
        project_root,
        commit_sha,
        runner,
    )
    _require_same_archive(
        archive_path,
        archive_sha256,
    )
    _require_same_regular_file(
        receipt_path,
        receipt_sha256,
        "Sites candidate receipt",
    )
    return SiteCandidateResult(
        commit_sha=commit_sha,
        archive_sha256=archive_sha256,
        receipt_sha256=receipt_sha256,
        archive=archive_path,
        receipt=receipt_path,
    )


def verify_site_candidate(
    root: Path,
    archive: Path,
    receipt: Path,
    *,
    expected_receipt_sha256: str | None = None,
    exported_source_repository: str | None = None,
    expected_exported_source_repository: str | None = None,
    run_command: CommandRunner | None = None,
) -> SiteCandidateResult:
    project_root = root.expanduser().resolve()
    archive_path = _candidate_evidence_path(archive)
    receipt_path = _candidate_evidence_path(receipt)
    runner = run_command or _run_command

    if (
        exported_source_repository is not None
        and expected_receipt_sha256 is None
    ):
        raise SiteCandidateError(
            "exported source verification requires an approved receipt digest"
        )
    if (
        expected_receipt_sha256 is not None
        and exported_source_repository is None
    ):
        raise SiteCandidateError(
            "approved receipt digest requires exported source verification"
        )
    if (
        exported_source_repository is None
        and expected_exported_source_repository is not None
    ):
        raise SiteCandidateError(
            "expected exported source repository requires exported source "
            "verification"
        )
    if (
        exported_source_repository is not None
        and expected_exported_source_repository is None
    ):
        raise SiteCandidateError(
            "exported source verification requires the approved Sites "
            "repository identity"
        )
    source_repository = (
        _validated_source_repository(exported_source_repository)
        if exported_source_repository is not None
        else None
    )
    approved_source_repository_identity: str | None = None
    if expected_exported_source_repository is not None:
        approved_source_repository = _validated_source_repository(
            expected_exported_source_repository
        )
        _require_remote_repository_identity(
            approved_source_repository,
            "approved Sites source repository",
        )
        approved_source_repository_identity = (
            _canonical_repository_identity(
                approved_source_repository,
                "approved Sites source repository",
            )
        )
    source_repository_identity: str | None = None
    if source_repository is not None:
        source_repository_identity = _resolved_repository_identity(
            source_repository,
            "exported source repository",
            project_root,
            runner,
        )
        if (
            source_repository_identity
            != approved_source_repository_identity
        ):
            raise SiteCandidateError(
                "repository does not match approved Sites repository"
            )
        origin_repository_identity = _resolved_repository_identity(
            "origin",
            "origin repository",
            project_root,
            runner,
        )
        _require_separate_repository(
            source_repository_identity,
            origin_repository_identity,
        )

    _require_regular_file(project_root / "package-lock.json", "package lock")
    _require_regular_file(project_root / ".nvmrc", "Node runtime pin")
    _require_regular_file(
        project_root / ".openai" / "hosting.json",
        "Sites hosting metadata",
    )
    _require_regular_file(archive_path, "Sites candidate archive")
    _require_regular_file(receipt_path, "Sites candidate receipt")

    commit_sha = _synchronized_commit(project_root, runner)
    expected_candidate = _candidate_manifest(
        project_root,
        commit_sha,
        read_node_runtime_pin(project_root),
    )
    receipt_payload, receipt_sha256 = _read_json_object_with_sha256(
        receipt_path,
        "Sites candidate receipt",
    )
    if expected_receipt_sha256 is not None:
        approved_receipt_sha256 = _validated_sha256(
            expected_receipt_sha256,
            "expected receipt SHA-256",
        )
        if receipt_sha256 != approved_receipt_sha256:
            raise SiteCandidateError(
                "receipt digest does not match approved receipt"
            )
    _require_exact_keys(receipt_payload, RECEIPT_KEYS, "receipt")
    _require_schema_version(
        receipt_payload["schema_version"],
        "receipt",
    )

    candidate = receipt_payload["candidate"]
    if not isinstance(candidate, dict):
        raise SiteCandidateError("receipt candidate must be a JSON object")
    _require_exact_keys(candidate, CANDIDATE_KEYS, "receipt candidate")
    _require_schema_version(
        candidate["schema_version"],
        "receipt candidate",
    )
    for field, expected_value in expected_candidate.items():
        if type(candidate[field]) is not type(expected_value):
            raise SiteCandidateError(
                f"receipt candidate {field} does not match checkout"
            )
        if candidate[field] != expected_value:
            raise SiteCandidateError(
                f"receipt candidate {field} does not match checkout"
            )

    exported_commit_sha: str | None = None
    if source_repository is not None:
        exported_commit_sha = _exported_source_commit(
            source_repository,
            SOURCE_REF,
            project_root,
            runner,
        )
        if exported_commit_sha != commit_sha:
            raise SiteCandidateError(
                "exported source does not match approved candidate"
            )

    archive_evidence = receipt_payload["archive"]
    if not isinstance(archive_evidence, dict):
        raise SiteCandidateError("receipt archive must be a JSON object")
    _require_exact_keys(archive_evidence, ARCHIVE_KEYS, "receipt archive")
    if archive_evidence["name"] != archive_path.name:
        raise SiteCandidateError(
            "archive filename does not match receipt"
        )
    recorded_payload_digest = _validated_sha256(
        archive_evidence["payload_sha256"],
        "receipt archive payload_sha256",
    )
    recorded_digest = _validated_sha256(
        archive_evidence["sha256"],
        "receipt archive sha256",
    )
    archive_sha256 = _sha256(archive_path)
    if archive_sha256 != recorded_digest:
        raise SiteCandidateError("archive digest does not match receipt")

    _verify_archive(
        archive_path,
        candidate,
        recorded_payload_digest,
    )
    _require_same_synchronized_commit(
        project_root,
        commit_sha,
        runner,
    )
    _require_same_archive(
        archive_path,
        archive_sha256,
    )
    _require_same_regular_file(
        receipt_path,
        receipt_sha256,
        "Sites candidate receipt",
    )
    if source_repository is not None:
        final_source_repository_identity = _resolved_repository_identity(
            source_repository,
            "exported source repository",
            project_root,
            runner,
        )
        if (
            final_source_repository_identity
            != source_repository_identity
        ):
            raise SiteCandidateError(
                "exported source repository identity moved during candidate "
                "operation"
            )
        if (
            final_source_repository_identity
            != approved_source_repository_identity
        ):
            raise SiteCandidateError(
                "repository does not match approved Sites repository"
            )
        final_origin_repository_identity = _resolved_repository_identity(
            "origin",
            "origin repository",
            project_root,
            runner,
        )
        _require_separate_repository(
            final_source_repository_identity,
            final_origin_repository_identity,
        )
        final_exported_commit_sha = _exported_source_commit(
            source_repository,
            SOURCE_REF,
            project_root,
            runner,
        )
        if final_exported_commit_sha != exported_commit_sha:
            raise SiteCandidateError(
                "exported source moved during candidate operation"
            )
    return SiteCandidateResult(
        commit_sha=commit_sha,
        archive_sha256=archive_sha256,
        receipt_sha256=receipt_sha256,
        archive=archive_path,
        receipt=receipt_path,
    )


def _run_command(command: Sequence[str], root: Path) -> str:
    result = subprocess.run(
        command,
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip()
        rendered = " ".join(command)
        suffix = f": {detail}" if detail else ""
        raise SiteCandidateError(
            f"command failed with exit {result.returncode}: {rendered}{suffix}"
        )
    return result.stdout.strip()


def _require_clean_worktree(
    root: Path,
    run_command: CommandRunner,
) -> None:
    status = run_command(
        ("git", "status", "--porcelain", "--untracked-files=all"),
        root,
    ).strip()
    if status:
        first_change = status.splitlines()[0]
        raise SiteCandidateError(
            f"worktree must be clean for candidate operations: {first_change}"
        )


def _synchronized_commit(
    root: Path,
    run_command: CommandRunner,
) -> str:
    _require_clean_worktree(root, run_command)
    branch = run_command(("git", "branch", "--show-current"), root).strip()
    current_ref = f"refs/heads/{branch}" if branch else "detached HEAD"
    if current_ref != SOURCE_REF:
        raise SiteCandidateError(
            f"candidate operations require {SOURCE_REF}; found {current_ref}"
        )
    commit_sha = _validated_sha(
        run_command(("git", "rev-parse", "HEAD"), root),
        "HEAD",
    )
    origin_sha = _validated_sha(
        run_command(("git", "rev-parse", "origin/main"), root),
        "origin/main",
    )
    if commit_sha != origin_sha:
        raise SiteCandidateError(
            f"HEAD {commit_sha} does not match origin/main {origin_sha}"
        )
    return commit_sha


def _require_same_synchronized_commit(
    root: Path,
    expected_commit_sha: str,
    run_command: CommandRunner,
) -> None:
    current_commit_sha = _synchronized_commit(root, run_command)
    if current_commit_sha != expected_commit_sha:
        raise SiteCandidateError(
            "synchronized source moved during candidate operation: "
            f"expected {expected_commit_sha}; found {current_commit_sha}"
        )


def _validated_sha(value: str, label: str) -> str:
    normalized = value.strip()
    if SHA_PATTERN.fullmatch(normalized) is None:
        raise SiteCandidateError(
            f"{label} did not resolve to a full lowercase commit SHA"
        )
    return normalized


def _validated_sha256(value: object, label: str) -> str:
    if not isinstance(value, str) or DIGEST_PATTERN.fullmatch(value) is None:
        raise SiteCandidateError(
            f"{label} must be a lowercase SHA-256 digest"
        )
    return value


def _validated_source_repository(value: str) -> str:
    if (
        not value
        or value.startswith("-")
        or any(ord(character) < 32 for character in value)
    ):
        raise SiteCandidateError(
            "exported source repository must be a non-empty Git repository "
            "identity without control characters"
        )
    parsed = urlsplit(value)
    if (
        parsed.password is not None
        or parsed.query
        or parsed.fragment
        or (
            parsed.scheme.lower() in {"http", "https"}
            and parsed.username is not None
        )
    ):
        raise SiteCandidateError(
            "exported source repository must not embed credentials or URL "
            "parameters"
        )
    return value


def _resolved_repository_identity(
    repository: str,
    label: str,
    root: Path,
    run_command: CommandRunner,
) -> str:
    output = run_command(
        ("git", "ls-remote", "--get-url", repository),
        root,
    )
    lines = output.splitlines()
    if len(lines) != 1:
        raise SiteCandidateError(
            f"{label} must resolve to exactly one Git repository identity"
        )
    resolved = _validated_source_repository(lines[0])
    _require_remote_repository_identity(resolved, label)
    return _canonical_repository_identity(resolved, label)


def _require_remote_repository_identity(value: str, label: str) -> None:
    parsed = urlsplit(value)
    if (
        parsed.scheme.lower() in REMOTE_REPOSITORY_SCHEMES
        and parsed.hostname
    ):
        return
    if SCP_REPOSITORY_PATTERN.fullmatch(value) is not None:
        return
    raise SiteCandidateError(
        f"{label} must resolve to a remote Git repository"
    )


def _canonical_repository_identity(value: str, label: str) -> str:
    parsed = urlsplit(value)
    if (
        parsed.scheme.lower() in REMOTE_REPOSITORY_SCHEMES
        and parsed.hostname
    ):
        scheme = parsed.scheme.lower()
        host = (parsed.hostname or "").lower()
        try:
            port = parsed.port
        except ValueError as exc:
            raise SiteCandidateError(
                f"{label} must be a valid remote Git repository identity"
            ) from exc
        authority = f"[{host}]" if ":" in host else host
        if (
            port is not None
            and port != DEFAULT_REPOSITORY_PORTS[scheme]
        ):
            authority = f"{authority}:{port}"
        path = parsed.path.rstrip("/")
        if path.endswith(".git"):
            path = path[:-4]
        return f"{authority}/{path.lstrip('/')}"
    scp_match = SCP_REPOSITORY_PATTERN.fullmatch(value)
    if scp_match is None:
        raise SiteCandidateError(
            f"{label} must be a valid remote Git repository identity"
        )
    path = scp_match.group("path").rstrip("/")
    if path.endswith(".git"):
        path = path[:-4]
    return f"{scp_match.group('host').lower()}/{path.lstrip('/')}"


def _require_separate_repository(
    source_repository_identity: str,
    origin_repository_identity: str,
) -> None:
    if source_repository_identity == origin_repository_identity:
        raise SiteCandidateError(
            "exported source repository must be separate from origin"
        )


def _exported_source_commit(
    repository: str,
    source_ref: str,
    root: Path,
    run_command: CommandRunner,
) -> str:
    output = run_command(
        (
            "git",
            "ls-remote",
            "--exit-code",
            "--refs",
            repository,
            source_ref,
        ),
        root,
    )
    lines = output.splitlines()
    if len(lines) != 1:
        raise SiteCandidateError(
            f"exported source repository must resolve exactly one {source_ref}"
        )
    fields = lines[0].split()
    if len(fields) != 2 or fields[1] != source_ref:
        raise SiteCandidateError(
            f"exported source repository returned an invalid {source_ref}"
        )
    return _validated_sha(fields[0], f"exported source {source_ref}")


def _candidate_evidence_path(path: Path) -> Path:
    absolute = Path(os.path.abspath(path.expanduser()))
    return absolute.parent.resolve() / absolute.name


def _require_regular_file(path: Path, label: str) -> None:
    if path.is_symlink() or not path.is_file():
        raise SiteCandidateError(f"{label} must be a regular file: {path}")


def _read_json_object(path: Path, label: str) -> dict[str, object]:
    payload, _ = _read_json_object_with_sha256(path, label)
    return payload


def _read_json_object_with_sha256(
    path: Path,
    label: str,
) -> tuple[dict[str, object], str]:
    try:
        content = path.read_bytes()
        payload = _load_json_with_unique_keys(
            content.decode("utf-8"),
            label,
        )
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise SiteCandidateError(f"could not read {label}: {exc}") from exc
    if not isinstance(payload, dict):
        raise SiteCandidateError(f"{label} must contain a JSON object")
    return payload, hashlib.sha256(content).hexdigest()


def _load_json_with_unique_keys(content: str, label: str) -> object:
    try:
        return json.loads(
            content,
            object_pairs_hook=_reject_duplicate_json_keys,
        )
    except _DuplicateJsonKeyError as exc:
        raise SiteCandidateError(
            f"{label} contains duplicate JSON key: {exc.key}"
        ) from exc


def _reject_duplicate_json_keys(
    pairs: list[tuple[str, object]],
) -> dict[str, object]:
    values: dict[str, object] = {}
    for key, value in pairs:
        if key in values:
            raise _DuplicateJsonKeyError(key)
        values[key] = value
    return values


def _candidate_manifest(
    project_root: Path,
    commit_sha: str,
    node_version: str,
) -> dict[str, object]:
    hosting = _read_json_object(
        project_root / ".openai" / "hosting.json",
        "Sites hosting metadata",
    )
    project_id = hosting.get("project_id")
    if not isinstance(project_id, str) or not project_id.strip():
        raise SiteCandidateError(
            "Sites hosting metadata must contain a non-empty project_id"
        )
    return {
        "schema_version": SCHEMA_VERSION,
        "commit_sha": commit_sha,
        "source_ref": SOURCE_REF,
        "node_version": node_version,
        "package_lock_sha256": _sha256(
            project_root / "package-lock.json"
        ),
        "project_id": project_id,
    }


def read_node_runtime_pin(project_root: Path) -> str:
    runtime_path = project_root.expanduser().resolve() / ".nvmrc"
    _require_regular_file(runtime_path, "Node runtime pin")
    try:
        value = runtime_path.read_text(encoding="ascii")
    except (OSError, UnicodeError) as exc:
        raise SiteCandidateError(
            f"could not read Node runtime pin: {exc}"
        ) from exc
    if NODE_VERSION_PATTERN.fullmatch(value) is None:
        raise SiteCandidateError(
            "Node runtime pin must contain one semantic version"
        )
    return value.rstrip("\n")


def _require_exact_keys(
    payload: dict[str, object],
    expected_keys: frozenset[str],
    label: str,
) -> None:
    if set(payload) != expected_keys:
        expected = ", ".join(sorted(expected_keys))
        raise SiteCandidateError(
            f"{label} must contain exactly: {expected}"
        )


def _require_schema_version(value: object, label: str) -> None:
    if type(value) is not int or value != SCHEMA_VERSION:
        raise SiteCandidateError(
            f"{label} schema_version must be {SCHEMA_VERSION}"
        )


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        with path.open("rb") as source:
            for chunk in iter(lambda: source.read(1024 * 1024), b""):
                digest.update(chunk)
    except OSError as exc:
        raise SiteCandidateError(f"could not hash {path}: {exc}") from exc
    return digest.hexdigest()


def _require_same_archive(path: Path, expected_sha256: str) -> None:
    _require_same_regular_file(
        path,
        expected_sha256,
        "Sites candidate archive",
    )


def _require_same_regular_file(
    path: Path,
    expected_sha256: str,
    label: str,
) -> None:
    if path.is_symlink() or not path.is_file():
        raise SiteCandidateError(
            f"{label} changed during candidate operation"
        )
    if _sha256(path) != expected_sha256:
        raise SiteCandidateError(
            f"{label} changed during candidate operation"
        )


def _candidate_payload_sha256(project_root: Path) -> str:
    entries: dict[str, Path] = {}
    _overlay_payload_entries(
        entries,
        project_root / ARCHIVE_ROOT,
        PurePosixPath(ARCHIVE_ROOT),
        "built Sites output",
    )
    entries["dist/.openai/hosting.json"] = (
        project_root / ".openai" / "hosting.json"
    )

    drizzle = project_root / "drizzle"
    if drizzle.is_symlink():
        raise SiteCandidateError(
            f"Sites drizzle payload must be a regular directory: {drizzle}"
        )
    if drizzle.exists():
        if not drizzle.is_dir():
            raise SiteCandidateError(
                f"Sites drizzle payload must be a regular directory: {drizzle}"
            )
        _overlay_payload_entries(
            entries,
            drizzle,
            PurePosixPath("dist/.openai/drizzle"),
            "Sites drizzle payload",
        )

    digest = hashlib.sha256()
    for name, path in sorted(entries.items()):
        try:
            details = path.lstat()
            mode = stat.S_IMODE(details.st_mode)
            if stat.S_ISDIR(details.st_mode):
                if mode != REQUIRED_DIRECTORY_MODE:
                    raise SiteCandidateError(
                        "tested Sites payload directory mode must be 0755: "
                        f"{path}"
                    )
                _update_payload_digest(
                    digest,
                    name,
                    b"d",
                    mode,
                    0,
                    (),
                )
            elif stat.S_ISREG(details.st_mode):
                with path.open("rb") as source:
                    _update_payload_digest(
                        digest,
                        name,
                        b"f",
                        mode,
                        details.st_size,
                        iter(lambda: source.read(1024 * 1024), b""),
                    )
            else:
                raise SiteCandidateError(
                    "tested Sites payload must contain only regular files "
                    f"and directories: {path}"
                )
        except SiteCandidateError:
            raise
        except OSError as exc:
            raise SiteCandidateError(
                f"could not hash tested Sites payload {path}: {exc}"
            ) from exc
    return digest.hexdigest()


def _overlay_payload_entries(
    entries: dict[str, Path],
    source_root: Path,
    archive_root: PurePosixPath,
    label: str,
) -> None:
    if source_root.is_symlink() or not source_root.is_dir():
        raise SiteCandidateError(
            f"{label} must be a regular directory: {source_root}"
        )
    entries[archive_root.as_posix()] = source_root
    for path in sorted(source_root.rglob("*")):
        relative = path.relative_to(source_root)
        if path.is_symlink() or not (path.is_file() or path.is_dir()):
            raise SiteCandidateError(
                f"{label} must contain only regular files and directories: "
                f"{path}"
            )
        entries[(archive_root / relative.as_posix()).as_posix()] = path


def _update_payload_digest(
    digest: HashDigest,
    name: str,
    entry_type: bytes,
    mode: int,
    size: int,
    chunks: Iterable[bytes],
) -> None:
    encoded_name = name.encode("utf-8")
    digest.update(len(encoded_name).to_bytes(8, "big"))
    digest.update(encoded_name)
    digest.update(entry_type)
    digest.update(mode.to_bytes(4, "big"))
    digest.update(size.to_bytes(8, "big"))
    for chunk in chunks:
        digest.update(chunk)


def _atomic_write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    serialized = _serialize_json(payload)
    temporary_path: Path | None = None
    try:
        with NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as temporary:
            temporary_path = Path(temporary.name)
            temporary.write(serialized)
            temporary.flush()
            os.fsync(temporary.fileno())
        os.replace(temporary_path, path)
    except OSError as exc:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)
        raise SiteCandidateError(f"could not write {path}: {exc}") from exc


def _atomic_create_json(
    path: Path,
    payload: dict[str, object],
    label: str,
) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    serialized = _serialize_json(payload)
    temporary_path: Path | None = None
    try:
        with NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as temporary:
            temporary_path = Path(temporary.name)
            temporary.write(serialized)
            temporary.flush()
            os.fsync(temporary.fileno())
    except OSError as exc:
        _remove_staged_file(temporary_path)
        raise SiteCandidateError(f"could not stage {path}: {exc}") from exc

    if temporary_path is None:
        raise SiteCandidateError(f"could not stage {path}")
    try:
        receipt_sha256 = _sha256(temporary_path)
        _publish_new_output(temporary_path, path, label)
    except SiteCandidateError:
        _remove_staged_file(temporary_path)
        raise

    try:
        temporary_path.unlink()
    except OSError as exc:
        raise SiteCandidateError(
            f"{label} output was published to {path}, but staging cleanup "
            f"failed for {temporary_path}: {exc}"
        ) from exc
    return receipt_sha256


def _publish_new_output(
    staged_path: Path,
    output_path: Path,
    label: str,
) -> None:
    try:
        os.link(staged_path, output_path)
    except FileExistsError as exc:
        raise SiteCandidateError(
            f"{label} output appeared during candidate operation; "
            f"refusing to overwrite: {output_path}"
        ) from exc
    except OSError as exc:
        raise SiteCandidateError(
            f"could not publish {label} output {output_path}: {exc}"
        ) from exc


def _remove_staged_file(path: Path | None) -> None:
    if path is None:
        return
    try:
        path.unlink(missing_ok=True)
    except OSError:
        pass


def _serialize_json(payload: dict[str, object]) -> str:
    return json.dumps(
        payload,
        indent=2,
        sort_keys=True,
        ensure_ascii=True,
    ) + "\n"


def _verify_archive(
    archive: Path,
    expected_manifest: dict[str, object],
    expected_payload_sha256: str,
) -> None:
    try:
        with tarfile.open(archive, "r:gz") as bundle:
            members: dict[str, tarfile.TarInfo] = {}
            for member in bundle.getmembers():
                name = member.name.rstrip("/")
                normalized = PurePosixPath(name)
                parts = normalized.parts
                if (
                    not name
                    or name.startswith("/")
                    or ".." in parts
                    or normalized.as_posix() != name
                    or member.issym()
                    or member.islnk()
                ):
                    raise SiteCandidateError(
                        f"unsafe archive member: {member.name}"
                    )
                if not parts or parts[0] != ARCHIVE_ROOT:
                    raise SiteCandidateError(
                        "archive member must stay within "
                        f"{ARCHIVE_ROOT}/: {member.name}"
                    )
                if not (member.isfile() or member.isdir()):
                    raise SiteCandidateError(
                        "archive member must be a regular file or directory: "
                        f"{member.name}"
                    )
                if name in members:
                    raise SiteCandidateError(
                        f"duplicate archive member: {member.name}"
                    )
                members[name] = member

            for required_name in REQUIRED_ARCHIVE_MEMBERS:
                member = members.get(required_name)
                if member is None or not member.isfile():
                    raise SiteCandidateError(
                        f"archive is missing regular file {required_name}"
                    )

            manifest = _read_archived_json(
                bundle,
                members["dist/.openai/site-candidate.json"],
                "site candidate manifest",
            )
            if manifest != expected_manifest:
                raise SiteCandidateError(
                    "archive site candidate manifest does not match validated "
                    "source"
                )
            hosting = _read_archived_json(
                bundle,
                members["dist/.openai/hosting.json"],
                "Sites hosting metadata",
            )
            if hosting.get("project_id") != expected_manifest["project_id"]:
                raise SiteCandidateError(
                    "archive Sites project does not match validated source"
                )
            payload_sha256 = _archived_payload_sha256(bundle, members)
            if payload_sha256 != expected_payload_sha256:
                raise SiteCandidateError(
                    "archive payload does not match tested build"
                )
    except SiteCandidateError:
        raise
    except (OSError, tarfile.TarError) as exc:
        raise SiteCandidateError(
            f"could not validate Sites candidate archive: {exc}"
        ) from exc


def _archived_payload_sha256(
    bundle: tarfile.TarFile,
    members: dict[str, tarfile.TarInfo],
) -> str:
    digest = hashlib.sha256()
    for name, member in sorted(members.items()):
        if member.isdir():
            _update_payload_digest(
                digest,
                name,
                b"d",
                member.mode,
                0,
                (),
            )
        else:
            source = bundle.extractfile(member)
            if source is None:
                raise SiteCandidateError(
                    f"could not read archived payload file {name}"
                )
            _update_payload_digest(
                digest,
                name,
                b"f",
                member.mode,
                member.size,
                iter(lambda: source.read(1024 * 1024), b""),
            )
    return digest.hexdigest()


def _read_archived_json(
    bundle: tarfile.TarFile,
    member: tarfile.TarInfo,
    label: str,
) -> dict[str, object]:
    source = bundle.extractfile(member)
    if source is None:
        raise SiteCandidateError(f"could not read archived {label}")
    try:
        payload = _load_json_with_unique_keys(
            source.read().decode("utf-8"),
            f"archived {label}",
        )
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise SiteCandidateError(
            f"archived {label} is not valid UTF-8 JSON: {exc}"
        ) from exc
    if not isinstance(payload, dict):
        raise SiteCandidateError(f"archived {label} must be a JSON object")
    return payload


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Build a fail-closed Sites candidate tied to clean, synchronized, "
            "validated Repo Scout source."
        )
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=PROJECT_ROOT,
        help="Repository root. Defaults to the current Repo Scout checkout.",
    )
    parser.add_argument(
        "--package-script",
        type=Path,
        help=(
            "Absolute path to the trusted Sites package-site.sh helper. "
            "Required unless --verify-only is used."
        ),
    )
    parser.add_argument(
        "--verify-only",
        action="store_true",
        help=(
            "Verify an existing archive and receipt against the checkout "
            "without building, packaging, exporting, or deploying."
        ),
    )
    parser.add_argument(
        "--archive",
        type=Path,
        required=True,
        help=(
            "Candidate .tar.gz path outside the repository. Preparation "
            "requires a new path; --verify-only requires an existing path."
        ),
    )
    parser.add_argument(
        "--receipt",
        type=Path,
        required=True,
        help=(
            "Candidate JSON receipt path outside the repository. Preparation "
            "requires a new path; --verify-only requires an existing path."
        ),
    )
    parser.add_argument(
        "--expected-receipt-sha256",
        help=(
            "Approved lowercase receipt SHA-256 to require during "
            "pre-save --verify-only. Requires both exported source "
            "repository options."
        ),
    )
    parser.add_argument(
        "--exported-source-repository",
        help=(
            "Existing Sites Git repository URL or configured remote name to "
            "verify read-only before saving. It must resolve to the approved "
            "remote identity, separate from origin. Requires --verify-only, "
            "--expected-receipt-sha256, and "
            "--expected-exported-source-repository."
        ),
    )
    parser.add_argument(
        "--expected-exported-source-repository",
        help=(
            "Credential-free remote Sites repository identity recorded in "
            "source-export approval. Requires --verify-only and "
            "--exported-source-repository."
        ),
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.verify_only:
            if args.package_script is not None:
                parser.error(
                    "--package-script cannot be used with --verify-only"
                )
            if (
                args.exported_source_repository is not None
                and args.expected_receipt_sha256 is None
            ):
                parser.error(
                    "--exported-source-repository requires "
                    "--expected-receipt-sha256"
                )
            if (
                args.expected_receipt_sha256 is not None
                and args.exported_source_repository is None
            ):
                parser.error(
                    "--expected-receipt-sha256 requires "
                    "--exported-source-repository"
                )
            if (
                args.exported_source_repository is None
                and args.expected_exported_source_repository is not None
            ):
                parser.error(
                    "--expected-exported-source-repository requires "
                    "--exported-source-repository"
                )
            if (
                args.exported_source_repository is not None
                and args.expected_exported_source_repository is None
            ):
                parser.error(
                    "--exported-source-repository requires "
                    "--expected-exported-source-repository"
                )
            result = verify_site_candidate(
                args.root,
                args.archive,
                args.receipt,
                expected_receipt_sha256=args.expected_receipt_sha256,
                exported_source_repository=(
                    args.exported_source_repository
                ),
                expected_exported_source_repository=(
                    args.expected_exported_source_repository
                ),
            )
            action = "verified"
        else:
            if args.package_script is None:
                parser.error(
                    "--package-script is required unless --verify-only is used"
                )
            if args.expected_receipt_sha256 is not None:
                parser.error(
                    "--expected-receipt-sha256 requires --verify-only"
                )
            if args.exported_source_repository is not None:
                parser.error(
                    "--exported-source-repository requires --verify-only"
                )
            if args.expected_exported_source_repository is not None:
                parser.error(
                    "--expected-exported-source-repository requires "
                    "--verify-only"
                )
            result = prepare_site_candidate(
                args.root,
                args.archive,
                args.receipt,
                args.package_script,
            )
            action = "ready"
    except SiteCandidateError as exc:
        print(f"site-candidate: {exc}", file=sys.stderr)
        return 2
    print(
        f"site candidate {action}: "
        f"commit={result.commit_sha} "
        f"archive={result.archive.name} "
        f"sha256={result.archive_sha256} "
        f"receipt={result.receipt.name} "
        f"receipt_sha256={result.receipt_sha256}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
