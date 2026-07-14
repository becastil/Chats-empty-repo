from __future__ import annotations

from contextlib import redirect_stdout
import io
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from repo_scout import __version__
from repo_scout import cli
from repo_scout import distribution
from repo_scout import growth
from repo_scout import outreach
from repo_scout import pilot_funnel
from repo_scout import policy_templates
from repo_scout import rollout_summary


class PublicCommandVersionTests(unittest.TestCase):
    def test_every_public_command_reports_the_package_version(self) -> None:
        commands = (
            ("repo-scout", cli.build_parser),
            ("repo-scout-distribution", distribution.build_parser),
            ("repo-scout-growth", growth.build_parser),
            ("repo-scout-outreach", outreach.build_parser),
            ("repo-scout-pilot", pilot_funnel.build_parser),
            ("repo-scout-policy", policy_templates.build_parser),
            ("repo-scout-rollout", rollout_summary.build_parser),
        )

        for command, parser_factory in commands:
            with self.subTest(command=command):
                stdout = io.StringIO()
                with redirect_stdout(stdout), self.assertRaises(SystemExit) as exit:
                    parser_factory().parse_args(["--version"])

                self.assertEqual(exit.exception.code, 0)
                self.assertEqual(stdout.getvalue(), f"{command} {__version__}\n")


if __name__ == "__main__":
    unittest.main()
