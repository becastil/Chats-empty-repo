from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
import re
import sys
from typing import Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SURFACE_PATTERNS = (
    ".github/workflows/*.yml",
    ".github/workflows/*.yaml",
    "examples/github-actions/*.yml",
    "examples/github-actions/*.yaml",
)
DOGFOOD_POLICY_PATH = Path(".github/workflows/repo-scout-policy.yml")
CUSTOMER_POLICY_PATH = Path("examples/github-actions/repo-scout-policy.yml")
USES_PATTERN = re.compile(
    r"(?m)^[ \t]*(?:-[ \t]*)?uses:[ \t]*(?P<value>[^\r\n]*)$"
)
ACTION_PATTERN = re.compile(
    r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.-]+)*\Z"
)
SHA_PATTERN = re.compile(r"[0-9a-f]{40}\Z")
VERSION_PATTERN = re.compile(r"v[0-9]+\.[0-9]+\.[0-9]+\Z")


class ActionPinAuditError(RuntimeError):
    """Raised when hosted and customer action pins are not review-consistent."""


@dataclass(frozen=True)
class ActionReference:
    action: str
    sha: str
    version: str
    path: Path
    line: int

    @property
    def location(self) -> str:
        return f"{self.path}:{self.line}"


@dataclass(frozen=True)
class ActionPin:
    action: str
    sha: str
    version: str
    references: tuple[str, ...]


def audit_action_pins(root: Path) -> tuple[ActionPin, ...]:
    project_root = root.expanduser().resolve()
    surface_paths = _surface_paths(project_root)
    references: list[ActionReference] = []
    references_by_path: dict[Path, tuple[ActionReference, ...]] = {}

    for relative_path in surface_paths:
        path_references = _read_action_references(
            project_root / relative_path,
            relative_path,
        )
        references.extend(path_references)
        references_by_path[relative_path] = path_references

    if not references:
        raise ActionPinAuditError(
            "no external GitHub Action references were found in hosted or "
            "copy-ready workflow surfaces"
        )

    grouped: dict[str, list[ActionReference]] = {}
    for reference in references:
        grouped.setdefault(reference.action, []).append(reference)

    pins: list[ActionPin] = []
    for action, action_references in sorted(grouped.items()):
        identities = {
            (reference.sha, reference.version)
            for reference in action_references
        }
        if len(identities) != 1:
            details = ", ".join(
                f"{reference.sha} ({reference.version}) at "
                f"{reference.location}"
                for reference in sorted(
                    action_references,
                    key=lambda item: (str(item.path), item.line),
                )
            )
            raise ActionPinAuditError(
                f"{action} has multiple pinned identities: {details}"
            )
        sha, version = identities.pop()
        pins.append(
            ActionPin(
                action=action,
                sha=sha,
                version=version,
                references=tuple(
                    reference.location
                    for reference in sorted(
                        action_references,
                        key=lambda item: (str(item.path), item.line),
                    )
                ),
            )
        )

    dogfood_actions = _action_sequence(
        references_by_path,
        DOGFOOD_POLICY_PATH,
    )
    customer_actions = _action_sequence(
        references_by_path,
        CUSTOMER_POLICY_PATH,
    )
    if dogfood_actions != customer_actions:
        raise ActionPinAuditError(
            "dogfood and copy-ready policy action sequences differ: "
            f"dogfood={dogfood_actions}, customer={customer_actions}"
        )

    return tuple(pins)


def _surface_paths(root: Path) -> tuple[Path, ...]:
    paths = {
        path.relative_to(root)
        for pattern in SURFACE_PATTERNS
        for path in root.glob(pattern)
        if path.is_file()
    }
    for required_path in (DOGFOOD_POLICY_PATH, CUSTOMER_POLICY_PATH):
        if required_path not in paths:
            raise ActionPinAuditError(
                f"required paid-CI workflow surface is missing: {required_path}"
            )
    return tuple(sorted(paths, key=str))


def _read_action_references(
    target: Path,
    relative_path: Path,
) -> tuple[ActionReference, ...]:
    try:
        content = target.read_text(encoding="utf-8")
    except OSError as exc:
        raise ActionPinAuditError(
            f"could not read {relative_path}: {exc}"
        ) from exc

    references: list[ActionReference] = []
    for match in USES_PATTERN.finditer(content):
        raw_value = match.group("value").strip()
        raw_spec, separator, raw_comment = raw_value.partition("#")
        spec = raw_spec.strip()
        comment = raw_comment.strip() if separator else ""
        line = content.count("\n", 0, match.start()) + 1
        location = f"{relative_path}:{line}"

        if spec.startswith("./"):
            continue
        if spec.startswith("docker://"):
            raise ActionPinAuditError(
                f"{location} has unsupported external action reference {spec!r}"
            )
        if "@" not in spec:
            raise ActionPinAuditError(
                f"{location} external action reference must include a pin"
            )
        action, ref = spec.rsplit("@", 1)
        if ACTION_PATTERN.fullmatch(action) is None:
            raise ActionPinAuditError(
                f"{location} has unsupported external action reference {spec!r}"
            )
        if SHA_PATTERN.fullmatch(ref) is None:
            raise ActionPinAuditError(
                f"{location} must pin {action} to a full 40-character "
                "lowercase commit SHA"
            )
        if VERSION_PATTERN.fullmatch(comment) is None:
            raise ActionPinAuditError(
                f"{location} must annotate {action}@{ref} with exactly one "
                "semantic release comment such as '# v1.2.3'"
            )
        references.append(
            ActionReference(
                action=action,
                sha=ref,
                version=comment,
                path=relative_path,
                line=line,
            )
        )
    return tuple(references)


def _action_sequence(
    references_by_path: dict[Path, tuple[ActionReference, ...]],
    path: Path,
) -> tuple[str, ...]:
    try:
        references = references_by_path[path]
    except KeyError as exc:
        raise ActionPinAuditError(
            f"required paid-CI workflow surface was not audited: {path}"
        ) from exc
    return tuple(reference.action for reference in references)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Audit immutable GitHub Action identities across hosted and "
            "copy-ready paid-CI workflow surfaces."
        )
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=PROJECT_ROOT,
        help="Repository root. Defaults to the current Repo Scout checkout.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        pins = audit_action_pins(args.root)
    except ActionPinAuditError as exc:
        print(f"action-pin-audit: {exc}", file=sys.stderr)
        return 2
    reference_count = sum(len(pin.references) for pin in pins)
    surface_count = len(
        {
            reference.rsplit(":", 1)[0]
            for pin in pins
            for reference in pin.references
        }
    )
    print(
        "action pin audit passed: "
        f"actions={len(pins)}, references={reference_count}, "
        f"surfaces={surface_count}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
