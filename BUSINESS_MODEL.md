# Business Model

## Revenue Goal

Repo Scout will become a paid local and CI policy tool for small software teams
that use coding agents heavily and need consistent repository handoffs and
guardrails without sending source code to a hosted service.

The immediate target is three paid founding-team pilots, producing $897 in
initial revenue before licensing or billing infrastructure is built.

## Ideal Customer

- Software teams with 5 to 50 developers.
- Teams using coding agents across multiple repositories.
- Engineering leads who own review quality, repository standards, or handoffs.
- Security-conscious teams that prefer local tooling over source-code uploads.

## Market Positioning

A qualitative review completed on 2026-08-01 places Repo Scout beside four
established categories rather than above them. Semgrep and SonarQube analyze
source code, Trunk orchestrates code-quality tools, Conftest and Open Policy
Agent provide a broad build-it-yourself policy engine, and GitHub rulesets
govern activity in GitHub's control plane. Repo Scout does not replace those
products or claim better vulnerability, lint, or hosting enforcement.

The narrow paid wedge is one repository-operating baseline, normalized policy
identity reported by each submitted rollout bundle, and hands-on adoption
across up to 10 projects. Internal scripts and Conftest are credible
substitutes; the pilot earns its price only when its fixed scope, evidence
contract, and remediation help cost less than building and supporting the same
workflow internally. The dated category map, official sources, buyer fit,
objection answers, and claims to avoid are recorded in
[`docs/competitive-positioning.md`](docs/competitive-positioning.md).

This is positioning evidence, not demand evidence or a moat. Billing and
license enforcement remain deferred until a team pays for the pilot.

## Offer

### Free Core

- Local repository snapshots in text, JSON, and Markdown.
- Attention findings and CI-friendly exit codes.
- Saved snapshot comparison and bounded changed-path details.
- A copy-ready, read-only GitHub Actions policy gate with failure evidence.
- Offline starter policies for baseline, Python, flexible Node, npm-only, and agent-ready services.
- Exact required and forbidden file rules with stable policy fingerprints.
- A no-install, single-file zipapp for the primary CLI.
- Versioned GitHub release artifacts with checksums and verifiable build provenance.

The free CLI should be good enough to adopt without a sales conversation.

Verified GitHub releases remove source-checkout trust and installation friction
from pilot onboarding. PyPI distribution, billing, and license enforcement stay
deferred until paid demand justifies their operational cost.
The website, README, and release guide now keep each portable download and its
Python invocation in one shell AND-list. A failed transfer therefore preserves
the download error and cannot execute an older `/tmp/repo-scout.pyz` left by a
previous evaluation. Exact-snippet shell tests enforce that buyer-facing
activation boundary. This removes a false-success path; it does not establish
an install, customer use, pilot demand, payment, or revenue.
The hash-locked release builder now pins the advisory-fixed `setuptools`
`83.0.0` wheel and its exact PyPI SHA-256 digest before producing either public
wheel or source artifacts. The executable lock contract binds every release
package/version pair to its specific hash, and clean-environment evidence
rebuilds the wheel, source archive, portable CLI, and checksum manifest without
isolation. This protects the paid-CI trust path; updating build infrastructure
does not publish a release or establish an install, demand, payment, or revenue.
Release preparation now refuses to write `SHA256SUMS` through a symlink or
other non-regular path. It preserves the mode of an existing regular manifest
and publishes new checksum bytes through a flushed, synced, same-directory
staging file and atomic replacement, so a replacement failure leaves the
previous manifest intact. This protects the release evidence consumed by paid
CI without creating a release, install, demand, payment, or revenue event.
A separate read-only pre-tag workflow now runs the exact release contracts,
force-verifies the hash-locked tools in a fresh environment, checks dependency
compatibility, and builds candidate wheel, source, portable, and checksum
artifacts on Python 3.11 whenever release inputs change. Candidate artifacts
remain in runner temp, but the exact wheel is installed into a separate smoke
environment with package indexes, dependency resolution, and pip's remote
version check disabled. All seven packaged command versions are reconciled,
then the installed wheel runs the same policy-activation, guarded-outreach,
pilot-funnel, and rollout-summary acceptance journeys required during
publication. The zipapp also performs a real repository scan. An executable
parity contract keeps those four ordered scripts aligned as paid workflows
evolve. Nothing is uploaded or attested. This moves build, packaging, and
commercial-workflow failures before tag creation while leaving the tag-only
publication and immutable-release boundary unchanged.
Both release boundaries also rebuild the exact generated source archive into a
wheel with the same hash-locked interpreter, no package indexes or wheel cache,
no dependency resolution, and no isolated replacement toolchain. A structured
wheel comparison rejects duplicate entries and requires the rebuilt artifact
to match every direct-wheel path, byte, and stored mode; archive timestamps,
ordering, and compression are intentionally non-semantic. This proves the
attested source artifact can reproduce the already smoke-tested installable
contents without counting the rebuild as an install, demand, payment, or
revenue event.
The tag-only publisher now repeats that isolation at the release boundary. It
creates a new runner-temp environment, force-verifies every locked wheel, checks
dependency compatibility, and uses only that interpreter to build and validate
the portable CLI, wheel, source archive, and checksum manifest. Ambient
hosted-runner build packages can no longer satisfy the lock without a verified
reinstall or remain visible to the package backend. This strengthens paid-CI
artifact trust without creating a release, install, demand, payment, or revenue
event. Its separate publication smoke environment also installs only the
canonical wheel derived from the validated tag, with package indexes,
dependency resolution, and the remote version check disabled.
After the wheel and portable smoke tests read the built artifacts, the
publisher now revalidates every manifest entry immediately before passing that
same `SHA256SUMS` file to provenance attestation. An executable contract proves
that intact artifacts pass and any post-manifest byte mutation fails closed.
This protects paid-CI distribution evidence without creating a release,
customer install, demand, payment, or revenue event.
The final GitHub Release command now names the tag-derived wheel, source
archive, and portable CLI paths explicitly alongside `SHA256SUMS`. Shell globs
cannot add a later matching file outside the exact artifact set already
validated, smoke-tested, checksummed, and attested. This narrows publication
authority without creating a release, install, demand, payment, or revenue
event.
The public verification guide reconciles its downloaded-file, checksum, and
provenance-command counts to the three artifacts defined by the release builder.
It also resolves the annotated tag's exact source commit and constrains every
attestation to that repository, semantic tag, commit, release workflow, and a
GitHub-hosted runner. Executable documentation tests require all five identity
constraints for every artifact. This keeps the buyer-facing trust procedure
aligned with paid CI without proving activation, demand, payment, or revenue.
Repository-level release immutability is enabled. After publishing, the release
job queries the exact semantic tag through the versioned GitHub API and fails
unless its release object reports `immutable: true`. Version `0.3.51` is the
first release boundary required to pass that lock. After a separate public-
artifact reconciliation, both paid-CI gates now pin its exact source commit and
wheel digest alongside the manifest, tag, signer workflow, hosted runner, and
provenance constraints.
Before any release work begins, the publishing workflow also requires the
semantic ref to be an annotated Git tag whose peeled commit exactly matches the
GitHub push commit. Lightweight tags and annotated tags aimed at another commit
stop before main-branch ancestry, tests, builds, attestations, or publication.
This keeps the public peel-and-verify procedure available to paid-CI operators;
it does not create a release, install, demand, payment, or revenue event.
The wheel adoption path now reports all 7 packaged commands, and its release
test derives complete version-smoke coverage from `[project.scripts]` instead
of a second hardcoded command list. This keeps the paid CI activation surface
truthful as entry points change; it does not prove customer usage or revenue.

The copy-ready CI gate consumes those releases with independent digest and
provenance checks. This makes the free activation path closer to the paid pilot
deployment model: teams can evaluate a repeatable, auditable install before
buying cross-repository rollout support.
After the verified GitHub download, both policy gates install only the local
wheel with package indexes, dependency resolution, and pip's remote version
check disabled. This closes an unnecessary mutable-registry path during paid-CI
activation without proving customer usage, demand, payment, or revenue.
Both policy gates retry release download and provenance verification up to four
times with bounded backoff. Download attempts remain isolated, and every
download attempt must produce and promote both the wheel and manifest before it
can break the loop. Every provenance attempt retains the pinned wheel, source,
tag, signer workflow, and hosted-runner requirements. This directly addresses
observed complete and partial GitHub REST failures without accepting incomplete
release pairs or weakening artifact identity; persistent failures still stop
before installation. It reduces false-negative activation friction but does
not prove customer usage, demand, payment, or revenue. The CI contract executes
both shell blocks with injected transient, partial-success, and terminal
failures, proving exact waits, trusted-file promotion, recovery, and explicit
terminal failure without calling GitHub.
Before either provenance loop begins, the manifest must contain exactly one
canonical entry binding the independently pinned digest to the expected wheel
filename. Missing, altered, and duplicate wheel entries stop activation before
an attestation request, closing the case where `sha256sum --ignore-missing`
accepts a manifest whose listed artifacts are all absent. Executable customer
and dogfood contracts cover each rejection without treating trust validation as
customer usage, demand, payment, or revenue.
Existing handoff and rollout reports are now replaced only after a complete
new report is staged, with the original access permissions carried into the
atomic swap. A failed swap leaves the prior evidence unchanged. This protects
the artifact a pilot operator may need for remediation or review; it does not
prove customer activation, demand, payment, or revenue.

### Founding Team Pilot

Price: $299 for 90 days, covering up to 10 repositories.

The pilot includes:

- A shared, version-controlled repository policy.
- CI enforcement guidance and rollout support.
- One custom policy pack for the team's repository standards.
- First-repository readiness evidence and a reusable rollout checklist.
- Direct feedback access and priority fixes during the pilot.

The paid value is consistency across repositories and teams, not access to the
basic local scanner.

Post-payment delivery uses one explicit acceptance contract. The operator keeps
the 90-day dates, customer owner, agreed standards, CI provider, and up to 10
stable repository IDs in a customer-approved private system. Acceptance
requires a reviewed custom policy pack, agreed CI integration, current
bundle for each scoped repository, counts-only rollout summary, and closeout
record. `pilot-paid`, `pilot-active`, and `pilot-converted` remain human-applied
business events; command output does not infer them. GitHub Actions is the only
copy-ready gate currently shipped, so any other CI provider requires an
explicit integration decision before payment.
Rollout aggregation now requires each customer bundle to remain a direct
regular-file leaf no larger than 1 MiB. Parsing stays on one descriptor and
acceptance requires the exact bytes and requested leaf to remain unchanged.
Symlinks, special files, replacement, mutation, and oversized sparse evidence
therefore fail before a cross-repository summary is emitted. This protects the
paid delivery acceptance record without treating a bundle as customer
activation, payment, demand, or revenue.
Controlled parser, validation, inspection, and loading failures preserve
ordinary printable evidence names but JSON-escape any control-bearing source
path and repeated operating-system context onto one line. Valid detailed JSON
still carries the exact path as structured data, while the privacy-default
summary still omits paths. Installed release smoke proves a malformed filename
cannot forge metrics or mutate evidence. This protects paid-delivery error
presentation without authenticating the file or creating activation, payment,
or revenue evidence.
Rollout repository IDs are limited to non-empty printable values of at most
128 characters without surrounding whitespace. The same validation runs before
the primary CLI generates a bundle and before the aggregator constructs a
summary. Line breaks, terminal controls, bidirectional controls, Unicode
separators, and oversized values fail without being echoed, so a
customer-controlled identity cannot use those controls to forge detailed text
metrics or alter terminal presentation. This protects the paid delivery record;
it does not authenticate a repository, establish customer activation, or
create payment or revenue.
Printable IDs can still contain Markdown backticks. Bundle generation now uses
a code-span fence longer than the longest embedded run and adds delimiter
padding only when an ID begins or ends with a backtick. The visible identity
cannot close its own code span, while schema-2 metadata retains the exact
logical ID. Installed release smoke runs the packaged `repo-scout` producer and
requires that containment before the packaged aggregator checks the synthetic
bundles. This is rendering integrity for paid acceptance evidence, not
authentication, freshness, customer activation, payment, or revenue.
Ambiguous rollout JSON already fails on duplicate keys before metadata
validation. The decoded duplicate key is now JSON-escaped in the controlled
error, so legal JSON escapes for newlines, C1 terminal controls, and
bidirectional controls cannot become extra operator lines. Installed release
smoke requires that one-line rejection, empty report output, and unchanged
evidence. This protects paid-delivery error integrity; it does not authenticate
a bundle, prove customer activation, payment, or revenue.
Closed rollout metadata rejects unknown top-level, policy, and Git fields.
Ordinary printable field names keep their existing diagnostic, while a decoded
control-bearing key is JSON-escaped before parser or direct-summary errors
reach an operator. Installed release smoke requires a one-line error, no
summary, and unchanged evidence. This protects paid-delivery diagnostics; it
does not authenticate a bundle, prove activation, payment, or revenue.
Rollout branch metadata is also limited to null or a non-empty printable value
of at most 1,024 characters without surrounding whitespace. Line breaks,
terminal controls, bidirectional controls, and oversized values fail before
counts-only or detailed output and are not echoed in the error. This prevents a
customer-controlled bundle from forging operator metrics or changing terminal
presentation; it does not establish customer activation, willingness to pay,
payment, or revenue.
Operators can start from a blank, copy-ready delivery record with exactly 10
repository slots, but the completed copy belongs only in the
customer-approved private system. The template records the CI decision, five
deliverable acceptances, first-repository acknowledgement, and closeout without
creating a public customer-data or payment record.
A short-lived local fallback uses the ignored `pilot-private/` directory with
owner-only `700/600` permissions and an explicit `git check-ignore` preflight.
Ignore rules are not encryption or access control, so durable evidence still
belongs in the customer-approved private system and completed records must
never be force-added.
The public revenue ledger crosses from `pilot-paid` to `pilot-active` only
after every activation condition in the paid delivery contract is satisfied,
including customer acknowledgement of the first-repository handoff in that
private delivery record. The public issue receives the cumulative label and a
non-sensitive status note, never the repository identity, access details, CI
evidence, payment details, or acknowledgement record.

