from __future__ import annotations

from datetime import date, datetime, timezone
import hashlib
import json
from pathlib import Path
import stat
import subprocess
import tomllib
from typing import Any

from ._file_evidence import (
    FileSizeLimitError,
    StableContentError,
    StablePathError,
    read_stable_regular_file,
)
from .rollout import format_evidence_source, validate_repository_id


EXCEPTION_LEDGER_VERSION = 1
MAX_EXCEPTION_LEDGER_BYTES = 128 * 1024
MAX_EXCEPTION_ID_CHARACTERS = 64
MAX_EXCEPTION_ACTOR_CHARACTERS = 128
MAX_EXCEPTION_REASON_CHARACTERS = 1024
MAX_EXCEPTION_DURATION_DAYS = 366
_DIGEST_PREFIX = "sha256:"
_DIGEST_CHARACTERS = 64
_ROOT_KEYS = {"version", "repository_id", "policy_fingerprint", "exceptions"}
_EXCEPTION_KEYS = {
    "id",
    "violation_id",
    "owner",
    "approved_by",
    "reason",
    "approved_on",
    "expires_on",
}


class PolicyExceptionError(ValueError):
    """Raised when policy exception evidence is unsafe or inconsistent."""


def load_exception_ledger(path: str | Path) -> dict[str, Any]:
    requested = Path(path).expanduser()
    requested_display = format_evidence_source(requested)
    try:
        if "\0" in str(requested):
            raise ValueError("NUL is not allowed")
        source = requested.parent.resolve() / requested.name
        source_details = source.lstat()
    except FileNotFoundError as exc:
        raise PolicyExceptionError(
            f"exception ledger does not exist: {requested_display}"
        ) from exc
    except (OSError, RuntimeError, ValueError) as exc:
        detail = format_evidence_source(str(exc))
        raise PolicyExceptionError(
            f"could not inspect exception ledger {requested_display}: {detail}"
        ) from exc

    if stat.S_ISLNK(source_details.st_mode):
        raise PolicyExceptionError(
            f"exception ledger must not be a symlink: {requested_display}"
        )
    if not stat.S_ISREG(source_details.st_mode):
        raise PolicyExceptionError(
            f"exception ledger must be a regular file: {requested_display}"
        )

    try:
        with read_stable_regular_file(
            source,
            source_details,
            max_bytes=MAX_EXCEPTION_LEDGER_BYTES,
        ) as content:
            return parse_exception_ledger(content, source=str(source))
    except StablePathError as exc:
        raise PolicyExceptionError(
            f"exception ledger path changed during loading: {requested_display}"
        ) from exc
    except StableContentError as exc:
        raise PolicyExceptionError(
            f"exception ledger changed during loading: {requested_display}"
        ) from exc
    except FileSizeLimitError as exc:
        raise PolicyExceptionError(
            "exception ledger exceeds "
            f"{MAX_EXCEPTION_LEDGER_BYTES} bytes: {requested_display}"
        ) from exc
    except (OSError, UnicodeDecodeError) as exc:
        detail = format_evidence_source(str(exc))
        raise PolicyExceptionError(
            f"could not read exception ledger {requested_display}: {detail}"
        ) from exc


def parse_exception_ledger(
    content: str, *, source: str = "<exception ledger>"
) -> dict[str, Any]:
    source_display = format_evidence_source(source)
    try:
        ledger = tomllib.loads(content)
    except tomllib.TOMLDecodeError as exc:
        raise PolicyExceptionError(
            f"invalid TOML in exception ledger {source_display}: {exc}"
        ) from exc
    return _validate_exception_ledger(ledger, source)


