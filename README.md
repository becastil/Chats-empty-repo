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
curl -fL https://github.com/becastil/Chats-empty-repo/releases/download/v0.3.51/repo-scout-0.3.51.pyz -o /tmp/repo-scout.pyz &&
python3 /tmp/repo-scout.pyz --version &&
python3 /tmp/repo-scout.pyz --languages .
```

Repo Scout requires Python 3.11 or newer. The portable file contains the free
primary CLI. Install the wheel when you also
need the `repo-scout-distribution`, `repo-scout-growth`, `repo-scout-policy`,
`repo-scout-rollout`, `repo-scout-pilot`, or maintainer-only
`repo-scout-outreach` commands:

```bash
python3 -m pip install https://github.com/becastil/Chats-empty-repo/releases/download/v0.3.51/repo_scout-0.3.51-py3-none-any.whl
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

Forced replacements are atomic and preserve the existing report's access
permissions. A failed replacement leaves the prior report unchanged.

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

The `--policy` argument must name a direct regular-file leaf. Repo Scout opens
that leaf once through a non-inheritable read-only descriptor, adding no-follow
and nonblocking flags where the platform provides them. The descriptor must
match the initially inspected file. Repo Scout parses and validates one exact
UTF-8 byte buffer, then rereads the bytes and rechecks the requested leaf at the
policy-acceptance checkpoint. Static symlinks, directories, FIFOs, and other
special files return exit code 2 before a scan report is emitted; a symlink
target is neither followed nor named. Replacement or same-inode mutation
detected at that checkpoint also fails closed. Policy input is capped at
128 KiB (131,072 bytes); the descriptor size and both bounded reads enforce the
ceiling before parsing and during the acceptance reread.

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
performs no uploads, and requires no API key. Duplicate-key errors JSON-escape
the decoded key so presentation controls cannot create extra terminal lines.
Unknown-field errors preserve ordinary printable key names but JSON-escape a
control-bearing decoded key before it enters operator output.
Parser and file-loading errors similarly preserve ordinary printable evidence
paths but JSON-escape a control-bearing path and exception context onto one
line. Successful detailed JSON retains the exact path as structured data.
Every input must be a direct
regular-file leaf no larger than 1 MiB (1,048,576 bytes). The command parses
one descriptor-bound UTF-8 buffer, then accepts it only if the exact bytes and
requested leaf remain unchanged. Repository IDs must be non-empty printable
strings of at most 128 characters without surrounding whitespace, and branch
metadata must be null or a non-empty printable string of at most 1,024
characters without surrounding whitespace. Values outside those contracts fail
with exit code 2 before bundle generation or summary output and are not echoed
in the error. Printable IDs may contain backticks; Markdown output selects a
code-span delimiter longer than the longest embedded run so the exact ID stays
inside one inline code value and remains unchanged in rollout metadata.

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
policy fingerprint for CI handoff evidence. The output leaf must be a direct
file path; initial and dangling symlinks fail even with `--force`, leave their
targets unchanged, and emit no receipt. Other failed writes also emit no
receipt.
Save that JSON to a file and use `verify-receipt` to prove the current policy
still has the recorded version and fingerprint. The receipt argument itself
must name a direct regular-file leaf. Symlinks, directories, FIFOs, other
special leaves, replacement, or in-place mutation return exit code 2 without a
verification report. Receipt JSON is parsed and validated through one opened
descriptor, then its exact bytes and requested leaf are rechecked before use.
Duplicate and unknown receipt-field errors preserve ordinary printable keys but
JSON-escape control-bearing decoded names onto one line before verification
output.
Receipt input is capped at 128 KiB (131,072 bytes), as is the selected policy;
oversized sparse files and growth during the bounded reread fail without
allocating the full input.
Receipt output evidence must be an absolute, valid file leaf; relative or
NUL-bearing values return exit code 2 before an override is considered. A moved
policy can be selected with `--policy`. The selected policy leaf must remain a
direct path: an initial or dangling symlink returns exit code 6, preserves the
requested leaf in the report, and neither follows nor names its target. It must
also be a regular file; directories, FIFOs, and other special leaves return
exit code 6 before the policy loader can read or block on them. Verification
parses and fingerprints the policy through one opened regular-file descriptor,
then rechecks its exact bytes and requested leaf. Replacing the path with a
symlink or a different regular file, even one with identical bytes, or changing
the opened file in place returns exit code 6 with actual identity unavailable.
Policy drift or a missing policy also returns exit code 6 with expected and
actual identity evidence.
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
evidence, and a downloadable schema-2 rollout bundle. It installs the `v0.3.51`
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

