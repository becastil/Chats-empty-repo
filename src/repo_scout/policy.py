from __future__ import annotations

import hashlib
import json
from pathlib import Path, PurePosixPath
import subprocess
import tomllib
from typing import Any


POLICY_VERSION = 4
SUPPORTED_POLICY_VERSIONS = (1, 2, 3, POLICY_VERSION)
MAX_FORBIDDEN_PATTERN_PATHS = 20

_ROOT_KEYS = {"version", "repository"}
_REPOSITORY_KEYS_V1 = {
    "required_files",
    "max_files",
    "max_total_bytes",
    "require_clean_git",
}
_REPOSITORY_KEYS_V2 = _REPOSITORY_KEYS_V1 | {"forbidden_files"}
_REPOSITORY_KEYS_V3 = _REPOSITORY_KEYS_V2 | {"forbidden_file_patterns"}
_REPOSITORY_KEYS_V4 = _REPOSITORY_KEYS_V3 | {"required_file_groups"}


class PolicyError(ValueError):
    """Raised when a team policy cannot be read or validated."""


def load_policy(path: str | Path) -> dict[str, Any]:
    source = Path(path).expanduser().resolve()
    try:
        with source.open("rb") as policy_file:
            policy = tomllib.load(policy_file)
    except FileNotFoundError as exc:
        raise PolicyError(f"policy file does not exist: {source}") from exc
    except OSError as exc:
        raise PolicyError(f"could not read policy file {source}: {exc}") from exc
    except tomllib.TOMLDecodeError as exc:
        raise PolicyError(f"invalid TOML in policy file {source}: {exc}") from exc

    return _validate_policy(policy, source)


def parse_policy(content: str, source: str = "<policy>") -> dict[str, Any]:
    try:
        policy = tomllib.loads(content)
    except tomllib.TOMLDecodeError as exc:
        raise PolicyError(f"invalid TOML in {source}: {exc}") from exc
    return _validate_policy(policy, source)


def evaluate_policy(
    snapshot: dict[str, Any], policy: dict[str, Any]
) -> dict[str, Any]:
    rules = policy["repository"]
    root = Path(snapshot["root"])
    violations: list[dict[str, Any]] = []

    for required_file in rules.get("required_files", []):
        if not (root / required_file).is_file():
            violations.append(
                {
                    "rule": "repository.required_files",
                    "path": required_file,
                    "message": f"Required file is missing: {required_file}.",
                }
            )

    for required_group in rules.get("required_file_groups", []):
        if not any((root / candidate).is_file() for candidate in required_group):
            detail = ", ".join(required_group)
            violations.append(
                {
                    "rule": "repository.required_file_groups",
                    "paths": required_group,
                    "message": f"Required file group has no present file: {detail}.",
                }
            )

    for forbidden_file in rules.get("forbidden_files", []):
        if _forbidden_file_exists(snapshot, root, forbidden_file):
            violations.append(
                {
                    "rule": "repository.forbidden_files",
                    "path": forbidden_file,
                    "message": f"Forbidden file is present: {forbidden_file}.",
                }
            )

    forbidden_patterns = rules.get("forbidden_file_patterns", [])
    if forbidden_patterns:
        visible_paths = _policy_visible_paths(snapshot, root)
        for pattern in forbidden_patterns:
            matched_paths = [
                path
                for path in visible_paths
                if _matches_file_pattern(path, pattern)
            ]
            if not matched_paths:
                continue
            shown_paths = matched_paths[:MAX_FORBIDDEN_PATTERN_PATHS]
            truncated = len(matched_paths) > len(shown_paths)
            detail = ", ".join(shown_paths)
            if truncated:
                detail += f", and {len(matched_paths) - len(shown_paths)} more"
            violations.append(
                {
                    "rule": "repository.forbidden_file_patterns",
                    "pattern": pattern,
                    "paths": shown_paths,
                    "match_count": len(matched_paths),
                    "paths_truncated": truncated,
                    "message": (
                        f"Forbidden file pattern {pattern} matched "
                        f"{len(matched_paths)} file(s): {detail}."
                    ),
                }
            )

    max_files = rules.get("max_files")
    file_count = snapshot["files"]["total"]
    if max_files is not None and file_count > max_files:
        violations.append(
            {
                "rule": "repository.max_files",
                "actual": file_count,
                "expected_max": max_files,
                "message": f"Repository has {file_count} files; policy allows {max_files}.",
            }
        )

    max_total_bytes = rules.get("max_total_bytes")
    total_bytes = snapshot["files"]["total_bytes"]
    if max_total_bytes is not None and total_bytes > max_total_bytes:
        violations.append(
            {
                "rule": "repository.max_total_bytes",
                "actual": total_bytes,
                "expected_max": max_total_bytes,
                "message": (
                    f"Repository contains {total_bytes} bytes; "
                    f"policy allows {max_total_bytes}."
                ),
            }
        )

    if rules.get("require_clean_git"):
        git = snapshot["git"]
        if not git["is_repo"]:
            violations.append(
                {
                    "rule": "repository.require_clean_git",
                    "message": "Repository must be a Git repository.",
                }
            )
        elif git["dirty_files"]:
            violations.append(
                {
                    "rule": "repository.require_clean_git",
                    "actual": git["dirty_files"],
                    "expected": 0,
                    "message": (
                        f"Git has {git['dirty_files']} changed files; policy requires 0."
                    ),
                }
            )

    return {
        "version": policy["version"],
        "source": policy["source"],
        "fingerprint": policy_fingerprint(policy),
        "status": "fail" if violations else "pass",
        "rules_checked": len(rules),
        "violations": violations,
    }


