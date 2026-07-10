# Changelog

## 0.2.7 - 2026-07-10

- Added a tag-driven GitHub release workflow for wheel and source distributions.
- Added exact tag, package-version, artifact-name, and artifact-set validation.
- Added deterministic SHA-256 manifests and GitHub build-provenance attestations.
- Hash-locked all release-only build dependencies and pinned every release action by commit.
- Added clean-environment smoke tests for all three installed commands before publication.
- Added release contract tests covering version drift, missing artifacts, unexpected artifacts, permissions, pins, and dependency hashes.
- Added the MIT license text to the repository and packaged distributions.
- Documented version-specific installation, checksum verification, provenance verification, and the maintainer release contract.

## 0.2.6 - 2026-07-10

- Added deterministic follow-up reporting for stale open lead, qualified, and offered pilot issues.
- Added `--as-of YYYY-MM-DD` and `--stale-days` controls with whole-day UTC semantics.
- Added normalized activity timestamps, age, follow-up status, and stable priority ordering to funnel JSON schema 2.
- Added warnings for closed pre-payment issues without loss labels, missing timestamps, and future activity dates.
- Added boundary, timezone-offset, state/stage matrix, invalid timestamp, malformed option, text, and JSON coverage.
- Documented that GitHub issue activity is an inactivity signal rather than evidence of buyer contact.

## 0.2.5 - 2026-07-10

- Added four packaged starter policies for baseline, Python, npm, and agent-ready services.
- Added `repo-scout-policy list` with human-readable and stable JSON catalogs.
- Added `repo-scout-policy show` for exact, read-only TOML inspection.
- Added overwrite-safe `repo-scout-policy init` with custom output paths and atomic `--force` replacement.
- Applied the same strict policy validator to in-memory package resources and local files.
- Added profile enforcement, output safety, missing-resource, deterministic catalog, and package-data coverage.
- Updated package license metadata to the modern SPDX expression format.
- Documented profile selection, clean-worktree onboarding, GitHub Actions handoff, and the paid custom-policy path.

## 0.2.4 - 2026-07-10

- Added `repo-scout-pilot` for dependency-free pilot funnel reporting from GitHub issue JSON.
- Added order-independent text and JSON totals for stages, paid pilots, booked revenue, target gaps, annual conversions, and losses.
- Added warnings for skipped cumulative stages, unknown pilot labels, and conflicting terminal outcomes.
- Added `pilot-lead` to the founding-team request form and configured seven lifecycle labels on GitHub.
- Added deterministic fixtures and coverage for custom targets, stdin, invalid input, duplicate protection, revenue semantics, and module execution.
- Documented weekly operating cadence, label transitions, booked-revenue definitions, refunds, and public-issue privacy boundaries.

## 0.2.3 - 2026-07-10

- Added a GitHub Actions policy gate that dogfoods Repo Scout on pull requests and `main`.
- Added copy-ready workflow and policy templates for founding-team pilot repositories.
- Pinned GitHub actions and an isolated external Repo Scout checkout to immutable commits with read-only permissions.
- Preserved Markdown policy evidence in the job summary and a 14-day artifact even when enforcement fails.
- Added repeatable clean-worktree coverage for the exact example command and policy contract.
- Documented setup, rollout sequencing, exit codes, report access, and dependency-pin maintenance.

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
