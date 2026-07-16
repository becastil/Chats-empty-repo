from __future__ import annotations

import argparse
from dataclasses import dataclass
from importlib import resources
import json
import os
from pathlib import Path
import re
import stat
import sys
from tempfile import NamedTemporaryFile
from typing import Any, Sequence

from .version import add_version_argument

from .policy import PolicyError, load_policy, parse_policy, policy_fingerprint


TEMPLATE_SCHEMA_VERSION = 1
RECOMMENDATION_SCHEMA_VERSION = 1
BOOTSTRAP_SCHEMA_VERSION = 1
RECEIPT_VERIFICATION_SCHEMA_VERSION = 1
OUTPUT_ERROR_EXIT_CODE = 4
POLICY_MISMATCH_EXIT_CODE = 6


@dataclass(frozen=True)
class TemplateDefinition:
    name: str
    title: str
    description: str


TEMPLATES = (
    TemplateDefinition(
        "service-baseline",
        "Service baseline",
        "A conservative starting point for an existing software service.",
    ),
    TemplateDefinition(
        "python-service",
        "Python service",
        "A Python service with committed project metadata and bounded size.",
    ),
    TemplateDefinition(
        "node-npm-service",
        "Node npm service",
        "A Node service that commits an npm lockfile for repeatable installs.",
    ),
    TemplateDefinition(
        "node-service",
        "Node service",
        "A Node service using npm, pnpm, or Yarn with a committed lockfile.",
    ),
    TemplateDefinition(
        "agent-ready-service",
        "Agent-ready service",
        "A service with explicit instructions for developers and coding agents.",
    ),
)
TEMPLATE_BY_NAME = {template.name: template for template in TEMPLATES}


class TemplateError(RuntimeError):
    """Raised when a packaged policy template cannot be read."""


def get_template(name: str) -> str:
    if name not in TEMPLATE_BY_NAME:
        raise TemplateError(f"unknown policy template: {name}")

    resource = (
        resources.files("repo_scout")
        .joinpath("templates")
        .joinpath("policies")
        .joinpath(f"{name}.toml")
    )
    try:
        return resource.read_text(encoding="utf-8")
    except (FileNotFoundError, OSError) as exc:
        raise TemplateError(f"could not read packaged policy template {name}: {exc}") from exc


def list_templates() -> dict[str, Any]:
    templates = []
    for definition in TEMPLATES:
        try:
            policy = parse_policy(
                get_template(definition.name),
                source=f"packaged policy template {definition.name}",
            )
        except PolicyError as exc:
            raise TemplateError(
                f"packaged policy template {definition.name} is invalid: {exc}"
            ) from exc
        templates.append(
            {
                "name": definition.name,
                "title": definition.title,
                "description": definition.description,
                "rules": policy["repository"],
            }
        )
    return {"schema_version": TEMPLATE_SCHEMA_VERSION, "templates": templates}


def format_templates(catalog: dict[str, Any]) -> str:
    lines = ["Repo Scout Policy Templates"]
    for template in catalog["templates"]:
        rules = template["rules"]
        required = ", ".join(rules.get("required_files", [])) or "none"
        lines.extend(
            [
                f"{template['name']} - {template['title']}",
                f"  {template['description']}",
                f"  Required files: {required}",
            ]
        )
        for group in rules.get("required_file_groups", []):
            lines.append(f"  Required alternative: {' or '.join(group)}")
        lines.append(
            f"  Limits: {rules.get('max_files', 'none')} files / "
            f"{rules.get('max_total_bytes', 'none')} bytes"
        )
    return "\n".join(lines)


def recommend_template(path: str | Path) -> dict[str, Any]:
    root = Path(path).expanduser().resolve()
    if not root.is_dir():
        raise TemplateError(f"recommendation path is not a directory: {root}")

    signal_names = (
        "README.md",
        "AGENTS.md",
        "pyproject.toml",
        "package.json",
        "package-lock.json",
        "pnpm-lock.yaml",
        "yarn.lock",
    )
    signals = [name for name in signal_names if (root / name).is_file()]
    has_node = "package.json" in signals
    has_python = "pyproject.toml" in signals
    node_lockfiles = [
        name
        for name in ("package-lock.json", "pnpm-lock.yaml", "yarn.lock")
        if name in signals
    ]

    if has_node:
        if node_lockfiles == ["package-lock.json"]:
            name = "node-npm-service"
            reason = "package.json and the npm lockfile were detected."
        else:
            name = "node-service"
            if node_lockfiles:
                reason = (
                    "package.json and a supported flexible Node lockfile "
                    "were detected."
                )
            else:
                reason = (
                    "package.json was detected; the flexible Node starter "
                    "will require a committed npm, pnpm, or Yarn lockfile."
                )
    elif has_python:
        name = "python-service"
        reason = "pyproject.toml was detected."
    elif "AGENTS.md" in signals:
        name = "agent-ready-service"
        reason = "AGENTS.md was detected without a language-specific manifest."
    else:
        name = "service-baseline"
        reason = "No supported language-specific manifest was detected."

    definition = TEMPLATE_BY_NAME[name]
    review_required = has_node and has_python
    review_note = None
    if review_required:
        review_note = (
            "Both package.json and pyproject.toml were detected; combine the "
            "relevant Node and Python rules before team rollout."
        )
    return {
        "schema_version": RECOMMENDATION_SCHEMA_VERSION,
        "recommendation": {
            "name": definition.name,
            "title": definition.title,
            "reason": reason,
        },
        "signals": signals,
        "review_required": review_required,
        "review_note": review_note,
        "init_command": f"repo-scout-policy init {definition.name}",
    }


