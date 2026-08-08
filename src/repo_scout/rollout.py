from __future__ import annotations

import json
from pathlib import Path
import re
import stat
from typing import Any

from ._file_evidence import (
    FileSizeLimitError,
    StableContentError,
    StablePathError,
    read_stable_regular_file,
)


ROLLOUT_SCHEMA_VERSION = 3
SUPPORTED_ROLLOUT_SCHEMA_VERSIONS = {1, 2, ROLLOUT_SCHEMA_VERSION}
ROLLOUT_METADATA_START = "## Rollout Metadata\n\n```json\n"
ROLLOUT_METADATA_END = "\n```"
MAX_ROLLOUT_EVIDENCE_BYTES = 1024 * 1024
MAX_GIT_BRANCH_CHARACTERS = 1024
MAX_REPOSITORY_ID_CHARACTERS = 128
_POLICY_FINGERPRINT_PATTERN = re.compile(r"sha256:[0-9a-f]{64}")
_GIT_COMMIT_PATTERN = re.compile(r"(?:[0-9a-f]{40}|[0-9a-f]{64})")


class RolloutEvidenceError(ValueError):
    """Raised when rollout evidence is missing, malformed, or inconsistent."""


def build_rollout_metadata(
    snapshot: dict[str, Any], repository_id: str
) -> dict[str, Any]:
    repository_id = validate_repository_id(repository_id)
    policy = snapshot.get("policy")
    if not isinstance(policy, dict):
        raise RolloutEvidenceError("rollout evidence requires evaluated policy data")

    git = snapshot["git"]
    exceptions = policy.get("exceptions")
    schema_version = 3 if exceptions is not None else 2
    policy_passes = (
        exceptions["enforcement_status"] != "fail"
        if exceptions is not None
        else policy["status"] == "pass"
    )
    git_clean = bool(git["is_repo"] and git["dirty_files"] == 0)
    has_commit = git["commit"] is not None
    return {
        "schema_version": schema_version,
        "repository_id": repository_id,
        "readiness": (
            "ready-for-ci"
            if policy_passes and git_clean and has_commit
            else "remediation-required"
        ),
        "policy": {
            "version": policy["version"],
            "fingerprint": policy["fingerprint"],
            "status": policy["status"],
            "rules_checked": policy["rules_checked"],
            "violations": len(policy["violations"]),
            **(
                {
                    "enforcement_status": exceptions["enforcement_status"],
                    "exception_ledger_fingerprint": exceptions["fingerprint"],
                    "exception_decisions_total": (
                        len(exceptions["active"])
                        + len(exceptions["pending"])
                        + len(exceptions["expired"])
                    ),
                    "exception_decisions_applied": len(exceptions["applied"]),
                    "exception_decisions_expired": len(exceptions["expired"]),
                    "exception_decisions_pending": len(exceptions["pending"]),
                    "exception_decisions_stale": len(exceptions["stale"]),
                    "unresolved_violations": len(
                        exceptions["unresolved_violation_ids"]
                    ),
                }
                if exceptions is not None
                else {}
            ),
        },
        "git": {
            "is_repo": git["is_repo"],
            "branch": git["branch"],
            "commit": git["commit"],
            "dirty_files": git["dirty_files"],
            "clean": git_clean,
        },
        "attention_findings": len(snapshot["attention"]["items"]),
    }


def format_rollout_metadata(metadata: dict[str, Any]) -> str:
    validated = validate_rollout_metadata(metadata)
    return json.dumps(validated, indent=2, sort_keys=True)


def _format_operator_text(text: str) -> str:
    return text if text.isprintable() else json.dumps(text)


def format_evidence_source(source: str | Path) -> str:
    return _format_operator_text(str(source))


