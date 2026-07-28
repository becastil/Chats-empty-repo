# Project State

## Current Project

`repo-scout` is a dependency-free Python CLI that summarizes local repository state for developer handoffs, reviews, and work-session orientation.

The repository also includes a small hosted web companion that explains the CLI and lets visitors switch between sample text and JSON snapshots.

Revenue is the primary product constraint. The free CLI is the adoption layer for a paid team policy and CI enforcement offer documented in `BUSINESS_MODEL.md`.

The delivery goal is 1,000 meaningful commits. This update is commit 275 of
1,000, with 725 remaining. Quality, test coverage, distribution, and revenue
alignment take priority over commit volume.

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
- Direct report writing with overwrite protection plus permission-preserving,
  mutation-free atomic `--force` replacement for existing evidence.
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
- A tested paid-pilot delivery contract for private scope, shipped-command
  acceptance evidence, and human-applied payment, activation, and conversion
  boundaries.
- A copy-ready private pilot delivery record with exactly 10 repository slots,
  CI integration selection, five deliverable checklists, first-repository
  acknowledgement, and 90-day closeout evidence.
- An ignored, owner-only `pilot-private/` local fallback with executable ignore
  verification for short-lived completed delivery records.
- A public `pilot-active` handoff tied to every private delivery activation
  condition, with executable proof that the local fallback receives
  `700/600` permissions in the local and hosted pilot contract suites.
- Unit tests covering scanner behavior and JSON CLI output.
- Responsive Repo Scout web companion with a server-rendered snapshot lab and accessible format toggle.
- A hosted founding-team pilot offer with price, scope, implemented policy proof, and a direct conversion CTA.
- A structured public pilot intake that qualifies team size, repository count, CI provider, and policy need.
- A dependency-free pilot funnel reporter with stable text and JSON revenue summaries.
- Duplicate-key-safe pilot issue ingestion that rejects ambiguous payment
  labels before revenue reporting, with source and installed-command proof that
  no report or label value is emitted.
- Bounded printable pilot issue titles that reject forged lines, terminal
  controls, bidirectional controls, Unicode separators, and oversized text
  before any commercial report can be emitted.
- Empty-or-printable pilot issue URLs capped at 2,048 characters without
  surrounding whitespace before operator output.
- Generic operator warnings for unrecognized public form answers and pilot
  labels, retaining raw values only in structurally escaped JSON fields.
- Qualification-aware ready-buyer actions that preserve normal terms and
  payment guidance only for target-profile GitHub Actions requests within the
  10-repository offer. Non-GitHub or unresolved CI evidence retains its
  integration gate, incomplete or outside-target GitHub evidence requires
  scope review, and larger target requests require an explicit first-10 scope.
  Schema-7 growth ingestion validates every queue action against its stage,
  readiness, qualification, CI provider, and configured price before its
  commercial bottlenecks defer to that queue.
- Strict positive-integer pilot price, target, and inactivity controls that
  reject booleans, floats, and strings before revenue evidence is built.
- Release-blocking installed-wheel proof that offers remain outside revenue,
  paid pilots book $299 toward the $897 target, and qualification, attribution,
  sales queues, and non-sensitive reporting retain their commercial semantics.
- Cumulative GitHub labels for lead, qualification, offer, payment, activation, conversion, and loss.
- A dependency-free live audit and conservative repair command for the seven public pilot lifecycle labels.
- A dedicated GitHub check that detects intake-label drift without deleting unexpected labels.
- A dedicated pilot-intake workflow contract covering both trigger blocks,
  read-only permissions, immutable actions, bounded runtime, exact test and
  live-label commands, test-before-audit ordering, and the absence of repair,
  secrets, or failure masking. The workflow runs the complete pilot-funnel
  behavior suite, including payment-backed conversion accounting, before the
  live audit and watches that suite's fixture plus every commercial document
  read by the paid-delivery tests.
- Label-drift warnings and tested $299 pilot / $897 target accounting semantics.
- Exact `pilot-paid` revenue recognition that keeps later-stage label drift
  visible without treating missing payment evidence as booked revenue.
- Payment-backed annual-conversion accounting that preserves skipped-stage
  warnings without letting unsupported retention evidence enter overall or
  segmented funnel and growth totals.
- Executable commercial-documentation proof that later lifecycle labels cannot
  substitute for the human-applied payment event.
- Missing-stage warnings for loss records that lack the cumulative public lead
  history required by the pilot funnel.
- Conflict-safe terminal accounting that excludes converted-and-lost records
  from both resolved outcome totals while retaining historical booked revenue.
- Deterministic stale-deal follow-up with explicit UTC dates, thresholds, and issue-activity ages.
- Follow-up data-quality warnings for missing, future, and closed pre-payment records.
- Host-derived Open Graph and X metadata with a product-specific social preview.
- Sites hosting metadata and a Cloudflare Workers-compatible production build.
- A dependency-free production audit that reconciles canonical metadata, the
  free structured offer, project release version, structured and visible
  portable download URLs, paid pilot service, website-attributed application
  link, and the link's visitor-facing $299 price.
- A read-only daily production workflow that runs its workflow and auditor
  behavior contracts before the live release-identity and $299 conversion-path
  audit, with immutable action pins and no repository secrets.
