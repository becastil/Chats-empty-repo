from __future__ import annotations

from contextlib import redirect_stderr, redirect_stdout
import io
import json
import os
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import tomllib
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from repo_scout.policy import evaluate_policy, load_policy, parse_policy
from repo_scout.policy_templates import (
    TEMPLATE_BY_NAME,
    get_template,
    list_templates,
    main,
    recommend_template,
)
from repo_scout.scanner import scan_project


EXPECTED_TEMPLATES = [
    "service-baseline",
    "python-service",
    "node-npm-service",
    "node-service",
    "agent-ready-service",
]


class PolicyTemplateTests(unittest.TestCase):
    def test_catalog_has_stable_text_and_json_output(self) -> None:
        self.assertEqual(list(TEMPLATE_BY_NAME), EXPECTED_TEMPLATES)

        json_stdout = io.StringIO()
        with redirect_stdout(json_stdout):
            json_exit_code = main(["list", "--format", "json"])
        catalog = json.loads(json_stdout.getvalue())

        text_stdout = io.StringIO()
        with redirect_stdout(text_stdout):
            text_exit_code = main(["list"])

        self.assertEqual(json_exit_code, 0)
        self.assertEqual(text_exit_code, 0)
        self.assertEqual(catalog["schema_version"], 1)
        self.assertEqual(
            [template["name"] for template in catalog["templates"]],
            EXPECTED_TEMPLATES,
        )
        for template in catalog["templates"]:
            self.assertIn("required_files", template["rules"])
            self.assertEqual(
                template["rules"]["forbidden_files"], [".env", ".env.local"]
            )
            self.assertEqual(
                template["rules"]["forbidden_file_patterns"],
                ["**/.env", "**/.env.local"],
            )
            self.assertTrue(template["rules"]["require_clean_git"])
        node_service = next(
            template
            for template in catalog["templates"]
            if template["name"] == "node-service"
        )
        self.assertEqual(
            node_service["rules"]["required_file_groups"],
            [["package-lock.json", "pnpm-lock.yaml", "yarn.lock"]],
        )
        self.assertIn("Repo Scout Policy Templates", text_stdout.getvalue())
        self.assertIn(
            "Required alternative: package-lock.json or pnpm-lock.yaml or yarn.lock",
            text_stdout.getvalue(),
        )
        self.assertLess(
            text_stdout.getvalue().index("service-baseline"),
            text_stdout.getvalue().index("agent-ready-service"),
        )

    def test_show_and_init_preserve_exact_template_content(self) -> None:
        for name in EXPECTED_TEMPLATES:
            with self.subTest(template=name), TemporaryDirectory() as tmp:
                content = get_template(name)
                self.assertTrue(content.endswith("\n"))
                self.assertFalse(content.endswith("\n\n"))

                stdout = io.StringIO()
                with redirect_stdout(stdout):
                    show_exit_code = main(["show", name])

                output_path = Path(tmp) / "policy.toml"
                with redirect_stderr(io.StringIO()):
                    init_exit_code = main(
                        ["init", name, "--output", str(output_path)]
                    )

                self.assertEqual(show_exit_code, 0)
                self.assertEqual(init_exit_code, 0)
                self.assertEqual(stdout.getvalue(), content)
                self.assertEqual(output_path.read_text(encoding="utf-8"), content)
                expected_version = 4 if name == "node-service" else 3
                self.assertEqual(
                    load_policy(output_path)["version"], expected_version
                )

    def test_recommends_starters_from_repository_signals(self) -> None:
        cases = (
            (("package.json", "package-lock.json"), "node-npm-service"),
            (
                ("package.json", "package-lock.json", "pnpm-lock.yaml"),
                "node-service",
            ),
            (("package.json", "pnpm-lock.yaml"), "node-service"),
            (("package.json", "yarn.lock"), "node-service"),
            (("package.json",), "node-service"),
            (("pyproject.toml",), "python-service"),
            (("AGENTS.md",), "agent-ready-service"),
            ((), "service-baseline"),
        )

        for files, expected in cases:
            with self.subTest(files=files), TemporaryDirectory() as tmp:
                root = Path(tmp)
                for filename in files:
                    (root / filename).write_text("{}\n", encoding="utf-8")

                recommendation = recommend_template(root)

                self.assertEqual(
                    recommendation["recommendation"]["name"], expected
                )
                self.assertEqual(
                    recommendation["init_command"],
                    f"repo-scout-policy init {expected}",
                )
                self.assertFalse(recommendation["review_required"])

    def test_recommendation_marks_polyglot_repositories_for_review(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "package.json").write_text("{}\n", encoding="utf-8")
            (root / "pnpm-lock.yaml").write_text("lockfileVersion: 9\n")
            (root / "pyproject.toml").write_text("[project]\n", encoding="utf-8")

            recommendation = recommend_template(root)

            self.assertEqual(
                recommendation["recommendation"]["name"], "node-service"
            )
            self.assertTrue(recommendation["review_required"])
            self.assertIn("combine", recommendation["review_note"])

    def test_recommend_command_has_stable_text_and_json_output(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "package.json").write_text("{}\n", encoding="utf-8")
            (root / "yarn.lock").write_text("# yarn\n", encoding="utf-8")

            text_stdout = io.StringIO()
            with redirect_stdout(text_stdout):
                text_exit_code = main(["recommend", str(root)])
            json_stdout = io.StringIO()
            with redirect_stdout(json_stdout):
                json_exit_code = main(
                    ["recommend", str(root), "--format", "json"]
                )

            self.assertEqual(text_exit_code, 0)
            self.assertEqual(json_exit_code, 0)
            self.assertIn(
                "Starter: node-service - Node service", text_stdout.getvalue()
            )
            self.assertIn("Review required: no", text_stdout.getvalue())
            result = json.loads(json_stdout.getvalue())
            self.assertEqual(result["schema_version"], 1)
            self.assertEqual(result["signals"], ["package.json", "yarn.lock"])
            self.assertEqual(result["recommendation"]["name"], "node-service")

    def test_recommend_command_rejects_a_non_directory_path(self) -> None:
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "package.json"
            path.write_text("{}\n", encoding="utf-8")
            stderr = io.StringIO()
            with redirect_stderr(stderr):
                exit_code = main(["recommend", str(path)])

            self.assertEqual(exit_code, 2)
            self.assertIn("is not a directory", stderr.getvalue())

    def test_init_defaults_to_current_directory_and_protects_overwrites(self) -> None:
        with TemporaryDirectory() as tmp:
            original_directory = Path.cwd()
            os.chdir(tmp)
            try:
                with redirect_stderr(io.StringIO()):
                    first_exit_code = main(["init", "python-service"])

                target = Path("repo-scout-policy.toml")
                original_content = target.read_text(encoding="utf-8")
                target.write_text("keep me\n", encoding="utf-8")

                stderr = io.StringIO()
                with redirect_stderr(stderr):
                    protected_exit_code = main(["init", "python-service"])

                self.assertEqual(first_exit_code, 0)
                self.assertEqual(protected_exit_code, 4)
                self.assertEqual(target.read_text(encoding="utf-8"), "keep me\n")
                self.assertIn("--force", stderr.getvalue())

                with redirect_stderr(io.StringIO()):
                    force_exit_code = main(
                        ["init", "python-service", "--force"]
                    )

                self.assertEqual(force_exit_code, 0)
                self.assertEqual(
                    target.read_text(encoding="utf-8"), original_content
                )
            finally:
                os.chdir(original_directory)

    def test_init_reports_unsupported_and_unwritable_destinations(self) -> None:
        stderr = io.StringIO()
        with redirect_stderr(stderr):
            stdout_exit_code = main(
                ["init", "service-baseline", "--output", "-"]
            )

        self.assertEqual(stdout_exit_code, 2)
        self.assertIn("use show for stdout", stderr.getvalue())

        with TemporaryDirectory() as tmp:
            missing_parent = Path(tmp) / "missing" / "policy.toml"
            directory_target = Path(tmp) / "target"
            directory_target.mkdir()

            with redirect_stderr(io.StringIO()):
                missing_parent_exit_code = main(
                    [
                        "init",
                        "service-baseline",
                        "--output",
                        str(missing_parent),
                    ]
                )
                directory_exit_code = main(
                    [
                        "init",
                        "service-baseline",
                        "--output",
                        str(directory_target),
                        "--force",
                    ]
                )

            self.assertEqual(missing_parent_exit_code, 4)
            self.assertEqual(directory_exit_code, 4)
            self.assertTrue(directory_target.is_dir())

    def test_every_template_passes_then_reports_a_missing_required_file(self) -> None:
        for name in EXPECTED_TEMPLATES:
            with self.subTest(template=name), TemporaryDirectory() as tmp:
                root = Path(tmp)
                policy_path = root / "repo-scout-policy.toml"
                policy_path.write_text(get_template(name), encoding="utf-8")
                policy = load_policy(policy_path)
                required_files = policy["repository"]["required_files"]
                for required_file in required_files:
                    path = root / required_file
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_text(f"# {required_file}\n", encoding="utf-8")
                for required_group in policy["repository"].get(
                    "required_file_groups", []
                ):
                    (root / required_group[0]).write_text(
                        "# generated lockfile\n", encoding="utf-8"
                    )
                self._commit_repository(root)

                passing_result = evaluate_policy(scan_project(root), policy)
                self.assertEqual(passing_result["status"], "pass")

                missing_path = root / required_files[0]
                missing_path.unlink()
                self._commit_all(root, "Remove required file")
                failing_result = evaluate_policy(scan_project(root), policy)

                self.assertEqual(failing_result["status"], "fail")
                self.assertEqual(
                    failing_result["violations"][0]["path"], required_files[0]
                )

    def test_node_service_accepts_each_supported_lockfile(self) -> None:
        policy = parse_policy(
            get_template("node-service"), source="node-service template"
        )
        alternatives = policy["repository"]["required_file_groups"][0]

        for lockfile in alternatives:
            with self.subTest(lockfile=lockfile), TemporaryDirectory() as tmp:
                root = Path(tmp)
                (root / "README.md").write_text("# Service\n", encoding="utf-8")
                (root / "package.json").write_text("{}\n", encoding="utf-8")
                (root / lockfile).write_text("# lockfile\n", encoding="utf-8")
                self._commit_repository(root)

                self.assertEqual(
                    evaluate_policy(scan_project(root), policy)["status"], "pass"
                )

                (root / lockfile).unlink()
                self._commit_all(root, "Remove lockfile")
                failing = evaluate_policy(scan_project(root), policy)
                self.assertEqual(failing["status"], "fail")
                self.assertEqual(
                    failing["violations"][0]["rule"],
                    "repository.required_file_groups",
                )

    def test_missing_packaged_resource_is_a_controlled_error(self) -> None:
        with TemporaryDirectory() as tmp:
            stderr = io.StringIO()
            with patch(
                "repo_scout.policy_templates.resources.files",
                return_value=Path(tmp),
            ), redirect_stderr(stderr):
                exit_code = main(["list"])

        self.assertEqual(exit_code, 2)
        self.assertIn("could not read packaged policy template", stderr.getvalue())

    def test_parse_policy_applies_strict_validation_to_memory_content(self) -> None:
        with self.assertRaisesRegex(ValueError, "unknown repository key"):
            parse_policy("version = 1\n[repository]\nmax_filez = 10\n")

    def test_distribution_metadata_includes_command_and_toml_resources(self) -> None:
        with (Path(__file__).resolve().parents[1] / "pyproject.toml").open(
            "rb"
        ) as project_file:
            project = tomllib.load(project_file)

        self.assertEqual(
            project["project"]["scripts"]["repo-scout-policy"],
            "repo_scout.policy_templates:main",
        )
        self.assertEqual(
            project["tool"]["setuptools"]["package-data"]["repo_scout"],
            ["templates/policies/*.toml"],
        )

    @staticmethod
    def _commit_repository(root: Path) -> None:
        commands = [
            ("init", "--quiet"),
            ("config", "user.name", "Repo Scout Tests"),
            ("config", "user.email", "tests@example.invalid"),
        ]
        for command in commands:
            subprocess.run(
                ["git", "-C", str(root), *command],
                check=True,
                capture_output=True,
                text=True,
            )
        PolicyTemplateTests._commit_all(root, "Initial commit")

    @staticmethod
    def _commit_all(root: Path, message: str) -> None:
        subprocess.run(
            ["git", "-C", str(root), "add", "--all"],
            check=True,
            capture_output=True,
            text=True,
        )
        subprocess.run(
            ["git", "-C", str(root), "commit", "--quiet", "-m", message],
            check=True,
            capture_output=True,
            text=True,
        )


if __name__ == "__main__":
    unittest.main()
