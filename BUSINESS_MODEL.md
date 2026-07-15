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

The copy-ready CI gate consumes those releases with independent digest and
provenance checks. This makes the free activation path closer to the paid pilot
deployment model: teams can evaluate a repeatable, auditable install before
buying cross-repository rollout support.

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

Policy version 2 can reject tracked or unignored sensitive paths without
failing on properly ignored local copies. A founding-team custom pack can use
the team's agreed credential, generated-secret, and local-configuration paths.
This is useful free CI enforcement; the paid work remains agreeing on the
right rules and rolling the same reviewed policy across uneven repositories.
Versions 1 and 2 remain readable so verified CI upgrades can be staged safely.
The dogfood and copy-ready gates now install the independently verified
`v0.3.40` wheel, so v4 policies can run locally and in CI
without source checkout, mutable package resolution, or a team-managed secret.
Maintainer pin upgrades now preflight and update the dogfood workflow,
copy-ready customer example, and contract test as one reviewed change, reducing
the chance that distribution trust metadata diverges between internal and
customer activation paths.

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

An AI can recreate a scanner, but that is not the commercial claim being
tested. The active website experiment presents the paid outcome in plain
language: help agreeing on one rulebook, installing it across uneven projects,
and keeping reviewable evidence useful without uploading private code. The
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
self-reported intake and paid-stage labels affect commercial validation.

Machine-readable offer data keeps the free and paid layers distinct. The
current zipapp is represented as a $0 `SoftwareApplication`; the founding-team
pilot is a separate $299 `Service` with the same duration, repository limit,
audience, and local-code boundary shown to visitors. No review or rating data
is published because none has been earned. Search presentation remains outside
the revenue ledger until a buyer submits intake and reaches a paid stage.

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
The committed schema-3 baseline contains only aggregate counts. All five remain
`drafted`: approved messages, attempted outreach, replies, pilot requests, and
revenue are still zero until a human reviews and sends each message through its
published business channel.

The operator can now request one deterministic `--review-next` checklist. It
names only the next private alias and permitted channel, reports qualification
counts instead of URLs, and prints five unchecked criteria covering observation,
recipient, price and scope, local-code handling, and opt-out behavior. The mode
does not expose draft text, edit status or dates, approve a message, or send it.
Its output stays private and cannot be used as a counts-only public baseline;
review readiness remains operator preparation rather than demand or revenue.
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

After a human completes those checks, guarded `--approve-next` can record the
decision without hand-editing CSV. It requires the exact next alias, an explicit
review date, and a confirmation flag; validates all rows before and after; and
atomically preserves file permissions while changing only status and approval
date. The receipt excludes evidence and review dates. Approval still sends
nothing, creates no contact or follow-up date, and is not an attempt, lead,
pilot request, or revenue event. Private text output carries each selected
alias, date, confirmation flag, and shell-quoted ledger path into a complete
next command. This removes manual command reconstruction without completing a
review, sending a message, or treating operator activity as demand.

When the human instead decides a draft must not be sent, guarded
`--decline-next` requires the exact same next alias and an explicit no-send
confirmation. It atomically changes only status to `review-declined`, preserves
the private file boundary, reports the privacy-safe remaining-draft count, and
records no action date. It emits the next review command only while another
draft remains and ends truthfully when the bounded queue reaches zero. The
aggregate report counts this as closed before contact and never as an attempt.
This keeps the acquisition queue moving without converting negative review
judgment into an approval or a false outreach event.

After a human sends that approved message, guarded `--record-contact` records
the exact next approved alias with an explicit send date and confirmation flag.
It retains approval evidence, atomically changes only status, contact date, and
the exact seven-day next action, and produces a private receipt that omits
evidence and approval dates. The follow-up date makes send timing inferable, so
the receipt stays private. The tool does not deliver the message or an automatic
follow-up. A recorded contact enters outreach-attempt operations, but still is
not a lead, pilot request, payment, or revenue.

After a human sends the one allowed follow-up on or after day seven, guarded
`--record-follow-up` records the earliest due contacted alias. It retains the
approval and initial-contact evidence, atomically changes only status,
follow-up date, and next action, then clears that next action so no second
follow-up is scheduled. Early, future, and out-of-order records are rejected.
The alias-only receipt remains private, and the tool sends nothing. A follow-up
is still outreach operations, not a new prospect, lead, pilot request, payment,
or revenue event. The contact receipt's next command uses the calculated due
date for both reporting and follow-up recording, avoiding calendar drift while
leaving the actual send and confirmation under human control.

