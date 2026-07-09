from __future__ import annotations

import argparse
import json
import sys
from typing import Any, Sequence

from .scanner import ScanLimitExceeded, scan_project


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="repo-scout",
        description="Summarize local repository state for reviews and handoffs.",
    )
    parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Project directory to scan. Defaults to the current directory.",
    )
    parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Output format. Defaults to text.",
    )
    parser.add_argument(
        "--ignore",
        action="append",
        default=[],
        metavar="PATTERN",
        help=(
            "Ignore files or directories matching PATTERN. Can be used more than once."
        ),
    )
    parser.add_argument(
        "--max-files",
        type=_positive_int,
        metavar="COUNT",
        help="Stop scanning if more than COUNT files match the scan filters.",
    )
    parser.add_argument(
        "--languages",
        action="store_true",
        help="Include a best-effort file count grouped by language name.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        snapshot = scan_project(
            args.path,
            ignore_patterns=args.ignore,
            max_files=args.max_files,
            include_languages=args.languages,
        )
    except (FileNotFoundError, NotADirectoryError) as exc:
        print(f"repo-scout: {exc}", file=sys.stderr)
        return 2
    except ScanLimitExceeded as exc:
        print(f"repo-scout: {exc}", file=sys.stderr)
        return 3

    if args.format == "json":
        print(json.dumps(snapshot, indent=2, sort_keys=True))
    else:
        print(format_snapshot(snapshot))

    return 0


def format_snapshot(snapshot: dict[str, Any]) -> str:
    git = snapshot["git"]
    docs = snapshot["docs"]
    files = snapshot["files"]

    lines = [
        "Repo Scout Snapshot",
        f"Root: {snapshot['root']}",
        f"Git: {_format_git(git)}",
        f"Docs: {_format_docs(docs)}",
        f"Files: {files['total']} scanned, {files['total_bytes']} bytes",
    ]

    ignored = snapshot["filters"]["ignored"]
    if ignored:
        lines.append(f"Ignored: {', '.join(ignored)}")

    max_files = snapshot["filters"]["max_files"]
    if max_files is not None:
        lines.append(f"Max files: {max_files}")

    extensions = files["by_extension"]
    if extensions:
        lines.append("Extensions:")
        for extension, count in sorted(
            extensions.items(), key=lambda item: (-item[1], item[0])
        ):
            lines.append(f"  {extension}: {count}")

    languages = files.get("by_language")
    if languages:
        lines.append("Languages:")
        for language, count in sorted(
            languages.items(), key=lambda item: (-item[1], item[0])
        ):
            lines.append(f"  {language}: {count}")

    largest_files = files["largest"]
    if largest_files:
        lines.append("Largest files:")
        for entry in largest_files:
            lines.append(f"  {entry['path']} ({entry['bytes']} bytes)")

    return "\n".join(lines)


def _format_git(git: dict[str, Any]) -> str:
    if not git["is_repo"]:
        return "not a Git repository"

    branch = git["branch"] or "detached"
    dirty_files = git["dirty_files"]
    if dirty_files == 0:
        return f"{branch}, clean"

    suffix = "file" if dirty_files == 1 else "files"
    return f"{branch}, {dirty_files} changed {suffix}"


def _format_docs(docs: dict[str, list[str]]) -> str:
    present = len(docs["present"])
    missing = len(docs["missing"])
    return f"{present} present, {missing} missing"


def _positive_int(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be a positive integer") from exc

    if parsed < 1:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return parsed
