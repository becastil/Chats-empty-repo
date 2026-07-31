# Changelog

## Unreleased

- Rejected decision-ready outreach drafts that negate the canonical `$299`
  offer or include any competing dollar amount before a review receipt or
  owner-only bundle can be emitted.
- Extended API, owner-only writing, and installed-command lifecycle coverage
  across missing, repeated, negated, competing, and lookalike price text while
  preserving private-output and ledger-mutation boundaries.
- Required every guarded outreach approval to carry the digest and private
  notes path from a complete evidence-and-draft review.
- Removed approval handoffs from redacted and partial reviews while retaining
  an explicit no-send decline path for malformed or unsuitable drafts.
- Extended source and installed-command lifecycle coverage to prove a confirmed
  receipt-free approval emits no private output and leaves the ledger unchanged.
- Enforced one pending approved outreach message at a time by rejecting another
  review, approval, decline, or owner-only review write until the existing
  approved send is recorded.
- Kept legacy multi-approved ledgers readable and contact-recordable while
  returning an alias-safe, mutation-free error for blocked draft work.
- Extended source and installed-command coverage to reject the emitted
  next-review handoff before contact, then accept the same handoff after the
  manual send record succeeds.
- Advanced private approval receipts to schema 2 with a privacy-safe
  remaining-draft count and a truthful terminal queue state.
- Added a distinct post-contact next-review handoff for nonterminal approvals,
  preserving complete private evidence-and-draft options and the shell-quoted
  owner-only review destination without sending or recording outreach.
- Extended unit and installed-command lifecycle coverage through approval,
  manual contact recording, and generation of the next prospect's private
  content-bound review.
- Added a guarded terminal `existing-solution` outreach outcome and dedicated
  aggregate count so explicit substitute or DIY preference remains distinct
  from price resistance and generic fit rejection.
- Advanced outreach reports to schema 11 and outcome receipts to schema 4 while
  retaining confirmation, first-reply timing, closed cadence, and null
  conversion links for substitute objections.
- Extended the installed outreach lifecycle to record and count an existing
  solution objection without retaining private response text or inferring a
  competitor from silence.
- Reissued the counts-only five-draft checkpoint as schema 11 with zero
  existing-solution objections, attempts, replies, or pilot requests.
- Added a guarded terminal `price-objection` outreach outcome and dedicated
  aggregate count so explicit `$299` resistance remains distinct from generic
  fit rejection.
- Advanced outreach reports to schema 10 and outcome receipts to schema 3,
  retaining human-observation confirmation, first-reply dates, closed cadence,
  and null conversion links for price objections.
- Extended the installed outreach lifecycle to record and count a price
  objection without exposing private response content or inventing demand.
- Reissued the counts-only five-draft checkpoint as schema 10 with zero price
  objections, zero attempts, and no private aliases or evidence.
- Required exactly one `$299` disclosure in every complete outreach review
  before Repo Scout can emit a content-bound receipt or owner-only bundle.
- Added API, owner-only file-writing, stale-decision, and installed-lifecycle
  coverage for missing or repeated price text without private output, ledger
  mutation, or staging residue.
- Revalidated the existing five-draft private queue under the price preflight
  without approving or sending outreach.
- Refused decision-ready outreach reviews when the selected private draft omits
  or repeats the canonical source-attributed offer route.
- Added API, owner-only file-writing, and installed-lifecycle proof that route
  rejection emits no bundle, leaves no staging file, preserves ledger bytes,
  and does not repeat private draft text.
- Revalidated the existing ignored schema-6 review queue under the exact-once
  route preflight without approving or sending outreach.
- Bound complete private outreach reviews to the canonical
  `?source=outreach#why-teams-buy` offer route and added a sixth human check
  that confirms the selected draft preserves that attribution.
- Advanced content-bound outreach receipts to schema 6 so route, row, private
  draft, and checklist drift all require a fresh review before approval or
  decline.
- Generated a fresh ignored, owner-only schema-6 review bundle without
  approving, sending, or mutating any prospect state.
- Refreshed the reviewed public distribution, pilot, and joined-growth
  baselines on 2026-07-30, reconciling 55 complete releases and 403 cumulative
  primary artifact requests without warnings.
- Recorded the signed increase of 135 primary requests as 5 portable and 130
  wheel requests while preserving zero pilot requests and $0 booked revenue.
- Prioritized approved, source-identifiable outreach as the next revenue action
  instead of treating CI-confounded release traffic as customer demand.
- Made a failed mandatory Sites dependency audit explicitly block candidate
  approval with separate vulnerability and audit-endpoint recovery guidance,
  without offering a bypass or weakened command.
- Added API and real CLI coverage proving a multi-line audit failure emits one
  bounded error, stops before lint, build, tests, packaging, or evidence
  publication, and cannot forge candidate or source-export status.
- Made the Sites release handoff fail clearly unless the active plugin's
  trusted root packaging helper is executable and the existing project's
  credential-free source repository is available before an approval request.
- Replaced reusable fixed candidate paths with a fresh private directory and
  named no-clobber archive and receipt variables shared by prepare, approval,
  and pre-save verification commands.
- Documented ephemeral, per-command source authentication and added executable
  documentation contracts for prerequisite ordering, fresh evidence paths, and
  credential separation.
- JSON-serialized complete presentation-unsafe `SiteCandidateError` messages at
  the shared Sites candidate CLI boundary, including archive and receipt paths
  plus wrapped operating-system context.
- Preserved byte-for-byte printable diagnostics and existing pre-escaped
  archive-member errors while preventing rejected evidence paths from forging
  candidate or source-export status lines.
- Added real prepare and verify CLI coverage for both evidence paths, requiring
  empty stdout, one stderr line, no packaging commands, and unchanged or absent
  outputs as appropriate.
- JSON-serialized presentation-unsafe Sites archive member names before
  unsafe-path, root-containment, special-file, or duplicate-member errors.
- Preserved exact printable member diagnostics and all structural rejection
  semantics while preventing invalid archives from forging candidate or
  source-export status lines.
- Added branch-complete archive-error coverage and real `--verify-only` CLI
  proof that rejection emits no status and leaves archive and receipt evidence
  unchanged.
- JSON-serialized presentation-unsafe duplicate Sites JSON keys before
  including them in candidate preparation or verification errors.
- Applied the one-line boundary to checkout hosting metadata, candidate
  receipts, and archived manifests while preserving duplicate rejection at
  every object depth.
- Preserved printable key diagnostics and added real prepare and `--verify-only`
  CLI proof that control-bearing keys emit no candidate or source-export status
  and leave approval evidence unchanged.
- Rejected empty or presentation-unsafe release asset names in both raw exports
  and saved distribution baselines before artifact classification, request
  totals, warnings, or signed movement.
- Preserved ordinary printable Unicode asset names while returning a generic,
  location-only error that never repeats rejected evidence.
- Extended source and installed-command coverage to require no report and no
  evidence mutation when current or baseline asset names contain line,
  terminal, Unicode-separator, or bidirectional controls.
- JSON-escaped control-bearing duplicate and unknown bootstrap receipt keys
  before including them in policy-verification errors.
- Preserved ordinary printable receipt-field diagnostics while preventing
  rejected evidence from forging a successful policy-match line.
- Extended the installed policy-activation smoke to require one-line key
  rejection with no verification output or evidence mutation.
- JSON-escaped control-bearing unknown rollout metadata keys before including
  them in top-level, policy, or Git validation errors.
- Preserved ordinary printable unknown-field diagnostics while preventing
  rejected keys from forging terminal lines through parser or direct-summary
  validation.
- Extended the installed rollout smoke to require one-line unknown-key
  rejection with no report or evidence mutation.
- JSON-escaped control-bearing rollout evidence paths and source labels before
  including them in parser, validation, or file-loading errors.
- Preserved ordinary printable path errors and exact successful detailed JSON
  path values while preventing filenames from forging terminal lines.
- Extended the installed rollout smoke to require escaped path context, empty
  report output, and unchanged evidence for an unsafe malformed filename.
- JSON-escaped duplicated rollout metadata keys before including them in
  operator errors.
- Prevented decoded line, C1 terminal, and bidirectional controls in ambiguous
  bundle keys from injecting extra error lines.
- Extended the installed rollout smoke to require one-line duplicate-key
  rejection with no report or evidence mutation.
- Replaced backslash-escaped Markdown backticks with a delimiter longer than the
  longest backtick run in each inline code value.
- Preserved the exact printable rollout repository ID in schema-2 metadata while
  keeping embedded backticks inside one visible Markdown code span.
- Extended the installed rollout smoke to require both packaged producer and
  aggregator commands and prove code-span containment before release.
- Required rollout repository IDs to remain non-empty printable strings of at
  most 128 characters without surrounding whitespace.
- Rejected line, terminal-control, bidirectional-control, Unicode-separator,
  and oversized repository IDs before bundle generation or summary output,
  without echoing the untrusted value.
- Extended the installed rollout smoke to prove control-bearing repository
  identities cannot forge detailed operator metrics or alter their evidence.
- Rejected duplicate JSON keys at every depth of raw GitHub release exports and
  saved distribution baselines before calculating artifact totals or signed
  request movement.
- Kept distribution duplicate-key failures input-and-field specific while
  emitting no report and withholding both competing values.
- Extended the installed commercial smoke to prove both producer input paths
  fail closed through the packaged distribution command.
- Rejected duplicate JSON keys at every depth of both distribution and pilot
  reports before joined growth can calculate revenue, activation work, or a
  commercial bottleneck.
- Kept duplicate-key failures report-and-field specific while emitting no
  growth JSON and withholding both competing values.
- Extended the installed commercial smoke to prove duplicate saved
  distribution and pilot fields, including ambiguous payment evidence, fail
  through the packaged growth command.
- Added an ordered schema-9+ activation queue that names every exact
  booked-but-unactivated issue and its canonical paid-delivery or terminal
  reconciliation action using only validated public lifecycle fields.
- Preserved explicit `null` queue semantics for schema 5 through schema 8 and
  removed completed activations from the schema-9+ queue without exposing
  titles, free text, or private delivery evidence.
- Extended source and installed-command regressions across live paid,
  converted-without-activation, completed activation, queue ordering, text
  output, and private-text boundaries.
- Upgraded pilot reporting to schema 10 with payment-backed activation totals
  by source, purchase readiness, and purchase criterion.
- Derived every schema-10 activation segment from detailed deal evidence and
  rejected globally balanced attribution swaps while preserving schema-9
  global activation compatibility.
- Extended the installed commercial smoke to prove activation attribution
  survives packaging and forged source attribution fails without a report.
- Upgraded pilot reporting to schema 9 with explicit payment-backed activation
  evidence on every detailed deal and a reconciled activation summary.
- Prioritized booked-but-unactivated paid delivery before another pilot sale,
  retention, or expansion while preserving schema-5 through schema-8 growth
  compatibility without invented activation counts.
- Extended the installed commercial smoke to prove paid-only activation remains
  false, explicit paid activation reopens the founding-pilot target, and
  malformed activation evidence is rejected without a report.
- Made the installed commercial smoke journey preserve asymmetric schema-8
  lead and paid progression across source, purchase readiness, and purchase
  criterion.
- Required the packaged growth command to reject a tampered lead milestone
  without emitting JSON or disclosing private qualification evidence.
- Upgraded pilot reporting to schema 8 with explicit boolean qualification and
  offer milestones on every detailed deal while preserving schema-7 growth
  compatibility.
- Derived qualification and offer attribution from schema-8 deals across
  source, purchase readiness, and purchase criterion, rejecting globally
  balanced milestone redistribution before commercial decisions use it.
- Added validated schema-7 purchase-readiness rows to joined JSON and text
  growth reviews, reconciling every readiness segment and summary counter to
  source totals.
- Derived readiness request, booking, conversion, and loss attribution from
  detailed deals and rejected globally balanced intent-segment rewrites.
- Derived schema-7 request counts from every detailed deal's recognized source
  and purchase criterion before joined growth trusts segment totals.
- Rejected globally balanced request-count redistribution that preserves the
  funnel total while redirecting acquisition or buyer-learning evidence.
- Derived schema-7 booked-pilot attribution from detailed deals by source and
  purchase criterion, binding each segment's revenue through the fixed $299
  price formula.
- Rejected coordinated booked-count and booked-revenue swaps that preserve
  global revenue while assigning payment to a different channel or criterion.
- Derived schema-7 conversion and resolved-loss attribution from each detailed
  deal's recognized source and purchase criterion.
- Rejected globally balanced source or criterion outcome swaps and malformed
  detailed attribution before joined growth reports channel or buyer learning.
- Derived schema-7 annual conversions from booked converted deals and resolved
  losses from lost-stage deals before joined growth selects a bottleneck.
- Rejected coordinated summary, source, and purchase-criterion edits that
  manufacture global retention evidence or erase a detailed resolved loss.
- Derived schema-7 complete, target-profile, review-required, and first-10
  subset counts from validated qualification evidence on every detailed deal.
- Rejected aggregate-only profile edits and malformed qualification evidence on
  closed historical deals before joined growth reports customer fit.
- Reconciled schema-7 booked-pilot totals to explicit boolean booking evidence
  on every detailed deal before joined growth computes revenue or a bottleneck.
- Rejected aggregate-only false bookings, non-boolean payment evidence, booked
  pre-payment stages, and attempts to erase payment from a paid-stage deal.
- Derived every actionable schema-7 deal age from the report's canonical date
  and UTC activity timestamp before joined growth trusts queue ordering.
- Rejected coordinated detail/queue age edits, malformed report dates, and
  queue timestamp drift while preserving valid missing, future, and
  offset-normalized activity evidence.
- Rejected reordered schema-7 pilot sales queues during joined growth
  validation instead of accepting their members as an unordered mapping.
- Bound each queued priority and age to its canonical detailed deal and reused
  the funnel producer's readiness-stage-age-number sort contract before growth
  can defer a paid-pilot action to that queue.
