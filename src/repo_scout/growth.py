from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any, Sequence

from .pilot_funnel import DECISION_CRITERION_KEYS


SCHEMA_VERSION = 2
SUPPORTED_DISTRIBUTION_SCHEMAS = {2}
SUPPORTED_PILOT_SCHEMAS = {5, 6, 7}
DELTA_FIELDS = (
    "primary_artifact_downloads_delta",
    "portable_downloads_delta",
    "wheel_downloads_delta",
    "source_downloads_delta",
    "manifest_downloads_delta",
    "unknown_downloads_delta",
)
SOURCE_TOTAL_FIELDS = (
    "deals",
    "qualified_pilots",
    "offered_pilots",
    "booked_pilots",
    "booked_revenue_usd",
    "annual_conversions",
    "lost_pilots",
)


class GrowthInputError(ValueError):
    """Raised when growth evidence cannot be joined safely."""


def build_growth_report(
    distribution_report: Any,
    pilot_report: Any,
) -> dict[str, Any]:
    distribution = _parse_distribution_report(distribution_report)
    pilot = _parse_pilot_report(pilot_report)
    pilot_summary = pilot["summary"]
    pricing = pilot["pricing"]
    source_rows = pilot["sources"]
    criterion_rows = pilot["decision_criteria"]
    qualified_pilots = sum(row["qualified_pilots"] for row in source_rows)
    offered_pilots = sum(row["offered_pilots"] for row in source_rows)

    bottleneck = _choose_bottleneck(
        distribution["change"],
        tracked_pilot_requests=pilot_summary["tracked_issues"],
        qualified_pilots=qualified_pilots,
        offered_pilots=offered_pilots,
        booked_pilots=pilot_summary["booked_pilots"],
        target_pilots=pricing["target_pilots"],
        annual_conversions=pilot_summary["annual_conversions"],
    )

    warnings: list[dict[str, str]] = []
    if distribution["change"] is None:
        warnings.append(
            {
                "kind": "missing_distribution_baseline",
                "message": (
                    "Distribution movement is unavailable until a baseline report "
                    "is supplied."
                ),
            }
        )
    if distribution["warning_count"]:
        warnings.append(
            {
                "kind": "distribution_evidence_warnings",
                "message": (
                    f"The distribution report contains "
                    f"{distribution['warning_count']} warning(s)."
                ),
            }
        )
    if pilot["warning_count"]:
        warnings.append(
            {
                "kind": "pilot_evidence_warnings",
                "message": (
                    f"The pilot report contains {pilot['warning_count']} warning(s)."
                ),
            }
        )
    if pilot_summary["unattributed_issues"]:
        warnings.append(
            {
                "kind": "unattributed_pilot_requests",
                "message": (
                    f"{pilot_summary['unattributed_issues']} pilot request(s) have "
                    "no self-reported discovery source."
                ),
            }
        )
    if pilot_summary["unknown_source_issues"]:
        warnings.append(
            {
                "kind": "unknown_pilot_sources",
                "message": (
                    f"{pilot_summary['unknown_source_issues']} pilot request(s) have "
                    "ambiguous or unrecognized source evidence."
                ),
            }
        )
    if not pilot["decision_criterion_reporting_available"]:
        warnings.append(
            {
                "kind": "decision_criterion_evidence_unavailable",
                "message": (
                    "The schema-5 pilot report predates purchase-criterion "
                    "evidence."
                ),
            }
        )
    else:
        if pilot_summary["missing_decision_criterion_issues"]:
            warnings.append(
                {
                    "kind": "missing_decision_criteria",
                    "message": (
                        f"{pilot_summary['missing_decision_criterion_issues']} "
                        "pilot request(s) have no primary purchase criterion."
                    ),
                }
            )
        if pilot_summary["unknown_decision_criterion_issues"]:
            warnings.append(
                {
                    "kind": "unknown_decision_criteria",
                    "message": (
                        f"{pilot_summary['unknown_decision_criterion_issues']} "
                        "pilot request(s) have ambiguous or unrecognized purchase "
                        "criterion evidence."
                    ),
                }
            )
    if (
        pilot["qualification_reporting_available"]
        and pilot_summary["qualification_review_issues"]
    ):
        warnings.append(
            {
                "kind": "qualification_scope_review_required",
                "message": (
                    f"{pilot_summary['qualification_review_issues']} pilot "
                    "request(s) need scope or target-profile review."
                ),
            }
        )

    return {
        "schema_version": SCHEMA_VERSION,
        "summary": {
            "distribution_baseline_present": distribution["change"] is not None,
            "tracked_pilot_requests": pilot_summary["tracked_issues"],
            "attributed_pilot_requests": pilot_summary["attributed_issues"],
            "qualified_pilots": qualified_pilots,
            "offered_pilots": offered_pilots,
            "booked_pilots": pilot_summary["booked_pilots"],
            "booked_revenue_usd": pilot_summary["booked_revenue_usd"],
            "target_pilots": pricing["target_pilots"],
            "target_revenue_usd": pricing["target_revenue_usd"],
            "annual_conversions": pilot_summary["annual_conversions"],
            "lost_pilots": pilot_summary["lost_pilots"],
            "open_sales_actions": pilot_summary["sales_actions"],
            "decision_criterion_reporting_available": pilot[
                "decision_criterion_reporting_available"
            ],
            "declared_decision_criterion_requests": pilot_summary.get(
                "declared_decision_criterion_issues"
            ),
            "missing_decision_criterion_requests": pilot_summary.get(
                "missing_decision_criterion_issues"
            ),
            "unknown_decision_criterion_requests": pilot_summary.get(
                "unknown_decision_criterion_issues"
            ),
            "qualification_reporting_available": pilot[
                "qualification_reporting_available"
            ],
            "complete_qualification_requests": pilot_summary.get(
                "complete_qualification_issues"
            ),
            "target_profile_requests": pilot_summary.get(
                "target_profile_issues"
            ),
            "qualification_review_requests": pilot_summary.get(
                "qualification_review_issues"
            ),
            "subset_scope_requests": pilot_summary.get("subset_scope_issues"),
        },
        "distribution_change": distribution["change"],
        "sources": source_rows,
        "decision_criteria": criterion_rows,
        "bottleneck": bottleneck,
        "evidence_quality": {
            "distribution_warnings": distribution["warning_count"],
            "pilot_warnings": pilot["warning_count"],
            "pilot_schema_version": pilot["schema_version"],
            "decision_criterion_reporting_available": pilot[
                "decision_criterion_reporting_available"
            ],
            "unattributed_pilot_requests": pilot_summary["unattributed_issues"],
            "unknown_source_pilot_requests": pilot_summary[
                "unknown_source_issues"
            ],
            "missing_decision_criterion_requests": pilot_summary.get(
                "missing_decision_criterion_issues"
            ),
            "unknown_decision_criterion_requests": pilot_summary.get(
                "unknown_decision_criterion_issues"
            ),
            "qualification_reporting_available": pilot[
                "qualification_reporting_available"
            ],
            "qualification_review_requests": pilot_summary.get(
                "qualification_review_issues"
            ),
        },
        "warnings": warnings,
        "measurement_note": (
            "Artifact request deltas can include CI, maintainer checks, and retries. "
            "They are not unique-user or conversion-rate denominators and cannot "
            "be assigned to self-reported lead sources or purchase criteria. "
            "Purchase criteria are self-reported evaluation priorities, not causal "
            "attribution, willingness to pay, or proof of a moat. Only paid pilot "
            "stages count as revenue."
        ),
    }


