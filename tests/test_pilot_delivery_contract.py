from __future__ import annotations

import os
from pathlib import Path
import shutil
import stat
import subprocess
from tempfile import TemporaryDirectory
import tomllib
import unittest


ROOT = Path(__file__).resolve().parents[1]
ROLLOUT_GUIDE = ROOT / "docs" / "pilot-rollout.md"
PILOT_TRACKING = ROOT / "docs" / "pilot-tracking.md"
CI_GUIDE = ROOT / "docs" / "github-actions.md"
BUSINESS_MODEL = ROOT / "BUSINESS_MODEL.md"
INTAKE_FORM = ROOT / ".github" / "ISSUE_TEMPLATE" / "founding-team-pilot.yml"
DELIVERY_TEMPLATE = ROOT / "examples" / "pilot-delivery-record.md"


class PilotDeliveryContractTests(unittest.TestCase):
    def test_delivery_scope_matches_the_paid_offer(self) -> None:
        guide = ROLLOUT_GUIDE.read_text(encoding="utf-8")
        normalized = " ".join(guide.split())
        business_model = " ".join(
            BUSINESS_MODEL.read_text(encoding="utf-8").split()
        )

        self.assertIn("## Paid Pilot Delivery Contract", guide)
        self.assertIn("The $299 pilot", guide)
        self.assertIn("90-day start and end dates", normalized)
        self.assertIn("no more than 10 stable repository IDs", normalized)
        self.assertIn("customer-controlled access method", normalized)
        self.assertIn("standards and exception owner", normalized)
        self.assertIn("private communication and evidence location", normalized)
        self.assertIn("first repository identified", normalized)
        self.assertIn("One reviewed, version-controlled custom policy pack", guide)
        self.assertIn("One closeout record", guide)
        self.assertIn(
            "Price: $299 for 90 days, covering up to 10 repositories.",
            business_model,
        )

    def test_delivery_contract_discloses_the_shipped_ci_boundary(self) -> None:
        guide = " ".join(ROLLOUT_GUIDE.read_text(encoding="utf-8").split())
        intake = INTAKE_FORM.read_text(encoding="utf-8")

        for provider in ("GitHub Actions", "GitLab CI", "CircleCI", "Buildkite"):
            self.assertIn(provider, intake)
            self.assertIn(provider, guide)

        self.assertIn(
            "GitHub Actions is the only copy-ready gate currently shipped",
            guide,
        )
        self.assertIn("record before payment", guide)
        self.assertIn("do not imply shipped provider support", guide)

    def test_blank_delivery_record_is_bounded_private_and_copy_ready(self) -> None:
        template = DELIVERY_TEMPLATE.read_text(encoding="utf-8")
        normalized = " ".join(template.split())
        repository_slots = [
            line for line in template.splitlines() if line.startswith("- Repository ")
        ]

        self.assertIn("# Repo Scout Paid Pilot Delivery Record", template)
        self.assertIn("Blank operator template", template)
        self.assertIn("Maximum repository scope: 10", template)
        self.assertEqual(
            repository_slots,
            [
                f"- Repository {number:02d}: `[PRIVATE REPOSITORY ID]` "
                "| Status: `In scope / Unused`"
                for number in range(1, 11)
            ],
        )
        for field in (
            "Payment confirmed at (UTC)",
            "Payment confirmed by",
            "Private payment evidence reference",
            "Pilot start date (UTC)",
            "Pilot end date (UTC)",
            "Customer:",
            "Public funnel issue number",
            "Customer owner",
            "Repo Scout delivery owner",
            "CI provider",
            "Customer-controlled access method",
            "Private communication and evidence location",
            "Agreed policy objective",
            "Exception owner",
            "First repository",
            "Repo Scout version",
            "Exact source and artifact pin reference",
            "First CI run result",
            "Customer acknowledgement date (UTC)",
            "Annual-license decision",
            "Customer closeout acknowledgement (UTC)",
        ):
            self.assertIn(field, template)

        self.assertIn("Record the option agreed before payment", template)
        self.assertIn("Scope changes require dated written approval", template)
        self.assertIn("never add an eleventh slot", template)
        self.assertIn("GitHub Actions is the only copy-ready gate", template)
        self.assertIn("verify-receipt bootstrap-receipt.json", template)
        self.assertIn("`repo-scout-rollout` summary generated", template)
        self.assertIn("## Shipped-Command Evidence", template)
        self.assertIn("## Revenue Stage Ledger", template)
        self.assertIn(
            "`pilot-converted` and `pilot-lost` are not both applied",
            template,
        )
        self.assertLess(
            normalized.index("`pilot-paid` applied"),
            normalized.index("`pilot-active` applied"),
        )
        self.assertLess(
            normalized.index("`pilot-active` applied"),
            normalized.index("`pilot-converted` applied"),
        )
        self.assertNotIn("https://", template)
        self.assertNotIn("@", template)
        self.assertNotIn("prospect-", template)

    def test_delivery_evidence_uses_shipped_commands(self) -> None:
        guide = ROLLOUT_GUIDE.read_text(encoding="utf-8")
        pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
        scripts = pyproject["project"]["scripts"]

        for command in ("repo-scout", "repo-scout-policy", "repo-scout-rollout"):
            self.assertIn(command, scripts)
            self.assertIn(f"{command} ", guide)

        self.assertIn("verify-receipt bootstrap-receipt.json", guide)
        self.assertIn("--rollout-checklist", guide)
        self.assertIn("--repository-id owner/repository", guide)

    def test_local_delivery_workspace_is_ignored_and_owner_only(self) -> None:
        guide = ROLLOUT_GUIDE.read_text(encoding="utf-8")
        gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")

        self.assertIn("/pilot-private/", gitignore)
        self.assertIn("install -d -m 700 pilot-private", guide)
        self.assertIn(
            "install -m 600 examples/pilot-delivery-record.md", guide
        )
        self.assertIn(
            "git check-ignore --quiet pilot-private/delivery-record.md", guide
        )
        self.assertIn("An ignored path is not encryption or access control", guide)
        self.assertIn("never force-add the completed copy", guide)

        ignored = subprocess.run(
            ["git", "check-ignore", "--quiet", "pilot-private/delivery-record.md"],
            cwd=ROOT,
            check=False,
        )
        tracked_template = subprocess.run(
            ["git", "check-ignore", "--quiet", "examples/pilot-delivery-record.md"],
            cwd=ROOT,
            check=False,
        )
        self.assertEqual(ignored.returncode, 0)
        self.assertNotEqual(tracked_template.returncode, 0)

    def test_local_delivery_workspace_commands_set_owner_only_modes(self) -> None:
        if os.name != "posix" or shutil.which("install") is None:
            self.skipTest("POSIX install command is unavailable")

        guide = ROLLOUT_GUIDE.read_text(encoding="utf-8").replace("\\\n", "")
        guide = " ".join(guide.split())
        self.assertIn("install -d -m 700 pilot-private", guide)
        self.assertIn(
            "install -m 600 examples/pilot-delivery-record.md "
            "pilot-private/delivery-record.md",
            guide,
        )

        with TemporaryDirectory() as temporary_directory:
            isolated_root = Path(temporary_directory)
            isolated_examples = isolated_root / "examples"
            isolated_examples.mkdir()
            isolated_template = isolated_examples / "pilot-delivery-record.md"
            shutil.copyfile(DELIVERY_TEMPLATE, isolated_template)

            subprocess.run(
                ["install", "-d", "-m", "700", "pilot-private"],
                cwd=isolated_root,
                check=True,
            )
            subprocess.run(
                [
                    "install",
                    "-m",
                    "600",
                    "examples/pilot-delivery-record.md",
                    "pilot-private/delivery-record.md",
                ],
                cwd=isolated_root,
                check=True,
            )

            workspace = isolated_root / "pilot-private"
            completed_record = workspace / "delivery-record.md"
            self.assertTrue(workspace.is_dir())
            self.assertTrue(completed_record.is_file())
            self.assertEqual(stat.S_IMODE(workspace.stat().st_mode), 0o700)
            self.assertEqual(stat.S_IMODE(completed_record.stat().st_mode), 0o600)
            self.assertEqual(
                completed_record.read_bytes(),
                DELIVERY_TEMPLATE.read_bytes(),
            )

    def test_payment_activation_and_conversion_remain_human_evidence(self) -> None:
        guide = ROLLOUT_GUIDE.read_text(encoding="utf-8")
        normalized = " ".join(guide.split())

        self.assertIn("Apply `pilot-paid` only after payment is received", normalized)
        self.assertIn("Apply `pilot-active` only", normalized)
        self.assertIn("one completed CI policy run", normalized)
        self.assertIn("passing or remediation-required rollout bundle", normalized)
        self.assertIn("remediation owner and next repository recorded", normalized)
        self.assertIn("customer acknowledgement of the handoff", normalized)
        self.assertIn("Apply `pilot-converted` only", normalized)
        self.assertIn("never apply labels automatically", normalized)
        self.assertIn("is not payment, activation", normalized)
        self.assertLess(
            normalized.index("Apply `pilot-paid`"),
            normalized.index("Apply `pilot-active`"),
        )
        self.assertLess(
            normalized.index("Apply `pilot-active`"),
            normalized.index("Apply `pilot-converted`"),
        )

    def test_public_activation_label_requires_private_handoff_evidence(self) -> None:
        tracking = " ".join(PILOT_TRACKING.read_text(encoding="utf-8").split())

        self.assertIn(
            "[paid delivery contract]"
            "(pilot-rollout.md#paid-pilot-delivery-contract)",
            tracking,
        )
        self.assertIn(
            "Apply `pilot-active` only after `pilot-paid` is already present",
            tracking,
        )
        self.assertIn(
            "every activation condition in that contract is satisfied",
            tracking,
        )
        self.assertIn(
            "including customer acknowledgement of the first-repository "
            "handoff",
            tracking,
        )
        self.assertIn(
            "Keep repository identity, access, CI evidence, payment details, "
            "and the acknowledgement record in the customer-approved private "
            "system",
            tracking,
        )
        self.assertIn(
            "The public issue receives only the cumulative label and a "
            "non-sensitive status note",
            tracking,
        )

    def test_delivery_details_stay_out_of_the_public_issue(self) -> None:
        guide = ROLLOUT_GUIDE.read_text(encoding="utf-8")
        ci_guide = CI_GUIDE.read_text(encoding="utf-8")

        for private_detail in (
            "private repository names",
            "source code",
            "credentials",
            "customer data",
            "payment details",
            "rollout bundles",
        ):
            self.assertIn(private_detail, guide)

        self.assertIn(
            "[paid delivery contract](pilot-rollout.md#paid-pilot-delivery-contract)",
            ci_guide,
        )
        self.assertIn(
            "[blank delivery record template](../examples/pilot-delivery-record.md)",
            guide,
        )


if __name__ == "__main__":
    unittest.main()