- A contract-tested public-site deployment handoff that binds the exact tested
  source, lockfile, hosted Node runtime, archive digest, and existing Sites
  project in a fail-closed candidate receipt. A read-only independent mode
  strictly verifies the receipt against clean synchronized source and the
  archive before source-export approval without running Node, npm, packaging,
  network, export, save, or deployment operations. The later pre-save form
  performs read-only network checks against the approval-bound Sites source
  repository. The handoff requires explicit source-export approval before any
  push to that separate repository, keeps saved versions distinct from live
  production, requires separate deployment approval, and immediately audits a
  successful publish. Sites versions 46 and 47 are superseded and must not be
  published.
- A canonical `.nvmrc` pin for exact Node `22.13.0` candidate builds, shared by
  local preflight, candidate receipts, and the hosted dependency contract.
  Strict parsing rejects malformed pins before commands run, while package
  metadata retains `>=22.13.0` as the general compatibility floor.
- A scope-constrained Sites archive validator that permits only canonical
  regular files and directories under `dist/`, rejecting path aliases, links,
  devices, pipes, and unrelated source before a candidate receipt is written.
- Schema-2 Sites receipts that bind every tested payload file's canonical path,
  permission mode, and bytes before packaging, then require the helper-produced
  archive and later read-only verification to reproduce that digest exactly.
  macOS AppleDouble metadata is disabled rather than admitted around the scope
  boundary.
- A schema-3 test-bracketed payload checkpoint that builds once, adds the
  candidate manifest, captures all deployable paths, modes, and bytes, runs
  site tests against that exact existing output, and rejects any ignored
  build-output drift before the packaging helper can run.
- A schema-4 complete-tree payload digest that binds every regular directory
  and file path, entry type, and deterministic permission mode alongside file
  size and bytes. Tested directories must be `0755`, packaging uses an explicit
  `022` umask, and injected empty directories or archive-mode drift fail closed.
- A schema-5 owner-review identity that strictly reads `project.version` from
  `pyproject.toml`, requires the website's single `RELEASE_VERSION` declaration
  to match before commands run, binds that public release version into the
  archived manifest and receipt, verifies it against the checkout, and prints
  it beside the commit and receipt digest for source-export approval. The
  read-only hosted site contract watches both release-identity sources.
- Receipt-bound Sites project identity in preparation and verification results
  and CLI output. Source-export approval now records the validated existing
  `project_id` with the public release version, receipt digest, canonical source
  repository, source ref, and commit instead of leaving the target project to
  an operator inference.
- A copy-ready pending Sites source-export request emitted only after offline
  independent verification. The request locally canonicalizes the existing
  source repository, rejects `origin`, and carries the complete approval tuple
  in one compact JSON record with boolean `deployment_approved=false`.
  Candidate status is also single-line JSON, so opaque IDs and filenames cannot
  inject sibling fields or terminal lines. Raw repository whitespace fails
  while percent-encoded URL paths remain valid. The request cannot be combined
  with the post-export pre-save mode or mistaken for tool-granted consent.
- Duplicate-free Sites JSON evidence across checkout hosting metadata,
  schema-5 receipts, and archived manifests. Repeated keys fail even when their
  values match, preventing approval identity from depending on decoder-specific
  first-key or last-key behavior.
- Candidate source-stability checks that repeat clean `HEAD == origin/main`
  validation after the long test phase, after packaging, and at the end of
  read-only verification, requiring the same synchronized commit at every
  acceptance checkpoint before a receipt or approval-ready success.
- Branch-bound Sites source evidence requiring the checkout to remain on
  `refs/heads/main` at every synchronized-source checkpoint. Detached HEAD and
  alternate local branches fail even when their commit equals `origin/main`,
  so the receipt's recorded source ref matches the source actually validated.
- Archive-stable Sites evidence that records the packaged digest before
  structural validation and requires the same regular archive and digest after
  the final synchronized-source checkpoint. A persistent path or byte change
  withholds both the candidate receipt and read-only verification success.
- No-clobber Sites candidate publication that refuses pre-existing outputs,
  packages into a private same-filesystem staging directory, validates that
  staged archive, and atomically links the archive and synced receipt into
  their requested paths only when absent. A destination claimed after
  preflight remains unchanged and withholds approval-ready success.
- Symlink-visible Sites evidence paths that resolve parent directories without
  dereferencing the requested archive or receipt leaf. Initial and dangling
  leaf symlinks fail before commands or evidence reads, while an existing
  symlinked parent that resolves inside the repository fails containment.
- Filesystem-identity-aware Sites output containment that walks existing
  archive and receipt parent ancestors against every non-symlink repository
  directory, rejects stable alternate-spelling, whole-repository, and
  subdirectory-only aliases, deduplicates directory identities to avoid mount
  cycles, and fails closed when traversal or identity checks report errors.
- Destination-anchored Sites evidence publication that requires existing
  output parents and supported POSIX descriptor-relative staging and hard
  links, opens each unique parent once before commands, keeps its descriptor
  non-inheritable and live through validation, reuses one descriptor for shared
  parents, and creates each no-clobber leaf relative to that held identity so a
  later path replacement cannot redirect publication.
- Archive-staging-anchored Sites evidence that creates a private `0700`
  directory relative to the held archive parent, accepts only the regular
  archive opened through that directory descriptor, and retains that file
  through hashing, tar validation, source recheck, and publication. Publication
  requires the current source leaf to match the held file immediately before
  resolving it relative to the staging directory, then requires the new output
  to share that same identity. Cleanup removes only recorded archive and
  directory identities, preserving uncertain replacements and failing instead
  of deleting them.
