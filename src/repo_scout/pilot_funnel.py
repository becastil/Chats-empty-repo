from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
from pathlib import Path
import sys
from typing import Any, Sequence, TextIO


SCHEMA_VERSION = 1
DEFAULT_PILOT_PRICE_USD = 299
DEFAULT_TARGET_PILOTS = 3

STAGE_LABELS = (
    "pilot-lead",
    "pilot-qualified",
    "pilot-offered",
    "pilot-paid",
    "pilot-active",
    "pilot-converted",
)
LOST_LABEL = "pilot-lost"
KNOWN_LABELS = set(STAGE_LABELS) | {LOST_LABEL}
DISPLAY_STAGES = (
    "lead",
    "qualified",
    "offered",
    "paid",
    "active",
    "converted",
    "lost",
    "conflict",
    "untracked",
)


class FunnelInputError(ValueError):
    """Raised when a pilot issue export cannot be analyzed safely."""


@dataclass(frozen=True)
class PilotIssue:
    number: int
    title: str
    url: str
    labels: frozenset[str]


def build_funnel(
    payload: Any,
    pilot_price_usd: int = DEFAULT_PILOT_PRICE_USD,
    target_pilots: int = DEFAULT_TARGET_PILOTS,
) -> dict[str, Any]:
    if not isinstance(payload, list):
        raise FunnelInputError("issue export must be a JSON array")
    if pilot_price_usd < 1:
        raise FunnelInputError("pilot price must be a positive integer")
    if target_pilots < 1:
        raise FunnelInputError("target pilots must be a positive integer")

    by_stage = {stage: 0 for stage in DISPLAY_STAGES}
    deals: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []
    ignored_issues = 0
    booked_pilots = 0
    annual_conversions = 0
    lost_pilots = 0
    seen_issue_numbers: set[int] = set()
    issues: list[PilotIssue] = []

    for index, raw_issue in enumerate(payload):
        issue = _parse_issue(raw_issue, index)
        if issue.number in seen_issue_numbers:
            raise FunnelInputError(
                f"issue export contains duplicate issue number: {issue.number}"
            )
        seen_issue_numbers.add(issue.number)
        issues.append(issue)

    for issue in sorted(issues, key=lambda item: item.number):
        pilot_labels = {label for label in issue.labels if label.startswith("pilot-")}
        known_labels = pilot_labels & KNOWN_LABELS
        unknown_labels = sorted(pilot_labels - KNOWN_LABELS)

        if not pilot_labels:
            ignored_issues += 1
            continue

        for label in unknown_labels:
            warnings.append(
                _warning(
                    issue,
                    "unknown_pilot_label",
                    f"Unknown pilot label: {label}.",
                    labels=[label],
                )
            )

        present_stages = [
            position
            for position, label in enumerate(STAGE_LABELS)
            if label in known_labels
        ]
        furthest_stage = max(present_stages, default=-1)
        has_lost = LOST_LABEL in known_labels
        has_converted = STAGE_LABELS[-1] in known_labels

        if has_lost and has_converted:
            stage = "conflict"
            warnings.append(
                _warning(
                    issue,
                    "conflicting_terminal_labels",
                    "Issue is labeled as both converted and lost.",
                    labels=[STAGE_LABELS[-1], LOST_LABEL],
                )
            )
        elif has_lost:
            stage = "lost"
        elif furthest_stage >= 0:
            stage = STAGE_LABELS[furthest_stage].removeprefix("pilot-")
        else:
            stage = "untracked"
            warnings.append(
                _warning(
                    issue,
                    "missing_known_stage",
                    "Issue has pilot labels but no recognized funnel stage.",
                    labels=unknown_labels,
                )
            )

        if furthest_stage >= 0:
            required_labels = set(STAGE_LABELS[: furthest_stage + 1])
            missing_labels = sorted(required_labels - known_labels)
            if missing_labels:
                warnings.append(
                    _warning(
                        issue,
                        "missing_prior_stage",
                        "Later funnel stage is present without all prior labels.",
                        labels=missing_labels,
                    )
                )

        by_stage[stage] += 1
        is_booked = furthest_stage >= STAGE_LABELS.index("pilot-paid")
        booked_pilots += int(is_booked)
        annual_conversions += int(has_converted)
        lost_pilots += int(has_lost)
        deals.append(
            {
                "number": issue.number,
                "title": issue.title,
                "url": issue.url,
                "stage": stage,
                "booked": is_booked,
            }
        )

    booked_revenue = booked_pilots * pilot_price_usd
    target_revenue = target_pilots * pilot_price_usd
    remaining_pilots = max(0, target_pilots - booked_pilots)
    return {
        "schema_version": SCHEMA_VERSION,
        "pricing": {
            "pilot_price_usd": pilot_price_usd,
            "target_pilots": target_pilots,
            "target_revenue_usd": target_revenue,
        },
        "summary": {
            "input_issues": len(payload),
            "tracked_issues": len(deals),
            "ignored_issues": ignored_issues,
            "booked_pilots": booked_pilots,
            "booked_revenue_usd": booked_revenue,
            "remaining_pilots": remaining_pilots,
            "remaining_revenue_usd": remaining_pilots * pilot_price_usd,
            "target_attainment_percent": round(
                booked_pilots / target_pilots * 100, 1
            ),
            "annual_conversions": annual_conversions,
            "lost_pilots": lost_pilots,
        },
        "by_stage": by_stage,
        "deals": sorted(deals, key=lambda deal: deal["number"]),
        "warnings": warnings,
    }


