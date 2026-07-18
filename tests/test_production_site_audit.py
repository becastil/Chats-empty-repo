from __future__ import annotations

from contextlib import redirect_stderr, redirect_stdout
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
VERSION = "0.3.45"


def page(
    *,
    canonical_url: str = URL,
    software_version: str = VERSION,
    download_url: str | None = None,
) -> str:
    resolved_download = download_url or (
        "https://github.com/becastil/Chats-empty-repo/releases/download/"
        f"v{software_version}/repo-scout-{software_version}.pyz"
    )
    structured_data = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "SoftwareApplication",
                "url": canonical_url,
                "softwareVersion": software_version,
                "downloadUrl": resolved_download,
                "offers": {
                    "@type": "Offer",
                    "price": "0",
                    "url": resolved_download,
                },
            },
            {
                "@type": "Service",
                "name": "Repo Scout Founding Team Pilot",
            },
        ],
    }
    return (
        "<!doctype html><html><head>"
        f'<link rel="canonical" href="{canonical_url}">'
        '<script type="application/ld+json">'
        f"{json.dumps(structured_data)}"
        "</script></head><body></body></html>"
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
            ("canonical", "software-version", "download-url", "free-offer"),
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
        self.assertIn("version=0.3.45", stdout.getvalue())
        self.assertIn("software-version", stdout.getvalue())

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
