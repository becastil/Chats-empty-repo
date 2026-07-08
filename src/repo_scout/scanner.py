from __future__ import annotations

from collections import Counter
from pathlib import Path
import subprocess
from typing import Any, Iterable


EXPECTED_DOCS = (
    "README.md",
    "PROJECT_STATE.md",
    "ROADMAP.md",
    "CHANGELOG.md",
    "DECISIONS.md",
)

EXCLUDED_DIRS = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    "build",
    "dist",
    "node_modules",
    "venv",
}


def scan_project(path: str | Path) -> dict[str, Any]:
    root = Path(path).expanduser().resolve()
    if not root.exists():
        raise FileNotFoundError(f"{root} does not exist")
    if not root.is_dir():
        raise NotADirectoryError(f"{root} is not a directory")

    files = _discover_files(root)
    entries = [_file_entry(root, file_path) for file_path in files]
    by_extension = Counter(_extension_label(Path(entry["path"])) for entry in entries)

    return {
        "root": str(root),
        "git": _git_summary(root),
        "docs": _doc_summary(root),
        "files": {
            "total": len(entries),
            "total_bytes": sum(entry["bytes"] for entry in entries),
            "by_extension": dict(sorted(by_extension.items())),
            "largest": sorted(
                entries, key=lambda entry: (-entry["bytes"], entry["path"])
            )[:5],
        },
    }


def _discover_files(root: Path) -> list[Path]:
    git_files = _git_list_files(root)
    if git_files is not None:
        return sorted(
            (root / relative_path for relative_path in git_files),
            key=lambda path: path.as_posix(),
        )

    return sorted(_walk_files(root), key=lambda path: path.as_posix())


def _walk_files(root: Path) -> Iterable[Path]:
    for path in root.rglob("*"):
        if any(part in EXCLUDED_DIRS for part in path.relative_to(root).parts):
            continue
        if path.is_file():
            yield path


def _git_list_files(root: Path) -> list[str] | None:
    if _git_root(root) != root:
        return None

    lines = _git_lines(root, "ls-files", "--cached", "--others", "--exclude-standard")
    if lines is None:
        return None
    return [line for line in lines if line]


def _file_entry(root: Path, file_path: Path) -> dict[str, Any]:
    try:
        size = file_path.stat().st_size
    except OSError:
        size = 0

    return {
        "path": file_path.relative_to(root).as_posix(),
        "bytes": size,
    }


def _extension_label(path: Path) -> str:
    suffix = path.suffix.lower()
    return suffix if suffix else "[no extension]"


def _doc_summary(root: Path) -> dict[str, list[str]]:
    present = [doc for doc in EXPECTED_DOCS if (root / doc).is_file()]
    missing = [doc for doc in EXPECTED_DOCS if doc not in present]
    return {"present": present, "missing": missing}


def _git_summary(root: Path) -> dict[str, Any]:
    git_root = _git_root(root)
    if git_root is None:
        return {
            "is_repo": False,
            "root": None,
            "branch": None,
            "dirty_files": 0,
        }

    branch = _git_output(root, "branch", "--show-current") or None
    status = _git_lines(root, "status", "--porcelain") or []
    return {
        "is_repo": True,
        "root": str(git_root),
        "branch": branch,
        "dirty_files": len(status),
    }


def _git_root(root: Path) -> Path | None:
    output = _git_output(root, "rev-parse", "--show-toplevel")
    if output is None:
        return None
    return Path(output).resolve()


def _git_output(root: Path, *args: str) -> str | None:
    lines = _git_lines(root, *args)
    if lines is None:
        return None
    return "\n".join(lines).strip()


def _git_lines(root: Path, *args: str) -> list[str] | None:
    try:
        completed = subprocess.run(
            ["git", "-C", str(root), *args],
            capture_output=True,
            check=True,
            text=True,
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        return None

    return completed.stdout.splitlines()