def format_growth_report(report: dict[str, Any]) -> str:
    summary = report["summary"]
    change = report["distribution_change"]
    quality = report["evidence_quality"]
    if change is None:
        reach = "not available (baseline required)"
    else:
        reach = (
            f"{_signed(change['primary_artifact_downloads_delta'])} primary / "
            f"{_signed(change['portable_downloads_delta'])} portable / "
            f"{_signed(change['wheel_downloads_delta'])} wheel"
        )

    lines = [
        "Repo Scout Growth Review",
        f"Reach movement: {reach}",
        (
            f"Pilot funnel: {summary['tracked_pilot_requests']} requests / "
            f"{summary['attributed_pilot_requests']} attributed / "
            f"{summary['qualified_pilots']} qualified / "
            f"{summary['offered_pilots']} offered / "
            f"{summary['booked_pilots']} booked"
        ),
        (
            f"Revenue: ${summary['booked_revenue_usd']} booked / "
            f"${summary['target_revenue_usd']} target"
        ),
        (
            "Qualification scope: schema-7 pilot report required"
            if not summary["qualification_reporting_available"]
            else (
                f"Qualification scope: "
                f"{summary['complete_qualification_requests']} complete / "
                f"{summary['target_profile_requests']} target / "
                f"{summary['qualification_review_requests']} review / "
                f"{summary['subset_scope_requests']} subset required"
            )
        ),
        f"Bottleneck: {report['bottleneck']['stage']}",
        f"Reason: {report['bottleneck']['reason']}",
        f"Next action: {report['bottleneck']['next_action']}",
        "Sources:",
    ]
    if report["sources"]:
        for source in report["sources"]:
            lines.append(
                f"  {source['source']}: {source['deals']} requests, "
                f"{source['qualified_pilots']} qualified, "
                f"{source['offered_pilots']} offered, "
                f"{source['booked_pilots']} booked "
                f"(${source['booked_revenue_usd']})"
            )
    else:
        lines.append("  none")

    lines.append("Purchase criteria:")
    if not quality["decision_criterion_reporting_available"]:
        lines.append("  schema-6+ pilot report required")
    elif report["decision_criteria"]:
        for criterion in report["decision_criteria"]:
            lines.append(
                f"  {criterion['criterion']}: {criterion['deals']} requests, "
                f"{criterion['qualified_pilots']} qualified, "
                f"{criterion['offered_pilots']} offered, "
                f"{criterion['booked_pilots']} booked "
                f"(${criterion['booked_revenue_usd']})"
            )
    else:
        lines.append("  none")

    lines.extend(
        [
            (
                "Evidence quality: "
                f"{quality['distribution_warnings']} distribution warnings / "
                f"{quality['pilot_warnings']} pilot warnings / "
                f"{quality['unattributed_pilot_requests']} unattributed requests / "
                f"{quality['unknown_source_pilot_requests']} unknown sources / "
                f"schema {quality['pilot_schema_version']} pilot evidence"
            ),
            "Warnings:",
        ]
    )
    if report["warnings"]:
        for warning in report["warnings"]:
            lines.append(f"  {warning['kind']}: {warning['message']}")
    else:
        lines.append("  none")
    lines.append(f"Note: {report['measurement_note']}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="repo-scout-growth",
        description=(
            "Review distribution movement beside attributed pilot revenue evidence."
        ),
    )
    parser.add_argument(
        "distribution_report",
        type=Path,
        metavar="DISTRIBUTION_REPORT",
        help="Schema-2 repo-scout-distribution JSON report.",
    )
    parser.add_argument(
        "pilot_report",
        type=Path,
        metavar="PILOT_REPORT",
        help="Schema-5, schema-6, or schema-7 repo-scout-pilot JSON report.",
    )
    parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Output format. Defaults to text.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        distribution = _read_report(args.distribution_report, "distribution")
        pilot = _read_report(args.pilot_report, "pilot")
        report = build_growth_report(distribution, pilot)
    except GrowthInputError as exc:
        print(f"repo-scout-growth: {exc}", file=sys.stderr)
        return 2

    if args.format == "json":
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(format_growth_report(report))
    return 0


