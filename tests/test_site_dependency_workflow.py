from __future__ import annotations

from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "site-dependencies.yml"

CHECKOUT_ACTION = (
    "actions/checkout@9c091bb21b7c1c1d1991bb908d89e4e9dddfe3e0"
)
SETUP_NODE_ACTION = (
    "actions/setup-node@48b55a011bda9f5d6aeb4c2d9c7362e8dae4041e"
)


class SiteDependencyWorkflowContractTests(unittest.TestCase):
    def test_workflow_is_bounded_read_only_and_immutably_pinned(self) -> None:
        self.assertTrue(
            WORKFLOW.is_file(),
            f"missing site dependency workflow: {WORKFLOW.relative_to(ROOT)}",
        )
        workflow = WORKFLOW.read_text(encoding="utf-8")

        self.assertIn("pull_request:", workflow)
        self.assertIn("push:", workflow)
        self.assertIn("branches: [main]", workflow)
        self.assertIn("workflow_dispatch:", workflow)
        self.assertEqual(workflow.count("cron:"), 1)
        self.assertIn('cron: "23 15 * * 1"', workflow)

        for path in (
            "package.json",
            "package-lock.json",
            "tests/dependency-compatibility.test.mjs",
            ".github/workflows/site-dependencies.yml",
        ):
            self.assertEqual(workflow.count(f"- {path}"), 2, path)

        self.assertRegex(
            workflow,
            r"(?m)^permissions:\n  contents: read\n(?:\n|$)",
        )
        self.assertEqual(workflow.count("permissions:"), 1)
        self.assertNotRegex(workflow, r"(?m)^\s*[\w-]+:\s*write\s*$")
        self.assertNotIn("pull_request_target", workflow)
        self.assertNotRegex(workflow, r"(?im)^\s*secrets\s*:")
        self.assertNotRegex(workflow, r"\$\{\{\s*secrets\.")

        self.assertIn("cancel-in-progress: true", workflow)
        timeouts = re.findall(
            r"^\s+timeout-minutes:\s*(\d+)\s*$",
            workflow,
            re.MULTILINE,
        )
        self.assertEqual(timeouts, ["8"])

        actions = re.findall(
            r"^\s*uses:\s*([^\s#]+)",
            workflow,
            re.MULTILINE,
        )
        self.assertEqual(actions, [CHECKOUT_ACTION, SETUP_NODE_ACTION])
        for action in actions:
            self.assertRegex(action, r"^[\w.-]+/[\w.-]+@[0-9a-f]{40}$")

        self.assertIn("ref: ${{ github.sha }}", workflow)
        self.assertIn("persist-credentials: false", workflow)
        self.assertIn('node-version: "22.13.0"', workflow)
        self.assertIn("package-manager-cache: false", workflow)

        run_commands = re.findall(
            r"^\s+run:\s*(\S.*?)\s*$",
            workflow,
            re.MULTILINE,
        )
        self.assertEqual(
            run_commands,
            [
                "npm ci",
                "npm run audit:dependencies",
                "npm test",
                "npm run lint",
            ],
        )
        self.assertNotIn("npm audit fix", workflow)
        self.assertNotIn("continue-on-error", workflow)
        self.assertNotIn("|| true", workflow)


if __name__ == "__main__":
    unittest.main()