- Receipt-staging-anchored Sites evidence that creates a private `0600` leaf
  relative to the held receipt parent, writes, syncs, hashes, rechecks, and
  publishes through one non-inheritable regular-file descriptor, and requires
  the staged digest to equal the intended serialized JSON bytes. Publication
  resolves the source leaf relative to that same held parent and requires it
  to retain the held file's identity. Cleanup removes only the recorded
  identity, preserves replacements, reports uncertainty, and closes both
  staged and partially transferred published descriptors on failure.
- Published-file-anchored Sites evidence checks that open each new archive and
  receipt relative to its held parent, require it to share the staged source's
  filesystem identity, retain non-inheritable file descriptors through the
  final source and digest checks, and reconcile the requested parent and leaf
  identities before reporting success.
- Receipt-stable Sites verification that parses one exact byte buffer and
  requires the same regular receipt and digest after archive and source
  validation. Mutation or replacement with a link during verification
  withholds approval-ready success.
- Approval-pinned Sites receipt identity that records the exact staged receipt
  SHA-256, repeats source, archive, and receipt checks after publication,
  exposes that digest in preparation and verification output, and lets the
  pre-save check require the digest the owner approved. Semantically equivalent
  reserialization therefore fails closed across the approval interval.
- Export-bound Sites pre-save verification that requires the owner-approved
  receipt digest plus the canonical remote identity of the existing Sites
  repository recorded in the same approval. It resolves operational aliases,
  rejects local source, `origin`, unrelated forks, equivalent aliases, and
  repository identity drift, then checks the approval-bound
  `refs/heads/main` twice with read-only `git ls-remote` before version saving.
  The earlier pre-approval verification remains offline.
- Atomic Sites pre-save mode requiring the approved receipt digest,
  operational repository, and approved canonical repository identity together.
  Digest-only verification cannot report a pre-save success without the
  exported-source network and commit checks.
- Authority-bound Sites repository identity that normalizes standard Git,
  HTTP, HTTPS, and SSH ports across legitimate protocol aliases while retaining
  every non-default port. A matching host, path, and commit on an unapproved
  port therefore cannot satisfy source-export approval.
- A zero-vulnerability site dependency lock with Next `16.2.11`, React and
  React Server Components `19.2.8`, `brace-expansion` `5.0.8`, current
  Cloudflare and Vite tooling, and advisory-fixed PostCSS and Sharp overrides.
  Direct ESLint 10, TypeScript, React Hooks, and Next rule sets preserve linting
  without the vulnerable legacy config bundle. Sites version 47 contains the
  prior lock and is superseded; production is unchanged.
- A read-only hosted site dependency contract that runs on relevant lock and
  workflow changes, manual dispatch, and a weekly schedule. It installs the
  exact lock on Node `22.13.0`, requires zero reported vulnerabilities, builds
  and exercises the patched runtime, and lints without repository secrets or
  write permissions.
- Enabled repository vulnerability alerts and review-only automated security
  fixes, backed by a low-noise Dependabot policy. npm proposals are grouped and
  security-only; pinned GitHub Actions updates run weekly, group minor and patch
  changes, and allow at most two open version-update pull requests. Nothing
  auto-merges or deploys.
- Advanced `actions/checkout` from `v7.0.0` to the verified full-commit pin for
  `v7.0.1` across all six hosted workflows and the copy-ready customer gate.
  Executable pin contracts moved with the runtime references.
- Advanced `actions/setup-python` from `v6.3.0` to the verified full-commit pin
  for `v7.0.0` across all five Python workflows and the copy-ready customer
  gate. The used `python-version` input and Node 24 runtime are unchanged, the
  removed `pip-install` input is unused, and hosted evidence confirms Python
  3.11.15 through the complete paid-CI activation path.
- A repository-wide action-pin audit covering all 17 external references across
  the six hosted workflows and copy-ready customer gate. It rejects mutable
  refs, missing exact release annotations, split identities for one action, and
  dogfood/customer action-sequence drift, including the previously uncovered
  pilot-intake pins.
- Direct hosted enforcement of that action audit whenever its script, test, or
  any workflow changes. The dependency job invokes the audit before Node setup
  and general test discovery, so deleting its test cannot silently remove the
  paid-CI supply-chain gate.
- Tag-driven wheel and source releases with strict version alignment and exact artifact validation.
- Hash-locked release build tooling with the advisory-fixed `setuptools`
  `83.0.0` wheel digest, exact package/version/hash contract evidence,
  deterministic SHA-256 manifests, and clean-environment build and command
  smoke tests.
- Fail-closed checksum manifest publication that rejects symlinked or other
  non-regular `SHA256SUMS` paths, preserves an existing regular file's mode,
  and atomically replaces it only after a same-directory staging file is
  flushed and synced. A failed replacement leaves the prior manifest intact.
- A dedicated read-only pre-tag release-tooling workflow that runs exact
  release contracts on Python 3.11, force-verifies the hash-locked builder in a
  fresh virtual environment, checks dependency compatibility, produces
  candidate wheel, source, portable, and checksum artifacts in runner temp,
  installs the exact wheel into a separate smoke environment, reconciles all
  seven packaged commands, runs the same four installed-wheel acceptance
  journeys as publication, and directly exercises the zipapp whenever release
  inputs change. It has no publication authority.
- A matching isolated tag-time build that force-verifies every hash-locked
  release tool, checks dependency compatibility, and uses only that fresh
  runner-temp interpreter for the portable, wheel, source, and checksum build
  before smoke tests, attestations, or publication.
- Exact package-index-free wheel smoke installs at both pre-tag and publication
  boundaries, bound to the canonical versioned filename with dependency
  resolution and pip's remote version check disabled.
