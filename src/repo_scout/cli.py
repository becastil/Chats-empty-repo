from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import stat
import sys
from tempfile import NamedTemporaryFile
from typing import Any, Sequence

from .comparison import SnapshotReadError, compare_snapshot_files
from .policy import PolicyError, evaluate_policy, load_policy
from .rollout import (
    RolloutEvidenceError,
    build_rollout_metadata,
    format_rollout_metadata,
    validate_repository_id,
)
from .scanner import (
    DEFAULT_LARGE_FILE_BYTES,
    SNAPSHOT_SCHEMA_VERSION,
    ScanLimitExceeded,
    scan_project,
)
from .version import add_version_argument


OUTPUT_ERROR_EXIT_CODE = 4
ATTENTION_EXIT_CODE = 5
POLICY_EXIT_CODE = 6


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="repo-scout",
        description="Summarize local repository state for reviews and handoffs.",
    )
    add_version_argument(parser)
    parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Project directory to scan. Defaults to the current directory.",
    )
    parser.add_argument(
        "--compare",
        nargs=2,
        metavar=("BEFORE", "AFTER"),
        help="Compare two saved JSON snapshots instead of scanning a directory.",
    )
    parser.add_argument(
        "--output",
        metavar="PATH",
        help="Write the rendered report to PATH instead of stdout.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Allow --output to replace an existing file.",
    )
    parser.add_argument(
        "--fail-on-attention",
        action="store_true",
        help="Exit 5 after reporting when attention findings are present.",
    )
    parser.add_argument(
        "--policy",
        metavar="PATH",
        help="Apply a version-controlled TOML team policy and exit 6 on violations.",
    )
    parser.add_argument(
        "--rollout-checklist",
        action="store_true",
        help=(
            "Append first-repository rollout readiness and handoff actions to "
            "a Markdown policy report."
        ),
    )
    parser.add_argument(
        "--repository-id",
        metavar="ID",
        help=(
            "Stable logical repository name required for rollout evidence."
        ),
    )
    parser.add_argument(
        "--format",
        choices=("text", "json", "markdown"),
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
        "--large-file-bytes",
        type=_positive_int,
        default=DEFAULT_LARGE_FILE_BYTES,
        metavar="BYTES",
        help=(
            "Flag files at or above BYTES in the attention summary. "
            f"Defaults to {DEFAULT_LARGE_FILE_BYTES}."
        ),
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

    if args.force and args.output is None:
        print("repo-scout: --force requires --output", file=sys.stderr)
        return 2

    if args.rollout_checklist and args.compare:
        print(
            "repo-scout: --rollout-checklist cannot be used with --compare",
            file=sys.stderr,
        )
        return 2

    if args.repository_id and not args.rollout_checklist:
        print(
            "repo-scout: --repository-id requires --rollout-checklist",
            file=sys.stderr,
        )
        return 2

    if args.rollout_checklist and not args.policy:
        print(
            "repo-scout: --rollout-checklist requires --policy",
            file=sys.stderr,
        )
        return 2

    if args.rollout_checklist and args.format != "markdown":
        print(
            "repo-scout: --rollout-checklist requires --format markdown",
            file=sys.stderr,
        )
        return 2

    if args.rollout_checklist and args.repository_id is None:
        print(
            "repo-scout: --rollout-checklist requires --repository-id",
            file=sys.stderr,
        )
        return 2

    if args.repository_id is not None:
        try:
            args.repository_id = validate_repository_id(args.repository_id)
        except RolloutEvidenceError as exc:
            print(f"repo-scout: {exc}", file=sys.stderr)
            return 2

    if args.compare and args.fail_on_attention:
        print(
            "repo-scout: --fail-on-attention cannot be used with --compare",
            file=sys.stderr,
        )
        return 2

    if args.compare and args.policy:
        print("repo-scout: --policy cannot be used with --compare", file=sys.stderr)
        return 2

    if args.compare:
        try:
            comparison = compare_snapshot_files(*args.compare)
        except SnapshotReadError as exc:
            print(f"repo-scout: {exc}", file=sys.stderr)
            return 2

        if args.format == "json":
            report = json.dumps(comparison, indent=2, sort_keys=True)
        elif args.format == "markdown":
            report = format_comparison_markdown(comparison)
        else:
            report = format_comparison(comparison)
        return _emit_report(report, args.output, args.force)

    policy = None
    if args.policy:
        try:
            policy = load_policy(args.policy)
        except PolicyError as exc:
            print(f"repo-scout: {exc}", file=sys.stderr)
            return 2

    try:
        snapshot = scan_project(
            args.path,
            ignore_patterns=args.ignore,
            max_files=args.max_files,
            include_languages=args.languages,
            large_file_bytes=args.large_file_bytes,
        )
    except (FileNotFoundError, NotADirectoryError) as exc:
        print(f"repo-scout: {exc}", file=sys.stderr)
        return 2
    except ScanLimitExceeded as exc:
        print(f"repo-scout: {exc}", file=sys.stderr)
        return 3

    if policy is not None:
        snapshot["policy"] = evaluate_policy(snapshot, policy)

    if args.format == "json":
        report = json.dumps(snapshot, indent=2, sort_keys=True)
    elif args.format == "markdown":
        rollout_repository_id = args.repository_id
        report = format_markdown(
            snapshot,
            include_rollout_checklist=args.rollout_checklist,
            rollout_repository_id=rollout_repository_id,
        )
    else:
        report = format_snapshot(snapshot)

    output_exit_code = _emit_report(report, args.output, args.force)
    if output_exit_code != 0:
        return output_exit_code
    if snapshot.get("policy", {}).get("status") == "fail":
        return POLICY_EXIT_CODE
    if args.fail_on_attention and snapshot["attention"]["items"]:
        return ATTENTION_EXIT_CODE
    return 0


def _emit_report(report: str, output: str | None, force: bool) -> int:
    if output is None:
        print(report)
        return 0

    target = Path(output).expanduser()
    if target.exists() and not force:
        print(
            f"repo-scout: output already exists: {target}; pass --force to replace it",
            file=sys.stderr,
        )
        return OUTPUT_ERROR_EXIT_CODE

    content = f"{report.rstrip()}\n"
    if force and target.exists():
        temporary_path: Path | None = None
        try:
            target_mode = stat.S_IMODE(target.stat().st_mode)
            with NamedTemporaryFile(
                "w",
                encoding="utf-8",
                dir=target.parent,
                prefix=f".{target.name}.",
                delete=False,
            ) as temporary:
                temporary.write(content)
                temporary_path = Path(temporary.name)
            os.chmod(temporary_path, target_mode)
            os.replace(temporary_path, target)
        except OSError as exc:
            if temporary_path is not None:
                temporary_path.unlink(missing_ok=True)
            print(f"repo-scout: could not write {target}: {exc}", file=sys.stderr)
            return OUTPUT_ERROR_EXIT_CODE
    else:
        try:
            target.write_text(content, encoding="utf-8")
        except OSError as exc:
            print(f"repo-scout: could not write {target}: {exc}", file=sys.stderr)
            return OUTPUT_ERROR_EXIT_CODE

    print(f"repo-scout: wrote {target}", file=sys.stderr)
    return 0


def format_snapshot(snapshot: dict[str, Any]) -> str:
    git = snapshot["git"]
    docs = snapshot["docs"]
    files = snapshot["files"]

    lines = [
        "Repo Scout Snapshot",
        f"Schema: {SNAPSHOT_SCHEMA_VERSION}",
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

    _append_text_policy(lines, snapshot.get("policy"))
    _append_text_attention(lines, snapshot["attention"])

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


def _append_text_policy(
    lines: list[str], policy: dict[str, Any] | None
) -> None:
    if policy is None:
        return

    lines.append(
        f"Policy: {policy['status']} ({policy['rules_checked']} rules) from {policy['source']}"
    )
    lines.extend(
        f"  ! {violation['message']}" for violation in policy["violations"]
    )


def _append_text_attention(lines: list[str], attention: dict[str, Any]) -> None:
    items = attention["items"]
    if not items:
        lines.append("Attention: none")
        return

    lines.append("Attention:")
    lines.extend(f"  ! {item['message']}" for item in items)


def format_markdown(
    snapshot: dict[str, Any],
    *,
    include_rollout_checklist: bool = False,
    rollout_repository_id: str | None = None,
) -> str:
    git = snapshot["git"]
    docs = snapshot["docs"]
    files = snapshot["files"]
    filters = snapshot["filters"]

    lines = [
        "# Repo Scout Snapshot",
        "",
        f"- **Schema:** {_markdown_code(str(SNAPSHOT_SCHEMA_VERSION))}",
        f"- **Root:** {_markdown_code(snapshot['root'])}",
        f"- **Git:** {_markdown_code(_format_git(git))}",
        f"- **Docs:** {_format_docs(docs)}",
        f"- **Files:** {files['total']} scanned, {files['total_bytes']} bytes",
    ]

    if docs["present"] or docs["missing"]:
        lines.extend(["", "## Project Documents"])
        if docs["present"]:
            lines.append(f"- Present: {', '.join(_markdown_code(doc) for doc in docs['present'])}")
        if docs["missing"]:
            lines.append(f"- Missing: {', '.join(_markdown_code(doc) for doc in docs['missing'])}")

    if (
        filters["ignored"]
        or filters["max_files"] is not None
        or filters["large_file_bytes"] != DEFAULT_LARGE_FILE_BYTES
    ):
        lines.extend(["", "## Scan Filters"])
        if filters["ignored"]:
            lines.append(
                f"- Ignored: {', '.join(_markdown_code(pattern) for pattern in filters['ignored'])}"
            )
        if filters["max_files"] is not None:
            lines.append(f"- Max files: {filters['max_files']}")
        if filters["large_file_bytes"] != DEFAULT_LARGE_FILE_BYTES:
            lines.append(f"- Large-file threshold: {filters['large_file_bytes']} bytes")

    policy = snapshot.get("policy")
    if policy is not None:
        lines.extend(
            [
                "",
                "## Team Policy",
                "",
                f"- Status: {_markdown_code(policy['status'])}",
                f"- Source: {_markdown_code(policy['source'])}",
                f"- Rules checked: {policy['rules_checked']}",
            ]
        )
        if policy["violations"]:
            lines.extend(
                f"- Violation: {violation['message']}"
                for violation in policy["violations"]
            )
        else:
            lines.append("- Violations: none.")

    lines.extend(["", "## Attention Needed"])
    attention_items = snapshot["attention"]["items"]
    if attention_items:
        lines.extend(f"- {item['message']}" for item in attention_items)
    else:
        lines.append("- None detected.")

    extensions = files["by_extension"]
    if extensions:
        lines.extend(["", "## Extensions", "", "| Extension | Files |", "| --- | ---: |"])
        lines.extend(
            f"| {_markdown_code(extension)} | {count} |"
            for extension, count in sorted(
                extensions.items(), key=lambda item: (-item[1], item[0])
            )
        )

    languages = files.get("by_language")
    if languages:
        lines.extend(["", "## Languages", "", "| Language | Files |", "| --- | ---: |"])
        lines.extend(
            f"| {_markdown_cell(language)} | {count} |"
            for language, count in sorted(
                languages.items(), key=lambda item: (-item[1], item[0])
            )
        )

    largest_files = files["largest"]
    if largest_files:
        lines.extend(["", "## Largest Files", "", "| Path | Bytes |", "| --- | ---: |"])
        lines.extend(
            f"| {_markdown_code(entry['path'])} | {entry['bytes']} |"
            for entry in largest_files
        )

    if include_rollout_checklist:
        if rollout_repository_id is None:
            raise ValueError("rollout checklist requires a repository ID")
        _append_rollout_checklist(lines, snapshot, rollout_repository_id)

    return "\n".join(lines)


def _append_rollout_checklist(
    lines: list[str], snapshot: dict[str, Any], repository_id: str
) -> None:
    policy = snapshot.get("policy")
    if policy is None:
        raise ValueError("rollout checklist requires evaluated policy data")

    git = snapshot["git"]
    metadata = build_rollout_metadata(snapshot, repository_id)
    policy_passes = metadata["policy"]["status"] == "pass"
    is_clean_repository = metadata["git"]["clean"]
    readiness = metadata["readiness"]
    violation_count = len(policy["violations"])
    violation_label = "violation" if violation_count == 1 else "violations"
    rule_label = "rule" if policy["rules_checked"] == 1 else "rules"
    attention_count = len(snapshot["attention"]["items"])
    attention_label = "finding" if attention_count == 1 else "findings"

    lines.extend(
        [
            "",
            "## First-Repository Rollout",
            "",
            f"- **Repository ID:** {_markdown_code(repository_id)}",
            f"- **Readiness:** {_markdown_code(readiness)}",
            f"- **Policy evidence:** {_markdown_code(policy['status'])}",
            "",
            "### Automated Readiness",
            "",
            (
                f"- [x] Team policy version {policy['version']} was loaded and "
                f"evaluated across {policy['rules_checked']} {rule_label}."
            ),
        ]
    )

    if policy_passes:
        lines.append("- [x] Repository baseline passes every configured policy rule.")
    else:
        lines.append(
            f"- [ ] Resolve {violation_count} policy {violation_label} before "
            "enabling required CI."
        )

    if git["is_repo"]:
        branch = git["branch"] or "detached HEAD"
        lines.append(
            f"- [x] Git repository detected on {_markdown_code(branch)}."
        )
    else:
        lines.append("- [ ] Initialize Git before starting the rollout.")

    if is_clean_repository:
        lines.append("- [x] Git worktree was clean at scan time.")
    elif git["is_repo"]:
        lines.append(
            f"- [ ] Resolve {git['dirty_files']} changed files before the "
            "rollout handoff."
        )
    else:
        lines.append("- [ ] A clean Git worktree could not be verified.")

    if git["commit"] is not None:
        lines.append(
            f"- [x] Git commit identity recorded as {_markdown_code(git['commit'])}."
        )
    elif git["is_repo"]:
        lines.append("- [ ] Create an initial Git commit before the rollout handoff.")

    if attention_count:
        lines.append(
            f"- [ ] Review {attention_count} additional attention "
            f"{attention_label}."
        )
    else:
        lines.append("- [x] No additional attention findings were detected.")

    lines.extend(
        [
            "",
            "### Team Handoff",
            "",
            "- [ ] Commit the team policy and verified Repo Scout workflow in one reviewed pull request.",
            "- [ ] Assign an engineering owner for policy exceptions and remediation.",
            "- [ ] Require the Repo Scout check after the baseline passes.",
            "- [ ] Record one week of CI evidence before enrolling another repository.",
            "- [ ] Select the next repository and reuse the approved policy pack.",
            "",
            "## Rollout Metadata",
            "",
            "```json",
            format_rollout_metadata(metadata),
            "```",
        ]
    )


def format_comparison(comparison: dict[str, Any]) -> str:
    before = comparison["before"]
    after = comparison["after"]
    files = comparison["files"]
    lines = [
        "Repo Scout Comparison",
        f"Status: {comparison['status']}",
        f"Schema: {_format_value_change(comparison['schema_version'])}",
        f"Before: {before['label']}",
        f"After: {after['label']}",
        f"Files: {_format_numeric_change(files['total'])}",
        f"Bytes: {_format_numeric_change(files['total_bytes'])}",
    ]

    if comparison["status"] == "unchanged":
        lines.append("No changes detected.")
        return "\n".join(lines)

    _append_text_counter_change(lines, "Extensions", files["by_extension"])
    if "by_language" in files:
        _append_text_counter_change(lines, "Languages", files["by_language"])
    _append_text_path_change(lines, files.get("paths"))

    docs = comparison["docs"]
    doc_lines = []
    for section in ("present", "missing"):
        if docs[section]["added"]:
            doc_lines.append(
                f"  {section.title()} added: {', '.join(docs[section]['added'])}"
            )
        if docs[section]["removed"]:
            doc_lines.append(
                f"  {section.title()} removed: {', '.join(docs[section]['removed'])}"
            )
    if doc_lines:
        lines.append("Documents:")
        lines.extend(doc_lines)

    git = comparison["git"]
    if git["is_repo"]["changed"] or git["branch"]["changed"] or git["dirty_files"]["delta"]:
        lines.append("Git:")
        if git["is_repo"]["changed"]:
            lines.append(f"  Repository: {_format_value_change(git['is_repo'])}")
        if git["branch"]["changed"]:
            lines.append(f"  Branch: {_format_value_change(git['branch'])}")
        if git["dirty_files"]["delta"]:
            lines.append(
                f"  Changed files: {_format_numeric_change(git['dirty_files'])}"
            )

    attention = comparison["attention"]
    if attention["status"]["changed"] or attention["item_count"]["delta"]:
        lines.append("Attention:")
        if attention["status"]["changed"]:
            lines.append(f"  Status: {_format_value_change(attention['status'])}")
        if attention["item_count"]["delta"]:
            lines.append(
                f"  Items: {_format_numeric_change(attention['item_count'])}"
            )

    return "\n".join(lines)


def format_comparison_markdown(comparison: dict[str, Any]) -> str:
    before = comparison["before"]
    after = comparison["after"]
    files = comparison["files"]
    lines = [
        "# Repo Scout Comparison",
        "",
        f"- **Status:** {_markdown_code(comparison['status'])}",
        f"- **Schema:** {_markdown_value_change(comparison['schema_version'])}",
        f"- **Before:** {_markdown_code(before['label'])}",
        f"- **After:** {_markdown_code(after['label'])}",
        "",
        "## File Totals",
        "",
        "| Metric | Before | After | Delta |",
        "| --- | ---: | ---: | ---: |",
        _markdown_numeric_row("Files", files["total"]),
        _markdown_numeric_row("Bytes", files["total_bytes"]),
    ]

    if comparison["status"] == "unchanged":
        lines.extend(["", "No changes detected."])
        return "\n".join(lines)

    if comparison["schema_version"]["changed"]:
        lines.extend(
            [
                "",
                "## Schema Change",
                "",
                f"- Snapshot schema: {_markdown_value_change(comparison['schema_version'])}",
            ]
        )

    _append_markdown_counter_change(
        lines, "Extension Changes", files["by_extension"]
    )
    if "by_language" in files:
        _append_markdown_counter_change(lines, "Language Changes", files["by_language"])
    _append_markdown_path_change(lines, files.get("paths"))

    docs = comparison["docs"]
    doc_rows = []
    for section in ("present", "missing"):
        for path in docs[section]["added"]:
            doc_rows.append(f"- {section.title()} added: {_markdown_code(path)}")
        for path in docs[section]["removed"]:
            doc_rows.append(f"- {section.title()} removed: {_markdown_code(path)}")
    if doc_rows:
        lines.extend(["", "## Document Changes", ""])
        lines.extend(doc_rows)

    git = comparison["git"]
    if git["is_repo"]["changed"] or git["branch"]["changed"] or git["dirty_files"]["delta"]:
        lines.extend(["", "## Git Changes", ""])
        if git["is_repo"]["changed"]:
            lines.append(f"- Repository: {_markdown_value_change(git['is_repo'])}")
        if git["branch"]["changed"]:
            lines.append(f"- Branch: {_markdown_value_change(git['branch'])}")
        if git["dirty_files"]["delta"]:
            lines.append(
                f"- Changed files: {_markdown_numeric_change(git['dirty_files'])}"
            )

    attention = comparison["attention"]
    if attention["status"]["changed"] or attention["item_count"]["delta"]:
        lines.extend(["", "## Attention Changes", ""])
        if attention["status"]["changed"]:
            lines.append(f"- Status: {_markdown_value_change(attention['status'])}")
        if attention["item_count"]["delta"]:
            lines.append(
                f"- Items: {_markdown_numeric_change(attention['item_count'])}"
            )

    return "\n".join(lines)


def _append_text_counter_change(
    lines: list[str], title: str, change: dict[str, Any]
) -> None:
    if not (change["added"] or change["removed"] or change["changed"]):
        return
    lines.append(f"{title}:")
    lines.extend(f"  Added: {name} ({count})" for name, count in change["added"].items())
    lines.extend(f"  Removed: {name} ({count})" for name, count in change["removed"].items())
    lines.extend(
        f"  Changed: {name} ({_format_numeric_change(values)})"
        for name, values in change["changed"].items()
    )


def _append_text_path_change(
    lines: list[str], change: dict[str, Any] | None
) -> None:
    if not change or not (change["added"] or change["removed"]):
        return
    lines.append("Paths:")
    if change["added"]:
        lines.append(f"  Added ({change['added_count']}): {', '.join(change['added'])}")
    if change["removed"]:
        lines.append(
            f"  Removed ({change['removed_count']}): {', '.join(change['removed'])}"
        )
    if change["truncated"]:
        lines.append(f"  Details capped at {change['limit']} paths.")


def _append_markdown_counter_change(
    lines: list[str], title: str, change: dict[str, Any]
) -> None:
    rows = []
    for name, count in change["added"].items():
        rows.append((name, 0, count, count))
    for name, count in change["removed"].items():
        rows.append((name, count, 0, -count))
    for name, values in change["changed"].items():
        rows.append((name, values["before"], values["after"], values["delta"]))
    if not rows:
        return

    lines.extend(
        ["", f"## {title}", "", "| Name | Before | After | Delta |", "| --- | ---: | ---: | ---: |"]
    )
    lines.extend(
        f"| {_markdown_code(name)} | {before} | {after} | {_signed(delta)} |"
        for name, before, after, delta in sorted(rows)
    )


def _append_markdown_path_change(
    lines: list[str], change: dict[str, Any] | None
) -> None:
    if not change or not (change["added"] or change["removed"]):
        return
    lines.extend(["", "## Changed Paths", ""])
    if change["added"]:
        paths = ", ".join(_markdown_code(path) for path in change["added"])
        lines.append(f"- Added ({change['added_count']}): {paths}")
    if change["removed"]:
        paths = ", ".join(_markdown_code(path) for path in change["removed"])
        lines.append(f"- Removed ({change['removed_count']}): {paths}")
    if change["truncated"]:
        lines.append(f"- Details capped at {change['limit']} paths.")


def _format_numeric_change(change: dict[str, int]) -> str:
    return f"{change['before']} -> {change['after']} ({_signed(change['delta'])})"


def _format_value_change(change: dict[str, Any]) -> str:
    return f"{change['before']} -> {change['after']}"


def _markdown_numeric_row(label: str, change: dict[str, int]) -> str:
    return f"| {label} | {change['before']} | {change['after']} | {_signed(change['delta'])} |"


def _markdown_numeric_change(change: dict[str, int]) -> str:
    return f"{change['before']} -> {change['after']} ({_signed(change['delta'])})"


def _markdown_value_change(change: dict[str, Any]) -> str:
    return f"{_markdown_code(str(change['before']))} -> {_markdown_code(str(change['after']))}"


def _signed(value: int) -> str:
    return f"+{value}" if value > 0 else str(value)


def _markdown_code(value: str) -> str:
    escaped = value.replace("`", "\\`")
    return f"`{escaped}`"


def _markdown_cell(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")


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
