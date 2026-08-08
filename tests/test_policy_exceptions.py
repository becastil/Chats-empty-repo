from __future__ import annotations

from datetime import date
from pathlib import Path
import sys
import subprocess
from tempfile import TemporaryDirectory
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from repo_scout.policy import evaluate_policy, parse_policy
from repo_scout.policy_exceptions import (
    PolicyExceptionError,
    apply_policy_exceptions,
    exception_ledger_fingerprint,
    load_exception_ledger,
    parse_exception_ledger,
    verify_exception_ledger_checkout,
)
from repo_scout.scanner import scan_project


class PolicyExceptionTests(unittest.TestCase):
    def test_active_exception_suppresses_only_its_bound_violation(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            policy_result = evaluate_policy(
                scan_project(root),
                parse_policy(
                    'version = 1\n[repository]\nrequired_files = ["README.md"]\n'
                ),
            )
            ledger = parse_exception_ledger(
                self._ledger(
                    policy_result["fingerprint"],
                    policy_result["violation_ids"][0],
                ),
                source="repo-scout-exceptions.toml",
            )

            result = apply_policy_exceptions(
                policy_result,
                ledger,
                repository_id="platform/api",
                evaluated_on=date(2026, 8, 8),
            )

            self.assertEqual(result["status"], "fail")
            self.assertEqual(len(result["violations"]), 1)
            self.assertEqual(len(result["violation_ids"]), 1)
            self.assertEqual(
                result["exceptions"]["enforcement_status"],
                "pass-with-exceptions",
            )
            self.assertEqual(len(result["exceptions"]["applied"]), 1)
            excepted = result["exceptions"]["applied"][0]
            self.assertEqual(excepted["exception"]["id"], "EXC-2026-001")
            self.assertEqual(
                excepted["violation"]["message"],
                "Required file is missing: README.md.",
            )
            self.assertEqual(result["exceptions"]["evaluated_on"], "2026-08-08")
            self.assertEqual(len(result["exceptions"]["active"]), 1)
            self.assertEqual(result["exceptions"]["pending"], [])
            self.assertEqual(result["exceptions"]["expired"], [])
            self.assertRegex(
                result["exceptions"]["fingerprint"], r"^sha256:[0-9a-f]{64}$"
            )

    def test_pending_and_expired_exceptions_do_not_suppress_a_violation(self) -> None:
        with TemporaryDirectory() as tmp:
            policy_result = evaluate_policy(
                scan_project(tmp),
                parse_policy(
                    'version = 1\n[repository]\nrequired_files = ["README.md"]\n'
                ),
            )
            cases = (
                ("2026-08-10", "2026-08-20", "pending"),
                ("2026-07-01", "2026-07-31", "expired"),
            )
            for approved_on, expires_on, state in cases:
                with self.subTest(state=state):
                    ledger = parse_exception_ledger(
                        self._ledger(
                            policy_result["fingerprint"],
                            policy_result["violation_ids"][0],
                            approved_on=approved_on,
                            expires_on=expires_on,
                        )
                    )

                    result = apply_policy_exceptions(
                        policy_result,
                        ledger,
                        repository_id="platform/api",
                        evaluated_on=date(2026, 8, 8),
                    )

                    self.assertEqual(result["status"], "fail")
                    self.assertEqual(len(result["violations"]), 1)
                    self.assertEqual(result["exceptions"]["applied"], [])
                    self.assertEqual(len(result["exceptions"][state]), 1)

    def test_active_exception_fails_closed_when_violation_is_not_current(self) -> None:
        with TemporaryDirectory() as tmp:
            policy_result = evaluate_policy(
                scan_project(tmp),
                parse_policy(
                    'version = 1\n[repository]\nrequired_files = ["README.md"]\n'
                ),
            )
            ledger = parse_exception_ledger(
                self._ledger(policy_result["fingerprint"], f"sha256:{'0' * 64}")
            )

            result = apply_policy_exceptions(
                policy_result,
                ledger,
                repository_id="platform/api",
                evaluated_on=date(2026, 8, 8),
            )

            self.assertEqual(result["exceptions"]["enforcement_status"], "fail")
            self.assertEqual(
                result["exceptions"]["stale"][0]["id"], "EXC-2026-001"
            )

    def test_repository_and_policy_identity_must_match(self) -> None:
        with TemporaryDirectory() as tmp:
            policy_result = evaluate_policy(
                scan_project(tmp),
                parse_policy(
                    'version = 1\n[repository]\nrequired_files = ["README.md"]\n'
                ),
            )
            ledger = parse_exception_ledger(
                self._ledger(
                    policy_result["fingerprint"],
                    policy_result["violation_ids"][0],
                )
            )

            with self.assertRaisesRegex(PolicyExceptionError, "repository_id"):
                apply_policy_exceptions(
                    policy_result,
                    ledger,
                    repository_id="platform/web",
                    evaluated_on=date(2026, 8, 8),
                )

            changed_policy = dict(policy_result)
            changed_policy["fingerprint"] = f"sha256:{'f' * 64}"
            with self.assertRaisesRegex(PolicyExceptionError, "policy fingerprint"):
                apply_policy_exceptions(
                    changed_policy,
                    ledger,
                    repository_id="platform/api",
                    evaluated_on=date(2026, 8, 8),
                )

    def test_ledger_schema_rejects_unsafe_or_unbounded_decisions(self) -> None:
        valid = self._ledger(f"sha256:{'a' * 64}", f"sha256:{'b' * 64}")
        cases = (
            (valid.replace("version = 1", "version = 2"), "version must be 1"),
            (valid.replace("version = 1", "version = true"), "version must be 1"),
            (
                valid.replace('reason = "Migration is tracked in ENG-123."', 'reason = " bad"'),
                "reason must be a non-empty printable string",
            ),
            (
                valid.replace("expires_on = 2026-09-30", "expires_on = 2027-09-30"),
                "duration cannot exceed 366 days",
            ),
            (
                valid.replace("expires_on = 2026-09-30", "expires_on = 2026-07-01"),
                "cannot precede approved_on",
            ),
            (
                valid.replace("[[exceptions]]", 'unknown = true\n\n[[exceptions]]', 1),
                "unknown exception ledger key: unknown",
            ),
        )
        for content, message in cases:
            with self.subTest(message=message), self.assertRaisesRegex(
                PolicyExceptionError, message
            ):
                parse_exception_ledger(content)

    def test_ledger_rejects_duplicate_ids_and_violation_bindings(self) -> None:
        record = self._ledger(f"sha256:{'a' * 64}", f"sha256:{'b' * 64}")
        second = record.split("[[exceptions]]\n", 1)[1]
        duplicate_id = f"{record}\n[[exceptions]]\n{second}"
        with self.assertRaisesRegex(PolicyExceptionError, "duplicate exception id"):
            parse_exception_ledger(duplicate_id)

        duplicate_violation = duplicate_id.replace(
            'id = "EXC-2026-001"', 'id = "EXC-2026-002"', 1
        )
        with self.assertRaisesRegex(
            PolicyExceptionError, "duplicate exception for violation"
        ):
            parse_exception_ledger(duplicate_violation)

    def test_fingerprint_is_independent_of_exception_order(self) -> None:
        first = parse_exception_ledger(
            self._two_record_ledger(order=("001", "002"))
        )
        reordered = parse_exception_ledger(
            self._two_record_ledger(order=("002", "001"))
        )
        changed = parse_exception_ledger(
            self._two_record_ledger(order=("001", "002")).replace(
                "Migration 001", "Changed rationale", 1
            )
        )

        self.assertEqual(
            exception_ledger_fingerprint(first),
            exception_ledger_fingerprint(reordered),
        )
        self.assertNotEqual(
            exception_ledger_fingerprint(first),
            exception_ledger_fingerprint(changed),
        )

    def test_violation_identity_changes_when_observed_evidence_drifts(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            first_secret = root / "services" / "api.env"
            first_secret.parent.mkdir()
            first_secret.write_text("SECRET=one\n", encoding="utf-8")
            pattern_policy = parse_policy(
                'version = 3\n[repository]\nforbidden_file_patterns = ["*.env"]\n'
            )
            first_pattern = evaluate_policy(scan_project(root), pattern_policy)

            first_secret.unlink()
            (root / "services" / "worker.env").write_text(
                "SECRET=two\n", encoding="utf-8"
            )
            changed_pattern = evaluate_policy(scan_project(root), pattern_policy)

            self.assertEqual(
                first_pattern["violations"][0]["match_count"],
                changed_pattern["violations"][0]["match_count"],
            )
            self.assertNotEqual(
                first_pattern["violation_ids"][0],
                changed_pattern["violation_ids"][0],
            )

            size_policy = parse_policy(
                "version = 1\n[repository]\nmax_total_bytes = 1\n"
            )
            first_size = evaluate_policy(scan_project(root), size_policy)
            (root / "extra.txt").write_text("more evidence\n", encoding="utf-8")
            changed_size = evaluate_policy(scan_project(root), size_policy)

            self.assertNotEqual(
                first_size["violations"][0]["actual"],
                changed_size["violations"][0]["actual"],
            )
            self.assertNotEqual(
                first_size["violation_ids"][0],
                changed_size["violation_ids"][0],
            )

            required_only = parse_policy(
                'version = 1\n[repository]\nrequired_files = ["SECURITY.md"]\n'
            )
            required_with_limit = parse_policy(
                'version = 1\n[repository]\nrequired_files = ["SECURITY.md"]\n'
                "max_files = 10000\n"
            )
            first_policy = evaluate_policy(scan_project(root), required_only)
            changed_policy = evaluate_policy(scan_project(root), required_with_limit)
            self.assertEqual(first_policy["violations"], changed_policy["violations"])
            self.assertNotEqual(
                first_policy["violation_ids"][0],
                changed_policy["violation_ids"][0],
            )

    def test_loader_rejects_symlinked_exception_ledger(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "real.toml"
            target.write_text(
                self._ledger(f"sha256:{'a' * 64}", f"sha256:{'b' * 64}"),
                encoding="utf-8",
            )
            alias = root / "alias.toml"
            alias.symlink_to(target)

            with self.assertRaisesRegex(PolicyExceptionError, "must not be a symlink"):
                load_exception_ledger(alias)

    def test_checkout_verification_requires_in_repo_tracked_clean_evidence(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp) / "repository"
            root.mkdir()
            subprocess.run(["git", "init", "-q", str(root)], check=True)
            ledger_path = root / "repo-scout-exceptions.toml"
            ledger_path.write_text(
                self._ledger(f"sha256:{'a' * 64}", f"sha256:{'b' * 64}"),
                encoding="utf-8",
            )
            subprocess.run(
                ["git", "-C", str(root), "add", ledger_path.name], check=True
            )
            subprocess.run(
                [
                    "git",
                    "-C",
                    str(root),
                    "-c",
                    "user.name=Repo Scout Tests",
                    "-c",
                    "user.email=tests@example.com",
                    "commit",
                    "-qm",
                    "Add exception ledger",
                ],
                check=True,
            )
            ledger = load_exception_ledger(ledger_path)
            snapshot = scan_project(root)

            verify_exception_ledger_checkout(root, ledger, snapshot)

            ledger_path.write_text(
                ledger_path.read_text(encoding="utf-8").replace(
                    "Migration is tracked in ENG-123.",
                    "Migration is tracked in ENG-456.",
                ),
                encoding="utf-8",
            )
            subprocess.run(
                ["git", "-C", str(root), "add", ledger_path.name], check=True
            )
            subprocess.run(
                ["git", "-C", str(root), "commit", "-qm", "Revise decision"],
                check=True,
            )
            with self.assertRaisesRegex(
                PolicyExceptionError, "does not match tracked Git evidence"
            ):
                verify_exception_ledger_checkout(root, ledger, scan_project(root))

            ledger = load_exception_ledger(ledger_path)

            (root / "untracked.txt").write_text("dirty\n", encoding="utf-8")
            with self.assertRaisesRegex(
                PolicyExceptionError, "requires a clean Git worktree"
            ):
                verify_exception_ledger_checkout(root, ledger, scan_project(root))

            outside = Path(tmp) / "outside.toml"
            outside.write_text(ledger_path.read_text(encoding="utf-8"))
            outside_ledger = load_exception_ledger(outside)
            with self.assertRaisesRegex(
                PolicyExceptionError, "must be inside the scanned repository"
            ):
                verify_exception_ledger_checkout(root, outside_ledger, snapshot)

    @staticmethod
    def _ledger(
        policy_fingerprint: str,
        violation_id: str,
        *,
        approved_on: str = "2026-08-01",
        expires_on: str = "2026-09-30",
    ) -> str:
        return f'''version = 1
repository_id = "platform/api"
policy_fingerprint = "{policy_fingerprint}"

[[exceptions]]
id = "EXC-2026-001"
violation_id = "{violation_id}"
owner = "platform-team"
approved_by = "engineering-lead"
reason = "Migration is tracked in ENG-123."
approved_on = {approved_on}
expires_on = {expires_on}
'''

    @staticmethod
    def _two_record_ledger(*, order: tuple[str, str]) -> str:
        records = {
            "001": f'''[[exceptions]]
id = "EXC-2026-001"
violation_id = "sha256:{'b' * 64}"
owner = "platform-team"
approved_by = "engineering-lead"
reason = "Migration 001"
approved_on = 2026-08-01
expires_on = 2026-09-30
''',
            "002": f'''[[exceptions]]
id = "EXC-2026-002"
violation_id = "sha256:{'c' * 64}"
owner = "security-team"
approved_by = "engineering-lead"
reason = "Migration 002"
approved_on = 2026-08-01
expires_on = 2026-09-30
''',
        }
        return (
            f'''version = 1
repository_id = "platform/api"
policy_fingerprint = "sha256:{'a' * 64}"

'''
            + "\n".join(records[key] for key in order)
        )


if __name__ == "__main__":
    unittest.main()
