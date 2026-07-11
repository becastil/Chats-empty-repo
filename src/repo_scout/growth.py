from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any, Sequence


SCHEMA_VERSION = 1
SUPPORTED_DISTRIBUTION_SCHEMAS = {2}
SUPPORTED_PILOT_SCHEMAS = {5, 6}
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
        },
        "distribution_change": distribution["change"],
        "sources": source_rows,
        "bottleneck": bottleneck,
        "evidence_quality": {
            "distribution_warnings": distribution["warning_count"],
            "pilot_warnings": pilot["warning_count"],
            "unattributed_pilot_requests": pilot_summary["unattributed_issues"],
            "unknown_source_pilot_requests": pilot_summary[
                "unknown_source_issues"
            ],
        },
        "warnings": warnings,
        "measurement_note": (
            "Artifact request deltas can include CI, maintainer checks, and retries. "
            "They cannot be assigned to self-reported lead sources and are not a "
            "conversion-rate denominator. Only paid pilot stages count as revenue."
        ),
    }


def format_growth_report(report: dict[str, Any]) -> str:
    summary = report["summary"]
    change = report["distribution_change"]
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

    quality = report["evidence_quality"]
    lines.extend(
        [
            (
                "Evidence quality: "
                f"{quality['distribution_warnings']} distribution warnings / "
                f"{quality['pilot_warnings']} pilot warnings / "
                f"{quality['unattributed_pilot_requests']} unattributed requests / "
                f"{quality['unknown_source_pilot_requests']} unknown sources"
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
        help="Schema-5 or schema-6 repo-scout-pilot JSON report.",
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
        _validate_source_totals(source, totals, pricing["pilot_price_usd"])
        if totals["deals"]:
            sources.append({"source": source, **totals})

    _validate_pilot_totals(summary, pricing, sources)
    raw_warnings = root.get("warnings")
    if not isinstance(raw_warnings, list):
        raise GrowthInputError("pilot report.warnings must be an array")

    return {
        "schema_version": schema,
        "summary": summary,
        "pricing": pricing,
        "sources": sources,
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


def _validate_source_totals(
    source: str, totals: dict[str, int], pilot_price_usd: int
) -> None:
    deals = totals["deals"]
    progression = (
        totals["qualified_pilots"],
        totals["offered_pilots"],
        totals["booked_pilots"],
    )
    if any(count > deals for count in progression):
        raise GrowthInputError(
            f"pilot report.by_source.{source} stage totals exceed deals"
        )
    if not progression[0] >= progression[1] >= progression[2]:
        raise GrowthInputError(
            f"pilot report.by_source.{source} stage totals are not cumulative"
        )
    if totals["annual_conversions"] > totals["booked_pilots"]:
        raise GrowthInputError(
            f"pilot report.by_source.{source} conversions exceed booked pilots"
        )
    if totals["lost_pilots"] > deals:
        raise GrowthInputError(
            f"pilot report.by_source.{source} losses exceed deals"
        )
    expected_revenue = totals["booked_pilots"] * pilot_price_usd
    if totals["booked_revenue_usd"] != expected_revenue:
        raise GrowthInputError(
            f"pilot report.by_source.{source} booked revenue does not match pilots"
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