When a response or stop condition arrives, guarded `--record-outcome` records
the exact alias because replies can arrive out of send order. It accepts
`replied`, `pilot-requested`, `not-a-fit`, or `do-not-contact` only after contact,
requires explicit confirmation that a human observed the outcome, preserves
approval and contact history, and clears any pending follow-up. A generic reply
may later be refined to a specific terminal outcome. The action sends nothing
and schedules nothing. Private `pilot-requested` is an operator signal, not a
public funnel event; the prospect must still submit pilot intake, and only paid
stages count as revenue.

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
duplicate repository before emitting a report. Synthetic bundles validate the
distribution contract; they are not pilot usage or customer evidence.

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
dependency-free `repo-scout-pilot` report. Only issues that reach `pilot-paid`
or a later paid stage count toward the three-pilot and $897 initial-revenue
targets. Qualified leads and written offers remain pipeline, not booked
revenue. Label warnings must be resolved before totals are used in a roadmap or
sales decision.

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
cash; only `pilot-paid` or a later paid stage counts as booked revenue.

The intake requires one primary purchase criterion covering policy fit,
cross-repository rollout, leadership or audit evidence, privacy and security,
implementation capacity, commercial fit, or other. Schema-7 funnel totals
connect that criterion to qualification, offers, payment, conversion, and loss.
This creates structured customer learning before outreach scales, but a stated
criterion is not a moat or proof of demand. Repeated paid outcomes must show
which policy packs, evidence patterns, and rollout playbooks are defensible.

Schema-7 reporting also turns every open pre-payment request into a prioritized
sales action. Ready buyers surface first, approval-dependent buyers receive an
approval-oriented action, exploratory buyers receive a proof or decision-criteria
action, and unclear answers require clarification. Funnel stage and issue age
order deals within those groups. The queue is an operating aid, not an automated
decision, and it neither sends outreach nor changes booked-revenue semantics.

Schema 7 also verifies the required application scope before an operator relies
on a qualification label. It normalizes team size, repository count, and CI
provider, records only whether the requested standard is present, and marks the
request as target, outside-target, or incomplete with explicit review reasons.
Teams above the 10-repository pilot limit are scoped to a first-10 subset rather
than discarded. This is qualification evidence, not an automated buying
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

The latest 2026-07-15 UTC public checkpoint records 153 cumulative primary
artifact requests across 44 contract-complete releases: 19 portable and 134
wheel. That is 6 more primary requests than the prior checkpoint: 3 on the new
`v0.3.40` release and 3 additional `v0.3.39` wheel requests. Repo Scout's own
release, verification, pinning, and CI activity materially confound those
counts. The same checkpoint records zero pilot requests, zero outreach attempts,
and $0 booked revenue, so acquisition remains the honest bottleneck.

The owner-visible 14-day GitHub traffic checkpoint adds one unique repository
viewer, 119 unique cloners, and 310 clone events. That extreme clone-to-view
gap is consistent with CI, hosting, and maintainer automation and cannot be
presented as 119 users, installs, or qualified prospects. Together with zero
pilot requests, it confirms that acquisition remains the honest bottleneck.

The dependency-free `repo-scout-growth` review places those signed deltas beside
schema-5, schema-6, or schema-7 pilot source, qualification, offer, payment, and
revenue totals. It names one current commercial bottleneck and next action so
weekly roadmap work responds to the paid funnel instead of optimizing raw
download counts. Input warnings and missing or ambiguous source answers remain
visible.
Because release requests are neither unique people nor attributable sessions,
the review never computes a download-to-lead conversion rate or assigns request
movement to a discovery source.

The installed commercial smoke test now processes baseline and current raw
GitHub release exports through the built wheel's public
`repo-scout-distribution` command before feeding the resulting signed
six-request delta and its synthetic schema-7 pilot report through the public
`repo-scout-growth` command. The pilot report also comes from the installed
`repo-scout-pilot` command. Release attestation requires all three entry points
to exist and execute the complete artifact contract, two attributed
target-profile requests, one $299 booking, the open $897 pilot target, and the
`pilot_target` bottleneck while retaining both commands' request-not-customer
boundaries. Duplicate release assets and a primary delta that does not equal
portable plus wheel movement must fail without a report. These fixtures prove
packaged entry-point, parsing, joining, and validation behavior, not adoption,
attribution, demand, or revenue.

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
