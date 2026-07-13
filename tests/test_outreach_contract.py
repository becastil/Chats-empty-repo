from __future__ import annotations

import csv
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
PLAYBOOK = ROOT / "docs" / "direct-outreach.md"
LEDGER_TEMPLATE = ROOT / "examples" / "outreach-ledger.csv"


class DirectOutreachContractTests(unittest.TestCase):
    def test_playbook_preserves_offer_source_and_bounded_cadence(self) -> None:
        playbook = PLAYBOOK.read_text(encoding="utf-8")

        self.assertIn("$299, 90-day pilot", playbook)
        self.assertIn("up to 10 projects", playbook)
        self.assertIn("without uploading source code", playbook)
        self.assertIn("?source=outreach#why-teams-buy", playbook)
        self.assertIn("Contact 10 qualified prospects", playbook)
        self.assertIn("at most one follow-up after seven days", playbook)
        self.assertIn("Drafted and approved rows have no", playbook)
        self.assertIn("do not count as attempted outreach", playbook)
        self.assertIn("does not approve or", playbook)
        self.assertIn("Stop immediately after an opt-out", playbook)
        self.assertIn("reply, page visit, or release request", playbook)
        self.assertIn("do not count", playbook.lower())
        self.assertNotIn("limited time", playbook.lower())
        self.assertNotIn("guaranteed", playbook.lower())

    def test_private_ledger_template_has_no_prospect_data(self) -> None:
        with LEDGER_TEMPLATE.open(newline="", encoding="utf-8") as ledger_file:
            rows = list(csv.reader(ledger_file))

        self.assertEqual(
            rows,
            [
                [
                    "prospect_id",
                    "fit_signals",
                    "fit_evidence",
                    "contacted_on",
                    "channel",
                    "status",
                    "followed_up_on",
                    "next_action_on",
                ]
            ],
        )
        gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
        self.assertIn("/outreach-private/", gitignore)
        playbook = PLAYBOOK.read_text(encoding="utf-8")
        self.assertIn("do not store names, email addresses", playbook)


if __name__ == "__main__":
    unittest.main()
