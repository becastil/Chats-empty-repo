from __future__ import annotations

from pathlib import Path
import re
import tomllib
import unittest


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "release-tooling.yml"
RELEASE_WORKFLOW = ROOT / ".github" / "workflows" / "release.yml"

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
    "scripts/compare_wheel_contents.py",
    "scripts/prepare_release.py",
    "scripts/smoke_test_outreach_lifecycle.py",
    "scripts/smoke_test_pilot_funnel.py",
    "scripts/smoke_test_policy_activation.py",
    "scripts/smoke_test_rollout_summary.py",
    "src/**",
    "tests/**",
)
ACCEPTANCE_SCRIPTS = (
    "smoke_test_policy_activation.py",
    "smoke_test_outreach_lifecycle.py",
    "smoke_test_pilot_funnel.py",
    "smoke_test_rollout_summary.py",
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
        smoke_marker = "      - name: Smoke test candidate artifacts\n"
        self.assertIn(smoke_marker, workflow)
        smoke_step = workflow[workflow.index(smoke_marker) :]
        self.assertIn(
            'smoke_venv="$RUNNER_TEMP/repo-scout-release-smoke"',
            smoke_step,
        )
        self.assertIn('python -m venv "$smoke_venv"', smoke_step)
        self.assertIn(
            '"$smoke_venv/bin/python" -m pip install \\\n',
            smoke_step,
        )
        self.assertIn("--disable-pip-version-check", smoke_step)
        self.assertIn("--no-index", smoke_step)
        self.assertIn("--no-deps", smoke_step)
        self.assertNotIn("--index-url", smoke_step)
        self.assertNotIn("--extra-index-url", smoke_step)
        self.assertNotIn("--find-links", smoke_step)
        self.assertNotIn("*.whl", smoke_step)
        self.assertIn(
            '"$dist/repo_scout-${version}-py3-none-any.whl"',
            smoke_step,
        )
        self.assertIn(
            '"$smoke_venv/bin/$command" --version',
            smoke_step,
        )
        self.assertIn('test "$actual" = "$command $version"', smoke_step)
        _, loop_heading, command_tail = smoke_step.partition(
            "          for command in \\\n"
        )
        command_block, loop_end, _ = command_tail.partition("; do")
        self.assertTrue(loop_heading)
        self.assertTrue(loop_end)
        smoke_commands = re.findall(
            r"^            (repo-scout(?:-[a-z]+)*)",
            command_block,
            re.MULTILINE,
        )
        with (ROOT / "pyproject.toml").open("rb") as project_file:
            packaged_commands = set(
                tomllib.load(project_file)["project"]["scripts"]
            )
        self.assertEqual(len(smoke_commands), len(set(smoke_commands)))
        self.assertEqual(set(smoke_commands), packaged_commands)
        self.assertIn(
            'test "$(python "$dist/repo-scout-${version}.pyz" --version)" '
            '= "repo-scout $version"',
            smoke_step,
        )
        self.assertIn(
            'python "$dist/repo-scout-${version}.pyz" --help',
            smoke_step,
        )
        self.assertIn(
            'python "$dist/repo-scout-${version}.pyz" --format json . > '
            '"$RUNNER_TEMP/repo-scout-candidate-snapshot.json"',
            smoke_step,
        )

        self.assertEqual(workflow.count("pip install"), 2)
        self.assertEqual(workflow.count("--force-reinstall"), 1)
        self.assertEqual(workflow.count("pip check"), 1)
        self.assertNotRegex(workflow, r"(?m)^\s+source\s+")
        self.assertEqual(
            len(re.findall(r"^\s+run:", workflow, re.MULTILINE)),
            5,
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
        self.assertLess(
            workflow.index(build_command),
            workflow.index(smoke_marker),
        )

        self.assertNotIn("gh release", workflow)
        self.assertNotIn("attest", workflow)
        self.assertNotIn("upload-artifact", workflow)
        self.assertNotIn("continue-on-error", workflow)
        self.assertNotIn("|| true", workflow)

    def test_candidate_smoke_matches_publication_acceptance_scripts(self) -> None:
        candidate_workflow = WORKFLOW.read_text(encoding="utf-8")
        release_workflow = RELEASE_WORKFLOW.read_text(encoding="utf-8")
        script_pattern = r"python scripts/(smoke_test_[a-z_]+\.py) \\"
        smoke_marker = "      - name: Smoke test candidate artifacts\n"
        smoke_step = candidate_workflow[
            candidate_workflow.index(smoke_marker) :
        ]

        publication_scripts = re.findall(script_pattern, release_workflow)
        candidate_scripts = re.findall(script_pattern, smoke_step)
        self.assertEqual(publication_scripts, list(ACCEPTANCE_SCRIPTS))
        self.assertEqual(candidate_scripts, publication_scripts)

        install_marker = (
            '"$smoke_venv/bin/python" -m pip install \\\n'
        )
        portable_marker = (
            'test "$(python "$dist/repo-scout-${version}.pyz" --version)"'
        )
        self.assertIn(install_marker, smoke_step)
        self.assertIn(portable_marker, smoke_step)
        self.assertLess(
            smoke_step.index(install_marker),
            smoke_step.index(f"python scripts/{ACCEPTANCE_SCRIPTS[0]}"),
        )
        self.assertLess(
            smoke_step.index(f"python scripts/{ACCEPTANCE_SCRIPTS[-1]}"),
            smoke_step.index(portable_marker),
        )
        self.assertEqual(
            smoke_step.count('--python "$smoke_venv/bin/python"'),
            len(ACCEPTANCE_SCRIPTS),
        )
        self.assertEqual(
            smoke_step.count('--command-directory "$smoke_venv/bin"'),
            len(ACCEPTANCE_SCRIPTS),
        )

    def test_candidate_rebuilds_exact_source_distribution_offline(self) -> None:
        workflow = WORKFLOW.read_text(encoding="utf-8")
        build_marker = "      - name: Build candidate artifacts\n"
        source_marker = "      - name: Verify source distribution rebuild\n"
        smoke_marker = "      - name: Smoke test candidate artifacts\n"
        for marker in (build_marker, source_marker, smoke_marker):
            self.assertIn(marker, workflow)
        self.assertLess(workflow.index(build_marker), workflow.index(source_marker))
        self.assertLess(workflow.index(source_marker), workflow.index(smoke_marker))

        source_step = workflow[
            workflow.index(source_marker) : workflow.index(smoke_marker)
        ]
        self.assertIn("        run: |\n", source_step)
        self.assertIn(
            'release_python="$RUNNER_TEMP/repo-scout-release-venv/bin/python"',
            source_step,
        )
        self.assertIn(
            'rebuilt_wheels="$RUNNER_TEMP/repo-scout-sdist-wheels"',
            source_step,
        )
        self.assertIn('"$release_python" -m pip wheel \\\n', source_step)
        self.assertIn("--disable-pip-version-check", source_step)
        self.assertIn("--no-cache-dir", source_step)
        self.assertIn("--no-index", source_step)
        self.assertIn("--no-deps", source_step)
        self.assertIn("--no-build-isolation", source_step)
        self.assertIn('--wheel-dir "$rebuilt_wheels"', source_step)
        self.assertIn(
            '"$dist/repo_scout-${version}.tar.gz"',
            source_step,
        )
        self.assertIn(
            '"$release_python" scripts/compare_wheel_contents.py \\\n',
            source_step,
        )
        self.assertIn(
            '"$dist/repo_scout-${version}-py3-none-any.whl" \\\n',
            source_step,
        )
        self.assertIn(
            '"$rebuilt_wheels/repo_scout-${version}-py3-none-any.whl"',
            source_step,
        )
        self.assertNotIn("*.tar.gz", source_step)
        self.assertNotIn("*.whl", source_step)
        self.assertNotIn("--index-url", source_step)
        self.assertNotIn("--extra-index-url", source_step)
        self.assertNotIn("--find-links", source_step)
        self.assertNotIn("|| true", source_step)


if __name__ == "__main__":
    unittest.main()