- Exact tag-derived final upload paths for the wheel, source archive, and
  portable CLI, preventing shell globs from widening the validated release set.
- Package-index-free rebuilds of the exact source archive at both pre-tag and
  publication boundaries, using the hash-locked release environment without
  build isolation and requiring identical wheel members, bytes, and stored
  modes before the already tested wheel can advance.
- A post-smoke release checksum gate that revalidates every built artifact
  against `SHA256SUMS` immediately before provenance attestation, with
  executable proof that any post-manifest byte mutation stops publication.
- GitHub build-provenance attestations and immutable-action release automation.
- Repository-level release immutability enabled for future publications, with
  executable proof that the release job rejects any exact tagged release whose
  GitHub API evidence is not `immutable: true`.
- A pre-publication tag guard that requires an annotated Git tag whose peeled
  commit exactly matches the GitHub push commit before main-branch ancestry,
  tests, artifact builds, attestations, or release creation can begin.
- Explicit MIT license text included in packaged distributions.
- Required self-reported discovery channels in founding-team pilot intake.
- Schema-3 source attribution for qualification, offers, booked revenue, conversion, loss, and follow-up.
- Explicit missing, unknown, and ambiguous source warnings for legacy or edited issues.
- Copy-ready and dogfooded CI bootstrap from a versioned Repo Scout wheel instead of a source checkout.
- Independent wheel digest, release manifest, source commit, tag, signer workflow, and hosted-runner verification.
- Exact single-entry binding between the pinned wheel digest, canonical wheel
  filename, and downloaded release manifest before provenance verification.
- Runner-temp virtual-environment installation that leaves the protected checkout unchanged.
- Package-index-free verified wheel installation with dependency resolution
  and pip's remote version check disabled in both policy gates.
- Four isolated verified-release download attempts with bounded backoff and an
  explicit terminal failure in both dogfood and copy-ready policy gates.
- Complete wheel-and-manifest promotion required inside every download attempt,
  with successful partial responses retained only in isolated attempt folders.
- Executable injected-failure proof for retry recovery, exact waits, artifact
  promotion, terminal attempt count, and partial-file exclusion.
- Four bounded provenance-verification attempts with executable recovery and
  terminal-failure proof while retaining every immutable identity requirement.
- Markdown first-repository rollout bundles generated from evaluated team-policy evidence.
- Automated readiness checks separated from explicit, unchecked team handoff actions.
- Rollout remediation evidence preserved before policy exit code 6.
- Schema-1 non-sensitive rollout metadata embedded in first-repository Markdown bundles.
- Required stable logical repository IDs with strict validation and no collision-prone implicit defaults.
- Dependency-free multi-repository rollout summaries in deterministic text and JSON.
- Duplicate, malformed, unsupported, and contradictory evidence rejection.
- Counts-only aggregate privacy defaults with explicit repository-detail opt-in.
- Release-blocking installed-wheel proof for shared-policy identity, mixed
  readiness and remediation, complete commit coverage, counts-only privacy,
  explicit details, and duplicate-repository rejection.
- Direct regular-file rollout summary inputs capped at 1 MiB, with
  descriptor-bound parsing and exact-byte and requested-leaf acceptance checks
  that fail before summary output on redirection, mutation, or oversize.
- Release-blocking installed-command proof that rollout evidence symlinks and
  oversized sparse bundles fail without emitting a cross-repository summary.
- Bounded printable rollout branch metadata that rejects line, terminal-control,
  bidirectional-control, whitespace, and oversized values before any operator
  summary can be emitted.
- Schema-2 rollout evidence with normalized policy fingerprints and exact Git commit IDs.
- Backward-compatible schema-1 aggregation with explicit policy and commit identity coverage.
- Shared-policy verification only for complete matching fingerprints across multiple repositories.
- Copy-ready and dogfooded CI generation of schema-2 rollout bundles from the verified `v0.3.46` release.
- Stable GitHub `owner/repository` evidence identity with 14-day passing and remediation artifacts.
- Required self-reported $299 purchase readiness in public pilot intake.
- Schema-4 funnel reporting for readiness-stage, revenue, conversion, and loss outcomes.
- Explicit missing, unknown, and ambiguous readiness warnings for legacy or edited issues.
- Hosted cross-repository rollout proof with policy-fingerprint coverage, scanned-commit coverage, remediation visibility, and a price-specific pilot CTA.
- Deterministic sales-action queues ranked by disclosed purchase readiness, funnel stage, issue age, and issue number.
- Stage-specific next actions for ready, approval-dependent, exploratory, missing, and unrecognized purchase intent.
- Single-file, no-install zipapp distribution for the free primary CLI.
- Fail-closed portable quick starts on the website, in the README, and in the
  release guide. Each published shell block now requires the download to
  succeed before Python can execute the requested file, with exact-snippet
  regressions proving a failed transfer cannot fall through to a stale local
  artifact.
- Release checksums, provenance attestations, and direct-execution smoke tests covering the portable artifact.
- Artifact-count-linked release documentation proving the public verification
  guide covers all three checksum entries and all three provenance commands.
- Exact repository, tag, source commit, signer workflow, and hosted-runner
  constraints on every public release attestation command.
- Public package URLs and checkout-free website and README onboarding.
- Dependency-free distribution reporting from exported public GitHub release records.
- Version-aware portable, wheel, source, and checksum artifact contract audits.
- Explicit separation of primary artifact requests from unique installs, activation, pilot demand, and revenue.
- Backward-compatible weekly distribution baselines with signed per-channel request deltas.
- New-release, removed-release, removed-asset, and decreasing-counter evidence warnings.
- Dependency-free weekly growth reviews that join signed distribution movement to attributed pilot, offer, and booked-revenue evidence.
- Price-consistent offer recommendations that carry the validated pilot price
  into the commercial bottleneck action instead of silently quoting $299.
