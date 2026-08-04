from __future__ import annotations

from contextlib import redirect_stderr, redirect_stdout
import csv
from datetime import date
import io
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
from tempfile import TemporaryDirectory
import time
import tomllib
import unittest
from unittest.mock import patch


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from repo_scout.outreach import (  # noqa: E402
    DATE_PLACEHOLDER,
    DIRECT_OUTREACH_ROUTE,
    LEGACY_LEDGER_FIELDS,
    LEGACY_UNBOUND_REVIEW,
    LEDGER_FIELDS,
    OUTCOME_LEDGER_FIELDS,
    OUTCOME_PLACEHOLDER,
    OutreachInputError,
    PRIVATE_OUTPUT_EXIT_CODE,
    PUBLIC_PILOT_INTAKE_URL,
    REVIEW_OUTPUT_PLACEHOLDER,
    build_parser,
    build_next_outreach_review,
    build_outreach_report,
    format_next_outreach_review,
    format_outreach_contact,
    format_outreach_decline,
    format_outreach_follow_up,
    format_outreach_outcome,
    format_outreach_report,
    load_outreach_report,
    main,
    _write_private_review,
)


ROOT = Path(__file__).resolve().parents[1]
SIGNALS = "team_5_50;multi_repo;agent_use"
EVIDENCE = (
    "team_5_50=https://evidence.example/team;"
    "multi_repo=https://evidence.example/repositories;"
    "agent_use=https://evidence.example/agents"
)


def _row(**overrides: str) -> dict[str, str]:
    status = overrides.get("status", "contacted")
    row = {
        "prospect_id": "prospect-001",
        "fit_signals": SIGNALS,
        "fit_evidence": EVIDENCE,
        "contacted_on": "2026-07-01",
        "channel": "published-business",
        "status": status,
        "followed_up_on": "",
        "next_action_on": "2026-07-08",
        "approved_on": "2026-06-30",
        "outcome_on": "",
        "approved_review_digest": (
            ""
            if status in {"researched", "drafted", "review-declined"}
            else LEGACY_UNBOUND_REVIEW
        ),
    }
    row.update(overrides)
    return row


def _review_message(message: str) -> str:
    return f"{message}\n\nPilot price: $299\n\n{DIRECT_OUTREACH_ROUTE}"


