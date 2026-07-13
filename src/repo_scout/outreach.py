from __future__ import annotations

import argparse
import csv
from datetime import date, timedelta
import json
import os
from pathlib import Path
import re
import stat
import sys
from tempfile import NamedTemporaryFile
from typing import Any, Sequence
from urllib.parse import urlsplit


SCHEMA_VERSION = 5
REVIEW_SCHEMA_VERSION = 1
APPROVAL_SCHEMA_VERSION = 1
CONTACT_SCHEMA_VERSION = 1
MAX_PROSPECTS = 10
FOLLOW_UP_DAYS = 7
MAX_FOLLOW_UPS = 1
LEDGER_FIELDS = (
    "prospect_id",
    "fit_signals",
    "fit_evidence",
    "contacted_on",
    "channel",
    "status",
    "followed_up_on",
    "next_action_on",
    "approved_on",
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
    "drafted",
    "approved",
    "contacted",
    "followed-up",
    "replied",
    "pilot-requested",
    "not-a-fit",
    "do-not-contact",
)
PRE_CONTACT_STATUSES = {"researched", "drafted", "approved"}
NO_NEXT_ACTION_STATUSES = {
    "followed-up",
    "replied",
    "pilot-requested",
    "not-a-fit",
    "do-not-contact",
}
PROSPECT_ID_PATTERN = re.compile(r"prospect-[0-9]{3}\Z")
HUMAN_REVIEW_CHECKS = (
    "Confirm the public observation is accurate and current.",
    "Confirm the recipient and published business channel are appropriate.",
    "Confirm the message states the $299 price and 90-day scope accurately.",
    "Confirm the message states that source code stays local.",
    "Confirm the message includes appropriate opt-out behavior.",
)


class OutreachInputError(ValueError):
    """Raised when private outreach activity cannot be processed safely."""


def load_outreach_report(path: Path, *, as_of: date | None = None) -> dict[str, Any]:
    report_date = as_of or date.today()
    if type(report_date) is not date:
        raise OutreachInputError("as-of must be a date")

    return build_outreach_report(_load_outreach_rows(path), as_of=report_date)


def load_next_outreach_review(
    path: Path, *, as_of: date | None = None
) -> dict[str, Any]:
    report_date = as_of or date.today()
    if type(report_date) is not date:
        raise OutreachInputError("as-of must be a date")

    return build_next_outreach_review(
        _load_outreach_rows(path), as_of=report_date
    )


def approve_next_outreach_draft(
    path: Path,
    *,
    prospect_id: str,
    approved_on: date,
    review_confirmed: bool,
    as_of: date | None = None,
) -> dict[str, Any]:
    report_date = as_of or date.today()
    if type(report_date) is not date:
        raise OutreachInputError("as-of must be a date")
    if type(approved_on) is not date:
        raise OutreachInputError("approved-on must be a date")
    if review_confirmed is not True:
        raise OutreachInputError(
            "--approve-next requires --confirm-reviewed after a human "
            "completes every review check"
        )
    if not PROSPECT_ID_PATTERN.fullmatch(prospect_id):
        raise OutreachInputError("prospect_id must match prospect-NNN")

    rows = _load_outreach_rows(path)
    build_outreach_report(rows, as_of=report_date)
    next_draft = _next_status_row(rows, "drafted")
    if next_draft is None:
        raise OutreachInputError("no drafted prospects await human approval")
    if next_draft["prospect_id"] != prospect_id:
        raise OutreachInputError(
            f"next drafted prospect is {next_draft['prospect_id']}; "
            "review and approve it first"
        )

    updated_rows = [dict(row) for row in rows]
    for row in updated_rows:
        if (row.get("prospect_id") or "").strip() == prospect_id:
            row["status"] = "approved"
            row["approved_on"] = approved_on.isoformat()
            break

    build_outreach_report(updated_rows, as_of=report_date)
    _write_outreach_rows(path, updated_rows)
    return {
        "schema_version": APPROVAL_SCHEMA_VERSION,
        "as_of": report_date.isoformat(),
        "private_output": True,
        "human_review_confirmed": True,
        "approval": {
            "prospect_id": prospect_id,
            "status": "approved",
        },
        "action_note": (
            "Human approval was recorded atomically. No outreach was sent, "
            "and no contact or follow-up date was created."
        ),
    }


