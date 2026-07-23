from __future__ import annotations

from contextlib import redirect_stderr, redirect_stdout
import importlib.util
from io import StringIO
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "audit_action_pins.py"
SPEC = importlib.util.spec_from_file_location("audit_action_pins", SCRIPT_PATH)
assert SPEC is not None
assert SPEC.loader is not None
audit_action_pins = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = audit_action_pins
SPEC.loader.exec_module(audit_action_pins)

CHECKOUT = "actions/checkout"
SETUP_PYTHON = "actions/setup-python"
UPLOAD_ARTIFACT = "actions/upload-artifact"
CHECKOUT_SHA = "1" * 40
SETUP_PYTHON_SHA = "2" * 40
UPLOAD_ARTIFACT_SHA = "3" * 40


def action_line(action: str, sha: str, version: str) -> str:
    return f"      - uses: {action}@{sha} # {version}\n"


class ActionPinAuditTests(unittest.TestCase):
    def test_current_repository_has_one_reviewed_identity_per_action(self) -> None:
        pins = audit_action_pins.audit_action_pins(ROOT)

        self.assertEqual(
            {
                pin.action: (pin.version, len(pin.references))
                for pin in pins
            },
            {
                "actions/attest-build-provenance": ("v4.1.1", 1),
                CHECKOUT: ("v7.0.1", 6),
                "actions/setup-node": ("v6.4.0", 1),
                SETUP_PYTHON: ("v7.0.0", 5),
                UPLOAD_ARTIFACT: ("v7.0.1", 2),
            },
        )
        for pin in pins:
            self.assertRegex(pin.sha, r"^[0-9a-f]{40}$")

    def test_rejects_a_tag_instead_of_a_full_commit_pin(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_policy_surfaces(
                root,
                hosted="      - uses: actions/checkout@v7 # v7.0.1\n",
                customer=action_line(CHECKOUT, CHECKOUT_SHA, "v7.0.1"),
            )

            with self.assertRaisesRegex(
                audit_action_pins.ActionPinAuditError,
                "full 40-character lowercase commit SHA",
            ):
                audit_action_pins.audit_action_pins(root)

    def test_rejects_a_missing_or_nonsemantic_release_comment(self) -> None:
        for label, suffix in (
            ("missing", ""),
            ("major-only", " # v7"),
            ("extra-comment", " # v7.0.1 reviewed"),
        ):
            with self.subTest(case=label), TemporaryDirectory() as tmp:
                root = Path(tmp)
                hosted = f"      - uses: {CHECKOUT}@{CHECKOUT_SHA}{suffix}\n"
                self._write_policy_surfaces(
                    root,
                    hosted=hosted,
                    customer=action_line(CHECKOUT, CHECKOUT_SHA, "v7.0.1"),
                )

                with self.assertRaisesRegex(
                    audit_action_pins.ActionPinAuditError,
                    "semantic release comment",
                ):
                    audit_action_pins.audit_action_pins(root)

    def test_rejects_partial_dependabot_identity_drift(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_policy_surfaces(
                root,
                hosted=action_line(CHECKOUT, "a" * 40, "v7.0.1"),
                customer=action_line(CHECKOUT, "b" * 40, "v7.0.1"),
            )

            with self.assertRaisesRegex(
                audit_action_pins.ActionPinAuditError,
                "actions/checkout has multiple pinned identities",
            ):
                audit_action_pins.audit_action_pins(root)

    def test_rejects_release_annotation_drift_for_the_same_commit(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_policy_surfaces(
                root,
                hosted=action_line(CHECKOUT, CHECKOUT_SHA, "v7.0.1"),
                customer=action_line(CHECKOUT, CHECKOUT_SHA, "v7.0.0"),
            )

            with self.assertRaisesRegex(
                audit_action_pins.ActionPinAuditError,
                "actions/checkout has multiple pinned identities",
            ):
                audit_action_pins.audit_action_pins(root)

    def test_rejects_dogfood_and_customer_action_sequence_drift(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            hosted = (
                action_line(CHECKOUT, CHECKOUT_SHA, "v7.0.1")
                + action_line(SETUP_PYTHON, SETUP_PYTHON_SHA, "v7.0.0")
            )
            self._write_policy_surfaces(
                root,
                hosted=hosted,
                customer=action_line(CHECKOUT, CHECKOUT_SHA, "v7.0.1"),
            )

            with self.assertRaisesRegex(
                audit_action_pins.ActionPinAuditError,
                "policy action sequences differ",
            ):
                audit_action_pins.audit_action_pins(root)

    def test_rejects_an_external_container_outside_the_commit_contract(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            external = action_line(CHECKOUT, CHECKOUT_SHA, "v7.0.1")
            container = "      - uses: docker://alpine:3.22\n"
            self._write_policy_surfaces(
                root,
                hosted=external + container,
                customer=external + container,
            )

            with self.assertRaisesRegex(
                audit_action_pins.ActionPinAuditError,
                "unsupported external action reference 'docker://alpine:3.22'",
            ):
                audit_action_pins.audit_action_pins(root)

    def test_local_actions_do_not_enter_the_external_pin_inventory(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            external = action_line(CHECKOUT, CHECKOUT_SHA, "v7.0.1")
            local = "      - uses: ./local-action\n"
            self._write_policy_surfaces(
                root,
                hosted=external + local,
                customer=external + local,
            )

            pins = audit_action_pins.audit_action_pins(root)

            self.assertEqual(
                [(pin.action, pin.references) for pin in pins],
                [
                    (
                        CHECKOUT,
                        (
                            ".github/workflows/repo-scout-policy.yml:1",
                            "examples/github-actions/repo-scout-policy.yml:1",
                        ),
                    )
                ],
            )

    def test_main_reports_bounded_inventory_without_changing_files(self) -> None:
        stdout = StringIO()
        with redirect_stdout(stdout):
            status = audit_action_pins.main(["--root", str(ROOT)])

        self.assertEqual(status, 0)
        self.assertEqual(
            stdout.getvalue().strip(),
            "action pin audit passed: actions=5, references=15, surfaces=6",
        )

    def test_main_fails_closed_on_an_unpinned_reference(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_policy_surfaces(
                root,
                hosted="      - uses: actions/checkout@main # v7.0.1\n",
                customer=action_line(CHECKOUT, CHECKOUT_SHA, "v7.0.1"),
            )
            stderr = StringIO()

            with redirect_stderr(stderr):
                status = audit_action_pins.main(["--root", str(root)])

            self.assertEqual(status, 2)
            self.assertIn(
                "full 40-character lowercase commit SHA",
                stderr.getvalue(),
            )

    @staticmethod
    def _write_policy_surfaces(
        root: Path,
        *,
        hosted: str,
        customer: str,
    ) -> None:
        paths = {
            Path(".github/workflows/repo-scout-policy.yml"): hosted,
            Path("examples/github-actions/repo-scout-policy.yml"): customer,
        }
        for relative_path, content in paths.items():
            target = root / relative_path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
