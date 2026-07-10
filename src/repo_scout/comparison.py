from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from .scanner import SNAPSHOT_SCHEMA_VERSION


MAX_REPORTED_PATHS = 50


class SnapshotReadError(ValueError):
    """Raised when a saved snapshot cannot be read or validated."""


def compare_snapshot_files(
    before_path: str | Path, after_path: str | Path
) -> dict[str, Any]:
    before = Path(before_path).expanduser()
    after = Path(after_path).expanduser()
    return compare_snapshots(
        _load_snapshot(before),
        _load_snapshot(after),
        before_label=before.as_posix(),
        after_label=after.as_posix(),
    )


def compare_snapshots(
    before: Mapping[str, Any],
    after: Mapping[str, Any],
    before_label: str = "before",
    after_label: str = "after",
) -> dict[str, Any]:
    before_files = _files(before)
    after_files = _files(after)
    before_docs = _docs(before)
    after_docs = _docs(after)
    before_git = _git(before)
    after_git = _git(after)
    before_attention = _attention(before)
    after_attention = _attention(after)

    result = {
        "schema_version": _value_change(
            _schema_version(before), _schema_version(after)
        ),
        "before": {
            "label": before_label,
            "root": str(before.get("root", "")),
        },
        "after": {
            "label": after_label,
            "root": str(after.get("root", "")),
        },
        "files": {
            "total": _numeric_change(before_files.get("total", 0), after_files.get("total", 0)),
            "total_bytes": _numeric_change(
                before_files.get("total_bytes", 0), after_files.get("total_bytes", 0)
            ),
            "by_extension": _counter_change(
                _counter(before_files.get("by_extension", {})),
                _counter(after_files.get("by_extension", {})),
            ),
        },
        "docs": {
            "present": _list_change(before_docs["present"], after_docs["present"]),
            "missing": _list_change(before_docs["missing"], after_docs["missing"]),
        },
        "git": {
            "is_repo": _value_change(
                before_git.get("is_repo", False), after_git.get("is_repo", False)
            ),
            "branch": _value_change(
                before_git.get("branch"), after_git.get("branch")
            ),
            "dirty_files": _numeric_change(
                before_git.get("dirty_files", 0), after_git.get("dirty_files", 0)
            ),
        },
        "attention": {
            "status": _value_change(
                before_attention["status"], after_attention["status"]
            ),
            "item_count": _numeric_change(
                len(before_attention["items"]), len(after_attention["items"])
            ),
        },
    }

    if "by_language" in before_files or "by_language" in after_files:
        result["files"]["by_language"] = _counter_change(
            _counter(before_files.get("by_language", {})),
            _counter(after_files.get("by_language", {})),
        )

    if "paths" in before_files and "paths" in after_files:
        result["files"]["paths"] = _path_change(before_files, after_files)

    result["status"] = "changed" if _has_changes(result) else "unchanged"
    return result


