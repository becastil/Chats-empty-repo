from __future__ import annotations

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / ".github" / "dependabot.yml"


class DependabotContractTests(unittest.TestCase):
    def test_updates_are_review_only_grouped_and_bounded(self) -> None:
        self.assertTrue(
            CONFIG.is_file(),
            f"missing Dependabot configuration: {CONFIG.relative_to(ROOT)}",
        )
        config = CONFIG.read_text(encoding="utf-8")

        self.assertIn("version: 2", config)
        self.assertEqual(config.count("package-ecosystem:"), 2)
        self.assertNotIn("target-branch:", config)
        self.assertNotIn("registries:", config)
        self.assertNotIn("assignees:", config)
        self.assertNotIn("automerge", config.lower())
        self.assertNotIn("${{", config)

        npm_marker = '  - package-ecosystem: "npm"\n'
        actions_marker = '  - package-ecosystem: "github-actions"\n'
        npm_start = config.index(npm_marker)
        actions_start = config.index(actions_marker)
        npm = config[npm_start:actions_start]
        actions = config[actions_start:]

        self.assertIn('directory: "/"', npm)
        self.assertIn('interval: "weekly"', npm)
        self.assertIn('day: "monday"', npm)
        self.assertIn('time: "16:00"', npm)
        self.assertIn('timezone: "Etc/UTC"', npm)
        self.assertIn("open-pull-requests-limit: 0", npm)
        self.assertIn("site-security:", npm)
        self.assertIn("applies-to: security-updates", npm)
        self.assertIn('          - "*"', npm)
        self.assertNotIn("version-updates", npm)

        self.assertIn('directory: "/"', actions)
        self.assertIn('interval: "weekly"', actions)
        self.assertIn('day: "monday"', actions)
        self.assertIn('time: "16:30"', actions)
        self.assertIn('timezone: "Etc/UTC"', actions)
        self.assertIn("open-pull-requests-limit: 2", actions)
        self.assertIn("pinned-actions:", actions)
        self.assertIn("applies-to: version-updates", actions)
        self.assertIn('          - "*"', actions)
        self.assertIn('          - "minor"', actions)
        self.assertIn('          - "patch"', actions)


if __name__ == "__main__":
    unittest.main()
