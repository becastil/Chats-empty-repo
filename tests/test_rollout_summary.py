from __future__ import annotations

from contextlib import redirect_stderr, redirect_stdout
import io
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from repo_scout.rollout import (
    ROLLOUT_METADATA_END,
    ROLLOUT_METADATA_START,
    RolloutEvidenceError,
    format_rollout_metadata,
    parse_rollout_metadata,
)
from repo_scout.rollout_summary import (
    build_rollout_summary,
    format_rollout_summary,
    main,
)

POLICY_FINGERPRINT = f"sha256:{'a' * 64}"
GIT_COMMIT = "b" * 40


class RolloutSummaryTests(unittest.TestCase):
    def test_summary_is_order_independent_and_tracks_readiness_totals(self) -> None:
        ready = self._metadata("platform/api")
        remediation = self._metadata(
            "platform/web",
            policy_status="fail",
            violations=2,
            dirty_files=3,
            attention_findings=4,
        )
        reports = [("web.md", remediation), ("api.md", ready)]

        summary = build_rollout_summary(reports, include_details=True)

        self.assertEqual(
            summary,
            build_rollout_summary(
                list(reversed(reports)), include_details=True
            ),
        )
        self.assertEqual(summary["schema_version"], 2)
        self.assertEqual(
            summary["scope"],
            {
                "readiness": "bundle-reported",
                "freshness_verified": False,
                "shared_policy_verified": True,
                "policy_fingerprint_coverage": 2,
                "git_commit_coverage": 2,
                "policy_versions": [1],
            },
        )
        self.assertEqual(
            summary["summary"],
            {
                "input_reports": 2,
                "reported_ready_for_ci": 1,
                "reported_remediation_required": 1,
                "policy_pass": 1,
                "policy_fail": 1,
                "clean_worktrees": 1,
                "total_policy_violations": 2,
                "repositories_with_attention": 1,
                "total_attention_findings": 4,
            },
        )
        self.assertEqual(
            [item["repository_id"] for item in summary["repositories"]],
            ["platform/api", "platform/web"],
        )
        text = format_rollout_summary(summary)
        self.assertIn("Scope: bundle-reported", text)
        self.assertIn("shared policy verified by fingerprints", text)
        self.assertIn("Policy identity: 2/2 fingerprints", text)
        self.assertIn("Git identity: 2/2 commits recorded", text)
        self.assertIn("Repositories: 2", text)
        self.assertIn("Bundle-reported ready for CI: 1", text)
        self.assertIn("Bundle-reported remediation required: 1", text)
        self.assertIn(
            "platform/api: ready-for-ci; policy pass (0 violations); Git clean",
            text,
        )
        self.assertIn("platform/web: remediation-required; policy fail", text)

        counts_only = build_rollout_summary(reports)
        counts_text = format_rollout_summary(counts_only)
        self.assertNotIn("repositories", counts_only)
        self.assertNotIn("platform/api", counts_text)
        self.assertNotIn("platform/web", counts_text)
        self.assertNotIn("api.md", counts_text)
        self.assertNotIn("web.md", counts_text)
        self.assertNotIn(POLICY_FINGERPRINT, counts_text)
        self.assertNotIn(GIT_COMMIT, counts_text)

    def test_main_reads_markdown_bundles_and_emits_json(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            api = root / "api.md"
            web = root / "web.md"
            api.write_text(self._bundle(self._metadata("api")), encoding="utf-8")
            web.write_text(
                self._bundle(
                    self._metadata(
                        "web",
                        policy_status="fail",
                        violations=1,
                        is_repo=False,
                        branch=None,
                    )
                ),
                encoding="utf-8",
            )

            stdout = io.StringIO()
            with redirect_stdout(stdout):
                exit_code = main(["--format", "json", str(web), str(api)])

            report = json.loads(stdout.getvalue())
            self.assertEqual(exit_code, 0)
            self.assertEqual(report["summary"]["input_reports"], 2)
            self.assertEqual(report["summary"]["reported_ready_for_ci"], 1)
            self.assertEqual(report["summary"]["policy_fail"], 1)
            self.assertNotIn("repositories", report)
            self.assertNotIn(str(root), stdout.getvalue())
            self.assertNotIn('"api"', stdout.getvalue())
            self.assertNotIn('"web"', stdout.getvalue())

            stdout = io.StringIO()
            with redirect_stdout(stdout):
                detailed_exit_code = main(
                    ["--format", "json", "--details", str(web), str(api)]
                )
            detailed = json.loads(stdout.getvalue())
            self.assertEqual(detailed_exit_code, 0)
            self.assertEqual(
                detailed["repositories"][0]["repository_id"], "api"
            )
            self.assertEqual(
                detailed["repositories"][1]["repository_id"], "web"
            )
            self.assertEqual(detailed["repositories"][0]["policy_version"], 1)
            self.assertEqual(
                detailed["repositories"][0]["policy_fingerprint"],
                POLICY_FINGERPRINT,
            )
            self.assertEqual(detailed["repositories"][0]["git_commit"], GIT_COMMIT)

    def test_rejects_duplicate_repository_ids(self) -> None:
        metadata = self._metadata("api")
        with self.assertRaisesRegex(RolloutEvidenceError, "duplicate repository_id"):
            build_rollout_summary([("one.md", metadata), ("two.md", metadata)])

    def test_direct_summary_call_validates_each_bundle(self) -> None:
        legacy_with_new_field = self._metadata("legacy", schema_version=1)
        legacy_with_new_field["policy"]["fingerprint"] = POLICY_FINGERPRINT
        with self.assertRaisesRegex(RolloutEvidenceError, "legacy.md.*unknown key"):
            build_rollout_summary([("legacy.md", legacy_with_new_field)])

        malformed_current = self._metadata("current")
        malformed_current["policy"]["fingerprint"] = "sha256:invalid"
        with self.assertRaisesRegex(
            RolloutEvidenceError, "current.md.*policy.fingerprint"
        ):
            build_rollout_summary([("current.md", malformed_current)])

    def test_rejects_missing_malformed_and_inconsistent_metadata(self) -> None:
        with self.assertRaisesRegex(RolloutEvidenceError, "exactly one"):
            parse_rollout_metadata("# Plain report\n", source="plain.md")

        malformed = f"# Report\n\n{ROLLOUT_METADATA_START}{{\n{ROLLOUT_METADATA_END}\n"
        with self.assertRaisesRegex(RolloutEvidenceError, "invalid rollout metadata JSON"):
            parse_rollout_metadata(malformed, source="malformed.md")

        inconsistent = self._metadata("api")
        inconsistent["readiness"] = "remediation-required"
        encoded = json.dumps(inconsistent, indent=2, sort_keys=True)
        bundle = f"# Report\n\n{ROLLOUT_METADATA_START}{encoded}{ROLLOUT_METADATA_END}\n"
        with self.assertRaisesRegex(RolloutEvidenceError, "readiness contradicts"):
            parse_rollout_metadata(bundle, source="edited.md")

        unsupported = self._metadata("api")
        unsupported["schema_version"] = 3
        encoded = json.dumps(unsupported, indent=2, sort_keys=True)
        bundle = f"# Report\n\n{ROLLOUT_METADATA_START}{encoded}{ROLLOUT_METADATA_END}\n"
        with self.assertRaisesRegex(RolloutEvidenceError, "schema_version must be 1 or 2"):
            parse_rollout_metadata(bundle, source="future.md")

        boolean_schema = self._metadata("api")
        boolean_schema["schema_version"] = True
        encoded = json.dumps(boolean_schema, indent=2, sort_keys=True)
        bundle = f"# Report\n\n{ROLLOUT_METADATA_START}{encoded}{ROLLOUT_METADATA_END}\n"
        with self.assertRaisesRegex(RolloutEvidenceError, "schema_version must be 1 or 2"):
            parse_rollout_metadata(bundle, source="boolean.md")

        non_git_dirty = self._metadata(
            "api",
            policy_status="fail",
            violations=1,
            is_repo=False,
            branch=None,
            dirty_files=1,
        )
        encoded = json.dumps(non_git_dirty, indent=2, sort_keys=True)
        bundle = f"# Report\n\n{ROLLOUT_METADATA_START}{encoded}{ROLLOUT_METADATA_END}\n"
        with self.assertRaisesRegex(RolloutEvidenceError, "changed files"):
            parse_rollout_metadata(bundle, source="non-git-dirty.md")

        duplicate_key = json.dumps(self._metadata("api"), sort_keys=True)
        duplicate_key = duplicate_key.replace(
            '"repository_id": "api"',
            '"repository_id": "api", "repository_id": "api"',
        )
        bundle = (
            f"# Report\n\n{ROLLOUT_METADATA_START}{duplicate_key}"
            f"{ROLLOUT_METADATA_END}\n"
        )
        with self.assertRaisesRegex(RolloutEvidenceError, "duplicate key"):
            parse_rollout_metadata(bundle, source="duplicate-key.md")

    def test_schema_one_bundles_remain_compatible_without_identity_claims(self) -> None:
        legacy = self._metadata("api", schema_version=1)

        parsed = parse_rollout_metadata(self._bundle(legacy), source="legacy.md")
        summary = build_rollout_summary(
            [("legacy.md", parsed), ("current.md", self._metadata("web"))]
        )

        self.assertEqual(parsed, legacy)
        self.assertEqual(summary["scope"]["policy_fingerprint_coverage"], 1)
        self.assertEqual(summary["scope"]["git_commit_coverage"], 1)
        self.assertFalse(summary["scope"]["shared_policy_verified"])

    def test_shared_policy_requires_complete_matching_fingerprints(self) -> None:
        api = self._metadata("api")
        web = self._metadata("web")
        web["policy"]["fingerprint"] = f"sha256:{'c' * 64}"

        summary = build_rollout_summary([("api.md", api), ("web.md", web)])

        self.assertEqual(summary["scope"]["policy_fingerprint_coverage"], 2)
        self.assertFalse(summary["scope"]["shared_policy_verified"])

    def test_schema_two_rejects_invalid_policy_and_commit_identities(self) -> None:
        invalid_policy = self._metadata("api")
        invalid_policy["policy"]["fingerprint"] = "sha256:ABC"
        with self.assertRaisesRegex(RolloutEvidenceError, "policy.fingerprint"):
            parse_rollout_metadata(self._bundle_unvalidated(invalid_policy))

        invalid_commit = self._metadata("api")
        invalid_commit["git"]["commit"] = "abc123"
        with self.assertRaisesRegex(RolloutEvidenceError, "git.commit"):
            parse_rollout_metadata(self._bundle_unvalidated(invalid_commit))

        non_git_commit = self._metadata(
            "api", policy_status="fail", violations=1, is_repo=False, branch=None
        )
        non_git_commit["git"]["commit"] = GIT_COMMIT
        with self.assertRaisesRegex(RolloutEvidenceError, "non-Git.*commit"):
            parse_rollout_metadata(self._bundle_unvalidated(non_git_commit))

        missing_commit = self._metadata("api")
        missing_commit["git"]["commit"] = None
        with self.assertRaisesRegex(RolloutEvidenceError, "readiness contradicts"):
            parse_rollout_metadata(self._bundle_unvalidated(missing_commit))

    def test_main_reports_input_errors_without_stdout(self) -> None:
        stderr = io.StringIO()
        stdout = io.StringIO()
        with redirect_stderr(stderr), redirect_stdout(stdout):
            exit_code = main(["missing.md"])

        self.assertEqual(exit_code, 2)
        self.assertEqual(stdout.getvalue(), "")
        self.assertIn("could not read missing.md", stderr.getvalue())

    @staticmethod
    def _bundle(metadata: dict[str, object]) -> str:
        return (
            "# Repo Scout Snapshot\n\n"
            f"{ROLLOUT_METADATA_START}"
            f"{format_rollout_metadata(metadata)}"
            f"{ROLLOUT_METADATA_END}\n"
        )

    @staticmethod
    def _bundle_unvalidated(metadata: dict[str, object]) -> str:
        return (
            f"# Report\n\n{ROLLOUT_METADATA_START}"
            f"{json.dumps(metadata, sort_keys=True)}"
            f"{ROLLOUT_METADATA_END}\n"
        )

    @staticmethod
    def _metadata(
        repository_id: str,
        *,
        schema_version: int = 2,
        policy_status: str = "pass",
        violations: int = 0,
        is_repo: bool = True,
        branch: str | None = "main",
        dirty_files: int = 0,
        attention_findings: int = 0,
    ) -> dict[str, object]:
        clean = is_repo and dirty_files == 0
        policy = {
            "version": 1,
            "status": policy_status,
            "rules_checked": 3,
            "violations": violations,
        }
        git = {
            "is_repo": is_repo,
            "branch": branch,
            "dirty_files": dirty_files,
            "clean": clean,
        }
        if schema_version >= 2:
            policy["fingerprint"] = POLICY_FINGERPRINT
            git["commit"] = GIT_COMMIT if is_repo else None
        return {
            "schema_version": schema_version,
            "repository_id": repository_id,
            "readiness": (
                "ready-for-ci"
                if policy_status == "pass" and clean
                else "remediation-required"
            ),
            "policy": policy,
            "git": git,
            "attention_findings": attention_findings,
        }


if __name__ == "__main__":
    unittest.main()