def format_recommendation(recommendation: dict[str, Any]) -> str:
    selected = recommendation["recommendation"]
    signals = ", ".join(recommendation["signals"]) or "none"
    lines = [
        "Repo Scout Policy Recommendation",
        f"Starter: {selected['name']} - {selected['title']}",
        f"Reason: {selected['reason']}",
        f"Signals: {signals}",
        (
            "Review required: yes"
            if recommendation["review_required"]
            else "Review required: no"
        ),
    ]
    if recommendation["review_note"] is not None:
        lines.append(f"Review note: {recommendation['review_note']}")
    lines.append(f"Next command: {recommendation['init_command']}")
    return "\n".join(lines)


def prepare_bootstrap(
    path: str | Path, output: str | Path | None = None
) -> tuple[dict[str, Any], Path, str]:
    root = Path(path).expanduser().resolve()
    recommendation = recommend_template(root)
    if recommendation["review_required"]:
        raise TemplateError(
            "bootstrap requires policy review: "
            f"{recommendation['review_note']}"
        )

    if output is None:
        target = root / "repo-scout-policy.toml"
    else:
        requested = Path(output).expanduser()
        if requested.is_absolute():
            target = requested
        else:
            target = (root / requested).resolve()
            if root not in target.parents:
                raise TemplateError(
                    f"relative bootstrap output escapes repository: {output}"
                )
    name = recommendation["recommendation"]["name"]
    return recommendation, target, get_template(name)


def bootstrap_receipt(
    recommendation: dict[str, Any],
    target: Path,
    content: str,
    *,
    replaced: bool,
) -> dict[str, Any]:
    selected = recommendation["recommendation"]
    try:
        policy = parse_policy(
            content,
            source=f"packaged policy template {selected['name']}",
        )
    except PolicyError as exc:
        raise TemplateError(
            f"packaged policy template {selected['name']} is invalid: {exc}"
        ) from exc
    return {
        "schema_version": BOOTSTRAP_SCHEMA_VERSION,
        "status": "replaced" if replaced else "created",
        "output": str(target.expanduser().resolve()),
        "starter": {
            "name": selected["name"],
            "title": selected["title"],
            "reason": selected["reason"],
        },
        "policy": {
            "version": policy["version"],
            "fingerprint": policy_fingerprint(policy),
        },
    }


def load_bootstrap_receipt(path: str | Path) -> dict[str, Any]:
    source = Path(path).expanduser().resolve()
    try:
        content = source.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise TemplateError(f"bootstrap receipt does not exist: {source}") from exc
    except (OSError, UnicodeDecodeError) as exc:
        raise TemplateError(
            f"could not read bootstrap receipt {source}: {exc}"
        ) from exc

    try:
        receipt = json.loads(
            content,
            object_pairs_hook=_reject_duplicate_json_keys,
        )
    except json.JSONDecodeError as exc:
        raise TemplateError(
            f"invalid bootstrap receipt JSON in {source}: {exc.msg}"
        ) from exc
    except TemplateError as exc:
        raise TemplateError(
            f"invalid bootstrap receipt JSON in {source}: {exc}"
        ) from exc
    return _validate_bootstrap_receipt(receipt)


def verify_bootstrap_receipt(
    receipt_path: str | Path,
    policy_path: str | Path | None = None,
) -> dict[str, Any]:
    receipt_source = Path(receipt_path).expanduser().resolve()
    receipt = load_bootstrap_receipt(receipt_source)
    target_value = receipt["output"] if policy_path is None else policy_path
    target = Path(target_value).expanduser().resolve()
    expected = dict(receipt["policy"])

    try:
        policy = load_policy(target)
    except PolicyError as exc:
        actual = None
        status = "fail"
        message = str(exc)
    else:
        actual = {
            "version": policy["version"],
            "fingerprint": policy_fingerprint(policy),
        }
        status = "pass" if actual == expected else "fail"
        message = (
            "Policy matches bootstrap receipt."
            if status == "pass"
            else "Policy identity does not match bootstrap receipt."
        )

    return {
        "schema_version": RECEIPT_VERIFICATION_SCHEMA_VERSION,
        "status": status,
        "receipt": str(receipt_source),
        "policy": str(target),
        "expected": expected,
        "actual": actual,
        "message": message,
    }


