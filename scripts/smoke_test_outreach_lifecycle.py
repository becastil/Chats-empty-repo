from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shlex
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
    "outcome_on",
)
SIGNALS = "team_5_50;multi_repo;agent_use"
EVIDENCE = (
    "team_5_50=https://evidence.example/team;"
    "multi_repo=https://evidence.example/repositories;"
    "agent_use=https://evidence.example/agents"
)
OPT_OUT_REVIEW_CHECK = (
    "Confirm the message gives a clear opt-out and promises no further contact."
)
SOURCE_ROUTE_REVIEW_CHECK = (
    "Confirm the message uses the source-preserving direct-outreach route "
    "shown above."
)
DIRECT_OUTREACH_ROUTE = (
    "https://repo-scout.becastil.chatgpt.site/"
    "?source=outreach#why-teams-buy"
)
PILOT_PRICE_TEXT = "$299"
DATE_PLACEHOLDER = "YYYY-MM-DD"
OUTCOME_PLACEHOLDER = "OUTCOME"
REVIEW_OUTPUT_PLACEHOLDER = "PRIVATE-REVIEW-PATH"
PUBLIC_PILOT_INTAKE_URL = (
    "https://github.com/becastil/Chats-empty-repo/issues/new"
    "?template=founding-team-pilot.yml"
    "&discovery_source=Direct+outreach"
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
        utc_ledger = Path(tmp) / "UTC default ledger.csv"
        _write_ledger(
            utc_ledger,
            _row(
                contacted_on="",
                status="drafted",
                next_action_on="",
                approved_on="",
            ),
        )
        utc_before = datetime.now(timezone.utc).date().isoformat()
        local_dates: set[str] = set()
        utc_reports: list[dict[str, Any]] = []
        for local_timezone in ("Etc/GMT+12", "Etc/GMT-14"):
            non_utc_environment = (
                dict(environment)
                if environment is not None
                else os.environ.copy()
            )
            non_utc_environment["TZ"] = local_timezone
            local_probe = subprocess.run(
                [
                    python_command,
                    "-c",
                    "from datetime import date; print(date.today().isoformat())",
                ],
                capture_output=True,
                text=True,
                env=non_utc_environment,
            )
            _require(
                local_probe.returncode == 0,
                "could not establish a release-smoke timezone",
            )
            local_dates.add(local_probe.stdout.strip())
            utc_default = _run_arguments(
                outreach_command,
                (str(utc_ledger), "--format", "json"),
                environment=non_utc_environment,
            )
            try:
                utc_report = json.loads(utc_default.stdout)
            except json.JSONDecodeError as exc:
                raise SmokeTestError(
                    "UTC-default outreach audit did not emit valid JSON"
                ) from exc
            _require(
                isinstance(utc_report, dict),
                "UTC-default outreach audit emitted a non-object report",
            )
            utc_reports.append(utc_report)

        utc_after = datetime.now(timezone.utc).date().isoformat()
        _require(
            len(local_dates) == 2,
            "release-smoke timezones did not produce different calendar dates",
        )
        _require(
            all(
                report.get("as_of") in {utc_before, utc_after}
                for report in utc_reports
            ),
            "outreach audit did not default to the current UTC calendar date",
        )
        checked.append("utc-date-default")

        handoff_ledger = Path(tmp) / "handoff ledger.csv"
        handoff_draft = _row(
            contacted_on="",
            status="drafted",
            next_action_on="",
            approved_on="",
        )
        _write_ledger(handoff_ledger, handoff_draft)
        handoff_ledger.chmod(0o640)
        handoff_bytes = handoff_ledger.read_bytes()
        permissive_handoff = _run(
            outreach_command,
            handoff_ledger,
            as_of="2026-07-01",
            arguments=("--review-next",),
            environment=environment,
            expected_exit_code=2,
        )
        _require(
            "chmod 600" in permissive_handoff.stderr,
            "permissive private ledger did not produce its controlled error",
        )
        _require(
            handoff_ledger.read_bytes() == handoff_bytes,
            "permission rejection modified the private ledger",
        )
        checked.append("permissive-ledger-rejected")
        handoff_ledger.chmod(0o600)

        private_review = Path(tmp) / "private review.md"
        written_review = _run_arguments(
            outreach_command,
            (
                "--as-of",
                "2026-07-01",
                "--review-next",
                "--write-review",
                str(private_review),
                "--",
                str(handoff_ledger),
            ),
            environment=environment,
        )
        _require(
            written_review.stdout
            == "Private review written with owner-only permissions.\n",
            "private review write disclosed alias-bearing output",
        )
        _require(
            "prospect-001" in private_review.read_text(encoding="utf-8"),
            "private review write omitted the selected alias",
        )
        if os.name == "posix":
            _require(
                private_review.stat().st_mode & 0o777 == 0o600,
                "private review write did not use owner-only permissions",
            )
        checked.append("private-review-written")

        handoff_review = _run_arguments(
            outreach_command,
            (
                "--as-of",
                "2026-07-01",
                "--review-next",
                "--",
                str(handoff_ledger),
            ),
            environment=environment,
        )
        approval_arguments = _handoff_arguments(
            handoff_review.stdout,
            action="--approve-next",
            ledger=handoff_ledger,
        )
        approval_arguments = _replace_event_date(
            approval_arguments,
            event_date="2026-07-02",
            action="approval",
        )
        handoff_approval = _run_arguments(
            outreach_command,
            approval_arguments,
            environment=environment,
        )
        contact_arguments = _handoff_arguments(
            handoff_approval.stdout,
            action="--record-contact",
            ledger=handoff_ledger,
        )
        contact_arguments = _replace_event_date(
            contact_arguments,
            event_date="2026-07-03",
            action="contact",
        )
        handoff_contact = _run_arguments(
            outreach_command,
            contact_arguments,
            environment=environment,
        )
        follow_up_arguments = _handoff_arguments(
            handoff_contact.stdout,
            action="--record-follow-up",
            ledger=handoff_ledger,
        )
        _require(
            "Manual follow-up due: 2026-07-10" in handoff_contact.stdout,
            "contact handoff did not display the exact follow-up due date",
        )
        follow_up_arguments = _replace_event_date(
            follow_up_arguments,
            event_date="2026-07-10",
            action="follow-up",
        )
        handoff_follow_up = _run_arguments(
            outreach_command,
            follow_up_arguments,
            environment=environment,
        )
        outcome_arguments = _handoff_arguments(
            handoff_follow_up.stdout,
            action="--record-outcome",
            ledger=handoff_ledger,
        )
        outcome_arguments = _replace_outcome(
            outcome_arguments,
            as_of="2026-07-13",
            observed_on="2026-07-11",
            outcome="replied",
        )
        handoff_outcome = _run_arguments(
            outreach_command,
            outcome_arguments,
            environment=environment,
        )
        refinement_arguments = _handoff_arguments(
            handoff_outcome.stdout,
            action="--record-outcome",
            ledger=handoff_ledger,
        )
        refinement_arguments = _replace_outcome(
            refinement_arguments,
            as_of="2026-07-13",
            observed_on="2026-07-12",
            outcome="pilot-requested",
        )
        handoff_refinement = _run_arguments(
            outreach_command,
            refinement_arguments,
            environment=environment,
        )
        _require(
            "repo-scout-outreach " not in handoff_refinement.stdout,
            "terminal outcome emitted another action command",
        )
        _require(
            PUBLIC_PILOT_INTAKE_URL in handoff_refinement.stdout,
            "private pilot request omitted its source-prefilled public intake",
        )
        handoff_row = _read_row(handoff_ledger)
        _require(
            handoff_row["status"] == "pilot-requested"
            and handoff_row["contacted_on"] == "2026-07-03"
            and handoff_row["followed_up_on"] == "2026-07-10"
            and handoff_row["outcome_on"] == "2026-07-11",
            "copy-ready handoffs did not complete the synthetic lifecycle",
        )
        checked.append("copy-ready-handoffs")

        decline_ledger = Path(tmp) / "decline ledger.csv"
        decline_draft = _row(
            contacted_on="",
            status="drafted",
            next_action_on="",
            approved_on="",
        )
        _write_ledger(decline_ledger, decline_draft)
        decline_ledger.chmod(0o600)
        decline_review = _run_arguments(
            outreach_command,
            (
                "--as-of",
                "2026-07-01",
                "--review-next",
                "--",
                str(decline_ledger),
            ),
            environment=environment,
        )
        decline_arguments = _handoff_arguments(
            decline_review.stdout,
            action="--decline-next",
            ledger=decline_ledger,
        )
        _require(
            "--confirm-not-send" in decline_arguments,
            "decline handoff omitted human no-send confirmation",
        )
        decline_arguments = _replace_event_date(
            decline_arguments,
            event_date="2026-07-02",
            action="decline",
            placeholder_count=1,
        )
        decline_receipt = _run_arguments(
            outreach_command,
            decline_arguments,
            environment=environment,
        )
        _require(
            "Drafts remaining: 0" in decline_receipt.stdout
            and "Review queue complete" in decline_receipt.stdout
            and "--review-next" not in decline_receipt.stdout,
            "final decline emitted a nonexistent next-review handoff",
        )
        declined_row = _read_row(decline_ledger)
        _require(
            declined_row["status"] == "review-declined",
            "human no-send decision was not saved",
        )
        _require(
            not declined_row["approved_on"]
            and not declined_row["contacted_on"]
            and not declined_row["followed_up_on"]
            and not declined_row["next_action_on"],
            "human no-send decision created outreach activity",
        )
        declined_report = _report(
            outreach_command,
            decline_ledger,
            as_of="2026-07-01",
            environment=environment,
        )
        declined_summary = declined_report.get("summary", {})
        _require(
            declined_report.get("schema_version") == 11,
            "outreach schema changed",
        )
        _require(
            declined_report.get("private_output") is False,
            "counts-only decline report was marked private",
        )
        counts_only_report = _run(
            outreach_command,
            decline_ledger,
            as_of="2026-07-01",
            arguments=("--require-counts-only",),
            environment=environment,
            expected_exit_code=0,
        )
        _require(
            json.loads(counts_only_report.stdout).get("private_output") is False,
            "counts-only guard did not emit the public-safe report",
        )
        _require(
            declined_summary.get("review_declined") == 1
            and declined_summary.get("closed") == 1
            and declined_summary.get("attempted_prospects") == 0,
            "human no-send decision inflated outreach activity",
        )
        checked.append("draft-declined-without-contact")

        continuation_ledger = Path(tmp) / "continuation ledger.csv"
        with continuation_ledger.open(
            "w", newline="", encoding="utf-8"
        ) as ledger_file:
            writer = csv.DictWriter(
                ledger_file,
                fieldnames=LEDGER_FIELDS,
                lineterminator="\n",
            )
            writer.writeheader()
            writer.writerows(
                (
                    _row(
                        prospect_id="prospect-001",
                        contacted_on="",
                        status="drafted",
                        next_action_on="",
                        approved_on="",
                    ),
                    _row(
                        prospect_id="prospect-002",
                        contacted_on="",
                        status="drafted",
                        next_action_on="",
                        approved_on="",
                    ),
                )
            )
        continuation_ledger.chmod(0o600)
        continuation_drafts = Path(tmp) / "continuation drafts.md"
        continuation_drafts.write_text(
            "# Private drafts\n\n"
            "## prospect-001\n\n"
            f"First private message for {PILOT_PRICE_TEXT}\n\n"
            f"{DIRECT_OUTREACH_ROUTE}\n\n"
            "## prospect-002\n\n"
            f"Second private message for {PILOT_PRICE_TEXT}\n\n"
            f"{DIRECT_OUTREACH_ROUTE}\n",
            encoding="utf-8",
        )
        continuation_drafts.chmod(0o600)
        continuation_review = _json_command(
            outreach_command,
            continuation_ledger,
            as_of="2026-07-02",
            arguments=(
                "--review-next",
                "--include-private-evidence",
                "--include-private-draft",
                str(continuation_drafts),
            ),
            environment=environment,
        )
        continuation_digest = continuation_review.get("review_digest")
        _require(
            isinstance(continuation_digest, str),
            "content-bound continuation review omitted its digest",
        )
        continuation_decline = _run_arguments(
            outreach_command,
            (
                "--as-of",
                "2026-07-03",
                "--decline-next",
                "prospect-001",
                "--confirm-not-send",
                "--review-digest",
                continuation_digest,
                "--reviewed-private-draft",
                str(continuation_drafts),
                "--",
                str(continuation_ledger),
            ),
            environment=environment,
        )
        continuation_arguments = _handoff_arguments(
            continuation_decline.stdout,
            action="--review-next",
            ledger=continuation_ledger,
        )
        _require(
            "--write-review" in continuation_arguments
            and continuation_arguments[
                continuation_arguments.index("--write-review") + 1
            ]
            == REVIEW_OUTPUT_PLACEHOLDER,
            "content-bound decline did not require an owner-only review output",
        )
        continuation_lines = [
            line
            for line in continuation_decline.stdout.splitlines()
            if line.startswith("repo-scout-outreach ")
            and " --review-next " in line
        ]
        _require(
            len(continuation_lines) == 1,
            "content-bound decline did not emit one copy-ready continuation",
        )
        continuation_line = continuation_lines[0]
        _require(
            f"'{REVIEW_OUTPUT_PLACEHOLDER}'" in continuation_line,
            "continued review output placeholder was not shell-quoted",
        )
        date_only_arguments = _replace_event_date(
            continuation_arguments,
            event_date="2026-07-04",
            action="continued review",
            placeholder_count=1,
        )
        unchanged_ledger = continuation_ledger.read_bytes()
        placeholder_rejection = _run_arguments(
            outreach_command,
            date_only_arguments,
            environment=environment,
            expected_exit_code=2,
        )
        _require(
            f"replace {REVIEW_OUTPUT_PLACEHOLDER}"
            in placeholder_rejection.stderr,
            "unchanged review output placeholder did not fail closed",
        )
        next_review_path = Path(tmp) / "next complete review.md"
        replaced_continuation = continuation_line.replace(
            DATE_PLACEHOLDER,
            "2026-07-04",
        ).replace(
            REVIEW_OUTPUT_PLACEHOLDER,
            str(next_review_path),
        )
        next_review_command = shlex.split(replaced_continuation)
        _require(
            next_review_command[
                next_review_command.index("--write-review") + 1
            ]
            == str(next_review_path),
            "literal review path replacement did not preserve one argument",
        )
        next_review_result = _run_arguments(
            outreach_command,
            tuple(next_review_command[1:]),
            environment=environment,
        )
        _require(
            next_review_result.stdout
            == "Private review written with owner-only permissions.\n",
            "continued review disclosed alias-bearing terminal output",
        )
        next_review_text = next_review_path.read_text(encoding="utf-8")
        _require(
            "Prospect alias: prospect-002" in next_review_text
            and "Second private message" in next_review_text
            and "https://evidence.example" in next_review_text
            and "prospect-002" not in next_review_result.stdout,
            "continued review did not confine the next private bundle",
        )
        if os.name == "posix":
            _require(
                next_review_path.stat().st_mode & 0o777 == 0o600,
                "continued review did not use owner-only permissions",
            )
        _require(
            continuation_ledger.read_bytes() == unchanged_ledger,
            "continued review generation modified the declined ledger",
        )
        checked.append("owner-only-decline-continuation")

        with continuation_ledger.open(
            "w", newline="", encoding="utf-8"
        ) as ledger_file:
            writer = csv.DictWriter(
                ledger_file,
                fieldnames=LEDGER_FIELDS,
                lineterminator="\n",
            )
            writer.writeheader()
            writer.writerows(
                (
                    _row(
                        prospect_id="prospect-001",
                        contacted_on="",
                        status="drafted",
                        next_action_on="",
                        approved_on="",
                    ),
                    _row(
                        prospect_id="prospect-002",
                        contacted_on="",
                        status="drafted",
                        next_action_on="",
                        approved_on="",
                    ),
                )
            )
        continuation_ledger.chmod(0o600)
        approval_review = _json_command(
            outreach_command,
            continuation_ledger,
            as_of="2026-07-05",
            arguments=(
                "--review-next",
                "--include-private-evidence",
                "--include-private-draft",
                str(continuation_drafts),
            ),
            environment=environment,
        )
        approval_digest = approval_review.get("review_digest")
        _require(
            isinstance(approval_digest, str),
            "content-bound approval review omitted its digest",
        )
        approval_continuation = _run_arguments(
            outreach_command,
            (
                "--as-of",
                "2026-07-06",
                "--approve-next",
                "prospect-001",
                "--approved-on",
                "2026-07-06",
                "--confirm-reviewed",
                "--review-digest",
                approval_digest,
                "--reviewed-private-draft",
                str(continuation_drafts),
                "--",
                str(continuation_ledger),
            ),
            environment=environment,
        )
        _require(
            "Drafts remaining: 1" in approval_continuation.stdout
            and "After that send is recorded" in approval_continuation.stdout,
            "approval did not preserve the post-contact review handoff",
        )
        approval_review_arguments = _handoff_arguments(
            approval_continuation.stdout,
            action="--review-next",
            ledger=continuation_ledger,
        )
        _require(
            "--include-private-evidence" in approval_review_arguments
            and approval_review_arguments[
                approval_review_arguments.index("--include-private-draft") + 1
            ]
            == str(continuation_drafts)
            and approval_review_arguments[
                approval_review_arguments.index("--write-review") + 1
            ]
            == REVIEW_OUTPUT_PLACEHOLDER,
            "approval did not preserve the complete private review options",
        )
        approval_review_lines = [
            line
            for line in approval_continuation.stdout.splitlines()
            if line.startswith("repo-scout-outreach ")
            and " --review-next " in line
        ]
        _require(
            len(approval_review_lines) == 1
            and f"'{REVIEW_OUTPUT_PLACEHOLDER}'" in approval_review_lines[0],
            "approval did not emit one shell-safe next-review handoff",
        )
        blocked_review_path = Path(tmp) / "blocked approval review.md"
        blocked_approval_review = approval_review_lines[0].replace(
            DATE_PLACEHOLDER,
            "2026-07-07",
        ).replace(
            REVIEW_OUTPUT_PLACEHOLDER,
            str(blocked_review_path),
        )
        before_blocked_review = continuation_ledger.read_bytes()
        blocked_review = _run_arguments(
            outreach_command,
            tuple(shlex.split(blocked_approval_review)[1:]),
            environment=environment,
            expected_exit_code=2,
        )
        _require(
            "send the pending approved message manually" in blocked_review.stderr
            and not blocked_review.stdout
            and not blocked_review_path.exists()
            and continuation_ledger.read_bytes() == before_blocked_review,
            "approval review handoff advanced before contact was recorded",
        )
        approval_contact_arguments = _handoff_arguments(
            approval_continuation.stdout,
            action="--record-contact",
            ledger=continuation_ledger,
        )
        approval_contact_arguments = _replace_event_date(
            approval_contact_arguments,
            event_date="2026-07-07",
            action="approval continuation contact",
        )
        _run_arguments(
            outreach_command,
            approval_contact_arguments,
            environment=environment,
        )
        approval_next_review_path = Path(tmp) / "approval next review.md"
        replaced_approval_review = approval_review_lines[0].replace(
            DATE_PLACEHOLDER,
            "2026-07-08",
        ).replace(
            REVIEW_OUTPUT_PLACEHOLDER,
            str(approval_next_review_path),
        )
        approval_next_review = _run_arguments(
            outreach_command,
            tuple(shlex.split(replaced_approval_review)[1:]),
            environment=environment,
        )
        _require(
            approval_next_review.stdout
            == "Private review written with owner-only permissions.\n",
            "post-contact review disclosed alias-bearing terminal output",
        )
        approval_next_review_text = approval_next_review_path.read_text(
            encoding="utf-8"
        )
        _require(
            "Prospect alias: prospect-002" in approval_next_review_text
            and "Second private message" in approval_next_review_text
            and "First private message" not in approval_next_review_text,
            "post-contact handoff did not write the next private review",
        )
        if os.name == "posix":
            _require(
                approval_next_review_path.stat().st_mode & 0o777 == 0o600,
                "post-contact review did not use owner-only permissions",
            )
        checked.append("owner-only-approval-continuation")

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
        private_drafts.chmod(0o600)

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
            len(review.get("review", {}).get("checks", ())) == 6,
            "review checklist changed",
        )
        _require(
            review.get("review", {}).get("campaign_route")
            == DIRECT_OUTREACH_ROUTE,
            "review omitted the source-preserving outreach route",
        )
        _require(
            SOURCE_ROUTE_REVIEW_CHECK
            in review.get("review", {}).get("checks", ()),
            "review checklist lost the outreach attribution check",
        )
        _require(
            OPT_OUT_REVIEW_CHECK in review.get("review", {}).get("checks", ()),
            "review checklist lost the explicit opt-out promise",
        )
        _require_private_values_absent(
            review,
            ("https://evidence.example",),
            context="review",
        )
        checked.append("draft-reviewed")

        drifted_review = _run(
            outreach_command,
            ledger,
            as_of="2026-07-02",
            arguments=(
                "--review-next",
                "--include-private-draft",
                str(private_drafts),
            ),
            environment=environment,
            expected_exit_code=2,
        )
        _require(
            "section absent from the ledger: prospect-002" in drifted_review.stderr,
            "draft identity drift did not produce its controlled error",
        )
        _require(
            "Other private message" not in drifted_review.stderr,
            "draft identity drift exposed private message text",
        )
        _require(
            ledger.read_bytes() == draft_bytes,
            "draft identity drift modified the ledger",
        )
        checked.append("draft-ledger-drift-rejected")

        private_drafts.write_text(
            "# Private drafts\n\n"
            f"## {draft['prospect_id']}\n\nSelected private message\n",
            encoding="utf-8",
        )
        missing_route_review = _run(
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
            expected_exit_code=2,
        )
        _require(
            missing_route_review.stdout == "",
            "missing-route review emitted a private bundle",
        )
        _require(
            "private draft must contain the canonical direct-outreach route "
            "exactly once"
            in missing_route_review.stderr,
            "missing-route review did not produce its controlled error",
        )
        _require(
            "Selected private message" not in missing_route_review.stderr,
            "missing-route review exposed private message text",
        )
        _require(
            ledger.read_bytes() == draft_bytes,
            "missing-route review modified the ledger",
        )
        checked.append("draft-route-rejected")

        private_drafts.write_text(
            "# Private drafts\n\n"
            f"## {draft['prospect_id']}\n\n"
            f"Selected private message\n\n{DIRECT_OUTREACH_ROUTE}\n",
            encoding="utf-8",
        )
        missing_price_review = _run(
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
            expected_exit_code=2,
        )
        _require(
            missing_price_review.stdout == "",
            "missing-price review emitted a private bundle",
        )
        _require(
            f"private draft must disclose the {PILOT_PRICE_TEXT} pilot price "
            "exactly once"
            in missing_price_review.stderr,
            "missing-price review did not produce its controlled error",
        )
        _require(
            "Selected private message" not in missing_price_review.stderr,
            "missing-price review exposed private message text",
        )
        _require(
            ledger.read_bytes() == draft_bytes,
            "missing-price review modified the ledger",
        )
        checked.append("draft-price-rejected")

        private_drafts.write_text(
            "# Private drafts\n\n"
            f"## {draft['prospect_id']}\n\n"
            f"Selected private message\n\n"
            f"Pilot price: {PILOT_PRICE_TEXT}\n\n"
            f"{DIRECT_OUTREACH_ROUTE}\n",
            encoding="utf-8",
        )

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
            private_draft
            == (
                f"Selected private message\n\n"
                f"Pilot price: {PILOT_PRICE_TEXT}\n\n"
                f"{DIRECT_OUTREACH_ROUTE}"
            ),
            "private review did not select the synthetic draft notes",
        )
        review_digest = evidence_review.get("review_digest")
        _require(
            isinstance(review_digest, str)
            and review_digest.startswith("sha256:")
            and len(review_digest) == 71
            and all(character in "0123456789abcdef" for character in review_digest[7:]),
            "private review did not emit a SHA-256 content receipt",
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
                "--review-digest",
                review_digest,
                "--reviewed-private-draft",
                str(private_drafts),
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
            approval.get("schema_version") == 2
            and approval.get("queue") == {"drafts_remaining": 0},
            "approval receipt did not report the remaining review queue",
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
        _require(approved_report.get("schema_version") == 11, "schema changed")
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
        _require(
            approved_report.get("next_approved")
            == {"prospect_id": draft["prospect_id"]},
            "approved report did not recover the next alias",
        )
        _require(
            approved_report.get("private_output") is True,
            "approved alias report was not marked private",
        )
        private_report = _run(
            outreach_command,
            ledger,
            as_of="2026-07-02",
            arguments=("--require-counts-only",),
            environment=environment,
            expected_exit_code=7,
        )
        _require(
            not private_report.stdout,
            "counts-only guard emitted private report output",
        )
        _require(
            "refused output" in private_report.stderr
            and draft["prospect_id"] not in private_report.stderr,
            "counts-only guard did not fail privately",
        )
        for private_value in ("2026-07-01", "https://evidence.example"):
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
        checked.append("counts-only-publication-guard")

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

        unconfirmed_outcome = _run(
            outreach_command,
            ledger,
            as_of="2026-07-11",
            arguments=(
                "--record-outcome",
                draft["prospect_id"],
                "--outcome",
                "pilot-requested",
                "--outcome-on",
                "2026-07-11",
            ),
            environment=environment,
            expected_exit_code=2,
        )
        _require(
            "requires --confirm-outcome-observed" in unconfirmed_outcome.stderr,
            "unconfirmed outcome did not produce its controlled error",
        )
        _require(
            ledger.read_bytes() == followed_bytes,
            "unconfirmed outcome modified the ledger",
        )
        checked.append("unconfirmed-outcome-rejected")

        outcome = _json_command(
            outreach_command,
            ledger,
            as_of="2026-07-11",
            arguments=(
                "--record-outcome",
                draft["prospect_id"],
                "--outcome",
                "pilot-requested",
                "--outcome-on",
                "2026-07-11",
                "--confirm-outcome-observed",
            ),
            environment=environment,
        )
        _require(
            outcome.get("human_outcome_confirmed") is True,
            "outcome confirmation is missing",
        )
        _require(
            outcome.get("outcome", {}).get("status") == "pilot-requested",
            "pilot-requested outcome was not recorded",
        )
        _require(
            outcome.get("public_pilot_intake_url")
            == PUBLIC_PILOT_INTAKE_URL,
            "pilot-requested JSON omitted its source-prefilled public intake",
        )
        _require_private_values_absent(
            outcome,
            (
                "2026-07-01",
                "2026-07-03",
                "2026-07-10",
                "https://evidence.example",
            ),
            context="outcome receipt",
        )
        outcome_row = _read_row(ledger)
        _require(
            outcome_row["status"] == "pilot-requested"
            and not outcome_row["next_action_on"]
            and outcome_row["outcome_on"] == "2026-07-11",
            "outcome did not stop the follow-up cadence",
        )
        _require(
            outcome_row["approved_on"] == "2026-07-01"
            and outcome_row["contacted_on"] == "2026-07-03"
            and outcome_row["followed_up_on"] == "2026-07-10",
            "outcome discarded approval or contact history",
        )
        outcome_report = _report(
            outreach_command,
            ledger,
            as_of="2026-07-11",
            environment=environment,
        )
        _require(
            outcome_report.get("summary", {}).get("pilot_requested") == 1,
            "pilot-requested outcome was not counted",
        )
        _require(
            outcome_report.get("summary", {}).get("attempted_prospects") == 1,
            "outcome inflated the attempted-prospect count",
        )
        _require(
            outcome_report.get("summary", {}).get("dated_outcomes") == 1,
            "outcome observation date was not retained",
        )
        checked.append("pilot-outcome-recorded")

        price_objection_ledger = Path(tmp) / "price objection ledger.csv"
        _write_ledger(
            price_objection_ledger,
            _row(
                status="replied",
                next_action_on="",
                outcome_on="2026-07-11",
            ),
        )
        price_objection_ledger.chmod(0o600)
        price_objection = _json_command(
            outreach_command,
            price_objection_ledger,
            as_of="2026-07-12",
            arguments=(
                "--record-outcome",
                "prospect-001",
                "--outcome",
                "price-objection",
                "--outcome-on",
                "2026-07-12",
                "--confirm-outcome-observed",
            ),
            environment=environment,
        )
        _require(
            price_objection.get("schema_version") == 4,
            "price-objection receipt schema changed",
        )
        _require(
            price_objection.get("outcome", {}).get("status")
            == "price-objection",
            "human-observed price objection was not recorded",
        )
        _require(
            price_objection.get("public_pilot_intake_url") is None,
            "price objection exposed a pilot conversion URL",
        )
        price_objection_row = _read_row(price_objection_ledger)
        _require(
            price_objection_row["status"] == "price-objection"
            and not price_objection_row["next_action_on"]
            and price_objection_row["outcome_on"] == "2026-07-11",
            "price objection did not preserve the first reply observation",
        )
        price_objection_report = _report(
            outreach_command,
            price_objection_ledger,
            as_of="2026-07-12",
            environment=environment,
        )
        _require(
            price_objection_report.get("summary", {}).get("price_objections")
            == 1,
            "price objection was not counted separately",
        )
        _require(
            price_objection_report.get("summary", {}).get("closed") == 1,
            "price objection did not close the outreach cadence",
        )
        checked.append("price-objection-recorded")

        existing_solution_ledger = Path(tmp) / "existing solution ledger.csv"
        _write_ledger(
            existing_solution_ledger,
            _row(
                status="replied",
                next_action_on="",
                outcome_on="2026-07-11",
            ),
        )
        existing_solution_ledger.chmod(0o600)
        existing_solution = _json_command(
            outreach_command,
            existing_solution_ledger,
            as_of="2026-07-12",
            arguments=(
                "--record-outcome",
                "prospect-001",
                "--outcome",
                "existing-solution",
                "--outcome-on",
                "2026-07-12",
                "--confirm-outcome-observed",
            ),
            environment=environment,
        )
        _require(
            existing_solution.get("schema_version") == 4,
            "existing-solution receipt schema changed",
        )
        _require(
            existing_solution.get("outcome", {}).get("status")
            == "existing-solution",
            "human-observed existing-solution objection was not recorded",
        )
        _require(
            existing_solution.get("public_pilot_intake_url") is None,
            "existing-solution objection exposed a pilot conversion URL",
        )
        existing_solution_row = _read_row(existing_solution_ledger)
        _require(
            existing_solution_row["status"] == "existing-solution"
            and not existing_solution_row["next_action_on"]
            and existing_solution_row["outcome_on"] == "2026-07-11",
            "existing-solution objection did not preserve the first reply observation",
        )
        existing_solution_report = _report(
            outreach_command,
            existing_solution_ledger,
            as_of="2026-07-12",
            environment=environment,
        )
        _require(
            existing_solution_report.get("summary", {}).get(
                "existing_solution_objections"
            )
            == 1,
            "existing-solution objection was not counted separately",
        )
        _require(
            existing_solution_report.get("summary", {}).get("closed") == 1,
            "existing-solution objection did not close the outreach cadence",
        )
        checked.append("existing-solution-recorded")

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
            "ledger row must have exactly 10 columns; found 11"
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
        "outcome_on": "",
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


def _run_arguments(
    command: Sequence[str],
    arguments: Sequence[str],
    *,
    environment: Mapping[str, str] | None,
    expected_exit_code: int = 0,
) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(
        [*command, *arguments],
        capture_output=True,
        text=True,
        env=dict(environment) if environment is not None else None,
    )
    if completed.returncode != expected_exit_code:
        detail = completed.stderr.strip() or completed.stdout.strip() or "no output"
        raise SmokeTestError(
            f"outreach handoff exited {completed.returncode}; expected "
            f"{expected_exit_code}: {detail}"
        )
    return completed


def _handoff_arguments(
    output: str,
    *,
    action: str,
    ledger: Path,
) -> tuple[str, ...]:
    parsed_commands: list[list[str]] = []
    for line in output.splitlines():
        if not line.startswith("repo-scout-outreach "):
            continue
        try:
            parsed = shlex.split(line)
        except ValueError as exc:
            raise SmokeTestError(f"{action} handoff is not valid shell syntax") from exc
        if action in parsed:
            parsed_commands.append(parsed)
    _require(
        len(parsed_commands) == 1,
        f"{action} handoff command was not emitted once",
    )
    parsed = parsed_commands[0]
    _require(parsed[0] == "repo-scout-outreach", "handoff command name changed")
    _require(action in parsed, f"handoff command omitted {action}")
    _require(
        parsed[-2:] == ["--", str(ledger)],
        "handoff command did not preserve the private ledger path",
    )
    return tuple(parsed[1:])


def _replace_event_date(
    arguments: Sequence[str],
    *,
    event_date: str,
    action: str,
    placeholder_count: int = 2,
) -> tuple[str, ...]:
    placeholder_label = (
        "placeholder" if placeholder_count == 1 else "placeholders"
    )
    _require(
        arguments.count(DATE_PLACEHOLDER) == placeholder_count,
        f"{action} handoff must require {placeholder_count} "
        f"actual-date {placeholder_label}",
    )
    return tuple(
        event_date if value == DATE_PLACEHOLDER else value
        for value in arguments
    )


def _replace_outcome(
    arguments: Sequence[str],
    *,
    as_of: str,
    observed_on: str,
    outcome: str,
) -> tuple[str, ...]:
    _require(
        arguments.count(DATE_PLACEHOLDER) == 2,
        "outcome handoff must require recording and observation dates",
    )
    _require(
        arguments.count(OUTCOME_PLACEHOLDER) == 1,
        "outcome handoff must require one observed-outcome placeholder",
    )
    replacements = {
        "--as-of": as_of,
        "--outcome-on": observed_on,
    }
    replaced: list[str] = []
    for index, value in enumerate(arguments):
        if value == DATE_PLACEHOLDER:
            previous = arguments[index - 1] if index else ""
            _require(
                previous in replacements,
                "outcome handoff date placeholder has no known option",
            )
            replaced.append(replacements[previous])
        elif value == OUTCOME_PLACEHOLDER:
            replaced.append(outcome)
        else:
            replaced.append(value)
    return tuple(replaced)


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
