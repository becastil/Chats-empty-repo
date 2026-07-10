from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys
from typing import Any, Sequence, TextIO


SCHEMA_VERSION = 1
PORTABLE_SINCE = (0, 3, 4)
SEMVER_TAG = re.compile(r"v(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\Z")
CHANNEL_ORDER = ("portable", "wheel", "source", "manifest", "unknown")


class DistributionInputError(ValueError):
    """Raised when GitHub release evidence cannot be analyzed safely."""


def build_distribution_report(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, list):
        raise DistributionInputError("release export must be a JSON array")

    stable_releases: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []
    seen_tags: set[str] = set()
    draft_releases = 0
    prerelease_releases = 0

    for index, raw_release in enumerate(payload):
        release = _parse_release(raw_release, index)
        tag = release["tag"]
        if tag in seen_tags:
            raise DistributionInputError(
                f"release export contains duplicate tag: {tag}"
            )
        seen_tags.add(tag)

        if release["draft"]:
            draft_releases += 1
            continue
        if release["prerelease"]:
            prerelease_releases += 1
            continue

        analyzed, release_warnings = _analyze_release(release)
        stable_releases.append(analyzed)
        warnings.extend(release_warnings)

    stable_releases.sort(key=lambda release: release["version"], reverse=True)
    warnings.sort(key=_warning_sort_key)
    totals = {channel: 0 for channel in CHANNEL_ORDER}
    for release in stable_releases:
        for channel in CHANNEL_ORDER:
            totals[channel] += release["downloads"][channel]

    primary_artifact_downloads = totals["portable"] + totals["wheel"]
    return {
        "schema_version": SCHEMA_VERSION,
        "summary": {
            "input_releases": len(payload),
            "stable_releases": len(stable_releases),
            "draft_releases": draft_releases,
            "prerelease_releases": prerelease_releases,
            "complete_releases": sum(
                release["contract"]["complete"] for release in stable_releases
            ),
            "primary_artifact_downloads": primary_artifact_downloads,
            "portable_downloads": totals["portable"],
            "wheel_downloads": totals["wheel"],
            "source_downloads": totals["source"],
            "manifest_downloads": totals["manifest"],
            "unknown_downloads": totals["unknown"],
            "portable_primary_share_percent": (
                round(totals["portable"] / primary_artifact_downloads * 100, 1)
                if primary_artifact_downloads
                else None
            ),
            "warning_count": len(warnings),
        },
        "latest": stable_releases[0] if stable_releases else None,
        "releases": stable_releases,
        "warnings": warnings,
        "measurement_note": (
            "GitHub asset download counts are cumulative requests and can include "
            "CI jobs, maintainer verification, and retries; they are not unique "
            "installs, active users, pilot requests, or revenue."
        ),
    }


def format_distribution_report(report: dict[str, Any]) -> str:
    summary = report["summary"]
    portable_share = summary["portable_primary_share_percent"]
    share_text = "n/a" if portable_share is None else f"{portable_share}%"
    lines = [
        "Repo Scout Distribution",
        (
            f"Releases: {summary['stable_releases']} stable / "
            f"{summary['complete_releases']} contract-complete / "
            f"{summary['draft_releases']} draft / "
            f"{summary['prerelease_releases']} prerelease"
        ),
        (
            f"Primary artifact downloads: {summary['primary_artifact_downloads']} total / "
            f"{summary['portable_downloads']} portable / "
            f"{summary['wheel_downloads']} wheel"
        ),
        f"Portable primary share: {share_text}",
        (
            f"Supporting downloads: {summary['source_downloads']} source / "
            f"{summary['manifest_downloads']} manifests / "
            f"{summary['unknown_downloads']} unknown"
        ),
        "Releases:",
    ]

    if report["releases"]:
        for release in report["releases"]:
            status = "complete" if release["contract"]["complete"] else "drift"
            downloads = release["downloads"]
            lines.append(
                f"  {release['tag']} [{status}]: "
                f"{downloads['portable']} portable, {downloads['wheel']} wheel, "
                f"{downloads['source']} source, {downloads['manifest']} manifests, "
                f"{downloads['unknown']} unknown"
            )
    else:
        lines.append("  none")

    lines.append("Warnings:")
    if report["warnings"]:
        for warning in report["warnings"]:
            lines.append(
                f"  {warning['tag']} {warning['kind']}: {warning['message']}"
            )
    else:
        lines.append("  none")
    lines.append(f"Note: {report['measurement_note']}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="repo-scout-distribution",
        description="Summarize GitHub release artifact requests from exported JSON.",
    )
    parser.add_argument(
        "input",
        nargs="?",
        default="-",
        help="GitHub release JSON file, or - for stdin. Defaults to stdin.",
    )
    parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Output format. Defaults to text.",
    )
    return parser


