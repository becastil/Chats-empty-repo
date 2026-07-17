from __future__ import annotations

import argparse
import csv
from datetime import date, datetime, timedelta, timezone
from hashlib import sha256
from hmac import compare_digest
import json
import os
from pathlib import Path
import re
import shlex
import stat
import subprocess
import sys
from tempfile import NamedTemporaryFile
from typing import Any, Mapping, Sequence

from .version import add_version_argument
from urllib.parse import urlsplit


SCHEMA_VERSION = 6
REVIEW_SCHEMA_VERSION = 4
APPROVAL_SCHEMA_VERSION = 1
DECLINE_SCHEMA_VERSION = 2
CONTACT_SCHEMA_VERSION = 1
FOLLOW_UP_SCHEMA_VERSION = 1
OUTCOME_SCHEMA_VERSION = 1
MAX_PROSPECTS = 10
FOLLOW_UP_DAYS = 7
MAX_FOLLOW_UPS = 1
MAX_PRIVATE_DRAFT_BYTES = 128 * 1024
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
    "review-declined",
    "approved",
    "contacted",
    "followed-up",
    "replied",
    "pilot-requested",
    "not-a-fit",
    "do-not-contact",
)
PRE_CONTACT_STATUSES = {"researched", "drafted", "review-declined", "approved"}
NO_NEXT_ACTION_STATUSES = {
    "review-declined",
    "followed-up",
    "replied",
    "pilot-requested",
    "not-a-fit",
    "do-not-contact",
}
OUTCOME_STATUSES = (
    "replied",
    "pilot-requested",
    "not-a-fit",
    "do-not-contact",
)
OUTCOME_SOURCE_STATUSES = {"contacted", "followed-up", "replied"}
PROSPECT_ID_PATTERN = re.compile(r"prospect-[0-9]{3}\Z")
PRIVATE_DRAFT_HEADING_PATTERN = re.compile(r"## (prospect-[0-9]{3})\Z")
REVIEW_DIGEST_PATTERN = re.compile(r"sha256:[0-9a-f]{64}\Z")
HUMAN_REVIEW_CHECKS = (
    "Confirm the public observation is accurate and current.",
    "Confirm the recipient and published business channel are appropriate.",
    "Confirm the message states the $299 price and 90-day scope accurately.",
    "Confirm the message states that source code stays local.",
    "Confirm the message gives a clear opt-out and promises no further contact.",
)


class OutreachInputError(ValueError):
    """Raised when private outreach activity cannot be processed safely."""


def load_outreach_report(path: Path, *, as_of: date | None = None) -> dict[str, Any]:
    report_date = as_of or _utc_today()
    if type(report_date) is not date:
        raise OutreachInputError("as-of must be a date")

    return build_outreach_report(_load_outreach_rows(path), as_of=report_date)


def load_next_outreach_review(
    path: Path,
    *,
    as_of: date | None = None,
    include_private_evidence: bool = False,
    private_drafts_path: Path | None = None,
) -> dict[str, Any]:
    report_date = as_of or _utc_today()
    if type(report_date) is not date:
        raise OutreachInputError("as-of must be a date")

    _require_private_live_path(path, label="outreach ledger")
    if private_drafts_path is not None:
        _require_private_live_path(private_drafts_path, label="private draft notes")

    return build_next_outreach_review(
        _load_outreach_rows(path),
        as_of=report_date,
        include_private_evidence=include_private_evidence,
        private_drafts=(
            _load_private_drafts(private_drafts_path)
            if private_drafts_path is not None
            else None
        ),
    )