Policy version 2 can reject tracked or unignored sensitive paths without
failing on properly ignored local copies. A founding-team custom pack can use
the team's agreed credential, generated-secret, and local-configuration paths.
This is useful free CI enforcement; the paid work remains agreeing on the
right rules and rolling the same reviewed policy across uneven repositories.
Versions 1 and 2 remain readable so verified CI upgrades can be staged safely.
The dogfood and copy-ready gates now install the independently verified
`v0.3.51` wheel, so v4 policies can run locally and in CI
without source checkout, mutable package resolution, or a team-managed secret.
Maintainer pin upgrades now preflight and update the dogfood workflow,
copy-ready customer example, buyer-facing README, commercial model and
project-state claims, and contract test as one reviewed change, reducing the
chance that distribution trust metadata diverges between internal and customer
activation paths. A mid-write failure now restores every already-replaced
target from staged originals instead of leaving internal and customer pins
split.
Every version-bearing target also rejects a numerically older release before
staging starts. Revalidating the current release remains supported, so a
maintainer can reconcile its source commit and wheel digest without weakening
the paid CI path to an older artifact.
The maintainer can run that complete validation through `--check` before the
transaction. Check mode reports every verified target but creates no staging
file and replaces no repository content, keeping review separate from commit.
Staging now stores normalized permission bits rather than raw filesystem mode
metadata. Regression coverage proves successful updates and rollback restores
retain each target's access mode, recovery copies keep the original mode, and
completed transactions leave no staged pin or rollback files behind. This
protects repeatable paid CI distribution maintenance; it does not demonstrate
customer activation, demand, payment, or revenue.
Cleanup failures now retain the transaction outcome: operators are told when
the verified pin was already committed, while failed writes still report their
rollback result and every retained temporary path. This avoids retry decisions
based on a masked filesystem error without creating customer or revenue
evidence.

Policy version 3 extends custom packs beyond exact root paths. A reviewed
pattern can protect nested service `.env` files or certificate-like filenames
across a monorepo, while ignored local files remain outside Git enforcement.
Pattern evidence is bounded to 20 sorted paths with a full match count so one
broad rule cannot flood CI summaries. Existing v1 and v2 policies remain
readable. General profiles protect nested `.env` files but omit broad `*.pem`
matching because public certificates may be legitimate; that decision belongs
in a reviewed paid custom pack.

Policy version 4 lets a reviewed custom pack express standards that have valid
alternatives. For example, one lockfile group can accept npm, pnpm, or Yarn
while still failing a repository with no lockfile. This makes one shared policy
credible across teams with uneven JavaScript tooling without weakening the
standard to the least common denominator. Existing v1-v3 policies remain
readable. The packaged `node-service` profile now uses this capability for
npm, pnpm, and Yarn, while the existing npm-only profile remains available for
teams that standardize on npm.

The published `v0.3.25` wheel has been exercised across every recommendation
route plus clean npm, pnpm, and Yarn policy enforcement. Every future release
repeats that installed-wheel smoke test before publication. This protects the
activation path customers actually use: discover a starter, initialize it from
the wheel, and receive stable pass or remediation evidence without depending
on a source checkout.

Starter recommendation shortens free-to-team activation without pretending a
local heuristic can design a paid policy. It maps clear manifests and lockfiles
to the closest packaged profile, emits stable JSON for automation, and marks
mixed Python and Node repositories for review. The paid pilot remains the work
of combining and operating standards across uneven repositories.

Guarded bootstrap removes another setup step for clear repositories by writing
the recommended starter with existing overwrite protection. It refuses mixed
Node and Python repositories, where automatic policy generation would conceal
the cross-project decisions that make the paid rollout valuable. Teams retain
separate recommendation and initialization commands when they need review.
Force replacement now carries an existing policy's permission bits onto the
fully written temporary file before the atomic swap. A permission failure keeps
the original policy and mode intact and removes the unused staging file. This
protects shared policy access during free and paid activation; it does not prove
customer usage, pilot demand, payment, or revenue.
Bootstrap and initialization now require the requested output leaf to be a
direct path rather than an initial or dangling symlink. Relative bootstrap
normalization resolves the parent while preserving the requested leaf for this
check. Rejection leaves the link and target untouched and emits no bootstrap
receipt, preventing first-repository handoff evidence from naming a former
symlink target.
Successful automation can now retain a versioned bootstrap receipt containing
the selected starter, destination, normalized policy version and fingerprint,
and whether the file was created or replaced. This gives a team auditable
handoff evidence without a hosted service; the paid value remains choosing and
operating one reviewed standard across repositories.
Receipt verification closes that local handoff loop by comparing the archived
version and fingerprint to the policy a team is about to commit or enforce.
It produces stable drift evidence and a CI failure without uploading either
file. This is useful free activation proof; paid value remains resolving drift
and operating one reviewed standard across repositories and teams.
Duplicate and unknown receipt keys already fail before policy comparison.
Their decoded names now preserve ordinary printable diagnostics but become
one-line JSON string literals when they contain presentation controls.
Installed activation smoke requires empty verification output and unchanged
evidence for both forms. This prevents malformed handoff evidence from forging
a successful match; it does not authenticate a receipt, establish policy use,
pilot demand, payment, or revenue.
The archived receipt argument must now name a direct regular-file leaf before
JSON is read. Receipt validation stays on one descriptor and accepts the
evidence only after the same requested leaf and exact bytes survive a final
check. Symlinks, special files, path replacement, and same-inode mutation fail
as command-input errors without a verification report, preventing untrusted
handoff evidence from redirecting or stalling first-repository activation.
Verification now preserves the receipt-recorded or explicitly overridden policy
leaf instead of resolving through it. An initial or dangling symlink fails with
the normal policy-mismatch exit, retains expected identity evidence, reports no
actual identity, and does not expose or change the referent. This keeps a
first-repository handoff from passing against a policy stored somewhere other
than the path under review; it does not prove customer use, pilot demand,
payment, or revenue.
The strict receipt loader also requires bootstrap `output` evidence to be an
absolute, valid file leaf and rejects relative or NUL-bearing values before an
override is considered. A forged receipt therefore cannot reinterpret its
original policy location against an operator's working directory, bypass a
malformed path through `--policy`, or crash CI while parsing evidence.
The selected policy leaf must also be a regular file before verification reads
it. Directories, FIFOs, sockets, devices, and other special files fail with
actual identity unavailable, preventing a crafted pipe from stalling a paid-CI
activation check while preserving the normal mismatch evidence contract.
Receipt verification now also binds parsing and fingerprinting to one opened
regular-file descriptor. The descriptor must match the initially inspected
leaf, and that requested leaf must still identify the same file after the
fingerprint is calculated. The exact opened bytes are reread at that acceptance
point as well. A symlink redirect, different regular-file replacement, or
same-inode mutation therefore cannot turn stale policy bytes into false
first-repository or paid-CI activation evidence. This strengthens the free
activation proof without establishing customer use, pilot demand, payment, or
revenue.

The primary `repo-scout --policy` path now applies the same file-evidence
boundary before any repository scan. It preserves the requested policy leaf,
requires a direct regular file, parses and validates one exact UTF-8 buffer
through a non-inheritable descriptor with no-follow and nonblocking flags where
available, then rereads the bytes and confirms the leaf still names that file at
the acceptance checkpoint. Static symlinks and special files return a
configuration error without a report, as do different-inode replacement and
same-inode mutation detected at that checkpoint. This protects the copy-ready
customer gate from redirection or blocking at the command teams actually run;
it does not establish an install, customer use, pilot demand, payment, or
revenue.
Primary policy files, bootstrap receipts, and receipt-selected policies are now
bounded to 128 KiB before parsing. The opened regular-file size rejects sparse
oversized inputs without reading them, while both descriptor reads stop after
the ceiling plus one byte so concurrent growth cannot force an unbounded first
read or acceptance reread. An oversized primary policy or receipt is a
configuration error without a report; an oversized receipt-selected policy
retains expected identity and returns the existing mismatch evidence with
actual identity unavailable. This is an activation-availability correction,
not another paid-policy feature or evidence of demand.

An AI can recreate a scanner, but that is not the commercial claim being
tested. The active website experiment now explicitly tells buyers to keep
their scanners and presents the paid outcome in plain language: help agreeing
on one repository-policy baseline, installing it across uneven projects, and
comparing the normalized policy fingerprint reported by each submitted bundle
without uploading source code to a hosted Repo Scout service. It links the
dated competitor-category review rather than claiming exclusivity. The
experiment succeeds only when the public intake records website-attributed
pilot demand; copy alone is not evidence of a moat or willingness to pay.

GitHub visitors now see the team outcome and disclosed price before the CLI
reference. They can either inspect the website objection section or apply
directly. Application links prefill the visible discovery-source answer for
the channel they came from, reducing form work without replacing self-report.
Hosted campaign routes preserve GitHub, outreach, referral, search, and social
context through the objection page. The server maps only the closed intake
taxonomy and defaults unknown values to website, so campaign sharing cannot
inject arbitrary source text into the form.

Visitors can open a prewritten referral email to an engineering lead from the
team-value section. The message discloses the $299 pilot, up-to-10-project
scope, and local-code boundary before linking through the referral campaign.
It uses the visitor's email client and creates no lead or revenue evidence
until a recipient independently submits intake and advances through the funnel.

The hosted offer now has one canonical search identity, a crawler policy, and a
one-page sitemap. Campaign query variants keep their source-specific intake
behavior for people while pointing search engines at the same production page.
This is acquisition infrastructure, not evidence of traffic or demand; only
self-reported intake and explicit `pilot-paid` payment evidence affect
commercial validation.

