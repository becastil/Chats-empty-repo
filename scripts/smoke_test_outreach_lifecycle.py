from __future__ import annotations

import argparse
import csv
import json
import os
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
from typing import Any, Mapping, Sequence


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
SIGNALS = "team_5_50;multi_repo;agent_use"
EVIDENCE = (
    "team_5_50=https://evidence.example/team;"
    "multi_repo=https://evidence.example/repositories;"
    "agent_use=https://evidence.example/agents"
)


class SmokeTestError(RuntimeError):
    """Raised when installed outreach behavior violates its release contract."""


def verify_outreach_lifecycle(
    python: str | Path,
    *,
    command_directory: str | Path | None = None,
    environment: Mapping[str, str] | None = None,
) -> tuple[str, ...]:
    python_command = str(Path(python))
    outreach_command = _outreach_command(
        python_command,
        command_directory=command_directory,
    )
    checked: list[str] = []

    with TemporaryDirectory() as tmp:
        ledger = Path(tmp) / "outreach-ledger.csv"
        draft = _row(
            contacted_on="",
            status="drafted",
            next_action_on="",
            approved_on="",
        )
        _write_ledger(ledger, draft)
        ledger.chmod(0o600)
        draft_bytes = ledger.read_bytes()
        private_drafts = Path(tmp) / "drafts.md"
        private_drafts.write_text(
            "# Private drafts\n\n"
            "## prospect-002\n\nOther private message\n\n"
            f"## {draft['prospect_id']}\n\nSelected private message\n",
            encoding="utf-8",
        )

        review = _json_command(
            outreach_command,
            ledger,
            as_of="2026-07-02",
            arguments=("--review-next",),
            environment=environment,
        )
        _require(ledger.read_bytes() == draft_bytes, "review modified the ledger")
        _require(review.get("private_output") is True, "review was not private")
        _require(
            review.get("review", {}).get("prospect_id") == draft["prospect_id"],
            "review did not select the synthetic draft",
        )
        _require(
            len(review.get("review", {}).get("checks", ())) == 5,
            "review checklist changed",
        )
        _require_private_values_absent(
            review,
            ("https://evidence.example",),
            context="review",
        )
        checked.append("draft-reviewed")

        evidence_review = _json_command(
            outreach_command,
            ledger,
            as_of="2026-07-02",
            arguments=(
                "--review-next",
                "--include-private-evidence",
                "--include-private-draft",
                str(private_drafts),
            ),
            environment=environment,
        )
        _require(
            ledger.read_bytes() == draft_bytes,
            "private evidence review modified the ledger",
        )
        _require(
            evidence_review.get("private_evidence_included") is True,
            "private evidence review did not mark its disclosure",
        )
        _require(
            evidence_review.get("private_draft_included") is True,
            "private draft review did not mark its disclosure",
        )
        disclosed_evidence = evidence_review.get("review", {}).get(
            "private_evidence", ()
        )
        _require(
            len(disclosed_evidence) == 3,
            "private evidence review did not disclose all qualification links",
        )
        disclosed_urls = {item.get("url") for item in disclosed_evidence}
        _require(
            disclosed_urls
            == {
                "https://evidence.example/agents",
                "https://evidence.example/repositories",
                "https://evidence.example/team",
            },
            "private evidence review disclosed unexpected links",
        )
        private_draft = evidence_review.get("review", {}).get("private_draft")
        _require(
            private_draft == "Selected private message",
            "private review did not select the synthetic draft notes",
        )
        _require(
            "Other private message" not in json.dumps(evidence_review),
            "private review exposed a different prospect's draft notes",
        )
        checked.append("private-review-bundle")

        unconfirmed = _run(
            outreach_command,
            ledger,
            as_of="2026-07-02",
            arguments=(
                "--approve-next",
                draft["prospect_id"],
                "--approved-on",
                "2026-07-01",
            ),
            environment=environment,
            expected_exit_code=2,
        )
        _require(
            "requires --confirm-reviewed" in unconfirmed.stderr,
            "unconfirmed approval did not produce its controlled error",
        )
        _require(
            ledger.read_bytes() == draft_bytes,
            "unconfirmed approval modified the ledger",
        )
        _require(
            "https://evidence.example" not in unconfirmed.stderr,
            "unconfirmed-approval error exposed evidence",
        )
        checked.append("unconfirmed-approval-rejected")

        approval = _json_command(
            outreach_command,
            ledger,
            as_of="2026-07-02",
            arguments=(
                "--approve-next",
                draft["prospect_id"],
                "--approved-on",
                "2026-07-01",
                "--confirm-reviewed",
            ),
            environment=environment,
        )
        _require(
            ledger.stat().st_mode & 0o777 == 0o600,
            "approval changed ledger permissions",
        )
        _require(
            approval.get("human_review_confirmed") is True,
            "approval confirmation is missing",
        )
        _require(
            approval.get("approval", {}).get("status") == "approved",
            "draft was not approved",
        )
        _require_private_values_absent(
            approval,
            (draft["approved_on"], "2026-07-01", "https://evidence.example"),
            context="approval receipt",
        )
        approved_report = _report(
            outreach_command,
            ledger,
            as_of="2026-07-02",
            environment=environment,
        )
        _require(approved_report.get("schema_version") == 5, "schema changed")
        _require(
            approved_report.get("experiment", {}).get("human_approval_required")
            is True,
            "human approval flag is missing",
        )
        approved_summary = approved_report.get("summary", {})
        _require(approved_summary.get("approved") == 1, "approval was not counted")
        _require(
            approved_summary.get("attempted_prospects") == 0,
            "approval was counted as a contact attempt",
        )
        serialized = json.dumps(approved_report, sort_keys=True)
        for private_value in (
            draft["prospect_id"],
            "2026-07-01",
            "https://evidence.example",
        ):
            _require(
                private_value not in serialized,
                "approved report exposed private ledger data",
            )
        approved_row = _read_row(ledger)
        _require(approved_row["status"] == "approved", "approval was not saved")
        _require(
            approved_row["approved_on"] == "2026-07-01",
            "approval date was not saved",
        )
        _require(
            not approved_row["contacted_on"] and not approved_row["next_action_on"],
            "approval created contact activity",
        )
        checked.append("draft-approved")

        contact = _json_command(
            outreach_command,
            ledger,
            as_of="2026-07-04",
            arguments=(
                "--record-contact",
                draft["prospect_id"],
                "--contacted-on",
                "2026-07-03",
                "--confirm-sent",
            ),
            environment=environment,
        )
        _require(
            contact.get("human_send_confirmed") is True,
            "contact confirmation is missing",
        )
        _require(
            contact.get("contact", {}).get("follow_up_due") == "2026-07-10",
            "contact did not create the exact seven-day follow-up",
        )
        _require_private_values_absent(
            contact,
            ("2026-07-01", "2026-07-03", "https://evidence.example"),
            context="contact receipt",
        )
        contacted_report = _report(
            outreach_command,
            ledger,
            as_of="2026-07-04",
            environment=environment,
        )
        contacted_summary = contacted_report.get("summary", {})
        _require(
            contacted_summary.get("contacted") == 1,
            "contacted prospect was not counted",
        )
        _require(
            contacted_summary.get("attempted_prospects") == 1,
            "contact attempt total changed",
        )
        _require(
            contacted_summary.get("due_followups") == 0,
            "future follow-up was reported as due",
        )
        contacted_row = _read_row(ledger)
        _require(
            contacted_row["approved_on"] == "2026-07-01",
            "contact discarded approval evidence",
        )
        _require(
            contacted_row["contacted_on"] == "2026-07-03",
            "contact date was not saved",
        )
        _require(
            contacted_row["next_action_on"] == "2026-07-10",
            "follow-up date was not saved",
        )
        checked.append("contact-recorded")

        follow_up = _json_command(
            outreach_command,
            ledger,
            as_of="2026-07-11",
            arguments=(
                "--record-follow-up",
                draft["prospect_id"],
                "--followed-up-on",
                "2026-07-10",
                "--confirm-follow-up-sent",
            ),
            environment=environment,
        )
        _require(
            follow_up.get("human_follow_up_confirmed") is True,
            "follow-up confirmation is missing",
        )
        _require(
            follow_up.get("follow_up", {}).get("status") == "followed-up",
            "follow-up was not recorded",
        )
        _require_private_values_absent(
            follow_up,
            (
                "2026-07-01",
                "2026-07-03",
                "2026-07-10",
                "https://evidence.example",
            ),
            context="follow-up receipt",
        )
        followed_report = _report(
            outreach_command,
            ledger,
            as_of="2026-07-11",
            environment=environment,
        )
        followed_summary = followed_report.get("summary", {})
        _require(
            followed_summary.get("followed_up") == 1,
            "follow-up was not counted",
        )
        _require(
            followed_summary.get("attempted_prospects") == 1,
            "follow-up inflated the prospect attempt total",
        )
        _require(
            followed_summary.get("due_followups") == 0,
            "completed follow-up remained due",
        )
        followed_row = _read_row(ledger)
        _require(
            followed_row["approved_on"] == "2026-07-01"
            and followed_row["contacted_on"] == "2026-07-03",
            "follow-up discarded approval or contact evidence",
        )
        _require(
            followed_row["followed_up_on"] == "2026-07-10"
            and not followed_row["next_action_on"],
            "follow-up state was not saved safely",
        )
        checked.append("follow-up-recorded")

        followed_bytes = ledger.read_bytes()
        duplicate = _run(
            outreach_command,
            ledger,
            as_of="2026-07-11",
            arguments=(
                "--record-follow-up",
                draft["prospect_id"],
                "--followed-up-on",
                "2026-07-10",
                "--confirm-follow-up-sent",
            ),
            environment=environment,
            expected_exit_code=2,
        )
        _require(
            "no contacted prospects await a follow-up record" in duplicate.stderr,
            "duplicate follow-up did not produce its controlled error",
        )
        _require(
            ledger.read_bytes() == followed_bytes,
            "duplicate follow-up modified the ledger",
        )
        checked.append("duplicate-follow-up-rejected")

        _write_ledger(ledger, _row(approved_on=""))
        missing_approval = _run(
            outreach_command,
            ledger,
            as_of="2026-07-01",
            environment=environment,
            expected_exit_code=2,
        )
        _require(
            "approved_on is required after draft review" in missing_approval.stderr,
            "missing approval did not produce its controlled error",
        )
        _require(
            "https://evidence.example" not in missing_approval.stderr,
            "missing-approval error exposed evidence",
        )
        checked.append("missing-approval-rejected")

        _write_ledger(ledger, _row(), extra_value="private-extra-value")
        extra_column = _run(
            outreach_command,
            ledger,
            as_of="2026-07-01",
            environment=environment,
            expected_exit_code=2,
        )
        _require(
            "ledger row must have exactly 9 columns; found 10"
            in extra_column.stderr,
            "extra column did not produce its controlled error",
        )
        _require(
            "private-extra-value" not in extra_column.stderr,
            "row-width error exposed the extra value",
        )
        checked.append("extra-column-rejected")

    return tuple(checked)