The dependency-free reporter counts booked pilots, payment-backed activations,
booked revenue, remaining distance to the three-pilot goal, annual conversions,
losses, label drift, and open pre-payment issues inactive for at least seven UTC
calendar days. Schema 10 preserves qualification, offer, and explicit activation
milestones on every detailed deal. Activation requires both `pilot-paid` and
`pilot-active`; later stages do not substitute for either human-applied event.
Growth reviews derive qualification and offer progression alongside booked
revenue for each self-reported discovery channel, readiness state, and purchase
criterion without treating intent as cash. They validate global and per-segment
activation counts from detailed deals and prioritize any
booked-but-unactivated pilot before another sale, retention work, or expansion.
For schema-9+ evidence, the joined report also emits a public-safe activation
queue with the exact issue number, lifecycle stage, source, readiness, purchase
criterion, and canonical delivery or reconciliation action for every
booked-but-unactivated pilot. It never copies issue titles, repository
standards, contracts, payment details, or customer acknowledgement into that
queue.
The report also groups the primary purchase criterion
behind each request, including policy fit, rollout fit, evidence, privacy,
implementation capacity, and commercial fit, so repeated paid outcomes can
shape stronger policy packs and rollout playbooks. A deterministic sales queue ranks every open
pre-payment deal by declared readiness and funnel stage, then names the next
conversion action without advancing labels automatically.
Ready-to-purchase requests receive the normal stage-specific terms or payment
action only when the CI provider is GitHub Actions, the qualification is
target-profile, and the requested scope is within the 10-repository offer.
Recognized non-GitHub providers require the private integration decision first;
missing, edited, no-response, or ambiguous provider evidence requires provider
clarification. Ready GitHub requests with incomplete or outside-target evidence
require qualification review, while larger target requests require an explicit
first-10 scope. Queue membership, ranking, classification, and revenue
accounting remain unchanged. Schema-7+ growth bottlenecks that would send terms,
confirm payment, or close the next pilot point back to this
qualification-aware queue after validating each exact action against its stage,
readiness, qualification, provider, and public-intake-bound price. When that
validated queue is empty during a pre-target milestone, growth retains
historical milestones but says no open pre-payment deal exists and recommends
replenishing the queue instead of inventing a deal action. At those pre-target
stages, an open request with untracked or conflicting lifecycle evidence
requires label repair before another sales action, even when another deal is
already queued. Saved schema-7+ evidence that omits or adds an open queue member,
changes its stage, readiness, or action-driving qualification fields, disagrees
with stage totals or cumulative source progression, or bypasses another queue
boundary fails growth ingestion.
Pilot issue JSON with duplicate keys is rejected before issue parsing, so
conflicting `labels` fields cannot silently change booked-pilot or revenue
totals.
The joined growth command applies the same fail-closed rule at every depth of
both saved distribution and pilot reports. A repeated field exits with code 2,
emits no growth report, and identifies only the report type and escaped key,
so duplicate booking or activation evidence cannot be resolved silently by the
JSON decoder.
Issue titles are trimmed, then must be non-empty printable text of at most
1,024 characters. Any remaining line break, terminal control, bidirectional
control, Unicode separator, or oversized text fails with exit code 2 before a
funnel report is emitted, and the error does not echo the title. Issue URLs
must be empty or printable text of at most 2,048 characters without surrounding
whitespace. Unrecognized edited form answers and pilot labels remain available
in escaped JSON review fields, but terminal-facing warnings use generic
messages and never interpolate those values.
Schema-7+ reports also normalize the required team size, repository count, and
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
  --as-of "$(date -u +%F)"
```

When JSON is destined for a committed measurement baseline or CI artifact,
require the report to be alias-free before Repo Scout writes it:

```bash
repo-scout-outreach outreach-private/outreach-ledger.csv \
  --as-of "$(date -u +%F)" --format json \
  --require-counts-only > outreach-baseline.json
