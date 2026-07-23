from __future__ import annotations

from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "production-site-audit.yml"

CHECKOUT_ACTION = (
    "actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1"
)
SETUP_PYTHON_ACTION = (
    "actions/setup-python@ece7cb06caefa5fff74198d8649806c4678c61a1"
)


class ProductionSiteWorkflowContractTests(unittest.TestCase):
    def test_production_site_audit_workflow_is_bounded_and_read_only(self) -> None:
        self.assertTrue(
            WORKFLOW.is_file(),
            f"missing production-site audit workflow: {WORKFLOW.relative_to(ROOT)}",
        )
        workflow = WORKFLOW.read_text(encoding="utf-8")

        self.assertIn("workflow_dispatch:", workflow)
        cron_entries = re.findall(
            r'^\s*-\s+cron:\s*["\']?(\d+)\s+(\d+)\s+\*\s+\*\s+\*["\']?\s*$',
            workflow,
            re.MULTILINE,
        )
        self.assertEqual(workflow.count("cron:"), 1)
        self.assertEqual(len(cron_entries), 1)
        minute, hour = (int(value) for value in cron_entries[0])
        self.assertIn(minute, range(60))
        self.assertIn(hour, range(24))

        self.assertRegex(
            workflow,
            r"(?m)^permissions:\n  contents: read\n(?:\n|$)",
        )
        self.assertEqual(workflow.count("permissions:"), 1)
        self.assertNotRegex(workflow, r"(?m)^\s*[\w-]+:\s*write\s*$")
        self.assertNotRegex(workflow, r"(?im)^\s*secrets\s*:")
        self.assertNotRegex(workflow, r"\$\{\{\s*secrets\.")

        timeouts = re.findall(
            r"^\s+timeout-minutes:\s*(\d+)\s*$",
            workflow,
            re.MULTILINE,
        )
        self.assertEqual(len(timeouts), 1)
        self.assertIn(int(timeouts[0]), range(1, 6))

        actions = re.findall(
            r"^\s*uses:\s*([^\s#]+)",
            workflow,
            re.MULTILINE,
        )
        self.assertEqual(actions, [CHECKOUT_ACTION, SETUP_PYTHON_ACTION])
        for action in actions:
            self.assertRegex(action, r"^[\w.-]+/[\w.-]+@[0-9a-f]{40}$")

        self.assertIn("ref: ${{ github.sha }}", workflow)
        self.assertIn("persist-credentials: false", workflow)
        self.assertIn('python-version: "3.11"', workflow)

        run_commands = re.findall(
            r"^\s+run:\s*(\S.*?)\s*$",
            workflow,
            re.MULTILINE,
        )
        self.assertEqual(
            run_commands,
            ["python3 scripts/audit_production_site.py"],
        )


if __name__ == "__main__":
    unittest.main()
