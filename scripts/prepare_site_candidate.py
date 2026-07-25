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
from tempfile import NamedTemporaryFile
from typing import Callable, Iterable, Protocol, Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SOURCE_REF = "refs/heads/main"
SCHEMA_VERSION = 2
VALIDATION_COMMANDS = (
    ("npm", "ci"),
    ("npm", "run", "audit:dependencies"),
    ("npm", "test"),
    ("npm", "run", "lint"),
)
REQUIRED_ARCHIVE_MEMBERS = (
    "dist/server/index.js",
    "dist/.openai/hosting.json",
    "dist/.openai/site-candidate.json",
)
ARCHIVE_ROOT = "dist"
PACKAGING_ENV = ("env", "COPYFILE_DISABLE=1")
SHA_PATTERN = re.compile(r"[0-9a-f]{40}\Z")
DIGEST_PATTERN = re.compile(r"[0-9a-f]{64}\Z")
NODE_VERSION_PATTERN = re.compile(
    r"(?:0|[1-9][0-9]*)\."
    r"(?:0|[1-9][0-9]*)\."
    r"(?:0|[1-9][0-9]*)(?:\n)?\Z"
)
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


class HashDigest(Protocol):
    def update(self, data: bytes, /) -> None: ...


CommandRunner = Callable[[Sequence[str], Path], str]


@dataclass(frozen=True)
class SiteCandidateResult:
    commit_sha: str
    archive_sha256: str
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
    archive_path = archive.expanduser().resolve()
    receipt_path = receipt.expanduser().resolve()
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

    commit_sha = _synchronized_commit(project_root, runner)

    node_output = runner(("node", "--version"), project_root).strip()
    expected_node_output = f"v{expected_node_version}"
    if node_output != expected_node_output:
        raise SiteCandidateError(
            "site candidate requires Node "
            f"{expected_node_version}; found {node_output or 'no version'}"
        )

    for command in VALIDATION_COMMANDS:
        runner(command, project_root)
    _require_clean_worktree(project_root, runner)

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

    archive_path.parent.mkdir(parents=True, exist_ok=True)
    runner(
        (
            *PACKAGING_ENV,
            str(package_path),
            str(project_root),
            str(archive_path),
        ),
        project_root,
    )
    _require_clean_worktree(project_root, runner)
    _require_regular_file(archive_path, "Sites candidate archive")
    _verify_archive(
        archive_path,
        manifest,
        payload_sha256,
    )

    archive_sha256 = _sha256(archive_path)
    receipt_payload = {
        "schema_version": SCHEMA_VERSION,
        "candidate": manifest,
        "archive": {
            "name": archive_path.name,
            "payload_sha256": payload_sha256,
            "sha256": archive_sha256,
        },
    }
    _atomic_write_json(receipt_path, receipt_payload)
    return SiteCandidateResult(
        commit_sha=commit_sha,
        archive_sha256=archive_sha256,
        archive=archive_path,
        receipt=receipt_path,
    )


