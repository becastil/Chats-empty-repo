from __future__ import annotations

import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
METRICS = ROOT / "metrics"


class MetricsBaselineTests(unittest.TestCase):
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
        self.assertEqual(report["latest"]["tag"], "v0.3.30")
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

        self.assertEqual(pilot["schema_version"], 6)
        self.assertEqual(pilot["summary"]["tracked_issues"], 0)
        self.assertEqual(pilot["summary"]["booked_revenue_usd"], 0)
        self.assertEqual(pilot["warnings"], [])

        self.assertEqual(growth["schema_version"], 2)
        self.assertEqual(growth["summary"]["tracked_pilot_requests"], 0)
        self.assertEqual(growth["summary"]["booked_revenue_usd"], 0)
        self.assertTrue(growth["summary"]["distribution_baseline_present"])
        self.assertEqual(growth["bottleneck"]["stage"], "acquisition")
        self.assertEqual(growth["warnings"], [])
        for key, value in growth["distribution_change"].items():
            self.assertEqual(value, [] if key.endswith("releases") else 0)

    @staticmethod
    def _read(name: str) -> dict[str, object]:
        return json.loads((METRICS / name).read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