def load_rollout_metadata(path: str | Path) -> dict[str, Any]:
    requested = Path(path)
    requested_display = format_evidence_source(requested)
    try:
        if "\0" in str(requested):
            raise ValueError("NUL is not allowed")
        source = requested.parent.resolve() / requested.name
        source_details = source.lstat()
    except FileNotFoundError as exc:
        detail = format_evidence_source(str(exc))
        raise RolloutEvidenceError(
            f"could not read {requested_display}: {detail}"
        ) from exc
    except (OSError, RuntimeError, ValueError) as exc:
        detail = format_evidence_source(str(exc))
        raise RolloutEvidenceError(
            "could not inspect rollout evidence path "
            f"{requested_display}: {detail}"
        ) from exc
    if stat.S_ISLNK(source_details.st_mode):
        raise RolloutEvidenceError(
            "rollout evidence path must not be a symlink: "
            f"{requested_display}"
        )
    if not stat.S_ISREG(source_details.st_mode):
        raise RolloutEvidenceError(
            "rollout evidence path must be a regular file: "
            f"{requested_display}"
        )

    try:
        with read_stable_regular_file(
            source,
            source_details,
            max_bytes=MAX_ROLLOUT_EVIDENCE_BYTES,
        ) as content:
            return parse_rollout_metadata(content, source=str(requested))
    except StablePathError as exc:
        raise RolloutEvidenceError(
            "rollout evidence path changed during loading: "
            f"{requested_display}"
        ) from exc
    except StableContentError as exc:
        raise RolloutEvidenceError(
            f"rollout evidence changed during loading: {requested_display}"
        ) from exc
    except FileSizeLimitError as exc:
        raise RolloutEvidenceError(
            "rollout evidence exceeds "
            f"{MAX_ROLLOUT_EVIDENCE_BYTES} bytes: {requested_display}"
        ) from exc
    except (OSError, UnicodeDecodeError) as exc:
        detail = format_evidence_source(str(exc))
        raise RolloutEvidenceError(
            f"could not read {requested_display}: {detail}"
        ) from exc


def parse_rollout_metadata(
    content: str, *, source: str = "<rollout evidence>"
) -> dict[str, Any]:
    source_display = format_evidence_source(source)
    marker_count = content.count(ROLLOUT_METADATA_START)
    if marker_count != 1:
        raise RolloutEvidenceError(
            f"{source_display} must contain exactly one rollout metadata section"
        )

    encoded = content.split(ROLLOUT_METADATA_START, 1)[1]
    end = encoded.find(ROLLOUT_METADATA_END)
    if end < 0:
        raise RolloutEvidenceError(
            f"{source_display} has an unterminated metadata block"
        )
    if encoded[end + len(ROLLOUT_METADATA_END) :].strip():
        raise RolloutEvidenceError(
            f"{source_display} has content after rollout metadata"
        )

    try:
        metadata = json.loads(
            encoded[:end],
            object_pairs_hook=_reject_duplicate_json_keys,
        )
    except json.JSONDecodeError as exc:
        raise RolloutEvidenceError(
            f"invalid rollout metadata JSON in {source_display}: {exc.msg}"
        ) from exc
    except RolloutEvidenceError as exc:
        raise RolloutEvidenceError(
            f"invalid rollout metadata JSON in {source_display}: {exc}"
        ) from exc
    try:
        return validate_rollout_metadata(metadata)
    except RolloutEvidenceError as exc:
        raise RolloutEvidenceError(
            f"invalid rollout metadata in {source_display}: {exc}"
        ) from exc


