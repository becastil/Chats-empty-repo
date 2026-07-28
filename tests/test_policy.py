from __future__ import annotations

import os
from pathlib import Path
import stat
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import repo_scout.policy as policy_module
from repo_scout.policy import (
    MAX_POLICY_BYTES,
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

    def test_required_file_groups_accept_one_alternative_per_group(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "pnpm-lock.yaml").write_text("lockfileVersion: 9\n")
            (root / "Dockerfile").write_text("FROM scratch\n")
            policy = parse_policy(
                """version = 4
[repository]
required_file_groups = [
  ["package-lock.json", "pnpm-lock.yaml", "yarn.lock"],
  ["Dockerfile", "Containerfile"],
]
"""
            )

            passing = evaluate_policy(scan_project(root), policy)
            self.assertEqual(passing["status"], "pass")
            self.assertEqual(passing["rules_checked"], 1)

            (root / "pnpm-lock.yaml").unlink()
            failing = evaluate_policy(scan_project(root), policy)
            self.assertEqual(failing["status"], "fail")
            self.assertEqual(
                failing["violations"],
                [
                    {
                        "rule": "repository.required_file_groups",
                        "paths": [
                            "package-lock.json",
                            "pnpm-lock.yaml",
                            "yarn.lock",
                        ],
                        "message": (
                            "Required file group has no present file: "
                            "package-lock.json, pnpm-lock.yaml, yarn.lock."
                        ),
                    }
                ],
            )

    def test_policy_versions_before_four_reject_required_file_groups(self) -> None:
        for version in (1, 2, 3):
            with self.subTest(version=version), self.assertRaisesRegex(
                PolicyError, "unknown repository key: required_file_groups"
            ):
                parse_policy(
                    f'''version = {version}
[repository]
required_file_groups = [["package-lock.json", "pnpm-lock.yaml"]]
'''
                )

    def test_policy_rejects_invalid_or_contradictory_file_groups(self) -> None:
        invalid_policies = (
            (
                """version = 4
[repository]
required_file_groups = []
""",
                "must be a non-empty array",
            ),
            (
                """version = 4
[repository]
required_file_groups = [[]]
""",
                "required_file_groups\\[0\\] must be a non-empty array",
            ),
            (
                """version = 4
[repository]
required_file_groups = [["a.lock", "b.lock"], ["b.lock", "a.lock"]]
""",
                "contains a duplicate group",
            ),
            (
                """version = 4
[repository]
required_files = ["package-lock.json"]
required_file_groups = [["package-lock.json", "pnpm-lock.yaml"]]
""",
                "duplicates required path: package-lock.json",
            ),
            (
                """version = 4
[repository]
forbidden_files = ["yarn.lock"]
required_file_groups = [["package-lock.json", "yarn.lock"]]
""",
                "contains forbidden path: yarn.lock",
            ),
            (
                """version = 4
[repository]
required_file_groups = [["package-lock.json", "secrets/prod.lock"]]
forbidden_file_patterns = ["secrets/*.lock"]
""",
                "path secrets/prod.lock matches forbidden pattern",
            ),
        )

        for policy, message in invalid_policies:
            with self.subTest(message=message), self.assertRaisesRegex(
                PolicyError, message
            ):
                parse_policy(policy)

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

    def test_load_policy_rejects_oversized_file_before_parsing(self) -> None:
        with TemporaryDirectory() as tmp:
            policy_path = Path(tmp) / "team-policy.toml"
            with policy_path.open("wb") as policy_file:
                policy_file.truncate(MAX_POLICY_BYTES + 1)

            with patch(
                "repo_scout.policy.tomllib.loads",
                side_effect=AssertionError(
                    "oversized policy must not be parsed"
                ),
            ) as parser, patch(
                "repo_scout._file_evidence.os.read",
                side_effect=AssertionError(
                    "oversized sparse policy must not be read"
                ),
            ) as descriptor_reader, self.assertRaisesRegex(
                PolicyError,
                f"policy file exceeds {MAX_POLICY_BYTES} bytes",
            ):
                load_policy(policy_path)

            parser.assert_not_called()
            descriptor_reader.assert_not_called()
            self.assertEqual(
                policy_path.stat().st_size,
                MAX_POLICY_BYTES + 1,
            )

    def test_load_policy_accepts_file_at_size_limit(self) -> None:
        with TemporaryDirectory() as tmp:
            policy_path = Path(tmp) / "team-policy.toml"
            base = b"version = 1\n[repository]\nmax_files = 10\n"
            padding = b"#" + (
                b"x" * (MAX_POLICY_BYTES - len(base) - 2)
            ) + b"\n"
            policy_path.write_bytes(base + padding)

            policy = load_policy(policy_path)

            self.assertEqual(policy["version"], 1)
            self.assertEqual(policy["repository"], {"max_files": 10})
            self.assertEqual(policy_path.stat().st_size, MAX_POLICY_BYTES)

    def test_load_policy_bounds_growth_during_initial_read(self) -> None:
        with TemporaryDirectory() as tmp:
            policy_path = Path(tmp) / "team-policy.toml"
            policy_path.write_text(
                "version = 1\n[repository]\nmax_files = 10\n",
                encoding="utf-8",
            )
            original_details = policy_path.stat()
            original_read = os.read
            policy_grew = False

            def grow_before_first_read(
                descriptor: int,
                size: int,
            ) -> bytes:
                nonlocal policy_grew
                if not policy_grew:
                    with policy_path.open("r+b") as policy_file:
                        policy_file.truncate(MAX_POLICY_BYTES + 1)
                    policy_grew = True
                return original_read(descriptor, size)

            with patch(
                "repo_scout._file_evidence.os.read",
                side_effect=grow_before_first_read,
            ), self.assertRaisesRegex(
                PolicyError,
                f"policy file exceeds {MAX_POLICY_BYTES} bytes",
            ):
                load_policy(policy_path)

            self.assertTrue(policy_grew)
            self.assertTrue(
                os.path.samestat(original_details, policy_path.stat())
            )
            self.assertEqual(
                policy_path.stat().st_size,
                MAX_POLICY_BYTES + 1,
            )

    def test_load_policy_rejects_non_regular_paths_before_read(self) -> None:
        kinds = ["directory"]
        if hasattr(os, "symlink"):
            kinds.append("symlink")
        if hasattr(os, "mkfifo"):
            kinds.append("fifo")
        for kind in kinds:
            with self.subTest(kind=kind), TemporaryDirectory() as tmp:
                root = Path(tmp)
                policy_path = root / "team-policy.toml"
                target = root / "stored-policy.toml"
                target.write_text(
                    "version = 1\n[repository]\nmax_files = 10\n",
                    encoding="utf-8",
                )
                if kind == "symlink":
                    policy_path.symlink_to(target)
                elif kind == "directory":
                    policy_path.mkdir()
                else:
                    os.mkfifo(policy_path)

                with patch(
                    "repo_scout.policy.read_stable_regular_file",
                    side_effect=AssertionError(
                        "non-regular policy path must not be read"
                    ),
                ) as stable_reader, self.assertRaises(PolicyError) as raised:
                    load_policy(policy_path)

                message = str(raised.exception)
                self.assertIn(
                    (
                        "policy path must not be a symlink"
                        if kind == "symlink"
                        else "policy path must be a regular file"
                    ),
                    message,
                )
                self.assertIn(str(policy_path), message)
                stable_reader.assert_not_called()
                if kind == "symlink":
                    resolved_target = target.parent.resolve() / target.name
                    self.assertNotIn(str(resolved_target), message)
                    self.assertTrue(policy_path.is_symlink())
                    self.assertTrue(target.is_file())
                elif kind == "directory":
                    self.assertTrue(policy_path.is_dir())
                else:
                    self.assertTrue(stat.S_ISFIFO(policy_path.lstat().st_mode))

    def test_load_policy_rejects_leaf_replacement_before_read(self) -> None:
        replacement_kinds = ["regular"]
        if hasattr(os, "symlink"):
            replacement_kinds.append("symlink")
        for replacement_kind in replacement_kinds:
            with self.subTest(
                replacement_kind=replacement_kind
            ), TemporaryDirectory() as tmp:
                root = Path(tmp)
                policy_path = root / "team-policy.toml"
                policy_content = (
                    "version = 1\n[repository]\nmax_files = 10\n"
                )
                policy_path.write_text(policy_content, encoding="utf-8")
                replacement = root / "replacement-policy.toml"
                replacement.write_text(policy_content, encoding="utf-8")
                original = root / "original-policy.toml"
                expected_policy_path = (
                    policy_path.parent.resolve() / policy_path.name
                )
                original_lstat = Path.lstat
                replacement_made = False

                def replace_after_lstat(path: Path) -> os.stat_result:
                    nonlocal replacement_made
                    details = original_lstat(path)
                    if path == expected_policy_path and not replacement_made:
                        policy_path.replace(original)
                        if replacement_kind == "symlink":
                            policy_path.symlink_to(original)
                        else:
                            replacement.replace(policy_path)
                        replacement_made = True
                    return details

                with patch.object(
                    Path,
                    "lstat",
                    replace_after_lstat,
                ), self.assertRaisesRegex(
                    PolicyError,
                    "policy path changed during loading",
                ):
                    load_policy(policy_path)

                self.assertTrue(replacement_made)
                self.assertTrue(original.is_file())
                if replacement_kind == "symlink":
                    self.assertTrue(policy_path.is_symlink())
                    self.assertTrue(replacement.is_file())
                else:
                    self.assertTrue(policy_path.is_file())
                    self.assertFalse(policy_path.is_symlink())

    def test_load_policy_rechecks_leaf_after_validation(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            policy_path = root / "team-policy.toml"
            policy_content = "version = 1\n[repository]\nmax_files = 10\n"
            policy_path.write_text(policy_content, encoding="utf-8")
            replacement = root / "replacement-policy.toml"
            replacement.write_text(policy_content, encoding="utf-8")
            original = root / "original-policy.toml"
            original_validator = policy_module._validate_policy
            replacement_made = False

            def replace_after_validation(
                policy: object,
                source: str | Path,
            ) -> dict[str, object]:
                nonlocal replacement_made
                validated = original_validator(policy, source)
                policy_path.replace(original)
                replacement.replace(policy_path)
                replacement_made = True
                return validated

            with patch(
                "repo_scout.policy._validate_policy",
                side_effect=replace_after_validation,
            ), self.assertRaisesRegex(
                PolicyError,
                "policy path changed during loading",
            ):
                load_policy(policy_path)

            self.assertTrue(replacement_made)
            self.assertTrue(original.is_file())
            self.assertTrue(policy_path.is_file())

    def test_load_policy_rechecks_bytes_after_validation(self) -> None:
        with TemporaryDirectory() as tmp:
            policy_path = Path(tmp) / "team-policy.toml"
            policy_path.write_text(
                "version = 1\n[repository]\nmax_files = 10\n",
                encoding="utf-8",
            )
            original_details = policy_path.stat()
            original_validator = policy_module._validate_policy
            policy_rewritten = False

            def rewrite_after_validation(
                policy: object,
                source: str | Path,
            ) -> dict[str, object]:
                nonlocal policy_rewritten
                validated = original_validator(policy, source)
                policy_path.write_text("version = 999\n", encoding="utf-8")
                policy_rewritten = True
                return validated

            with patch(
                "repo_scout.policy._validate_policy",
                side_effect=rewrite_after_validation,
            ), self.assertRaisesRegex(
                PolicyError,
                "policy changed during loading",
            ):
                load_policy(policy_path)

            self.assertTrue(policy_rewritten)
            self.assertTrue(
                os.path.samestat(original_details, policy_path.stat())
            )

    def test_load_policy_bounds_growth_during_validation(self) -> None:
        with TemporaryDirectory() as tmp:
            policy_path = Path(tmp) / "team-policy.toml"
            policy_path.write_text(
                "version = 1\n[repository]\nmax_files = 10\n",
                encoding="utf-8",
            )
            original_details = policy_path.stat()
            original_validator = policy_module._validate_policy
            policy_grew = False

            def grow_after_validation(
                policy: object,
                source: str | Path,
            ) -> dict[str, object]:
                nonlocal policy_grew
                validated = original_validator(policy, source)
                with policy_path.open("r+b") as policy_file:
                    policy_file.truncate(MAX_POLICY_BYTES + 1)
                policy_grew = True
                return validated

            with patch(
                "repo_scout.policy._validate_policy",
                side_effect=grow_after_validation,
            ), self.assertRaisesRegex(
                PolicyError,
                "policy changed during loading",
            ):
                load_policy(policy_path)

            self.assertTrue(policy_grew)
            self.assertTrue(
                os.path.samestat(original_details, policy_path.stat())
            )
            self.assertEqual(
                policy_path.stat().st_size,
                MAX_POLICY_BYTES + 1,
            )

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

    def test_policy_fingerprint_normalizes_required_file_groups(self) -> None:
        first = parse_policy(
            """version = 4
[repository]
required_file_groups = [
  ["package-lock.json", "pnpm-lock.yaml"],
  ["Dockerfile", "Containerfile"],
]
"""
        )
        reordered = parse_policy(
            """version = 4
[repository]
required_file_groups = [
  ["Containerfile", "Dockerfile"],
  ["pnpm-lock.yaml", "package-lock.json"],
]
"""
        )
        changed = parse_policy(
            """version = 4
[repository]
required_file_groups = [
  ["package-lock.json", "yarn.lock"],
  ["Dockerfile", "Containerfile"],
]
"""
        )

        self.assertEqual(policy_fingerprint(first), policy_fingerprint(reordered))
        self.assertNotEqual(policy_fingerprint(first), policy_fingerprint(changed))


if __name__ == "__main__":
    unittest.main()
