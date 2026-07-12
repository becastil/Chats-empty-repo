from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import tomllib
from typing import Mapping, Sequence


LOCKFILES = ("package-lock.json", "pnpm-lock.yaml", "yarn.lock")


class SmokeTestError(RuntimeError):
    """Raised when installed policy activation does not satisfy its contract."""


def verify_policy_activation(
    python: str | Path,
    *,
    environment: Mapping[str, str] | None = None,
) -> tuple[str, ...]:
    python_command = str(Path(python))
    checked: list[str] = []

    for lockfile in LOCKFILES:
        with TemporaryDirectory() as tmp:
            root = Path(tmp) / "service"
            root.mkdir()
            policy_path = root / "repo-scout-policy.toml"
            (root / "README.md").write_text("# Node service\n", encoding="utf-8")
            (root / "package.json").write_text("{}\n", encoding="utf-8")
            (root / lockfile).write_text("# lockfile\n", encoding="utf-8")

            recommendation = _recommend(
                python_command, root, environment=environment
            )
            expected_starter = (
                "node-npm-service"
                if lockfile == "package-lock.json"
                else "node-service"
            )
            actual_starter = recommendation.get("recommendation", {}).get("name")
            if actual_starter != expected_starter:
                raise SmokeTestError(
                    f"{lockfile} recommended {actual_starter}; "
                    f"expected {expected_starter}"
                )
            recommended_policy = root / "recommended-policy.toml"
            bootstrap = _run(
                [
                    python_command,
                    "-m",
                    "repo_scout.policy_templates",
                    "bootstrap",
                    str(root),
                    "--output",
                    recommended_policy.name,
                    "--format",
                    "json",
                ],
                cwd=root,
                environment=environment,
            )
            if not recommended_policy.is_file():
                raise SmokeTestError(f"{lockfile} bootstrap did not write policy")
            _assert_bootstrap_receipt(
                bootstrap, recommended_policy, expected_starter
            )

            _run(
                [
                    python_command,
                    "-m",
                    "repo_scout.policy_templates",
                    "init",
                    "node-service",
                    "--output",
                    str(policy_path),
                ],
                cwd=root,
                environment=environment,
            )
            with policy_path.open("rb") as policy_file:
                policy = tomllib.load(policy_file)
            if policy.get("version") != 4:
                raise SmokeTestError("node-service did not initialize policy version 4")
            groups = policy.get("repository", {}).get("required_file_groups")
            if groups != [list(LOCKFILES)]:
                raise SmokeTestError(
                    "node-service lockfile alternatives do not match the release contract"
                )

            _initialize_repository(root)
            passing = _scan(
                python_command, root, policy_path, environment=environment
            )
            if passing.get("policy", {}).get("status") != "pass":
                raise SmokeTestError(f"node-service rejected {lockfile}")

            (root / lockfile).unlink()
            _commit_all(root, "Remove lockfile")
            failing = _scan(
                python_command,
                root,
                policy_path,
                environment=environment,
                expected_exit_code=6,
            )
            violations = failing.get("policy", {}).get("violations", [])
            if not violations or violations[0].get("rule") != (
                "repository.required_file_groups"
            ):
                raise SmokeTestError(
                    f"node-service did not reject missing {lockfile} alternatives"
                )
            if violations[0].get("paths") != list(LOCKFILES):
                raise SmokeTestError("missing-lockfile evidence changed alternatives")
            checked.append(lockfile)

    recommendation_cases = (
        (
            "python-service",
            {"pyproject.toml": "[project]\n"},
            "python-service",
            False,
        ),
        (
            "agent-ready-service",
            {"AGENTS.md": "# Agent instructions\n"},
            "agent-ready-service",
            False,
        ),
        ("service-baseline", {}, "service-baseline", False),
        (
            "polyglot-review",
            {
                "package.json": "{}\n",
                "pnpm-lock.yaml": "lockfileVersion: 9\n",
                "pyproject.toml": "[project]\n",
            },
            "node-service",
            True,
        ),
    )
    for label, files, expected_starter, expected_review in recommendation_cases:
        with TemporaryDirectory() as tmp:
            root = Path(tmp) / "service"
            root.mkdir()
            for filename, content in files.items():
                (root / filename).write_text(content, encoding="utf-8")

            recommendation = _recommend(
                python_command, root, environment=environment
            )
            actual_starter = recommendation.get("recommendation", {}).get("name")
            if actual_starter != expected_starter:
                raise SmokeTestError(
                    f"{label} recommended {actual_starter}; "
                    f"expected {expected_starter}"
                )
            if recommendation.get("review_required") is not expected_review:
                raise SmokeTestError(
                    f"{label} review flag did not match {expected_review}"
                )
            if expected_review and not recommendation.get("review_note"):
                raise SmokeTestError(f"{label} omitted its required review note")
            bootstrap_policy = root / "repo-scout-policy.toml"
            bootstrap = _run(
                [
                    python_command,
                    "-m",
                    "repo_scout.policy_templates",
                    "bootstrap",
                    str(root),
                    "--format",
                    "json",
                ],
                cwd=root,
                environment=environment,
                expected_exit_code=2 if expected_review else 0,
            )
            if expected_review:
                if bootstrap_policy.exists():
                    raise SmokeTestError(f"{label} bootstrap wrote unsafe policy")
                if "requires policy review" not in bootstrap.stderr:
                    raise SmokeTestError(f"{label} bootstrap omitted review reason")
            elif not bootstrap_policy.is_file():
                raise SmokeTestError(f"{label} bootstrap did not write policy")
            else:
                _assert_bootstrap_receipt(
                    bootstrap, bootstrap_policy, expected_starter
                )
            checked.append(label)

    return tuple(checked)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Smoke test installed Repo Scout policy activation."
    )
    parser.add_argument(
        "--python",
        default=sys.executable,
        help="Python interpreter from the Repo Scout installation to test.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        checked = verify_policy_activation(args.python, environment=os.environ)
    except SmokeTestError as exc:
        print(f"policy activation smoke test: {exc}", file=sys.stderr)
        return 1
    print(f"policy activation smoke test: passed {', '.join(checked)}")
    return 0


def _recommend(
    python: str,
    root: Path,
    *,
    environment: Mapping[str, str] | None,
) -> dict[str, object]:
    completed = _run(
        [
            python,
            "-m",
            "repo_scout.policy_templates",
            "recommend",
            str(root),
            "--format",
            "json",
        ],
        cwd=root,
        environment=environment,
    )
    try:
        result = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise SmokeTestError(
            "policy recommendation did not emit valid JSON"
        ) from exc
    if not isinstance(result, dict):
        raise SmokeTestError("policy recommendation JSON must be an object")
    return result


def _assert_bootstrap_receipt(
    completed: subprocess.CompletedProcess[str],
    policy_path: Path,
    expected_starter: str,
) -> None:
    try:
        receipt = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise SmokeTestError("policy bootstrap did not emit valid JSON") from exc
    if receipt.get("schema_version") != 1:
        raise SmokeTestError("policy bootstrap receipt schema changed")
    if receipt.get("status") != "created":
        raise SmokeTestError("policy bootstrap did not report a created policy")
    if receipt.get("output") != str(policy_path.resolve()):
        raise SmokeTestError("policy bootstrap receipt output path changed")
    if receipt.get("starter", {}).get("name") != expected_starter:
        raise SmokeTestError("policy bootstrap receipt starter changed")
    policy = receipt.get("policy", {})
    fingerprint = policy.get("fingerprint")
    if not isinstance(policy.get("version"), int):
        raise SmokeTestError("policy bootstrap receipt omitted policy version")
    if not isinstance(fingerprint, str) or not fingerprint.startswith("sha256:"):
        raise SmokeTestError("policy bootstrap receipt omitted policy fingerprint")


def _scan(
    python: str,
    root: Path,
    policy_path: Path,
    *,
    environment: Mapping[str, str] | None,
    expected_exit_code: int = 0,
) -> dict[str, object]:
    completed = _run(
        [
            python,
            "-m",
            "repo_scout",
            "--format",
            "json",
            "--policy",
            str(policy_path),
            str(root),
        ],
        cwd=root,
        environment=environment,
        expected_exit_code=expected_exit_code,
    )
    try:
        result = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise SmokeTestError("Repo Scout did not emit valid JSON") from exc
    if not isinstance(result, dict):
        raise SmokeTestError("Repo Scout JSON output must be an object")
    return result


def _initialize_repository(root: Path) -> None:
    _run(["git", "init", "--quiet"], cwd=root)
    _run(["git", "config", "user.name", "Repo Scout Release"], cwd=root)
    _run(
        ["git", "config", "user.email", "release@example.invalid"], cwd=root
    )
    _commit_all(root, "Initialize Node service")


def _commit_all(root: Path, message: str) -> None:
    _run(["git", "add", "--all"], cwd=root)
    _run(["git", "commit", "--quiet", "-m", message], cwd=root)


def _run(
    command: list[str],
    *,
    cwd: Path,
    environment: Mapping[str, str] | None = None,
    expected_exit_code: int = 0,
) -> subprocess.CompletedProcess[str]:
    try:
        completed = subprocess.run(
            command,
            cwd=cwd,
            env=dict(environment) if environment is not None else None,
            capture_output=True,
            text=True,
        )
    except OSError as exc:
        raise SmokeTestError(f"could not run {command[0]}: {exc}") from exc
    if completed.returncode != expected_exit_code:
        detail = completed.stderr.strip() or completed.stdout.strip() or "no output"
        raise SmokeTestError(
            f"{' '.join(command)} exited {completed.returncode}; "
            f"expected {expected_exit_code}: {detail}"
        )
    return completed


if __name__ == "__main__":
    raise SystemExit(main())
