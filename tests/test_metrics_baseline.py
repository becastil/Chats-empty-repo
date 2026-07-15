from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
METRICS = ROOT / "metrics"


class MetricsBaselineTests(unittest.TestCase):
    def test_github_traffic_baseline_reconciles_rolling_aggregates(self) -> None:
        report = self._read("github-traffic-baseline.json")
        views = report["views"]
        clones = report["clones"]

        self.assertEqual(report["schema_version"], 1)
        self.assertEqual(report["repository"], "becastil/Chats-empty-repo")
        self.assertEqual(report["window"]["days"], 14)
        self.assertEqual(len(views["views"]), 14)
        self.assertEqual(len(clones["clones"]), 14)
        self.assertEqual(
            [day["timestamp"] for day in views["views"]],
            [day["timestamp"] for day in clones["clones"]],
        )
        self.assertEqual(report["window"]["starts_at"], views["views"][0]["timestamp"])
        self.assertEqual(report["window"]["ends_at"], views["views"][-1]["timestamp"])
        datetime.fromisoformat(report["captured_at"].replace("Z", "+00:00"))

        for aggregate, daily_key in ((views, "views"), (clones, "clones")):
            self.assertEqual(
                aggregate["count"],
                sum(day["count"] for day in aggregate[daily_key]),
            )
            self.assertLessEqual(aggregate["uniques"], aggregate["count"])
            for day in aggregate[daily_key]:
                self.assertLessEqual(day["uniques"], day["count"])

        self.assertEqual(
            sum(item["count"] for item in report["referrers"]), views["count"]
        )
        self.assertEqual(
            sum(item["count"] for item in report["popular_paths"]), views["count"]
        )
        self.assertIn("not verified users", report["measurement_note"])

    def test_distribution_baseline_reconciles_and_has_no_warnings(self) -> None:
        report = self._read("distribution-baseline.json")
        summary = report["summary"]
        releases = report["releases"]

        self.assertEqual(report["schema_version"], 2)
        self.assertIsNone(report["change"])
        self.assertEqual(report["warnings"], [])
        self.assertEqual(summary["stable_releases"], len(releases))
        self.assertEqual(summary["complete_releases"], len(releases))
        self.assertTrue(all(release["contract"]["complete"] for release in releases))
        self.assertEqual(report["latest"]["tag"], "v0.3.40")
        self.assertEqual(summary["stable_releases"], 44)
        self.assertEqual(summary["primary_artifact_downloads"], 153)
        self.assertEqual(summary["portable_downloads"], 19)
        self.assertEqual(summary["wheel_downloads"], 134)
        self.assertEqual(summary["source_downloads"], 22)
        self.assertEqual(summary["manifest_downloads"], 125)
        self.assertEqual(summary["unknown_downloads"], 0)
        self.assertEqual(
            summary["primary_artifact_downloads"],
            summary["portable_downloads"] + summary["wheel_downloads"],
        )
        for channel, summary_key in (
            ("portable", "portable_downloads"),
            ("wheel", "wheel_downloads"),
            ("source", "source_downloads"),
            ("manifest", "manifest_downloads"),
            ("unknown", "unknown_downloads"),
        ):
            self.assertEqual(
                summary[summary_key],
                sum(release["downloads"][channel] for release in releases),
            )

    def test_pilot_and_growth_baselines_preserve_zero_revenue_truth(self) -> None:
        pilot = self._read("pilot-baseline.json")
        growth = self._read("growth-baseline.json")

        self.assertEqual(pilot["schema_version"], 7)
        self.assertEqual(pilot["follow_up"]["as_of"], "2026-07-15")
        self.assertEqual(pilot["summary"]["tracked_issues"], 0)
        self.assertEqual(pilot["summary"]["booked_revenue_usd"], 0)
        self.assertEqual(pilot["summary"]["qualification_review_issues"], 0)
        self.assertEqual(pilot["warnings"], [])

        self.assertEqual(growth["schema_version"], 2)
        self.assertEqual(growth["summary"]["tracked_pilot_requests"], 0)
        self.assertEqual(growth["summary"]["booked_revenue_usd"], 0)
        self.assertTrue(growth["summary"]["distribution_baseline_present"])
        self.assertTrue(growth["summary"]["qualification_reporting_available"])
        self.assertEqual(growth["bottleneck"]["stage"], "acquisition")
        self.assertEqual(growth["warnings"], [])
        self.assertEqual(
            growth["distribution_change"],
            {
                "manifest_downloads_delta": 5,
                "new_releases": ["v0.3.40"],
                "portable_downloads_delta": 1,
                "primary_artifact_downloads_delta": 6,
                "removed_releases": [],
                "source_downloads_delta": 1,
                "unknown_downloads_delta": 0,
                "wheel_downloads_delta": 5,
            },
        )

    def test_outreach_draft_baseline_is_aggregate_and_unsent(self) -> None:
        report = self._read("outreach-draft-baseline.json")
        summary = report["summary"]
        serialized = json.dumps(report)

        self.assertEqual(report["schema_version"], 5)
        self.assertEqual(report["as_of"], "2026-07-14")
        self.assertEqual(summary["prospects"], 5)
        self.assertEqual(summary["drafted"], 5)
        self.assertEqual(summary["fit_evidence_links"], 16)
        self.assertEqual(summary["attempted_prospects"], 0)
        self.assertEqual(summary["approved"], 0)
        self.assertEqual(summary["contacted"], 0)
        self.assertEqual(summary["replied"], 0)
        self.assertEqual(summary["pilot_requested"], 0)
        self.assertEqual(report["due_followups"], [])
        self.assertNotIn("prospect-", serialized)
        self.assertNotIn("https://", serialized)
        self.assertNotIn("@", serialized)
        self.assertIn("not lead, demand, payment, or revenue", report["evidence_note"])

    @staticmethod
    def _read(name: str) -> dict[str, object]:
        return json.loads((METRICS / name).read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
