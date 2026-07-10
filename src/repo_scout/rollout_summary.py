from __future__ import annotations

import argparse
import json
import sys
from typing import Any, Sequence

from .rollout import RolloutEvidenceError, load_rollout_metadata


SUMMARY_SCHEMA_VERSION = 1


def build_rollout_summary(
    reports: Sequence[tuple[str, dict[str, Any]]],
    *,
    include_details: bool = False,
) -> dict[str, Any]:
    if not reports:
        raise RolloutEvidenceError("at least one rollout evidence file is required")

    repositories: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for evidence_file, metadata in sorted(
        reports,
        key=lambda item: (item[1]["repository_id"], item[0]),
    ):
        repository_id = metadata["repository_id"]
        if repository_id in seen_ids:
            raise RolloutEvidenceError(
                f"duplicate repository_id across evidence files: {repository_id}"
            )
        seen_ids.add(repository_id)
        repositories.append(
            {
                "repository_id": repository_id,
                "evidence_file": evidence_file,
                "readiness": metadata["readiness"],
                "policy_version": metadata["policy"]["version"],
                "policy_status": metadata["policy"]["status"],
                "rules_checked": metadata["policy"]["rules_checked"],
                "policy_violations": metadata["policy"]["violations"],
                "git_is_repo": metadata["git"]["is_repo"],
                "git_branch": metadata["git"]["branch"],
                "git_dirty_files": metadata["git"]["dirty_files"],
                "git_clean": metadata["git"]["clean"],
                "attention_findings": metadata["attention_findings"],
            }
        )

    report: dict[str, Any] = {
        "schema_version": SUMMARY_SCHEMA_VERSION,
        "scope": {
            "readiness": "bundle-reported",
            "freshness_verified": False,
            "shared_policy_verified": False,
            "policy_versions": sorted(
                {repository["policy_version"] for repository in repositories}
            ),
        },
        "summary": {
            "input_reports": len(repositories),
            "reported_ready_for_ci": sum(
                repository["readiness"] == "ready-for-ci"
                for repository in repositories
            ),
            "reported_remediation_required": sum(
                repository["readiness"] == "remediation-required"
                for repository in repositories
            ),
            "policy_pass": sum(
                repository["policy_status"] == "pass"
                for repository in repositories
            ),
            "policy_fail": sum(
                repository["policy_status"] == "fail"
                for repository in repositories
            ),
            "clean_worktrees": sum(
                repository["git_clean"] for repository in repositories
            ),
            "total_policy_violations": sum(
                repository["policy_violations"] for repository in repositories
            ),
            "repositories_with_attention": sum(
                repository["attention_findings"] > 0
                for repository in repositories
            ),
            "total_attention_findings": sum(
                repository["attention_findings"] for repository in repositories
            ),
        },
    }
    if include_details:
        report["repositories"] = repositories
    return report


def format_rollout_summary(report: dict[str, Any]) -> str:
    summary = report["summary"]
    violation_label = (
        "violation"
        if summary["total_policy_violations"] == 1
        else "violations"
    )
    attention_repository_label = (
        "repository"
        if summary["repositories_with_attention"] == 1
        else "repositories"
    )
    attention_finding_label = (
        "finding" if summary["total_attention_findings"] == 1 else "findings"
    )
    lines = [
        "Repo Scout Pilot Rollout",
        "Scope: bundle-reported; freshness and shared policy are not verified",
        f"Repositories: {summary['input_reports']}",
        f"Bundle-reported ready for CI: {summary['reported_ready_for_ci']}",
        (
            "Bundle-reported remediation required: "
            f"{summary['reported_remediation_required']}"
        ),
        (
            f"Policy: {summary['policy_pass']} pass / "
            f"{summary['policy_fail']} fail / "
            f"{summary['total_policy_violations']} {violation_label}"
        ),
        (
            f"Git: {summary['clean_worktrees']} clean worktrees / "
            f"{summary['input_reports'] - summary['clean_worktrees']} not clean"
        ),
        (
            f"Attention: {summary['repositories_with_attention']} "
            f"{attention_repository_label} / "
            f"{summary['total_attention_findings']} {attention_finding_label}"
        ),
    ]
    repositories = report.get("repositories")
    if repositories is None:
        return "\n".join(lines)

    lines.append("Repository details:")
    for repository in repositories:
        git_status = _format_git_status(repository)
        repository_violation_label = (
            "violation" if repository["policy_violations"] == 1 else "violations"
        )
        repository_attention_label = (
            "finding" if repository["attention_findings"] == 1 else "findings"
        )
        lines.append(
            f"  {repository['repository_id']}: {repository['readiness']}; "
            f"policy {repository['policy_status']} "
            f"({repository['policy_violations']} {repository_violation_label}); "
            f"{git_status}; {repository['attention_findings']} attention "
            f"{repository_attention_label}"
        )
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="repo-scout-rollout",
        description="Summarize reported readiness from rollout evidence bundles.",
    )
    parser.add_argument(
        "evidence",
        nargs="+",
        metavar="REPORT",
        help="Markdown rollout evidence file. Provide one or more.",
    )
    parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Output format. Defaults to text.",
    )
    parser.add_argument(
        "--details",
        action="store_true",
        help="Include repository IDs, branches, and evidence paths in output.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        reports = [
            (source, load_rollout_metadata(source)) for source in args.evidence
        ]
        summary = build_rollout_summary(reports, include_details=args.details)
    except RolloutEvidenceError as exc:
        print(f"repo-scout-rollout: {exc}", file=sys.stderr)
        return 2

    if args.format == "json":
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print(format_rollout_summary(summary))
    return 0


def _format_git_status(repository: dict[str, Any]) -> str:
    if not repository["git_is_repo"]:
        return "not a Git repository"
    branch = repository["git_branch"] or "detached HEAD"
    if repository["git_clean"]:
        return f"Git clean on {branch}"
    changed = repository["git_dirty_files"]
    suffix = "file" if changed == 1 else "files"
    return f"Git {changed} changed {suffix} on {branch}"


if __name__ == "__main__":
    raise SystemExit(main())