- Made Sites pre-save verification accept the exact canonical source-repository
  identity emitted by the pending approval request, so the documented approval
  tuple can be replayed without translating it back into a URL.
- Preserved nonstandard SSH and SCP usernames in canonical repository identity
  while retaining conventional `git@` and default-port protocol equivalence,
  and used a collision-free `scp-relative://` prefix to distinguish
  home-relative SCP paths from absolute SSH/SCP paths for those usernames.
- Added pre-save regressions for canonical-identity replay, approved username
  matching, unapproved SSH URL and SCP username aliases, and relative-versus-
  absolute SCP paths.
- Distinguished legacy, active, empty, and repair-required states in joined
  growth reviews, preventing historical records or open
  malformed evidence from producing phantom commercial actions.
- Reconciled every schema-7 queue member's issue identity, stage, readiness,
  and action-driving qualification evidence to the complete open pre-payment
  deal set, reconciled detailed deal stages to `by_stage`, and required visible
  qualification and offer progression to agree with `by_source`.
- Rejected forged empty queues even when their saved action count was changed
  to match, as well as self-authorized CI gates and coordinated detail/queue
  stage escalation that disagrees with stage or source totals.
- Preserved cumulative funnel milestones and legacy schema-5/6 recommendations
  while adding integration coverage across qualification, offer, payment,
  pilot-target, mislabeled-closed, correctly lost, paid, open-untracked,
  mixed active-plus-repair, and forged queue states.
- Bound schema-7 pilot reporting to the $299 price named in public intake,
  rejecting any configured mismatch before issue parsing, sales actions,
  booked-revenue arithmetic, or output.
- Made joined growth ingestion reject saved schema-7 evidence with a divergent
  pilot price, while preserving older aggregate-schema compatibility and
  configurable positive-integer pilot targets and inactivity windows.
- Derived price-bearing readiness and commercial-fit options from the same
  public-intake constant and added direct API, CLI, and growth regressions.
- Made the website, README, and release-guide portable quick starts one shell
  AND-list, preventing a failed download from executing a stale
  `/tmp/repo-scout.pyz` or returning a misleading successful scan.
- Added exact-snippet shell regressions that replace `curl` and `python3`,
  force download exit 22, and prove every public quick start preserves that
  failure without invoking Python.
- Withheld normal terms and payment guidance from ready GitHub Actions
  requests whose qualification is incomplete, outside the target profile, or
  still requires a first-10-repository pilot scope.
- Preserved the existing CI-provider gate ahead of qualification review and
  left approval-dependent, exploratory, and unclear-readiness coaching
  unchanged.
- Centralized the schema-7 sales-action contract and made growth ingestion
  validate every queued stage, readiness, qualification status, repository
  scope, CI provider, public-intake-bound price, and exact next action before
  deferring.
- Added source and installed-command regressions proving out-of-profile buyers
  cannot receive payment guidance and saved qualified-stage evidence cannot
  substitute a later payment action.
- Required ready-to-purchase requests to identify GitHub Actions before the
  pilot sales queue can recommend normal terms or payment actions.
- Routed recognized non-GitHub providers to a private integration-decision
  action and missing, edited, no-response, or ambiguous provider evidence to a
  provider-clarification action without changing queue order or qualification.
- Made schema-7 offer, payment, and open pilot-target growth bottlenecks defer
  to that qualification-aware queue instead of emitting a contradictory
  commercial action; older aggregate schemas retain their existing
  recommendations.
- Required growth ingestion to reconcile the schema-7 sales-action count and
  reject missing queues or ready-buyer actions that predate the CI gate before
  it describes that queue as qualification-aware.
- Added source and installed-command regressions across every supported
  provider, all readiness buckets, legacy evidence, and the packaged $299
  commercial workflow.
- Normalized surrounding whitespace in pilot issue titles, then required
  non-empty printable text of at most 1,024 characters before funnel analysis.
- Rejected line injection, terminal controls, bidirectional controls, Unicode
  separators, and oversized titles with exit code 2, no report, and no echo of
  the untrusted value.
- Required issue URLs to remain empty or bounded one-line printable text
  without surrounding whitespace before they can enter operator output.
- Kept unrecognized form answers and pilot labels in escaped JSON review fields
  while replacing terminal-facing warning interpolation with generic messages.
- Added source and installed-command regressions proving public request text
  cannot forge revenue or warning lines in the operator's $299/$897 report.
- Required rollout branch metadata to be null or a non-empty printable string
  of at most 1,024 characters without surrounding whitespace.
- Rejected line, terminal-control, bidirectional-control, and oversized branch
  values with exit code 2 before text or JSON output, without echoing the
  untrusted value.
- Added source and installed-command regressions proving crafted branch evidence
  cannot forge operator metrics, alter terminal output, or modify its bundle.
- Required `repo-scout-rollout` inputs to remain direct regular-file leaves,
  rejecting symlinks and special files before cross-repository evidence reads.
- Capped each rollout bundle at 1 MiB and bound parsing plus the acceptance
  reread to one descriptor, failing on detected replacement, mutation, or
  growth before a summary is emitted.
- Added source proof for non-regular leaves, sparse oversize, exact-limit
  acceptance, and in-place mutation, plus installed-command proof for symlink
  and oversized rollout evidence.
- Capped primary policies, bootstrap receipts, and receipt-selected policies at
  128 KiB through the shared descriptor reader, rejecting oversized sparse
  inputs before parsing.
- Bounded both the initial read and acceptance reread to the ceiling plus one
  byte, so concurrent file growth cannot trigger unbounded activation evidence
  allocation.
- Added source proof for pre-parse policy and receipt rejection, receipt-policy
  mismatch evidence, and policy growth during validation, plus installed-command
  proof for oversized primary policy and receipt inputs.
- Required the primary `repo-scout --policy` argument to remain a direct
  regular-file leaf, rejecting symlinks and special files with exit 2 before a
  scan report can be emitted.
- Bound primary policy parsing and validation to one non-inheritable descriptor,
  then rechecked the exact bytes and requested leaf so different-inode
  replacement and same-inode mutation detected at the acceptance checkpoint
  fail closed.
- Added deterministic source proof across symlink, directory, FIFO, pre-read
  replacement, post-validation replacement, and in-place mutation, plus
  installed-command proof for symlink and directory policy inputs.
- Required bootstrap receipt arguments to name direct regular-file leaves,
  rejecting symlinks and special files before reads with exit 2 and no
  verification report.
- Bound receipt JSON parsing and validation to one descriptor, then rechecked
  its exact bytes and requested leaf before use; the shared verifier now also
  detects same-inode policy mutation after fingerprinting.
- Added source activation proof across receipt symlinks, directories, FIFOs,
  pre-read replacement, post-validation replacement, and in-place byte
  mutation, plus installed-command proof for symlink and directory inputs.
- Bound bootstrap-receipt parsing and fingerprinting to one opened regular-file
  descriptor, requiring the selected leaf to retain the same filesystem
  identity before a match can pass.
- Added deterministic source proof that symlink, identical-byte regular-file,
  and post-fingerprint leaf replacements return exit-6 evidence with actual
  identity unavailable.
- Required receipt-recorded and overridden policy leaves to be regular files
  before loading, returning exit-6 mismatch evidence for directories, FIFOs,
  sockets, devices, and other special files instead of reading or blocking.
- Added source proof that directory and FIFO leaves never reach the policy
  loader plus installed-command proof that non-regular evidence remains
  unchanged and reports actual identity as unavailable.
- Preserved the receipt-recorded or overridden policy leaf during bootstrap
  receipt verification and rejected initial or dangling symlinks with normal
  exit-6 mismatch evidence instead of following their targets.
- Required archived bootstrap outputs to be absolute, valid file leaves,
  rejecting relative and NUL-bearing values with a controlled receipt error
  before any policy override can be honored.
- Added source proof for recorded and override paths plus installed-command
  proof that malformed outputs fail and symlink verification keeps the
  requested leaf, withholds target identity, and leaves both link and policy
  evidence unchanged.
- Required policy bootstrap and initialization outputs to be direct leaves,
  rejecting initial and dangling symlinks even with `--force` before a policy
  or bootstrap receipt can be written.
- Preserved relative bootstrap output leaves during parent normalization and
  added source plus installed-command proof that rejected links and targets
  remain unchanged with no JSON receipt.
- Rejected duplicate JSON keys at every depth of pilot issue exports before
  issue parsing, preventing last-key-wins `pilot-paid` evidence from changing
  booked-pilot and revenue totals.
- Extended source and installed-command commercial checks to prove an
  ambiguous payment-label export emits no report or label value.
- Kept generated content-bound decline continuations copy-ready by always
  shell-quoting the `PRIVATE-REVIEW-PATH` marker, so literal replacement with
  an owner-only destination containing spaces remains one argument.
- Extended the source and installed-command outreach lifecycle checks to run a
  literally replaced continuation with a spaced private review path.
- Emitted Sites candidate status and pending source-export approval evidence as
  compact single-line JSON records, preventing opaque project IDs or output
  filenames from injecting misleading fields or extra terminal lines.
- Rejected raw whitespace in configured or resolved Sites source repository
  identities while preserving percent-encoded URL paths, so the canonical
  repository recorded for approval remains unambiguous.
- Kept content-bound review queues owner-only after a human no-send decision by
  carrying `--write-review PRIVATE-REVIEW-PATH` into the next complete review
  command and rejecting the unchanged path before private material is read.
- Proved that a replaced continuation path writes the next alias, evidence, and
  draft only to a `600` review file while terminal output remains alias-free and
  the declined ledger remains unchanged during review generation.
- Advanced private outreach reviews to schema 5 by excluding the bundle's
  ledger-audit date from its content receipt, so an unchanged row, draft, and
  checklist can be decided on a later UTC date without weakening stale-content
  rejection.
- Replaced copied review dates in generated approval and decline commands with
  explicit `YYYY-MM-DD` placeholders, preventing a delayed human decision from
  silently backdating approval evidence.
- Added an offline, copy-ready pending Sites source-export request after
  independent candidate verification, with local canonical repository
  resolution, `origin` rejection, complete approval identity, explicit
  `deployment_approved=false`, and strict separation from pre-save mode.
- Renamed the candidate CLI's generic archive `sha256` label to
  `archive_sha256` so archive and receipt digests remain unambiguous during
  human review.
- Exposed the receipt-bound existing Sites `project_id` in both candidate
  preparation and verification results and CLI output, and made it required
  source-export approval evidence alongside the release version, receipt
  digest, canonical repository identity, source ref, and commit.
- Advanced Sites evidence to schema 5 by strictly reconciling
  `pyproject.toml` `project.version` with the website's single
  `RELEASE_VERSION` declaration before commands run, then binding that public
  release version into preparation, archived manifests, receipts, independent
  verification, and owner-facing CLI output. The read-only hosted site
  contract now runs when either release-identity source changes.
- Bound Sites receipt staging to the output-parent descriptor held from
  preflight, retaining one private `0600` regular-file descriptor through
  writing, syncing, intended-byte digest validation, recheck, and no-clobber
  publication. Cleanup removes only the recorded identity, preserves uncertain
  replacements, reports failure, and closes staged or partially transferred
  descriptors instead of deleting an unowned leaf.
- Bound Sites archive staging to the output-parent descriptor held from
  preflight, retaining private staging-directory and regular archive
  descriptors through hashing, tar validation, source recheck, and publication.
  Cleanup removes only recorded filesystem identities, preserves uncertain
  replacements for investigation, and rejects helper output written through a
  replaced visible parent.
- Held the exact newly published Sites archive and receipt descriptors through
  final source and digest checks, rejecting link-to-open substitution,
  byte-identical leaf replacement, and replaced requested parents before
  success.
- Held each unique validated Sites output-parent descriptor from preflight
  through archive and receipt publication, reusing shared parents and closing
  every descriptor on success, command failure, or partial acquisition.
- Anchored final Sites archive and receipt publication to each prevalidated
  output parent's open descriptor, rejecting parent replacement before the
  no-clobber link and preventing a rename after verification from redirecting
  publication into a replacement directory.
- Extended Sites output containment across every non-symlink repository
  directory, rejecting stable subdirectory-only filesystem aliases with a
  cycle-safe identity scan that fails closed on traversal errors.
- Rejected Sites archive and receipt parents whose existing ancestor has the
  repository's filesystem identity, closing stable case-folded, Unicode, and
  whole-repository aliases while failing closed on ambiguous identity checks.
- Preserved requested Sites evidence leaf paths during path normalization so
  initial or dangling archive and receipt symlinks fail closed, while resolving
  parent directories still rejects an existing symlink routed into the
  repository.
- Made the approved receipt digest and both exported-source repository
  arguments an atomic pre-save verification mode, preventing digest-only
  success from omitting the network source and commit checks.
- Preserved non-default ports in canonical Sites repository identities while
  normalizing protocol-default ports, rejecting an operational endpoint on an
  unapproved authority even when its host, path, and commit match.
- Bound pre-save source verification to the canonical remote Sites repository
  identity recorded in owner approval, rejecting `origin`, local repositories,
  unrelated forks, equivalent aliases, and identity drift before version save.
- Added approval-bound pre-save verification for the separate Sites source
  repository, requiring the approved receipt digest and checking its exported
  `refs/heads/main` twice for candidate mismatch or movement before success.
- Made the exact Sites receipt SHA-256 part of preparation and verification
  output, rechecked source, archive, and receipt after publication, and let the
  pre-save verifier require the digest recorded in owner approval.
- Bracketed the exact Sites candidate receipt bytes parsed during read-only
  verification through the final acceptance checkpoint, rejecting later
  mutation or replacement before reporting approval-ready success.
- Published newly prepared Sites archives and synced receipts through atomic
  no-clobber links from private same-filesystem staging paths, preserving any
  destination claimed after preflight and withholding approval-ready success
  instead of replacing concurrent evidence.
- Made Sites candidate preparation refuse pre-existing archive or receipt
  outputs before running source, build, test, or packaging commands, preserving
  previously reviewed evidence and requiring a fresh output pair for each run.
