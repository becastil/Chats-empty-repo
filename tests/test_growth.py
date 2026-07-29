from __future__ import annotations

from contextlib import redirect_stderr, redirect_stdout
from datetime import date
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
from repo_scout.pilot_funnel import (  # noqa: E402
    DECISION_CRITERION_KEYS,
    DISPLAY_STAGES,
    build_funnel,
)


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
        self.assertIn("Purchase criteria:\n  schema-6+ pilot report required", text)

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

    def test_accepts_schema_seven_qualification_reports(self) -> None:
        pilot = self._pilot(
            schema_version=7,
            sources={"website": self._source(deals=1, qualified=1)},
            criteria={"rollout_fit": self._source(deals=1, qualified=1)},
        )

        report = build_growth_report(self._distribution(), pilot)

        self.assertEqual(report["evidence_quality"]["pilot_schema_version"], 7)
        self.assertTrue(
            report["summary"]["decision_criterion_reporting_available"]
        )
        self.assertEqual(report["decision_criteria"][0]["criterion"], "rollout_fit")
        self.assertEqual(report["summary"]["target_profile_requests"], 1)
        self.assertEqual(report["summary"]["qualification_review_requests"], 0)
        self.assertIn(
            "Qualification scope: 1 complete / 1 target / 0 review / "
            "0 subset required",
            format_growth_report(report),
        )

    def test_payment_gate_prevents_cross_issue_conversion_masking(self) -> None:
        body = (
            "### How did you hear about Repo Scout?\n\n"
            "Direct outreach\n\n"
            "### Purchase readiness\n\n"
            "Ready to purchase the $299 pilot\n\n"
            "### Primary purchase criterion\n\n"
            "Supports our required repository standards"
        )
        pilot = build_funnel(
            [
                {
                    "number": 201,
                    "title": "Converted without payment evidence",
                    "url": "https://github.com/example/repo/issues/201",
                    "state": "CLOSED",
                    "updatedAt": "2026-07-10T12:00:00Z",
                    "labels": [
                        {"name": label}
                        for label in (
                            "pilot-lead",
                            "pilot-qualified",
                            "pilot-offered",
                            "pilot-active",
                            "pilot-converted",
                        )
                    ],
                    "body": body,
                },
                {
                    "number": 202,
                    "title": "Paid pilot without annual conversion",
                    "url": "https://github.com/example/repo/issues/202",
                    "state": "OPEN",
                    "updatedAt": "2026-07-10T12:00:00Z",
                    "labels": [
                        {"name": label}
                        for label in (
                            "pilot-lead",
                            "pilot-qualified",
                            "pilot-offered",
                            "pilot-paid",
                        )
                    ],
                    "body": body,
                },
            ],
            as_of=date(2026, 7, 10),
        )

        report = build_growth_report(self._distribution(), pilot)

        self.assertEqual(report["summary"]["booked_pilots"], 1)
        self.assertEqual(report["summary"]["annual_conversions"], 0)
        self.assertEqual(report["sources"][0]["annual_conversions"], 0)
        self.assertEqual(
            report["decision_criteria"][0]["annual_conversions"], 0
        )

    def test_rejects_inconsistent_schema_seven_qualification_evidence(self) -> None:
        pilot = self._pilot(
            schema_version=7,
            sources={"website": self._source(deals=1)},
        )
        pilot["summary"]["target_profile_issues"] = 2

        with self.assertRaisesRegex(
            GrowthInputError, "target profile exceeds complete qualification"
        ):
            build_growth_report(self._distribution(), pilot)

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
            (missing_key, "keys do not match schema 6+"),
            (extra_key, "keys do not match schema 6+"),
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

    def test_legacy_offer_bottleneck_uses_configured_pilot_price(self) -> None:
        for schema_version in (5, 6):
            with self.subTest(schema_version=schema_version):
                pilot = self._pilot(
                    schema_version=schema_version,
                    sources={"website": self._source(deals=1, qualified=1)},
                )
                pilot["pricing"] = {
                    "pilot_price_usd": 400,
                    "target_pilots": 3,
                    "target_revenue_usd": 1200,
                }

                report = build_growth_report(self._distribution(), pilot)

                self.assertEqual(report["bottleneck"]["stage"], "offer")
                self.assertEqual(
                    report["bottleneck"]["next_action"],
                    "Send the explicit $400 pilot terms to a qualified team.",
                )

    def test_schema_seven_commercial_actions_defer_to_the_sales_queue(
        self,
    ) -> None:
        def issue(
            number: int,
            *,
            ci_provider: str,
            labels: list[str],
        ) -> dict[str, object]:
            return {
                "number": number,
                "title": f"Pilot {number}",
                "state": "OPEN",
                "updatedAt": "2026-07-10T00:00:00Z",
                "body": "\n\n".join(
                    (
                        "### Team size\n\n12",
                        "### Repository count\n\n6",
                        f"### CI provider\n\n{ci_provider}",
                        "### Repository standard to enforce\n\n"
                        "Use one reviewed repository policy.",
                        "### How did you hear about Repo Scout?\n\n"
                        "Repo Scout website",
                        "### Purchase readiness\n\n"
                        "Ready to purchase the $299 pilot",
                        "### Primary purchase criterion\n\n"
                        "Works across our repositories and CI",
                    )
                ),
                "labels": labels,
            }

        cases = (
            (
                [
                    issue(
                        1,
                        ci_provider="GitLab CI",
                        labels=["pilot-lead", "pilot-qualified"],
                    )
                ],
                "offer",
                (
                    "Work the qualification-aware pilot sales queue before "
                    "sending the explicit $299 pilot terms."
                ),
            ),
            (
                [
                    issue(
                        1,
                        ci_provider="GitLab CI",
                        labels=[
                            "pilot-lead",
                            "pilot-qualified",
                            "pilot-offered",
                        ],
                    )
                ],
                "payment",
                (
                    "Work the qualification-aware pilot sales queue before "
                    "confirming purchase or payment."
                ),
            ),
            (
                [
                    issue(
                        1,
                        ci_provider="GitLab CI",
                        labels=[
                            "pilot-lead",
                            "pilot-qualified",
                            "pilot-offered",
                        ],
                    ),
                    issue(
                        2,
                        ci_provider="GitHub Actions",
                        labels=[
                            "pilot-lead",
                            "pilot-qualified",
                            "pilot-offered",
                            "pilot-paid",
                        ],
                    ),
                ],
                "pilot_target",
                (
                    "Work the qualification-aware pilot sales queue before "
                    "closing the next pilot."
                ),
            ),
        )

        for issues, stage, expected_action in cases:
            with self.subTest(stage=stage):
                pilot = build_funnel(
                    issues,
                    as_of=date(2026, 7, 10),
                )
                report = build_growth_report(self._distribution(), pilot)

                self.assertEqual(report["bottleneck"]["stage"], stage)
                self.assertEqual(
                    report["bottleneck"]["next_action"],
                    expected_action,
                )
                self.assertIn(
                    "private CI integration decision",
                    pilot["sales_queue"]["deals"][0]["next_action"],
                )

    def test_schema_seven_empty_queue_never_creates_a_phantom_deal_action(
        self,
    ) -> None:
        def closed_issue(labels: list[str]) -> dict[str, object]:
            return {
                "number": 1,
                "title": "Closed pilot request",
                "state": "CLOSED",
                "updatedAt": "2026-07-10T00:00:00Z",
                "body": "\n\n".join(
                    (
                        "### Team size\n\n12",
                        "### Repository count\n\n6",
                        "### CI provider\n\nGitHub Actions",
                        "### Repository standard to enforce\n\n"
                        "Use one reviewed repository policy.",
                        "### How did you hear about Repo Scout?\n\n"
                        "Repo Scout website",
                        "### Purchase readiness\n\n"
                        "Ready to purchase the $299 pilot",
                        "### Primary purchase criterion\n\n"
                        "Works across our repositories and CI",
                    )
                ),
                "labels": labels,
            }

        cases = (
            (
                ["pilot-lead"],
                "qualification",
                (
                    "Pilot request history exists, but no open pre-payment deal "
                    "is available for qualification."
                ),
                True,
            ),
            (
                ["pilot-lead", "pilot-qualified"],
                "offer",
                (
                    "Qualified pilot history exists, but no open pre-payment "
                    "deal is available for an offer."
                ),
                True,
            ),
            (
                ["pilot-lead", "pilot-qualified", "pilot-offered"],
                "payment",
                (
                    "Pilot offer history exists, but no open pre-payment deal "
                    "is available for payment follow-up."
                ),
                True,
            ),
            (
                [
                    "pilot-lead",
                    "pilot-qualified",
                    "pilot-offered",
                    "pilot-lost",
                ],
                "payment",
                (
                    "Pilot offer history exists, but no open pre-payment deal "
                    "is available for payment follow-up."
                ),
                False,
            ),
            (
                [
                    "pilot-lead",
                    "pilot-qualified",
                    "pilot-offered",
                    "pilot-paid",
                ],
                "pilot_target",
                (
                    "Booked revenue is real, but no open pre-payment deal is "
                    "available to close the next pilot."
                ),
                False,
            ),
        )

        for labels, stage, reason, expects_closed_warning in cases:
            with self.subTest(labels=labels):
                pilot = build_funnel(
                    [closed_issue(labels)],
                    as_of=date(2026, 7, 10),
                )

                self.assertEqual(pilot["summary"]["sales_actions"], 0)
                self.assertEqual(pilot["sales_queue"]["deals"], [])
                self.assertEqual(
                    any(
                        warning["kind"] == "closed_without_lost"
                        for warning in pilot["warnings"]
                    ),
                    expects_closed_warning,
                )

                report = build_growth_report(self._distribution(), pilot)

                self.assertEqual(report["bottleneck"]["stage"], stage)
                self.assertEqual(report["bottleneck"]["reason"], reason)
                self.assertEqual(
                    report["bottleneck"]["next_action"],
                    (
                        "No open pre-payment deal is available; replenish the "
                        "pilot sales queue."
                    ),
                )

    def test_schema_seven_empty_queue_prioritizes_open_lifecycle_repair(
        self,
    ) -> None:
        raw_issue = {
            "number": 1,
            "title": "Open request with unknown lifecycle",
            "state": "OPEN",
            "updatedAt": "2026-07-10T00:00:00Z",
            "body": "\n\n".join(
                (
                    "### Team size\n\n12",
                    "### Repository count\n\n6",
                    "### CI provider\n\nGitHub Actions",
                    "### Repository standard to enforce\n\n"
                    "Use one reviewed repository policy.",
                    "### How did you hear about Repo Scout?\n\n"
                    "Repo Scout website",
                    "### Purchase readiness\n\n"
                    "Ready to purchase the $299 pilot",
                    "### Primary purchase criterion\n\n"
                    "Works across our repositories and CI",
                )
            ),
            "labels": ["pilot-needs-review"],
        }
        pilot = build_funnel(
            [raw_issue],
            as_of=date(2026, 7, 10),
        )

        self.assertEqual(pilot["deals"][0]["stage"], "untracked")
        self.assertEqual(pilot["sales_queue"]["deals"], [])
        self.assertIn(
            "missing_known_stage",
            [warning["kind"] for warning in pilot["warnings"]],
        )

        report = build_growth_report(self._distribution(), pilot)

        self.assertEqual(report["bottleneck"]["stage"], "qualification")
        self.assertEqual(
            report["bottleneck"]["reason"],
            (
                "An open pilot request cannot enter the sales queue until its "
                "lifecycle evidence is reconciled."
            ),
        )
        self.assertEqual(
            report["bottleneck"]["next_action"],
            (
                "Reconcile open pilot lifecycle labels before selecting another "
                "sales action."
            ),
        )

        open_lead = json.loads(json.dumps(raw_issue))
        open_lead.update(
            {
                "number": 2,
                "title": "Open lead",
                "labels": ["pilot-lead"],
            }
        )
        mixed_pilot = build_funnel(
            [raw_issue, open_lead],
            as_of=date(2026, 7, 10),
        )
        self.assertEqual(len(mixed_pilot["sales_queue"]["deals"]), 1)

        mixed_report = build_growth_report(self._distribution(), mixed_pilot)

        self.assertEqual(
            mixed_report["bottleneck"]["next_action"],
            (
                "Reconcile open pilot lifecycle labels before selecting another "
                "sales action."
            ),
        )

    def test_schema_seven_growth_rejects_an_untrusted_sales_queue_gate(
        self,
    ) -> None:
        raw_issue = {
            "number": 1,
            "title": "GitLab pilot",
            "state": "OPEN",
            "updatedAt": "2026-07-10T00:00:00Z",
            "body": "\n\n".join(
                (
                    "### Team size\n\n12",
                    "### Repository count\n\n6",
                    "### CI provider\n\nGitLab CI",
                    "### Repository standard to enforce\n\n"
                    "Use one reviewed repository policy.",
                    "### How did you hear about Repo Scout?\n\n"
                    "Repo Scout website",
                    "### Purchase readiness\n\n"
                    "Ready to purchase the $299 pilot",
                    "### Primary purchase criterion\n\n"
                    "Works across our repositories and CI",
                )
            ),
            "labels": [
                "pilot-lead",
                "pilot-qualified",
                "pilot-offered",
            ],
        }
        pilot = build_funnel(
            [raw_issue],
            as_of=date(2026, 7, 10),
        )

        unsafe_action = json.loads(json.dumps(pilot))
        unsafe_action["sales_queue"]["deals"][0]["next_action"] = (
            "Confirm the purchase and payment path."
        )
        with self.assertRaisesRegex(
            GrowthInputError,
            "next_action does not preserve the ready CI provider gate",
        ):
            build_growth_report(self._distribution(), unsafe_action)

        self_authorized_action = json.loads(json.dumps(pilot))
        self_authorized_action["sales_queue"]["deals"][0]["qualification"][
            "ci_provider"
        ] = "github_actions"
        self_authorized_action["sales_queue"]["deals"][0]["next_action"] = (
            "Confirm the purchase and payment path."
        )
        with self.assertRaisesRegex(
            GrowthInputError,
            "sales_queue.deals does not match open pre-payment deals",
        ):
            build_growth_report(
                self._distribution(),
                self_authorized_action,
            )

        coordinated_stage_edit = json.loads(json.dumps(pilot))
        coordinated_stage_edit["deals"][0]["stage"] = "qualified"
        coordinated_stage_edit["sales_queue"]["deals"][0]["stage"] = "qualified"
        with self.assertRaisesRegex(
            GrowthInputError,
            "by_stage does not match deals",
        ):
            build_growth_report(
                self._distribution(),
                coordinated_stage_edit,
            )

        lead_issue = json.loads(json.dumps(raw_issue))
        lead_issue["labels"] = ["pilot-lead"]
        coordinated_progression_edit = build_funnel(
            [lead_issue],
            as_of=date(2026, 7, 10),
        )
        coordinated_progression_edit["deals"][0]["stage"] = "offered"
        coordinated_progression_edit["sales_queue"]["deals"][0][
            "stage"
        ] = "offered"
        coordinated_progression_edit["by_stage"]["lead"] = 0
        coordinated_progression_edit["by_stage"]["offered"] = 1
        with self.assertRaisesRegex(
            GrowthInputError,
            "by_source offered_pilots does not match visible deal stages",
        ):
            build_growth_report(
                self._distribution(),
                coordinated_progression_edit,
            )

        missing_queue = json.loads(json.dumps(pilot))
        del missing_queue["sales_queue"]
        with self.assertRaisesRegex(
            GrowthInputError,
            r"pilot report\.sales_queue must be a JSON object",
        ):
            build_growth_report(self._distribution(), missing_queue)

        inconsistent_count = json.loads(json.dumps(pilot))
        inconsistent_count["summary"]["sales_actions"] = 0
        with self.assertRaisesRegex(
            GrowthInputError,
            "sales_actions does not match sales_queue.deals",
        ):
            build_growth_report(self._distribution(), inconsistent_count)

        forged_empty_queue = json.loads(json.dumps(pilot))
        forged_empty_queue["summary"]["sales_actions"] = 0
        forged_empty_queue["sales_queue"]["deals"] = []
        with self.assertRaisesRegex(
            GrowthInputError,
            "sales_queue.deals does not match open pre-payment deals",
        ):
            build_growth_report(self._distribution(), forged_empty_queue)

        canonical_queue = build_funnel(
            [
                {
                    **raw_issue,
                    "number": 2,
                    "updatedAt": "2026-07-05T00:00:00Z",
                },
                {
                    **raw_issue,
                    "number": 3,
                    "updatedAt": "2026-07-09T00:00:00Z",
                },
            ],
            as_of=date(2026, 7, 10),
        )
        self.assertEqual(
            [
                deal["number"]
                for deal in canonical_queue["sales_queue"]["deals"]
            ],
            [2, 3],
        )
        reordered_queue = json.loads(json.dumps(canonical_queue))
        reordered_queue["sales_queue"]["deals"].reverse()
        with self.assertRaisesRegex(
            GrowthInputError,
            "sales_queue.deals is not in canonical priority order",
        ):
            build_growth_report(self._distribution(), reordered_queue)

        forged_priority = json.loads(json.dumps(canonical_queue))
        forged_priority["sales_queue"]["deals"][0]["priority"] = 2
        with self.assertRaisesRegex(
            GrowthInputError,
            "priority does not match purchase readiness",
        ):
            build_growth_report(self._distribution(), forged_priority)

        forged_age = json.loads(json.dumps(canonical_queue))
        forged_age["sales_queue"]["deals"][0]["age_days"] = 4
        with self.assertRaisesRegex(
            GrowthInputError,
            "age_days does not match updated_at and follow_up.as_of",
        ):
            build_growth_report(self._distribution(), forged_age)

        unsafe_scope = build_funnel(
            [
                {
                    "number": 2,
                    "title": "Out-of-profile GitHub pilot",
                    "state": "OPEN",
                    "updatedAt": "2026-07-10T00:00:00Z",
                    "body": "\n\n".join(
                        (
                            "### Team size\n\n2",
                            "### Repository count\n\n1",
                            "### CI provider\n\nGitHub Actions",
                            "### Repository standard to enforce\n\n"
                            "Use one reviewed repository policy.",
                            "### How did you hear about Repo Scout?\n\n"
                            "Repo Scout website",
                            "### Purchase readiness\n\n"
                            "Ready to purchase the $299 pilot",
                            "### Primary purchase criterion\n\n"
                            "Works across our repositories and CI",
                        )
                    ),
                    "labels": [
                        "pilot-lead",
                        "pilot-qualified",
                        "pilot-offered",
                    ],
                }
            ],
            as_of=date(2026, 7, 10),
        )
        unsafe_scope["sales_queue"]["deals"][0]["next_action"] = (
            "Confirm the purchase and payment path."
        )
        with self.assertRaisesRegex(
            GrowthInputError,
            "next_action does not preserve the ready qualification scope gate",
        ):
            build_growth_report(self._distribution(), unsafe_scope)

        wrong_stage_action = build_funnel(
            [
                {
                    "number": 3,
                    "title": "Qualified GitHub pilot",
                    "state": "OPEN",
                    "updatedAt": "2026-07-10T00:00:00Z",
                    "body": "\n\n".join(
                        (
                            "### Team size\n\n12",
                            "### Repository count\n\n6",
                            "### CI provider\n\nGitHub Actions",
                            "### Repository standard to enforce\n\n"
                            "Use one reviewed repository policy.",
                            "### How did you hear about Repo Scout?\n\n"
                            "Repo Scout website",
                            "### Purchase readiness\n\n"
                            "Ready to purchase the $299 pilot",
                            "### Primary purchase criterion\n\n"
                            "Works across our repositories and CI",
                        )
                    ),
                    "labels": ["pilot-lead", "pilot-qualified"],
                }
            ],
            as_of=date(2026, 7, 10),
        )
        wrong_stage_action["sales_queue"]["deals"][0]["next_action"] = (
            "Confirm the purchase and payment path."
        )
        with self.assertRaisesRegex(
            GrowthInputError,
            "next_action does not match the stage-specific sales action contract",
        ):
            build_growth_report(self._distribution(), wrong_stage_action)

        price_divergent = json.loads(json.dumps(wrong_stage_action))
        price_divergent["pricing"] = {
            "pilot_price_usd": 400,
            "target_pilots": 3,
            "target_revenue_usd": 1200,
        }
        price_divergent["sales_queue"]["deals"][0]["next_action"] = (
            "Send the $299 pilot terms."
        )
        with self.assertRaisesRegex(
            GrowthInputError,
            (
                "pilot report.pricing.pilot_price_usd must match public intake "
                r"price of \$299"
            ),
        ):
            build_growth_report(self._distribution(), price_divergent)

        malformed_cases = (
            ("stage", [], "stage must be an open pre-payment stage"),
            (
                "qualification.status",
                [],
                "qualification.status must be a recognized value",
            ),
            (
                "qualification.pilot_repository_scope",
                [],
                "pilot_repository_scope must be a recognized value",
            ),
            (
                "qualification.ci_provider",
                "future_ci",
                "ci_provider must be null or a recognized value",
            ),
            (
                "qualification.ci_provider",
                [],
                "ci_provider must be null or a recognized value",
            ),
            (
                "qualification.ci_provider",
                None,
                "ci_provider must be recognized for complete qualification",
            ),
        )
        for field, value, message in malformed_cases:
            with self.subTest(field=field):
                malformed = json.loads(json.dumps(wrong_stage_action))
                queue_deal = malformed["sales_queue"]["deals"][0]
                if field == "stage":
                    queue_deal["stage"] = value
                elif field == "qualification.status":
                    queue_deal["qualification"]["status"] = value
                elif field == "qualification.ci_provider":
                    queue_deal["qualification"]["ci_provider"] = value
                else:
                    queue_deal["qualification"][
                        "pilot_repository_scope"
                    ] = value
                with self.assertRaisesRegex(GrowthInputError, message):
                    build_growth_report(self._distribution(), malformed)

        for field in ("pilot_repository_scope", "ci_provider"):
            with self.subTest(missing=field):
                missing_qualification_field = json.loads(
                    json.dumps(wrong_stage_action)
                )
                del missing_qualification_field["sales_queue"]["deals"][0][
                    "qualification"
                ][field]
                with self.assertRaisesRegex(
                    GrowthInputError,
                    rf"qualification\.{field} must be present",
                ):
                    build_growth_report(
                        self._distribution(),
                        missing_qualification_field,
                    )

    def test_schema_seven_growth_derives_queue_age_from_activity(
        self,
    ) -> None:
        body = "\n\n".join(
            (
                "### Team size\n\n12",
                "### Repository count\n\n6",
                "### CI provider\n\nGitHub Actions",
                "### Repository standard to enforce\n\n"
                "Use one reviewed repository policy.",
                "### How did you hear about Repo Scout?\n\n"
                "Repo Scout website",
                "### Purchase readiness\n\n"
                "Ready to purchase the $299 pilot",
                "### Primary purchase criterion\n\n"
                "Works across our repositories and CI",
            )
        )
        pilot = build_funnel(
            [
                {
                    "number": 1,
                    "title": "Older ready buyer",
                    "state": "OPEN",
                    "updatedAt": "2026-07-05T00:00:00Z",
                    "body": body,
                    "labels": [
                        "pilot-lead",
                        "pilot-qualified",
                        "pilot-offered",
                    ],
                },
                {
                    "number": 2,
                    "title": "Newer ready buyer",
                    "state": "OPEN",
                    "updatedAt": "2026-07-09T00:00:00Z",
                    "body": body,
                    "labels": [
                        "pilot-lead",
                        "pilot-qualified",
                        "pilot-offered",
                    ],
                },
            ],
            as_of=date(2026, 7, 10),
        )
        self.assertEqual(
            [deal["number"] for deal in pilot["sales_queue"]["deals"]],
            [1, 2],
        )

        forged = json.loads(json.dumps(pilot))
        details_by_number = {
            deal["number"]: deal for deal in forged["deals"]
        }
        queue_by_number = {
            deal["number"]: deal for deal in forged["sales_queue"]["deals"]
        }
        details_by_number[1]["age_days"] = 0
        queue_by_number[1]["age_days"] = 0
        details_by_number[2]["age_days"] = 6
        queue_by_number[2]["age_days"] = 6
        forged["sales_queue"]["deals"].reverse()

        with self.assertRaisesRegex(
            GrowthInputError,
            "age_days does not match updated_at and follow_up.as_of",
        ):
            build_growth_report(self._distribution(), forged)

        for as_of in (None, "", "20260710", "2026-7-10"):
            with self.subTest(as_of=as_of):
                malformed_date = json.loads(json.dumps(pilot))
                if as_of is None:
                    del malformed_date["follow_up"]["as_of"]
                else:
                    malformed_date["follow_up"]["as_of"] = as_of
                with self.assertRaisesRegex(
                    GrowthInputError,
                    r"follow_up\.as_of must be canonical YYYY-MM-DD",
                ):
                    build_growth_report(
                        self._distribution(),
                        malformed_date,
                    )

        timestamp_drift = json.loads(json.dumps(pilot))
        timestamp_drift["sales_queue"]["deals"][0].update(
            {
                "updated_at": "2026-07-06T00:00:00Z",
                "age_days": 4,
            }
        )
        with self.assertRaisesRegex(
            GrowthInputError,
            "sales_queue.deals does not match open pre-payment deals",
        ):
            build_growth_report(self._distribution(), timestamp_drift)

        edge_timestamps = build_funnel(
            [
                {
                    "number": 10,
                    "title": "Missing activity",
                    "state": "OPEN",
                    "body": body,
                    "labels": [
                        "pilot-lead",
                        "pilot-qualified",
                        "pilot-offered",
                    ],
                },
                {
                    "number": 11,
                    "title": "Future activity",
                    "state": "OPEN",
                    "updatedAt": "2026-07-11T00:00:00Z",
                    "body": body,
                    "labels": [
                        "pilot-lead",
                        "pilot-qualified",
                        "pilot-offered",
                    ],
                },
                {
                    "number": 12,
                    "title": "Offset activity",
                    "state": "OPEN",
                    "updatedAt": "2026-07-04T00:30:00+02:00",
                    "body": body,
                    "labels": [
                        "pilot-lead",
                        "pilot-qualified",
                        "pilot-offered",
                    ],
                },
            ],
            as_of=date(2026, 7, 10),
        )

        edge_report = build_growth_report(
            self._distribution(),
            edge_timestamps,
        )

        self.assertEqual(edge_report["summary"]["open_sales_actions"], 3)
        self.assertEqual(
            [
                (
                    deal["number"],
                    deal["updated_at"],
                    deal["age_days"],
                )
                for deal in edge_timestamps["sales_queue"]["deals"]
            ],
            [
                (12, "2026-07-03T22:30:00Z", 7),
                (10, None, None),
                (11, "2026-07-11T00:00:00Z", -1),
            ],
        )

    def test_schema_seven_growth_derives_bookings_from_deals(
        self,
    ) -> None:
        raw_issue = {
            "number": 1,
            "title": "Offered pilot",
            "state": "OPEN",
            "updatedAt": "2026-07-10T00:00:00Z",
            "body": "\n\n".join(
                (
                    "### Team size\n\n12",
                    "### Repository count\n\n6",
                    "### CI provider\n\nGitHub Actions",
                    "### Repository standard to enforce\n\n"
                    "Use one reviewed repository policy.",
                    "### How did you hear about Repo Scout?\n\n"
                    "Repo Scout website",
                    "### Purchase readiness\n\n"
                    "Ready to purchase the $299 pilot",
                    "### Primary purchase criterion\n\n"
                    "Works across our repositories and CI",
                )
            ),
            "labels": [
                "pilot-lead",
                "pilot-qualified",
                "pilot-offered",
            ],
        }

        def set_bookings(report: dict[str, object], count: int) -> None:
            report["summary"]["booked_pilots"] = count
            report["summary"]["booked_revenue_usd"] = count * 299
            for segment_name in ("by_source", "by_decision_criterion"):
                segment = next(
                    totals
                    for totals in report[segment_name].values()
                    if totals["deals"]
                )
                segment["booked_pilots"] = count
                segment["booked_revenue_usd"] = count * 299

        pilot = build_funnel([raw_issue], as_of=date(2026, 7, 10))
        self.assertFalse(pilot["deals"][0]["booked"])
        self.assertEqual(
            build_growth_report(self._distribution(), pilot)["bottleneck"][
                "stage"
            ],
            "payment",
        )

        forged = json.loads(json.dumps(pilot))
        set_bookings(forged, 1)
        with self.assertRaisesRegex(
            GrowthInputError,
            "booked_pilots does not match deals",
        ):
            build_growth_report(self._distribution(), forged)

        coordinated = json.loads(json.dumps(forged))
        coordinated["deals"][0]["booked"] = True
        with self.assertRaisesRegex(
            GrowthInputError,
            "booked contradicts its pre-payment stage",
        ):
            build_growth_report(self._distribution(), coordinated)

        malformed = json.loads(json.dumps(pilot))
        malformed["deals"][0]["booked"] = 1
        with self.assertRaisesRegex(
            GrowthInputError,
            "booked must be a boolean",
        ):
            build_growth_report(self._distribution(), malformed)

        paid = build_funnel(
            [
                {
                    **raw_issue,
                    "labels": [
                        *raw_issue["labels"],
                        "pilot-paid",
                    ],
                }
            ],
            as_of=date(2026, 7, 10),
        )
        self.assertTrue(paid["deals"][0]["booked"])
        self.assertEqual(
            build_growth_report(self._distribution(), paid)["bottleneck"][
                "stage"
            ],
            "pilot_target",
        )
        erased = json.loads(json.dumps(paid))
        erased["deals"][0]["booked"] = False
        set_bookings(erased, 0)
        with self.assertRaisesRegex(
            GrowthInputError,
            "booked must be true for the paid stage",
        ):
            build_growth_report(self._distribution(), erased)

    def test_schema_seven_growth_derives_terminal_outcomes_from_deals(
        self,
    ) -> None:
        raw_issue = {
            "number": 1,
            "title": "Paid active pilot",
            "state": "OPEN",
            "updatedAt": "2026-07-10T00:00:00Z",
            "body": "\n\n".join(
                (
                    "### Team size\n\n12",
                    "### Repository count\n\n6",
                    "### CI provider\n\nGitHub Actions",
                    "### Repository standard to enforce\n\n"
                    "Use one reviewed repository policy.",
                    "### How did you hear about Repo Scout?\n\n"
                    "Repo Scout website",
                    "### Purchase readiness\n\n"
                    "Ready to purchase the $299 pilot",
                    "### Primary purchase criterion\n\n"
                    "Works across our repositories and CI",
                )
            ),
            "labels": [
                "pilot-lead",
                "pilot-qualified",
                "pilot-offered",
                "pilot-paid",
                "pilot-active",
            ],
        }

        def set_terminal_outcome(
            report: dict[str, object],
            field: str,
            count: int,
        ) -> None:
            report["summary"][field] = count
            for segment_name in ("by_source", "by_decision_criterion"):
                segment = next(
                    totals
                    for totals in report[segment_name].values()
                    if totals["deals"]
                )
                segment[field] = count

        active = build_funnel(
            [raw_issue],
            target_pilots=1,
            as_of=date(2026, 7, 10),
        )
        self.assertEqual(
            build_growth_report(self._distribution(), active)["bottleneck"][
                "stage"
            ],
            "retention",
        )
        forged_conversion = json.loads(json.dumps(active))
        set_terminal_outcome(
            forged_conversion,
            "annual_conversions",
            1,
        )
        with self.assertRaisesRegex(
            GrowthInputError,
            "annual_conversions does not match deals",
        ):
            build_growth_report(self._distribution(), forged_conversion)

        converted = build_funnel(
            [
                {
                    **raw_issue,
                    "title": "Converted pilot",
                    "state": "CLOSED",
                    "labels": [
                        *raw_issue["labels"],
                        "pilot-converted",
                    ],
                }
            ],
            target_pilots=1,
            as_of=date(2026, 7, 10),
        )
        self.assertEqual(converted["summary"]["annual_conversions"], 1)
        self.assertEqual(
            build_growth_report(self._distribution(), converted)[
                "bottleneck"
            ]["stage"],
            "validated",
        )

        lost = build_funnel(
            [
                {
                    **raw_issue,
                    "title": "Lost pilot",
                    "state": "CLOSED",
                    "labels": ["pilot-lead", "pilot-lost"],
                }
            ],
            target_pilots=1,
            as_of=date(2026, 7, 10),
        )
        self.assertEqual(lost["summary"]["lost_pilots"], 1)
        build_growth_report(self._distribution(), lost)
        erased_loss = json.loads(json.dumps(lost))
        set_terminal_outcome(erased_loss, "lost_pilots", 0)
        with self.assertRaisesRegex(
            GrowthInputError,
            "lost_pilots does not match deals",
        ):
            build_growth_report(self._distribution(), erased_loss)

        conflict = build_funnel(
            [
                {
                    **raw_issue,
                    "title": "Conflicting terminal pilot",
                    "labels": [
                        *raw_issue["labels"],
                        "pilot-converted",
                        "pilot-lost",
                    ],
                }
            ],
            target_pilots=1,
            as_of=date(2026, 7, 10),
        )
        self.assertEqual(conflict["deals"][0]["stage"], "conflict")
        self.assertEqual(conflict["summary"]["annual_conversions"], 0)
        self.assertEqual(conflict["summary"]["lost_pilots"], 0)
        build_growth_report(self._distribution(), conflict)

    def test_schema_seven_growth_derives_terminal_outcome_attribution(
        self,
    ) -> None:
        body = "\n\n".join(
            (
                "### Team size\n\n12",
                "### Repository count\n\n6",
                "### CI provider\n\nGitHub Actions",
                "### Repository standard to enforce\n\n"
                "Use one reviewed repository policy.",
                "### How did you hear about Repo Scout?\n\n"
                "Repo Scout website",
                "### Purchase readiness\n\n"
                "Ready to purchase the $299 pilot",
                "### Primary purchase criterion\n\n"
                "Supports our required repository standards",
            )
        )
        converted_issue = {
            "number": 1,
            "title": "Converted website pilot",
            "state": "CLOSED",
            "updatedAt": "2026-07-10T00:00:00Z",
            "body": body,
            "labels": [
                "pilot-lead",
                "pilot-qualified",
                "pilot-offered",
                "pilot-paid",
                "pilot-active",
                "pilot-converted",
            ],
        }
        lost_issue = {
            **converted_issue,
            "number": 2,
            "title": "Lost outreach pilot",
            "body": body.replace(
                "Repo Scout website",
                "Direct outreach",
            ).replace(
                "Supports our required repository standards",
                "Works across our repositories and CI",
            ),
            "labels": [
                "pilot-lead",
                "pilot-qualified",
                "pilot-offered",
                "pilot-paid",
                "pilot-active",
                "pilot-lost",
            ],
        }
        pilot = build_funnel(
            [converted_issue, lost_issue],
            target_pilots=2,
            as_of=date(2026, 7, 10),
        )
        build_growth_report(self._distribution(), pilot)

        unknown = build_funnel(
            [
                {
                    **converted_issue,
                    "number": 3,
                    "title": "Converted pilot with edited answers",
                    "body": body.replace(
                        "Repo Scout website",
                        "Email newsletter",
                    ).replace(
                        "Supports our required repository standards",
                        "Lowest price",
                    ),
                }
            ],
            target_pilots=1,
            as_of=date(2026, 7, 10),
        )
        self.assertEqual(unknown["deals"][0]["source"], "unknown")
        self.assertEqual(
            unknown["deals"][0]["decision_criterion"],
            "unknown",
        )
        build_growth_report(self._distribution(), unknown)

        swap_cases = (
            (
                "by_source",
                "website",
                "outreach",
                "annual_conversions",
            ),
            ("by_source", "website", "outreach", "lost_pilots"),
            (
                "by_decision_criterion",
                "policy_fit",
                "rollout_fit",
                "annual_conversions",
            ),
            (
                "by_decision_criterion",
                "policy_fit",
                "rollout_fit",
                "lost_pilots",
            ),
        )
        for table, first, second, field in swap_cases:
            with self.subTest(table=table, field=field):
                forged = json.loads(json.dumps(pilot))
                rows = forged[table]
                rows[first][field], rows[second][field] = (
                    rows[second][field],
                    rows[first][field],
                )
                with self.assertRaisesRegex(
                    GrowthInputError,
                    rf"{table}\.{first}\.{field} does not match deals",
                ):
                    build_growth_report(self._distribution(), forged)

        malformed_cases = (
            ("source", ["email"]),
            ("source", "email"),
            ("decision_criterion", {"name": "price"}),
            ("decision_criterion", "price"),
        )
        for field, value in malformed_cases:
            with self.subTest(field=field, value_type=type(value).__name__):
                malformed = json.loads(json.dumps(pilot))
                malformed["deals"][0][field] = value
                with self.assertRaisesRegex(
                    GrowthInputError,
                    rf"deals\[0\]\.{field} must be a recognized value",
                ):
                    build_growth_report(self._distribution(), malformed)

    def test_schema_seven_growth_derives_booking_attribution(
        self,
    ) -> None:
        body = "\n\n".join(
            (
                "### Team size\n\n12",
                "### Repository count\n\n6",
                "### CI provider\n\nGitHub Actions",
                "### Repository standard to enforce\n\n"
                "Use one reviewed repository policy.",
                "### How did you hear about Repo Scout?\n\n"
                "Repo Scout website",
                "### Purchase readiness\n\n"
                "Ready to purchase the $299 pilot",
                "### Primary purchase criterion\n\n"
                "Supports our required repository standards",
            )
        )
        booked_issue = {
            "number": 1,
            "title": "Paid website pilot",
            "state": "CLOSED",
            "updatedAt": "2026-07-10T00:00:00Z",
            "body": body,
            "labels": [
                "pilot-lead",
                "pilot-qualified",
                "pilot-offered",
                "pilot-paid",
                "pilot-active",
            ],
        }
        offered_issue = {
            **booked_issue,
            "number": 2,
            "title": "Offered outreach pilot",
            "body": body.replace(
                "Repo Scout website",
                "Direct outreach",
            ).replace(
                "Supports our required repository standards",
                "Works across our repositories and CI",
            ),
            "labels": [
                "pilot-lead",
                "pilot-qualified",
                "pilot-offered",
            ],
        }
        pilot = build_funnel(
            [booked_issue, offered_issue],
            target_pilots=1,
            as_of=date(2026, 7, 10),
        )
        build_growth_report(self._distribution(), pilot)

        cases = (
            ("by_source", "website", "outreach"),
            (
                "by_decision_criterion",
                "policy_fit",
                "rollout_fit",
            ),
        )
        for table, booked_segment, offered_segment in cases:
            with self.subTest(table=table):
                forged = json.loads(json.dumps(pilot))
                rows = forged[table]
                for field in ("booked_pilots", "booked_revenue_usd"):
                    rows[booked_segment][field], rows[offered_segment][
                        field
                    ] = (
                        rows[offered_segment][field],
                        rows[booked_segment][field],
                    )
                with self.assertRaisesRegex(
                    GrowthInputError,
                    (
                        rf"{table}\.{booked_segment}\.booked_pilots "
                        r"does not match deals"
                    ),
                ):
                    build_growth_report(self._distribution(), forged)

    def test_schema_seven_growth_derives_qualification_from_deals(
        self,
    ) -> None:
        raw_issue = {
            "number": 1,
            "title": "Target-profile pilot",
            "state": "OPEN",
            "updatedAt": "2026-07-10T00:00:00Z",
            "body": "\n\n".join(
                (
                    "### Team size\n\n12",
                    "### Repository count\n\n6",
                    "### CI provider\n\nGitHub Actions",
                    "### Repository standard to enforce\n\n"
                    "Use one reviewed repository policy.",
                    "### How did you hear about Repo Scout?\n\n"
                    "Repo Scout website",
                    "### Purchase readiness\n\n"
                    "Ready to purchase the $299 pilot",
                    "### Primary purchase criterion\n\n"
                    "Works across our repositories and CI",
                )
            ),
            "labels": [
                "pilot-lead",
                "pilot-qualified",
                "pilot-offered",
            ],
        }
        pilot = build_funnel([raw_issue], as_of=date(2026, 7, 10))
        self.assertEqual(pilot["summary"]["target_profile_issues"], 1)
        self.assertEqual(pilot["summary"]["qualification_review_issues"], 0)
        build_growth_report(self._distribution(), pilot)

        forged = json.loads(json.dumps(pilot))
        forged["summary"]["target_profile_issues"] = 0
        forged["summary"]["qualification_review_issues"] = 1
        with self.assertRaisesRegex(
            GrowthInputError,
            "target_profile_issues does not match deals",
        ):
            build_growth_report(self._distribution(), forged)

        incomplete_issue = {
            **raw_issue,
            "number": 2,
            "body": raw_issue["body"].replace(
                "### Team size\n\n12\n\n",
                "",
            ),
        }
        incomplete = build_funnel(
            [incomplete_issue],
            as_of=date(2026, 7, 10),
        )
        self.assertEqual(incomplete["summary"]["complete_qualification_issues"], 0)
        build_growth_report(self._distribution(), incomplete)
        forged_complete = json.loads(json.dumps(incomplete))
        forged_complete["summary"]["complete_qualification_issues"] = 1
        with self.assertRaisesRegex(
            GrowthInputError,
            "complete_qualification_issues does not match deals",
        ):
            build_growth_report(self._distribution(), forged_complete)

        subset_issue = {
            **raw_issue,
            "number": 3,
            "body": raw_issue["body"].replace(
                "### Repository count\n\n6",
                "### Repository count\n\n11",
            ),
        }
        subset = build_funnel([subset_issue], as_of=date(2026, 7, 10))
        self.assertEqual(subset["summary"]["subset_scope_issues"], 1)
        build_growth_report(self._distribution(), subset)
        forged_subset = json.loads(json.dumps(subset))
        forged_subset["summary"]["subset_scope_issues"] = 0
        with self.assertRaisesRegex(
            GrowthInputError,
            "subset_scope_issues does not match deals",
        ):
            build_growth_report(self._distribution(), forged_subset)

        closed = build_funnel(
            [{**raw_issue, "state": "CLOSED"}],
            as_of=date(2026, 7, 10),
        )
        malformed_closed = json.loads(json.dumps(closed))
        del malformed_closed["deals"][0]["qualification"]["ci_provider"]
        with self.assertRaisesRegex(
            GrowthInputError,
            r"qualification\.ci_provider must be present",
        ):
            build_growth_report(self._distribution(), malformed_closed)

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
            (valid_distribution, {**valid_pilot, "schema_version": 8}, "schema_version"),
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
        if schema_version >= 6:
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
        if schema_version == 7:
            report["summary"].update(
                {
                    "complete_qualification_issues": tracked,
                    "target_profile_issues": tracked,
                    "qualification_review_issues": 0,
                    "subset_scope_issues": 0,
                }
            )
            qualified = sum(
                source["qualified_pilots"]
                for source in source_totals.values()
            )
            offered = sum(
                source["offered_pilots"]
                for source in source_totals.values()
            )
            stage_plan = (
                ["lead"] * (tracked - qualified)
                + ["qualified"] * (qualified - offered)
                + ["offered"] * (offered - booked)
                + ["paid"] * (booked - converted)
                + ["converted"] * converted
            )
            source_plan = [
                source
                for source, totals in source_totals.items()
                for _ in range(totals["deals"])
            ]
            criterion_plan = [
                criterion
                for criterion, totals in criterion_totals.items()
                for _ in range(totals["deals"])
            ]
            report["deals"] = [
                {
                    "number": index + 1,
                    "stage": stage,
                    "state": "CLOSED",
                    "booked": stage in {"paid", "active", "converted"},
                    "source": source_plan[index],
                    "decision_criterion": criterion_plan[index],
                    "qualification": {
                        "status": "target",
                        "pilot_repository_scope": "within_offer",
                        "ci_provider": "github_actions",
                    },
                }
                for index, stage in enumerate(stage_plan)
            ]
            report["by_stage"] = {
                stage: stage_plan.count(stage)
                for stage in DISPLAY_STAGES
            }
            report["follow_up"] = {
                "as_of": "2026-07-10",
                "stale_days": 7,
                "deals": [],
            }
            report["sales_queue"] = {"deals": []}
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
