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
MAX_ACTIVATION_INPUT_BYTES = 128 * 1024


class SmokeTestError(RuntimeError):
    """Raised when installed policy activation does not satisfy its contract."""


def verify_policy_activation(
    python: str | Path,
    *,
    command_directory: str | Path | None = None,
    environment: Mapping[str, str] | None = None,
) -> tuple[str, ...]:
    python_command = str(Path(python))
    policy_command, scan_command = _installed_commands(
        python_command,
        command_directory=command_directory,
    )
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
                policy_command, root, environment=environment
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
                    *policy_command,
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
            _verify_receipt(
                policy_command,
                root,
                bootstrap,
                environment=environment,
            )

            _run(
                [
                    *policy_command,
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
                scan_command, root, policy_path, environment=environment
            )
            if passing.get("policy", {}).get("status") != "pass":
                raise SmokeTestError(f"node-service rejected {lockfile}")

            (root / lockfile).unlink()
            _commit_all(root, "Remove lockfile")
            failing = _scan(
                scan_command,
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
                policy_command, root, environment=environment
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
                    *policy_command,
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
                _verify_receipt(
                    policy_command,
                    root,
                    bootstrap,
                    environment=environment,
                )
            checked.append(label)

    with TemporaryDirectory() as tmp:
        root = Path(tmp) / "service"
        root.mkdir()
        (root / "pyproject.toml").write_text("[project]\n", encoding="utf-8")
        config = root / "config"
        config.mkdir()
        existing_policy = root / "existing-policy.toml"
        existing_policy.write_text("keep me\n", encoding="utf-8")
        bootstrap_policy = config / "team-policy.toml"
        bootstrap_policy.symlink_to(existing_policy)

        symlink_bootstrap = _run(
            [
                *policy_command,
                "bootstrap",
                str(root),
                "--output",
                "config/team-policy.toml",
                "--force",
                "--format",
                "json",
            ],
            cwd=root,
            environment=environment,
            expected_exit_code=4,
        )
        if symlink_bootstrap.stdout:
            raise SmokeTestError("symlink bootstrap output emitted a receipt")
        if "output must not be a symlink" not in symlink_bootstrap.stderr:
            raise SmokeTestError("symlink bootstrap output was not rejected")
        if not bootstrap_policy.is_symlink():
            raise SmokeTestError("symlink bootstrap output replaced the link")
        if existing_policy.read_text(encoding="utf-8") != "keep me\n":
            raise SmokeTestError("symlink bootstrap output changed its target")
        checked.append("symlink-bootstrap-output-rejected")

    with TemporaryDirectory() as tmp:
        root = Path(tmp) / "service"
        root.mkdir()
        (root / "README.md").write_text("# Service\n", encoding="utf-8")
        stored_policy = root / "stored-policy.toml"
        stored_policy.write_text(
            "version = 1\n[repository]\nrequired_files = [\"README.md\"]\n",
            encoding="utf-8",
        )
        policy_path = root / "team-policy.toml"
        policy_path.symlink_to(stored_policy)

        symlink_policy_scan = _run(
            [
                *scan_command,
                "--format",
                "json",
                "--policy",
                str(policy_path),
                str(root),
            ],
            cwd=root,
            environment=environment,
            expected_exit_code=2,
        )
        if symlink_policy_scan.stdout:
            raise SmokeTestError("symlink CLI policy emitted a scan report")
        if "policy path must not be a symlink" not in symlink_policy_scan.stderr:
            raise SmokeTestError("symlink CLI policy was not rejected")
        resolved_stored_policy = (
            stored_policy.parent.resolve() / stored_policy.name
        )
        if str(resolved_stored_policy) in symlink_policy_scan.stderr:
            raise SmokeTestError("symlink CLI policy disclosed its target")
        if not policy_path.is_symlink() or not stored_policy.is_file():
            raise SmokeTestError("symlink CLI policy scan changed policy evidence")
        checked.append("symlink-cli-policy-rejected")

        policy_path.unlink()
        policy_path.mkdir()
        non_regular_policy_scan = _run(
            [
                *scan_command,
                "--format",
                "json",
                "--policy",
                str(policy_path),
                str(root),
            ],
            cwd=root,
            environment=environment,
            expected_exit_code=2,
        )
        if non_regular_policy_scan.stdout:
            raise SmokeTestError("non-regular CLI policy emitted a scan report")
        if (
            "policy path must be a regular file"
            not in non_regular_policy_scan.stderr
        ):
            raise SmokeTestError("non-regular CLI policy was not rejected")
        if not policy_path.is_dir() or not stored_policy.is_file():
            raise SmokeTestError(
                "non-regular CLI policy scan changed policy evidence"
            )
        checked.append("nonregular-cli-policy-rejected")

        policy_path.rmdir()
        with policy_path.open("wb") as policy_file:
            policy_file.truncate(MAX_ACTIVATION_INPUT_BYTES + 1)
        oversized_policy_scan = _run(
            [
                *scan_command,
                "--format",
                "json",
                "--policy",
                str(policy_path),
                str(root),
            ],
            cwd=root,
            environment=environment,
            expected_exit_code=2,
        )
        if oversized_policy_scan.stdout:
            raise SmokeTestError("oversized CLI policy emitted a scan report")
        if (
            f"policy file exceeds {MAX_ACTIVATION_INPUT_BYTES} bytes"
            not in oversized_policy_scan.stderr
        ):
            raise SmokeTestError("oversized CLI policy was not rejected")
        if policy_path.stat().st_size != MAX_ACTIVATION_INPUT_BYTES + 1:
            raise SmokeTestError("oversized CLI policy evidence changed")
        checked.append("oversized-cli-policy-rejected")

    with TemporaryDirectory() as tmp:
        root = Path(tmp) / "service"
        root.mkdir()
        (root / "pyproject.toml").write_text("[project]\n", encoding="utf-8")
        bootstrap = _run(
            [
                *policy_command,
                "bootstrap",
                str(root),
                "--format",
                "json",
            ],
            cwd=root,
            environment=environment,
        )
        receipt_path = root / "bootstrap-receipt.json"
        receipt_path.write_text(bootstrap.stdout, encoding="utf-8")
        policy_path = root / "repo-scout-policy.toml"
        invalid_receipt = json.loads(bootstrap.stdout)
        invalid_receipt["output"] = policy_path.name
        invalid_receipt_path = root / "relative-output-receipt.json"
        invalid_receipt_path.write_text(
            json.dumps(invalid_receipt),
            encoding="utf-8",
        )
        invalid_verification = _run(
            [
                *policy_command,
                "verify-receipt",
                str(invalid_receipt_path),
                "--policy",
                str(policy_path),
                "--format",
                "json",
            ],
            cwd=root,
            environment=environment,
            expected_exit_code=2,
        )
        if invalid_verification.stdout:
            raise SmokeTestError("relative receipt output emitted verification")
        if "output must be an absolute path" not in invalid_verification.stderr:
            raise SmokeTestError("relative receipt output was not rejected")
        checked.append("relative-receipt-output-rejected")

        stored_receipt = root / "stored-bootstrap-receipt.json"
        receipt_path.replace(stored_receipt)
        receipt_path.symlink_to(stored_receipt)
        symlink_receipt_verification = _run(
            [
                *policy_command,
                "verify-receipt",
                str(receipt_path),
                "--format",
                "json",
            ],
            cwd=root,
            environment=environment,
            expected_exit_code=2,
        )
        if symlink_receipt_verification.stdout:
            raise SmokeTestError(
                "symlink bootstrap receipt emitted verification"
            )
        if (
            "bootstrap receipt path must not be a symlink"
            not in symlink_receipt_verification.stderr
        ):
            raise SmokeTestError("symlink bootstrap receipt was not rejected")
        if str(stored_receipt) in symlink_receipt_verification.stderr:
            raise SmokeTestError("symlink bootstrap receipt disclosed its target")
        if not receipt_path.is_symlink() or not stored_receipt.is_file():
            raise SmokeTestError(
                "symlink bootstrap receipt verification changed evidence"
            )
        checked.append("symlink-bootstrap-receipt-rejected")

        receipt_path.unlink()
        stored_receipt.replace(receipt_path)
        receipt_path.replace(stored_receipt)
        receipt_path.mkdir()
        non_regular_receipt_verification = _run(
            [
                *policy_command,
                "verify-receipt",
                str(receipt_path),
                "--format",
                "json",
            ],
            cwd=root,
            environment=environment,
            expected_exit_code=2,
        )
        if non_regular_receipt_verification.stdout:
            raise SmokeTestError(
                "non-regular bootstrap receipt emitted verification"
            )
        if (
            "bootstrap receipt path must be a regular file"
            not in non_regular_receipt_verification.stderr
        ):
            raise SmokeTestError(
                "non-regular bootstrap receipt was not rejected"
            )
        if not receipt_path.is_dir() or not stored_receipt.is_file():
            raise SmokeTestError(
                "non-regular bootstrap receipt verification changed evidence"
            )
        checked.append("nonregular-bootstrap-receipt-rejected")

        receipt_path.rmdir()
        with receipt_path.open("wb") as receipt_file:
            receipt_file.truncate(MAX_ACTIVATION_INPUT_BYTES + 1)
        oversized_receipt_verification = _run(
            [
                *policy_command,
                "verify-receipt",
                str(receipt_path),
                "--format",
                "json",
            ],
            cwd=root,
            environment=environment,
            expected_exit_code=2,
        )
        if oversized_receipt_verification.stdout:
            raise SmokeTestError(
                "oversized bootstrap receipt emitted verification"
            )
        if (
            f"bootstrap receipt exceeds {MAX_ACTIVATION_INPUT_BYTES} bytes"
            not in oversized_receipt_verification.stderr
        ):
            raise SmokeTestError("oversized bootstrap receipt was not rejected")
        if receipt_path.stat().st_size != MAX_ACTIVATION_INPUT_BYTES + 1:
            raise SmokeTestError("oversized bootstrap receipt evidence changed")
        checked.append("oversized-bootstrap-receipt-rejected")

        receipt_path.unlink()
        stored_receipt.replace(receipt_path)
        moved_policy = root / "moved-policy.toml"
        policy_path.replace(moved_policy)
        policy_path.symlink_to(moved_policy)

        verification = _run(
            [
                *policy_command,
                "verify-receipt",
                str(receipt_path),
                "--format",
                "json",
            ],
            cwd=root,
            environment=environment,
            expected_exit_code=6,
        )
        try:
            result = json.loads(verification.stdout)
        except json.JSONDecodeError as exc:
            raise SmokeTestError(
                "symlink policy verification did not emit valid JSON"
            ) from exc
        requested_policy = policy_path.parent.resolve() / policy_path.name
        resolved_target = moved_policy.parent.resolve() / moved_policy.name
        if result.get("status") != "fail" or result.get("actual") is not None:
            raise SmokeTestError("symlink policy verification did not fail closed")
        if result.get("policy") != str(requested_policy):
            raise SmokeTestError("symlink policy verification changed its leaf")
        if "policy path must not be a symlink" not in result.get("message", ""):
            raise SmokeTestError("symlink policy verification omitted its reason")
        if str(resolved_target) in verification.stdout:
            raise SmokeTestError("symlink policy verification disclosed its target")
        if not policy_path.is_symlink() or not moved_policy.is_file():
            raise SmokeTestError("symlink policy verification changed policy evidence")
        checked.append("symlink-receipt-policy-rejected")

        policy_path.unlink()
        policy_path.mkdir()
        non_regular_verification = _run(
            [
                *policy_command,
                "verify-receipt",
                str(receipt_path),
                "--format",
                "json",
            ],
            cwd=root,
            environment=environment,
            expected_exit_code=6,
        )
        try:
            non_regular_result = json.loads(non_regular_verification.stdout)
        except json.JSONDecodeError as exc:
            raise SmokeTestError(
                "non-regular policy verification did not emit valid JSON"
            ) from exc
        if (
            non_regular_result.get("status") != "fail"
            or non_regular_result.get("actual") is not None
        ):
            raise SmokeTestError(
                "non-regular policy verification did not fail closed"
            )
        if non_regular_result.get("policy") != str(requested_policy):
            raise SmokeTestError(
                "non-regular policy verification changed its leaf"
            )
        if "policy path must be a regular file" not in non_regular_result.get(
            "message", ""
        ):
            raise SmokeTestError(
                "non-regular policy verification omitted its reason"
            )
        if not policy_path.is_dir() or not moved_policy.is_file():
            raise SmokeTestError(
                "non-regular policy verification changed policy evidence"
            )
        checked.append("nonregular-receipt-policy-rejected")

    return tuple(checked)


def _installed_commands(
    python: str,
    *,
    command_directory: str | Path | None,
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    if command_directory is None:
        return (
            (python, "-m", "repo_scout.policy_templates"),
            (python, "-m", "repo_scout"),
        )

    directory = Path(command_directory)
    commands: list[tuple[str, ...]] = []
    for name in ("repo-scout-policy", "repo-scout"):
        path = directory / name
        if not path.is_file() or not os.access(path, os.X_OK):
            raise SmokeTestError(
                f"installed command is missing or not executable: {path}"
            )
        commands.append((str(path),))
    return commands[0], commands[1]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Smoke test installed Repo Scout policy activation."
    )
    parser.add_argument(
        "--python",
        default=sys.executable,
        help="Python interpreter from the Repo Scout installation to test.",
    )
    parser.add_argument(
        "--command-directory",
        type=Path,
        help=(
            "Directory containing installed repo-scout and "
            "repo-scout-policy commands."
        ),
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        checked = verify_policy_activation(
            args.python,
            command_directory=args.command_directory,
            environment=os.environ,
        )
    except SmokeTestError as exc:
        print(f"policy activation smoke test: {exc}", file=sys.stderr)
        return 1
    print(f"policy activation smoke test: passed {', '.join(checked)}")
    return 0


def _recommend(
    command: Sequence[str],
    root: Path,
    *,
    environment: Mapping[str, str] | None,
) -> dict[str, object]:
    completed = _run(
        [
            *command,
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


def _verify_receipt(
    command: Sequence[str],
    root: Path,
    bootstrap: subprocess.CompletedProcess[str],
    *,
    environment: Mapping[str, str] | None,
) -> None:
    receipt_path = root / "bootstrap-receipt.json"
    receipt_path.write_text(bootstrap.stdout, encoding="utf-8")
    completed = _run(
        [
            *command,
            "verify-receipt",
            str(receipt_path),
            "--format",
            "json",
        ],
        cwd=root,
        environment=environment,
    )
    try:
        verification = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise SmokeTestError(
            "policy receipt verification did not emit valid JSON"
        ) from exc
    if verification.get("status") != "pass":
        raise SmokeTestError("bootstrap receipt did not verify its policy")
    if verification.get("expected") != verification.get("actual"):
        raise SmokeTestError("receipt verification identities did not match")


def _scan(
    command: Sequence[str],
    root: Path,
    policy_path: Path,
    *,
    environment: Mapping[str, str] | None,
    expected_exit_code: int = 0,
) -> dict[str, object]:
    completed = _run(
        [
            *command,
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