- Bracketed Sites archive validation with the same regular-file digest through
  the final source checkpoint, withholding receipts and read-only success when
  the archive path or bytes change during either candidate operation.
- Required every Sites candidate source checkpoint to remain on
  `refs/heads/main`, rejecting detached or alternate-branch checkouts even when
  their commit still matches `origin/main`.
- Rejected duplicate JSON keys throughout Sites source metadata, candidate
  receipts, and archived manifests, even when repeated values match, so
  approval evidence cannot depend on parser-specific key selection.
- Advanced Sites receipts to schema 4 and bound every regular directory's path,
  type, and deterministic `0755` mode alongside file bytes, rejecting injected
  empty directories, noncanonical source modes, and archive permission drift
  under an explicit packaging umask.
- Added schema-3 Sites receipts that build once, bind the complete candidate
  payload, test that exact existing output without rebuilding, and refuse
  packaging when any ignored build byte changes during the tests.
- Required the same clean `HEAD == origin/main` commit at every Sites
  validation, packaged-archive, and read-only verification checkpoint,
  rejecting persistent ref moves before a receipt or approval-ready success.
- Bound every Sites candidate payload file's canonical path, permission mode,
  and bytes before the external packaging helper runs, requiring schema-2
  receipts and later read-only verification to reproduce the recorded digest.
- Disabled macOS AppleDouble archive metadata during packaging so strict
  deployable-output scope remains portable instead of admitting sidecar files.
- Restricted Sites candidates to canonical regular files and directories under
  `dist/`, rejecting unrelated source paths, aliases, links, and special files
  before either preparation or independent verification can accept an archive.
- Added one strict `.nvmrc` source of truth for exact Node `22.13.0` Sites
  candidate builds, receipts, and hosted dependency checks, with fail-fast
  malformed-pin coverage and an explicit local runtime-selection handoff.
- Added independent, read-only Sites candidate verification that strictly
  reconciles a receipt with clean synchronized source, the local lockfile and
  project identity, the archive digest, and its embedded manifest before
  source-export approval and again before version saving.
- Added a fail-closed Sites candidate preflight that rejects dirty,
  unsynchronized, or runtime-drifted source and binds the tested commit,
  lockfile, Sites project, Node runtime, and archive digest in a receipt.
- Split Sites source-export approval from production-deployment approval, with
  executable ordering proof that source cannot leave its existing origin
  before consent and that export consent cannot authorize publication.
- Remediated newly published high-severity React Server Components and
  `brace-expansion` denial-of-service advisories without suppressing the full
  dependency audit, and replaced the legacy Next lint bundle with direct
  ESLint 10, TypeScript, React Hooks, and Next rule sets.
- Bound the final GitHub Release upload to the exact tag-derived wheel, source
  archive, and portable CLI names, with executable proof that no artifact glob
  can widen the checksummed and attested publication set.
- Required the website-attributed production application CTA to disclose the
  exact $299 pilot price, with controlled failures for unpriced and mispriced
  labels even when the structured paid offer remains correct.
- Required the production audit to find the current portable release in a
  visitor-visible link, with controlled failures for missing or stale anchors
  even when the structured download metadata remains current.
- Required the daily production-site workflow to run its workflow contract and
  complete auditor behavior suite before trusting the live release, $299
  service, or pilot-application checks.
- Added the complete pilot-funnel behavioral suite to the dedicated hosted
  intake contract before its live label audit, and added both the suite and its
  revenue fixture to pull-request and `main` trigger paths.
- Made release checksum publication reject symlinked or other non-regular
  `SHA256SUMS` paths and replace regular manifests through a flushed,
  same-directory staging file, preserving the prior manifest when atomic
  replacement fails.
- Rebuilt the exact candidate and publication source archives without package
  indexes, dependency resolution, or a second build environment before either
  release boundary can advance.
- Added duplicate-safe wheel parity checks requiring the source-rebuilt wheel
  to match every direct-wheel member path, byte, and stored mode while ignoring
  only archive ordering, compression, and timestamps.
- Ran the publication workflow's policy-activation, outreach-lifecycle,
  pilot-funnel, and rollout-summary acceptance journeys against every installed
  pre-tag candidate wheel.
- Added an executable parity contract that keeps the ordered pre-tag and
  publication acceptance-script sets identical as paid workflows evolve.
- Made both pre-tag and tag-time wheel smoke installs package-index-free, with
  dependency resolution and pip's remote version check disabled.
- Replaced the publication smoke step's wheel wildcard with the exact canonical
  filename derived from the validated release tag.
- Installed every pre-tag candidate wheel into a separate smoke environment,
  reconciled all seven packaged command versions, and directly exercised the
  candidate zipapp before a maintainer can create a release tag.
- Expanded the pre-tag trigger contract to include all four release smoke
  helpers so changing release-boundary behavior selects the same hosted proof.
- Revalidated every release artifact against `SHA256SUMS` after wheel and
  zipapp smoke tests and immediately before provenance attestation.
- Added executable workflow proof that intact artifacts pass while any
  post-manifest byte mutation stops the release before attestation.
- Moved the actual tag-time artifact build into a fresh runner-temp Python
  environment instead of trusting packages already present on the hosted
  runner.
- Required forced hash verification, a clean dependency check, and the same
  isolated interpreter for portable, wheel, source, and checksum generation.
- Required the publishing workflow to reject lightweight release tags and
  annotated tags whose peeled commit differs from the GitHub push commit before
  main ancestry, tests, builds, attestations, or publication.
- Added executable success, wrong-commit, and lightweight-tag regressions using
  real temporary Git repositories.
- Added a dedicated pre-tag release-tooling workflow for relevant source,
  packaging, lock, test, and release-workflow changes plus manual checks.
- Required read-only Python 3.11 execution, exact self-testing release
  contracts, a fresh virtual environment that force-verifies every hash-locked
  tool, a dependency check, and complete candidate artifact and checksum
  generation in runner temp without publishing or uploading anything.
- Advanced the hash-locked release builder from vulnerable `setuptools`
  `80.9.0` to the advisory-fixed `83.0.0` wheel and its independently verified
  SHA-256 digest.
- Strengthened the release lock contract to bind every package and version to
  its exact hash, then clean-installed the lock and rebuilt the source, wheel,
  portable, and checksum artifacts without publishing a release.
- Added a dedicated fail-closed contract for the public pilot-intake workflow's
  triggers, read-only permissions, immutable actions, bounded runtime, exact
  tests, and non-repairing live-label audit.
- Made the hosted command run that contract itself and added the contract plus
  `DISTRIBUTION.md` to both path filters so changing conversion evidence or its
  protection selects the same hosted check.
- Wired the action-pin audit script and test into the hosted dependency
  workflow's pull-request and `main` path filters.
- Invoked the audit explicitly before Node setup and general test discovery so
  deleting or renaming its unit contract cannot silently disable hosted pin
  enforcement.
- Added a repository-wide immutable-action audit for all 17 external references
  across the six hosted workflows and copy-ready customer gate, including the
  previously uncovered pilot-intake pins.
- Required full lowercase commit SHAs, exact semantic release annotations, one
  identity per action, and matching dogfood/customer action sequences so future
  partial Dependabot proposals fail without automating upstream approval.
- Advanced every hosted and copy-ready `actions/setup-python` reference to the
  verified `v7.0.0` commit after confirming the used input and action runtime
  remain compatible with the existing workflows.
- Reconciled the major pin with independent customer-example, production-audit,
  and release expectations after hosted evidence set up Python 3.11.15 and ran
  the complete verified-wheel policy path successfully.
- Advanced every hosted and copy-ready `actions/checkout` reference to the
  verified `v7.0.1` commit, carrying its checkout-safety and Git-config fixes
  through the existing immutable-pin contract.
- Updated all independent workflow, release, and customer-example expectations
  with the checkout pin so a partial Dependabot edit still fails review; the
  setup-python major remained a separate compatibility transaction.
- Enabled GitHub vulnerability alerts and automated security-fix pull requests
  without enabling automatic merges or deployment.
- Added a contract-tested Dependabot policy that groups npm security updates,
  disables routine npm version-update noise, and caps weekly pinned-action
  update proposals at two open pull requests.
- Extended the hosted site dependency contract to validate the Dependabot and
  every workflow change through the full repository suite before installing,
  auditing, building, testing, and linting the site dependency tree.
- Added a read-only hosted site dependency contract for relevant changes,
  manual checks, and weekly advisory refreshes using immutable checkout and
  Node setup actions.
- Required the hosted contract to install the exact lock, report zero
  vulnerabilities, build and exercise the PostCSS, Sharp, and Miniflare
  compatibility path, and lint before success.
- Recorded exact security-hardened commit `4d0053f` as saved Sites version 47
  without crossing the separate public-deployment approval boundary.
- Patched Next and its matching lint rules to `16.2.11`, Cloudflare's Vite
  plugin to `1.46.0`, Vite to `8.1.5`, and Wrangler to `4.113.0` without
  changing the public site or offer.
- Forced the advisory-fixed PostCSS `8.5.22` and Sharp `0.35.3` releases across
  the dependency tree, then refreshed remaining vulnerable transitive packages
  within their supported ranges.
- Added a complete dependency-audit command and release-contract coverage that
  requires a zero-vulnerability result before a public site version is built,
  saved, approved, or deployed, plus runtime compatibility checks for the
  patched Sharp override and Miniflare.
- Marked unpublished Sites version 46 as superseded and prepared the exact
  security-hardened source for a replacement save while preserving the
  explicit public-publish approval boundary.
- Detected that the public site still advertises `v0.3.50` while the released
  download and paid-CI trust pins are on immutable `v0.3.51`.
- Built, tested, linted, and packaged the exact `v0.3.51` site source, pushed
  that commit to the existing Sites source repository, and saved Sites version
  46 without claiming it was publicly deployed.
- Added a release-contract test for the existing-project handoff, explicit
  public-publish approval, saved-versus-live distinction, and immediate
  post-deployment production audit.
- Independently reconciled the immutable public `v0.3.51` manifest, annotated
  tag, main ancestry, release workflow, and all three provenance attestations.
- Measured the released wheel digest separately and matched every downloaded
  artifact to the published checksum manifest.
- Advanced the dogfood and copy-ready policy gates to the exact `v0.3.51`
  source commit and wheel digest through the atomic six-target pin updater.
- Preserved the commercial boundary: verified CI distribution created no
  customer install, outreach attempt, pilot request, payment, or revenue.

## 0.3.51 - 2026-07-22

- Enabled GitHub release immutability for future repository releases.
- Required the release job to query the exact published tag and fail unless
  GitHub returns `immutable: true` under the current REST API contract.
- Added executable success, false-state, malformed-state, and API-failure
  coverage for release immutability verification.
- Documented that `v0.3.50` predates enforcement and remains digest-and-
  provenance verified but mutable.
- Carried the validated pilot price into growth-report offer recommendations
  instead of hard-coding `$299` when direct callers configure another price.
- Added a custom-price regression proving a `$400` pilot report recommends
  `$400` terms while leaving the public `$299` founding offer unchanged.
- Made `None` the only current-UTC default sentinel for pilot and outreach API
  report dates instead of treating every falsey value as omitted.
- Added cross-entry-point rejection coverage proving falsey non-date values fail
  before funnel construction or private outreach path access.
- Required genuine positive integers for direct pilot price, target-pilot, and
  stale-day controls before building revenue or follow-up evidence.
- Added controlled rejection coverage for boolean, float, and numeric-string
  values across all three pilot reporter controls.
- Rejected compact and ISO week-date spellings in every outreach ledger field
  and CLI date option before private queue selection or mutation.
- Added a guarded follow-up regression proving an earlier noncanonical due date
  cannot be reordered behind a later canonical date.
- Required explicit `pilot-paid` evidence before `pilot-converted` contributes
  to overall or segmented annual-conversion totals, while preserving its stage
  and skipped-payment warning for repair.
- Added a joined-growth regression proving an unsupported conversion cannot be
  hidden by a separate legitimate payment in the same aggregate segment.
- Required the paid-CI release manifest to contain exactly one canonical entry
  binding the pinned wheel digest to the expected wheel filename.
- Added executable missing, altered, and duplicate manifest regressions that
  fail before any provenance request, even when checksum tooling ignores absent
  artifacts.
- Kept wheel, manifest, and promotion checks inside each bounded release
  download attempt so successful one-asset responses retry instead of aborting.
- Added executable recovery and terminal-failure coverage for GitHub CLI calls
  that return success after downloading only the wheel.
- Disabled package-index access and pip's remote version check when both policy
  gates install the already verified local wheel.
- Kept dependency resolution disabled and made the customer and dogfood install
  blocks byte-identical under an executable Bash syntax contract.
- Documented that paid-CI activation contacts no Python registry after the
  bounded GitHub release download.
- Bound every public release attestation command to the exact repository,
  semantic tag, peeled source commit, signer workflow, and hosted-runner rule.
- Resolved the source commit from the remote annotated tag without requiring a
  repository checkout and stopped verification when it cannot be resolved.
- Used the platform checksum command available on Linux or macOS and added an
  offline Bash syntax contract for the published verification block.
- Extended the artifact-count documentation contract so every distributable
  must retain all five strict provenance identity constraints.
- Independently reconciled the public `v0.3.50` manifest, annotated tag, main
  ancestry, release workflow, and all three provenance attestations.
- Measured the released wheel digest separately and matched every downloaded
  artifact to the published checksum manifest.
- Advanced the dogfood and copy-ready policy gates to the exact `v0.3.50`
  source commit and wheel digest through the atomic six-target pin updater.
- Preserved the commercial boundary: verified CI distribution created no
  customer install, outreach attempt, pilot request, payment, or revenue.

## 0.3.50 - 2026-07-22

- Reported private outreach ledger staging-cleanup failures alongside the
  original guarded-mutation error instead of silently leaving a hidden copy.