def record_next_outreach_contact(
    path: Path,
    *,
    prospect_id: str,
    contacted_on: date,
    send_confirmed: bool,
    as_of: date | None = None,
) -> dict[str, Any]:
    report_date = as_of or date.today()
    if type(report_date) is not date:
        raise OutreachInputError("as-of must be a date")
    if type(contacted_on) is not date:
        raise OutreachInputError("contacted-on must be a date")
    if send_confirmed is not True:
        raise OutreachInputError(
            "--record-contact requires --confirm-sent after a human sends "
            "the approved message"
        )
    if not PROSPECT_ID_PATTERN.fullmatch(prospect_id):
        raise OutreachInputError("prospect_id must match prospect-NNN")

    rows = _load_outreach_rows(path)
    build_outreach_report(rows, as_of=report_date)
    next_approved = _next_status_row(rows, "approved")
    if next_approved is None:
        raise OutreachInputError("no approved prospects await contact recording")
    if next_approved["prospect_id"] != prospect_id:
        raise OutreachInputError(
            f"next approved prospect is {next_approved['prospect_id']}; "
            "record it first"
        )

    follow_up_due = contacted_on + timedelta(days=FOLLOW_UP_DAYS)
    updated_rows = [dict(row) for row in rows]
    for row in updated_rows:
        if (row.get("prospect_id") or "").strip() == prospect_id:
            row["status"] = "contacted"
            row["contacted_on"] = contacted_on.isoformat()
            row["next_action_on"] = follow_up_due.isoformat()
            break

    build_outreach_report(updated_rows, as_of=report_date)
    _write_outreach_rows(path, updated_rows)
    return {
        "schema_version": CONTACT_SCHEMA_VERSION,
        "as_of": report_date.isoformat(),
        "private_output": True,
        "human_send_confirmed": True,
        "contact": {
            "prospect_id": prospect_id,
            "status": "contacted",
            "follow_up_due": follow_up_due.isoformat(),
        },
        "action_note": (
            "The human-confirmed send was recorded atomically. Repo Scout "
            "sent nothing and scheduled no automatic follow-up."
        ),
    }


def _load_outreach_rows(path: Path) -> list[dict[str, str]]:
    try:
        with path.open(newline="", encoding="utf-8") as ledger_file:
            reader = csv.reader(ledger_file, strict=True)
            header = next(reader, [])
            if tuple(header) != LEDGER_FIELDS:
                expected = ",".join(LEDGER_FIELDS)
                raise OutreachInputError(
                    f"ledger header must be exactly: {expected}"
                )
            rows = []
            for row_number, values in enumerate(reader, start=2):
                if len(values) != len(LEDGER_FIELDS):
                    raise OutreachInputError(
                        f"row {row_number}: ledger row must have exactly "
                        f"{len(LEDGER_FIELDS)} columns; found {len(values)}"
                    )
                rows.append(dict(zip(LEDGER_FIELDS, values, strict=True)))
    except csv.Error as exc:
        raise OutreachInputError(f"cannot parse outreach ledger: {exc}") from exc
    except (OSError, UnicodeError) as exc:
        raise OutreachInputError(f"cannot read outreach ledger: {exc}") from exc

    return rows


