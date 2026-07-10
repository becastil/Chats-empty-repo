from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import date, datetime, timezone
import json
from pathlib import Path
import re
import sys
from typing import Any, Sequence, TextIO


SCHEMA_VERSION = 5
DEFAULT_PILOT_PRICE_USD = 299
DEFAULT_TARGET_PILOTS = 3
DEFAULT_STALE_DAYS = 7

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
FOLLOW_UP_STAGES = {"lead", "qualified", "offered"}
SOURCE_FIELD_HEADING = "How did you hear about Repo Scout?"
SOURCE_OPTIONS = (
    ("github", "GitHub repository or release"),
    ("website", "Repo Scout website"),
    ("outreach", "Direct outreach"),
    ("referral", "Teammate or referral"),
    ("search", "Search"),
    ("social", "Social media or community"),
    ("other", "Other"),
)
SOURCE_BY_ANSWER = {answer: source for source, answer in SOURCE_OPTIONS}
ATTRIBUTED_SOURCES = tuple(source for source, _ in SOURCE_OPTIONS)
SOURCE_KEYS = (*ATTRIBUTED_SOURCES, "unattributed", "unknown")
READINESS_FIELD_HEADING = "Purchase readiness"
READINESS_OPTIONS = (
    ("ready", "Ready to purchase the $299 pilot"),
    ("needs_approval", "Need internal approval for $299"),
    ("exploring", "Exploring before requesting budget"),
)
READINESS_BY_ANSWER = {
    answer: readiness for readiness, answer in READINESS_OPTIONS
}
DECLARED_READINESS = tuple(readiness for readiness, _ in READINESS_OPTIONS)
READINESS_KEYS = (*DECLARED_READINESS, "unattributed", "unknown")
SALES_PRIORITY_BY_READINESS = {
    "ready": 1,
    "needs_approval": 2,
    "exploring": 3,
    "unattributed": 4,
    "unknown": 4,
}
SALES_STAGE_ORDER = {"offered": 0, "qualified": 1, "lead": 2}
SALES_ACTIONS = {
    "ready": {
        "lead": "Qualify the team and send the ${pilot_price_usd} pilot terms.",
        "qualified": "Send the ${pilot_price_usd} pilot terms.",
        "offered": "Confirm the purchase and payment path.",
    },
    "needs_approval": {
        "lead": "Qualify the team and prepare an internal approval brief.",
        "qualified": "Send an internal approval brief.",
        "offered": "Resolve the internal approval blocker.",
    },
    "exploring": {
        "lead": "Qualify the repository standard and evidence need.",
        "qualified": "Share rollout proof and confirm decision criteria.",
        "offered": "Confirm budget timing and decision criteria.",
    },
}


class FunnelInputError(ValueError):
    """Raised when a pilot issue export cannot be analyzed safely."""


@dataclass(frozen=True)
class PilotIssue:
    number: int
    title: str
    url: str
    labels: frozenset[str]
    state: str
    updated_at: datetime | None
    body: str