def main(argv: Sequence[str] | None = None, stdin: TextIO | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        payload = _read_payload(args.input, stdin or sys.stdin)
        report = build_distribution_report(payload)
    except DistributionInputError as exc:
        print(f"repo-scout-distribution: {exc}", file=sys.stderr)
        return 2

    if args.format == "json":
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(format_distribution_report(report))
    return 0


def _read_payload(source: str, stdin: TextIO) -> Any:
    try:
        content = stdin.read() if source == "-" else Path(source).read_text("utf-8")
    except OSError as exc:
        raise DistributionInputError(f"could not read {source}: {exc}") from exc
    try:
        return json.loads(content)
    except json.JSONDecodeError as exc:
        raise DistributionInputError(
            f"invalid JSON at line {exc.lineno}, column {exc.colno}: {exc.msg}"
        ) from exc


def _parse_release(raw_release: Any, index: int) -> dict[str, Any]:
    location = f"release export item {index}"
    if not isinstance(raw_release, dict):
        raise DistributionInputError(f"{location} must be an object")

    tag = raw_release.get("tag_name")
    if not isinstance(tag, str) or not tag:
        raise DistributionInputError(
            f"{location}.tag_name must be a non-empty string"
        )
    draft = raw_release.get("draft")
    prerelease = raw_release.get("prerelease")
    if not isinstance(draft, bool):
        raise DistributionInputError(f"{location}.draft must be a boolean")
    if not isinstance(prerelease, bool):
        raise DistributionInputError(f"{location}.prerelease must be a boolean")
    tag_match = SEMVER_TAG.fullmatch(tag)
    if tag_match is None and not draft and not prerelease:
        raise DistributionInputError(
            f"{location}.tag_name must use vMAJOR.MINOR.PATCH for a stable release"
        )
    version = tuple(int(part) for part in tag_match.groups()) if tag_match else None

    published_at = raw_release.get("published_at")
    if published_at is not None and not isinstance(published_at, str):
        raise DistributionInputError(
            f"{location}.published_at must be a string or null"
        )
    url = raw_release.get("html_url", "")
    if not isinstance(url, str):
        raise DistributionInputError(f"{location}.html_url must be a string")

    raw_assets = raw_release.get("assets")
    if not isinstance(raw_assets, list):
        raise DistributionInputError(f"{location}.assets must be an array")
    assets: list[dict[str, Any]] = []
    seen_asset_names: set[str] = set()
    for asset_index, raw_asset in enumerate(raw_assets):
        asset_location = f"{location}.assets[{asset_index}]"
        if not isinstance(raw_asset, dict):
            raise DistributionInputError(f"{asset_location} must be an object")
        name = raw_asset.get("name")
        if not isinstance(name, str) or not name:
            raise DistributionInputError(
                f"{asset_location}.name must be a non-empty string"
            )
        if name in seen_asset_names:
            raise DistributionInputError(
                f"{location} contains duplicate asset name: {name}"
            )
        seen_asset_names.add(name)
        download_count = raw_asset.get("download_count")
        if (
            not isinstance(download_count, int)
            or isinstance(download_count, bool)
            or download_count < 0
        ):
            raise DistributionInputError(
                f"{asset_location}.download_count must be a non-negative integer"
            )
        assets.append({"name": name, "download_count": download_count})

    return {
        "tag": tag,
        "version": version,
        "draft": draft,
        "prerelease": prerelease,
        "published_at": published_at,
        "url": url,
        "assets": assets,
    }


def _analyze_release(
    release: dict[str, Any],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    tag = release["tag"]
    version_text = tag.removeprefix("v")
    expected = {
        "wheel": f"repo_scout-{version_text}-py3-none-any.whl",
        "source": f"repo_scout-{version_text}.tar.gz",
        "manifest": "SHA256SUMS",
    }
    if release["version"] >= PORTABLE_SINCE:
        expected["portable"] = f"repo-scout-{version_text}.pyz"

    channel_by_name = {name: channel for channel, name in expected.items()}
    downloads = {channel: 0 for channel in CHANNEL_ORDER}
    unexpected: list[str] = []
    for asset in release["assets"]:
        channel = channel_by_name.get(asset["name"], "unknown")
        downloads[channel] += asset["download_count"]
        if channel == "unknown":
            unexpected.append(asset["name"])

    asset_names = {asset["name"] for asset in release["assets"]}
    missing = sorted(name for name in expected.values() if name not in asset_names)
    unexpected.sort()
    warnings: list[dict[str, Any]] = []
    if missing:
        warnings.append(
            {
                "tag": tag,
                "kind": "missing_artifacts",
                "message": f"Missing expected artifacts: {', '.join(missing)}.",
                "artifacts": missing,
            }
        )
    if unexpected:
        warnings.append(
            {
                "tag": tag,
                "kind": "unexpected_artifacts",
                "message": f"Unexpected artifacts: {', '.join(unexpected)}.",
                "artifacts": unexpected,
            }
        )

    primary_downloads = downloads["portable"] + downloads["wheel"]
    return (
        {
            "tag": tag,
            "version": list(release["version"]),
            "published_at": release["published_at"],
            "url": release["url"],
            "contract": {
                "complete": not missing and not unexpected,
                "expected_artifacts": sorted(expected.values()),
                "missing_artifacts": missing,
                "unexpected_artifacts": unexpected,
            },
            "downloads": {
                **downloads,
                "primary": primary_downloads,
                "total": sum(downloads.values()),
            },
            "assets": sorted(release["assets"], key=lambda asset: asset["name"]),
        },
        warnings,
    )


def _warning_sort_key(warning: dict[str, Any]) -> tuple[int, int, int, str]:
    version = tuple(
        int(part) for part in warning["tag"].removeprefix("v").split(".")
    )
    return (-version[0], -version[1], -version[2], warning["kind"])


if __name__ == "__main__":
    raise SystemExit(main())