Machine-readable offer data keeps the free and paid layers distinct. The
current zipapp is represented as a $0 `SoftwareApplication`; the founding-team
pilot is a separate $299 `Service` with the same duration, repository limit,
audience, and local-code boundary shown to visitors. No review or rating data
is published because none has been earned. Search presentation remains outside
the revenue ledger until a buyer submits intake and the human-applied
`pilot-paid` label records received payment.
The maintainer production audit now fails when the deployed canonical metadata,
free software offer, release version, structured portable download URL, or
visitor-clickable portable download link drifts from the current project
version. It also requires the browser's final response URL to be the canonical
production page, preventing matching HTML reached on another host from
certifying the paid conversion path. This protects the existing buyer path
from sending a visitor to an obsolete artifact or unexpected destination; it
does not add a campaign, prove a visit, create demand, or record revenue.
The same check now runs daily in a read-only GitHub workflow and remains
manually dispatchable after deployment. Before requesting the live page, the
workflow runs its own permission and command-order contract plus the auditor's
behavior suite for stale releases, malformed free and paid offers, and missing
or incorrectly priced website-attributed pilot links. It receives no secrets
and changes no release, site, customer record, or commercial evidence.
The release handoff now requires lockfile installation, a tested production
build, a zero-vulnerability dependency audit, lint, a candidate receipt binding
the source commit, lockfile, hosted Node runtime, Sites project, and archive
digest, independent read-only verification before source-export approval,
explicit approval before pushing to the separate Sites source repository,
repeat verification before an exact-source save against the existing Sites
project, separate owner approval before public deployment, and an immediate
live audit afterward. The site lock advances Next to its `16.2.11` security
patch, current supported Cloudflare and Vite tooling, and advisory-fixed
PostCSS and Sharp releases without changing the offer. The lock now also pins
every resolved `fast-uri`, PostCSS, and Undici copy to `3.1.5`, `8.5.23`, and
`7.29.0`, respectively, closing the seven ranges GitHub reported on
2026-08-03. Sites version 46 is superseded; exact-source commit `4d0053f` was
saved as version 47, but newly published July 24 dependency advisories
supersede that undeployed candidate too. Production remains on `v0.3.50` until
a newly tested replacement is saved, explicitly approved, deployed, and
audited. A clean audit or saved version is not a visitor, customer activation,
demand, payment, or revenue event.
The repository now carries one exact `.nvmrc` selector for Node `22.13.0`.
Local candidate preparation strictly parses that pin before running commands,
uses it for the active-runtime gate and receipt, and the hosted dependency
contract reads the same file. Package metadata remains `>=22.13.0` so the free
site code keeps its tested compatibility floor without weakening the exact
paid-distribution handoff. This makes candidate evidence reproducible; it does
not authorize source export, save a Sites version, deploy production, or create
demand, payment, or revenue evidence.
Candidate validation now also limits every archive member to a canonical path
under `dist/` and permits only regular files or directories. A packaging helper
cannot silently carry unrelated repository source, credentials, links, devices,
or pipes across the source-export boundary and still receive a candidate
receipt. This strengthens the local-code promise for security-conscious buyers;
it does not approve an export, save or deploy a version, or establish demand,
payment, or revenue.
When those structural checks reject an archive member, printable names remain
exact while line, terminal, Unicode-separator, and bidirectional controls are
JSON-serialized inside one operator error. Unsafe paths, outside-root members,
special files, and duplicates therefore cannot forge a candidate result or
source-export request. This protects paid-distribution review integrity; it
does not authenticate an archive, grant approval, export source, save or deploy
a version, or create demand, payment, or revenue.
The candidate command now applies that presentation boundary once more to every
controlled `SiteCandidateError` before stderr. This contains requested archive
and receipt filenames plus operating-system context that may repeat them,
without changing any fully printable diagnostic or double-escaping an already
safe archive-member error. Real prepare and verification regressions preserve
reviewed evidence and emit no candidate or approval status. This protects
paid-distribution operator decisions; it does not make malformed argv or an
unhandled runtime fault safe, authenticate evidence, grant approval, export
source, save or deploy a version, or create demand, payment, or revenue.
Schema-2 candidate receipts now bind every tested deployable file's canonical
path, permission mode, and bytes before the external packaging helper runs.
Preparation rejects changed or injected output, while later `--verify-only`
checks reproduce the same payload digest without rebuilding. macOS packaging
suppresses AppleDouble metadata so portability does not weaken archive scope.
This closes the gap between a passing build and the artifact awaiting approval;
it does not authorize export, save or deploy a version, or create customer or
revenue evidence.
Candidate preparation now separates the production build from the site tests.
After install, audit, lint, and build, it writes the deterministic manifest and
captures the complete payload digest. `npm run test:site` then exercises that
exact existing `dist/` without rebuilding, and a second digest must match before
packaging can begin. The built executable output is therefore test-bracketed;
hosting metadata, Drizzle configuration, and the candidate manifest remain
integrity-bound and structurally checked. Schema-3 receipts established this
bracket so older post-hoc schema-2 evidence fails closed. This strengthens paid
distribution evidence without authorizing source export, version saving,
deployment, or recording customer or revenue evidence.
Schema-4 receipts extend that test-bracketed identity from regular files to the
complete payload tree. Every regular directory and file contributes its
canonical archive path, entry type, and permission mode; files also contribute
their size and bytes. Tested directories must use deterministic mode `0755`,
and packaging runs under an explicit `022` umask so helper-created staging
directories reproduce that contract across environments. Preparation and
independent verification reject noncanonical source modes, unexpected empty
directories, and changed archive permissions. This prevents extraction behavior
from drifting at the paid-distribution boundary without authorizing source
export, version saving, deployment, or recording customer or revenue evidence.
Schema-4 evidence also rejects duplicate JSON keys in checkout hosting
metadata, candidate receipts, and archived manifests, even when repeated values
match. Different JSON implementations can select the first or last repeated
value, so accepting either interpretation would make approval identity
parser-dependent. This closes that ambiguity without changing valid schema-4
receipts, granting approval, or creating customer or revenue evidence.
The shared duplicate-key failure now preserves printable names and
JSON-serializes presentation-unsafe names before operator output. Line,
terminal, Unicode-separator, and bidirectional controls therefore remain
escaped inside one explicit string instead of forging a candidate result or
source-export request. This preserves valid evidence and approval boundaries;
it does not authenticate a candidate, grant consent, export source, save or
deploy a version, or create demand, payment, or revenue.
Schema-5 evidence adds the public release identity the owner is being asked to
advance. Preparation strictly parses `project.version` and the website's single
`RELEASE_VERSION` declaration before commands run, requires the same semantic
version, and binds it into the archived manifest and receipt. Independent
verification recomputes that value, while prepare and verify output expose it
beside the exact receipt digest. Source-export approval can therefore state
that the candidate advances the buyer path from production `v0.3.50` to
`v0.3.51` without relying on an operator inference from source files. This
invariant is watched by the read-only hosted site contract whenever either
release-identity source changes. It strengthens paid-distribution review
without approving export, saving or deploying a version, or creating customer,
demand, payment, or revenue evidence.
Preparation and independent verification now also expose the receipt-bound
Sites `project_id` in their owner-facing result. Source-export approval records
that existing project identity with the public release version, exact receipt
digest, canonical source repository, source ref, and commit instead of leaving
the target project to an operator inference. This reduces approval and save
friction without granting consent, exporting source, saving or deploying a
version, or creating customer, demand, payment, or revenue evidence.
Plain independent verification can now accept the existing Sites source URL or
configured alias solely to produce a copy-ready pending export request. It
resolves that identity locally, rejects `origin`, and prints the release
version, project ID, exact receipt digest, canonical repository, source ref,
and commit in one compact JSON record with boolean
`deployment_approved=false`. Candidate status uses the same single-line JSON
boundary, preserving opaque project IDs and filenames without letting their
contents create sibling approval fields or extra terminal lines. Configured or
resolved source repository identities containing raw whitespace fail; URL path
spaces must be percent-encoded and remain exact after canonicalization. The
request cannot be combined with the later pre-save mode, does not query a
remote ref, and grants no approval. This turns validated distribution evidence
into a precise human decision without exporting source, saving or deploying a
version, or creating customer, demand, payment, or revenue evidence.
The release runbook now resolves the operational inputs that a real candidate
attempt exposed instead of assuming they already exist in an operator's shell.
It requires the active Sites plugin's trusted root packaging helper to be
executable, allocates one fresh private evidence directory per attempt, and
requires the existing project's credential-free source remote before printing
the pending request. Temporary source credentials stay out of remote URLs, Git
configuration, logs, documentation, and retained approval evidence; they are
reserved for the eventual approved push's per-command credential context.
This makes the paid-distribution handoff reproducible without granting consent,
exporting source, saving or deploying a version, or creating customer, demand,
payment, or revenue evidence.
The mandatory dependency audit now has an explicit failure boundary. A
nonzero audit reports that no candidate was produced and approval remains
blocked, stops before lint, build, tests, packaging, receipt publication, or
any later handoff action, and distinguishes vulnerability remediation from
rerunning the unchanged preflight when an audit endpoint is unavailable.
Because the audit may send resolved dependency metadata to its configured
endpoint, that retry is limited to an environment explicitly authorized for
the disclosure. The guidance never offers a skip, omission, or weakened audit.
This protects the paid buyer path without treating a blocked audit as a
candidate, approval, deployment, demand, payment, or revenue event.
Candidate preparation now also repeats the complete clean
`HEAD == origin/main` check after validation and packaging, requiring both
observations to retain the original synchronized commit. Read-only verification
repeats the same proof after validating the archive and receipt. A concurrent
clean commit or remote-tracking ref move that persists to an acceptance
checkpoint can no longer leave an approval-ready result labeled with an earlier
source identity. This strengthens paid distribution evidence; it does not
authorize source export, version saving, deployment, or create customer or
revenue evidence.
Those synchronized-source checks now also require the checkout's active branch
to remain `refs/heads/main`. A detached HEAD or alternate local branch at the
same `origin/main` commit can no longer receive a manifest that claims the main
source ref. This makes the approval identity truthful without changing valid
schema-4 receipts, granting source-export or deployment approval, or creating
customer or revenue evidence.
Candidate operations now bracket archive identity as well. Preparation hashes
the packaged archive before structural validation and requires the same regular
file and digest after its final synchronized-source proof before writing a
receipt. Read-only verification repeats the receipt-bound digest after archive
validation and its final source proof before reporting success. This closes a
mutation window in approval evidence without changing schema 4, granting an
approval, or creating customer or revenue evidence.
Read-only verification now brackets receipt identity too. It parses one exact
receipt byte buffer, retains that buffer's digest through archive and
synchronized-source validation, then requires the receipt path to remain the
same regular file with the same bytes before reporting success. A later edit
or replacement with a link fails closed. This strengthens paid-distribution
evidence without changing schema 4, granting approval, exporting source,
deploying a version, or creating customer or revenue evidence.
That exact receipt digest now crosses the approval interval explicitly.
Preparation derives it from the flushed staging file, publishes the receipt,
then repeats synchronized-source, archive, and receipt checks before reporting
success. Preparation and read-only verification both print `receipt_sha256`;
the owner records it with source-export approval, and the later pre-save check
can require it through `--expected-receipt-sha256`. Reformatting otherwise
equivalent JSON therefore cannot silently replace the reviewed evidence. This
makes paid distribution approval reproducible without granting approval,
exporting source, saving or deploying a version, or creating customer or
revenue evidence.
The pre-save verifier now binds that approved artifact identity to the source
that actually crossed the export boundary. Owner approval records the
credential-free canonical identity of the existing Sites repository alongside
the receipt digest, source ref, and commit. The pre-save check resolves the
operational URL or remote alias and requires that identity to match approval,
remain stable, and differ from `origin`; local repositories, public origin,
equivalent aliases, and unrelated forks fail even when they contain the same
commit. It then performs two read-only `git ls-remote` resolutions of the
approval-bound repository's `refs/heads/main` and requires both to equal the
receipt commit. A wrong or moving export therefore cannot advance to version
saving even when the local checkout, archive, and receipt remain valid. The
pre-approval verifier remains offline, and this additional check neither
exports source nor saves or deploys a version. It protects the paid
distribution path without creating customer, demand, payment, or revenue
evidence.
The approved receipt digest and both repository arguments now form one atomic
pre-save mode. Supplying the digest alone fails before local evidence checks
instead of returning a generic verification success without querying the
approved source repository. Plain pre-approval verification remains offline
and prints the digest an owner can review. This prevents an operator omission
from weakening the paid-distribution gate without exporting source, saving or
deploying a version, or creating customer or revenue evidence.
Canonical repository identity now retains any non-default network port while
normalizing the standard Git, HTTP, HTTPS, and SSH ports across legitimate
protocol aliases. The pending request's exact canonical identity can be passed
back to pre-save verification without reconstructing a URL. Conventional
`git@` remains protocol-neutral, while every other SSH URL or SCP username is
retained as approval-significant authority. For those users, home-relative SCP
paths remain distinct from absolute SSH URL or SCP paths. A server on an
unapproved port, username, or path mode can no longer inherit approval from the
same visible host and path merely by exposing the receipt commit. This closes
authority ambiguities in the paid-distribution handoff without exporting
source, saving or deploying a version, or creating customer or revenue
evidence.
Candidate preparation also refuses any pre-existing requested archive or
receipt before source checks or build commands begin. It gives the packaging
helper a private staging path on the archive destination's filesystem,
validates and rechecks source against that staged archive, then atomically
hard-links the archive into its requested path only if the path is still
absent. The receipt is written, flushed, and synced to its own same-directory
staging file and published through the same no-clobber primitive. A destination
claimed after preflight keeps its bytes and causes preparation to fail instead
of replacing evidence. A late receipt collision can leave the validated
archive published without an approval-ready receipt, so that unpaired archive
must not advance the handoff. This changes no schema-4 evidence, authorizes no
source export or deployment, and creates no customer or revenue evidence.
Archive and receipt path normalization now resolves each parent directory while
preserving the requested leaf. Preparation therefore rejects initial and
dangling output symlinks instead of following them to an unapproved evidence
location, and verification rejects a link before reading candidate bytes.
Resolving the parent still rejects an existing symlinked directory that points
back into the protected checkout. This keeps paid-
distribution approval attached to the exact evidence leaf an operator supplied
without exporting source, saving or deploying a version, or creating customer
or revenue evidence.
Output containment now also inventories every non-symlink checkout directory
and compares those filesystem identities with each existing output-parent
ancestor. Stable alternate case or Unicode spellings, whole-repository aliases,
and aliases exposing only a checkout subdirectory therefore fail before source
checks or build commands even when lexical containment differs. Missing output
directories are skipped, repeated directory identities stop mount cycles, and
reported traversal or ambiguous identity lookup failures stop preparation. This
does not detect an alias whose filesystem remaps identity. The guard protects
paid distribution evidence without exporting source, saving or deploying a
version, or creating customer or revenue evidence.
Final candidate publication now narrows the concurrent replacement boundary
too. Both direct output parents must already exist on a POSIX host with
descriptor-relative staging and hard-link support. Preparation opens each
unique parent without following a symlink before running commands, verifies
repository containment and requested-leaf absence through that descriptor, and
keeps it non-inheritable and live through validation and publication. Archive
and receipt paths sharing one parent reuse one descriptor, preventing two opens
from binding one candidate pair to different directory instances. Each leaf is
created relative to its held parent, so later path replacement cannot redirect
publication. Publication now opens the staged source without following links,
opens the new leaf relative to the held parent, and requires both descriptors
to identify the same regular file.
Archive staging now uses a private `0700` directory created and opened relative
to the held archive parent. The packaging helper still receives a visible path,
but preparation accepts only the regular archive opened relative to the held
staging descriptor, then hashes, validates, rechecks, and publishes while
holding that exact file. The hard-link source name is resolved relative to the
held staging directory only after its inode is rechecked against the held
archive; the published inode must match again after the link. Cleanup compares
the current leaf and directory with their recorded identities; a substitution
is preserved for investigation and fails rather than being deleted. If the
visible parent was replaced, any helper artifact written there is left
untouched and cannot satisfy acceptance.
Receipt staging now creates a private `0600` leaf relative to the receipt
parent held from preflight and retains one non-inheritable regular-file
descriptor through writing, syncing, hashing, recheck, and publication. The
staged digest must equal the exact deterministic JSON bytes preparation
intended to write, so same-inode mutation cannot silently become approval
evidence. Publication resolves the source name relative to the held parent and
requires it to match the staged file before linking. Cleanup removes only the
recorded identity, preserves and reports a substituted or uncertain leaf, and
closes staged or partially transferred descriptors on failure.
Preparation keeps the exact archive and receipt descriptors non-inheritable and
live through the final source and digest checks. Before success, it reopens each
requested parent, requires that parent to match the held descriptor, and
compares the leaf relative to it with the published file descriptor.
Link-to-open substitution, byte-identical leaf replacement, and a replaced
parent re-linking the same file therefore fail closed. Both archive and receipt
staging now remain descriptor-bound through their acceptance and cleanup
boundaries. This strengthens paid-distribution integrity without exporting
source, saving or deploying a version, or creating customer or revenue
evidence.
A separate read-only hosted dependency contract runs for every source change
under `app/`, relevant lock and workflow changes, manual dispatch, and a weekly
schedule so a paid CTA or newly published advisory does not wait for an
unrelated package edit. It uses the minimum supported Node version, installs
only the committed lock, audits the complete dependency tree, builds and
exercises the rendered buyer path plus the patched Sharp and Miniflare runtime,
and lints. It has no repository secrets or write permission and cannot save or
deploy a site. A passing contract protects the buyer path; it does not prove a
visit, install, pilot request, payment, or revenue.
That hosted contract caught high-severity denial-of-service advisories in React
Server Components and every installed pre-`5.0.8` `brace-expansion` line on the
day GitHub reviewed them. The repaired lock advances React, React DOM, and the
server-components package to `19.2.8`, pins `brace-expansion` `5.0.8`, and
replaces the legacy lint bundle with direct ESLint 10, TypeScript, React Hooks,
and Next rule sets. The complete lock still receives an unsuppressed
zero-vulnerability audit, build, runtime compatibility test, and lint check.
This is operational protection for the paid buyer path, not evidence of demand,
payment, or revenue.
Preparing the replacement for superseded Sites version 47 exposed a second
boundary: saving a candidate requires pushing the repository to a separate
Sites-managed source repository. That source export stopped before any push
because it lacked explicit owner approval. The handoff now requires export
approval before source transfer, then a distinct deployment approval after a
version is saved. Before either action, a fail-closed preflight requires the
hosted Node runtime, a clean `origin/main` checkout, the complete dependency
and build checks, and a provenance-bound archive receipt. A separate read-only
mode then checks strict receipt structure, synchronized source and lock
identity, archive bytes, and the embedded project manifest immediately before
export approval and again before saving. It runs no build, network, source
export, save, or deployment operation. Export consent cannot authorize
production. This protects the local-first promise made to security-conscious
buyers; it does not create a saved version, deployment, visit, pilot request,
payment, or revenue event.
Repository vulnerability alerts and automated security-fix proposals are now
enabled. The committed Dependabot policy disables routine npm version-update
pull requests while grouping npm security fixes, and checks pinned GitHub
Actions weekly with at most two open version-update pull requests. Every change
proposal remains review-only and triggers the dependency contract; nothing
auto-merges, saves a Sites version, or deploys production. This shortens
security response for the buyer path without treating maintenance activity as
demand or revenue.
The first bounded action review advanced `actions/checkout` to the full commit
behind `v7.0.1` only after the upstream tag resolved to a GitHub-verified commit
and every hosted workflow, copy-ready customer example, and executable pin
expectation moved together. The separately proposed `actions/setup-python`
major was left for an independent compatibility review rather than bundled into
that patch transaction.
That review advanced `actions/setup-python` to the full commit behind `v7.0.0`
after confirming that both versions use Node 24, Repo Scout uses only the
unchanged `python-version` input, and the removed `pip-install` input appears
nowhere in its workflows. Hosted proposal evidence set up CPython 3.11.15 and
completed the verified release download, provenance check, index-free install,
policy enforcement, rollout upload, and pilot contract. All five hosted Python
workflows, the copy-ready customer example, and their independent pin contracts
now accept the same identity. Together these reviews prove the proposal queue
can preserve paid-CI trust boundaries without auto-merging, deploying the site,
or creating customer or revenue evidence.
A repository-wide action-pin audit now discovers every external `uses:`
reference across all six hosted workflows and the copy-ready customer gate.
It rejects mutable refs, missing exact release annotations, multiple accepted
identities for one action, and dogfood/customer action-sequence drift. This
covers the pilot-intake pins that had no direct identity contract and makes
future partial Dependabot proposals fail closed. Repository consistency does
not verify an upstream tag, establish input or runtime compatibility, approve
an upgrade, or create customer, demand, payment, or revenue evidence.
The hosted dependency contract invokes this audit explicitly before Node setup
and general test discovery, and runs when either the audit script or its unit
contract changes. Removing the discoverable test therefore cannot silently
bypass the paid-CI supply-chain gate. The job remains read-only and secret-free,
and a passing run remains maintenance evidence rather than customer or revenue
evidence.
The audit also requires exactly one $299 USD founding-team service at the
production pilot section and at least one website-attributed link to the public
application form whose CTA discloses the same $299 price. This detects a broken
or misleading paid conversion path; it does not submit the form, create a
request, or establish willingness to pay.