- Deterministic commercial bottlenecks from missing measurement through acquisition, qualification, offer, payment, pilot target, retention, and validation.
- Explicit refusal to calculate download-to-lead conversion rates from non-unique artifact requests.
- Release-blocking installed-wheel proof that raw GitHub release exports become
  a complete schema-2 baseline comparison before signed reach movement joins to
  schema-7 qualification, attribution, $299 revenue, and the open pilot target.
- Controlled rejection of duplicate release assets and inconsistent growth
  deltas without emitting reports or inventing conversion rates.
- Release-blocking behavioral proof through the installed `repo-scout-pilot`,
  `repo-scout-distribution`, and `repo-scout-growth` console commands instead of
  bypassing public entry points after their help checks.
- Complete installed-entry-point release proof for policy activation and
  enforcement, guarded outreach, commercial reporting, and rollout aggregation,
  with controlled rejection when any required command is unavailable.
- Consistent `--version` identity across all seven installed commands and the
  portable zipapp, with release-tag reconciliation before attestation.
- Package-metadata-derived proof that the release smoke covers every installed
  command and the adoption guide reports the complete wheel command count.
- A refreshed schema-2 distribution, schema-7 pilot, and joined growth baseline
  generated from public evidence on 2026-07-22 UTC.
- Baseline contract tests reconciling every release channel while preserving zero pilot and revenue truth.
- A warning-free signed checkpoint showing 50 additional primary artifact
  requests through the verified `v0.3.49` release, including 45 wheel and 5
  portable requests, with zero pilot requests and revenue.
- A refreshed 14-day owner-visible GitHub traffic baseline with reconciled
  daily views and clones, partial top referrers and paths, and explicit rolling
  window and automation caveats.
- Required self-reported primary purchase criteria in public pilot intake.
- Schema-6 criterion totals for qualification, offers, booked revenue, conversion, and loss.
- Schema-7 scope qualification from required team size, repository count, CI provider, and repository-standard answers.
- Target, outside-target, incomplete, and first-10-repository subset classifications without repeating free-text standards.
- Normalized criterion evidence across deals, stale follow-up, and sales queues with explicit missing, edited, and duplicate-answer warnings.
- Backward-compatible schema-5, schema-6, and schema-7 pilot support in weekly growth reviews.
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
- An explicit initial-message opt-out promising no further contact, mirrored in
  all five private drafts and the human review checklist.
- `v0.3.37` patch-release boundary that packages the explicit opt-out in every
  installed outreach review command.
- A dependency-free `repo-scout-outreach` auditor for private, alias-only campaign ledgers.
- Strict three-signal qualification, permitted-channel, 10-prospect, seven-day follow-up, and terminal-stop validation.
- Aggregate outreach activity and due-alias reporting that remains explicitly separate from lead and revenue evidence.
- Schema-2 outreach reporting with a reviewed-draft state that requires a permitted channel and remains excluded from attempted-prospect totals.
- Schema-3 outreach qualification requiring one private, secure evidence link for every declared fit signal.
- Aggregate qualification-link reporting that never emits private source URLs.
- Schema-4 outreach approval tracking that separates drafts awaiting review,
  human-approved messages, and actual contact attempts.
- Permitted-channel and no-contact-date enforcement for both drafted and
  approved messages, with explicit approved-to-send text and JSON counts.
- Schema-5 approval-date retention across approved, contacted, follow-up,
  reply, pilot-requested, rejection, and opt-out states.
- Missing, future, and post-contact approval-date rejection without exposing
  private review dates in report output.
- Backward-compatible nine-column outreach reads and strict ten-column current
  writes with controlled malformed-quoting, missing-cell, and extra-cell
  rejection.
- Durable outcome observation dates with chronology validation, backdated
  refinement rejection, first-observation retention across classification, and
  explicit dated-versus-legacy outcome coverage.
- Separate required outcome-event and ledger-audit dates so delayed human
  recording retains the actual observation without weakening future-date
  validation.
- An executable operator-guide contract deriving the current ten-column
  private outreach ledger shape from runtime fields while preserving explicit
  legacy nine-column reads.
- Current-UTC defaults and explicit UTC operator dates across outreach review,
  approval, contact, follow-up, and outcome recording.
- Canonical zero-padded outreach dates enforced in private ledgers and CLI
  options before queue ordering or guarded mutation.
- Explicit `None`-only current-UTC defaults across pilot and outreach APIs so
  falsey non-date values cannot silently shift commercial reporting windows.
- Release-blocking installed-wheel proof for the guarded draft review, approval,
  contact, and one-follow-up lifecycle, including private-field omission,
  permission retention, safe failed writes, and bounded CSV rejection.
- An explicit `--review-next` mode that surfaces one private alias and five
  unchecked human criteria without editing, approving, or sending outreach.
- Qualification counts in the review checklist without evidence URLs, draft
  text, approval dates, recipient details, or public-baseline eligibility.
- An explicit private-evidence review opt-in that maps the selected draft's fit
  signals to source links while leaving default review output redacted.
- An explicit bounded private-draft opt-in that selects only the next alias's
  `## prospect-NNN` Markdown section for the same human review.
- Duplicate, malformed, empty, oversized, and missing selected private-draft
  section rejection without modifying the outreach ledger.
