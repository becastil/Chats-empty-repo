# Decisions

## 2026-07-08: Build a Local Repository Snapshot CLI

`repo-scout` was chosen because it is practical for developers, testable in small increments, and useful without remote services or API keys. It can grow through focused additions such as ignore rules, report formats, and snapshot comparisons.

## 2026-07-08: Start Dependency-Free

The first version uses only the Python standard library. This keeps installation and testing simple while the project proves its core workflow.

## 2026-07-08: Prefer Deterministic Snapshot Data

The scanner avoids timestamps in its output so tests remain stable and repeated runs are easier to compare.