The first direct-acquisition batch is deliberately small: 10 qualified
engineering leads, personalized from relevant public evidence, with one initial
message and at most one follow-up. Contact uses warm introductions or clearly
published business addresses, never scraped personal data or sales pitches in
GitHub collaboration channels. The private outreach ledger records attempts
and replies, but only pilot intake and paid labels enter the revenue funnel.
Every initial message now gives the recipient a clear way to decline and
promises no further contact after that response; silence permits only the one
bounded follow-up already disclosed by the experiment.
The local outreach auditor enforces the 10-prospect boundary, three-signal
qualification, alias-only records, permitted channels, one seven-day follow-up,
and terminal stop states. It sends nothing and exposes no recipient details;
its totals remain operator activity rather than commercial evidence.
Its omitted-date default and every documented lifecycle command use the current
UTC calendar date. This keeps a review receipt, approval, manual contact, and
follow-up on one reproducible day convention when the operator's local date
differs near midnight; it does not make or send any of those decisions.
Every nonblank ledger date and CLI date option must also use canonical,
zero-padded `YYYY-MM-DD`. Compact and ISO week spellings fail before queue
selection or mutation so textual due-date ordering cannot contradict calendar
ordering.
Across the pilot and outreach Python APIs, only `as_of=None` selects the
current UTC date. Falsey booleans, numbers, and strings fail before funnel
evidence is built or a private outreach path is inspected, preventing a caller
mistake from silently moving the operating window to today.
Schema-3 outreach reports separate drafts from sent attempts. Schema 5 adds an
explicit `approved` checkpoint and requires its private approval date
to survive every later status. Drafted and approved rows require a permitted
channel but forbid contact and follow-up dates, preventing message preparation
or approval queues from inflating acquisition activity. Every approved or sent
row must retain an approval date no later than contact. Approval is a human
record that the observation, recipient, channel, and offer were checked; the
auditor does not make that judgment. Every declared fit signal must map to one
private HTTPS source before the auditor accepts a prospect. Reports retain only
aggregate link and approval counts, not source URLs or approval dates. A valid
link makes qualification reviewable but does not make the source authoritative,
accurate, or current; Sales Intelligence or narrow public evidence still
requires human review. Strict CSV parsing also rejects malformed quoting and
any row with missing or extra cells, so a shifted private date or status cannot
silently disappear from the operating record.

Outreach schema 6 adds `review-declined` as a pre-contact terminal decision.
The guarded decline command requires the deterministic next draft and explicit
human no-send confirmation, then atomically changes only its status. It leaves
approval and contact dates blank, counts the row as closed rather than
attempted, and advances the review queue without requiring a hand-edited CSV.
This preserves negative human judgment instead of nudging every reviewed draft
toward approval, and it creates no lead, demand, or revenue evidence.
The buyer-facing README now names that packaged schema-6 behavior directly, and
a contract test derives the documented schema number from the runtime constant.
This prevents released review controls from being presented as future work and
strengthens distribution credibility; it does not create a prospect action,
pilot request, payment, or revenue.

Future tagged releases must exercise the complete guarded lifecycle through the
installed wheel before provenance attestation. One synthetic draft follows the
copy-ready no-send command and proves a closed review with zero attempts. A
second requests the private human checklist, rejects an unconfirmed approval
without changing the file, records confirmed approval and contact, calculates
the exact seven-day follow-up, closes that one follow-up, and refuses a duplicate
without changing the file. The check also proves permission retention,
attempted-prospect accounting, private-field omission, and bounded
missing-approval and extra-cell errors. Temporary synthetic rows are used, so
the check sends nothing and creates no prospect, demand, or revenue evidence.

The same verified `v0.3.34` distribution now carries outreach schema 5 and
pilot qualification schema 7, so operator workflows and customer CI examples
come from one source commit,
manifest, wheel digest, and provenance-attested release. This alignment reduces
deployment ambiguity; it does not create qualified prospects or demand.

Public `v0.3.33` adds the schema-5 approval status and retained approval-date
checks needed to execute the prepared outreach batch without relying on source
checkout. Its portable, wheel, and source artifacts use the same checksum and
provenance release contract. It established the independently measured wheel,
source-commit, and provenance pinning path; publishing a package does not count
as a prospect, attempt, lead, or sale.