- Release-smoke coverage proving the opt-ins expose only the selected evidence
  and draft, mark both disclosures as private, and never mutate the ledger.
- Cross-file private review preflight requiring notes for every drafted ledger
  alias, rejecting aliases absent from the ledger, and retaining progressed
  aliases as history without exposing their messages.
- Schema-5 content-bound private review receipts carried into generated approval
  and decline commands, with mutation-free stale evidence and draft rejection,
  date-independent content identity, and actual-date placeholders that keep a
  delayed human decision from inheriting the bundle's ledger-audit date.
- Locked private-notes revision checks that reject edits occurring after
  content receipt verification but before approval or decline commits.
- Symmetric approval and decline race coverage proving commit-window notes
  edits preserve ledger evidence, hide changed text, and clean staged output.
- Atomic `--write-review` creation for owner-only private review bundles, with
  no terminal disclosure, overwrite, ledger mutation, or retained staging file
  after a clean result.
- Truthful post-publication cleanup failures that retain the completed review,
  identify the owner-only staging copy, and prevent a misleading success receipt.
- Truthful guarded-ledger cleanup failures that retain the original mutation
  error, identify only a neutral owner-only staging filename, and keep private
  ledger identity out of terminal guidance.
- Live outreach review and mutation preflight that rejects tracked, unignored,
  or symlinked in-repository ledgers and draft notes before reading private
  material.
- Owner-only `700/600` private-workspace setup while retaining counts-only
  audits for the empty tracked ledger example.
- POSIX live-action enforcement for owner-only private ledger, draft-file, and
  immediate-parent permissions, with mutation-free installed-command rejection
  of permissive paths and unchanged counts-only public audits.
- `v0.3.36` patch-release boundary for explicit, bounded private evidence and
  draft review with complete note-to-ledger identity preflight.
- Guarded `--approve-next` recording that requires the exact next alias, an
  explicit review date, and confirmation that a human completed every check.
- Schema-9 alias-only recovery of the next approved message and its guarded
  contact-recording handoff after the one-time approval receipt is lost, with
  machine-readable privacy classification for approved and due-follow-up
  reports versus alias-free counts-only output.
- A mutation-free `--require-counts-only` publication guard that emits no
  alias-bearing report and returns a dedicated exit code for CI automation.
- Schema-6 pre-contact `review-declined` decisions that close an unsuitable
  draft without approval, contact dates, or attempted-prospect inflation.
- A runtime-linked buyer-facing outreach contract that describes the packaged
  schema-6 approval and review-decline counts without calling released behavior
  unreleased.
- Guarded `--decline-next` recording that requires the exact next alias and an
  explicit human no-send confirmation before atomically changing only status.
- Schema-2 decline receipts that report the privacy-safe remaining-draft count,
  advance only nonempty queues, and terminate cleanly when no draft remains.
- Actual-date placeholders in nonterminal decline handoffs so a later review
  cannot silently inherit the prior draft's decision date.
- Complete-review continuity after a content-bound decline, preserving private
  evidence, draft notes, and the exact notes path while requiring a replaced
  shell-quoted `PRIVATE-REVIEW-PATH` to write the next `600` bundle without
  terminal disclosure, including when the literal replacement contains spaces.
- Full-ledger preflight and postflight validation plus permission-preserving,
  atomic approval writes that never create contact or follow-up dates.
- Revision-checked, per-ledger lifecycle locking that preserves newer outreach
  evidence when concurrent approval, contact, follow-up, or outcome writes race.
- Locked commit-point file-type and owner-only permission revalidation that
  rejects late private-ledger privacy drift without replacing its bytes.
- Guarded `--record-contact` recording that requires the exact next approved
  alias, an explicit send date, and confirmation that a human already sent it.
- Approval-date retention and automatic calculation of the exact seven-day
  next action without sending or scheduling an automatic message.
- Guarded `--record-follow-up` recording for the earliest due contacted alias
  after a human confirms the one allowed follow-up was already sent.
- Early, future, out-of-order, and repeated follow-up prevention with retained
  approval/contact evidence and no remaining next action.
- Guarded exact-alias outcome recording after contact or follow-up for replies,
  pilot requests, rejections, and opt-outs, with human-observation confirmation,
  preserved contact history, and no remaining follow-up action.
- Exact shell-quoted outcome handoffs after contact and follow-up, with required
  observation-date and status placeholders that fail before private ledger
  access when left unchanged.
- One guarded refinement handoff after a generic reply, limited to the three
  specific terminal outcomes and absent from terminal receipts.
- Schema-2 outcome receipts that carry the existing source-prefilled public
  intake only for private pilot interest, without opening or submitting it.
- Safe refinement of generic replies into specific terminal outcomes without
  converting private outreach status into public demand or revenue evidence.
- Complete shell-quoted private text handoffs from review through approval,
  contact, and follow-up recording, with required actual-send-date placeholders
  that fail before mutation when left unchanged and preserve aliases,
  confirmation flags, and ledger paths containing spaces.
- `v0.3.38` patch-release boundary for ignored-path enforcement, copy-ready
  human handoffs, and POSIX owner-only permission checks through the installed
  outreach command.
- `v0.3.39` patch-release boundary for guarded human no-send decisions that
  close unsuitable drafts without approval, contact, or attempt inflation.
- `v0.3.40` patch-release boundary for truthful terminal decline receipts and
  release-blocking proof that completed review queues emit no dead handoff.
- `v0.3.41` patch-release boundary for guarded observed-outcome recording after
  contact, including installed-command proof of mutation-free rejection and a
  private pilot-requested outcome that remains outside public demand and revenue.
