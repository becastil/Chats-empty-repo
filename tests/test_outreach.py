from __future__ import annotations

from contextlib import redirect_stderr, redirect_stdout
import csv
from datetime import date
import io
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import tomllib
import unittest
from unittest.mock import patch


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from repo_scout.outreach import (  # noqa: E402
    LEDGER_FIELDS,
    OutreachInputError,
    build_next_outreach_review,
    build_outreach_report,
    format_next_outreach_review,
    format_outreach_contact,
    format_outreach_follow_up,
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
        ]

        report = build_outreach_report(rows, as_of=date(2026, 7, 10))

        self.assertEqual(report["schema_version"], 5)
        self.assertTrue(report["experiment"]["human_approval_required"])
        self.assertEqual(report["summary"]["prospects"], 8)
        self.assertEqual(report["summary"]["attempted_prospects"], 5)
        self.assertEqual(report["summary"]["drafted"], 1)
        self.assertEqual(report["summary"]["approved"], 1)
        self.assertEqual(report["summary"]["fit_evidence_links"], 24)
        self.assertIn(
            "Drafts awaiting review: 1", format_outreach_report(report)
        )
        self.assertIn("Approved to send: 1", format_outreach_report(report))
        self.assertIn("Qualification links: 24", format_outreach_report(report))
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

        self.assertEqual(report["schema_version"], 2)
        self.assertTrue(report["human_review_required"])
        self.assertTrue(report["private_output"])
        self.assertFalse(report["private_evidence_included"])
        self.assertEqual(report["review"]["prospect_id"], "prospect-001")
        self.assertEqual(report["review"]["channel"], "published-business")
        self.assertEqual(report["review"]["fit_signals"], 3)
        self.assertEqual(report["review"]["fit_evidence_links"], 3)
        self.assertEqual(len(report["review"]["checks"]), 5)
        self.assertNotIn("private_evidence", report["review"])
        serialized = json.dumps(report)
        self.assertNotIn("evidence.example", serialized)
        self.assertNotIn("approved_on", serialized)
        self.assertNotIn("2026-07-11", serialized)
        text = format_next_outreach_review(report)
        self.assertEqual(text.count("- [ ]"), 5)
        self.assertIn("Keep this alias-only checklist in the private workspace", text)
        self.assertIn("does not approve, modify, or send", text)

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
        text = format_next_outreach_review(report)
        self.assertIn("Private evidence (do not commit or share):", text)
        self.assertIn(
            "- agent_use: https://evidence.example/agents",
            text,
        )
        self.assertIn("evidence-bearing review", text)
        self.assertIn("does not approve, modify, or send", text)

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

    def test_private_evidence_flag_requires_review_next(self) -> None:
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

            with redirect_stderr(stderr):
                exit_code = main(
                    [
                        str(ledger),
                        "--as-of",
                        "2026-07-13",
                        "--include-private-evidence",
                    ]
                )

            self.assertEqual(exit_code, 2)
            self.assertIn(
                "--include-private-evidence requires --review-next",
                stderr.getvalue(),
            )

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
        self.assertIn(
            "No drafts are awaiting human review.",
            format_next_outreach_review(report),
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
            text = format_outreach_contact(receipt)
            self.assertIn("Manual follow-up due: 2026-07-19", text)
            self.assertIn("follow up manually", text)
            self.assertEqual(list(Path(tmp).glob(".ledger.csv.*.tmp")), [])

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
            text = format_outreach_follow_up(receipt)
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

    def test_rejects_wrong_row_width_and_malformed_csv(self) -> None:
        with TemporaryDirectory() as tmp:
            ledger = Path(tmp) / "ledger.csv"
            header = ",".join(LEDGER_FIELDS)
            values = [_row()[field] for field in LEDGER_FIELDS]
            invalid_ledgers = (
                (
                    header + "\n" + ",".join(values + ["unexpected"]) + "\n",
                    "must have exactly 9 columns; found 10",
                ),
                (
                    header + "\n" + ",".join(values[:-1]) + "\n",
                    "must have exactly 9 columns; found 8",
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