def _write_outreach_rows(path: Path, rows: list[dict[str, str]]) -> None:
    temporary_path: Path | None = None
    try:
        existing_mode = stat.S_IMODE(path.stat().st_mode)
        with NamedTemporaryFile(
            "w",
            newline="",
            encoding="utf-8",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as ledger_file:
            temporary_path = Path(ledger_file.name)
            writer = csv.DictWriter(
                ledger_file,
                fieldnames=LEDGER_FIELDS,
                extrasaction="raise",
                lineterminator="\n",
            )
            writer.writeheader()
            writer.writerows(rows)
            ledger_file.flush()
            os.fsync(ledger_file.fileno())
        os.chmod(temporary_path, existing_mode)
        os.replace(temporary_path, path)
    except (csv.Error, OSError, UnicodeError, ValueError) as exc:
        if temporary_path is not None:
            try:
                temporary_path.unlink(missing_ok=True)
            except OSError:
                pass
        raise OutreachInputError("cannot update outreach ledger safely") from exc


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
    fit_evidence_links = 0

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
        evidence = _fit_evidence(row["fit_evidence"], row_number=row_number)
        missing_evidence = sorted(set(signals) - set(evidence))
        if missing_evidence:
            raise OutreachInputError(
                f"row {row_number}: missing fit evidence for: {missing_evidence[0]}"
            )
        extra_evidence = sorted(set(evidence) - set(signals))
        if extra_evidence:
            raise OutreachInputError(
                f"row {row_number}: fit evidence has undeclared signal: "
                f"{extra_evidence[0]}"
            )
        fit_evidence_links += len(evidence)

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
        approved_on = _optional_date(
            row["approved_on"], row_number=row_number, field="approved_on"
        )

        if status in PRE_CONTACT_STATUSES:
            if any(
                action_date is not None
                for action_date in (contacted_on, followed_up_on, next_action_on)
            ):
                raise OutreachInputError(
                    f"row {row_number}: {status} prospects cannot have contact dates"
                )
            if status in {"drafted", "approved"} and channel not in CHANNELS:
                raise OutreachInputError(
                    f"row {row_number}: {status} prospects require a permitted channel"
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

        if status in {"researched", "drafted"}:
            if approved_on is not None:
                raise OutreachInputError(
                    f"row {row_number}: {status} prospects cannot have approved_on"
                )
        else:
            if approved_on is None:
                raise OutreachInputError(
                    f"row {row_number}: approved_on is required after draft review"
                )
            if approved_on > as_of:
                raise OutreachInputError(
                    f"row {row_number}: approved_on cannot be after as-of"
                )
            if contacted_on is not None and approved_on > contacted_on:
                raise OutreachInputError(
                    f"row {row_number}: approved_on must be no later than contacted_on"
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
    attempted = len(rows) - sum(
        status_counts[status] for status in PRE_CONTACT_STATUSES
    )
    closed = status_counts["not-a-fit"] + status_counts["do-not-contact"]
    return {
        "schema_version": SCHEMA_VERSION,
        "as_of": as_of.isoformat(),
        "experiment": {
            "max_prospects": MAX_PROSPECTS,
            "follow_up_days": FOLLOW_UP_DAYS,
            "max_follow_ups": MAX_FOLLOW_UPS,
            "human_approval_required": True,
        },
        "summary": {
            "prospects": len(rows),
            "attempted_prospects": attempted,
            "researched": status_counts["researched"],
            "drafted": status_counts["drafted"],
            "approved": status_counts["approved"],
            "contacted": status_counts["contacted"],
            "followed_up": status_counts["followed-up"],
            "replied": status_counts["replied"],
            "pilot_requested": status_counts["pilot-requested"],
            "closed": closed,
            "due_followups": len(due_followups),
            "fit_evidence_links": fit_evidence_links,
        },
        "by_status": status_counts,
        "due_followups": due_followups,
        "evidence_note": (
            "Outreach ledger activity is not lead, demand, payment, or revenue "
            "evidence."
        ),
    }


def build_next_outreach_review(
    rows: list[dict[str, str | None]], *, as_of: date
) -> dict[str, Any]:
    build_outreach_report(rows, as_of=as_of)
    draft = _next_status_row(rows, "drafted")
    review = None
    if draft is not None:
        review = {
            "prospect_id": draft["prospect_id"],
            "channel": draft["channel"],
            "fit_signals": len(draft["fit_signals"].split(";")),
            "fit_evidence_links": len(draft["fit_evidence"].split(";")),
            "checks": list(HUMAN_REVIEW_CHECKS),
        }
    return {
        "schema_version": REVIEW_SCHEMA_VERSION,
        "as_of": as_of.isoformat(),
        "human_review_required": True,
        "private_output": True,
        "review": review,
        "action_note": (
            "This checklist does not approve, modify, or send outreach."
        ),
    }


def _next_status_row(
    rows: list[dict[str, str | None]],
    status: str,
) -> dict[str, str] | None:
    matching_rows = sorted(
        (
            {field: (raw_row.get(field) or "").strip() for field in LEDGER_FIELDS}
            for raw_row in rows
            if (raw_row.get("status") or "").strip() == status
        ),
        key=lambda row: row["prospect_id"],
    )
    return matching_rows[0] if matching_rows else None


def format_outreach_report(report: dict[str, Any]) -> str:
    summary = report["summary"]
    experiment = report["experiment"]
    lines = [
        "Repo Scout outreach operations",
        f"As of: {report['as_of']}",
        f"Prospects: {summary['prospects']} / {experiment['max_prospects']}",
        f"Qualification links: {summary['fit_evidence_links']}",
        f"Drafts awaiting review: {summary['drafted']}",
        f"Approved to send: {summary['approved']}",
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


def format_next_outreach_review(review_report: dict[str, Any]) -> str:
    review = review_report["review"]
    lines = ["Repo Scout next outreach review", f"As of: {review_report['as_of']}"]
    if review is None:
        lines.append("No drafts are awaiting human review.")
    else:
        lines.extend(
            [
                f"Prospect alias: {review['prospect_id']}",
                f"Permitted channel: {review['channel']}",
                (
                    "Qualification: "
                    f"{review['fit_signals']} signals / "
                    f"{review['fit_evidence_links']} private links"
                ),
                "Human checks:",
                *(f"- [ ] {check}" for check in review["checks"]),
                (
                    "Next: after a human completes every check, run "
                    f"--approve-next {review['prospect_id']} with --approved-on "
                    "and --confirm-reviewed."
                ),
            ]
        )
    lines.append("Privacy: Keep this alias-only checklist in the private workspace.")
    lines.append(f"Boundary: {review_report['action_note']}")
    return "\n".join(lines)


def format_outreach_approval(approval_report: dict[str, Any]) -> str:
    approval = approval_report["approval"]
    lines = [
        "Repo Scout outreach approval",
        f"As of: {approval_report['as_of']}",
        f"Prospect alias: {approval['prospect_id']}",
        f"Status: {approval['status']}",
        "Private ledger updated atomically.",
        f"Boundary: {approval_report['action_note']}",
        (
            "Next: send this one message manually, then run "
            f"--record-contact {approval['prospect_id']} with --contacted-on "
            "and --confirm-sent."
        ),
    ]
    return "\n".join(lines)


def format_outreach_contact(contact_report: dict[str, Any]) -> str:
    contact = contact_report["contact"]
    lines = [
        "Repo Scout outreach contact record",
        f"As of: {contact_report['as_of']}",
        f"Prospect alias: {contact['prospect_id']}",
        f"Status: {contact['status']}",
        f"Manual follow-up due: {contact['follow_up_due']}",
        "Private ledger updated atomically.",
        f"Boundary: {contact_report['action_note']}",
        (
            "Next: if there is no reply or opt-out, follow up manually on the "
            "due date."
        ),
    ]
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="repo-scout-outreach",
        description=(
            "Validate a private outreach ledger, review drafts, record human "
            "approvals and sent contacts, and report bounded follow-ups."
        ),
    )
    parser.add_argument("ledger", type=Path, help="Path to the private outreach CSV.")
    parser.add_argument(
        "--as-of",
        type=_date_argument,
        default=date.today(),
        metavar="YYYY-MM-DD",
        help="Report date. Defaults to the local calendar date.",
    )
    action_group = parser.add_mutually_exclusive_group()
    action_group.add_argument(
        "--review-next",
        action="store_true",
        help=(
            "Show one alias-only human review checklist without modifying "
            "the ledger or sending outreach."
        ),
    )
    action_group.add_argument(
        "--approve-next",
        metavar="PROSPECT_ID",
        help=(
            "Record human approval for the next reviewed draft without "
            "sending outreach."
        ),
    )
    action_group.add_argument(
        "--record-contact",
        metavar="PROSPECT_ID",
        help=(
            "After a human sends it, record contact for the next approved "
            "message and its seven-day follow-up."
        ),
    )
    parser.add_argument(
        "--approved-on",
        type=_date_argument,
        metavar="YYYY-MM-DD",
        help="Human review date. Required with --approve-next.",
    )
    parser.add_argument(
        "--confirm-reviewed",
        action="store_true",
        help=(
            "Confirm a human completed every --review-next check. Required "
            "with --approve-next."
        ),
    )
    parser.add_argument(
        "--contacted-on",
        type=_date_argument,
        metavar="YYYY-MM-DD",
        help="Human send date. Required with --record-contact.",
    )
    parser.add_argument(
        "--confirm-sent",
        action="store_true",
        help=(
            "Confirm a human already sent the approved message. Required "
            "with --record-contact."
        ),
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
        if args.approve_next is not None:
            if args.contacted_on is not None or args.confirm_sent:
                raise OutreachInputError(
                    "--contacted-on and --confirm-sent require --record-contact"
                )
            if args.approved_on is None:
                raise OutreachInputError(
                    "--approve-next requires --approved-on YYYY-MM-DD"
                )
            report = approve_next_outreach_draft(
                args.ledger,
                prospect_id=args.approve_next,
                approved_on=args.approved_on,
                review_confirmed=args.confirm_reviewed,
                as_of=args.as_of,
            )
        elif args.record_contact is not None:
            if args.approved_on is not None or args.confirm_reviewed:
                raise OutreachInputError(
                    "--approved-on and --confirm-reviewed require --approve-next"
                )
            if args.contacted_on is None:
                raise OutreachInputError(
                    "--record-contact requires --contacted-on YYYY-MM-DD"
                )
            report = record_next_outreach_contact(
                args.ledger,
                prospect_id=args.record_contact,
                contacted_on=args.contacted_on,
                send_confirmed=args.confirm_sent,
                as_of=args.as_of,
            )
        elif args.approved_on is not None or args.confirm_reviewed:
            raise OutreachInputError(
                "--approved-on and --confirm-reviewed require --approve-next"
            )
        elif args.contacted_on is not None or args.confirm_sent:
            raise OutreachInputError(
                "--contacted-on and --confirm-sent require --record-contact"
            )
        elif args.review_next:
            report = load_next_outreach_review(args.ledger, as_of=args.as_of)
        else:
            report = load_outreach_report(args.ledger, as_of=args.as_of)
    except OutreachInputError as exc:
        print(f"repo-scout-outreach: {exc}", file=sys.stderr)
        return 2

    if args.format == "json":
        print(json.dumps(report, indent=2, sort_keys=True))
    elif args.record_contact is not None:
        print(format_outreach_contact(report))
    elif args.approve_next is not None:
        print(format_outreach_approval(report))
    elif args.review_next:
        print(format_next_outreach_review(report))
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


def _fit_evidence(value: str, *, row_number: int) -> dict[str, str]:
    entries = [entry.strip() for entry in value.split(";")]
    if not value or "" in entries:
        raise OutreachInputError(
            f"row {row_number}: fit_evidence must map each signal to an HTTPS URL"
        )

    evidence: dict[str, str] = {}
    for entry in entries:
        signal, separator, url = entry.partition("=")
        signal = signal.strip()
        url = url.strip()
        if not separator or not signal or not url:
            raise OutreachInputError(
                f"row {row_number}: fit_evidence entries must be signal=https://..."
            )
        if signal in evidence:
            raise OutreachInputError(
                f"row {row_number}: fit_evidence contains duplicate signal: {signal}"
            )
        parsed = urlsplit(url)
        if (
            parsed.scheme != "https"
            or not parsed.hostname
            or parsed.username is not None
            or parsed.password is not None
            or any(character.isspace() for character in url)
        ):
            raise OutreachInputError(
                f"row {row_number}: fit evidence for {signal} must be a secure "
                "HTTPS URL without credentials"
            )
        evidence[signal] = url
    return evidence


def _date_argument(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be YYYY-MM-DD") from exc


if __name__ == "__main__":
    raise SystemExit(main())