def verify_site_candidate(
    root: Path,
    archive: Path,
    receipt: Path,
    *,
    run_command: CommandRunner | None = None,
) -> SiteCandidateResult:
    project_root = root.expanduser().resolve()
    archive_path = archive.expanduser().resolve()
    receipt_path = receipt.expanduser().resolve()
    runner = run_command or _run_command

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
    receipt_payload = _read_json_object(
        receipt_path,
        "Sites candidate receipt",
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

    archive_evidence = receipt_payload["archive"]
    if not isinstance(archive_evidence, dict):
        raise SiteCandidateError("receipt archive must be a JSON object")
    _require_exact_keys(archive_evidence, ARCHIVE_KEYS, "receipt archive")
    if archive_evidence["name"] != archive_path.name:
        raise SiteCandidateError(
            "archive filename does not match receipt"
        )
    recorded_payload_digest = archive_evidence["payload_sha256"]
    if (
        not isinstance(recorded_payload_digest, str)
        or DIGEST_PATTERN.fullmatch(recorded_payload_digest) is None
    ):
        raise SiteCandidateError(
            "receipt archive payload_sha256 must be a lowercase SHA-256 digest"
        )
    recorded_digest = archive_evidence["sha256"]
    if (
        not isinstance(recorded_digest, str)
        or DIGEST_PATTERN.fullmatch(recorded_digest) is None
    ):
        raise SiteCandidateError(
            "receipt archive sha256 must be a lowercase SHA-256 digest"
        )
    archive_sha256 = _sha256(archive_path)
    if archive_sha256 != recorded_digest:
        raise SiteCandidateError("archive digest does not match receipt")

    _verify_archive(
        archive_path,
        candidate,
        recorded_payload_digest,
    )
    return SiteCandidateResult(
        commit_sha=commit_sha,
        archive_sha256=archive_sha256,
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


def _validated_sha(value: str, label: str) -> str:
    normalized = value.strip()
    if SHA_PATTERN.fullmatch(normalized) is None:
        raise SiteCandidateError(
            f"{label} did not resolve to a full lowercase commit SHA"
        )
    return normalized


def _require_regular_file(path: Path, label: str) -> None:
    if path.is_symlink() or not path.is_file():
        raise SiteCandidateError(f"{label} must be a regular file: {path}")


def _read_json_object(path: Path, label: str) -> dict[str, object]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise SiteCandidateError(f"could not read {label}: {exc}") from exc
    if not isinstance(payload, dict):
        raise SiteCandidateError(f"{label} must contain a JSON object")
    return payload


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


def _candidate_payload_sha256(project_root: Path) -> str:
    files: dict[str, Path] = {}
    _overlay_payload_files(
        files,
        project_root / ARCHIVE_ROOT,
        PurePosixPath(ARCHIVE_ROOT),
        "built Sites output",
    )
    files["dist/.openai/hosting.json"] = (
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
        _overlay_payload_files(
            files,
            drizzle,
            PurePosixPath("dist/.openai/drizzle"),
            "Sites drizzle payload",
        )

    digest = hashlib.sha256()
    for name, path in sorted(files.items()):
        try:
            details = path.stat()
            size = details.st_size
            mode = stat.S_IMODE(details.st_mode)
            with path.open("rb") as source:
                _update_payload_digest(
                    digest,
                    name,
                    mode,
                    size,
                    iter(lambda: source.read(1024 * 1024), b""),
                )
        except OSError as exc:
            raise SiteCandidateError(
                f"could not hash tested build payload {path}: {exc}"
            ) from exc
    return digest.hexdigest()


def _overlay_payload_files(
    files: dict[str, Path],
    source_root: Path,
    archive_root: PurePosixPath,
    label: str,
) -> None:
    if source_root.is_symlink() or not source_root.is_dir():
        raise SiteCandidateError(
            f"{label} must be a regular directory: {source_root}"
        )
    for path in sorted(source_root.rglob("*")):
        relative = path.relative_to(source_root)
        if path.is_symlink() or not (path.is_file() or path.is_dir()):
            raise SiteCandidateError(
                f"{label} must contain only regular files and directories: "
                f"{path}"
            )
        if path.is_file():
            files[(archive_root / relative.as_posix()).as_posix()] = path


def _update_payload_digest(
    digest: HashDigest,
    name: str,
    mode: int,
    size: int,
    chunks: Iterable[bytes],
) -> None:
    encoded_name = name.encode("utf-8")
    digest.update(len(encoded_name).to_bytes(8, "big"))
    digest.update(encoded_name)
    digest.update(mode.to_bytes(4, "big"))
    digest.update(size.to_bytes(8, "big"))
    for chunk in chunks:
        digest.update(chunk)


def _atomic_write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    serialized = json.dumps(
        payload,
        indent=2,
        sort_keys=True,
        ensure_ascii=True,
    ) + "\n"
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
        if not member.isfile():
            continue
        source = bundle.extractfile(member)
        if source is None:
            raise SiteCandidateError(
                f"could not read archived payload file {name}"
            )
        _update_payload_digest(
            digest,
            name,
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
        payload = json.loads(source.read().decode("utf-8"))
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
        help="Candidate .tar.gz path outside the repository.",
    )
    parser.add_argument(
        "--receipt",
        type=Path,
        required=True,
        help="Candidate JSON receipt path outside the repository.",
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
            result = verify_site_candidate(
                args.root,
                args.archive,
                args.receipt,
            )
            action = "verified"
        else:
            if args.package_script is None:
                parser.error(
                    "--package-script is required unless --verify-only is used"
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
        f"receipt={result.receipt.name}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
