from __future__ import annotations

import argparse
import csv
import json
import os
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
from typing import Any, Mapping, Sequence


LEDGER_FIELDS = (
    "prospect_id",
    "fit_signals",
    "fit_evidence",
    "contacted_on",
    "channel",
    "status",
    "followed_up_on",
    "next_action_on",
    "approved_on",
)
SIGNALS = "team_5_50;multi_repo;agent_use"
EVIDENCE = (
    "team_5_50=https://evidence.example/team;"
    "multi_repo=https://evidence.example/repositories;"
    "agent_use=https://evidence.example/agents"
)


class SmokeTestError(RuntimeError):
    """Raised when installed outreach behavior violates its release contract."""


def verify_outreach_lifecycle(
    python: str | Path,
    *,
    environment: Mapping[str, str] | None = None,
) -> tuple[str, ...]:
    python_command = str(Path(python))
    checked: list[str] = []

    with TemporaryDirectory() as tmp:
        ledger = Path(tmp) / "outreach-ledger.csv"

        approved = _row(
            contacted_on="",
            status="approved",
            next_action_on="",
        )
        _write_ledger(ledger, approved)
        approved_report = _report(
            python_command,
            ledger,
            as_of="2026-07-01",
            environment=environment,
        )
        _require(approved_report.get("schema_version") == 5, "schema changed")
        _require(
            approved_report.get("experiment", {}).get("human_approval_required")
            is True,
            "human approval flag is missing",
        )
        approved_summary = approved_report.get("summary", {})
        _require(approved_summary.get("approved") == 1, "approval was not counted")
        _require(
            approved_summary.get("attempted_prospects") == 0,
            "approval was counted as a contact attempt",
        )
        serialized = json.dumps(approved_report, sort_keys=True)
        for private_value in (
            approved["prospect_id"],
            approved["approved_on"],
            "https://evidence.example",
        ):
            _require(
                private_value not in serialized,
                "approved report exposed private ledger data",
            )
        checked.append("approved")

        contacted = _row()
        _write_ledger(ledger, contacted)
        contacted_report = _report(
            python_command,
            ledger,
            as_of="2026-07-01",
            environment=environment,
        )
        contacted_summary = contacted_report.get("summary", {})
        _require(
            contacted_summary.get("contacted") == 1,
            "contacted prospect was not counted",
        )
        _require(
            contacted_summary.get("attempted_prospects") == 1,
            "contact attempt total changed",
        )
        _require(
            contacted_summary.get("due_followups") == 0,
            "future follow-up was reported as due",
        )
        checked.append("contacted")

        _write_ledger(ledger, _row(approved_on=""))
        missing_approval = _run(
            python_command,
            ledger,
            as_of="2026-07-01",
            environment=environment,
            expected_exit_code=2,
        )
        _require(
            "approved_on is required after draft review" in missing_approval.stderr,
            "missing approval did not produce its controlled error",
        )
        _require(
            "https://evidence.example" not in missing_approval.stderr,
            "missing-approval error exposed evidence",
        )
        checked.append("missing-approval-rejected")

        _write_ledger(ledger, _row(), extra_value="private-extra-value")
        extra_column = _run(
            python_command,
            ledger,
            as_of="2026-07-01",
            environment=environment,
            expected_exit_code=2,
        )
        _require(
            "ledger row must have exactly 9 columns; found 10"
            in extra_column.stderr,
            "extra column did not produce its controlled error",
        )
        _require(
            "private-extra-value" not in extra_column.stderr,
            "row-width error exposed the extra value",
        )
        checked.append("extra-column-rejected")

    return tuple(checked)


def _row(**overrides: str) -> dict[str, str]:
    row = {
        "prospect_id": "prospect-001",
        "fit_signals": SIGNALS,
        "fit_evidence": EVIDENCE,
        "contacted_on": "2026-07-01",
        "channel": "published-business",
        "status": "contacted",
        "followed_up_on": "",
        "next_action_on": "2026-07-08",
        "approved_on": "2026-06-30",
    }
    row.update(overrides)
    return row


def _write_ledger(
    path: Path,
    row: Mapping[str, str],
    *,
    extra_value: str | None = None,
) -> None:
    with path.open("w", newline="", encoding="utf-8") as ledger_file:
        writer = csv.writer(ledger_file, lineterminator="\n")
        writer.writerow(LEDGER_FIELDS)
        values = [row[field] for field in LEDGER_FIELDS]
        if extra_value is not None:
            values.append(extra_value)
        writer.writerow(values)


def _report(
    python: str,
    ledger: Path,
    *,
    as_of: str,
    environment: Mapping[str, str] | None,
) -> dict[str, Any]:
    completed = _run(
        python,
        ledger,
        as_of=as_of,
        environment=environment,
        expected_exit_code=0,
    )
    try:
        report = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise SmokeTestError("outreach command did not emit valid JSON") from exc
    if not isinstance(report, dict):
        raise SmokeTestError("outreach command emitted a non-object report")
    return report


def _run(
    python: str,
    ledger: Path,
    *,
    as_of: str,
    environment: Mapping[str, str] | None,
    expected_exit_code: int,
) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(
        [
            python,
            "-m",
            "repo_scout.outreach",
            str(ledger),
            "--as-of",
            as_of,
            "--format",
            "json",
        ],
        capture_output=True,
        text=True,
        env=dict(environment) if environment is not None else None,
    )
    if completed.returncode != expected_exit_code:
        detail = completed.stderr.strip() or completed.stdout.strip() or "no output"
        raise SmokeTestError(
            f"outreach command exited {completed.returncode}; "
            f"expected {expected_exit_code}: {detail}"
        )
    return completed


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise SmokeTestError(message)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Smoke test the installed Repo Scout outreach lifecycle."
    )
    parser.add_argument("--python", default=sys.executable)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        checked = verify_outreach_lifecycle(args.python, environment=os.environ)
    except SmokeTestError as exc:
        print(f"outreach lifecycle smoke test failed: {exc}", file=sys.stderr)
        return 1
    print("outreach lifecycle smoke test passed: " + ", ".join(checked))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
