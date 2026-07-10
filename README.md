# repo-scout

`repo-scout` is a small local CLI for getting a compact snapshot of a codebase before a handoff, review, or work session.

It currently reports:

- Git branch and changed-file count when the target is inside a Git repository
- Presence of common project state documents
- Total scanned files and bytes
- File counts by extension
- Optional best-effort file counts by language name
- Attention summary for dirty Git state, missing docs, and large files
- Largest files in the scanned tree

The tool has no cloud dependencies and does not require API keys.

The repository also includes a small web companion for browsing the workflow and
switching between representative text and JSON snapshot output. Run its local
preview with:

```bash
npm install
npm run dev
```

## Quick Start

Run from a checkout:

```bash
PYTHONPATH=src python3 -m repo_scout .
```

Machine-readable output is available too:

```bash
PYTHONPATH=src python3 -m repo_scout --format json .
```

Create a handoff or pull-request-ready report:

```bash
PYTHONPATH=src python3 -m repo_scout --format markdown --languages .
```

Markdown output includes the summary, project document status, active filters,
file composition tables, and largest files.

Compare two saved JSON snapshots to see project drift:

```bash
PYTHONPATH=src python3 -m repo_scout --format json . > before.json
PYTHONPATH=src python3 -m repo_scout --format json . > after.json
PYTHONPATH=src python3 -m repo_scout --format markdown --compare before.json after.json
```

Comparison JSON reports numeric deltas, added and removed document entries,
Git changes, and attention-status changes.

Snapshots include `schema_version: 1`. Older snapshots without that field are
read as version 1 for comparison compatibility; unsupported future versions
are rejected with a clear error.

Write reports directly and require `--force` before replacing an existing file:

```bash
PYTHONPATH=src python3 -m repo_scout --format markdown --output handoff.md .
PYTHONPATH=src python3 -m repo_scout --format markdown --output handoff.md --force .
```

Ignore extra local files or directories without editing `.gitignore`:

```bash
PYTHONPATH=src python3 -m repo_scout --ignore "*.log" --ignore private .
```

Protect large scans with a file-count limit:

```bash
PYTHONPATH=src python3 -m repo_scout --max-files 5000 .
```

Add a language-level summary while keeping raw extension counts:

```bash
PYTHONPATH=src python3 -m repo_scout --languages .
```

Language detection uses common filenames and file extensions. Unrecognized files are
grouped under `Other`.

Show the attention summary with a custom large-file threshold:

```bash
PYTHONPATH=src python3 -m repo_scout --format markdown --large-file-bytes 250000 .
```

The default threshold is 100,000 bytes.

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