- `v0.3.42` patch-release boundary for verified-pin transaction recovery,
  release-contract reconciliation, and permission-preserving policy and report
  replacement through the installable distribution.
- `v0.3.43` patch-release boundary for content-bound outreach review decisions
  and bounded GitHub download and provenance recovery through the installable
  distribution.
- `v0.3.44` patch-release boundary for UTC outreach lifecycle defaults, with
  installed-command proof under a deliberately non-UTC local timezone.
- `v0.3.45` patch-release boundary for actual-date outreach handoffs, with
  installed-wheel proof of delayed contact and follow-up recording.
- `v0.3.46` patch-release boundary for truthful private outcome history, exact
  public payment evidence, and the source-preserving pilot-intake handoff.
- `v0.3.47` patch-release boundary for recoverable approved-send handoffs and
  fail-closed privacy classification before outreach reports reach artifacts.
- `v0.3.48` patch-release boundary for atomic owner-only review bundles that
  keep complete private outreach material out of terminal capture.
- `v0.3.49` patch-release boundary for truthful, alias-safe private-review
  staging cleanup failures through the installable distribution.
- `v0.3.50` patch-release boundary for truthful, identity-safe private-ledger
  staging cleanup failures through the installable outreach command.
- `v0.3.51` patch-release boundary for an immutable public tag and artifact set
  before the separately reviewed paid-CI trust pins can advance.
- Public `v0.3.34` release of strict schema-5 outreach operations in the wheel
  and source archive alongside the portable CLI, checksums, and provenance.
- `v0.3.35` patch-release boundary for guarded outreach operations, complete
  installed-command behavior, and consistent wheel and zipapp version identity.
- Five personalized, qualified outreach drafts prepared from narrow
  company-controlled public evidence and kept in the ignored private workspace.
- A committed schema-9 outreach review checkpoint proving 5 drafts, 16 reviewed
  fit links, 0 approvals, and 0 attempts while exposing no identity, address,
  alias, draft, review date, or source URL.
- Backward-compatible policy v2 `forbidden_files` rules with normalized exact paths and contradictory-rule rejection.
- Git-aware forbidden-file enforcement that catches tracked or unignored files without failing properly ignored local environment files.
- Manual team-policy, CLI, fingerprint, and compatibility coverage for `.env` and `.env.local` protection.
- Policy v2 `.env` and `.env.local` protection in all packaged starters, dogfood policy, and copy-ready CI policy.
- End-to-end copy-ready evidence proving forbidden-file failures still emit remediation-ready rollout bundles.
- Backward-compatible policy v3 `forbidden_file_patterns` for nested monorepo and filename-wide protection.
- Git-aware pattern matching across all tracked or unignored paths, independent of the snapshot's 500-path detail cap.
- Bounded pattern evidence with full match counts, 20 sorted paths per pattern, and explicit truncation state.
- Strict wildcard, path, duplicate, required-file conflict, exact-rule overlap, and fingerprint validation for pattern rules.
- Independently pinned `v0.3.51` wheel digest, source commit, manifest,
  provenance, signer workflow, and hosted-runner checks in both policy gates.
- A preflighted maintainer updater that changes the dogfood workflow, customer
  example, buyer-facing README, commercial model and project-state claims, and
  CI pin contract together or refuses layout drift before writing.
- Numeric release-order checks across all six verified-pin targets that reject
  downgrades before staging while allowing same-version revalidation.
- A tested maintainer guide covering the complete six-target pin transaction,
  downgrade boundary, permission preservation, and rollback behavior.
- A `--check` release-pin preflight that validates the full six-target update
  without creating staging files or replacing repository content.
- Staged-original rollback that restores every verified-pin target already
  replaced when a later filesystem write fails, with retained recovery evidence
  if rollback itself cannot complete.
- Permission-bit normalization and regression proof that successful verified-pin
  updates, rollback restores, and retained recovery copies preserve target modes
  while completed transactions remove every staging file.
- Truthful verified-pin cleanup errors that distinguish committed updates from
  rolled-back writes and retain the original failure plus recovery outcome.
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
- Local starter recommendation from Node, Python, agent-instruction, and lockfile signals.
- Stable human and JSON recommendation output with an initialization command and polyglot review warning.
- Release-blocking installed-wheel proof for npm-only and flexible Node recommendation behavior.
- Installed-wheel recommendation proof for Python, agent-ready, baseline, and mixed Node/Python repositories.
- One generalized release-blocking policy-activation smoke covering all recommendation routes and Node enforcement.
- Guarded one-command policy bootstrap for recommendations that do not require review.
- Repository-contained relative output, escape rejection, direct-leaf symlink
  refusal, overwrite protection, permission-preserving atomic force
  replacement, mutation-free permission failures, and no implicit
  parent-directory creation for bootstrap.
- Explicit bootstrap refusal for mixed Node/Python repositories, with installed-wheel release proof across every route.
- Stable schema-1 JSON bootstrap receipts proving create or replace status, resolved output, selected starter, policy version, and policy fingerprint.
- No-success-receipt behavior for bootstrap review, overwrite, symlink, and
  write failures.
- Installed-wheel release proof for machine-readable bootstrap receipts across every clear recommendation route.
- Strict bootstrap-receipt verification against the current policy version and
  normalized fingerprint, requiring an absolute valid output before overrides,
  preserving the recorded or overridden policy leaf, and rejecting symlinks or
  non-regular files before reads with exit-6 mismatch evidence that does not
  expose, modify, or block on the target.
