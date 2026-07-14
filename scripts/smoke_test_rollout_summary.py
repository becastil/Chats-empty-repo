from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
from typing import Any, Mapping, Sequence


POLICY_FINGERPRINT = f"sha256:{'a' * 64}"
API_COMMIT = "b" * 40
WEB_COMMIT = "c" * 40


class SmokeTestError(RuntimeError):
    """Raised when installed rollout summaries violate the release contract."""


def verify_rollout_summary(
    python: str | Path,
    *,
    environment: Mapping[str, str] | None = None,
) -> tuple[str, ...]:
    python_command = str(Path(python))
    checked: list[str] = []

    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        api = root / "api.md"
        web = root / "web.md"
        _write_bundle(api, _metadata("company/api", commit=API_COMMIT))
        _write_bundle(
            web,
            _metadata(
                "company/web",
                commit=WEB_COMMIT,
                policy_status="fail",
                violations=2,
                dirty_files=1,
                attention_findings=3,
            ),
        )

        report = _json_report(
            python_command,
            (web, api),
            environment=environment,
        )
        _require(report.get("schema_version") == 2, "summary schema changed")
        _require(
            report.get("scope")
            == {
                "readiness": "bundle-reported",
                "freshness_verified": False,
                "shared_policy_verified": True,
                "policy_fingerprint_coverage": 2,
                "git_commit_coverage": 2,
                "policy_versions": [4],
            },
            "rollout scope changed",
        )
        _require(
            report.get("summary")
            == {
                "input_reports": 2,
                "reported_ready_for_ci": 1,
                "reported_remediation_required": 1,
                "policy_pass": 1,
                "policy_fail": 1,
                "clean_worktrees": 1,
                "total_policy_violations": 2,
                "repositories_with_attention": 1,
                "total_attention_findings": 3,
            },
            "rollout totals changed",
        )
        _require("repositories" not in report, "counts-only output exposed details")
        _require_private_values_absent(report, root)
        checked.append("counts-only-summary")

        text_report = _run(
            python_command,
            (web, api),
            output_format="text",
            environment=environment,
            expected_exit_code=0,
        ).stdout
        for expected_line in (
            "Repositories: 2",
            "Bundle-reported ready for CI: 1",
            "Bundle-reported remediation required: 1",
            "Policy: 1 pass / 1 fail / 2 violations",
            "Policy identity: 2/2 fingerprints; shared policy verified",
            "Git: 1 clean worktrees / 1 not clean",
            "Attention: 1 repository / 3 findings",
        ):
            _require(expected_line in text_report, "operator rollout text changed")
        _require_private_values_absent(text_report, root)
        checked.append("shared-policy-remediation")

        detailed = _json_report(
            python_command,
            (web, api),
            details=True,
            environment=environment,
        )
        repositories = detailed.get("repositories", [])
        _require(
            [item.get("repository_id") for item in repositories]
            == ["company/api", "company/web"],
            "explicit repository details changed",
        )
        _require(
            repositories[0].get("policy_fingerprint") == POLICY_FINGERPRINT
            and repositories[0].get("git_commit") == API_COMMIT,
            "explicit rollout identities changed",
        )
        _require(
            repositories[1].get("evidence_file") == str(web),
            "explicit evidence path changed",
        )
        checked.append("explicit-details")

        duplicate = root / "duplicate.md"
        _write_bundle(duplicate, _metadata("company/api", commit=WEB_COMMIT))
        rejected = _run(
            python_command,
            (api, duplicate),
            output_format="json",
            environment=environment,
            expected_exit_code=2,
        )
        _require(not rejected.stdout, "duplicate evidence emitted a report")
        _require(
            "duplicate repository_id across evidence files" in rejected.stderr,
            "duplicate repository ID did not produce its controlled error",
        )
        checked.append("duplicate-rejected")

    return tuple(checked)


def _metadata(
    repository_id: str,
    *,
    commit: str,
    policy_status: str = "pass",
    violations: int = 0,
    dirty_files: int = 0,
    attention_findings: int = 0,
) -> dict[str, Any]:
    clean = dirty_files == 0
    return {
        "schema_version": 2,
        "repository_id": repository_id,
        "readiness": (
            "ready-for-ci"
            if policy_status == "pass" and clean
            else "remediation-required"
        ),
        "policy": {
            "version": 4,
            "fingerprint": POLICY_FINGERPRINT,
            "status": policy_status,
            "rules_checked": 5,
            "violations": violations,
        },
        "git": {
            "is_repo": True,
            "branch": "main",
            "commit": commit,
            "dirty_files": dirty_files,
            "clean": clean,
        },
        "attention_findings": attention_findings,
    }


def _write_bundle(path: Path, metadata: Mapping[str, Any]) -> None:
    path.write_text(
        "# Synthetic rollout evidence\n\n"
        "## Rollout Metadata\n\n```json\n"
        f"{json.dumps(metadata, indent=2, sort_keys=True)}\n```\n",
        encoding="utf-8",
    )


def _json_report(
    python: str,
    evidence: Sequence[Path],
    *,
    details: bool = False,
    environment: Mapping[str, str] | None,
) -> dict[str, Any]:
    completed = _run(
        python,
        evidence,
        output_format="json",
        details=details,
        environment=environment,
        expected_exit_code=0,
    )
    try:
        report = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise SmokeTestError("rollout command did not emit valid JSON") from exc
    if not isinstance(report, dict):
        raise SmokeTestError("rollout command emitted a non-object report")
    return report


def _run(
    python: str,
    evidence: Sequence[Path],
    *,
    output_format: str,
    details: bool = False,
    environment: Mapping[str, str] | None,
    expected_exit_code: int,
) -> subprocess.CompletedProcess[str]:
    command = [
        python,
        "-m",
        "repo_scout.rollout_summary",
        "--format",
        output_format,
    ]
    if details:
        command.append("--details")
    command.extend(str(path) for path in evidence)
    completed = subprocess.run(
        command,
        capture_output=True,
        text=True,
        env=dict(environment) if environment is not None else None,
    )
    if completed.returncode != expected_exit_code:
        detail = completed.stderr.strip() or completed.stdout.strip() or "no output"
        raise SmokeTestError(
            f"rollout command exited {completed.returncode}; "
            f"expected {expected_exit_code}: {detail}"
        )
    return completed


def _require_private_values_absent(
    report: Mapping[str, Any] | str,
    root: Path,
) -> None:
    serialized = (
        json.dumps(report, sort_keys=True)
        if isinstance(report, Mapping)
        else report
    )
    for private_value in (
        "company/api",
        "company/web",
        POLICY_FINGERPRINT,
        API_COMMIT,
        WEB_COMMIT,
        str(root),
    ):
        _require(private_value not in serialized, "counts-only output leaked details")


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise SmokeTestError(message)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Smoke test installed Repo Scout rollout summaries."
    )
    parser.add_argument("--python", default=sys.executable)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        checked = verify_rollout_summary(args.python, environment=os.environ)
    except SmokeTestError as exc:
        print(f"rollout summary smoke test failed: {exc}", file=sys.stderr)
        return 1
    print("rollout summary smoke test passed: " + ", ".join(checked))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