- Replaced destination-derived lifecycle staging names with a neutral prefix
  and omitted filesystem details that could disclose a private ledger identity.
- Preserved the original ledger bytes and owner-only staging permissions while
  giving the operator an exact retained filename to remove before continuing.
- Refreshed public distribution, schema-7 pilot, and joined growth baselines
  after the independently verified `v0.3.49` release and paid-CI promotion.
- Recorded 50 additional primary artifact requests across four new releases
  and later `v0.3.45` activity: 45 wheel requests versus 5 portable requests.
- Preserved a warning-free zero-pilot, zero-revenue checkpoint that keeps
  acquisition and the bounded human outreach queue as the commercial bottleneck.
- Independently reconciled the public `v0.3.49` manifest, annotated tag, main
  ancestry, release workflow, and all three provenance attestations.
- Measured the released wheel digest separately and matched every downloaded
  artifact to the published checksum manifest.
- Advanced the dogfood and copy-ready policy gates to the exact `v0.3.49`
  source commit and wheel digest through the atomic six-target pin updater.
- Preserved the commercial boundary: verified CI distribution created no
  customer install, outreach attempt, pilot request, payment, or revenue.

## 0.3.49 - 2026-07-21

- Reported post-publication private-review cleanup failures instead of silently
  claiming success while a hidden staging copy remains.
- Preserved the completed owner-only review and identified a neutral retained
  staging filename so operators can clean it without exposing the destination
  name or retrying into overwrite protection.
- Created the first complete owner-only review bundle from the independently
  verified `v0.3.48` wheel without changing the private outreach ledger.
- Refreshed the committed counts-only outreach checkpoint to schema 9 after the
  bundle write, preserving 5 drafts, 16 fit links, 0 approvals, 0 attempts, and
  no private alias, address, message, review date, or evidence URL.
- Independently verified the public `v0.3.48` manifest, annotated tag, main
  ancestry, and provenance attestations for all three distributable artifacts.
- Measured the released wheel digest separately from the release workflow and
  reconciled it to the published checksum manifest.
- Advanced the dogfood and copy-ready policy gates to the exact `v0.3.48`
  source commit and wheel digest through the atomic six-target pin updater.
- Preserved the commercial boundary: CI distribution created no customer
  install, outreach attempt, pilot request, payment, or revenue.

## 0.3.48 - 2026-07-21

- Added `--write-review` to atomically create a complete outreach review bundle
  with owner-only permissions while keeping aliases, drafts, and evidence out
  of terminal output.
- Refused existing, symbolic-link, tracked, unignored, permissive-parent, and
  non-text review destinations without changing the private outreach ledger.
- Removed staged review files after success or failure and extended the
  installed-command smoke contract through the private write path.
- Preserved the commercial boundary: writing review evidence does not perform
  human judgment, approve or send outreach, create a pilot request, or record
  revenue.
- Independently verified the public `v0.3.47` manifest, annotated tag, main
  ancestry, and provenance attestations for all three distributable artifacts.
- Verified all seven installed command identities, the portable CLI, and four
  paid-workflow smoke harnesses from a fresh no-dependency `v0.3.47` wheel
  installation.
- Advanced the dogfood and copy-ready policy gates to the independently
  measured `v0.3.47` wheel digest and exact release source commit.
- Preserved the honest commercial boundary: verification and CI distribution
  created no customer install, outreach attempt, pilot request, payment, or
  revenue.
- Added the current verified-pin claim in `PROJECT_STATE.md` to the atomic
  maintainer pin update instead of relying on a separate manual edit.
- Preflighted the project-state layout with the other five targets and rolled
  back its replacement through the same permission-preserving transaction.
- Added focused success, permission, and mutation-free layout-drift coverage
  for the expanded six-target update.
- Rejected a verified-pin update when its numeric release version is older than
  the current claim in any workflow, buyer-facing document, state record, or
  executable contract target.
- Kept equal-version revalidation and forward upgrades supported while failing
  a downgrade before any transaction file is staged or replaced.
- Added per-target regression coverage proving all six version claims enforce
  the same monotonic release boundary without partial writes.
- Updated the maintainer CI guide to name all six atomic pin targets and the
  downgrade, same-version, permission-preservation, and rollback contracts.
- Added an executable documentation check so those release-upgrade instructions
  cannot regress to the older shape-only, five-target description.
- Added `--check` to the maintainer release-pin updater so all six layouts,
  identities, and downgrade boundaries can be reviewed without a write.
- Emitted `verified` target receipts in check mode while leaving every file,
  permission bit, and staging path unchanged.
- Documented the preflight-before-update workflow and covered its exact output
  and mutation-free behavior through the command entry point.

## 0.3.47 - 2026-07-20

- Added schema-9 recovery for the next approved outreach alias when the
  one-time approval receipt is no longer visible.
- Regenerated the guarded contact-recording handoff with required UTC date
  placeholders while omitting drafts, evidence, channels, and approval dates.
- Marked reports with a next-approved or due-follow-up alias as private through
  a machine-readable flag and matching terminal warning.
- Marked reports with neither alias source as counts-only so publication
  automation can reject private execution evidence before committing it.
- Added `--require-counts-only` to emit only alias-free ordinary reports and
  fail with exit code 7 before private JSON or text reaches standard output.
- Made the publication guard mutually exclusive with every review and lifecycle
  action so it cannot mutate the private ledger.
- Extended source, documentation, and installed-command contracts without
  sending outreach or changing attempted-prospect and revenue boundaries.
- Corrected the private outreach playbook from a stale nine-column requirement
  to the current ten-column ledger contract ending in `outcome_on`.
- Derived the template and operator-guide column checks from the runtime
  `LEDGER_FIELDS` schema while retaining explicit legacy nine-column reads.
- Independently verified the public `v0.3.46` manifest, annotated tag, main
  ancestry, and provenance attestations for all three distributable artifacts.
- Verified all seven installed command identities and four paid-workflow smoke
  harnesses from a fresh no-dependency `v0.3.46` wheel installation.
- Advanced the dogfood and copy-ready policy gates to the independently
  measured `v0.3.46` wheel digest and exact release source commit.
- Preserved the honest commercial boundary: verification and CI distribution
  created no customer install, outreach attempt, pilot request, payment, or
  revenue.

## 0.3.46 - 2026-07-20

- Added a required `--outcome-on` date so private outreach outcomes can retain
  an earlier human observation while the complete ledger is audited today.
- Rejected outcome observations after `--as-of` and emitted separate
  recording-date, observation-date, and status placeholders in every handoff.
- Extended source and installed-wheel lifecycle coverage through delayed reply
  recording and later terminal classification.
- Preserved the first observed private outreach outcome date when a generic
  reply is later classified as a pilot request, rejection, or opt-out.
- Added source and installed-package lifecycle regressions proving refinement
  changes the status without replacing the original observation date.
- Retained the human-observed date for every newly recorded private outreach
  outcome in a durable `outcome_on` ledger field.
- Rejected outcome dates outside contact and follow-up chronology, future
  observations, and refinements backdated before the original generic reply.
- Kept legacy nine-column ledgers readable while reporting undated historical
  outcomes explicitly and upgrading later guarded writes to ten columns.
- Warned when a `pilot-lost` record lacks the required cumulative `pilot-lead`
  history.
- Kept the explicit loss visible while preventing that skipped public-request
  milestone from passing as warning-free funnel evidence.
- Added focused coverage for the loss total, zero revenue, and exact missing
  label.
- Aligned the business model, distribution guide, and pilot operator guide on
  the exact `pilot-paid` revenue boundary.
- Removed stale language that allowed later lifecycle labels to stand in for
  missing payment evidence.
- Added an executable documentation contract that prevents those three
  commercial guides from restoring the inferred-payment rule.
- Required the exact `pilot-paid` label before a public pilot contributes to
  booked-pilot or booked-revenue totals.
- Kept later-stage label drift visible while excluding its unsupported revenue
  from source, readiness, and purchase-criterion segments.
- Corrected the synthetic drift fixture from four inferred bookings to three
  evidenced bookings and the exact $897 target.
- Added outcome receipt schema 2 with the existing source-prefilled public
  pilot intake URL only for confirmed private `pilot-requested` outcomes.
- Printed the same buyer-controlled handoff in default text while leaving every
  other outcome at an explicit JSON null with no text link.
- Extended source and installed-command contracts without opening a form,
  submitting intake, or converting private interest into public demand.
- Extended the private-notes commit-race regression from approval to both
  content-bound review decisions.
- Approval and decline now share proof that an edit during the locked commit
  window preserves ledger bytes, hides changed text, and removes staged output.
- Preserved complete private evidence-and-draft review context when a
  content-bound decline advances to another prepared prospect.
- The next-review handoff now retains both disclosure flags and the exact
  shell-quoted notes path while requiring a fresh UTC review date.
- Added a two-draft regression proving the emitted command produces a new
  content-bound digest without exposing the previously declined message.
- Added a guarded, shell-quoted refinement handoff after a generic outreach
  reply, limited to pilot request, rejection, or opt-out outcomes.
- Required a fresh observation date and explicit terminal status while keeping
  terminal outcome receipts free of another action command.
- Extended installed-command lifecycle proof from generic reply through private
  pilot classification without treating it as public demand or revenue.
- Added exact, shell-quoted outcome handoffs to contact and follow-up receipts,
  preserving the prospect alias and private ledger path.
- Required operators to replace both observation-date and outcome placeholders;
  unchanged handoffs fail before the private ledger is read or modified.
- Extended installed-command lifecycle proof through a human-observed response
  without turning private outreach evidence into public demand or revenue.
- Carried the bounded private draft-notes revision from content receipt
  verification into the locked approval and decline commit.
- Private notes edited during that commit window now force a fresh review while
  preserving the unmodified outreach ledger and removing staged output.
- Replaced the prior decline date in next-draft review handoffs with a required
  `YYYY-MM-DD` placeholder for the actual UTC review date.
- Unchanged next-review placeholders now fail before reading or modifying the
  remaining private draft queue.
- Revalidated the private outreach ledger's file type and owner-only permissions
  inside every locked lifecycle commit.
- Late permission drift now stops the action without replacing ledger bytes or
  leaving its staged private file behind.
- Added per-ledger operating-system locks and SHA-256 revision checks to every
  mutating outreach lifecycle action.
- Concurrent or stale writers now fail with a retry instruction while
  preserving the newer private ledger, its permissions, and truthful attempt
  counts.
- Fixed conflicting `pilot-converted` plus `pilot-lost` records so they no
  longer inflate either resolved conversion or loss totals.
- Preserved historical booked revenue for conflict records that reached
  `pilot-paid`, while retaining their visible conflict stage and warning.
- Extended the production audit to require the exact $299 founding-team service
  and a website-attributed link to the public pilot application.
- Added controlled failures for missing, duplicated, mispriced, or mislinked
  paid pilot conversion metadata without changing the offer or funnel.
- Added a daily, manually dispatchable production-site audit workflow with
  read-only repository access, immutable action pins, and no secrets.
- Added a workflow contract that locks its schedule, timeout, Python runtime,
  exact audit command, and least-privilege boundary.
- Added a dependency-free production-site audit for canonical metadata, the
  current free software offer, release version, and portable download URL.
- Added controlled failures for stale versions, stale downloads, malformed
  structured offers, unexpected content types, and unavailable production.
- Documented the read-only post-deployment check without adding a new campaign
  route, product feature, or demand claim.
- Refreshed the warning-free commercial evidence checkpoint after the verified
  `v0.3.45` release and CI rollout.
- Recorded 17 additional primary artifact requests: 7 on `v0.3.45` and 10 later
  `v0.3.44` wheel requests, all materially confounded by Repo Scout's own
  release, verification, and policy-gate activity.
- Preserved zero pilot requests, zero outreach attempts, and $0 booked revenue,
  with human-reviewed outreach still the commercial priority.
- Independently verified the public `v0.3.45` manifest, annotated tag, source
  ancestry, exact signer workflow, hosted runner, and provenance for all three
  distributable artifacts.
- Verified all seven installed commands and four paid-workflow smoke harnesses
  from a fresh no-dependency `v0.3.45` wheel installation.
- Advanced the dogfood and copy-ready policy gates to the independently measured
  `v0.3.45` wheel digest and exact release source commit.
- Preserved the honest commercial baseline: no customer install, outreach
  attempt, pilot request, payment, demand, or revenue resulted from this work.

## 0.3.45 - 2026-07-18

- Replaced approval-date and due-date assumptions in generated contact and
  follow-up commands with required `YYYY-MM-DD` placeholders for the actual
  human send dates.
- Added lifecycle coverage for approval on July 1, contact on July 3, and the
  correctly derived July 10 follow-up, including mutation-free placeholder
  rejection.
- Corrected the stale commercial paid-CI claim from verified `v0.3.43` to
  `v0.3.44` and added it as a preflighted, atomic release-pin updater target.
- Extended the live CI contract to require the README, business model, both
  policy gates, and pin constants to advertise one verified release version.
- Linked public `pilot-active` application to every paid delivery contract
  condition, including the acknowledged first-repository handoff, while
  keeping private evidence out of the public issue.
- Added executable proof that the documented local delivery workspace commands
  create a `700` directory and `600` completed record, with the delivery
  contract included in the hosted pilot gate.
- Added an ignored `pilot-private/` workspace and owner-only POSIX setup for
  short-lived completed delivery records.
- Added executable coverage that the completed-record path is ignored while the
  blank public template remains trackable.
- Added a copy-ready private paid-pilot delivery record with exactly 10
  repository slots, an explicit CI integration choice, five acceptance
  checklists, first-repository acknowledgement, and 90-day closeout.
- Extended the delivery contract test to keep the blank template free of
  customer data and preserve paid-before-active-before-converted ordering.
- Added a tested paid-pilot delivery contract covering private scope records,
  the five $299 deliverables, shipped-command acceptance evidence, and exact
  payment, activation, and annual-conversion boundaries.
