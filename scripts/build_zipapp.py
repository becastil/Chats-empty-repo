#!/usr/bin/env python3
"""Build the portable Repo Scout zipapp release artifact."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys
import zipapp

from prepare_release import load_project_version


def build_zipapp(project_root: Path, dist_dir: Path) -> Path:
    """Build and return the versioned, executable Repo Scout zipapp."""
    source_dir = project_root / "src"
    if not (source_dir / "repo_scout" / "__init__.py").is_file():
        raise ValueError(f"Repo Scout package source does not exist: {source_dir}")

    version = load_project_version(project_root)
    dist_dir.mkdir(parents=True, exist_ok=True)
    target = dist_dir / f"repo-scout-{version}.pyz"
    zipapp.create_archive(
        source_dir,
        target=target,
        interpreter="/usr/bin/env python3",
        main="repo_scout.cli:main",
        filter=_include_source,
        compressed=True,
    )
    return target


def _include_source(path: Path) -> bool:
    return not (
        path.suffix in {".pyc", ".pyo"}
        or "__pycache__" in path.parts
        or any(part.endswith(".egg-info") for part in path.parts)
    )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build the portable Repo Scout .pyz artifact."
    )
    parser.add_argument(
        "--project-root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help=argparse.SUPPRESS,
    )
    parser.add_argument(
        "--dist",
        type=Path,
        default=Path("dist"),
        help="Artifact directory. Defaults to dist.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        artifact = build_zipapp(args.project_root, args.dist)
    except (OSError, ValueError) as exc:
        print(f"build-zipapp: {exc}", file=sys.stderr)
        return 2
    print(artifact)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
