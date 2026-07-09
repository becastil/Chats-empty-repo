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