def build_funnel(
    payload: Any,
    pilot_price_usd: int = DEFAULT_PILOT_PRICE_USD,
    target_pilots: int = DEFAULT_TARGET_PILOTS,
    as_of: date | None = None,
    stale_days: int = DEFAULT_STALE_DAYS,
) -> dict[str, Any]:
    if not isinstance(payload, list):
        raise FunnelInputError("issue export must be a JSON array")
    if pilot_price_usd < 1:
        raise FunnelInputError("pilot price must be a positive integer")
    if target_pilots < 1:
        raise FunnelInputError("target pilots must be a positive integer")
    if stale_days < 1:
        raise FunnelInputError("stale days must be a positive integer")
    report_date = as_of or _utc_today()
    if isinstance(report_date, datetime) or not isinstance(report_date, date):
        raise FunnelInputError("as-of must be a date")

    by_stage = {stage: 0 for stage in DISPLAY_STAGES}
    by_source = {source: _empty_segment_totals() for source in SOURCE_KEYS}
    by_readiness = {
        readiness: _empty_segment_totals() for readiness in READINESS_KEYS
    }
    readiness_counts = {readiness: 0 for readiness in READINESS_KEYS}
    deals: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []
    stale_deals: list[dict[str, Any]] = []
    sales_actions: list[dict[str, Any]] = []
    ignored_issues = 0
    booked_pilots = 0
    annual_conversions = 0
    lost_pilots = 0
    attributed_issues = 0
    unattributed_issues = 0
    unknown_source_issues = 0
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

        source, source_raw, source_warning = _classify_lead_source(issue)
        if source_warning is not None:
            warnings.append(source_warning)
        if source in ATTRIBUTED_SOURCES:
            attributed_issues += 1
        elif source == "unattributed":
            unattributed_issues += 1
        else:
            unknown_source_issues += 1

        readiness, readiness_raw, readiness_warning = _classify_purchase_readiness(
            issue
        )
        if readiness_warning is not None:
            warnings.append(readiness_warning)
        readiness_counts[readiness] += 1

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

        age_days: int | None = None
        if issue.updated_at is not None:
            age_days = (report_date - issue.updated_at.date()).days
            if age_days < 0:
                warnings.append(
                    _warning(
                        issue,
                        "future_updated_at",
                        (
                            f"Issue updated date {issue.updated_at.date()} is after "
                            f"report date {report_date}."
                        ),
                    )
                )

        sales_priority: int | None = None
        next_action: str | None = None
        if stage in FOLLOW_UP_STAGES and issue.state == "OPEN":
            sales_priority = SALES_PRIORITY_BY_READINESS[readiness]
            next_action = _sales_action(stage, readiness, pilot_price_usd)
            sales_actions.append(
                {
                    "number": issue.number,
                    "title": issue.title,
                    "url": issue.url,
                    "stage": stage,
                    "source": source,
                    "purchase_readiness": readiness,
                    "priority": sales_priority,
                    "next_action": next_action,
                    "age_days": age_days,
                    "updated_at": _format_timestamp(issue.updated_at),
                }
            )

        needs_follow_up = False
        if stage in FOLLOW_UP_STAGES and issue.state == "CLOSED":
            warnings.append(
                _warning(
                    issue,
                    "closed_without_lost",
                    "Closed pre-payment issue needs the pilot-lost label.",
                )
            )
        elif stage in FOLLOW_UP_STAGES and issue.state == "OPEN":
            if issue.updated_at is None:
                warnings.append(
                    _warning(
                        issue,
                        "missing_updated_at",
                        "Open pre-payment issue has no updatedAt timestamp.",
                    )
                )
            elif age_days is not None and age_days >= stale_days:
                needs_follow_up = True
                stale_deals.append(
                    {
                        "number": issue.number,
                        "title": issue.title,
                        "url": issue.url,
                        "stage": stage,
                        "source": source,
                        "purchase_readiness": readiness,
                        "priority": sales_priority,
                        "next_action": next_action,
                        "age_days": age_days,
                        "updated_at": _format_timestamp(issue.updated_at),
                    }
                )

        by_stage[stage] += 1
        is_booked = furthest_stage >= STAGE_LABELS.index("pilot-paid")
        booked_pilots += int(is_booked)
        annual_conversions += int(has_converted)
        lost_pilots += int(has_lost)
        is_qualified = furthest_stage >= STAGE_LABELS.index("pilot-qualified")
        is_offered = furthest_stage >= STAGE_LABELS.index("pilot-offered")
        for totals in (by_source[source], by_readiness[readiness]):
            _record_segment_totals(
                totals,
                is_qualified=is_qualified,
                is_offered=is_offered,
                is_booked=is_booked,
                has_converted=has_converted,
                has_lost=has_lost,
                pilot_price_usd=pilot_price_usd,
            )
        deals.append(
            {
                "number": issue.number,
                "title": issue.title,
                "url": issue.url,
                "stage": stage,
                "source": source,
                "source_raw": source_raw,
                "purchase_readiness": readiness,
                "purchase_readiness_raw": readiness_raw,
                "booked": is_booked,
                "state": issue.state,
                "updated_at": _format_timestamp(issue.updated_at),
                "age_days": age_days,
                "needs_follow_up": needs_follow_up,
                "sales_priority": sales_priority,
                "next_action": next_action,
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
            "stale_deals": len(stale_deals),
            "sales_actions": len(sales_actions),
            "attributed_issues": attributed_issues,
            "unattributed_issues": unattributed_issues,
            "unknown_source_issues": unknown_source_issues,
            "ready_issues": readiness_counts["ready"],
            "needs_approval_issues": readiness_counts["needs_approval"],
            "exploring_issues": readiness_counts["exploring"],
            "missing_readiness_issues": readiness_counts["unattributed"],
            "unknown_readiness_issues": readiness_counts["unknown"],
        },
        "follow_up": {
            "as_of": report_date.isoformat(),
            "stale_days": stale_days,
            "deals": sorted(
                stale_deals,
                key=lambda deal: (-deal["age_days"], deal["number"]),
            ),
        },
        "sales_queue": {
            "deals": sorted(sales_actions, key=_sales_queue_sort_key),
        },
        "by_stage": by_stage,
        "by_source": by_source,
        "by_readiness": by_readiness,
        "deals": sorted(deals, key=lambda deal: deal["number"]),
        "warnings": warnings,
    }