def _outreach_command(
    python: str,
    *,
    command_directory: str | Path | None,
) -> tuple[str, ...]:
    if command_directory is None:
        return (python, "-m", "repo_scout.outreach")

    path = Path(command_directory) / "repo-scout-outreach"
    if not path.is_file() or not os.access(path, os.X_OK):
        raise SmokeTestError(
            f"installed command is missing or not executable: {path}"
        )
    return (str(path),)


def _row(**overrides: str) -> dict[str, str]:
    row = {
        "prospect_id": "prospect-001",
        "fit_signals": SIGNALS,
        "fit_evidence": EVIDENCE,
        "contacted_on": "2026-07-01",
        "channel": "published-business",
        "status": "contacted",
        "followed_up_on": "",
        "next_action_on": "2026-07-08",
        "approved_on": "2026-06-30",
    }
    row.update(overrides)
    return row


def _write_ledger(
    path: Path,
    row: Mapping[str, str],
    *,
    extra_value: str | None = None,
) -> None:
    with path.open("w", newline="", encoding="utf-8") as ledger_file:
        writer = csv.writer(ledger_file, lineterminator="\n")
        writer.writerow(LEDGER_FIELDS)
        values = [row[field] for field in LEDGER_FIELDS]
        if extra_value is not None:
            values.append(extra_value)
        writer.writerow(values)


