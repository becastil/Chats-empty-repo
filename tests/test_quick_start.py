from __future__ import annotations

import os
from pathlib import Path
import re
import subprocess
from tempfile import TemporaryDirectory
import tomllib
import unittest


ROOT = Path(__file__).resolve().parents[1]
with (ROOT / "pyproject.toml").open("rb") as project_file:
    PROJECT_VERSION = tomllib.load(project_file)["project"]["version"]
PORTABLE_RELEASE_URL = (
    "https://github.com/becastil/Chats-empty-repo/releases/download/"
    f"v{PROJECT_VERSION}/repo-scout-{PROJECT_VERSION}.pyz"
)


def shell_block_after(path: Path, heading: str) -> str:
    content = path.read_text(encoding="utf-8")
    _, separator, remainder = content.partition(heading)
    if not separator:
        raise AssertionError(f"{path.name} is missing {heading!r}")
    match = re.search(r"```bash\n(?P<commands>.*?)\n```", remainder, re.DOTALL)
    if match is None:
        raise AssertionError(
            f"{path.name} is missing a bash block after {heading!r}"
        )
    return match.group("commands")


def site_quick_start() -> str:
    content = (ROOT / "app" / "repo-scout-page.tsx").read_text(encoding="utf-8")
    match = re.search(
        r"const quickStart = `(?P<commands>[^`]+)`;",
        content,
    )
    if match is None:
        raise AssertionError("the site is missing its quick-start command")
    return match.group("commands").replace(
        "${PORTABLE_RELEASE_URL}",
        PORTABLE_RELEASE_URL,
    )


class QuickStartTests(unittest.TestCase):
    def test_public_quick_starts_stop_when_download_fails(self) -> None:
        snippets = {
            "README": shell_block_after(ROOT / "README.md", "## Quick Start"),
            "release guide": shell_block_after(
                ROOT / "docs" / "releases.md",
                "## Install A Release",
            ),
            "website": site_quick_start(),
        }
        for name, snippet in snippets.items():
            with self.subTest(name=name, contract="release URL"):
                self.assertIn(PORTABLE_RELEASE_URL, snippet)

        with TemporaryDirectory() as temporary_directory:
            temporary = Path(temporary_directory)
            bin_directory = temporary / "bin"
            bin_directory.mkdir()
            marker = temporary / "python-called"

            curl = bin_directory / "curl"
            curl.write_text("#!/bin/sh\nexit 22\n", encoding="utf-8")
            curl.chmod(0o755)

            python = bin_directory / "python3"
            python.write_text(
                '#!/bin/sh\nprintf "called\\n" > "$PYTHON_MARKER"\n',
                encoding="utf-8",
            )
            python.chmod(0o755)

            environment = {
                **os.environ,
                "PATH": str(bin_directory),
                "PYTHON_MARKER": str(marker),
            }
            for name, snippet in snippets.items():
                with self.subTest(name=name):
                    marker.unlink(missing_ok=True)
                    completed = subprocess.run(
                        ["/bin/sh", "-c", snippet],
                        env=environment,
                        capture_output=True,
                        text=True,
                        check=False,
                    )

                    self.assertEqual(completed.returncode, 22)
                    self.assertFalse(
                        marker.exists(),
                        f"{name} ran Python after the download failed",
                    )


if __name__ == "__main__":
    unittest.main()
