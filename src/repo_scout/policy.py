from __future__ import annotations

import hashlib
import json
from pathlib import Path, PurePosixPath
import subprocess
import tomllib
from typing import Any


POLICY_VERSION = 2
SUPPORTED_POLICY_VERSIONS = (1, POLICY_VERSION)

_ROOT_KEYS = {"version", "repository"}
_REPOSITORY_KEYS_V1 = {
    "required_files",
    "max_files",
    "max_total_bytes",
    "require_clean_git",
}
_REPOSITORY_KEYS_V2 = _REPOSITORY_KEYS_V1 | {"forbidden_files"}


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

    for forbidden_file in rules.get("forbidden_files", []):
        if _forbidden_file_exists(snapshot, root, forbidden_file):
            violations.append(
                {
                    "rule": "repository.forbidden_files",
                    "path": forbidden_file,
                    "message": f"Forbidden file is present: {forbidden_file}.",
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
    for key in ("required_files", "forbidden_files"):
        if key in repository:
            repository[key] = sorted(repository[key])
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
            "policy version must be 1 or 2: "
            f"{source}"
        )

    repository = policy.get("repository")
    if not isinstance(repository, dict):
        raise PolicyError(f"policy must define a [repository] table: {source}")
    if not repository:
        raise PolicyError(f"[repository] must define at least one rule: {source}")

    repository_keys = (
        _REPOSITORY_KEYS_V1 if version == 1 else _REPOSITORY_KEYS_V2
    )
    _reject_unknown_keys(repository, repository_keys, "repository")
    normalized: dict[str, Any] = {}

    for key in ("required_files", "forbidden_files"):
        if key in repository:
            normalized[key] = _validate_file_paths(repository[key], source, key)

    overlap = set(normalized.get("required_files", [])) & set(
        normalized.get("forbidden_files", [])
    )
    if overlap:
        path = sorted(overlap)[0]
        raise PolicyError(f"repository path is both required and forbidden: {path}")

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


def _reject_unknown_keys(
    values: dict[str, Any], allowed: set[str], table_name: str
) -> None:
    unknown = sorted(set(values) - allowed)
    if unknown:
        raise PolicyError(f"unknown {table_name} key: {unknown[0]}")


def _is_integer(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)
