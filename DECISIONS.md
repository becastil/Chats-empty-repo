# Decisions

## 2026-07-08: Build a Local Repository Snapshot CLI

`repo-scout` was chosen because it is practical for developers, testable in small increments, and useful without remote services or API keys. It can grow through focused additions such as ignore rules, report formats, and snapshot comparisons.

## 2026-07-08: Start Dependency-Free

The first version uses only the Python standard library. This keeps installation and testing simple while the project proves its core workflow.

## 2026-07-08: Prefer Deterministic Snapshot Data

The scanner avoids timestamps in its output so tests remain stable and repeated runs are easier to compare.

## 2026-07-08: Use Simple Glob Ignore Patterns

User-supplied ignore filters use standard shell-style glob matching against repository-relative paths and path parts. This keeps `--ignore` understandable without introducing a separate pattern language.

## 2026-07-09: Add File Count Guard Before Byte Guard

`--max-files` was added before a byte-size guard because file count is cheap to evaluate during discovery and gives users a clear safety valve for very large repositories.

## 2026-07-09: Keep Language Detection Optional and Transparent

Language totals are derived from a small built-in filename and extension map and only appear when `--languages` is requested. Raw extension counts remain available so callers can inspect the underlying evidence, while unknown files are grouped under `Other` instead of being silently omitted.

## 2026-07-09: Add a Static Companion Surface

The CLI remains the source of truth for local scans, while a small static web companion makes the workflow legible to visitors without requiring a checkout, server-side storage, or API credentials. The page uses a representative snapshot and keeps the interactive behavior limited to output-format switching and command copying.

## 2026-07-09: Make Markdown a First-Class Output Format

Markdown output is generated from the same deterministic snapshot used by text and JSON modes. It favors copy-pasteable summary bullets and tables for handoffs and pull requests while preserving JSON as the machine-readable contract.

## 2026-07-09: Keep Attention Checks Additive and Tunable

Attention findings are added as a separate status-and-items field so existing snapshot consumers can ignore them safely. Large-file warnings use a documented 100,000-byte default and a CLI override because repository size expectations vary by project.

## 2026-07-09: Compare Saved JSON Snapshots

Snapshot comparison accepts JSON files produced by the existing `--format json` mode. It returns explicit numeric deltas and added or removed entries, keeps the original snapshots untouched, and supports text, JSON, and Markdown output so the same comparison can serve both agents and human handoffs.

## 2026-07-09: Protect Direct Report Writes

`--output` refuses to replace an existing file unless the caller also passes `--force`. This keeps handoff reports from being silently overwritten while retaining an explicit escape hatch for repeatable automation.

## 2026-07-10: Version the Snapshot Contract

Every new snapshot declares schema version 1. Comparison treats missing schema metadata as version 1 so existing saved files remain usable, while an explicit version change appears as a comparison finding for future migrations.

## 2026-07-10: Reject Unsupported Snapshot Versions

Comparison accepts the current schema and metadata-free legacy snapshots, but rejects any other explicit version before reading its fields. This prevents a future format from being misreported as a valid comparison.
