from __future__ import annotations

from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "release-tooling.yml"

CHECKOUT_ACTION = (
    "actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1"
)
SETUP_PYTHON_ACTION = (
    "actions/setup-python@5fda3b95a4ea91299a34e894583c3862153e4b97"
)
TRIGGER_PATHS = (
    ".github/release-requirements.txt",
    ".github/workflows/release-tooling.yml",
    ".github/workflows/release.yml",
    "LICENSE",
    "README.md",
    "pyproject.toml",
    "scripts/build_zipapp.py",
    "scripts/prepare_release.py",
    "src/**",
    "tests/**",
)


class ReleaseToolingWorkflowContractTests(unittest.TestCase):
    def test_workflow_is_pre_tag_read_only_and_fail_closed(self) -> None:
        self.assertTrue(
            WORKFLOW.is_file(),
            f"missing release tooling workflow: {WORKFLOW.relative_to(ROOT)}",
        )
        workflow = WORKFLOW.read_text(encoding="utf-8")

        self.assertIn("name: Release tooling contract", workflow)
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
        self.assertNotIn("tags:", trigger_block)
        self.assertNotIn("schedule:", trigger_block)
        self.assertNotIn("pull_request_target", trigger_block)

        self.assertRegex(
            workflow,
            r"(?m)^permissions:\n  contents: read\n(?:\n|$)",
        )
        self.assertEqual(workflow.count("permissions:"), 1)
        self.assertNotRegex(workflow, r"(?m)^\s*[\w-]+:\s*write\s*$")
        self.assertNotRegex(workflow, r"(?im)^\s*secrets\s*:")
        self.assertNotRegex(workflow, r"\$\{\{\s*secrets\.")
        self.assertNotIn("GH_TOKEN", workflow)

        self.assertEqual(workflow.count("\njobs:\n"), 1)
        jobs_block = workflow[workflow.index("jobs:\n") :]
        jobs = re.findall(r"^  ([\w-]+):\s*$", jobs_block, re.MULTILINE)
        self.assertEqual(jobs, ["verify"])
        self.assertIn("runs-on: ubuntu-24.04", jobs_block)
        self.assertIn("cancel-in-progress: true", workflow)
        timeouts = re.findall(
            r"^\s+timeout-minutes:\s*(\d+)\s*$",
            workflow,
            re.MULTILINE,
        )
        self.assertEqual(timeouts, ["5"])

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
        self.assertIn("ref: ${{ github.sha }}", workflow)
        self.assertIn("persist-credentials: false", workflow)
        self.assertIn('python-version: "3.11"', workflow)

        test_command = (
            "run: >-\n"
            "          python -m unittest\n"
            "          tests.test_release\n"
            "          tests.test_release_tooling_workflow"
        )
        install_command = (
            "run: |\n"
            '          release_venv="$RUNNER_TEMP/repo-scout-release-venv"\n'
            '          python -m venv "$release_venv"\n'
            '          "$release_venv/bin/python" -m pip install \\\n'
            "            --disable-pip-version-check \\\n"
            "            --require-hashes \\\n"
            "            --force-reinstall \\\n"
            "            -r .github/release-requirements.txt\n"
            '          "$release_venv/bin/python" -m pip check'
        )
        build_command = (
            "run: |\n"
            '          dist="$RUNNER_TEMP/repo-scout-release-dist"\n'
            '          release_python="$RUNNER_TEMP/repo-scout-release-venv/bin/python"\n'
            '          "$release_python" scripts/build_zipapp.py --dist "$dist"\n'
            '          "$release_python" -m build --no-isolation --sdist --wheel '
            '--outdir "$dist"\n'
            '          version="$(\n'
            "            \"$release_python\" -c 'import tomllib; "
            'print(tomllib.load(open("pyproject.toml", "rb"))'
            '["project"]["version"])\'\n'
            "          )\"\n"
            '          "$release_python" scripts/prepare_release.py '
            '--tag "v${version}" --dist "$dist"'
        )
        self.assertEqual(workflow.count(test_command), 1)
        self.assertEqual(workflow.count(install_command), 1)
        self.assertEqual(workflow.count(build_command), 1)
        self.assertEqual(workflow.count("pip install"), 1)
        self.assertEqual(workflow.count("--force-reinstall"), 1)
        self.assertEqual(workflow.count("pip check"), 1)
        self.assertNotIn("source ", workflow)
        self.assertEqual(
            len(re.findall(r"^\s+run:", workflow, re.MULTILINE)),
            3,
        )
        self.assertLess(
            workflow.index(f"uses: {CHECKOUT_ACTION}"),
            workflow.index(f"uses: {SETUP_PYTHON_ACTION}"),
        )
        self.assertLess(
            workflow.index(f"uses: {SETUP_PYTHON_ACTION}"),
            workflow.index(test_command),
        )
        self.assertLess(
            workflow.index(test_command),
            workflow.index(install_command),
        )
        self.assertLess(
            workflow.index(install_command),
            workflow.index(build_command),
        )

        self.assertNotIn("gh release", workflow)
        self.assertNotIn("attest", workflow)
        self.assertNotIn("upload-artifact", workflow)
        self.assertNotIn("continue-on-error", workflow)
        self.assertNotIn("|| true", workflow)


if __name__ == "__main__":
    unittest.main()
