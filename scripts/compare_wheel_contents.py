#!/usr/bin/env python3
"""Compare the install-relevant contents of two wheel archives."""

from __future__ import annotations

import argparse
from collections import Counter
import hashlib
from pathlib import Path
import sys
from zipfile import BadZipFile, ZipFile, ZipInfo


class WheelComparisonError(ValueError):
    """Raised when wheel archives cannot prove content parity."""


def compare_wheel_contents(reference: Path, rebuilt: Path) -> int:
    """Require matching member names, bytes, and stored Unix mode bits."""
    reference_members = _wheel_members(reference, label="reference wheel")
    rebuilt_members = _wheel_members(rebuilt, label="rebuilt wheel")

    reference_names = set(reference_members)
    rebuilt_names = set(rebuilt_members)
    missing = sorted(reference_names - rebuilt_names)
    unexpected = sorted(rebuilt_names - reference_names)
    if missing or unexpected:
        details = []
        if missing:
            details.append(f"missing members: {_bounded_names(missing)}")
        if unexpected:
            details.append(f"unexpected members: {_bounded_names(unexpected)}")
        raise WheelComparisonError("; ".join(details))

    changed = sorted(
        name
        for name in reference_names
        if reference_members[name] != rebuilt_members[name]
    )
    if changed:
        raise WheelComparisonError(
            f"member content or mode differs: {_bounded_names(changed)}"
        )
    return len(reference_members)


def _wheel_members(
    path: Path,
    *,
    label: str,
) -> dict[str, tuple[int, int, str]]:
    try:
        with ZipFile(path) as archive:
            infos = archive.infolist()
            names = [info.filename for info in infos]
            duplicates = sorted(
                name for name, count in Counter(names).items() if count > 1
            )
            if duplicates:
                raise WheelComparisonError(
                    f"{label} contains duplicate members: "
                    f"{_bounded_names(duplicates)}"
                )
            return {
                info.filename: _member_fingerprint(archive, info)
                for info in infos
            }
    except WheelComparisonError:
        raise
    except (BadZipFile, OSError) as exc:
        raise WheelComparisonError(f"cannot read {label} {path}: {exc}") from exc


def _member_fingerprint(
    archive: ZipFile,
    info: ZipInfo,
) -> tuple[int, int, str]:
    digest = hashlib.sha256()
    with archive.open(info) as member:
        for chunk in iter(lambda: member.read(1024 * 1024), b""):
            digest.update(chunk)
    stored_mode = (info.external_attr >> 16) & 0xFFFF
    return info.file_size, stored_mode, digest.hexdigest()


def _bounded_names(names: list[str], *, limit: int = 10) -> str:
    visible = names[:limit]
    rendered = ", ".join(visible)
    if len(names) > limit:
        rendered += f", ... ({len(names) - limit} more)"
    return rendered


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Compare wheel member paths, bytes, and stored modes while ignoring "
            "archive timestamps, ordering, and compression."
        )
    )
    parser.add_argument("reference_wheel", type=Path)
    parser.add_argument("rebuilt_wheel", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        member_count = compare_wheel_contents(
            args.reference_wheel,
            args.rebuilt_wheel,
        )
    except WheelComparisonError as exc:
        print(f"compare-wheel-contents: {exc}", file=sys.stderr)
        return 2
    print(f"Wheel contents match across {member_count} members.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
