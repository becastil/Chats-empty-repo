from __future__ import annotations

from collections import Counter
import fnmatch
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

LANGUAGE_BY_FILENAME = {
    "cmakelists.txt": "CMake",
    "dockerfile": "Dockerfile",
    "makefile": "Makefile",
}

LANGUAGE_BY_SUFFIX = {
    ".bash": "Shell",
    ".c": "C",
    ".cc": "C++",
    ".cpp": "C++",
    ".cs": "C#",
    ".css": "CSS",
    ".cxx": "C++",
    ".dart": "Dart",
    ".ex": "Elixir",
    ".exs": "Elixir",
    ".fish": "Shell",
    ".go": "Go",
    ".h": "C/C++ Header",
    ".html": "HTML",
    ".htm": "HTML",
    ".java": "Java",
    ".js": "JavaScript",
    ".json": "JSON",
    ".jsx": "JavaScript",
    ".kt": "Kotlin",
    ".kts": "Kotlin",
    ".less": "Less",
    ".lua": "Lua",
    ".md": "Markdown",
    ".php": "PHP",
    ".ps1": "PowerShell",
    ".py": "Python",
    ".r": "R",
    ".rb": "Ruby",
    ".rs": "Rust",
    ".sass": "Sass",
    ".scala": "Scala",
    ".scss": "SCSS",
    ".sh": "Shell",
    ".sql": "SQL",
    ".svelte": "Svelte",
    ".swift": "Swift",
    ".toml": "TOML",
    ".ts": "TypeScript",
    ".tsx": "TypeScript",
    ".vue": "Vue",
    ".xml": "XML",
    ".yaml": "YAML",
    ".yml": "YAML",
    ".zsh": "Shell",
}


class ScanLimitExceeded(RuntimeError):
    """Raised when a scan exceeds a user-supplied safety limit."""


def scan_project(
    path: str | Path,
    ignore_patterns: Iterable[str] = (),
    max_files: int | None = None,
    include_languages: bool = False,
) -> dict[str, Any]:
    root = Path(path).expanduser().resolve()
    if not root.exists():
        raise FileNotFoundError(f"{root} does not exist")
    if not root.is_dir():
        raise NotADirectoryError(f"{root} is not a directory")
    if max_files is not None and max_files < 1:
        raise ValueError("max_files must be a positive integer")

    normalized_ignores = _normalize_ignore_patterns(ignore_patterns)
    files = _discover_files(root, normalized_ignores, max_files)
    entries = [_file_entry(root, file_path) for file_path in files]
    by_extension = Counter(_extension_label(Path(entry["path"])) for entry in entries)

    file_summary = {
        "total": len(entries),
        "total_bytes": sum(entry["bytes"] for entry in entries),
        "by_extension": dict(sorted(by_extension.items())),
        "largest": sorted(
            entries, key=lambda entry: (-entry["bytes"], entry["path"])
        )[:5],
    }
    if include_languages:
        by_language = Counter(
            _language_label(Path(entry["path"])) for entry in entries
        )
        file_summary["by_language"] = dict(sorted(by_language.items()))

    return {
        "root": str(root),
        "git": _git_summary(root),
        "docs": _doc_summary(root),
        "filters": {"ignored": list(normalized_ignores), "max_files": max_files},
        "files": file_summary,
    }


def _discover_files(
    root: Path, ignore_patterns: tuple[str, ...], max_files: int | None
) -> list[Path]:
    git_files = _git_list_files(root)
    if git_files is not None:
        candidates = (root / relative_path for relative_path in git_files)
    else:
        candidates = _walk_files(root)

    files = []
    for path in candidates:
        if _matches_ignore(path.relative_to(root), ignore_patterns):
            continue

        files.append(path)
        if max_files is not None and len(files) > max_files:
            raise ScanLimitExceeded(
                f"scan exceeded --max-files={max_files}; "
                "raise the limit or add --ignore patterns"
            )

    return sorted(files, key=lambda path: path.as_posix())


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


def _language_label(path: Path) -> str:
    filename_language = LANGUAGE_BY_FILENAME.get(path.name.lower())
    if filename_language is not None:
        return filename_language
    return LANGUAGE_BY_SUFFIX.get(path.suffix.lower(), "Other")


def _normalize_ignore_patterns(ignore_patterns: Iterable[str]) -> tuple[str, ...]:
    return tuple(
        pattern.strip().replace("\\", "/")
        for pattern in ignore_patterns
        if pattern.strip()
    )


def _matches_ignore(relative_path: Path, ignore_patterns: tuple[str, ...]) -> bool:
    path = relative_path.as_posix()
    parts = relative_path.parts

    for pattern in ignore_patterns:
        normalized = pattern.rstrip("/")
        if fnmatch.fnmatchcase(path, normalized):
            return True
        if "/" not in normalized and any(
            fnmatch.fnmatchcase(part, normalized) for part in parts
        ):
            return True
        if path == normalized or path.startswith(f"{normalized}/"):
            return True

    return False


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