- Descriptor-bound receipt parsing and fingerprinting with initial and final
  policy-leaf identity checks, rejecting symlink or distinct regular-file
  replacement with actual identity unavailable even when the bytes match.
- Direct regular-file bootstrap receipt inputs with descriptor-bound JSON
  validation, exact-byte rereads, and final leaf checks that reject symlinks,
  special files, replacement, and same-inode mutation before evidence is used.
- Installed-wheel activation proof that receipt symlinks and non-regular leaves
  fail as command-input errors without emitting a verification report.
- Direct regular-file inputs for the primary `repo-scout --policy` command,
  with descriptor-bound TOML parsing and validation, exact-byte rereads, and
  acceptance-point leaf checks that reject static symlinks and special files
  before reads and fail on detected replacement or same-inode mutation before
  a scan report is emitted.
- Installed-command activation proof that the primary policy gate rejects
  symlink and non-regular policy leaves without disclosing or changing their
  evidence.
- A 128 KiB descriptor-level ceiling for primary policies, bootstrap receipts,
  and receipt-selected policies, rejecting oversized sparse files before
  parsing and bounding concurrent growth during both exact-byte reads.
- Installed-command activation proof that oversized primary policies and
  bootstrap receipts fail without reports or evidence mutation.
- Stable text and JSON pass or drift evidence, policy-path overrides, and exit code 6 for missing, invalid, or changed policies.
- Duplicate-key, unsupported-schema, malformed-shape, and unknown-field rejection for receipt evidence.
- Installed-wheel release proof that every clear bootstrap receipt verifies its generated policy.

## How To Run

```bash
curl -fL https://github.com/becastil/Chats-empty-repo/releases/download/v0.3.51/repo-scout-0.3.51.pyz -o /tmp/repo-scout.pyz &&
python3 /tmp/repo-scout.pyz --languages .
python3 -m unittest discover -s tests
python3 scripts/audit_action_pins.py
python3 scripts/audit_pilot_labels.py --repo becastil/Chats-empty-repo
```

## Next Small Task

The public site still advertises `v0.3.50`. Sites versions 46 and 47 are
superseded and must not be deployed; version 47 predates the July 24 React
Server Components and `brace-expansion` advisories. Run `nvm install` and
`nvm use` to select the repository's exact Node `22.13.0` pin, then run the
deployment handoff with `scripts/prepare_site_candidate.py`, using fresh
outside-repository archive and receipt paths so any previously reviewed pair
remains unchanged. Both requested paths must be direct regular-file leaves,
not symlinks. Stable alternate case or Unicode spellings, whole-repository
aliases, and aliases that expose only a repository subdirectory now fail by
filesystem identity. Archive and receipt staging, staged reads, validation,
publication, and cleanup now stay anchored to descriptors held from preflight;
helper output written through a replaced visible archive parent is not
accepted, staged receipt bytes must equal the intended serialization, and
uncertain replacements are preserved instead of deleted. Final archive and
receipt publication holds each unique validated output-parent descriptor from
preflight through the no-clobber link, then holds each exact published regular
file through the final source and digest checks. Obtain independent
`--verify-only` evidence for
its schema-5 release-bound, complete-tree, duplicate-free,
branch-bound, archive-stable, receipt-stable, test-bracketed evidence before
recording the printed `release_version`, receipt-bound `project_id`,
`receipt_sha256`, canonical remote Sites repository identity,
`refs/heads/main`, and receipt commit in an explicit owner approval to push the
receipt's exact patched source. Generate that copy-ready pending tuple by
passing the existing Sites source URL or alias through
`--approval-source-repository`; confirm the printed canonical repository
belongs to the printed project, parse the complete single-line JSON request,
and treat boolean `deployment_approved=false` as a hard boundary rather than
consent. Raw spaces in a remote URL must be percent-encoded. Only after explicit
source-export approval, push the source, then verify the unchanged archive and
receipt with
`--expected-receipt-sha256` set to the approved digest,
`--exported-source-repository` set to the URL or configured alias used for the
push, and `--expected-exported-source-repository` set to the approved canonical
identity. The digest and both repository options are required together. Save
the candidate only after that check proves the resolved repository is remote,
separate from `origin`, approval-matched including any non-default port,
stable, and its exported `refs/heads/main` is the receipt commit.
Source-export approval does not authorize production; record the saved
version, source identity, and archive
digest, then obtain separate owner approval before deployment. After deployment
approval, publish that replacement and run
`python3 scripts/audit_production_site.py`; do not describe it as live before
both steps pass.

Then human-review the fresh owner-only schema-5 bundle at
`outreach-private/next-review-v5.md` while keeping the July 21 schema-4 review
superseded. Replace every `YYYY-MM-DD` value in the chosen decision command with
the actual UTC decision date, and record the human decision with its
content-bound `--approve-next` or `--decline-next` command. Send only approved
drafts one at a time through their published business channels. After a
nonterminal decline, replace `PRIVATE-REVIEW-PATH` inside its existing single
quotes with a new ignored owner-only destination before running the emitted
review command.
Immediately record each human send with guarded `--record-contact`, which
retains approval and calculates the exact seven-day follow-up before the next
message. When due, send that one follow-up manually and close its cadence
through guarded `--record-follow-up`. No outreach has been approved or attempted
yet, and drafts are not leads or revenue. Do not add another acquisition asset
or paid-policy feature before five real attempts.
Release, pilot, repository-traffic, and outreach-draft baselines are recorded;
refresh them only at a deliberate review point or meaningful funnel change.
