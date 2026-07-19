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
    LEDGER_FIELDS,
    OUTCOME_PLACEHOLDER,
    OutreachInputError,
    PUBLIC_PILOT_INTAKE_URL,
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
)


ROOT = Path(__file__).resolve().parents[1]
SIGNALS = "team_5_50;multi_repo;agent_use"
EVIDENCE = (
    "team_5_50=https://evidence.example/team;"
    "multi_repo=https://evidence.example/repositories;"
    "agent_use=https://evidence.example/agents"
)


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
                status="do-not-contact",
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
        ]

        report = build_outreach_report(rows, as_of=date(2026, 7, 10))

        self.assertEqual(report["schema_version"], 7)
        self.assertTrue(report["experiment"]["human_approval_required"])
        self.assertEqual(report["summary"]["prospects"], 9)
        self.assertEqual(report["summary"]["attempted_prospects"], 5)
        self.assertEqual(report["summary"]["drafted"], 1)
        self.assertEqual(report["summary"]["review_declined"], 1)
        self.assertEqual(report["summary"]["approved"], 1)
        self.assertEqual(report["summary"]["closed"], 2)
        self.assertEqual(report["summary"]["fit_evidence_links"], 27)
        self.assertEqual(report["summary"]["dated_outcomes"], 0)
        self.assertEqual(report["summary"]["undated_outcomes"], 3)
        self.assertIn(
            "Drafts awaiting review: 1", format_outreach_report(report)
        )
        self.assertIn("Approved to send: 1", format_outreach_report(report))
        self.assertIn("Declined before contact: 1", format_outreach_report(report))
        self.assertIn("Qualification links: 27", format_outreach_report(report))
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
        self.assertEqual(report["due_followups"], [])

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
                prospect_id="prospect-003",
                status="approved",
                contacted_on="",
                next_action_on="",
                approved_on="2026-07-11",
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

        self.assertEqual(report["schema_version"], 4)
        self.assertTrue(report["human_review_required"])
        self.assertTrue(report["private_output"])
        self.assertFalse(report["private_evidence_included"])
        self.assertFalse(report["private_draft_included"])
        self.assertEqual(report["review"]["prospect_id"], "prospect-001")
        self.assertEqual(report["review"]["channel"], "published-business")
        self.assertEqual(report["review"]["fit_signals"], 3)
        self.assertEqual(report["review"]["fit_evidence_links"], 3)
        self.assertEqual(len(report["review"]["checks"]), 5)
        self.assertIn(
            "Confirm the message gives a clear opt-out and promises no further contact.",
            report["review"]["checks"],
        )
        self.assertNotIn("private_evidence", report["review"])
        self.assertNotIn("private_draft", report["review"])
        serialized = json.dumps(report)
        self.assertNotIn("evidence.example", serialized)
        self.assertNotIn("approved_on", serialized)
        self.assertNotIn("2026-07-11", serialized)
        text = format_next_outreach_review(report, ledger=Path("ledger.csv"))
        self.assertEqual(text.count("- [ ]"), 5)
        self.assertIn("Keep this alias-only checklist in the private workspace", text)
        self.assertIn("does not approve, modify, or send", text)
        self.assertIn("After human review, choose exactly one decision", text)
        self.assertIn("--approve-next prospect-001", text)
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
                status="approved",
                contacted_on="",
                next_action_on="",
                approved_on="2026-07-12",
            ),
        ]

        report = build_next_outreach_review(
            rows,
            as_of=date(2026, 7, 13),
            private_drafts={
                "prospect-001": "Selected message",
                "prospect-002": "Previously approved message",
            },
        )

        self.assertEqual(report["review"]["prospect_id"], "prospect-001")
        self.assertEqual(report["review"]["private_draft"], "Selected message")
        self.assertNotIn("Previously approved message", json.dumps(report))

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
                "## prospect-001\n\nSelected private message\n",
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
                report["review"]["private_draft"], "Selected private message"
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

    def test_approve_next_records_review_without_contact_or_private_data(self) -> None:
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
            ledger.chmod(0o600)
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
            self.assertEqual(changed_fields, {"status", "approved_on"})
            self.assertEqual(
                rows_by_id["prospect-002"], original_by_id["prospect-002"]
            )
            self.assertEqual(approved["status"], "approved")
            self.assertEqual(approved["approved_on"], "2026-07-12")
            self.assertEqual(approved["contacted_on"], "")
            self.assertEqual(approved["next_action_on"], "")
            report = load_outreach_report(ledger, as_of=date(2026, 7, 13))
            self.assertEqual(report["summary"]["approved"], 1)
            self.assertEqual(report["summary"]["drafted"], 1)
            self.assertEqual(report["summary"]["attempted_prospects"], 0)
            receipt = json.loads(stdout.getvalue())
            self.assertTrue(receipt["private_output"])
            self.assertTrue(receipt["human_review_confirmed"])
            self.assertEqual(receipt["approval"]["status"], "approved")
            self.assertNotIn("approved_on", json.dumps(receipt))
            self.assertNotIn("2026-07-12", json.dumps(receipt))
            self.assertNotIn("evidence.example", json.dumps(receipt))
            self.assertIn("No outreach was sent", receipt["action_note"])
            self.assertEqual(list(Path(tmp).glob(".ledger.csv.*.tmp")), [])

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
                "## prospect-001\n\nReviewed private message\n",
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

            notes.write_text(
                "## prospect-001\n\nEdited after human review\n",
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
                "review content changed; run --review-next again before deciding",
                stderr.getvalue(),
            )
            self.assertNotIn("Edited after human review", stderr.getvalue())
            self.assertEqual(list(Path(tmp).glob(".ledger.csv.*.tmp")), [])

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
                    "## prospect-001\n\nReviewed private message\n",
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
                        f"## prospect-001\n\n{edited_message}\n",
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
                self.assertEqual(list(Path(tmp).glob(".ledger.csv.*.tmp")), [])

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
                "## prospect-001\n\nReviewed private message\n",
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
                "## prospect-001\n\nReviewed private message\n",
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
            self.assertEqual(list(Path(tmp).glob(".ledger.csv.*.tmp")), [])

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
                "## prospect-001\n\nFirst private message\n\n"
                "## prospect-002\n\nSecond private message\n",
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
            self.assertEqual(command[-2:], ["--", str(ledger)])
            before_review = ledger.read_bytes()
            with redirect_stderr(io.StringIO()), self.assertRaises(
                SystemExit
            ) as ctx:
                main(command)
            self.assertEqual(ctx.exception.code, 2)
            self.assertEqual(ledger.read_bytes(), before_review)

            next_review_stdout = io.StringIO()
            with redirect_stdout(next_review_stdout):
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
                    0,
                )
            next_review = next_review_stdout.getvalue()
            self.assertIn("Prospect alias: prospect-002", next_review)
            self.assertIn("Private evidence (do not commit or share):", next_review)
            self.assertIn("Second private message", next_review)
            self.assertNotIn("First private message", next_review)
            self.assertIn("Content-bound review receipt: sha256:", next_review)
            self.assertIn("--review-digest sha256:", next_review)
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
            self.assertEqual(report["schema_version"], 7)
            self.assertEqual(report["summary"]["review_declined"], 1)
            self.assertEqual(report["summary"]["closed"], 1)
            self.assertEqual(report["summary"]["attempted_prospects"], 0)
            review = build_next_outreach_review(rows, as_of=date(2026, 7, 13))
            self.assertEqual(review["review"]["prospect_id"], "prospect-002")

            receipt = json.loads(stdout.getvalue())
            self.assertEqual(receipt["schema_version"], 2)
            self.assertTrue(receipt["private_output"])
            self.assertTrue(receipt["human_no_send_confirmed"])
            self.assertEqual(receipt["queue"], {"drafts_remaining": 1})
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
            self.assertEqual(list(Path(tmp).glob(".ledger.csv.*.tmp")), [])

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
                    "--confirm-not-send requires --decline-next",
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
                        list(Path(tmp).glob(".ledger.csv.*.tmp")), []
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
                        list(Path(tmp).glob(".ledger.csv.*.tmp")), []
                    )

    def test_approve_next_preserves_original_when_atomic_replace_fails(self) -> None:
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
                    ]
                )

            self.assertEqual(exit_code, 2)
            self.assertIn("cannot update outreach ledger safely", stderr.getvalue())
            self.assertEqual(ledger.read_bytes(), before)
            self.assertEqual(list(Path(tmp).glob(".ledger.csv.*.tmp")), [])

    def test_lifecycle_lock_rejects_concurrent_approval_then_allows_retry(
        self,
    ) -> None:
        from repo_scout.outreach import _outreach_ledger_lock

        with TemporaryDirectory() as tmp:
            ledger = Path(tmp) / "private-ledger.csv"
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
                    as_of=date(2026, 7, 13),
                )

            self.assertEqual(ledger.read_bytes(), before)
            self.assertEqual(ledger.stat().st_mode & 0o777, 0o640)
            self.assertEqual(
                list(Path(tmp).glob(".private-ledger.csv.*.tmp")),
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
            self.assertTrue(receipt["private_output"])
            self.assertTrue(receipt["human_send_confirmed"])
            self.assertEqual(receipt["contact"]["status"], "contacted")
            self.assertEqual(receipt["contact"]["follow_up_due"], "2026-07-19")
            serialized = json.dumps(receipt)
            self.assertNotIn("approved_on", serialized)
            self.assertNotIn("contacted_on", serialized)
            self.assertNotIn("2026-07-12", serialized)
            self.assertNotIn("evidence.example", serialized)
            self.assertIn("Repo Scout sent nothing", receipt["action_note"])
            text = format_outreach_contact(receipt, ledger=ledger)
            self.assertIn("Manual follow-up due: 2026-07-19", text)
            self.assertIn("follow up manually", text)
            self.assertEqual(list(Path(tmp).glob(".ledger.csv.*.tmp")), [])

    def test_text_handoffs_require_actual_human_event_dates(self) -> None:
        with TemporaryDirectory() as tmp:
            ledger = Path(tmp) / "private ledger.csv"
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
                [str(ledger), "--as-of", "2026-07-01", "--review-next"]
            )
            approval_command = command_for(review_output, "--approve-next")
            self.assertNotIn(DATE_PLACEHOLDER, approval_command)
            approval_output = run(approval_command)

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
                "one of pilot-requested, not-a-fit, do-not-contact",
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
            self.assertEqual(row["approved_on"], "2026-07-01")
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
                        list(Path(tmp).glob(".ledger.csv.*.tmp")), []
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
            self.assertEqual(list(Path(tmp).glob(".ledger.csv.*.tmp")), [])

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
            self.assertEqual(receipt["schema_version"], 2)
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
            self.assertEqual(list(Path(tmp).glob(".ledger.csv.*.tmp")), [])

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
                        list(Path(tmp).glob(".ledger.csv.*.tmp")), []
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
            self.assertEqual(list(Path(tmp).glob(".ledger.csv.*.tmp")), [])

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
            self.assertEqual(list(Path(tmp).glob(".ledger.csv.*.tmp")), [])

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
                        list(Path(tmp).glob(".ledger.csv.*.tmp")), []
                    )

    def test_guarded_outreach_lifecycle_actions_compose(self) -> None:
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
            legacy_fields = LEDGER_FIELDS[:-1]
            row = _row(status="replied", next_action_on="")
            ledger.write_text(
                ",".join(legacy_fields)
                + "\n"
                + ",".join(row[field] for field in legacy_fields)
                + "\n",
                encoding="utf-8",
            )

            report = load_outreach_report(ledger, as_of=date(2026, 7, 13))

            self.assertEqual(report["schema_version"], 7)
            self.assertEqual(report["summary"]["dated_outcomes"], 0)
            self.assertEqual(report["summary"]["undated_outcomes"], 1)

    def test_rejects_wrong_row_width_and_malformed_csv(self) -> None:
        with TemporaryDirectory() as tmp:
            ledger = Path(tmp) / "ledger.csv"
            header = ",".join(LEDGER_FIELDS)
            values = [_row()[field] for field in LEDGER_FIELDS]
            invalid_ledgers = (
                (
                    header + "\n" + ",".join(values + ["unexpected"]) + "\n",
                    "must have exactly 10 columns; found 11",
                ),
                (
                    header + "\n" + ",".join(values[:-1]) + "\n",
                    "must have exactly 10 columns; found 9",
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
