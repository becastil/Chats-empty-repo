from __future__ import annotations

import argparse
from html.parser import HTMLParser
import json
from pathlib import Path
import sys
import tomllib
from typing import Sequence
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_URL = "https://repo-scout.becastil.chatgpt.site/"


class ProductionSiteAuditError(RuntimeError):
    """Raised when the deployed site does not match its release contract."""


class _PageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.anchor_urls: list[str] = []
        self.canonical_urls: list[str] = []
        self.json_ld_scripts: list[str] = []
        self._json_ld_parts: list[str] | None = None

    def handle_starttag(
        self, tag: str, attrs: list[tuple[str, str | None]]
    ) -> None:
        attributes = dict(attrs)
        if tag == "a":
            href = attributes.get("href")
            if href is not None:
                self.anchor_urls.append(href)
        if tag == "link" and attributes.get("rel") == "canonical":
            href = attributes.get("href")
            if href is not None:
                self.canonical_urls.append(href)
        if (
            tag == "script"
            and attributes.get("type", "").lower() == "application/ld+json"
        ):
            self._json_ld_parts = []

    def handle_data(self, data: str) -> None:
        if self._json_ld_parts is not None:
            self._json_ld_parts.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "script" and self._json_ld_parts is not None:
            self.json_ld_scripts.append("".join(self._json_ld_parts))
            self._json_ld_parts = None


def load_project_version(root: Path) -> str:
    try:
        with (root / "pyproject.toml").open("rb") as handle:
            document = tomllib.load(handle)
        version = document["project"]["version"]
    except (OSError, KeyError, tomllib.TOMLDecodeError) as exc:
        raise ProductionSiteAuditError(
            f"could not read project version from {root / 'pyproject.toml'}: {exc}"
        ) from exc
    if not isinstance(version, str) or not version:
        raise ProductionSiteAuditError("project.version must be a nonempty string")
    return version


