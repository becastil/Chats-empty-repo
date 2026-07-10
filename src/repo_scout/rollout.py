from __future__ import annotations

import json
from pathlib import Path
import re
from typing import Any


ROLLOUT_SCHEMA_VERSION = 2
SUPPORTED_ROLLOUT_SCHEMA_VERSIONS = {1, ROLLOUT_SCHEMA_VERSION}
ROLLOUT_METADATA_START = "## Rollout Metadata\n\n```json\n"
ROLLOUT_METADATA_END = "\n```"
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
    policy_passes = policy["status"] == "pass"
    git_clean = bool(git["is_repo"] and git["dirty_files"] == 0)
    has_commit = git["commit"] is not None
    return {
        "schema_version": ROLLOUT_SCHEMA_VERSION,
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

    schema_version = metadata["schema_version"]
    if (
        not isinstance(schema_version, int)
        or isinstance(schema_version, bool)
        or schema_version not in SUPPORTED_ROLLOUT_SCHEMA_VERSIONS
    ):
        raise RolloutEvidenceError("schema_version must be 1 or 2")
    repository_id = validate_repository_id(metadata["repository_id"])
    if metadata["readiness"] not in {"ready-for-ci", "remediation-required"}:
        raise RolloutEvidenceError("readiness is unsupported")

    policy = metadata["policy"]
    if not isinstance(policy, dict):
        raise RolloutEvidenceError("policy must be an object")
    policy_keys = {"version", "status", "rules_checked", "violations"}
    if schema_version >= 2:
        policy_keys.add("fingerprint")
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

    git = metadata["git"]
    if not isinstance(git, dict):
        raise RolloutEvidenceError("git must be an object")
    git_keys = {"is_repo", "branch", "dirty_files", "clean"}
    if schema_version >= 2:
        git_keys.add("commit")
    _require_exact_keys(git, git_keys, "git")
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
    expected_readiness = (
        "ready-for-ci"
        if policy["status"] == "pass" and git["clean"] and has_required_commit
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
        },
        "git": {
            "is_repo": git["is_repo"],
            "branch": git["branch"],
            **({"commit": git["commit"]} if schema_version >= 2 else {}),
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
