from __future__ import annotations

from contextlib import redirect_stderr, redirect_stdout
from datetime import date
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from repo_scout.pilot_funnel import (
    FunnelInputError,
    build_funnel,
    format_funnel,
    main,
)


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests/fixtures/pilot_issues.json"


class PilotFunnelTests(unittest.TestCase):
    def test_build_funnel_tracks_revenue_stages_and_label_drift(self) -> None:
        payload = json.loads(FIXTURE.read_text(encoding="utf-8"))

        report = build_funnel(payload, as_of=date(2026, 7, 10))

        self.assertEqual(report["schema_version"], 2)
        self.assertEqual(report["summary"]["tracked_issues"], 8)
        self.assertEqual(report["summary"]["ignored_issues"], 1)
        self.assertEqual(report["summary"]["booked_pilots"], 4)
        self.assertEqual(report["summary"]["booked_revenue_usd"], 1196)
        self.assertEqual(report["summary"]["remaining_pilots"], 0)
        self.assertEqual(report["summary"]["target_attainment_percent"], 133.3)
        self.assertEqual(report["summary"]["annual_conversions"], 2)
        self.assertEqual(report["summary"]["lost_pilots"], 2)
        self.assertEqual(report["summary"]["stale_deals"], 2)
        self.assertEqual(
            report["by_stage"],
            {
                "lead": 1,
                "qualified": 1,
                "offered": 0,
                "paid": 1,
                "active": 1,
                "converted": 1,
                "lost": 1,
                "conflict": 1,
                "untracked": 1,
            },
        )
        self.assertEqual(
            [warning["kind"] for warning in report["warnings"]],
            [
                "missing_prior_stage",
                "conflicting_terminal_labels",
                "unknown_pilot_label",
                "missing_known_stage",
            ],
        )
        self.assertEqual(
            report["warnings"][0]["labels"],
            ["pilot-paid", "pilot-qualified"],
        )
        self.assertEqual(report["follow_up"]["as_of"], "2026-07-10")
        self.assertEqual(report["follow_up"]["stale_days"], 7)
        self.assertEqual(
            [deal["number"] for deal in report["follow_up"]["deals"]],
            [1, 2],
        )
        self.assertEqual(
            [deal["age_days"] for deal in report["follow_up"]["deals"]],
            [9, 7],
        )
        self.assertEqual(
            report["summary"]["stale_deals"],
            len(report["follow_up"]["deals"]),
        )
        self.assertEqual(
            report,
            build_funnel(list(reversed(payload)), as_of=date(2026, 7, 10)),
        )

    def test_main_emits_stable_json_with_custom_commercial_targets(self) -> None:
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            exit_code = main(
                [
                    str(FIXTURE),
                    "--format",
                    "json",
                    "--pilot-price",
                    "400",
                    "--target-pilots",
                    "5",
                    "--as-of",
                    "2026-07-10",
                    "--stale-days",
                    "10",
                ]
            )

        report = json.loads(stdout.getvalue())
        self.assertEqual(exit_code, 0)
        self.assertEqual(report["pricing"]["target_revenue_usd"], 2000)
        self.assertEqual(report["summary"]["booked_revenue_usd"], 1600)
        self.assertEqual(report["summary"]["remaining_pilots"], 1)
        self.assertEqual(report["summary"]["remaining_revenue_usd"], 400)
        self.assertEqual(report["summary"]["stale_deals"], 0)

    def test_main_reads_stdin_and_reports_empty_pipeline(self) -> None:
        stdout = io.StringIO()
        with patch(
            "repo_scout.pilot_funnel._utc_today",
            return_value=date(2026, 7, 10),
        ), redirect_stdout(stdout):
            exit_code = main([], stdin=io.StringIO("[]"))

        self.assertEqual(exit_code, 0)
        self.assertIn("Pilots: 0 booked / 3 target", stdout.getvalue())
        self.assertIn("Revenue: $0 booked / $897 target", stdout.getvalue())
        self.assertIn(
            "Follow-up: 0 stale open pre-payment deals (7+ days as of 2026-07-10)",
            stdout.getvalue(),
        )
        self.assertIn("Deals:\n  none", stdout.getvalue())
        self.assertIn("Stale deals:\n  none", stdout.getvalue())
        self.assertIn("Warnings:\n  none", stdout.getvalue())

    def test_main_rejects_invalid_json(self) -> None:
        stderr = io.StringIO()
        with redirect_stderr(stderr):
            exit_code = main([], stdin=io.StringIO("["))

        self.assertEqual(exit_code, 2)
        self.assertIn("invalid JSON", stderr.getvalue())

    def test_build_funnel_rejects_invalid_issue_shape(self) -> None:
        with self.assertRaisesRegex(FunnelInputError, "labels must be an array"):
            build_funnel([{"number": 1, "title": "Pilot", "labels": "pilot-lead"}])

    def test_build_funnel_rejects_duplicate_issue_numbers(self) -> None:
        issue = {
            "number": 1,
            "title": "Pilot",
            "state": "OPEN",
            "updatedAt": "2026-07-01T00:00:00Z",
            "labels": ["pilot-lead"],
        }
        with self.assertRaisesRegex(FunnelInputError, "duplicate issue number: 1"):
            build_funnel([issue, issue])

    def test_follow_up_handles_boundaries_offsets_and_data_quality(self) -> None:
        payload = [
            {
                "number": 10,
                "title": "Missing activity timestamp",
                "state": "OPEN",
                "labels": ["pilot-lead"],
            },
            {
                "number": 11,
                "title": "Closed offer without loss",
                "state": "CLOSED",
                "updatedAt": "2026-07-01T00:00:00Z",
                "labels": ["pilot-lead", "pilot-qualified", "pilot-offered"],
            },
            {
                "number": 12,
                "title": "Future activity timestamp",
                "state": "OPEN",
                "updatedAt": "2026-07-11T00:00:00Z",
                "labels": ["pilot-lead", "pilot-qualified"],
            },
            {
                "number": 13,
                "title": "UTC boundary is stale",
                "state": "OPEN",
                "updatedAt": "2026-07-04T00:30:00+02:00",
                "labels": ["pilot-lead", "pilot-qualified", "pilot-offered"],
            },
            {
                "number": 14,
                "title": "One day inside threshold",
                "state": "OPEN",
                "updatedAt": "2026-07-04T00:00:00Z",
                "labels": ["pilot-lead", "pilot-qualified", "pilot-offered"],
            },
            {
                "number": 15,
                "title": "Closed lost lead",
                "state": "CLOSED",
                "updatedAt": "2026-06-01T00:00:00Z",
                "labels": ["pilot-lead", "pilot-lost"],
            },
            {
                "number": 16,
                "title": "Paid deal does not need lead follow-up",
                "state": "OPEN",
                "updatedAt": "2026-06-01T00:00:00Z",
                "labels": [
                    "pilot-lead",
                    "pilot-qualified",
                    "pilot-offered",
                    "pilot-paid",
                ],
            },
        ]

        report = build_funnel(payload, as_of=date(2026, 7, 10), stale_days=7)

        self.assertEqual(report["summary"]["stale_deals"], 1)
        self.assertEqual(report["follow_up"]["deals"][0]["number"], 13)
        self.assertEqual(report["follow_up"]["deals"][0]["age_days"], 7)
        self.assertEqual(
            report["follow_up"]["deals"][0]["updated_at"],
            "2026-07-03T22:30:00Z",
        )
        self.assertFalse(
            next(deal for deal in report["deals"] if deal["number"] == 14)[
                "needs_follow_up"
            ]
        )
        self.assertEqual(
            [warning["kind"] for warning in report["warnings"]],
            [
                "missing_updated_at",
                "closed_without_lost",
                "future_updated_at",
            ],
        )
        text_report = format_funnel(report)
        self.assertIn(
            "Follow-up: 1 stale open pre-payment deal (7+ days as of 2026-07-10)",
            text_report,
        )
        self.assertIn(
            "#13 [offered, 7 days] UTC boundary is stale "
            "(updated 2026-07-03T22:30:00Z)",
            text_report,
        )

    def test_timestamp_and_state_validation_is_strict(self) -> None:
        invalid_timestamps = [
            "not-a-timestamp",
            "2026-02-30T00:00:00Z",
            "2026-07-03",
            42,
        ]
        for updated_at in invalid_timestamps:
            with self.subTest(updated_at=updated_at), self.assertRaisesRegex(
                FunnelInputError, "updatedAt"
            ):
                build_funnel(
                    [
                        {
                            "number": 1,
                            "title": "Pilot",
                            "state": "OPEN",
                            "updatedAt": updated_at,
                            "labels": ["pilot-lead"],
                        }
                    ]
                )

        for state in (None, "UNKNOWN", 42):
            with self.subTest(state=state), self.assertRaisesRegex(
                FunnelInputError, "state must be OPEN or CLOSED"
            ):
                build_funnel(
                    [
                        {
                            "number": 1,
                            "title": "Pilot",
                            "state": state,
                            "labels": ["pilot-lead"],
                        }
                    ]
                )

    def test_cli_rejects_invalid_follow_up_options_without_output(self) -> None:
        environment = os.environ.copy()
        environment["PYTHONPATH"] = str(ROOT / "src")
        for arguments in (
            ["--as-of", "not-a-date"],
            ["--stale-days", "0"],
        ):
            with self.subTest(arguments=arguments):
                completed = subprocess.run(
                    [
                        sys.executable,
                        "-m",
                        "repo_scout.pilot_funnel",
                        str(FIXTURE),
                        *arguments,
                    ],
                    cwd=ROOT.parent,
                    env=environment,
                    capture_output=True,
                    text=True,
                )
                self.assertEqual(completed.returncode, 2)
                self.assertEqual(completed.stdout, "")
                self.assertIn("error:", completed.stderr)

    def test_module_entrypoint_runs_from_another_directory(self) -> None:
        environment = os.environ.copy()
        environment["PYTHONPATH"] = str(ROOT / "src")
        completed = subprocess.run(
            [
                sys.executable,
                "-m",
                "repo_scout.pilot_funnel",
                str(FIXTURE),
                "--format",
                "json",
                "--as-of",
                "2026-07-10",
            ],
            cwd=ROOT.parent,
            env=environment,
            capture_output=True,
            text=True,
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(json.loads(completed.stdout)["summary"]["booked_pilots"], 4)


if __name__ == "__main__":
    unittest.main()
