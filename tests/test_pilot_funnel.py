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
    CI_PROVIDER_FIELD_HEADING,
    CI_PROVIDER_OPTIONS,
    DECISION_CRITERION_FIELD_HEADING,
    DECISION_CRITERION_OPTIONS,
    FunnelInputError,
    READINESS_FIELD_HEADING,
    READINESS_OPTIONS,
    REPOSITORY_COUNT_FIELD_HEADING,
    REPOSITORY_STANDARD_FIELD_HEADING,
    SOURCE_FIELD_HEADING,
    SOURCE_OPTIONS,
    TEAM_SIZE_FIELD_HEADING,
    build_funnel,
    format_funnel,
    main,
)


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests/fixtures/pilot_issues.json"


class PilotFunnelTests(unittest.TestCase):
    def test_issue_form_source_options_match_the_reporter_taxonomy(self) -> None:
        form = (
            ROOT / ".github/ISSUE_TEMPLATE/founding-team-pilot.yml"
        ).read_text(encoding="utf-8")

        self.assertIn("id: discovery_source", form)
        self.assertIn(f"label: {SOURCE_FIELD_HEADING}", form)
        source_section = form[form.index("id: discovery_source") :]
        next_field = source_section.find("\n  - type:")
        source_section = source_section[:next_field]
        positions = [
            source_section.index(f"        - {answer}")
            for _, answer in SOURCE_OPTIONS
        ]
        self.assertEqual(positions, sorted(positions))

        self.assertIn("id: purchase_readiness", form)
        self.assertIn(f"label: {READINESS_FIELD_HEADING}", form)
        readiness_section = form[form.index("id: purchase_readiness") :]
        next_field = readiness_section.find("\n  - type:")
        readiness_section = readiness_section[:next_field]
        readiness_positions = [
            readiness_section.index(f"        - {answer}")
            for _, answer in READINESS_OPTIONS
        ]
        self.assertEqual(readiness_positions, sorted(readiness_positions))
        self.assertIn("required: true", readiness_section)

        self.assertIn("id: decision_criterion", form)
        self.assertIn(f"label: {DECISION_CRITERION_FIELD_HEADING}", form)
        criterion_section = form[form.index("id: decision_criterion") :]
        next_field = criterion_section.find("\n  - type:")
        criterion_section = criterion_section[:next_field]
        criterion_positions = [
            criterion_section.index(f"        - {answer}")
            for _, answer in DECISION_CRITERION_OPTIONS
        ]
        self.assertEqual(criterion_positions, sorted(criterion_positions))
        self.assertIn("required: true", criterion_section)

        for field_id, heading in (
            ("team_size", TEAM_SIZE_FIELD_HEADING),
            ("repository_count", REPOSITORY_COUNT_FIELD_HEADING),
            ("repository_standard", REPOSITORY_STANDARD_FIELD_HEADING),
        ):
            self.assertIn(f"id: {field_id}", form)
            self.assertIn(f"label: {heading}", form)

        self.assertIn("id: ci_provider", form)
        self.assertIn(f"label: {CI_PROVIDER_FIELD_HEADING}", form)
        ci_section = form[form.index("id: ci_provider") :]
        next_field = ci_section.find("\n  - type:")
        ci_section = ci_section[:next_field]
        ci_positions = [
            ci_section.index(f"        - {answer}")
            for _, answer in CI_PROVIDER_OPTIONS
        ]
        self.assertEqual(ci_positions, sorted(ci_positions))

    def test_build_funnel_tracks_revenue_stages_and_label_drift(self) -> None:
        payload = json.loads(FIXTURE.read_text(encoding="utf-8"))

        report = build_funnel(payload, as_of=date(2026, 7, 10))

        self.assertEqual(report["schema_version"], 7)
        self.assertEqual(report["summary"]["tracked_issues"], 8)
        self.assertEqual(report["summary"]["ignored_issues"], 1)
        self.assertEqual(report["summary"]["booked_pilots"], 3)
        self.assertEqual(report["summary"]["booked_revenue_usd"], 897)
        self.assertEqual(report["summary"]["remaining_pilots"], 0)
        self.assertEqual(report["summary"]["target_attainment_percent"], 100.0)
        self.assertEqual(report["summary"]["annual_conversions"], 1)
        self.assertEqual(report["summary"]["lost_pilots"], 1)
        self.assertEqual(report["summary"]["stale_deals"], 2)
        self.assertEqual(report["summary"]["sales_actions"], 2)
        self.assertEqual(report["summary"]["attributed_issues"], 8)
        self.assertEqual(report["summary"]["unattributed_issues"], 0)
        self.assertEqual(report["summary"]["unknown_source_issues"], 0)
        self.assertEqual(report["summary"]["ready_issues"], 3)
        self.assertEqual(report["summary"]["needs_approval_issues"], 3)
        self.assertEqual(report["summary"]["exploring_issues"], 2)
        self.assertEqual(report["summary"]["missing_readiness_issues"], 0)
        self.assertEqual(report["summary"]["unknown_readiness_issues"], 0)
        self.assertEqual(
            report["summary"]["declared_decision_criterion_issues"], 8
        )
        self.assertEqual(
            report["summary"]["missing_decision_criterion_issues"], 0
        )
        self.assertEqual(
            report["summary"]["unknown_decision_criterion_issues"], 0
        )
        self.assertEqual(report["summary"]["complete_qualification_issues"], 0)
        self.assertEqual(report["summary"]["target_profile_issues"], 0)
        self.assertEqual(report["summary"]["qualification_review_issues"], 8)
        self.assertEqual(report["summary"]["subset_scope_issues"], 0)
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
            [deal["number"] for deal in report["sales_queue"]["deals"]],
            [1, 2],
        )
        self.assertEqual(
            report["sales_queue"]["deals"][0]["next_action"],
            "Qualify the team and send the $299 pilot terms.",
        )
        self.assertEqual(report["sales_queue"]["deals"][0]["priority"], 1)
        self.assertEqual(
            report["sales_queue"]["deals"][0]["decision_criterion"],
            "commercial_fit",
        )
        self.assertEqual(report["sales_queue"]["deals"][1]["priority"], 2)
        self.assertEqual(
            report["by_source"]["github"],
            {
                "deals": 2,
                "qualified_pilots": 2,
                "offered_pilots": 2,
                "booked_pilots": 2,
                "booked_revenue_usd": 598,
                "annual_conversions": 1,
                "lost_pilots": 0,
            },
        )
        self.assertEqual(report["by_source"]["website"]["deals"], 1)
        self.assertEqual(report["by_source"]["outreach"]["booked_pilots"], 1)
        self.assertEqual(report["by_source"]["referral"]["booked_pilots"], 0)
        self.assertEqual(report["by_source"]["social"]["lost_pilots"], 1)
        self.assertEqual(report["deals"][0]["source"], "website")
        self.assertEqual(report["follow_up"]["deals"][0]["source"], "website")
        self.assertEqual(
            report["follow_up"]["deals"][0]["purchase_readiness"], "ready"
        )
        self.assertEqual(
            report["follow_up"]["deals"][1]["purchase_readiness"],
            "needs_approval",
        )
        self.assertEqual(
            report["by_readiness"]["ready"],
            {
                "deals": 3,
                "qualified_pilots": 2,
                "offered_pilots": 2,
                "booked_pilots": 2,
                "booked_revenue_usd": 598,
                "annual_conversions": 1,
                "lost_pilots": 0,
            },
        )
        self.assertEqual(
            report["by_readiness"]["needs_approval"],
            {
                "deals": 3,
                "qualified_pilots": 3,
                "offered_pilots": 2,
                "booked_pilots": 1,
                "booked_revenue_usd": 299,
                "annual_conversions": 0,
                "lost_pilots": 0,
            },
        )
        self.assertEqual(report["by_readiness"]["exploring"]["deals"], 2)
        self.assertEqual(report["by_readiness"]["exploring"]["lost_pilots"], 1)
        self.assertEqual(
            report["by_decision_criterion"]["policy_fit"]["booked_pilots"],
            1,
        )
        self.assertEqual(
            report["by_decision_criterion"]["rollout_fit"]["booked_pilots"],
            0,
        )
        self.assertEqual(
            report["by_decision_criterion"]["privacy_security"][
                "annual_conversions"
            ],
            1,
        )
        self.assertEqual(
            sum(
                totals["deals"]
                for totals in report["by_decision_criterion"].values()
            ),
            report["summary"]["tracked_issues"],
        )
        self.assertEqual(
            sum(totals["deals"] for totals in report["by_readiness"].values()),
            report["summary"]["tracked_issues"],
        )
        self.assertEqual(report["deals"][0]["purchase_readiness"], "ready")
        active_drift = next(
            deal for deal in report["deals"] if deal["number"] == 4
        )
        self.assertEqual(active_drift["stage"], "active")
        self.assertFalse(active_drift["booked"])
        self.assertEqual(
            report,
            build_funnel(list(reversed(payload)), as_of=date(2026, 7, 10)),
        )

    def test_terminal_conflict_is_booked_without_resolved_outcome_totals(
        self,
    ) -> None:
        payload = [
            {
                "number": 101,
                "title": "Paid pilot with conflicting terminal labels",
                "url": "https://github.com/example/repo/issues/101",
                "state": "CLOSED",
                "updatedAt": "2026-07-10T12:00:00Z",
                "labels": [
                    {"name": label}
                    for label in (
                        "pilot-lead",
                        "pilot-qualified",
                        "pilot-offered",
                        "pilot-paid",
                        "pilot-active",
                        "pilot-converted",
                        "pilot-lost",
                    )
                ],
                "body": (
                    "### How did you hear about Repo Scout?\n\n"
                    "Direct outreach\n\n"
                    "### Purchase readiness\n\n"
                    "Ready to purchase the $299 pilot\n\n"
                    "### Primary purchase criterion\n\n"
                    "Supports our required repository standards"
                ),
            }
        ]

        report = build_funnel(payload, as_of=date(2026, 7, 10))

        self.assertEqual(report["deals"][0]["stage"], "conflict")
        self.assertTrue(report["deals"][0]["booked"])
        self.assertEqual(report["summary"]["booked_pilots"], 1)
        self.assertEqual(report["summary"]["booked_revenue_usd"], 299)
        self.assertEqual(
            [warning["kind"] for warning in report["warnings"]],
            ["conflicting_terminal_labels"],
        )
        self.assertEqual(report["summary"]["annual_conversions"], 0)
        self.assertEqual(report["summary"]["lost_pilots"], 0)
        for segment, key in (
            (report["by_source"], "outreach"),
            (report["by_readiness"], "ready"),
            (report["by_decision_criterion"], "policy_fit"),
        ):
            self.assertEqual(segment[key]["booked_pilots"], 1)
            self.assertEqual(segment[key]["booked_revenue_usd"], 299)
            self.assertEqual(segment[key]["annual_conversions"], 0)
            self.assertEqual(segment[key]["lost_pilots"], 0)

    def test_classifies_application_scope_without_exposing_standard_text(self) -> None:
        common = (
            "### How did you hear about Repo Scout?\n\nRepo Scout website\n\n"
            "### Purchase readiness\n\nReady to purchase the $299 pilot\n\n"
            "### Primary purchase criterion\n\n"
            "Works across our repositories and CI"
        )

        def issue(
            number: int,
            *,
            team_size: str,
            repository_count: str,
            ci_provider: str = "GitHub Actions",
            standard: str = "Use one reviewed repository policy.",
        ) -> dict[str, object]:
            return {
                "number": number,
                "title": f"Pilot {number}",
                "state": "OPEN",
                "updatedAt": "2026-07-13T00:00:00Z",
                "labels": ["pilot-lead"],
                "body": (
                    f"### Team size\n\n{team_size}\n\n"
                    f"### Repository count\n\n{repository_count}\n\n"
                    f"### CI provider\n\n{ci_provider}\n\n"
                    f"### Repository standard to enforce\n\n{standard}\n\n"
                    f"{common}"
                ),
            }

        report = build_funnel(
            [
                issue(1, team_size="12", repository_count="6"),
                issue(2, team_size="2", repository_count="1"),
                issue(
                    3,
                    team_size="20",
                    repository_count="15",
                    ci_provider="GitLab CI",
                ),
                issue(4, team_size="about ten", repository_count="_No response_"),
            ],
            as_of=date(2026, 7, 13),
        )

        self.assertEqual(report["summary"]["complete_qualification_issues"], 3)
        self.assertEqual(report["summary"]["target_profile_issues"], 2)
        self.assertEqual(report["summary"]["qualification_review_issues"], 2)
        self.assertEqual(report["summary"]["subset_scope_issues"], 1)
        self.assertEqual(
            [deal["qualification"]["status"] for deal in report["deals"]],
            ["target", "outside_target", "target", "incomplete"],
        )
        self.assertEqual(
            report["deals"][1]["qualification"]["review_reasons"],
            ["team_size_outside_target", "single_repository"],
        )
        self.assertEqual(
            report["deals"][2]["qualification"]["ci_provider"], "gitlab_ci"
        )
        self.assertEqual(
            report["deals"][2]["qualification"]["pilot_repository_scope"],
            "subset_required",
        )
        self.assertEqual(
            report["deals"][3]["qualification"]["review_reasons"],
            ["invalid_team_size", "missing_repository_count"],
        )
        serialized = json.dumps(report)
        self.assertNotIn("Use one reviewed repository policy.", serialized)
        self.assertIn(
            "Qualification scope: 3 complete / 2 target / 2 review / "
            "1 subset required",
            format_funnel(report),
        )

    def test_source_attribution_handles_legacy_unknown_and_ambiguous_answers(
        self,
    ) -> None:
        heading = "### How did you hear about Repo Scout?"
        readiness = "### Purchase readiness"
        criterion = (
            "### Primary purchase criterion\n\n"
            "Supports our required repository standards"
        )
        payload = [
            {
                "number": 1,
                "title": "Paid GitHub lead",
                "state": "OPEN",
                "updatedAt": "2026-07-10T00:00:00Z",
                "body": (
                    f"{heading}\n\nGitHub repository or release\n\n"
                    f"{readiness}\n\nReady to purchase the $299 pilot\n\n"
                    f"{criterion}"
                ),
                "labels": [
                    "pilot-lead",
                    "pilot-qualified",
                    "pilot-offered",
                    "pilot-paid",
                ],
            },
            {
                "number": 2,
                "title": "Legacy lead without source",
                "state": "OPEN",
                "updatedAt": "2026-07-10T00:00:00Z",
                "body": (
                    f"{readiness}\n\nExploring before requesting budget\n\n"
                    f"{criterion}"
                ),
                "labels": ["pilot-lead"],
            },
            {
                "number": 3,
                "title": "Edited unknown source",
                "state": "OPEN",
                "updatedAt": "2026-07-10T00:00:00Z",
                "body": (
                    f"{heading}\n\nConference\n\n{readiness}\n\n"
                    f"Need internal approval for $299\n\n{criterion}"
                ),
                "labels": ["pilot-lead", "pilot-qualified"],
            },
            {
                "number": 4,
                "title": "Duplicate source headings",
                "state": "CLOSED",
                "updatedAt": "2026-07-10T00:00:00Z",
                "body": (
                    f"{heading}\n\nSearch\n\n{heading}\n\nDirect outreach\n\n"
                    f"{readiness}\n\nExploring before requesting budget\n\n"
                    f"{criterion}"
                ),
                "labels": ["pilot-lead", "pilot-lost"],
            },
        ]

        report = build_funnel(
            payload,
            pilot_price_usd=400,
            as_of=date(2026, 7, 10),
        )

        self.assertEqual(report["summary"]["attributed_issues"], 1)
        self.assertEqual(report["summary"]["unattributed_issues"], 1)
        self.assertEqual(report["summary"]["unknown_source_issues"], 2)
        self.assertEqual(
            [warning["kind"] for warning in report["warnings"]],
            [
                "missing_lead_source",
                "unknown_lead_source",
                "ambiguous_lead_source",
            ],
        )
        self.assertEqual(report["by_source"]["github"]["booked_revenue_usd"], 400)
        self.assertEqual(report["by_source"]["unattributed"]["deals"], 1)
        self.assertEqual(report["by_source"]["unknown"]["deals"], 2)
        self.assertEqual(report["by_source"]["unknown"]["qualified_pilots"], 1)
        self.assertEqual(report["by_source"]["unknown"]["lost_pilots"], 1)
        self.assertEqual(report["deals"][1]["source"], "unattributed")
        self.assertIsNone(report["deals"][1]["source_raw"])
        self.assertEqual(report["deals"][2]["source_raw"], "Conference")
        self.assertEqual(
            report["deals"][3]["source_raw"],
            "Search; Direct outreach",
        )
        text_report = format_funnel(report)
        self.assertIn("Attribution: 1 attributed / 1 missing / 2 unknown", text_report)
        self.assertIn(
            "github: 1 deal, 1 qualified, 1 offered, 1 booked ($400)",
            text_report,
        )

    def test_purchase_readiness_handles_missing_unknown_and_ambiguous_answers(
        self,
    ) -> None:
        source = "### How did you hear about Repo Scout?\n\nRepo Scout website"
        heading = "### Purchase readiness"
        criterion = (
            "### Primary purchase criterion\n\n"
            "Supports our required repository standards"
        )
        payload = [
            {
                "number": 1,
                "title": "Ready buyer",
                "state": "OPEN",
                "updatedAt": "2026-07-10T00:00:00Z",
                "body": (
                    f"{source}\n\n{heading}\n\nReady to purchase the $299 pilot"
                    f"\n\n{criterion}"
                ),
                "labels": ["pilot-lead"],
            },
            {
                "number": 2,
                "title": "Legacy request",
                "state": "OPEN",
                "updatedAt": "2026-07-10T00:00:00Z",
                "body": f"{source}\n\n{criterion}",
                "labels": ["pilot-lead"],
            },
            {
                "number": 3,
                "title": "Edited answer",
                "state": "OPEN",
                "updatedAt": "2026-07-10T00:00:00Z",
                "body": f"{source}\n\n{heading}\n\nBudget maybe\n\n{criterion}",
                "labels": ["pilot-lead"],
            },
            {
                "number": 4,
                "title": "Duplicate readiness headings",
                "state": "OPEN",
                "updatedAt": "2026-07-10T00:00:00Z",
                "body": (
                    f"{source}\n\n{heading}\n\nNeed internal approval for $299\n\n"
                    f"{heading}\n\nExploring before requesting budget\n\n"
                    f"{criterion}"
                ),
                "labels": ["pilot-lead"],
            },
            {
                "number": 5,
                "title": "Generated no-response answer",
                "state": "OPEN",
                "updatedAt": "2026-07-10T00:00:00Z",
                "body": (
                    f"{source}\n\n{heading}\n\n_No response_\n\n{criterion}"
                ),
                "labels": ["pilot-lead"],
            },
        ]

        report = build_funnel(payload, as_of=date(2026, 7, 10))

        self.assertEqual(report["summary"]["ready_issues"], 1)
        self.assertEqual(report["summary"]["missing_readiness_issues"], 2)
        self.assertEqual(report["summary"]["unknown_readiness_issues"], 2)
        self.assertEqual(
            [warning["kind"] for warning in report["warnings"]],
            [
                "missing_purchase_readiness",
                "unknown_purchase_readiness",
                "ambiguous_purchase_readiness",
                "missing_purchase_readiness",
            ],
        )
        self.assertEqual(report["by_readiness"]["ready"]["deals"], 1)
        self.assertEqual(report["by_readiness"]["unattributed"]["deals"], 2)
        self.assertEqual(report["by_readiness"]["unknown"]["deals"], 2)
        self.assertIsNone(report["deals"][1]["purchase_readiness_raw"])
        self.assertEqual(report["deals"][2]["purchase_readiness_raw"], "Budget maybe")
        self.assertEqual(
            report["deals"][3]["purchase_readiness_raw"],
            "Need internal approval for $299; Exploring before requesting budget",
        )
        text_report = format_funnel(report)
        self.assertIn(
            "Purchase readiness: 1 ready / 0 need approval / 0 exploring / "
            "2 missing / 2 unknown",
            text_report,
        )

    def test_decision_criterion_handles_missing_unknown_and_ambiguous_answers(
        self,
    ) -> None:
        common = (
            "### How did you hear about Repo Scout?\n\nRepo Scout website\n\n"
            "### Purchase readiness\n\nExploring before requesting budget"
        )
        heading = "### Primary purchase criterion"
        payload = [
            {
                "number": 1,
                "title": "Policy-fit buyer",
                "state": "OPEN",
                "updatedAt": "2026-07-10T00:00:00Z",
                "body": (
                    f"{common}\n\n{heading}\n\n"
                    "Supports our required repository standards"
                ),
                "labels": ["pilot-lead", "pilot-qualified"],
            },
            {
                "number": 2,
                "title": "Legacy request",
                "state": "OPEN",
                "updatedAt": "2026-07-10T00:00:00Z",
                "body": common,
                "labels": ["pilot-lead"],
            },
            {
                "number": 3,
                "title": "Edited criterion",
                "state": "OPEN",
                "updatedAt": "2026-07-10T00:00:00Z",
                "body": f"{common}\n\n{heading}\n\nNeeds magic",
                "labels": ["pilot-lead"],
            },
            {
                "number": 4,
                "title": "Duplicate criterion headings",
                "state": "OPEN",
                "updatedAt": "2026-07-10T00:00:00Z",
                "body": (
                    f"{common}\n\n{heading}\n\n"
                    "Works across our repositories and CI\n\n"
                    f"{heading}\n\nThe $299 scope and price fit"
                ),
                "labels": ["pilot-lead"],
            },
            {
                "number": 5,
                "title": "Generated no-response criterion",
                "state": "OPEN",
                "updatedAt": "2026-07-10T00:00:00Z",
                "body": f"{common}\n\n{heading}\n\n_No response_",
                "labels": ["pilot-lead"],
            },
        ]

        report = build_funnel(payload, as_of=date(2026, 7, 10))

        self.assertEqual(
            report["summary"]["declared_decision_criterion_issues"], 1
        )
        self.assertEqual(
            report["summary"]["missing_decision_criterion_issues"], 2
        )
        self.assertEqual(
            report["summary"]["unknown_decision_criterion_issues"], 2
        )
        self.assertEqual(
            [warning["kind"] for warning in report["warnings"]],
            [
                "missing_decision_criterion",
                "unknown_decision_criterion",
                "ambiguous_decision_criterion",
                "missing_decision_criterion",
            ],
        )
        self.assertEqual(
            report["by_decision_criterion"]["policy_fit"][
                "qualified_pilots"
            ],
            1,
        )
        self.assertEqual(
            report["by_decision_criterion"]["unattributed"]["deals"], 2
        )
        self.assertEqual(
            report["by_decision_criterion"]["unknown"]["deals"], 2
        )
        self.assertEqual(report["deals"][0]["decision_criterion"], "policy_fit")
        self.assertEqual(
            report["deals"][0]["decision_criterion_raw"],
            "Supports our required repository standards",
        )
        self.assertIsNone(report["deals"][1]["decision_criterion_raw"])
        self.assertEqual(
            report["deals"][3]["decision_criterion_raw"],
            "Works across our repositories and CI; The $299 scope and price fit",
        )
        self.assertIn(
            "Purchase criteria: 1 declared / 2 missing / 2 unknown",
            format_funnel(report),
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
        self.assertEqual(report["summary"]["booked_revenue_usd"], 1200)
        self.assertEqual(report["summary"]["remaining_pilots"], 2)
        self.assertEqual(report["summary"]["remaining_revenue_usd"], 800)
        self.assertEqual(report["summary"]["stale_deals"], 0)
        self.assertIn(
            "$400 pilot terms",
            report["sales_queue"]["deals"][0]["next_action"],
        )

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
        self.assertIn("Sources:\n  none", stdout.getvalue())
        self.assertIn("Purchase readiness:\n  none", stdout.getvalue())
        self.assertIn("Purchase criteria:\n  none", stdout.getvalue())
        self.assertIn("Sales actions: 0 open pre-payment deals", stdout.getvalue())
        self.assertIn("Sales queue:\n  none", stdout.getvalue())
        self.assertIn("Warnings:\n  none", stdout.getvalue())

    def test_sales_queue_prioritizes_readiness_stage_and_age(self) -> None:
        source = "### How did you hear about Repo Scout?\n\nRepo Scout website"
        criterion = (
            "### Primary purchase criterion\n\n"
            "Works across our repositories and CI"
        )

        def issue(
            number: int,
            *,
            stage_labels: list[str],
            readiness: str,
            updated_at: str,
            state: str = "OPEN",
        ) -> dict[str, object]:
            return {
                "number": number,
                "title": f"Pilot {number}",
                "state": state,
                "updatedAt": updated_at,
                "body": (
                    f"{source}\n\n### Purchase readiness\n\n{readiness}\n\n"
                    f"{criterion}"
                ),
                "labels": stage_labels,
            }

        payload = [
            issue(
                1,
                stage_labels=["pilot-lead"],
                readiness="Ready to purchase the $299 pilot",
                updated_at="2026-07-01T00:00:00Z",
            ),
            issue(
                2,
                stage_labels=["pilot-lead", "pilot-qualified", "pilot-offered"],
                readiness="Ready to purchase the $299 pilot",
                updated_at="2026-07-09T00:00:00Z",
            ),
            issue(
                3,
                stage_labels=["pilot-lead", "pilot-qualified"],
                readiness="Need internal approval for $299",
                updated_at="2026-07-08T00:00:00Z",
            ),
            issue(
                8,
                stage_labels=["pilot-lead", "pilot-qualified", "pilot-offered"],
                readiness="Ready to purchase the $299 pilot",
                updated_at="2026-07-05T00:00:00Z",
            ),
            issue(
                4,
                stage_labels=["pilot-lead"],
                readiness="Exploring before requesting budget",
                updated_at="2026-07-07T00:00:00Z",
            ),
            issue(
                5,
                stage_labels=["pilot-lead"],
                readiness="Edited answer",
                updated_at="2026-07-06T00:00:00Z",
            ),
            issue(
                6,
                stage_labels=["pilot-lead", "pilot-qualified", "pilot-offered"],
                readiness="Ready to purchase the $299 pilot",
                updated_at="2026-07-01T00:00:00Z",
                state="CLOSED",
            ),
            issue(
                7,
                stage_labels=[
                    "pilot-lead",
                    "pilot-qualified",
                    "pilot-offered",
                    "pilot-paid",
                ],
                readiness="Ready to purchase the $299 pilot",
                updated_at="2026-07-01T00:00:00Z",
            ),
        ]

        report = build_funnel(payload, as_of=date(2026, 7, 10))
        queue = report["sales_queue"]["deals"]

        self.assertEqual([deal["number"] for deal in queue], [8, 2, 1, 3, 4, 5])
        self.assertEqual(
            [deal["priority"] for deal in queue], [1, 1, 1, 2, 3, 4]
        )
        self.assertEqual(
            [deal["next_action"] for deal in queue],
            [
                "Confirm the purchase and payment path.",
                "Confirm the purchase and payment path.",
                "Qualify the team and send the $299 pilot terms.",
                "Send an internal approval brief.",
                "Qualify the repository standard and evidence need.",
                "Clarify purchase readiness before advancing.",
            ],
        )
        self.assertIsNone(report["deals"][5]["next_action"])
        self.assertIsNone(report["deals"][6]["sales_priority"])
        text_report = format_funnel(report)
        self.assertIn("Sales actions: 6 open pre-payment deals", text_report)
        self.assertIn(
            "#2 [P1, offered, ready, rollout_fit] "
            "Confirm the purchase and payment path.",
            text_report,
        )

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
        for issue in payload:
            issue["body"] = (
                "### How did you hear about Repo Scout?\n\nRepo Scout website\n\n"
                "### Purchase readiness\n\nNeed internal approval for $299\n\n"
                "### Primary purchase criterion\n\n"
                "Fits our implementation capacity and timing"
            )

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
            "#13 [offered, needs_approval, 7 days] UTC boundary is stale "
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

        with self.assertRaisesRegex(
            FunnelInputError, "body must be a string or null"
        ):
            build_funnel(
                [
                    {
                        "number": 1,
                        "title": "Pilot",
                        "state": "OPEN",
                        "body": 42,
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
        self.assertEqual(json.loads(completed.stdout)["summary"]["booked_pilots"], 3)


if __name__ == "__main__":
    unittest.main()
