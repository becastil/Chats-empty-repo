from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import json
import subprocess
import sys
from typing import Any, Callable, Sequence


@dataclass(frozen=True)
class LabelSpec:
    name: str
    color: str
    description: str


PILOT_LABELS = (
    LabelSpec("pilot-lead", "d4c5f9", "Founding-team pilot request received"),
    LabelSpec(
        "pilot-qualified",
        "0e8a16",
        "Pilot fits the target team and repository profile",
    ),
    LabelSpec(
        "pilot-offered",
        "fbca04",
        "Written founding-team pilot scope has been offered",
    ),
    LabelSpec(
        "pilot-paid",
        "1d76db",
        "Founding-team pilot payment has been received",
    ),
    LabelSpec(
        "pilot-active",
        "0052cc",
        "Paid pilot is running in at least one repository",
    ),
    LabelSpec(
        "pilot-converted",
        "5319e7",
        "Pilot converted to an annual team license",
    ),
    LabelSpec(
        "pilot-lost",
        "b60205",
        "Pilot opportunity is no longer being pursued",
    ),
)


class LabelAuditError(RuntimeError):
    """Raised when the public pilot label contract cannot be audited."""


Runner = Callable[..., subprocess.CompletedProcess[str]]


def audit_labels(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, list):
        raise LabelAuditError("GitHub label payload must be an array")

    live: dict[str, LabelSpec] = {}
    for index, raw_label in enumerate(payload):
        if not isinstance(raw_label, dict):
            raise LabelAuditError(f"labels[{index}] must be an object")
        name = raw_label.get("name")
        color = raw_label.get("color")
        description = raw_label.get("description")
        if not isinstance(name, str) or not name:
            raise LabelAuditError(f"labels[{index}].name must be a non-empty string")
        if not name.startswith("pilot-"):
            continue
        if name in live:
            raise LabelAuditError(f"duplicate label in payload: {name}")
        if not isinstance(color, str) or not color:
            raise LabelAuditError(f"label {name} must have a color")
        if description is None:
            description = ""
        if not isinstance(description, str):
            raise LabelAuditError(f"label {name} description must be a string or null")
        live[name] = LabelSpec(name, color.lower(), description)

    expected = {label.name: label for label in PILOT_LABELS}
    missing = sorted(set(expected) - set(live))
    unexpected = sorted(set(live) - set(expected))
    drift = []
    for name in sorted(set(expected) & set(live)):
        wanted = expected[name]
        actual = live[name]
        fields = []
        if actual.color != wanted.color:
            fields.append("color")
        if actual.description != wanted.description:
            fields.append("description")
        if fields:
            drift.append(
                {
                    "name": name,
                    "fields": fields,
                    "expected": asdict(wanted),
                    "actual": asdict(actual),
                }
            )

    return {
        "schema_version": 1,
        "ready": not missing and not unexpected and not drift,
        "expected_labels": len(expected),
        "matched_labels": len(expected) - len(missing) - len(drift),
        "missing": missing,
        "unexpected": unexpected,
        "drift": drift,
    }


def fetch_labels(repo: str | None, *, runner: Runner = subprocess.run) -> Any:
    command = [
        "gh",
        "label",
        "list",
        "--limit",
        "100",
        "--json",
        "name,color,description",
    ]
    if repo:
        command.extend(("--repo", repo))
    completed = runner(command, capture_output=True, text=True, check=False)
    if completed.returncode != 0:
        detail = completed.stderr.strip() or "GitHub CLI returned no error detail"
        raise LabelAuditError(f"could not read GitHub labels: {detail}")
    try:
        return json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise LabelAuditError(f"GitHub CLI returned invalid JSON: {exc.msg}") from exc


def repair_labels(
    report: dict[str, Any],
    repo: str | None,
    *,
    runner: Runner = subprocess.run,
) -> None:
    expected = {label.name: label for label in PILOT_LABELS}
    repair_names = list(report["missing"]) + [item["name"] for item in report["drift"]]
    for name in repair_names:
        label = expected[name]
        command = [
            "gh",
            "label",
            "create",
            label.name,
            "--force",
            "--color",
            label.color,
            "--description",
            label.description,
        ]
        if repo:
            command.extend(("--repo", repo))
        completed = runner(command, capture_output=True, text=True, check=False)
        if completed.returncode != 0:
            detail = completed.stderr.strip() or "GitHub CLI returned no error detail"
            raise LabelAuditError(f"could not repair {name}: {detail}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Audit the public GitHub labels used by the paid pilot funnel."
    )
    parser.add_argument(
        "--repo",
        help="GitHub OWNER/REPOSITORY. Defaults to the current repository.",
    )
    parser.add_argument(
        "--repair",
        action="store_true",
        help="Create missing labels and restore changed colors or descriptions.",
    )
    parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Output format. Defaults to text.",
    )
    return parser


def main(
    argv: Sequence[str] | None = None,
    *,
    runner: Runner = subprocess.run,
) -> int:
    args = build_parser().parse_args(argv)
    try:
        report = audit_labels(fetch_labels(args.repo, runner=runner))
        if args.repair and (report["missing"] or report["drift"]):
            repair_labels(report, args.repo, runner=runner)
            report = audit_labels(fetch_labels(args.repo, runner=runner))
    except LabelAuditError as exc:
        print(f"audit-pilot-labels: {exc}", file=sys.stderr)
        return 2

    if args.format == "json":
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        status = "ready" if report["ready"] else "drift detected"
        print(
            f"Pilot intake labels: {status} "
            f"({report['matched_labels']}/{report['expected_labels']} matched)"
        )
        for name in report["missing"]:
            print(f"  missing: {name}")
        for item in report["drift"]:
            print(f"  changed: {item['name']} ({', '.join(item['fields'])})")
        for name in report["unexpected"]:
            print(f"  unexpected: {name}")
    return 0 if report["ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
