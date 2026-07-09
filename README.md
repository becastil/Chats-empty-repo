# repo-scout

`repo-scout` is a small local CLI for getting a compact snapshot of a codebase before a handoff, review, or work session.

It currently reports:

- Git branch and changed-file count when the target is inside a Git repository
- Presence of common project state documents
- Total scanned files and bytes
- File counts by extension
- Largest files in the scanned tree

The tool has no cloud dependencies and does not require API keys.

## Quick Start

Run from a checkout:

```bash
PYTHONPATH=src python3 -m repo_scout .
```

Machine-readable output is available too:

```bash
PYTHONPATH=src python3 -m repo_scout --format json .
```

Ignore extra local files or directories without editing `.gitignore`:

```bash
PYTHONPATH=src python3 -m repo_scout --ignore "*.log" --ignore private .
```

Protect large scans with a file-count limit:

```bash
PYTHONPATH=src python3 -m repo_scout --max-files 5000 .
```

Install it locally in editable mode:

```bash
python3 -m pip install -e .
repo-scout .
```

Run the tests:

```bash
python3 -m unittest discover -s tests
```

## Why This Exists

Developers often need to quickly understand an unfamiliar repository, especially at the start of a review, agent handoff, or maintenance session. `repo-scout` aims to provide the first useful page of context without requiring remote services, indexing daemons, or heavyweight project setup.