- Linked the copy-ready CI guide to that post-payment contract without adding a
  new acquisition channel, software feature, or unearned revenue claim.
- Refreshed the warning-free commercial evidence checkpoint after the verified
  `v0.3.44` release and CI rollout.
- Recorded 11 additional primary artifact requests: 7 on `v0.3.44` and 4 later
  `v0.3.43` wheel requests, all materially confounded by Repo Scout's own
  release, verification, and policy-gate activity.
- Preserved zero pilot requests, zero outreach attempts, and $0 booked revenue,
  with human-reviewed outreach still the commercial priority.
- Independently verified the public `v0.3.44` manifest, annotated tag, source
  ancestry, exact signer workflow, hosted runner, and wheel provenance.
- Verified all seven installed commands and four paid-workflow smoke harnesses
  from a fresh no-dependency `v0.3.44` wheel installation.
- Advanced the dogfood and copy-ready policy gates to the independently measured
  `v0.3.44` wheel digest and exact release source commit.
- Preserved the honest commercial baseline: no customer install, demand signal,
  outreach attempt, pilot request, payment, or revenue resulted from this work.

## 0.3.44 - 2026-07-18

- Standardized direct-outreach report defaults and every copy-ready lifecycle
  command on the current UTC calendar date.
- Added regression coverage that prevents local-midnight review, approval,
  contact, follow-up, and outcome dates from drifting across operator timezones.
- Extended the installed-command release smoke to prove the UTC default while
  the process runs under a deliberately different local calendar date.
- Refreshed the warning-free commercial evidence checkpoint after the verified
  `v0.3.43` release and CI rollout.
- Recorded 14 additional primary artifact requests: 7 on `v0.3.43` and 7 later
  `v0.3.42` wheel requests, all materially confounded by Repo Scout's own
  release, verification, and policy-gate activity.
- Preserved zero pilot requests, zero outreach attempts, and $0 booked revenue,
  with human-reviewed outreach still the commercial priority.
- Independently verified the public `v0.3.43` manifest, annotated tag, source
  ancestry, exact signer workflow, hosted runner, and provenance for all three
  distributable artifacts.
- Advanced the dogfood and copy-ready policy gates to the independently measured
  `v0.3.43` wheel digest and exact release source commit.
- Verified all seven installed commands and the four paid-workflow smoke
  harnesses from a fresh no-dependency wheel installation before changing pins.

## 0.3.43 - 2026-07-17

- Added schema-4 content-bound SHA-256 receipts for complete private outreach
  reviews, covering the normalized ledger row, selected draft, review date, and
  five human checks.
- Carried each receipt and reviewed notes path into generated approve and
  decline commands, with mutation-free rejection when evidence or draft content
  changed after human review.
- Extended source and release-smoke coverage for matching reviews, stale
  private drafts, stale fit evidence, private error output, and unchanged
  ledgers.
- Refreshed the owner-visible 14-day repository traffic checkpoint to 3 views
  from 1 unique viewer, 293 unique cloners, and 962 clone events.
- Recorded that the overlapping-window rise of 652 clone events produced only
  2 additional views and no additional unique viewer, preserving acquisition
  as the commercial bottleneck instead of presenting automation as adoption.
- Corrected the traffic contract to treat GitHub's popular referrers and paths
  as partial rankings, with stricter UTC cadence, nonnegative-count, and
  uniqueness validation.
- Added four bounded provenance-verification attempts to both policy gates while
  retaining the pinned wheel, repository, source, tag, signer workflow, and
  hosted-runner requirements on every attempt.
- Executed transient and terminal provenance failures with fake network commands
  to prove exact waits, recovery, and explicit fourth-attempt failure.
- Executed the verified-release download block against a fake GitHub CLI to
  prove third-attempt recovery, exact backoff waits, complete artifact
  promotion, four-attempt termination, and exclusion of partial trusted files.
- Added four isolated verified-release download attempts with bounded backoff
  to the dogfood and copy-ready policy gates after an observed GitHub REST
  outage caused a false-negative check.
- Added a workflow parity contract for the retry count, isolated attempt paths,
  successful artifact promotion, and explicit terminal failure.
- Refreshed the warning-free commercial evidence checkpoint after the verified
  `v0.3.42` release and CI rollout.
- Recorded 15 additional primary artifact requests: 3 on `v0.3.42` and 12 later
  `v0.3.41` wheel requests, all materially confounded by Repo Scout's own
  release, verification, and policy-gate activity.
- Preserved zero pilot requests, zero outreach attempts, and $0 booked revenue,
  with acquisition and human-reviewed outreach still the commercial priority.
- Independently verified the public `v0.3.42` manifest, annotated tag, source
  ancestry, signer workflow, GitHub-hosted runner, and provenance for all three
  distributable artifacts.
- Advanced the dogfood and copy-ready policy gates to the independently measured
  `v0.3.42` wheel digest and exact release source commit.
- Verified all seven installed commands and the four paid-workflow smoke
  harnesses from a fresh no-dependency wheel installation before changing pins.

## 0.3.42 - 2026-07-16

- Made `repo-scout --output --force` stage complete reports before atomically
  replacing existing handoff or rollout evidence.
- Preserved existing report permissions and kept prior report bytes unchanged
  when the final replacement fails.
- Preserved existing POSIX permission bits when `repo-scout-policy init --force`
  or guarded bootstrap atomically replaces a team policy.
- Made permission-application failures leave the original policy unchanged and
  remove the unused temporary file.
- Made verified-pin temporary cleanup failures report whether replacements were
  already committed or a failed write was rolled back.
- Preserved original write and rollback evidence when cleanup also fails, with
  focused coverage for both post-commit and recovery paths.
- Corrected the distribution adoption path from six to seven packaged wheel
  commands.
- Derived release-smoke command coverage and the documented command-count
  contract from `[project.scripts]` package metadata.
- Corrected the public release guide from two to three expected checksum and
  provenance-verification results across the portable, wheel, and source
  artifacts.
- Added an artifact-count-derived contract test for downloaded-file, checksum,
  and attestation-command coverage in the buyer-facing verification guide.
- Normalized verified-pin target modes to permission bits before staging
  replacements and rollback copies.
- Added regression coverage proving successful updates and rollback restores
  preserve target permissions, recovery copies retain the original mode, and
  completed transactions remove every staging file.
- Corrected the buyer-facing outreach documentation to describe the packaged
  schema-6 approval and review-decline counts instead of calling schema 5
  unreleased.
- Added a runtime-linked contract test that fails when the documented outreach
  schema drifts from `repo-scout-outreach` behavior.
- Made mid-commit verified-pin write failures restore every already-replaced
  workflow, README, and contract target from staged originals.
- Added a deterministic second-write failure test proving all target contents
  and temporary files return to their pre-update state, plus recovery-copy
  coverage when rollback itself fails.
- Added the buyer-facing README release claim to the preflighted pin updater
  and CI contract so it cannot silently drift behind both customer workflows.
- Corrected the stale copy-ready CI claim from `v0.3.29` to independently
  verified `v0.3.41` without changing the separate current-release quick start.
- Refreshed the warning-free commercial evidence checkpoint after the verified
  `v0.3.41` release and CI rollout.
- Recorded 8 additional primary artifact requests: 5 on `v0.3.41` and 3 later
  `v0.3.40` wheel requests, all materially confounded by Repo Scout's own
  release, verification, and policy-gate activity.
- Preserved zero pilot requests, zero outreach attempts, and $0 booked revenue,
  with acquisition still identified as the commercial bottleneck.
- Independently verified and pinned the `v0.3.41` wheel, source commit
  `7fa869310fe1dc1f07cff13a7768f36e4654ce22`, and SHA-256
  `4f6ef0dd1b996b5c0a35c53b4be7e528a53a4548c80dc1333fc7d8010822281e`
  in both CI gates.
- Reconciled all four release assets with the manifest, annotated tag, signer
  workflow, provenance, successful release job, and GitHub-hosted runner.
- Installed the public wheel without dependencies and proved all command
  versions, policy activation, guarded outreach outcomes, commercial reporting,
  and rollout aggregation through the packaged entry points.

## 0.3.41 - 2026-07-15

- Added guarded `repo-scout-outreach --record-outcome` recording for exact
  contacted aliases after a human observes a reply, pilot request, rejection,
  or opt-out.
- Allowed asynchronous outcomes after initial contact or follow-up, plus later
  refinement of a generic reply, while atomically preserving contact history
  and clearing any pending follow-up.
- Made unconfirmed and invalid outcome transitions mutation-free and extended
  the release smoke through a private pilot-requested outcome without treating
  it as public demand or revenue evidence.
- Refreshed the warning-free commercial evidence checkpoint after the verified
  `v0.3.40` release and CI rollout.
- Recorded 6 additional primary artifact requests: 3 on `v0.3.40` and 3 later
  `v0.3.39` wheel requests, all materially confounded by Repo Scout's own
  release, verification, and policy-gate activity.
- Preserved zero pilot requests, zero outreach attempts, and $0 booked revenue,
  with acquisition still identified as the commercial bottleneck.
- Independently verified and pinned the `v0.3.40` wheel, source commit
  `9a8db84a5ebe640eb33634279845bb58e4aa900f`, and SHA-256
  `d973eb08d7209bc14630482c86d7b34d3805e38ed7e25b9b54daab7afa0f9241`
  in both CI gates.
- Reconciled every release artifact with its manifest, semantic tag, signer
  workflow, provenance, successful release job, and hosted-runner constraint.
- Installed the public wheel without dependencies and proved all command
  versions, policy activation, guarded outreach, commercial reporting, and
  rollout aggregation through the packaged entry points.

## 0.3.40 - 2026-07-15

- Made guarded decline receipts report the privacy-safe number of drafts still
  awaiting review and stop emitting a nonexistent next-review command at zero.
- Advanced the decline receipt to schema 2 and made the installed lifecycle
  smoke prove the one-draft review queue terminates truthfully.
- Refreshed the warning-free commercial evidence checkpoint after the verified
  `v0.3.39` release and CI rollout.
- Recorded 6 additional primary artifact requests: 3 on `v0.3.39` and 3 later
  `v0.3.38` wheel requests, all materially confounded by Repo Scout's own
  release, verification, and policy-gate activity.
- Preserved zero pilot requests, zero outreach attempts, and $0 booked revenue,
  with acquisition still identified as the commercial bottleneck.
- Independently verified and pinned the `v0.3.39` wheel, source commit
  `86886448f86dbfdc04f03248cc8017a81e688dbe`, and SHA-256
  `9fe9317b0e479e6b874d68c35511785308b373fff10367a76dc3006b5a667e36`
  in both CI gates.
- Reconciled every release artifact with its manifest, semantic tag, signer
  workflow, provenance, successful release job, and hosted runner.
- Installed the public wheel without dependencies and proved all command
  versions, policy activation, guarded no-send outreach, commercial reporting,
  and rollout aggregation through the packaged entry points.

## 0.3.39 - 2026-07-15

- Added a guarded human no-send decision for the deterministic next outreach
  draft, atomically moving only its status to `review-declined`.
- Counted review-declined drafts as closed before contact rather than attempts,
  while requiring the same private path, permission, validation, and exact-alias
  boundaries as approval.
- Emitted copy-ready approve and decline choices from text review output and
  made the installed-command release smoke execute the negative branch.
- Refreshed the warning-free commercial evidence checkpoint after the verified
  `v0.3.38` release and CI rollout.
- Recorded 21 additional primary artifact requests: 5 on `v0.3.38`, 12 on
  `v0.3.37`, and 4 later `v0.3.36` wheel requests, all materially confounded by
  Repo Scout's own release, verification, and policy-gate activity.
- Preserved zero pilot requests, zero outreach attempts, and $0 booked revenue,
  with acquisition still identified as the commercial bottleneck.
- Independently verified and pinned the `v0.3.38` wheel, source commit
  `3f074aad56670d70645c858b4f5d6f58182b33ef`, and SHA-256
  `9775171f3d19d4a6ca75d66bc1553910c1beba9feb18cd5172c799cb01d2f5d5`
  in both CI gates.
- Reconciled every release artifact with its manifest, semantic tag, signer
  workflow, provenance, successful release job, and hosted runner.
- Installed the public wheel without dependencies and proved all command
  versions, policy activation, guarded outreach, commercial reporting, and
  rollout aggregation through the packaged entry points.

## 0.3.38 - 2026-07-15

- Refused live outreach review, approval, contact, and follow-up actions on
  POSIX when a private ledger, draft file, or immediate parent directory grants
  group or world access.
- Kept counts-only audits available for public templates while proving
  permissive private ledgers fail without mutation through the installed
  command lifecycle.
- Emitted complete shell-quoted commands from private outreach review,
  approval, and contact text output, carrying the exact alias, action date,
  confirmation flag, and ledger path into the next human-controlled step.
- Executed those emitted commands through the complete installed-command
  lifecycle, including a ledger path with spaces and the exact follow-up due
  date, while retaining all existing JSON privacy checks.
- Refused live outreach review, approval, contact, and follow-up actions when
  an in-repository ledger or draft file is tracked, not ignored, or symlinked.
- Kept counts-only template audits available while proving ignored, untracked
  private bundles still pass review without modifying the ledger.
- Made new outreach workspaces owner-only with `700` directory and `600` file
  setup instructions and regression coverage.
- Independently verified and pinned the `v0.3.37` wheel, source commit
  `d0fd199894b2c7a1ea0b3097a122e37399990568`, and SHA-256
  `b241330e0614cb4759bf764d353cf46871f6957a01f78541f65a9a73bd3b9864`
  in both CI gates.
- Reconciled every release artifact with its manifest, semantic tag, signer
  workflow, provenance, successful release job, and hosted runner.
- Installed the public wheel without dependencies and proved all command
  versions, policy activation, and the exact outreach opt-out review check.

## 0.3.37 - 2026-07-14

- Made the initial direct-outreach template and all five private drafts state a
  clear opt-out that ends further contact.
- Tightened the human review checklist and regression contract so a vague
  decline prompt cannot silently replace that promise.