def format_funnel(report: dict[str, Any]) -> str:
    summary = report["summary"]
    pricing = report["pricing"]
    lines = [
        "Repo Scout Pilot Funnel",
        (
            f"Pilots: {summary['booked_pilots']} booked / "
            f"{pricing['target_pilots']} target"
        ),
        (
            f"Revenue: ${summary['booked_revenue_usd']} booked / "
            f"${pricing['target_revenue_usd']} target"
        ),
        (
            f"Remaining: {summary['remaining_pilots']} pilots / "
            f"${summary['remaining_revenue_usd']}"
        ),
        f"Annual conversions: {summary['annual_conversions']}",
        f"Lost pilots: {summary['lost_pilots']}",
        "Stages:",
    ]
    for stage in DISPLAY_STAGES:
        lines.append(f"  {stage}: {report['by_stage'][stage]}")

    lines.append("Deals:")
    if report["deals"]:
        for deal in report["deals"]:
            suffix = f" {deal['url']}" if deal["url"] else ""
            lines.append(
                f"  #{deal['number']} [{deal['stage']}] {deal['title']}{suffix}"
            )
    else:
        lines.append("  none")

    lines.append("Warnings:")
    if report["warnings"]:
        for warning in report["warnings"]:
            lines.append(
                f"  #{warning['issue_number']} {warning['kind']}: "
                f"{warning['message']}"
            )
    else:
        lines.append("  none")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="repo-scout-pilot",
        description="Summarize Repo Scout founding-pilot issues from GitHub JSON.",
    )
    parser.add_argument(
        "input",
        nargs="?",
        default="-",
        help="GitHub issue JSON file, or - for stdin. Defaults to stdin.",
    )
    parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Output format. Defaults to text.",
    )
    parser.add_argument(
        "--pilot-price",
        type=_positive_int,
        default=DEFAULT_PILOT_PRICE_USD,
        metavar="USD",
        help=f"Pilot price in whole USD. Defaults to {DEFAULT_PILOT_PRICE_USD}.",
    )
    parser.add_argument(
        "--target-pilots",
        type=_positive_int,
        default=DEFAULT_TARGET_PILOTS,
        metavar="COUNT",
        help=f"Paid-pilot target. Defaults to {DEFAULT_TARGET_PILOTS}.",
    )
    return parser


def main(argv: Sequence[str] | None = None, stdin: TextIO | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    input_stream = stdin or sys.stdin

    try:
        payload = _read_payload(args.input, input_stream)
        report = build_funnel(payload, args.pilot_price, args.target_pilots)
    except FunnelInputError as exc:
        print(f"repo-scout-pilot: {exc}", file=sys.stderr)
        return 2

    if args.format == "json":
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(format_funnel(report))
    return 0


def _read_payload(source: str, stdin: TextIO) -> Any:
    try:
        content = stdin.read() if source == "-" else Path(source).read_text("utf-8")
    except OSError as exc:
        raise FunnelInputError(f"could not read {source}: {exc}") from exc

    try:
        return json.loads(content)
    except json.JSONDecodeError as exc:
        raise FunnelInputError(
            f"invalid JSON at line {exc.lineno}, column {exc.colno}: {exc.msg}"
        ) from exc


def _parse_issue(raw_issue: Any, index: int) -> PilotIssue:
    location = f"issue export item {index}"
    if not isinstance(raw_issue, dict):
        raise FunnelInputError(f"{location} must be an object")

    number = raw_issue.get("number")
    if not isinstance(number, int) or isinstance(number, bool) or number < 1:
        raise FunnelInputError(f"{location}.number must be a positive integer")

    title = raw_issue.get("title")
    if not isinstance(title, str) or not title.strip():
        raise FunnelInputError(f"{location}.title must be a non-empty string")

    url = raw_issue.get("url", "")
    if not isinstance(url, str):
        raise FunnelInputError(f"{location}.url must be a string")

    raw_labels = raw_issue.get("labels")
    if not isinstance(raw_labels, list):
        raise FunnelInputError(f"{location}.labels must be an array")
    labels: set[str] = set()
    for label_index, raw_label in enumerate(raw_labels):
        if isinstance(raw_label, str):
            name = raw_label
        elif isinstance(raw_label, dict):
            name = raw_label.get("name")
        else:
            name = None
        if not isinstance(name, str) or not name:
            raise FunnelInputError(
                f"{location}.labels[{label_index}] must contain a non-empty name"
            )
        labels.add(name)

    return PilotIssue(number, title.strip(), url, frozenset(labels))


def _warning(
    issue: PilotIssue,
    kind: str,
    message: str,
    labels: list[str],
) -> dict[str, Any]:
    return {
        "issue_number": issue.number,
        "kind": kind,
        "message": message,
        "labels": labels,
    }


def _positive_int(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be a positive integer") from exc
    if parsed < 1:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return parsed


if __name__ == "__main__":
    raise SystemExit(main())