def _parse_distribution_report(report: Any) -> dict[str, Any]:
    root = _require_object(report, "distribution report")
    schema = _require_schema(
        root, "distribution report", SUPPORTED_DISTRIBUTION_SCHEMAS
    )
    summary = _require_object(root.get("summary"), "distribution report.summary")
    warning_count = _require_non_negative_int(
        summary.get("warning_count"), "distribution report.summary.warning_count"
    )
    raw_warnings = root.get("warnings")
    if not isinstance(raw_warnings, list):
        raise GrowthInputError("distribution report.warnings must be an array")
    if warning_count != len(raw_warnings):
        raise GrowthInputError(
            "distribution report warning_count does not match warnings"
        )

    raw_change = root.get("change")
    change = None
    if raw_change is not None:
        change_object = _require_object(
            raw_change, "distribution report.change"
        )
        change = {
            field: _require_int(
                change_object.get(field), f"distribution report.change.{field}"
            )
            for field in DELTA_FIELDS
        }
        for field in ("new_releases", "removed_releases"):
            change[field] = _require_string_array(
                change_object.get(field), f"distribution report.change.{field}"
            )
        if change["primary_artifact_downloads_delta"] != (
            change["portable_downloads_delta"] + change["wheel_downloads_delta"]
        ):
            raise GrowthInputError(
                "distribution report primary delta does not match portable and wheel"
            )

    return {
        "schema_version": schema,
        "change": change,
        "warning_count": warning_count,
    }


