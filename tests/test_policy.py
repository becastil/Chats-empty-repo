from __future__ import annotations

from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from repo_scout.policy import (
    PolicyError,
    evaluate_policy,
    load_policy,
    parse_policy,
    policy_fingerprint,
)
from repo_scout.scanner import scan_project


class PolicyTests(unittest.TestCase):
    def test_policy_passes_when_repository_satisfies_every_rule(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "README.md").write_text("# Example\n", encoding="utf-8")
            policy_path = root / "policy.toml"
            policy_path.write_text(
                """version = 2
[repository]
required_files = ["README.md"]
forbidden_files = [".env"]
max_files = 3
max_total_bytes = 1000
""",
                encoding="utf-8",
            )

            result = evaluate_policy(scan_project(root), load_policy(policy_path))

            self.assertEqual(result["status"], "pass")
            self.assertRegex(result["fingerprint"], r"^sha256:[0-9a-f]{64}$")
            self.assertEqual(result["rules_checked"], 4)
            self.assertEqual(result["violations"], [])

    def test_policy_reports_each_repository_violation(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "app.py").write_text("print('too large')\n", encoding="utf-8")
            (root / ".env").write_text("SECRET=unsafe\n", encoding="utf-8")
            policy_path = root / "policy.toml"
            policy_path.write_text(
                """version = 2
[repository]
required_files = ["README.md"]
forbidden_files = [".env"]
max_files = 1
max_total_bytes = 5
require_clean_git = true
""",
                encoding="utf-8",
            )

            result = evaluate_policy(scan_project(root), load_policy(policy_path))

            self.assertEqual(result["status"], "fail")
            self.assertEqual(
                [violation["rule"] for violation in result["violations"]],
                [
                    "repository.required_files",
                    "repository.forbidden_files",
                    "repository.max_files",
                    "repository.max_total_bytes",
                    "repository.require_clean_git",
                ],
            )

    def test_forbidden_files_ignore_gitignored_local_environment(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".gitignore").write_text(".env\n", encoding="utf-8")
            (root / ".env").write_text("SECRET=local\n", encoding="utf-8")
            subprocess.run(
                ["git", "init", "--quiet", str(root)],
                check=True,
                capture_output=True,
                text=True,
            )
            policy = parse_policy(
                'version = 2\n[repository]\nforbidden_files = [".env"]\n'
            )

            result = evaluate_policy(scan_project(root), policy)

            self.assertEqual(result["status"], "pass")

            subprocess.run(
                ["git", "-C", str(root), "add", "--force", ".env"],
                check=True,
                capture_output=True,
                text=True,
            )
            tracked_result = evaluate_policy(scan_project(root), policy)

            self.assertEqual(tracked_result["status"], "fail")
            self.assertEqual(
                tracked_result["violations"][0]["rule"],
                "repository.forbidden_files",
            )

    def test_policy_rejects_contradictory_file_rules(self) -> None:
        with self.assertRaisesRegex(
            PolicyError, "both required and forbidden: SECURITY.md"
        ):
            parse_policy(
                """version = 2
[repository]
required_files = ["README.md", "SECURITY.md"]
forbidden_files = ["SECURITY.md"]
"""
            )

    def test_policy_rejects_invalid_forbidden_paths(self) -> None:
        with self.assertRaisesRegex(
            PolicyError, "repository.forbidden_files paths must be normalized"
        ):
            parse_policy(
                """version = 2
[repository]
forbidden_files = ["../.env"]
"""
            )

    def test_policy_version_one_rejects_forbidden_files(self) -> None:
        with self.assertRaisesRegex(
            PolicyError, "unknown repository key: forbidden_files"
        ):
            parse_policy(
                """version = 1
[repository]
forbidden_files = [".env"]
"""
            )

    def test_forbidden_patterns_match_nested_policy_visible_files(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "services/api").mkdir(parents=True)
            (root / "certs").mkdir()
            (root / ".env").write_text("ROOT=unsafe\n", encoding="utf-8")
            (root / "services/api/.env").write_text(
                "NESTED=unsafe\n", encoding="utf-8"
            )
            (root / "certs/prod.pem").write_text(
                "not-a-real-key\n", encoding="utf-8"
            )
            policy = parse_policy(
                """version = 3
[repository]
forbidden_files = [".env"]
forbidden_file_patterns = ["**/.env", "*.pem"]
"""
            )

            result = evaluate_policy(scan_project(root), policy)

            self.assertEqual(result["status"], "fail")
            self.assertEqual(
                [violation["rule"] for violation in result["violations"]],
                [
                    "repository.forbidden_files",
                    "repository.forbidden_file_patterns",
                    "repository.forbidden_file_patterns",
                ],
            )
            self.assertEqual(
                result["violations"][1],
                {
                    "rule": "repository.forbidden_file_patterns",
                    "pattern": "**/.env",
                    "paths": ["services/api/.env"],
                    "match_count": 1,
                    "paths_truncated": False,
                    "message": (
                        "Forbidden file pattern **/.env matched 1 file(s): "
                        "services/api/.env."
                    ),
                },
            )
            self.assertEqual(
                result["violations"][2]["paths"], ["certs/prod.pem"]
            )

    def test_forbidden_patterns_ignore_then_catch_force_tracked_files(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            nested = root / "services/api"
            nested.mkdir(parents=True)
            (root / ".gitignore").write_text("**/.env\n", encoding="utf-8")
            (nested / ".env").write_text("SECRET=local\n", encoding="utf-8")
            subprocess.run(
                ["git", "init", "--quiet", str(root)],
                check=True,
                capture_output=True,
                text=True,
            )
            policy = parse_policy(
                """version = 3
[repository]
forbidden_file_patterns = ["**/.env"]
"""
            )

            self.assertEqual(
                evaluate_policy(scan_project(root), policy)["status"], "pass"
            )

            subprocess.run(
                ["git", "-C", str(root), "add", "--force", "services/api/.env"],
                check=True,
                capture_output=True,
                text=True,
            )
            tracked = evaluate_policy(scan_project(root), policy)

            self.assertEqual(tracked["status"], "fail")
            self.assertEqual(
                tracked["violations"][0]["paths"], ["services/api/.env"]
            )

    def test_forbidden_pattern_details_are_bounded(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            for index in range(25):
                path = root / "certs" / f"service-{index:02d}.pem"
                path.parent.mkdir(exist_ok=True)
                path.write_text("not-a-real-key\n", encoding="utf-8")
            policy = parse_policy(
                """version = 3
[repository]
forbidden_file_patterns = ["*.pem"]
"""
            )

            result = evaluate_policy(scan_project(root), policy)
            violation = result["violations"][0]

            self.assertEqual(violation["match_count"], 25)
            self.assertEqual(len(violation["paths"]), 20)
            self.assertTrue(violation["paths_truncated"])
            self.assertIn("and 5 more", violation["message"])

    def test_forbidden_patterns_scan_beyond_snapshot_path_details(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            for index in range(510):
                path = root / "generated" / f"file-{index:03d}.txt"
                path.parent.mkdir(exist_ok=True)
                path.write_text("ok\n", encoding="utf-8")
            secret = root / "services/api/prod.pem"
            secret.parent.mkdir(parents=True)
            secret.write_text("not-a-real-key\n", encoding="utf-8")
            policy = parse_policy(
                """version = 3
[repository]
forbidden_file_patterns = ["*.pem"]
"""
            )

            snapshot = scan_project(root)
            result = evaluate_policy(snapshot, policy)

            self.assertTrue(snapshot["files"]["paths_truncated"])
            self.assertEqual(
                result["violations"][0]["paths"], ["services/api/prod.pem"]
            )

    def test_policy_versions_before_three_reject_forbidden_patterns(self) -> None:
        for version in (1, 2):
            with self.subTest(version=version), self.assertRaisesRegex(
                PolicyError, "unknown repository key: forbidden_file_patterns"
            ):
                parse_policy(
                    f"""version = {version}
[repository]
forbidden_file_patterns = ["*.pem"]
"""
                )

    def test_policy_rejects_invalid_or_contradictory_patterns(self) -> None:
        invalid_policies = (
            (
                """version = 3
[repository]
forbidden_file_patterns = ["secrets.pem"]
""",
                "must contain a wildcard",
            ),
            (
                """version = 3
[repository]
required_files = ["certs/prod.pem"]
forbidden_file_patterns = ["*.pem"]
""",
                "required path certs/prod.pem matches forbidden pattern",
            ),
            (
                """version = 3
[repository]
forbidden_files = ["certs/prod.pem"]
forbidden_file_patterns = ["*.pem"]
""",
                "forbidden path certs/prod.pem duplicates pattern",
            ),
        )

        for policy, message in invalid_policies:
            with self.subTest(message=message), self.assertRaisesRegex(
                PolicyError, message
            ):
                parse_policy(policy)

    def test_policy_rejects_unknown_keys(self) -> None:
        with TemporaryDirectory() as tmp:
            policy_path = Path(tmp) / "policy.toml"
            policy_path.write_text(
                """version = 1
[repository]
max_filez = 10
""",
                encoding="utf-8",
            )

            with self.assertRaisesRegex(PolicyError, "unknown repository key: max_filez"):
                load_policy(policy_path)

    def test_policy_rejects_paths_that_escape_repository(self) -> None:
        with TemporaryDirectory() as tmp:
            policy_path = Path(tmp) / "policy.toml"
            policy_path.write_text(
                """version = 1
[repository]
required_files = ["../secret.txt"]
""",
                encoding="utf-8",
            )

            with self.assertRaisesRegex(PolicyError, "normalized and relative"):
                load_policy(policy_path)

    def test_policy_fingerprint_tracks_normalized_rule_semantics(self) -> None:
        first = parse_policy(
            """version = 2
[repository]
required_files = ["README.md", "SECURITY.md"]
forbidden_files = [".env", ".env.local"]
max_files = 100
""",
            source="first.toml",
        )
        reordered = parse_policy(
            """version = 2
[repository]
max_files = 100
required_files = ["SECURITY.md", "README.md"]
forbidden_files = [".env.local", ".env"]
""",
            source="reordered.toml",
        )
        changed = parse_policy(
            """version = 2
[repository]
required_files = ["README.md", "SECURITY.md"]
forbidden_files = [".env", ".env.local"]
max_files = 101
""",
            source="changed.toml",
        )
        explicit_default = parse_policy(
            """version = 2
[repository]
required_files = ["README.md", "SECURITY.md"]
forbidden_files = [".env", ".env.local"]
max_files = 100
require_clean_git = false
""",
            source="explicit-default.toml",
        )
        clean_required = parse_policy(
            """version = 2
[repository]
required_files = ["README.md", "SECURITY.md"]
forbidden_files = [".env", ".env.local"]
max_files = 100
require_clean_git = true
""",
            source="clean-required.toml",
        )

        self.assertEqual(policy_fingerprint(first), policy_fingerprint(reordered))
        self.assertEqual(
            policy_fingerprint(first), policy_fingerprint(explicit_default)
        )
        self.assertNotEqual(policy_fingerprint(first), policy_fingerprint(changed))
        self.assertNotEqual(
            policy_fingerprint(first), policy_fingerprint(clean_required)
        )
        forbidden_changed = parse_policy(
            """version = 2
[repository]
required_files = ["README.md", "SECURITY.md"]
forbidden_files = [".env", "credentials.json"]
max_files = 100
""",
            source="forbidden-changed.toml",
        )
        self.assertNotEqual(
            policy_fingerprint(first), policy_fingerprint(forbidden_changed)
        )

    def test_policy_fingerprint_normalizes_forbidden_pattern_order(self) -> None:
        first = parse_policy(
            """version = 3
[repository]
forbidden_file_patterns = ["**/.env", "*.pem"]
"""
        )
        reordered = parse_policy(
            """version = 3
[repository]
forbidden_file_patterns = ["*.pem", "**/.env"]
"""
        )
        changed = parse_policy(
            """version = 3
[repository]
forbidden_file_patterns = ["**/.env", "*.key"]
"""
        )

        self.assertEqual(policy_fingerprint(first), policy_fingerprint(reordered))
        self.assertNotEqual(policy_fingerprint(first), policy_fingerprint(changed))


if __name__ == "__main__":
    unittest.main()