Public `v0.3.34` adds exact nine-cell ledger enforcement and makes the installed
outreach lifecycle smoke test part of the release boundary. This closes the
row-shift ambiguity found after `v0.3.33` while keeping the human approval,
privacy, checksum, and provenance contracts together in one installable wheel.
Both policy gates now pin its independently measured wheel digest and exact
source commit after a separate manifest, tag, signer-workflow, provenance,
hosted-runner, policy-activation, and outreach-lifecycle review. Publication and
pinning do not approve or send the five drafts and do not create a prospect,
pilot request, or sale.

Public `v0.3.35` packages the guarded approval, contact, and one-follow-up
operations added after `v0.3.34`, along with complete installed-entry-point
behavioral checks and consistent command and zipapp version identity. Its
release boundary blocks publication unless the paid-workflow commands compose
through the built wheel and report the semantic tag exactly. Both customer and
dogfood CI gates now pin its independently measured wheel digest, exact source
commit, checksum manifest, signer workflow, and GitHub-hosted provenance after
separate installed policy-activation and guarded-outreach checks. This improves
paid-pilot distribution readiness; it does not approve drafts, create attempts,
validate demand, or book revenue.

Public `v0.3.36` packages the complete private human-review bundle needed before
those guarded operations: explicit evidence links, bounded selected draft text,
and full note-to-ledger identity preflight. The installed-wheel release smoke
proves default output stays redacted, disclosed material is selected and marked
private, drift fails without message leakage, and the ledger remains unchanged.
This removes source-checkout dependence from the immediate outreach decision;
it still does not make the judgment, approve, send, or create revenue evidence.

Public `v0.3.37` packages the explicit initial-message opt-out and the matching
human review check. The release smoke still exercises the complete private
review, exact opt-out checklist, approval, contact, and one-follow-up lifecycle
through the installed wheel. This makes the distributed operator path match the
five prepared drafts; it does not approve a draft, contact a prospect, or
validate demand.

Public `v0.3.38` packages the private execution boundary added after that
release: live in-repository paths must be ignored and untracked, POSIX files and
parent directories must remain owner-only, and private text handoffs carry
complete shell-quoted commands through the guarded lifecycle. The installed
wheel smoke rejects permissive paths without mutation and executes every emitted
handoff. This distributes a safer acquisition workflow; it does not review or
send the five drafts and does not establish demand or revenue.

Public `v0.3.39` packages the guarded human no-send branch for the outreach
queue. An unsuitable draft can now move to `review-declined` only after exact
alias matching, private-ledger validation, and explicit human confirmation;
the installed smoke proves that decision closes the draft without approval,
contact dates, or attempted-prospect inflation. This makes negative review
decisions usable from the distributed operator path; it does not make a real
decision, contact a prospect, establish demand, or book revenue.

Public `v0.3.40` packages truthful terminal receipts for that no-send branch.
Decline schema 2 reports only the remaining draft count, advances nonempty
queues, and emits no review command when the bounded queue reaches zero. The
installed lifecycle smoke proves the one-draft terminal path. This removes a
misleading operator handoff; it does not make a review decision, contact a
prospect, establish demand, or book revenue.

Public `v0.3.41` packages guarded observed-outcome recording after contact or
follow-up. The installed lifecycle smoke proves an unconfirmed write cannot
change the private ledger, then records one synthetic `pilot-requested` outcome
through the installed command while retaining prior contact evidence. This
closes the operator feedback loop without inflating the public funnel: a private
outcome is not demand until public intake and is not revenue until payment.

Version `0.3.42` advances the package, portable CLI, website metadata,
verification guide, and installed commercial smoke fixture together. It
packages verified-pin rollback and recovery reporting, release-contract
reconciliation, and permission-preserving atomic replacement for existing team
policies and rollout reports. After separate public-artifact verification,
customer and dogfood CI now pin source commit
`6d9edda82e8a84782a3532c8772690bc0973bc7a` and wheel SHA-256
`207931651b217dc02dfacb64886da409b5518d78c3ada702edace58ea9db1e5e`.
The downloaded manifest, annotated tag ancestry, all three provenance
attestations, pinned signer workflow, hosted `ubuntu-24.04` runner, seven
installed command identities, and four commercial smoke harnesses passed before
the pins changed. This makes existing activation safeguards distributable; it
does not establish an install, customer usage, demand, payment, or revenue.

The first five personalized outreach drafts now exist in the ignored private
workspace. Sixteen fit links were reviewed against narrow, company-controlled
public evidence because no Sales Intelligence or CRM provider is connected.
Live review and mutation now reject any in-repository ledger or draft file that
is tracked, not ignored, or symlinked, and the documented workspace uses
owner-only directory and file permissions. POSIX live actions enforce that
boundary by rejecting group/world-accessible files and immediate parent
directories before reading private material. Counts-only validation of the
empty public template remains available. This reduces accidental prospect-data
disclosure; it does not approve a draft, create an attempt, or establish demand.
The committed schema-12 checkpoint contains only aggregate counts. The first
complete owner-only review bundle was created in the ignored private workspace
from the verified `v0.3.48` wheel without changing the ledger, but its July 21
schema-4 date binding is now superseded and must not be used for a later
decision. A fresh schema-6 bundle now exists at
`outreach-private/next-review-v6.md` with owner-only permissions and no ledger
mutation. The schema-4 and schema-5 bundles are superseded. All five remain
`drafted`: approved messages, attempted outreach, replies, pilot requests, and
revenue are still zero until a human reviews and sends each message through its
published business channel.

The operator can now request one deterministic `--review-next` checklist. It
names only the next private alias and permitted channel, reports qualification
counts instead of URLs, displays the canonical direct-outreach offer route, and
prints six unchecked criteria covering observation, recipient, price and scope,
local-code handling, source preservation, and opt-out behavior. The mode does
not expose draft text, edit status or dates, approve a message, or send it. Its
output stays private and cannot be used as a counts-only public baseline; review
readiness remains operator preparation rather than demand or revenue.
When the reviewer needs the underlying qualification sources, the explicit
`--include-private-evidence` opt-in maps that one draft's signals to their HTTPS
links without editing the ledger. Default output remains redacted, while the
opt-in output is clearly private and excluded from committed reports and CI
artifacts. This removes manual CSV parsing from the human decision without
turning a link into verification, approval, contact, demand, or revenue.
The companion `--include-private-draft` opt-in reads a bounded private Markdown
file and selects only the exact `## prospect-NNN` section matching that review.
Together the flags put the recipient, message, and qualification sources in one
private checklist. A cross-file preflight requires notes for every still-drafted
ledger alias, rejects note aliases absent from the ledger, and permits retained
history for aliases that progressed. This prevents stale or mismatched private
material from entering a decision while keeping the ledger read-only. It does
not let Repo Scout judge, approve, send, or count the message as demand or
revenue.
A complete evidence-and-draft review now emits a schema-6 SHA-256 receipt over
the normalized selected ledger row, selected private draft, displayed
source-preserving campaign route, and six human checks. Its generated approve
and decline commands carry that receipt plus the reviewed notes path, while
using actual-date placeholders instead of copying the bundle's ledger-audit
date into a later human decision. Before either mutation, Repo Scout reloads
the private files and recomputes the receipt; a changed source, channel, draft,
route, or check fails without modifying the ledger or exposing the changed
content. An unchanged review can therefore be decided on a later UTC date
without backdating approval evidence. This binds a human decision to what was
actually reviewed without making Repo Scout perform the judgment.
Redacted, evidence-only, and draft-only inspections now omit an approval
command, and guarded `--approve-next` always requires both the digest and
reviewed notes path. An unbound decline remains available as an explicit
no-send escape hatch so a malformed draft can be rejected without repairing it.
This makes send eligibility depend on review of the exact `$299` offer while
keeping negative judgment operationally cheap.
Before Repo Scout emits that decision-ready receipt, the selected private draft
must contain the exact canonical direct-outreach route once. Missing and
repeated routes fail before JSON or owner-only bundle output, preserve the
ledger, and leave draft text out of the error. Redacted and draft-only review
remain available as correction paths. The same boundary now requires one
canonical `$299` disclosure, no competing dollar amount, and no obvious
negation. Explicit language saying the recipient will not pay or no payment is
required fails regardless of whether it appears before or after the price, so
each approved attempt can test willingness to pay for the stated offer.
Missing, repeated, negated, nonpayable, or competing price text fails without
output or mutation. Later receipt verification maps
route or pricing drift to the same generic stale-review failure. The existing
schema-6 owner-only queue passes both preflights without changing its receipt,
but a human still decides whether the message is accurate and appropriate.
The verified private notes revision now travels into the locked approval or
decline commit as well. An editor save after receipt verification therefore
forces a fresh review instead of recording a decision against content that no
longer matches the human evidence. Symmetric regression coverage now forces
that exact commit-window edit during both approval and decline, proving each
branch preserves ledger bytes, hides changed text, and removes staged output.
The approval receipt's manual-send handoff now retains the same review digest
and private notes path. Before `--record-contact` counts the attempt, Repo Scout
reconstructs the approved row's reviewed state, reloads the selected draft, and
holds the verified notes revision through the atomic ledger write. Selected
message drift before or during contact recording fails without exposing the
changed text or creating activity. Approval also persists that digest in the
current eleven-column private ledger and schema-3 receipt. If the one-time
receipt is lost, schema-12 reporting regenerates a digest-bound contact handoff
that must exactly match the durable approval identity; it cannot revalidate
later draft edits without the notes path, but it no longer discards the human
review's identity. Nine- and ten-column legacy approvals remain recoverable
through an explicitly unbound marker and never masquerade as current bound
evidence. This protects the normal `$299` experiment path without claiming
what was transmitted outside Repo Scout.

The same complete review can now be created with `--write-review` inside the
ignored private workspace instead of exposing the draft, alias, and evidence to
terminal capture or relying on shell redirection. The command stages and syncs
the full text with owner-only permissions, atomically publishes only to a new
path, refuses overwrite or symbolic-link destinations, and prints only an
alias-free confirmation. A failed staging cleanup after publication now reports
the completed review and a neutral retained owner-only filename instead of
claiming clean success or repeating a potentially sensitive destination name.
This allows manual cleanup without an overwrite-producing retry. The ledger
remains unchanged. This makes the bounded human review queue easier to execute
without performing the review, approving or sending a message, creating public
demand, or recording revenue.

The guarded approval, decline, contact, follow-up, and outcome mutations now
apply the same truthful cleanup boundary to the private CSV ledger. If a failed
mutation also cannot remove its staged replacement, the command retains the
original mutation error, reports only a neutral owner-only staging filename,
and tells the operator to remove that file before continuing. It does not print
the destination-derived name or the cleanup exception, either of which could
contain private ledger identity. A failed replacement leaves the current ledger
unchanged. This protects the bounded acquisition workflow without approving,
sending, or counting outreach as pilot demand or revenue.

Version `0.3.51` packages the paid-CI activation hardening, exact public
provenance constraints, payment-backed conversion accounting, strict commercial
inputs and dates, configured-price recommendations, and post-publication
immutable-release evidence accumulated since `v0.3.50`. The complete source and
installed-command contracts passed before publication. After separate public-
artifact verification, customer and dogfood CI now pin source commit
`e38c54c1564a65427ed6616eda180e5dadf40414` and wheel SHA-256
`506925aaba1acec2e4e4f6332753f1a140a0ec3d3ed133e15489613883e425b5`.
The manifest, annotated tag ancestry, main ancestry, release workflow,
`immutable: true` state, all three provenance attestations, exact signer
workflow, and GitHub-hosted-runner restriction passed before the pins changed.
Publishing and pinning these artifacts does not establish a customer install,
outreach attempt, pilot request, payment, or revenue.

Version `0.3.50` packages that guarded-ledger cleanup boundary so the human
approval and send-recording workflow does not depend on a source checkout. The
source suite proved the dual mutation-and-cleanup failure preserves current
ledger bytes, owner-only staging permissions, the original error, and private
identity redaction. The installed lifecycle smoke proved the complete guarded
path before release. After separate public-artifact verification, customer and
dogfood CI now pin source commit
`371d6fd8da0dc33f60b5c808ca3a3c516125cd7b` and wheel SHA-256
`a684e16240c0d50357ba552e8b56fa9024c32e80b9ae7b23bd44a874eec1df24`.
The manifest, annotated tag ancestry, release workflow, all three provenance
attestations, exact signer workflow, and GitHub-hosted-runner restriction passed
before the pins changed. Publishing and pinning this safeguard does not review
or send outreach, create a pilot request, collect payment, or record revenue.