def _parse_pilot_report(report: Any) -> dict[str, Any]:
    root = _require_object(report, "pilot report")
    schema = _require_schema(root, "pilot report", SUPPORTED_PILOT_SCHEMAS)
    summary_object = _require_object(root.get("summary"), "pilot report.summary")
    pricing_object = _require_object(root.get("pricing"), "pilot report.pricing")
    summary_fields = (
        "tracked_issues",
        "attributed_issues",
        "unattributed_issues",
        "unknown_source_issues",
        "booked_pilots",
        "booked_revenue_usd",
        "annual_conversions",
        "lost_pilots",
        "sales_actions",
    )
    summary = {
        field: _require_non_negative_int(
            summary_object.get(field), f"pilot report.summary.{field}"
        )
        for field in summary_fields
    }
    if schema >= 6:
        for field in (
            "declared_decision_criterion_issues",
            "missing_decision_criterion_issues",
            "unknown_decision_criterion_issues",
        ):
            summary[field] = _require_non_negative_int(
                summary_object.get(field), f"pilot report.summary.{field}"
            )
    if schema == 7:
        for field in (
            "complete_qualification_issues",
            "target_profile_issues",
            "qualification_review_issues",
            "subset_scope_issues",
        ):
            summary[field] = _require_non_negative_int(
                summary_object.get(field), f"pilot report.summary.{field}"
            )
        if summary["complete_qualification_issues"] > summary["tracked_issues"]:
            raise GrowthInputError(
                "pilot report complete qualification exceeds tracked issues"
            )
        if (
            summary["target_profile_issues"]
            > summary["complete_qualification_issues"]
        ):
            raise GrowthInputError(
                "pilot report target profile exceeds complete qualification"
            )
        if summary["qualification_review_issues"] != (
            summary["tracked_issues"] - summary["target_profile_issues"]
        ):
            raise GrowthInputError(
                "pilot report qualification review does not reconcile to tracked "
                "and target issues"
            )
        if (
            summary["subset_scope_issues"]
            > summary["complete_qualification_issues"]
        ):
            raise GrowthInputError(
                "pilot report subset scope exceeds complete qualification"
            )
    pricing = {
        field: _require_positive_int(
            pricing_object.get(field), f"pilot report.pricing.{field}"
        )
        for field in (
            "pilot_price_usd",
            "target_pilots",
            "target_revenue_usd",
        )
    }

    raw_sources = _require_object(root.get("by_source"), "pilot report.by_source")
    sources: list[dict[str, Any]] = []
    for source, raw_totals in sorted(raw_sources.items()):
        if not isinstance(source, str) or not source:
            raise GrowthInputError("pilot report.by_source keys must be non-empty")
        totals_object = _require_object(
            raw_totals, f"pilot report.by_source.{source}"
        )
        totals = {
            field: _require_non_negative_int(
                totals_object.get(field),
                f"pilot report.by_source.{source}.{field}",
            )
            for field in SOURCE_TOTAL_FIELDS
        }
        _validate_segment_totals(
            f"pilot report.by_source.{source}",
            totals,
            pricing["pilot_price_usd"],
        )
        if totals["deals"]:
            sources.append({"source": source, **totals})

    _validate_pilot_totals(summary, pricing, sources)
    decision_criteria: list[dict[str, Any]] | None = None
    if schema >= 6:
        raw_criteria = _require_object(
            root.get("by_decision_criterion"),
            "pilot report.by_decision_criterion",
        )
        if any(
            not isinstance(criterion, str) or not criterion
            for criterion in raw_criteria
        ):
            raise GrowthInputError(
                "pilot report.by_decision_criterion keys must be non-empty strings"
            )
        expected_criteria = set(DECISION_CRITERION_KEYS)
        actual_criteria = set(raw_criteria)
        if actual_criteria != expected_criteria:
            missing = sorted(expected_criteria - actual_criteria)
            unexpected = sorted(actual_criteria - expected_criteria)
            details: list[str] = []
            if missing:
                details.append(f"missing: {', '.join(missing)}")
            if unexpected:
                details.append(f"unexpected: {', '.join(unexpected)}")
            raise GrowthInputError(
                "pilot report.by_decision_criterion keys do not match schema 6+ "
                f"({'; '.join(details)})"
            )
        decision_criteria = []
        for criterion in DECISION_CRITERION_KEYS:
            raw_totals = raw_criteria[criterion]
            location = f"pilot report.by_decision_criterion.{criterion}"
            totals_object = _require_object(raw_totals, location)
            totals = {
                field: _require_non_negative_int(
                    totals_object.get(field), f"{location}.{field}"
                )
                for field in SOURCE_TOTAL_FIELDS
            }
            _validate_segment_totals(
                location,
                totals,
                pricing["pilot_price_usd"],
            )
            if totals["deals"]:
                decision_criteria.append({"criterion": criterion, **totals})
        _validate_criterion_totals(summary, decision_criteria, sources)

    raw_warnings = root.get("warnings")
    if not isinstance(raw_warnings, list):
        raise GrowthInputError("pilot report.warnings must be an array")

    return {
        "schema_version": schema,
        "summary": summary,
        "pricing": pricing,
        "sources": sources,
        "decision_criterion_reporting_available": schema >= 6,
        "qualification_reporting_available": schema == 7,
        "decision_criteria": decision_criteria,
        "warning_count": len(raw_warnings),
    }