def _write_ledger(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as ledger_file:
        writer = csv.DictWriter(
            ledger_file,
            fieldnames=LEDGER_FIELDS,
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)
    if os.name == "posix":
        path.chmod(0o600)


def _write_content_bound_review(
    path: Path,
    rows: list[dict[str, str]],
    *,
    as_of: date,
) -> str:
    private_drafts = {
        row["prospect_id"]: _review_message(
            f"Reviewed private message for {row['prospect_id']}"
        )
        for row in rows
        if row["status"] == "drafted"
    }
    path.write_text(
        "\n\n".join(
            f"## {prospect_id}\n\n{message}"
            for prospect_id, message in sorted(private_drafts.items())
        )
        + "\n",
        encoding="utf-8",
    )
    if os.name == "posix":
        path.chmod(0o600)
    report = build_next_outreach_review(
        rows,
        as_of=as_of,
        include_private_evidence=True,
        private_drafts=private_drafts,
    )
    review_digest = report["review_digest"]
    if not isinstance(review_digest, str):
        raise AssertionError("complete review did not produce a digest")
    return review_digest


class OutreachReportTests(unittest.TestCase):
    def test_installed_command_points_to_the_outreach_auditor(self) -> None:
        with (ROOT / "pyproject.toml").open("rb") as project_file:
            scripts = tomllib.load(project_file)["project"]["scripts"]

        self.assertEqual(
            scripts["repo-scout-outreach"],
            "repo_scout.outreach:main",
        )

    def test_reports_only_aliases_and_aggregate_activity(self) -> None:
        rows = [
            _row(),
            _row(
                prospect_id="prospect-002",
                status="followed-up",
                followed_up_on="2026-07-08",
                next_action_on="",
            ),
            _row(
                prospect_id="prospect-003",
                status="replied",
                next_action_on="",
            ),
            _row(
                prospect_id="prospect-004",
                status="pilot-requested",
                next_action_on="",
            ),
            _row(
                prospect_id="prospect-005",
                status="existing-solution",
                next_action_on="",
            ),
            _row(
                prospect_id="prospect-006",
                status="researched",
                contacted_on="",
                channel="",
                followed_up_on="",
                next_action_on="",
                approved_on="",
            ),
            _row(
                prospect_id="prospect-007",
                status="drafted",
                contacted_on="",
                followed_up_on="",
                next_action_on="",
                approved_on="",
            ),
            _row(
                prospect_id="prospect-008",
                status="approved",
                contacted_on="",
                followed_up_on="",
                next_action_on="",
                approved_on="2026-07-01",
            ),
            _row(
                prospect_id="prospect-009",
                status="review-declined",
                contacted_on="",
                followed_up_on="",
                next_action_on="",
                approved_on="",
            ),
            _row(
                prospect_id="prospect-010",
                status="price-objection",
                next_action_on="",
            ),
        ]

        report = build_outreach_report(rows, as_of=date(2026, 7, 10))

        self.assertEqual(report["schema_version"], 12)
        self.assertTrue(report["experiment"]["human_approval_required"])
        self.assertEqual(report["summary"]["prospects"], 10)
        self.assertEqual(report["summary"]["attempted_prospects"], 6)
        self.assertEqual(report["summary"]["drafted"], 1)
        self.assertEqual(report["summary"]["review_declined"], 1)
        self.assertEqual(report["summary"]["approved"], 1)
        self.assertEqual(report["summary"]["price_objections"], 1)
        self.assertEqual(report["summary"]["existing_solution_objections"], 1)
        self.assertEqual(report["summary"]["closed"], 3)
        self.assertEqual(report["summary"]["fit_evidence_links"], 30)
        self.assertEqual(report["summary"]["dated_outcomes"], 0)
        self.assertEqual(report["summary"]["undated_outcomes"], 4)
        text = format_outreach_report(report, ledger=Path("private ledger.csv"))
        self.assertIn("Drafts awaiting review: 1", text)
        self.assertIn("Approved to send: 1", text)
        self.assertIn("Declined before contact: 1", text)
        self.assertIn("Price objections: 1", text)
        self.assertIn("Existing-solution objections: 1", text)
        self.assertIn("Qualification links: 30", text)
        self.assertEqual(
            report["next_approved"],
            {"prospect_id": "prospect-008", "review_digest": None},
        )
        self.assertTrue(report["private_output"])
        self.assertEqual(
            report["privacy_note"],
            "This report contains private prospect aliases and must not be "
            "committed or shared.",
        )
        self.assertIn(
            "Privacy: This report contains private prospect aliases", text
        )
        self.assertIn(
            "Next approved message awaiting manual send: prospect-008", text
        )
        self.assertIn(
            "repo-scout-outreach --as-of YYYY-MM-DD "
            "--record-contact prospect-008 --contacted-on YYYY-MM-DD "
            "--confirm-sent -- 'private ledger.csv'",
            text,
        )
        self.assertIn(
            "repo-scout-outreach --as-of YYYY-MM-DD "
            "--decline-next prospect-008 --confirm-not-send "
            "--confirm-not-sent -- "
            "'private ledger.csv'",
            text,
        )
        self.assertEqual(report["summary"]["due_followups"], 1)
        self.assertEqual(report["summary"]["pilot_requested"], 1)
        self.assertEqual(
            report["due_followups"],
            [
                {
                    "prospect_id": "prospect-001",
                    "due_on": "2026-07-08",
                    "overdue_days": 2,
                }
            ],
        )
        self.assertIn(
            "not lead, demand, payment, or revenue",
            report["evidence_note"],
        )
        self.assertNotIn("channel", report["due_followups"][0])
        self.assertNotIn("evidence.example", json.dumps(report))
        self.assertNotIn("approved_on", json.dumps(report))
        self.assertNotIn("2026-06-30", json.dumps(report))

    def test_template_is_a_valid_empty_private_ledger(self) -> None:
        report = load_outreach_report(
            ROOT / "examples" / "outreach-ledger.csv",
            as_of=date(2026, 7, 11),
        )

        self.assertEqual(report["summary"]["prospects"], 0)
        self.assertIsNone(report["next_approved"])
        self.assertEqual(report["due_followups"], [])
        self.assertFalse(report["private_output"])
        self.assertEqual(
            report["privacy_note"],
            "This report is counts-only and contains no prospect aliases.",
        )
        self.assertIn(
            "Privacy: This report is counts-only and contains no prospect aliases.",
            format_outreach_report(report),
        )

    def test_marks_due_followup_aliases_private_without_an_approval(self) -> None:
        report = build_outreach_report(
            [_row()],
            as_of=date(2026, 7, 8),
        )

        self.assertIsNone(report["next_approved"])
        self.assertEqual(
            report["due_followups"][0]["prospect_id"], "prospect-001"
        )
        self.assertTrue(report["private_output"])
        self.assertIn("must not be committed or shared", report["privacy_note"])

    def test_recovers_only_the_lowest_approved_alias(self) -> None:
        rows = [
            _row(
                prospect_id="prospect-003",
                status="approved",
                contacted_on="",
                next_action_on="",
                approved_on="2026-07-11",
            ),
            _row(
                prospect_id="prospect-002",
                status="approved",
                contacted_on="",
                next_action_on="",
                approved_on="2026-07-12",
            ),
        ]

        report = build_outreach_report(rows, as_of=date(2026, 7, 13))
        text = format_outreach_report(report, ledger=Path("ledger.csv"))

        self.assertEqual(
            report["next_approved"],
            {"prospect_id": "prospect-002", "review_digest": None},
        )
        self.assertIn("--record-contact prospect-002", text)
        self.assertIn(
            "Legacy recovery boundary",
            text,
        )
        self.assertNotIn("prospect-003", json.dumps(report))
        self.assertNotIn("prospect-003", text)

    def test_surfaces_one_alias_only_human_review_at_a_time(self) -> None:
        rows = [
            _row(
                prospect_id="prospect-002",
                status="drafted",
                contacted_on="",
                next_action_on="",
                approved_on="",
            ),
            _row(
                prospect_id="prospect-001",
                status="drafted",
                contacted_on="",
                next_action_on="",
                approved_on="",
            ),
        ]

        report = build_next_outreach_review(rows, as_of=date(2026, 7, 13))

        self.assertEqual(report["schema_version"], 6)
        self.assertTrue(report["human_review_required"])
        self.assertTrue(report["private_output"])
        self.assertFalse(report["private_evidence_included"])
        self.assertFalse(report["private_draft_included"])
        self.assertEqual(report["review"]["prospect_id"], "prospect-001")
        self.assertEqual(report["review"]["channel"], "published-business")
        self.assertEqual(report["review"]["fit_signals"], 3)
        self.assertEqual(report["review"]["fit_evidence_links"], 3)
        self.assertEqual(len(report["review"]["checks"]), 6)
        self.assertEqual(
            report["review"]["campaign_route"],
            DIRECT_OUTREACH_ROUTE,
        )
        self.assertIn(
            "Confirm the message uses the source-preserving direct-outreach "
            "route shown above.",
            report["review"]["checks"],
        )
        self.assertIn(
            "Confirm the message gives a clear opt-out and promises no further contact.",
            report["review"]["checks"],
        )
        self.assertNotIn("private_evidence", report["review"])
        self.assertNotIn("private_draft", report["review"])
        serialized = json.dumps(report)
        self.assertNotIn("evidence.example", serialized)
        self.assertNotIn("approved_on", serialized)
        text = format_next_outreach_review(report, ledger=Path("ledger.csv"))
        self.assertEqual(text.count("- [ ]"), 6)
        self.assertIn(
            f"Source-preserving offer route: {DIRECT_OUTREACH_ROUTE}",
            text,
        )
        self.assertIn("Keep this alias-only checklist in the private workspace", text)
        self.assertIn("does not approve, modify, or send", text)
        self.assertIn(
            "Approval requires a complete evidence-and-draft review", text
        )
        self.assertNotIn("--approve-next", text)
        self.assertIn("--decline-next prospect-001 --confirm-not-send", text)

    def test_review_next_can_explicitly_include_private_evidence(self) -> None:
        rows = [
            _row(
                prospect_id="prospect-001",
                status="drafted",
                contacted_on="",
                next_action_on="",
                approved_on="",
            )
        ]

        report = build_next_outreach_review(
            rows,
            as_of=date(2026, 7, 13),
            include_private_evidence=True,
        )

        self.assertTrue(report["private_output"])
        self.assertTrue(report["private_evidence_included"])
        self.assertFalse(report["private_draft_included"])
        self.assertEqual(
            report["review"]["private_evidence"],
            [
                {
                    "signal": "agent_use",
                    "url": "https://evidence.example/agents",
                },
                {
                    "signal": "multi_repo",
                    "url": "https://evidence.example/repositories",
                },
                {
                    "signal": "team_5_50",
                    "url": "https://evidence.example/team",
                },
            ],
        )
        text = format_next_outreach_review(report, ledger=Path("ledger.csv"))
        self.assertIn("Private evidence (do not commit or share):", text)
        self.assertIn(
            "- agent_use: https://evidence.example/agents",
            text,
        )
        self.assertIn("evidence-bearing review", text)
        self.assertNotIn("--approve-next", text)
        self.assertIn("--decline-next prospect-001 --confirm-not-send", text)
        self.assertIn("does not approve, modify, or send", text)

    def test_review_next_can_include_only_the_selected_private_draft(self) -> None:
        rows = [
            _row(
                prospect_id="prospect-002",
                status="drafted",
                contacted_on="",
                next_action_on="",
                approved_on="",
            ),
            _row(
                prospect_id="prospect-001",
                status="drafted",
                contacted_on="",
                next_action_on="",
                approved_on="",
            ),
        ]

        report = build_next_outreach_review(
            rows,
            as_of=date(2026, 7, 13),
            private_drafts={
                "prospect-001": "Recipient: first@example.test\n\nSelected message",
                "prospect-002": "Recipient: second@example.test\n\nOther message",
            },
        )

        self.assertTrue(report["private_draft_included"])
        self.assertFalse(report["private_evidence_included"])
        self.assertEqual(
            report["review"]["private_draft"],
            "Recipient: first@example.test\n\nSelected message",
        )
        serialized = json.dumps(report)
        self.assertNotIn("second@example.test", serialized)
        text = format_next_outreach_review(report, ledger=Path("ledger.csv"))
        self.assertIn("Private draft notes (do not commit or share):", text)
        self.assertIn("Selected message", text)
        self.assertIn("draft-bearing review", text)
        self.assertNotIn("--approve-next", text)
        self.assertIn("--decline-next prospect-001 --confirm-not-send", text)

    def test_private_draft_notes_can_retain_progressed_ledger_sections(self) -> None:
        rows = [
            _row(
                prospect_id="prospect-001",
                status="drafted",
                contacted_on="",
                next_action_on="",
                approved_on="",
            ),
            _row(
                prospect_id="prospect-002",
                status="contacted",
            ),
        ]

        report = build_next_outreach_review(
            rows,
            as_of=date(2026, 7, 13),
            private_drafts={
                "prospect-001": "Selected message",
                "prospect-002": "Previously contacted message",
            },
        )

        self.assertEqual(report["review"]["prospect_id"], "prospect-001")
        self.assertEqual(report["review"]["private_draft"], "Selected message")
        self.assertNotIn("Previously contacted message", json.dumps(report))

    def test_review_next_cli_does_not_modify_the_private_ledger(self) -> None:
        with TemporaryDirectory() as tmp:
            ledger = Path(tmp) / "ledger.csv"
            row = _row(
                status="drafted",
                contacted_on="",
                next_action_on="",
                approved_on="",
            )
            ledger.write_text(
                ",".join(LEDGER_FIELDS)
                + "\n"
                + ",".join(row[field] for field in LEDGER_FIELDS)
                + "\n",
                encoding="utf-8",
            )
            if os.name == "posix":
                ledger.chmod(0o600)
            before = ledger.read_bytes()
            stdout = io.StringIO()

            with redirect_stdout(stdout):
                exit_code = main(
                    [
                        str(ledger),
                        "--as-of",
                        "2026-07-13",
                        "--review-next",
                        "--format",
                        "json",
                    ]
                )

            self.assertEqual(exit_code, 0)
            self.assertEqual(ledger.read_bytes(), before)
            report = json.loads(stdout.getvalue())
            self.assertEqual(report["review"]["prospect_id"], "prospect-001")
            self.assertIn("does not approve", report["action_note"])

    def test_review_next_writes_private_bundle_without_terminal_disclosure(self) -> None:
        with TemporaryDirectory() as tmp:
            private_directory = Path(tmp) / "private"
            private_directory.mkdir(mode=0o700)
            ledger = private_directory / "ledger.csv"
            notes = private_directory / "drafts.md"
            review = private_directory / "review.md"
            _write_ledger(
                ledger,
                [
                    _row(
                        status="drafted",
                        contacted_on="",
                        next_action_on="",
                        approved_on="",
                    )
                ],
            )
            notes.write_text(
                f"## prospect-001\n\n"
                f"{_review_message('Selected private message')}\n",
                encoding="utf-8",
            )
            if os.name == "posix":
                notes.chmod(0o600)
            ledger_before = ledger.read_bytes()
            stdout = io.StringIO()

            with redirect_stdout(stdout):
                exit_code = main(
                    [
                        str(ledger),
                        "--as-of",
                        "2026-07-13",
                        "--review-next",
                        "--include-private-evidence",
                        "--include-private-draft",
                        str(notes),
                        "--write-review",
                        str(review),
                    ]
                )

            self.assertEqual(exit_code, 0)
            self.assertEqual(ledger.read_bytes(), ledger_before)
            self.assertEqual(
                stdout.getvalue(),
                "Private review written with owner-only permissions.\n",
            )
            self.assertNotIn("prospect-001", stdout.getvalue())
            review_text = review.read_text(encoding="utf-8")
            self.assertIn("prospect-001", review_text)
            self.assertIn("Selected private message", review_text)
            self.assertIn("team_5_50: https://evidence.example/team", review_text)
            self.assertIn("--approve-next prospect-001", review_text)
            self.assertIn("--decline-next prospect-001", review_text)
            self.assertEqual(
                list(private_directory.glob(".repo-scout-review.*.tmp")),
                [],
            )
            if os.name == "posix":
                self.assertEqual(review.stat().st_mode & 0o777, 0o600)

    def test_write_review_rejects_invalid_commercial_markers_without_artifacts(
        self,
    ) -> None:
        with TemporaryDirectory() as tmp:
            private_directory = Path(tmp) / "private"
            private_directory.mkdir(mode=0o700)
            ledger = private_directory / "ledger.csv"
            notes = private_directory / "drafts.md"
            review = private_directory / "review.md"
            _write_ledger(
                ledger,
                [
                    _row(
                        status="drafted",
                        contacted_on="",
                        next_action_on="",
                        approved_on="",
                    )
                ],
            )
            ledger_before = ledger.read_bytes()
            cases = (
                (
                    "Private message without campaign route for $299",
                    "private draft must contain the canonical "
                    "direct-outreach route exactly once",
                ),
                (
                    "Private message with repeated campaign route for $299\n\n"
                    f"{DIRECT_OUTREACH_ROUTE}\n\n{DIRECT_OUTREACH_ROUTE}",
                    "private draft must contain the canonical "
                    "direct-outreach route exactly once",
                ),
                (
                    "Private message without price\n\n"
                    f"{DIRECT_OUTREACH_ROUTE}",
                    "private draft must disclose the $299 pilot price "
                    "exactly once without negation or another dollar price",
                ),
                (
                    "Private message with $299 repeated at $299\n\n"
                    f"{DIRECT_OUTREACH_ROUTE}",
                    "private draft must disclose the $299 pilot price "
                    "exactly once without negation or another dollar price",
                ),
                (
                    "This pilot is not $299.\n\n"
                    f"{DIRECT_OUTREACH_ROUTE}",
                    "private draft must disclose the $299 pilot price "
                    "exactly once without negation or another dollar price",
                ),
                (
                    "Pilot price: $299; alternate price: $199\n\n"
                    f"{DIRECT_OUTREACH_ROUTE}",
                    "private draft must disclose the $299 pilot price "
                    "exactly once without negation or another dollar price",
                ),
            )

            for private_draft, expected_error in cases:
                with self.subTest(
                    route_count=private_draft.count(DIRECT_OUTREACH_ROUTE),
                    price_count=private_draft.count("$299"),
                ):
                    notes.write_text(
                        f"## prospect-001\n\n{private_draft}\n",
                        encoding="utf-8",
                    )
                    if os.name == "posix":
                        notes.chmod(0o600)
                    stdout = io.StringIO()
                    stderr = io.StringIO()

                    with redirect_stdout(stdout), redirect_stderr(stderr):
                        exit_code = main(
                            [
                                str(ledger),
                                "--as-of",
                                "2026-07-13",
                                "--review-next",
                                "--include-private-evidence",
                                "--include-private-draft",
                                str(notes),
                                "--write-review",
                                str(review),
                            ]
                        )

                    self.assertEqual(exit_code, 2)
                    self.assertEqual(stdout.getvalue(), "")
                    self.assertIn(expected_error, stderr.getvalue())
                    self.assertNotIn("Private message", stderr.getvalue())
                    self.assertEqual(ledger.read_bytes(), ledger_before)
                    self.assertFalse(review.exists())
                    self.assertEqual(
                        list(
                            private_directory.glob(
                                ".repo-scout-review.*.tmp"
                            )
                        ),
                        [],
                    )

    def test_write_review_refuses_overwrite_without_leaving_staged_files(self) -> None:
        with TemporaryDirectory() as tmp:
            private_directory = Path(tmp) / "private"
            private_directory.mkdir(mode=0o700)
            ledger = private_directory / "ledger.csv"
            review = private_directory / "review.md"
            _write_ledger(
                ledger,
                [
                    _row(
                        status="drafted",
                        contacted_on="",
                        next_action_on="",
                        approved_on="",
                    )
                ],
            )
            review.write_text("existing private review\n", encoding="utf-8")
            if os.name == "posix":
                review.chmod(0o600)
            stderr = io.StringIO()

            with redirect_stderr(stderr):
                exit_code = main(
                    [
                        str(ledger),
                        "--as-of",
                        "2026-07-13",
                        "--review-next",
                        "--write-review",
                        str(review),
                    ]
                )

            self.assertEqual(exit_code, 2)
            self.assertEqual(
                review.read_text(encoding="utf-8"),
                "existing private review\n",
            )
            self.assertIn("refusing to overwrite", stderr.getvalue())
            self.assertEqual(
                list(private_directory.glob(".repo-scout-review.*.tmp")),
                [],
            )

    def test_write_review_rejects_unsafe_options_and_parent_permissions(self) -> None:
        with TemporaryDirectory() as tmp:
            private_directory = Path(tmp) / "private"
            private_directory.mkdir(mode=0o700)
            ledger = private_directory / "ledger.csv"
            review = private_directory / "review.md"
            qualified_placeholder = (
                private_directory / REVIEW_OUTPUT_PLACEHOLDER
            )
            _write_ledger(
                ledger,
                [
                    _row(
                        status="drafted",
                        contacted_on="",
                        next_action_on="",
                        approved_on="",
                    )
                ],
            )

            cases = (
                (["--write-review", str(review)], "requires --review-next"),
                (
                    [
                        "--review-next",
                        "--format",
                        "json",
                        "--write-review",
                        str(review),
                    ],
                    "requires --format text",
                ),
                (
                    [
                        "--review-next",
                        "--write-review",
                        REVIEW_OUTPUT_PLACEHOLDER,
                    ],
                    f"replace {REVIEW_OUTPUT_PLACEHOLDER}",
                ),
                (
                    [
                        "--review-next",
                        "--write-review",
                        str(qualified_placeholder),
                    ],
                    f"replace {REVIEW_OUTPUT_PLACEHOLDER}",
                ),
            )
            for arguments, expected in cases:
                with self.subTest(expected=expected):
                    before_ledger = ledger.read_bytes()
                    stdout = io.StringIO()
                    stderr = io.StringIO()
                    with redirect_stdout(stdout), redirect_stderr(stderr):
                        exit_code = main(
                            [str(ledger), "--as-of", "2026-07-13", *arguments]
                        )
                    self.assertEqual(exit_code, 2)
                    self.assertEqual(stdout.getvalue(), "")
                    self.assertIn(expected, stderr.getvalue())
                    self.assertFalse(review.exists())
                    self.assertFalse(qualified_placeholder.exists())
                    self.assertEqual(ledger.read_bytes(), before_ledger)
                    self.assertEqual(
                        list(
                            private_directory.glob(
                                ".repo-scout-review.*.tmp"
                            )
                        ),
                        [],
                    )

            with self.assertRaisesRegex(
                OutreachInputError,
                f"replace {REVIEW_OUTPUT_PLACEHOLDER}",
            ):
                _write_private_review(
                    private_directory
                    / "nested"
                    / ".."
                    / REVIEW_OUTPUT_PLACEHOLDER,
                    "private review",
                )
            self.assertFalse(qualified_placeholder.exists())
            self.assertEqual(
                list(private_directory.glob(".repo-scout-review.*.tmp")),
                [],
            )

            if os.name == "posix":
                private_directory.chmod(0o750)
                stderr = io.StringIO()
                with redirect_stderr(stderr):
                    exit_code = main(
                        [
                            str(ledger),
                            "--as-of",
                            "2026-07-13",
                            "--review-next",
                            "--write-review",
                            str(review),
                        ]
                    )
                self.assertEqual(exit_code, 2)
                self.assertIn("chmod 700", stderr.getvalue())
                self.assertFalse(review.exists())

    def test_write_review_removes_staging_file_after_publish_failure(self) -> None:
        with TemporaryDirectory() as tmp:
            private_directory = Path(tmp) / "private"
            private_directory.mkdir(mode=0o700)
            ledger = private_directory / "ledger.csv"
            review = private_directory / "review.md"
            _write_ledger(
                ledger,
                [
                    _row(
                        status="drafted",
                        contacted_on="",
                        next_action_on="",
                        approved_on="",
                    )
                ],
            )
            stderr = io.StringIO()

            with patch(
                "repo_scout.outreach.os.link",
                side_effect=OSError("injected publish failure"),
            ), redirect_stderr(stderr):
                exit_code = main(
                    [
                        str(ledger),
                        "--as-of",
                        "2026-07-13",
                        "--review-next",
                        "--write-review",
                        str(review),
                    ]
                )

            self.assertEqual(exit_code, 2)
            self.assertFalse(review.exists())
            self.assertIn("cannot publish", stderr.getvalue())
            self.assertEqual(
                list(private_directory.glob(".repo-scout-review.*.tmp")),
                [],
            )

    def test_write_review_reports_cleanup_failure_after_publication(self) -> None:
        with TemporaryDirectory() as tmp:
            private_directory = Path(tmp) / "private"
            private_directory.mkdir(mode=0o700)
            ledger = private_directory / "ledger.csv"
            review = private_directory / "prospect-001-review.md"
            _write_ledger(
                ledger,
                [
                    _row(
                        status="drafted",
                        contacted_on="",
                        next_action_on="",
                        approved_on="",
                    )
                ],
            )
            stdout = io.StringIO()
            stderr = io.StringIO()

            with patch.object(
                Path,
                "unlink",
                side_effect=OSError("injected cleanup failure"),
            ), redirect_stdout(stdout), redirect_stderr(stderr):
                exit_code = main(
                    [
                        str(ledger),
                        "--as-of",
                        "2026-07-13",
                        "--review-next",
                        "--write-review",
                        str(review),
                    ]
                )

            self.assertEqual(exit_code, 2)
            self.assertEqual(stdout.getvalue(), "")
            self.assertTrue(review.is_file())
            staged = list(private_directory.glob(".repo-scout-review.*.tmp"))
            self.assertEqual(len(staged), 1)
            self.assertIn("review output was written", stderr.getvalue())
            self.assertIn("temporary cleanup incomplete", stderr.getvalue())
            self.assertIn(staged[0].name, stderr.getvalue())
            self.assertIn("remove that staging file", stderr.getvalue())
            self.assertNotIn("prospect-001", stderr.getvalue())
            if os.name == "posix":
                self.assertEqual(review.stat().st_mode & 0o777, 0o600)
                self.assertEqual(staged[0].stat().st_mode & 0o777, 0o600)
            staged[0].unlink()

    def test_write_review_requires_ignored_untracked_git_destination(self) -> None:
        with TemporaryDirectory() as tmp:
            repository = Path(tmp)
            subprocess.run(
                ["git", "init", "--quiet", str(repository)],
                check=True,
            )
            private_directory = repository / "private"
            private_directory.mkdir(mode=0o700)
            (repository / ".gitignore").write_text(
                "/private/\n",
                encoding="utf-8",
            )
            ledger = private_directory / "ledger.csv"
            _write_ledger(
                ledger,
                [
                    _row(
                        status="drafted",
                        contacted_on="",
                        next_action_on="",
                        approved_on="",
                    )
                ],
            )
            unignored_review = repository / "review.md"
            stderr = io.StringIO()

            with redirect_stderr(stderr):
                exit_code = main(
                    [
                        str(ledger),
                        "--as-of",
                        "2026-07-13",
                        "--review-next",
                        "--write-review",
                        str(unignored_review),
                    ]
                )

            self.assertEqual(exit_code, 2)
            self.assertFalse(unignored_review.exists())
            self.assertIn("must be ignored and untracked", stderr.getvalue())

            ignored_review = private_directory / "review.md"
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                exit_code = main(
                    [
                        str(ledger),
                        "--as-of",
                        "2026-07-13",
                        "--review-next",
                        "--write-review",
                        str(ignored_review),
                    ]
                )

            self.assertEqual(exit_code, 0)
            self.assertTrue(ignored_review.is_file())
            self.assertNotIn("prospect-001", stdout.getvalue())

    def test_live_actions_require_ignored_untracked_git_paths(self) -> None:
        with TemporaryDirectory() as tmp:
            repository = Path(tmp)
            subprocess.run(
                ["git", "init", "--quiet", str(repository)],
                check=True,
            )
            row = _row(
                status="drafted",
                contacted_on="",
                next_action_on="",
                approved_on="",
            )
            unignored_ledger = repository / "candidate.csv"
            tracked_ledger = repository / "tracked.csv"
            _write_ledger(unignored_ledger, [row])
            _write_ledger(tracked_ledger, [row])
            subprocess.run(
                ["git", "-C", str(repository), "add", "tracked.csv"],
                check=True,
            )

            live_actions = (
                ("review", ["--review-next"]),
                (
                    "approval",
                    [
                        "--approve-next",
                        "prospect-001",
                        "--approved-on",
                        "2026-07-13",
                        "--confirm-reviewed",
                    ],
                ),
                (
                    "decline",
                    [
                        "--decline-next",
                        "prospect-001",
                        "--confirm-not-send",
                    ],
                ),
                (
                    "contact",
                    [
                        "--record-contact",
                        "prospect-001",
                        "--contacted-on",
                        "2026-07-13",
                        "--confirm-sent",
                    ],
                ),
                (
                    "follow-up",
                    [
                        "--record-follow-up",
                        "prospect-001",
                        "--followed-up-on",
                        "2026-07-13",
                        "--confirm-follow-up-sent",
                    ],
                ),
            )
            for action, arguments in live_actions:
                with self.subTest(path="unignored", action=action):
                    stderr = io.StringIO()
                    with redirect_stderr(stderr):
                        exit_code = main(
                            [
                                str(unignored_ledger),
                                "--as-of",
                                "2026-07-13",
                                *arguments,
                            ]
                        )
                    self.assertEqual(exit_code, 2)
                    self.assertIn(
                        "must be ignored and untracked before live outreach actions",
                        stderr.getvalue(),
                    )

            stderr = io.StringIO()
            with redirect_stderr(stderr):
                exit_code = main(
                    [
                        str(tracked_ledger),
                        "--as-of",
                        "2026-07-13",
                        "--review-next",
                    ]
                )
            self.assertEqual(exit_code, 2)
            self.assertIn(
                "must be ignored and untracked before live outreach actions",
                stderr.getvalue(),
            )

            private_directory = repository / "outreach-private"
            private_directory.mkdir(mode=0o700)
            (repository / ".gitignore").write_text(
                "/outreach-private/\n", encoding="utf-8"
            )
            private_ledger = private_directory / "outreach-ledger.csv"
            private_notes = private_directory / "drafts.md"
            _write_ledger(private_ledger, [row])
            private_notes.write_text(
                "## prospect-001\n\nSelected private message\n",
                encoding="utf-8",
            )
            if os.name == "posix":
                private_notes.chmod(0o600)

                private_ledger.chmod(0o640)
                before = private_ledger.read_bytes()
                stderr = io.StringIO()
                with redirect_stderr(stderr):
                    exit_code = main(
                        [
                            str(private_ledger),
                            "--as-of",
                            "2026-07-13",
                            "--review-next",
                        ]
                    )
                self.assertEqual(exit_code, 2)
                self.assertEqual(private_ledger.read_bytes(), before)
                self.assertIn("chmod 600", stderr.getvalue())
                private_ledger.chmod(0o600)

                private_directory.chmod(0o750)
                stderr = io.StringIO()
                with redirect_stderr(stderr):
                    exit_code = main(
                        [
                            str(private_ledger),
                            "--as-of",
                            "2026-07-13",
                            "--review-next",
                        ]
                    )
                self.assertEqual(exit_code, 2)
                self.assertIn("chmod 700", stderr.getvalue())
                private_directory.chmod(0o700)

                private_notes.chmod(0o644)
                stderr = io.StringIO()
                with redirect_stderr(stderr):
                    exit_code = main(
                        [
                            str(private_ledger),
                            "--as-of",
                            "2026-07-13",
                            "--review-next",
                            "--include-private-draft",
                            str(private_notes),
                        ]
                    )
                self.assertEqual(exit_code, 2)
                self.assertIn("chmod 600", stderr.getvalue())
                private_notes.chmod(0o600)

            linked_ledger = private_directory / "linked-ledger.csv"
            linked_ledger.symlink_to(unignored_ledger)
            stderr = io.StringIO()
            with redirect_stderr(stderr):
                exit_code = main(
                    [
                        str(linked_ledger),
                        "--as-of",
                        "2026-07-13",
                        "--review-next",
                    ]
                )
            self.assertEqual(exit_code, 2)
            self.assertIn("must not be a symbolic link", stderr.getvalue())

            unignored_notes = repository / "drafts.md"
            unignored_notes.write_text(
                "## prospect-001\n\nSelected private message\n",
                encoding="utf-8",
            )
            if os.name == "posix":
                unignored_notes.chmod(0o600)
            stderr = io.StringIO()
            with redirect_stderr(stderr):
                exit_code = main(
                    [
                        str(private_ledger),
                        "--as-of",
                        "2026-07-13",
                        "--review-next",
                        "--include-private-draft",
                        str(unignored_notes),
                    ]
                )
            self.assertEqual(exit_code, 2)
            self.assertIn(
                "private draft notes inside a Git worktree must be ignored",
                stderr.getvalue(),
            )

            stdout = io.StringIO()
            with redirect_stdout(stdout):
                exit_code = main(
                    [
                        str(private_ledger),
                        "--as-of",
                        "2026-07-13",
                        "--review-next",
                        "--include-private-draft",
                        str(private_notes),
                        "--format",
                        "json",
                    ]
                )

            self.assertEqual(exit_code, 0)
            report = json.loads(stdout.getvalue())
            self.assertEqual(report["review"]["prospect_id"], "prospect-001")
            self.assertEqual(
                report["review"]["private_draft"], "Selected private message"
            )

    def test_review_next_cli_builds_a_read_only_private_review_bundle(self) -> None:
        with TemporaryDirectory() as tmp:
            ledger = Path(tmp) / "ledger.csv"
            notes = Path(tmp) / "drafts.md"
            row = _row(
                status="drafted",
                contacted_on="",
                next_action_on="",
                approved_on="",
            )
            _write_ledger(ledger, [row])
            notes.write_text(
                "# Private drafts\n\n"
                f"## prospect-001\n\n"
                f"{_review_message('Selected private message')}\n",
                encoding="utf-8",
            )
            if os.name == "posix":
                notes.chmod(0o600)
            before = ledger.read_bytes()
            stdout = io.StringIO()

            with redirect_stdout(stdout):
                exit_code = main(
                    [
                        str(ledger),
                        "--as-of",
                        "2026-07-13",
                        "--review-next",
                        "--include-private-evidence",
                        "--include-private-draft",
                        str(notes),
                        "--format",
                        "json",
                    ]
                )

            self.assertEqual(exit_code, 0)
            self.assertEqual(ledger.read_bytes(), before)
            report = json.loads(stdout.getvalue())
            self.assertTrue(report["private_evidence_included"])
            self.assertTrue(report["private_draft_included"])
            self.assertRegex(report["review_digest"], r"\Asha256:[0-9a-f]{64}\Z")
            self.assertEqual(
                report["review"]["private_draft"],
                _review_message("Selected private message"),
            )
            text = format_next_outreach_review(
                report,
                ledger=ledger,
                private_drafts_path=notes,
            )
            self.assertIn(
                f"--review-digest {report['review_digest']}",
                text,
            )
            self.assertEqual(text.count("--reviewed-private-draft"), 2)
            self.assertIn(shlex.quote(str(notes)), text)
            self.assertEqual(text.count("--as-of YYYY-MM-DD"), 2)
            self.assertIn("--approved-on YYYY-MM-DD", text)
            self.assertNotIn("--as-of 2026-07-13 --approve-next", text)

    def test_content_bound_review_requires_exactly_one_campaign_route(
        self,
    ) -> None:
        rows = [
            _row(
                status="drafted",
                contacted_on="",
                next_action_on="",
                approved_on="",
            )
        ]
        cases = (
            "Reviewed private message without the offer link",
            (
                "Reviewed private message\n\n"
                f"{DIRECT_OUTREACH_ROUTE}\n\n"
                f"{DIRECT_OUTREACH_ROUTE}"
            ),
        )

        for private_draft in cases:
            with self.subTest(
                route_count=private_draft.count(DIRECT_OUTREACH_ROUTE)
            ):
                with self.assertRaisesRegex(
                    OutreachInputError,
                    "private draft must contain the canonical "
                    "direct-outreach route exactly once",
                ):
                    build_next_outreach_review(
                        rows,
                        as_of=date(2026, 7, 13),
                        include_private_evidence=True,
                        private_drafts={"prospect-001": private_draft},
                    )

    def test_content_bound_review_requires_unambiguous_pilot_price(
        self,
    ) -> None:
        rows = [
            _row(
                status="drafted",
                contacted_on="",
                next_action_on="",
                approved_on="",
            )
        ]
        cases = (
            f"Reviewed private message\n\n{DIRECT_OUTREACH_ROUTE}",
            (
                "Reviewed private message for $299, repeated at $299\n\n"
                f"{DIRECT_OUTREACH_ROUTE}"
            ),
            (
                "Reviewed private message: this pilot is not $299.\n\n"
                f"{DIRECT_OUTREACH_ROUTE}"
            ),
            (
                "Pilot price: $299, but you will not pay it.\n\n"
                f"{DIRECT_OUTREACH_ROUTE}"
            ),
            (
                "Pilot price: $299; there is no payment required.\n\n"
                f"{DIRECT_OUTREACH_ROUTE}"
            ),
            (
                "No payment is required for this pilot. "
                "The pilot price is $299.\n\n"
                f"{DIRECT_OUTREACH_ROUTE}"
            ),
            (
                "Reviewed private message for $299, or $199 instead.\n\n"
                f"{DIRECT_OUTREACH_ROUTE}"
            ),
            (
                "Reviewed private message for $2999.\n\n"
                f"{DIRECT_OUTREACH_ROUTE}"
            ),
        )

        for private_draft in cases:
            with self.subTest(price_count=private_draft.count("$299")):
                with self.assertRaisesRegex(
                    OutreachInputError,
                    r"private draft must disclose the \$299 pilot price "
                    "exactly once without negation or another dollar price",
                ):
                    build_next_outreach_review(
                        rows,
                        as_of=date(2026, 7, 13),
                        include_private_evidence=True,
                        private_drafts={"prospect-001": private_draft},
                    )

    def test_content_bound_review_accepts_fixed_pilot_price_wording(
        self,
    ) -> None:
        rows = [
            _row(
                status="drafted",
                contacted_on="",
                next_action_on="",
                approved_on="",
            )
        ]
        private_draft = (
            "The pilot price is not negotiable at $299.\n\n"
            f"{DIRECT_OUTREACH_ROUTE}"
        )

        report = build_next_outreach_review(
            rows,
            as_of=date(2026, 7, 13),
            include_private_evidence=True,
            private_drafts={"prospect-001": private_draft},
        )

        self.assertIsInstance(report["review_digest"], str)

    def test_content_bound_review_can_be_decided_on_a_later_date(self) -> None:
        cases = (
            (
                "approval",
                (
                    "--approve-next",
                    "prospect-001",
                    "--approved-on",
                    "2026-07-15",
                    "--confirm-reviewed",
                ),
                "approved",
                "2026-07-15",
            ),
            (
                "decline",
                (
                    "--decline-next",
                    "prospect-001",
                    "--confirm-not-send",
                ),
                "review-declined",
                "",
            ),
        )
        for decision, arguments, expected_status, expected_approved_on in cases:
            with self.subTest(decision=decision), TemporaryDirectory() as tmp:
                ledger = Path(tmp) / "ledger.csv"
                notes = Path(tmp) / "drafts.md"
                _write_ledger(
                    ledger,
                    [
                        _row(
                            status="drafted",
                            contacted_on="",
                            next_action_on="",
                            approved_on="",
                        )
                    ],
                )
                notes.write_text(
                    f"## prospect-001\n\n"
                    f"{_review_message('Reviewed private message')}\n",
                    encoding="utf-8",
                )
                if os.name == "posix":
                    notes.chmod(0o600)

                review_stdout = io.StringIO()
                with redirect_stdout(review_stdout):
                    review_exit_code = main(
                        [
                            str(ledger),
                            "--as-of",
                            "2026-07-13",
                            "--review-next",
                            "--include-private-evidence",
                            "--include-private-draft",
                            str(notes),
                            "--format",
                            "json",
                        ]
                    )
                self.assertEqual(review_exit_code, 0)
                review_digest = json.loads(review_stdout.getvalue())[
                    "review_digest"
                ]

                decision_stdout = io.StringIO()
                with redirect_stdout(decision_stdout):
                    decision_exit_code = main(
                        [
                            str(ledger),
                            "--as-of",
                            "2026-07-15",
                            *arguments,
                            "--review-digest",
                            review_digest,
                            "--reviewed-private-draft",
                            str(notes),
                        ]
                    )

                self.assertEqual(decision_exit_code, 0)
                with ledger.open(newline="", encoding="utf-8") as ledger_file:
                    row = next(csv.DictReader(ledger_file))
                self.assertEqual(row["status"], expected_status)
                self.assertEqual(row["approved_on"], expected_approved_on)

    def test_private_draft_notes_reject_missing_or_ambiguous_sections(self) -> None:
        with TemporaryDirectory() as tmp:
            ledger = Path(tmp) / "ledger.csv"
            notes = Path(tmp) / "drafts.md"
            _write_ledger(
                ledger,
                [
                    _row(
                        status="drafted",
                        contacted_on="",
                        next_action_on="",
                        approved_on="",
                    )
                ],
            )
            cases = (
                (
                    "## prospect-002\n\nOther private message\n",
                    "missing a drafted section: prospect-001",
                ),
                (
                    "## prospect-001\n\nFirst\n\n## prospect-001\n\nSecond\n",
                    "duplicate section: prospect-001",
                ),
                (
                    "## recipient details\n\nPrivate message\n",
                    "section heading must be ## prospect-NNN",
                ),
                (
                    "## prospect-001\n\n",
                    "private draft section prospect-001 cannot be empty",
                ),
                (
                    "x" * (128 * 1024 + 1),
                    "private draft notes exceed 131072 bytes",
                ),
                (
                    "## prospect-001\n\nPrivate\x1b[31m message\n",
                    "private draft notes cannot contain control characters",
                ),
            )

            for content, expected in cases:
                with self.subTest(expected=expected):
                    notes.write_text(content, encoding="utf-8")
                    if os.name == "posix":
                        notes.chmod(0o600)
                    stderr = io.StringIO()
                    with redirect_stderr(stderr):
                        exit_code = main(
                            [
                                str(ledger),
                                "--as-of",
                                "2026-07-13",
                                "--review-next",
                                "--include-private-draft",
                                str(notes),
                            ]
                        )
                    self.assertEqual(exit_code, 2)
                    self.assertIn(expected, stderr.getvalue())
                    self.assertNotIn("Private message", stderr.getvalue())

    def test_private_draft_notes_reject_sections_absent_from_ledger(self) -> None:
        with TemporaryDirectory() as tmp:
            ledger = Path(tmp) / "ledger.csv"
            notes = Path(tmp) / "drafts.md"
            _write_ledger(
                ledger,
                [
                    _row(
                        status="drafted",
                        contacted_on="",
                        next_action_on="",
                        approved_on="",
                    )
                ],
            )
            notes.write_text(
                "## prospect-001\n\nSelected private message\n\n"
                "## prospect-999\n\nUnknown private message\n",
                encoding="utf-8",
            )
            if os.name == "posix":
                notes.chmod(0o600)
            before = ledger.read_bytes()
            stderr = io.StringIO()

            with redirect_stderr(stderr):
                exit_code = main(
                    [
                        str(ledger),
                        "--as-of",
                        "2026-07-13",
                        "--review-next",
                        "--include-private-draft",
                        str(notes),
                    ]
                )

            self.assertEqual(exit_code, 2)
            self.assertEqual(ledger.read_bytes(), before)
            self.assertIn(
                "section absent from the ledger: prospect-999",
                stderr.getvalue(),
            )
            self.assertNotIn("Unknown private message", stderr.getvalue())

    def test_private_review_flags_require_review_next(self) -> None:
        with TemporaryDirectory() as tmp:
            ledger = Path(tmp) / "ledger.csv"
            _write_ledger(
                ledger,
                [
                    _row(
                        status="drafted",
                        contacted_on="",
                        next_action_on="",
                        approved_on="",
                    )
                ],
            )
            stderr = io.StringIO()

            cases = (
                (
                    ["--include-private-evidence"],
                    "--include-private-evidence requires --review-next",
                ),
                (
                    ["--include-private-draft", str(Path(tmp) / "drafts.md")],
                    "--include-private-draft requires --review-next",
                ),
            )
            for arguments, expected in cases:
                with self.subTest(expected=expected):
                    stderr = io.StringIO()
                    with redirect_stderr(stderr):
                        exit_code = main(
                            [
                                str(ledger),
                                "--as-of",
                                "2026-07-13",
                                *arguments,
                            ]
                        )
                    self.assertEqual(exit_code, 2)
                    self.assertIn(expected, stderr.getvalue())

    def test_review_next_reports_when_no_drafts_are_waiting(self) -> None:
        report = build_next_outreach_review(
            [
                _row(
                    status="approved",
                    contacted_on="",
                    next_action_on="",
                    approved_on="2026-07-11",
                )
            ],
            as_of=date(2026, 7, 13),
            include_private_evidence=True,
        )

        self.assertIsNone(report["review"])
        self.assertFalse(report["private_evidence_included"])
        self.assertFalse(report["private_draft_included"])
        self.assertIn(
            "No drafts are awaiting human review.",
            format_next_outreach_review(report, ledger=Path("ledger.csv")),
        )

    def test_pending_approval_blocks_another_review_or_decision(self) -> None:
        rows = [
            _row(
                prospect_id="prospect-001",
                status="approved",
                contacted_on="",
                next_action_on="",
                approved_on="2026-07-12",
            ),
            _row(
                prospect_id="prospect-002",
                status="drafted",
                contacted_on="",
                next_action_on="",
                approved_on="",
            ),
        ]
        message = "send the pending approved message manually"

        with self.assertRaisesRegex(OutreachInputError, message):
            build_next_outreach_review(rows, as_of=date(2026, 7, 13))

        with TemporaryDirectory() as tmp:
            ledger = Path(tmp) / "ledger.csv"
            blocked_review = Path(tmp) / "blocked review.md"
            cases = (
                ["--review-next"],
                ["--review-next", "--write-review", str(blocked_review)],
                [
                    "--approve-next",
                    "prospect-002",
                    "--approved-on",
                    "2026-07-13",
                    "--confirm-reviewed",
                ],
                [
                    "--decline-next",
                    "prospect-002",
                    "--confirm-not-send",
                ],
            )
            for arguments in cases:
                with self.subTest(arguments=arguments):
                    _write_ledger(ledger, rows)
                    before = ledger.read_bytes()
                    before_mode = ledger.stat().st_mode
                    stdout = io.StringIO()
                    stderr = io.StringIO()
                    with redirect_stdout(stdout), redirect_stderr(stderr):
                        exit_code = main(
                            [
                                str(ledger),
                                "--as-of",
                                "2026-07-13",
                                *arguments,
                            ]
                        )

                    self.assertEqual(exit_code, 2)
                    self.assertEqual(stdout.getvalue(), "")
                    self.assertIn(message, stderr.getvalue())
                    self.assertNotIn("prospect-001", stderr.getvalue())
                    self.assertNotIn("evidence.example", stderr.getvalue())
                    self.assertEqual(ledger.read_bytes(), before)
                    self.assertEqual(ledger.stat().st_mode, before_mode)
                    self.assertFalse(blocked_review.exists())
                    self.assertEqual(
                        list(Path(tmp).glob(".repo-scout-ledger.*.tmp")),
                        [],
                    )
                    self.assertEqual(
                        list(Path(tmp).glob(".repo-scout-review.*.tmp")),
                        [],
                    )

            with redirect_stdout(io.StringIO()):
                self.assertEqual(
                    main(
                        [
                            str(ledger),
                            "--as-of",
                            "2026-07-13",
                            "--record-contact",
                            "prospect-001",
                            "--contacted-on",
                            "2026-07-13",
                            "--confirm-sent",
                        ]
                    ),
                    0,
                )
            review_stdout = io.StringIO()
            with redirect_stdout(review_stdout):
                self.assertEqual(
                    main(
                        [
                            str(ledger),
                            "--as-of",
                            "2026-07-13",
                            "--review-next",
                        ]
                    ),
                    0,
                )
            self.assertIn("Prospect alias: prospect-002", review_stdout.getvalue())

    def test_pending_approval_can_be_canceled_without_an_attempt(self) -> None:
        with TemporaryDirectory() as tmp:
            ledger = Path(tmp) / "ledger.csv"
            original_rows = [
                _row(
                    prospect_id="prospect-001",
                    status="approved",
                    contacted_on="",
                    next_action_on="",
                    approved_on="2026-07-12",
                    approved_review_digest=f"sha256:{'a' * 64}",
                ),
                _row(
                    prospect_id="prospect-002",
                    status="drafted",
                    contacted_on="",
                    next_action_on="",
                    approved_on="",
                ),
            ]
            _write_ledger(ledger, original_rows)
            before = ledger.read_bytes()
            before_mode = ledger.stat().st_mode
            rejected_stdout = io.StringIO()
            rejected_stderr = io.StringIO()

            with redirect_stdout(rejected_stdout), redirect_stderr(
                rejected_stderr
            ):
                rejected_exit_code = main(
                    [
                        str(ledger),
                        "--as-of",
                        "2026-07-13",
                        "--decline-next",
                        "prospect-001",
                        "--confirm-not-send",
                    ]
                )

            self.assertEqual(rejected_exit_code, 2)
            self.assertEqual(rejected_stdout.getvalue(), "")
            self.assertIn(
                "requires --confirm-not-sent",
                rejected_stderr.getvalue(),
            )
            self.assertNotIn("prospect-001", rejected_stderr.getvalue())
            self.assertEqual(ledger.read_bytes(), before)
            self.assertEqual(ledger.stat().st_mode, before_mode)
            self.assertEqual(
                list(Path(tmp).glob(".repo-scout-ledger.*.tmp")), []
            )
            stdout = io.StringIO()

            with redirect_stdout(stdout):
                exit_code = main(
                    [
                        str(ledger),
                        "--as-of",
                        "2026-07-13",
                        "--decline-next",
                        "prospect-001",
                        "--confirm-not-send",
                        "--confirm-not-sent",
                        "--format",
                        "json",
                    ]
                )

            self.assertEqual(exit_code, 0)
            self.assertEqual(ledger.stat().st_mode & 0o777, 0o600)
            with ledger.open(newline="", encoding="utf-8") as ledger_file:
                rows = list(csv.DictReader(ledger_file))
            original_by_id = {row["prospect_id"]: row for row in original_rows}
            rows_by_id = {row["prospect_id"]: row for row in rows}
            canceled = rows_by_id["prospect-001"]
            changed_fields = {
                field
                for field in LEDGER_FIELDS
                if canceled[field] != original_by_id["prospect-001"][field]
            }
            self.assertEqual(
                changed_fields,
                {"status", "approved_on", "approved_review_digest"},
            )
            self.assertEqual(canceled["status"], "review-declined")
            self.assertEqual(canceled["approved_on"], "")
            self.assertEqual(canceled["approved_review_digest"], "")
            self.assertEqual(
                rows_by_id["prospect-002"], original_by_id["prospect-002"]
            )

            report = load_outreach_report(ledger, as_of=date(2026, 7, 13))
            self.assertEqual(report["summary"]["approved"], 0)
            self.assertEqual(report["summary"]["review_declined"], 1)
            self.assertEqual(report["summary"]["attempted_prospects"], 0)
            review = build_next_outreach_review(rows, as_of=date(2026, 7, 13))
            self.assertEqual(review["review"]["prospect_id"], "prospect-002")

            receipt = json.loads(stdout.getvalue())
            self.assertEqual(receipt["schema_version"], 4)
            self.assertTrue(receipt["human_not_sent_confirmed"])
            self.assertEqual(
                receipt["queue"],
                {"drafts_remaining": 1, "approvals_remaining": 0},
            )
            self.assertEqual(receipt["decline"]["previous_status"], "approved")
            self.assertIn("pending approval was canceled", receipt["action_note"])
            self.assertNotIn("approved_on", json.dumps(receipt))
            self.assertNotIn("review_digest", json.dumps(receipt))
            self.assertEqual(
                list(Path(tmp).glob(".repo-scout-ledger.*.tmp")), []
            )

    def test_canceling_one_of_multiple_approvals_keeps_review_blocked(
        self,
    ) -> None:
        with TemporaryDirectory() as tmp:
            ledger = Path(tmp) / "ledger.csv"
            rows = [
                _row(
                    prospect_id="prospect-001",
                    status="approved",
                    contacted_on="",
                    next_action_on="",
                    approved_on="2026-07-11",
                ),
                _row(
                    prospect_id="prospect-002",
                    status="approved",
                    contacted_on="",
                    next_action_on="",
                    approved_on="2026-07-12",
                ),
                _row(
                    prospect_id="prospect-003",
                    status="drafted",
                    contacted_on="",
                    next_action_on="",
                    approved_on="",
                ),
            ]
            _write_ledger(ledger, rows)
            before = ledger.read_bytes()
            stderr = io.StringIO()

            with redirect_stderr(stderr):
                exit_code = main(
                    [
                        str(ledger),
                        "--as-of",
                        "2026-07-13",
                        "--decline-next",
                        "prospect-002",
                        "--confirm-not-send",
                    ]
                )

            self.assertEqual(exit_code, 2)
            self.assertIn("send the pending approved message", stderr.getvalue())
            self.assertEqual(ledger.read_bytes(), before)

            stdout = io.StringIO()
            with redirect_stdout(stdout):
                self.assertEqual(
                    main(
                        [
                            str(ledger),
                            "--as-of",
                            "2026-07-13",
                            "--decline-next",
                            "prospect-001",
                            "--confirm-not-send",
                            "--confirm-not-sent",
                        ]
                    ),
                    0,
                )

            text = stdout.getvalue()
            self.assertIn("Approvals remaining: 1", text)
            self.assertIn("Review remains blocked", text)
            self.assertNotIn("--review-next", text)
            report = load_outreach_report(ledger, as_of=date(2026, 7, 13))
            self.assertEqual(report["summary"]["approved"], 1)
            self.assertEqual(report["summary"]["review_declined"], 1)
            self.assertEqual(report["summary"]["drafted"], 1)
            self.assertEqual(report["summary"]["attempted_prospects"], 0)

    def test_contacted_message_cannot_be_canceled(self) -> None:
        with TemporaryDirectory() as tmp:
            ledger = Path(tmp) / "ledger.csv"
            _write_ledger(ledger, [_row()])
            before = ledger.read_bytes()
            stderr = io.StringIO()

            with redirect_stderr(stderr):
                exit_code = main(
                    [
                        str(ledger),
                        "--as-of",
                        "2026-07-13",
                        "--decline-next",
                        "prospect-001",
                        "--confirm-not-send",
                    ]
                )

            self.assertEqual(exit_code, 2)
            self.assertIn(
                "no drafted prospects await a review decision",
                stderr.getvalue(),
            )
            self.assertEqual(ledger.read_bytes(), before)
            report = load_outreach_report(ledger, as_of=date(2026, 7, 13))
            self.assertEqual(report["summary"]["attempted_prospects"], 1)

    def test_approve_next_records_review_without_contact_or_private_data(self) -> None:
        with TemporaryDirectory() as tmp:
            ledger = Path(tmp) / "ledger.csv"
            notes = Path(tmp) / "drafts.md"
            original_rows = [
                _row(
                    prospect_id="prospect-002",
                    status="drafted",
                    contacted_on="",
                    next_action_on="",
                    approved_on="",
                ),
                _row(
                    prospect_id="prospect-001",
                    status="drafted",
                    contacted_on="",
                    next_action_on="",
                    approved_on="",
                ),
            ]
            _write_ledger(ledger, original_rows)
            ledger.chmod(0o600)
            review_digest = _write_content_bound_review(
                notes,
                original_rows,
                as_of=date(2026, 7, 13),
            )
            stdout = io.StringIO()

            with redirect_stdout(stdout):
                exit_code = main(
                    [
                        str(ledger),
                        "--as-of",
                        "2026-07-13",
                        "--approve-next",
                        "prospect-001",
                        "--approved-on",
                        "2026-07-12",
                        "--confirm-reviewed",
                        "--review-digest",
                        review_digest,
                        "--reviewed-private-draft",
                        str(notes),
                        "--format",
                        "json",
                    ]
                )

            self.assertEqual(exit_code, 0)
            self.assertEqual(ledger.stat().st_mode & 0o777, 0o600)
            with ledger.open(newline="", encoding="utf-8") as ledger_file:
                rows = list(csv.DictReader(ledger_file))
            original_by_id = {row["prospect_id"]: row for row in original_rows}
            rows_by_id = {row["prospect_id"]: row for row in rows}
            approved = rows_by_id["prospect-001"]
            changed_fields = {
                field
                for field in LEDGER_FIELDS
                if approved[field] != original_by_id["prospect-001"][field]
            }
            self.assertEqual(
                changed_fields,
                {"status", "approved_on", "approved_review_digest"},
            )
            self.assertEqual(
                rows_by_id["prospect-002"], original_by_id["prospect-002"]
            )
            self.assertEqual(approved["status"], "approved")
            self.assertEqual(approved["approved_on"], "2026-07-12")
            self.assertEqual(
                approved["approved_review_digest"], review_digest
            )
            self.assertEqual(approved["contacted_on"], "")
            self.assertEqual(approved["next_action_on"], "")
            report = load_outreach_report(ledger, as_of=date(2026, 7, 13))
            self.assertEqual(report["summary"]["approved"], 1)
            self.assertEqual(report["summary"]["drafted"], 1)
            self.assertEqual(report["summary"]["attempted_prospects"], 0)
            self.assertEqual(
                report["next_approved"],
                {
                    "prospect_id": "prospect-001",
                    "review_digest": review_digest,
                },
            )
            receipt = json.loads(stdout.getvalue())
            self.assertEqual(receipt["schema_version"], 3)
            self.assertTrue(receipt["private_output"])
            self.assertTrue(receipt["human_review_confirmed"])
            self.assertEqual(receipt["approval"]["status"], "approved")
            self.assertEqual(
                receipt["approval"]["review_digest"], review_digest
            )
            self.assertEqual(receipt["queue"], {"drafts_remaining": 1})
            self.assertNotIn("approved_on", json.dumps(receipt))
            self.assertNotIn("2026-07-12", json.dumps(receipt))
            self.assertNotIn("evidence.example", json.dumps(receipt))
            self.assertIn("No outreach was sent", receipt["action_note"])
            self.assertEqual(
                list(Path(tmp).glob(".repo-scout-ledger.*.tmp")), []
            )

    def test_approve_next_requires_a_content_bound_review_without_mutation(
        self,
    ) -> None:
        with TemporaryDirectory() as tmp:
            ledger = Path(tmp) / "ledger.csv"
            rows = [
                _row(
                    status="drafted",
                    contacted_on="",
                    next_action_on="",
                    approved_on="",
                )
            ]
            _write_ledger(ledger, rows)
            before = ledger.read_bytes()
            before_mode = ledger.stat().st_mode
            stdout = io.StringIO()
            stderr = io.StringIO()

            with redirect_stdout(stdout), redirect_stderr(stderr):
                exit_code = main(
                    [
                        str(ledger),
                        "--as-of",
                        "2026-07-13",
                        "--approve-next",
                        "prospect-001",
                        "--approved-on",
                        "2026-07-12",
                        "--confirm-reviewed",
                    ]
                )

            self.assertEqual(exit_code, 2)
            self.assertEqual(stdout.getvalue(), "")
            self.assertIn(
                "--approve-next requires --review-digest and "
                "--reviewed-private-draft",
                stderr.getvalue(),
            )
            self.assertNotIn("prospect-001", stderr.getvalue())
            self.assertNotIn("evidence.example", stderr.getvalue())
            self.assertEqual(ledger.read_bytes(), before)
            self.assertEqual(ledger.stat().st_mode, before_mode)
            self.assertEqual(
                list(Path(tmp).glob(".repo-scout-ledger.*.tmp")), []
            )

    def test_content_bound_approval_preserves_post_contact_next_review(
        self,
    ) -> None:
        with TemporaryDirectory() as tmp:
            ledger = Path(tmp) / "private ledger.csv"
            notes = Path(tmp) / "private drafts.md"
            _write_ledger(
                ledger,
                [
                    _row(
                        prospect_id="prospect-001",
                        status="drafted",
                        contacted_on="",
                        next_action_on="",
                        approved_on="",
                    ),
                    _row(
                        prospect_id="prospect-002",
                        status="drafted",
                        contacted_on="",
                        next_action_on="",
                        approved_on="",
                    ),
                ],
            )
            notes.write_text(
                f"## prospect-001\n\n"
                f"{_review_message('First private message')}\n\n"
                f"## prospect-002\n\n"
                f"{_review_message('Second private message')}\n",
                encoding="utf-8",
            )
            if os.name == "posix":
                notes.chmod(0o600)

            review_stdout = io.StringIO()
            with redirect_stdout(review_stdout):
                self.assertEqual(
                    main(
                        [
                            str(ledger),
                            "--as-of",
                            "2026-07-13",
                            "--review-next",
                            "--include-private-evidence",
                            "--include-private-draft",
                            str(notes),
                            "--format",
                            "json",
                        ]
                    ),
                    0,
                )
            first_review = json.loads(review_stdout.getvalue())

            approval_stdout = io.StringIO()
            with redirect_stdout(approval_stdout):
                self.assertEqual(
                    main(
                        [
                            str(ledger),
                            "--as-of",
                            "2026-07-13",
                            "--approve-next",
                            "prospect-001",
                            "--approved-on",
                            "2026-07-13",
                            "--confirm-reviewed",
                            "--review-digest",
                            first_review["review_digest"],
                            "--reviewed-private-draft",
                            str(notes),
                        ]
                    ),
                    0,
                )

            approval_text = approval_stdout.getvalue()
            self.assertIn("Drafts remaining: 1", approval_text)
            self.assertIn("After that send is recorded", approval_text)
            command_lines = [
                line
                for line in approval_text.splitlines()
                if line.startswith("repo-scout-outreach ")
            ]
            self.assertEqual(len(command_lines), 3)

            cancel_command = shlex.split(
                next(
                    line
                    for line in command_lines
                    if "--decline-next" in shlex.split(line)
                )
            )[1:]
            self.assertEqual(cancel_command.count(DATE_PLACEHOLDER), 1)
            self.assertIn("--confirm-not-send", cancel_command)
            self.assertIn("--confirm-not-sent", cancel_command)
            self.assertNotIn("--review-digest", cancel_command)

            contact_command = shlex.split(
                next(
                    line
                    for line in command_lines
                    if "--record-contact" in shlex.split(line)
                )
            )[1:]
            self.assertEqual(contact_command.count(DATE_PLACEHOLDER), 2)
            with redirect_stdout(io.StringIO()):
                self.assertEqual(
                    main(
                        [
                            (
                                "2026-07-14"
                                if value == DATE_PLACEHOLDER
                                else value
                            )
                            for value in contact_command
                        ]
                    ),
                    0,
                )

            next_review_line = next(
                line
                for line in command_lines
                if "--review-next" in shlex.split(line)
            )
            next_review_command = shlex.split(next_review_line)[1:]
            self.assertEqual(next_review_command.count(DATE_PLACEHOLDER), 1)
            self.assertIn("--include-private-evidence", next_review_command)
            self.assertEqual(
                next_review_command[
                    next_review_command.index("--include-private-draft") + 1
                ],
                str(notes),
            )
            self.assertEqual(
                next_review_command[
                    next_review_command.index("--write-review") + 1
                ],
                REVIEW_OUTPUT_PLACEHOLDER,
            )
            self.assertIn(f"'{REVIEW_OUTPUT_PLACEHOLDER}'", next_review_line)
            next_review_path = Path(tmp) / "next review.md"
            replaced_command = next_review_line.replace(
                DATE_PLACEHOLDER,
                "2026-07-15",
            ).replace(
                REVIEW_OUTPUT_PLACEHOLDER,
                str(next_review_path),
            )
            next_review_stdout = io.StringIO()
            with redirect_stdout(next_review_stdout):
                self.assertEqual(
                    main(shlex.split(replaced_command)[1:]),
                    0,
                )
            self.assertEqual(
                next_review_stdout.getvalue(),
                "Private review written with owner-only permissions.\n",
            )
            next_review = next_review_path.read_text(encoding="utf-8")
            self.assertIn("Prospect alias: prospect-002", next_review)
            self.assertIn("Second private message", next_review)
            self.assertNotIn("First private message", next_review)
            if os.name == "posix":
                self.assertEqual(
                    next_review_path.stat().st_mode & 0o777,
                    0o600,
                )

    def test_content_bound_approve_rejects_an_edited_private_draft(self) -> None:
        with TemporaryDirectory() as tmp:
            ledger = Path(tmp) / "ledger.csv"
            notes = Path(tmp) / "drafts.md"
            _write_ledger(
                ledger,
                [
                    _row(
                        status="drafted",
                        contacted_on="",
                        next_action_on="",
                        approved_on="",
                    )
                ],
            )
            notes.write_text(
                f"## prospect-001\n\n"
                f"{_review_message('Reviewed private message')}\n",
                encoding="utf-8",
            )
            if os.name == "posix":
                notes.chmod(0o600)
            review_stdout = io.StringIO()
            with redirect_stdout(review_stdout):
                exit_code = main(
                    [
                        str(ledger),
                        "--as-of",
                        "2026-07-13",
                        "--review-next",
                        "--include-private-evidence",
                        "--include-private-draft",
                        str(notes),
                        "--format",
                        "json",
                    ]
                )
            self.assertEqual(exit_code, 0)
            review_digest = json.loads(review_stdout.getvalue())["review_digest"]

            edited_drafts = (
                _review_message("Edited after human review"),
                (
                    "Edited after removing the price\n\n"
                    f"{DIRECT_OUTREACH_ROUTE}"
                ),
            )
            for edited_draft in edited_drafts:
                with self.subTest(price_count=edited_draft.count("$299")):
                    notes.write_text(
                        f"## prospect-001\n\n{edited_draft}\n",
                        encoding="utf-8",
                    )
                    if os.name == "posix":
                        notes.chmod(0o600)
                    before = ledger.read_bytes()
                    stderr = io.StringIO()
                    with redirect_stderr(stderr):
                        exit_code = main(
                            [
                                str(ledger),
                                "--as-of",
                                "2026-07-13",
                                "--approve-next",
                                "prospect-001",
                                "--approved-on",
                                "2026-07-13",
                                "--confirm-reviewed",
                                "--review-digest",
                                review_digest,
                                "--reviewed-private-draft",
                                str(notes),
                            ]
                        )

                    self.assertEqual(exit_code, 2)
                    self.assertEqual(ledger.read_bytes(), before)
                    self.assertIn(
                        "review content changed; run --review-next again "
                        "before deciding",
                        stderr.getvalue(),
                    )
                    self.assertNotIn("Edited after", stderr.getvalue())
                    self.assertEqual(
                        list(Path(tmp).glob(".repo-scout-ledger.*.tmp")),
                        [],
                    )

    def test_content_bound_approve_rejects_campaign_route_drift(self) -> None:
        with TemporaryDirectory() as tmp:
            ledger = Path(tmp) / "ledger.csv"
            notes = Path(tmp) / "drafts.md"
            _write_ledger(
                ledger,
                [
                    _row(
                        status="drafted",
                        contacted_on="",
                        next_action_on="",
                        approved_on="",
                    )
                ],
            )
            notes.write_text(
                f"## prospect-001\n\n"
                f"{_review_message('Reviewed private message')}\n",
                encoding="utf-8",
            )
            if os.name == "posix":
                notes.chmod(0o600)

            review_stdout = io.StringIO()
            with redirect_stdout(review_stdout):
                self.assertEqual(
                    main(
                        [
                            str(ledger),
                            "--as-of",
                            "2026-07-13",
                            "--review-next",
                            "--include-private-evidence",
                            "--include-private-draft",
                            str(notes),
                            "--format",
                            "json",
                        ]
                    ),
                    0,
                )
            review_digest = json.loads(review_stdout.getvalue())["review_digest"]
            before = ledger.read_bytes()
            stderr = io.StringIO()

            with (
                patch(
                    "repo_scout.outreach.DIRECT_OUTREACH_ROUTE",
                    "https://example.invalid/changed-route",
                ),
                redirect_stderr(stderr),
            ):
                exit_code = main(
                    [
                        str(ledger),
                        "--as-of",
                        "2026-07-13",
                        "--approve-next",
                        "prospect-001",
                        "--approved-on",
                        "2026-07-13",
                        "--confirm-reviewed",
                        "--review-digest",
                        review_digest,
                        "--reviewed-private-draft",
                        str(notes),
                    ]
                )

            self.assertEqual(exit_code, 2)
            self.assertEqual(ledger.read_bytes(), before)
            self.assertIn(
                "review content changed; run --review-next again before deciding",
                stderr.getvalue(),
            )
            self.assertNotIn("changed-route", stderr.getvalue())
            self.assertEqual(
                list(Path(tmp).glob(".repo-scout-ledger.*.tmp")), []
            )

    def test_content_bound_decisions_reject_private_draft_commit_races(
        self,
    ) -> None:
        import repo_scout.outreach as outreach_module

        cases = (
            (
                "approval",
                (
                    "--approve-next",
                    "prospect-001",
                    "--approved-on",
                    "2026-07-13",
                    "--confirm-reviewed",
                ),
            ),
            (
                "decline",
                (
                    "--decline-next",
                    "prospect-001",
                    "--confirm-not-send",
                ),
            ),
        )
        for decision, decision_arguments in cases:
            with self.subTest(decision=decision), TemporaryDirectory() as tmp:
                ledger = Path(tmp) / "ledger.csv"
                notes = Path(tmp) / "drafts.md"
                _write_ledger(
                    ledger,
                    [
                        _row(
                            status="drafted",
                            contacted_on="",
                            next_action_on="",
                            approved_on="",
                        )
                    ],
                )
                notes.write_text(
                    f"## prospect-001\n\n"
                    f"{_review_message('Reviewed private message')}\n",
                    encoding="utf-8",
                )
                if os.name == "posix":
                    notes.chmod(0o600)
                review = outreach_module.load_next_outreach_review(
                    ledger,
                    as_of=date(2026, 7, 13),
                    include_private_evidence=True,
                    private_drafts_path=notes,
                )
                before = ledger.read_bytes()
                original_write = outreach_module._write_outreach_rows
                edited_message = f"Edited during {decision}"

                def write_after_private_edit(
                    path: Path,
                    rows: list[dict[str, str]],
                    *,
                    expected_revision: str | None = None,
                    expected_private_draft_revision: (
                        tuple[Path, str] | None
                    ) = None,
                ) -> None:
                    notes.write_text(
                        f"## prospect-001\n\n"
                        f"{_review_message(edited_message)}\n",
                        encoding="utf-8",
                    )
                    original_write(
                        path,
                        rows,
                        expected_revision=expected_revision,
                        expected_private_draft_revision=(
                            expected_private_draft_revision
                        ),
                    )

                stderr = io.StringIO()
                with (
                    patch.object(
                        outreach_module,
                        "_write_outreach_rows",
                        side_effect=write_after_private_edit,
                    ),
                    redirect_stderr(stderr),
                ):
                    exit_code = main(
                        [
                            str(ledger),
                            "--as-of",
                            "2026-07-13",
                            *decision_arguments,
                            "--review-digest",
                            review["review_digest"],
                            "--reviewed-private-draft",
                            str(notes),
                        ]
                    )

                self.assertEqual(exit_code, 2)
                self.assertEqual(ledger.read_bytes(), before)
                self.assertIn(
                    "review content changed; run --review-next again before "
                    "deciding",
                    stderr.getvalue(),
                )
                self.assertNotIn(edited_message, stderr.getvalue())
                self.assertEqual(
                    list(Path(tmp).glob(".repo-scout-ledger.*.tmp")), []
                )

    def test_content_bound_approve_accepts_the_current_private_review(self) -> None:
        with TemporaryDirectory() as tmp:
            ledger = Path(tmp) / "ledger.csv"
            notes = Path(tmp) / "drafts.md"
            _write_ledger(
                ledger,
                [
                    _row(
                        status="drafted",
                        contacted_on="",
                        next_action_on="",
                        approved_on="",
                    )
                ],
            )
            notes.write_text(
                f"## prospect-001\n\n"
                f"{_review_message('Reviewed private message')}\n",
                encoding="utf-8",
            )
            if os.name == "posix":
                notes.chmod(0o600)
            review_stdout = io.StringIO()
            with redirect_stdout(review_stdout):
                exit_code = main(
                    [
                        str(ledger),
                        "--as-of",
                        "2026-07-13",
                        "--review-next",
                        "--include-private-evidence",
                        "--include-private-draft",
                        str(notes),
                        "--format",
                        "json",
                    ]
                )
            self.assertEqual(exit_code, 0)
            review_digest = json.loads(review_stdout.getvalue())["review_digest"]

            with redirect_stdout(io.StringIO()):
                exit_code = main(
                    [
                        str(ledger),
                        "--as-of",
                        "2026-07-13",
                        "--approve-next",
                        "prospect-001",
                        "--approved-on",
                        "2026-07-13",
                        "--confirm-reviewed",
                        "--review-digest",
                        review_digest,
                        "--reviewed-private-draft",
                        str(notes),
                    ]
                )

            self.assertEqual(exit_code, 0)
            report = load_outreach_report(ledger, as_of=date(2026, 7, 13))
            self.assertEqual(report["summary"]["approved"], 1)
            self.assertEqual(report["summary"]["attempted_prospects"], 0)

    def test_content_bound_decline_rejects_edited_fit_evidence(self) -> None:
        with TemporaryDirectory() as tmp:
            ledger = Path(tmp) / "ledger.csv"
            notes = Path(tmp) / "drafts.md"
            row = _row(
                status="drafted",
                contacted_on="",
                next_action_on="",
                approved_on="",
            )
            _write_ledger(ledger, [row])
            notes.write_text(
                f"## prospect-001\n\n"
                f"{_review_message('Reviewed private message')}\n",
                encoding="utf-8",
            )
            if os.name == "posix":
                notes.chmod(0o600)
            review_stdout = io.StringIO()
            with redirect_stdout(review_stdout):
                exit_code = main(
                    [
                        str(ledger),
                        "--as-of",
                        "2026-07-13",
                        "--review-next",
                        "--include-private-evidence",
                        "--include-private-draft",
                        str(notes),
                        "--format",
                        "json",
                    ]
                )
            self.assertEqual(exit_code, 0)
            review_digest = json.loads(review_stdout.getvalue())["review_digest"]

            changed_row = dict(row)
            changed_row["fit_evidence"] = EVIDENCE.replace(
                "https://evidence.example/agents",
                "https://evidence.example/edited-agents",
            )
            _write_ledger(ledger, [changed_row])
            before = ledger.read_bytes()
            stderr = io.StringIO()
            with redirect_stderr(stderr):
                exit_code = main(
                    [
                        str(ledger),
                        "--as-of",
                        "2026-07-13",
                        "--decline-next",
                        "prospect-001",
                        "--confirm-not-send",
                        "--review-digest",
                        review_digest,
                        "--reviewed-private-draft",
                        str(notes),
                    ]
                )

            self.assertEqual(exit_code, 2)
            self.assertEqual(ledger.read_bytes(), before)
            self.assertIn(
                "review content changed; run --review-next again before deciding",
                stderr.getvalue(),
            )
            self.assertNotIn("edited-agents", stderr.getvalue())
            self.assertEqual(
                list(Path(tmp).glob(".repo-scout-ledger.*.tmp")), []
            )

    def test_content_bound_decline_preserves_complete_next_review(self) -> None:
        with TemporaryDirectory() as tmp:
            ledger = Path(tmp) / "private ledger.csv"
            notes = Path(tmp) / "private drafts.md"
            _write_ledger(
                ledger,
                [
                    _row(
                        prospect_id="prospect-001",
                        status="drafted",
                        contacted_on="",
                        next_action_on="",
                        approved_on="",
                    ),
                    _row(
                        prospect_id="prospect-002",
                        status="drafted",
                        contacted_on="",
                        next_action_on="",
                        approved_on="",
                    ),
                ],
            )
            notes.write_text(
                f"## prospect-001\n\n"
                f"{_review_message('First private message')}\n\n"
                f"## prospect-002\n\n"
                f"{_review_message('Second private message')}\n",
                encoding="utf-8",
            )
            if os.name == "posix":
                notes.chmod(0o600)

            review_stdout = io.StringIO()
            with redirect_stdout(review_stdout):
                self.assertEqual(
                    main(
                        [
                            str(ledger),
                            "--as-of",
                            "2026-07-13",
                            "--review-next",
                            "--include-private-evidence",
                            "--include-private-draft",
                            str(notes),
                            "--format",
                            "json",
                        ]
                    ),
                    0,
                )
            first_review = json.loads(review_stdout.getvalue())

            decline_stdout = io.StringIO()
            with redirect_stdout(decline_stdout):
                self.assertEqual(
                    main(
                        [
                            str(ledger),
                            "--as-of",
                            "2026-07-13",
                            "--decline-next",
                            "prospect-001",
                            "--confirm-not-send",
                            "--review-digest",
                            first_review["review_digest"],
                            "--reviewed-private-draft",
                            str(notes),
                        ]
                    ),
                    0,
                )

            command_line = next(
                line
                for line in decline_stdout.getvalue().splitlines()
                if line.startswith("repo-scout-outreach ")
            )
            command = shlex.split(command_line)[1:]
            self.assertEqual(command.count(DATE_PLACEHOLDER), 1)
            self.assertIn("--include-private-evidence", command)
            self.assertEqual(
                command[command.index("--include-private-draft") + 1],
                str(notes),
            )
            self.assertIn("--write-review", command)
            self.assertEqual(
                command[command.index("--write-review") + 1],
                REVIEW_OUTPUT_PLACEHOLDER,
            )
            self.assertIn(
                f"'{REVIEW_OUTPUT_PLACEHOLDER}'",
                command_line,
            )
            self.assertEqual(command[-2:], ["--", str(ledger)])
            before_review = ledger.read_bytes()
            with redirect_stderr(io.StringIO()), self.assertRaises(
                SystemExit
            ) as ctx:
                main(command)
            self.assertEqual(ctx.exception.code, 2)
            self.assertEqual(ledger.read_bytes(), before_review)

            placeholder_stdout = io.StringIO()
            placeholder_stderr = io.StringIO()
            with redirect_stdout(placeholder_stdout), redirect_stderr(
                placeholder_stderr
            ):
                self.assertEqual(
                    main(
                        [
                            (
                                "2026-07-14"
                                if value == DATE_PLACEHOLDER
                                else value
                            )
                            for value in command
                        ]
                    ),
                    2,
                )
            self.assertEqual(placeholder_stdout.getvalue(), "")
            self.assertIn(
                f"replace {REVIEW_OUTPUT_PLACEHOLDER}",
                placeholder_stderr.getvalue(),
            )
            self.assertFalse(
                (Path.cwd() / REVIEW_OUTPUT_PLACEHOLDER).exists()
            )
            self.assertEqual(
                list(Path(tmp).glob(".repo-scout-review.*.tmp")),
                [],
            )
            self.assertEqual(ledger.read_bytes(), before_review)

            next_review_path = Path(tmp) / "next review.md"
            replaced_command = command_line.replace(
                DATE_PLACEHOLDER,
                "2026-07-14",
            ).replace(
                REVIEW_OUTPUT_PLACEHOLDER,
                str(next_review_path),
            )
            next_review_command = shlex.split(replaced_command)[1:]
            self.assertEqual(
                next_review_command[
                    next_review_command.index("--write-review") + 1
                ],
                str(next_review_path),
            )
            next_review_stdout = io.StringIO()
            with redirect_stdout(next_review_stdout):
                self.assertEqual(main(next_review_command), 0)
            self.assertEqual(
                next_review_stdout.getvalue(),
                "Private review written with owner-only permissions.\n",
            )
            next_review = next_review_path.read_text(encoding="utf-8")
            self.assertIn("Prospect alias: prospect-002", next_review)
            self.assertIn("Private evidence (do not commit or share):", next_review)
            self.assertIn("Second private message", next_review)
            self.assertNotIn("First private message", next_review)
            self.assertIn("Content-bound review receipt: sha256:", next_review)
            self.assertIn("--review-digest sha256:", next_review)
            if os.name == "posix":
                self.assertEqual(next_review_path.stat().st_mode & 0o777, 0o600)
            self.assertEqual(ledger.read_bytes(), before_review)

    def test_decline_next_closes_without_contact_and_advances_queue(self) -> None:
        with TemporaryDirectory() as tmp:
            ledger = Path(tmp) / "ledger.csv"
            original_rows = [
                _row(
                    prospect_id="prospect-002",
                    status="drafted",
                    contacted_on="",
                    next_action_on="",
                    approved_on="",
                ),
                _row(
                    prospect_id="prospect-001",
                    status="drafted",
                    contacted_on="",
                    next_action_on="",
                    approved_on="",
                ),
            ]
            _write_ledger(ledger, original_rows)
            stdout = io.StringIO()

            with redirect_stdout(stdout):
                exit_code = main(
                    [
                        str(ledger),
                        "--as-of",
                        "2026-07-13",
                        "--decline-next",
                        "prospect-001",
                        "--confirm-not-send",
                        "--format",
                        "json",
                    ]
                )

            self.assertEqual(exit_code, 0)
            self.assertEqual(ledger.stat().st_mode & 0o777, 0o600)
            with ledger.open(newline="", encoding="utf-8") as ledger_file:
                rows = list(csv.DictReader(ledger_file))
            original_by_id = {row["prospect_id"]: row for row in original_rows}
            rows_by_id = {row["prospect_id"]: row for row in rows}
            declined = rows_by_id["prospect-001"]
            changed_fields = {
                field
                for field in LEDGER_FIELDS
                if declined[field] != original_by_id["prospect-001"][field]
            }
            self.assertEqual(changed_fields, {"status"})
            self.assertEqual(declined["status"], "review-declined")
            self.assertEqual(
                rows_by_id["prospect-002"], original_by_id["prospect-002"]
            )

            report = load_outreach_report(ledger, as_of=date(2026, 7, 13))
            self.assertEqual(report["schema_version"], 12)
            self.assertEqual(report["summary"]["review_declined"], 1)
            self.assertEqual(report["summary"]["closed"], 1)
            self.assertEqual(report["summary"]["attempted_prospects"], 0)
            review = build_next_outreach_review(rows, as_of=date(2026, 7, 13))
            self.assertEqual(review["review"]["prospect_id"], "prospect-002")

            receipt = json.loads(stdout.getvalue())
            self.assertEqual(receipt["schema_version"], 4)
            self.assertTrue(receipt["private_output"])
            self.assertTrue(receipt["human_no_send_confirmed"])
            self.assertFalse(receipt["human_not_sent_confirmed"])
            self.assertEqual(
                receipt["queue"],
                {"drafts_remaining": 1, "approvals_remaining": 0},
            )
            self.assertEqual(receipt["decline"]["previous_status"], "drafted")
            self.assertEqual(receipt["decline"]["status"], "review-declined")
            self.assertNotIn("approved_on", json.dumps(receipt))
            self.assertNotIn("contacted_on", json.dumps(receipt))
            self.assertNotIn("evidence.example", json.dumps(receipt))
            self.assertIn("No outreach was approved or sent", receipt["action_note"])
            decline_text = format_outreach_decline(receipt, ledger=ledger)
            self.assertIn("Drafts remaining: 1", decline_text)
            self.assertIn("--review-next", decline_text)
            self.assertIn(
                f"--as-of {DATE_PLACEHOLDER} --review-next",
                decline_text,
            )
            self.assertNotIn("--write-review", decline_text)
            self.assertNotIn(
                "--as-of 2026-07-13 --review-next",
                decline_text,
            )
            next_review_command = shlex.split(
                next(
                    line
                    for line in decline_text.splitlines()
                    if line.startswith("repo-scout-outreach ")
                )
            )[1:]
            before_next_review = ledger.read_bytes()
            with redirect_stderr(io.StringIO()), self.assertRaises(
                SystemExit
            ) as ctx:
                main(next_review_command)
            self.assertEqual(ctx.exception.code, 2)
            self.assertEqual(ledger.read_bytes(), before_next_review)
            self.assertEqual(
                list(Path(tmp).glob(".repo-scout-ledger.*.tmp")), []
            )

    def test_decline_final_draft_ends_the_review_queue(self) -> None:
        with TemporaryDirectory() as tmp:
            ledger = Path(tmp) / "ledger.csv"
            _write_ledger(
                ledger,
                [
                    _row(
                        status="drafted",
                        contacted_on="",
                        next_action_on="",
                        approved_on="",
                    )
                ],
            )
            stdout = io.StringIO()

            with redirect_stdout(stdout):
                exit_code = main(
                    [
                        str(ledger),
                        "--as-of",
                        "2026-07-13",
                        "--decline-next",
                        "prospect-001",
                        "--confirm-not-send",
                    ]
                )

            self.assertEqual(exit_code, 0)
            text = stdout.getvalue()
            self.assertIn("Drafts remaining: 0", text)
            self.assertIn("Review queue complete", text)
            self.assertNotIn("--review-next", text)
            self.assertNotIn("--write-review", text)

    def test_decline_next_rejects_unsafe_transitions_without_mutation(self) -> None:
        with TemporaryDirectory() as tmp:
            ledger = Path(tmp) / "ledger.csv"
            rows = [
                _row(
                    prospect_id="prospect-002",
                    status="drafted",
                    contacted_on="",
                    next_action_on="",
                    approved_on="",
                ),
                _row(
                    prospect_id="prospect-001",
                    status="drafted",
                    contacted_on="",
                    next_action_on="",
                    approved_on="",
                ),
            ]
            cases = (
                (
                    ["--decline-next", "prospect-001"],
                    "requires --confirm-not-send",
                ),
                (
                    [
                        "--decline-next",
                        "prospect-002",
                        "--confirm-not-send",
                    ],
                    "next drafted prospect is prospect-001",
                ),
                (
                    [
                        "--decline-next",
                        "prospect-001",
                        "--confirm-not-send",
                        "--approved-on",
                        "2026-07-12",
                    ],
                    "--approved-on and --confirm-reviewed require --approve-next",
                ),
                (
                    ["--confirm-not-send"],
                    "--confirm-not-send and --confirm-not-sent require "
                    "--decline-next",
                ),
                (
                    [
                        "--decline-next",
                        "prospect-001",
                        "--confirm-not-send",
                        "--confirm-not-sent",
                    ],
                    "--confirm-not-sent applies only when canceling",
                ),
            )

            for arguments, message in cases:
                with self.subTest(message=message):
                    _write_ledger(ledger, rows)
                    before = ledger.read_bytes()
                    stderr = io.StringIO()
                    with redirect_stderr(stderr):
                        exit_code = main(
                            [
                                str(ledger),
                                "--as-of",
                                "2026-07-13",
                                *arguments,
                            ]
                        )

                    self.assertEqual(exit_code, 2)
                    self.assertIn(message, stderr.getvalue())
                    self.assertEqual(ledger.read_bytes(), before)
                    self.assertEqual(
                        list(Path(tmp).glob(".repo-scout-ledger.*.tmp")), []
                    )

    def test_approve_next_rejects_unsafe_transitions_without_mutation(self) -> None:
        with TemporaryDirectory() as tmp:
            ledger = Path(tmp) / "ledger.csv"
            rows = [
                _row(
                    prospect_id="prospect-002",
                    status="drafted",
                    contacted_on="",
                    next_action_on="",
                    approved_on="",
                ),
                _row(
                    prospect_id="prospect-001",
                    status="drafted",
                    contacted_on="",
                    next_action_on="",
                    approved_on="",
                ),
            ]
            cases = (
                (
                    [
                        "--approve-next",
                        "prospect-001",
                        "--confirm-reviewed",
                    ],
                    "requires --approved-on",
                ),
                (
                    [
                        "--approve-next",
                        "prospect-001",
                        "--approved-on",
                        "2026-07-12",
                    ],
                    "requires --confirm-reviewed",
                ),
                (
                    [
                        "--approve-next",
                        "prospect-002",
                        "--approved-on",
                        "2026-07-12",
                        "--confirm-reviewed",
                    ],
                    "next drafted prospect is prospect-001",
                ),
                (
                    [
                        "--approve-next",
                        "prospect-001",
                        "--approved-on",
                        "2026-07-14",
                        "--confirm-reviewed",
                    ],
                    "approved_on cannot be after as-of",
                ),
                (
                    [
                        "--approve-next",
                        "prospect-001",
                        "--approved-on",
                        "2026-07-12",
                        "--confirm-reviewed",
                        "--contacted-on",
                        "2026-07-12",
                    ],
                    "--contacted-on and --confirm-sent require --record-contact",
                ),
            )

            for arguments, message in cases:
                with self.subTest(message=message):
                    _write_ledger(ledger, rows)
                    before = ledger.read_bytes()
                    stderr = io.StringIO()
                    with redirect_stderr(stderr):
                        exit_code = main(
                            [
                                str(ledger),
                                "--as-of",
                                "2026-07-13",
                                *arguments,
                            ]
                        )

                    self.assertEqual(exit_code, 2)
                    self.assertIn(message, stderr.getvalue())
                    self.assertEqual(ledger.read_bytes(), before)
                    self.assertEqual(
                        list(Path(tmp).glob(".repo-scout-ledger.*.tmp")), []
                    )

    def test_approve_next_preserves_original_when_atomic_replace_fails(self) -> None:
        with TemporaryDirectory() as tmp:
            ledger = Path(tmp) / "ledger.csv"
            notes = Path(tmp) / "drafts.md"
            rows = [
                _row(
                    status="drafted",
                    contacted_on="",
                    next_action_on="",
                    approved_on="",
                )
            ]
            _write_ledger(ledger, rows)
            review_digest = _write_content_bound_review(
                notes,
                rows,
                as_of=date(2026, 7, 13),
            )
            before = ledger.read_bytes()
            stderr = io.StringIO()

            with patch(
                "repo_scout.outreach.os.replace",
                side_effect=OSError("synthetic replace failure"),
            ), redirect_stderr(stderr):
                exit_code = main(
                    [
                        str(ledger),
                        "--as-of",
                        "2026-07-13",
                        "--approve-next",
                        "prospect-001",
                        "--approved-on",
                        "2026-07-12",
                        "--confirm-reviewed",
                        "--review-digest",
                        review_digest,
                        "--reviewed-private-draft",
                        str(notes),
                    ]
                )

            self.assertEqual(exit_code, 2)
            self.assertIn("cannot update outreach ledger safely", stderr.getvalue())
            self.assertEqual(ledger.read_bytes(), before)
            self.assertEqual(
                list(Path(tmp).glob(".repo-scout-ledger.*.tmp")), []
            )

    def test_approve_next_reports_staging_cleanup_failure_privately(self) -> None:
        with TemporaryDirectory() as tmp:
            private_directory = Path(tmp) / "private"
            private_directory.mkdir(mode=0o700)
            ledger = private_directory / "prospect-001-private-ledger.csv"
            notes = private_directory / "drafts.md"
            rows = [
                _row(
                    status="drafted",
                    contacted_on="",
                    next_action_on="",
                    approved_on="",
                )
            ]
            _write_ledger(ledger, rows)
            review_digest = _write_content_bound_review(
                notes,
                rows,
                as_of=date(2026, 7, 13),
            )
            before = ledger.read_bytes()
            stdout = io.StringIO()
            stderr = io.StringIO()

            with (
                patch(
                    "repo_scout.outreach.os.replace",
                    side_effect=OSError("injected publish failure"),
                ),
                patch.object(
                    Path,
                    "unlink",
                    side_effect=OSError(
                        "cleanup failed for prospect-001-private-ledger.csv"
                    ),
                ),
                redirect_stdout(stdout),
                redirect_stderr(stderr),
            ):
                exit_code = main(
                    [
                        str(ledger),
                        "--as-of",
                        "2026-07-13",
                        "--approve-next",
                        "prospect-001",
                        "--approved-on",
                        "2026-07-12",
                        "--confirm-reviewed",
                        "--review-digest",
                        review_digest,
                        "--reviewed-private-draft",
                        str(notes),
                    ]
                )

            self.assertEqual(exit_code, 2)
            self.assertEqual(stdout.getvalue(), "")
            self.assertEqual(ledger.read_bytes(), before)
            staged = list(
                private_directory.glob(".repo-scout-ledger.*.tmp")
            )
            self.assertEqual(len(staged), 1)
            error = stderr.getvalue()
            self.assertIn("cannot update outreach ledger safely", error)
            self.assertIn("temporary cleanup incomplete", error)
            self.assertIn(staged[0].name, error)
            self.assertIn("remove that staging file", error)
            self.assertNotIn(ledger.name, error)
            self.assertNotIn(str(ledger), error)
            self.assertNotIn("prospect-001", error)
            if os.name == "posix":
                self.assertEqual(ledger.stat().st_mode & 0o777, 0o600)
                self.assertEqual(staged[0].stat().st_mode & 0o777, 0o600)
            staged[0].unlink()

    def test_lifecycle_lock_rejects_concurrent_approval_then_allows_retry(
        self,
    ) -> None:
        from repo_scout.outreach import _outreach_ledger_lock

        with TemporaryDirectory() as tmp:
            ledger = Path(tmp) / "private-ledger.csv"
            notes = Path(tmp) / "drafts.md"
            rows = [
                _row(
                    status="drafted",
                    contacted_on="",
                    next_action_on="",
                    approved_on="",
                )
            ]
            _write_ledger(ledger, rows)
            review_digest = _write_content_bound_review(
                notes,
                rows,
                as_of=date(2026, 7, 13),
            )
            before = ledger.read_bytes()
            environment = os.environ.copy()
            environment["PYTHONPATH"] = str(ROOT / "src")
            command = [
                sys.executable,
                "-m",
                "repo_scout.outreach",
                str(ledger),
                "--as-of",
                "2026-07-13",
                "--approve-next",
                "prospect-001",
                "--approved-on",
                "2026-07-12",
                "--confirm-reviewed",
                "--review-digest",
                review_digest,
                "--reviewed-private-draft",
                str(notes),
            ]

            with _outreach_ledger_lock(ledger):
                lock_files = [
                    path
                    for path in ledger.parent.iterdir()
                    if path != ledger and path.name.startswith(".") and path.is_file()
                ]
                self.assertEqual(len(lock_files), 1)
                lock_file = lock_files[0]
                if os.name == "posix":
                    self.assertEqual(lock_file.stat().st_mode & 0o777, 0o600)
                lock_bytes = lock_file.read_bytes()
                self.assertNotEqual(lock_bytes, before)
                self.assertNotIn(b"prospect-001", lock_bytes)
                self.assertNotIn(b"evidence.example", lock_bytes)

                started = time.monotonic()
                blocked = subprocess.run(
                    command,
                    cwd=ROOT,
                    env=environment,
                    capture_output=True,
                    text=True,
                    timeout=2,
                    check=False,
                )
                elapsed = time.monotonic() - started

                self.assertLess(elapsed, 1.5)
                self.assertEqual(blocked.returncode, 2)
                self.assertRegex(
                    f"{blocked.stdout}\n{blocked.stderr}".lower(),
                    r"retry|another (?:outreach )?action",
                )
                self.assertEqual(ledger.read_bytes(), before)

            completed = subprocess.run(
                command,
                cwd=ROOT,
                env=environment,
                capture_output=True,
                text=True,
                timeout=2,
                check=False,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            with ledger.open(newline="", encoding="utf-8") as ledger_file:
                approved = next(csv.DictReader(ledger_file))
            self.assertEqual(approved["status"], "approved")
            self.assertEqual(approved["approved_on"], "2026-07-12")

    def test_stale_lifecycle_writer_preserves_newer_attempt_evidence(self) -> None:
        import repo_scout.outreach as outreach_module

        with TemporaryDirectory() as tmp:
            ledger = Path(tmp) / "private-ledger.csv"
            _write_ledger(
                ledger,
                [
                    _row(
                        status="approved",
                        contacted_on="",
                        next_action_on="",
                    ),
                    _row(
                        prospect_id="prospect-002",
                        status="approved",
                        contacted_on="",
                        next_action_on="",
                    ),
                ],
            )
            original_write = outreach_module._write_outreach_rows
            interleaved = False

            def write_after_newer_actions(
                path: Path,
                rows: list[dict[str, str]],
                *,
                expected_revision: str | None = None,
            ) -> None:
                nonlocal interleaved
                if not interleaved:
                    interleaved = True
                    current_rows, current_revision = (
                        outreach_module._load_outreach_snapshot(path)
                    )
                    for row in current_rows:
                        row["status"] = "contacted"
                        row["contacted_on"] = "2026-07-13"
                        row["next_action_on"] = "2026-07-20"
                    original_write(
                        path,
                        current_rows,
                        expected_revision=current_revision,
                    )
                original_write(
                    path,
                    rows,
                    expected_revision=expected_revision,
                )

            with (
                patch.object(
                    outreach_module,
                    "_write_outreach_rows",
                    side_effect=write_after_newer_actions,
                ),
                self.assertRaisesRegex(
                    OutreachInputError,
                    "ledger changed during this action; retry",
                ),
            ):
                outreach_module.record_next_outreach_contact(
                    ledger,
                    prospect_id="prospect-001",
                    contacted_on=date(2026, 7, 13),
                    send_confirmed=True,
                    as_of=date(2026, 7, 13),
                )

            report = load_outreach_report(
                ledger,
                as_of=date(2026, 7, 13),
            )
            self.assertEqual(report["summary"]["attempted_prospects"], 2)
            with ledger.open(newline="", encoding="utf-8") as ledger_file:
                rows = list(csv.DictReader(ledger_file))
            self.assertEqual(
                [row["status"] for row in rows],
                ["contacted", "contacted"],
            )

    def test_lifecycle_write_rejects_permission_drift_after_preflight(
        self,
    ) -> None:
        if os.name != "posix":
            self.skipTest("owner-only outreach permissions are POSIX-specific")

        import repo_scout.outreach as outreach_module

        with TemporaryDirectory() as tmp:
            ledger = Path(tmp) / "private-ledger.csv"
            notes = Path(tmp) / "drafts.md"
            rows = [
                _row(
                    status="drafted",
                    contacted_on="",
                    next_action_on="",
                    approved_on="",
                )
            ]
            _write_ledger(ledger, rows)
            review_digest = _write_content_bound_review(
                notes,
                rows,
                as_of=date(2026, 7, 13),
            )
            before = ledger.read_bytes()
            original_write = outreach_module._write_outreach_rows

            def write_after_permission_drift(
                path: Path,
                rows: list[dict[str, str]],
                *,
                expected_revision: str | None = None,
                expected_private_draft_revision: tuple[Path, str] | None = None,
            ) -> None:
                path.chmod(0o640)
                original_write(
                    path,
                    rows,
                    expected_revision=expected_revision,
                    expected_private_draft_revision=(
                        expected_private_draft_revision
                    ),
                )

            with (
                patch.object(
                    outreach_module,
                    "_write_outreach_rows",
                    side_effect=write_after_permission_drift,
                ),
                self.assertRaisesRegex(
                    OutreachInputError,
                    "must use owner-only file permissions",
                ),
            ):
                outreach_module.approve_next_outreach_draft(
                    ledger,
                    prospect_id="prospect-001",
                    approved_on=date(2026, 7, 13),
                    review_confirmed=True,
                    review_digest=review_digest,
                    reviewed_private_drafts_path=notes,
                    as_of=date(2026, 7, 13),
                )

            self.assertEqual(ledger.read_bytes(), before)
            self.assertEqual(ledger.stat().st_mode & 0o777, 0o640)
            self.assertEqual(
                list(Path(tmp).glob(".repo-scout-ledger.*.tmp")),
                [],
            )

    def test_record_contact_tracks_human_send_and_exact_follow_up(self) -> None:
        with TemporaryDirectory() as tmp:
            ledger = Path(tmp) / "ledger.csv"
            original_rows = [
                _row(
                    prospect_id="prospect-002",
                    status="approved",
                    contacted_on="",
                    next_action_on="",
                    approved_on="2026-07-10",
                ),
                _row(
                    prospect_id="prospect-001",
                    status="approved",
                    contacted_on="",
                    next_action_on="",
                    approved_on="2026-07-11",
                ),
            ]
            _write_ledger(ledger, original_rows)
            ledger.chmod(0o600)
            stdout = io.StringIO()

            with redirect_stdout(stdout):
                exit_code = main(
                    [
                        str(ledger),
                        "--as-of",
                        "2026-07-13",
                        "--record-contact",
                        "prospect-001",
                        "--contacted-on",
                        "2026-07-12",
                        "--confirm-sent",
                        "--format",
                        "json",
                    ]
                )

            self.assertEqual(exit_code, 0)
            self.assertEqual(ledger.stat().st_mode & 0o777, 0o600)
            with ledger.open(newline="", encoding="utf-8") as ledger_file:
                rows = list(csv.DictReader(ledger_file))
            original_by_id = {row["prospect_id"]: row for row in original_rows}
            rows_by_id = {row["prospect_id"]: row for row in rows}
            contacted = rows_by_id["prospect-001"]
            changed_fields = {
                field
                for field in LEDGER_FIELDS
                if contacted[field] != original_by_id["prospect-001"][field]
            }
            self.assertEqual(
                changed_fields, {"status", "contacted_on", "next_action_on"}
            )
            self.assertEqual(contacted["status"], "contacted")
            self.assertEqual(contacted["contacted_on"], "2026-07-12")
            self.assertEqual(contacted["next_action_on"], "2026-07-19")
            self.assertEqual(contacted["approved_on"], "2026-07-11")
            self.assertEqual(
                rows_by_id["prospect-002"], original_by_id["prospect-002"]
            )
            report = load_outreach_report(ledger, as_of=date(2026, 7, 13))
            self.assertEqual(report["summary"]["approved"], 1)
            self.assertEqual(report["summary"]["contacted"], 1)
            self.assertEqual(report["summary"]["attempted_prospects"], 1)
            self.assertEqual(report["summary"]["due_followups"], 0)
            receipt = json.loads(stdout.getvalue())
            self.assertEqual(receipt["schema_version"], 2)
            self.assertTrue(receipt["private_output"])
            self.assertTrue(receipt["human_send_confirmed"])
            self.assertEqual(receipt["contact"]["status"], "contacted")
            self.assertEqual(receipt["contact"]["follow_up_due"], "2026-07-19")
            self.assertEqual(
                receipt["review_binding"],
                {
                    "approved_review_digest": None,
                    "content_revalidated": False,
                },
            )
            serialized = json.dumps(receipt)
            self.assertNotIn("approved_on", serialized)
            self.assertNotIn("contacted_on", serialized)
            self.assertNotIn("2026-07-12", serialized)
            self.assertNotIn("evidence.example", serialized)
            self.assertNotIn(LEGACY_UNBOUND_REVIEW, serialized)
            self.assertIn("Repo Scout sent nothing", receipt["action_note"])
            text = format_outreach_contact(receipt, ledger=ledger)
            self.assertIn(
                "Review binding: legacy approval without a durable review "
                "digest; current content not revalidated.",
                text,
            )
            self.assertIn("Manual follow-up due: 2026-07-19", text)
            self.assertIn("follow up manually", text)
            self.assertEqual(
                list(Path(tmp).glob(".repo-scout-ledger.*.tmp")), []
            )

    def test_approval_contact_handoff_rejects_draft_drift(self) -> None:
        with TemporaryDirectory() as tmp:
            ledger = Path(tmp) / "private-ledger.csv"
            notes = Path(tmp) / "drafts.md"
            rows = [
                _row(
                    status="drafted",
                    contacted_on="",
                    next_action_on="",
                    approved_on="",
                )
            ]
            _write_ledger(ledger, rows)
            review_digest = _write_content_bound_review(
                notes,
                rows,
                as_of=date(2026, 7, 13),
            )
            approval_stdout = io.StringIO()

            with redirect_stdout(approval_stdout):
                exit_code = main(
                    [
                        str(ledger),
                        "--as-of",
                        "2026-07-13",
                        "--approve-next",
                        "prospect-001",
                        "--approved-on",
                        "2026-07-13",
                        "--confirm-reviewed",
                        "--review-digest",
                        review_digest,
                        "--reviewed-private-draft",
                        str(notes),
                    ]
                )

            self.assertEqual(exit_code, 0)
            contact_commands = [
                shlex.split(line)
                for line in approval_stdout.getvalue().splitlines()
                if line.startswith("repo-scout-outreach ")
                and "--record-contact" in shlex.split(line)
            ]
            self.assertEqual(len(contact_commands), 1)
            contact_command = contact_commands[0]
            self.assertIn("--review-digest", contact_command)
            self.assertIn(review_digest, contact_command)
            self.assertIn("--reviewed-private-draft", contact_command)
            self.assertIn(str(notes), contact_command)
            contact_arguments = [
                (
                    "2026-07-14"
                    if value == DATE_PLACEHOLDER
                    else value
                )
                for value in contact_command[1:]
            ]
            separator_index = contact_arguments.index("--")
            contact_arguments[separator_index:separator_index] = [
                "--format",
                "json",
            ]

            edited_message = "Edited after approval"
            notes.write_text(
                f"## prospect-001\n\n"
                f"{_review_message(edited_message)}\n",
                encoding="utf-8",
            )
            before_contact = ledger.read_bytes()
            stderr = io.StringIO()
            with redirect_stderr(stderr):
                exit_code = main(contact_arguments)

            self.assertEqual(exit_code, 2)
            self.assertIn(
                "approved review content changed; restore the reviewed draft "
                "before recording contact",
                stderr.getvalue(),
            )
            self.assertNotIn(edited_message, stderr.getvalue())
            self.assertEqual(ledger.read_bytes(), before_contact)

            notes.write_text(
                f"## prospect-001\n\n"
                f"{_review_message('Reviewed private message for prospect-001')}"
                "\n",
                encoding="utf-8",
            )
            contact_stdout = io.StringIO()
            with redirect_stdout(contact_stdout):
                exit_code = main(contact_arguments)

            self.assertEqual(exit_code, 0)
            contact_receipt = json.loads(contact_stdout.getvalue())
            self.assertEqual(contact_receipt["schema_version"], 2)
            self.assertEqual(
                contact_receipt["review_binding"],
                {
                    "approved_review_digest": review_digest,
                    "content_revalidated": True,
                },
            )
            with ledger.open(newline="", encoding="utf-8") as ledger_file:
                contacted = next(csv.DictReader(ledger_file))
            self.assertEqual(contacted["status"], "contacted")
            self.assertEqual(contacted["contacted_on"], "2026-07-14")
            self.assertEqual(
                list(Path(tmp).glob(".repo-scout-ledger.*.tmp")), []
            )

    def test_legacy_contact_receipt_separates_revalidation_from_approval_identity(
        self,
    ) -> None:
        with TemporaryDirectory() as tmp:
            ledger = Path(tmp) / "legacy-ledger.csv"
            notes = Path(tmp) / "drafts.md"
            draft_rows = [
                _row(
                    status="drafted",
                    contacted_on="",
                    next_action_on="",
                    approved_on="",
                )
            ]
            review_digest = _write_content_bound_review(
                notes,
                draft_rows,
                as_of=date(2026, 7, 13),
            )
            approved_row = dict(draft_rows[0])
            approved_row["status"] = "approved"
            approved_row["approved_on"] = "2026-07-13"
            with ledger.open("w", newline="", encoding="utf-8") as ledger_file:
                writer = csv.DictWriter(
                    ledger_file,
                    fieldnames=OUTCOME_LEDGER_FIELDS,
                    lineterminator="\n",
                    extrasaction="ignore",
                )
                writer.writeheader()
                writer.writerow(approved_row)
            if os.name == "posix":
                ledger.chmod(0o600)

            stdout = io.StringIO()
            with redirect_stdout(stdout):
                self.assertEqual(
                    main(
                        [
                            str(ledger),
                            "--as-of",
                            "2026-07-14",
                            "--record-contact",
                            "prospect-001",
                            "--contacted-on",
                            "2026-07-14",
                            "--confirm-sent",
                            "--review-digest",
                            review_digest,
                            "--reviewed-private-draft",
                            str(notes),
                            "--format",
                            "json",
                        ]
                    ),
                    0,
                )

            receipt = json.loads(stdout.getvalue())
            self.assertEqual(
                receipt["review_binding"],
                {
                    "approved_review_digest": None,
                    "content_revalidated": True,
                },
            )
            self.assertNotIn(review_digest, json.dumps(receipt))
            self.assertNotIn(LEGACY_UNBOUND_REVIEW, json.dumps(receipt))
            self.assertTrue(receipt["private_output"])
            text = format_outreach_contact(receipt, ledger=ledger)
            self.assertIn(
                "legacy approval without a durable review digest; current "
                "content revalidated",
                text,
            )

    def test_report_recovers_contact_with_the_stored_review_digest(self) -> None:
        with TemporaryDirectory() as tmp:
            ledger = Path(tmp) / "private-ledger.csv"
            notes = Path(tmp) / "drafts.md"
            rows = [
                _row(
                    status="drafted",
                    contacted_on="",
                    next_action_on="",
                    approved_on="",
                )
            ]
            _write_ledger(ledger, rows)
            review_digest = _write_content_bound_review(
                notes,
                rows,
                as_of=date(2026, 7, 13),
            )
            with redirect_stdout(io.StringIO()):
                self.assertEqual(
                    main(
                        [
                            str(ledger),
                            "--as-of",
                            "2026-07-13",
                            "--approve-next",
                            "prospect-001",
                            "--approved-on",
                            "2026-07-13",
                            "--confirm-reviewed",
                            "--review-digest",
                            review_digest,
                            "--reviewed-private-draft",
                            str(notes),
                        ]
                    ),
                    0,
                )

            report = load_outreach_report(ledger, as_of=date(2026, 7, 14))
            recovery_text = format_outreach_report(report, ledger=ledger)
            recovery_line = next(
                line
                for line in recovery_text.splitlines()
                if line.startswith("repo-scout-outreach ")
            )
            recovery_command = shlex.split(recovery_line)[1:]
            self.assertIn("--review-digest", recovery_command)
            self.assertIn(review_digest, recovery_command)
            self.assertNotIn("--reviewed-private-draft", recovery_command)
            self.assertIn("Recovery binding", recovery_text)
            self.assertNotIn("Legacy recovery boundary", recovery_text)

            before_contact = ledger.read_bytes()
            digest_index = recovery_command.index("--review-digest")
            missing_digest_command = (
                recovery_command[:digest_index]
                + recovery_command[digest_index + 2 :]
            )
            missing_digest_command = [
                "2026-07-14" if value == DATE_PLACEHOLDER else value
                for value in missing_digest_command
            ]
            stderr = io.StringIO()
            with redirect_stderr(stderr):
                self.assertEqual(main(missing_digest_command), 2)
            self.assertIn(
                "requires --review-digest from the approval receipt or "
                "digest-bound recovery handoff",
                stderr.getvalue(),
            )
            self.assertEqual(ledger.read_bytes(), before_contact)

            wrong_digest_command = [
                (
                    "sha256:" + "0" * 64
                    if value == review_digest
                    else "2026-07-14"
                    if value == DATE_PLACEHOLDER
                    else value
                )
                for value in recovery_command
            ]
            stderr = io.StringIO()
            with redirect_stderr(stderr):
                self.assertEqual(main(wrong_digest_command), 2)
            self.assertIn(
                "review digest does not match the approved message",
                stderr.getvalue(),
            )
            self.assertEqual(ledger.read_bytes(), before_contact)

            recovered_command = [
                "2026-07-14" if value == DATE_PLACEHOLDER else value
                for value in recovery_command
            ]
            separator_index = recovered_command.index("--")
            recovered_command[separator_index:separator_index] = [
                "--format",
                "json",
            ]
            recovered_stdout = io.StringIO()
            with redirect_stdout(recovered_stdout):
                self.assertEqual(main(recovered_command), 0)
            recovered_receipt = json.loads(recovered_stdout.getvalue())
            self.assertEqual(recovered_receipt["schema_version"], 2)
            self.assertEqual(
                recovered_receipt["review_binding"],
                {
                    "approved_review_digest": review_digest,
                    "content_revalidated": False,
                },
            )
            with ledger.open(newline="", encoding="utf-8") as ledger_file:
                contacted = next(csv.DictReader(ledger_file))
            self.assertEqual(contacted["status"], "contacted")
            self.assertEqual(
                contacted["approved_review_digest"], review_digest
            )

    def test_content_bound_contact_rejects_commit_window_draft_edit(
        self,
    ) -> None:
        import repo_scout.outreach as outreach_module

        with TemporaryDirectory() as tmp:
            ledger = Path(tmp) / "private-ledger.csv"
            notes = Path(tmp) / "drafts.md"
            rows = [
                _row(
                    status="drafted",
                    contacted_on="",
                    next_action_on="",
                    approved_on="",
                )
            ]
            _write_ledger(ledger, rows)
            review_digest = _write_content_bound_review(
                notes,
                rows,
                as_of=date(2026, 7, 13),
            )
            outreach_module.approve_next_outreach_draft(
                ledger,
                prospect_id="prospect-001",
                approved_on=date(2026, 7, 13),
                review_confirmed=True,
                review_digest=review_digest,
                reviewed_private_drafts_path=notes,
                as_of=date(2026, 7, 13),
            )
            before_contact = ledger.read_bytes()
            original_write = outreach_module._write_outreach_rows
            edited_message = "Edited during contact recording"

            def write_after_private_edit(
                path: Path,
                rows: list[dict[str, str]],
                *,
                expected_revision: str | None = None,
                expected_private_draft_revision: (
                    tuple[Path, str] | None
                ) = None,
                private_draft_change_error: str = "",
            ) -> None:
                notes.write_text(
                    f"## prospect-001\n\n"
                    f"{_review_message(edited_message)}\n",
                    encoding="utf-8",
                )
                original_write(
                    path,
                    rows,
                    expected_revision=expected_revision,
                    expected_private_draft_revision=(
                        expected_private_draft_revision
                    ),
                    private_draft_change_error=private_draft_change_error,
                )

            with (
                patch.object(
                    outreach_module,
                    "_write_outreach_rows",
                    side_effect=write_after_private_edit,
                ),
                self.assertRaisesRegex(
                    OutreachInputError,
                    "approved review content changed; restore the reviewed "
                    "draft before recording contact",
                ) as raised,
            ):
                outreach_module.record_next_outreach_contact(
                    ledger,
                    prospect_id="prospect-001",
                    contacted_on=date(2026, 7, 14),
                    send_confirmed=True,
                    review_digest=review_digest,
                    reviewed_private_drafts_path=notes,
                    as_of=date(2026, 7, 14),
                )

            self.assertEqual(ledger.read_bytes(), before_contact)
            self.assertNotIn(edited_message, str(raised.exception))
            self.assertEqual(
                list(Path(tmp).glob(".repo-scout-ledger.*.tmp")), []
            )

    def test_text_handoffs_require_actual_human_event_dates(self) -> None:
        with TemporaryDirectory() as tmp:
            ledger = Path(tmp) / "private ledger.csv"
            notes = Path(tmp) / "private drafts.md"
            rows = [
                _row(
                    status="drafted",
                    contacted_on="",
                    next_action_on="",
                    approved_on="",
                )
            ]
            _write_ledger(ledger, rows)
            _write_content_bound_review(
                notes,
                rows,
                as_of=date(2026, 7, 1),
            )

            def run(arguments: list[str]) -> str:
                stdout = io.StringIO()
                with redirect_stdout(stdout):
                    self.assertEqual(main(arguments), 0)
                return stdout.getvalue()

            def command_for(output: str, action: str) -> list[str]:
                commands = [
                    line
                    for line in output.splitlines()
                    if line.startswith("repo-scout-outreach ")
                    and action in shlex.split(line)
                ]
                self.assertEqual(len(commands), 1)
                command = commands[0]
                parsed = shlex.split(command)
                self.assertEqual(parsed[0], "repo-scout-outreach")
                self.assertEqual(parsed[-2:], ["--", str(ledger)])
                return parsed[1:]

            def with_event_date(command: list[str], event_date: str) -> list[str]:
                self.assertIn(DATE_PLACEHOLDER, command)
                return [
                    event_date if value == DATE_PLACEHOLDER else value
                    for value in command
                ]

            review_output = run(
                [
                    str(ledger),
                    "--as-of",
                    "2026-07-01",
                    "--review-next",
                    "--include-private-evidence",
                    "--include-private-draft",
                    str(notes),
                ]
            )
            approval_command = command_for(review_output, "--approve-next")
            self.assertEqual(approval_command.count(DATE_PLACEHOLDER), 2)
            self.assertNotIn("2026-07-01", approval_command)
            before_approval = ledger.read_bytes()
            with redirect_stderr(io.StringIO()), self.assertRaises(
                SystemExit
            ) as ctx:
                main(approval_command)
            self.assertEqual(ctx.exception.code, 2)
            self.assertEqual(ledger.read_bytes(), before_approval)
            approval_output = run(
                with_event_date(approval_command, "2026-07-02")
            )
            self.assertIn("Drafts remaining: 0", approval_output)
            self.assertIn(
                "the bounded review queue is complete",
                approval_output,
            )
            self.assertNotIn("--review-next", approval_output)

            contact_command = command_for(
                approval_output, "--record-contact"
            )
            self.assertEqual(contact_command.count(DATE_PLACEHOLDER), 2)
            self.assertNotIn("2026-07-01", contact_command)
            before_contact = ledger.read_bytes()
            with redirect_stderr(io.StringIO()), self.assertRaises(
                SystemExit
            ) as ctx:
                main(contact_command)
            self.assertEqual(ctx.exception.code, 2)
            self.assertEqual(ledger.read_bytes(), before_contact)
            contact_output = run(
                with_event_date(contact_command, "2026-07-03")
            )

            contact_outcome_command = command_for(
                contact_output, "--record-outcome"
            )
            self.assertEqual(contact_outcome_command.count(DATE_PLACEHOLDER), 2)
            self.assertEqual(
                contact_outcome_command.count(OUTCOME_PLACEHOLDER), 1
            )
            follow_up_command = command_for(
                contact_output, "--record-follow-up"
            )
            self.assertEqual(follow_up_command.count(DATE_PLACEHOLDER), 2)
            self.assertNotIn("2026-07-10", follow_up_command)
            follow_up_output = run(
                with_event_date(follow_up_command, "2026-07-10")
            )

            outcome_command = command_for(
                follow_up_output, "--record-outcome"
            )
            self.assertEqual(outcome_command, contact_outcome_command)
            self.assertEqual(outcome_command.count(DATE_PLACEHOLDER), 2)
            self.assertEqual(outcome_command.count(OUTCOME_PLACEHOLDER), 1)
            self.assertIn("--confirm-outcome-observed", outcome_command)
            before_outcome = ledger.read_bytes()
            with redirect_stderr(io.StringIO()), self.assertRaises(
                SystemExit
            ) as ctx:
                main(outcome_command)
            self.assertEqual(ctx.exception.code, 2)
            self.assertEqual(ledger.read_bytes(), before_outcome)
            outcome_output = run(
                [
                    (
                        "2026-07-11"
                        if value == DATE_PLACEHOLDER
                        else "replied"
                        if value == OUTCOME_PLACEHOLDER
                        else value
                    )
                    for value in outcome_command
                ]
            )
            self.assertIn(
                "one of pilot-requested, price-objection, existing-solution, "
                "not-a-fit, do-not-contact",
                outcome_output,
            )
            self.assertNotIn("one of replied", outcome_output)
            refinement_command = command_for(
                outcome_output, "--record-outcome"
            )
            self.assertEqual(refinement_command.count(DATE_PLACEHOLDER), 2)
            self.assertEqual(refinement_command.count(OUTCOME_PLACEHOLDER), 1)
            before_refinement = ledger.read_bytes()
            with redirect_stderr(io.StringIO()), self.assertRaises(
                SystemExit
            ) as ctx:
                main(refinement_command)
            self.assertEqual(ctx.exception.code, 2)
            self.assertEqual(ledger.read_bytes(), before_refinement)
            refinement_output = run(
                [
                    (
                        "2026-07-12"
                        if value == DATE_PLACEHOLDER
                        else "pilot-requested"
                        if value == OUTCOME_PLACEHOLDER
                        else value
                    )
                    for value in refinement_command
                ]
            )
            self.assertNotIn("repo-scout-outreach ", refinement_output)
            self.assertIn(PUBLIC_PILOT_INTAKE_URL, refinement_output)
            report = load_outreach_report(ledger, as_of=date(2026, 7, 12))
            self.assertEqual(report["summary"]["pilot_requested"], 1)
            self.assertEqual(report["summary"]["attempted_prospects"], 1)
            with ledger.open(newline="", encoding="utf-8") as ledger_file:
                row = next(csv.DictReader(ledger_file))
            self.assertEqual(row["approved_on"], "2026-07-02")
            self.assertEqual(row["contacted_on"], "2026-07-03")
            self.assertEqual(row["followed_up_on"], "2026-07-10")
            self.assertEqual(row["status"], "pilot-requested")
            self.assertEqual(row["outcome_on"], "2026-07-11")

    def test_record_contact_rejects_unsafe_transitions_without_mutation(self) -> None:
        with TemporaryDirectory() as tmp:
            ledger = Path(tmp) / "ledger.csv"
            rows = [
                _row(
                    prospect_id="prospect-002",
                    status="approved",
                    contacted_on="",
                    next_action_on="",
                    approved_on="2026-07-10",
                ),
                _row(
                    prospect_id="prospect-001",
                    status="approved",
                    contacted_on="",
                    next_action_on="",
                    approved_on="2026-07-11",
                ),
            ]
            cases = (
                (
                    ["--record-contact", "prospect-001", "--confirm-sent"],
                    "requires --contacted-on",
                ),
                (
                    [
                        "--record-contact",
                        "prospect-001",
                        "--contacted-on",
                        "2026-07-12",
                    ],
                    "requires --confirm-sent",
                ),
                (
                    [
                        "--record-contact",
                        "prospect-002",
                        "--contacted-on",
                        "2026-07-12",
                        "--confirm-sent",
                    ],
                    "next approved prospect is prospect-001",
                ),
                (
                    [
                        "--record-contact",
                        "prospect-001",
                        "--contacted-on",
                        "2026-07-10",
                        "--confirm-sent",
                    ],
                    "approved_on must be no later than contacted_on",
                ),
                (
                    [
                        "--record-contact",
                        "prospect-001",
                        "--contacted-on",
                        "2026-07-14",
                        "--confirm-sent",
                    ],
                    "contacted_on cannot be after as-of",
                ),
                (
                    [
                        "--record-contact",
                        "prospect-001",
                        "--contacted-on",
                        "2026-07-12",
                        "--confirm-sent",
                        "--approved-on",
                        "2026-07-11",
                    ],
                    "--approved-on and --confirm-reviewed require --approve-next",
                ),
            )

            for arguments, message in cases:
                with self.subTest(message=message):
                    _write_ledger(ledger, rows)
                    before = ledger.read_bytes()
                    stderr = io.StringIO()
                    with redirect_stderr(stderr):
                        exit_code = main(
                            [
                                str(ledger),
                                "--as-of",
                                "2026-07-13",
                                *arguments,
                            ]
                        )

                    self.assertEqual(exit_code, 2)
                    self.assertIn(message, stderr.getvalue())
                    self.assertEqual(ledger.read_bytes(), before)
                    self.assertEqual(
                        list(Path(tmp).glob(".repo-scout-ledger.*.tmp")), []
                    )

    def test_record_contact_preserves_original_when_atomic_replace_fails(self) -> None:
        with TemporaryDirectory() as tmp:
            ledger = Path(tmp) / "ledger.csv"
            _write_ledger(
                ledger,
                [
                    _row(
                        status="approved",
                        contacted_on="",
                        next_action_on="",
                        approved_on="2026-07-11",
                    )
                ],
            )
            before = ledger.read_bytes()
            stderr = io.StringIO()

            with patch(
                "repo_scout.outreach.os.replace",
                side_effect=OSError("synthetic replace failure"),
            ), redirect_stderr(stderr):
                exit_code = main(
                    [
                        str(ledger),
                        "--as-of",
                        "2026-07-13",
                        "--record-contact",
                        "prospect-001",
                        "--contacted-on",
                        "2026-07-12",
                        "--confirm-sent",
                    ]
                )

            self.assertEqual(exit_code, 2)
            self.assertIn("cannot update outreach ledger safely", stderr.getvalue())
            self.assertEqual(ledger.read_bytes(), before)
            self.assertEqual(
                list(Path(tmp).glob(".repo-scout-ledger.*.tmp")), []
            )

    def test_record_outcome_clears_follow_up_and_preserves_history(self) -> None:
        with TemporaryDirectory() as tmp:
            ledger = Path(tmp) / "ledger.csv"
            original_rows = [
                _row(prospect_id="prospect-001"),
                _row(
                    prospect_id="prospect-002",
                    contacted_on="2026-07-02",
                    next_action_on="2026-07-09",
                    approved_on="2026-07-01",
                ),
            ]
            _write_ledger(ledger, original_rows)
            stdout = io.StringIO()

            with redirect_stdout(stdout):
                exit_code = main(
                    [
                        str(ledger),
                        "--as-of",
                        "2026-07-05",
                        "--record-outcome",
                        "prospect-002",
                        "--outcome",
                        "pilot-requested",
                        "--outcome-on",
                        "2026-07-05",
                        "--confirm-outcome-observed",
                        "--format",
                        "json",
                    ]
                )

            self.assertEqual(exit_code, 0)
            self.assertEqual(ledger.stat().st_mode & 0o777, 0o600)
            with ledger.open(newline="", encoding="utf-8") as ledger_file:
                rows = list(csv.DictReader(ledger_file))
            original_by_id = {row["prospect_id"]: row for row in original_rows}
            rows_by_id = {row["prospect_id"]: row for row in rows}
            outcome = rows_by_id["prospect-002"]
            changed_fields = {
                field
                for field in LEDGER_FIELDS
                if outcome[field] != original_by_id["prospect-002"][field]
            }
            self.assertEqual(
                changed_fields,
                {"status", "next_action_on", "outcome_on"},
            )
            self.assertEqual(outcome["status"], "pilot-requested")
            self.assertEqual(outcome["next_action_on"], "")
            self.assertEqual(outcome["outcome_on"], "2026-07-05")
            self.assertEqual(outcome["approved_on"], "2026-07-01")
            self.assertEqual(outcome["contacted_on"], "2026-07-02")
            self.assertEqual(
                rows_by_id["prospect-001"], original_by_id["prospect-001"]
            )
            report = load_outreach_report(ledger, as_of=date(2026, 7, 5))
            self.assertEqual(report["summary"]["pilot_requested"], 1)
            self.assertEqual(report["summary"]["attempted_prospects"], 2)
            self.assertEqual(report["summary"]["due_followups"], 0)
            receipt = json.loads(stdout.getvalue())
            self.assertEqual(receipt["schema_version"], 4)
            self.assertTrue(receipt["private_output"])
            self.assertTrue(receipt["human_outcome_confirmed"])
            self.assertEqual(receipt["outcome"]["status"], "pilot-requested")
            self.assertEqual(
                receipt["public_pilot_intake_url"],
                PUBLIC_PILOT_INTAKE_URL,
            )
            serialized = json.dumps(receipt)
            self.assertNotIn("approved_on", serialized)
            self.assertNotIn("contacted_on", serialized)
            self.assertNotIn("next_action_on", serialized)
            self.assertNotIn("2026-07-01", serialized)
            self.assertNotIn("2026-07-02", serialized)
            self.assertNotIn("evidence.example", serialized)
            text = format_outreach_outcome(receipt, ledger=ledger)
            self.assertIn("Follow-up cadence closed", text)
            self.assertIn("public pilot intake", text)
            self.assertIn("public demand or revenue evidence", text)
            self.assertIn(PUBLIC_PILOT_INTAKE_URL, text)
            self.assertNotIn("repo-scout-outreach ", text)
            self.assertEqual(
                list(Path(tmp).glob(".repo-scout-ledger.*.tmp")), []
            )

    def test_record_outcome_separates_observation_date_from_as_of(self) -> None:
        with TemporaryDirectory() as tmp:
            ledger = Path(tmp) / "ledger.csv"
            _write_ledger(ledger, [_row()])
            stdout = io.StringIO()

            with redirect_stdout(stdout):
                exit_code = main(
                    [
                        str(ledger),
                        "--as-of",
                        "2026-07-10",
                        "--record-outcome",
                        "prospect-001",
                        "--outcome",
                        "replied",
                        "--outcome-on",
                        "2026-07-05",
                        "--confirm-outcome-observed",
                        "--format",
                        "json",
                    ]
                )

            self.assertEqual(exit_code, 0)
            with ledger.open(newline="", encoding="utf-8") as ledger_file:
                updated = next(csv.DictReader(ledger_file))
            self.assertEqual(updated["outcome_on"], "2026-07-05")
            self.assertEqual(json.loads(stdout.getvalue())["as_of"], "2026-07-10")

    def test_record_outcome_accepts_followed_up_and_replied_sources(self) -> None:
        cases = (
            (
                _row(
                    status="followed-up",
                    followed_up_on="2026-07-08",
                    next_action_on="",
                ),
                "do-not-contact",
            ),
            (_row(status="replied", next_action_on=""), "not-a-fit"),
            (_row(), "price-objection"),
            (_row(), "existing-solution"),
        )
        for row, outcome in cases:
            with self.subTest(source=row["status"], outcome=outcome):
                with TemporaryDirectory() as tmp:
                    ledger = Path(tmp) / "ledger.csv"
                    _write_ledger(ledger, [row])
                    stdout = io.StringIO()

                    with redirect_stdout(stdout):
                        exit_code = main(
                            [
                                str(ledger),
                                "--as-of",
                                "2026-07-10",
                                "--record-outcome",
                                "prospect-001",
                                "--outcome",
                                outcome,
                                "--outcome-on",
                                "2026-07-10",
                                "--confirm-outcome-observed",
                                "--format",
                                "json",
                            ]
                        )

                    self.assertEqual(exit_code, 0)
                    receipt = json.loads(stdout.getvalue())
                    self.assertIsNone(receipt["public_pilot_intake_url"])
                    with ledger.open(newline="", encoding="utf-8") as ledger_file:
                        updated = next(csv.DictReader(ledger_file))
                    self.assertEqual(updated["status"], outcome)
                    self.assertEqual(updated["approved_on"], row["approved_on"])
                    self.assertEqual(updated["contacted_on"], row["contacted_on"])
                    self.assertEqual(updated["followed_up_on"], row["followed_up_on"])
                    self.assertEqual(updated["next_action_on"], "")
                    self.assertEqual(updated["outcome_on"], "2026-07-10")
                    if outcome == "price-objection":
                        text = format_outreach_outcome(receipt, ledger=ledger)
                        self.assertIn("willingness-to-pay evidence", text)
                        report = load_outreach_report(
                            ledger,
                            as_of=date(2026, 7, 10),
                        )
                        self.assertEqual(report["summary"]["price_objections"], 1)
                    if outcome == "existing-solution":
                        text = format_outreach_outcome(receipt, ledger=ledger)
                        self.assertIn("substitute evidence", text)
                        report = load_outreach_report(
                            ledger,
                            as_of=date(2026, 7, 10),
                        )
                        self.assertEqual(
                            report["summary"]["existing_solution_objections"],
                            1,
                        )

    def test_refined_outcome_cannot_precede_recorded_reply(self) -> None:
        with TemporaryDirectory() as tmp:
            ledger = Path(tmp) / "ledger.csv"
            _write_ledger(
                ledger,
                [
                    _row(
                        status="replied",
                        next_action_on="",
                        outcome_on="2026-07-11",
                    )
                ],
            )
            before = ledger.read_bytes()
            stderr = io.StringIO()

            with redirect_stderr(stderr):
                exit_code = main(
                    [
                        str(ledger),
                        "--as-of",
                        "2026-07-12",
                        "--record-outcome",
                        "prospect-001",
                        "--outcome",
                        "pilot-requested",
                        "--outcome-on",
                        "2026-07-10",
                        "--confirm-outcome-observed",
                    ]
                )

            self.assertEqual(exit_code, 2)
            self.assertIn(
                "cannot be before the recorded reply date 2026-07-11",
                stderr.getvalue(),
            )
            self.assertEqual(ledger.read_bytes(), before)

            with redirect_stdout(io.StringIO()):
                exit_code = main(
                    [
                        str(ledger),
                        "--as-of",
                        "2026-07-12",
                        "--record-outcome",
                        "prospect-001",
                        "--outcome",
                        "pilot-requested",
                        "--outcome-on",
                        "2026-07-12",
                        "--confirm-outcome-observed",
                    ]
                )

            self.assertEqual(exit_code, 0)
            with ledger.open(newline="", encoding="utf-8") as ledger_file:
                updated = next(csv.DictReader(ledger_file))
            self.assertEqual(updated["status"], "pilot-requested")
            self.assertEqual(updated["outcome_on"], "2026-07-11")

    def test_record_outcome_rejects_unsafe_transitions_without_mutation(self) -> None:
        with TemporaryDirectory() as tmp:
            ledger = Path(tmp) / "ledger.csv"
            cases = (
                (
                    _row(),
                    ["--record-outcome", "prospect-001"],
                    "requires --outcome STATUS",
                ),
                (
                    _row(),
                    [
                        "--record-outcome",
                        "prospect-001",
                        "--outcome",
                        "replied",
                        "--outcome-on",
                        "2026-07-10",
                    ],
                    "requires --confirm-outcome-observed",
                ),
                (
                    _row(),
                    [
                        "--record-outcome",
                        "prospect-001",
                        "--outcome",
                        "replied",
                        "--confirm-outcome-observed",
                    ],
                    "requires --outcome-on YYYY-MM-DD",
                ),
                (
                    _row(),
                    [
                        "--record-outcome",
                        "prospect-001",
                        "--outcome",
                        "replied",
                        "--outcome-on",
                        "2026-07-11",
                        "--confirm-outcome-observed",
                    ],
                    "outcome-on cannot be after as-of",
                ),
                (
                    _row(
                        status="approved",
                        contacted_on="",
                        next_action_on="",
                    ),
                    [
                        "--record-outcome",
                        "prospect-001",
                        "--outcome",
                        "replied",
                        "--outcome-on",
                        "2026-07-10",
                        "--confirm-outcome-observed",
                    ],
                    "status approved cannot record an outcome",
                ),
                (
                    _row(status="pilot-requested", next_action_on=""),
                    [
                        "--record-outcome",
                        "prospect-001",
                        "--outcome",
                        "not-a-fit",
                        "--outcome-on",
                        "2026-07-10",
                        "--confirm-outcome-observed",
                    ],
                    "status pilot-requested cannot record an outcome",
                ),
                (
                    _row(status="replied", next_action_on=""),
                    [
                        "--record-outcome",
                        "prospect-001",
                        "--outcome",
                        "replied",
                        "--outcome-on",
                        "2026-07-10",
                        "--confirm-outcome-observed",
                    ],
                    "already has outcome replied",
                ),
                (
                    _row(),
                    [
                        "--record-outcome",
                        "prospect-999",
                        "--outcome",
                        "replied",
                        "--outcome-on",
                        "2026-07-10",
                        "--confirm-outcome-observed",
                    ],
                    "prospect_id is not present",
                ),
                (
                    _row(),
                    [
                        "--outcome",
                        "replied",
                        "--outcome-on",
                        "2026-07-10",
                        "--confirm-outcome-observed",
                    ],
                    "require --record-outcome",
                ),
                (
                    _row(),
                    [
                        "--record-outcome",
                        "prospect-001",
                        "--outcome",
                        "replied",
                        "--outcome-on",
                        "2026-07-10",
                        "--confirm-outcome-observed",
                        "--contacted-on",
                        "2026-07-01",
                    ],
                    "--contacted-on and --confirm-sent require --record-contact",
                ),
            )

            for row, arguments, message in cases:
                with self.subTest(message=message):
                    _write_ledger(ledger, [row])
                    before = ledger.read_bytes()
                    stderr = io.StringIO()
                    with redirect_stderr(stderr):
                        exit_code = main(
                            [
                                str(ledger),
                                "--as-of",
                                "2026-07-10",
                                *arguments,
                            ]
                        )

                    self.assertEqual(exit_code, 2)
                    self.assertIn(message, stderr.getvalue())
                    self.assertEqual(ledger.read_bytes(), before)
                    self.assertEqual(
                        list(Path(tmp).glob(".repo-scout-ledger.*.tmp")), []
                    )

    def test_record_outcome_preserves_original_when_atomic_replace_fails(self) -> None:
        with TemporaryDirectory() as tmp:
            ledger = Path(tmp) / "ledger.csv"
            _write_ledger(ledger, [_row()])
            before = ledger.read_bytes()
            stderr = io.StringIO()

            with patch(
                "repo_scout.outreach.os.replace",
                side_effect=OSError("synthetic replace failure"),
            ), redirect_stderr(stderr):
                exit_code = main(
                    [
                        str(ledger),
                        "--as-of",
                        "2026-07-05",
                        "--record-outcome",
                        "prospect-001",
                        "--outcome",
                        "replied",
                        "--outcome-on",
                        "2026-07-05",
                        "--confirm-outcome-observed",
                    ]
                )

            self.assertEqual(exit_code, 2)
            self.assertIn("cannot update outreach ledger safely", stderr.getvalue())
            self.assertEqual(ledger.read_bytes(), before)
            self.assertEqual(
                list(Path(tmp).glob(".repo-scout-ledger.*.tmp")), []
            )

    def test_record_follow_up_closes_the_earliest_due_contact(self) -> None:
        with TemporaryDirectory() as tmp:
            ledger = Path(tmp) / "ledger.csv"
            original_rows = [
                _row(
                    prospect_id="prospect-001",
                    contacted_on="2026-07-05",
                    next_action_on="2026-07-12",
                    approved_on="2026-07-04",
                ),
                _row(
                    prospect_id="prospect-002",
                    contacted_on="2026-07-03",
                    next_action_on="2026-07-10",
                    approved_on="2026-07-02",
                ),
            ]
            _write_ledger(ledger, original_rows)
            ledger.chmod(0o600)
            stdout = io.StringIO()

            with redirect_stdout(stdout):
                exit_code = main(
                    [
                        str(ledger),
                        "--as-of",
                        "2026-07-11",
                        "--record-follow-up",
                        "prospect-002",
                        "--followed-up-on",
                        "2026-07-10",
                        "--confirm-follow-up-sent",
                        "--format",
                        "json",
                    ]
                )

            self.assertEqual(exit_code, 0)
            self.assertEqual(ledger.stat().st_mode & 0o777, 0o600)
            with ledger.open(newline="", encoding="utf-8") as ledger_file:
                rows = list(csv.DictReader(ledger_file))
            original_by_id = {row["prospect_id"]: row for row in original_rows}
            rows_by_id = {row["prospect_id"]: row for row in rows}
            followed_up = rows_by_id["prospect-002"]
            changed_fields = {
                field
                for field in LEDGER_FIELDS
                if followed_up[field] != original_by_id["prospect-002"][field]
            }
            self.assertEqual(
                changed_fields, {"status", "followed_up_on", "next_action_on"}
            )
            self.assertEqual(followed_up["status"], "followed-up")
            self.assertEqual(followed_up["followed_up_on"], "2026-07-10")
            self.assertEqual(followed_up["next_action_on"], "")
            self.assertEqual(followed_up["contacted_on"], "2026-07-03")
            self.assertEqual(followed_up["approved_on"], "2026-07-02")
            self.assertEqual(
                rows_by_id["prospect-001"], original_by_id["prospect-001"]
            )
            report = load_outreach_report(ledger, as_of=date(2026, 7, 11))
            self.assertEqual(report["summary"]["contacted"], 1)
            self.assertEqual(report["summary"]["followed_up"], 1)
            self.assertEqual(report["summary"]["attempted_prospects"], 2)
            self.assertEqual(report["summary"]["due_followups"], 0)
            receipt = json.loads(stdout.getvalue())
            self.assertTrue(receipt["private_output"])
            self.assertTrue(receipt["human_follow_up_confirmed"])
            self.assertEqual(receipt["follow_up"]["status"], "followed-up")
            serialized = json.dumps(receipt)
            self.assertNotIn("approved_on", serialized)
            self.assertNotIn("contacted_on", serialized)
            self.assertNotIn("followed_up_on", serialized)
            self.assertNotIn("2026-07-10", serialized)
            self.assertNotIn("evidence.example", serialized)
            self.assertIn("Repo Scout sent nothing", receipt["action_note"])
            text = format_outreach_follow_up(receipt, ledger=ledger)
            self.assertIn("stop immediately after an opt-out", text)
            self.assertEqual(
                list(Path(tmp).glob(".repo-scout-ledger.*.tmp")), []
            )

    def test_record_follow_up_rejects_noncanonical_date_before_selection(
        self,
    ) -> None:
        with TemporaryDirectory() as tmp:
            ledger = Path(tmp) / "ledger.csv"
            rows = [
                _row(
                    prospect_id="prospect-001",
                    contacted_on="2026-07-03",
                    next_action_on="20260710",
                    approved_on="2026-07-02",
                ),
                _row(
                    prospect_id="prospect-002",
                    contacted_on="2026-07-05",
                    next_action_on="2026-07-12",
                    approved_on="2026-07-04",
                ),
            ]
            _write_ledger(ledger, rows)
            before = ledger.read_bytes()
            stderr = io.StringIO()

            with redirect_stderr(stderr):
                exit_code = main(
                    [
                        str(ledger),
                        "--as-of",
                        "2026-07-12",
                        "--record-follow-up",
                        "prospect-001",
                        "--followed-up-on",
                        "2026-07-10",
                        "--confirm-follow-up-sent",
                    ]
                )

            self.assertEqual(exit_code, 2)
            self.assertIn(
                "row 2: next_action_on must be YYYY-MM-DD",
                stderr.getvalue(),
            )
            self.assertEqual(ledger.read_bytes(), before)

    def test_record_follow_up_rejects_unsafe_transitions_without_mutation(self) -> None:
        with TemporaryDirectory() as tmp:
            ledger = Path(tmp) / "ledger.csv"
            rows = [
                _row(
                    prospect_id="prospect-001",
                    contacted_on="2026-07-05",
                    next_action_on="2026-07-12",
                    approved_on="2026-07-04",
                ),
                _row(
                    prospect_id="prospect-002",
                    contacted_on="2026-07-03",
                    next_action_on="2026-07-10",
                    approved_on="2026-07-02",
                ),
            ]
            cases = (
                (
                    [
                        "--record-follow-up",
                        "prospect-002",
                        "--confirm-follow-up-sent",
                    ],
                    "requires --followed-up-on",
                ),
                (
                    [
                        "--record-follow-up",
                        "prospect-002",
                        "--followed-up-on",
                        "2026-07-10",
                    ],
                    "requires --confirm-follow-up-sent",
                ),
                (
                    [
                        "--record-follow-up",
                        "prospect-001",
                        "--followed-up-on",
                        "2026-07-12",
                        "--confirm-follow-up-sent",
                    ],
                    "next contacted prospect is prospect-002 due 2026-07-10",
                ),
                (
                    [
                        "--record-follow-up",
                        "prospect-002",
                        "--followed-up-on",
                        "2026-07-09",
                        "--confirm-follow-up-sent",
                    ],
                    "followed_up_on cannot be before 2026-07-10",
                ),
                (
                    [
                        "--record-follow-up",
                        "prospect-002",
                        "--followed-up-on",
                        "2026-07-12",
                        "--confirm-follow-up-sent",
                    ],
                    "followed_up_on cannot be after as-of",
                ),
                (
                    [
                        "--record-follow-up",
                        "prospect-002",
                        "--followed-up-on",
                        "2026-07-10",
                        "--confirm-follow-up-sent",
                        "--contacted-on",
                        "2026-07-03",
                    ],
                    "--contacted-on and --confirm-sent require --record-contact",
                ),
            )

            for arguments, message in cases:
                with self.subTest(message=message):
                    _write_ledger(ledger, rows)
                    before = ledger.read_bytes()
                    stderr = io.StringIO()
                    with redirect_stderr(stderr):
                        exit_code = main(
                            [
                                str(ledger),
                                "--as-of",
                                "2026-07-11",
                                *arguments,
                            ]
                        )

                    self.assertEqual(exit_code, 2)
                    self.assertIn(message, stderr.getvalue())
                    self.assertEqual(ledger.read_bytes(), before)
                    self.assertEqual(
                        list(Path(tmp).glob(".repo-scout-ledger.*.tmp")), []
                    )

    def test_guarded_outreach_lifecycle_actions_compose(self) -> None:
        with TemporaryDirectory() as tmp:
            ledger = Path(tmp) / "ledger.csv"
            notes = Path(tmp) / "drafts.md"
            rows = [
                _row(
                    status="drafted",
                    contacted_on="",
                    next_action_on="",
                    approved_on="",
                )
            ]
            _write_ledger(ledger, rows)
            review_digest = _write_content_bound_review(
                notes,
                rows,
                as_of=date(2026, 7, 10),
            )
            stdout = io.StringIO()

            with redirect_stdout(stdout):
                approval_exit = main(
                    [
                        str(ledger),
                        "--as-of",
                        "2026-07-10",
                        "--approve-next",
                        "prospect-001",
                        "--approved-on",
                        "2026-07-01",
                        "--confirm-reviewed",
                        "--review-digest",
                        review_digest,
                        "--reviewed-private-draft",
                        str(notes),
                    ]
                )
                contact_exit = main(
                    [
                        str(ledger),
                        "--as-of",
                        "2026-07-10",
                        "--record-contact",
                        "prospect-001",
                        "--contacted-on",
                        "2026-07-02",
                        "--confirm-sent",
                        "--review-digest",
                        review_digest,
                        "--reviewed-private-draft",
                        str(notes),
                    ]
                )
                follow_up_exit = main(
                    [
                        str(ledger),
                        "--as-of",
                        "2026-07-10",
                        "--record-follow-up",
                        "prospect-001",
                        "--followed-up-on",
                        "2026-07-09",
                        "--confirm-follow-up-sent",
                    ]
                )

            self.assertEqual(
                (approval_exit, contact_exit, follow_up_exit), (0, 0, 0)
            )
            before_retry = ledger.read_bytes()
            stderr = io.StringIO()
            with redirect_stderr(stderr):
                retry_exit = main(
                    [
                        str(ledger),
                        "--as-of",
                        "2026-07-10",
                        "--record-follow-up",
                        "prospect-001",
                        "--followed-up-on",
                        "2026-07-09",
                        "--confirm-follow-up-sent",
                    ]
                )
            self.assertEqual(retry_exit, 2)
            self.assertIn(
                "no contacted prospects await a follow-up record",
                stderr.getvalue(),
            )
            self.assertEqual(ledger.read_bytes(), before_retry)
            with ledger.open(newline="", encoding="utf-8") as ledger_file:
                row = next(csv.DictReader(ledger_file))
            self.assertEqual(row["status"], "followed-up")
            self.assertEqual(row["approved_on"], "2026-07-01")
            self.assertEqual(row["contacted_on"], "2026-07-02")
            self.assertEqual(row["followed_up_on"], "2026-07-09")
            self.assertEqual(row["next_action_on"], "")
            report = load_outreach_report(ledger, as_of=date(2026, 7, 10))
            self.assertEqual(report["summary"]["attempted_prospects"], 1)
            self.assertEqual(report["summary"]["followed_up"], 1)
            self.assertEqual(report["summary"]["due_followups"], 0)

    def test_requires_aliases_and_three_closed_fit_signals(self) -> None:
        invalid_rows = (
            (_row(prospect_id="lead@example.com"), "prospect-NNN"),
            (_row(fit_signals="team_5_50;multi_repo"), "at least three"),
            (
                _row(fit_signals="team_5_50;multi_repo;private_email"),
                "unknown fit signal",
            ),
            (
                _row(fit_signals="team_5_50;multi_repo;multi_repo"),
                "contains duplicates",
            ),
        )

        for rows, message in invalid_rows:
            with self.subTest(message=message), self.assertRaisesRegex(
                OutreachInputError, message
            ):
                build_outreach_report([rows], as_of=date(2026, 7, 11))

    def test_requires_one_secure_evidence_link_per_fit_signal(self) -> None:
        invalid_rows = (
            (_row(fit_evidence=""), "must map each signal"),
            (
                _row(
                    fit_evidence=(
                        "team_5_50=https://evidence.example/team;"
                        "multi_repo=https://evidence.example/repositories"
                    )
                ),
                "missing fit evidence for: agent_use",
            ),
            (
                _row(
                    fit_evidence=(
                        EVIDENCE
                        + ";local_privacy=https://evidence.example/privacy"
                    )
                ),
                "undeclared signal: local_privacy",
            ),
            (
                _row(
                    fit_evidence=(
                        EVIDENCE
                        + ";agent_use=https://evidence.example/duplicate"
                    )
                ),
                "duplicate signal: agent_use",
            ),
            (
                _row(
                    fit_evidence=EVIDENCE.replace(
                        "https://evidence.example/team",
                        "http://evidence.example/team",
                    )
                ),
                "must be a secure HTTPS URL",
            ),
            (
                _row(
                    fit_evidence=EVIDENCE.replace(
                        "https://evidence.example/team",
                        "https://user:secret@evidence.example/team",
                    )
                ),
                "without credentials",
            ),
        )

        for row, message in invalid_rows:
            with self.subTest(message=message), self.assertRaisesRegex(
                OutreachInputError, message
            ):
                build_outreach_report([row], as_of=date(2026, 7, 11))

    def test_enforces_one_seven_day_follow_up_and_terminal_stop(self) -> None:
        invalid_rows = (
            (_row(next_action_on="2026-07-07"), "one follow-up on 2026-07-08"),
            (
                _row(
                    status="followed-up",
                    followed_up_on="2026-07-07",
                    next_action_on="",
                ),
                "followed_up_on cannot be before 2026-07-08",
            ),
            (
                _row(status="followed-up", next_action_on=""),
                "requires followed_up_on",
            ),
            (
                _row(status="do-not-contact", next_action_on="2026-07-08"),
                "cannot have a next action",
            ),
            (
                _row(status="researched", channel="", next_action_on=""),
                "cannot have contact dates",
            ),
            (
                _row(
                    status="drafted",
                    contacted_on="",
                    channel="",
                    next_action_on="",
                    approved_on="",
                ),
                "require a permitted channel",
            ),
            (
                _row(
                    status="drafted",
                    contacted_on="2026-07-01",
                    next_action_on="",
                    approved_on="",
                ),
                "drafted prospects cannot have contact dates",
            ),
            (
                _row(
                    status="approved",
                    contacted_on="",
                    channel="",
                    next_action_on="",
                    approved_on="2026-07-01",
                ),
                "approved prospects require a permitted channel",
            ),
            (
                _row(
                    status="approved",
                    contacted_on="2026-07-01",
                    next_action_on="",
                    approved_on="2026-07-01",
                ),
                "approved prospects cannot have contact dates",
            ),
            (
                _row(
                    status="drafted",
                    contacted_on="",
                    next_action_on="",
                    approved_on="2026-07-01",
                ),
                "drafted prospects cannot have approved_on",
            ),
            (
                _row(
                    status="approved",
                    contacted_on="",
                    next_action_on="",
                    approved_on="",
                ),
                "approved_on is required after draft review",
            ),
            (
                _row(
                    status="approved",
                    contacted_on="",
                    next_action_on="",
                    approved_on="2026-07-12",
                ),
                "approved_on cannot be after as-of",
            ),
            (
                _row(approved_on="2026-07-02"),
                "approved_on must be no later than contacted_on",
            ),
        )

        for rows, message in invalid_rows:
            with self.subTest(message=message), self.assertRaisesRegex(
                OutreachInputError, message
            ):
                build_outreach_report([rows], as_of=date(2026, 7, 11))

    def test_validates_outcome_observation_dates(self) -> None:
        invalid_rows = (
            (
                _row(outcome_on="2026-07-02"),
                "status contacted cannot have outcome_on",
            ),
            (
                _row(
                    status="replied",
                    next_action_on="",
                    outcome_on="2026-07-12",
                ),
                "outcome_on cannot be after as-of",
            ),
            (
                _row(
                    status="replied",
                    next_action_on="",
                    outcome_on="2026-06-30",
                ),
                "outcome_on cannot be before contacted_on",
            ),
            (
                _row(
                    status="replied",
                    followed_up_on="2026-07-08",
                    next_action_on="",
                    outcome_on="2026-07-07",
                ),
                "outcome_on cannot be before followed_up_on",
            ),
        )

        for row, message in invalid_rows:
            with self.subTest(message=message), self.assertRaisesRegex(
                OutreachInputError, message
            ):
                build_outreach_report([row], as_of=date(2026, 7, 11))

        report = build_outreach_report(
            [
                _row(
                    status="replied",
                    next_action_on="",
                    outcome_on="2026-07-02",
                )
            ],
            as_of=date(2026, 7, 11),
        )
        self.assertEqual(report["summary"]["dated_outcomes"], 1)
        self.assertEqual(report["summary"]["undated_outcomes"], 0)
        self.assertIn("Dated outcomes: 1 / 1", format_outreach_report(report))

    def test_caps_the_experiment_at_ten_prospects(self) -> None:
        rows = [
            _row(
                prospect_id=f"prospect-{index:03d}",
                status="researched",
                contacted_on="",
                channel="",
                followed_up_on="",
                next_action_on="",
                approved_on="",
            )
            for index in range(1, 12)
        ]

        with self.assertRaisesRegex(OutreachInputError, "maximum is 10"):
            build_outreach_report(rows, as_of=date(2026, 7, 11))

    def test_cli_emits_json_and_rejects_bad_headers(self) -> None:
        with TemporaryDirectory() as tmp:
            ledger = Path(tmp) / "ledger.csv"
            ledger.write_text(
                ",".join(LEDGER_FIELDS)
                + "\n"
                + ",".join(_row()[field] for field in LEDGER_FIELDS)
                + "\n",
                encoding="utf-8",
            )
            if os.name == "posix":
                ledger.chmod(0o644)
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                exit_code = main(
                    [str(ledger), "--as-of", "2026-07-08", "--format", "json"]
                )

            self.assertEqual(exit_code, 0)
            report = json.loads(stdout.getvalue())
            self.assertEqual(report["due_followups"][0]["overdue_days"], 0)

            ledger.write_text("prospect_id,status\n", encoding="utf-8")
            stderr = io.StringIO()
            with redirect_stderr(stderr):
                exit_code = main([str(ledger), "--as-of", "2026-07-08"])

            self.assertEqual(exit_code, 2)
            self.assertIn("ledger header must be exactly", stderr.getvalue())

    def test_cli_fails_closed_when_counts_only_output_would_be_private(
        self,
    ) -> None:
        with TemporaryDirectory() as tmp:
            ledger = Path(tmp) / "ledger.csv"
            _write_ledger(ledger, [_row()])
            stdout = io.StringIO()
            stderr = io.StringIO()

            with redirect_stdout(stdout), redirect_stderr(stderr):
                exit_code = main(
                    [
                        str(ledger),
                        "--as-of",
                        "2026-07-08",
                        "--format",
                        "json",
                        "--require-counts-only",
                    ]
                )

            self.assertEqual(exit_code, PRIVATE_OUTPUT_EXIT_CODE)
            self.assertEqual(stdout.getvalue(), "")
            self.assertIn("refused output", stderr.getvalue())
            self.assertNotIn("prospect-001", stderr.getvalue())

    def test_cli_emits_a_verified_counts_only_report(self) -> None:
        with TemporaryDirectory() as tmp:
            ledger = Path(tmp) / "ledger.csv"
            _write_ledger(
                ledger,
                [
                    _row(
                        status="drafted",
                        contacted_on="",
                        next_action_on="",
                        approved_on="",
                    )
                ],
            )
            stdout = io.StringIO()

            with redirect_stdout(stdout):
                exit_code = main(
                    [
                        str(ledger),
                        "--as-of",
                        "2026-07-08",
                        "--format",
                        "json",
                        "--require-counts-only",
                    ]
                )

            self.assertEqual(exit_code, 0)
            self.assertFalse(json.loads(stdout.getvalue())["private_output"])

    def test_counts_only_guard_is_mutually_exclusive_with_private_actions(
        self,
    ) -> None:
        private_actions = (
            ("--review-next",),
            ("--approve-next", "prospect-001"),
            ("--decline-next", "prospect-001"),
            ("--record-contact", "prospect-001"),
            ("--record-follow-up", "prospect-001"),
            ("--record-outcome", "prospect-001"),
        )

        for private_action in private_actions:
            with self.subTest(private_action=private_action):
                with redirect_stderr(io.StringIO()), self.assertRaises(
                    SystemExit
                ) as raised:
                    main(
                        [
                            "ledger.csv",
                            "--require-counts-only",
                            *private_action,
                        ]
                    )

                self.assertEqual(raised.exception.code, 2)

    def test_cli_rejects_noncanonical_iso_date_spellings(self) -> None:
        for value in ("20260708", "2026-W28-3"):
            with self.subTest(value=value):
                stderr = io.StringIO()
                with redirect_stderr(stderr), self.assertRaises(
                    SystemExit
                ) as raised:
                    build_parser().parse_args(
                        ["ledger.csv", "--as-of", value]
                    )

                self.assertEqual(raised.exception.code, 2)
                self.assertIn("must be YYYY-MM-DD", stderr.getvalue())

    def test_api_wrappers_reject_falsey_non_date_as_of_before_path_access(
        self,
    ) -> None:
        import repo_scout.outreach as outreach_module

        missing_ledger = Path("missing-outreach-ledger.csv")
        event_date = date(2026, 7, 22)
        operations = (
            (
                "load report",
                lambda value: outreach_module.load_outreach_report(
                    missing_ledger, as_of=value
                ),
            ),
            (
                "load review",
                lambda value: outreach_module.load_next_outreach_review(
                    missing_ledger, as_of=value
                ),
            ),
            (
                "approve",
                lambda value: outreach_module.approve_next_outreach_draft(
                    missing_ledger,
                    prospect_id="prospect-001",
                    approved_on=event_date,
                    review_confirmed=True,
                    as_of=value,
                ),
            ),
            (
                "decline",
                lambda value: outreach_module.decline_next_outreach_draft(
                    missing_ledger,
                    prospect_id="prospect-001",
                    decline_confirmed=True,
                    as_of=value,
                ),
            ),
            (
                "record contact",
                lambda value: outreach_module.record_next_outreach_contact(
                    missing_ledger,
                    prospect_id="prospect-001",
                    contacted_on=event_date,
                    send_confirmed=True,
                    as_of=value,
                ),
            ),
            (
                "record follow-up",
                lambda value: outreach_module.record_next_outreach_follow_up(
                    missing_ledger,
                    prospect_id="prospect-001",
                    followed_up_on=event_date,
                    send_confirmed=True,
                    as_of=value,
                ),
            ),
            (
                "record outcome",
                lambda value: outreach_module.record_outreach_outcome(
                    missing_ledger,
                    prospect_id="prospect-001",
                    outcome="replied",
                    outcome_on=event_date,
                    outcome_confirmed=True,
                    as_of=value,
                ),
            ),
        )

        for operation, call in operations:
            for value in (False, 0, ""):
                with self.subTest(operation=operation, value=value):
                    with self.assertRaisesRegex(
                        OutreachInputError,
                        "as-of must be a date",
                    ):
                        call(value)

    def test_cli_defaults_to_the_current_utc_calendar_date(self) -> None:
        with TemporaryDirectory() as tmp:
            ledger = Path(tmp) / "ledger.csv"
            _write_ledger(
                ledger,
                [
                    _row(
                        status="drafted",
                        contacted_on="",
                        next_action_on="",
                        approved_on="",
                    )
                ],
            )
            stdout = io.StringIO()
            with patch(
                "repo_scout.outreach._utc_today",
                return_value=date(2026, 7, 18),
            ), redirect_stdout(stdout):
                library_report = load_outreach_report(ledger)
                exit_code = main([str(ledger), "--format", "json"])

        self.assertEqual(exit_code, 0)
        self.assertEqual(library_report["as_of"], "2026-07-18")
        self.assertEqual(json.loads(stdout.getvalue())["as_of"], "2026-07-18")

    def test_reads_legacy_nine_column_ledgers_without_inventing_dates(
        self,
    ) -> None:
        with TemporaryDirectory() as tmp:
            ledger = Path(tmp) / "legacy-ledger.csv"
            legacy_fields = LEGACY_LEDGER_FIELDS
            row = _row(status="replied", next_action_on="")
            ledger.write_text(
                ",".join(legacy_fields)
                + "\n"
                + ",".join(row[field] for field in legacy_fields)
                + "\n",
                encoding="utf-8",
            )

            report = load_outreach_report(ledger, as_of=date(2026, 7, 13))

            self.assertEqual(report["schema_version"], 12)
            self.assertEqual(report["summary"]["dated_outcomes"], 0)
            self.assertEqual(report["summary"]["undated_outcomes"], 1)

    def test_reads_prior_ten_column_ledgers_without_inventing_a_digest(
        self,
    ) -> None:
        with TemporaryDirectory() as tmp:
            ledger = Path(tmp) / "prior-ledger.csv"
            prior_fields = OUTCOME_LEDGER_FIELDS
            row = _row(
                status="approved",
                contacted_on="",
                next_action_on="",
                approved_on="2026-07-12",
            )
            ledger.write_text(
                ",".join(prior_fields)
                + "\n"
                + ",".join(row[field] for field in prior_fields)
                + "\n",
                encoding="utf-8",
            )
            if os.name == "posix":
                ledger.chmod(0o600)

            report = load_outreach_report(ledger, as_of=date(2026, 7, 13))
            self.assertEqual(
                report["next_approved"],
                {"prospect_id": "prospect-001", "review_digest": None},
            )
            before_contact = ledger.read_bytes()
            stderr = io.StringIO()
            with redirect_stderr(stderr):
                self.assertEqual(
                    main(
                        [
                            str(ledger),
                            "--as-of",
                            "2026-07-13",
                            "--record-contact",
                            "prospect-001",
                            "--contacted-on",
                            "2026-07-13",
                            "--confirm-sent",
                            "--review-digest",
                            "sha256:" + "0" * 64,
                        ]
                    ),
                    2,
                )
            self.assertIn(
                "digest-only contact recovery requires an approval with a "
                "stored review digest",
                stderr.getvalue(),
            )
            self.assertEqual(ledger.read_bytes(), before_contact)
            with redirect_stdout(io.StringIO()):
                self.assertEqual(
                    main(
                        [
                            str(ledger),
                            "--as-of",
                            "2026-07-13",
                            "--record-contact",
                            "prospect-001",
                            "--contacted-on",
                            "2026-07-13",
                            "--confirm-sent",
                        ]
                    ),
                    0,
                )
            with ledger.open(newline="", encoding="utf-8") as ledger_file:
                contacted = next(csv.DictReader(ledger_file))
            self.assertEqual(tuple(contacted), LEDGER_FIELDS)
            self.assertEqual(
                contacted["approved_review_digest"], LEGACY_UNBOUND_REVIEW
            )

    def test_current_ledger_rejects_a_blank_post_approval_digest(self) -> None:
        with TemporaryDirectory() as tmp:
            ledger = Path(tmp) / "current-ledger.csv"
            _write_ledger(
                ledger,
                [
                    _row(
                        status="approved",
                        contacted_on="",
                        next_action_on="",
                        approved_on="2026-07-12",
                        approved_review_digest="",
                    )
                ],
            )

            with self.assertRaisesRegex(
                OutreachInputError,
                "approved prospects require approved_review_digest",
            ):
                load_outreach_report(ledger, as_of=date(2026, 7, 13))

    def test_pre_upgrade_review_receipt_approves_a_ten_column_ledger(
        self,
    ) -> None:
        with TemporaryDirectory() as tmp:
            ledger = Path(tmp) / "prior-ledger.csv"
            notes = Path(tmp) / "drafts.md"
            rows = [
                _row(
                    status="drafted",
                    contacted_on="",
                    next_action_on="",
                    approved_on="",
                )
            ]
            review_digest = _write_content_bound_review(
                notes,
                rows,
                as_of=date(2026, 7, 13),
            )
            row = rows[0]
            ledger.write_text(
                ",".join(OUTCOME_LEDGER_FIELDS)
                + "\n"
                + ",".join(row[field] for field in OUTCOME_LEDGER_FIELDS)
                + "\n",
                encoding="utf-8",
            )
            if os.name == "posix":
                ledger.chmod(0o600)

            with redirect_stdout(io.StringIO()):
                self.assertEqual(
                    main(
                        [
                            str(ledger),
                            "--as-of",
                            "2026-07-13",
                            "--approve-next",
                            "prospect-001",
                            "--approved-on",
                            "2026-07-13",
                            "--confirm-reviewed",
                            "--review-digest",
                            review_digest,
                            "--reviewed-private-draft",
                            str(notes),
                        ]
                    ),
                    0,
                )
            with ledger.open(newline="", encoding="utf-8") as ledger_file:
                approved = next(csv.DictReader(ledger_file))
            self.assertEqual(tuple(approved), LEDGER_FIELDS)
            self.assertEqual(approved["approved_review_digest"], review_digest)

    def test_rejects_wrong_row_width_and_malformed_csv(self) -> None:
        with TemporaryDirectory() as tmp:
            ledger = Path(tmp) / "ledger.csv"
            header = ",".join(LEDGER_FIELDS)
            values = [_row()[field] for field in LEDGER_FIELDS]
            invalid_ledgers = (
                (
                    header + "\n" + ",".join(values + ["unexpected"]) + "\n",
                    "must have exactly 11 columns; found 12",
                ),
                (
                    header + "\n" + ",".join(values[:-1]) + "\n",
                    "must have exactly 11 columns; found 10",
                ),
                (
                    header + '\n"unterminated\n',
                    "cannot parse outreach ledger",
                ),
            )

            for contents, message in invalid_ledgers:
                with self.subTest(message=message):
                    ledger.write_text(contents, encoding="utf-8")
                    with self.assertRaisesRegex(OutreachInputError, message):
                        load_outreach_report(ledger, as_of=date(2026, 7, 13))


if __name__ == "__main__":
    unittest.main()