def validate_rollout_metadata(metadata: Any) -> dict[str, Any]:
    if not isinstance(metadata, dict):
        raise RolloutEvidenceError("metadata must be a JSON object")
    _require_exact_keys(
        metadata,
        {
            "schema_version",
            "repository_id",
            "readiness",
            "policy",
            "git",
            "attention_findings",
        },
        "metadata",
    )

    schema_version = metadata["schema_version"]
    if (
        not isinstance(schema_version, int)
        or isinstance(schema_version, bool)
        or schema_version not in SUPPORTED_ROLLOUT_SCHEMA_VERSIONS
    ):
        raise RolloutEvidenceError("schema_version must be 1, 2, or 3")
    repository_id = validate_repository_id(metadata["repository_id"])
    if metadata["readiness"] not in {"ready-for-ci", "remediation-required"}:
        raise RolloutEvidenceError("readiness is unsupported")

    policy = metadata["policy"]
    if not isinstance(policy, dict):
        raise RolloutEvidenceError("policy must be an object")
    policy_keys = {"version", "status", "rules_checked", "violations"}
    if schema_version >= 2:
        policy_keys.add("fingerprint")
    if schema_version >= 3:
        policy_keys.update(
            {
                "enforcement_status",
                "exception_ledger_fingerprint",
                "exception_decisions_total",
                "exception_decisions_applied",
                "exception_decisions_expired",
                "exception_decisions_pending",
                "exception_decisions_stale",
                "unresolved_violations",
            }
        )
    _require_exact_keys(policy, policy_keys, "policy")
    if not _is_non_negative_integer(policy["version"]) or policy["version"] < 1:
        raise RolloutEvidenceError("policy.version must be positive")
    if policy["status"] not in {"pass", "fail"}:
        raise RolloutEvidenceError("policy.status must be pass or fail")
    if not _is_non_negative_integer(policy["rules_checked"]) or policy[
        "rules_checked"
    ] < 1:
        raise RolloutEvidenceError("policy.rules_checked must be positive")
    if not _is_non_negative_integer(policy["violations"]):
        raise RolloutEvidenceError("policy.violations must be non-negative")
    if policy["status"] == "pass" and policy["violations"] != 0:
        raise RolloutEvidenceError("passing policy cannot contain violations")
    if policy["status"] == "fail" and policy["violations"] < 1:
        raise RolloutEvidenceError("failing policy must contain violations")
    if schema_version >= 2 and (
        not isinstance(policy["fingerprint"], str)
        or _POLICY_FINGERPRINT_PATTERN.fullmatch(policy["fingerprint"]) is None
    ):
        raise RolloutEvidenceError(
            "policy.fingerprint must be a lowercase sha256 digest"
        )
    if schema_version >= 3:
        _validate_policy_exception_evidence(policy)

    git = metadata["git"]
    if not isinstance(git, dict):
        raise RolloutEvidenceError("git must be an object")
    git_keys = {"is_repo", "branch", "dirty_files", "clean"}
    if schema_version >= 2:
        git_keys.add("commit")
    _require_exact_keys(git, git_keys, "git")
    if not isinstance(git["is_repo"], bool) or not isinstance(git["clean"], bool):
        raise RolloutEvidenceError("git repository and clean values must be booleans")
    branch = _validate_git_branch(git["branch"])
    if not git["is_repo"] and branch is not None:
        raise RolloutEvidenceError("non-Git evidence cannot declare a branch")
    if not _is_non_negative_integer(git["dirty_files"]):
        raise RolloutEvidenceError("git.dirty_files must be non-negative")
    if not git["is_repo"] and git["dirty_files"] != 0:
        raise RolloutEvidenceError("non-Git evidence cannot declare changed files")
    if schema_version >= 2:
        commit = git["commit"]
        if commit is not None and (
            not isinstance(commit, str)
            or _GIT_COMMIT_PATTERN.fullmatch(commit) is None
        ):
            raise RolloutEvidenceError(
                "git.commit must be a lowercase 40- or 64-character object ID or null"
            )
        if not git["is_repo"] and commit is not None:
            raise RolloutEvidenceError("non-Git evidence cannot declare a commit")
    expected_clean = git["is_repo"] and git["dirty_files"] == 0
    if git["clean"] != expected_clean:
        raise RolloutEvidenceError("git.clean contradicts repository state")

    attention_findings = metadata["attention_findings"]
    if not _is_non_negative_integer(attention_findings):
        raise RolloutEvidenceError("attention_findings must be non-negative")

    has_required_commit = schema_version == 1 or git["commit"] is not None
    policy_ready = (
        policy["enforcement_status"] != "fail"
        if schema_version >= 3
        else policy["status"] == "pass"
    )
    expected_readiness = (
        "ready-for-ci"
        if policy_ready and git["clean"] and has_required_commit
        else "remediation-required"
    )
    if metadata["readiness"] != expected_readiness:
        raise RolloutEvidenceError("readiness contradicts policy or Git evidence")

    return {
        "schema_version": schema_version,
        "repository_id": repository_id,
        "readiness": metadata["readiness"],
        "policy": {
            "version": policy["version"],
            **(
                {"fingerprint": policy["fingerprint"]}
                if schema_version >= 2
                else {}
            ),
            "status": policy["status"],
            "rules_checked": policy["rules_checked"],
            "violations": policy["violations"],
            **(
                {
                    "enforcement_status": policy["enforcement_status"],
                    "exception_ledger_fingerprint": policy[
                        "exception_ledger_fingerprint"
                    ],
                    "exception_decisions_total": policy[
                        "exception_decisions_total"
                    ],
                    "exception_decisions_applied": policy[
                        "exception_decisions_applied"
                    ],
                    "exception_decisions_expired": policy[
                        "exception_decisions_expired"
                    ],
                    "exception_decisions_pending": policy[
                        "exception_decisions_pending"
                    ],
                    "exception_decisions_stale": policy[
                        "exception_decisions_stale"
                    ],
                    "unresolved_violations": policy["unresolved_violations"],
                }
                if schema_version >= 3
                else {}
            ),
        },
        "git": {
            "is_repo": git["is_repo"],
            "branch": branch,
            **({"commit": git["commit"]} if schema_version >= 2 else {}),
            "dirty_files": git["dirty_files"],
            "clean": git["clean"],
        },
        "attention_findings": attention_findings,
    }


