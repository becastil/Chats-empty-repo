# repo-scout

`repo-scout` is a small local CLI for getting a compact snapshot of a codebase before a handoff, review, or work session.

For teams using coding agents across multiple repositories, the free scanner is
the starting point. The $299 founding-team pilot turns the team's rules into one
reviewed standard, rolls it out across up to 10 projects, and helps fix the
repositories that do not fit neatly without uploading source code.

[See why teams buy](https://repo-scout.becastil.chatgpt.site/?source=github#why-teams-buy) | [Apply for the $299 pilot](https://github.com/becastil/Chats-empty-repo/issues/new?template=founding-team-pilot.yml&discovery_source=GitHub+repository+or+release)

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

Download the portable release and scan the current repository. This path does
not require a checkout, package installation, administrator access, or an API
key:

```bash
curl -fL https://github.com/becastil/Chats-empty-repo/releases/download/v0.3.38/repo-scout-0.3.38.pyz -o /tmp/repo-scout.pyz
python3 /tmp/repo-scout.pyz --version
python3 /tmp/repo-scout.pyz --languages .
```

Repo Scout requires Python 3.11 or newer. The portable file contains the free
primary CLI. Install the wheel when you also
need the `repo-scout-distribution`, `repo-scout-growth`, `repo-scout-policy`,
`repo-scout-rollout`, `repo-scout-pilot`, or maintainer-only
`repo-scout-outreach` commands:

```bash
python3 -m pip install https://github.com/becastil/Chats-empty-repo/releases/download/v0.3.38/repo_scout-0.3.38-py3-none-any.whl
repo-scout --languages .
```

Every installed Repo Scout command supports `--version`, so local and CI logs
can confirm the exact package identity without running a scan or reading source.

Machine-readable output is available too:

```bash
python3 /tmp/repo-scout.pyz --format json .
```

Create a handoff or pull-request-ready report:

```bash
python3 /tmp/repo-scout.pyz --format markdown --languages .
```

Markdown output includes the summary, project document status, active filters,
file composition tables, and largest files.

Compare two saved JSON snapshots to see project drift:

```bash
python3 /tmp/repo-scout.pyz --format json . > before.json
python3 /tmp/repo-scout.pyz --format json . > after.json
python3 /tmp/repo-scout.pyz --format markdown --compare before.json after.json
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
python3 /tmp/repo-scout.pyz --format markdown --output handoff.md .
python3 /tmp/repo-scout.pyz --format markdown --output handoff.md --force .
```

Ignore extra local files or directories without editing `.gitignore`:

```bash
python3 /tmp/repo-scout.pyz --ignore "*.log" --ignore private .
```

Protect large scans with a file-count limit:

```bash
python3 /tmp/repo-scout.pyz --max-files 5000 .
```

Add a language-level summary while keeping raw extension counts:

```bash
python3 /tmp/repo-scout.pyz --languages .
```

Language detection uses common filenames and file extensions. Unrecognized files are
grouped under `Other`.

Show the attention summary with a custom large-file threshold:

```bash
python3 /tmp/repo-scout.pyz --format markdown --large-file-bytes 250000 .
```

The default threshold is 100,000 bytes.

Fail CI after still emitting the report when attention is required:

```bash
python3 /tmp/repo-scout.pyz --format markdown --fail-on-attention .
```

Exit code 5 means the scan completed but attention findings were present.

Apply a shared team policy and fail CI when the repository violates it:

```bash
python3 /tmp/repo-scout.pyz --format markdown --policy examples/team-policy.toml .
```

Policy files use a strict, versioned TOML contract:

```toml
version = 4

[repository]
required_files = ["README.md", "SECURITY.md"]
required_file_groups = [["package-lock.json", "pnpm-lock.yaml", "yarn.lock"]]
forbidden_files = [".env", ".env.local"]
forbidden_file_patterns = ["**/.env", "**/.env.local"]
max_files = 5000
max_total_bytes = 50000000
require_clean_git = true
```

All rules are optional, but a policy must define at least one. Required and
forbidden file paths must be normalized paths relative to the repository, and
the same path cannot appear in both lists. In Git repositories, forbidden files
fail when tracked or unignored; ignored local files remain outside enforcement.
Non-Git scans enforce forbidden files directly from the folder. Unknown keys,
invalid values, and unsupported policy versions are rejected instead of being
silently ignored. Repo Scout continues to read policy versions 1 through 3;
version 2 adds exact `forbidden_files`, version 3 adds
`forbidden_file_patterns` for nested and filename-wide rules, and version 4
adds `required_file_groups`. Every group requires at least one listed path, so
one shared policy can accept npm, pnpm, or Yarn without accepting no lockfile.
The general
profiles use `**/.env` and `**/.env.local` for nested services. Broader patterns
such as `*.pem` match at any depth and belong in reviewed custom policies, not
the defaults. Each pattern reports at most 20 sorted paths plus the full match
count, keeping CI evidence bounded.

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

The counts-only default omits repository IDs, branches, commits, policy
fingerprints, and evidence paths; `--details` opts into repository-level
output. Schema-2 bundles identify normalized policy rules and the scanned Git
commit, so the aggregate can verify complete matching policy fingerprints
across two or more repositories. Results remain bundle-reported and do not
prove freshness. The aggregator accepts legacy schema-1 bundles, rejects
duplicate IDs, duplicate JSON keys, and malformed or contradictory metadata,
performs no uploads, and requires no API key.

Initialize an offline starter policy for a common repository type:

```bash
repo-scout-policy bootstrap .
repo-scout-policy bootstrap . --format json
repo-scout-policy verify-receipt bootstrap-receipt.json
repo-scout-policy recommend .
repo-scout-policy list
repo-scout-policy show python-service
repo-scout-policy init python-service
```

`bootstrap` recommends and writes `repo-scout-policy.toml` when no policy review
is required. It refuses to overwrite an existing file and stops on mixed Node
and Python repositories. Its stable JSON receipt records whether the policy was
created or replaced, its output path, selected starter, policy version, and
policy fingerprint for CI handoff evidence. Failed writes emit no receipt.
Save that JSON to a file and use `verify-receipt` to prove the current policy
still has the recorded version and fingerprint. A moved policy can be selected
with `--policy`; policy drift or a missing policy returns exit code 6 with
expected and actual identity evidence.
`recommend` uses local manifests and lockfiles, can emit stable JSON, and flags
mixed Python and Node repositories for review instead of presenting one starter
as a complete team policy.

Profiles are available for baseline services, Python services, flexible Node
services, npm-only services, and agent-ready services. The `node-service`
profile accepts npm, pnpm, or Yarn but still requires one committed lockfile.
Initialization protects existing files unless
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
evidence, and a downloadable schema-2 rollout bundle. It installs the `v0.3.29`
wheel only after checking its pinned digest, release manifest, source commit,
tag, signer workflow, and GitHub-hosted provenance. The bundle uses GitHub's
stable `owner/repository` identity and is preserved even when policy enforcement
fails. See
[docs/github-actions.md](docs/github-actions.md) for setup and failure handling.

## Team Pilot

Repo Scout's free core stays local and dependency-free. The $299 founding-team
pilot adds shared repository policies, CI rollout help, and one custom policy
pack for up to 10 repositories over 90 days. See [BUSINESS_MODEL.md](BUSINESS_MODEL.md)
for the offer and validation milestones.

[Request a founding-team pilot](https://github.com/becastil/Chats-empty-repo/issues/new?template=founding-team-pilot.yml&discovery_source=GitHub+repository+or+release)

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
discovery channel and groups ready, approval-dependent, and exploratory intent
without treating intent as cash. It also groups the primary purchase criterion
behind each request, including policy fit, rollout fit, evidence, privacy,
implementation capacity, and commercial fit, so repeated paid outcomes can
shape stronger policy packs and rollout playbooks. A deterministic sales queue ranks every open
pre-payment deal by declared readiness and funnel stage, then names the next
conversion action without advancing labels automatically.
Schema-7 reports also normalize the required team size, repository count, and
CI provider, confirm that a repository-standard answer exists without copying
its text into reports, and mark each request as target, outside-target, or
incomplete. Teams with more than 10 repositories are flagged for a first-10
subset rather than rejected.
See [docs/pilot-tracking.md](docs/pilot-tracking.md) for stage definitions and
privacy rules.

Maintainers can audit the private, alias-only direct-outreach ledger before a
contact session without sending messages or exposing recipients:

```bash
repo-scout-outreach outreach-private/outreach-ledger.csv \
  --as-of "$(date +%F)"
```

After the batch passes validation, surface one private, alias-only checklist for
the required human review without changing the ledger or sending a message:

```bash
repo-scout-outreach outreach-private/outreach-ledger.csv \
  --as-of "$(date +%F)" --review-next
```

Keep this review output private; it intentionally names the next ledger alias.

After a human completes all five checks, record approval for that exact next
alias with an explicit review date:

```bash
repo-scout-outreach outreach-private/outreach-ledger.csv \
  --as-of "$(date +%F)" \
  --approve-next prospect-001 \
  --approved-on "$(date +%F)" \
  --confirm-reviewed
```

The guarded action validates the full ledger before and after the change,
atomically records only `status=approved` and `approved_on`, and preserves the
ledger's file permissions. It refuses an alias other than the one shown by
`--review-next`. It does not send a message or create contact or follow-up dates.

After a human actually sends that approved message, record the send and its
required follow-up without hand-editing the ledger:

```bash
repo-scout-outreach outreach-private/outreach-ledger.csv \
  --as-of "$(date +%F)" \
  --record-contact prospect-001 \
  --contacted-on "$(date +%F)" \
  --confirm-sent
```

This action accepts only the next approved alias, retains `approved_on`, records
the contact date, and sets `next_action_on` to exactly seven days later. Its
private receipt names the manual follow-up date. Repo Scout sends no message and
schedules no automatic follow-up.

On that due date, after a human sends the one allowed follow-up, close the
cadence with a guarded record:

```bash
repo-scout-outreach outreach-private/outreach-ledger.csv \
  --as-of "$(date +%F)" \
  --record-follow-up prospect-001 \
  --followed-up-on "$(date +%F)" \
  --confirm-follow-up-sent
```

The action selects the earliest due contact, rejects an early or future send,
retains approval and initial-contact evidence, and clears `next_action_on` so no
second follow-up is scheduled. Repo Scout still sends nothing.

The reporter enforces the 10-prospect experiment, three-signal qualification,
one private HTTPS evidence link per signal, permitted contact channels, one
seven-day follow-up, and opt-out stop states. Schema-3 reports separate
personalized drafts awaiting review from messages actually sent and expose only
aggregate evidence-link counts, so neither draft preparation nor untraceable
qualification can inflate attempted-prospect counts.
Unreleased schema-5 reports add an explicit human-approved pre-send count and
require a retained approval date no later than contact, while keeping both
drafted and approved messages outside attempted outreach.
The auditor also rejects malformed CSV and any row with missing or extra cells
instead of silently dropping private sales evidence.
Its activity totals are not lead or revenue evidence. See
[docs/direct-outreach.md](docs/direct-outreach.md) for the operating contract.

Install it locally in editable mode:

```bash
python3 -m pip install -e .
repo-scout .
```

Repo Scout requires Python 3.11 or newer and has no runtime dependencies.

Portable, wheel, and source releases are available from GitHub with SHA-256
manifests and build-provenance attestations. Install and verify a specific
release using the commands in
[docs/releases.md](docs/releases.md).

Measure the public artifact request signal without granting the reporter network
or repository credentials:

```bash
curl -fsSL 'https://api.github.com/repos/becastil/Chats-empty-repo/releases?per_page=100' \
  | repo-scout-distribution
```

The report validates each release artifact contract and separates portable,
wheel, source, manifest, and unknown requests. Counts can include CI downloads,
maintainer checks, and retries, so they are not unique installs or revenue. See
[DISTRIBUTION.md](DISTRIBUTION.md) for the channel contract.

Save a JSON report as the weekly baseline, then pass it back on the next run for
signed request deltas and release-set changes:

```bash
curl -fsSL 'https://api.github.com/repos/becastil/Chats-empty-repo/releases?per_page=100' \
  -o releases.json
repo-scout-distribution --format json releases.json > distribution-baseline.json
repo-scout-distribution releases.json --baseline distribution-baseline.json
```

Join a baseline-aware distribution report to the current pilot funnel for one
honest weekly commercial review:

```bash
repo-scout-distribution --format json releases.json \
  --baseline distribution-baseline.json > distribution-current.json
repo-scout-pilot --format json --as-of "$(date -u +%F)" \
  pilot-issues.json > pilot-current.json
repo-scout-growth distribution-current.json pilot-current.json
```

The growth review reports signed reach movement, attributed pilot progress,
booked revenue, purchase-criterion outcomes, evidence warnings, and one current
bottleneck from acquisition through retention. Schema-5 pilot reports remain
readable with criterion evidence marked unavailable; schema-6 and schema-7
reports reconcile every criterion total to the same deals and revenue as source
reporting. The
review never calculates a download-to-lead conversion rate: GitHub artifact
requests are not unique people and cannot be assigned to a discovery source or
purchase criterion.

The reviewed public or counts-only baseline under [`metrics/`](metrics/)
provides the current comparison point and records why cumulative GitHub
requests and private outreach drafts are not users, leads, or revenue.

Run the tests:

```bash
python3 -m unittest discover -s tests
```

## Why This Exists

Developers often need to quickly understand an unfamiliar repository, especially at the start of a review, agent handoff, or maintenance session. `repo-scout` aims to provide the first useful page of context without requiring remote services, indexing daemons, or heavyweight project setup.
