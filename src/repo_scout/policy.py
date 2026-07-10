from __future__ import annotations

from pathlib import Path, PurePosixPath
import tomllib
from typing import Any


POLICY_VERSION = 1

_ROOT_KEYS = {"version", "repository"}
_REPOSITORY_KEYS = {
    "required_files",
    "max_files",
    "max_total_bytes",
    "require_clean_git",
}


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
        "status": "fail" if violations else "pass",
        "rules_checked": len(rules),
        "violations": violations,
    }


def _validate_policy(policy: Any, source: Path) -> dict[str, Any]:
    if not isinstance(policy, dict):
        raise PolicyError(f"policy must be a TOML table: {source}")

    _reject_unknown_keys(policy, _ROOT_KEYS, "policy")
    version = policy.get("version")
    if not _is_integer(version) or version != POLICY_VERSION:
        raise PolicyError(f"policy version must be {POLICY_VERSION}: {source}")

    repository = policy.get("repository")
    if not isinstance(repository, dict):
        raise PolicyError(f"policy must define a [repository] table: {source}")
    if not repository:
        raise PolicyError(f"[repository] must define at least one rule: {source}")

    _reject_unknown_keys(repository, _REPOSITORY_KEYS, "repository")
    normalized: dict[str, Any] = {}

    if "required_files" in repository:
        normalized["required_files"] = _validate_required_files(
            repository["required_files"], source
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


def _validate_required_files(value: Any, source: Path) -> list[str]:
    if not isinstance(value, list) or not value:
        raise PolicyError(
            f"repository.required_files must be a non-empty array: {source}"
        )

    required_files: list[str] = []
    for entry in value:
        if not isinstance(entry, str) or not entry:
            raise PolicyError(
                f"repository.required_files entries must be non-empty strings: {source}"
            )
        if "\\" in entry:
            raise PolicyError(
                f"repository.required_files paths must use forward slashes: {entry}"
            )

        path = PurePosixPath(entry)
        if (
            not path.parts
            or path.is_absolute()
            or path.as_posix() != entry
            or ".." in path.parts
        ):
            raise PolicyError(
                f"repository.required_files paths must be normalized and relative: {entry}"
            )
        if entry in required_files:
            raise PolicyError(f"repository.required_files contains a duplicate: {entry}")
        required_files.append(entry)

    return required_files


def _reject_unknown_keys(
    values: dict[str, Any], allowed: set[str], table_name: str
) -> None:
    unknown = sorted(set(values) - allowed)
    if unknown:
        raise PolicyError(f"unknown {table_name} key: {unknown[0]}")


def _is_integer(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)
