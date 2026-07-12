from __future__ import annotations

import argparse
from dataclasses import dataclass
import os
from pathlib import Path
import re
import sys
from tempfile import NamedTemporaryFile
from typing import Sequence


TARGETS = (
    Path(".github/workflows/repo-scout-policy.yml"),
    Path("examples/github-actions/repo-scout-policy.yml"),
    Path("tests/test_ci_examples.py"),
)
VERSION_PATTERN = re.compile(r"[0-9]+\.[0-9]+\.[0-9]+\Z")
SHA_PATTERN = re.compile(r"[0-9a-f]{40}\Z")
DIGEST_PATTERN = re.compile(r"[0-9a-f]{64}\Z")


class PinUpdateError(RuntimeError):
    """Raised when a verified-release pin cannot be updated safely."""


@dataclass(frozen=True)
class ReleasePin:
    version: str
    source_sha: str
    wheel_sha256: str

    def validate(self) -> None:
        if VERSION_PATTERN.fullmatch(self.version) is None:
            raise PinUpdateError("version must be MAJOR.MINOR.PATCH")
        if SHA_PATTERN.fullmatch(self.source_sha) is None:
            raise PinUpdateError("source SHA must be 40 lowercase hexadecimal characters")
        if DIGEST_PATTERN.fullmatch(self.wheel_sha256) is None:
            raise PinUpdateError(
                "wheel SHA-256 must be 64 lowercase hexadecimal characters"
            )


def update_release_pin(root: Path, pin: ReleasePin) -> tuple[Path, ...]:
    pin.validate()
    project_root = root.expanduser().resolve()
    prepared: dict[Path, str] = {}

    for relative_path in TARGETS:
        target = project_root / relative_path
        try:
            content = target.read_text(encoding="utf-8")
        except OSError as exc:
            raise PinUpdateError(f"could not read {relative_path}: {exc}") from exc
        prepared[target] = (
            _update_test_contract(content, pin, relative_path)
            if relative_path.name == "test_ci_examples.py"
            else _update_workflow(content, pin, relative_path)
        )

    temporary_paths: dict[Path, Path] = {}
    try:
        for target, content in prepared.items():
            with NamedTemporaryFile(
                "w",
                encoding="utf-8",
                dir=target.parent,
                prefix=f".{target.name}.",
                delete=False,
            ) as temporary:
                temporary.write(content)
                temporary_paths[target] = Path(temporary.name)
            os.chmod(temporary_paths[target], target.stat().st_mode)
        for target, temporary_path in temporary_paths.items():
            os.replace(temporary_path, target)
    except OSError as exc:
        for temporary_path in temporary_paths.values():
            temporary_path.unlink(missing_ok=True)
        raise PinUpdateError(f"could not write verified release pin: {exc}") from exc

    return TARGETS


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Update every verified Repo Scout CI release pin together."
    )
    parser.add_argument("--version", required=True, help="Release version without v.")
    parser.add_argument("--source-sha", required=True, help="Verified source commit.")
    parser.add_argument(
        "--wheel-sha256",
        required=True,
        help="Independently measured wheel SHA-256 digest.",
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path.cwd(),
        help="Repository root. Defaults to the current directory.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    pin = ReleasePin(args.version, args.source_sha, args.wheel_sha256)
    try:
        updated = update_release_pin(args.root, pin)
    except PinUpdateError as exc:
        print(f"update-release-pin: {exc}", file=sys.stderr)
        return 2
    for path in updated:
        print(f"updated {path}")
    return 0


def _update_workflow(content: str, pin: ReleasePin, source: Path) -> str:
    replacements = (
        (
            re.compile(
                r'(?m)^  REPO_SCOUT_VERSION: "[0-9]+\.[0-9]+\.[0-9]+"$'
            ),
            f'  REPO_SCOUT_VERSION: "{pin.version}"',
            "version",
        ),
        (
            re.compile(r"(?m)^  REPO_SCOUT_SOURCE_SHA: [0-9a-f]{40}$"),
            f"  REPO_SCOUT_SOURCE_SHA: {pin.source_sha}",
            "source SHA",
        ),
        (
            re.compile(r"(?m)^  REPO_SCOUT_WHEEL_SHA256: [0-9a-f]{64}$"),
            f"  REPO_SCOUT_WHEEL_SHA256: {pin.wheel_sha256}",
            "wheel SHA-256",
        ),
    )
    return _apply_replacements(content, replacements, source)


def _update_test_contract(content: str, pin: ReleasePin, source: Path) -> str:
    replacements = (
        (
            re.compile(
                r'(?m)^REPO_SCOUT_VERSION = "[0-9]+\.[0-9]+\.[0-9]+"$'
            ),
            f'REPO_SCOUT_VERSION = "{pin.version}"',
            "version",
        ),
        (
            re.compile(r'(?m)^REPO_SCOUT_SOURCE_SHA = "[0-9a-f]{40}"$'),
            f'REPO_SCOUT_SOURCE_SHA = "{pin.source_sha}"',
            "source SHA",
        ),
        (
            re.compile(
                r'REPO_SCOUT_WHEEL_SHA256 = \(\n    "[0-9a-f]{64}"\n\)'
            ),
            (
                "REPO_SCOUT_WHEEL_SHA256 = (\n"
                f'    "{pin.wheel_sha256}"\n'
                ")"
            ),
            "wheel SHA-256",
        ),
    )
    return _apply_replacements(content, replacements, source)


def _apply_replacements(
    content: str,
    replacements: tuple[tuple[re.Pattern[str], str, str], ...],
    source: Path,
) -> str:
    updated = content
    for pattern, replacement, label in replacements:
        updated, count = pattern.subn(replacement, updated)
        if count != 1:
            raise PinUpdateError(
                f"{source} must contain exactly one {label} pin; found {count}"
            )
    return updated


if __name__ == "__main__":
    raise SystemExit(main())
