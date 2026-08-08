from __future__ import annotations

from contextlib import redirect_stderr, redirect_stdout
import io
import json
import os
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from repo_scout.rollout import (
    MAX_GIT_BRANCH_CHARACTERS,
    MAX_ROLLOUT_EVIDENCE_BYTES,
    ROLLOUT_METADATA_END,
    ROLLOUT_METADATA_START,
    RolloutEvidenceError,
    format_rollout_metadata,
    load_rollout_metadata,
    parse_rollout_metadata,
    validate_repository_id,
    validate_rollout_metadata,
)
from repo_scout.rollout_summary import (
    build_rollout_summary,
    format_rollout_summary,
    main,
)

POLICY_FINGERPRINT = f"sha256:{'a' * 64}"
EXCEPTION_LEDGER_FINGERPRINT = f"sha256:{'d' * 64}"
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
        self.assertEqual(summary["schema_version"], 3)
        self.assertEqual(
            summary["scope"],
            {
                "readiness": "bundle-reported",
                "freshness_verified": False,
                "shared_policy_verified": True,
                "policy_fingerprint_coverage": 2,
                "git_commit_coverage": 2,
                "exception_ledger_coverage": 0,
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
                "policy_enforcement_pass": 1,
                "policy_enforcement_pass_with_exceptions": 0,
                "policy_enforcement_fail": 1,
                "repositories_with_applied_exceptions": 0,
                "total_exception_decisions": 0,
                "total_applied_exceptions": 0,
                "total_expired_exceptions": 0,
                "total_pending_exceptions": 0,
                "total_stale_exceptions": 0,
                "total_unresolved_violations": 2,
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
        self.assertIn("shared base policy verified by fingerprints", text)
        self.assertIn("Policy identity: 2/2 fingerprints", text)
        self.assertIn("Git identity: 2/2 commits recorded", text)
        self.assertIn("Repositories: 2", text)
        self.assertIn("Bundle-reported ready for CI: 1", text)
        self.assertIn("Bundle-reported remediation required: 1", text)
        self.assertIn(
            (
                "platform/api: ready-for-ci; policy pass (0 violations); "
                "enforcement pass (0 unresolved, 0 exceptions applied); Git clean"
            ),
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

    def test_schema_three_reports_raw_failures_and_effective_exceptions(self) -> None:
        api = self._metadata(
            "platform/api",
            schema_version=3,
            policy_status="fail",
            violations=1,
            enforcement_status="pass-with-exceptions",
            applied=1,
            unresolved=0,
        )
        web = self._metadata("platform/web")

        validated = validate_rollout_metadata(api)
        summary = build_rollout_summary(
            [("api.md", validated), ("web.md", web)], include_details=True
        )

        self.assertEqual(validated["readiness"], "ready-for-ci")
        self.assertEqual(validated["policy"]["status"], "fail")
        self.assertEqual(
            validated["policy"]["enforcement_status"], "pass-with-exceptions"
        )
        self.assertEqual(summary["scope"]["exception_ledger_coverage"], 1)
        self.assertEqual(
            summary["summary"]["policy_enforcement_pass_with_exceptions"], 1
        )
        self.assertEqual(summary["summary"]["total_policy_violations"], 1)
        self.assertEqual(summary["summary"]["total_applied_exceptions"], 1)
        self.assertEqual(summary["summary"]["total_unresolved_violations"], 0)
        text = format_rollout_summary(summary)
        self.assertIn("1 pass with exceptions", text)
        self.assertIn("1 applied across 1 repositories", text)
        self.assertNotIn(EXCEPTION_LEDGER_FINGERPRINT, text.split("Repository details:")[0])

    def test_schema_three_rejects_inconsistent_exception_evidence(self) -> None:
        cases = []
        wrong_total = self._metadata(
            "api",
            schema_version=3,
            policy_status="fail",
            violations=1,
            enforcement_status="pass-with-exceptions",
            applied=1,
            unresolved=0,
        )
        wrong_total["policy"]["exception_decisions_total"] = 2
        cases.append((wrong_total, "counts do not reconcile"))

        unresolved_pass = self._metadata(
            "api",
            schema_version=3,
            policy_status="fail",
            violations=2,
            enforcement_status="pass-with-exceptions",
            applied=1,
            unresolved=0,
        )
        unresolved_pass["policy"]["unresolved_violations"] = 1
        cases.append((unresolved_pass, "pass-with-exceptions contradicts"))

        invalid_fingerprint = self._metadata(
            "api",
            schema_version=3,
            policy_status="fail",
            violations=1,
            enforcement_status="pass-with-exceptions",
            applied=1,
            unresolved=0,
        )
        invalid_fingerprint["policy"]["exception_ledger_fingerprint"] = "sha256:bad"
        cases.append((invalid_fingerprint, "exception_ledger_fingerprint"))

        missing_applied = self._metadata(
            "api",
            schema_version=3,
            policy_status="fail",
            violations=2,
            enforcement_status="fail",
            applied=1,
            unresolved=0,
        )
        cases.append((missing_applied, "raw policy violations do not reconcile"))

        for metadata, message in cases:
            with self.subTest(message=message), self.assertRaisesRegex(
                RolloutEvidenceError, message
            ):
                validate_rollout_metadata(metadata)

    def test_rejects_duplicate_repository_ids(self) -> None:
        metadata = self._metadata("api")
        with self.assertRaisesRegex(RolloutEvidenceError, "duplicate repository_id"):
            build_rollout_summary([("one.md", metadata), ("two.md", metadata)])

    def test_rejects_unsafe_repository_ids_without_echoing_them(self) -> None:
        unsafe_repository_ids = (
            "",
            " platform/api",
            "platform/api ",
            "platform/api\nRepositories: 999",
            "platform/api\x1b[31m",
            "platform/api\u009b31m",
            "platform/api\u202eattack",
            "platform/api\u2028Repositories: 999",
            "x" * 129,
        )
        expected_error = (
            "repository_id must be a non-empty printable string of at most "
            "128 characters without surrounding whitespace"
        )

        for repository_id in unsafe_repository_ids:
            with self.subTest(repository_id=repr(repository_id)):
                with self.assertRaises(RolloutEvidenceError) as raised:
                    validate_repository_id(repository_id)

                self.assertEqual(str(raised.exception), expected_error)
                if repository_id:
                    self.assertNotIn(repository_id, str(raised.exception))

    def test_accepts_bounded_printable_repository_ids(self) -> None:
        for repository_id in (
            "platform/api",
            "équipe/café",
            "x" * 128,
        ):
            with self.subTest(repository_id=repository_id):
                self.assertEqual(
                    validate_repository_id(repository_id),
                    repository_id,
                )

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
        unsupported["schema_version"] = 4
        encoded = json.dumps(unsupported, indent=2, sort_keys=True)
        bundle = f"# Report\n\n{ROLLOUT_METADATA_START}{encoded}{ROLLOUT_METADATA_END}\n"
        with self.assertRaisesRegex(
            RolloutEvidenceError, "schema_version must be 1, 2, or 3"
        ):
            parse_rollout_metadata(bundle, source="future.md")

        boolean_schema = self._metadata("api")
        boolean_schema["schema_version"] = True
        encoded = json.dumps(boolean_schema, indent=2, sort_keys=True)
        bundle = f"# Report\n\n{ROLLOUT_METADATA_START}{encoded}{ROLLOUT_METADATA_END}\n"
        with self.assertRaisesRegex(
            RolloutEvidenceError, "schema_version must be 1, 2, or 3"
        ):
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

    def test_duplicate_json_key_error_escapes_presentation_controls(self) -> None:
        injected_key = "\nRepositories: 999\u009b\u202e"
        encoded_key = json.dumps(injected_key)
        duplicate_key = f"{{{encoded_key}: 1, {encoded_key}: 2}}"
        bundle = (
            f"# Report\n\n{ROLLOUT_METADATA_START}{duplicate_key}"
            f"{ROLLOUT_METADATA_END}\n"
        )

        with self.assertRaises(RolloutEvidenceError) as raised:
            parse_rollout_metadata(bundle, source="duplicate-key.md")

        message = str(raised.exception)
        self.assertIn(f"duplicate key: {encoded_key}", message)
        self.assertNotIn("\nRepositories: 999", message)
        self.assertNotIn("\u009b", message)
        self.assertNotIn("\u202e", message)

    def test_unknown_key_errors_escape_presentation_controls(self) -> None:
        ordinary = self._metadata("api")
        ordinary["extra"] = True
        with self.assertRaises(RolloutEvidenceError) as raised:
            validate_rollout_metadata(ordinary)
        self.assertEqual(
            str(raised.exception),
            "metadata has unknown key: extra",
        )

        injected_key = (
            "\nRepositories: 999\r\x1b\u009b\u2028\u202e"
        )
        encoded_key = json.dumps(injected_key)
        cases = []

        top_level = self._metadata("api")
        top_level[injected_key] = True
        cases.append(("metadata", top_level))

        policy = self._metadata("api")
        policy["policy"][injected_key] = True
        cases.append(("policy", policy))

        git = self._metadata("api")
        git["git"][injected_key] = True
        cases.append(("git", git))

        for location, metadata in cases:
            with self.subTest(location=location):
                with self.assertRaises(RolloutEvidenceError) as raised:
                    parse_rollout_metadata(
                        self._bundle_unvalidated(metadata),
                        source=f"{location}.md",
                    )

                message = str(raised.exception)
                self.assertIn(
                    f"{location} has unknown key: {encoded_key}",
                    message,
                )
                self.assertEqual(len(message.splitlines()), 1)
                self.assertNotIn("\nRepositories: 999", message)
                self.assertNotIn("\r", message)
                self.assertNotIn("\x1b", message)
                self.assertNotIn("\u009b", message)
                self.assertNotIn("\u2028", message)
                self.assertNotIn("\u202e", message)

        with self.assertRaises(RolloutEvidenceError) as raised:
            build_rollout_summary([("direct.md", top_level)])

        message = str(raised.exception)
        self.assertIn(
            f"metadata has unknown key: {encoded_key}",
            message,
        )
        self.assertEqual(len(message.splitlines()), 1)
        self.assertNotIn("\nRepositories: 999", message)
        self.assertNotIn("\r", message)
        self.assertNotIn("\x1b", message)
        self.assertNotIn("\u009b", message)
        self.assertNotIn("\u2028", message)
        self.assertNotIn("\u202e", message)

    def test_unsafe_source_labels_are_escaped_in_validation_errors(self) -> None:
        ordinary_source = "reports/café.md"
        with self.assertRaises(RolloutEvidenceError) as raised:
            parse_rollout_metadata("# Plain report\n", source=ordinary_source)
        self.assertEqual(
            str(raised.exception),
            (
                f"{ordinary_source} must contain exactly one rollout "
                "metadata section"
            ),
        )

        source = (
            "bundle\nRepositories: 999\r\x1b\u009b\u2028\u202e.md"
        )
        encoded_source = json.dumps(source)

        with self.assertRaises(RolloutEvidenceError) as raised:
            parse_rollout_metadata("# Plain report\n", source=source)

        message = str(raised.exception)
        self.assertIn(encoded_source, message)
        self.assertEqual(len(message.splitlines()), 1)
        self.assertNotIn("\nRepositories: 999", message)
        self.assertNotIn("\r", message)
        self.assertNotIn("\x1b", message)
        self.assertNotIn("\u009b", message)
        self.assertNotIn("\u2028", message)
        self.assertNotIn("\u202e", message)

        invalid = self._metadata("api")
        invalid["policy"]["fingerprint"] = "sha256:invalid"
        with self.assertRaises(RolloutEvidenceError) as raised:
            build_rollout_summary([(source, invalid)])

        message = str(raised.exception)
        self.assertIn(encoded_source, message)
        self.assertEqual(len(message.splitlines()), 1)
        self.assertNotIn("\nRepositories: 999", message)
        self.assertNotIn("\r", message)
        self.assertNotIn("\x1b", message)
        self.assertNotIn("\u009b", message)
        self.assertNotIn("\u2028", message)
        self.assertNotIn("\u202e", message)

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

    def test_rejects_unsafe_git_branch_text_without_echoing_it(self) -> None:
        invalid_branches = (
            "",
            " main",
            "main ",
            "main\nBundle-reported ready for CI: 999",
            "main\x1b[31m",
            "main\u202eattack",
            "main\u2028Injected metric",
            "x" * (MAX_GIT_BRANCH_CHARACTERS + 1),
        )
        expected_error = (
            "git.branch must be null or a non-empty printable string "
            f"of at most {MAX_GIT_BRANCH_CHARACTERS} characters without "
            "surrounding whitespace"
        )

        for branch in invalid_branches:
            with self.subTest(branch=repr(branch)):
                metadata = self._metadata("api", branch=branch)
                with self.assertRaises(RolloutEvidenceError) as raised:
                    validate_rollout_metadata(metadata)

                self.assertEqual(str(raised.exception), expected_error)
                if branch:
                    self.assertNotIn(branch, str(raised.exception))

    def test_main_rejects_repository_id_presentation_controls_without_output(
        self,
    ) -> None:
        injected_marker = "Repositories: 999"
        repository_id = f"company/api\u2028{injected_marker}\u202e"
        with TemporaryDirectory() as tmp:
            legacy_path = Path(tmp) / "legacy.md"
            current_path = Path(tmp) / "current.md"
            legacy_path.write_text(
                self._bundle_unvalidated(
                    self._metadata(repository_id, schema_version=1)
                ),
                encoding="utf-8",
            )
            current_path.write_text(
                self._bundle_unvalidated(self._metadata(repository_id)),
                encoding="utf-8",
            )
            original_legacy = legacy_path.read_bytes()
            original_current = current_path.read_bytes()

            stdout = io.StringIO()
            stderr = io.StringIO()
            with redirect_stdout(stdout), redirect_stderr(stderr):
                exit_code = main(
                    ["--details", str(legacy_path), str(current_path)]
                )

            self.assertEqual(exit_code, 2)
            self.assertEqual(stdout.getvalue(), "")
            self.assertIn(
                (
                    "repository_id must be a non-empty printable string of at "
                    "most 128 characters without surrounding whitespace"
                ),
                stderr.getvalue(),
            )
            self.assertNotIn(injected_marker, stderr.getvalue())
            self.assertNotIn("\u202e", stderr.getvalue())
            self.assertNotIn("duplicate repository_id", stderr.getvalue())
            self.assertEqual(legacy_path.read_bytes(), original_legacy)
            self.assertEqual(current_path.read_bytes(), original_current)

    def test_accepts_bounded_printable_git_branch_text(self) -> None:
        branches = (
            None,
            "main",
            "feature/café",
            "x" * MAX_GIT_BRANCH_CHARACTERS,
        )

        for branch in branches:
            with self.subTest(branch=repr(branch)):
                metadata = self._metadata("api", branch=branch)

                validated = validate_rollout_metadata(metadata)

                self.assertEqual(validated["git"]["branch"], branch)

    def test_main_rejects_branch_line_injection_without_partial_output(
        self,
    ) -> None:
        injected_marker = "Bundle-reported ready for CI: 999"
        with TemporaryDirectory() as tmp:
            evidence_path = Path(tmp) / "rollout.md"
            original_evidence = self._bundle_unvalidated(
                self._metadata(
                    "api",
                    branch=f"main\n{injected_marker}\x1b[31m",
                )
            )
            evidence_path.write_text(original_evidence, encoding="utf-8")

            stdout = io.StringIO()
            stderr = io.StringIO()
            with redirect_stdout(stdout), redirect_stderr(stderr):
                exit_code = main(["--details", str(evidence_path)])

            self.assertEqual(exit_code, 2)
            self.assertEqual(stdout.getvalue(), "")
            self.assertIn("git.branch must be null", stderr.getvalue())
            self.assertNotIn(injected_marker, stderr.getvalue())
            self.assertNotIn("\x1b", stderr.getvalue())
            self.assertEqual(
                evidence_path.read_text(encoding="utf-8"),
                original_evidence,
            )

    def test_main_reports_input_errors_without_stdout(self) -> None:
        stderr = io.StringIO()
        stdout = io.StringIO()
        with redirect_stderr(stderr), redirect_stdout(stdout):
            exit_code = main(["missing.md"])

        self.assertEqual(exit_code, 2)
        self.assertEqual(stdout.getvalue(), "")
        self.assertIn("could not read missing.md", stderr.getvalue())

    def test_main_escapes_unsafe_missing_evidence_path(self) -> None:
        with TemporaryDirectory() as tmp:
            missing = Path(tmp) / (
                "missing\nRepositories: 999\r\x1b\u009b\u2028\u202e.md"
            )
            encoded_path = json.dumps(str(missing))
            stderr = io.StringIO()
            stdout = io.StringIO()

            with redirect_stderr(stderr), redirect_stdout(stdout):
                exit_code = main([str(missing)])

            message = stderr.getvalue()
            self.assertEqual(exit_code, 2)
            self.assertEqual(stdout.getvalue(), "")
            self.assertIn(encoded_path, message)
            self.assertEqual(len(message.splitlines()), 1)
            self.assertNotIn("\nRepositories: 999", message)
            self.assertNotIn("\r", message)
            self.assertNotIn("\x1b", message)
            self.assertNotIn("\u009b", message)
            self.assertNotIn("\u2028", message)
            self.assertNotIn("\u202e", message)

    def test_json_details_preserve_unsafe_path_as_structured_data(self) -> None:
        with TemporaryDirectory() as tmp:
            evidence = Path(tmp) / (
                "bundle\nRepositories: 999\r\x1b\u009b\u2028\u202e.md"
            )
            evidence.write_text(
                self._bundle(self._metadata("api")),
                encoding="utf-8",
            )
            stdout = io.StringIO()

            with redirect_stdout(stdout):
                exit_code = main(
                    ["--format", "json", "--details", str(evidence)]
                )

            encoded = stdout.getvalue()
            report = json.loads(encoded)
            self.assertEqual(exit_code, 0)
            self.assertEqual(
                report["repositories"][0]["evidence_file"],
                str(evidence),
            )
            self.assertIn(json.dumps(str(evidence)), encoded)
            self.assertNotIn("\nRepositories: 999", encoded)
            self.assertNotIn("\r", encoded)
            self.assertNotIn("\x1b", encoded)
            self.assertNotIn("\u009b", encoded)
            self.assertNotIn("\u2028", encoded)
            self.assertNotIn("\u202e", encoded)

    def test_main_rejects_non_regular_evidence_before_read(self) -> None:
        kinds = ["directory"]
        if hasattr(os, "symlink"):
            kinds.append("symlink")
        if hasattr(os, "mkfifo"):
            kinds.append("fifo")

        for kind in kinds:
            with self.subTest(kind=kind), TemporaryDirectory() as tmp:
                root = Path(tmp)
                evidence_path = root / "rollout.md"
                target_path = root / "stored-rollout.md"
                target_path.write_text(
                    self._bundle(self._metadata("api")),
                    encoding="utf-8",
                )
                if kind == "directory":
                    evidence_path.mkdir()
                elif kind == "symlink":
                    evidence_path.symlink_to(target_path)
                else:
                    os.mkfifo(evidence_path)

                stdout = io.StringIO()
                stderr = io.StringIO()
                with patch.object(
                    Path,
                    "read_text",
                    side_effect=AssertionError(
                        "non-regular rollout evidence must not be read"
                    ),
                ), redirect_stdout(stdout), redirect_stderr(stderr):
                    exit_code = main([str(evidence_path)])

                self.assertEqual(exit_code, 2)
                self.assertEqual(stdout.getvalue(), "")
                if kind == "symlink":
                    self.assertIn("must not be a symlink", stderr.getvalue())
                    self.assertEqual(
                        target_path.read_text(encoding="utf-8"),
                        self._bundle(self._metadata("api")),
                    )
                else:
                    self.assertIn("must be a regular file", stderr.getvalue())

    def test_main_rejects_oversized_evidence_before_parsing(self) -> None:
        with TemporaryDirectory() as tmp:
            evidence_path = Path(tmp) / "rollout.md"
            with evidence_path.open("wb") as evidence_file:
                evidence_file.truncate(MAX_ROLLOUT_EVIDENCE_BYTES + 1)

            stdout = io.StringIO()
            stderr = io.StringIO()
            with patch(
                "repo_scout.rollout.parse_rollout_metadata",
                side_effect=AssertionError(
                    "oversized rollout evidence must not be parsed"
                ),
            ) as parser, patch(
                "repo_scout._file_evidence.os.read",
                side_effect=AssertionError(
                    "oversized sparse rollout evidence must not be read"
                ),
            ) as descriptor_reader:
                with redirect_stdout(stdout), redirect_stderr(stderr):
                    exit_code = main([str(evidence_path)])

            self.assertEqual(exit_code, 2)
            self.assertEqual(stdout.getvalue(), "")
            self.assertIn(
                (
                    "rollout evidence exceeds "
                    f"{MAX_ROLLOUT_EVIDENCE_BYTES} bytes"
                ),
                stderr.getvalue(),
            )
            parser.assert_not_called()
            descriptor_reader.assert_not_called()
            self.assertEqual(
                evidence_path.stat().st_size,
                MAX_ROLLOUT_EVIDENCE_BYTES + 1,
            )

    def test_load_accepts_evidence_at_size_limit(self) -> None:
        with TemporaryDirectory() as tmp:
            evidence_path = Path(tmp) / "rollout.md"
            bundle = self._bundle(self._metadata("api")).encode("utf-8")
            prefix_size = MAX_ROLLOUT_EVIDENCE_BYTES - len(bundle)
            evidence_path.write_bytes(
                b"#" + (b"x" * (prefix_size - 2)) + b"\n" + bundle
            )

            metadata = load_rollout_metadata(evidence_path)

            self.assertEqual(metadata["repository_id"], "api")
            self.assertEqual(
                evidence_path.stat().st_size,
                MAX_ROLLOUT_EVIDENCE_BYTES,
            )

    def test_load_rejects_evidence_mutation_during_parsing(self) -> None:
        with TemporaryDirectory() as tmp:
            evidence_path = Path(tmp) / "rollout.md"
            evidence_path.write_text(
                self._bundle(self._metadata("api")),
                encoding="utf-8",
            )
            original_parser = parse_rollout_metadata
            evidence_changed = False

            def mutate_after_parsing(
                content: str,
                *,
                source: str = "<rollout evidence>",
            ) -> dict[str, object]:
                nonlocal evidence_changed
                metadata = original_parser(content, source=source)
                with evidence_path.open("ab") as evidence_file:
                    evidence_file.write(b"\n")
                evidence_changed = True
                return metadata

            with patch(
                "repo_scout.rollout.parse_rollout_metadata",
                side_effect=mutate_after_parsing,
            ), self.assertRaisesRegex(
                RolloutEvidenceError,
                "rollout evidence changed during loading",
            ):
                load_rollout_metadata(evidence_path)

            self.assertTrue(evidence_changed)

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
        enforcement_status: str | None = None,
        applied: int = 0,
        expired: int = 0,
        pending: int = 0,
        stale: int = 0,
        unresolved: int | None = None,
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
        if schema_version >= 3:
            effective_status = enforcement_status or policy_status
            unresolved_count = (
                violations if unresolved is None and effective_status == "fail" else 0
                if unresolved is None
                else unresolved
            )
            policy.update(
                {
                    "enforcement_status": effective_status,
                    "exception_ledger_fingerprint": EXCEPTION_LEDGER_FINGERPRINT,
                    "exception_decisions_total": applied + expired + pending + stale,
                    "exception_decisions_applied": applied,
                    "exception_decisions_expired": expired,
                    "exception_decisions_pending": pending,
                    "exception_decisions_stale": stale,
                    "unresolved_violations": unresolved_count,
                }
            )
        return {
            "schema_version": schema_version,
            "repository_id": repository_id,
            "readiness": (
                "ready-for-ci"
                if (
                    policy.get("enforcement_status", policy_status) != "fail"
                    and clean
                )
                else "remediation-required"
            ),
            "policy": policy,
            "git": git,
            "attention_findings": attention_findings,
        }


if __name__ == "__main__":
    unittest.main()
