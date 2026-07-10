# Changelog

## 0.2.2 - 2026-07-10

- Added the $299 founding-team pilot offer and conversion CTA to the hosted companion.
- Added implemented team-policy proof, 90-day scope, and the 10-repository limit to the offer.
- Added a structured GitHub issue form that qualifies pilot requests without collecting source code.
- Added a responsive pilot layout with stable breakpoint typography and accessible navigation targets.
- Added product-specific Open Graph and X metadata with a generated 1200x630 social preview.
- Expanded rendered production coverage for commercial content, conversion links, intake fields, and host-derived social metadata.

## 0.2.1 - 2026-07-10

- Added strict, versioned TOML team policies through `--policy PATH`.
- Added policy rules for required files, file and byte limits, and clean Git state.
- Included policy results and violations in text, JSON, and Markdown reports.
- Added exit code 6 for completed scans that violate team policy.
- Added a copy-ready example policy and raised the minimum Python version to 3.11 for standard-library TOML parsing.

## 0.2.0 - 2026-07-10

- Added a responsive Repo Scout web companion with sample Text and JSON snapshot views.
- Added production build, lint, and rendered HTML coverage for the hosted surface.
- Added Sites hosting metadata for the deployable web build.
- Added `--format markdown` for handoff notes and pull-request-ready reports.
- Added Markdown report coverage for filters, documents, languages, and largest files.
- Added an additive attention summary for dirty Git state, missing docs, and large files.
- Added `--large-file-bytes` to tune the large-file warning threshold.
- Added `--compare BEFORE AFTER` for saved snapshot drift reports.
- Added comparison output in text, JSON, and Markdown with regression coverage.
- Added `--output` for direct report files and `--force` overwrite protection.
- Added `schema_version: 1` metadata to snapshots and schema drift reporting.
- Added explicit rejection of unsupported future snapshot schema versions.
- Added bounded added and removed path details to snapshot comparisons.
- Added `--fail-on-attention` with exit code 5 for CI enforcement.
- Added the founding-team pilot business model and revenue milestones.
- Established a tracked goal of 1,000 meaningful, revenue-aligned commits.

## 0.1.3 - 2026-07-09

- Added an opt-in `--languages` summary alongside raw extension counts.
- Recognized common source, markup, configuration, and build file types without adding dependencies.
- Grouped unrecognized files under `Other` and added scanner and CLI coverage.

## 0.1.2 - 2026-07-09

- Added a `--max-files` CLI guard that stops scans when too many files match.
- Included the active max-file limit in snapshot filter metadata.
- Added tests for successful guarded scans and limit-exceeded errors.

## 0.1.1 - 2026-07-08

- Added repeatable `--ignore` CLI filters for excluding local files or directories from snapshots.
- Included active ignore filters in JSON output.
- Added tests for scanner-level and CLI-level ignore behavior.

## 0.1.0 - 2026-07-08

- Created the `repo-scout` Python CLI project.
- Added text and JSON repository snapshot output.
- Added scanning for Git state, project docs, file extension counts, total bytes, and largest files.
- Added unit tests and basic project documentation.