def exception_ledger_fingerprint(ledger: dict[str, Any]) -> str:
    canonical_exceptions = []
    for record in sorted(ledger["exceptions"], key=lambda item: item["id"]):
        canonical_exceptions.append(
            {
                **record,
                "approved_on": record["approved_on"].isoformat(),
                "expires_on": record["expires_on"].isoformat(),
            }
        )
    canonical = json.dumps(
        {
            "version": ledger["version"],
            "repository_id": ledger["repository_id"],
            "policy_fingerprint": ledger["policy_fingerprint"],
            "exceptions": canonical_exceptions,
        },
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return f"sha256:{hashlib.sha256(canonical).hexdigest()}"


def apply_policy_exceptions(
    policy_result: dict[str, Any],
    ledger: dict[str, Any],
    *,
    repository_id: str,
    evaluated_on: date | None = None,
) -> dict[str, Any]:
    repository_id = validate_repository_id(repository_id)
    if ledger["repository_id"] != repository_id:
        raise PolicyExceptionError(
            "exception ledger repository_id does not match --repository-id"
        )

    policy_fingerprint = policy_result["fingerprint"]
    if ledger["policy_fingerprint"] != policy_fingerprint:
        raise PolicyExceptionError(
            "exception ledger policy fingerprint does not match evaluated policy"
        )

    if evaluated_on is None:
        evaluated_on = datetime.now(timezone.utc).date()
    if type(evaluated_on) is not date:
        raise PolicyExceptionError("evaluated_on must be a calendar date")

    active: list[dict[str, Any]] = []
    pending: list[dict[str, Any]] = []
    expired: list[dict[str, Any]] = []
    for record in ledger["exceptions"]:
        if evaluated_on < record["approved_on"]:
            pending.append(record)
        elif evaluated_on > record["expires_on"]:
            expired.append(record)
        else:
            active.append(record)

    violations_by_id = dict(
        zip(policy_result["violation_ids"], policy_result["violations"], strict=True)
    )
    active_by_violation = {record["violation_id"]: record for record in active}
    applied: list[dict[str, Any]] = []
    unresolved_violation_ids: list[str] = []
    for violation_id, violation in zip(
        policy_result["violation_ids"], policy_result["violations"], strict=True
    ):
        record = active_by_violation.get(violation_id)
        if record is None:
            unresolved_violation_ids.append(violation_id)
            continue
        applied.append(
            {
                "violation_id": violation_id,
                "violation": violation,
                "exception": _serialize_record(record),
            }
        )

    stale = [
        record
        for record in active
        if record["violation_id"] not in violations_by_id
    ]
    if (
        unresolved_violation_ids
        or expired
        or pending
        or stale
    ):
        enforcement_status = "fail"
    elif applied:
        enforcement_status = "pass-with-exceptions"
    else:
        enforcement_status = "pass"

    result = dict(policy_result)
    result["exceptions"] = {
        "version": ledger["version"],
        "source": ledger["source"],
        "repository_id": ledger["repository_id"],
        "fingerprint": exception_ledger_fingerprint(ledger),
        "evaluated_on": evaluated_on.isoformat(),
        "enforcement_status": enforcement_status,
        "active": [_serialize_record(record) for record in active],
        "applied": applied,
        "pending": [_serialize_record(record) for record in pending],
        "expired": [_serialize_record(record) for record in expired],
        "stale": [_serialize_record(record) for record in stale],
        "unresolved_violation_ids": unresolved_violation_ids,
    }
    return result


def verify_exception_ledger_checkout(
    repository_root: str | Path,
    ledger: dict[str, Any],
    snapshot: dict[str, Any],
) -> None:
    root = Path(repository_root).resolve()
    source = Path(ledger["source"]).resolve()
    try:
        relative_source = source.relative_to(root)
    except ValueError as exc:
        raise PolicyExceptionError(
            "exception ledger must be inside the scanned repository"
        ) from exc

    git = snapshot["git"]
    if not git["is_repo"] or git["commit"] is None:
        raise PolicyExceptionError(
            "exception ledger requires a Git repository with an initial commit"
        )
    if git["dirty_files"] != 0:
        raise PolicyExceptionError(
            "exception ledger requires a clean Git worktree"
        )
    try:
        completed = subprocess.run(
            [
                "git",
                "-C",
                str(root),
                "ls-files",
                "--error-unmatch",
                "--",
                relative_source.as_posix(),
            ],
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError as exc:
        raise PolicyExceptionError(
            "could not verify that the exception ledger is tracked by Git"
        ) from exc
    if completed.returncode != 0:
        raise PolicyExceptionError(
            "exception ledger must be tracked by Git"
        )
    try:
        tracked = subprocess.run(
            [
                "git",
                "-C",
                str(root),
                "show",
                f":{relative_source.as_posix()}",
            ],
            check=False,
            capture_output=True,
            text=True,
        )
    except (OSError, UnicodeDecodeError) as exc:
        raise PolicyExceptionError(
            "could not read tracked exception ledger evidence"
        ) from exc
    if tracked.returncode != 0:
        raise PolicyExceptionError("could not read tracked exception ledger evidence")
    try:
        tracked_ledger = parse_exception_ledger(
            tracked.stdout, source=f":{relative_source.as_posix()}"
        )
    except PolicyExceptionError as exc:
        raise PolicyExceptionError(
            "tracked exception ledger evidence is invalid"
        ) from exc
    if exception_ledger_fingerprint(tracked_ledger) != exception_ledger_fingerprint(
        ledger
    ):
        raise PolicyExceptionError(
            "loaded exception ledger does not match tracked Git evidence"
        )


def _validate_exception_ledger(ledger: Any, source: str) -> dict[str, Any]:
    source_display = format_evidence_source(source)
    if not isinstance(ledger, dict):
        raise PolicyExceptionError(
            f"exception ledger must be a TOML table: {source_display}"
        )
    _require_exact_keys(ledger, _ROOT_KEYS, "exception ledger")
    if (
        not isinstance(ledger["version"], int)
        or isinstance(ledger["version"], bool)
        or ledger["version"] != EXCEPTION_LEDGER_VERSION
    ):
        raise PolicyExceptionError(
            f"exception ledger version must be 1: {source_display}"
        )
    try:
        repository_id = validate_repository_id(ledger["repository_id"])
    except ValueError as exc:
        raise PolicyExceptionError(str(exc)) from exc
    policy_fingerprint = _digest(
        ledger["policy_fingerprint"], field="exception ledger policy_fingerprint"
    )

    records = ledger["exceptions"]
    if not isinstance(records, list) or not records:
        raise PolicyExceptionError(
            f"exceptions must be a non-empty array of tables: {source_display}"
        )

    normalized: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    seen_violations: set[str] = set()
    for index, record in enumerate(records):
        if not isinstance(record, dict):
            raise PolicyExceptionError(
                f"exceptions[{index}] must be a table: {source_display}"
            )
        _require_exact_keys(record, _EXCEPTION_KEYS, f"exceptions[{index}]")
        exception_id = _bounded_text(
            record["id"],
            field=f"exceptions[{index}].id",
            max_characters=MAX_EXCEPTION_ID_CHARACTERS,
        )
        if exception_id in seen_ids:
            raise PolicyExceptionError(f"duplicate exception id: {exception_id}")
        seen_ids.add(exception_id)

        violation_id = _digest(
            record["violation_id"],
            field=f"exceptions[{index}].violation_id",
        )
        if violation_id in seen_violations:
            raise PolicyExceptionError(
                f"duplicate exception for violation: {violation_id}"
            )
        seen_violations.add(violation_id)

        approved_on = _calendar_date(
            record["approved_on"], field=f"exceptions[{index}].approved_on"
        )
        expires_on = _calendar_date(
            record["expires_on"], field=f"exceptions[{index}].expires_on"
        )
        duration = (expires_on - approved_on).days
        if duration < 0:
            raise PolicyExceptionError(
                f"exceptions[{index}].expires_on cannot precede approved_on"
            )
        if duration > MAX_EXCEPTION_DURATION_DAYS:
            raise PolicyExceptionError(
                f"exceptions[{index}] duration cannot exceed "
                f"{MAX_EXCEPTION_DURATION_DAYS} days"
            )

        normalized.append(
            {
                "id": exception_id,
                "violation_id": violation_id,
                "owner": _bounded_text(
                    record["owner"],
                    field=f"exceptions[{index}].owner",
                    max_characters=MAX_EXCEPTION_ACTOR_CHARACTERS,
                ),
                "approved_by": _bounded_text(
                    record["approved_by"],
                    field=f"exceptions[{index}].approved_by",
                    max_characters=MAX_EXCEPTION_ACTOR_CHARACTERS,
                ),
                "reason": _bounded_text(
                    record["reason"],
                    field=f"exceptions[{index}].reason",
                    max_characters=MAX_EXCEPTION_REASON_CHARACTERS,
                ),
                "approved_on": approved_on,
                "expires_on": expires_on,
            }
        )

    return {
        "version": EXCEPTION_LEDGER_VERSION,
        "source": source,
        "repository_id": repository_id,
        "policy_fingerprint": policy_fingerprint,
        "exceptions": normalized,
    }


def _require_exact_keys(
    values: dict[str, Any], expected: set[str], context: str
) -> None:
    unknown = sorted(set(values) - expected)
    if unknown:
        raise PolicyExceptionError(f"unknown {context} key: {unknown[0]}")
    missing = sorted(expected - set(values))
    if missing:
        raise PolicyExceptionError(f"missing {context} key: {missing[0]}")


def _bounded_text(value: Any, *, field: str, max_characters: int) -> str:
    if (
        not isinstance(value, str)
        or not value
        or value != value.strip()
        or not value.isprintable()
        or len(value) > max_characters
    ):
        raise PolicyExceptionError(
            f"{field} must be a non-empty printable string of at most "
            f"{max_characters} characters without surrounding whitespace"
        )
    return value


def _digest(value: Any, *, field: str) -> str:
    if (
        not isinstance(value, str)
        or not value.startswith(_DIGEST_PREFIX)
        or len(value) != len(_DIGEST_PREFIX) + _DIGEST_CHARACTERS
        or any(character not in "0123456789abcdef" for character in value[7:])
    ):
        raise PolicyExceptionError(f"{field} must be a lowercase sha256 digest")
    return value


def _calendar_date(value: Any, *, field: str) -> date:
    if type(value) is not date:
        raise PolicyExceptionError(f"{field} must be a TOML local date")
    return value


def _serialize_record(record: dict[str, Any]) -> dict[str, Any]:
    return {
        **record,
        "approved_on": record["approved_on"].isoformat(),
        "expires_on": record["expires_on"].isoformat(),
    }
