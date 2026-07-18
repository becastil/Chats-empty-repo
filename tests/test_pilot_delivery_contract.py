from __future__ import annotations

from pathlib import Path
import tomllib
import unittest


ROOT = Path(__file__).resolve().parents[1]
ROLLOUT_GUIDE = ROOT / "docs" / "pilot-rollout.md"
CI_GUIDE = ROOT / "docs" / "github-actions.md"
BUSINESS_MODEL = ROOT / "BUSINESS_MODEL.md"
INTAKE_FORM = ROOT / ".github" / "ISSUE_TEMPLATE" / "founding-team-pilot.yml"


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


if __name__ == "__main__":
    unittest.main()
