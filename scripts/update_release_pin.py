from __future__ import annotations

import argparse
from dataclasses import dataclass
import os
from pathlib import Path
import re
import sys
from tempfile import NamedTemporaryFile
from typing import Iterable, Sequence


README_PATH = Path("README.md")
TEST_CONTRACT_PATH = Path("tests/test_ci_examples.py")
TARGETS = (
    Path(".github/workflows/repo-scout-policy.yml"),
    Path("examples/github-actions/repo-scout-policy.yml"),
    README_PATH,
    TEST_CONTRACT_PATH,
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
    originals: dict[Path, tuple[str, int]] = {}

    for relative_path in TARGETS:
        target = project_root / relative_path
        try:
            content = target.read_text(encoding="utf-8")
            mode = target.stat().st_mode
        except OSError as exc:
            raise PinUpdateError(f"could not read {relative_path}: {exc}") from exc
        originals[target] = (content, mode)
        if relative_path == README_PATH:
            prepared[target] = _update_readme(content, pin, relative_path)
        elif relative_path == TEST_CONTRACT_PATH:
            prepared[target] = _update_test_contract(content, pin, relative_path)
        else:
            prepared[target] = _update_workflow(content, pin, relative_path)

    update_paths: dict[Path, Path] = {}
    rollback_paths: dict[Path, Path] = {}
    replaced: list[Path] = []
    try:
        for target, content in prepared.items():
            original, mode = originals[target]
            update_paths[target] = _write_temporary(
                target, content, mode, "pin-update"
            )
            rollback_paths[target] = _write_temporary(
                target, original, mode, "pin-rollback"
            )
        for target in prepared:
            os.replace(update_paths[target], target)
            replaced.append(target)
    except OSError as exc:
        rollback_failures: list[tuple[Path, Path, OSError]] = []
        for target in reversed(replaced):
            rollback_path = rollback_paths[target]
            try:
                os.replace(rollback_path, target)
            except OSError as rollback_exc:
                rollback_failures.append((target, rollback_path, rollback_exc))

        _remove_temporaries(update_paths.values())
        failed_rollback_paths = {path for _, path, _ in rollback_failures}
        _remove_temporaries(
            path
            for path in rollback_paths.values()
            if path not in failed_rollback_paths
        )

        message = f"could not write verified release pin: {exc}"
        if rollback_failures:
            recoveries = ", ".join(
                f"{target} (original retained at {path}: {rollback_exc})"
                for target, path, rollback_exc in rollback_failures
            )
            message = f"{message}; rollback incomplete for {recoveries}"
        elif replaced:
            message = f"{message}; rolled back {len(replaced)} updated target(s)"
        raise PinUpdateError(message) from exc

    _remove_temporaries(update_paths.values())
    _remove_temporaries(rollback_paths.values())

    return TARGETS


def _write_temporary(target: Path, content: str, mode: int, label: str) -> Path:
    temporary_path: Path | None = None
    try:
        with NamedTemporaryFile(
            "w",
            encoding="utf-8",
            dir=target.parent,
            prefix=f".{target.name}.{label}.",
            delete=False,
        ) as temporary:
            temporary_path = Path(temporary.name)
            temporary.write(content)
        assert temporary_path is not None
        os.chmod(temporary_path, mode)
    except OSError:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)
        raise
    assert temporary_path is not None
    return temporary_path


def _remove_temporaries(paths: Iterable[Path]) -> None:
    for path in paths:
        path.unlink(missing_ok=True)


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


def _update_readme(content: str, pin: ReleasePin, source: Path) -> str:
    replacements = (
        (
            re.compile(
                r"(?m)^evidence, and a downloadable schema-2 rollout bundle\. "
                r"It installs the `v[0-9]+\.[0-9]+\.[0-9]+`$"
            ),
            (
                "evidence, and a downloadable schema-2 rollout bundle. "
                f"It installs the `v{pin.version}`"
            ),
            "verified CI version",
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
