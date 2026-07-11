from __future__ import annotations

from contextlib import redirect_stderr, redirect_stdout
from datetime import date
import io
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import tomllib
import unittest


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from repo_scout.outreach import (  # noqa: E402
    LEDGER_FIELDS,
    OutreachInputError,
    build_outreach_report,
    load_outreach_report,
    main,
)


ROOT = Path(__file__).resolve().parents[1]
SIGNALS = "team_5_50;multi_repo;agent_use"


def _row(**overrides: str) -> dict[str, str]:
    row = {
        "prospect_id": "prospect-001",
        "fit_signals": SIGNALS,
        "contacted_on": "2026-07-01",
        "channel": "published-business",
        "status": "contacted",
        "followed_up_on": "",
        "next_action_on": "2026-07-08",
    }
    row.update(overrides)
    return row


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
            ),
        ]

        report = build_outreach_report(rows, as_of=date(2026, 7, 10))

        self.assertEqual(report["schema_version"], 1)
        self.assertEqual(report["summary"]["prospects"], 6)
        self.assertEqual(report["summary"]["attempted_prospects"], 5)
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

    def test_template_is_a_valid_empty_private_ledger(self) -> None:
        report = load_outreach_report(
            ROOT / "examples" / "outreach-ledger.csv",
            as_of=date(2026, 7, 11),
        )

        self.assertEqual(report["summary"]["prospects"], 0)
        self.assertEqual(report["due_followups"], [])

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


if __name__ == "__main__":
    unittest.main()
