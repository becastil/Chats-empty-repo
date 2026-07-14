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
    """Raised when installed pilot reporting violates its release contract."""


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


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise SmokeTestError(message)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Smoke test the installed Repo Scout pilot funnel."
    )
    parser.add_argument("--python", default=sys.executable)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        checked = verify_pilot_funnel(args.python, environment=os.environ)
    except SmokeTestError as exc:
        print(f"pilot funnel smoke test failed: {exc}", file=sys.stderr)
        return 1
    print("pilot funnel smoke test passed: " + ", ".join(checked))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
