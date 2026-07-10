from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROLLOUT_SCHEMA_VERSION = 1
ROLLOUT_METADATA_START = "## Rollout Metadata\n\n```json\n"
ROLLOUT_METADATA_END = "\n```"


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
    policy_passes = policy["status"] == "pass"
    git_clean = bool(git["is_repo"] and git["dirty_files"] == 0)
    return {
        "schema_version": ROLLOUT_SCHEMA_VERSION,
        "repository_id": repository_id,
        "readiness": (
            "ready-for-ci"
            if policy_passes and git_clean
            else "remediation-required"
        ),
        "policy": {
            "version": policy["version"],
            "status": policy["status"],
            "rules_checked": policy["rules_checked"],
            "violations": len(policy["violations"]),
        },
        "git": {
            "is_repo": git["is_repo"],
            "branch": git["branch"],
            "dirty_files": git["dirty_files"],
            "clean": git_clean,
        },
        "attention_findings": len(snapshot["attention"]["items"]),
    }


def format_rollout_metadata(metadata: dict[str, Any]) -> str:
    validated = validate_rollout_metadata(metadata)
    return json.dumps(validated, indent=2, sort_keys=True)


def load_rollout_metadata(path: str | Path) -> dict[str, Any]:
    source = Path(path)
    try:
        content = source.read_text(encoding="utf-8")
    except OSError as exc:
        raise RolloutEvidenceError(f"could not read {source}: {exc}") from exc
    return parse_rollout_metadata(content, source=str(source))


def parse_rollout_metadata(
    content: str, *, source: str = "<rollout evidence>"
) -> dict[str, Any]:
    marker_count = content.count(ROLLOUT_METADATA_START)
    if marker_count != 1:
        raise RolloutEvidenceError(
            f"{source} must contain exactly one rollout metadata section"
        )

    encoded = content.split(ROLLOUT_METADATA_START, 1)[1]
    end = encoded.find(ROLLOUT_METADATA_END)
    if end < 0:
        raise RolloutEvidenceError(f"{source} has an unterminated metadata block")
    if encoded[end + len(ROLLOUT_METADATA_END) :].strip():
        raise RolloutEvidenceError(f"{source} has content after rollout metadata")

    try:
        metadata = json.loads(
            encoded[:end],
            object_pairs_hook=_reject_duplicate_json_keys,
        )
    except json.JSONDecodeError as exc:
        raise RolloutEvidenceError(
            f"invalid rollout metadata JSON in {source}: {exc.msg}"
        ) from exc
    except RolloutEvidenceError as exc:
        raise RolloutEvidenceError(
            f"invalid rollout metadata JSON in {source}: {exc}"
        ) from exc
    try:
        return validate_rollout_metadata(metadata)
    except RolloutEvidenceError as exc:
        raise RolloutEvidenceError(f"invalid rollout metadata in {source}: {exc}") from exc


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

    if (
        not isinstance(metadata["schema_version"], int)
        or isinstance(metadata["schema_version"], bool)
        or metadata["schema_version"] != ROLLOUT_SCHEMA_VERSION
    ):
        raise RolloutEvidenceError(
            f"schema_version must be {ROLLOUT_SCHEMA_VERSION}"
        )
    repository_id = validate_repository_id(metadata["repository_id"])
    if metadata["readiness"] not in {"ready-for-ci", "remediation-required"}:
        raise RolloutEvidenceError("readiness is unsupported")

    policy = metadata["policy"]
    if not isinstance(policy, dict):
        raise RolloutEvidenceError("policy must be an object")
    _require_exact_keys(
        policy,
        {"version", "status", "rules_checked", "violations"},
        "policy",
    )
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

    git = metadata["git"]
    if not isinstance(git, dict):
        raise RolloutEvidenceError("git must be an object")
    _require_exact_keys(
        git,
        {"is_repo", "branch", "dirty_files", "clean"},
        "git",
    )
    if not isinstance(git["is_repo"], bool) or not isinstance(git["clean"], bool):
        raise RolloutEvidenceError("git repository and clean values must be booleans")
    if git["branch"] is not None and not isinstance(git["branch"], str):
        raise RolloutEvidenceError("git.branch must be a string or null")
    if not git["is_repo"] and git["branch"] is not None:
        raise RolloutEvidenceError("non-Git evidence cannot declare a branch")
    if not _is_non_negative_integer(git["dirty_files"]):
        raise RolloutEvidenceError("git.dirty_files must be non-negative")
    if not git["is_repo"] and git["dirty_files"] != 0:
        raise RolloutEvidenceError("non-Git evidence cannot declare changed files")
    expected_clean = git["is_repo"] and git["dirty_files"] == 0
    if git["clean"] != expected_clean:
        raise RolloutEvidenceError("git.clean contradicts repository state")

    attention_findings = metadata["attention_findings"]
    if not _is_non_negative_integer(attention_findings):
        raise RolloutEvidenceError("attention_findings must be non-negative")

    expected_readiness = (
        "ready-for-ci"
        if policy["status"] == "pass" and git["clean"]
        else "remediation-required"
    )
    if metadata["readiness"] != expected_readiness:
        raise RolloutEvidenceError("readiness contradicts policy or Git evidence")

    return {
        "schema_version": ROLLOUT_SCHEMA_VERSION,
        "repository_id": repository_id,
        "readiness": metadata["readiness"],
        "policy": {
            "version": policy["version"],
            "status": policy["status"],
            "rules_checked": policy["rules_checked"],
            "violations": policy["violations"],
        },
        "git": {
            "is_repo": git["is_repo"],
            "branch": git["branch"],
            "dirty_files": git["dirty_files"],
            "clean": git["clean"],
        },
        "attention_findings": attention_findings,
    }


def validate_repository_id(value: Any) -> str:
    if not isinstance(value, str) or not value:
        raise RolloutEvidenceError("repository_id must be a non-empty string")
    if value != value.strip():
        raise RolloutEvidenceError("repository_id cannot have surrounding whitespace")
    if len(value) > 128:
        raise RolloutEvidenceError("repository_id cannot exceed 128 characters")
    if any(ord(character) < 32 or ord(character) == 127 for character in value):
        raise RolloutEvidenceError("repository_id cannot contain control characters")
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
    raise RolloutEvidenceError(f"{location} has unknown key: {unknown[0]}")


def _is_non_negative_integer(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def _reject_duplicate_json_keys(
    pairs: list[tuple[str, Any]],
) -> dict[str, Any]:
    values: dict[str, Any] = {}
    for key, value in pairs:
        if key in values:
            raise RolloutEvidenceError(f"duplicate key: {key}")
        values[key] = value
    return values
