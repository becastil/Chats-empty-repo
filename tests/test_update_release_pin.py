from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "update_release_pin.py"
SPEC = importlib.util.spec_from_file_location("update_release_pin", SCRIPT_PATH)
assert SPEC is not None and SPEC.loader is not None
update_release_pin = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = update_release_pin
SPEC.loader.exec_module(update_release_pin)


OLD_VERSION = "1.2.3"
OLD_SOURCE = "1" * 40
OLD_DIGEST = "2" * 64
NEW_PIN = update_release_pin.ReleasePin("2.0.1", "a" * 40, "b" * 64)


class UpdateReleasePinTests(unittest.TestCase):
    def test_updates_workflows_readme_and_test_contract(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_fixture(root)

            updated = update_release_pin.update_release_pin(root, NEW_PIN)

            self.assertEqual(updated, update_release_pin.TARGETS)
            for path in updated:
                content = (root / path).read_text(encoding="utf-8")
                self.assertIn(NEW_PIN.version, content)
                self.assertNotIn(OLD_VERSION, content)
                if path != update_release_pin.README_PATH:
                    self.assertIn(NEW_PIN.source_sha, content)
                    self.assertIn(NEW_PIN.wheel_sha256, content)
            readme = (root / update_release_pin.README_PATH).read_text(
                encoding="utf-8"
            )
            self.assertIn("Quick start remains `v9.9.9`.", readme)

    def test_preflight_failure_leaves_every_target_unchanged(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_fixture(root)
            broken = root / "examples/github-actions/repo-scout-policy.yml"
            broken.write_text("name: missing pins\n", encoding="utf-8")
            before = {
                path: (root / path).read_text(encoding="utf-8")
                for path in update_release_pin.TARGETS
            }

            with self.assertRaisesRegex(
                update_release_pin.PinUpdateError, "exactly one version pin"
            ):
                update_release_pin.update_release_pin(root, NEW_PIN)

            self.assertEqual(
                {
                    path: (root / path).read_text(encoding="utf-8")
                    for path in update_release_pin.TARGETS
                },
                before,
            )

    def test_readme_layout_failure_leaves_every_target_unchanged(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_fixture(root)
            readme = root / update_release_pin.README_PATH
            readme.write_text("# missing verified CI version\n", encoding="utf-8")
            before = {
                path: (root / path).read_text(encoding="utf-8")
                for path in update_release_pin.TARGETS
            }

            with self.assertRaisesRegex(
                update_release_pin.PinUpdateError, "verified CI version"
            ):
                update_release_pin.update_release_pin(root, NEW_PIN)

            self.assertEqual(
                {
                    path: (root / path).read_text(encoding="utf-8")
                    for path in update_release_pin.TARGETS
                },
                before,
            )

    def test_mid_commit_failure_rolls_back_every_updated_target(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_fixture(root)
            before = {
                path: (root / path).read_text(encoding="utf-8")
                for path in update_release_pin.TARGETS
            }
            real_replace = update_release_pin.os.replace
            replace_calls = 0

            def fail_second_replace(source: Path, target: Path) -> None:
                nonlocal replace_calls
                replace_calls += 1
                if replace_calls == 2:
                    raise OSError("synthetic second replace failure")
                real_replace(source, target)

            with patch.object(
                update_release_pin.os,
                "replace",
                side_effect=fail_second_replace,
            ), self.assertRaisesRegex(
                update_release_pin.PinUpdateError,
                "rolled back 1 updated target",
            ):
                update_release_pin.update_release_pin(root, NEW_PIN)

            self.assertEqual(
                {
                    path: (root / path).read_text(encoding="utf-8")
                    for path in update_release_pin.TARGETS
                },
                before,
            )
            self.assertEqual(
                [
                    path
                    for path in root.rglob(".*.pin-*")
                    if path.is_file()
                ],
                [],
            )

    def test_rollback_failure_retains_original_for_recovery(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_fixture(root)
            first_target = root / update_release_pin.TARGETS[0]
            original = first_target.read_text(encoding="utf-8")
            real_replace = update_release_pin.os.replace
            replace_calls = 0

            def fail_write_and_rollback(source: Path, target: Path) -> None:
                nonlocal replace_calls
                replace_calls += 1
                if replace_calls in {2, 3}:
                    raise OSError(f"synthetic replace failure {replace_calls}")
                real_replace(source, target)

            with patch.object(
                update_release_pin.os,
                "replace",
                side_effect=fail_write_and_rollback,
            ), self.assertRaisesRegex(
                update_release_pin.PinUpdateError,
                "rollback incomplete.*original retained at",
            ):
                update_release_pin.update_release_pin(root, NEW_PIN)

            recovery_paths = [
                path
                for path in first_target.parent.glob(
                    f".{first_target.name}.pin-rollback.*"
                )
                if path.is_file()
            ]
            self.assertEqual(len(recovery_paths), 1)
            self.assertEqual(
                recovery_paths[0].read_text(encoding="utf-8"),
                original,
            )

    def test_rejects_unverified_identity_shapes(self) -> None:
        invalid = (
            (update_release_pin.ReleasePin("v1.2.3", "a" * 40, "b" * 64), "version"),
            (update_release_pin.ReleasePin("1.2.3", "A" * 40, "b" * 64), "source"),
            (update_release_pin.ReleasePin("1.2.3", "a" * 40, "b" * 63), "wheel"),
        )
        for pin, message in invalid:
            with self.subTest(message=message), self.assertRaisesRegex(
                update_release_pin.PinUpdateError, message
            ):
                pin.validate()

    @staticmethod
    def _write_fixture(root: Path) -> None:
        workflow = (
            "env:\n"
            f'  REPO_SCOUT_VERSION: "{OLD_VERSION}"\n'
            f"  REPO_SCOUT_SOURCE_SHA: {OLD_SOURCE}\n"
            f"  REPO_SCOUT_WHEEL_SHA256: {OLD_DIGEST}\n"
        )
        for path in update_release_pin.TARGETS[:2]:
            target = root / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(workflow, encoding="utf-8")

        readme = root / update_release_pin.README_PATH
        readme.write_text(
            "Quick start remains `v9.9.9`.\n"
            "evidence, and a downloadable schema-2 rollout bundle. "
            f"It installs the `v{OLD_VERSION}`\n",
            encoding="utf-8",
        )

        contract = root / update_release_pin.TEST_CONTRACT_PATH
        contract.parent.mkdir(parents=True, exist_ok=True)
        contract.write_text(
            f'REPO_SCOUT_VERSION = "{OLD_VERSION}"\n'
            f'REPO_SCOUT_SOURCE_SHA = "{OLD_SOURCE}"\n'
            "REPO_SCOUT_WHEEL_SHA256 = (\n"
            f'    "{OLD_DIGEST}"\n'
            ")\n",
            encoding="utf-8",
        )


if __name__ == "__main__":
    unittest.main()
