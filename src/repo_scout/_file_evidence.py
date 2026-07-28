from __future__ import annotations

from contextlib import contextmanager
import os
from pathlib import Path
import stat
from typing import Iterator


class StablePathError(RuntimeError):
    """Raised when an inspected regular-file leaf changes during one read."""


class StableContentError(RuntimeError):
    """Raised when an opened regular file changes during one read."""


@contextmanager
def read_stable_regular_file(
    target: Path,
    expected_details: os.stat_result,
) -> Iterator[str]:
    flags = os.O_RDONLY
    for flag_name in ("O_BINARY", "O_CLOEXEC", "O_NOFOLLOW", "O_NONBLOCK"):
        flags |= getattr(os, flag_name, 0)

    descriptor: int | None = None
    try:
        try:
            descriptor = os.open(target, flags)
        except OSError as exc:
            if not _regular_path_matches(target, expected_details):
                raise StablePathError from exc
            raise

        os.set_inheritable(descriptor, False)
        opened_details = os.fstat(descriptor)
        if (
            not stat.S_ISREG(opened_details.st_mode)
            or not os.path.samestat(expected_details, opened_details)
        ):
            raise StablePathError
        original_content = _read_descriptor_bytes(descriptor)
        yield original_content.decode("utf-8")
        os.lseek(descriptor, 0, os.SEEK_SET)
        if _read_descriptor_bytes(descriptor) != original_content:
            raise StableContentError
        if not _regular_path_matches(target, opened_details):
            raise StablePathError
    finally:
        if descriptor is not None:
            os.close(descriptor)


def _read_descriptor_bytes(descriptor: int) -> bytes:
    chunks: list[bytes] = []
    while True:
        chunk = os.read(descriptor, 65536)
        if not chunk:
            break
        chunks.append(chunk)
    return b"".join(chunks)


def _regular_path_matches(
    target: Path,
    expected_details: os.stat_result,
) -> bool:
    try:
        current_details = target.lstat()
    except OSError:
        return False
    return stat.S_ISREG(current_details.st_mode) and os.path.samestat(
        expected_details,
        current_details,
    )