```

If an approved send or due follow-up makes the report private, the guard writes
nothing to standard output and exits with code 7. It is mutually exclusive with
review and lifecycle actions, so it cannot approve, decline, or mutate a ledger.

After the batch passes validation, surface one complete private checklist for
the required human review without changing the ledger or sending a message:

```bash
repo-scout-outreach outreach-private/outreach-ledger.csv \
  --as-of "$(date -u +%F)" --review-next \
  --include-private-evidence \
  --include-private-draft outreach-private/drafts.md \
  --write-review outreach-private/next-review.md
```

The command creates an owner-only private file only after the complete bundle
has been written, keeps its alias and evidence out of terminal output, and
refuses to overwrite an earlier review. The bundle contains the next ledger
alias, qualification sources, draft, the canonical source-preserving
direct-outreach route, SHA-256 review receipt, and exact content-bound approval
and decline commands. Their `YYYY-MM-DD` placeholders must be replaced with the
actual UTC decision date; the receipt remains valid across dates only while the
reviewed row, draft, route, and checklist are unchanged.
Before emitting that receipt, the complete review requires that canonical route
exactly once in the selected private draft. A missing or repeated route fails
without a review bundle or ledger mutation; redacted and draft-only inspection
remain available for correction.
It also requires the disclosed `$299` price exactly once so the approved
attempt tests the stated paid offer. Missing or repeated price text has the
same no-bundle, no-mutation boundary.
Remove or privately archive the bundle after the human decision before writing
the next review.
After a content-bound decline, the generated continuation retains the evidence
and draft flags and uses `--write-review 'PRIVATE-REVIEW-PATH'`. Replace the
literal inside those existing quotes with a new ignored owner-only destination;
a path containing spaces remains one shell argument, and leaving it unchanged
fails before private material is read. A valid path keeps the next complete
review out of terminal capture.
Omit `--as-of` to use the current UTC calendar date; the explicit UTC date in
these examples keeps the initial ledger audit reproducible across operator
timezones without becoming a later approval date.

After a human completes all six checks, including confirming the draft uses the
displayed direct-outreach route, record approval for that exact next
alias with the exact command emitted by the review. Its shape is:

```bash
repo-scout-outreach outreach-private/outreach-ledger.csv \
  --as-of "$(date -u +%F)" \
  --approve-next prospect-001 \
  --approved-on "$(date -u +%F)" \
  --confirm-reviewed \
  --review-digest 'sha256:<digest-from-review-output>' \
  --reviewed-private-draft outreach-private/drafts.md
```

The guarded action validates the full ledger before and after the change,
atomically records only `status=approved` and `approved_on`, and preserves the
ledger's file permissions. It refuses an alias other than the one shown by
`--review-next`, and refuses when the reviewed row or private draft changed
after the receipt was created. It does not send a message or create contact or
follow-up dates.

After a human actually sends that approved message, record the send and its
required follow-up without hand-editing the ledger:

```bash
repo-scout-outreach outreach-private/outreach-ledger.csv \
  --as-of "$(date -u +%F)" \
  --record-contact prospect-001 \
  --contacted-on "$(date -u +%F)" \
  --confirm-sent
```

This action accepts only the next approved alias, retains `approved_on`, records
the contact date, and sets `next_action_on` to exactly seven days later. Its
private receipt names the manual follow-up date. Repo Scout sends no message and
schedules no automatic follow-up. The generated contact-recording command uses
date placeholders so approval and sending on different days cannot silently
backdate the send.

On that due date, after a human sends the one allowed follow-up, close the
cadence with a guarded record:

```bash
repo-scout-outreach outreach-private/outreach-ledger.csv \
  --as-of "$(date -u +%F)" \
  --record-follow-up prospect-001 \
  --followed-up-on "$(date -u +%F)" \
  --confirm-follow-up-sent
```

The action selects the earliest due contact, rejects an early or future send,
retains approval and initial-contact evidence, and clears `next_action_on` so no
second follow-up is scheduled. The contact receipt shows the due date but leaves
the actual follow-up send date as placeholders, preserving a later send
truthfully. Repo Scout still sends nothing.

When a human observes a reply or stop condition, record the exact alias and
outcome without hand-editing the private ledger:

```bash
repo-scout-outreach outreach-private/outreach-ledger.csv \
  --as-of "$(date -u +%F)" \
  --record-outcome prospect-001 \
  --outcome pilot-requested \
  --outcome-on "$(date -u +%F)" \
  --confirm-outcome-observed
