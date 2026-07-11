from __future__ import annotations

import argparse
import csv
from datetime import date, timedelta
import json
from pathlib import Path
import re
import sys
from typing import Any, Sequence


SCHEMA_VERSION = 1
MAX_PROSPECTS = 10
FOLLOW_UP_DAYS = 7
MAX_FOLLOW_UPS = 1
LEDGER_FIELDS = (
    "prospect_id",
    "fit_signals",
    "contacted_on",
    "channel",
    "status",
    "followed_up_on",
    "next_action_on",
)
FIT_SIGNALS = (
    "team_5_50",
    "multi_repo",
    "agent_use",
    "engineering_owner",
    "local_privacy",
)
CHANNELS = ("warm-intro", "published-business")
STATUSES = (
    "researched",
    "contacted",
    "followed-up",
    "replied",
    "pilot-requested",
    "not-a-fit",
    "do-not-contact",
)
NO_NEXT_ACTION_STATUSES = {
    "followed-up",
    "replied",
    "pilot-requested",
    "not-a-fit",
    "do-not-contact",
}
PROSPECT_ID_PATTERN = re.compile(r"prospect-[0-9]{3}\Z")


class OutreachInputError(ValueError):
    """Raised when private outreach activity cannot be reported safely."""


def load_outreach_report(path: Path, *, as_of: date | None = None) -> dict[str, Any]:
    report_date = as_of or date.today()
    if type(report_date) is not date:
        raise OutreachInputError("as-of must be a date")

    try:
        with path.open(newline="", encoding="utf-8") as ledger_file:
            reader = csv.DictReader(ledger_file)
            if tuple(reader.fieldnames or ()) != LEDGER_FIELDS:
                expected = ",".join(LEDGER_FIELDS)
                raise OutreachInputError(
                    f"ledger header must be exactly: {expected}"
                )
            rows = list(reader)
    except (OSError, UnicodeError) as exc:
        raise OutreachInputError(f"cannot read outreach ledger: {exc}") from exc

    return build_outreach_report(rows, as_of=report_date)