def _read_row(path: Path) -> dict[str, str]:
    with path.open(newline="", encoding="utf-8") as ledger_file:
        rows = list(csv.DictReader(ledger_file))
    if len(rows) != 1:
        raise SmokeTestError("synthetic ledger did not contain exactly one row")
    return rows[0]


def _report(
    command: Sequence[str],
    ledger: Path,
    *,
    as_of: str,
    environment: Mapping[str, str] | None,
) -> dict[str, Any]:
    completed = _run(
        command,
        ledger,
        as_of=as_of,
        environment=environment,
        expected_exit_code=0,
    )
    try:
        report = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise SmokeTestError("outreach command did not emit valid JSON") from exc
    if not isinstance(report, dict):
        raise SmokeTestError("outreach command emitted a non-object report")
    return report


def _json_command(
    command: Sequence[str],
    ledger: Path,
    *,
    as_of: str,
    arguments: Sequence[str],
    environment: Mapping[str, str] | None,
) -> dict[str, Any]:
    completed = _run(
        command,
        ledger,
        as_of=as_of,
        arguments=arguments,
        environment=environment,
        expected_exit_code=0,
    )
    try:
        report = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise SmokeTestError("outreach action did not emit valid JSON") from exc
    if not isinstance(report, dict):
        raise SmokeTestError("outreach action emitted a non-object report")
    return report


