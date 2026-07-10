from __future__ import annotations

import argparse
from dataclasses import dataclass
from importlib import resources
import json
import os
from pathlib import Path
import sys
from tempfile import NamedTemporaryFile
from typing import Any, Sequence

from .policy import PolicyError, parse_policy


TEMPLATE_SCHEMA_VERSION = 1
OUTPUT_ERROR_EXIT_CODE = 4


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
                (
                    f"  Limits: {rules.get('max_files', 'none')} files / "
                    f"{rules.get('max_total_bytes', 'none')} bytes"
                ),
            ]
        )
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="repo-scout-policy",
        description="Discover and initialize Repo Scout policy templates.",
    )
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


def _write_template(content: str, output: str, force: bool) -> int:
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
            with NamedTemporaryFile(
                "w",
                encoding="utf-8",
                dir=target.parent,
                prefix=f".{target.name}.",
                delete=False,
            ) as temporary:
                temporary.write(content)
                temporary_path = Path(temporary.name)
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

    print(f"repo-scout-policy: wrote {target}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
