from __future__ import annotations

from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "pilot-intake.yml"

CHECKOUT_ACTION = (
    "actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1"
)
SETUP_PYTHON_ACTION = (
    "actions/setup-python@5fda3b95a4ea91299a34e894583c3862153e4b97"
)
TRIGGER_PATHS = (
    ".gitignore",
    ".github/ISSUE_TEMPLATE/founding-team-pilot.yml",
    ".github/workflows/pilot-intake.yml",
    "BUSINESS_MODEL.md",
    "DISTRIBUTION.md",
    "docs/github-actions.md",
    "docs/pilot-rollout.md",
    "docs/pilot-tracking.md",
    "examples/pilot-delivery-record.md",
    "pyproject.toml",
    "scripts/audit_pilot_labels.py",
    "src/repo_scout/pilot_funnel.py",
    "tests/test_pilot_delivery_contract.py",
    "tests/test_pilot_intake_workflow.py",
    "tests/test_pilot_label_audit.py",
)


class PilotIntakeWorkflowContractTests(unittest.TestCase):
    def test_workflow_is_read_only_bounded_and_fail_closed(self) -> None:
        self.assertTrue(
            WORKFLOW.is_file(),
            f"missing pilot intake workflow: {WORKFLOW.relative_to(ROOT)}",
        )
        workflow = WORKFLOW.read_text(encoding="utf-8")

        self.assertIn("name: Pilot intake contract", workflow)
        trigger_block = workflow[
            workflow.index("on:\n") : workflow.index("\npermissions:\n")
        ]
        events = re.findall(
            r"^  ([a-z_]+):(?:\s.*)?$",
            trigger_block,
            re.MULTILINE,
        )
        self.assertEqual(events, ["pull_request", "push", "workflow_dispatch"])
        self.assertEqual(trigger_block.count("branches: [main]"), 1)
        trigger_paths = re.findall(
            r'^\s{6}- "([^"]+)"$',
            trigger_block,
            re.MULTILINE,
        )
        self.assertEqual(trigger_paths, list(TRIGGER_PATHS) * 2)

        self.assertRegex(
            workflow,
            r"(?m)^permissions:\n  contents: read\n  issues: read\n(?:\n|$)",
        )
        self.assertEqual(workflow.count("permissions:"), 1)
        self.assertEqual(workflow.count("\njobs:\n"), 1)
        jobs_block = workflow[workflow.index("jobs:\n") :]
        jobs = re.findall(r"^  ([\w-]+):\s*$", jobs_block, re.MULTILINE)
        self.assertEqual(jobs, ["audit"])
        self.assertIn("runs-on: ubuntu-24.04", jobs_block)
        self.assertNotRegex(workflow, r"(?m)^\s*[\w-]+:\s*write\s*$")
        self.assertNotRegex(workflow, r"(?im)^\s*secrets\s*:")
        self.assertNotRegex(workflow, r"\$\{\{\s*secrets\.")

        timeouts = re.findall(
            r"^\s+timeout-minutes:\s*(\d+)\s*$",
            workflow,
            re.MULTILINE,
        )
        self.assertEqual(timeouts, ["2"])

        actions = re.findall(
            r"^\s*uses:\s*([^\s#]+)",
            workflow,
            re.MULTILINE,
        )
        self.assertEqual(actions, [CHECKOUT_ACTION, SETUP_PYTHON_ACTION])
        self.assertEqual(
            workflow.count(f"uses: {CHECKOUT_ACTION} # v7.0.1"),
            1,
        )
        self.assertEqual(
            workflow.count(f"uses: {SETUP_PYTHON_ACTION} # v7.0.0"),
            1,
        )
        for action in actions:
            self.assertRegex(action, r"^[\w.-]+/[\w.-]+@[0-9a-f]{40}$")

        self.assertIn("persist-credentials: false", workflow)
        self.assertIn('python-version: "3.11"', workflow)

        contract_command = (
            "run: >-\n"
            "          python -m unittest\n"
            "          tests.test_pilot_intake_workflow\n"
            "          tests.test_pilot_label_audit\n"
            "          tests.test_pilot_delivery_contract"
        )
        label_audit_command = (
            'run: python scripts/audit_pilot_labels.py --repo '
            '"$GITHUB_REPOSITORY"'
        )
        self.assertEqual(workflow.count(contract_command), 1)
        self.assertEqual(workflow.count(label_audit_command), 1)
        self.assertEqual(
            len(re.findall(r"^\s+run:", workflow, re.MULTILINE)),
            2,
        )
        self.assertLess(
            workflow.index(f"uses: {CHECKOUT_ACTION}"),
            workflow.index(f"uses: {SETUP_PYTHON_ACTION}"),
        )
        self.assertLess(
            workflow.index(f"uses: {SETUP_PYTHON_ACTION}"),
            workflow.index(contract_command),
        )
        self.assertLess(
            workflow.index(contract_command),
            workflow.index(label_audit_command),
        )
        live_audit_step = (
            "      - name: Audit live pilot labels\n"
            "        env:\n"
            "          GH_TOKEN: ${{ github.token }}\n"
            f"        {label_audit_command}"
        )
        self.assertEqual(workflow.count(live_audit_step), 1)
        self.assertEqual(workflow.count("GH_TOKEN:"), 1)
        self.assertNotIn("--repair", workflow)
        self.assertNotIn("continue-on-error", workflow)
        self.assertNotIn("|| true", workflow)


if __name__ == "__main__":
    unittest.main()