def _run(
    command: Sequence[str],
    ledger: Path,
    *,
    as_of: str,
    arguments: Sequence[str] = (),
    environment: Mapping[str, str] | None,
    expected_exit_code: int,
) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(
        [
            *command,
            str(ledger),
            "--as-of",
            as_of,
            "--format",
            "json",
            *arguments,
        ],
        capture_output=True,
        text=True,
        env=dict(environment) if environment is not None else None,
    )
    if completed.returncode != expected_exit_code:
        detail = completed.stderr.strip() or completed.stdout.strip() or "no output"
        raise SmokeTestError(
            f"outreach command exited {completed.returncode}; "
            f"expected {expected_exit_code}: {detail}"
        )
    return completed


def _require_private_values_absent(
    report: Mapping[str, Any],
    private_values: Sequence[str],
    *,
    context: str,
) -> None:
    serialized = json.dumps(report, sort_keys=True)
    for private_value in private_values:
        if private_value:
            _require(
                private_value not in serialized,
                f"{context} exposed private ledger data",
            )


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise SmokeTestError(message)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Smoke test the installed Repo Scout outreach lifecycle."
    )
    parser.add_argument("--python", default=sys.executable)
    parser.add_argument(
        "--command-directory",
        type=Path,
        help="Directory containing the installed repo-scout-outreach command.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        checked = verify_outreach_lifecycle(
            args.python,
            command_directory=args.command_directory,
            environment=os.environ,
        )
    except SmokeTestError as exc:
        print(f"outreach lifecycle smoke test failed: {exc}", file=sys.stderr)
        return 1
    print("outreach lifecycle smoke test passed: " + ", ".join(checked))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