def _validate_policy_exception_evidence(policy: dict[str, Any]) -> None:
    if policy["enforcement_status"] not in {
        "pass",
        "pass-with-exceptions",
        "fail",
    }:
        raise RolloutEvidenceError(
            "policy.enforcement_status must be pass, pass-with-exceptions, or fail"
        )
    ledger_fingerprint = policy["exception_ledger_fingerprint"]
    if (
        not isinstance(ledger_fingerprint, str)
        or _POLICY_FINGERPRINT_PATTERN.fullmatch(ledger_fingerprint) is None
    ):
        raise RolloutEvidenceError(
            "policy.exception_ledger_fingerprint must be a lowercase sha256 digest"
        )

    count_keys = (
        "exception_decisions_total",
        "exception_decisions_applied",
        "exception_decisions_expired",
        "exception_decisions_pending",
        "exception_decisions_stale",
        "unresolved_violations",
    )
    for key in count_keys:
        if not _is_non_negative_integer(policy[key]):
            raise RolloutEvidenceError(f"policy.{key} must be non-negative")

    accounted = (
        policy["exception_decisions_applied"]
        + policy["exception_decisions_expired"]
        + policy["exception_decisions_pending"]
        + policy["exception_decisions_stale"]
    )
    if policy["exception_decisions_total"] != accounted:
        raise RolloutEvidenceError(
            "policy exception decision counts do not reconcile"
        )
    if policy["unresolved_violations"] > policy["violations"]:
        raise RolloutEvidenceError(
            "policy.unresolved_violations cannot exceed raw violations"
        )
    if policy["violations"] != (
        policy["exception_decisions_applied"] + policy["unresolved_violations"]
    ):
        raise RolloutEvidenceError(
            "raw policy violations do not reconcile to applied exceptions and "
            "unresolved violations"
        )

    enforcement_status = policy["enforcement_status"]
    clean_exception_pass = (
        policy["exception_decisions_applied"] > 0
        and policy["exception_decisions_expired"] == 0
        and policy["exception_decisions_pending"] == 0
        and policy["exception_decisions_stale"] == 0
        and policy["unresolved_violations"] == 0
    )
    if enforcement_status == "pass-with-exceptions" and (
        policy["status"] != "fail" or not clean_exception_pass
    ):
        raise RolloutEvidenceError(
            "pass-with-exceptions contradicts policy exception evidence"
        )
    if enforcement_status == "pass" and (
        policy["status"] != "pass"
        or policy["violations"] != 0
        or policy["exception_decisions_total"] != 0
    ):
        raise RolloutEvidenceError("passing enforcement contradicts policy evidence")
    if enforcement_status != "fail" and policy["unresolved_violations"] != 0:
        raise RolloutEvidenceError(
            "non-failing enforcement cannot retain unresolved violations"
        )


def _validate_git_branch(value: Any) -> str | None:
    if value is None:
        return None
    if (
        not isinstance(value, str)
        or not value
        or len(value) > MAX_GIT_BRANCH_CHARACTERS
        or value != value.strip()
        or not value.isprintable()
    ):
        raise RolloutEvidenceError(
            "git.branch must be null or a non-empty printable string "
            f"of at most {MAX_GIT_BRANCH_CHARACTERS} characters without "
            "surrounding whitespace"
        )
    return value


def validate_repository_id(value: Any) -> str:
    if (
        not isinstance(value, str)
        or not value
        or len(value) > MAX_REPOSITORY_ID_CHARACTERS
        or value != value.strip()
        or not value.isprintable()
    ):
        raise RolloutEvidenceError(
            "repository_id must be a non-empty printable string of at most "
            f"{MAX_REPOSITORY_ID_CHARACTERS} characters without surrounding "
            "whitespace"
        )
    return value


def _require_exact_keys(
    values: dict[str, Any], expected: set[str], location: str
) -> None:
    actual = set(values)
    if actual == expected:
        return
    missing = sorted(expected - actual)
    unknown = sorted(actual - expected)
    if missing:
        raise RolloutEvidenceError(f"{location} is missing key: {missing[0]}")
    unknown_display = _format_operator_text(unknown[0])
    raise RolloutEvidenceError(
        f"{location} has unknown key: {unknown_display}"
    )


def _is_non_negative_integer(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def _reject_duplicate_json_keys(
    pairs: list[tuple[str, Any]],
) -> dict[str, Any]:
    values: dict[str, Any] = {}
    for key, value in pairs:
        if key in values:
            raise RolloutEvidenceError(f"duplicate key: {json.dumps(key)}")
        values[key] = value
    return values
