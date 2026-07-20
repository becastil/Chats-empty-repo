from __future__ import annotations

import csv
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from repo_scout.outreach import (  # noqa: E402
    LEDGER_FIELDS,
    PUBLIC_PILOT_INTAKE_URL,
    SCHEMA_VERSION,
)


README = ROOT / "README.md"
PLAYBOOK = ROOT / "docs" / "direct-outreach.md"
LEDGER_TEMPLATE = ROOT / "examples" / "outreach-ledger.csv"


class DirectOutreachContractTests(unittest.TestCase):
    def test_readme_describes_the_packaged_outreach_report_schema(self) -> None:
        readme = README.read_text(encoding="utf-8")
        normalized_readme = " ".join(readme.split())

        self.assertNotIn("Unreleased schema-", readme)
        self.assertIn(
            f"Schema-{SCHEMA_VERSION} reports add explicit human-approved and "
            "review-declined pre-send counts",
            normalized_readme,
        )
        self.assertIn(
            "recovers only the next approved alias",
            normalized_readme,
        )
        self.assertIn(
            "A review-declined row counts as closed without becoming a contact "
            "attempt.",
            normalized_readme,
        )

    def test_playbook_preserves_offer_source_and_bounded_cadence(self) -> None:
        playbook = PLAYBOOK.read_text(encoding="utf-8")
        normalized_playbook = " ".join(playbook.split())

        self.assertIn("$299, 90-day pilot", playbook)
        self.assertIn("up to 10 projects", playbook)
        self.assertIn("without uploading source code", playbook)
        self.assertIn("?source=outreach#why-teams-buy", playbook)
        self.assertIn("Contact 10 qualified prospects", playbook)
        self.assertIn("at most one follow-up after seven days", playbook)
        _, initial_heading, initial_tail = playbook.partition("## Initial Message")
        initial_message, follow_heading, _ = initial_tail.partition(
            "## One Follow-Up"
        )
        self.assertTrue(initial_heading)
        self.assertTrue(follow_heading)
        self.assertIn(
            "If this is not relevant, say so and I will not follow up.",
            " ".join(initial_message.split()),
        )
        self.assertIn(
            "Drafted and review-declined rows cannot have an approval date",
            normalized_playbook,
        )
        self.assertIn("Approved rows require one", normalized_playbook)
        self.assertIn(
            "None of those three statuses counts as attempted",
            normalized_playbook,
        )
        self.assertIn(
            "Keep `approved_on` on every later status",
            " ".join(playbook.split()),
        )
        self.assertIn("does not approve or", playbook)
        self.assertIn("--review-next", playbook)
        self.assertIn("--include-private-evidence", playbook)
        self.assertIn("--include-private-draft", playbook)
        self.assertIn("--review-digest", playbook)
        self.assertIn("--reviewed-private-draft", playbook)
        self.assertIn("stale review content", normalized_playbook)
        self.assertIn("Without the flags, review output remains redacted", playbook)
        self.assertIn("## prospect-NNN", playbook)
        self.assertIn("does not edit the ledger", " ".join(playbook.split()))
        self.assertIn("current UTC calendar date", normalized_playbook)
        self.assertIn('$(date -u +%F)', playbook)
        self.assertNotIn('$(date +%F)', playbook)
        self.assertIn("--approve-next", playbook)
        self.assertIn("--confirm-reviewed", playbook)
        self.assertIn("--decline-next", playbook)
        self.assertIn("--confirm-not-send", playbook)
        self.assertIn(
            "atomically changes only `status` to `review-declined`",
            normalized_playbook,
        )
        self.assertIn(
            "counts as closed but never as attempted outreach",
            normalized_playbook,
        )
        self.assertIn("number of drafts remaining", normalized_playbook)
        self.assertIn("emits no dead handoff", normalized_playbook)
        self.assertIn(
            "atomically changes only `status` and `approved_on`",
            normalized_playbook,
        )
        self.assertIn("does not send outreach", playbook)
        self.assertIn("--record-contact", playbook)
        self.assertIn("--confirm-sent", playbook)
        self.assertIn(
            "changes only `status`, `contacted_on`, and `next_action_on`",
            playbook,
        )
        self.assertIn("Repo Scout sends nothing", playbook)
        self.assertIn(
            "only the next approved alias and a guarded `--record-contact` "
            "handoff",
            normalized_playbook,
        )
        self.assertIn(
            "omits the draft, evidence, channel, and approval date",
            normalized_playbook,
        )
        self.assertIn("makes send timing inferable", " ".join(playbook.split()))
        self.assertIn("--record-follow-up", playbook)
        self.assertIn("--confirm-follow-up-sent", playbook)
        self.assertIn(
            "changes only `status`, `followed_up_on`, and `next_action_on`",
            " ".join(playbook.split()),
        )
        self.assertIn(
            "second follow-up is not scheduled", " ".join(playbook.split())
        )
        self.assertIn("--record-outcome", playbook)
        self.assertIn("--confirm-outcome-observed", playbook)
        self.assertIn(
            "atomically changes only `status` while clearing `next_action_on`",
            normalized_playbook,
        )
        self.assertIn(
            "public pilot intake before counting demand, payment, or revenue",
            normalized_playbook,
        )
        self.assertIn(PUBLIC_PILOT_INTAKE_URL, playbook)
        self.assertIn("Stop immediately after an opt-out", playbook)
        self.assertIn("reply, page visit, or release request", playbook)
        self.assertIn("do not count", playbook.lower())
        self.assertNotIn("limited time", playbook.lower())
        self.assertNotIn("guaranteed", playbook.lower())
        self.assertIn(
            f"exactly {len(LEDGER_FIELDS)} header columns",
            normalized_playbook,
        )
        self.assertIn(
            "Legacy nine-column ledgers remain readable",
            playbook,
        )

        readme = README.read_text(encoding="utf-8")
        self.assertIn("current UTC calendar date", " ".join(readme.split()))
        self.assertNotIn('$(date +%F)', readme)

    def test_private_ledger_template_has_no_prospect_data(self) -> None:
        with LEDGER_TEMPLATE.open(newline="", encoding="utf-8") as ledger_file:
            rows = list(csv.reader(ledger_file))

        self.assertEqual(rows, [list(LEDGER_FIELDS)])
        gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
        self.assertIn("/outreach-private/", gitignore)
        playbook = PLAYBOOK.read_text(encoding="utf-8")
        normalized_playbook = " ".join(playbook.split())
        self.assertIn("do not store names, email addresses", normalized_playbook)
        self.assertIn("install -d -m 700 outreach-private", playbook)
        self.assertIn(
            "install -m 600 examples/outreach-ledger.csv", playbook
        )
        self.assertIn("chmod 600 outreach-private/drafts.md", playbook)


if __name__ == "__main__":
    unittest.main()