- Refreshed the warning-free commercial evidence checkpoint after the verified
  `v0.3.36` release and CI rollout.
- Recorded 11 additional primary artifact requests: 7 on the new release and 4
  wheel requests on `v0.3.35`, all materially confounded by Repo Scout's own
  release, verification, and policy-gate activity.
- Preserved zero pilot requests, zero outreach attempts, and $0 booked revenue,
  with acquisition still identified as the commercial bottleneck.
- Independently verified and pinned the `v0.3.36` wheel, source commit
  `f4f4d33fd19ce8287298bfef38458d3328fff3ad`, and SHA-256
  `282cad5ee04f388c5487f87b0c99e1423a4d879ba0a4174680bb104d4e7d6e97`
  in both CI gates.
- Reconciled all three distributable artifacts with the checksum manifest,
  semantic tag, signer workflow, provenance, and `ubuntu-24.04` release job.
- Installed the public wheel without dependencies and proved all command
  versions plus policy activation and the private outreach review lifecycle.

## 0.3.36 - 2026-07-14

- Preflighted private draft notes against the complete outreach ledger before
  review, requiring coverage for every drafted alias and rejecting unknown ones.
- Preserved notes for approved or contacted aliases as private history while
  keeping review output limited to the deterministic next prospect.
- Made note-to-ledger identity drift release-blocking and proved controlled
  rejection does not modify the ledger or expose private message text.
- Added `--include-private-draft DRAFTS_MD` as an explicit `--review-next`
  opt-in that selects only the next alias's bounded Markdown section.
- Rejected duplicate, malformed, empty, oversized, and missing selected draft
  sections without modifying the private ledger or exposing other messages.
- Extended the release smoke test through one combined private draft-and-evidence
  review bundle while preserving redacted default output and human-only approval.
- Refreshed the warning-free distribution, pilot, growth, and aggregate outreach
  baselines at the first verified `v0.3.35` post-release checkpoint.
- Recorded 31 additional primary artifact requests across three new complete
  releases, including 28 wheel requests materially confounded by Repo Scout's
  own release, CI, pinning, and maintainer verification.
- Preserved the commercial truth of zero pilot requests, zero outreach attempts,
  and $0 revenue, with acquisition still identified as the bottleneck.
- Added `--include-private-evidence` as an explicit `--review-next` opt-in so a
  human can inspect the selected draft's fit-signal sources without parsing CSV.
- Kept default review output redacted and marked evidence-bearing text and JSON
  as private material that must not enter committed reports or CI artifacts.
- Extended release smoke coverage to prove private evidence disclosure is
  complete, explicit, and read-only before guarded approval can proceed.
- Independently verified and pinned the `v0.3.35` wheel, source commit
  `d095f2f9db4991e7c9f69d6f939b8bdf9a40964f`, and SHA-256
  `c3730e78d55d04385062931f6f2f3c5ba022120c8fc43a5117db9e06f109a650` in both CI gates.
- Confirmed all release assets against the checksum manifest, semantic tag,
  signer workflow, provenance, and GitHub-hosted runner before changing pins.
- Installed the public wheel without dependencies and proved policy activation,
  command-version identity, and the guarded outreach lifecycle before advancing
  the copy-ready customer workflow.

## 0.3.35 - 2026-07-14

- Added a consistent `--version` flag to every public Repo Scout command and the
  portable zipapp for support and CI diagnostics.
- Required all seven built-wheel commands and the zipapp to report the exact
  tagged package version before release provenance attestation.
- Added one shared version-argument implementation and contract coverage for
  every parser, installed entry point, and portable distribution path.
- Completed installed-entry-point release coverage by routing policy activation,
  main policy enforcement, guarded outreach, and rollout aggregation through
  the built wheel's public commands.
- Added controlled missing-command rejection to the policy, outreach, and
  rollout smoke harnesses while preserving fast source-module test mode.
- Required all four behavioral release harnesses to receive the exact wheel
  installation directory before provenance attestation.
- Routed release-blocking pilot, distribution, and growth behavior through the
  built wheel's public console commands rather than their Python modules.
- Added controlled rejection when any required installed commercial command is
  missing or not executable, while retaining fast module-mode source coverage.
- Required the release workflow to supply its exact installation directory to
  the commercial smoke harness before provenance attestation.
- Replaced the hand-built reach delta in the installed commercial smoke test
  with baseline and current raw GitHub release exports processed by
  `repo-scout-distribution` from the built wheel.
- Proved the packaged artifact contract, signed `+6` primary request movement,
  and request-not-customer measurement boundary before joining growth evidence.
- Made duplicate release assets fail without a report alongside the existing
  inconsistent primary-versus-channel growth-delta rejection.
- Extended the installed commercial-reporting smoke test through
  `repo-scout-growth` with signed synthetic distribution movement.
- Proved packaged reach, qualification, attribution, one $299 booking, and the
  open $897 pilot target reconcile to the `pilot_target` bottleneck.
- Preserved the no-conversion-rate and paid-stage revenue boundaries, and made
  inconsistent primary-versus-channel deltas release-blocking.
- Added an installed-wheel cross-repository rollout smoke test to releases.
- Proved matching policy fingerprints, complete commit coverage, and one ready
  plus one remediation-required repository survive packaged aggregation.
- Kept repository IDs, fingerprints, commits, and evidence paths out of default
  output while testing explicit details and duplicate-repository rejection.
- Added an installed-wheel pilot-funnel smoke test to the release boundary.
- Proved a synthetic offer remains outside revenue while one synthetic paid
  pilot books $299 toward the three-pilot, $897 target.
- Covered target-profile qualification, source attribution, the open sales
  queue, operator text, free-text omission, and controlled invalid input.
- Expanded the installed-wheel outreach release check from prebuilt rows to a
  complete synthetic draft-review, approval, contact, and follow-up journey.
- Proved the wheel preserves private dates and evidence, ledger permissions,
  the seven-day cadence, and one attempted-prospect count through every step.
- Made unconfirmed approval and duplicate follow-up rejection release-blocking,
  including byte-for-byte proof that failed actions do not modify the ledger.
- Added guarded `repo-scout-outreach --record-follow-up` recording for the
  earliest due contacted alias after a human confirms the one allowed follow-up.
- Rejected early, future, and out-of-order follow-up records while retaining
  approval and initial-contact evidence through an atomic ledger replacement.
- Cleared the completed row's next action to prevent a second follow-up, with an
  alias-only private receipt and no automated delivery or scheduling.
- Added guarded `repo-scout-outreach --record-contact` recording for the exact
  next human-approved alias after a human confirms the message was already sent.
- Retained private approval evidence while atomically changing only status,
  contact date, and the automatically calculated seven-day next action.
- Kept recording distinct from delivery: Repo Scout sends nothing, schedules no
  automatic follow-up, and omits evidence and approval dates from a receipt
  kept private because its follow-up date makes send timing inferable.
- Added guarded `repo-scout-outreach --approve-next` recording for the exact
  alias selected by the deterministic one-at-a-time review queue.
- Required an explicit review date and human-confirmation flag, with full-ledger
  validation before and after a permission-preserving atomic CSV replacement.
- Kept approval distinct from contact: the action creates no contact or
  follow-up date, sends nothing, and omits private evidence and review dates
  from its receipt.
- Added `repo-scout-outreach --review-next` to surface one deterministic,
  alias-only draft with five explicit criteria for the required human decision.
- Kept review output private and free of evidence URLs, draft text, approval
  dates, recipient details, and any automatic ledger mutation or sending.
- Preserved zero approval and attempt semantics: an unchecked checklist remains
  operator preparation, not contact, pilot demand, or revenue evidence.
- Independently verified and pinned the `v0.3.34` wheel, source commit
  `fbfbbc59350b1b0f6e411f2cb481b3c447ea7a0b`, and SHA-256
  `f2164f4b328c0d311e16492faf16a52d42c3944073a850b9d64d9b8a013cb668` in both CI gates.
- Confirmed all release assets against the checksum manifest, semantic tag,
  signer workflow, provenance, and GitHub-hosted runner before changing pins.
- Installed the public wheel without dependencies and proved policy activation
  plus strict outreach approval, contact, privacy, and row-width behavior.

## 0.3.34 - 2026-07-13

- Published strict nine-column outreach parsing in the wheel and source archive,
  with installed-wheel lifecycle verification before release publication.
- Advanced website metadata, machine-readable software identity, public install
  instructions, and the verification guide to the same `v0.3.34` artifact set.
- Added an installed-wheel outreach lifecycle smoke test covering approved and
  contacted states plus the human-approval and aggregate-count contract.
- Required future releases to prove approved-row aliases, evidence URLs, and
  approval dates stay out of aggregate reports before attestation.
- Blocked publication when the installed outreach command accepts a missing
  approval date or an extra private CSV cell.
- Replaced permissive outreach row mapping with strict standard-library CSV
  parsing and exact nine-column enforcement.
- Rejected malformed quoting plus missing and extra row cells with controlled
  errors that do not echo private prospect values.
- Normalized the ignored five-draft ledger to the exact schema without changing
  approval, attempt, pilot-request, or revenue evidence.
- Independently verified and pinned the `v0.3.33` wheel, source commit
  `b2838064940003ebfb40af686ea91445eae9c984`, and SHA-256
  `66c120d5107b9e51986dd08a884d66db06eef54629af208b82456506562e2e3e` in both CI gates.
- Confirmed the exact release assets, checksum manifest, semantic tag, signer
  workflow, provenance, and GitHub-hosted runner before changing trust metadata.
- Installed the downloaded wheel without dependencies and proved its package
  version and schema-5 outreach behavior before advancing customer CI.

## 0.3.33 - 2026-07-12

- Published the schema-5 outreach approval workflow in the portable, wheel,
  and source distributions with the existing checksum and provenance contract.
- Advanced website metadata, machine-readable software identity, and public
  install instructions to the same `v0.3.33` artifact set.
- Added outreach schema 5 with a private `approved_on` date that must persist
  from human approval through every later lifecycle status.
- Rejected missing and future approval dates plus approvals recorded after the
  contact date, closing the status-only review gap.
- Kept approval dates out of text and JSON reports while exposing that human
  approval is required as non-sensitive experiment metadata.
- Extended the public and ignored private ledger headers without changing the
  existing five-draft, zero-approval, zero-attempt evidence.
- Added outreach schema 4 with an explicit `approved` status between a saved
  draft and a sent contact.
- Reported drafts awaiting review and human-approved messages separately while
  excluding both from attempted-prospect totals.
- Required approved messages to retain a permitted channel and no contact or
  follow-up dates until they are actually sent.
- Documented the one-at-a-time review, approval, send, and exact seven-day
  follow-up workflow without changing the five-draft, zero-attempt baseline.
- Refreshed public distribution, schema-7 pilot, and joined growth baselines at the first qualified-draft review point.
- Recorded 17 additional primary artifact requests across two new complete releases, while preserving zero pilot requests and $0 booked revenue.
- Advanced baseline contracts to `v0.3.32` and schema-7 qualification evidence with no distribution, pilot, or growth warnings.
- Prepared five personalized outreach drafts from narrow, company-controlled public evidence and kept all identities, business addresses, messages, and source links in the ignored private workspace.
- Audited the batch as five schema-3 drafts with 16 fit-evidence links and zero contact attempts, replies, pilot requests, or revenue.
- Added a counts-only outreach baseline and regression coverage that rejects leaked aliases, URLs, or email addresses from the committed evidence.
- Independently verified and pinned the `v0.3.32` wheel, source commit `2c983c8db3d32ec40b8a20ed585dfc2a48feed2c`, and SHA-256 `14ed1f4bd1138574a59cd86c68cf0f67395216a902e0a49aef2d6d98d4173649` in both CI gates.
- Confirmed the wheel against its release manifest, semantic tag, signer workflow, provenance, and GitHub-hosted runner before changing customer trust metadata.

## 0.3.32 - 2026-07-12

- Upgraded pilot reporting to schema 7 with normalized team size, repository count, CI provider, and repository-standard-presence evidence.
- Classified every tracked request as target, outside-target, or incomplete while preserving explicit review reasons.
- Flagged teams with more than 10 repositories for a first-10 subset instead of rejecting an otherwise qualified multi-repository buyer.
- Kept repository-standard free text out of funnel, follow-up, and sales-queue output.
- Extended weekly growth reviews to accept schema-7 reports while retaining schema-5 and schema-6 compatibility.
- Recorded that workspace search found no suitable Repo Scout prospect list and excluded an unrelated healthcare contact workbook; no prospect or outreach activity was claimed.
- Independently verified and pinned the `v0.3.31` wheel, source commit `949b345c71f800d384ea4b2f056efc7e7a41a6d3`, and SHA-256 `9742b31057e657a4db9a1cc2664c3d40e0bcfd87c659e856f6f4753d4b009db0` in both CI gates.
- Confirmed the wheel against its release manifest, version tag, signer workflow, provenance, and GitHub-hosted runner before changing customer trust metadata.
- Kept package and site version `0.3.31` unchanged; no redundant release, prospect, outreach attempt, lead, or revenue was claimed.

## 0.3.31 - 2026-07-12