def fetch_html(url: str, timeout: float) -> str:
    request = Request(
        url,
        headers={
            "Accept": "text/html",
            "User-Agent": "repo-scout-production-audit",
        },
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            status = response.status
            content_type = response.headers.get_content_type()
            charset = response.headers.get_content_charset() or "utf-8"
            payload = response.read()
    except (HTTPError, URLError, TimeoutError, OSError) as exc:
        raise ProductionSiteAuditError(f"could not fetch {url}: {exc}") from exc
    if status != 200:
        raise ProductionSiteAuditError(f"{url} returned HTTP {status}")
    if content_type != "text/html":
        raise ProductionSiteAuditError(
            f"{url} returned content type {content_type}, expected text/html"
        )
    try:
        return payload.decode(charset)
    except (LookupError, UnicodeDecodeError) as exc:
        raise ProductionSiteAuditError(
            f"could not decode {url} as {charset}: {exc}"
        ) from exc


def audit_production_html(
    html: str, *, production_url: str, expected_version: str
) -> tuple[str, ...]:
    canonical_url = production_url.rstrip("/") + "/"
    parser = _PageParser()
    parser.feed(html)
    parser.close()

    if parser.canonical_urls != [canonical_url]:
        raise ProductionSiteAuditError(
            "canonical URL mismatch: "
            f"expected exactly {canonical_url}, found {parser.canonical_urls}"
        )

    applications: list[dict[str, object]] = []
    services: list[dict[str, object]] = []
    for raw_script in parser.json_ld_scripts:
        try:
            document = json.loads(raw_script)
        except json.JSONDecodeError as exc:
            raise ProductionSiteAuditError(
                f"production JSON-LD is invalid: {exc}"
            ) from exc
        if not isinstance(document, dict):
            continue
        candidates = document.get("@graph", [document])
        if not isinstance(candidates, list):
            continue
        applications.extend(
            candidate
            for candidate in candidates
            if isinstance(candidate, dict)
            and candidate.get("@type") == "SoftwareApplication"
        )
        services.extend(
            candidate
            for candidate in candidates
            if isinstance(candidate, dict) and candidate.get("@type") == "Service"
        )

    if len(applications) != 1:
        raise ProductionSiteAuditError(
            "expected exactly one SoftwareApplication in production JSON-LD, "
            f"found {len(applications)}"
        )

    application = applications[0]
    if application.get("softwareVersion") != expected_version:
        raise ProductionSiteAuditError(
            "softwareVersion mismatch: "
            f"expected {expected_version}, found {application.get('softwareVersion')}"
        )
    if application.get("url") != canonical_url:
        raise ProductionSiteAuditError(
            f"SoftwareApplication URL must be {canonical_url}"
        )

    expected_download = (
        "https://github.com/becastil/Chats-empty-repo/releases/download/"
        f"v{expected_version}/repo-scout-{expected_version}.pyz"
    )
    if application.get("downloadUrl") != expected_download:
        raise ProductionSiteAuditError(
            "downloadUrl mismatch: "
            f"expected {expected_download}, found {application.get('downloadUrl')}"
        )

    offers = application.get("offers")
    if not isinstance(offers, dict):
        raise ProductionSiteAuditError("SoftwareApplication must publish one offer")
    if offers.get("price") != "0" or offers.get("url") != expected_download:
        raise ProductionSiteAuditError(
            "free software offer must use price 0 and the current download URL"
        )

    if len(services) != 1:
        raise ProductionSiteAuditError(
            "expected exactly one paid pilot Service in production JSON-LD, "
            f"found {len(services)}"
        )

    pilot_url = f"{canonical_url}#team-pilot"
    service = services[0]
    if (
        service.get("name") != "Repo Scout Founding Team Pilot"
        or service.get("url") != pilot_url
    ):
        raise ProductionSiteAuditError(
            "paid pilot Service must use the founding-team name and production "
            f"section {pilot_url}"
        )
    pilot_offer = service.get("offers")
    if not isinstance(pilot_offer, dict):
        raise ProductionSiteAuditError("paid pilot Service must publish one offer")
    if (
        pilot_offer.get("price") != "299"
        or pilot_offer.get("priceCurrency") != "USD"
        or pilot_offer.get("availability")
        != "https://schema.org/LimitedAvailability"
        or pilot_offer.get("url") != pilot_url
    ):
        raise ProductionSiteAuditError(
            "paid pilot offer must use $299 USD, limited availability, and the "
            "production pilot section"
        )

    expected_application = (
        "https://github.com/becastil/Chats-empty-repo/issues/new"
        "?template=founding-team-pilot.yml"
        "&discovery_source=Repo+Scout+website"
    )
    if expected_application not in parser.anchor_urls:
        raise ProductionSiteAuditError(
            "production must link to the website-attributed founding-team "
            f"pilot application: {expected_application}"
        )

    return (
        "canonical",
        "software-version",
        "download-url",
        "free-offer",
        "paid-service",
        "pilot-application",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Audit the deployed Repo Scout release and paid pilot conversion "
            "identity."
        )
    )
    parser.add_argument(
        "--url",
        default=DEFAULT_URL,
        help=f"Production page to audit. Defaults to {DEFAULT_URL}",
    )
    parser.add_argument(
        "--version",
        help="Expected release version. Defaults to project.version.",
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=PROJECT_ROOT,
        help="Repository root used to read pyproject.toml.",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=15.0,
        help="Network timeout in seconds. Defaults to 15.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        version = args.version or load_project_version(args.root.resolve())
        html = fetch_html(args.url, args.timeout)
        checked = audit_production_html(
            html,
            production_url=args.url,
            expected_version=version,
        )
    except ProductionSiteAuditError as exc:
        print(f"production-site-audit: {exc}", file=sys.stderr)
        return 2
    print(
        "production site audit passed: "
        f"version={version}, checks={','.join(checked)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
