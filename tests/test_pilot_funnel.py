from __future__ import annotations

from contextlib import redirect_stderr, redirect_stdout
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from repo_scout.pilot_funnel import FunnelInputError, build_funnel, main


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests/fixtures/pilot_issues.json"


class PilotFunnelTests(unittest.TestCase):
    def test_build_funnel_tracks_revenue_stages_and_label_drift(self) -> None:
        payload = json.loads(FIXTURE.read_text(encoding="utf-8"))

        report = build_funnel(payload)

        self.assertEqual(report["schema_version"], 1)
        self.assertEqual(report["summary"]["tracked_issues"], 8)
        self.assertEqual(report["summary"]["ignored_issues"], 1)
        self.assertEqual(report["summary"]["booked_pilots"], 4)
        self.assertEqual(report["summary"]["booked_revenue_usd"], 1196)
        self.assertEqual(report["summary"]["remaining_pilots"], 0)
        self.assertEqual(report["summary"]["target_attainment_percent"], 133.3)
        self.assertEqual(report["summary"]["annual_conversions"], 2)
        self.assertEqual(report["summary"]["lost_pilots"], 2)
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
        self.assertEqual(report, build_funnel(list(reversed(payload))))

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
                ]
            )

        report = json.loads(stdout.getvalue())
        self.assertEqual(exit_code, 0)
        self.assertEqual(report["pricing"]["target_revenue_usd"], 2000)
        self.assertEqual(report["summary"]["booked_revenue_usd"], 1600)
        self.assertEqual(report["summary"]["remaining_pilots"], 1)
        self.assertEqual(report["summary"]["remaining_revenue_usd"], 400)

    def test_main_reads_stdin_and_reports_empty_pipeline(self) -> None:
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            exit_code = main([], stdin=io.StringIO("[]"))

        self.assertEqual(exit_code, 0)
        self.assertIn("Pilots: 0 booked / 3 target", stdout.getvalue())
        self.assertIn("Revenue: $0 booked / $897 target", stdout.getvalue())
        self.assertIn("Deals:\n  none", stdout.getvalue())
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
        issue = {"number": 1, "title": "Pilot", "labels": ["pilot-lead"]}
        with self.assertRaisesRegex(FunnelInputError, "duplicate issue number: 1"):
            build_funnel([issue, issue])

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
