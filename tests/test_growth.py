from __future__ import annotations

from contextlib import redirect_stderr, redirect_stdout
import io
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from repo_scout.growth import (  # noqa: E402
    GrowthInputError,
    build_growth_report,
    format_growth_report,
    main,
)
from repo_scout.pilot_funnel import DECISION_CRITERION_KEYS  # noqa: E402


class GrowthReportTests(unittest.TestCase):
    def test_identifies_acquisition_gap_without_treating_requests_as_people(
        self,
    ) -> None:
        report = build_growth_report(
            self._distribution(primary=4, portable=3, wheel=1),
            self._pilot(),
        )

        self.assertEqual(report["schema_version"], 2)
        self.assertTrue(report["summary"]["distribution_baseline_present"])
        self.assertEqual(report["summary"]["tracked_pilot_requests"], 0)
        self.assertEqual(report["distribution_change"]["primary_artifact_downloads_delta"], 4)
        self.assertEqual(report["bottleneck"]["stage"], "acquisition")
        self.assertIn("increased", report["bottleneck"]["reason"])
        self.assertEqual(report["sources"], [])
        self.assertIsNone(report["decision_criteria"])
        self.assertEqual(
            [warning["kind"] for warning in report["warnings"]],
            ["decision_criterion_evidence_unavailable"],
        )
        self.assertIn("not unique-user or conversion-rate", report["measurement_note"])

        text = format_growth_report(report)
        self.assertIn("Reach movement: +4 primary / +3 portable / +1 wheel", text)
        self.assertIn("Pilot funnel: 0 requests", text)
        self.assertIn("Bottleneck: acquisition", text)
        self.assertIn("Sources:\n  none", text)
        self.assertIn("Purchase criteria:\n  schema-6 pilot report required", text)

    def test_joins_source_progress_and_selects_payment_bottleneck(self) -> None:
        pilot = self._pilot(
            sources={
                "website": self._source(
                    deals=1,
                    qualified=1,
                    offered=1,
                )
            }
        )

        report = build_growth_report(
            self._distribution(primary=2, wheel=2), pilot
        )

        self.assertEqual(report["summary"]["attributed_pilot_requests"], 1)
        self.assertEqual(report["summary"]["qualified_pilots"], 1)
        self.assertEqual(report["summary"]["offered_pilots"], 1)
        self.assertEqual(report["bottleneck"]["stage"], "payment")
        self.assertEqual(report["sources"][0]["source"], "website")
        self.assertIn("website: 1 requests", format_growth_report(report))

    def test_joins_ordered_schema_six_purchase_criterion_outcomes(self) -> None:
        pilot = self._pilot(
            schema_version=6,
            sources={
                "website": self._source(
                    deals=2, qualified=2, offered=1, booked=1
                )
            },
            criteria={
                "privacy_security": self._source(deals=1, qualified=1),
                "policy_fit": self._source(
                    deals=1, qualified=1, offered=1, booked=1
                ),
            },
            booked=1,
        )

        report = build_growth_report(self._distribution(), pilot)

        self.assertEqual(report["schema_version"], 2)
        self.assertTrue(
            report["summary"]["decision_criterion_reporting_available"]
        )
        self.assertEqual(
            report["summary"]["declared_decision_criterion_requests"], 2
        )
        self.assertEqual(
            [row["criterion"] for row in report["decision_criteria"]],
            ["policy_fit", "privacy_security"],
        )
        self.assertEqual(
            report["decision_criteria"][0]["booked_revenue_usd"], 299
        )
        self.assertEqual(report["warnings"], [])
        text = format_growth_report(report)
        self.assertIn("Purchase criteria:", text)
        self.assertIn(
            "policy_fit: 1 requests, 1 qualified, 1 offered, 1 booked ($299)",
            text,
        )

    def test_surfaces_missing_and_unknown_purchase_criteria(self) -> None:
        pilot = self._pilot(
            schema_version=6,
            sources={"website": self._source(deals=2)},
            criteria={
                "unattributed": self._source(deals=1),
                "unknown": self._source(deals=1),
            },
            pilot_warnings=[
                {"kind": "missing_decision_criterion"},
                {"kind": "unknown_decision_criterion"},
            ],
        )

        report = build_growth_report(self._distribution(), pilot)

        self.assertEqual(
            report["summary"]["missing_decision_criterion_requests"], 1
        )
        self.assertEqual(
            report["summary"]["unknown_decision_criterion_requests"], 1
        )
        self.assertEqual(
            [warning["kind"] for warning in report["warnings"]],
            [
                "pilot_evidence_warnings",
                "missing_decision_criteria",
                "unknown_decision_criteria",
            ],
        )
        self.assertEqual(
            report["evidence_quality"][
                "missing_decision_criterion_requests"
            ],
            1,
        )

    def test_rejects_inconsistent_schema_six_criterion_evidence(self) -> None:
        valid = self._pilot(
            schema_version=6,
            sources={"website": self._source(deals=1, qualified=1)},
            criteria={"policy_fit": self._source(deals=1, qualified=1)},
        )
        missing_key = json.loads(json.dumps(valid))
        missing_key["by_decision_criterion"].pop("other")
        extra_key = json.loads(json.dumps(valid))
        extra_key["by_decision_criterion"]["future"] = self._source(deals=0)
        non_string_key = json.loads(json.dumps(valid))
        non_string_key["by_decision_criterion"].pop("other")
        non_string_key["by_decision_criterion"][1] = self._source(deals=0)
        boolean_count = json.loads(json.dumps(valid))
        boolean_count["by_decision_criterion"]["policy_fit"]["deals"] = True
        stage_mismatch = json.loads(json.dumps(valid))
        stage_mismatch["by_decision_criterion"]["policy_fit"][
            "qualified_pilots"
        ] = 0
        summary_mismatch = json.loads(json.dumps(valid))
        summary_mismatch["summary"]["declared_decision_criterion_issues"] = 0
        revenue_mismatch = json.loads(json.dumps(valid))
        revenue_mismatch["by_decision_criterion"]["policy_fit"][
            "booked_revenue_usd"
        ] = 1
        cases = [
            (missing_key, "keys do not match schema 6"),
            (extra_key, "keys do not match schema 6"),
            (non_string_key, "keys must be non-empty strings"),
            (boolean_count, "must be an integer"),
            (stage_mismatch, "qualified_pilots does not match by_source"),
            (summary_mismatch, "declared_decision_criterion_issues"),
            (revenue_mismatch, "booked revenue does not match pilots"),
        ]
        for pilot, message in cases:
            with self.subTest(message=message), self.assertRaisesRegex(
                GrowthInputError, message
            ):
                build_growth_report(self._distribution(), pilot)

    def test_selects_revenue_bottlenecks_from_observed_funnel_stages(self) -> None:
        cases = [
            (
                {"github": self._source(deals=1)},
                0,
                0,
                "qualification",
            ),
            (
                {"github": self._source(deals=1, qualified=1)},
                0,
                0,
                "offer",
            ),
            (
                {
                    "referral": self._source(
                        deals=1, qualified=1, offered=1, booked=1
                    )
                },
                1,
                0,
                "pilot_target",
            ),
            (
                {
                    "referral": self._source(
                        deals=3, qualified=3, offered=3, booked=3
                    )
                },
                3,
                0,
                "retention",
            ),
            (
                {
                    "referral": self._source(
                        deals=3,
                        qualified=3,
                        offered=3,
                        booked=3,
                        converted=1,
                    )
                },
                3,
                1,
                "validated",
            ),
        ]
        for sources, booked, converted, expected in cases:
            with self.subTest(expected=expected):
                pilot = self._pilot(
                    sources=sources,
                    booked=booked,
                    converted=converted,
                )
                report = build_growth_report(self._distribution(), pilot)
                self.assertEqual(report["bottleneck"]["stage"], expected)

    def test_requires_a_baseline_before_prioritizing_commercial_movement(self) -> None:
        distribution = self._distribution()
        distribution["change"] = None

        report = build_growth_report(distribution, self._pilot())

        self.assertEqual(report["bottleneck"]["stage"], "measurement")
        self.assertEqual(
            [warning["kind"] for warning in report["warnings"]],
            [
                "missing_distribution_baseline",
                "decision_criterion_evidence_unavailable",
            ],
        )
        self.assertIn("baseline required", format_growth_report(report))

    def test_surfaces_input_quality_and_missing_source_warnings(self) -> None:
        distribution = self._distribution(warnings=[{"kind": "release_drift"}])
        pilot = self._pilot(
            sources={
                "unattributed": self._source(deals=1),
                "unknown": self._source(deals=1),
            },
            pilot_warnings=[{"kind": "missing_lead_source"}],
        )

        report = build_growth_report(distribution, pilot)

        self.assertEqual(
            [warning["kind"] for warning in report["warnings"]],
            [
                "distribution_evidence_warnings",
                "pilot_evidence_warnings",
                "unattributed_pilot_requests",
                "unknown_pilot_sources",
                "decision_criterion_evidence_unavailable",
            ],
        )
        self.assertEqual(report["evidence_quality"]["distribution_warnings"], 1)
        self.assertEqual(report["evidence_quality"]["pilot_warnings"], 1)

    def test_rejects_unsupported_or_inconsistent_reports(self) -> None:
        valid_distribution = self._distribution()
        valid_pilot = self._pilot()
        schema_six_pilot = self._pilot(schema_version=6)
        self.assertEqual(
            build_growth_report(valid_distribution, schema_six_pilot)[
                "bottleneck"
            ]["stage"],
            "acquisition",
        )
        cases = [
            ({**valid_distribution, "schema_version": 3}, valid_pilot, "schema_version"),
            (valid_distribution, {**valid_pilot, "schema_version": 7}, "schema_version"),
            (
                {**valid_distribution, "change": {"portable_downloads_delta": 1}},
                valid_pilot,
                "primary_artifact_downloads_delta",
            ),
            (
                {
                    **valid_distribution,
                    "change": {
                        **valid_distribution["change"],
                        "primary_artifact_downloads_delta": 1,
                    },
                },
                valid_pilot,
                "primary delta does not match",
            ),
            (
                valid_distribution,
                {
                    **valid_pilot,
                    "summary": {**valid_pilot["summary"], "tracked_issues": 1},
                },
                "tracked_issues does not match",
            ),
            (
                valid_distribution,
                {
                    **valid_pilot,
                    "pricing": {**valid_pilot["pricing"], "target_revenue_usd": 1},
                },
                "target revenue",
            ),
            (
                valid_distribution,
                self._pilot(
                    sources={
                        "github": self._source(
                            deals=1, qualified=0, offered=1
                        )
                    }
                ),
                "not cumulative",
            ),
        ]
        for distribution, pilot, message in cases:
            with self.subTest(message=message), self.assertRaisesRegex(
                GrowthInputError, message
            ):
                build_growth_report(distribution, pilot)

    def test_cli_reads_two_reports_and_reports_invalid_json(self) -> None:
        with TemporaryDirectory() as tmp:
            distribution_path = Path(tmp) / "distribution.json"
            pilot_path = Path(tmp) / "pilot.json"
            distribution_path.write_text(
                json.dumps(self._distribution(primary=2, wheel=2)),
                encoding="utf-8",
            )
            pilot_path.write_text(json.dumps(self._pilot()), encoding="utf-8")
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                exit_code = main(
                    [str(distribution_path), str(pilot_path), "--format", "json"]
                )

            self.assertEqual(exit_code, 0)
            self.assertEqual(
                json.loads(stdout.getvalue())["bottleneck"]["stage"], "acquisition"
            )

            pilot_path.write_text("not-json", encoding="utf-8")
            stderr = io.StringIO()
            with redirect_stderr(stderr):
                exit_code = main([str(distribution_path), str(pilot_path)])
            self.assertEqual(exit_code, 2)
            self.assertIn("repo-scout-growth: invalid pilot JSON", stderr.getvalue())

    @staticmethod
    def _distribution(
        *,
        primary: int = 0,
        portable: int = 0,
        wheel: int = 0,
        warnings: list[dict[str, str]] | None = None,
    ) -> dict[str, object]:
        report_warnings = warnings or []
        return {
            "schema_version": 2,
            "summary": {"warning_count": len(report_warnings)},
            "change": {
                "baseline_schema_version": 2,
                "primary_artifact_downloads_delta": primary,
                "portable_downloads_delta": portable,
                "wheel_downloads_delta": wheel,
                "source_downloads_delta": 0,
                "manifest_downloads_delta": 0,
                "unknown_downloads_delta": 0,
                "new_releases": [],
                "removed_releases": [],
            },
            "warnings": report_warnings,
        }

    @classmethod
    def _pilot(
        cls,
        *,
        schema_version: int = 5,
        sources: dict[str, dict[str, int]] | None = None,
        criteria: dict[str, dict[str, int]] | None = None,
        booked: int = 0,
        converted: int = 0,
        pilot_warnings: list[dict[str, str]] | None = None,
    ) -> dict[str, object]:
        source_totals = sources or {}
        tracked = sum(source["deals"] for source in source_totals.values())
        attributed = sum(
            source["deals"]
            for name, source in source_totals.items()
            if name not in {"unattributed", "unknown"}
        )
        unattributed = source_totals.get("unattributed", {}).get("deals", 0)
        unknown = source_totals.get("unknown", {}).get("deals", 0)
        report = {
            "schema_version": schema_version,
            "pricing": {
                "pilot_price_usd": 299,
                "target_pilots": 3,
                "target_revenue_usd": 897,
            },
            "summary": {
                "tracked_issues": tracked,
                "attributed_issues": attributed,
                "unattributed_issues": unattributed,
                "unknown_source_issues": unknown,
                "booked_pilots": booked,
                "booked_revenue_usd": booked * 299,
                "annual_conversions": converted,
                "lost_pilots": 0,
                "sales_actions": 0,
            },
            "by_source": source_totals,
            "warnings": pilot_warnings or [],
        }
        if schema_version == 6:
            empty = cls._source(deals=0)
            criterion_totals = {
                criterion: dict(empty) for criterion in DECISION_CRITERION_KEYS
            }
            if criteria is None:
                criterion_totals["policy_fit"] = {
                    field: sum(source[field] for source in source_totals.values())
                    for field in empty
                }
            else:
                for criterion, totals in criteria.items():
                    criterion_totals[criterion] = totals
            declared = sum(
                totals["deals"]
                for criterion, totals in criterion_totals.items()
                if criterion not in {"unattributed", "unknown"}
            )
            report["summary"].update(
                {
                    "declared_decision_criterion_issues": declared,
                    "missing_decision_criterion_issues": criterion_totals[
                        "unattributed"
                    ]["deals"],
                    "unknown_decision_criterion_issues": criterion_totals[
                        "unknown"
                    ]["deals"],
                }
            )
            report["by_decision_criterion"] = criterion_totals
        return report

    @staticmethod
    def _source(
        *,
        deals: int,
        qualified: int = 0,
        offered: int = 0,
        booked: int = 0,
        converted: int = 0,
    ) -> dict[str, int]:
        return {
            "deals": deals,
            "qualified_pilots": qualified,
            "offered_pilots": offered,
            "booked_pilots": booked,
            "booked_revenue_usd": booked * 299,
            "annual_conversions": converted,
            "lost_pilots": 0,
        }


if __name__ == "__main__":
    unittest.main()
