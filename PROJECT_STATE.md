# Project State

## Current Project

`repo-scout` is a dependency-free Python CLI that summarizes local repository state for developer handoffs, reviews, and work-session orientation.

## Implemented

- Package skeleton with an installable `repo-scout` console command.
- Text and JSON snapshot output.
- Repository scanning for Git state, expected project documents, file counts by extension, total bytes, and largest files.
- Repeatable `--ignore` filters for local files or directories that should be excluded from a scan.
- `--max-files` guard that stops scans once the filtered file count exceeds a user-supplied limit.
- Optional `--languages` summary derived from common filenames and file extensions.
- Unit tests covering scanner behavior and JSON CLI output.

## How To Run

```bash
PYTHONPATH=src python3 -m repo_scout .
python3 -m unittest discover -s tests
```

## Next Small Task

Add Markdown report output for handoff notes and pull request descriptions.