def _validate_pilot_totals(
    summary: dict[str, int],
    pricing: dict[str, int],
    sources: list[dict[str, Any]],
) -> None:
    checks = {
        "tracked_issues": sum(row["deals"] for row in sources),
        "booked_pilots": sum(row["booked_pilots"] for row in sources),
        "booked_revenue_usd": sum(
            row["booked_revenue_usd"] for row in sources
        ),
        "annual_conversions": sum(
            row["annual_conversions"] for row in sources
        ),
        "lost_pilots": sum(row["lost_pilots"] for row in sources),
    }
    for field, source_total in checks.items():
        if summary[field] != source_total:
            raise GrowthInputError(
                f"pilot report {field} does not match by_source totals"
            )
    attributed = sum(
        row["deals"]
        for row in sources
        if row["source"] not in {"unattributed", "unknown"}
    )
    if summary["attributed_issues"] != attributed:
        raise GrowthInputError(
            "pilot report attributed_issues does not match by_source totals"
        )
    source_by_name = {row["source"]: row for row in sources}
    for field, source in (
        ("unattributed_issues", "unattributed"),
        ("unknown_source_issues", "unknown"),
    ):
        source_total = source_by_name.get(source, {}).get("deals", 0)
        if summary[field] != source_total:
            raise GrowthInputError(
                f"pilot report {field} does not match by_source totals"
            )
    expected_target_revenue = (
        pricing["pilot_price_usd"] * pricing["target_pilots"]
    )
    if pricing["target_revenue_usd"] != expected_target_revenue:
        raise GrowthInputError(
            "pilot report target revenue does not match pilot price and target"
        )


def _validate_criterion_totals(
    summary: dict[str, int],
    criteria: list[dict[str, Any]],
    sources: list[dict[str, Any]],
) -> None:
    for field in SOURCE_TOTAL_FIELDS:
        criterion_total = sum(row[field] for row in criteria)
        source_total = sum(row[field] for row in sources)
        if criterion_total != source_total:
            raise GrowthInputError(
                f"pilot report by_decision_criterion {field} does not match "
                "by_source totals"
            )

    criteria_by_name = {row["criterion"]: row for row in criteria}
    declared = sum(
        row["deals"]
        for row in criteria
        if row["criterion"] not in {"unattributed", "unknown"}
    )
    if summary["declared_decision_criterion_issues"] != declared:
        raise GrowthInputError(
            "pilot report declared_decision_criterion_issues does not match "
            "by_decision_criterion totals"
        )
    for field, criterion in (
        ("missing_decision_criterion_issues", "unattributed"),
        ("unknown_decision_criterion_issues", "unknown"),
    ):
        criterion_total = criteria_by_name.get(criterion, {}).get("deals", 0)
        if summary[field] != criterion_total:
            raise GrowthInputError(
                f"pilot report {field} does not match "
                "by_decision_criterion totals"
            )


def _validate_segment_totals(
    location: str, totals: dict[str, int], pilot_price_usd: int
) -> None:
    deals = totals["deals"]
    progression = (
        totals["qualified_pilots"],
        totals["offered_pilots"],
        totals["booked_pilots"],
    )
    if any(count > deals for count in progression):
        raise GrowthInputError(
            f"{location} stage totals exceed deals"
        )
    if not progression[0] >= progression[1] >= progression[2]:
        raise GrowthInputError(
            f"{location} stage totals are not cumulative"
        )
    if totals["annual_conversions"] > totals["booked_pilots"]:
        raise GrowthInputError(
            f"{location} conversions exceed booked pilots"
        )
    if totals["lost_pilots"] > deals:
        raise GrowthInputError(
            f"{location} losses exceed deals"
        )
    expected_revenue = totals["booked_pilots"] * pilot_price_usd
    if totals["booked_revenue_usd"] != expected_revenue:
        raise GrowthInputError(
            f"{location} booked revenue does not match pilots"
        )