Version `0.3.49` packages that truthful cleanup boundary so future owner-only
review bundles do not depend on a source checkout. The installed lifecycle
smoke proved clean review publication, exact permissions, alias-free terminal
output, and zero ledger mutation before release. After separate public-artifact
verification, customer and dogfood CI now pin source commit
`78abdb3e7dc2bfe2e2060727ea5a7636d9dc63fb` and wheel SHA-256
`47b68b7fb5e93665fd8888972c8cb1e07e3a89db4262f8c38127709295c21bc3`.
The manifest, annotated tag ancestry, release workflow, all three provenance
attestations, exact signer workflow, and GitHub-hosted-runner restriction passed
before the pins changed. Publishing and pinning this safeguard does not perform
a review, send outreach, create demand, collect payment, or record revenue.

Version `0.3.48` advances the package, portable CLI, website identity,
verification guide, and installed commercial smoke fixture together so that
owner-only review-file creation reaches the existing five-draft workflow. The
tag must prove the complete private write through the installed wheel, including
alias-free terminal output and exact `600` file permissions, before checksums
and provenance are published. After separate public-artifact verification,
customer and dogfood CI now pin source commit
`608de9ff4c2ee2e995917ee02346c4420c6b18e1` and wheel SHA-256
`448c1b7ba2bd1953d4c0ef04656c9886ef2613ef31386812a857f2bb20ee5b22`.
The manifest, annotated tag ancestry, and all three provenance attestations
passed before the pins changed. Publishing and pinning this operator safeguard
does not perform a review, send outreach, create demand, collect payment, or
record revenue.

Version `0.3.43` advances the package, runtime, website, download guide, and
installed-command smoke identities together so the schema-4 content receipt can
reach the five-draft operator workflow. The same boundary ships bounded GitHub
download and provenance recovery already exercised on main. After separate
public-artifact verification, customer and dogfood CI now pin source commit
`e041d9d786c16bce2b645a407d3556ed4146d427` and wheel SHA-256
`6fdf59d039cd168fa830f1dc72b6b4627e1df6a30f52c933ccdc559643497f16`.
The downloaded manifest, annotated tag ancestry, all three provenance
attestations, exact signer workflow, hosted-runner restriction, seven installed
command identities, and four paid-workflow smoke harnesses passed before the
pins changed. This makes review safety distributable; it does not perform a
review, send outreach, establish demand, or create revenue.

Version `0.3.44` advances the package, runtime, website, download guide, and
installed smoke identity together so UTC outreach defaults reach the same
operator workflow. Its wheel smoke runs the installed outreach command under a
local timezone whose calendar date differs from UTC and requires the report to
retain the current UTC date. After separate public-artifact verification,
customer and dogfood policy gates now pin source commit
`7012255f5b88ab01fbd84e58ccfec310a397b614` and wheel SHA-256
`1855cc8066434f2c07d998caa869e0f898511d6df996b03a03cb61df5eb10d89`.
The downloaded manifest, annotated tag ancestry, wheel provenance, exact signer
workflow, hosted-runner restriction, seven installed command identities, and
four paid-workflow smoke harnesses passed before the pins changed. This removes
a distribution mismatch; it does not prove a customer install, review or send
a draft, create demand, or record revenue.

Version `0.3.45` packages the actual-date outreach handoffs so the public wheel
matches the documented human workflow. Its installed-command smoke approves on
July 1, records the real send on July 3, displays the July 10 due date, and
records the follow-up on July 10. It requires both generated future-action date
placeholders before substituting those event dates. After separate
public-artifact verification, customer and dogfood policy gates now pin source
commit `607745873a2262f2f7710609f02ea3b617d3db9e` and wheel SHA-256
`fdf5642f3b205eb73644c96ee782b4cb34771c77dc77f9b21441e0716c76792d`.
The downloaded manifest, annotated tag ancestry, all three provenance
attestations, exact signer workflow, hosted-runner restriction, seven installed
command identities, and four paid-workflow smoke harnesses passed before the
pins changed. Distribution baselines remain on their measured `v0.3.44`
boundary. This distributes truthful private evidence handling; it does not
prove a customer install, review or send a draft, create demand, or record
revenue.

Version `0.3.46` packages the next execution boundary for the existing private
review queue. The installed wheel now retains first outcome observation dates,
separates delayed outcome events from the ledger audit date, links confirmed
private pilot interest to the buyer-controlled public intake form, and requires
the exact `pilot-paid` label before reporting booked revenue. It also warns on
lost opportunities missing public lead history. After separate public-artifact
verification, customer and dogfood policy gates now pin source commit
`6a352d76e0c22679096f7606c5bab1429872e961` and wheel SHA-256
`5a32dffabbeb7abf98d13fec5bca148830b8e80a1d4de0f6f424b1b57dc8db45`.
The downloaded manifest, annotated tag ancestry, all three provenance
attestations, seven installed command identities, and four paid-workflow smoke
harnesses passed before the pins changed. Public traffic baselines and measured
release evidence remain on their last deliberate `v0.3.45` checkpoint. This
makes current conversion evidence controls distributable; it does not review or
send outreach, create a public request, collect payment, or claim revenue.

Version `0.3.47` packages the privacy-safe recovery path for that same private
queue. Schema-9 reports recover only the next approved alias, classify every
next-approved or due-follow-up alias as private, and expose an alias-free
counts-only state for publication automation. The installed
`--require-counts-only` guard emits nothing and exits 7 before a private report
can reach an artifact, and it cannot be combined with review or lifecycle
mutations. Verified customer and dogfood CI pins remain on `v0.3.46` until the
new artifacts are independently reconciled. This distributes an execution
safeguard; it does not review or send outreach, create demand, collect payment,
or claim revenue.

After a human completes those checks, guarded `--approve-next` can record the
decision without hand-editing CSV. It requires the exact next alias, an explicit
review date, a confirmation flag, the complete review digest, and the reviewed
private notes path; validates all rows before and after; and always revalidates
the content-bound receipt before atomically preserving file permissions while
changing only status, approval date, and approved review digest. The approval
result receipt excludes evidence and review dates.
Approval still sends nothing, creates no contact or follow-up date, and is not
an attempt, lead, pilot request, or revenue event. Private complete-review
output carries the selected alias, confirmation flag, review receipt,
shell-quoted private paths, and actual-date placeholders into a complete
decision command. The approval receipt's contact handoff instead uses explicit
date placeholders;
requiring the operator to replace them prevents a later manual send from
inheriting the earlier approval date. Schema-3 approval receipts also report
the remaining drafted count. When another draft remains, the text receipt
emits a separate command for use only after that contact record succeeds. A
content-bound approval preserves the private evidence and draft flags, exact
notes path, and shell-quoted owner-only review destination so the next
prospect receives a fresh complete bundle instead of being stranded after a
successful send. At zero, the receipt ends the bounded queue without a dead
handoff. This removes manual command reconstruction without completing a
review, sending a message, or treating operator activity as demand.

That sequence is now enforced rather than merely described. While any approved
message and another drafted row coexist, review, approval, decline, and
owner-only review writing fail before output or mutation. The operator must
send the pending approved message manually and record it through the existing
guarded contact transition before the next draft can advance. Reports still
read legacy ledgers with multiple approved rows and recover the lowest alias
for contact recording, so the new boundary does not strand earlier evidence.
This serializes the paid-offer experiment without sending outreach, inferring a
send, or creating demand or revenue evidence.

When the human instead decides a draft must not be sent, guarded
`--decline-next` requires the exact same next alias and an explicit no-send
confirmation. The generated complete-review command revalidates the same
content receipt before it atomically changes only status to `review-declined`,
preserves the private file boundary, reports the privacy-safe remaining-draft
count, and records no action date. It emits the next review command only while
another draft remains and ends truthfully when the bounded queue reaches zero.
For a content-bound decline, that command retains the private evidence flag,
draft flag, and exact notes path, then requires a new owner-only review output
path before writing the next complete bundle. The
`PRIVATE-REVIEW-PATH` marker is always shell-quoted, so literal replacement
with a path containing spaces remains one argument; leaving the marker
unchanged fails before private files are read. A replaced path produces only
an alias-free terminal confirmation while the selected alias, sources,
message, and fresh digest remain in the `600` file. This avoids regressing a
private review back to terminal disclosure after a no-send decision.
That future review command requires an actual-date placeholder instead of
reusing the decline date, so a delayed next decision cannot silently backdate
its content receipt or approval evidence.
The aggregate report counts this as closed before contact and never as an
attempt. This keeps the acquisition queue moving without converting negative
review judgment into an approval or a false outreach event.

After a human sends that approved message, guarded `--record-contact` records
the exact next approved alias with an explicit send date and confirmation flag.
It retains approval evidence, atomically changes only status, contact date, and
the exact seven-day next action, and produces a private receipt that omits
evidence and approval dates. The follow-up date makes send timing inferable, so
the receipt stays private. The tool does not deliver the message or an automatic
follow-up. A recorded contact enters outreach-attempt operations, but still is
not a lead, pilot request, payment, or revenue.

Contact receipt schema 2 now preserves the approval-to-attempt audit link in a
structured `review_binding`. `approved_review_digest` records only identity
that was stored at approval and is null for a legacy approval, while the
separate `content_revalidated` boolean records whether the private notes were
checked at contact time. The four combinations therefore distinguish current
approval with full revalidation, current digest-only recovery, legacy approval
with current notes revalidation, and fully unbound legacy contact. The private
receipt still omits draft text, evidence URLs, approval dates, the explicit
contact date, and the internal legacy marker. This can show which Repo Scout
review boundary governed the ledger transition, but it cannot prove what the
external channel delivered or that a prospect saw or answered the message.

Schema 12 makes that transition recoverable if the one-time approval receipt is
lost. The ordinary report surfaces only the lowest approved alias and the
durable review digest, then regenerates a digest-bound guarded contact command
with required send-date placeholders. It does not expose the draft,
qualification evidence, channel, approval date, or private notes path, and a
machine-readable `private_output` flag marks that alias-bearing report as
private. Due-follow-up aliases receive the same classification; only reports
with neither kind of alias are marked counts-only. Legacy approvals that predate
the digest column remain explicitly unbound instead of receiving invented
identity. This lets publication automation refuse private execution evidence
before it becomes an artifact and prevents a reviewed message from being
stranded without approving or sending it, creating demand, or recording
revenue.
The companion `--require-counts-only` guard makes that refusal executable: it
emits no report and exits with code 7 when either alias source is present. The
flag cannot be combined with a review or lifecycle mutation, so a CI or
publication job can fail closed without changing private sales evidence.

After a human sends the one allowed follow-up on or after day seven, guarded
`--record-follow-up` records the earliest due contacted alias. It retains the
approval and initial-contact evidence, atomically changes only status,
follow-up date, and next action, then clears that next action so no second
follow-up is scheduled. Early, future, and out-of-order records are rejected.
The alias-only receipt remains private, and the tool sends nothing. A follow-up
is still outreach operations, not a new prospect, lead, pilot request, payment,
or revenue event. The contact receipt displays the calculated due date but uses
date placeholders for follow-up recording, so a later human send is retained
truthfully while validation still rejects a send before the due date.

When a response or stop condition arrives, guarded `--record-outcome` records
the exact alias because replies can arrive out of send order. It accepts
`replied`, `pilot-requested`, `price-objection`, `existing-solution`,
`not-a-fit`, or `do-not-contact` only after contact, requires explicit
confirmation that a human observed the outcome, preserves approval and contact
history, and clears any pending follow-up. A generic reply may later be refined
to a specific terminal outcome, but the refinement date cannot precede the
recorded reply date and does not replace that first observation date. New
outcomes retain
their actual observation date in `outcome_on`; legacy nine-column ledgers
remain readable, and older outcomes without dates are reported as undated
rather than assigned invented history.
The required `--outcome-on` can precede the ledger's `--as-of` audit date, so a
later operating session can preserve an earlier human observation; an outcome
after the audit date is rejected. The action sends nothing and schedules
nothing. Contact and
follow-up receipts now preserve the exact alias and private ledger path in a
shell-quoted outcome handoff. Separate required recording-date,
observation-date, and status placeholders stop an unchanged command before
ledger access, keeping the operator responsible for the observed evidence. A
generic reply receipt similarly carries one exact refinement handoff limited
to `pilot-requested`, `price-objection`, `existing-solution`, `not-a-fit`, or
`do-not-contact`; terminal outcomes emit no next command.
Private `pilot-requested` is an operator signal, not a public funnel event; the
prospect must still submit pilot intake, and booked revenue requires the
human-applied `pilot-paid` label.
Private `price-objection` is human-observed willingness-to-pay evidence, not a
lead or sale. Report schema 10 gives it a dedicated `price_objections` count
and closes the contact cadence without exposing response text.
Private `existing-solution` is human-observed substitute evidence, not a lead
or competitive-loss claim. Report schema 11 gives it a dedicated
`existing_solution_objections` count and closes the cadence without retaining
response text, the substitute identity, or inferred intent.
Outcome receipt schema 4 carries the existing GitHub intake with
`Direct outreach` visibly prefilled in both JSON and default text, but only for
that private pilot-interest status. Other outcomes expose no conversion link.
The tool does not open or submit the form, and the prospect retains control of
the editable source answer and public submission.