def policy_fingerprint(policy: dict[str, Any]) -> str:
    """Return a stable identity for the policy's enforced semantics."""
    repository = dict(policy["repository"])
    for key in (
        "required_files",
        "forbidden_files",
        "forbidden_file_patterns",
    ):
        if key in repository:
            repository[key] = sorted(repository[key])
    if "required_file_groups" in repository:
        repository["required_file_groups"] = sorted(
            sorted(group) for group in repository["required_file_groups"]
        )
    if repository.get("require_clean_git") is False:
        del repository["require_clean_git"]
    canonical = json.dumps(
        {"version": policy["version"], "repository": repository},
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return f"sha256:{hashlib.sha256(canonical).hexdigest()}"


def _validate_policy(policy: Any, source: str | Path) -> dict[str, Any]:
    if not isinstance(policy, dict):
        raise PolicyError(f"policy must be a TOML table: {source}")

    _reject_unknown_keys(policy, _ROOT_KEYS, "policy")
    version = policy.get("version")
    if not _is_integer(version) or version not in SUPPORTED_POLICY_VERSIONS:
        raise PolicyError(
            "policy version must be 1, 2, 3, or 4: "
            f"{source}"
        )

    repository = policy.get("repository")
    if not isinstance(repository, dict):
        raise PolicyError(f"policy must define a [repository] table: {source}")
    if not repository:
        raise PolicyError(f"[repository] must define at least one rule: {source}")

    repository_keys = {
        1: _REPOSITORY_KEYS_V1,
        2: _REPOSITORY_KEYS_V2,
        3: _REPOSITORY_KEYS_V3,
        4: _REPOSITORY_KEYS_V4,
    }[version]
    _reject_unknown_keys(repository, repository_keys, "repository")
    normalized: dict[str, Any] = {}

    for key in ("required_files", "forbidden_files"):
        if key in repository:
            normalized[key] = _validate_file_paths(repository[key], source, key)

    if "forbidden_file_patterns" in repository:
        normalized["forbidden_file_patterns"] = _validate_file_patterns(
            repository["forbidden_file_patterns"], source
        )

    if "required_file_groups" in repository:
        normalized["required_file_groups"] = _validate_file_groups(
            repository["required_file_groups"], source
        )

    overlap = set(normalized.get("required_files", [])) & set(
        normalized.get("forbidden_files", [])
    )
    if overlap:
        path = sorted(overlap)[0]
        raise PolicyError(f"repository path is both required and forbidden: {path}")

    required_files = set(normalized.get("required_files", []))
    forbidden_files = set(normalized.get("forbidden_files", []))
    for group in normalized.get("required_file_groups", []):
        for candidate in group:
            if candidate in required_files:
                raise PolicyError(
                    f"required file group duplicates required path: {candidate}"
                )
            if candidate in forbidden_files:
                raise PolicyError(
                    f"required file group contains forbidden path: {candidate}"
                )

    patterns = normalized.get("forbidden_file_patterns", [])
    for required_path in normalized.get("required_files", []):
        matching_pattern = next(
            (
                pattern
                for pattern in patterns
                if _matches_file_pattern(required_path, pattern)
            ),
            None,
        )
        if matching_pattern is not None:
            raise PolicyError(
                f"required path {required_path} matches forbidden pattern: "
                f"{matching_pattern}"
            )
    for forbidden_path in normalized.get("forbidden_files", []):
        matching_pattern = next(
            (
                pattern
                for pattern in patterns
                if _matches_file_pattern(forbidden_path, pattern)
            ),
            None,
        )
        if matching_pattern is not None:
            raise PolicyError(
                f"forbidden path {forbidden_path} duplicates pattern: "
                f"{matching_pattern}"
            )
    for group in normalized.get("required_file_groups", []):
        for candidate in group:
            matching_pattern = next(
                (
                    pattern
                    for pattern in patterns
                    if _matches_file_pattern(candidate, pattern)
                ),
                None,
            )
            if matching_pattern is not None:
                raise PolicyError(
                    f"required file group path {candidate} matches forbidden pattern: "
                    f"{matching_pattern}"
                )

    for key in ("max_files", "max_total_bytes"):
        if key not in repository:
            continue
        value = repository[key]
        if not _is_integer(value) or value < 1:
            raise PolicyError(f"repository.{key} must be a positive integer: {source}")
        normalized[key] = value

    if "require_clean_git" in repository:
        value = repository["require_clean_git"]
        if not isinstance(value, bool):
            raise PolicyError(
                f"repository.require_clean_git must be true or false: {source}"
            )
        normalized["require_clean_git"] = value

    return {
        "version": version,
        "source": str(source),
        "repository": normalized,
    }


def _validate_file_paths(
    value: Any, source: str | Path, rule_name: str
) -> list[str]:
    if not isinstance(value, list) or not value:
        raise PolicyError(
            f"repository.{rule_name} must be a non-empty array: {source}"
        )

    paths: list[str] = []
    for entry in value:
        if not isinstance(entry, str) or not entry:
            raise PolicyError(
                f"repository.{rule_name} entries must be non-empty strings: {source}"
            )
        if "\\" in entry:
            raise PolicyError(
                f"repository.{rule_name} paths must use forward slashes: {entry}"
            )

        path = PurePosixPath(entry)
        if (
            not path.parts
            or path.is_absolute()
            or path.as_posix() != entry
            or ".." in path.parts
        ):
            raise PolicyError(
                f"repository.{rule_name} paths must be normalized and relative: {entry}"
            )
        if entry in paths:
            raise PolicyError(
                f"repository.{rule_name} contains a duplicate: {entry}"
            )
        paths.append(entry)

    return paths


def _validate_file_groups(value: Any, source: str | Path) -> list[list[str]]:
    rule_name = "required_file_groups"
    if not isinstance(value, list) or not value:
        raise PolicyError(
            f"repository.{rule_name} must be a non-empty array: {source}"
        )

    groups: list[list[str]] = []
    identities: set[tuple[str, ...]] = set()
    for index, value_group in enumerate(value):
        group = _validate_file_paths(
            value_group, source, f"{rule_name}[{index}]"
        )
        identity = tuple(sorted(group))
        if identity in identities:
            raise PolicyError(
                f"repository.{rule_name} contains a duplicate group: "
                f"{', '.join(group)}"
            )
        identities.add(identity)
        groups.append(group)

    return groups


def _validate_file_patterns(value: Any, source: str | Path) -> list[str]:
    rule_name = "forbidden_file_patterns"
    if not isinstance(value, list) or not value:
        raise PolicyError(
            f"repository.{rule_name} must be a non-empty array: {source}"
        )

    patterns: list[str] = []
    for entry in value:
        if not isinstance(entry, str) or not entry:
            raise PolicyError(
                f"repository.{rule_name} entries must be non-empty strings: {source}"
            )
        if "\\" in entry:
            raise PolicyError(
                f"repository.{rule_name} patterns must use forward slashes: {entry}"
            )
        path = PurePosixPath(entry)
        if (
            not path.parts
            or path.is_absolute()
            or path.as_posix() != entry
            or ".." in path.parts
        ):
            raise PolicyError(
                f"repository.{rule_name} patterns must be normalized and relative: "
                f"{entry}"
            )
        if not any(token in entry for token in ("*", "?", "[")):
            raise PolicyError(
                f"repository.{rule_name} entry must contain a wildcard: {entry}"
            )
        if entry in patterns:
            raise PolicyError(
                f"repository.{rule_name} contains a duplicate: {entry}"
            )
        patterns.append(entry)

    return patterns


def _forbidden_file_exists(
    snapshot: dict[str, Any], root: Path, relative_path: str
) -> bool:
    candidate = root / relative_path
    if not candidate.is_file():
        return False
    if not snapshot["git"]["is_repo"]:
        return True

    try:
        completed = subprocess.run(
            [
                "git",
                "-C",
                str(root),
                "ls-files",
                "--cached",
                "--others",
                "--exclude-standard",
                "--",
                relative_path,
            ],
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError:
        return True
    if completed.returncode != 0:
        return True

    return relative_path in completed.stdout.splitlines()


def _policy_visible_paths(snapshot: dict[str, Any], root: Path) -> list[str]:
    if snapshot["git"]["is_repo"]:
        try:
            completed = subprocess.run(
                [
                    "git",
                    "-C",
                    str(root),
                    "ls-files",
                    "--cached",
                    "--others",
                    "--exclude-standard",
                    "-z",
                    "--",
                    ".",
                ],
                check=False,
                capture_output=True,
                text=True,
            )
        except OSError:
            completed = None
        if completed is not None and completed.returncode == 0:
            return sorted(
                path
                for path in completed.stdout.split("\0")
                if path and (root / path).is_file()
            )

    return sorted(
        path.relative_to(root).as_posix()
        for path in root.rglob("*")
        if path.is_file() and ".git" not in path.relative_to(root).parts
    )


def _matches_file_pattern(path: str, pattern: str) -> bool:
    return PurePosixPath(path).match(pattern)


def _reject_unknown_keys(
    values: dict[str, Any], allowed: set[str], table_name: str
) -> None:
    unknown = sorted(set(values) - allowed)
    if unknown:
        raise PolicyError(f"unknown {table_name} key: {unknown[0]}")


def _is_integer(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)
