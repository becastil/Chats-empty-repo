from __future__ import annotations

from contextlib import redirect_stderr, redirect_stdout
import io
import json
import os
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
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

        self.assertEqual(report["schema_version"], 2)
        self.assertIsNone(report["change"])
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
        self.assertIn("Baseline change: not provided", text)

    def test_compares_current_counts_to_schema_one_baseline(self) -> None:
        baseline_payload = [
            self._release(
                "v0.3.4",
                {
                    "repo-scout-0.3.4.pyz": 2,
                    "repo_scout-0.3.4-py3-none-any.whl": 3,
                    "repo_scout-0.3.4.tar.gz": 1,
                    "SHA256SUMS": 2,
                },
            )
        ]
        baseline = build_distribution_report(baseline_payload)
        baseline["schema_version"] = 1
        baseline.pop("change")
        current_payload = [
            self._release(
                "v0.3.5",
                {
                    "repo-scout-0.3.5.pyz": 0,
                    "repo_scout-0.3.5-py3-none-any.whl": 0,
                    "repo_scout-0.3.5.tar.gz": 0,
                    "SHA256SUMS": 0,
                },
            ),
            self._release(
                "v0.3.4",
                {
                    "repo-scout-0.3.4.pyz": 5,
                    "repo_scout-0.3.4-py3-none-any.whl": 4,
                    "repo_scout-0.3.4.tar.gz": 1,
                    "SHA256SUMS": 3,
                },
            ),
        ]

        report = build_distribution_report(current_payload, baseline=baseline)
        change = report["change"]

        self.assertEqual(change["baseline_schema_version"], 1)
        self.assertEqual(change["new_releases"], ["v0.3.5"])
        self.assertEqual(change["removed_releases"], [])
        self.assertEqual(change["primary_artifact_downloads_delta"], 4)
        self.assertEqual(change["portable_downloads_delta"], 3)
        self.assertEqual(change["wheel_downloads_delta"], 1)
        self.assertEqual(change["source_downloads_delta"], 0)
        self.assertEqual(change["manifest_downloads_delta"], 1)
        self.assertEqual(change["unknown_downloads_delta"], 0)
        self.assertEqual(report["warnings"], [])
        text = format_distribution_report(report)
        self.assertIn(
            "Baseline change: +4 primary / +3 portable / +1 wheel / "
            "+0 source / +1 manifests / +0 unknown",
            text,
        )
        self.assertIn("Release set: 1 new / 0 removed", text)

    def test_warns_when_cumulative_evidence_decreases_or_disappears(self) -> None:
        baseline = build_distribution_report(
            [
                self._release(
                    "v0.3.4",
                    {
                        "repo-scout-0.3.4.pyz": 5,
                        "repo_scout-0.3.4-py3-none-any.whl": 4,
                        "repo_scout-0.3.4.tar.gz": 1,
                        "SHA256SUMS": 2,
                    },
                ),
                self._release(
                    "v0.3.3",
                    {
                        "repo_scout-0.3.3-py3-none-any.whl": 2,
                        "repo_scout-0.3.3.tar.gz": 1,
                        "SHA256SUMS": 1,
                    },
                ),
            ]
        )
        current = [
            self._release(
                "v0.3.4",
                {
                    "repo-scout-0.3.4.pyz": 3,
                    "repo_scout-0.3.4-py3-none-any.whl": 4,
                    "repo_scout-0.3.4.tar.gz": 1,
                },
            )
        ]

        report = build_distribution_report(current, baseline=baseline)

        self.assertEqual(report["change"]["removed_releases"], ["v0.3.3"])
        self.assertEqual(report["change"]["portable_downloads_delta"], -2)
        self.assertEqual(report["change"]["wheel_downloads_delta"], -2)
        self.assertEqual(
            [warning["kind"] for warning in report["warnings"]],
            [
                "assets_removed_since_baseline",
                "download_count_decreased",
                "missing_artifacts",
                "release_removed_since_baseline",
            ],
        )
        self.assertEqual(report["summary"]["warning_count"], 4)
        self.assertIn("Baseline change: -4 primary", format_distribution_report(report))

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

    def test_rejects_malformed_baseline_reports(self) -> None:
        current = [
            self._release(
                "v0.3.4",
                {
                    "repo-scout-0.3.4.pyz": 0,
                    "repo_scout-0.3.4-py3-none-any.whl": 0,
                    "repo_scout-0.3.4.tar.gz": 0,
                    "SHA256SUMS": 0,
                },
            )
        ]
        valid = build_distribution_report(current)
        duplicate_release = valid["releases"][0]
        cases = [
            ([], "JSON object"),
            ({"schema_version": 3, "releases": []}, "schema_version"),
            ({"schema_version": True, "releases": []}, "schema_version"),
            ({"schema_version": 1}, "releases must be an array"),
            (
                {
                    "schema_version": 1,
                    "releases": [duplicate_release, duplicate_release],
                },
                "duplicate tag",
            ),
            (
                {
                    "schema_version": 1,
                    "releases": [{**duplicate_release, "assets": "none"}],
                },
                "assets must be an array",
            ),
        ]
        for baseline, message in cases:
            with self.subTest(message=message), self.assertRaisesRegex(
                DistributionInputError, message
            ):
                build_distribution_report(current, baseline=baseline)

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

        baseline_payload = [
            self._release(
                "v0.3.4",
                {
                    "repo-scout-0.3.4.pyz": 1,
                    "repo_scout-0.3.4-py3-none-any.whl": 1,
                    "repo_scout-0.3.4.tar.gz": 0,
                    "SHA256SUMS": 1,
                },
            )
        ]
        with TemporaryDirectory() as tmp:
            baseline_path = Path(tmp) / "baseline.json"
            baseline_path.write_text(
                json.dumps(build_distribution_report(baseline_payload)),
                encoding="utf-8",
            )
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                exit_code = main(
                    ["--format", "json", "--baseline", str(baseline_path)],
                    stdin=io.StringIO(json.dumps(payload)),
                )
        self.assertEqual(exit_code, 0)
        self.assertEqual(
            json.loads(stdout.getvalue())["change"]["portable_downloads_delta"],
            2,
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