Every approval, decline, contact, follow-up, and outcome write now carries the
SHA-256 revision of the private ledger it validated. The staged replacement
uses an owner-only adjacent operating-system lock, compares that revision under
the lock, and refuses a concurrent or stale commit with a retry instruction.
This prevents a later process from silently restoring an earlier status and
undercounting real outreach attempts; the lock file contains no prospect data.
The same locked commit point revalidates the live ledger's regular-file type and
owner-only POSIX file and parent permissions. A late privacy change stops the
mutation, preserves the current bytes, and removes the staged replacement
instead of carrying a permissive mode into private operating evidence.

Rollout bundles carry a stable, non-sensitive metadata contract so a pilot lead
can summarize bundle-reported readiness, policy failures, violations, worktree
state, and attention across repositories without sending source code to Repo
Scout. Counts are private by default; repository details require explicit opt-in.
Normalized policy fingerprints let the operator verify that complete schema-2
bundles used identical enforced rules, while Git commit IDs identify the exact
revisions scanned. Neither field proves evidence age or authenticity, so paid
rollout support still includes controlled evidence handling and CI operations.
The copy-ready CI gate now produces one aggregatable rollout bundle on every
completed scan, including policy failures. This turns weekly CI use and
cross-repository policy reuse into evidence a pilot operator can review without
a Repo Scout-hosted database.

Future tagged releases aggregate two temporary schema-2 bundles through the
installed wheel before provenance attestation. The check requires one
ready-for-CI repository, one remediation-required repository, complete policy
fingerprint and Git commit coverage, and verified shared policy identity. It
also proves the default summary omits repository IDs, fingerprints, commits,
and evidence paths while explicit details remain available, and rejects a
duplicate repository, a presentation-unsafe repository identity, or a
control-bearing duplicate or unknown JSON key before emitting a report.
Malformed evidence under a control-bearing filename must also retain one-line
escaped path context. The check additionally generates one repository ID
containing Markdown backticks through the packaged primary command and requires
exact metadata plus one contained visible code span. Synthetic bundles validate
the distribution contract; they are not pilot usage or customer evidence.

The hosted offer now leads with this cross-repository outcome: complete policy
and commit identity coverage, shared-policy verification, and visible
remediation work. Its example is labeled bundle-reported and the application
CTA repeats the $299 price, so purchase-readiness responses follow a concrete,
price-disclosed offer rather than a generic request for contact.

The first shared-policy release supports required files, repository file and
byte limits, and clean Git enforcement through a strict TOML file that can be
committed once and reused in CI.

## Conversion Path

1. A developer downloads the portable release and adopts the free CLI for handoffs or reviews.
2. The team initializes and commits the closest starter policy.
3. The team copies the GitHub Actions gate into its first repository.
4. The team records a passing rollout bundle and needs the same standard across repositories.
5. The engineering lead reviews the hosted offer and submits a qualified pilot request.
6. The engineering lead buys a pilot for shared policies and rollout support.

The current request form is a public GitHub issue and warns teams not to share
source code or sensitive details. A private intake channel is deferred until
pilot demand validates the additional infrastructure.

## Validation Milestones

- Sell three pilots before building billing or license enforcement.
- At least two pilot teams run Repo Scout in CI weekly.
- At least one pilot policy is reused across three repositories.
- At least one pilot converts to an annual team license.

## Revenue Evidence

Founding-team requests are tracked with cumulative `pilot-*` labels and the
dependency-free `repo-scout-pilot` report. Booked revenue requires the
`pilot-paid` label itself; later labels do not substitute for missing payment
evidence. Qualified leads and written offers remain pipeline, not booked
revenue. Label warnings must be resolved before totals are used in a roadmap or
sales decision.
Pilot issue JSON with duplicate keys is rejected before issue parsing, so
conflicting `labels` fields cannot silently change booked-pilot or revenue
totals. The controlled error identifies only the repeated field and emits no
report.
Saved distribution and pilot reports receive the same duplicate-key boundary
when joined by `repo-scout-growth`. Repeated fields at any nesting depth fail
before commercial arithmetic or bottleneck selection, emit no growth report,
and expose only the report type and escaped field name rather than either
competing value. This prevents the standard JSON last-value behavior from
silently choosing between ambiguous booking or activation evidence; it does
not authenticate a report or prove the underlying public lifecycle labels.
Public pilot issue titles are normalized around surrounding whitespace and
limited to non-empty printable text of at most 1,024 characters. Any remaining
line break, terminal control, bidirectional control, Unicode separator, or
oversized value fails before commercial output without repeating the title.
Issue URLs must be empty or printable text of at most 2,048 characters without
surrounding whitespace and use the same no-echo rejection. This prevents a
request author or edited export from forging revenue or sales-queue lines in an
operator report; it does not qualify a lead, prove willingness to pay, collect
payment, or record revenue.
Unrecognized edited source, readiness, and purchase-criterion answers remain
available in escaped JSON deal fields. Unknown pilot labels remain in escaped
JSON warning fields. Operator-facing warning messages are generic and never
interpolate those values into terminal output.
An issue carrying only unknown pilot labels now emits both taxonomy-repair
warnings and is ignored before source, readiness, purchase-criterion,
qualification, stage, deal, queue, and joined-growth accounting. It therefore
cannot fabricate demand or displace acquisition as the commercial bottleneck.
An unknown extra label still warns when a recognized lifecycle label makes the
underlying request reportable.

Schema-7 through schema-10 joined growth require every detailed deal to carry an
explicit boolean `booked` value and reconcile their total to
`summary.booked_pilots` before computing revenue or selecting a bottleneck.
Pre-payment and untracked stages cannot claim booking evidence, and the paid
stage cannot omit it.
Coordinating only the summary, source, and purchase-criterion aggregates can no
longer turn an offered deal into $299 of booked revenue. Growth also derives
request and booked-pilot counts independently for each detailed source and
purchase criterion. A coordinated aggregate rewrite therefore cannot move
request volume to another channel or buyer criterion. Because schema 7+ uses
one validated $299 price and requires every segment's revenue to equal price
times booked pilots, a coordinated booked-count-and-revenue swap cannot move
payment evidence either. Schema 8 now records explicit boolean `qualified` and
`offered` milestones on every detailed deal, so growth also derives those
counts by source, purchase readiness, and purchase criterion. Schema 7 remains
readable with aggregate qualification and offer progression checks. These
checks establish internal saved-report consistency, not authentication of a
wholly rewritten report, causal attribution, or proof that payment occurred
outside the human-applied `pilot-paid` label.

Schema 9 adds explicit boolean `activated` evidence on every detailed deal and
reconciles its sum to `summary.activated_pilots`. Activation counts only when
both `pilot-paid` and `pilot-active` are present; an active label without
payment and a paid record without the active label remain false. Joined growth
rejects activation on impossible pre-activation stages and requires an active
stage to match payment-backed activation. Terminal converted, lost, and
conflicting records may retain either activation value because their final
stage alone does not prove whether the human-applied active milestone occurred.
Schema-5 through schema-8 reports expose activation as unavailable rather than
zero. These checks preserve the public lifecycle evidence boundary and do not
replace the private delivery acceptance record or customer acknowledgement.
The existing annual-conversion rule remains payment-backed: a paid converted
record that skipped `pilot-active` retains its explicit conversion and
missing-stage warning, but activation remains false and the activation
bottleneck prevents expansion until the lifecycle evidence is reconciled.

Schema 10 adds `activated_pilots` to source, purchase-readiness, and
purchase-criterion totals. Joined growth requires each segment count to remain
within its booked pilots, reconciles every activation segment family to the
global summary, and derives each count independently from the detailed deal
milestone. A globally balanced edit therefore cannot move activation to a more
attractive channel or buyer profile. These rows support directional learning
about which paid teams reach delivery; they do not establish causal
attribution, authenticate a rewritten report, or replace private acceptance
evidence. Schema 9 remains readable with global activation available and
segment activation attribution unavailable.

Joined growth now turns that aggregate activation gap into an exact,
public-safe work queue. For schema-9+ evidence it derives one action from every
validated booked-but-unactivated detailed deal, carrying only the issue number,
terminal or paid stage, normalized source, readiness, purchase criterion, and a
canonical delivery or reconciliation instruction. Live paid delivery comes
before terminal reconciliation, and completed activation removes the record.
Schemas 5 through 8 expose the queue and action count as unavailable rather
than inventing zero work. This gives an operator a bounded paid-fulfillment
list without publishing titles, repository standards, customer identity,
contracts, payment details, acknowledgement, closeout, or refund evidence. It
does not verify private delivery, apply `pilot-active`, contact a customer,
collect payment, or record a real activation.

Joined growth also consumes the complete schema-7+ purchase-readiness table
instead of leaving that willingness-to-pay signal outside the review. It
requires the exact public readiness taxonomy, reconciles every readiness funnel
total and all five readiness summary counters to source totals, and derives
request, booking, conversion, and loss attribution from each detailed deal's
recognized readiness value. The validated rows appear in both JSON and text
growth output, so a coordinated aggregate edit cannot turn approval-dependent
or exploratory demand into ready-buyer evidence. Schema 8 additionally derives
qualification and offer progression for each readiness segment from detailed
milestones. Readiness remains self-reported intent, not payment, authenticated
evidence, or proof of willingness to pay.

Direct callers may change the pilot target and inactivity threshold only with
genuine positive integers. Booleans, floats, and numeric strings fail before
issue parsing. Schema-7+ pilot pricing is additionally bound to the $299 price
named in public readiness and commercial-fit answers. Another configured price
fails before issue parsing, booked-revenue arithmetic, or sales actions, and
joined growth applies the same boundary to saved schema-7+ evidence. Older
aggregate schemas remain readable, but current public intake cannot be used as
evidence of willingness to pay a different price.

Resolved annual conversions require the same explicit payment milestone. A
`pilot-converted` issue without `pilot-paid` remains visibly converted and
retains its skipped-stage warning, but contributes zero annual conversions to
the summary, source, readiness, purchase-criterion, and joined growth totals.
This prevents one unsupported conversion from being hidden by another issue's
legitimate payment inside an aggregate segment. Schema-7 joined growth derives
that total again from detailed deals, counting only records whose stage is
converted and whose explicit booking evidence is true. It also derives resolved
losses only from the detailed lost stage. Coordinated summary, source, and
purchase-criterion edits therefore cannot manufacture retention evidence or
erase a detailed loss from the global outcome totals. Growth also requires each
detailed source and purchase criterion to use the public intake taxonomy, then
derives conversion and resolved-loss counts for both segment tables. A saved
report cannot move a converted website request to outreach, or move a loss
between purchase criteria, merely by swapping globally balanced aggregate
outcomes. This protects directional channel and buyer-learning evidence; it
does not prove that a source caused the outcome.

An issue carrying both `pilot-converted` and `pilot-lost` remains a visible
terminal conflict. It retains booked revenue when the cumulative paid milestone
is present, but contributes to neither resolved conversion nor resolved loss
totals until the labels are corrected. This prevents one ambiguous customer
record from overstating both outcomes. Joined growth preserves that exclusion
when it reconciles detailed terminal outcomes. These checks establish internal
saved-report consistency; they do not authenticate a wholly rewritten report
or prove an external payment or loss event.

Future tagged releases exercise that accounting contract through the installed
wheel before provenance attestation. A temporary synthetic export proves an
offer remains at $0, one paid pilot books exactly $299 toward the $897 target,
both requests retain target-profile and source segmentation, and only the open
pre-payment request enters the sales queue. Repository-standard free text stays
out of JSON and operator output. These fixtures validate distribution behavior;
they are not real requests, payments, or revenue evidence.