def approve_next_outreach_draft(
    path: Path,
    *,
    prospect_id: str,
    approved_on: date,
    review_confirmed: bool,
    review_digest: str | None = None,
    reviewed_private_drafts_path: Path | None = None,
    as_of: date | None = None,
) -> dict[str, Any]:
    report_date = as_of or _utc_today()
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
    _validate_review_binding_options(
        review_digest=review_digest,
        private_drafts_path=reviewed_private_drafts_path,
    )

    _require_private_live_path(path, label="outreach ledger")
    if reviewed_private_drafts_path is not None:
        _require_private_live_path(
            reviewed_private_drafts_path,
            label="reviewed private draft notes",
        )
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
    _verify_next_outreach_review(
        rows,
        as_of=report_date,
        review_digest=review_digest,
        private_drafts_path=reviewed_private_drafts_path,
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


def decline_next_outreach_draft(
    path: Path,
    *,
    prospect_id: str,
    decline_confirmed: bool,
    review_digest: str | None = None,
    reviewed_private_drafts_path: Path | None = None,
    as_of: date | None = None,
) -> dict[str, Any]:
    report_date = as_of or _utc_today()
    if type(report_date) is not date:
        raise OutreachInputError("as-of must be a date")
    if decline_confirmed is not True:
        raise OutreachInputError(
            "--decline-next requires --confirm-not-send after a human decides "
            "the draft must not be sent"
        )
    if not PROSPECT_ID_PATTERN.fullmatch(prospect_id):
        raise OutreachInputError("prospect_id must match prospect-NNN")
    _validate_review_binding_options(
        review_digest=review_digest,
        private_drafts_path=reviewed_private_drafts_path,
    )

    _require_private_live_path(path, label="outreach ledger")
    if reviewed_private_drafts_path is not None:
        _require_private_live_path(
            reviewed_private_drafts_path,
            label="reviewed private draft notes",
        )
    rows = _load_outreach_rows(path)
    build_outreach_report(rows, as_of=report_date)
    next_draft = _next_status_row(rows, "drafted")
    if next_draft is None:
        raise OutreachInputError("no drafted prospects await a review decision")
    if next_draft["prospect_id"] != prospect_id:
        raise OutreachInputError(
            f"next drafted prospect is {next_draft['prospect_id']}; "
            "review and decide it first"
        )
    _verify_next_outreach_review(
        rows,
        as_of=report_date,
        review_digest=review_digest,
        private_drafts_path=reviewed_private_drafts_path,
    )

    updated_rows = [dict(row) for row in rows]
    for row in updated_rows:
        if (row.get("prospect_id") or "").strip() == prospect_id:
            row["status"] = "review-declined"
            break

    updated_report = build_outreach_report(updated_rows, as_of=report_date)
    _write_outreach_rows(path, updated_rows)
    return {
        "schema_version": DECLINE_SCHEMA_VERSION,
        "as_of": report_date.isoformat(),
        "private_output": True,
        "human_no_send_confirmed": True,
        "queue": {
            "drafts_remaining": updated_report["summary"]["drafted"],
        },
        "decline": {
            "prospect_id": prospect_id,
            "status": "review-declined",
        },
        "action_note": (
            "The human no-send decision was recorded atomically. No outreach "
            "was approved or sent, and no contact or follow-up date was created."
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
    report_date = as_of or _utc_today()
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

    _require_private_live_path(path, label="outreach ledger")
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


def record_next_outreach_follow_up(
    path: Path,
    *,
    prospect_id: str,
    followed_up_on: date,
    send_confirmed: bool,
    as_of: date | None = None,
) -> dict[str, Any]:
    report_date = as_of or _utc_today()
    if type(report_date) is not date:
        raise OutreachInputError("as-of must be a date")
    if type(followed_up_on) is not date:
        raise OutreachInputError("followed-up-on must be a date")
    if send_confirmed is not True:
        raise OutreachInputError(
            "--record-follow-up requires --confirm-follow-up-sent after a "
            "human sends the one allowed follow-up"
        )
    if not PROSPECT_ID_PATTERN.fullmatch(prospect_id):
        raise OutreachInputError("prospect_id must match prospect-NNN")

    _require_private_live_path(path, label="outreach ledger")
    rows = _load_outreach_rows(path)
    build_outreach_report(rows, as_of=report_date)
    next_contacted = _next_contacted_row(rows)
    if next_contacted is None:
        raise OutreachInputError("no contacted prospects await a follow-up record")
    if next_contacted["prospect_id"] != prospect_id:
        raise OutreachInputError(
            f"next contacted prospect is {next_contacted['prospect_id']} "
            f"due {next_contacted['next_action_on']}; record it first"
        )

    updated_rows = [dict(row) for row in rows]
    for row in updated_rows:
        if (row.get("prospect_id") or "").strip() == prospect_id:
            row["status"] = "followed-up"
            row["followed_up_on"] = followed_up_on.isoformat()
            row["next_action_on"] = ""
            break

    build_outreach_report(updated_rows, as_of=report_date)
    _write_outreach_rows(path, updated_rows)
    return {
        "schema_version": FOLLOW_UP_SCHEMA_VERSION,
        "as_of": report_date.isoformat(),
        "private_output": True,
        "human_follow_up_confirmed": True,
        "follow_up": {
            "prospect_id": prospect_id,
            "status": "followed-up",
        },
        "action_note": (
            "The human-confirmed follow-up was recorded atomically. Repo "
            "Scout sent nothing and scheduled no additional message."
        ),
    }


def record_outreach_outcome(
    path: Path,
    *,
    prospect_id: str,
    outcome: str,
    outcome_confirmed: bool,
    as_of: date | None = None,
) -> dict[str, Any]:
    report_date = as_of or _utc_today()
    if type(report_date) is not date:
        raise OutreachInputError("as-of must be a date")
    if outcome_confirmed is not True:
        raise OutreachInputError(
            "--record-outcome requires --confirm-outcome-observed after a human "
            "observes the response or stop condition"
        )
    if not PROSPECT_ID_PATTERN.fullmatch(prospect_id):
        raise OutreachInputError("prospect_id must match prospect-NNN")
    if outcome not in OUTCOME_STATUSES:
        raise OutreachInputError(
            f"outcome must be one of: {', '.join(OUTCOME_STATUSES)}"
        )

    _require_private_live_path(path, label="outreach ledger")
    rows = _load_outreach_rows(path)
    build_outreach_report(rows, as_of=report_date)
    selected = next(
        (
            {field: (row.get(field) or "").strip() for field in LEDGER_FIELDS}
            for row in rows
            if (row.get("prospect_id") or "").strip() == prospect_id
        ),
        None,
    )
    if selected is None:
        raise OutreachInputError("prospect_id is not present in the outreach ledger")
    current_status = selected["status"]
    if current_status not in OUTCOME_SOURCE_STATUSES:
        raise OutreachInputError(
            f"prospect status {current_status} cannot record an outcome; expected "
            "contacted, followed-up, or replied"
        )
    if current_status == outcome:
        raise OutreachInputError(f"prospect already has outcome {outcome}")

    updated_rows = [dict(row) for row in rows]
    for row in updated_rows:
        if (row.get("prospect_id") or "").strip() == prospect_id:
            row["status"] = outcome
            row["next_action_on"] = ""
            break

    build_outreach_report(updated_rows, as_of=report_date)
    _write_outreach_rows(path, updated_rows)
    return {
        "schema_version": OUTCOME_SCHEMA_VERSION,
        "as_of": report_date.isoformat(),
        "private_output": True,
        "human_outcome_confirmed": True,
        "outcome": {
            "prospect_id": prospect_id,
            "status": outcome,
        },
        "action_note": (
            "The human-observed outcome was recorded atomically. Repo Scout sent "
            "nothing, scheduled no further message, and created no public pilot "
            "request or revenue evidence."
        ),
    }


def _require_private_live_path(path: Path, *, label: str) -> None:
    protected_path = path.parent.resolve() / path.name
    if protected_path.is_symlink():
        raise OutreachInputError(
            f"{label} must not be a symbolic link for live outreach actions"
        )
    _require_owner_only_permissions(protected_path, label=label)
    try:
        worktree = subprocess.run(
            [
                "git",
                "-C",
                str(protected_path.parent),
                "rev-parse",
                "--show-toplevel",
            ],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
        )
    except OSError:
        return
    if worktree.returncode != 0:
        return

    worktree_root = Path(worktree.stdout.strip()).resolve()
    try:
        relative_path = protected_path.relative_to(worktree_root).as_posix()
    except ValueError:
        return

    tracked = subprocess.run(
        [
            "git",
            "-C",
            str(worktree_root),
            "ls-files",
            "--error-unmatch",
            "--",
            relative_path,
        ],
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    ignored = subprocess.run(
        [
            "git",
            "-C",
            str(worktree_root),
            "check-ignore",
            "--quiet",
            "--",
            relative_path,
        ],
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    if tracked.returncode == 0 or ignored.returncode != 0:
        raise OutreachInputError(
            f"{label} inside a Git worktree must be ignored and untracked "
            "before live outreach actions"
        )


def _require_owner_only_permissions(path: Path, *, label: str) -> None:
    if os.name != "posix":
        return

    try:
        path_stat = path.stat()
    except FileNotFoundError:
        return
    except OSError as exc:
        raise OutreachInputError(
            f"cannot inspect {label} permissions: {exc}"
        ) from exc

    if not stat.S_ISREG(path_stat.st_mode):
        raise OutreachInputError(
            f"{label} must be a regular file for live outreach actions"
        )
    if path_stat.st_mode & (stat.S_IRWXG | stat.S_IRWXO):
        raise OutreachInputError(
            f"{label} must use owner-only file permissions (chmod 600) "
            "before live outreach actions"
        )

    try:
        parent_stat = path.parent.stat()
    except OSError as exc:
        raise OutreachInputError(
            f"cannot inspect {label} parent permissions: {exc}"
        ) from exc
    if parent_stat.st_mode & (stat.S_IRWXG | stat.S_IRWXO):
        raise OutreachInputError(
            f"{label} parent directory must use owner-only permissions "
            "(chmod 700) before live outreach actions"
        )


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


def _load_private_drafts(path: Path) -> dict[str, str]:
    try:
        if path.stat().st_size > MAX_PRIVATE_DRAFT_BYTES:
            raise OutreachInputError(
                f"private draft notes exceed {MAX_PRIVATE_DRAFT_BYTES} bytes"
            )
        text = path.read_text(encoding="utf-8")
    except OutreachInputError:
        raise
    except (OSError, UnicodeError) as exc:
        raise OutreachInputError(f"cannot read private draft notes: {exc}") from exc

    if any(
        (ord(character) < 32 and character not in "\n\r\t")
        or ord(character) == 127
        for character in text
    ):
        raise OutreachInputError(
            "private draft notes cannot contain control characters"
        )

    drafts: dict[str, str] = {}
    current_id: str | None = None
    current_lines: list[str] = []

    def finish_section() -> None:
        if current_id is None:
            return
        content = "\n".join(current_lines).strip()
        if not content:
            raise OutreachInputError(
                f"private draft section {current_id} cannot be empty"
            )
        drafts[current_id] = content

    for line_number, line in enumerate(text.splitlines(), start=1):
        if line.startswith("## "):
            match = PRIVATE_DRAFT_HEADING_PATTERN.fullmatch(line)
            if match is None:
                raise OutreachInputError(
                    f"private draft notes line {line_number}: section heading "
                    "must be ## prospect-NNN"
                )
            finish_section()
            current_id = match.group(1)
            if current_id in drafts:
                raise OutreachInputError(
                    f"private draft notes contain duplicate section: {current_id}"
                )
            current_lines = []
        elif current_id is not None:
            current_lines.append(line)
    finish_section()

    if not drafts:
        raise OutreachInputError(
            "private draft notes must contain at least one ## prospect-NNN section"
        )
    return drafts


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
            if (
                status in {"drafted", "review-declined", "approved"}
                and channel not in CHANNELS
            ):
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

        if status in {"researched", "drafted", "review-declined"}:
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
    closed = (
        status_counts["review-declined"]
        + status_counts["not-a-fit"]
        + status_counts["do-not-contact"]
    )
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
            "review_declined": status_counts["review-declined"],
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
    rows: list[dict[str, str | None]],
    *,
    as_of: date,
    include_private_evidence: bool = False,
    private_drafts: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    build_outreach_report(rows, as_of=as_of)
    if private_drafts is not None:
        ledger_ids = {
            (row.get("prospect_id") or "").strip() for row in rows
        }
        drafted_ids = {
            (row.get("prospect_id") or "").strip()
            for row in rows
            if (row.get("status") or "").strip() == "drafted"
        }
        note_ids = set(private_drafts)
        missing_ids = sorted(drafted_ids - note_ids)
        if missing_ids:
            raise OutreachInputError(
                "private draft notes are missing a drafted section: "
                f"{missing_ids[0]}"
            )
        unknown_ids = sorted(note_ids - ledger_ids)
        if unknown_ids:
            raise OutreachInputError(
                "private draft notes contain a section absent from the ledger: "
                f"{unknown_ids[0]}"
            )
    draft = _next_status_row(rows, "drafted")
    review = None
    review_digest = None
    private_evidence_included = include_private_evidence and draft is not None
    private_draft_included = private_drafts is not None and draft is not None
    if draft is not None:
        private_evidence = []
        if private_evidence_included:
            evidence = _fit_evidence(draft["fit_evidence"], row_number=2)
            private_evidence = [
                {"signal": signal, "url": evidence[signal]}
                for signal in sorted(evidence)
            ]
        review = {
            "prospect_id": draft["prospect_id"],
            "channel": draft["channel"],
            "fit_signals": len(draft["fit_signals"].split(";")),
            "fit_evidence_links": len(draft["fit_evidence"].split(";")),
            "checks": list(HUMAN_REVIEW_CHECKS),
        }
        if private_evidence_included:
            review["private_evidence"] = private_evidence
        if private_draft_included:
            private_draft = private_drafts.get(draft["prospect_id"])
            if not isinstance(private_draft, str) or not private_draft.strip():
                raise OutreachInputError(
                    "private draft notes are missing a drafted section: "
                    f"{draft['prospect_id']}"
                )
            review["private_draft"] = private_draft.strip()
        if private_evidence_included and private_draft_included:
            review_digest = _build_outreach_review_digest(
                draft,
                private_draft=review["private_draft"],
                as_of=as_of,
            )
    return {
        "schema_version": REVIEW_SCHEMA_VERSION,
        "as_of": as_of.isoformat(),
        "human_review_required": True,
        "private_output": True,
        "private_evidence_included": private_evidence_included,
        "private_draft_included": private_draft_included,
        "review_digest": review_digest,
        "review": review,
        "action_note": (
            "This checklist does not approve, modify, or send outreach. "
            + _private_review_disclosure_note(
                evidence_included=private_evidence_included,
                draft_included=private_draft_included,
            )
        ),
    }


def _build_outreach_review_digest(
    draft: Mapping[str, str],
    *,
    private_draft: str,
    as_of: date,
) -> str:
    payload = {
        "as_of": as_of.isoformat(),
        "checks": list(HUMAN_REVIEW_CHECKS),
        "ledger_row": {field: draft[field] for field in LEDGER_FIELDS},
        "private_draft": private_draft,
        "review_schema_version": REVIEW_SCHEMA_VERSION,
    }
    encoded = json.dumps(
        payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return f"sha256:{sha256(encoded).hexdigest()}"


def _validate_review_binding_options(
    *,
    review_digest: str | None,
    private_drafts_path: Path | None,
) -> None:
    if (review_digest is None) != (private_drafts_path is None):
        raise OutreachInputError(
            "content-bound decisions require both --review-digest and "
            "--reviewed-private-draft"
        )
    if review_digest is not None and not REVIEW_DIGEST_PATTERN.fullmatch(
        review_digest
    ):
        raise OutreachInputError(
            "--review-digest must match sha256:<64 lowercase hex digits>"
        )


def _verify_next_outreach_review(
    rows: list[dict[str, str | None]],
    *,
    as_of: date,
    review_digest: str | None,
    private_drafts_path: Path | None,
) -> None:
    if review_digest is None or private_drafts_path is None:
        return
    current_review = build_next_outreach_review(
        rows,
        as_of=as_of,
        include_private_evidence=True,
        private_drafts=_load_private_drafts(private_drafts_path),
    )
    current_digest = current_review["review_digest"]
    if not isinstance(current_digest, str) or not compare_digest(
        current_digest, review_digest
    ):
        raise OutreachInputError(
            "review content changed; run --review-next again before deciding"
        )


def _private_review_disclosure_note(
    *, evidence_included: bool, draft_included: bool
) -> str:
    if evidence_included and draft_included:
        return "Private evidence links and draft notes are included for human review."
    if evidence_included:
        return "Private evidence links are included only for human review."
    if draft_included:
        return "Private draft notes are included only for human review."
    return "Private evidence links and draft notes remain redacted."


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


def _next_contacted_row(
    rows: list[dict[str, str | None]],
) -> dict[str, str] | None:
    contacted_rows = sorted(
        (
            {field: (raw_row.get(field) or "").strip() for field in LEDGER_FIELDS}
            for raw_row in rows
            if (raw_row.get("status") or "").strip() == "contacted"
        ),
        key=lambda row: (row["next_action_on"], row["prospect_id"]),
    )
    return contacted_rows[0] if contacted_rows else None


def format_outreach_report(report: dict[str, Any]) -> str:
    summary = report["summary"]
    experiment = report["experiment"]
    lines = [
        "Repo Scout outreach operations",
        f"As of: {report['as_of']}",
        f"Prospects: {summary['prospects']} / {experiment['max_prospects']}",
        f"Qualification links: {summary['fit_evidence_links']}",
        f"Drafts awaiting review: {summary['drafted']}",
        f"Declined before contact: {summary['review_declined']}",
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


def format_next_outreach_review(
    review_report: dict[str, Any],
    *,
    ledger: Path,
    private_drafts_path: Path | None = None,
) -> str:
    review = review_report["review"]
    review_digest = review_report["review_digest"]
    if review_digest is not None and private_drafts_path is None:
        raise OutreachInputError(
            "content-bound review formatting requires the private draft path"
        )
    decision_guard = (
        (
            "--review-digest",
            review_digest,
            "--reviewed-private-draft",
            str(private_drafts_path),
        )
        if review_digest is not None
        else ()
    )
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
                *(
                    [
                        "Private evidence (do not commit or share):",
                        *(
                            f"- {item['signal']}: {item['url']}"
                            for item in review.get("private_evidence", [])
                        ),
                    ]
                    if review_report["private_evidence_included"]
                    else []
                ),
                *(
                    [
                        "Private draft notes (do not commit or share):",
                        review["private_draft"],
                    ]
                    if review_report["private_draft_included"]
                    else []
                ),
                "Human checks:",
                *(f"- [ ] {check}" for check in review["checks"]),
                *(
                    [f"Content-bound review receipt: {review_digest}"]
                    if review_digest is not None
                    else []
                ),
                "After human review, choose exactly one decision:",
                "Approve for manual sending:",
                _format_outreach_command(
                    ledger,
                    "--as-of",
                    review_report["as_of"],
                    "--approve-next",
                    review["prospect_id"],
                    "--approved-on",
                    review_report["as_of"],
                    "--confirm-reviewed",
                    *decision_guard,
                ),
                "Decline without sending:",
                _format_outreach_command(
                    ledger,
                    "--as-of",
                    review_report["as_of"],
                    "--decline-next",
                    review["prospect_id"],
                    "--confirm-not-send",
                    *decision_guard,
                ),
            ]
        )
    if review_report["private_evidence_included"] and review_report[
        "private_draft_included"
    ]:
        privacy_description = "evidence-and-draft review"
    elif review_report["private_evidence_included"]:
        privacy_description = "evidence-bearing review"
    elif review_report["private_draft_included"]:
        privacy_description = "draft-bearing review"
    else:
        privacy_description = "alias-only checklist"
    lines.append(
        f"Privacy: Keep this {privacy_description} in the private workspace."
    )
    lines.append(f"Boundary: {review_report['action_note']}")
    return "\n".join(lines)


def format_outreach_approval(
    approval_report: dict[str, Any], *, ledger: Path
) -> str:
    approval = approval_report["approval"]
    lines = [
        "Repo Scout outreach approval",
        f"As of: {approval_report['as_of']}",
        f"Prospect alias: {approval['prospect_id']}",
        f"Status: {approval['status']}",
        "Private ledger updated atomically.",
        f"Boundary: {approval_report['action_note']}",
        "Next: send this one message manually, then record that send:",
        _format_outreach_command(
            ledger,
            "--as-of",
            approval_report["as_of"],
            "--record-contact",
            approval["prospect_id"],
            "--contacted-on",
            approval_report["as_of"],
            "--confirm-sent",
        ),
    ]
    return "\n".join(lines)


def format_outreach_decline(
    decline_report: dict[str, Any], *, ledger: Path
) -> str:
    decline = decline_report["decline"]
    drafts_remaining = decline_report["queue"]["drafts_remaining"]
    lines = [
        "Repo Scout outreach review decline",
        f"As of: {decline_report['as_of']}",
        f"Prospect alias: {decline['prospect_id']}",
        f"Status: {decline['status']}",
        "Private ledger updated atomically.",
        f"Boundary: {decline_report['action_note']}",
        f"Drafts remaining: {drafts_remaining}",
    ]
    if drafts_remaining:
        lines.extend(
            [
                "Next: review the next drafted prospect:",
                _format_outreach_command(
                    ledger,
                    "--as-of",
                    decline_report["as_of"],
                    "--review-next",
                ),
            ]
        )
    else:
        lines.append(
            "Review queue complete: no drafted prospects remain for human review."
        )
    return "\n".join(lines)


def format_outreach_contact(
    contact_report: dict[str, Any], *, ledger: Path
) -> str:
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
            "Next: record any observed response or stop condition with "
            "--record-outcome. If none arrives, follow up manually on the due "
            "date, then record it:"
        ),
        _format_outreach_command(
            ledger,
            "--as-of",
            contact["follow_up_due"],
            "--record-follow-up",
            contact["prospect_id"],
            "--followed-up-on",
            contact["follow_up_due"],
            "--confirm-follow-up-sent",
        ),
    ]
    return "\n".join(lines)


def _format_outreach_command(ledger: Path, *arguments: str) -> str:
    return shlex.join(
        ["repo-scout-outreach", *arguments, "--", str(ledger)]
    )


def format_outreach_follow_up(follow_up_report: dict[str, Any]) -> str:
    follow_up = follow_up_report["follow_up"]
    lines = [
        "Repo Scout outreach follow-up record",
        f"As of: {follow_up_report['as_of']}",
        f"Prospect alias: {follow_up['prospect_id']}",
        f"Status: {follow_up['status']}",
        "Private ledger updated atomically.",
        f"Boundary: {follow_up_report['action_note']}",
        (
            "Next: wait for a response, record it with --record-outcome, and "
            "stop immediately after an opt-out or not-interested response."
        ),
    ]
    return "\n".join(lines)


def format_outreach_outcome(outcome_report: dict[str, Any]) -> str:
    outcome = outcome_report["outcome"]
    if outcome["status"] == "replied":
        next_step = (
            "Next: assess the reply, then record a more specific outcome only "
            "after a human observes it."
        )
    elif outcome["status"] == "pilot-requested":
        next_step = (
            "Next: ask the prospect to submit the public pilot intake before "
            "counting the request as public demand or revenue evidence."
        )
    else:
        next_step = "Next: stop contact; no further message is scheduled."
    lines = [
        "Repo Scout outreach outcome record",
        f"As of: {outcome_report['as_of']}",
        f"Prospect alias: {outcome['prospect_id']}",
        f"Status: {outcome['status']}",
        "Follow-up cadence closed.",
        "Private ledger updated atomically.",
        f"Boundary: {outcome_report['action_note']}",
        next_step,
    ]
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="repo-scout-outreach",
        description=(
            "Validate a private outreach ledger, review drafts, record human "
            "review decisions, contacts, follow-ups, and observed outcomes, "
            "and report bounded activity."
        ),
    )
    add_version_argument(parser)
    parser.add_argument("ledger", type=Path, help="Path to the private outreach CSV.")
    parser.add_argument(
        "--as-of",
        type=_date_argument,
        default=_utc_today(),
        metavar="YYYY-MM-DD",
        help="Report date. Defaults to the current UTC calendar date.",
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
        "--decline-next",
        metavar="PROSPECT_ID",
        help=(
            "Record a human decision not to send the next reviewed draft, "
            "without creating contact activity."
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
    action_group.add_argument(
        "--record-follow-up",
        metavar="PROSPECT_ID",
        help=(
            "After a human sends it, record the one allowed follow-up for "
            "the earliest due contacted prospect."
        ),
    )
    action_group.add_argument(
        "--record-outcome",
        metavar="PROSPECT_ID",
        help=(
            "Record a human-observed reply, pilot request, rejection, or opt-out "
            "for a contacted prospect."
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
        "--confirm-not-send",
        action="store_true",
        help=(
            "Confirm a human decided the selected draft must not be sent. "
            "Required with --decline-next."
        ),
    )
    parser.add_argument(
        "--review-digest",
        metavar="SHA256",
        help=(
            "Content-bound receipt emitted by a complete --review-next bundle. "
            "Use with --reviewed-private-draft when approving or declining."
        ),
    )
    parser.add_argument(
        "--reviewed-private-draft",
        type=Path,
        metavar="DRAFTS_MD",
        help=(
            "Private draft notes used for a content-bound review. Required "
            "with --review-digest."
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
        "--followed-up-on",
        type=_date_argument,
        metavar="YYYY-MM-DD",
        help="Human follow-up send date. Required with --record-follow-up.",
    )
    parser.add_argument(
        "--confirm-follow-up-sent",
        action="store_true",
        help=(
            "Confirm a human already sent the one allowed follow-up. "
            "Required with --record-follow-up."
        ),
    )
    parser.add_argument(
        "--outcome",
        choices=OUTCOME_STATUSES,
        help="Observed status. Required with --record-outcome.",
    )
    parser.add_argument(
        "--confirm-outcome-observed",
        action="store_true",
        help=(
            "Confirm a human observed the response or stop condition. Required "
            "with --record-outcome."
        ),
    )
    parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Output format. Defaults to text.",
    )
    parser.add_argument(
        "--include-private-evidence",
        action="store_true",
        help=(
            "With --review-next, include the selected draft's private fit "
            "evidence links. Never use for committed output."
        ),
    )
    parser.add_argument(
        "--include-private-draft",
        type=Path,
        metavar="DRAFTS_MD",
        help=(
            "With --review-next, include the selected ## prospect-NNN "
            "section from bounded private Markdown notes."
        ),
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    approval_options = args.approved_on is not None or args.confirm_reviewed
    decline_options = args.confirm_not_send
    contact_options = args.contacted_on is not None or args.confirm_sent
    follow_up_options = (
        args.followed_up_on is not None or args.confirm_follow_up_sent
    )
    outcome_options = args.outcome is not None or args.confirm_outcome_observed
    try:
        if args.include_private_evidence and not args.review_next:
            raise OutreachInputError(
                "--include-private-evidence requires --review-next"
            )
        if args.include_private_draft is not None and not args.review_next:
            raise OutreachInputError(
                "--include-private-draft requires --review-next"
            )
        _validate_review_binding_options(
            review_digest=args.review_digest,
            private_drafts_path=args.reviewed_private_draft,
        )
        if (
            args.review_digest is not None
            and args.approve_next is None
            and args.decline_next is None
        ):
            raise OutreachInputError(
                "--review-digest requires --approve-next or --decline-next"
            )
        if args.record_outcome is None and outcome_options:
            raise OutreachInputError(
                "--outcome and --confirm-outcome-observed require --record-outcome"
            )
        if args.approve_next is not None:
            if decline_options:
                raise OutreachInputError(
                    "--confirm-not-send requires --decline-next"
                )
            if contact_options:
                raise OutreachInputError(
                    "--contacted-on and --confirm-sent require --record-contact"
                )
            if follow_up_options:
                raise OutreachInputError(
                    "--followed-up-on and --confirm-follow-up-sent require "
                    "--record-follow-up"
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
                review_digest=args.review_digest,
                reviewed_private_drafts_path=args.reviewed_private_draft,
                as_of=args.as_of,
            )
        elif args.decline_next is not None:
            if approval_options:
                raise OutreachInputError(
                    "--approved-on and --confirm-reviewed require --approve-next"
                )
            if contact_options:
                raise OutreachInputError(
                    "--contacted-on and --confirm-sent require --record-contact"
                )
            if follow_up_options:
                raise OutreachInputError(
                    "--followed-up-on and --confirm-follow-up-sent require "
                    "--record-follow-up"
                )
            report = decline_next_outreach_draft(
                args.ledger,
                prospect_id=args.decline_next,
                decline_confirmed=args.confirm_not_send,
                review_digest=args.review_digest,
                reviewed_private_drafts_path=args.reviewed_private_draft,
                as_of=args.as_of,
            )
        elif args.record_contact is not None:
            if decline_options:
                raise OutreachInputError(
                    "--confirm-not-send requires --decline-next"
                )
            if approval_options:
                raise OutreachInputError(
                    "--approved-on and --confirm-reviewed require --approve-next"
                )
            if follow_up_options:
                raise OutreachInputError(
                    "--followed-up-on and --confirm-follow-up-sent require "
                    "--record-follow-up"
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
        elif args.record_follow_up is not None:
            if decline_options:
                raise OutreachInputError(
                    "--confirm-not-send requires --decline-next"
                )
            if approval_options:
                raise OutreachInputError(
                    "--approved-on and --confirm-reviewed require --approve-next"
                )
            if contact_options:
                raise OutreachInputError(
                    "--contacted-on and --confirm-sent require --record-contact"
                )
            if args.followed_up_on is None:
                raise OutreachInputError(
                    "--record-follow-up requires --followed-up-on YYYY-MM-DD"
                )
            report = record_next_outreach_follow_up(
                args.ledger,
                prospect_id=args.record_follow_up,
                followed_up_on=args.followed_up_on,
                send_confirmed=args.confirm_follow_up_sent,
                as_of=args.as_of,
            )
        elif args.record_outcome is not None:
            if decline_options:
                raise OutreachInputError(
                    "--confirm-not-send requires --decline-next"
                )
            if approval_options:
                raise OutreachInputError(
                    "--approved-on and --confirm-reviewed require --approve-next"
                )
            if contact_options:
                raise OutreachInputError(
                    "--contacted-on and --confirm-sent require --record-contact"
                )
            if follow_up_options:
                raise OutreachInputError(
                    "--followed-up-on and --confirm-follow-up-sent require "
                    "--record-follow-up"
                )
            if args.outcome is None:
                raise OutreachInputError(
                    "--record-outcome requires --outcome STATUS"
                )
            report = record_outreach_outcome(
                args.ledger,
                prospect_id=args.record_outcome,
                outcome=args.outcome,
                outcome_confirmed=args.confirm_outcome_observed,
                as_of=args.as_of,
            )
        elif approval_options:
            raise OutreachInputError(
                "--approved-on and --confirm-reviewed require --approve-next"
            )
        elif decline_options:
            raise OutreachInputError("--confirm-not-send requires --decline-next")
        elif contact_options:
            raise OutreachInputError(
                "--contacted-on and --confirm-sent require --record-contact"
            )
        elif follow_up_options:
            raise OutreachInputError(
                "--followed-up-on and --confirm-follow-up-sent require "
                "--record-follow-up"
            )
        elif args.review_next:
            report = load_next_outreach_review(
                args.ledger,
                as_of=args.as_of,
                include_private_evidence=args.include_private_evidence,
                private_drafts_path=args.include_private_draft,
            )
        else:
            report = load_outreach_report(args.ledger, as_of=args.as_of)
    except OutreachInputError as exc:
        print(f"repo-scout-outreach: {exc}", file=sys.stderr)
        return 2

    if args.format == "json":
        print(json.dumps(report, indent=2, sort_keys=True))
    elif args.record_outcome is not None:
        print(format_outreach_outcome(report))
    elif args.record_follow_up is not None:
        print(format_outreach_follow_up(report))
    elif args.record_contact is not None:
        print(format_outreach_contact(report, ledger=args.ledger))
    elif args.approve_next is not None:
        print(format_outreach_approval(report, ledger=args.ledger))
    elif args.decline_next is not None:
        print(format_outreach_decline(report, ledger=args.ledger))
    elif args.review_next:
        print(
            format_next_outreach_review(
                report,
                ledger=args.ledger,
                private_drafts_path=args.include_private_draft,
            )
        )
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


def _utc_today() -> date:
    return datetime.now(timezone.utc).date()


if __name__ == "__main__":
    raise SystemExit(main())
