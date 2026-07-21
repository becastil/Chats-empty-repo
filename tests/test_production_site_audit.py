from __future__ import annotations

from contextlib import redirect_stderr, redirect_stdout
from html import escape
import importlib.util
from io import StringIO
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "audit_production_site.py"
SPEC = importlib.util.spec_from_file_location("audit_production_site", SCRIPT_PATH)
assert SPEC is not None
assert SPEC.loader is not None
audit_production_site = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = audit_production_site
SPEC.loader.exec_module(audit_production_site)

URL = "https://repo-scout.becastil.chatgpt.site/"
VERSION = "0.3.48"
PILOT_URL = f"{URL}#team-pilot"
PILOT_APPLICATION_URL = (
    "https://github.com/becastil/Chats-empty-repo/issues/new"
    "?template=founding-team-pilot.yml"
    "&discovery_source=Repo+Scout+website"
)


def page(
    *,
    canonical_url: str = URL,
    software_version: str = VERSION,
    download_url: str | None = None,
    pilot_price: str = "299",
    pilot_service_count: int = 1,
    pilot_application_url: str | None = PILOT_APPLICATION_URL,
) -> str:
    resolved_download = download_url or (
        "https://github.com/becastil/Chats-empty-repo/releases/download/"
        f"v{software_version}/repo-scout-{software_version}.pyz"
    )
    software = {
        "@type": "SoftwareApplication",
        "url": canonical_url,
        "softwareVersion": software_version,
        "downloadUrl": resolved_download,
        "offers": {
            "@type": "Offer",
            "price": "0",
            "url": resolved_download,
        },
    }
    pilot_service = {
        "@type": "Service",
        "name": "Repo Scout Founding Team Pilot",
        "url": PILOT_URL,
        "offers": {
            "@type": "Offer",
            "price": pilot_price,
            "priceCurrency": "USD",
            "availability": "https://schema.org/LimitedAvailability",
            "url": PILOT_URL,
        },
    }
    structured_data = {
        "@context": "https://schema.org",
        "@graph": [
            software,
            *[pilot_service for _ in range(pilot_service_count)],
        ],
    }
    pilot_application_link = ""
    if pilot_application_url is not None:
        pilot_application_link = (
            f'<a href="{escape(pilot_application_url, quote=True)}">'
            "Apply for the Repo Scout Founding Team Pilot"
            "</a>"
        )
    return (
        "<!doctype html><html><head>"
        f'<link rel="canonical" href="{canonical_url}">'
        '<script type="application/ld+json">'
        f"{json.dumps(structured_data)}"
        f"</script></head><body>{pilot_application_link}</body></html>"
    )


class ProductionSiteAuditTests(unittest.TestCase):
    def test_accepts_current_canonical_release_offer(self) -> None:
        checked = audit_production_site.audit_production_html(
            page(),
            production_url=URL,
            expected_version=VERSION,
        )

        self.assertEqual(
            checked,
            (
                "canonical",
                "software-version",
                "download-url",
                "free-offer",
                "paid-service",
                "pilot-application",
            ),
        )

    def test_rejects_wrong_paid_pilot_price(self) -> None:
        for stale_price in ("0", "399"):
            with (
                self.subTest(pilot_price=stale_price),
                self.assertRaisesRegex(
                    audit_production_site.ProductionSiteAuditError,
                    "paid pilot offer",
                ),
            ):
                audit_production_site.audit_production_html(
                    page(pilot_price=stale_price),
                    production_url=URL,
                    expected_version=VERSION,
                )

    def test_rejects_missing_or_duplicate_paid_pilot_service(self) -> None:
        for service_count in (0, 2):
            with (
                self.subTest(pilot_service_count=service_count),
                self.assertRaisesRegex(
                    audit_production_site.ProductionSiteAuditError,
                    "exactly one paid pilot Service",
                ),
            ):
                audit_production_site.audit_production_html(
                    page(pilot_service_count=service_count),
                    production_url=URL,
                    expected_version=VERSION,
                )

    def test_rejects_missing_or_wrong_visible_pilot_application_link(self) -> None:
        wrong_source_url = (
            "https://github.com/becastil/Chats-empty-repo/issues/new"
            "?template=founding-team-pilot.yml"
            "&discovery_source=GitHub+repository+or+release"
        )
        for label, application_url in (
            ("missing", None),
            ("wrong", wrong_source_url),
        ):
            with (
                self.subTest(case=label),
                self.assertRaisesRegex(
                    audit_production_site.ProductionSiteAuditError,
                    "pilot application",
                ),
            ):
                audit_production_site.audit_production_html(
                    page(pilot_application_url=application_url),
                    production_url=URL,
                    expected_version=VERSION,
                )

    def test_rejects_stale_software_version(self) -> None:
        with self.assertRaisesRegex(
            audit_production_site.ProductionSiteAuditError,
            "softwareVersion mismatch",
        ):
            audit_production_site.audit_production_html(
                page(software_version="0.3.44"),
                production_url=URL,
                expected_version=VERSION,
            )

    def test_rejects_stale_download_url(self) -> None:
        stale_download = (
            "https://github.com/becastil/Chats-empty-repo/releases/download/"
            "v0.3.44/repo-scout-0.3.44.pyz"
        )
        with self.assertRaisesRegex(
            audit_production_site.ProductionSiteAuditError,
            "downloadUrl mismatch",
        ):
            audit_production_site.audit_production_html(
                page(download_url=stale_download),
                production_url=URL,
                expected_version=VERSION,
            )

    def test_rejects_missing_structured_software_offer(self) -> None:
        html = f'<link rel="canonical" href="{URL}">'
        with self.assertRaisesRegex(
            audit_production_site.ProductionSiteAuditError,
            "exactly one SoftwareApplication",
        ):
            audit_production_site.audit_production_html(
                html,
                production_url=URL,
                expected_version=VERSION,
            )

    def test_main_uses_project_version_and_reports_checked_contract(self) -> None:
        stdout = StringIO()
        with (
            patch.object(audit_production_site, "fetch_html", return_value=page()),
            redirect_stdout(stdout),
        ):
            result = audit_production_site.main(
                ["--root", str(ROOT), "--url", URL]
            )

        self.assertEqual(result, 0)
        self.assertIn("version=0.3.48", stdout.getvalue())
        self.assertIn("software-version", stdout.getvalue())
        self.assertIn("paid-service", stdout.getvalue())
        self.assertIn("pilot-application", stdout.getvalue())

    def test_main_fails_without_hiding_stale_production(self) -> None:
        stderr = StringIO()
        with (
            patch.object(
                audit_production_site,
                "fetch_html",
                return_value=page(software_version="0.3.44"),
            ),
            redirect_stderr(stderr),
        ):
            result = audit_production_site.main(
                ["--root", str(ROOT), "--url", URL]
            )

        self.assertEqual(result, 2)
        self.assertIn("softwareVersion mismatch", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