The repository also audits the seven live GitHub lifecycle labels against one
tested maintainer contract. Its repair mode may create missing labels or restore
their color and description, but it never deletes an unexpected `pilot-*`
label. A dedicated read-only GitHub check catches drift before the public issue
form and revenue reporter silently disagree. Passing this check proves intake
configuration readiness only; it does not create a lead or establish demand.
That hosted check now has a dedicated fail-closed workflow contract covering
both trigger blocks, read-only permissions, immutable actions, bounded runtime,
the exact workflow, intake-label, and delivery tests, test-before-live-audit
ordering, and the absence of repair, secrets, or failure masking. The workflow
runs the complete pilot-funnel and joined-growth behavioral suites before the
live label audit, including direct proof that annual conversion requires
explicit payment and that unsupported post-payment stages require repair.
Both trigger blocks watch the two commercial producers, both suites, and the
funnel revenue fixture, while `DISTRIBUTION.md` remains watched because the
delivery test reads it. Weakening conversion evidence, commercial
prioritization, or their protection therefore selects the same hosted check.
This protects conversion infrastructure; it does not submit, qualify, or
contact a lead and does not create payment or revenue evidence.

Open lead, qualified, and offered issues inactive for seven UTC calendar days
appear in the funnel's follow-up list. This is an operating prompt based on
GitHub issue activity, not evidence that a buyer was or was not contacted.

The intake records one required, self-reported discovery channel. Funnel source
totals connect those channels to qualification, offers, booked revenue,
conversion, and loss. Missing or edited legacy answers remain explicit warning
buckets. This is directional acquisition evidence, not proof that a single
touchpoint caused a purchase.

The intake also requires one public purchase-readiness answer: ready to buy the
$299 pilot, needs internal approval, or exploring before requesting budget.
Funnel totals connect each readiness state to qualification, offers,
booked revenue, conversion, and loss. Readiness is self-reported intent, not
cash; only an explicit `pilot-paid` label counts as booked revenue.

The intake requires one primary purchase criterion covering policy fit,
cross-repository rollout, leadership or audit evidence, privacy and security,
implementation capacity, commercial fit, or other. Schema-7 funnel totals
connect that criterion to qualification, offers, payment, conversion, and loss.
This creates structured customer learning before outreach scales, but a stated
criterion is not a moat or proof of demand. Repeated paid outcomes must show
which policy packs, evidence patterns, and rollout playbooks are defensible.

Schema-7+ reporting also turns every open pre-payment request into a prioritized
sales action. Ready buyers surface first, approval-dependent buyers receive an
approval-oriented action, exploratory buyers receive a proof or decision-criteria
action, and unclear answers require clarification. Funnel stage and issue age
order deals within those groups. A ready buyer receives normal terms or payment
guidance only when the normalized provider is GitHub Actions, qualification is
target-profile, and the requested scope fits within 10 repositories. Recognized
non-GitHub providers require the existing private integration decision first,
while missing, no-response, edited, or ambiguous provider evidence requires
clarification. For GitHub Actions, incomplete or outside-target qualification
requires review and a larger target request requires a first-10-repository
scope before commercial advancement. This changes only the pilot queue's next
action: target-profile classification, ordering, counts, human-applied labels,
and booked-revenue semantics remain unchanged. Because private decisions are
not public evidence, the queue cannot infer that they were completed.
The aggregate growth review also lacks deal-level actionability. When it reads
schema-7+ reports and open sales actions exist, its offer, payment, and open
pilot-target recommendations therefore defer to the qualification-aware queue
instead of issuing a second commercial instruction. The offer-stage handoff
still carries the report's validated pilot price. Growth first reconciles the
reported action count with the embedded queue and verifies every queued stage,
readiness, qualification status, repository scope, provider, price-derived
action, and exact next action. A saved schema-7+ report with a provider-blind,
scope-blind, or stage-skipping action fails closed instead of acquiring new
meaning from its version number. Queue identity and stage must also reconcile
exactly to every open pre-payment deal. Readiness and the action-driving
qualification fields, priority, and issue age must match that canonical deal.
The queue sequence must reproduce the funnel producer's shared readiness,
stage, age, and issue-number order before growth can defer to it. Detailed deal
age must equal the canonical `follow_up.as_of` date minus its canonical UTC
`updated_at`, and the queue timestamp must match that detailed evidence.
Missing timestamps retain null age, future activity retains negative age, and
source offsets remain valid after producer normalization to UTC. Detailed deal
stages must reproduce `by_stage`. Schema 8 additionally derives qualification
and offer progression by source, purchase readiness, and purchase criterion
from explicit detailed milestones. Deleting an entry and changing the saved
count, coordinating false ages to place a newer peer ahead of an older buyer,
self-authorizing a copy-ready provider, or escalating both detail and queue
stage without changing aggregate evidence therefore fails.
During qualification through an open pilot target, a valid but empty schema-7+
queue is not treated as a legacy report: cumulative qualification, offer,
payment, and loss history remains visible, but growth states that no open
pre-payment deal exists and recommends replenishing the queue instead of
inventing commercial work. Open untracked or conflicting lifecycle evidence,
and open active or converted stages without booked payment evidence, take
repair precedence over another active deal at those stages. This prevents a
live buyer with contradictory post-payment evidence from disappearing behind a
queue-replenishment instruction. Acquisition and post-target retention keep
their existing evidence priorities. Older pilot schemas retain their existing
aggregate recommendations. The queue is an operating aid, not an automated
decision, and it neither sends outreach nor records payment.

Schema 7+ also verifies the required application scope before an operator relies
on a qualification label. It normalizes team size, repository count, and CI
provider, records only whether the requested standard is present, and marks the
request as target, outside-target, or incomplete with explicit review reasons.
Teams above the 10-repository pilot limit are scoped to a first-10 subset rather
than discarded. Joined growth validates status, repository scope, and CI
provider on every detailed deal, including closed records, then derives its
complete, target-profile, review-required, and subset counts from those deals.
Coordinated edits to summary counters alone cannot hide out-of-profile or
incomplete demand. This is qualification evidence, not an automated buying
decision, and repository-standard free text is not repeated in reports.

## Product Filter

New work must improve acquisition, activation, conversion, or retention for the
paid team workflow. Generic features that do not strengthen that path stay out
of the near-term roadmap.

The 1,000-commit delivery goal does not weaken this filter. Commit count is a
measure of sustained execution; revenue evidence remains the measure of product
success.

Distribution work must reduce the path from discovery to a successful local
scan, team CI activation, or a qualified pilot request. Portable and wheel
downloads, repository traffic, and source attribution are distribution evidence;
they do not replace booked revenue. The supported channel contract and metrics
live in `DISTRIBUTION.md`.

The local `repo-scout-distribution` report audits public release completeness
and separates portable, wheel, source, checksum, and unknown artifact requests.
Those counts can include Repo Scout's own CI, maintainer checks, and retries, so
they are directional reach evidence only. They must be reviewed beside pilot
source and purchase-readiness reports rather than presented as users or sales.

Weekly schema-2 baselines turn cumulative release counters into signed channel
movement and flag evidence resets or removals. These deltas make distribution
experiments comparable over time, but they retain the same CI and maintainer
confounders and therefore remain directional until a buyer self-reports a source
or enters the paid funnel.
The distribution producer rejects duplicate keys at every depth of both raw
release exports and saved baselines before calculating artifact totals or
signed movement. Controlled failures emit no report and expose only the input
type and escaped repeated key, not either competing count. This closes standard
JSON last-value ambiguity; it does not authenticate GitHub evidence, make
request counts unique, or turn them into demand or revenue.
The shared producer parser also requires every current and baseline asset name
to be non-empty printable text. Line, terminal, Unicode-separator, and
bidirectional controls fail with a generic location-only error before artifact
classification, request totals, warnings, or signed movement. Ordinary
printable Unicode names remain exact. This protects operator-facing
distribution evidence; it does not authenticate a GitHub export, make requests
unique, or establish demand, payment, or revenue.

The latest 2026-07-30 UTC public checkpoint records 403 cumulative primary
artifact requests across 55 contract-complete releases: 41 portable and 362
wheel. That is 135 more primary requests than the 2026-07-22 checkpoint. The
two new releases account for 132 requests; `v0.3.51` alone records 108 wheel
and 108 manifest requests but only one portable and one source request. The
period added 130 wheel and 127 manifest requests but only 5 portable and 5
source requests. That near-paired, wheel-heavy shape is consistent with Repo
Scout's own release, verification, pinning, and CI activity, not evidence of
130 prospects. The checkpoint still records zero pilot requests, zero outreach
attempts, and $0 booked revenue, so acquisition remains the honest bottleneck
and the next revenue action is source-identifiable outreach.

The refreshed owner-visible 14-day GitHub traffic checkpoint ending 2026-07-16
records 3 views from one unique repository viewer, 293 unique cloners, and 962
clone events. Compared with the overlapping window ending 2026-07-11, views
rose by 2 without another unique viewer while clone events rose by 652 and
unique cloners by 174. Rolling windows are not additive. The widening
clone-to-view gap is consistent with CI, hosting, and maintainer automation and
cannot be presented as 293 users, installs, or qualified prospects. Together
with zero pilot requests, it confirms that acquisition remains the honest
bottleneck.

The dependency-free `repo-scout-growth` review places those signed deltas beside
schema-5 through schema-10 pilot source, qualification, offer, payment,
activation, and revenue totals. It names one current commercial bottleneck and
next action so weekly roadmap work responds to the paid funnel instead of
optimizing raw download counts. For schema 9+, booked-but-unactivated delivery
takes precedence over another pilot sale, retention, or expansion. Missing
distribution measurement still takes precedence, and older schemas retain their
prior bottlenecks without invented activation counts. Input warnings and missing
or ambiguous source answers remain visible.
Schema 10 also shows which source, readiness state, and purchase criterion
reached payment-backed activation while rejecting attribution that does not
match detailed deals.
Because release requests are neither unique people nor attributable sessions,
the review never computes a download-to-lead conversion rate or assigns request
movement to a discovery source.

The installed commercial smoke test now processes baseline and current raw
GitHub release exports through the built wheel's public
`repo-scout-distribution` command before feeding the resulting signed
six-request delta and its synthetic schema-10 pilot report through the public
`repo-scout-growth` command. The pilot report also comes from the installed
`repo-scout-pilot` command. Its two requests deliberately separate a
lead-stage false/false qualification-and-offer history from a paid-stage
true/true history across source, purchase readiness, and purchase criterion.
That paid-only record must remain explicitly unactivated. The installed growth
command must select the activation bottleneck and reject a tampered lead
milestone, activation without payment, or a globally balanced source-activation
rewrite with exit code 2 and no JSON report.
Release attestation requires all three entry points to exist and execute the
complete artifact contract, two attributed target-profile requests, one $299
booking, zero synthetic activations, and the delivery-first activation action
while retaining both commands' request-not-customer boundaries. Duplicate
release assets and a primary delta that does not equal portable plus wheel
movement must fail without a report. These fixtures prove packaged entry-point,
parsing, joining, and validation behavior, not adoption, attribution, demand,
payment, activation, or revenue.

The release boundary applies the same installed-command rule to the rest of
the paid workflow. Policy recommendation, bootstrap, receipt verification, and
enforcement run through `repo-scout-policy` and `repo-scout`; the guarded human
outreach lifecycle runs through `repo-scout-outreach`; and cross-repository
evidence runs through `repo-scout-rollout`. Each harness receives the exact
wheel installation directory and fails cleanly if a required command is absent
or non-executable. Source tests retain direct module execution for speed. This
proves packaging routes customer commands to tested behavior; it does not prove
customer activation, outreach attempts, pilot demand, or revenue.

Every wheel command and the portable zipapp also exposes the same standard
`--version` identity. Tagged releases compare each installed command's output to
the tag before provenance attestation, giving pilot operators and support logs a
fast way to diagnose stale or mixed installations without scanning a repository
or inspecting package metadata. Version output proves installed package
identity only; it does not prove artifact authenticity, policy activation,
customer usage, or revenue, which retain their separate evidence contracts.

Schema-2 growth reviews also expose ordered schema-6+ purchase-criterion outcomes
and reconcile every criterion aggregate to the same source-reported deals and
revenue. Schema-5 reports mark criterion evidence unavailable instead of zero.
Missing and ambiguous criteria remain warnings. Criteria are self-reported
evaluation priorities, not attribution, willingness to pay, or proof of a moat;
only repeated paid outcomes can show which operational knowledge is defensible.
