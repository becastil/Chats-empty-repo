# Project State

## Current Project

`repo-scout` is a dependency-free Python CLI that summarizes local repository state for developer handoffs, reviews, and work-session orientation.

The repository also includes a small hosted web companion that explains the CLI and lets visitors switch between sample text and JSON snapshots.

Revenue is the primary product constraint. The free CLI is the adoption layer for a paid team policy and CI enforcement offer documented in `BUSINESS_MODEL.md`.

The delivery goal is 1,000 meaningful commits. This update is commit 19 of 1,000, with 981 remaining. Quality, test coverage, and revenue alignment take priority over commit volume.

## Implemented

- Package skeleton with an installable `repo-scout` console command.
- Text and JSON snapshot output.
- Repository scanning for Git state, expected project documents, file counts by extension, total bytes, and largest files.
- Repeatable `--ignore` filters for local files or directories that should be excluded from a scan.
- `--max-files` guard that stops scans once the filtered file count exceeds a user-supplied limit.
- Optional `--languages` summary derived from common filenames and file extensions.
- Markdown handoff reports with summary bullets and stable file tables.
- Attention summary for dirty Git state, missing docs, and configurable large-file thresholds.
- Snapshot comparison for file, document, Git, and attention drift.
- Direct report writing with overwrite protection and explicit `--force` support.
- Versioned snapshot metadata with backward-compatible comparison defaults.
- Explicit rejection of unsupported future snapshot schema versions.
- Bounded changed-path details in snapshot comparisons.
- CI gating with exit code 5 when attention findings are present.
- Strict version-controlled TOML team policies for required files, repository size, and clean Git state.
- Policy results in every report format with exit code 6 for CI violations.
- Four packaged starter profiles for baseline, Python, npm, and agent-ready services.
- `repo-scout-policy` discovery, inspection, and overwrite-safe initialization commands.
- A dogfooded GitHub Actions policy gate with read-only permissions and immutable action pins.
- Copy-ready CI and policy templates that preserve Markdown evidence when enforcement fails.
- A $299 founding-team pilot offer with explicit revenue validation milestones.
- Unit tests covering scanner behavior and JSON CLI output.
- Responsive Repo Scout web companion with a server-rendered snapshot lab and accessible format toggle.
- A hosted founding-team pilot offer with price, scope, implemented policy proof, and a direct conversion CTA.
- A structured public pilot intake that qualifies team size, repository count, CI provider, and policy need.
- A dependency-free pilot funnel reporter with stable text and JSON revenue summaries.
- Cumulative GitHub labels for lead, qualification, offer, payment, activation, conversion, and loss.
- Label-drift warnings and tested $299 pilot / $897 target accounting semantics.
- Host-derived Open Graph and X metadata with a product-specific social preview.
- Sites hosting metadata and a Cloudflare Workers-compatible production build.

## How To Run

```bash
PYTHONPATH=src python3 -m repo_scout .
python3 -m unittest discover -s tests
```

## Next Small Task

Add deterministic stale-lead follow-up reporting to the pilot funnel.
