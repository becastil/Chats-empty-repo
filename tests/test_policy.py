from __future__ import annotations

from pathlib import Path
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
                """version = 1
[repository]
required_files = ["README.md"]
max_files = 3
max_total_bytes = 1000
""",
                encoding="utf-8",
            )

            result = evaluate_policy(scan_project(root), load_policy(policy_path))

            self.assertEqual(result["status"], "pass")
            self.assertRegex(result["fingerprint"], r"^sha256:[0-9a-f]{64}$")
            self.assertEqual(result["rules_checked"], 3)
            self.assertEqual(result["violations"], [])

    def test_policy_reports_each_repository_violation(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "app.py").write_text("print('too large')\n", encoding="utf-8")
            policy_path = root / "policy.toml"
            policy_path.write_text(
                """version = 1
[repository]
required_files = ["README.md"]
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
                    "repository.max_files",
                    "repository.max_total_bytes",
                    "repository.require_clean_git",
                ],
            )

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
            """version = 1
[repository]
required_files = ["README.md", "SECURITY.md"]
max_files = 100
""",
            source="first.toml",
        )
        reordered = parse_policy(
            """version = 1
[repository]
max_files = 100
required_files = ["SECURITY.md", "README.md"]
""",
            source="reordered.toml",
        )
        changed = parse_policy(
            """version = 1
[repository]
required_files = ["README.md", "SECURITY.md"]
max_files = 101
""",
            source="changed.toml",
        )
        explicit_default = parse_policy(
            """version = 1
[repository]
required_files = ["README.md", "SECURITY.md"]
max_files = 100
require_clean_git = false
""",
            source="explicit-default.toml",
        )
        clean_required = parse_policy(
            """version = 1
[repository]
required_files = ["README.md", "SECURITY.md"]
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


if __name__ == "__main__":
    unittest.main()
