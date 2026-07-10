from __future__ import annotations

from contextlib import redirect_stderr, redirect_stdout
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from repo_scout.distribution import (  # noqa: E402
    DistributionInputError,
    build_distribution_report,
    format_distribution_report,
    main,
)


class DistributionReportTests(unittest.TestCase):
    def test_summarizes_portable_and_wheel_requests_across_contract_versions(
        self,
    ) -> None:
        payload = [
            self._release(
                "v0.3.3",
                {
                    "repo_scout-0.3.3-py3-none-any.whl": 5,
                    "repo_scout-0.3.3.tar.gz": 1,
                    "SHA256SUMS": 2,
                },
            ),
            self._release(
                "v0.3.4",
                {
                    "repo-scout-0.3.4.pyz": 8,
                    "repo_scout-0.3.4-py3-none-any.whl": 3,
                    "repo_scout-0.3.4.tar.gz": 2,
                    "SHA256SUMS": 4,
                },
            ),
            self._release("nightly", {}, draft=True),
            self._release("v0.4.0-rc.1", {}, prerelease=True),
        ]

        report = build_distribution_report(payload)

        self.assertEqual(report["schema_version"], 1)
        self.assertEqual(report["summary"]["input_releases"], 4)
        self.assertEqual(report["summary"]["stable_releases"], 2)
        self.assertEqual(report["summary"]["complete_releases"], 2)
        self.assertEqual(report["summary"]["draft_releases"], 1)
        self.assertEqual(report["summary"]["prerelease_releases"], 1)
        self.assertEqual(report["summary"]["portable_downloads"], 8)
        self.assertEqual(report["summary"]["wheel_downloads"], 8)
        self.assertEqual(report["summary"]["primary_artifact_downloads"], 16)
        self.assertEqual(report["summary"]["source_downloads"], 3)
        self.assertEqual(report["summary"]["manifest_downloads"], 6)
        self.assertEqual(
            report["summary"]["portable_primary_share_percent"], 50.0
        )
        self.assertEqual(report["latest"]["tag"], "v0.3.4")
        self.assertEqual(
            [release["tag"] for release in report["releases"]],
            ["v0.3.4", "v0.3.3"],
        )
        self.assertNotIn(
            "repo-scout-0.3.3.pyz",
            report["releases"][1]["contract"]["expected_artifacts"],
        )
        self.assertEqual(report["warnings"], [])
        self.assertIn("CI jobs", report["measurement_note"])
        self.assertIn("not unique installs", report["measurement_note"])
        self.assertEqual(report, build_distribution_report(list(reversed(payload))))

        text = format_distribution_report(report)
        self.assertIn(
            "Primary artifact downloads: 16 total / 8 portable / 8 wheel", text
        )
        self.assertIn("Portable primary share: 50.0%", text)
        self.assertIn("v0.3.4 [complete]", text)
        self.assertIn("Warnings:\n  none", text)

    def test_flags_missing_and_unexpected_release_artifacts(self) -> None:
        payload = [
            self._release(
                "v0.3.4",
                {
                    "repo_scout-0.3.4-py3-none-any.whl": 2,
                    "repo_scout-0.3.4.tar.gz": 1,
                    "SHA256SUMS": 1,
                    "notes.txt": 7,
                },
            )
        ]

        report = build_distribution_report(payload)
        release = report["latest"]

        self.assertFalse(release["contract"]["complete"])
        self.assertEqual(
            release["contract"]["missing_artifacts"],
            ["repo-scout-0.3.4.pyz"],
        )
        self.assertEqual(
            release["contract"]["unexpected_artifacts"], ["notes.txt"]
        )
        self.assertEqual(release["downloads"]["primary"], 2)
        self.assertEqual(release["downloads"]["unknown"], 7)
        self.assertEqual(report["summary"]["complete_releases"], 0)
        self.assertEqual(
            [warning["kind"] for warning in report["warnings"]],
            ["missing_artifacts", "unexpected_artifacts"],
        )
        self.assertIn("v0.3.4 [drift]", format_distribution_report(report))

    def test_empty_export_has_explicit_zero_state(self) -> None:
        report = build_distribution_report([])

        self.assertIsNone(report["latest"])
        self.assertIsNone(report["summary"]["portable_primary_share_percent"])
        self.assertEqual(report["summary"]["primary_artifact_downloads"], 0)
        self.assertIn("Portable primary share: n/a", format_distribution_report(report))
        self.assertIn("Releases:\n  none", format_distribution_report(report))

    def test_rejects_malformed_or_ambiguous_release_evidence(self) -> None:
        valid = self._release(
            "v0.3.4",
            {
                "repo-scout-0.3.4.pyz": 0,
                "repo_scout-0.3.4-py3-none-any.whl": 0,
                "repo_scout-0.3.4.tar.gz": 0,
                "SHA256SUMS": 0,
            },
        )
        cases = [
            (None, "JSON array"),
            ([{**valid, "tag_name": "latest"}], "vMAJOR.MINOR.PATCH"),
            ([{**valid, "draft": "false"}], "draft must be a boolean"),
            ([{**valid, "assets": "none"}], "assets must be an array"),
            (
                [
                    {
                        **valid,
                        "assets": [
                            {"name": "SHA256SUMS", "download_count": True}
                        ],
                    }
                ],
                "non-negative integer",
            ),
            (
                [
                    {
                        **valid,
                        "assets": [
                            {"name": "SHA256SUMS", "download_count": 0},
                            {"name": "SHA256SUMS", "download_count": 1},
                        ],
                    }
                ],
                "duplicate asset name",
            ),
            ([valid, valid], "duplicate tag"),
        ]
        for payload, message in cases:
            with self.subTest(message=message), self.assertRaisesRegex(
                DistributionInputError, message
            ):
                build_distribution_report(payload)

    def test_cli_supports_stdin_json_and_module_execution(self) -> None:
        payload = [
            self._release(
                "v0.3.4",
                {
                    "repo-scout-0.3.4.pyz": 3,
                    "repo_scout-0.3.4-py3-none-any.whl": 1,
                    "repo_scout-0.3.4.tar.gz": 0,
                    "SHA256SUMS": 2,
                },
            )
        ]
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            exit_code = main(
                ["--format", "json"], stdin=io.StringIO(json.dumps(payload))
            )

        self.assertEqual(exit_code, 0)
        self.assertEqual(
            json.loads(stdout.getvalue())["summary"]["primary_artifact_downloads"],
            4,
        )

        environment = os.environ.copy()
        environment["PYTHONPATH"] = str(ROOT / "src")
        completed = subprocess.run(
            [
                sys.executable,
                "-m",
                "repo_scout.distribution",
                "--format",
                "json",
            ],
            cwd=ROOT.parent,
            env=environment,
            input=json.dumps(payload),
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(
            json.loads(completed.stdout)["summary"]["portable_downloads"], 3
        )

    def test_cli_rejects_invalid_json_without_stdout(self) -> None:
        stdout = io.StringIO()
        stderr = io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            exit_code = main([], stdin=io.StringIO("["))

        self.assertEqual(exit_code, 2)
        self.assertEqual(stdout.getvalue(), "")
        self.assertIn("invalid JSON", stderr.getvalue())

    @staticmethod
    def _release(
        tag: str,
        assets: dict[str, int],
        *,
        draft: bool = False,
        prerelease: bool = False,
    ) -> dict[str, object]:
        return {
            "tag_name": tag,
            "draft": draft,
            "prerelease": prerelease,
            "published_at": "2026-07-10T00:00:00Z",
            "html_url": f"https://example.invalid/releases/{tag}",
            "assets": [
                {"name": name, "download_count": count}
                for name, count in assets.items()
            ],
        }


if __name__ == "__main__":
    unittest.main()