def format_receipt_verification(verification: dict[str, Any]) -> str:
    expected = verification["expected"]
    actual = verification["actual"]
    lines = [
        "Repo Scout Bootstrap Receipt Verification",
        f"Status: {verification['status']}",
        f"Receipt: {verification['receipt']}",
        f"Policy: {verification['policy']}",
        (
            f"Expected: version {expected['version']} / "
            f"{expected['fingerprint']}"
        ),
    ]
    if actual is None:
        lines.append("Actual: unavailable")
    else:
        lines.append(
            f"Actual: version {actual['version']} / {actual['fingerprint']}"
        )
    lines.append(f"Message: {verification['message']}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="repo-scout-policy",
        description="Discover and initialize Repo Scout policy templates.",
    )
    add_version_argument(parser)
    subparsers = parser.add_subparsers(dest="command", required=True)

    list_parser = subparsers.add_parser(
        "list", help="List available starter policies."
    )
    list_parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Output format. Defaults to text.",
    )

    recommend_parser = subparsers.add_parser(
        "recommend", help="Recommend a starter from local repository signals."
    )
    recommend_parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Repository path to inspect. Defaults to the current directory.",
    )
    recommend_parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Output format. Defaults to text.",
    )

    bootstrap_parser = subparsers.add_parser(
        "bootstrap",
        help="Recommend and write a starter when review is not required.",
    )
    bootstrap_parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Repository path to inspect. Defaults to the current directory.",
    )
    bootstrap_parser.add_argument(
        "--output",
        help=(
            "Destination path. Relative paths resolve inside the inspected "
            "repository; defaults to repo-scout-policy.toml."
        ),
    )
    bootstrap_parser.add_argument(
        "--force",
        action="store_true",
        help="Replace an existing destination file.",
    )
    bootstrap_parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Success output format. Defaults to text.",
    )

    verify_parser = subparsers.add_parser(
        "verify-receipt",
        help="Verify that a policy still matches a bootstrap receipt.",
    )
    verify_parser.add_argument(
        "receipt",
        help="Path to a JSON bootstrap receipt.",
    )
    verify_parser.add_argument(
        "--policy",
        help="Policy path override. Defaults to the receipt output path.",
    )
    verify_parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Output format. Defaults to text.",
    )

    show_parser = subparsers.add_parser(
        "show", help="Print one starter policy as TOML."
    )
    show_parser.add_argument("template", choices=tuple(TEMPLATE_BY_NAME))

    init_parser = subparsers.add_parser(
        "init", help="Write one starter policy to a local file."
    )
    init_parser.add_argument("template", choices=tuple(TEMPLATE_BY_NAME))
    init_parser.add_argument(
        "--output",
        default="repo-scout-policy.toml",
        metavar="PATH",
        help="Destination path. Defaults to repo-scout-policy.toml.",
    )
    init_parser.add_argument(
        "--force",
        action="store_true",
        help="Replace an existing destination file.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        if args.command == "list":
            catalog = list_templates()
            if args.format == "json":
                print(json.dumps(catalog, indent=2, sort_keys=True))
            else:
                print(format_templates(catalog))
            return 0

        if args.command == "recommend":
            recommendation = recommend_template(args.path)
            if args.format == "json":
                print(json.dumps(recommendation, indent=2, sort_keys=True))
            else:
                print(format_recommendation(recommendation))
            return 0

        if args.command == "bootstrap":
            recommendation, target, content = prepare_bootstrap(
                args.path, args.output
            )
            replaced = target.exists()
            selected = recommendation["recommendation"]
            receipt = bootstrap_receipt(
                recommendation, target, content, replaced=replaced
            )
            if args.format == "text":
                print(
                    f"repo-scout-policy: selected {selected['name']}: "
                    f"{selected['reason']}",
                    file=sys.stderr,
                )
            exit_code = _write_template(
                content,
                str(target),
                args.force,
                announce=args.format == "text",
            )
            if exit_code != 0:
                return exit_code
            if args.format == "json":
                print(json.dumps(receipt, indent=2, sort_keys=True))
            return 0

        if args.command == "verify-receipt":
            verification = verify_bootstrap_receipt(args.receipt, args.policy)
            if args.format == "json":
                print(json.dumps(verification, indent=2, sort_keys=True))
            else:
                print(format_receipt_verification(verification))
            return (
                0
                if verification["status"] == "pass"
                else POLICY_MISMATCH_EXIT_CODE
            )

        content = get_template(args.template)
    except TemplateError as exc:
        print(f"repo-scout-policy: {exc}", file=sys.stderr)
        return 2

    if args.command == "show":
        print(content, end="" if content.endswith("\n") else "\n")
        return 0

    if args.output == "-":
        print(
            "repo-scout-policy: --output - is not supported; use show for stdout",
            file=sys.stderr,
        )
        return 2

    return _write_template(content, args.output, args.force)


def _write_template(
    content: str, output: str, force: bool, *, announce: bool = True
) -> int:
    target = Path(output).expanduser()
    if target.exists() and not force:
        print(
            f"repo-scout-policy: output already exists: {target}; "
            "pass --force to replace it",
            file=sys.stderr,
        )
        return OUTPUT_ERROR_EXIT_CODE

    if force:
        temporary_path: Path | None = None
        try:
            target_mode = (
                stat.S_IMODE(target.stat().st_mode) if target.exists() else None
            )
            with NamedTemporaryFile(
                "w",
                encoding="utf-8",
                dir=target.parent,
                prefix=f".{target.name}.",
                delete=False,
            ) as temporary:
                temporary.write(content)
                temporary_path = Path(temporary.name)
            if target_mode is not None:
                os.chmod(temporary_path, target_mode)
            os.replace(temporary_path, target)
        except OSError as exc:
            if temporary_path is not None:
                temporary_path.unlink(missing_ok=True)
            print(
                f"repo-scout-policy: could not write {target}: {exc}",
                file=sys.stderr,
            )
            return OUTPUT_ERROR_EXIT_CODE
    else:
        try:
            with target.open("x", encoding="utf-8") as output_file:
                output_file.write(content)
        except FileExistsError:
            print(
                f"repo-scout-policy: output already exists: {target}; "
                "pass --force to replace it",
                file=sys.stderr,
            )
            return OUTPUT_ERROR_EXIT_CODE
        except OSError as exc:
            print(
                f"repo-scout-policy: could not write {target}: {exc}",
                file=sys.stderr,
            )
            return OUTPUT_ERROR_EXIT_CODE

    if announce:
        print(f"repo-scout-policy: wrote {target}", file=sys.stderr)
    return 0


def _validate_bootstrap_receipt(receipt: Any) -> dict[str, Any]:
    if not isinstance(receipt, dict):
        raise TemplateError("bootstrap receipt must be a JSON object")
    _require_exact_keys(
        receipt,
        {"schema_version", "status", "output", "starter", "policy"},
        "bootstrap receipt",
    )
    if receipt["schema_version"] != BOOTSTRAP_SCHEMA_VERSION or isinstance(
        receipt["schema_version"], bool
    ):
        raise TemplateError(
            f"bootstrap receipt schema_version must be {BOOTSTRAP_SCHEMA_VERSION}"
        )
    if receipt["status"] not in {"created", "replaced"}:
        raise TemplateError(
            "bootstrap receipt status must be created or replaced"
        )
    if not isinstance(receipt["output"], str) or not receipt["output"]:
        raise TemplateError(
            "bootstrap receipt output must be a non-empty string"
        )

    starter = receipt["starter"]
    if not isinstance(starter, dict):
        raise TemplateError("bootstrap receipt starter must be an object")
    _require_exact_keys(starter, {"name", "title", "reason"}, "starter")
    for key in ("name", "title", "reason"):
        if not isinstance(starter[key], str) or not starter[key]:
            raise TemplateError(
                f"bootstrap receipt starter.{key} must be a string"
            )

    policy = receipt["policy"]
    if not isinstance(policy, dict):
        raise TemplateError("bootstrap receipt policy must be an object")
    _require_exact_keys(policy, {"version", "fingerprint"}, "policy")
    if not isinstance(policy["version"], int) or isinstance(
        policy["version"], bool
    ):
        raise TemplateError("bootstrap receipt policy.version must be an integer")
    if not isinstance(policy["fingerprint"], str) or re.fullmatch(
        r"sha256:[0-9a-f]{64}", policy["fingerprint"]
    ) is None:
        raise TemplateError(
            "bootstrap receipt policy.fingerprint must be a SHA-256 identity"
        )
    return receipt


def _require_exact_keys(
    value: dict[str, Any], expected: set[str], label: str
) -> None:
    actual = set(value)
    if actual == expected:
        return
    missing = sorted(expected - actual)
    unknown = sorted(actual - expected)
    details = []
    if missing:
        details.append(f"missing keys: {', '.join(missing)}")
    if unknown:
        details.append(f"unknown keys: {', '.join(unknown)}")
    raise TemplateError(f"{label} has {'; '.join(details)}")


def _reject_duplicate_json_keys(
    pairs: list[tuple[str, Any]],
) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise TemplateError(f"duplicate key: {key}")
        result[key] = value
    return result


if __name__ == "__main__":
    raise SystemExit(main())
