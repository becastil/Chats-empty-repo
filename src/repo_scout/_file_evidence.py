from __future__ import annotations

from contextlib import contextmanager
import os
from pathlib import Path
import stat
from typing import Iterator


_READ_CHUNK_BYTES = 64 * 1024


class StablePathError(RuntimeError):
    """Raised when an inspected regular-file leaf changes during one read."""


class StableContentError(RuntimeError):
    """Raised when an opened regular file changes during one read."""


class FileSizeLimitError(RuntimeError):
    """Raised when an opened regular file exceeds its read ceiling."""


@contextmanager
def read_stable_regular_file(
    target: Path,
    expected_details: os.stat_result,
    *,
    max_bytes: int,
) -> Iterator[str]:
    if max_bytes < 1:
        raise ValueError("max_bytes must be positive")

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
        if opened_details.st_size > max_bytes:
            raise FileSizeLimitError
        original_content = _read_descriptor_bytes(
            descriptor,
            max_bytes=max_bytes,
        )
        yield original_content.decode("utf-8")
        os.lseek(descriptor, 0, os.SEEK_SET)
        try:
            accepted_content = _read_descriptor_bytes(
                descriptor,
                max_bytes=max_bytes,
            )
        except FileSizeLimitError as exc:
            raise StableContentError from exc
        if accepted_content != original_content:
            raise StableContentError
        if not _regular_path_matches(target, opened_details):
            raise StablePathError
    finally:
        if descriptor is not None:
            os.close(descriptor)


def _read_descriptor_bytes(
    descriptor: int,
    *,
    max_bytes: int,
) -> bytes:
    chunks: list[bytes] = []
    total = 0
    while True:
        chunk = os.read(
            descriptor,
            min(_READ_CHUNK_BYTES, max_bytes - total + 1),
        )
        if not chunk:
            break
        total += len(chunk)
        if total > max_bytes:
            raise FileSizeLimitError
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