def _load_snapshot(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise SnapshotReadError(f"could not read {path}: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise SnapshotReadError(f"invalid JSON in {path}: {exc.msg}") from exc

    if not isinstance(data, dict) or not isinstance(data.get("files"), dict):
        raise SnapshotReadError(f"{path} is not a repo-scout snapshot")
    return data


def _files(snapshot: Mapping[str, Any]) -> Mapping[str, Any]:
    files = snapshot.get("files")
    if not isinstance(files, dict):
        raise SnapshotReadError("snapshot files section must be an object")
    return files


def _docs(snapshot: Mapping[str, Any]) -> dict[str, list[str]]:
    docs = snapshot.get("docs", {})
    if not isinstance(docs, dict):
        raise SnapshotReadError("snapshot docs section must be an object")
    return {
        "present": _strings(docs.get("present", [])),
        "missing": _strings(docs.get("missing", [])),
    }


def _git(snapshot: Mapping[str, Any]) -> Mapping[str, Any]:
    git = snapshot.get("git", {})
    if not isinstance(git, dict):
        raise SnapshotReadError("snapshot git section must be an object")
    return git


def _attention(snapshot: Mapping[str, Any]) -> dict[str, Any]:
    attention = snapshot.get("attention", {})
    if not isinstance(attention, dict):
        raise SnapshotReadError("snapshot attention section must be an object")
    items = attention.get("items", [])
    if not isinstance(items, list):
        raise SnapshotReadError("snapshot attention items must be an array")
    return {
        "status": str(attention.get("status", "clear")),
        "items": items,
    }


def _schema_version(snapshot: Mapping[str, Any]) -> int:
    version = snapshot.get("schema_version", SNAPSHOT_SCHEMA_VERSION)
    if not isinstance(version, int) or isinstance(version, bool):
        raise SnapshotReadError("snapshot schema_version must be an integer")
    if version != SNAPSHOT_SCHEMA_VERSION:
        raise SnapshotReadError(
            f"unsupported snapshot schema_version {version}; "
            f"supported version is {SNAPSHOT_SCHEMA_VERSION}"
        )
    return version


def _counter(value: Any) -> dict[str, int]:
    if not isinstance(value, dict):
        raise SnapshotReadError("snapshot count section must be an object")
    result: dict[str, int] = {}
    for key, count in value.items():
        if not isinstance(key, str) or not isinstance(count, int) or isinstance(count, bool):
            raise SnapshotReadError("snapshot count sections must map names to integers")
        result[key] = count
    return result


def _path_change(
    before_files: Mapping[str, Any], after_files: Mapping[str, Any]
) -> dict[str, Any]:
    before_paths = _strings(before_files.get("paths", []))
    after_paths = _strings(after_files.get("paths", []))
    added_all = sorted(set(after_paths) - set(before_paths))
    removed_all = sorted(set(before_paths) - set(after_paths))
    source_truncated = bool(
        before_files.get("paths_truncated", False)
        or after_files.get("paths_truncated", False)
    )
    detail_truncated = (
        len(added_all) > MAX_REPORTED_PATHS
        or len(removed_all) > MAX_REPORTED_PATHS
    )
    return {
        "added": added_all[:MAX_REPORTED_PATHS],
        "removed": removed_all[:MAX_REPORTED_PATHS],
        "added_count": len(added_all),
        "removed_count": len(removed_all),
        "limit": MAX_REPORTED_PATHS,
        "truncated": source_truncated or detail_truncated,
        "complete": not (source_truncated or detail_truncated),
    }


def _strings(value: Any) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise SnapshotReadError("snapshot document sections must contain strings")
    return sorted(value)


def _numeric_change(before: Any, after: Any) -> dict[str, int]:
    if not isinstance(before, int) or isinstance(before, bool):
        before = 0
    if not isinstance(after, int) or isinstance(after, bool):
        after = 0
    return {"before": before, "after": after, "delta": after - before}


def _value_change(before: Any, after: Any) -> dict[str, Any]:
    return {"before": before, "after": after, "changed": before != after}


def _list_change(before: list[str], after: list[str]) -> dict[str, list[str]]:
    before_set = set(before)
    after_set = set(after)
    return {
        "added": sorted(after_set - before_set),
        "removed": sorted(before_set - after_set),
    }


def _counter_change(
    before: dict[str, int], after: dict[str, int]
) -> dict[str, dict[str, Any]]:
    added = {key: after[key] for key in sorted(after.keys() - before.keys())}
    removed = {key: before[key] for key in sorted(before.keys() - after.keys())}
    changed = {
        key: _numeric_change(before[key], after[key])
        for key in sorted(before.keys() & after.keys())
        if before[key] != after[key]
    }
    return {"added": added, "removed": removed, "changed": changed}


def _has_changes(comparison: Mapping[str, Any]) -> bool:
    if comparison["schema_version"]["changed"]:
        return True

    files = comparison["files"]
    if files["total"]["delta"] or files["total_bytes"]["delta"]:
        return True
    if _counter_has_changes(files["by_extension"]):
        return True
    if "by_language" in files and _counter_has_changes(files["by_language"]):
        return True
    if files.get("paths", {}).get("added") or files.get("paths", {}).get("removed"):
        return True

    docs = comparison["docs"]
    if any(docs[key]["added"] or docs[key]["removed"] for key in ("present", "missing")):
        return True

    git = comparison["git"]
    if any(git[key]["changed"] for key in ("is_repo", "branch")):
        return True
    if git["dirty_files"]["delta"]:
        return True

    attention = comparison["attention"]
    return attention["status"]["changed"] or attention["item_count"]["delta"] != 0


def _counter_has_changes(change: Mapping[str, Any]) -> bool:
    return bool(change["added"] or change["removed"] or change["changed"])