- Required every private outreach fit signal to map to one reviewable HTTPS evidence link before a prospect can pass the auditor.
- Rejected missing, extra, duplicate, insecure, credential-bearing, and malformed qualification evidence.
- Added schema-3 aggregate qualification-link counts while keeping source URLs and prospect identities out of report output.
- Updated the empty private-ledger template and direct-outreach playbook for Sales Intelligence or narrow public evidence links.
- Recorded that no connected Sales Intelligence provider or reviewed list was available, so no prospect, draft, attempt, lead, or revenue was claimed.
- Added a dependency-free maintainer audit for the seven live GitHub labels that connect public pilot intake to revenue reporting.
- Added an explicit repair mode for missing labels and changed colors or descriptions while leaving unexpected labels untouched for review.
- Added a dedicated, read-only GitHub check and contract tests tying live label definitions to the issue form and funnel reporter.
- Verified the current public intake contract at 7 of 7 matching labels with zero pilot requests; no lead or revenue was inferred.
- Added a 14-day owner-visible GitHub traffic baseline with aggregate views, clones, daily series, top referrers, and popular paths.
- Reconciled 1 unique viewer, 119 unique cloners, and 310 clone events while explicitly refusing to treat the automation-heavy clone signal as users.
- Added traffic baseline tests for capture timestamps, window boundaries, daily totals, uniqueness bounds, and top-traffic reconciliation.
- Added generated schema-2 distribution, schema-6 pilot, and joined growth baselines from public evidence captured on 2026-07-12.
- Recorded 34 contract-complete releases, 61 cumulative primary artifact requests, zero pilot requests, and $0 booked revenue without treating CI-confounded requests as users.
- Added baseline contract tests that reconcile per-release channels and preserve the acquisition bottleneck and zero-revenue state.
- Documented baseline provenance, privacy review, refresh cadence, and interpretation boundaries under `metrics/`.
- Added a preflighted maintainer command that updates both policy workflows and their CI contract to one verified release identity.
- Rejected invalid version, source-commit, and wheel-digest shapes before reading or writing pin targets.
- Refused missing or duplicate pin locations before changing any target, preventing layout drift from producing a knowingly mixed upgrade.
- Independently verified and pinned the `v0.3.30` wheel, source commit `65e1063e5a9c0e85a0f8f30523335eb0c0ce847e`, and SHA-256 `b7001e9fd38359a33f9be1a38961765ba5c37f22d56374b89ec9a9a62f934891` in both CI gates.
- Kept version `0.3.30`, acquisition, and revenue evidence unchanged; no redundant release or prospect activity was claimed.

## 0.3.30 - 2026-07-12

- Added a `drafted` private-ledger status for personalized outreach messages awaiting human review.
- Required every drafted prospect to use a permitted warm-introduction or published-business channel while forbidding contact and follow-up dates.
- Released schema-2 outreach reports with a separate draft count that remains excluded from attempted-prospect totals.
- Updated the playbook and contract tests to prevent draft preparation from being reported as sent outreach.
- Independently verified and pinned the `v0.3.29` wheel, source commit `ac710bb9833d6d1f2d46c7e65d0a16545ad43017`, and SHA-256 `0da9f82d85b41d6c1419c8f8ad190f1b3b040c5dd173a7fa5a66b23f6c855c82` in both CI gates.
- Recorded that no authoritative prospect source was available, so no private ledger, drafts, contact attempts, leads, or revenue were claimed.

## 0.3.29 - 2026-07-12

- Added `repo-scout-policy verify-receipt` to compare archived bootstrap evidence with the current policy.
- Emitted stable text and JSON pass or drift reports with expected and actual policy versions and fingerprints.
- Returned exit code 6 for missing, invalid, or changed policies while reserving exit code 2 for malformed receipt evidence.
- Added policy-path overrides for moved policies and strict duplicate-key, schema, shape, type, and unknown-field receipt validation.
- Extended installed-wheel release smoke coverage to verify every clear bootstrap receipt against its generated policy.
- Independently verified and pinned the `v0.3.28` wheel, source commit `7d3b9a0ba09b3f2a965a1ff795e94265a830f8aa`, and SHA-256 `f93297de4f2df1b62451169292b8a3d237d50f9ef9b040bbc77083d09b7a0e92` in both CI gates.
- Kept acquisition and revenue totals unchanged; no prospect outreach was attempted.

## 0.3.28 - 2026-07-12

- Added stable schema-1 JSON receipts for successful `repo-scout-policy bootstrap` runs.
- Recorded create or replace status, resolved output path, selected starter and reason, policy version, and normalized policy fingerprint.
- Kept JSON stdout clean for automation and emitted no success receipt for review, overwrite, or write failures.
- Extended release-blocking installed-wheel smoke coverage to verify bootstrap receipts across every clear recommendation route.
- Independently verified and pinned the `v0.3.27` wheel, source commit `53dc08b01141373b92e92b4b019c73800e961a4f`, and SHA-256 `8789202cae67ca91b9f410075f65f7a8c937f3fdecf1636700b3b1b48488c820` in both CI gates.
- Kept acquisition and revenue totals unchanged; no prospect outreach was attempted.

## 0.3.27 - 2026-07-11

- Added `repo-scout-policy bootstrap` to recommend and write a starter policy in one command for clear repositories.
- Kept bootstrap outputs inside the inspected repository by default and rejected relative custom paths that escape it.
- Reused existing overwrite protection, explicit `--force`, atomic replacement, and no-parent-creation behavior.
- Refused to write an automatic policy for mixed Node/Python repositories that require combined rule review.
- Extended installed-wheel release smoke coverage to prove bootstrap writes every clear recommendation and refuses the polyglot route.
- Independently verified and pinned the `v0.3.26` wheel, source commit `592348a8f9a75a4ea2f3dee8c231afc407a106d6`, and SHA-256 `c1774978ae1f03303e36674c87ff70a4b455f7962218b48c6f1cb227517d2f4d` in both CI gates.
- Kept acquisition and revenue totals unchanged; no prospect outreach was attempted.

## 0.3.26 - 2026-07-11

- Independently verified the `v0.3.25` wheel against its manifest, source commit, tag, signer workflow, provenance, and GitHub-hosted runner.
- Installed that wheel without dependencies and proved all seven policy activation routes from the published package.
- Expanded release smoke coverage to Python, agent-ready, baseline, and mixed Node/Python recommendation behavior.
- Retained full npm, pnpm, and Yarn recommendation plus Node policy pass/fail enforcement in the generalized activation smoke.
- Renamed the smoke harness to reflect its complete policy-activation scope.
- Pinned `v0.3.25`, source commit `e16b68f9ddf6a4ef81ab0e4b136c00e5819f5b82`, and wheel SHA-256 `bd939082cf63bdd9b3f78537e78b1f2a1e018e619a17842f9187aff4cba08a9a` in both CI gates.
- Kept acquisition and revenue totals unchanged; no prospect outreach was attempted.

## 0.3.25 - 2026-07-11

- Added `repo-scout-policy recommend` to select the closest packaged starter from local repository signals.
- Recommended npm-only policy only for a sole npm lockfile and the flexible Node policy for pnpm, Yarn, missing, or multiple Node lockfiles.
- Detected Python and agent-ready repositories while retaining the conservative service baseline fallback.
- Marked mixed Node and Python repositories for explicit review instead of presenting one starter as complete policy.
- Added stable text and JSON recommendation output with copy-ready initialization commands.
- Extended installed-wheel release smoke testing to verify npm, pnpm, and Yarn recommendation behavior before publication.
- Independently verified and pinned the `v0.3.24` wheel, source commit `1feb1737ed8b3476bf5447881c67ab9d85cefaa1`, and SHA-256 `05b000f451c3a99f6ac6916ec186359bab5b5381b15a88c9e92ce9c574f188df` in both CI gates.
- Kept acquisition and revenue totals unchanged; no prospect outreach was attempted.

## 0.3.24 - 2026-07-11

- Independently verified the `v0.3.23` wheel against its manifest, source commit, tag, signer workflow, provenance, and GitHub-hosted runner.
- Installed that wheel without dependencies and proved `node-service` pass/fail behavior in clean npm, pnpm, and Yarn repositories.
- Added a reusable dependency-free smoke script for installed Node starter verification.
- Required every future wheel release to initialize the packaged starter, accept each supported lockfile, and reject no lockfile before publication.
- Pinned `v0.3.23`, source commit `1375911f47a4a91f822314250771f8dd198c886c`, and wheel SHA-256 `ddd75b6662dcec53989c5db382cc596ba8f2cd9b741a7ff120f00012044fab7c` in both CI gates.
- Added source-level smoke-script and release-workflow contract coverage.
- Kept acquisition and revenue totals unchanged; no prospect outreach was attempted.

## 0.3.23 - 2026-07-11

- Independently verified the `v0.3.22` wheel against its release manifest, source commit, tag, signer workflow, provenance, and GitHub-hosted runner.
- Pinned `v0.3.22`, source commit `4ad97481a7f7d2d444cddc6fc77126503b4697d6`, and wheel SHA-256 `c79fa0ce2c5e706aae9356cdad124aee1f5771e1ecd41f82f9fba7a26011a556` in both CI gates.
- Added a packaged `node-service` policy that requires `package.json` plus one npm, pnpm, or Yarn lockfile.
- Preserved the existing `node-npm-service` profile for teams that explicitly standardize on npm.
- Exposed required alternatives in the human policy catalog and normalized rules in its JSON output.
- Added all-three-package-manager, missing-lockfile, catalog, initialization, package-resource, and portable-build coverage.
- Removed the temporary v4 policy example after promoting its behavior into the packaged starter catalog.
- Kept acquisition and revenue totals unchanged; no prospect outreach was attempted.

## 0.3.22 - 2026-07-11

- Added backward-compatible policy schema v4 with `repository.required_file_groups` while retaining v1-v3 reads.
- Required at least one existing path from every configured group, with one stable violation per unsatisfied group.
- Rejected empty or duplicate groups and candidates contradicted by exact requirements, exact forbids, or forbidden patterns.
- Normalized group and member ordering in cross-repository policy fingerprints.
- Added a staged mixed-package-manager policy that accepts npm, pnpm, or Yarn lockfiles without making lockfiles optional.
- Added policy, CLI, example, compatibility, validation, and fingerprint coverage for the new contract.
- Kept verified policy gates and packaged starters on v3 until the v4 release artifact can be independently pinned.
- Kept acquisition and revenue totals unchanged; no prospect outreach was attempted.

## 0.3.21 - 2026-07-11

- Upgraded dogfood and copy-ready policy gates to the independently verified `v0.3.20` wheel.
- Pinned source commit `a64d1ace85fea21797baf9d1cf2c4dda07e0d404` and wheel SHA-256 `d659d6f5a0695c4cb7380e797e7cf6c974ce11d188a96ad1899f3ad4d36a0767` in both workflows.
- Moved every packaged starter, the dogfood policy, and the copy-ready CI policy to schema v3.
- Added tracked-or-unignored `**/.env` and `**/.env.local` protection for nested service folders.
- Proved the released wheel fails a force-tracked nested environment file while preserving remediation-required rollout evidence.
- Kept broad `*.pem` matching out of defaults because legitimate public certificates and fixtures may use that suffix.
- Removed the temporary v3 example now that verified policy gates consume v3 directly.
- Kept acquisition and revenue totals unchanged; no prospect outreach was attempted.

## 0.3.20 - 2026-07-11

- Added backward-compatible policy schema v3 with `repository.forbidden_file_patterns` while retaining v1 and v2 reads.
- Matched basename patterns such as `*.pem` at any repository depth and path patterns such as `**/.env` across nested services.
- Applied patterns to all tracked or unignored Git files, or all non-Git files, independently of the snapshot path-detail cap.
- Bounded each pattern violation to 20 sorted path details while retaining the full match count and explicit truncation state.
- Rejected missing wildcards, malformed or duplicate patterns, required-file conflicts, and redundant exact-forbidden overlaps before scanning.
- Included normalized pattern ordering in stable cross-repository policy fingerprints.
- Added a staged v3 monorepo policy example and focused matching, ignore, force-track, scale, bound, validation, compatibility, and fingerprint tests.
- Kept verified policy gates and packaged starters on v2 until a v3-capable release can be independently pinned.
- Kept acquisition and revenue totals unchanged; no prospect outreach was attempted.

## 0.3.19 - 2026-07-11

- Upgraded dogfood and copy-ready policy gates from the verified `v0.3.1` wheel to the independently verified `v0.3.18` wheel.
- Pinned source commit `ae1b746e1fab81bf6536368666017f7a3dfbdde3` and wheel SHA-256 `6518ac0f1829b81cbae061764c053796e7646a3482bfd76d5cbb6737cab2a63f` in both workflows.
- Moved all four packaged starter profiles, the dogfood team policy, and the copy-ready CI policy to schema v2.
- Added tracked-or-unignored `.env` and `.env.local` protection to every v2 starter and example.
- Added an end-to-end copy-ready policy test that preserves rollout evidence when a tracked forbidden file fails CI.
- Removed the temporary separate v2 example now that the verified CI gates consume v2 directly.
- Kept acquisition and revenue totals unchanged; no prospect outreach was attempted.

## 0.3.18 - 2026-07-11

- Added backward-compatible policy schema v2 with strict `repository.forbidden_files` rules for exact normalized repository-relative paths while retaining v1 reads.
- Reported one stable policy violation per tracked or unignored forbidden file while leaving properly ignored local files alone in Git repositories.
- Rejected duplicate, escaping, absolute, backslash, empty, and required-plus-forbidden path contradictions before scanning.
- Included sorted forbidden-file semantics in stable cross-repository policy fingerprints.
- Added `.env` and `.env.local` protection to the manual team-policy example; pinned v1 starter and CI files remain unchanged until v0.3.18 can be verified immutably.
- Added focused policy, fingerprint, compatibility, CLI, and example tests for violations, ignored-local behavior, force-tracked files, invalid paths, and contradictory rules.
- Preserved the acquisition freeze and recorded that no prospect outreach or revenue evidence exists yet.

## 0.3.17 - 2026-07-11

- Added `repo-scout-outreach` for dependency-free validation and aggregate reporting of the private direct-outreach ledger.
- Required alias-only `prospect-NNN` records, at least three closed fit signals, and warm-introduction or published-business channels.
- Enforced the 10-prospect experiment cap, a follow-up scheduled exactly seven days after initial contact, no early recorded follow-up, and no next action after follow-up, reply, pilot request, rejection, or opt-out.
- Added deterministic due-follow-up aliases and aggregate status totals without exposing recipient details.
- Kept outreach replies and ledger pilot requests explicitly outside public lead, payment, and revenue evidence.
- Added release smoke coverage and focused tests for valid activity, empty-ledger startup, qualification, privacy, cadence, stop states, batch limits, CLI JSON, and malformed headers.

