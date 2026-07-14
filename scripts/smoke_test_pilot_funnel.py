from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
from typing import Any, Mapping, Sequence


PILOT_PRICE_USD = 299
TARGET_PILOTS = 3
TARGET_REVENUE_USD = 897
PRIVATE_STANDARD = "Require private service ownership evidence."


class SmokeTestError(RuntimeError):
    """Raised when installed commercial reporting violates its release contract."""


def verify_pilot_funnel(
    python: str | Path,
    *,
    environment: Mapping[str, str] | None = None,
) -> tuple[str, ...]:
    python_command = str(Path(python))
    checked: list[str] = []

    with TemporaryDirectory() as tmp:
        issue_export = Path(tmp) / "pilot-issues.json"
        issue_export.write_text(
            json.dumps(
                [
                    _issue(
                        number=101,
                        title="Website team awaiting purchase",
                        source="Repo Scout website",
                        readiness="Ready to purchase the $299 pilot",
                        criterion="Works across our repositories and CI",
                        labels=(
                            "pilot-lead",
                            "pilot-qualified",
                            "pilot-offered",
                        ),
                    ),
                    _issue(
                        number=102,
                        title="Outreach team with recorded payment",
                        source="Direct outreach",
                        readiness="Ready to purchase the $299 pilot",
                        criterion="The $299 scope and price fit",
                        labels=(
                            "pilot-lead",
                            "pilot-qualified",
                            "pilot-offered",
                            "pilot-paid",
                        ),
                    ),
                ],
                indent=2,
            ),
            encoding="utf-8",
        )

        report = _json_report(
            python_command,
            issue_export,
            environment=environment,
        )
        _require(report.get("schema_version") == 7, "pilot schema changed")
        _require(
            report.get("pricing")
            == {
                "pilot_price_usd": PILOT_PRICE_USD,
                "target_pilots": TARGET_PILOTS,
                "target_revenue_usd": TARGET_REVENUE_USD,
            },
            "default commercial target changed",
        )
        summary = report.get("summary", {})
        _require(summary.get("booked_pilots") == 1, "payment was not booked")
        _require(
            summary.get("booked_revenue_usd") == PILOT_PRICE_USD,
            "booked revenue changed",
        )
        _require(summary.get("remaining_pilots") == 2, "remaining pilots changed")
        _require(
            summary.get("remaining_revenue_usd") == 598,
            "remaining revenue changed",
        )
        _require(
            summary.get("target_attainment_percent") == 33.3,
            "target attainment changed",
        )
        checked.append("commercial-totals")

        _require(
            report.get("by_stage", {}).get("offered") == 1,
            "offer was not kept distinct from payment",
        )
        _require(
            report.get("by_stage", {}).get("paid") == 1,
            "paid stage was not counted",
        )
        website = report.get("by_source", {}).get("website", {})
        outreach = report.get("by_source", {}).get("outreach", {})
        _require(
            website.get("offered_pilots") == 1
            and website.get("booked_pilots") == 0,
            "website offer was counted as revenue",
        )
        _require(
            outreach.get("booked_pilots") == 1
            and outreach.get("booked_revenue_usd") == PILOT_PRICE_USD,
            "outreach payment attribution changed",
        )
        _require(
            summary.get("target_profile_issues") == 2,
            "target-profile qualification changed",
        )
        _require(summary.get("sales_actions") == 1, "sales queue changed")
        _require(not report.get("warnings"), "valid pilot export emitted warnings")
        _require(
            PRIVATE_STANDARD not in json.dumps(report, sort_keys=True),
            "repository-standard free text leaked into the report",
        )
        checked.append("qualified-segmentation")

        text_report = _run(
            python_command,
            issue_export,
            output_format="text",
            environment=environment,
            expected_exit_code=0,
        ).stdout
        for expected_line in (
            "Pilots: 1 booked / 3 target",
            "Revenue: $299 booked / $897 target",
            "Remaining: 2 pilots / $598",
            "Qualification scope: 2 complete / 2 target / 0 review / "
            "0 subset required",
            "Sales actions: 1 open pre-payment deal",
        ):
            _require(expected_line in text_report, "text pilot totals changed")
        _require(
            PRIVATE_STANDARD not in text_report,
            "repository-standard free text leaked into text output",
        )
        checked.append("operator-text")

        pilot_report = Path(tmp) / "pilot-report.json"
        distribution_report = Path(tmp) / "distribution-report.json"
        pilot_report.write_text(
            json.dumps(report, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        distribution = _distribution_report()
        distribution_report.write_text(
            json.dumps(distribution, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        growth = _growth_report(
            python_command,
            distribution_report,
            pilot_report,
            environment=environment,
        )
        growth_summary = growth.get("summary", {})
        for field, expected in (
            ("tracked_pilot_requests", 2),
            ("attributed_pilot_requests", 2),
            ("qualified_pilots", 2),
            ("offered_pilots", 2),
            ("booked_pilots", 1),
            ("booked_revenue_usd", PILOT_PRICE_USD),
            ("target_revenue_usd", TARGET_REVENUE_USD),
            ("target_profile_requests", 2),
        ):
            _require(
                growth_summary.get(field) == expected,
                f"growth summary {field} changed",
            )
        change = growth.get("distribution_change", {})
        _require(
            (
                change.get("primary_artifact_downloads_delta"),
                change.get("portable_downloads_delta"),
                change.get("wheel_downloads_delta"),
            )
            == (6, 2, 4),
            "growth reach movement changed",
        )
        _require(
            growth.get("bottleneck", {}).get("stage") == "pilot_target",
            "growth bottleneck changed",
        )
        _require(not growth.get("warnings"), "valid growth evidence emitted warnings")
        measurement_note = growth.get("measurement_note", "")
        _require(
            "not unique-user or conversion-rate denominators" in measurement_note,
            "growth report lost its conversion-rate boundary",
        )
        _require(
            "Only paid pilot stages count as revenue" in measurement_note,
            "growth report lost its revenue boundary",
        )
        _require(
            PRIVATE_STANDARD not in json.dumps(growth, sort_keys=True),
            "repository-standard free text leaked into growth output",
        )
        checked.append("joined-growth-review")

        growth_text = _run_growth(
            python_command,
            distribution_report,
            pilot_report,
            output_format="text",
            environment=environment,
            expected_exit_code=0,
        ).stdout
        for expected_line in (
            "Reach movement: +6 primary / +2 portable / +4 wheel",
            "Pilot funnel: 2 requests / 2 attributed / 2 qualified / "
            "2 offered / 1 booked",
            "Revenue: $299 booked / $897 target",
            "Qualification scope: 2 complete / 2 target / 0 review / "
            "0 subset required",
            "Bottleneck: pilot_target",
            "Warnings:\n  none",
        ):
            _require(expected_line in growth_text, "operator growth text changed")
        _require(
            PRIVATE_STANDARD not in growth_text,
            "repository-standard free text leaked into growth text",
        )
        checked.append("growth-boundaries")

        distribution["change"]["primary_artifact_downloads_delta"] = 7
        distribution_report.write_text(
            json.dumps(distribution, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        invalid_growth = _run_growth(
            python_command,
            distribution_report,
            pilot_report,
            output_format="json",
            environment=environment,
            expected_exit_code=2,
        )
        _require(not invalid_growth.stdout, "invalid growth evidence emitted a report")
        _require(
            "primary delta does not match portable and wheel"
            in invalid_growth.stderr,
            "invalid reach evidence did not produce its controlled error",
        )
        checked.append("invalid-growth-rejected")

        issue_export.write_text("{}\n", encoding="utf-8")
        invalid = _run(
            python_command,
            issue_export,
            output_format="json",
            environment=environment,
            expected_exit_code=2,
        )
        _require(
            "issue export must be a JSON array" in invalid.stderr,
            "invalid export did not produce its controlled error",
        )
        checked.append("invalid-export-rejected")

    return tuple(checked)


def _distribution_report() -> dict[str, Any]:
    return {
        "schema_version": 2,
        "summary": {"warning_count": 0},
        "change": {
            "baseline_schema_version": 2,
            "primary_artifact_downloads_delta": 6,
            "portable_downloads_delta": 2,
            "wheel_downloads_delta": 4,
            "source_downloads_delta": 0,
            "manifest_downloads_delta": 0,
            "unknown_downloads_delta": 0,
            "new_releases": [],
            "removed_releases": [],
        },
        "warnings": [],
    }


def _issue(
    *,
    number: int,
    title: str,
    source: str,
    readiness: str,
    criterion: str,
    labels: Sequence[str],
) -> dict[str, Any]:
    body = "\n\n".join(
        (
            "### Team size\n\n12",
            "### Repository count\n\n6",
            "### CI provider\n\nGitHub Actions",
            f"### How did you hear about Repo Scout?\n\n{source}",
            f"### Repository standard to enforce\n\n{PRIVATE_STANDARD}",
            f"### Primary purchase criterion\n\n{criterion}",
            f"### Purchase readiness\n\n{readiness}",
        )
    )
    return {
        "number": number,
        "title": title,
        "url": f"https://example.invalid/pilots/{number}",
        "state": "OPEN",
        "updatedAt": "2026-07-13T12:00:00Z",
        "body": body,
        "labels": [{"name": label} for label in labels],
    }


def _json_report(
    python: str,
    issue_export: Path,
    *,
    environment: Mapping[str, str] | None,
) -> dict[str, Any]:
    completed = _run(
        python,
        issue_export,
        output_format="json",
        environment=environment,
        expected_exit_code=0,
    )
    try:
        report = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise SmokeTestError("pilot command did not emit valid JSON") from exc
    if not isinstance(report, dict):
        raise SmokeTestError("pilot command emitted a non-object report")
    return report


def _growth_report(
    python: str,
    distribution_report: Path,
    pilot_report: Path,
    *,
    environment: Mapping[str, str] | None,
) -> dict[str, Any]:
    completed = _run_growth(
        python,
        distribution_report,
        pilot_report,
        output_format="json",
        environment=environment,
        expected_exit_code=0,
    )
    try:
        report = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise SmokeTestError("growth command did not emit valid JSON") from exc
    if not isinstance(report, dict):
        raise SmokeTestError("growth command emitted a non-object report")
    return report


def _run(
    python: str,
    issue_export: Path,
    *,
    output_format: str,
    environment: Mapping[str, str] | None,
    expected_exit_code: int,
) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(
        [
            python,
            "-m",
            "repo_scout.pilot_funnel",
            str(issue_export),
            "--format",
            output_format,
            "--as-of",
            "2026-07-14",
        ],
        capture_output=True,
        text=True,
        env=dict(environment) if environment is not None else None,
    )
    if completed.returncode != expected_exit_code:
        detail = completed.stderr.strip() or completed.stdout.strip() or "no output"
        raise SmokeTestError(
            f"pilot command exited {completed.returncode}; "
            f"expected {expected_exit_code}: {detail}"
        )
    return completed


def _run_growth(
    python: str,
    distribution_report: Path,
    pilot_report: Path,
    *,
    output_format: str,
    environment: Mapping[str, str] | None,
    expected_exit_code: int,
) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(
        [
            python,
            "-m",
            "repo_scout.growth",
            str(distribution_report),
            str(pilot_report),
            "--format",
            output_format,
        ],
        capture_output=True,
        text=True,
        env=dict(environment) if environment is not None else None,
    )
    if completed.returncode != expected_exit_code:
        detail = completed.stderr.strip() or completed.stdout.strip() or "no output"
        raise SmokeTestError(
            f"growth command exited {completed.returncode}; "
            f"expected {expected_exit_code}: {detail}"
        )
    return completed


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise SmokeTestError(message)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Smoke test installed Repo Scout pilot and growth reporting."
    )
    parser.add_argument("--python", default=sys.executable)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        checked = verify_pilot_funnel(args.python, environment=os.environ)
    except SmokeTestError as exc:
        print(f"commercial reporting smoke test failed: {exc}", file=sys.stderr)
        return 1
    print("commercial reporting smoke test passed: " + ", ".join(checked))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