def format_funnel(report: dict[str, Any]) -> str:
    summary = report["summary"]
    pricing = report["pricing"]
    follow_up_label = "deal" if summary["stale_deals"] == 1 else "deals"
    sales_action_label = "deal" if summary["sales_actions"] == 1 else "deals"
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
        (
            f"Attribution: {summary['attributed_issues']} attributed / "
            f"{summary['unattributed_issues']} missing / "
            f"{summary['unknown_source_issues']} unknown"
        ),
        (
            f"Purchase readiness: {summary['ready_issues']} ready / "
            f"{summary['needs_approval_issues']} need approval / "
            f"{summary['exploring_issues']} exploring / "
            f"{summary['missing_readiness_issues']} missing / "
            f"{summary['unknown_readiness_issues']} unknown"
        ),
        (
            f"Follow-up: {summary['stale_deals']} stale open pre-payment "
            f"{follow_up_label} "
            f"({report['follow_up']['stale_days']}+ days as of "
            f"{report['follow_up']['as_of']})"
        ),
        (
            f"Sales actions: {summary['sales_actions']} open pre-payment "
            f"{sales_action_label}"
        ),
        "Stages:",
    ]
    for stage in DISPLAY_STAGES:
        lines.append(f"  {stage}: {report['by_stage'][stage]}")

    lines.append("Sources:")
    populated_sources = [
        source for source in SOURCE_KEYS if report["by_source"][source]["deals"]
    ]
    if populated_sources:
        for source in populated_sources:
            totals = report["by_source"][source]
            source_deal_label = "deal" if totals["deals"] == 1 else "deals"
            lines.append(
                f"  {source}: {totals['deals']} {source_deal_label}, "
                f"{totals['qualified_pilots']} qualified, "
                f"{totals['offered_pilots']} offered, "
                f"{totals['booked_pilots']} booked "
                f"(${totals['booked_revenue_usd']}), "
                f"{totals['annual_conversions']} converted, "
                f"{totals['lost_pilots']} lost"
            )
    else:
        lines.append("  none")

    lines.append("Purchase readiness:")
    populated_readiness = [
        readiness
        for readiness in READINESS_KEYS
        if report["by_readiness"][readiness]["deals"]
    ]
    if populated_readiness:
        for readiness in populated_readiness:
            totals = report["by_readiness"][readiness]
            deal_label = "deal" if totals["deals"] == 1 else "deals"
            lines.append(
                f"  {readiness}: {totals['deals']} {deal_label}, "
                f"{totals['qualified_pilots']} qualified, "
                f"{totals['offered_pilots']} offered, "
                f"{totals['booked_pilots']} booked "
                f"(${totals['booked_revenue_usd']}), "
                f"{totals['annual_conversions']} converted, "
                f"{totals['lost_pilots']} lost"
            )
    else:
        lines.append("  none")

    lines.append("Deals:")
    if report["deals"]:
        for deal in report["deals"]:
            suffix = f" {deal['url']}" if deal["url"] else ""
            lines.append(
                f"  #{deal['number']} [{deal['stage']}, {deal['source']}, "
                f"{deal['purchase_readiness']}] "
                f"{deal['title']}{suffix}"
            )
    else:
        lines.append("  none")

    lines.append("Stale deals:")
    if report["follow_up"]["deals"]:
        for deal in report["follow_up"]["deals"]:
            suffix = f" {deal['url']}" if deal["url"] else ""
            lines.append(
                f"  #{deal['number']} [{deal['stage']}, "
                f"{deal['purchase_readiness']}, {deal['age_days']} days] "
                f"{deal['title']} (updated {deal['updated_at']}){suffix}"
            )
    else:
        lines.append("  none")

    lines.append("Sales queue:")
    if report["sales_queue"]["deals"]:
        for deal in report["sales_queue"]["deals"]:
            suffix = f" {deal['url']}" if deal["url"] else ""
            lines.append(
                f"  #{deal['number']} [P{deal['priority']}, {deal['stage']}, "
                f"{deal['purchase_readiness']}] {deal['next_action']} "
                f"{deal['title']}{suffix}"
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
    parser.add_argument(
        "--as-of",
        type=_iso_date,
        metavar="YYYY-MM-DD",
        help="UTC report date for reproducible follow-up ages. Defaults to today.",
    )
    parser.add_argument(
        "--stale-days",
        type=_positive_int,
        default=DEFAULT_STALE_DAYS,
        metavar="DAYS",
        help=f"Follow-up age threshold. Defaults to {DEFAULT_STALE_DAYS} days.",
    )
    return parser


def main(argv: Sequence[str] | None = None, stdin: TextIO | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    input_stream = stdin or sys.stdin

    try:
        payload = _read_payload(args.input, input_stream)
        report = build_funnel(
            payload,
            pilot_price_usd=args.pilot_price,
            target_pilots=args.target_pilots,
            as_of=args.as_of,
            stale_days=args.stale_days,
        )
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

    state = raw_issue.get("state")
    if not isinstance(state, str) or state.upper() not in {"OPEN", "CLOSED"}:
        raise FunnelInputError(f"{location}.state must be OPEN or CLOSED")

    updated_at = _parse_timestamp(raw_issue.get("updatedAt"), location)
    raw_body = raw_issue.get("body")
    if raw_body is None:
        body = ""
    elif isinstance(raw_body, str):
        body = raw_body
    else:
        raise FunnelInputError(f"{location}.body must be a string or null")
    return PilotIssue(
        number,
        title.strip(),
        url,
        frozenset(labels),
        state.upper(),
        updated_at,
        body,
    )


def _warning(
    issue: PilotIssue,
    kind: str,
    message: str,
    labels: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "issue_number": issue.number,
        "kind": kind,
        "message": message,
        "labels": labels or [],
    }


def _empty_segment_totals() -> dict[str, int]:
    return {
        "deals": 0,
        "qualified_pilots": 0,
        "offered_pilots": 0,
        "booked_pilots": 0,
        "booked_revenue_usd": 0,
        "annual_conversions": 0,
        "lost_pilots": 0,
    }


def _record_segment_totals(
    totals: dict[str, int],
    *,
    is_qualified: bool,
    is_offered: bool,
    is_booked: bool,
    has_converted: bool,
    has_lost: bool,
    pilot_price_usd: int,
) -> None:
    totals["deals"] += 1
    totals["qualified_pilots"] += int(is_qualified)
    totals["offered_pilots"] += int(is_offered)
    totals["booked_pilots"] += int(is_booked)
    totals["booked_revenue_usd"] += int(is_booked) * pilot_price_usd
    totals["annual_conversions"] += int(has_converted)
    totals["lost_pilots"] += int(has_lost)


def _sales_action(stage: str, readiness: str, pilot_price_usd: int) -> str:
    if readiness not in SALES_ACTIONS:
        return "Clarify purchase readiness before advancing."
    return SALES_ACTIONS[readiness][stage].format(
        pilot_price_usd=pilot_price_usd
    )


def _sales_queue_sort_key(deal: dict[str, Any]) -> tuple[int, int, int, int]:
    age_days = deal["age_days"]
    age_rank = -age_days if isinstance(age_days, int) and age_days >= 0 else 1
    return (
        deal["priority"],
        SALES_STAGE_ORDER[deal["stage"]],
        age_rank,
        deal["number"],
    )


def _classify_lead_source(
    issue: PilotIssue,
) -> tuple[str, str | None, dict[str, Any] | None]:
    answers = _issue_form_answers(issue.body, SOURCE_FIELD_HEADING)
    if not answers or answers == ["_No response_"]:
        return (
            "unattributed",
            None,
            _warning(
                issue,
                "missing_lead_source",
                "Pilot issue has no lead source answer.",
            ),
        )
    if len(answers) != 1:
        return (
            "unknown",
            "; ".join(answers),
            _warning(
                issue,
                "ambiguous_lead_source",
                "Pilot issue contains multiple lead source answers.",
            ),
        )

    raw_answer = answers[0]
    source = SOURCE_BY_ANSWER.get(raw_answer)
    if source is None:
        return (
            "unknown",
            raw_answer,
            _warning(
                issue,
                "unknown_lead_source",
                f"Unknown lead source answer: {raw_answer}.",
            ),
        )
    return source, raw_answer, None


def _classify_purchase_readiness(
    issue: PilotIssue,
) -> tuple[str, str | None, dict[str, Any] | None]:
    answers = _issue_form_answers(issue.body, READINESS_FIELD_HEADING)
    if not answers or answers == ["_No response_"]:
        return (
            "unattributed",
            None,
            _warning(
                issue,
                "missing_purchase_readiness",
                "Pilot issue has no purchase readiness answer.",
            ),
        )
    if len(answers) != 1:
        return (
            "unknown",
            "; ".join(answers),
            _warning(
                issue,
                "ambiguous_purchase_readiness",
                "Pilot issue contains multiple purchase readiness answers.",
            ),
        )

    raw_answer = answers[0]
    readiness = READINESS_BY_ANSWER.get(raw_answer)
    if readiness is None:
        return (
            "unknown",
            raw_answer,
            _warning(
                issue,
                "unknown_purchase_readiness",
                f"Unknown purchase readiness answer: {raw_answer}.",
            ),
        )
    return readiness, raw_answer, None


def _issue_form_answers(body: str, heading: str) -> list[str]:
    normalized = body.replace("\r\n", "\n").replace("\r", "\n")
    heading_pattern = re.compile(
        rf"^###\s+{re.escape(heading)}[ \t]*$",
        re.MULTILINE,
    )
    next_heading_pattern = re.compile(r"^###\s+", re.MULTILINE)
    answers: list[str] = []
    for match in heading_pattern.finditer(normalized):
        remainder = normalized[match.end() :]
        next_heading = next_heading_pattern.search(remainder)
        value = remainder[: next_heading.start() if next_heading else None].strip()
        if value:
            answers.append(value)
    return answers


def _parse_timestamp(value: Any, location: str) -> datetime | None:
    if value is None:
        return None
    if not isinstance(value, str) or not value:
        raise FunnelInputError(f"{location}.updatedAt must be an ISO 8601 timestamp")

    normalized = f"{value[:-1]}+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise FunnelInputError(
            f"{location}.updatedAt must be an ISO 8601 timestamp"
        ) from exc
    if parsed.tzinfo is None:
        raise FunnelInputError(f"{location}.updatedAt must include a timezone")
    return parsed.astimezone(timezone.utc)


def _format_timestamp(value: datetime | None) -> str | None:
    if value is None:
        return None
    return value.isoformat().replace("+00:00", "Z")


def _utc_today() -> date:
    return datetime.now(timezone.utc).date()


def _positive_int(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be a positive integer") from exc
    if parsed < 1:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return parsed


def _iso_date(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be YYYY-MM-DD") from exc


if __name__ == "__main__":
    raise SystemExit(main())
