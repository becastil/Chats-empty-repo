from __future__ import annotations

from contextlib import redirect_stderr, redirect_stdout
import io
import json
from pathlib import Path
import subprocess
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "src"))

from audit_pilot_labels import (  # noqa: E402
    PILOT_LABELS,
    LabelAuditError,
    audit_labels,
    main,
)
from repo_scout.pilot_funnel import KNOWN_LABELS  # noqa: E402


def label_payload() -> list[dict[str, str]]:
    return [
        {
            "name": label.name,
            "color": label.color,
            "description": label.description,
        }
        for label in PILOT_LABELS
    ]


class PilotLabelAuditTests(unittest.TestCase):
    def test_contract_matches_funnel_and_issue_form(self) -> None:
        self.assertEqual({label.name for label in PILOT_LABELS}, KNOWN_LABELS)
        form = (
            ROOT / ".github/ISSUE_TEMPLATE/founding-team-pilot.yml"
        ).read_text(encoding="utf-8")
        self.assertIn("labels:\n  - pilot-lead\n", form)

    def test_audit_accepts_exact_contract_and_ignores_other_labels(self) -> None:
        payload = label_payload() + [
            {"name": "documentation", "color": "0075ca", "description": None}
        ]

        report = audit_labels(payload)

        self.assertTrue(report["ready"])
        self.assertEqual(report["matched_labels"], 7)
        self.assertEqual(report["missing"], [])
        self.assertEqual(report["unexpected"], [])
        self.assertEqual(report["drift"], [])

    def test_audit_reports_missing_changed_and_unexpected_pilot_labels(self) -> None:
        payload = label_payload()
        payload = [label for label in payload if label["name"] != "pilot-paid"]
        payload[0]["color"] = "FFFFFF"
        payload[1]["description"] = "Edited"
        payload.append(
            {"name": "pilot-maybe", "color": "000000", "description": "Unknown"}
        )

        report = audit_labels(payload)

        self.assertFalse(report["ready"])
        self.assertEqual(report["matched_labels"], 4)
        self.assertEqual(report["missing"], ["pilot-paid"])
        self.assertEqual(report["unexpected"], ["pilot-maybe"])
        self.assertEqual(
            [(item["name"], item["fields"]) for item in report["drift"]],
            [
                ("pilot-lead", ["color"]),
                ("pilot-qualified", ["description"]),
            ],
        )

    def test_audit_rejects_invalid_payload(self) -> None:
        with self.assertRaisesRegex(LabelAuditError, "must be an array"):
            audit_labels({})
        with self.assertRaisesRegex(LabelAuditError, "duplicate label"):
            audit_labels([label_payload()[0], label_payload()[0]])

    def test_main_repairs_missing_and_changed_labels_then_rechecks(self) -> None:
        before = label_payload()
        before = [label for label in before if label["name"] != "pilot-paid"]
        before[0]["description"] = "Edited"
        calls: list[list[str]] = []
        responses = [json.dumps(before), "", "", json.dumps(label_payload())]

        def runner(command: list[str], **_: object) -> subprocess.CompletedProcess[str]:
            calls.append(command)
            stdout = responses.pop(0)
            return subprocess.CompletedProcess(command, 0, stdout=stdout, stderr="")

        output = io.StringIO()
        with redirect_stdout(output):
            exit_code = main(
                ["--repo", "owner/repo", "--repair", "--format", "json"],
                runner=runner,
            )

        self.assertEqual(exit_code, 0)
        self.assertEqual(len(calls), 4)
        self.assertEqual(calls[1][0:4], ["gh", "label", "create", "pilot-paid"])
        self.assertIn("--force", calls[1])
        self.assertEqual(calls[2][0:4], ["gh", "label", "create", "pilot-lead"])
        self.assertEqual(calls[1][-2:], ["--repo", "owner/repo"])
        self.assertTrue(json.loads(output.getvalue())["ready"])

    def test_main_returns_one_for_unrepaired_drift(self) -> None:
        payload = label_payload()[:-1]

        def runner(command: list[str], **_: object) -> subprocess.CompletedProcess[str]:
            return subprocess.CompletedProcess(
                command, 0, stdout=json.dumps(payload), stderr=""
            )

        output = io.StringIO()
        with redirect_stdout(output):
            exit_code = main([], runner=runner)

        self.assertEqual(exit_code, 1)
        self.assertIn("missing: pilot-lost", output.getvalue())

    def test_main_returns_two_when_github_query_fails(self) -> None:
        def runner(command: list[str], **_: object) -> subprocess.CompletedProcess[str]:
            return subprocess.CompletedProcess(command, 1, stdout="", stderr="denied")

        errors = io.StringIO()
        with redirect_stderr(errors):
            exit_code = main([], runner=runner)

        self.assertEqual(exit_code, 2)
        self.assertIn("could not read GitHub labels: denied", errors.getvalue())


if __name__ == "__main__":
    unittest.main()
