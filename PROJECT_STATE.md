# Project State

## Current Project

`repo-scout` is a dependency-free Python CLI that summarizes local repository state for developer handoffs, reviews, and work-session orientation.

The repository also includes a small hosted web companion that explains the CLI and lets visitors switch between sample text and JSON snapshots.

Revenue is the primary product constraint. The free CLI is the adoption layer for a paid team policy and CI enforcement offer documented in `BUSINESS_MODEL.md`.

The delivery goal is 1,000 meaningful commits. This update is commit 51 of 1,000, with 949 remaining. Quality, test coverage, distribution, and revenue alignment take priority over commit volume.

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
- Five packaged starter profiles for baseline, Python, flexible Node, npm-only, and agent-ready services.
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
- Deterministic stale-deal follow-up with explicit UTC dates, thresholds, and issue-activity ages.
- Follow-up data-quality warnings for missing, future, and closed pre-payment records.
- Host-derived Open Graph and X metadata with a product-specific social preview.
- Sites hosting metadata and a Cloudflare Workers-compatible production build.
- Tag-driven wheel and source releases with strict version alignment and exact artifact validation.
- Hash-locked release build tooling, deterministic SHA-256 manifests, and clean-environment command smoke tests.
- GitHub build-provenance attestations and immutable-action release automation.
- Explicit MIT license text included in packaged distributions.
- Required self-reported discovery channels in founding-team pilot intake.
- Schema-3 source attribution for qualification, offers, booked revenue, conversion, loss, and follow-up.
- Explicit missing, unknown, and ambiguous source warnings for legacy or edited issues.
- Copy-ready and dogfooded CI bootstrap from a versioned Repo Scout wheel instead of a source checkout.
- Independent wheel digest, release manifest, source commit, tag, signer workflow, and hosted-runner verification.
- Runner-temp virtual-environment installation that leaves the protected checkout unchanged.
- Markdown first-repository rollout bundles generated from evaluated team-policy evidence.
- Automated readiness checks separated from explicit, unchecked team handoff actions.
- Rollout remediation evidence preserved before policy exit code 6.
- Schema-1 non-sensitive rollout metadata embedded in first-repository Markdown bundles.
- Required stable logical repository IDs with strict validation and no collision-prone implicit defaults.
- Dependency-free multi-repository rollout summaries in deterministic text and JSON.
- Duplicate, malformed, unsupported, and contradictory evidence rejection.
- Counts-only aggregate privacy defaults with explicit repository-detail opt-in.
- Schema-2 rollout evidence with normalized policy fingerprints and exact Git commit IDs.
- Backward-compatible schema-1 aggregation with explicit policy and commit identity coverage.
- Shared-policy verification only for complete matching fingerprints across multiple repositories.
- Copy-ready and dogfooded CI generation of schema-2 rollout bundles from the verified `v0.3.23` release.
- Stable GitHub `owner/repository` evidence identity with 14-day passing and remediation artifacts.
- Required self-reported $299 purchase readiness in public pilot intake.
- Schema-4 funnel reporting for readiness-stage, revenue, conversion, and loss outcomes.
- Explicit missing, unknown, and ambiguous readiness warnings for legacy or edited issues.
- Hosted cross-repository rollout proof with policy-fingerprint coverage, scanned-commit coverage, remediation visibility, and a price-specific pilot CTA.
- Deterministic sales-action queues ranked by disclosed purchase readiness, funnel stage, issue age, and issue number.
- Stage-specific next actions for ready, approval-dependent, exploratory, missing, and unrecognized purchase intent.
- Single-file, no-install zipapp distribution for the free primary CLI.
- Release checksums, provenance attestations, and direct-execution smoke tests covering the portable artifact.
- Public package URLs and checkout-free website and README onboarding.
- Dependency-free distribution reporting from exported public GitHub release records.
- Version-aware portable, wheel, source, and checksum artifact contract audits.
- Explicit separation of primary artifact requests from unique installs, activation, pilot demand, and revenue.
- Backward-compatible weekly distribution baselines with signed per-channel request deltas.
- New-release, removed-release, removed-asset, and decreasing-counter evidence warnings.
- Dependency-free weekly growth reviews that join signed distribution movement to attributed pilot, offer, and booked-revenue evidence.
- Deterministic commercial bottlenecks from missing measurement through acquisition, qualification, offer, payment, pilot target, retention, and validation.
- Explicit refusal to calculate download-to-lead conversion rates from non-unique artifact requests.
- Required self-reported primary purchase criteria in public pilot intake.
- Schema-6 criterion totals for qualification, offers, booked revenue, conversion, and loss.
- Normalized criterion evidence across deals, stale follow-up, and sales queues with explicit missing, edited, and duplicate-answer warnings.
- Backward-compatible schema-5 and schema-6 pilot support in weekly growth reviews.
- Schema-2 growth reviews with ordered purchase-criterion qualification, offer, payment, conversion, and loss outcomes.
- Exact criterion-taxonomy and cross-segment reconciliation against source totals.
- Explicit schema-5 criterion unavailability and schema-6 missing or ambiguous criterion evidence warnings.
- A plain-language website objection section that separates the copyable free scan from the paid team rollout outcome.
- A source-identifiable website acquisition experiment with a dated review point and funnel-based success evidence.
- An above-fold GitHub README path from the team problem and disclosed $299 offer into the website experiment or pilot intake.
- Source-prefilled, buyer-editable pilot application links for website and GitHub repository discovery paths.
- Server-rendered campaign routes that preserve GitHub, outreach, referral, search, social, and website source context through the hosted offer.
- Closed campaign-source mapping with safe website fallback for missing or unsupported values.
- A user-initiated referral email action with disclosed price, local-code boundary, and source-preserving team-offer link.
- No-account referral sharing that sends nothing automatically and records no address or click event.
- Canonical search metadata that collapses every campaign-query variant onto one production page.
- Deterministic crawler policy and one-page sitemap routes with no campaign URLs.
- A recorded zero-request acquisition baseline that keeps crawler access and release activity separate from demand.
- Accurate JSON-LD separating the current free CLI download from the $299 founding-team service.
- Shared release identity across visible onboarding and machine-readable download metadata.
- Explicit omission of unearned reviews, ratings, hidden urgency, and campaign URLs from structured offers.
- A copy-ready direct-outreach playbook with an exact $299 offer, source route, qualification filter, and bounded follow-up cadence.
- A header-only private outreach ledger template with an ignored working directory and no committed prospect data.
- Tested anti-spam, opt-out, false-urgency, and revenue-evidence boundaries for the first 10-prospect batch.
- A dependency-free `repo-scout-outreach` auditor for private, alias-only campaign ledgers.
- Strict three-signal qualification, permitted-channel, 10-prospect, seven-day follow-up, and terminal-stop validation.
- Aggregate outreach activity and due-alias reporting that remains explicitly separate from lead and revenue evidence.
- Backward-compatible policy v2 `forbidden_files` rules with normalized exact paths and contradictory-rule rejection.
- Git-aware forbidden-file enforcement that catches tracked or unignored files without failing properly ignored local environment files.
- Manual team-policy, CLI, fingerprint, and compatibility coverage for `.env` and `.env.local` protection.
- Policy v2 `.env` and `.env.local` protection in all packaged starters, dogfood policy, and copy-ready CI policy.
- End-to-end copy-ready evidence proving forbidden-file failures still emit remediation-ready rollout bundles.
- Backward-compatible policy v3 `forbidden_file_patterns` for nested monorepo and filename-wide protection.
- Git-aware pattern matching across all tracked or unignored paths, independent of the snapshot's 500-path detail cap.
- Bounded pattern evidence with full match counts, 20 sorted paths per pattern, and explicit truncation state.
- Strict wildcard, path, duplicate, required-file conflict, exact-rule overlap, and fingerprint validation for pattern rules.
- Independently pinned `v0.3.23` wheel digest, source commit, manifest, provenance, signer workflow, and hosted-runner checks in both policy gates.
- Policy v3 nested `.env` and `.env.local` patterns in every starter, dogfood policy, and copy-ready CI policy.
- Released-wheel proof that a force-tracked nested environment file fails while preserving remediation rollout evidence.
- Explicit exclusion of broad `*.pem` matching from defaults to avoid blocking legitimate public certificates.
- Backward-compatible policy v4 `required_file_groups` for standards with valid file alternatives.
- Stable one-violation-per-group evidence and order-independent group fingerprints.
- Strict empty, duplicate, exact-rule, and forbidden-pattern contradiction checks for required groups.
- A packaged `node-service` starter that accepts one npm, pnpm, or Yarn lockfile while still rejecting no lockfile.
- Human-readable required alternatives in policy discovery and normalized group rules in JSON discovery.
- The retained npm-only starter for teams whose standard intentionally excludes pnpm and Yarn.
- Released-wheel proof that `node-service` initializes and enforces correctly in clean npm, pnpm, and Yarn repositories.
- A release-blocking installed-wheel smoke test for all three supported Node lockfiles and missing-lockfile remediation evidence.

## How To Run

```bash
curl -fL https://github.com/becastil/Chats-empty-repo/releases/download/v0.3.24/repo-scout-0.3.24.pyz -o /tmp/repo-scout.pyz
python3 /tmp/repo-scout.pyz --languages .
python3 -m unittest discover -s tests
```

## Next Small Task

Obtain authoritative company and contact evidence, then research, contact, and audit the first five qualified prospects. No outreach was attempted and no private ledger exists; do not add another acquisition asset before five real attempts. If authoritative prospect evidence remains unavailable, independently verify and pin `v0.3.24` before making another paid-policy change.
