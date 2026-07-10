#!/usr/bin/env python3
"""Validate release versions and write deterministic artifact checksums."""

from __future__ import annotations

import argparse
import ast
import hashlib
from pathlib import Path
import re
import sys
import tomllib


ARTIFACT_TEMPLATE = (
    "repo_scout-{version}-py3-none-any.whl",
    "repo_scout-{version}.tar.gz",
    "repo-scout-{version}.pyz",
)
CHECKSUMS_NAME = "SHA256SUMS"
SEMVER_TAG = re.compile(r"v[0-9]+\.[0-9]+\.[0-9]+\Z")


class ReleaseError(ValueError):
    """Raised when release inputs do not satisfy the distribution contract."""


def load_project_version(project_root: Path) -> str:
    """Return the version shared by package metadata and runtime code."""
    pyproject_path = project_root / "pyproject.toml"
    init_path = project_root / "src" / "repo_scout" / "__init__.py"

    try:
        with pyproject_path.open("rb") as pyproject_file:
            project_version = tomllib.load(pyproject_file)["project"]["version"]
    except (OSError, KeyError, tomllib.TOMLDecodeError) as exc:
        raise ReleaseError(f"cannot read project version: {exc}") from exc

    try:
        tree = ast.parse(init_path.read_text(encoding="utf-8"), filename=str(init_path))
    except (OSError, SyntaxError) as exc:
        raise ReleaseError(f"cannot read runtime version: {exc}") from exc

    runtime_version: str | None = None
    for statement in tree.body:
        if not isinstance(statement, ast.Assign):
            continue
        if not any(
            isinstance(target, ast.Name) and target.id == "__version__"
            for target in statement.targets
        ):
            continue
        if isinstance(statement.value, ast.Constant) and isinstance(
            statement.value.value, str
        ):
            runtime_version = statement.value.value
            break

    if not isinstance(project_version, str) or not project_version:
        raise ReleaseError("project.version must be a non-empty string")
    if runtime_version is None:
        raise ReleaseError("src/repo_scout/__init__.py must define __version__")
    if project_version != runtime_version:
        raise ReleaseError(
            "version mismatch: "
            f"pyproject.toml has {project_version!r}, runtime has {runtime_version!r}"
        )
    return project_version


def prepare_release(project_root: Path, dist_dir: Path, tag: str) -> Path:
    """Validate a release directory and write its checksum manifest."""
    version = load_project_version(project_root)
    expected_tag = f"v{version}"
    if not SEMVER_TAG.fullmatch(tag):
        raise ReleaseError(f"release tag must use vMAJOR.MINOR.PATCH, got {tag!r}")
    if tag != expected_tag:
        raise ReleaseError(
            f"release tag {tag!r} does not match project version {version!r}"
        )
    if not dist_dir.is_dir():
        raise ReleaseError(f"release directory does not exist: {dist_dir}")

    expected_names = tuple(
        template.format(version=version) for template in ARTIFACT_TEMPLATE
    )
    allowed_names = {*expected_names, CHECKSUMS_NAME}
    actual_names = {path.name for path in dist_dir.iterdir()}
    unexpected = sorted(actual_names - allowed_names)
    if unexpected:
        raise ReleaseError(f"unexpected release artifact(s): {', '.join(unexpected)}")

    artifacts: list[Path] = []
    for name in expected_names:
        artifact = dist_dir / name
        if not artifact.is_file() or artifact.is_symlink():
            raise ReleaseError(f"missing regular release artifact: {name}")
        artifacts.append(artifact)

    manifest = dist_dir / CHECKSUMS_NAME
    lines = [f"{_sha256(artifact)}  {artifact.name}\n" for artifact in artifacts]
    manifest.write_text("".join(lines), encoding="ascii")
    return manifest


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as artifact:
        for chunk in iter(lambda: artifact.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate Repo Scout release artifacts and write SHA256SUMS."
    )
    parser.add_argument("--tag", required=True, help="Git tag, such as v0.2.7")
    parser.add_argument(
        "--dist", type=Path, default=Path("dist"), help="Artifact directory"
    )
    parser.add_argument(
        "--project-root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help=argparse.SUPPRESS,
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        manifest = prepare_release(args.project_root, args.dist, args.tag)
    except ReleaseError as exc:
        print(f"prepare-release: {exc}", file=sys.stderr)
        return 2
    print(manifest)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
