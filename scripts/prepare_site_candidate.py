#!/usr/bin/env python3
from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
import tarfile
from tempfile import NamedTemporaryFile
from typing import Callable, Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[1]
EXPECTED_NODE_VERSION = "22.13.0"
SOURCE_REF = "refs/heads/main"
SCHEMA_VERSION = 1
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
SHA_PATTERN = re.compile(r"[0-9a-f]{40}\Z")


class SiteCandidateError(RuntimeError):
    """Raised when a Sites candidate cannot be tied to validated source."""


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

    _require_clean_worktree(project_root, runner)
    commit_sha = _validated_sha(
        runner(("git", "rev-parse", "HEAD"), project_root),
        "HEAD",
    )
    origin_sha = _validated_sha(
        runner(("git", "rev-parse", "origin/main"), project_root),
        "origin/main",
    )
    if commit_sha != origin_sha:
        raise SiteCandidateError(
            f"HEAD {commit_sha} does not match origin/main {origin_sha}"
        )

    node_output = runner(("node", "--version"), project_root).strip()
    expected_node_output = f"v{EXPECTED_NODE_VERSION}"
    if node_output != expected_node_output:
        raise SiteCandidateError(
            "site candidate requires Node "
            f"{EXPECTED_NODE_VERSION}; found {node_output or 'no version'}"
        )

    hosting = _read_json_object(hosting_path, "Sites hosting metadata")
    project_id = hosting.get("project_id")
    if not isinstance(project_id, str) or not project_id.strip():
        raise SiteCandidateError(
            "Sites hosting metadata must contain a non-empty project_id"
        )
    lock_sha256 = _sha256(project_root / "package-lock.json")

    for command in VALIDATION_COMMANDS:
        runner(command, project_root)
    _require_clean_worktree(project_root, runner)

    server_entry = project_root / "dist" / "server" / "index.js"
    _require_regular_file(server_entry, "built Sites server entry")
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "commit_sha": commit_sha,
        "source_ref": SOURCE_REF,
        "node_version": EXPECTED_NODE_VERSION,
        "package_lock_sha256": lock_sha256,
        "project_id": project_id,
    }
    manifest_path = (
        project_root / "dist" / ".openai" / "site-candidate.json"
    )
    _atomic_write_json(manifest_path, manifest)

    archive_path.parent.mkdir(parents=True, exist_ok=True)
    runner((str(package_path), str(project_root), str(archive_path)), project_root)
    _require_clean_worktree(project_root, runner)
    _require_regular_file(archive_path, "Sites candidate archive")
    _verify_archive(archive_path, manifest)

    archive_sha256 = _sha256(archive_path)
    receipt_payload = {
        "schema_version": SCHEMA_VERSION,
        "candidate": manifest,
        "archive": {
            "name": archive_path.name,
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
            f"worktree must be clean before packaging: {first_change}"
        )


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


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        with path.open("rb") as source:
            for chunk in iter(lambda: source.read(1024 * 1024), b""):
                digest.update(chunk)
    except OSError as exc:
        raise SiteCandidateError(f"could not hash {path}: {exc}") from exc
    return digest.hexdigest()


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
) -> None:
    try:
        with tarfile.open(archive, "r:gz") as bundle:
            members: dict[str, tarfile.TarInfo] = {}
            for member in bundle.getmembers():
                name = member.name.rstrip("/")
                parts = PurePosixPath(name).parts
                if (
                    not name
                    or name.startswith("/")
                    or ".." in parts
                    or member.issym()
                    or member.islnk()
                ):
                    raise SiteCandidateError(
                        f"unsafe archive member: {member.name}"
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
    except SiteCandidateError:
        raise
    except (OSError, tarfile.TarError) as exc:
        raise SiteCandidateError(
            f"could not validate Sites candidate archive: {exc}"
        ) from exc


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
        required=True,
        help="Absolute path to the trusted Sites package-site.sh helper.",
    )
    parser.add_argument(
        "--archive",
        type=Path,
        required=True,
        help="Output .tar.gz path outside the repository.",
    )
    parser.add_argument(
        "--receipt",
        type=Path,
        required=True,
        help="Output JSON receipt path outside the repository.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        result = prepare_site_candidate(
            args.root,
            args.archive,
            args.receipt,
            args.package_script,
        )
    except SiteCandidateError as exc:
        print(f"site-candidate: {exc}", file=sys.stderr)
        return 2
    print(
        "site candidate ready: "
        f"commit={result.commit_sha} "
        f"archive={result.archive.name} "
        f"sha256={result.archive_sha256} "
        f"receipt={result.receipt.name}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