def build_outreach_report(
    rows: list[dict[str, str | None]], *, as_of: date
) -> dict[str, Any]:
    if type(as_of) is not date:
        raise OutreachInputError("as-of must be a date")
    if len(rows) > MAX_PROSPECTS:
        raise OutreachInputError(
            f"outreach batch has {len(rows)} prospects; maximum is {MAX_PROSPECTS}"
        )

    status_counts = {status: 0 for status in STATUSES}
    seen_ids: set[str] = set()
    due_followups: list[dict[str, Any]] = []

    for row_number, raw_row in enumerate(rows, start=2):
        row = {field: (raw_row.get(field) or "").strip() for field in LEDGER_FIELDS}
        prospect_id = row["prospect_id"]
        if not PROSPECT_ID_PATTERN.fullmatch(prospect_id):
            raise OutreachInputError(
                f"row {row_number}: prospect_id must match prospect-NNN"
            )
        if prospect_id in seen_ids:
            raise OutreachInputError(
                f"row {row_number}: duplicate prospect_id: {prospect_id}"
            )
        seen_ids.add(prospect_id)

        signals = [signal.strip() for signal in row["fit_signals"].split(";")]
        if "" in signals:
            raise OutreachInputError(
                f"row {row_number}: fit_signals must be semicolon-separated keys"
            )
        if len(signals) != len(set(signals)):
            raise OutreachInputError(
                f"row {row_number}: fit_signals contains duplicates"
            )
        unknown_signals = sorted(set(signals) - set(FIT_SIGNALS))
        if unknown_signals:
            raise OutreachInputError(
                f"row {row_number}: unknown fit signal: {unknown_signals[0]}"
            )
        if len(signals) < 3:
            raise OutreachInputError(
                f"row {row_number}: at least three fit signals are required"
            )

        status = row["status"]
        if status not in STATUSES:
            raise OutreachInputError(
                f"row {row_number}: unknown status: {status or '<blank>'}"
            )
        status_counts[status] += 1

        channel = row["channel"]
        if channel and channel not in CHANNELS:
            raise OutreachInputError(
                f"row {row_number}: unknown channel: {channel}"
            )

        contacted_on = _optional_date(
            row["contacted_on"], row_number=row_number, field="contacted_on"
        )
        followed_up_on = _optional_date(
            row["followed_up_on"], row_number=row_number, field="followed_up_on"
        )
        next_action_on = _optional_date(
            row["next_action_on"], row_number=row_number, field="next_action_on"
        )

        if status == "researched":
            if any(
                action_date is not None
                for action_date in (contacted_on, followed_up_on, next_action_on)
            ):
                raise OutreachInputError(
                    f"row {row_number}: researched prospects cannot have contact dates"
                )
        else:
            if contacted_on is None:
                raise OutreachInputError(
                    f"row {row_number}: contacted_on is required after research"
                )
            if channel not in CHANNELS:
                raise OutreachInputError(
                    f"row {row_number}: a permitted channel is required after research"
                )
            if contacted_on > as_of:
                raise OutreachInputError(
                    f"row {row_number}: contacted_on cannot be after as-of"
                )

        if followed_up_on is not None:
            earliest_follow_up = contacted_on + timedelta(days=FOLLOW_UP_DAYS)
            if followed_up_on < earliest_follow_up:
                raise OutreachInputError(
                    f"row {row_number}: followed_up_on cannot be before "
                    f"{earliest_follow_up.isoformat()}"
                )
            if followed_up_on > as_of:
                raise OutreachInputError(
                    f"row {row_number}: followed_up_on cannot be after as-of"
                )

        if status == "contacted":
            if followed_up_on is not None:
                raise OutreachInputError(
                    f"row {row_number}: contacted prospects cannot be followed up"
                )
            expected_follow_up = contacted_on + timedelta(days=FOLLOW_UP_DAYS)
            if next_action_on != expected_follow_up:
                raise OutreachInputError(
                    f"row {row_number}: contacted prospects require one follow-up "
                    f"on {expected_follow_up.isoformat()}"
                )
            if next_action_on <= as_of:
                due_followups.append(
                    {
                        "prospect_id": prospect_id,
                        "due_on": next_action_on.isoformat(),
                        "overdue_days": (as_of - next_action_on).days,
                    }
                )
        elif status == "followed-up" and followed_up_on is None:
            raise OutreachInputError(
                f"row {row_number}: followed-up status requires followed_up_on"
            )
        elif status in NO_NEXT_ACTION_STATUSES and next_action_on is not None:
            raise OutreachInputError(
                f"row {row_number}: status {status} cannot have a next action"
            )

    due_followups.sort(key=lambda item: (item["due_on"], item["prospect_id"]))
    attempted = len(rows) - status_counts["researched"]
    closed = status_counts["not-a-fit"] + status_counts["do-not-contact"]
    return {
        "schema_version": SCHEMA_VERSION,
        "as_of": as_of.isoformat(),
        "experiment": {
            "max_prospects": MAX_PROSPECTS,
            "follow_up_days": FOLLOW_UP_DAYS,
            "max_follow_ups": MAX_FOLLOW_UPS,
        },
        "summary": {
            "prospects": len(rows),
            "attempted_prospects": attempted,
            "researched": status_counts["researched"],
            "contacted": status_counts["contacted"],
            "followed_up": status_counts["followed-up"],
            "replied": status_counts["replied"],
            "pilot_requested": status_counts["pilot-requested"],
            "closed": closed,
            "due_followups": len(due_followups),
        },
        "by_status": status_counts,
        "due_followups": due_followups,
        "evidence_note": (
            "Outreach ledger activity is not lead, demand, payment, or revenue "
            "evidence."
        ),
    }


def format_outreach_report(report: dict[str, Any]) -> str:
    summary = report["summary"]
    experiment = report["experiment"]
    lines = [
        "Repo Scout outreach operations",
        f"As of: {report['as_of']}",
        f"Prospects: {summary['prospects']} / {experiment['max_prospects']}",
        f"Attempted prospects: {summary['attempted_prospects']}",
        f"Due follow-ups: {summary['due_followups']}",
        f"Ledger pilot requests: {summary['pilot_requested']}",
    ]
    if report["due_followups"]:
        lines.append("Follow-ups due:")
        for item in report["due_followups"]:
            timing = (
                "due today"
                if item["overdue_days"] == 0
                else f"{item['overdue_days']} day(s) overdue"
            )
            lines.append(
                f"- {item['prospect_id']}: {item['due_on']} ({timing})"
            )
    lines.append(f"Evidence: {report['evidence_note']}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="repo-scout-outreach",
        description="Validate a private outreach ledger and report bounded follow-ups.",
    )
    parser.add_argument("ledger", type=Path, help="Path to the private outreach CSV.")
    parser.add_argument(
        "--as-of",
        type=_date_argument,
        default=date.today(),
        metavar="YYYY-MM-DD",
        help="Report date. Defaults to the local calendar date.",
    )
    parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Output format. Defaults to text.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        report = load_outreach_report(args.ledger, as_of=args.as_of)
    except OutreachInputError as exc:
        print(f"repo-scout-outreach: {exc}", file=sys.stderr)
        return 2

    if args.format == "json":
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(format_outreach_report(report))
    return 0


def _optional_date(value: str, *, row_number: int, field: str) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise OutreachInputError(
            f"row {row_number}: {field} must be YYYY-MM-DD"
        ) from exc


def _date_argument(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be YYYY-MM-DD") from exc


if __name__ == "__main__":
    raise SystemExit(main())
