# repo-scout

`repo-scout` is a small local CLI for getting a compact snapshot of a codebase before a handoff, review, or work session.

It currently reports:

- Git branch and changed-file count when the target is inside a Git repository
- Presence of common project state documents
- Total scanned files and bytes
- File counts by extension
- Optional best-effort file counts by language name
- Attention summary for dirty Git state, missing docs, and large files
- Version-controlled TOML team policies with CI enforcement
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

Current snapshots retain up to 500 sorted paths, and comparison reports show up
to 50 added or removed paths with a truncation marker when needed.

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

Fail CI after still emitting the report when attention is required:

```bash
PYTHONPATH=src python3 -m repo_scout --format markdown --fail-on-attention .
```

Exit code 5 means the scan completed but attention findings were present.

Apply a shared team policy and fail CI when the repository violates it:

```bash
PYTHONPATH=src python3 -m repo_scout --format markdown --policy examples/team-policy.toml .
```

Policy files use a strict, versioned TOML contract:

```toml
version = 1

[repository]
required_files = ["README.md", "SECURITY.md"]
max_files = 5000
max_total_bytes = 50000000
require_clean_git = true
```

All rules are optional, but a policy must define at least one. Required-file
paths must be normalized paths relative to the repository. Unknown keys,
invalid values, and unsupported policy versions are rejected instead of being
silently ignored.

Policy results are included in text, JSON, and Markdown reports. Exit code 6
means the scan completed and at least one team-policy rule failed. Policy
failure takes precedence over exit code 5 when `--fail-on-attention` is also
active.

Generate a first-repository rollout bundle from the same policy evidence:

```bash
repo-scout --format markdown --policy repo-scout-policy.toml \
  --rollout-checklist --repository-id platform/api \
  --output repo-scout-rollout.md .
```

The bundle records automated readiness without pre-checking human rollout
actions, and it is still written before policy exit code 6. See
[docs/pilot-rollout.md](docs/pilot-rollout.md) for the evidence contract and
privacy guidance.

Summarize readiness across locally saved pilot bundles:

```bash
repo-scout-rollout api-rollout.md web-rollout.md
repo-scout-rollout --details api-rollout.md web-rollout.md
repo-scout-rollout --format json api-rollout.md web-rollout.md
```

The counts-only default omits repository IDs, branches, and evidence paths;
`--details` opts into repository-level output. Results are explicitly
bundle-reported rather than freshness or shared-policy proof. The aggregator
rejects duplicate IDs, duplicate JSON keys, and malformed or contradictory
metadata. It performs no uploads and requires no API key.

Initialize an offline starter policy for a common repository type:

```bash
repo-scout-policy list
repo-scout-policy show python-service
repo-scout-policy init python-service
```

Profiles are available for baseline services, Python services, npm services,
and agent-ready services. Initialization protects existing files unless
`--force` is explicit. Review and commit the policy before enforcement because
the profiles require a clean Git worktree. See
[docs/policy-starters.md](docs/policy-starters.md) for the full profile matrix.

Run the same policy automatically on pull requests with the copy-ready GitHub
Actions workflow:

```text
examples/github-actions/repo-scout-policy.yml
examples/github-actions/repo-scout-policy.toml
```

The workflow uses read-only permissions, immutable dependency pins, job-summary
evidence, and a downloadable Markdown report. It installs the `v0.2.8` wheel
only after checking its pinned digest, release manifest, source commit, tag,
signer workflow, and GitHub-hosted provenance. See
[docs/github-actions.md](docs/github-actions.md) for setup and failure handling.

## Team Pilot

Repo Scout's free core stays local and dependency-free. The $299 founding-team
pilot adds shared repository policies, CI rollout help, and one custom policy
pack for up to 10 repositories over 90 days. See [BUSINESS_MODEL.md](BUSINESS_MODEL.md)
for the offer and validation milestones.

[Request a founding-team pilot](https://github.com/becastil/Chats-empty-repo/issues/new?template=founding-team-pilot.yml)

Pilot requests are public GitHub issues. Do not include source code, credentials,
customer data, or other sensitive details.

Maintainers can turn the labeled requests into an auditable revenue funnel:

```bash
gh issue list --repo becastil/Chats-empty-repo --state all --label pilot-lead --limit 100 --json number,title,body,state,labels,createdAt,updatedAt,closedAt,url | repo-scout-pilot --as-of "$(date -u +%F)"
```

The dependency-free reporter counts booked pilots, booked revenue, remaining
distance to the three-pilot goal, annual conversions, losses, label drift, and
open pre-payment issues inactive for at least seven UTC calendar days. It also
attributes qualification and booked revenue to the request form's self-reported
discovery channel.
See [docs/pilot-tracking.md](docs/pilot-tracking.md) for stage definitions and
privacy rules.

Install it locally in editable mode:

```bash
python3 -m pip install -e .
repo-scout .
```

Repo Scout requires Python 3.11 or newer and has no runtime dependencies.

Versioned wheel and source releases are also available from GitHub with
SHA-256 manifests and build-provenance attestations. Install and verify a
specific release using the commands in
[docs/releases.md](docs/releases.md).

Run the tests:

```bash
python3 -m unittest discover -s tests
```

## Why This Exists

Developers often need to quickly understand an unfamiliar repository, especially at the start of a review, agent handoff, or maintenance session. `repo-scout` aims to provide the first useful page of context without requiring remote services, indexing daemons, or heavyweight project setup.