## 0.3.16 - 2026-07-11

- Added a copy-ready direct-outreach playbook for the first 10 qualified engineering-lead prospects.
- Fixed the message contract at $299 for 90 days, up to 10 projects, local source handling, and the direct-outreach campaign route.
- Limited contact to one personalized initial message and one seven-day follow-up, with immediate opt-out handling.
- Prohibited scraped personal addresses and sales messages in GitHub issues, pull requests, or security channels.
- Added a header-only outreach ledger template and ignored its private working directory to prevent prospect-data commits.
- Added tests for offer accuracy, source preservation, cadence, anti-spam language, privacy boundaries, and an empty ledger baseline.
- Kept replies and operator activity outside demand and booked-revenue totals until public intake and funnel labels exist.

## 0.3.15 - 2026-07-11

- Added JSON-LD that represents the current free CLI as a `SoftwareApplication` with an exact $0 versioned download.
- Represented the founding-team pilot separately as a $299 `Service` with its visible 90-day and up-to-10-project scope.
- Centralized the public release version and portable URL across visible onboarding and machine-readable metadata.
- Excluded unearned ratings, reviews, hidden urgency, and campaign URLs from structured offers.
- Added parse-level contracts for schema types, versions, prices, currencies, availability, URLs, and pilot claims.
- Clarified that structured data can aid search understanding but does not guarantee traffic, demand, rich results, or revenue.

## 0.3.14 - 2026-07-10

- Added one production canonical URL for organic and campaign-query versions of the hosted offer.
- Added deterministic `robots.txt` and `sitemap.xml` routes that expose only the canonical page.
- Added canonical Open Graph URL and explicit index/follow metadata while retaining host-derived social images.
- Recorded the zero-pilot-request baseline and separated the lone recent wheel request from prospect evidence.
- Added production-render contracts for canonical metadata, crawler directives, sitemap content, and campaign-query exclusion.
- Clarified that crawler access and release requests are not search visits, demand, or revenue.

## 0.3.13 - 2026-07-10

- Added a "Share with your engineering lead" action beside the hosted $299 pilot offer.
- Prefilled a concise referral email with the disclosed price, up-to-10-project scope, and local-code boundary.
- Linked recipients through the source-preserving referral campaign route.
- Kept sharing user-initiated through the visitor's email client with no account, automatic send, address collection, or click tracking.
- Added rendered contracts for the visible referral action, encoded email content, and single mail link.
- Clarified that a referral becomes demand or revenue evidence only after independent intake and funnel progression.

## 0.3.12 - 2026-07-10

- Added server-rendered campaign routes for website, GitHub, direct outreach, referral, search, social/community, and other discovery sources.
- Preserved each supported campaign source through both hosted $299 pilot application buttons.
- Defaulted missing and unsupported campaign values to the website source instead of reflecting arbitrary query text into intake.
- Routed the README's hosted offer link through the GitHub campaign while retaining its direct GitHub-prefilled application path.
- Documented copy-ready hosted URLs for each acquisition context and required operators to share only the matching route.
- Added rendered coverage for every accepted campaign, both CTA destinations, and unknown-source fallback.

## 0.3.11 - 2026-07-10

- Added an above-fold README path that explains the paid team outcome and disclosed $299 pilot before the long CLI reference.
- Linked GitHub visitors into the live "Why teams buy" experiment and direct pilot intake.
- Prefilled the visible website discovery source on both hosted application buttons.
- Prefilled the visible GitHub repository or release source on README and repository-documentation application links.
- Added release and rendered-page contracts for the channel-specific links and exact intake option.
- Documented that prefills reduce form work but remain buyer-editable self-report rather than causal attribution.

## 0.3.10 - 2026-07-10

- Added a plain-language "Why teams buy" section that directly addresses AI recreation of the free scanner.
- Separated three paid operational outcomes from the free scan: a repeatable rulebook, one rollout across 10 projects, and evidence plus support when a project fails.
- Added a direct application path from that objection to the disclosed $299 founding-team pilot.
- Defined a source-identifiable website experiment with a hypothesis, funnel-based outcomes, guardrails, and a 2026-07-24 review point.
- Added rendered-page coverage for the objection, differentiators, and price-specific pilot path.

## 0.3.9 - 2026-07-10

- Upgraded weekly growth reviews to schema 2 with purchase-criterion outcome reporting.
- Added ordered schema-6 criterion rows for requests, qualification, offers, booked pilots, booked revenue, conversions, and losses.
- Kept schema-5 pilot reports readable with criterion evidence explicitly unavailable instead of zero.
- Required the exact schema-6 criterion taxonomy and reconciled every criterion aggregate to source totals.
- Added missing and unknown criterion evidence warnings without changing bottleneck or sales-priority semantics.
- Clarified that self-reported criteria are not attribution, willingness to pay, or proof of a moat.
- Added schema compatibility, ordering, malformed taxonomy, stage, revenue, summary, warning, and text-output coverage.

## 0.3.8 - 2026-07-10

- Added a required primary purchase criterion to the public founding-team pilot intake.
- Added a closed taxonomy for policy, rollout, evidence, privacy, implementation, commercial, and other purchase criteria.
- Upgraded pilot reporting to schema 6 with per-criterion qualification, offer, payment, conversion, and loss totals.
- Added normalized criteria to deal, stale-follow-up, and sales-queue records while preserving original answers on deals.
- Added explicit missing, unknown, and ambiguous criterion warnings without changing readiness-based sales priority or booked-revenue semantics.
- Kept `repo-scout-growth` compatible with both schema-5 and schema-6 pilot reports.
- Added form-contract, taxonomy, compatibility, malformed-answer, aggregate, and text-output coverage.

## 0.3.7 - 2026-07-10

- Added `repo-scout-growth` for dependency-free weekly review of distribution and paid-pilot evidence.
- Joined schema-2 signed release-request movement to schema-5 source, qualification, offer, payment, revenue, and conversion totals.
- Added deterministic bottlenecks and one commercial next action for measurement, acquisition, qualification, offer, payment, pilot-target, retention, and validated states.
- Surfaced release-contract, funnel-quality, missing-source, and ambiguous-source warnings in the combined review.
- Rejected unsupported schemas, inconsistent source totals, impossible cumulative stages, and mismatched revenue evidence.
- Explicitly prohibited download-to-lead conversion rates and per-source assignment from non-unique GitHub artifact requests.
- Added public-data dogfooding, seven focused growth-review tests, installed-command release smoke coverage, and a documented weekly operator workflow.

## 0.3.6 - 2026-07-10

- Added `--baseline REPORT` for signed weekly release-request comparisons.
- Added schema-2 change records for portable, wheel, source, manifest, unknown, and combined primary artifact deltas.
- Reported new and removed stable releases independently from download movement.
- Accepted schema-1 and schema-2 distribution reports as baselines.
- Warned when cumulative counters decrease or baseline releases and assets disappear.
- Kept no-baseline output explicit and preserved GitHub request-count caveats in every report.
- Added real public-data dogfooding and comprehensive baseline, compatibility, CLI, reset, removal, and validation coverage.

## 0.3.5 - 2026-07-10

- Added `repo-scout-distribution` for dependency-free reporting from exported GitHub release JSON.
- Added version-aware artifact contracts that require portable zipapps from `v0.3.4` while preserving valid earlier releases.
- Separated portable and wheel primary requests from source, manifest, and unknown artifact requests.
- Added stable text and schema-1 JSON output with latest-release details, channel totals, portable share, and contract warnings.
- Rejected malformed releases, duplicate tags or assets, invalid counts, and non-semantic stable tags.
- Explicitly documented CI, maintainer verification, retries, and GitHub's non-unique request semantics so distribution signals cannot be reported as installs or revenue.
- Added release smoke coverage for the fifth installed command and comprehensive reporter contract, drift, CLI, and validation tests.

## 0.3.4 - 2026-07-10

- Added a single-file `repo-scout-X.Y.Z.pyz` for checkout-free, no-install CLI adoption.
- Added release-time zipapp building, source filtering, direct execution smoke tests, checksums, provenance attestations, and immutable publication.
- Moved the README and hosted companion quick starts from source checkout commands to the portable release.
- Added direct portable and wheel install paths plus complete artifact verification guidance.
- Added public package URLs, distribution channel contracts, reach metrics, and the PyPI naming constraint.
- Expanded release, archive-content, functional zipapp, metadata, and rendered-site coverage.

## 0.3.3 - 2026-07-10

- Replaced the hosted single-repository policy mockup with cross-repository rollout proof for policy-fingerprint and scanned-commit coverage.
- Showed both ready and remediation-required repository outcomes so the paid rollout workflow demonstrates operational value without implying every check passes.
- Added the aggregate `repo-scout-rollout` command, bundle-reported freshness caveat, and an explicit $299 application CTA to the founding-team offer.
- Expanded production-render coverage for the new rollout evidence and conversion copy.
- Added a deterministic sales queue for every open pre-payment pilot deal.
- Prioritized disclosed ready, approval-dependent, exploratory, and unclear intent without counting any of it as revenue.
- Added stage-specific next actions with stable stage, activity-age, and issue-number ordering.
- Kept stale follow-up as a separate inactivity signal and excluded closed, paid, lost, and converted deals from sales actions.
- Documented the schema-5 queue contract and expanded funnel, text-output, and release-version coverage.

## 0.3.2 - 2026-07-10

- Upgraded copy-ready and dogfood policy workflows to the independently pinned and attested `v0.3.1` release.
- Generated schema-2 rollout evidence in CI with GitHub's stable `owner/repository` identity.
- Preserved passing and remediation bundles in job summaries and 14-day `repo-scout-rollout-evidence` artifacts.
- Added workflow contract and execution coverage for fingerprints, exact scanned commits, readiness, and policy-failure evidence.
- Documented artifact access, pull-request merge commits, local aggregation, and the no-hosted-service pilot workflow.
- Added a required public purchase-readiness answer for ready, approval-dependent, and exploratory pilot requests.
- Added schema-4 readiness totals by funnel stage, booked revenue, annual conversion, and loss.
- Added normalized readiness and original answers to deal records and readiness context to stale follow-up records.
- Added explicit warnings and buckets for legacy, edited, unknown, and duplicate readiness answers.
- Kept self-reported purchase intent separate from booked revenue, which still requires `pilot-paid` or a later paid stage.

## 0.3.1 - 2026-07-10

- Added deterministic SHA-256 fingerprints for normalized team-policy semantics.
- Recorded the exact checked-out Git commit in repository scans and schema-2 rollout evidence.
- Kept schema-1 rollout bundles readable with explicit zero identity coverage for missing fields.
- Verified shared policy only when at least two bundles have complete matching fingerprints.
- Added counts-only policy-fingerprint and Git-commit coverage without exposing identity values by default.
- Included fingerprints and commits in explicit `--details` output while preserving freshness and authenticity caveats.
- Required an identifiable initial commit before schema-2 evidence can report CI readiness.
- Revalidated evidence passed directly to the aggregate library API before counting it.
- Added semantic-ordering, committed/unborn Git, schema compatibility, invalid identity, privacy, and aggregate verification tests.

## 0.3.0 - 2026-07-10

- Added schema-1 rollout metadata to first-repository Markdown evidence bundles.
- Required explicit, strictly validated logical repository IDs for aggregatable evidence.
- Added the dependency-free `repo-scout-rollout` command for deterministic multi-repository text and JSON summaries.
- Added aggregate readiness, policy, violation, Git cleanliness, and attention counts with stable repository ordering.
- Rejected duplicate repository IDs, missing or malformed metadata, unknown fields, unsupported schemas, invalid types, and contradictory evidence.
- Made aggregate output counts-only by default with explicit `--details` repository disclosure.
- Rejected duplicate JSON keys, boolean schema versions, and impossible non-Git dirty-file claims.
- Labeled aggregate readiness as bundle-reported without claiming freshness or shared-policy equivalence.
- Added release smoke coverage for the fourth installed command and comprehensive metadata, aggregation, order, and CLI tests.
- Documented local multi-repository operation, metadata privacy, and the distinction between consistency checks and provenance.

## 0.2.9 - 2026-07-10

- Replaced the customer CI example's pinned source checkout with the published `v0.2.8` wheel.
- Added independent wheel-digest and release-manifest verification before installation.
- Added provenance checks for the exact source commit, version tag, signer workflow, and GitHub-hosted runner.
- Granted only read access to repository contents and artifact attestations.
- Installed Repo Scout without dependencies in a runner-temp virtual environment so the protected checkout remains unchanged.
- Applied the same verified-release bootstrap to Repo Scout's dogfood policy workflow.
- Expanded CI contract tests to forbid source-checkout and `PYTHONPATH` regressions and require every integrity control.
- Documented failure behavior and the atomic three-value release-pin upgrade process.
- Added `--rollout-checklist` for deterministic first-repository onboarding evidence in Markdown policy reports.
- Added automated policy, Git, worktree, and attention readiness checks without pre-checking human actions.
- Preserved rollout evidence before policy exit code 6 and rejected misleading non-policy, non-Markdown, and comparison combinations.
- Added passing, remediation, output, and misuse coverage plus pilot rollout and evidence-privacy documentation.

## 0.2.8 - 2026-07-10

- Added a required discovery-channel field to the founding-team pilot request form.
- Added stable source keys for GitHub, website, outreach, referral, search, social, other, unattributed, and unknown leads.
- Added per-source qualification, offer, booked-pilot, booked-revenue, conversion, and loss totals to funnel JSON schema 3.
- Added normalized source data to deal and stale follow-up records and source summaries to text reports.
- Added warnings for missing, unknown, and duplicate issue-form source answers without guessing attribution.
- Added deterministic fixtures and coverage for source revenue, legacy issues, edited answers, duplicate headings, and malformed bodies.
- Documented self-reported attribution limits and updated the GitHub export contract to include issue bodies.

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