```

The guarded action accepts `replied`, `pilot-requested`, `price-objection`,
`existing-solution`, `not-a-fit`, or `do-not-contact` after contact, preserves
approval and send history, and clears any pending follow-up. `--as-of` is the
UTC ledger-audit date, while the required `--outcome-on` retains when the human
actually observed the response or stop condition. A terminal
`price-objection` preserves human-observed willingness-to-pay evidence in the
dedicated `price_objections` aggregate without treating it as demand or
revenue. A terminal `existing-solution` preserves explicit substitute or DIY
preference in `existing_solution_objections`, without storing response text or
claiming a competitor win. The action sends nothing. Only public pilot intake
and paid funnel stages count as demand or revenue.

The reporter enforces the 10-prospect experiment, three-signal qualification,
one private HTTPS evidence link per signal, permitted contact channels, one
seven-day follow-up, and opt-out stop states. Schema-3 reports separate
personalized drafts awaiting review from messages actually sent and expose only
aggregate evidence-link counts, so neither draft preparation nor untraceable
qualification can inflate attempted-prospect counts.
Schema-9 reports add explicit human-approved and review-declined pre-send counts,
require a retained approval date no later than contact, and keep researched,
drafted, approved, and review-declined rows outside attempted outreach. They
also separate dated outcomes from legacy outcomes whose observation date was
never retained. When an approval receipt is no longer visible, the report
recovers only the next approved alias and an exact manual-send recording
handoff with required date placeholders. It still omits the draft, evidence,
channel, and approval date. A machine-readable `private_output` flag and matching
text note mark reports with that alias or any due-follow-up alias as private;
only reports containing neither are marked counts-only. A review-declined row
counts as closed without becoming a contact attempt. The auditor also rejects
malformed CSV and any row with missing or extra cells instead of silently
dropping private sales evidence. Schema-10 reports add the terminal
`price-objection` state and a dedicated `price_objections` count so the bounded
experiment can separate explicit price resistance from a generic fit rejection.
Schema-11 reports add the terminal `existing-solution` state and a dedicated
`existing_solution_objections` count so observed substitute resistance remains
separate from price and fit objections. Its activity totals are not lead or
revenue evidence. See
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
Raw release exports and saved distribution baselines reject duplicate JSON
keys at every depth before request totals or signed movement are calculated.
Failures emit no report and identify only the input type and escaped repeated
key, never either competing count.
Their shared asset parser also requires every asset name to be non-empty
printable text. Line, terminal, Unicode-separator, and bidirectional controls
fail with a location-only error before classification, warnings, counts, or
movement, while ordinary printable Unicode names remain exact.

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
readable with criterion evidence marked unavailable; schema-6 through schema-10
reports reconcile every criterion total to the same deals and revenue as source
reporting. Schema 8 adds detailed qualification and offer progression across
every segment. Schema 9 adds payment-backed activation evidence and inserts an
activation bottleneck after payment but before another pilot sale. Schema 10
attributes activation across source, readiness, and purchase criterion and
rejects segment totals that do not reproduce the detailed deals. Schemas 5
through 8 remain readable with activation and its action queue marked
unavailable rather than zero or empty. Schema-9+ reviews derive one ordered
action for each booked-but-unactivated deal, prioritizing live paid delivery
before terminal lifecycle reconciliation. The review never calculates a
download-to-lead conversion rate: GitHub artifact requests are not unique
people and cannot be assigned to a discovery source or purchase criterion.

The reviewed public or counts-only baseline under [`metrics/`](metrics/)
provides the current comparison point and records why cumulative GitHub
requests and private outreach drafts are not users, leads, or revenue.

Run the tests:

```bash
python3 -m unittest discover -s tests
```

## Why This Exists

Developers often need to quickly understand an unfamiliar repository, especially at the start of a review, agent handoff, or maintenance session. `repo-scout` aims to provide the first useful page of context without requiring remote services, indexing daemons, or heavyweight project setup.
