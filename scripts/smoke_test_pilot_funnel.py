from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
from typing import Any, Mapping, Sequence


PILOT_PRICE_USD = 299
TARGET_PILOTS = 3
TARGET_REVENUE_USD = 897
PRIVATE_STANDARD = "Require private service ownership evidence."
INJECTED_REVENUE_MARKER = "Revenue: $999 booked / $897 target"
INJECTED_WARNING_MARKER = "Revenue: $998 booked / $897 target"
INJECTED_URL_MARKER = "Revenue: $997 booked / $897 target"


class SmokeTestError(RuntimeError):
    """Raised when installed commercial reporting violates its release contract."""


def verify_pilot_funnel(
    python: str | Path,
    *,
    command_directory: str | Path | None = None,
    environment: Mapping[str, str] | None = None,
) -> tuple[str, ...]:
    python_command = str(Path(python))
    pilot_command, distribution_command, growth_command = _commercial_commands(
        python_command,
        command_directory=command_directory,
    )
    checked: list[str] = []

    with TemporaryDirectory() as tmp:
        issue_export = Path(tmp) / "pilot-issues.json"
        journey_issues = [
            _issue(
                number=101,
                title="Website team awaiting qualification",
                source="Repo Scout website",
                readiness="Need internal approval for $299",
                criterion="Works across our repositories and CI",
                labels=("pilot-lead",),
            ),
            _issue(
                number=102,
                title="Outreach team with recorded payment",
                source="Direct outreach",
                readiness="Ready to purchase the $299 pilot",
                criterion="The $299 scope and price fit",
                labels=(
                    "pilot-lead",
                    "pilot-qualified",
                    "pilot-offered",
                    "pilot-paid",
                ),
            ),
        ]
        issue_export.write_text(
            json.dumps(journey_issues, indent=2),
            encoding="utf-8",
        )

        report = _json_report(
            pilot_command,
            issue_export,
            environment=environment,
        )
        _require(report.get("schema_version") == 10, "pilot schema changed")
        _require(
            report.get("pricing")
            == {
                "pilot_price_usd": PILOT_PRICE_USD,
                "target_pilots": TARGET_PILOTS,
                "target_revenue_usd": TARGET_REVENUE_USD,
            },
            "default commercial target changed",
        )
        summary = report.get("summary", {})
        _require(summary.get("booked_pilots") == 1, "payment was not booked")
        _require(
            summary.get("activated_pilots") == 0,
            "payment was incorrectly treated as activation",
        )
        _require(
            summary.get("booked_revenue_usd") == PILOT_PRICE_USD,
            "booked revenue changed",
        )
        _require(summary.get("remaining_pilots") == 2, "remaining pilots changed")
        _require(
            summary.get("remaining_revenue_usd") == 598,
            "remaining revenue changed",
        )
        _require(
            summary.get("target_attainment_percent") == 33.3,
            "target attainment changed",
        )
        checked.append("commercial-totals")

        _require(
            report.get("by_stage", {}).get("lead") == 1,
            "lead stage was not kept distinct from payment",
        )
        _require(
            report.get("by_stage", {}).get("paid") == 1,
            "paid stage was not counted",
        )
        website = report.get("by_source", {}).get("website", {})
        outreach = report.get("by_source", {}).get("outreach", {})
        _require(
            website.get("qualified_pilots") == 0
            and website.get("offered_pilots") == 0
            and website.get("booked_pilots") == 0,
            "website lead progression changed",
        )
        _require(
            outreach.get("qualified_pilots") == 1
            and outreach.get("offered_pilots") == 1
            and outreach.get("booked_pilots") == 1
            and outreach.get("booked_revenue_usd") == PILOT_PRICE_USD,
            "outreach payment attribution changed",
        )
        _require(
            website.get("activated_pilots") == 0
            and outreach.get("activated_pilots") == 0,
            "pre-activation source attribution changed",
        )
        _require(
            summary.get("target_profile_issues") == 2,
            "target-profile qualification changed",
        )
        _require(summary.get("sales_actions") == 1, "sales queue changed")
        _require(not report.get("warnings"), "valid pilot export emitted warnings")
        _require(
            PRIVATE_STANDARD not in json.dumps(report, sort_keys=True),
            "repository-standard free text leaked into the report",
        )
        deals = report.get("deals", [])
        _require(
            len(deals) == 2
            and all(type(deal.get("qualified")) is bool for deal in deals)
            and all(type(deal.get("offered")) is bool for deal in deals)
            and all(type(deal.get("activated")) is bool for deal in deals),
            "detailed progression evidence changed",
        )
        _require(
            [
                (
                    deal.get("number"),
                    deal["qualified"],
                    deal["offered"],
                    deal["activated"],
                )
                for deal in deals
            ]
            == [
                (101, False, False, False),
                (102, True, True, False),
            ],
            "detailed progression does not match lead and paid stages",
        )
        checked.append("qualified-segmentation")
        checked.append("payment-backed-activation")

        text_report = _run(
            pilot_command,
            issue_export,
            output_format="text",
            environment=environment,
            expected_exit_code=0,
        ).stdout
        for expected_line in (
            "Pilots: 1 booked / 3 target",
            "Activated pilots: 0",
            "Revenue: $299 booked / $897 target",
            "Remaining: 2 pilots / $598",
            "Qualification scope: 2 complete / 2 target / 0 review / "
            "0 subset required",
            "Sales actions: 1 open pre-payment deal",
            "outreach: 1 deal, 1 qualified, 1 offered, 1 booked ($299), "
            "0 activated",
        ):
            _require(expected_line in text_report, "text pilot totals changed")
        _require(
            PRIVATE_STANDARD not in text_report,
            "repository-standard free text leaked into text output",
        )
        checked.append("operator-text")

        issue_export.write_text(
            json.dumps(
                [
                    _issue(
                        number=106,
                        title="Non-GitHub team awaiting integration decision",
                        source="Repo Scout website",
                        readiness="Ready to purchase the $299 pilot",
                        criterion="Works across our repositories and CI",
                        labels=(
                            "pilot-lead",
                            "pilot-qualified",
                            "pilot-offered",
                        ),
                        ci_provider="GitLab CI",
                    )
                ],
                indent=2,
            ),
            encoding="utf-8",
        )
        integration_report = _json_report(
            pilot_command,
            issue_export,
            environment=environment,
        )
        integration_queue = integration_report.get("sales_queue", {}).get(
            "deals", []
        )
        _require(
            len(integration_queue) == 1,
            "non-GitHub pre-payment request left the sales queue",
        )
        integration_action = integration_queue[0].get("next_action")
        _require(
            integration_action
            == (
                "Record the private CI integration decision before any "
                "further pilot terms or payment action."
            ),
            "non-GitHub request was not gated on an integration decision",
        )
        _require(
            "Confirm the purchase and payment path."
            not in json.dumps(integration_report, sort_keys=True),
            "non-GitHub request retained a payment-advancing action",
        )
        checked.append("ci-integration-payment-gate")

        issue_export.write_text(
            json.dumps(
                [
                    _issue(
                        number=107,
                        title="Out-of-profile team awaiting scope review",
                        source="Repo Scout website",
                        readiness="Ready to purchase the $299 pilot",
                        criterion="Works across our repositories and CI",
                        labels=(
                            "pilot-lead",
                            "pilot-qualified",
                            "pilot-offered",
                        ),
                        team_size=2,
                        repository_count=1,
                    )
                ],
                indent=2,
            ),
            encoding="utf-8",
        )
        qualification_report = _json_report(
            pilot_command,
            issue_export,
            environment=environment,
        )
        qualification_queue = qualification_report.get(
            "sales_queue", {}
        ).get("deals", [])
        _require(
            len(qualification_queue) == 1,
            "out-of-profile pre-payment request left the sales queue",
        )
        _require(
            qualification_queue[0].get("next_action")
            == (
                "Review the pilot qualification scope before any further "
                "pilot terms or payment action."
            ),
            "out-of-profile request was not gated on qualification review",
        )
        _require(
            "Confirm the purchase and payment path."
            not in json.dumps(qualification_report, sort_keys=True),
            "out-of-profile request retained a payment-advancing action",
        )
        checked.append("qualification-scope-payment-gate")

        pilot_report = Path(tmp) / "pilot-report.json"
        baseline_release_export = Path(tmp) / "baseline-releases.json"
        current_release_export = Path(tmp) / "current-releases.json"
        baseline_distribution_report = Path(tmp) / "baseline-distribution.json"
        distribution_report = Path(tmp) / "distribution-report.json"
        pilot_report.write_text(
            json.dumps(report, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        baseline_release_export.write_text(
            json.dumps(_release_export(portable=3, wheel=5), indent=2),
            encoding="utf-8",
        )
        current_release_export.write_text(
            json.dumps(_release_export(portable=5, wheel=9), indent=2),
            encoding="utf-8",
        )
        baseline_distribution = _distribution_json_report(
            distribution_command,
            baseline_release_export,
            baseline=None,
            environment=environment,
        )
        baseline_distribution_report.write_text(
            json.dumps(baseline_distribution, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        distribution = _distribution_json_report(
            distribution_command,
            current_release_export,
            baseline=baseline_distribution_report,
            environment=environment,
        )
        distribution_report.write_text(
            json.dumps(distribution, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        _require(
            distribution.get("schema_version") == 2,
            "distribution schema changed",
        )
        distribution_summary = distribution.get("summary", {})
        _require(
            distribution_summary.get("complete_releases") == 1,
            "release artifact contract was not complete",
        )
        _require(
            distribution_summary.get("warning_count") == 0,
            "valid release evidence emitted warnings",
        )
        _require(
            distribution.get("latest", {}).get("contract", {}).get("complete")
            is True,
            "latest release artifact contract changed",
        )
        distribution_change = distribution.get("change", {})
        _require(
            (
                distribution_change.get("primary_artifact_downloads_delta"),
                distribution_change.get("portable_downloads_delta"),
                distribution_change.get("wheel_downloads_delta"),
            )
            == (6, 2, 4),
            "installed distribution movement changed",
        )
        distribution_note = distribution.get("measurement_note", "")
        _require(
            "CI jobs" in distribution_note
            and "not unique installs" in distribution_note,
            "distribution report lost its request-count boundary",
        )
        _require(
            "pilot requests, or revenue" in distribution_note,
            "distribution report lost its commercial boundary",
        )
        checked.append("distribution-evidence")

        duplicate_release_export = Path(tmp) / "duplicate-release-export.json"
        duplicate_release_export.write_text(
            """[
              {
                "assets": [
                  {
                    "name": "repo-scout-0.3.51.pyz",
                    "download_count": 1,
                    "download_count": 999
                  }
                ]
              }
            ]""",
            encoding="utf-8",
        )
        duplicate_release = _run_distribution(
            distribution_command,
            duplicate_release_export,
            baseline=None,
            output_format="json",
            environment=environment,
            expected_exit_code=2,
        )
        _require(
            not duplicate_release.stdout,
            "duplicate release key emitted a distribution report",
        )
        _require(
            duplicate_release.stderr
            == (
                "repo-scout-distribution: release export contains duplicate "
                'JSON key: "download_count"\n'
            ),
            "duplicate release key did not produce its controlled error",
        )

        duplicate_baseline_report = (
            Path(tmp) / "duplicate-distribution-baseline.json"
        )
        duplicate_baseline_report.write_text(
            '{"schema_version": 2, "schema_version": 2}',
            encoding="utf-8",
        )
        duplicate_baseline = _run_distribution(
            distribution_command,
            current_release_export,
            baseline=duplicate_baseline_report,
            output_format="json",
            environment=environment,
            expected_exit_code=2,
        )
        _require(
            not duplicate_baseline.stdout,
            "duplicate baseline key emitted a distribution report",
        )
        _require(
            duplicate_baseline.stderr
            == (
                "repo-scout-distribution: baseline report contains duplicate "
                'JSON key: "schema_version"\n'
            ),
            "duplicate baseline key did not produce its controlled error",
        )
        checked.append("duplicate-distribution-keys-rejected")

        unsafe_asset_name = (
            "notes.txt\n"
            "Primary artifact downloads: 999 total / 999 portable / 0 wheel"
            "\x1b[31m\u202e"
        )
        unsafe_release_export = Path(tmp) / "unsafe-release-export.json"
        unsafe_release_payload = _release_export(portable=5, wheel=9)
        unsafe_release_payload[0]["assets"][0]["name"] = unsafe_asset_name
        unsafe_release_export.write_text(
            json.dumps(unsafe_release_payload, ensure_ascii=False),
            encoding="utf-8",
        )
        unsafe_release_bytes = unsafe_release_export.read_bytes()
        unsafe_release = _run_distribution(
            distribution_command,
            unsafe_release_export,
            baseline=None,
            output_format="text",
            environment=environment,
            expected_exit_code=2,
        )
        _require(
            not unsafe_release.stdout,
            "unsafe release asset name emitted a distribution report",
        )
        _require(
            unsafe_release.stderr
            == (
                "repo-scout-distribution: release export item "
                "0.assets[0].name must be non-empty printable text\n"
            ),
            "unsafe release asset name did not produce its controlled error",
        )
        _require(
            unsafe_release_export.read_bytes() == unsafe_release_bytes,
            "unsafe release evidence changed during rejection",
        )

        unsafe_baseline_report = Path(tmp) / "unsafe-distribution-baseline.json"
        unsafe_baseline = json.loads(json.dumps(baseline_distribution))
        unsafe_baseline["releases"][0]["assets"][0]["name"] = unsafe_asset_name
        unsafe_baseline_report.write_text(
            json.dumps(unsafe_baseline, ensure_ascii=False),
            encoding="utf-8",
        )
        unsafe_baseline_bytes = unsafe_baseline_report.read_bytes()
        current_release_bytes = current_release_export.read_bytes()
        unsafe_baseline_result = _run_distribution(
            distribution_command,
            current_release_export,
            baseline=unsafe_baseline_report,
            output_format="text",
            environment=environment,
            expected_exit_code=2,
        )
        _require(
            not unsafe_baseline_result.stdout,
            "unsafe baseline asset name emitted a distribution report",
        )
        _require(
            unsafe_baseline_result.stderr
            == (
                "repo-scout-distribution: baseline report release "
                "0.assets[0].name must be non-empty printable text\n"
            ),
            "unsafe baseline asset name did not produce its controlled error",
        )
        _require(
            unsafe_baseline_report.read_bytes() == unsafe_baseline_bytes
            and current_release_export.read_bytes() == current_release_bytes,
            "distribution evidence changed during unsafe baseline rejection",
        )
        checked.append("unsafe-distribution-asset-name-rejected")

        growth = _growth_report(
            growth_command,
            distribution_report,
            pilot_report,
            environment=environment,
        )
        growth_summary = growth.get("summary", {})
        for field, expected in (
            ("tracked_pilot_requests", 2),
            ("attributed_pilot_requests", 2),
            ("qualified_pilots", 1),
            ("offered_pilots", 1),
            ("booked_pilots", 1),
            ("activated_pilots", 0),
            ("booked_revenue_usd", PILOT_PRICE_USD),
            ("target_revenue_usd", TARGET_REVENUE_USD),
            ("target_profile_requests", 2),
        ):
            _require(
                growth_summary.get(field) == expected,
                f"growth summary {field} changed",
            )
        _require(
            growth_summary.get(
                "activation_attribution_reporting_available"
            )
            is True,
            "growth activation attribution became unavailable",
        )
        growth_sources = {
            row.get("source"): row
            for row in growth.get("sources", [])
            if isinstance(row, dict)
        }
        _require(
            (
                growth_sources.get("website", {}).get("qualified_pilots"),
                growth_sources.get("website", {}).get("offered_pilots"),
                growth_sources.get("website", {}).get("booked_pilots"),
                growth_sources.get("website", {}).get("activated_pilots"),
            )
            == (0, 0, 0, 0),
            "growth website progression changed",
        )
        _require(
            (
                growth_sources.get("outreach", {}).get("qualified_pilots"),
                growth_sources.get("outreach", {}).get("offered_pilots"),
                growth_sources.get("outreach", {}).get("booked_pilots"),
                growth_sources.get("outreach", {}).get("activated_pilots"),
            )
            == (1, 1, 1, 0),
            "growth outreach progression changed",
        )
        growth_readiness = {
            row.get("readiness"): row
            for row in growth.get("purchase_readiness", [])
            if isinstance(row, dict)
        }
        _require(
            (
                growth_readiness.get("needs_approval", {}).get(
                    "qualified_pilots"
                ),
                growth_readiness.get("needs_approval", {}).get(
                    "offered_pilots"
                ),
                growth_readiness.get("ready", {}).get("qualified_pilots"),
                growth_readiness.get("ready", {}).get("offered_pilots"),
            )
            == (0, 0, 1, 1),
            "growth readiness progression changed",
        )
        growth_criteria = {
            row.get("criterion"): row
            for row in growth.get("decision_criteria", [])
            if isinstance(row, dict)
        }
        _require(
            (
                growth_criteria.get("rollout_fit", {}).get(
                    "qualified_pilots"
                ),
                growth_criteria.get("rollout_fit", {}).get("offered_pilots"),
                growth_criteria.get("commercial_fit", {}).get(
                    "qualified_pilots"
                ),
                growth_criteria.get("commercial_fit", {}).get(
                    "offered_pilots"
                ),
            )
            == (0, 0, 1, 1),
            "growth criterion progression changed",
        )
        change = growth.get("distribution_change", {})
        _require(
            (
                change.get("primary_artifact_downloads_delta"),
                change.get("portable_downloads_delta"),
                change.get("wheel_downloads_delta"),
            )
            == (6, 2, 4),
            "growth reach movement changed",
        )
        _require(
            growth.get("bottleneck", {}).get("stage") == "activation",
            "growth bottleneck changed",
        )
        _require(
            growth.get("bottleneck", {}).get("next_action")
            == (
                "Verify the private paid-delivery contract, then complete "
                "first-repository activation or reconcile the lifecycle record "
                "before applying pilot-active."
            ),
            "growth bottleneck did not prioritize paid delivery",
        )
        activation_queue = growth.get("activation_queue")
        _require(
            growth_summary.get("activation_actions") == 1
            and activation_queue
            == [
                {
                    "number": 102,
                    "stage": "paid",
                    "source": "outreach",
                    "purchase_readiness": "ready",
                    "decision_criterion": "commercial_fit",
                    "next_action": (
                        "Verify the private paid-delivery contract and complete "
                        "first-repository activation before applying pilot-active."
                    ),
                }
            ],
            "growth activation queue changed",
        )
        _require(not growth.get("warnings"), "valid growth evidence emitted warnings")
        measurement_note = growth.get("measurement_note", "")
        _require(
            "not unique-user or conversion-rate denominators" in measurement_note,
            "growth report lost its conversion-rate boundary",
        )
        _require(
            "Only paid pilot stages count as revenue" in measurement_note,
            "growth report lost its revenue boundary",
        )
        _require(
            "Activation requires explicit, payment-backed pilot-active evidence"
            in measurement_note,
            "growth report lost its activation boundary",
        )
        _require(
            PRIVATE_STANDARD not in json.dumps(growth, sort_keys=True),
            "repository-standard free text leaked into growth output",
        )
        checked.append("joined-growth-review")
        checked.append("paid-delivery-activation-queue")

        active_issue_export = Path(tmp) / "active-pilot-issues.json"
        active_issues = json.loads(json.dumps(journey_issues))
        active_issues[1]["title"] = "Activated outreach pilot"
        active_issues[1]["labels"].append({"name": "pilot-active"})
        active_issue_export.write_text(
            json.dumps(active_issues, indent=2),
            encoding="utf-8",
        )
        active_report = _json_report(
            pilot_command,
            active_issue_export,
            environment=environment,
        )
        active_deals = active_report.get("deals", [])
        _require(
            active_report.get("summary", {}).get("activated_pilots") == 1
            and len(active_deals) == 2
            and active_deals[1].get("activated") is True,
            "explicit paid activation was not preserved",
        )
        _require(
            active_report.get("by_source", {})
            .get("outreach", {})
            .get("activated_pilots")
            == 1
            and active_report.get("by_readiness", {})
            .get("ready", {})
            .get("activated_pilots")
            == 1
            and active_report.get("by_decision_criterion", {})
            .get("commercial_fit", {})
            .get("activated_pilots")
            == 1,
            "explicit activation attribution was not preserved",
        )
        active_pilot_report = Path(tmp) / "active-pilot-report.json"
        active_pilot_report.write_text(
            json.dumps(active_report, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        active_growth = _growth_report(
            growth_command,
            distribution_report,
            active_pilot_report,
            environment=environment,
        )
        _require(
            active_growth.get("bottleneck", {}).get("stage") == "pilot_target",
            "activation evidence did not reopen the founding-pilot target",
        )
        _require(
            active_growth.get("summary", {}).get("activation_actions") == 0
            and active_growth.get("activation_queue") == [],
            "completed activation remained in the delivery queue",
        )
        _require(
            next(
                row
                for row in active_growth.get("sources", [])
                if row.get("source") == "outreach"
            ).get("activated_pilots")
            == 1,
            "growth output lost source activation attribution",
        )
        checked.append("payment-backed-activation-transition")

        invalid_progression = json.loads(json.dumps(report))
        invalid_progression["deals"][0]["qualified"] = True
        invalid_progression_report = (
            Path(tmp) / "invalid-progression-pilot-report.json"
        )
        invalid_progression_report.write_text(
            json.dumps(invalid_progression, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        rejected_progression = _run_growth(
            growth_command,
            distribution_report,
            invalid_progression_report,
            output_format="json",
            environment=environment,
            expected_exit_code=2,
        )
        _require(
            not rejected_progression.stdout,
            "invalid progression evidence emitted a growth report",
        )
        _require(
            "progression does not match its stage"
            in rejected_progression.stderr,
            "invalid progression evidence was not rejected",
        )
        _require(
            PRIVATE_STANDARD not in rejected_progression.stderr,
            "invalid progression rejection leaked private evidence",
        )
        checked.append("schema-eight-progression-gate")

        invalid_activation = json.loads(json.dumps(report))
        invalid_activation["deals"][0]["activated"] = True
        invalid_activation_report = (
            Path(tmp) / "invalid-activation-pilot-report.json"
        )
        invalid_activation_report.write_text(
            json.dumps(invalid_activation, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        rejected_activation = _run_growth(
            growth_command,
            distribution_report,
            invalid_activation_report,
            output_format="json",
            environment=environment,
            expected_exit_code=2,
        )
        _require(
            not rejected_activation.stdout,
            "invalid activation evidence emitted a growth report",
        )
        _require(
            "activated requires booked payment" in rejected_activation.stderr,
            "invalid activation evidence was not rejected",
        )
        checked.append("schema-ten-activation-gate")

        balanced_issues = json.loads(json.dumps(active_issues))
        for label in ("pilot-qualified", "pilot-offered", "pilot-paid"):
            balanced_issues[0]["labels"].append({"name": label})
        balanced_export = Path(tmp) / "balanced-activation-issues.json"
        balanced_export.write_text(
            json.dumps(balanced_issues, indent=2),
            encoding="utf-8",
        )
        forged_attribution = _json_report(
            pilot_command,
            balanced_export,
            environment=environment,
        )
        (
            forged_attribution["by_source"]["website"]["activated_pilots"],
            forged_attribution["by_source"]["outreach"]["activated_pilots"],
        ) = (
            forged_attribution["by_source"]["outreach"]["activated_pilots"],
            forged_attribution["by_source"]["website"]["activated_pilots"],
        )
        forged_attribution_report = (
            Path(tmp) / "forged-activation-attribution-report.json"
        )
        forged_attribution_report.write_text(
            json.dumps(forged_attribution, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        rejected_attribution = _run_growth(
            growth_command,
            distribution_report,
            forged_attribution_report,
            output_format="json",
            environment=environment,
            expected_exit_code=2,
        )
        _require(
            not rejected_attribution.stdout,
            "forged activation attribution emitted a growth report",
        )
        _require(
            "by_source.website.activated_pilots does not match deals"
            in rejected_attribution.stderr,
            "forged activation attribution was not rejected",
        )
        checked.append("schema-ten-activation-attribution-gate")

        growth_text = _run_growth(
            growth_command,
            distribution_report,
            pilot_report,
            output_format="text",
            environment=environment,
            expected_exit_code=0,
        ).stdout
        for expected_line in (
            "Reach movement: +6 primary / +2 portable / +4 wheel",
            "Pilot funnel: 2 requests / 2 attributed / 1 qualified / "
            "1 offered / 1 booked / 0 activated",
            "Revenue: $299 booked / $897 target",
            "outreach: 1 requests, 1 qualified, 1 offered, 1 booked "
            "($299), 0 activated",
            "Qualification scope: 2 complete / 2 target / 0 review / "
            "0 subset required",
            "Bottleneck: activation",
            "Activation queue:\n  #102 [paid, outreach, ready, commercial_fit]",
            "Warnings:\n  none",
        ):
            _require(expected_line in growth_text, "operator growth text changed")
        _require(
            PRIVATE_STANDARD not in growth_text,
            "repository-standard free text leaked into growth text",
        )
        checked.append("growth-boundaries")

        integration_pilot_report = Path(tmp) / "integration-pilot-report.json"
        integration_pilot_report.write_text(
            json.dumps(integration_report, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        integration_growth = _growth_report(
            growth_command,
            distribution_report,
            integration_pilot_report,
            environment=environment,
        )
        _require(
            integration_growth.get("bottleneck", {}).get("stage") == "payment",
            "non-GitHub growth bottleneck changed",
        )
        _require(
            integration_growth.get("bottleneck", {}).get("next_action")
            == (
                "Work the qualification-aware pilot sales queue before "
                "confirming purchase or payment."
            ),
            "growth report bypassed the non-GitHub integration gate",
        )
        checked.append("growth-ci-integration-gate")

        distribution["change"]["primary_artifact_downloads_delta"] = 7
        distribution_report.write_text(
            json.dumps(distribution, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        invalid_growth = _run_growth(
            growth_command,
            distribution_report,
            pilot_report,
            output_format="json",
            environment=environment,
            expected_exit_code=2,
        )
        _require(not invalid_growth.stdout, "invalid growth evidence emitted a report")
        _require(
            "primary delta does not match portable and wheel"
            in invalid_growth.stderr,
            "invalid reach evidence did not produce its controlled error",
        )
        checked.append("invalid-growth-rejected")

        duplicate_growth_pilot_report = (
            Path(tmp) / "duplicate-growth-pilot-report.json"
        )
        duplicate_growth_pilot_report.write_text(
            (
                '{"schema_version": 10, "summary": {'
                '"booked_pilots": 1, "booked_pilots": 999}}'
            ),
            encoding="utf-8",
        )
        duplicate_growth = _run_growth(
            growth_command,
            distribution_report,
            duplicate_growth_pilot_report,
            output_format="json",
            environment=environment,
            expected_exit_code=2,
        )
        _require(
            not duplicate_growth.stdout,
            "duplicate joined-report key emitted a growth report",
        )
        _require(
            duplicate_growth.stderr
            == (
                "repo-scout-growth: pilot report contains duplicate JSON key: "
                '"booked_pilots"\n'
            ),
            "duplicate joined-report key did not produce its controlled error",
        )

        duplicate_growth_distribution_report = (
            Path(tmp) / "duplicate-growth-distribution-report.json"
        )
        duplicate_growth_distribution_report.write_text(
            '{"schema_version": 2, "schema_version": 2}',
            encoding="utf-8",
        )
        duplicate_distribution_growth = _run_growth(
            growth_command,
            duplicate_growth_distribution_report,
            pilot_report,
            output_format="json",
            environment=environment,
            expected_exit_code=2,
        )
        _require(
            not duplicate_distribution_growth.stdout,
            "duplicate distribution key emitted a growth report",
        )
        _require(
            duplicate_distribution_growth.stderr
            == (
                "repo-scout-growth: distribution report contains duplicate "
                'JSON key: "schema_version"\n'
            ),
            "duplicate distribution key did not produce its controlled error",
        )
        checked.append("duplicate-growth-keys-rejected")

        current_release_export.write_text(
            json.dumps(
                _release_export(portable=5, wheel=9, duplicate_manifest=True),
                indent=2,
            ),
            encoding="utf-8",
        )
        invalid_distribution = _run_distribution(
            distribution_command,
            current_release_export,
            baseline=baseline_distribution_report,
            output_format="json",
            environment=environment,
            expected_exit_code=2,
        )
        _require(
            not invalid_distribution.stdout,
            "invalid release evidence emitted a distribution report",
        )
        _require(
            "duplicate asset name: SHA256SUMS" in invalid_distribution.stderr,
            "invalid release evidence did not produce its controlled error",
        )
        checked.append("invalid-distribution-rejected")

        issue_export.write_text(
            """[
  {
    "number": 103,
    "title": "Ambiguous payment evidence",
    "state": "OPEN",
    "updatedAt": "2026-07-13T12:00:00Z",
    "body": null,
    "labels": ["pilot-lead"],
    "labels": ["pilot-lead", "pilot-paid"]
  }
]
""",
            encoding="utf-8",
        )
        duplicate_key = _run(
            pilot_command,
            issue_export,
            output_format="json",
            environment=environment,
            expected_exit_code=2,
        )
        _require(
            not duplicate_key.stdout,
            "duplicate payment key emitted a pilot report",
        )
        _require(
            'duplicate JSON key: "labels"' in duplicate_key.stderr,
            "duplicate payment key did not produce its controlled error",
        )
        _require(
            "pilot-paid" not in duplicate_key.stderr,
            "duplicate payment key exposed ambiguous label evidence",
        )
        checked.append("duplicate-payment-key-rejected")

        issue_export.write_text(
            json.dumps(
                [
                    _issue(
                        number=103,
                        title="Edited intake answer",
                        source=(
                            "Edited source\n"
                            f"{INJECTED_WARNING_MARKER}\x1b[31m"
                        ),
                        readiness="Ready to purchase the $299 pilot",
                        criterion="The $299 scope and price fit",
                        labels=(
                            "pilot-lead",
                            f"pilot-edited\n{INJECTED_WARNING_MARKER}\x1b[31m",
                        ),
                    )
                ],
                indent=2,
            ),
            encoding="utf-8",
        )
        safe_warning = _run(
            pilot_command,
            issue_export,
            output_format="text",
            environment=environment,
            expected_exit_code=0,
        )
        _require(
            INJECTED_WARNING_MARKER not in safe_warning.stdout
            and "\x1b" not in safe_warning.stdout,
            "unknown intake answer altered operator warning output",
        )
        _require(
            "Pilot issue has an unrecognized lead source answer."
            in safe_warning.stdout,
            "unknown intake answer lost its review warning",
        )
        _require(
            "Pilot issue has an unrecognized pilot label."
            in safe_warning.stdout,
            "unknown pilot label lost its review warning",
        )
        checked.append("unknown-answer-text-safe")

        issue_export.write_text(
            json.dumps(
                [
                    _issue(
                        number=104,
                        title="Unknown-only lifecycle label",
                        source="Repo Scout website",
                        readiness="Ready to purchase the $299 pilot",
                        criterion="The $299 scope and price fit",
                        labels=("pilot-needs-review",),
                    )
                ],
                indent=2,
            ),
            encoding="utf-8",
        )
        unknown_only = _json_report(
            pilot_command,
            issue_export,
            environment=environment,
        )
        unknown_summary = unknown_only.get("summary", {})
        _require(
            unknown_summary.get("tracked_issues") == 0
            and unknown_summary.get("ignored_issues") == 1
            and unknown_summary.get("attributed_issues") == 0,
            "unknown-only pilot label counted as commercial demand",
        )
        _require(
            unknown_only.get("deals") == [],
            "unknown-only pilot label created a deal",
        )
        _require(
            [warning.get("kind") for warning in unknown_only.get("warnings", [])]
            == ["unknown_pilot_label", "missing_known_stage"],
            "unknown-only pilot label lost its repair warnings",
        )
        checked.append("unknown-label-not-demand")

        unsafe_url_issue = _issue(
            number=105,
            title="Unsafe exported URL",
            source="Repo Scout website",
            readiness="Ready to purchase the $299 pilot",
            criterion="The $299 scope and price fit",
            labels=("pilot-lead",),
        )
        unsafe_url_issue["url"] = (
            "https://example.invalid/pilots/105\n"
            f"{INJECTED_URL_MARKER}\x1b[31m"
        )
        issue_export.write_text(
            json.dumps([unsafe_url_issue], indent=2),
            encoding="utf-8",
        )
        unsafe_url = _run(
            pilot_command,
            issue_export,
            output_format="text",
            environment=environment,
            expected_exit_code=2,
        )
        _require(
            not unsafe_url.stdout,
            "unsafe issue URL emitted a commercial report",
        )
        _require(
            "url must be empty or printable text" in unsafe_url.stderr,
            "unsafe issue URL did not produce its controlled error",
        )
        _require(
            INJECTED_URL_MARKER not in unsafe_url.stderr
            and "\x1b" not in unsafe_url.stderr,
            "unsafe issue URL leaked into its rejection",
        )
        checked.append("unsafe-url-rejected")

        issue_export.write_text(
            json.dumps(
                [
                    _issue(
                        number=105,
                        title=(
                            "Forged operator line\n"
                            f"{INJECTED_REVENUE_MARKER}\x1b[31m"
                        ),
                        source="Repo Scout website",
                        readiness="Ready to purchase the $299 pilot",
                        criterion="The $299 scope and price fit",
                        labels=("pilot-lead", "pilot-qualified", "pilot-offered"),
                    )
                ],
                indent=2,
            ),
            encoding="utf-8",
        )
        original_unsafe_title = issue_export.read_bytes()
        unsafe_title = _run(
            pilot_command,
            issue_export,
            output_format="text",
            environment=environment,
            expected_exit_code=2,
        )
        _require(
            not unsafe_title.stdout,
            "unsafe pilot title emitted a commercial report",
        )
        _require(
            "title must be non-empty printable text" in unsafe_title.stderr,
            "unsafe pilot title did not produce its controlled error",
        )
        _require(
            INJECTED_REVENUE_MARKER not in unsafe_title.stderr
            and "\x1b" not in unsafe_title.stderr,
            "unsafe pilot title leaked into its rejection",
        )
        _require(
            issue_export.read_bytes() == original_unsafe_title,
            "unsafe pilot title export changed during rejection",
        )
        checked.append("unsafe-title-rejected")

        issue_export.write_text("{}\n", encoding="utf-8")
        invalid = _run(
            pilot_command,
            issue_export,
            output_format="json",
            environment=environment,
            expected_exit_code=2,
        )
        _require(
            "issue export must be a JSON array" in invalid.stderr,
            "invalid export did not produce its controlled error",
        )
        checked.append("invalid-export-rejected")

    return tuple(checked)


def _commercial_commands(
    python: str,
    *,
    command_directory: str | Path | None,
) -> tuple[tuple[str, ...], tuple[str, ...], tuple[str, ...]]:
    if command_directory is None:
        return (
            (python, "-m", "repo_scout.pilot_funnel"),
            (python, "-m", "repo_scout.distribution"),
            (python, "-m", "repo_scout.growth"),
        )

    directory = Path(command_directory)
    commands: list[tuple[str, ...]] = []
    for name in (
        "repo-scout-pilot",
        "repo-scout-distribution",
        "repo-scout-growth",
    ):
        path = directory / name
        if not path.is_file() or not os.access(path, os.X_OK):
            raise SmokeTestError(
                f"installed command is missing or not executable: {path}"
            )
        commands.append((str(path),))
    return commands[0], commands[1], commands[2]


def _release_export(
    *,
    portable: int,
    wheel: int,
    duplicate_manifest: bool = False,
) -> list[dict[str, Any]]:
    assets = [
        {"name": "repo-scout-0.3.51.pyz", "download_count": portable},
        {
            "name": "repo_scout-0.3.51-py3-none-any.whl",
            "download_count": wheel,
        },
        {"name": "repo_scout-0.3.51.tar.gz", "download_count": 1},
        {"name": "SHA256SUMS", "download_count": 1},
    ]
    if duplicate_manifest:
        assets.append({"name": "SHA256SUMS", "download_count": 1})
    return [
        {
            "tag_name": "v0.3.51",
            "draft": False,
            "prerelease": False,
            "published_at": "2026-07-13T00:00:00Z",
            "html_url": "https://example.invalid/releases/v0.3.51",
            "assets": assets,
        }
    ]


def _issue(
    *,
    number: int,
    title: str,
    source: str,
    readiness: str,
    criterion: str,
    labels: Sequence[str],
    ci_provider: str = "GitHub Actions",
    team_size: int = 12,
    repository_count: int = 6,
) -> dict[str, Any]:
    body = "\n\n".join(
        (
            f"### Team size\n\n{team_size}",
            f"### Repository count\n\n{repository_count}",
            f"### CI provider\n\n{ci_provider}",
            f"### How did you hear about Repo Scout?\n\n{source}",
            f"### Repository standard to enforce\n\n{PRIVATE_STANDARD}",
            f"### Primary purchase criterion\n\n{criterion}",
            f"### Purchase readiness\n\n{readiness}",
        )
    )
    return {
        "number": number,
        "title": title,
        "url": f"https://example.invalid/pilots/{number}",
        "state": "OPEN",
        "updatedAt": "2026-07-13T12:00:00Z",
        "body": body,
        "labels": [{"name": label} for label in labels],
    }


def _json_report(
    command: Sequence[str],
    issue_export: Path,
    *,
    environment: Mapping[str, str] | None,
) -> dict[str, Any]:
    completed = _run(
        command,
        issue_export,
        output_format="json",
        environment=environment,
        expected_exit_code=0,
    )
    try:
        report = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise SmokeTestError("pilot command did not emit valid JSON") from exc
    if not isinstance(report, dict):
        raise SmokeTestError("pilot command emitted a non-object report")
    return report


def _growth_report(
    command: Sequence[str],
    distribution_report: Path,
    pilot_report: Path,
    *,
    environment: Mapping[str, str] | None,
) -> dict[str, Any]:
    completed = _run_growth(
        command,
        distribution_report,
        pilot_report,
        output_format="json",
        environment=environment,
        expected_exit_code=0,
    )
    try:
        report = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise SmokeTestError("growth command did not emit valid JSON") from exc
    if not isinstance(report, dict):
        raise SmokeTestError("growth command emitted a non-object report")
    return report


def _distribution_json_report(
    command: Sequence[str],
    release_export: Path,
    *,
    baseline: Path | None,
    environment: Mapping[str, str] | None,
) -> dict[str, Any]:
    completed = _run_distribution(
        command,
        release_export,
        baseline=baseline,
        output_format="json",
        environment=environment,
        expected_exit_code=0,
    )
    try:
        report = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise SmokeTestError("distribution command did not emit valid JSON") from exc
    if not isinstance(report, dict):
        raise SmokeTestError("distribution command emitted a non-object report")
    return report


def _run(
    command: Sequence[str],
    issue_export: Path,
    *,
    output_format: str,
    environment: Mapping[str, str] | None,
    expected_exit_code: int,
) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(
        [
            *command,
            str(issue_export),
            "--format",
            output_format,
            "--as-of",
            "2026-07-14",
        ],
        capture_output=True,
        text=True,
        env=dict(environment) if environment is not None else None,
    )
    if completed.returncode != expected_exit_code:
        detail = (
            completed.stderr.strip() or completed.stdout.strip() or "no output"
        )
        raise SmokeTestError(
            f"pilot command exited {completed.returncode}; "
            f"expected {expected_exit_code}: {detail}"
        )
    return completed


def _run_distribution(
    command: Sequence[str],
    release_export: Path,
    *,
    baseline: Path | None,
    output_format: str,
    environment: Mapping[str, str] | None,
    expected_exit_code: int,
) -> subprocess.CompletedProcess[str]:
    arguments = [
        *command,
        str(release_export),
        "--format",
        output_format,
    ]
    if baseline is not None:
        arguments.extend(("--baseline", str(baseline)))
    completed = subprocess.run(
        arguments,
        capture_output=True,
        text=True,
        env=dict(environment) if environment is not None else None,
    )
    if completed.returncode != expected_exit_code:
        detail = completed.stderr.strip() or completed.stdout.strip() or "no output"
        raise SmokeTestError(
            f"distribution command exited {completed.returncode}; "
            f"expected {expected_exit_code}: {detail}"
        )
    return completed


def _run_growth(
    command: Sequence[str],
    distribution_report: Path,
    pilot_report: Path,
    *,
    output_format: str,
    environment: Mapping[str, str] | None,
    expected_exit_code: int,
) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(
        [
            *command,
            str(distribution_report),
            str(pilot_report),
            "--format",
            output_format,
        ],
        capture_output=True,
        text=True,
        env=dict(environment) if environment is not None else None,
    )
    if completed.returncode != expected_exit_code:
        detail = completed.stderr.strip() or completed.stdout.strip() or "no output"
        raise SmokeTestError(
            f"growth command exited {completed.returncode}; "
            f"expected {expected_exit_code}: {detail}"
        )
    return completed


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise SmokeTestError(message)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Smoke test installed Repo Scout pilot and growth reporting."
    )
    parser.add_argument("--python", default=sys.executable)
    parser.add_argument(
        "--command-directory",
        type=Path,
        help=(
            "Directory containing installed repo-scout-pilot, "
            "repo-scout-distribution, and repo-scout-growth commands."
        ),
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        checked = verify_pilot_funnel(
            args.python,
            command_directory=args.command_directory,
            environment=os.environ,
        )
    except SmokeTestError as exc:
        print(f"commercial reporting smoke test failed: {exc}", file=sys.stderr)
        return 1
    print("commercial reporting smoke test passed: " + ", ".join(checked))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