def _choose_bottleneck(
    change: dict[str, Any] | None,
    *,
    tracked_pilot_requests: int,
    qualified_pilots: int,
    offered_pilots: int,
    booked_pilots: int,
    target_pilots: int,
    annual_conversions: int,
) -> dict[str, str]:
    if change is None:
        return {
            "stage": "measurement",
            "reason": "Weekly distribution movement has no baseline yet.",
            "next_action": (
                "Save the current distribution report and compare the next run "
                "against it."
            ),
        }
    primary_delta = change["primary_artifact_downloads_delta"]
    if tracked_pilot_requests == 0:
        if primary_delta > 0:
            reason = (
                "Primary artifact requests increased, but no pilot request entered "
                "the attributed funnel."
            )
        else:
            reason = "No pilot request has entered the attributed funnel."
        return {
            "stage": "acquisition",
            "reason": reason,
            "next_action": (
                "Run one source-identifiable outreach or launch experiment and ask "
                "qualified teams to submit the price-disclosed pilot form."
            ),
        }
    if qualified_pilots == 0:
        return {
            "stage": "qualification",
            "reason": "Pilot requests exist, but none has reached qualification.",
            "next_action": "Work the sales queue and qualify the team policy need.",
        }
    if offered_pilots == 0:
        return {
            "stage": "offer",
            "reason": "Qualified pilot demand exists, but no offer is recorded.",
            "next_action": "Send the explicit $299 pilot terms to a qualified team.",
        }
    if booked_pilots == 0:
        return {
            "stage": "payment",
            "reason": "A pilot offer exists, but no paid pilot is recorded.",
            "next_action": "Resolve the top offered deal's purchase blocker.",
        }
    if booked_pilots < target_pilots:
        return {
            "stage": "pilot_target",
            "reason": "Booked revenue is real, but the founding-pilot target is open.",
            "next_action": "Repeat the best attributed source and close the next pilot.",
        }
    if annual_conversions == 0:
        return {
            "stage": "retention",
            "reason": "The founding-pilot target is met without an annual conversion.",
            "next_action": "Validate weekly CI use and earn the first annual conversion.",
        }
    return {
        "stage": "validated",
        "reason": "The paid-pilot and annual-conversion milestones are represented.",
        "next_action": "Review retention evidence before expanding the paid offer.",
    }


def _read_report(path: Path, label: str) -> Any:
    try:
        content = path.read_text("utf-8")
    except OSError as exc:
        raise GrowthInputError(f"could not read {label} report {path}: {exc}") from exc
    try:
        return json.loads(content)
    except json.JSONDecodeError as exc:
        raise GrowthInputError(
            f"invalid {label} JSON at line {exc.lineno}, column {exc.colno}: "
            f"{exc.msg}"
        ) from exc


def _require_object(value: Any, location: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise GrowthInputError(f"{location} must be a JSON object")
    return value


def _require_schema(
    root: dict[str, Any], location: str, supported: set[int]
) -> int:
    schema = root.get("schema_version")
    if (
        not isinstance(schema, int)
        or isinstance(schema, bool)
        or schema not in supported
    ):
        supported_text = ", ".join(str(version) for version in sorted(supported))
        raise GrowthInputError(
            f"{location}.schema_version must be one of: {supported_text}"
        )
    return schema


def _require_int(value: Any, location: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise GrowthInputError(f"{location} must be an integer")
    return value


def _require_non_negative_int(value: Any, location: str) -> int:
    parsed = _require_int(value, location)
    if parsed < 0:
        raise GrowthInputError(f"{location} must be non-negative")
    return parsed


def _require_positive_int(value: Any, location: str) -> int:
    parsed = _require_int(value, location)
    if parsed < 1:
        raise GrowthInputError(f"{location} must be positive")
    return parsed


def _require_string_array(value: Any, location: str) -> list[str]:
    if not isinstance(value, list) or any(
        not isinstance(item, str) or not item for item in value
    ):
        raise GrowthInputError(f"{location} must be an array of non-empty strings")
    return list(value)


def _signed(value: int) -> str:
    return f"{value:+d}"


if __name__ == "__main__":
    raise SystemExit(main())
