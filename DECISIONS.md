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

## 2026-07-09: Make Markdown a First-Class Output Format

Markdown output is generated from the same deterministic snapshot used by text and JSON modes. It favors copy-pasteable summary bullets and tables for handoffs and pull requests while preserving JSON as the machine-readable contract.

## 2026-07-09: Keep Attention Checks Additive and Tunable

Attention findings are added as a separate status-and-items field so existing snapshot consumers can ignore them safely. Large-file warnings use a documented 100,000-byte default and a CLI override because repository size expectations vary by project.

## 2026-07-09: Compare Saved JSON Snapshots

Snapshot comparison accepts JSON files produced by the existing `--format json` mode. It returns explicit numeric deltas and added or removed entries, keeps the original snapshots untouched, and supports text, JSON, and Markdown output so the same comparison can serve both agents and human handoffs.

## 2026-07-09: Protect Direct Report Writes

`--output` refuses to replace an existing file unless the caller also passes `--force`. This keeps handoff reports from being silently overwritten while retaining an explicit escape hatch for repeatable automation.

## 2026-07-10: Version the Snapshot Contract

Every new snapshot declares schema version 1. Comparison treats missing schema metadata as version 1 so existing saved files remain usable, while an explicit version change appears as a comparison finding for future migrations.

## 2026-07-10: Reject Unsupported Snapshot Versions

Comparison accepts the current schema and metadata-free legacy snapshots, but rejects any other explicit version before reading its fields. This prevents a future format from being misreported as a valid comparison.

## 2026-07-10: Bound Path-Level Comparison Details

Snapshots retain the first 500 sorted paths and reports show at most 50 added or removed paths. Counts and truncation metadata make the result honest for large repositories without turning a comparison report into a full file manifest.

## 2026-07-10: Free Core, Paid Team Policies

The local scanner, reports, comparisons, and basic CI gate remain free to maximize adoption. Revenue will come from a $299 founding-team pilot centered on shared policies, CI rollout support, and one custom policy pack. Billing and license enforcement wait until three teams have paid for the pilot.

## 2026-07-10: Emit Reports Before Failing CI

`--fail-on-attention` always renders or writes the requested report before returning exit code 5. This preserves the evidence needed to fix a failed CI job while giving automation a stable failure signal.

## 2026-07-10: Count Meaningful Commits, Not Activity

The project targets 1,000 commits, but only coherent improvements that pass tests and reach `origin/main` count. Empty commits and artificial change splitting are prohibited because the commit target is a persistence mechanism, not a substitute for product or revenue progress.

## 2026-07-10: Make Team Policies Strict and Versioned

Paid-team policy files use TOML with an explicit version and a closed set of supported keys. Invalid values, unsafe required-file paths, unknown keys, and unsupported versions fail before scanning so configuration mistakes cannot silently weaken enforcement. Policy violations are reported before the CLI returns exit code 6, distinct from the free attention gate's exit code 5. Using Python's standard-library TOML parser raises the minimum supported Python version to 3.11 while preserving the no-runtime-dependencies constraint.

## 2026-07-10: Convert Pilot Interest Without New Infrastructure

The hosted companion presents the implemented policy capability before asking for a $299 pilot request. Intake uses a structured GitHub issue form so the project can validate demand before building billing, authentication, or a lead database. The form and CTA explicitly warn that requests are public and must not contain source code or sensitive details. A private sales channel should replace it once pilot volume or buyer feedback justifies the infrastructure.

## 2026-07-10: Make CI Examples Auditable and Repeatable

The GitHub Actions policy gate grants only read access, disables persisted checkout credentials, and pins third-party actions by full commit SHA. External teams run Repo Scout from an isolated checkout at a previously tested source commit until a package release channel exists, avoiding package installation and mutable build dependencies. Reports are written outside the target checkout and replaced explicitly so repeated scans do not dirty the repository they enforce. The workflow always publishes available evidence to the job summary and a short-lived artifact, including after policy exit code 6.

## 2026-07-10: Count Cash, Not Optimism

Pilot issues use cumulative lifecycle labels so funnel history remains auditable. A written offer is pipeline but not revenue; booked revenue starts only at `pilot-paid` and remains historical if a paid pilot is later lost. The reporter consumes an exported JSON array instead of calling GitHub, keeping credentials and network behavior outside the accounting logic. It warns on skipped stages and conflicting terminal labels rather than silently forcing ambiguous issues into a clean funnel.

## 2026-07-10: Package Adoptable Policies, Sell Customization

Free starter profiles encode only common repository manifests, bounded size, and clean CI state. They are packaged resources with an explicit public registry, exact TOML inspection, stable JSON discovery, and overwrite-safe initialization. Teams review and commit a profile before enforcement, then add standards they already follow. The paid pilot remains differentiated by cross-repository rollout support and a custom policy pack rather than by withholding a usable starting point.

## 2026-07-10: Treat Issue Inactivity as a Follow-Up Prompt

The pilot funnel measures whole UTC calendar days since GitHub's `updatedAt` date and only flags open pre-payment stages. An explicit report date makes audits reproducible, while the current UTC date remains the convenient default. Issue activity is not proof of customer contact because comments and label edits also refresh it. Missing, future, and closed-without-loss records remain warnings and never become guessed follow-up tasks.

## 2026-07-10: Release From Version-Matched Tags With Provenance

Paid pilot teams need an installable artifact whose origin can be checked without trusting a source checkout. Repo Scout releases exactly one wheel and one source distribution when a semantic-version tag matches both package version declarations and points to a commit on `main`. The build uses hash-locked tooling, immutable action pins, a clean-environment command smoke test, deterministic checksums, and GitHub build-provenance attestations before creating the release. Checksums detect changed bytes but do not authenticate origin on their own. PyPI publishing remains deferred until customer demand justifies another distribution channel and its credentials.

## 2026-07-10: Attribute Revenue With A Closed Self-Reported Taxonomy

The public pilot form asks every new lead to choose one discovery channel from a small, stable list. The funnel reads that generated issue-body field and connects each source to qualification, offers, booked revenue, conversion, and loss. Legacy issues without an answer remain `unattributed`; edited or duplicate answers remain `unknown` and produce warnings. This preserves auditability without cookies, tracking pixels, or hosted analytics. Source totals are directional evidence for outreach decisions, not proof that one touchpoint caused a purchase.

## 2026-07-10: Bootstrap Customer CI From A Fully Pinned Release

Now that Repo Scout has a provenance-attested release channel, customer CI no longer needs a second source checkout or `PYTHONPATH`. The copy-ready gate pins the release version, source commit, and wheel digest independently; checks the published manifest; verifies the exact signer workflow, tag, and GitHub-hosted build; and installs the wheel without dependencies in runner-temporary storage. The protected repository remains untouched. Repo Scout's own policy workflow uses the same path so every push exercises the customer bootstrap. Release-pin upgrades must change version, source commit, and wheel digest together after review.

## 2026-07-10: Separate Observed Rollout Evidence From Team Commitments

First-repository onboarding extends the existing Markdown policy report instead of introducing a separate state store. `--rollout-checklist` checks only facts the local scan can establish: policy evaluation, Git presence, worktree cleanliness, and attention findings. Review, ownership, required-check activation, elapsed CI usage, and next-repository enrollment always remain unchecked team actions. A failing policy still writes remediation evidence before exit code 6. Readiness is deterministic and timestamp-free, and the report warns operators through documentation that paths and violation details belong in access-controlled systems for private repositories.

## 2026-07-10: Aggregate Validated Local Evidence Without A Rollout Database

Each Markdown rollout bundle ends with a visible schema-1 JSON block containing a required logical repository ID and only the policy, Git, readiness, and attention fields needed for cross-repository operations. Implicit directory names are rejected because they collide easily. `repo-scout-rollout` validates duplicate JSON keys, closed fields, exact types, supported schema, and internal consistency before producing order-independent text or JSON totals. Duplicate repository IDs fail instead of double-counting a repository. Counts-only output is the privacy default; `--details` explicitly reveals repository IDs, branches, and input paths. Results are labeled bundle-reported because validation is neither a signature nor proof of freshness or identical policy content.

## 2026-07-10: Identify Policy Semantics And Scanned Revisions

Schema-2 rollout evidence adds a SHA-256 fingerprint of the normalized policy version and effective repository rules plus the exact checked-out Git object ID when available. Policy source paths, TOML key order, required-file ordering, and an explicit no-op `require_clean_git = false` do not affect the fingerprint. A schema-2 bundle cannot report `ready-for-ci` until an initial commit exists. The aggregator validates direct library inputs and verifies shared policy only when at least two bundles all contain one matching fingerprint; schema-1 evidence remains accepted but contributes no identity coverage. Counts-only output reports coverage without exposing fingerprints or commits, while `--details` reveals them. These identities support auditable paid rollouts but are not signatures, timestamps, or proof that a bundle is fresh.

## 2026-07-10: Publish Rollout Bundles From Verified Customer CI

The copy-ready and dogfood policy workflows install the independently pinned, provenance-verified `v0.3.1` wheel and generate schema-2 evidence using GitHub's stable `owner/repository` identity. Output remains outside the protected checkout, is appended to the access-controlled job summary, and is uploaded as `repo-scout-rollout-evidence` for 14 days after both passing and failing policy scans. The required-check name remains stable. This gives paid-pilot operators repeatable cross-repository evidence without granting write permissions, adding secrets, or operating a hosted rollout database.

## 2026-07-10: Measure Purchase Readiness Without Counting Intent As Revenue

The public pilot form requires one closed purchase-readiness answer: ready to purchase the $299 pilot, needs internal approval, or exploring before requesting budget. The schema-4 funnel connects those self-reported states to qualification, offers, booked revenue, conversion, and loss while preserving missing and unknown buckets for legacy or edited issues. Duplicate or unrecognized answers produce warnings instead of guesses. Readiness helps prioritize outreach and test price acceptance, but booked revenue still begins only at `pilot-paid`.

## 2026-07-10: Sell The Cross-Repository Outcome

The hosted offer demonstrates aggregate rollout evidence instead of repeating the free single-repository policy check. It shows complete policy-fingerprint and scanned-commit coverage, matching shared-policy verification, and a remediation-required repository because paid value comes from operating one standard across uneven repositories. The example remains explicitly bundle-reported and does not claim freshness or authenticity. The primary CTA names the $299 price before sending a buyer to public intake so the resulting purchase-readiness answer measures a disclosed offer.

## 2026-07-10: Turn Declared Readiness Into An Auditable Sales Queue

Every open pre-payment deal receives a deterministic priority and stage-specific next action. Declared ready buyers rank first, approval-dependent buyers second, exploratory buyers third, and missing or edited answers fourth. Within each priority, later funnel stages rank before earlier ones, followed by issue age and issue number. The queue never advances labels or treats intent as revenue, and the existing stale list remains a separate measure of GitHub issue inactivity. This gives the operator a repeatable conversion cadence without adding a CRM, private data store, or automated outreach.

## 2026-07-10: Distribute The Free CLI As One Verified File

The free primary CLI ships as a versioned Python zipapp so a developer can try Repo Scout without cloning the repository, installing a package, or changing a Python environment. The portable artifact is built from the same tagged source as the wheel, excludes build residue, runs directly in release smoke tests, appears in the deterministic checksum manifest, and receives the same provenance attestation. The wheel remains the complete command distribution. PyPI is deferred because the normalized `repo-scout` name belongs to an unrelated package; a future launch must use a distinct distribution name and trusted publishing without changing the CLI command.

## 2026-07-10: Measure Artifact Requests Without Calling Them Users

Distribution reporting consumes an exported GitHub release array and performs no network calls itself. It audits exact versioned artifacts, requires the portable zipapp only from `v0.3.4`, and separates portable and wheel primary requests from source, checksum, and unknown requests. GitHub download counts are cumulative requests: Repo Scout's own CI downloads verified wheels, maintainers verify releases, and retries can increment counts. The report therefore never labels requests as unique installs, active users, pilot demand, or revenue. Actual commercial evidence continues to come from self-reported source, funnel progression, and payment labels.

## 2026-07-10: Compare Immutable Distribution Evidence Over Time

Schema-2 distribution reports accept a prior schema-1 or schema-2 report as a baseline and produce signed request deltas by channel. New releases start from zero, while removed releases contribute negative movement and a warning. A counter decrease or removed asset is also warned because published GitHub release evidence should be cumulative and immutable. The report does not erase or clamp negative values, guess the cause, or reinterpret deltas as unique adoption. This makes weekly movement reproducible while preserving evidence-quality failures for investigation.

## 2026-07-10: Review Reach Beside Revenue Without Inventing Conversion

`repo-scout-growth` joins an existing schema-2 distribution report to an existing schema-5 or schema-6 pilot report instead of calling GitHub, duplicating their source parsers, or adding a hosted analytics service. The combined report preserves signed artifact-request movement, source and funnel totals, booked revenue, and warnings, then selects one deterministic commercial bottleneck. Artifact requests are not unique people and cannot be assigned to a self-reported lead source, so the tool does not calculate a download-to-lead conversion rate or claim attribution. The review is an operator decision aid: payment labels remain the only revenue evidence, and its next action does not mutate funnel state.

## 2026-07-10: Learn Why Buyers Purchase Before Scaling Outreach

The public pilot form asks for one required primary purchase criterion from a closed taxonomy: policy fit, rollout fit, evidence fit, privacy and security, implementation capacity and timing, commercial fit, or other. Schema-6 funnel reporting connects that self-reported criterion to qualification, offers, booked revenue, conversion, and loss while preserving missing and edited legacy evidence. Sales priority remains readiness-based, so a criterion does not imply urgency or willingness to pay. The taxonomy creates structured learning that can improve policy packs and rollout playbooks; only repeated paid outcomes can turn that learning into a defensible advantage.

## 2026-07-10: Reconcile Moat Learning With Revenue Evidence

Schema-2 growth reviews expose schema-6 purchase-criterion outcomes only after validating the exact intake taxonomy, cumulative stages, booked revenue, and equality with source aggregates. Schema-5 reports remain compatible but represent criterion evidence as unavailable rather than zero. Missing and ambiguous schema-6 criteria remain warnings. Bottleneck selection and sales priority do not use criterion choice because there is not yet paid evidence that one criterion signals urgency. Artifact requests are never assigned to criteria, and stated evaluation priorities are not treated as causal attribution, willingness to pay, or proof of a moat.

## 2026-07-10: Launch A Source-Identifiable Website Objection Experiment

The public site now answers the strongest commercial objection directly: an AI
can recreate a scanner, while the paid pilot sells the operating work required
to agree on one standard, deploy it across uneven repositories, and maintain
reviewable evidence without uploading source code. The page points to the
existing price-disclosed public intake rather than adding analytics or a new
lead system. Success is the first request self-reporting the website as its
source, reviewed with qualification, readiness, purchase criterion, offer, and
payment stages. The experiment is reviewed after three requests or on
2026-07-24; visits and artifact requests are not treated as prospects or sales.

## 2026-07-10: Preserve Discovery Source In Public Application Links

The GitHub README now presents the team outcome and disclosed price before its
long CLI reference, then offers both a website-experiment path and direct pilot
intake. GitHub issue-form field IDs are canonical URL-prefill keys, so website
buttons prefill `Repo Scout website` and repository documentation prefills
`GitHub repository or release` using the existing closed taxonomy. The answer
remains visible, required, and buyer-editable. Prefilling removes a form choice;
it does not silently label a lead, prove causal attribution, or count revenue.

## 2026-07-10: Carry Campaign Source Through The Hosted Offer

The hosted offer accepts one closed `source` query key matching the existing
funnel taxonomy. GitHub, outreach, referral, search, social, website, and other
routes server-render both pilot application links with the corresponding
buyer-editable issue-form prefill. Missing or unsupported values default to
website, and repeated parameters use only their first value, preventing
arbitrary query text from reaching intake. These routes preserve the original
discovery context while every prospect sees the same objection handling and
price; they remain self-report aids, not analytics or causal attribution.

## 2026-07-10: Enable User-Initiated Referrals Without Tracking

The team-value section now offers a prewritten email for sharing Repo Scout
with an engineering lead. The message states the $299 pilot price, up-to-10-
project scope, and local-code boundary, then points to the referral-preserving
hosted route. A `mailto:` link keeps composition and sending in the visitor's
email client, so Repo Scout receives no address and does not claim a send or
click. Only a recipient's independent intake and labeled funnel progression
become commercial evidence.

## 2026-07-10: Give Campaign Pages One Search Identity

All hosted campaign-query variants now declare the same production canonical
URL. A deterministic crawler policy allows the public page and names a one-page
sitemap that excludes campaign URLs; Open Graph metadata also identifies the
canonical page while social images remain request-host aware for deployment
validation. This reduces duplicate search identities without removing the
source-prefilled experience for visitors. Crawler access, indexing, and release
requests remain acquisition signals at most; only self-reported intake and
paid-stage labels count toward revenue validation.

## 2026-07-11: Describe Free Software And Paid Service Separately

The canonical page now publishes one JSON-LD graph with two truthful entities.
The current portable CLI is a `SoftwareApplication` with its exact versioned
download and a $0 offer; the founding-team pilot is a separate `Service` with
the visible $299 price, 90-day duration, up-to-10-project scope, target team,
and local-code boundary. The visible page and structured graph share one release
constant. No reviews, ratings, campaign URLs, or urgency claims are included.
This follows the user-visible offer instead of manufacturing rich-result data,
and it creates no acquisition or revenue evidence on its own.

## 2026-07-11: Bound The First Direct-Outreach Batch

The first operator-led acquisition test covers 10 prospects that each satisfy
at least three public fit signals. Every message includes one specific public
observation, the disclosed $299 and 90-day offer, the up-to-10-project scope,
the local-code boundary, and the direct-outreach campaign route. Only one
seven-day follow-up is allowed, and an opt-out or not-interested response ends
contact. Scraped personal addresses and sales pitches in GitHub issues, pull
requests, or security channels are prohibited. A private ignored ledger records
operator activity with aliases; replies do not become leads or revenue until a
prospect independently submits intake and advances through cumulative labels.

## 2026-07-11: Audit Outreach Locally Without Storing Recipients

The first campaign's private CSV is validated by an installed, dependency-free
operator command. Records use `prospect-NNN` aliases, a closed five-signal fit
taxonomy, and only warm-introduction or published-business channels. The
auditor caps the batch at 10, requires one next action exactly seven days after
initial contact, records the actual follow-up date, rejects an early second
message, and rejects another action after follow-up, reply, pilot request,
rejection, or opt-out. Its output contains aggregate activity and due
aliases, never addresses or message content. It sends nothing, and its replies
or pilot-requested rows do not enter the public revenue funnel.

## 2026-07-11: Forbid Policy-Visible Files Without Blocking Local Secrets

Policy version 2 adds exact normalized `forbidden_files` paths while the parser
continues to accept version 1. In a Git repository, a matching file violates
policy when it is tracked or unignored; properly ignored local files remain
outside enforcement. In a non-Git folder, an existing matching file violates
policy directly. Required and forbidden lists cannot contain the same path,
both lists reject malformed or duplicate entries, and sorted forbidden paths
participate in the policy fingerprint. The manual team-policy example uses v2;
starter and copy-ready CI files remain on v1 until a v2-capable release has a
verified immutable wheel digest and provenance.

## 2026-07-11: Upgrade Policy Gates Only From Verified V2 Artifacts

Both policy gates now install the `v0.3.18` wheel after independently checking
its pinned SHA-256 digest, release manifest, source commit, tag, signer workflow,
and GitHub-hosted provenance. The dogfood, copy-ready, and packaged starter
policies can therefore move to schema v2 and forbid `.env` and `.env.local`
without relying on source checkout or mutable package resolution. A copy-ready
integration test confirms a tracked forbidden file returns policy exit code 6
while retaining remediation-required rollout evidence.

## 2026-07-11: Bound Monorepo Forbidden-Pattern Evidence

Policy version 3 adds `forbidden_file_patterns` while versions 1 and 2 remain
readable. Filename patterns match at any depth, path patterns can target nested
services, and evaluation uses every tracked or unignored Git file rather than
the snapshot's bounded path display. Each matching pattern creates one policy
violation with the full count, at most 20 sorted paths, and an explicit
truncation flag. Invalid or duplicate patterns, patterns without wildcards,
required-file conflicts, and overlap with exact forbidden paths fail during
policy parsing. The verified gates and packaged starters remain on v2 until a
v3-capable release has an independently checked digest and provenance.

## 2026-07-11: Promote Only Safe Nested Patterns To General Policies

Both policy gates now install the independently verified `v0.3.20` wheel, and
all packaged and copy-ready policies use schema v3. General defaults combine
exact root `.env` and `.env.local` rules with `**/.env` and `**/.env.local`
for nested services. They intentionally exclude broad `*.pem` matching because
public certificates and test fixtures may legitimately use that suffix. Such
filename-wide patterns belong in a reviewed custom pack. A released-wheel
simulation and the copy-ready integration test both confirm a force-tracked
nested environment file fails with remediation evidence preserved.

## 2026-07-11: Model Required Alternatives As File Groups

Policy version 4 adds `required_file_groups` while versions 1 through 3 remain
readable. Every group requires at least one listed repository-relative file,
and multiple groups must all be satisfied. Empty groups, semantically duplicate
groups, candidates already required exactly, and candidates forbidden exactly
or by pattern fail during parsing. Policy fingerprints sort both groups and
their members so equivalent TOML ordering produces one identity. The first
staged example accepts npm, pnpm, or Yarn lockfiles. Verified gates and packaged
starters remain on v3 until the `v0.3.22` digest and provenance are checked
independently.

## 2026-07-11: Add A Flexible Node Starter Without Replacing Npm Policy

The independently verified `v0.3.22` wheel, source commit
`4ad97481a7f7d2d444cddc6fc77126503b4697d6`, and wheel SHA-256
`c79fa0ce2c5e706aae9356cdad124aee1f5771e1ecd41f82f9fba7a26011a556`
are pinned together in both policy gates. A new `node-service` starter uses
policy v4 to require `package.json` and one npm, pnpm, or Yarn lockfile. The
existing `node-npm-service` starter remains unchanged because npm-only policy
is a valid stricter standard, and silently broadening it would weaken existing
expectations. Policy discovery names the alternatives explicitly, and the
temporary manual v4 example is removed now that the behavior has a packaged,
tested adoption path.

## 2026-07-11: Block Releases On Installed Node Starter Behavior

The independently verified `v0.3.23` wheel, source commit
`1375911f47a4a91f822314250771f8dd198c886c`, and wheel SHA-256
`ddd75b6662dcec53989c5db382cc596ba8f2cd9b741a7ff120f00012044fab7c`
are pinned together in both policy gates. A dependency-free smoke script uses
an installed Repo Scout Python environment to initialize `node-service` in
three separate clean Git repositories. It requires package-lock, pnpm-lock,
and Yarn lockfiles to pass individually, then removes each lockfile and requires
exit code 6 with the complete alternative-path evidence. The release workflow
runs this script after wheel installation and before provenance attestation or
publication, preventing a package-resource, entry-point, schema, or evaluation
regression from shipping even when source-level unit tests pass.

## 2026-07-11: Recommend A Starting Policy Without Claiming Full Fit

The independently verified `v0.3.24` wheel, source commit
`1feb1737ed8b3476bf5447881c67ab9d85cefaa1`, and wheel SHA-256
`05b000f451c3a99f6ac6916ec186359bab5b5381b15a88c9e92ce9c574f188df`
are pinned together in both policy gates. `repo-scout-policy recommend` uses
only local, explicit manifest and lockfile signals. A sole npm lockfile selects
the npm-only starter; pnpm, Yarn, no Node lockfile, or multiple Node lockfiles
select the flexible starter. Python and agent-ready profiles apply when no Node
manifest exists, with the baseline as fallback. Mixed Node and Python manifests
produce a review warning because one starter cannot represent a polyglot team
policy. The command emits stable text or JSON but does not write a policy,
inspect source content, upload data, or claim that a recommendation replaces
paid policy design. Installed-wheel release smoke tests verify all three Node
recommendation routes before publication.

## 2026-07-11: Test Every Recommendation Route From The Wheel

The independently verified `v0.3.25` wheel, source commit
`e16b68f9ddf6a4ef81ab0e4b136c00e5819f5b82`, and wheel SHA-256
`bd939082cf63bdd9b3f78537e78b1f2a1e018e619a17842f9187aff4cba08a9a`
are pinned together in both policy gates. The release-blocking smoke harness is
generalized from a Node-only name and scope to the complete policy activation
contract. It verifies npm-only, pnpm, Yarn, Python, agent-ready, baseline, and
mixed Node/Python review recommendations from the installed wheel, while
retaining Node starter initialization and pass/fail enforcement. This keeps
distribution proof aligned with every recommendation path exposed to a new
team rather than testing only the most recently added profile.

## 2026-07-11: Bootstrap Only When Recommendation Needs No Review

The independently verified `v0.3.26` wheel, source commit
`592348a8f9a75a4ea2f3dee8c231afc407a106d6`, and wheel SHA-256
`c1774978ae1f03303e36674c87ff70a4b455f7962218b48c6f1cb227517d2f4d`
are pinned together in both policy gates. `repo-scout-policy bootstrap` combines
recommendation and initialization only when the recommendation does not require
review. Its default output is `repo-scout-policy.toml` in the inspected
repository; relative custom outputs also resolve there. It inherits the
existing no-overwrite default, explicit atomic `--force`, and refusal to create
missing parent directories or follow a relative output outside the repository.
Mixed Node/Python repositories return a controlled
error without writing because combining project rules is a team policy decision,
not a safe heuristic. The installed-wheel release smoke verifies successful
bootstrap for every clear route and refusal for the polyglot route.

## 2026-07-12: Emit Bootstrap Receipts Only After Successful Writes

The independently verified `v0.3.27` wheel, source commit
`53dc08b01141373b92e92b4b019c73800e961a4f`, and wheel SHA-256
`8789202cae67ca91b9f410075f65f7a8c937f3fdecf1636700b3b1b48488c820`
are pinned together in both policy gates. `repo-scout-policy bootstrap
--format json` emits a versioned receipt only after the policy file has been
written successfully. The receipt distinguishes `created` from `replaced`,
records the resolved output, preserves the selected starter and reason, and
identifies the normalized policy by version and fingerprint. Review refusals,
overwrite conflicts, and write failures emit no success receipt. The
release-blocking installed-wheel smoke validates this contract across every
clear recommendation route.

## 2026-07-12: Verify Receipt Identity Without A Hosted Service

The independently verified `v0.3.28` wheel, source commit
`7d3b9a0ba09b3f2a965a1ff795e94265a830f8aa`, and wheel SHA-256
`f93297de4f2df1b62451169292b8a3d237d50f9ef9b040bbc77083d09b7a0e92`
are pinned together in both policy gates. `repo-scout-policy verify-receipt`
strictly parses a schema-1 bootstrap receipt and compares its policy version
and normalized fingerprint with the current TOML. A policy-path override
supports deliberate moves. Missing, invalid, or changed policies produce
stable expected-versus-actual evidence and exit code 6; malformed receipt
evidence remains a command error with exit code 2. This makes archived handoff
evidence independently checkable in local or CI workflows without creating a
hosted trust dependency.

## 2026-07-12: Separate Draft Review From Outreach Attempts

The independently verified `v0.3.29` wheel, source commit
`ac710bb9833d6d1f2d46c7e65d0a16545ad43017`, and wheel SHA-256
`0da9f82d85b41d6c1419c8f8ad190f1b3b040c5dd173a7fa5a66b23f6c855c82`
are pinned together in both policy gates. Outreach schema 2 adds `drafted` for
personalized messages awaiting human review. A draft requires a permitted
channel and cannot have contact, follow-up, or next-action dates. Drafts receive
their own aggregate count and remain excluded from attempted prospects. No
prospect list was created from broad web guesses because the current connector
set lacks authoritative sales-intelligence or CRM evidence; qualification and
outreach totals remain zero.

## 2026-07-12: Preflight Every Verified Release Pin Target

The independently verified `v0.3.30` wheel, source commit
`65e1063e5a9c0e85a0f8f30523335eb0c0ce847e`, and wheel SHA-256
`b7001e9fd38359a33f9be1a38961765ba5c37f22d56374b89ec9a9a62f934891`
are pinned together in both policy gates. A maintainer updater now validates
the release identity, requires exactly one version, source, and wheel pin in
the dogfood workflow, customer example, and CI contract, and prepares every
updated file before replacement. Layout drift fails before any target is
changed. Package version `0.3.30` remains unchanged because this maintainer and
configuration improvement does not alter the published CLI behavior.

## 2026-07-12: Commit A Deliberate Public Commercial Baseline

The repository now retains generated distribution schema 2, pilot schema 6,
and joined growth schema 2 reports captured from public GitHub evidence. The
checkpoint contains 34 contract-complete releases and 61 cumulative primary
artifact requests: 1 portable and 60 wheel. It also contains zero pilot
requests and $0 booked revenue. Wheel and manifest counts are materially
confounded by Repo Scout's own CI and maintainer verification, so the reports
remain directional distribution evidence rather than users or adoption.
Baseline tests reconcile every release channel and preserve the zero-revenue
truth. Refresh occurs only at a deliberate review point or meaningful public
funnel change, not on each automated commit.

## 2026-07-12: Treat Clone-Heavy Traffic As Automation-Confounded

The owner-visible GitHub traffic window ending 2026-07-11 contains one unique
repository viewer, 119 unique cloners, and 310 clone events. The daily totals,
window boundaries, top referrer, and popular path are committed as aggregate
evidence with reconciliation tests. The extreme clone-to-view gap is consistent
with ephemeral CI runners and other maintainer automation, so unique cloners
are not labeled users, installs, activations, or prospects. With zero public
pilot requests, acquisition remains the commercial bottleneck.

## 2026-07-12: Continuously Verify The Public Revenue Labels

The seven cumulative `pilot-*` labels now have one dependency-free maintainer
contract for names, colors, and descriptions. A dedicated read-only GitHub
check compares that contract with the live repository whenever the form,
funnel, audit, or workflow changes, and it can also be dispatched manually.
The optional repair mode creates missing labels and restores edited metadata,
but never deletes unexpected labels because those may contain evidence that
requires operator review. Tests tie the contract to the funnel's known stages
and the issue form's automatic `pilot-lead` entry label. A passing audit means
the conversion path is configured; it does not mean anyone applied or paid.

## 2026-07-12: Require Traceable Evidence Before Outreach

Outreach schema 3 requires every declared fit signal to map to one HTTPS source
in the ignored private ledger. Missing, extra, duplicate, malformed, insecure,
and credential-bearing mappings fail validation before a prospect, draft, or
attempt is accepted. The report exposes only an aggregate evidence-link count
and due aliases, never source URLs or prospect identity. A link preserves what
the operator reviewed; it does not prove that a provider or public claim is
authoritative, accurate, or current. No prospect rows were created because the
live connector registry still has no usable Sales Intelligence provider and no
reviewed prospect list was supplied.

## 2026-07-12: Advance Policy Gates To The Verified Outreach Release

Both policy gates now install the independently verified `v0.3.31` wheel from
source commit `949b345c71f800d384ea4b2f056efc7e7a41a6d3` with SHA-256
`9742b31057e657a4db9a1cc2664c3d40e0bcfd87c659e856f6f4753d4b009db0`.
The release manifest, semantic tag, signer workflow, GitHub-hosted provenance,
and artifact bytes were checked before the dogfood workflow, customer example,
and test contract moved together. Package and site versions remain `0.3.31`
because this change advances verified consumption rather than published
behavior.

## 2026-07-12: Verify Application Scope Without Repeating Buyer Free Text

Pilot schema 7 parses the form's required team size, repository count, CI
provider, and repository-standard fields before the sales queue is reviewed.
Complete teams of 5 to 50 developers with at least two repositories are marked
`target`; complete requests outside that profile are `outside_target`; missing,
duplicate, edited, or invalid answers are `incomplete` with stable review
reasons. More than 10 repositories produces `subset_required` for the first-10
pilot scope rather than automatic rejection. Reports retain only whether the
free-text standard exists, not its contents. Labels and payment stages remain
operator decisions, and schema-5 through schema-7 reports remain readable by
the growth review.

## 2026-07-12: Advance Policy Gates To The Verified Qualification Release

Both policy gates now install the independently verified `v0.3.32` wheel from
source commit `2c983c8db3d32ec40b8a20ed585dfc2a48feed2c` with SHA-256
`14ed1f4bd1138574a59cd86c68cf0f67395216a902e0a49aef2d6d98d4173649`.
The release manifest, semantic tag, signer workflow, GitHub-hosted provenance,
and artifact bytes were checked before the dogfood workflow, customer example,
and test contract moved together. This gives teams the same verified release as
the schema-7 qualification workflow without creating a redundant package or
site release. No prospect, outreach attempt, lead, or revenue is inferred.

## 2026-07-12: Prepare The First Draft Batch From Narrow Public Evidence

Five commercial software teams were qualified only after reviewing their own
public GitHub organizations, repository-level agent guidance, and official team,
privacy, or business-contact pages. The identities, published addresses,
personalized messages, aliases, and evidence URLs remain in the ignored private
workspace. `repo-scout-outreach` accepts the rows as five `drafted` prospects
with 16 evidence links. A committed aggregate baseline proves those counts and
is regression-tested to contain no alias, URL, or email address. No message was
sent, so attempted prospects, replies, pilot requests, leads, and revenue remain
zero. Human review is still required before each one-at-a-time contact.

## 2026-07-12: Refresh Commercial Evidence At The First Draft Checkpoint

The five qualified drafts are a meaningful funnel change, so distribution,
pilot, and growth baselines were deliberately refreshed rather than waiting for
another arbitrary hourly run. Public release evidence now covers 36 complete
releases and 78 primary artifact requests. The signed comparison shows 17 new
requests across `v0.3.31` and `v0.3.32`, but the public pilot queue remains empty
and booked revenue remains zero. Pilot evidence moves from schema 6 to schema 7,
and the growth report confirms qualification reporting is available with no
warnings. Artifact movement remains automation-confounded and is not labeled as
users, leads, demand, or revenue.

## 2026-07-12: Record Human Approval Before Counting A Contact

Outreach schema 4 adds `approved` between `drafted` and `contacted`. Drafted
means a personalized message is waiting for review; approved means a human has
checked the public observation, recipient, published business channel, stated
offer, and opt-out behavior. Both states require a permitted channel, forbid
contact and follow-up dates, and remain excluded from attempted-prospect totals.
The text and JSON reports expose only aggregate approval counts. The auditor
does not approve or send messages, and the existing five drafts remain
unapproved with zero attempts, leads, pilot requests, or revenue.

## 2026-07-12: Retain Approval Evidence After A Message Is Sent

Outreach schema 5 appends `approved_on` to the private ledger so adding the
human-review checkpoint does not disappear when a row advances to `contacted`
or a later status. Drafted and researched rows cannot carry the date; approved
and later rows require it; future dates and approvals after contact are
rejected. The report exposes only that human approval is required and the
aggregate approved count, never the private date. The existing five draft rows
remain valid with blank approval dates, zero approved messages, zero attempts,
and no revenue evidence.

## 2026-07-12: Release The Approval Workflow Before Outreach Execution

Version `0.3.33` publishes the schema-4 approval state and schema-5 retained
approval date through the portable zipapp, wheel, and source archive. Public
install instructions and hosted software metadata advance together so the
operator does not need an editable source checkout to audit the five prepared
drafts. The tag-driven release still builds checksums and provenance from the
main-branch release commit. Policy gates remain on independently verified
`v0.3.32` until a separate pin review; a new release is distribution evidence,
not a prospect, attempt, lead, or revenue event.

## 2026-07-13: Advance Both Policy Gates To Verified v0.3.33

The published wheel was downloaded independently and measured at SHA-256
`66c120d5107b9e51986dd08a884d66db06eef54629af208b82456506562e2e3e`.
Its manifest reconciles the exact wheel, source archive, and portable zipapp.
GitHub attestation verification enforced source commit
`b2838064940003ebfb40af686ea91445eae9c984`, tag `v0.3.33`, the repository's
release workflow, and a GitHub-hosted runner for all three artifacts. The wheel
was installed without dependencies and reported package version `0.3.33` plus
outreach schema 5 before the preflighted updater changed the dogfood workflow,
customer example, and CI contract together. This advances trusted distribution;
it does not create an outreach attempt, pilot request, or revenue.

## 2026-07-13: Reject Ambiguous Outreach CSV Rows

The private outreach loader now uses the standard CSV reader in strict mode and
requires exactly nine cells on every data row. Extra cells can otherwise be
silently placed under an unnamed key by a dictionary reader and omitted from
validation; missing cells can hide an incomplete approval record. Malformed
quoting, short rows, and long rows now produce bounded errors containing only
the row number and column count, never private values. The ignored five-draft
ledger was normalized to the exact width with no change to its zero approvals,
attempts, pilot requests, or revenue.

## 2026-07-13: Exercise Installed Outreach Behavior Before Release

The tag workflow previously proved only that the installed outreach command
could display help. Every future release now runs the built wheel through one
approved row, one contacted row, a missing approval date, and an extra CSV cell
before provenance attestation. The smoke test checks schema-5 counts, the human
approval flag, future follow-up handling, private-field omission, and bounded
validation errors. This protects the exact operator distribution used for the
first acquisition batch without approving, contacting, or exposing a real
prospect. Release verification is product safety, not demand or revenue.

## 2026-07-13: Release Strict Outreach Operations Before Contact

Version `0.3.34` publishes exact nine-cell CSV enforcement together with the
installed approval-to-contact smoke test. The public wheel is the operator path
for reviewing the five prepared drafts, and `v0.3.33` does not reject the
synthetic extra-cell case that the strict loader now catches. Package metadata,
portable and wheel URLs, verification instructions, and hosted software identity
advance together. Policy gates remain on independently verified `v0.3.33` until
the new artifacts receive a separate provenance review. This release sends no
message and leaves approvals, attempts, pilot requests, and revenue at zero.

## 2026-07-13: Advance Both Policy Gates To Verified v0.3.34

The public wheel was downloaded independently and measured at SHA-256
`f2164f4b328c0d311e16492faf16a52d42c3944073a850b9d64d9b8a013cb668`.
All three artifacts reconcile with the release manifest and attest to source
commit `fbfbbc59350b1b0f6e411f2cb481b3c447ea7a0b`, tag `v0.3.34`, the pinned
release workflow, and a GitHub-hosted runner. The wheel was installed without
dependencies and passed every policy-activation route plus approved, contacted,
missing-approval, and extra-column outreach checks. The preflighted updater then
advanced the dogfood workflow, customer example, and test contract together.
This reduces distribution ambiguity; it creates no prospect, attempt, request,
or revenue.

## 2026-07-13: Surface One Private Human Review At A Time

The public pilot queue remains empty while five private outreach rows remain
drafted, so acquisition execution is the active constraint. The auditor now
offers `--review-next`, which selects the lowest drafted alias and prints five
unchecked criteria for the observation, recipient and channel, price and scope,
local-code boundary, and opt-out behavior. It exposes only the alias, channel,
and qualification counts, marks the output private, and never includes source
URLs, draft text, or approval dates. It does not edit, approve, or send. A human
must still inspect the private evidence and draft, then record `approved` and
`approved_on` through an explicit action. The checklist is not an attempt, lead,
request, or sale.

## 2026-07-13: Guard The Human Approval Write

Manual CSV edits are the next avoidable failure point between a completed human
review and the first outreach attempt. `--approve-next` now requires the exact
lowest drafted alias, an explicit review date, and confirmation that a human
completed every checklist item. It validates the complete ledger before and
after changing only `status` and `approved_on`, then replaces the private CSV
atomically while preserving its permissions. Any missing confirmation,
out-of-order alias, future date, invalid transition, or write failure leaves the
original ledger untouched. The private receipt omits evidence and review dates.
This records a human decision only; it does not send a message, add contact or
follow-up dates, create a lead, or establish revenue.

## 2026-07-13: Record A Human Send Without Sending

The transition from approved message to contacted prospect is the second manual
CSV risk in the first acquisition batch. `--record-contact` now requires the
lowest approved alias, an explicit send date, and confirmation that a human
already sent the message through its permitted channel. It retains
`approved_on`, changes only `status`, `contacted_on`, and `next_action_on`, and
calculates that next action at exactly seven days. Full validation and the same
permission-preserving atomic replacement protect the original file on every
rejected transition or write failure. Its private receipt omits evidence,
approval dates, and the explicit contact field while exposing the manual
follow-up due date. That date makes send timing inferable, so the receipt stays
private. Repo Scout sends no message and schedules no follow-up. The recorded
attempt is operational evidence only, not a lead, pilot request, payment, or
revenue.

## 2026-07-14: Close The One-Follow-Up Cadence Explicitly

The bounded outreach experiment allows one follow-up no earlier than seven days
after initial contact, but manual CSV edits could record it early or leave a
second next action behind. `--record-follow-up` now selects the earliest due
contacted alias, requires an explicit date and confirmation that a human already
sent the follow-up, and rejects early, future, and out-of-order transitions. It
retains approval and initial-contact evidence, changes only `status`,
`followed_up_on`, and `next_action_on`, and clears the next action atomically.
The receipt omits explicit approval, contact, and follow-up fields but remains
private because it includes the alias and `as_of` context. Repo Scout sends
nothing and schedules no additional message. One initial message plus one
follow-up remains one attempted prospect and no lead, pilot request, payment,
or revenue unless separate funnel evidence appears.

## 2026-07-14: Release-Test The Guarded Journey, Not Prebuilt States

The installed-wheel smoke test previously loaded separate approved and
contacted rows, so it did not prove that the newly guarded commands compose in
the artifact an operator will install. Every future release now starts with one
synthetic draft and runs review, confirmed approval, confirmed contact, and the
one confirmed follow-up through the built wheel before provenance attestation.
The check verifies the exact seven-day cadence, retained approval and contact
evidence, one attempted-prospect total, private receipt and aggregate output,
and preserved file permissions. It also proves that missing approval
confirmation and a repeated follow-up fail without changing the ledger, while
retaining strict missing-approval and extra-cell rejection. All data is
temporary and synthetic; the check sends nothing and does not create demand or
revenue evidence. The five real drafts remain unapproved and unattempted.

## 2026-07-14: Exercise Revenue Accounting From The Installed Wheel

The release workflow previously checked only that `repo-scout-pilot --help`
started, leaving the installable artifact's commercial accounting untested.
Every future release now runs a temporary two-request export through the built
wheel before provenance attestation. One cumulative offered request must remain
outside booked revenue; one cumulative paid request must book exactly $299
toward the three-pilot, $897 target. The check also covers target-profile
qualification, website and outreach segmentation, the remaining pre-payment
sales action, stable operator totals, repository-standard free-text omission,
and controlled non-array input rejection. Synthetic labels and payment state
prove reporter behavior only. They do not create a request, payment, sale, or
revenue evidence, all of which remain grounded in the live public funnel.

## 2026-07-14: Release-Test The Cross-Repository Pilot Outcome

The installed release previously checked only that `repo-scout-rollout --help`
opened, even though cross-repository consistency is the central paid-pilot
outcome. Every future release now aggregates two temporary schema-2 evidence
bundles through the built wheel before provenance attestation. The fixtures
share one policy fingerprint and retain distinct scanned commits while showing
one ready repository and one remediation-required repository. The release is
blocked unless default text and JSON remain counts-only, shared-policy and
identity coverage remain accurate, explicit detail opt-in exposes the expected
records, and duplicate repository IDs fail without a summary. This strengthens
the existing paid workflow without creating another policy feature, customer,
usage event, or revenue claim.

## 2026-07-14: Join Reach And Revenue Evidence Before Release

The wheel's distribution, pilot, and growth commands previously started in the
release environment, but only pilot accounting had a behavioral commercial
test. The installed pilot smoke harness now persists its synthetic schema-7
report, combines it with a valid schema-2 distribution delta, and runs
`repo-scout-growth` before provenance attestation. The joined review must retain
two attributed target-profile requests, two offers, one $299 booking, the $897
target, and the `pilot_target` bottleneck. It must also state that artifact
requests are not unique-user or conversion-rate denominators, omit repository
standard free text, and reject a primary delta that does not equal portable plus
wheel movement without emitting a report. The synthetic join validates the
installed commercial decision aid; it does not establish reach, attribution,
demand, payment, or revenue in the live funnel.

## 2026-07-14: Derive Release Reach Before Joining It

The installed commercial smoke previously supplied `repo-scout-growth` with a
hand-built schema-2 distribution report. That proved growth validation but
skipped the raw release parser, artifact-contract audit, and baseline comparison
that create the evidence in practice. Future releases now run baseline and
current synthetic GitHub release exports through the built wheel's
`repo-scout-distribution` command, require one complete release with no
warnings, and pass its signed portable and wheel movement unchanged into the
growth review. Duplicate asset names must fail without output. Request counts
remain synthetic and non-unique; this test establishes packaged evidence-chain
integrity, not users, demand, attribution, payment, or revenue.

## 2026-07-14: Behavior-Test The Commands Customers Install

The release smoke previously ran commercial behavior with `python -m` after
checking each installed console script only with `--help`. That could miss
packaging metadata that starts successfully but routes real arguments to the
wrong behavior. The commercial harness now accepts an explicit installation
directory and runs pilot, distribution, and growth evidence through the exact
`repo-scout-pilot`, `repo-scout-distribution`, and `repo-scout-growth` scripts
from the built wheel. Source tests retain module mode for speed, and a missing
or non-executable installed command fails with a controlled error. This closes
a paid-distribution assurance gap; it does not create usage, demand, or revenue.

## 2026-07-14: Apply The Installed-Command Rule To Every Release Harness

Commercial reporting was not the only behavioral smoke that bypassed wheel
entry points after a shallow help check. Policy activation and enforcement,
guarded outreach, and rollout aggregation still used `python -m` for their real
assertions. The release workflow now passes its exact installation directory to
all four harnesses, which execute `repo-scout`, `repo-scout-policy`,
`repo-scout-outreach`, `repo-scout-pilot`, `repo-scout-distribution`,
`repo-scout-growth`, and `repo-scout-rollout` as customers receive them. Source
tests keep module mode, and every harness rejects missing or non-executable
commands before creating fixtures. This closes one packaging-risk class as a
single coherent change; it does not add a feature or create commercial evidence.

## 2026-07-14: Make Installed Version Identity Observable

Paid rollout support needs a quick, non-destructive way to determine which Repo
Scout package a developer or CI job is actually running. All seven wheel entry
points and the portable zipapp now support `--version` with the stable
`COMMAND VERSION` format from the package's single `__version__` value. The
release workflow compares every output to the semantic version tag before
attestation, preventing mixed or stale entry-point metadata from publishing
silently. This is a diagnostic and distribution contract, not provenance by
itself and not evidence of activation, demand, payment, or revenue.

## 2026-07-14: Release The Coherent Guarded-Operations Set

Thirteen tested commits after `v0.3.34` form one installable patch set: guarded
human approval, contact, and follow-up recording; behavioral release checks for
every paid-workflow entry point; raw distribution-to-growth evidence; and
observable command version identity. Version `0.3.35` publishes that set rather
than continuing to accumulate source-only improvements. Package, runtime,
portable, website, install-documentation, and release-test versions advance
together. Customer CI pins deliberately remain on independently verified
`v0.3.34` until the new release exists and its exact digest and provenance can
be measured. Publication is distribution evidence, not adoption or revenue.

## 2026-07-14: Advance Both Policy Gates To Verified v0.3.35

The public `v0.3.35` wheel now has an independently measured SHA-256 digest and
has been reconciled with every release asset, the checksum manifest, semantic
tag, exact source commit, signer workflow, GitHub-hosted provenance, and hosted
release run. A clean no-dependency install reports `0.3.35` through every
command and passes the policy-activation and guarded-outreach lifecycle checks.
The preflighted pin updater therefore advances the dogfood gate, copy-ready
customer gate, and their test contract together. This removes a known version
gap from paid-pilot onboarding; it does not prove activation, demand, or revenue.

## 2026-07-14: Make Qualification Evidence An Explicit Private Review Opt-In

The next commercial action is human review of the five prepared drafts, but the
default alias-only checklist hides the source links needed to complete that
review and forces the operator to parse the private CSV. `--review-next` now
accepts `--include-private-evidence` to show only the selected draft's validated
signal-to-URL mappings, clearly marked as private and read-only. Default text and
JSON remain redacted, the flag is rejected outside review mode, and release
smoke coverage proves neither path modifies the ledger. This reduces execution
friction without automating source judgment, approval, sending, or revenue.

## 2026-07-14: Record The First Verified v0.3.35 Demand Checkpoint

The independently pinned `v0.3.35` release and its customer CI gate create a
meaningful measurement boundary after the `v0.3.32` baseline. Public release
records now reconcile 39 complete releases and 109 cumulative primary artifact
requests, a signed increase of 31 across `v0.3.33` through `v0.3.35`. Twenty-eight
of those requests are wheels, and Repo Scout's own release, CI, pinning, and
maintainer verification materially confound them. The refreshed pilot and
schema-5 outreach baselines still show zero pilot requests, approvals, attempts,
and revenue, so the joined growth report keeps acquisition as the bottleneck.
This checkpoint measures reach without relabeling automation as adoption.

## 2026-07-14: Assemble One Explicit Private Human Review Bundle

Evidence links alone do not let a reviewer confirm the intended recipient,
observation, price language, local-code boundary, or opt-out text. The operator
still has to cross-reference a separate notes file before approval. The review
command now accepts `--include-private-draft DRAFTS_MD`, parses only exact
`## prospect-NNN` sections within a 128 KiB bound, and includes only the section
matching the deterministic next alias. Ambiguous, malformed, empty, oversized,
or missing selected sections fail without editing the ledger. Combined with the
evidence opt-in, this creates one clearly private decision bundle while keeping
default output redacted and all judgment, approval, and sending human-controlled.

## 2026-07-14: Require Private Notes And Ledger Identities To Reconcile

A selected section can look valid even when the private notes and ledger have
drifted elsewhere. Before including any draft text, review now requires one note
section for every row still marked `drafted` and rejects sections whose alias is
absent from the ledger. Notes for aliases that progressed may remain as private
history. The check runs after full ledger and bounded-note validation, exposes
no message text on failure, and never edits either file. This guards the human
decision input without approving, sending, or creating commercial evidence.

## 2026-07-14: Release The Complete Private Review Boundary

Five commits after `v0.3.35` form one narrow distribution set: independent
pinning of that release, explicit qualification-evidence review, a refreshed
commercial checkpoint, bounded private draft inclusion, and note-to-ledger
identity preflight. Version `0.3.36` packages the immediate human decision path
so it can run from a checksum- and provenance-backed wheel instead of a source
checkout. Package, runtime, website, installation, and release-test identities
advance together. Customer CI remains pinned to independently verified
`v0.3.35` until the new artifact is published and separately measured. A
release makes the workflow available; it is not an approval, attempt, lead, or
sale.

## 2026-07-14: Advance Both Policy Gates To Verified v0.3.36

The public `v0.3.36` wheel independently measures to SHA-256
`282cad5ee04f388c5487f87b0c99e1423a4d879ba0a4174680bb104d4e7d6e97`
and resolves through its annotated tag to source commit
`f4f4d33fd19ce8287298bfef38458d3328fff3ad` on `main`. Each of the three
distributable artifacts matches the manifest, and the wheel attestation matches
the immutable tag, source digest, signer workflow, and hosted `ubuntu-24.04`
release job while denying self-hosted runners. A clean no-dependency install
reports `0.3.36` through all seven commands and passes policy activation plus
the private review lifecycle. The preflighted updater therefore advances the
dogfood workflow, customer example, and contract test together. This closes the
source-checkout gap for outreach review; it does not prove customer activation,
demand, or revenue.

## 2026-07-14: Record The First Verified v0.3.36 Distribution Checkpoint

The independently pinned `v0.3.36` release and its rollout through both policy
gates create a deliberate measurement boundary after the verified `v0.3.35`
checkpoint. Public release records now reconcile 40 complete releases and 120
cumulative primary artifact requests, a signed increase of 11. The new release
accounts for 7 requests, while `v0.3.35` gained 4 wheel requests. Publication,
independent verification, pinning, and CI activity materially confound all of
this movement, so it is operational distribution proof rather than buyer
demand. Public pilot evidence and the aggregate outreach baseline still show
zero pilot requests, attempts, and revenue. Acquisition therefore remains the
commercial bottleneck, and human-reviewed outreach remains the next action.

## 2026-07-14: Make The Initial Outreach Opt-Out Explicit

The first-message template previously asked whether repository standardization
was not a priority, which left the stop condition implied while the review
checklist required appropriate opt-out behavior. Initial messages now say that
a recipient can decline and receive no further contact. Silence still permits
only the one bounded seven-day follow-up, and any decline remains a terminal
stop. The same wording is present in all five ignored private drafts, while the
review checklist now names the no-further-contact promise directly. This change
improves trust in the live acquisition test without automating approval,
sending, or revenue evidence.

## 2026-07-14: Release The Explicit Outreach Opt-Out

The initial-message safeguard must exist in the public operator command, not
only in source and private draft notes. Version `0.3.37` packages the explicit
no-further-contact review check and advances package, runtime, website,
installation, and release-test identities together. The installed-wheel smoke
requires the exact opt-out check while proving the guarded private review
through follow-up lifecycle.
Customer CI remains pinned to independently verified `v0.3.36` until the new
artifacts are published and separately verified. This release distributes a
trust safeguard; it is not an approval, contact attempt, lead, or sale.

## 2026-07-14: Advance Both Policy Gates To Verified v0.3.37

The public `v0.3.37` wheel independently measures to SHA-256
`b241330e0614cb4759bf764d353cf46871f6957a01f78541f65a9a73bd3b9864`
and its annotated tag resolves to source commit
`d0fd199894b2c7a1ea0b3097a122e37399990568` on `main`. All three
distributable artifacts match the manifest and their GitHub attestations. The
release job used the pinned signer workflow and hosted `ubuntu-24.04` runner,
and completed successfully. A clean no-dependency wheel install reports
`0.3.37` through all seven commands, passes policy activation, and exposes the
exact no-further-contact review check. The preflighted updater therefore moves
the dogfood workflow, customer example, and contract test together. This makes
the distributed trust safeguard available in customer CI; it does not prove
customer activation, outreach attempts, demand, or revenue.

## 2026-07-14: Refuse Live Outreach From Commit-Eligible Files

Git ignore was documented as the privacy boundary for the first outreach batch,
but the CLI would review or mutate any supplied path, including a tracked ledger
or an unignored file that could enter a later commit. Live review, approval,
contact, and follow-up operations now inspect in-repository ledger and draft
paths before reading private material. A tracked or merely untracked path is
rejected, as is a symlink that could redirect the read; an ignored, untracked
private path is accepted. Counts-only auditing remains available for the empty
tracked example. New workspaces use owner-only
`700` directory and `600` file modes, and the existing ignored workspace was
tightened to those modes without changing its contents. This protects the
execution path for the five prepared drafts; it does not record human approval,
contact a prospect, create a pilot request, or change revenue evidence.

## 2026-07-15: Make Human-Controlled Outreach Handoffs Executable

Private text receipts previously named the next outreach action but left the
operator to reconstruct its executable command, dates, alias, and ledger path.
Review, approval, and contact output now emits one complete shell-quoted command
for the next guarded transition. Each handoff carries the selected alias,
required confirmation flag, supplied private ledger path, and relevant action
date; contact uses the calculated follow-up due date exactly. A release smoke
test executes the printed commands through a complete installed lifecycle,
including a path with spaces. JSON receipts remain path-free, and every
approval, initial send, and follow-up still requires an explicit human action
and confirmation. This reduces execution errors for the prepared acquisition
test without creating an attempt, lead, pilot request, payment, or revenue.

## 2026-07-15: Enforce The Documented Private File Modes

The outreach playbook created its ignored workspace with `700` directory and
`600` file modes, but live commands only enforced Git and symlink boundaries.
On POSIX, every live review or mutation now rejects a ledger or draft file with
group/world permission bits and rejects an immediate parent directory with the
same exposure before reading private content. Missing paths retain their
existing controlled read errors, non-POSIX platforms retain the Git boundary,
and counts-only audits remain available for the tracked public template. The
installed lifecycle smoke proves a permissive ledger fails without mutation
before continuing through a correctly protected synthetic workflow. The real
ignored workspace already satisfies the enforced modes, so this hardens the
five prepared attempts without approving or sending them and without creating
demand or revenue evidence.

## 2026-07-15: Release The Private Outreach Execution Boundary

Four commits after `v0.3.37` form one narrow distribution set: independent
pinning of that release plus three operator-safety changes. Live paths inside a
repository must be ignored and untracked, review and mutation receipts emit
complete shell-quoted next commands, and POSIX live files and immediate parent
directories must remain owner-only. Version `0.3.38` advances package, runtime,
website, installation, and release-test identities together so those protections
are available from an attested wheel rather than only a source checkout. The
installed lifecycle smoke rejects a permissive ledger without mutation and then
executes every emitted command through one bounded follow-up.
Customer and dogfood CI remain pinned to independently verified `v0.3.37` until
the new artifacts are published and separately reconciled. This release makes
the prepared workflow distributable; it does not perform human review, contact
a prospect, create a pilot request, or book revenue.

## 2026-07-15: Advance Both Policy Gates To Verified v0.3.38

The public `v0.3.38` wheel independently measures to SHA-256
`9775171f3d19d4a6ca75d66bc1553910c1beba9feb18cd5172c799cb01d2f5d5`
and its annotated tag resolves to source commit
`3f074aad56670d70645c858b4f5d6f58182b33ef` on `main`. All three
distributable artifacts match the manifest and their GitHub attestations. The
release job used the pinned signer workflow and hosted `ubuntu-24.04` runner,
and completed successfully. A clean no-dependency wheel install reports
`0.3.38` through all seven commands and passes policy activation, guarded
outreach, commercial reporting, and rollout aggregation through the packaged
entry points. The preflighted updater therefore moves the dogfood workflow,
customer example, and contract test together. This distributes the private
outreach execution boundary through customer CI; it does not prove customer
activation, human approval, contact attempts, demand, or revenue.

## 2026-07-15: Record The First Verified v0.3.38 Distribution Checkpoint

The independently pinned `v0.3.38` release and its rollout through both policy
gates create a deliberate measurement boundary after the verified `v0.3.36`
checkpoint. Public release records now reconcile 42 complete releases and 141
cumulative primary artifact requests, a signed increase of 21. Releases
`v0.3.38` and `v0.3.37` account for 5 and 12 requests respectively, while
`v0.3.36` gained 4 wheel requests. Publication, independent verification,
pinning, and CI activity materially confound all of this movement, so it is
operational distribution proof rather than buyer demand. Public pilot evidence
and the aggregate outreach baseline still show zero pilot requests, attempts,
and revenue. Acquisition therefore remains the commercial bottleneck, and
human-reviewed outreach remains the next action.

## 2026-07-15: Make A Human No-Send Review Decision First-Class

The deterministic outreach queue previously offered only `--approve-next`.
When a human found a weak observation, inappropriate recipient, unsuitable
channel, inaccurate offer, or deficient opt-out, the safe choice was to stop;
the next draft remained blocked unless the operator hand-edited CSV outside the
guarded workflow. Outreach schema 6 therefore adds `review-declined` as a
pre-contact terminal state and `--decline-next` as its only automated
transition. The command requires the exact next drafted alias and explicit
`--confirm-not-send`, validates private path and ledger state before and after,
preserves permissions, and atomically changes only status. Review output offers
approve and decline commands side by side, while the decline receipt advances
to the next review. A declined draft counts as closed but never attempted and
has no approval, contact, follow-up, or next-action date. This removes pressure
toward approval and makes negative review evidence operable; it does not review
a real draft, send outreach, create a pilot request, or book revenue.

## 2026-07-15: Release The Guarded No-Send Decision

The schema-6 `review-declined` transition is operationally useful only when the
operator can install the same guarded command that the source suite exercises.
Version `0.3.39` advances package, runtime, website, installation, fixture, and
release-test identities together. Its installed outreach smoke executes the
negative review branch and proves a human-confirmed decline closes an unsuitable
draft without creating approval, contact, follow-up, next-action, or attempt
evidence. Customer and dogfood CI remain pinned to independently verified
`v0.3.38` until the new artifacts are published and separately reconciled. This
release distributes a safer acquisition decision; it does not make that human
decision, contact a prospect, validate demand, or book revenue.

## 2026-07-15: Advance Both Policy Gates To Verified v0.3.39

The public `v0.3.39` wheel independently measures to SHA-256
`9fe9317b0e479e6b874d68c35511785308b373fff10367a76dc3006b5a667e36`
and its annotated tag resolves to source commit
`86886448f86dbfdc04f03248cc8017a81e688dbe` on `main`. All three
distributable artifacts match the manifest and their GitHub attestations. The
release job used the pinned signer workflow and hosted `ubuntu-24.04` runner,
and completed successfully. A clean no-dependency wheel install reports
`0.3.39` through all seven commands and passes policy activation, guarded
no-send outreach, commercial reporting, and rollout aggregation through the
packaged entry points. The preflighted updater therefore moves the dogfood
workflow, customer example, and contract test together. This distributes the
human no-send decision through customer CI; it does not prove customer
activation, human review, contact attempts, demand, or revenue.

## 2026-07-15: Record The Verified v0.3.39 Distribution Checkpoint

The independently pinned `v0.3.39` release and its rollout through both policy
gates create a deliberate comparison boundary after the verified `v0.3.38`
checkpoint. Public release records now reconcile 43 complete releases and 147
cumulative primary artifact requests, a signed increase of 6. The new
`v0.3.39` release accounts for 3 requests, while `v0.3.38` gained 3 wheel
requests. Release publication, independent verification, pinning, and CI
activity materially confound this movement, so it is operational distribution
proof rather than buyer demand. Public pilot evidence and the aggregate
outreach baseline still show zero pilot requests, attempts, and revenue.
Acquisition therefore remains the commercial bottleneck, and human-reviewed
outreach remains the next action.

## 2026-07-15: Terminate Completed Review Queues Truthfully

The guarded decline path always emitted a `--review-next` handoff, even after a
human declined the only remaining draft. That command could not change state,
but it falsely implied that the bounded queue still contained work. Decline
receipt schema 2 therefore adds only a privacy-safe remaining-draft count. Text
output emits the next review command while the count is positive and reports a
completed queue without a command at zero. The installed lifecycle smoke now
uses the one-draft terminal branch. This removes a misleading acquisition
handoff without reviewing a real draft, exposing a prospect, sending outreach,
creating a pilot request, or booking revenue.

## 2026-07-15: Release Truthful Terminal Review Receipts

The prepared acquisition workflow should not require a source checkout to end
a review queue accurately. Version `0.3.40` advances package, runtime, website,
installation, fixture, and release-test identities together so decline receipt
schema 2 and its terminal text behavior are available from attested artifacts.
The installed lifecycle smoke declines its only synthetic draft and proves the
receipt reports zero remaining drafts without emitting `--review-next`.
Customer and dogfood CI remain pinned to independently verified `v0.3.39` until
the new artifacts are published and separately reconciled. This distributes an
honest operator handoff; it does not review a real draft, contact a prospect,
validate demand, or book revenue.

## 2026-07-15: Advance Both Policy Gates To Verified v0.3.40

The public `v0.3.40` wheel independently measures to SHA-256
`d973eb08d7209bc14630482c86d7b34d3805e38ed7e25b9b54daab7afa0f9241`
and its annotated tag resolves to source commit
`9a8db84a5ebe640eb33634279845bb58e4aa900f` on `main`. All three
distributable artifacts match the manifest and their GitHub attestations. The
release job used the pinned signer workflow with self-hosted runners denied and
completed successfully. A clean no-dependency wheel install reports `0.3.40`
through all seven commands and passes policy activation, guarded outreach,
commercial reporting, and rollout aggregation through the packaged entry
points. The preflighted updater therefore moves the dogfood workflow, customer
example, and contract test together. This makes the truthful terminal review
receipt available through customer CI; it does not prove customer activation,
human review, contact attempts, demand, or revenue.

## 2026-07-15: Record The Verified v0.3.40 Distribution Checkpoint

The independently pinned `v0.3.40` release and its rollout through both policy
gates create a deliberate comparison boundary after the verified `v0.3.39`
checkpoint. Public release records now reconcile 44 complete releases and 153
cumulative primary artifact requests, a signed increase of 6. The new
`v0.3.40` release accounts for 3 requests, while `v0.3.39` gained 3 wheel
requests. Release publication, independent verification, pinning, and CI
activity materially confound this movement, so it is operational distribution
proof rather than buyer demand. Public pilot evidence and the aggregate
outreach baseline still show zero pilot requests, attempts, and revenue.
Acquisition therefore remains the commercial bottleneck, and human-reviewed
outreach remains the next action.

## 2026-07-15: Guard Post-Contact Outcome Recording

Responses can arrive in a different order from initial sends, so outcome
recording selects an exact private alias rather than imposing the deterministic
send or follow-up queue. `--record-outcome` accepts `replied`,
`pilot-requested`, `not-a-fit`, or `do-not-contact` only from contacted,
followed-up, or generic-reply states and requires explicit human-observation
confirmation. It validates the full ledger before and after, preserves
approval, contact, and follow-up history, atomically clears `next_action_on`,
and leaves rejected actions mutation-free. A generic reply may later become a
specific pilot request, rejection, or opt-out. Receipts remain private and omit
dates and evidence. A private pilot-requested status does not enter the public
pilot funnel or book revenue; it prompts the operator to request public intake.

## 2026-07-15: Release Guarded Outreach Outcomes

The observed-response branch should work from an attested install instead of a
maintainer checkout. Version `0.3.41` advances package, runtime, website,
installation, fixture, and release-test identities together. Its installed
lifecycle smoke proves missing human confirmation cannot mutate the ledger and
then records one synthetic private pilot request while preserving approval and
contact history. Customer and dogfood CI remain pinned to independently
verified `v0.3.40` until the new artifacts are published and separately
reconciled. This distributes truthful response recording; it does not contact a
prospect, create public pilot intake, prove willingness to pay, or book revenue.

## 2026-07-15: Advance Both Policy Gates To Verified v0.3.41

The public `v0.3.41` wheel independently measures to SHA-256
`4f6ef0dd1b996b5c0a35c53b4be7e528a53a4548c80dc1333fc7d8010822281e`
and its annotated tag resolves to source commit
`7fa869310fe1dc1f07cff13a7768f36e4654ce22` on `main`. All four release
assets match the manifest, and all three distributable artifacts pass strict
provenance checks for the tag, source commit, pinned signer workflow, and
GitHub-hosted runner. The successful release job used `ubuntu-24.04`. A clean
no-dependency wheel install reports `0.3.41` through all seven commands and
passes policy activation, guarded outreach outcomes, commercial reporting, and
rollout aggregation through packaged entry points. The preflighted updater
therefore moves the dogfood workflow, customer example, and contract test
together. This distributes observed-response recording through customer CI; it
does not prove customer activation, outreach, demand, or revenue.

## 2026-07-16: Record The Verified v0.3.41 Distribution Checkpoint

The independently pinned `v0.3.41` release and its rollout through both policy
gates create a deliberate comparison boundary after the verified `v0.3.40`
checkpoint. Public release records now reconcile 45 complete releases and 161
cumulative primary artifact requests, a signed increase of 8. The new
`v0.3.41` release accounts for 5 requests, while `v0.3.40` gained 3 wheel
requests. Release publication, independent verification, pinning, and CI
activity materially confound this movement, so it is operational distribution
proof rather than buyer demand. Public pilot evidence and the aggregate
outreach baseline still show zero pilot requests, attempts, and revenue.
Acquisition therefore remains the commercial bottleneck, and human-reviewed
outreach remains the next action.

## 2026-07-16: Keep The Buyer-Facing CI Version In The Guarded Pin Contract

The README's copy-ready CI description still named `v0.3.29` after both policy
gates advanced to verified `v0.3.41`. That stale claim weakens buyer trust and
could make the customer example appear less maintained than it is. The guarded
pin updater now treats the exact README CI sentence as a fourth preflighted target
alongside the dogfood workflow, customer workflow, and contract constants. It
preflights exactly one buyer-facing version claim and refuses every write when
that layout drifts. The CI contract also reconciles the live README claim to the
verified pin. This improves distribution credibility; it does not establish a
customer activation, pilot request, payment, or revenue.

## 2026-07-16: Roll Back Partial Verified-Pin Writes

Complete preflight prevents layout drift from changing any pin target, but it
did not protect against a filesystem failure after one `os.replace` succeeded.
That narrow failure could leave the dogfood workflow, customer example, README
claim, and contract constants on different verified identities. The updater now
stages both new content and an original copy beside every target before the
first replacement. If a later write fails, it restores replaced targets in
reverse order and removes unused temporary files. If restoration itself fails,
the error names the affected target and retained original path for recovery.
A deterministic second-write failure test proves the normal rollback restores
all four targets. This hardens paid CI distribution; it does not create an
activation, pilot request, payment, or revenue.

## 2026-07-16: Tie The Buyer-Facing Outreach Claim To Packaged Schema 6

The README still described schema-5 approval tracking as unreleased after the
public package had advanced to schema 6 with guarded review-decline decisions.
That made shipped controls look speculative and omitted the current distinction
between closed no-send reviews and actual contact attempts. The README now
describes schema-6 approval and review-decline counts, retained approval dates,
and pre-contact attempted-count exclusions. A contract test imports the runtime
schema constant when checking the claim so the next schema change must update
buyer-facing documentation intentionally. This improves product credibility;
it does not review a real draft, contact a prospect, validate demand, or book
revenue.

## 2026-07-16: Preserve Verified-Pin Target Permissions Explicitly

Atomic replacement writes through temporary files, so the staged file's mode
becomes the final workflow, README, or contract mode. The updater already
intended to carry the target mode forward, but it stored raw `st_mode` metadata
and lacked regression proof across success, rollback, and retained recovery
paths. It now reduces filesystem metadata to permission bits before `chmod`.
Tests use distinct POSIX modes to prove a successful transaction preserves all
four targets and removes every staging file; failure coverage also proves
restored targets and retained originals keep their modes. This strengthens the
verified paid CI distribution path; it does not establish activation, demand,
payment, or revenue.

## 2026-07-16: Derive Public Verification Counts From Release Artifacts

The release guide listed three distributable artifacts and three attestation
commands but concluded that "both" checksum lines and commands must pass. That
understated the verification work for the portable, wheel, and source artifacts
and weakened a buyer-facing trust instruction. The guide now states 4 downloaded
files, including the manifest, 3 checksum lines, and 3 provenance commands. A
contract test derives those counts from `ARTIFACT_TEMPLATE` and counts the
documented commands, so changing the artifact contract requires an intentional
documentation update. This strengthens verified distribution; it does not
establish a customer activation, pilot request, payment, or revenue.

## 2026-07-16: Derive The Wheel Command Contract From Package Metadata

The distribution adoption path still said the wheel supplied six commands after
the package and release smoke had grown to seven. The release test also repeated
those command names manually, so a future entry point could drift between
package metadata, smoke coverage, and buyer-facing guidance. The guide now
states all 7 commands. Tests read `[project.scripts]`, require the release
workflow's version loop to cover that exact set without duplicates, and derive
the documented count from the same metadata. This strengthens the verified
wheel and paid CI activation path; it does not establish an install, pilot
request, payment, or revenue.

## 2026-07-16: Preserve The Pin Transaction Outcome When Cleanup Fails

Temporary-file deletion previously raised raw `OSError` exceptions. After a
successful replacement set, that made a committed pin update look like an
unspecified failure. During recovery, it could mask the original write error
and whether replaced targets were restored. Cleanup now collects path-specific
failures instead of raising immediately. A post-commit failure explicitly says
the verified pin was updated, while a write failure retains its rollback or
recovery result and appends every incomplete cleanup path. Tests inject both
branches and prove target contents match the reported state. This makes paid CI
distribution maintenance recoverable; it does not establish activation,
demand, payment, or revenue.

## 2026-07-16: Preserve Existing Policy Permissions Across Force Replacement

`repo-scout-policy init --force` and guarded bootstrap replace a completed
temporary file atomically, but the temporary file's restrictive default mode
previously became the team policy's new mode. Force replacement now records an
existing target's normalized permission bits and applies them to the staged
file before `os.replace`. If that permission step fails, the original policy
and mode remain unchanged and the temporary file is removed. New targets keep
their existing creation behavior. This protects the local and CI activation
path; it does not establish customer usage, demand, payment, or revenue.

## 2026-07-16: Preserve Existing Reports Until Forced Replacement Commits

The primary CLI previously implemented `--output --force` with `write_text`,
which truncates an existing report before the replacement content is complete.
A write failure could therefore destroy the last handoff or rollout artifact.
Forced replacement now writes a temporary sibling, applies the existing
report's normalized permission bits, and commits with `os.replace` only after
the staged content closes successfully. A failed final swap keeps the original
bytes and mode and removes the unused temporary file. First-time report creation
keeps its existing behavior. This protects paid rollout evidence; it does not
establish customer activation, demand, payment, or revenue.

## 2026-07-16: Release Distribution And Replacement Safeguards

The commits after `v0.3.41` harden workflows already used for paid activation:
verified-pin updates now preflight the buyer-facing claim, roll back partial
writes, preserve target permissions, and retain truthful cleanup outcomes;
release documentation and smoke coverage reconcile to the packaged artifact
and command contracts; and forced team-policy and report replacement preserves
existing evidence and access modes. Version `0.3.42` advances package, runtime,
website, installation, and release-smoke identities together so those safeguards
can ship through attested artifacts. Customer and dogfood CI stay pinned to
independently verified `v0.3.41` until publication and separate reconciliation.
This creates a release boundary, not customer activation, demand, payment, or
revenue evidence.

## 2026-07-16: Advance Both Policy Gates To Verified v0.3.42

The public `v0.3.42` wheel independently measures to SHA-256
`207931651b217dc02dfacb64886da409b5518d78c3ada702edace58ea9db1e5e` and
resolves through annotated tag `v0.3.42` to main-branch source commit
`6d9edda82e8a84782a3532c8772690bc0973bc7a`. The downloaded manifest verified
the wheel, portable zipapp, and source archive. GitHub attestations verified all
three artifacts against the repository, and release run `29535732423` used the
pinned signer workflow on a GitHub-hosted `ubuntu-24.04` runner. A fresh
no-dependency wheel install reported `0.3.42` from all seven public commands and
passed the policy activation, guarded outreach, commercial reporting, and
rollout aggregation smoke harnesses. The preflighted updater therefore advances
the dogfood workflow, copy-ready customer example, buyer-facing CI claim, and
pin contract together. This strengthens the paid activation distribution path;
it does not prove a customer install, pilot request, payment, or revenue.

## 2026-07-16: Record The Verified v0.3.42 Distribution Checkpoint

The independently pinned `v0.3.42` release and its rollout through both policy
gates create a deliberate comparison boundary after the verified `v0.3.41`
checkpoint. Public release records now reconcile 46 complete releases and 176
cumulative primary artifact requests, a signed increase of 15. The new
`v0.3.42` release accounts for 3 requests, while `v0.3.41` gained 12 wheel
requests. Release publication, independent verification, pinning, and CI
activity materially confound this movement, so it is operational distribution
proof rather than buyer demand. Public pilot evidence and the private aggregate
outreach audit still show zero pilot requests, approvals, attempts, and revenue.
Acquisition therefore remains the commercial bottleneck, and human-reviewed
outreach remains the next action.

## 2026-07-17: Bound Verified Release Download Retries

The verified `v0.3.42` policy gate failed while GitHub reported a major REST API
availability incident because its single `gh release download` attempt could not
see the existing public release. The same commit passed unchanged once GitHub
recovered, confirming an external false negative rather than artifact drift.
Both dogfood and copy-ready workflows now make at most four attempts with 5,
10, and 15-second waits. Every attempt uses a separate runner-temporary
directory, and only a complete wheel-plus-manifest result moves into the trusted
verification directory. The fourth failure exits before installation; retries
do not weaken the pinned digest, manifest, provenance, source, signer, or hosted
runner checks. This improves paid CI activation reliability without claiming a
customer install, pilot request, payment, or revenue.

## 2026-07-17: Execute The Verified Download Failure Paths

Text and syntax checks prove the retry loop is present and parseable, but they
do not prove failed attempts reach the intended later branches. The CI contract
now executes the exact dogfood download shell with temporary fake `gh` and
`sleep` commands. One case fails twice, records 5 and 10-second waits, succeeds
on the third isolated attempt, and promotes only the complete wheel and
manifest. A second case fails all four attempts, records the final 15-second
wait sequence, exits explicitly, and leaves no trusted wheel or manifest. The
test makes no network call and the customer workflow remains byte-identical to
the executed dogfood block. This strengthens paid CI reliability evidence; it
does not establish an external activation, pilot request, payment, or revenue.

## 2026-07-17: Bound Provenance Verification Retries

Release download and `gh attestation verify` both depend on GitHub REST
availability, but only download recovery was bounded after the observed outage.
Both policy gates now make at most four provenance attempts with 5, 10, and
15-second waits. Every attempt repeats the exact wheel, repository, source
commit, semantic tag, signer workflow, and hosted-runner restrictions; the
fourth failure exits before installation. Contract tests execute the exact
shell with fake checksum and network commands, proving third-attempt recovery
and terminal failure without weakening identity checks or calling GitHub. The
customer and dogfood verification blocks are byte-identical. This improves paid
CI activation reliability without establishing an external install, pilot
request, payment, or revenue.

## 2026-07-17: Refresh Traffic Without Treating Clones As Demand

The owner-visible rolling window ending 2026-07-16 records 3 repository views
from 1 unique viewer, 293 unique cloners, and 962 clone events. Compared with
the overlapping checkpoint ending 2026-07-11, the raw window totals rose by 2
views, 174 unique cloners, and 652 clone events, while unique viewers remained
at one. The windows overlap and GitHub's popular referrer and path lists are
partial rankings, so these differences are directional rather than additive or
fully attributable. The baseline contract now validates a strict UTC daily
cadence and nonnegative bounded counts without requiring partial top lists to
reconcile every view. The widening clone-to-view gap remains consistent with
CI, hosting, and maintainer automation. It does not establish 293 users,
installs, pilot requests, payments, or revenue, and the five-draft human review
queue remains the next commercial action.

## 2026-07-17: Bind Outreach Decisions To The Reviewed Content

The complete private review previously emitted copy-ready approval and decline
commands that identified the selected alias but did not bind the decision to
the evidence and draft the human had just read. An intervening edit could
therefore leave the alias first in the queue while changing the material being
approved or declined. Schema-4 complete reviews now emit a SHA-256 receipt over
the normalized selected ledger row, selected private draft, review date, and
five displayed checks. Both generated decisions carry that receipt and the
reviewed notes path. Before writing, Repo Scout reloads the private files,
recomputes the receipt, and rejects stale evidence or draft content without
mutating the ledger or printing the changed material. Direct legacy commands
remain compatible, while the documented five-draft workflow uses the
content-bound handoff. This protects the human decision boundary; it does not
perform the review, approve a message, send outreach, create demand, or record
revenue.

## 2026-07-17: Release Content-Bound Review Safety

The schema-4 review receipt is only useful to the five-draft operating queue
when the installable `repo-scout-outreach` command contains it. Version
`0.3.43` therefore advances package metadata, runtime identity, website
structured data, direct download instructions, artifact-verification examples,
and release-smoke fixtures together. The boundary also ships the bounded
download and provenance retries added after `v0.3.42`. The release smoke
requires the built wheel to emit a content receipt and approve a matching
private bundle through the installed command. Historical metrics remain on
their measured release versions, and both policy gates remain pinned to
independently verified `v0.3.42` until publication and separate reconciliation.
This creates an attested distribution boundary; it does not approve or send a
draft, prove an install, create a pilot request, or record revenue.

## 2026-07-17: Advance Both Policy Gates To Verified v0.3.43

The public `v0.3.43` wheel independently measures to SHA-256
`6fdf59d039cd168fa830f1dc72b6b4627e1df6a30f52c933ccdc559643497f16` and
resolves through annotated tag `v0.3.43` to main-branch source commit
`e041d9d786c16bce2b645a407d3556ed4146d427`. The downloaded manifest verified
the wheel, portable zipapp, and source archive. GitHub attestations verified all
three artifacts against the source commit, semantic tag, release signer
workflow, and hosted-runner restriction. Release run `29612283459` completed
successfully. A fresh no-dependency wheel install reported `0.3.43` from all
seven public commands and passed the policy activation, guarded outreach,
commercial reporting, and rollout aggregation smoke harnesses. The preflighted
updater therefore advances the dogfood workflow, copy-ready customer example,
buyer-facing CI claim, and pin contract together. This strengthens paid
activation distribution; it does not prove a customer install, outreach
attempt, pilot request, payment, or revenue.

## 2026-07-17: Record The Verified v0.3.43 Distribution Checkpoint

The independently pinned `v0.3.43` release and its rollout through both policy
gates create a deliberate comparison boundary after the verified `v0.3.42`
checkpoint. Public release records now reconcile 47 complete releases and 190
cumulative primary artifact requests, a signed increase of 14. The new
`v0.3.43` release accounts for 7 requests, while `v0.3.42` gained 7 wheel
requests. Release publication, independent verification, pinning, and CI
activity materially confound this movement, so it is operational distribution
proof rather than buyer demand. Public pilot evidence and the aggregate
outreach baseline still show zero pilot requests, attempts, and revenue.
Acquisition therefore remains the commercial bottleneck, and human-reviewed
outreach remains the next action.

## 2026-07-17: Use UTC Dates Across The Outreach Lifecycle

Direct-outreach commands previously derived review, approval, contact,
follow-up, and outcome dates from the operator's local calendar, while the
public pilot funnel already uses UTC. Around midnight, different operator
timezones could therefore bind a review receipt to one day but record a guarded
action on another, or reject an action as future-dated. The outreach CLI now
uses the current UTC calendar date when `--as-of` is omitted, and every
copy-ready lifecycle example passes that UTC date explicitly for both the
report and action date. Explicit ISO dates and dates carried forward by emitted
commands remain authoritative. This makes the private execution record
reproducible; it does not review, approve, send, or count outreach.

## 2026-07-18: Release UTC Outreach Defaults

The source tree and copy-ready documentation now use UTC across the private
outreach lifecycle, but the public `v0.3.43` wheel still defaults an omitted
`--as-of` value to the operator's local calendar date. Version `0.3.44`
therefore advances package, runtime, website, download, and release-smoke
identities together. Before publication, the installed-command smoke selects a
local timezone whose date differs from UTC and requires the audit to retain the
current UTC date. Historical metrics and independently verified policy pins
remain on their measured `v0.3.43` boundary until publication and separate
verification. This distributes an execution fix; it does not perform human
review, send outreach, prove adoption, create demand, or book revenue.

## 2026-07-18: Advance Both Policy Gates To Verified v0.3.44

The public `v0.3.44` wheel independently measures to SHA-256
`1855cc8066434f2c07d998caa869e0f898511d6df996b03a03cb61df5eb10d89` and
resolves through annotated tag `v0.3.44` to main-branch source commit
`7012255f5b88ab01fbd84e58ccfec310a397b614`. The downloaded manifest verified
the wheel, portable zipapp, and source archive. GitHub attestation verification
bound the wheel to the exact source, semantic tag, release workflow, and hosted
runner. All seven installed commands and four paid-workflow smoke harnesses
passed from a fresh no-dependency wheel installation.

The guarded release-pin updater changed the dogfood workflow, copy-ready
workflow, buyer-facing README claim, and CI contract test together. Both policy
gates retain exact source and wheel-digest verification before installation.
This strengthens paid CI distribution; it does not prove a customer install,
outreach attempt, pilot request, payment, demand, or revenue.

## 2026-07-18: Record The Verified v0.3.44 Distribution Checkpoint

The independently pinned `v0.3.44` release and its rollout through both policy
gates create a deliberate comparison boundary after the verified `v0.3.43`
checkpoint. Public release records now reconcile 48 complete releases and 201
cumulative primary artifact requests, a signed increase of 11. The new
`v0.3.44` release accounts for 7 requests, while `v0.3.43` gained 4 wheel
requests. Release publication, independent verification, pinning, and CI
activity materially confound this movement, so it is operational distribution
proof rather than buyer demand. Public pilot evidence and the aggregate
outreach baseline still show zero pilot requests, attempts, and revenue.
Acquisition therefore remains the commercial bottleneck, and human-reviewed
outreach remains the next action.

## 2026-07-18: Define Paid Pilot Delivery Acceptance Before First Payment

The $299 offer already names policy design, CI guidance, one custom policy pack,
and support across up to 10 repositories for 90 days, but it did not define a
shared post-payment acceptance boundary. The rollout guide now requires a
private scope record and five concrete deliverables produced through shipped
commands: the reviewed policy pack, agreed CI integration, current repository
bundles, counts-only rollout summary, and closeout record. GitHub Actions is the
only copy-ready gate currently shipped; another selected CI provider requires
an explicit integration decision before payment.

Payment, first-repository activation, and annual conversion remain
human-observed business events represented by `pilot-paid`, `pilot-active`, and
`pilot-converted`. Tool output never applies those labels or turns a passing
bundle into revenue. This reduces delivery ambiguity without adding another
acquisition channel or paid-policy feature before the five-draft outreach queue
is executed.

## 2026-07-18: Ship A Blank Private Pilot Delivery Record

The delivery acceptance contract defines what a paid pilot must produce, but an
operator still had to invent the kickoff record and could omit scope, ownership,
CI-provider, or acknowledgement fields. A copy-ready Markdown template now
contains exactly 10 private repository slots, one pre-payment CI integration
choice, the five accepted deliverables, first-repository handoff evidence, and
90-day closeout fields.

The blank template contains no customer or prospect data, and its completed
copy belongs only in a customer-approved private system. The test contract
locks the repository limit, shipped-command references, privacy boundary, and
human `pilot-paid` before `pilot-active` before `pilot-converted` ordering.
This improves paid delivery readiness without creating a new acquisition asset,
payment claim, or software feature.

## 2026-07-18: Ignore And Restrict Short-Lived Local Delivery Records

The completed pilot delivery record contains repository identity, access,
payment confirmation, CI, and customer-acceptance references. Warning operators
not to commit it was insufficient while the repository offered no protected
local destination. The `pilot-private/` path is now ignored, and the rollout
guide creates its directory and record with owner-only `700/600` permissions
before requiring `git check-ignore` to pass.

The tracked blank template remains outside that ignore rule. Ignore rules are
not encryption or access control, and `git add --force` can bypass them, so the
local workspace is only a short-lived fallback; durable completed evidence
still belongs in the customer-approved private system. This closes a paid
delivery privacy gap without adding acquisition behavior or claiming revenue.

## 2026-07-18: Link Private Handoff To Public Pilot Activation

The public funnel previously defined `pilot-active` only as a paid pilot
running in at least one repository, while the delivery contract requires a
reviewed policy, CI run, retained rollout bundle, remediation plan, and
customer-acknowledged first-repository handoff. The tracking guide now requires
every contract condition and `pilot-paid` before activation.

Repository identity, access, CI evidence, payment details, and acknowledgement
remain in the customer-approved private system or short-lived ignored fallback.
The public issue receives only the cumulative label and a non-sensitive status
note. Executable coverage now runs the documented local setup and proves its
directory and completed record use `700/600` permissions. The hosted pilot gate
runs that delivery contract whenever its implementation or documentation
changes. This makes paid delivery and revenue tracking agree without automating
business labels, creating an acquisition asset, or claiming a payment or
customer.

## 2026-07-18: Atomically Pin The Commercial Release Claim

Both policy gates, the README, and the CI contract had advanced to independently
verified `v0.3.44`, but the business model still claimed the paid CI path used
`v0.3.43`. That stale buyer-facing statement weakened distribution trust even
though the executable gates were correct.

The guarded release-pin updater now treats the exact business-model statement
as a fifth preflighted target. A missing or duplicate commercial claim stops
the update before any file is replaced, and the existing staged rollback and
permission guarantees apply to all five targets. The live CI contract also
requires the commercial claim to match the pinned constant. This corrects and
prevents factual drift in the existing paid workflow; it does not add a product
feature, outreach asset, customer, payment, or revenue.

## 2026-07-18: Require Actual Dates In Future Outreach Handoffs

Approval and contact receipts previously emitted executable next commands that
reused the approval date as the contact date and the calculated due date as the
follow-up send date. If a human sent later, running the command unchanged
backdated real activity and calculated the cadence from false evidence.

Generated contact and follow-up commands now contain `YYYY-MM-DD` placeholders
for both `--as-of` and the human event date. An unchanged command fails date
parsing before the private ledger can mutate. The receipt still carries the
exact alias, protected ledger path, confirmation flag, and follow-up due date,
but the operator must enter the actual UTC send date. This protects outreach
and follow-up evidence without sending a message, adding a prospect, or
claiming demand or revenue.

## 2026-07-18: Release Actual-Date Outreach Handoffs As v0.3.45

The source tree and documentation require generated contact and follow-up
commands to use explicit placeholders for real human send dates, but the public
`v0.3.44` wheel still reuses approval and due dates. Version `0.3.45` therefore
advances package, runtime, website, download, release-smoke, and synthetic
distribution identities together.

The release contract executes the installed outreach command with approval on
July 1, contact on July 3, and follow-up on July 10, and requires the calculated
July 10 due date to remain visible. Verified CI pins and measured distribution
evidence stay on `v0.3.44` until publication and independent verification. This
closes a public distribution mismatch; it does not perform human outreach,
create a pilot request, collect payment, or claim revenue.

## 2026-07-18: Advance Both Policy Gates To Verified v0.3.45

The public `v0.3.45` wheel independently measures to SHA-256
`fdf5642f3b205eb73644c96ee782b4cb34771c77dc77f9b21441e0716c76792d` and
resolves through annotated tag `v0.3.45` to main-branch source commit
`607745873a2262f2f7710609f02ea3b617d3db9e`. The downloaded manifest verified
the wheel, portable zipapp, and source archive. GitHub attestations bound all
three artifacts to the exact source, semantic tag, release workflow, and
GitHub-hosted `ubuntu-24.04` runner. All seven installed commands and four
paid-workflow smoke harnesses passed from a fresh no-dependency wheel
installation.

The guarded release-pin updater changed the dogfood workflow, copy-ready
workflow, buyer-facing README and commercial claims, and CI contract test
together. Both policy gates retain exact source and wheel-digest verification
before installation. This strengthens paid CI distribution; it does not prove
a customer install, outreach attempt, pilot request, payment, demand, or
revenue. Human review and actual execution of the five prepared outreach drafts
remain the next commercial action.

## 2026-07-18: Record The Verified v0.3.45 Distribution Checkpoint

The independently pinned `v0.3.45` release and its rollout through both policy
gates create a deliberate comparison boundary after the verified `v0.3.44`
checkpoint. Public release records now reconcile 49 complete releases and 218
cumulative primary artifact requests, a signed increase of 17. The new
`v0.3.45` release accounts for 7 requests, while `v0.3.44` gained 10 wheel
requests. Release publication, independent verification, pinning, and CI
activity materially confound this movement, so it is operational distribution
proof rather than buyer demand.

Public pilot evidence and the aggregate outreach baseline still show zero pilot
requests, attempts, and revenue. Acquisition therefore remains the commercial
bottleneck, and human-reviewed outreach remains the next action. No additional
acquisition asset or paid-policy feature is justified before that five-draft
queue is executed.

## 2026-07-18: Audit Production Release Identity Before Promotion

The public Sites deployment still advertised `v0.3.44` after the repository,
public release, and verified CI gates advanced to `v0.3.45`. Local render tests
proved the source was correct but could not detect that production lag.

A dependency-free maintainer audit now fetches the deployed HTML and requires
one canonical URL plus one JSON-LD `SoftwareApplication` whose version, portable
download, and free offer match `project.version`. Network, content-type,
malformed-data, stale-version, and stale-download failures stop explicitly.
This maintains the existing public path and adds no campaign route, policy
feature, customer action, demand, or revenue evidence.

## 2026-07-18: Schedule The Production Release Audit

The production release audit detected a real stale deployment, but a manual
command still depended on maintainer memory. A daily and manually dispatchable
GitHub workflow now runs that exact dependency-free check with read-only
contents access, immutable action pins, a two-minute timeout, and no secrets.

The workflow observes the existing public buyer path and fails visibly when its
release identity drifts. It does not deploy, repair, promote, create another
acquisition route, change a customer record, or count as demand or revenue.

## 2026-07-18: Audit The Paid Production Conversion Path

The scheduled production check initially proved only the free release identity.
Production could still omit or misprice the paid service, or remove the public
pilot application link, while the monitor remained green.

The same dependency-free audit now requires exactly one founding-team service
with the existing $299 USD limited offer at the production pilot section and at
least one website-attributed link to the existing GitHub application form. It
does not alter the offer, add tracking, submit intake, create a lead, or count
as demand or revenue.

## 2026-07-18: Exclude Terminal Conflicts From Resolved Outcomes

An issue labeled as both `pilot-converted` and `pilot-lost` was shown at the
conflict stage but still incremented both annual conversion and loss totals,
including every source, readiness, and purchase-criterion segment. One
unresolved record therefore overstated both clean commercial outcomes.

Terminal conflicts now contribute to neither resolved outcome until their
labels are corrected. A cumulative `pilot-paid` milestone still preserves the
historical $299 booking, and the conflict stage and warning remain visible.
This changes no customer state or revenue evidence; it makes the existing
report distinguish booked history from unresolved terminal classification.

## 2026-07-18: Reject Stale Outreach Lifecycle Commits

Atomic file replacement protected each individual outreach write but did not
make the read, validation, and later replacement one transaction. Two valid
processes could read the same private ledger, then a stale process could replace
a newer lifecycle state and undercount real contact evidence.

Each mutation now retains the SHA-256 revision it validated. A persistent,
owner-only adjacent lock serializes revision comparison and replacement without
being swapped alongside the ledger; a busy lock or changed revision stops with
a retry instruction. The lock contains no prospect data, failed commits remove
their staged file, and read-only reporting remains lock-free.

## 2026-07-18: Recheck Outreach Privacy At The Commit Point

Live outreach actions checked owner-only file and parent permissions before
loading the private ledger. A later permission change before staging could
therefore be preserved by the atomic replacement even though the same mode
would have stopped the original preflight.

Every lifecycle writer now repeats the regular-file and owner-only permission
check while holding the adjacent ledger lock, then applies only that validated
mode to the staged file. Late privacy drift stops without replacing current
bytes, and normal cleanup removes the unused staged file. The tool does not
silently repair the externally changed mode because that would hide evidence
that the private boundary changed.

## 2026-07-18: Require The Next Review's Actual Date

A nonterminal decline receipt reused its own `as_of` date in the generated
command for reviewing the next draft. If the operator resumed the queue later,
that old date entered the next content-bound receipt and generated approval,
silently backdating a separate human review.

The next-review handoff now uses the same required `YYYY-MM-DD` convention as
future contact and follow-up actions. The operator must enter the actual UTC
review date, while an unchanged placeholder fails during argument parsing
before the remaining private ledger is read or modified. A terminal decline
still emits no next command.

## 2026-07-18: Guard Reviewed Notes Through Decision Commit

Content-bound approval and decline reloaded the private notes and verified the
human receipt before building a ledger transition. The ledger replacement was
revision-checked later, but an editor save to the separate notes file in that
window could still let the decision commit against content the receipt no
longer represented.

Receipt verification now returns the SHA-256 revision of the bounded private
notes read. The approval or decline writer compares that revision again while
holding the ledger lock and rechecks the notes' private file boundary. Any
intervening edit emits the existing generic fresh-review instruction, leaves
the ledger bytes unchanged, and removes the staged replacement without exposing
private message text.

## 2026-07-18: Carry Exact Outcome Handoffs

Outcome recording can happen after initial contact or after follow-up and can
arrive out of send order. Asking the operator to reconstruct a command from
memory risks applying real response evidence to the wrong alias or private
ledger even though every earlier lifecycle transition already emits an exact
handoff.

Contact and follow-up text receipts now emit the same shell-quoted
`--record-outcome` command with the exact alias, private ledger path, and
confirmation flag. Required `YYYY-MM-DD` and `OUTCOME` placeholders preserve
the human observation step; an unchanged placeholder fails during argument
parsing before ledger access. This adds no sending, prospect, public demand, or
revenue evidence, and private pilot interest still requires public intake
before it enters the funnel.

## 2026-07-18: Carry Generic Replies To One Specific Outcome

A generic `replied` status intentionally closes the follow-up cadence before
the operator has classified the response. Its receipt previously described a
later refinement but discarded the exact alias and private ledger path, making
the only supported two-step outcome path less reliable than initial outcome
recording.

Only generic reply receipts now emit another shell-quoted outcome command. The
handoff keeps the alias and ledger path, requires a fresh UTC observation date,
and limits the stated choices to `pilot-requested`, `not-a-fit`, or
`do-not-contact`. Terminal receipts emit no command. A private
`pilot-requested` refinement remains an operator classification and must still
be followed by public intake before it counts as demand or revenue.

## 2026-07-18: Keep The Review Queue Content-Bound After Declines

The prescribed private workflow reviews each prepared prospect with both
private evidence and its draft notes. A nonterminal content-bound decline
previously emitted only `--review-next`, silently downgrading the following
prospect to an alias-only checklist and removing the digest guard from its
generated decision commands.

The decline formatter now carries the reviewed notes path into the next command
and restores both complete-review disclosure flags. The actual UTC review date
remains a required placeholder, and legacy alias-only declines retain their
existing handoff. This fixes the existing five-draft execution path without
adding a prospect, message, channel, approval, contact attempt, or revenue
claim.

## 2026-07-18: Prove Both Review Decisions Reject Commit-Window Edits

Approval and decline share the locked private-notes revision guard, but the
regression that forced an editor save after receipt verification exercised only
approval. A future change could therefore weaken no-send decisions without
failing the commercial workflow suite.

The same test contract now runs the race through both generated decision
shapes. Each must reject with the generic fresh-review instruction, preserve
the private ledger byte for byte, omit the edited message from errors, and
remove staged output. This creates no review decision or outreach event; it
protects the evidence boundary used when a human chooses either outcome.

## 2026-07-19: Link Private Pilot Interest To Existing Public Intake

The guarded outreach ledger deliberately keeps a human-observed
`pilot-requested` status private and outside the revenue funnel. Its receipt
previously told the operator to request public intake but omitted the existing
form, creating avoidable friction at the only point where private interest can
become source-attributed public evidence.

Outcome receipt schema 2 now includes that GitHub form with the visible
`Direct outreach` answer prefilled, in JSON and default text, only for
`pilot-requested`. Other outcomes use an explicit null and no text link. Repo
Scout does not open or submit the form, the prospect can edit the source answer,
and no lead, demand, payment, or revenue exists until the prospect independently
submits intake and the existing funnel advances.

## 2026-07-19: Require Exact Payment Evidence For Booked Revenue

The public pilot funnel uses cumulative labels, but it previously inferred a
booking whenever an issue reached `pilot-active` or `pilot-converted`, even if
the required `pilot-paid` label was absent. A skipped-stage warning therefore
coexisted with booked revenue that had no payment event, contradicting the
cash-not-optimism accounting boundary.

Booked-pilot and booked-revenue totals now require `pilot-paid` itself. A later
stage still remains visible and continues to produce the existing missing-stage
warning, while source, readiness, and purchase-criterion revenue segments all
exclude the unsupported booking. Paid records that later become lost or enter a
terminal conflict still retain historical revenue because their payment label
is present.

## 2026-07-19: Keep Commercial Guides On The Exact Payment Boundary

After revenue recognition was corrected to require `pilot-paid`, the business
model, distribution guide, and pilot tracking guide still said later lifecycle
stages could stand in for that label. An operator following those words could
present a warning-bearing active or converted record as booked revenue even
though the reporter correctly excluded it.

All three commercial guides now state one shared rule: booked revenue requires
the payment label itself, and later labels cannot replace missing payment
evidence. A focused contract test requires that sentence in each guide and
rejects the prior inferred-payment wording. This changes no live funnel data and
creates no payment or revenue; it keeps buyer-facing and operator-facing
accounting instructions aligned with executable behavior.

## 2026-07-19: Require Public Lead History Before A Clean Loss Record

The cumulative pilot contract permits an opportunity to become lost from any
funnel stage, but every tracked opportunity must first carry `pilot-lead`.
Because loss is outside the ordered positive-stage tuple, a record containing
only `pilot-lost` was counted as a loss without the missing-stage warning that
all other skipped histories receive.

Loss remains an explicit human-applied outcome and is still counted, but a
lost-only record now warns that `pilot-lead` is missing. Records that include a
positive later stage continue through the existing cumulative-stage check, so
the change adds no duplicate warning. This creates no lead, loss, or revenue;
it prevents incomplete public request history from appearing warning-free.

## 2026-07-19: Retain Private Outcome Observation Dates

The guarded outcome command required an explicit human observation date but
discarded it after validating the action. A later classification could
therefore use an earlier date without contradicting any durable ledger field,
weakening the evidence history behind the private conversion experiment.

The current ledger adds `outcome_on` and records the date on every new outcome.
It rejects dates outside contact and follow-up chronology, future dates, and a
specific refinement dated before its original generic reply. Existing
nine-column ledgers remain readable and upgrade on their next guarded write;
historical outcomes without a date are counted as undated instead of receiving
invented evidence. This creates no outreach result, public lead, payment, or
revenue.

## 2026-07-19: Preserve The First Private Outcome Observation

The first `outcome_on` implementation rejected a classification date before a
recorded generic reply but then replaced that reply date with the later
classification date. The check prevented backdating while the write still
discarded the evidence it depended on.

A refinement now changes only the status and keeps the original `outcome_on`.
Fresh outcomes and legacy outcomes without a retained date still receive the
current human observation date. Source and installed-package lifecycle tests
prove a July 11 reply remains July 11 after a July 12 pilot classification.
This preserves private experiment history without creating a public request,
payment, or revenue event.

## 2026-07-19: Separate Outcome Events From Ledger Audit Dates

The outcome command used `--as-of` as both the complete-ledger audit date and
the human observation date. An operator recording a July 5 reply on July 10
either had to misdate the reply or audit the entire ledger as of July 5, which
could conflict with valid later activity elsewhere in the bounded batch.

`--record-outcome` now requires `--outcome-on` independently. The event may be
on or before `--as-of`, must still follow the selected prospect's contact and
follow-up history, and cannot predate a retained generic reply during
classification. Generated handoffs require both dates explicitly, and
installed-package coverage records a reply and classification on their actual
dates during a later audit. This improves private conversion evidence without
creating demand, payment, or revenue.

## 2026-07-20: Release Current Conversion Evidence Controls As v0.3.46

The public `v0.3.45` wheel predates the current guarded outcome history, public
pilot-intake handoff, exact payment recognition, and missing-lead warning.
Keeping those controls only on `main` leaves the installable operator workflow
behind the documented revenue boundary.

Version `0.3.46` advances the package, runtime, website download identity,
verification guide, release smoke fixture, and structured software offer
together. The release workflow must pass every source test and execute the
complete guarded outreach and commercial reporting lifecycle through the built
wheel before publishing checksums and provenance. Existing verified CI pins and
measured baselines remain on `v0.3.45` until separate artifact verification.
Publishing creates no prospect action, pilot request, payment, or revenue.

## 2026-07-20: Advance Both Policy Gates To Verified v0.3.46

The public `v0.3.46` wheel independently measures to SHA-256
`5a32dffabbeb7abf98d13fec5bca148830b8e80a1d4de0f6f424b1b57dc8db45`
and resolves through annotated tag `v0.3.46` to main-branch source commit
`6a352d76e0c22679096f7606c5bab1429872e961`.

Before changing either pin, all three downloaded artifacts matched the public
manifest and verified against GitHub build provenance. A fresh no-dependency
wheel installation reconciled all seven command identities and passed the
policy activation, guarded outreach lifecycle, commercial reporting, and
rollout-summary harnesses. The atomic maintainer updater then advanced the
dogfood workflow, copy-ready customer workflow, buyer-facing README claim,
commercial model claim, and executable pin contract together. Measured traffic
and funnel baselines remain at their last deliberate checkpoint. This improves
paid CI distribution integrity without proving a customer install, outreach
attempt, pilot request, payment, or revenue.

## 2026-07-20: Recover One Approved Send Without Reopening The Ledger

Approval previously emitted the exact guarded contact-recording command only
once. If that terminal output disappeared before the human sent the message,
the ordinary report showed an approved count but no alias, forcing manual CSV
inspection and command reconstruction inside the live five-draft queue.

Outreach report schema 8 now exposes only the lowest approved alias and, in
text output, regenerates the contact-recording command with separate required
audit and send-date placeholders. The recovery omits the draft, evidence,
channel, approval date, and recipient details; alias-bearing output remains
private. JSON receives the same single `next_approved` alias so automation can
resume deterministically. This makes an existing human-approved transition
recoverable without approving, sending, creating demand, or recording revenue.

## 2026-07-20: Mark Alias-Bearing Outreach Reports Private

The ordinary report can contain a private alias for either the next approved
manual send or a due follow-up. Omitting URLs, recipients, and draft text limits
exposure, but automation still had to inspect arbitrary JSON strings to decide
whether the report was safe to commit as a counts-only baseline.

Outreach report schema 9 adds a top-level `private_output` boolean and stable
`privacy_note`. A next-approved alias or any due-follow-up alias sets the flag
to `true` and warns that the report must not be committed or shared; a report
with neither alias source sets it to `false` and identifies itself as counts-only.
Text output prints the same classification. Publication still requires a final
check for aliases and identity data, but automation can now fail closed without
parsing prose or private values. This protects execution evidence without
reviewing, approving, sending, creating demand, or recording revenue.

## 2026-07-20: Fail Closed Before Publishing Private Outreach Reports

The schema-9 `private_output` flag lets careful consumers classify a report,
but publication scripts would still have to emit and parse alias-bearing JSON
before deciding to reject it. That leaves a preventable disclosure path in CI
logs, temporary artifacts, and scripts that forget the check.

`--require-counts-only` is therefore an ordinary-report-only guard. It is
mutually exclusive with every human review and lifecycle action. After ledger
validation, it emits text or JSON only when no next-approved or due-follow-up
alias is present. Otherwise it writes no report to standard output, emits an
alias-free diagnostic, and returns dedicated exit code 7. Invalid ledgers retain
exit code 2. This gives CI and baseline publication a stable fail-closed contract
without mutating outreach evidence or creating demand, payment, or revenue.

## 2026-07-20: Release Private Report Safeguards As v0.3.47

The public `v0.3.46` wheel predates approved-send recovery, schema-9 privacy
classification, and the fail-closed counts-only publication guard. Keeping
those controls on `main` would leave the installed five-draft workflow unable
to recover a lost approval receipt safely or stop private aliases before output.

Version `0.3.47` advances the package, runtime, portable download, website
identity, verification guide, and commercial smoke fixture together. The tag
must execute the complete guarded outreach lifecycle through the installed
wheel, including successful alias-free output and exit-7 rejection with empty
standard output for an approved alias, before checksums and provenance are
published. Existing verified CI pins and measured baselines remain on
`v0.3.46` until separate artifact verification. Publishing creates no prospect
action, pilot request, payment, or revenue.

## 2026-07-20: Advance Both Policy Gates To Verified v0.3.47

The public `v0.3.47` wheel independently measures to SHA-256
`bd59a65be2eb9695af0cd49ec09abdea35d963646c9382893fa768b8a94e2f9c`
and resolves through annotated tag `v0.3.47` to main-branch source commit
`4f7113b018d33622f556adb86905ef625378c8e0`.

Before changing either pin, all three downloaded artifacts matched the public
manifest and verified against GitHub build provenance from the exact release
workflow on a GitHub-hosted runner. A fresh no-dependency wheel installation
reconciled all seven command identities and passed the policy activation,
guarded outreach lifecycle, commercial reporting, and rollout-summary
harnesses; the portable artifact also matched the release identity and scanned
the repository. The atomic maintainer updater then advanced the dogfood
workflow, copy-ready customer workflow, buyer-facing README claim, commercial
model claim, and executable pin contract together. Measured traffic and funnel
baselines remain at their last deliberate checkpoint. This improves paid CI
distribution integrity without proving a customer install, outreach attempt,
pilot request, payment, or revenue.

## 2026-07-20: Keep The Project-State Pin Claim In The Same Transaction

Verified-pin upgrades changed both policy workflows, the copy-ready example,
buyer-facing README and business-model claims, and the executable CI contract
together. `PROJECT_STATE.md` carried the same current verified version but
still required a separate manual edit, leaving one repository-facing claim
outside the preflight and rollback boundary.

The maintainer updater now treats that exact project-state line as a sixth
transaction target. It requires exactly one recognized claim before staging
any write, preserves its permission bits, and rolls it back with every other
target if a later replacement fails. Historical release references remain
untouched. This reduces paid-CI distribution drift without changing a policy,
publishing a release, contacting a prospect, or creating demand or revenue.

## 2026-07-20: Reject Verified CI Release Downgrades Before Staging

The atomic updater validated version, source-commit, and wheel-digest shapes but
accepted any syntactically valid version. A stale command could therefore move
both paid-CI workflows and all synchronized claims back to an older release
without triggering layout or transaction safeguards.

Each of the six version-bearing targets now captures its current numeric
release and rejects an incoming lower major, minor, or patch tuple before any
temporary file is written. Equal versions remain valid so maintainers can
revalidate or reconcile the current artifact identities, and forward upgrades
retain the existing atomic replacement and rollback behavior. This prevents an
accidental distribution downgrade without claiming adoption, demand, payment,
or revenue.

## 2026-07-20: Separate Release-Pin Preflight From The Write Transaction

The maintainer updater already prepared every replacement in memory before
writing, but its command exposed only the mutating path. Reviewing a future
release identity against all six live layouts therefore also entered the
staging and replacement transaction.

`--check` now stops after the same shape, layout, and numeric downgrade
validation and reports each target as verified. It creates no temporary file,
does not replace repository content or permissions, and leaves the existing
write path unchanged when the flag is absent. This gives paid-CI distribution
upgrades a mutation-free review step without verifying provenance itself or
claiming customer activation, demand, payment, or revenue.

## 2026-07-21: Publish Complete Outreach Reviews Only To New Private Files

The next required commercial action is human review of five prepared drafts.
The complete review mode previously printed each selected alias, message, and
qualification source to standard output. Keeping that material beyond one
terminal session depended on shell redirection, which could inherit a permissive
umask, expose content to terminal capture, or silently replace an earlier review
receipt.

`--write-review` now accepts only `--review-next` text output. It requires an
existing owner-only parent, enforces the ignored and untracked boundary inside a
Git worktree, fully writes and syncs a `600` adjacent staging file, then uses an
atomic no-overwrite publication step. Existing files and symbolic links are
refused, staging paths are removed before every clean result, and standard output
contains no prospect alias. The outreach ledger is read but never changed. This
helps execute the bounded human queue without making a review decision, sending
outreach, or claiming pilot demand, payment, or revenue.

## 2026-07-21: Release Private Review Files As v0.3.48

The owner-only review-file path is covered by source tests and the installed
outreach lifecycle harness, but `v0.3.47` cannot expose it to the operator. The
five prepared drafts should not depend on a source checkout or an unverified
local package build for their human review boundary.

Version `0.3.48` advances the package and runtime versions, portable download,
website metadata, verification guide, and installed commercial fixture as one
release. Its tag must run all source tests, build the exact portable, wheel, and
source artifacts, then prove the new private write through the installed wheel
before provenance attestation. Existing paid-CI pins remain on independently
verified `v0.3.47` until the new manifest, tag ancestry, signer workflow, and
attestations are checked separately. The release creates no outreach attempt,
pilot request, payment, or revenue.

## 2026-07-21: Advance Paid CI Only After Independent v0.3.48 Verification

The release workflow built and attested `v0.3.48`, but its own success was not
enough to change the artifact identity trusted by customer and dogfood policy
gates. A separate download reconciled all three manifest entries, confirmed the
annotated tag resolves to the release commit, measured the wheel SHA-256, and
verified all three attestations against the pinned signer workflow, source ref,
source commit, and GitHub-hosted runner requirement.

Only after those checks passed did the atomic pin updater advance both
workflows, the buyer-facing claim, the commercial model, project state, and the
executable CI contract together. This reduces paid-CI supply-chain drift while
leaving the roadmap focused on five human-reviewed outreach attempts. It does
not establish a customer install, demand, payment, or revenue.

## 2026-07-21: Stop Automation At The First Real Human Review

The verified `v0.3.48` wheel created the first complete review bundle inside
the ignored owner-only workspace. The destination is a nonempty `600` file,
remains untracked, and left no staging file. Ledger bytes and the schema-9
counts-only report were unchanged: five drafts, 16 fit-evidence links, zero
approvals, zero attempts, and zero pilot requests.

That bundle is the handoff to human judgment, not evidence that judgment
occurred. Automation must not run either generated decision, send a message, or
record contact without the explicit checks and real-world action required by
the operator contract. The public baseline records only aggregate readiness so
the next run cannot mistake a prepared file for demand, payment, or revenue.

## 2026-07-21: Treat Review Cleanup Failure As A Partial Success

The private review writer publishes with a no-overwrite hard link and then
removes its hidden staging name. A filesystem failure during that final unlink
previously left both owner-only names present while the command still printed a
clean success receipt. The review content and ledger were safe, but the receipt
made the retained private copy invisible to the operator.

The command now distinguishes this state explicitly: it exits unsuccessfully,
says the intended review was written, and identifies a neutral retained staging
filename inside the private output directory instead of repeating a potentially
sensitive destination name. The operator removes that file instead of retrying;
the destination remains intact and overwrite-protected. This keeps private
evidence handling truthful for the active human review queue; it does not make a
review decision, send outreach, create demand, or record revenue.

## 2026-07-21: Release Truthful Review Cleanup As v0.3.49

The cleanup-failure behavior on `main` protects private review evidence only for
operators running an editable checkout. The active workflow uses verified
GitHub releases, and future review bundles need the same truthful partial-success
receipt without weakening the human decision boundary.

Version `0.3.49` advances package, portable, website, verification-guide, and
installed commercial-fixture identities together. The release must pass every
source test and prove the clean private review path through the installed wheel
before checksums and provenance are published. Paid-CI pins stay on independently
verified `v0.3.48` until the new public artifacts are reconciled separately.
Publishing the fix does not approve or send outreach, create demand, collect
payment, or record revenue.

## 2026-07-21: Advance Paid CI Only After Independent v0.3.49 Verification

The `v0.3.49` release workflow built and attested the private-review cleanup
fix, but its own success was not sufficient evidence for customer and dogfood
policy gates to trust a new artifact identity. A separate download reconciled
all three checksum entries, confirmed the annotated tag resolves to a commit on
`main`, measured the wheel digest, and verified each attestation against the
exact release signer workflow, semantic tag, source commit, and GitHub-hosted
runner requirement.

Only after those checks passed did the atomic six-target updater advance both
workflows, the buyer-facing README, commercial model, project state, and
executable contract together. This strengthens paid-CI supply-chain integrity
while leaving the existing owner-only review bundle and required human decision
untouched. It does not establish a customer install, outreach attempt, pilot
request, payment, or revenue.

## 2026-07-22: Treat Post-Release Requests As Confounded Reach, Not Demand

Four complete releases and the verified paid-CI promotion landed after the last
deliberate commercial checkpoint. That is enough distribution change to refresh
the public release, pilot, and joined growth evidence without creating another
acquisition asset or touching the private review queue.

The warning-free comparison records 50 additional primary artifact requests:
45 wheel and 5 portable. It also records 44 manifest and 5 source requests,
four new releases, zero pilot requests, and $0 booked revenue. The concentration
in wheels and manifests is consistent with release verification, pinning, and
CI activity, so the movement remains directional reach rather than users,
installs, leads, or willingness to pay. Acquisition remains the commercial
bottleneck, and the next action remains human review of the prepared outreach
queue rather than another product or acquisition feature.

## 2026-07-22: Make Failed Ledger Cleanup Visible Without Leaking Identity

Every human approval, decline, contact, follow-up, and outcome record stages a
complete private CSV replacement before it acquires the ledger lock. A failed
mutation previously attempted to remove that staging file in a `finally` block
and silently ignored an unlink failure. The current ledger remained safe, but
an operator could not know that another private copy had been retained.

Lifecycle staging files now use a neutral name unrelated to the private ledger.
When both the mutation and cleanup fail, the command reports the original
mutation error plus the exact neutral owner-only filename to remove. It omits
the cleanup exception because real filesystem errors can contain the sensitive
destination path. Failed replacement still preserves the original ledger bytes
and permissions. This strengthens the existing acquisition workflow without
reviewing a draft, sending outreach, creating demand, or recording revenue.

## 2026-07-22: Release Guarded Ledger Cleanup As v0.3.50

The truthful private-ledger cleanup behavior on `main` protects lifecycle
mutations only for operators running a source checkout. The bounded human
review queue uses verified installable commands, and its next real decision can
be an approval or decline followed by contact recording. Those mutations need
the same observable, identity-safe failure boundary before they are used.

Version `0.3.50` advances package, portable, website, verification-guide, and
installed commercial-fixture identities together. The release must pass the
source regression for simultaneous mutation and cleanup failure, then exercise
the guarded outreach lifecycle from the built wheel before publishing checksums
and provenance. Paid-CI pins remain on independently verified `v0.3.49` until
the new artifacts are reconciled separately. Publishing does not review a
draft, send outreach, create demand, collect payment, or record revenue.

## 2026-07-22: Advance Paid CI Only After Independent v0.3.50 Verification

The `v0.3.50` release workflow built and attested the guarded private-ledger
cleanup fix, but its own success was not sufficient evidence for customer and
dogfood policy gates to trust a new artifact identity. A separate download
reconciled all three checksum entries, confirmed the annotated tag resolves to
a commit on `main`, measured the wheel digest, and verified each attestation
against the exact release signer workflow, semantic tag, source commit, and
GitHub-hosted-runner requirement.

Only after those checks passed did the atomic six-target updater advance both
workflows, the buyer-facing README, commercial model, project state, and
executable contract together. This strengthens paid-CI supply-chain integrity
while leaving the owner-only review bundle and required human decision
untouched. It does not establish a customer install, outreach attempt, pilot
request, payment, or revenue.

## 2026-07-22: Bind Public Verification To The Paid-CI Artifact Identity

The public release guide required checksums and repository-scoped GitHub
attestations, but repository scope alone did not reproduce the identity contract
used by customer CI. It did not require the exact semantic tag, source commit,
release workflow, or GitHub-hosted runner for each artifact.

The checkout-free guide now peels the remote annotated tag to its 40-character
source commit inside a fail-closed Bash subshell, validates the exact resolved
ref and digest shape, and selects the checksum command available on Linux or
macOS. Every portable, wheel, and source attestation is constrained to the
repository, tag, source digest, signer workflow, and hosted-runner rule. The
release documentation test derives the artifact count, requires all five
constraints for every command, and checks the block's Bash syntax offline.

Dynamic lookup verifies the tag target currently published by GitHub, while
paid CI retains the stronger separately reviewed fixed source and wheel pins.
This aligns their identity dimensions without claiming equal immutability, and
does not establish an install, activation, pilot request, payment, or revenue.

## 2026-07-22: Require Complete, Index-Free Paid-CI Activation

GitHub CLI can return success when one release pattern matches even if another
requested asset is absent. Both policy gates previously ran `mv` after that
success condition, so a missing manifest aborted under Bash error handling
instead of entering the documented bounded retry path. The later local-wheel
install also disabled dependencies but did not explicitly forbid package-index
access or pip's remote version check.

Each attempt now succeeds only when the download returns zero, both the wheel
and manifest are regular files, and both promote into the trusted release
directory. Successful partial responses remain isolated and retry with the
same 5, 10, and 15-second waits; a fourth partial response exits explicitly.
The verified local-wheel install now disables package indexes, dependency
resolution, and pip's version check. Executable tests cover partial recovery,
terminal partial failure, byte-identical customer and dogfood install blocks,
and Bash syntax. This reduces paid-CI activation failures and mutable network
access without establishing customer usage, demand, payment, or revenue.

## 2026-07-22: Bind The Release Manifest To The Pinned Wheel

Paid CI independently checked the pinned wheel digest and then ran
`sha256sum --check --ignore-missing --strict` against the downloaded release
manifest. A local executable reproduction showed that GNU `sha256sum` can exit
successfully when every manifest entry names an absent file. The digest still
protected the wheel bytes, but the separate manifest check did not require the
manifest to identify that wheel at all.

Both customer and dogfood gates now require exactly one canonical manifest line
containing the pinned SHA-256 digest, two-space separator, and expected wheel
filename before checksum or provenance verification. Missing entries, altered
digests, and duplicate canonical entries exit before any attestation request.
The ordinary checksum pass remains in place to reject conflicting entries for
present files. Executable tests keep the two workflows byte-identical and prove
all three new failures without contacting GitHub. This strengthens paid-CI
artifact identity without establishing an install, customer usage, demand,
payment, or revenue.

## 2026-07-22: Require Payment Evidence Before Counting Conversion

The funnel treated an unconflicted `pilot-converted` label as a resolved annual
conversion even when the cumulative `pilot-paid` milestone was absent. The
record produced a skipped-stage warning and booked no revenue, but it still
increased summary and segmented retention totals. Pairing that record with a
separate paid, unconverted issue in the same source or purchase-criterion
segment could satisfy the growth report's aggregate conversions-at-most-booked
validation and publish unsupported retention evidence.

Resolved conversion accounting now requires both `pilot-paid` and an
unconflicted `pilot-converted` label. A skipped-payment record keeps its visible
converted stage and `missing_prior_stage` warning so the public history can be
repaired, but contributes zero to summary, source, readiness,
purchase-criterion, and joined growth conversion totals. This aligns retention
evidence with the existing payment boundary without mutating labels, erasing
warnings, or claiming a real payment or conversion.

## 2026-07-22: Require Canonical Outreach Dates Before Queue Ordering

Python's ISO parser accepts compact calendar dates and ISO week dates in
addition to the documented `YYYY-MM-DD` form. Outreach validation therefore
accepted a compact `next_action_on` value as the correct calendar date, while
the guarded follow-up selector still sorted the original strings. An earlier
compact date could sort behind a later canonical date and make the recorder
demand the wrong prospect first.

All nonblank outreach ledger dates and every CLI date argument now pass through
one canonical parser that requires the parsed date to round-trip exactly to its
input. Noncanonical spellings fail before queue selection, private file
mutation, or output. The guarded regression pairs an earlier compact due date
with a later canonical one, verifies controlled rejection, and proves the
ledger remains unchanged. This protects the bounded conversion experiment's
chronology without reviewing, approving, or sending any real outreach.

## 2026-07-22: Reject Non-Integer Pilot Reporting Controls

The Python funnel API annotated pilot price, target-pilot count, and stale-day
threshold as integers but only compared each value with one. Because booleans
are integer subclasses and floats support that comparison, both entered
schema-7 reports; numeric strings instead leaked an uncontrolled `TypeError`.
A report could therefore contain a JSON boolean or fractional commercial
assumption that downstream growth validation correctly refused.

All three controls now require a non-boolean integer greater than zero before
any issue is parsed. A regression matrix covers boolean, float, and
numeric-string inputs for each control and requires the existing
`FunnelInputError` messages. This keeps pilot pricing, revenue targets, and
follow-up thresholds internally consistent without changing the $299 offer,
creating demand, or touching private outreach evidence.

## 2026-07-22: Use None As The Only Commercial Report-Date Default

Pilot and outreach APIs selected their report date with `as_of or today` before
validating its type. Valid dates behaved correctly, but falsey non-date values
such as `False`, `0`, and an empty string silently became the current UTC date.
That could shift stale-deal, follow-up, and outcome windows while making the
caller believe an explicit historical value had been checked.

The pilot reporter now defaults only when `as_of is None`. All seven outreach
load and guarded-mutation wrappers use one resolver with the same rule and
reject any supplied non-date before ledger access. Regressions cover each
wrapper and all three falsey value classes, plus direct pilot funnel use. This
keeps commercial chronology explicit without reading private outreach data,
changing public funnel state, or creating demand or revenue.

## 2026-07-22: Keep Growth Recommendations Bound To Reported Pricing

The pilot funnel supports a validated custom price for direct callers, but the
joined growth report hard-coded `$299` in its offer-stage next action. A valid
report configured for `$400` therefore reconciled its revenue correctly while
still telling the operator to send the wrong commercial terms.

The growth report now passes the validated `pilot_price_usd` into bottleneck
selection and formats the offer recommendation from that value. A regression
proves a `$400` report recommends `$400` terms. This preserves the public `$299`
founding offer while preventing custom reports from producing contradictory
sales guidance; it does not create an offer, payment, or revenue event.

## 2026-07-22: Require GitHub Evidence Of Release Immutability

The release workflow called its publication step immutable, and the maintainer
guide described an immutable tag, but repository release immutability was not
enabled. GitHub reported `immutable: false` for `v0.3.50`, so its independent
digest and provenance protected artifact identity while deletion or replacement
could still interrupt the paid CI download path.

Repository-level release immutability is now enabled for future publications.
The release workflow publishes from the tested tag, queries that exact release
through GitHub's versioned REST API, and fails unless the `immutable` field is
exactly `true`. Executable tests cover true, false, malformed, and failed API
responses. Because GitHub does not apply this setting retroactively, the guide
and project state retain an explicit `v0.3.50` caveat until the next immutable
patch release is published and independently pinned.

## 2026-07-22: Release The First Immutable Artifact Set As v0.3.51

The paid-CI gates still depend on a mutable `v0.3.50` release even though their
fixed source commit, wheel digest, manifest, and provenance checks protect the
accepted wheel identity. Deletion or replacement at the release layer could
still interrupt a new team activation, so the next distributable boundary must
exercise the repository-level immutable-release setting before those pins move.

Version `0.3.51` advances package, portable, website, verification-guide, and
installed commercial-fixture identities together. Its tag must remain on
`main`, pass the complete source and installed-wheel contracts, publish all
three attested artifacts plus their checksum manifest, and make the exact
GitHub release API report `immutable: true` before the release job succeeds.

Customer and dogfood CI remain pinned to independently verified `v0.3.50` in
this change. The new manifest, annotated tag, source commit, signer workflow,
hosted-runner rule, and all three attestations require a separate reconciliation
before the atomic six-target pin update. Publishing creates no customer install,
pilot request, payment, or revenue.

## 2026-07-22: Advance Paid CI After Independent v0.3.51 Verification

The `v0.3.51` release workflow built and attested the first artifact set covered
by repository-level release immutability, but workflow success alone was not
enough evidence for customer and dogfood policy gates to trust a new identity.
A separate download matched all three artifacts to `SHA256SUMS`, confirmed the
remote annotated tag peels to a commit on `main`, and required GitHub's exact
release object to report `immutable: true`.

Each artifact then passed provenance verification against the exact repository,
semantic tag, source commit, release workflow, and GitHub-hosted-runner rule.
Only after those checks passed did the atomic six-target updater advance both
workflows, the buyer-facing README, commercial model, project state, and
executable contract to source commit
`e38c54c1564a65427ed6616eda180e5dadf40414` and wheel SHA-256
`506925aaba1acec2e4e4f6332753f1a140a0ec3d3ed133e15489613883e425b5`.

This reduces interruption and artifact-substitution risk in paid-CI activation
without treating verification as a customer install, outreach attempt, pilot
request, payment, or revenue.

## 2026-07-22: Separate Saved Site Versions From Public Publication

The production audit found that the public site still advertised `v0.3.50`
after the immutable `v0.3.51` release and paid-CI pin promotion. The monitor
correctly detected the mismatch, but the release guide moved directly from
artifact verification to a post-publication audit without specifying how the
tested source reaches the existing Sites project or when a saved version becomes
live. The same operational gap had appeared after an earlier release.

The release handoff now requires the lockfile install, production build test,
lint, exact-source push and save against the existing project, explicit owner
approval before a public deployment, and an immediate production audit after a
successful publish. Executable documentation coverage protects each boundary.
The exact `v0.3.51` source has been pushed and saved as Sites version 46, but the
public site remains on `v0.3.50` until the approval-gated deployment succeeds.

Preparing a deployable version closes part of a demonstrated distribution gap;
it does not create a visit, install, outreach attempt, pilot request, payment,
or revenue event, and it does not justify silently crossing the public publish
boundary.

## 2026-07-22: Require A Clean Site Dependency Tree Before Publication

The clean site install exposed known vulnerabilities in the public framework,
image-processing, CSS-processing, local-worker, and development-server paths.
The production subset included a high-severity Sharp advisory and a moderate
PostCSS advisory. The complete build tree also included supported fixes in
Next, Cloudflare's Vite plugin, Wrangler, Vite, and transitive tooling. npm's
automatic forced remedy proposed an incompatible Next downgrade, so it was not
used.

The site now uses the current stable Next security patch and matching lint
rules, supported Cloudflare and Vite toolchain updates, and root overrides for
the advisory-fixed PostCSS and Sharp versions. A non-forced lockfile refresh
updated the remaining affected transitive packages within their declared
ranges. The complete 498-package install reports zero vulnerabilities, and the
release handoff now requires that audit before a version can be saved or
approved. Executable contracts pin the direct versions, override values,
resolved lock entries, and audit command. A runtime smoke test processes an
image with the newer Sharp release and starts Miniflare because those parent
packages have not yet widened their declared Sharp ranges.

The dependency update passes the production build and rendered-offer suite on
the minimum supported Node `22.13.0`. Sites version 46 is therefore superseded
and must not be published; only an exact-source save of the security-hardened
commit may cross the separate owner-approval boundary. This reduces buyer-path
supply-chain risk but does not create a visit, install, request, payment, or
revenue event.

## 2026-07-22: Recheck The Buyer-Path Dependency Contract In Hosted CI

The zero-vulnerability lock and local compatibility tests protected the saved
site candidate, but a new advisory can be published while that lock remains
unchanged. Waiting for the next manual publication handoff would leave the
buyer path silently stale, while running the complete site toolchain on every
repository commit would add unrelated CI cost during the 1,000-commit cadence.

A dedicated hosted contract now runs when the package manifests, compatibility
test, or workflow changes, on explicit manual dispatch, and every Monday. It
uses the exact minimum Node `22.13.0`, installs the committed lock, fails on any
reported vulnerability, builds and runs the site and override compatibility
tests, and lints. Checkout and Node setup actions are pinned to complete commit
identities; the job has only read access, receives no repository secrets, and
cannot publish a saved version or deploy production.

The previously audited source commit is now saved as Sites version 47, while
the public site remains on `v0.3.50` behind the existing owner-approval gate.
The hosted contract reduces the chance that vulnerable buyer-path dependencies
reach that gate; neither a passing run nor a saved version is evidence of a
visit, install, pilot request, payment, or revenue.

## 2026-07-23: Turn Dependency Findings Into Bounded Review Proposals

The hosted contract detects newly disclosed dependency risk, but repository
vulnerability alerts and automated security-fix proposals were disabled. A
failed weekly audit would therefore still depend on a maintainer noticing the
run, identifying the affected transitive path, and manually preparing an update
before the buyer path could recover.

Repository vulnerability alerts and automated security fixes are now enabled.
The committed Dependabot policy groups all npm security updates while setting
the npm version-update limit to zero, so ordinary package releases do not flood
the commercial execution queue. Pinned GitHub Actions are checked weekly;
minor and patch changes are grouped, while at most two version-update pull
requests may remain open. No rule auto-merges, publishes, or deploys anything.

The hosted dependency workflow now runs when either policy, its contract test,
or any workflow changes. It runs the full repository suite before the clean
install, zero-vulnerability audit, build, runtime compatibility checks, and
lint. This turns a supply-chain signal into a bounded, reviewable repair path
without crossing the public-site approval boundary or pretending maintenance
is buyer demand, payment, or revenue.

## 2026-07-23: Advance Action Pins Only Through Their Full Contract

The first weekly action proposals demonstrated the intended review boundary.
Dependabot changed the runtime workflow references, while independent tests and
the copy-ready customer gate retained the previously accepted identities and
made the hosted dependency contract fail. That failure was evidence of a
partial update, not permission to weaken the expectations or merge around them.

The `actions/checkout` patch was reviewed first because `v7.0.1` retains the
same major interface while adding checkout-safety and Git-config handling fixes.
Its upstream tag resolves to GitHub-verified commit
`3d3c42e5aac5ba805825da76410c181273ba90b1`. All five hosted workflows, the
customer example, and four executable pin expectations now accept that exact
identity together. The unrelated `actions/setup-python` 7 major proposal stays
open for a separate compatibility decision.

This keeps action updates bounded, reviewable, and fail-closed across the paid
CI activation surface. It does not auto-merge a proposal, publish or deploy the
site, establish customer use, or create demand, payment, or revenue evidence.

## 2026-07-23: Validate A Major Action Against Used Inputs And Hosted Activation

The remaining Dependabot proposal advanced `actions/setup-python` from
`v6.3.0` to `v7.0.0`. Its major boundary includes an ESM migration, dependency
updates, manifest-fetch retries, and removal of the `pip-install` input. A major
proposal therefore required compatibility evidence beyond changing the four
hosted workflow lines generated by Dependabot.

The `v7.0.0` tag resolves to GitHub-verified commit
`5fda3b95a4ea91299a34e894583c3862153e4b97`. Both accepted versions use the
Node 24 action runtime. Repo Scout supplies only `python-version`, whose action
contract is unchanged, and no workflow or example supplies the removed
`pip-install` input. On the proposal commit, GitHub Actions successfully set up
CPython 3.11.15, ran the pilot contract, and completed the paid-CI path through
release download, checksum and provenance verification, index-free wheel
installation, policy enforcement, and rollout evidence upload.

All four hosted Python workflows, the copy-ready customer gate, and three
independent executable pin expectations now accept that exact commit together.
The tag-only release workflow and scheduled production audit were not invoked
outside their normal boundaries; their unchanged input and exact action identity
remain statically contract-tested until those jobs next run normally.
This closes the bounded action-review queue without auto-merging, publishing,
deploying, creating a customer install, or recording demand or revenue.

## 2026-07-23: Audit Every Action Surface Without Automating Approval

The checkout and setup-python reviews proved that independent pin expectations
can stop partial Dependabot proposals. Those exact contracts covered 13 of the
15 external action references, however. The checkout and Python setup steps in
the hosted pilot-intake workflow had no direct action-identity contract, so a
maintainer could reconcile every previously tested surface while leaving that
paid-conversion workflow stale.

A repository-wide audit now discovers external `uses:` references in all five
hosted workflows and the copy-ready customer gate. Every reference must use a
40-character lowercase commit SHA and one exact semantic release annotation.
One action cannot resolve to multiple SHA/version identities anywhere in those
surfaces, and the dogfood and customer policy gates must retain the same action
sequence. The existing action-specific contracts still assert the exact
accepted commits and workflow behavior.

The audit deliberately does not update pins or contact GitHub. A consistent
repository cannot prove that a tag resolves to the expected commit, that a
major version preserves the used inputs, or that hosted behavior remains
compatible. Those remain explicit review decisions backed by upstream and
hosted evidence. Passing the audit does not merge a proposal, publish or deploy
the site, create a customer install, or record demand, payment, or revenue.

## 2026-07-23: Run The Action Audit Explicitly In Hosted CI

The repository-wide action audit was executable and covered by the local unit
suite, but its first push did not select the hosted dependency workflow. The
audit script and its test were outside that workflow's path filters. Relying
only on test discovery also meant deleting the test could remove hosted
enforcement while allowing the remaining suite to pass.

The dependency workflow now watches both audit files on pull requests and
`main`, in addition to every workflow definition. It invokes the audit directly
after credential-free checkout and before Node setup or general test discovery,
then continues through the existing locked install, zero-vulnerability
dependency check, production build, runtime compatibility tests, and lint. The
workflow contract requires both trigger paths and the explicit command in that
order.

This closes the hosted selection and test-deletion gaps without granting write
permission, exposing secrets, automating upstream pin approval, saving a site
version, or deploying production. A passing run proves only that the reviewed
repository surfaces remain internally consistent; it is not customer usage,
demand, payment, or revenue evidence.

## 2026-07-23: Contract-Test The Public Pilot Intake Workflow

The public issue form, delivery documents, label definitions, and funnel logic
already selected a read-only hosted check. The workflow itself had no dedicated
contract, however. A change could weaken its trigger coverage, permissions,
immutable action identities, runtime bound, exact test set, or non-repairing
live-label command while the underlying unit tests continued to pass locally.

A dedicated workflow contract now requires pull-request, `main`, and manual
triggers; every intake and delivery dependency in both path blocks; one
read-only `contents` and `issues` permission map; full action commit pins; a
two-minute job bound; the exact workflow, label, and delivery test modules
before the live audit; and the repository token without repository secrets.
Both trigger blocks include `DISTRIBUTION.md`, which the paid-delivery contract
reads. Repair mode, failure masking, unapproved events, extra run commands, and
write permissions remain forbidden. The workflow runs and watches the contract
file itself on both code paths.

This protects the existing public conversion path without adding another
acquisition asset, making a qualification decision, changing a label, or
contacting anyone. A passing contract proves intake infrastructure consistency,
not a lead, demand, payment, or revenue.

## 2026-07-23: Patch The Source-Distribution Builder Before Another Release

GitHub advisory `GHSA-h35f-9h28-mq5c` marks `setuptools` versions below
`83.0.0` vulnerable to a Unicode-normalization mismatch in `MANIFEST.in`
exclusions. Repo Scout pinned `80.9.0` in its release-only requirements and
publishes a source archive, so the affected behavior sat directly on the public
artifact trust path even though the dependency is not installed by CLI users.

The release lock now uses the non-yanked `setuptools` `83.0.0` wheel and exact
SHA-256 digest published by PyPI. Its Python `>=3.10` requirement includes the
release workflow's Python 3.11 runtime. The contract test now compares the
complete canonical lock text, binding all four package names and versions to
their specific hashes instead of accepting any four well-shaped hashes.

A fresh environment installed the complete lock with `--require-hashes`,
reported no broken requirements, and rebuilt the source archive, wheel,
portable CLI, and checksum manifest without isolation. This repairs release
infrastructure only: no tag or release was created, no public artifact changed,
and no customer install, demand, payment, or revenue was recorded.

## 2026-07-23: Prove Release Tooling Before A Tag Exists

The tag-driven release job safely installs the hash-locked builder before
publishing, but a bad lock digest or incompatible build-tool change would be
discovered only after creating a release tag. Reusing the site dependency job
would mix Python publication inputs with the Node production-site lock and make
both contracts less legible.

A dedicated pre-tag workflow now watches the release lock, release workflows,
packaging metadata, packaged source and tests, license, README, and build
scripts. On pull requests, `main`, or manual dispatch, one five-minute
read-only job checks out the exact candidate without credentials, sets up
Python 3.11, runs the release and workflow contracts, creates a fresh
runner-temp virtual environment, force-installs the builder with
`--require-hashes`, checks dependency compatibility, and generates the portable
CLI, wheel, source archive, and checksum manifest in runner temp.

The workflow cannot trigger from a tag, use repository secrets, write
repository content, attest or upload artifacts, or create a release. The
tag-driven release job remains the only publication boundary. A passing
candidate build protects paid-CI distribution trust but is not a public
artifact, customer install, demand, payment, or revenue event.

## 2026-07-23: Bind Publication To An Annotated Exact-Commit Tag

The public verification procedure resolves `refs/tags/vX.Y.Z^{}` so operators
can bind checksums and attestations to the tag's peeled source commit. The
publishing workflow required a matching semantic tag and main ancestry, but it
did not require an annotated tag object. A lightweight tag could therefore
reach the build while making the documented remote peel check impossible.

Before main-branch ancestry, tests, builds, attestations, or release creation,
the release job now requires `refs/tags/$GITHUB_REF_NAME` to be a Git tag object
and requires its peeled commit to exactly equal the GitHub push commit. An
executable contract runs the guard in temporary repositories and proves one
annotated exact-commit tag passes while a wrong-commit annotation and a
lightweight tag fail.

The guard does not create, move, sign, or publish a tag. Maintainers retain the
human release decision, and the immutable-release check remains the
post-publication boundary. Passing the guard is distribution-integrity
evidence, not a release, customer install, demand, payment, or revenue event.

## 2026-07-23: Isolate The Actual Publication Build

The pre-tag workflow force-verified every hash-locked build wheel in a fresh
virtual environment, but the tag-only publisher still installed into the
ambient setup-python environment. A matching package already present on the
runner could satisfy pip without rechecking its artifact hash, and unrelated
ambient packages remained visible to the no-isolation backend build.

The release job now creates a dedicated runner-temp build environment,
force-installs the complete hash-locked release requirements, and requires
`pip check` to report no broken dependencies. The portable builder, package
builder, and checksum preparer all run through that exact interpreter. The
separate wheel-smoke environment remains unchanged so installation evidence
does not share the build environment.

An executable workflow contract requires the fresh environment, forced hash
verification, dependency check, exact interpreter reuse, and step ordering. A
disposable Python 3.11 source copy also rebuilt the zipapp, wheel, source
archive, and checksum manifest through the isolated environment. This changes
publication infrastructure only; it creates no tag, release, customer install,
demand, payment, or revenue evidence.

## 2026-07-23: Revalidate Release Artifacts At The Attestation Boundary

The isolated release builder wrote `SHA256SUMS` before the wheel and portable
smoke tests exercised the artifacts. Provenance attestation later consumed that
manifest without a final byte check, leaving a narrow integrity gap if a
current or future smoke step changed an artifact after its digest was recorded.

The publishing workflow now revalidates every manifest entry from `dist` after
both smoke steps and immediately before attestation. It uses `sha256sum` when
available and the macOS-compatible `shasum` fallback, without ignoring missing
files or masking a failure. The same manifest then becomes the attestation
input.

An executable contract extracts the exact workflow script, proves three intact
artifacts pass, mutates the wheel after manifest creation, and proves the
release stops. This strengthens paid-CI distribution integrity only; no tag,
release, customer install, demand, payment, or revenue evidence was created.

## 2026-07-23: Execute Release Candidates Before Tagging

The pre-tag workflow proved the release contracts and built all four candidate
files, but it discarded them without installation or execution. Packaging or
entry-point failures could therefore remain hidden until a maintainer created a
tag and entered the publication workflow.

After the isolated build, the pre-tag workflow now creates a second virtual
environment and installs the exact candidate wheel with dependency resolution
and pip's remote version check disabled. It reconciles every command declared
in `[project.scripts]` to the candidate version, runs the primary help path,
then executes the candidate zipapp for its version, help, and a real JSON
repository scan. The trigger surface now includes all four release smoke
helpers consumed by the release contracts.

The executable workflow contract requires the separate environments, exact
local wheel path, complete command set, portable execution, and build-before-
smoke ordering. Candidate files remain in runner temp with read-only workflow
permissions and no upload, attestation, tag, or publication authority. Passing
this check strengthens paid-CI distribution readiness; it is not a customer
install, demand, payment, or revenue event.

## 2026-07-23: Keep Release Smoke Installs Offline And Exact

The customer and dogfood policy gates already installed one independently
verified local wheel without package indexes, dependency resolution, or pip's
remote version check. The pre-tag candidate smoke disabled dependencies and the
version check but still allowed index access, while the publication smoke used
`dist/*.whl` and left pip's version service enabled.

Both release smoke environments now install one canonical
`repo_scout-VERSION-py3-none-any.whl` path derived from the candidate version or
validated tag. `--no-index`, `--no-deps`, and
`--disable-pip-version-check` prevent the smoke proof from consulting a mutable
registry or accepting an ambiguous wheel set. The build-tool installation
remains separately hash-locked because it intentionally downloads the release
toolchain.

Executable contracts reject a missing flag, wildcard path, alternate index, or
find-links escape and preserve the build-before-smoke order. This narrows the
paid-CI publication trust path without creating a tag, release, customer
install, demand, payment, or revenue evidence.

## 2026-07-23: Move Installed-Wheel Acceptance Before Tags

The pre-tag workflow installed the candidate wheel, reconciled all seven entry
points, and executed the portable CLI, but the deepest business-workflow smoke
tests still ran only after a maintainer created a publication tag. A candidate
could therefore package correctly while breaking paid policy activation,
guarded outreach, pilot-funnel accounting, or rollout evidence.

The candidate smoke now runs the same four scripts, in the same order, against
its isolated installed wheel: `smoke_test_policy_activation.py`,
`smoke_test_outreach_lifecycle.py`, `smoke_test_pilot_funnel.py`, and
`smoke_test_rollout_summary.py`. Each script receives the candidate
interpreter and command directory, preserving the package-index-free install
boundary.

An executable parity contract derives the ordered script list independently
from both workflows and fails if either side adds, removes, or reorders an
acceptance journey. This moves paid-workflow packaging failures before the
human tagging decision without granting publication authority or creating a
release, customer install, demand, payment, or revenue evidence.

## 2026-07-23: Prove The Source Archive Rebuilds The Tested Wheel

The release contracts validated, checksummed, attested, and published one source
archive, but only the separately built wheel and portable artifact were
executed. A source archive could therefore remain well named and
cryptographically bound while omitting package files, entry points, policy
templates, or mode metadata required to reproduce the installable distribution.

Both the read-only pre-tag workflow and tag-only publisher now ask the same
hash-locked release interpreter to rebuild the exact versioned source archive.
The rebuild disables package indexes, wheel caches, dependency resolution, and
build isolation, so it cannot replace the reviewed toolchain or fill a missing
source file from a registry or prior build. A structured ZIP comparison rejects
duplicate members and requires the rebuilt wheel to match every direct-wheel
member name, byte digest, size, and stored 16-bit mode. ZIP timestamps,
ordering, and compression remain intentionally irrelevant because they do not
change installed contents.

The rebuilt wheel stays in runner temp and is neither added to `SHA256SUMS` nor
published. The direct wheel continues through the complete installed-command
acceptance suite, and the original source archive remains the attested artifact.
Passing this gate proves source-distribution parity only; it creates no tag,
release, customer install, demand, payment, or revenue evidence.

## 2026-07-24: Publish Release Checksums Without Following Paths

Release preparation allowed an existing `SHA256SUMS` entry but wrote it
directly. If that entry was a symlink, the write followed it outside the
validated release directory; an interrupted direct write could also truncate a
previously valid manifest.

The checksum writer now inspects the destination without following links and
accepts only an absent path or an existing regular file. It preserves the mode
of an existing manifest, writes the complete ASCII payload to a unique
same-directory staging file, flushes and syncs that file, and publishes it with
atomic replacement. Failed writes clean up their staging file and leave the
previous manifest intact.

Regression tests prove a symlink cannot redirect checksum bytes and a failed
replacement cannot destroy prior evidence. This hardens the paid-CI
distribution trust boundary only; no tag, release, customer install, demand,
payment, or revenue evidence was created.

## 2026-07-24: Run Funnel Behavior In Pilot Intake CI

The dedicated pilot-intake workflow selected changes to the funnel reporter but
ran only its workflow, label-audit, and delivery-contract tests. Its complete
behavioral suite was absent, so a regression such as counting
`pilot-converted` without explicit `pilot-paid` evidence could leave the
revenue-focused hosted check green.

The hosted test step now runs `tests.test_pilot_funnel` before the live label
audit. Both pull-request and `main` trigger blocks watch the behavioral test and
its `pilot_issues.json` revenue fixture, and the workflow contract requires the
exact expanded command and trigger surface.

This closes a conversion-accounting blind spot without changing the reporter,
labels, public intake, or human sales process. Passing the hosted check remains
infrastructure evidence only; it does not create a lead, payment, conversion,
or revenue event.

## 2026-07-24: Self-Test The Production Conversion Audit

The scheduled production workflow executed the live auditor directly. If a
parser or assertion regression made the auditor accept stale release metadata,
an incorrect $299 service, or a broken website-attributed application link, the
daily job could remain green without proving its detector still worked.

The workflow now runs `tests.test_production_site_workflow` and
`tests.test_production_site_audit` before requesting the public page. Those
contracts prove the read-only workflow shape and exercise accepted production
HTML plus stale release, malformed offer, and missing conversion-link failures.
The live audit remains the final step and still fails on network or production
drift.

This strengthens the existing buyer-path monitor without changing or deploying
the site. A passing self-test or live audit is operational evidence only; it is
not a visit, pilot request, payment, or revenue event.

## 2026-07-24: Audit The Visible Production Download

The production audit reconciled the current portable release only through
`SoftwareApplication.downloadUrl` and its structured free offer. Those fields
could remain correct while the visitor-facing anchor was removed or left on an
older release, allowing the monitored buyer path to pass without offering a
clickable current download.

The audit now requires the exact current portable release URL among the page's
anchors and reports that check separately from structured metadata. Regression
tests reject both missing and stale visible links while holding the structured
release identity current.

This closes an activation-path blind spot without changing or deploying the
site. The saved Sites version remains subject to explicit owner approval, and a
passing audit creates no visit, pilot request, payment, or revenue evidence.

## 2026-07-24: Bind The Visible Pilot Price To Its Application

The production audit required the structured service to cost $299 and required
a website-attributed application URL, but it treated those as independent
facts. The public page could therefore leave the CTA unpriced or label it with a
different price while the monitor remained green.

The HTML parser now retains normalized anchor labels. The audit requires at
least one website-attributed application link to disclose the exact $299 price
and reports that visitor-facing check separately from the structured service
and destination URL. Regressions hold the structured offer constant while
proving an unpriced label and a $399 label both fail.

This protects price clarity at the conversion point without changing or
deploying the site. It creates no visit, application, payment, or revenue
evidence, and Sites version 47 remains subject to explicit owner approval.

## 2026-07-24: Publish Only The Exact Release Artifact Set

Release preparation rejected missing, extra, and incorrectly named artifacts,
then the workflow smoke-tested and revalidated the exact manifest. The final
`gh release create` command nevertheless rediscovered the wheel, source
archive, and portable CLI through shell globs. A matching file introduced after
preparation could therefore widen the upload beyond the names that the command
intended to publish.

The publisher now derives the version from the already validated semantic tag
and names all three canonical artifact paths explicitly alongside
`SHA256SUMS`. The executable publication contract requires each path exactly
once in both workflow source and the expanded fake-GitHub invocation, and
rejects every wildcard in that step.

This makes final upload authority match the checksummed and attested artifact
set. It does not create a tag, release, customer install, demand, payment, or
revenue evidence.

## 2026-07-24: Repair Newly Disclosed Buyer-Path Dependency Risk Without Audit Suppression

The exact-SHA hosted checks for the release-publication change selected the site
dependency contract. That contract failed on two high-severity denial-of-service
advisories reviewed by GitHub on July 24: the installed React Server Components
19.2 line before `19.2.8`, and every `brace-expansion` release through `5.0.7`.
The second finding reached both ESLint and TypeScript lint paths. This was
current supply-chain evidence, not a flaky runner or permission to omit
development dependencies from `npm audit`.

React, React DOM, and `react-server-dom-webpack` now use `19.2.8`.
`brace-expansion` is pinned to its only patched release, `5.0.8`. Because the
legacy `eslint-config-next` bundle still required minimatch lines that could not
consume that release, it was replaced with direct ESLint 10, TypeScript, React
Hooks, and official Next core-web-vitals rule sets. The executable lock contract
requires those exact packages, rejects the legacy bundle, and proves every
resolved `brace-expansion` copy is `5.0.8`.

A fresh lock install reports zero vulnerabilities and passes the production
build, eight site and runtime tests, lint, 299 Python tests, and the immutable
action-pin audit. Sites version 47 contains the prior vulnerable lock and is
therefore superseded before deployment. No Sites version was saved or deployed,
and no visit, pilot request, payment, or revenue evidence was created.

## 2026-07-24: Bind Sites Candidates And Separate Export Approval

Preparing a replacement for superseded Sites version 47 reached the existing
Sites project's source handoff. Saving a version requires pushing the complete
repository state to a separate Sites-managed source repository. The documented
handoff gated only production deployment, so it did not establish explicit
consent for that earlier source export. The push was refused before repository
contents left the existing origin.

Repo Scout's paid offer targets security-conscious teams and promises local
operation without source-code uploads. Source export is therefore a material
trust boundary even when the destination only prepares a non-live version.

The existing packaging helper also accepted ignored `dist/` output without
proving it came from the current tested source. A stale build could therefore
be saved against a newer commit identity. The repository now owns a fail-closed
preflight that requires a clean checkout synchronized with `origin/main`, exact
hosted Node `22.13.0`, locked installation, the unsuppressed dependency audit,
the production test build, and lint. It embeds the commit, lock digest, runtime,
and existing Sites project in the archive, verifies the package, and writes a
receipt containing the archive digest.

The handoff now orders that preflight, explicit source-export approval, the
receipt's exact source push, receipt-matched version saving, separate deployment
approval, production deployment, and the immediate live audit. Its executable
contract requires the export approval before the push and the deployment
approval afterward. Export consent explicitly cannot authorize production.

No source was pushed to Sites, no replacement version was saved, production was
not changed, and no visit, pilot request, payment, or revenue evidence was
created.

## 2026-07-24: Independently Verify Sites Candidates Before Each Handoff

The Sites preflight verified its archive while producing it, but the release
guide later asked an operator to confirm the archive digest and project identity
manually before saving. There was no executable way to prove that the archive
and receipt still matched the exact synchronized checkout at either the
source-export approval boundary or the later version-save boundary.

The existing candidate tool now has a read-only `--verify-only` mode. It
requires clean `HEAD == origin/main`, strictly accepts only the current receipt
schema, reconciles the receipt's commit, lock digest, hosted Node identity, and
Sites project with the checkout, recomputes the archive digest, and validates
the embedded manifest and project identity. It invokes no Node, npm, packaging
helper, network request, source export, version save, or deployment action.

The handoff runs verification immediately before asking for source-export
approval and repeats it after the approved source push but before saving the
archive. Verification makes both human decisions refer to the same tested
candidate; it does not grant either approval or collapse source-export approval
into deployment approval.

No source was exported, no Sites version was saved or deployed, and no visit,
pilot request, payment, or revenue evidence was created.

## 2026-07-24: Use One Exact Runtime Pin For Sites Candidates

The candidate preflight required exact Node `22.13.0`, the hosted dependency
workflow duplicated that literal, and package metadata correctly expressed the
broader `>=22.13.0` compatibility floor. This checkout had only Node `26.0.0`
and no repository runtime selector, so an operator could discover the exact
candidate requirement only after invoking the preflight.

The repository now stores `22.13.0` in `.nvmrc`. Candidate preparation strictly
parses that file before any Git, Node, npm, or packaging command, compares the
active runtime with it, and records it in the candidate manifest. Independent
verification derives the expected receipt from the same pin. The hosted
dependency workflow also reads `.nvmrc` and watches it in both trigger blocks.
Package metadata remains `>=22.13.0`; it is a compatibility contract, not a
candidate identity.

The release handoff now selects the pin with `nvm install` and `nvm use` before
preflight. This makes the exact patched-site candidate reproducible across
local and hosted checks without weakening the paid distribution boundary. No
source was exported, no Sites version was saved or deployed, and no visit,
pilot request, payment, or revenue evidence was created.

## 2026-07-24: Constrain Sites Candidates To Deployable Output

The candidate validator rejected traversal paths and links but otherwise
accepted any archive member once the required server, hosting metadata, and
candidate manifest were present. A misconfigured packaging helper could
therefore include unrelated repository source, a credential file, or a special
filesystem entry and still receive a valid receipt before the separate Sites
source-export boundary.

Candidate archives must now contain only canonical paths rooted under `dist/`.
Every member must be a regular file or directory; aliases, links, devices,
pipes, and entries elsewhere are rejected during both preparation and
independent verification. A failed archive never receives a receipt.

This keeps the artifact handed toward paid-site distribution limited to
deployable output and makes the local-code promise fail closed. It does not
approve source export, save a Sites version, authorize production deployment,
or create a visit, pilot request, payment, or revenue event.

## 2026-07-24: Bind Sites Receipts To The Tested Build Payload

Candidate preparation tested `dist/` and then invoked a trusted external
packaging helper. Git cleanliness could not detect changes to that ignored
directory, while the archive manifest proved source identity but did not bind
the server and client bytes. A changed file or an extra deployable file added
between testing and packaging could therefore receive a valid receipt.

Before the helper runs, preparation now computes one digest over every regular
payload file's canonical archive path, permission mode, size, and bytes,
including the candidate manifest and final Sites metadata overlays. The helper
output must reproduce that digest exactly. Schema-2 receipts store the payload
digest beside the complete archive digest, and `--verify-only` independently
recomputes both without Node, npm, a build, or packaging. Schema-1 candidate
receipts fail closed because they predate payload binding.

An actual macOS run of the bundled Sites helper exposed an AppleDouble
`._dist` entry created by `tar`. Packaging now sets `COPYFILE_DISABLE=1`; the
real helper then passes without relaxing the archive root. This preserves the
same strict artifact on macOS and hosted Linux.

The receipt now proves that the artifact awaiting approval is the tested build,
not only a source label. No source was exported, no Sites version was saved or
deployed, and no visit, pilot request, payment, or revenue evidence was created.

## 2026-07-24: Hold One Synchronized Commit Across Candidate Operations

Candidate preparation required a clean `HEAD == origin/main` checkout at entry
and rechecked worktree cleanliness after validation and packaging. A concurrent
clean commit, reset, or remote-tracking ref move could therefore leave those
later checks green while the receipt retained the original commit identity.
Read-only verification had the same entry-only source observation.

Preparation now repeats the full clean synchronized-source proof after the long
validation phase and after packaging, and both observations must retain the
original commit SHA before a receipt is written. Independent verification
repeats that proof after reconciling the archive and receipt before reporting
success. Persistent worktree, `HEAD`, or `origin/main` drift fails closed.

This brackets each approval-evidence operation with the same source identity
instead of describing only its starting instant. It does not lock the
repository, approve source export, save or deploy a Sites version, or create a
visit, pilot request, payment, or revenue event.

## 2026-07-24: Test-Bracket The Exact Sites Payload

Candidate preparation previously ran the combined production build and site
tests before computing the expected payload digest. Because `dist/` is
intentionally ignored, a persistent file change or injection after `npm test`
returned but before the first digest could become the accepted baseline without
affecting Git cleanliness.

Preparation now installs, audits, lints, and builds once, writes the
deterministic candidate manifest, and captures the complete payload path,
permission mode, size, and byte digest. A separate `npm run test:site` command
then exercises that exact existing `dist/` without rebuilding. Preparation
repeats the digest after the tests and refuses to invoke the packaging helper
if any payload byte changed; the archive comparison still rejects later
packaging-time drift.

Receipts advance to schema 3 so schema-2 evidence created without this test
bracket fails closed. Built server and client output is test-bracketed, while
hosting metadata, Drizzle configuration, and the embedded manifest are
integrity-bound and structurally checked. No source was exported, no Sites
version was saved or deployed, and no visit, pilot request, payment, or revenue
evidence was created.

## 2026-07-25: Bind Sites Receipts To The Complete Payload Tree

The schema-3 payload digest covered every regular file's canonical path,
permission mode, size, and bytes but skipped tar directory entries. A packaging
helper could therefore add an unexpected empty directory or change an expected
directory's permissions and still receive a valid receipt. Directory
permissions affect whether extracted server and asset paths can be traversed,
so equal file bytes alone did not prove equal deployable behavior.

Schema-4 receipts digest every regular directory and file. Each entry
contributes its canonical archive path, file-or-directory type, and permission
mode; regular files additionally contribute size and bytes, while directory
size is normalized to zero across the filesystem and tar representations. The
bundled helper creates staging directories under the process umask instead of
preserving every source directory mode. Preparation therefore requires every
tested payload directory to use deterministic mode `0755`, and invokes
packaging under an explicit `022` umask. Noncanonical source modes fail before
packaging, archive mode drift fails before a receipt, and independent
verification reproduces the same complete-tree digest.

This keeps the artifact awaiting paid-distribution approval identical at the
filesystem boundary, including an intentionally empty Drizzle metadata
directory. No source was exported, no Sites version was saved or deployed, and
no visit, pilot request, payment, or revenue evidence was created.

## 2026-07-25: Reject Ambiguous Sites JSON Evidence

Sites candidate verification strictly checked schema versions, exact key sets,
source identity, payload bytes, and archive structure, but its JSON decoder
silently accepted repeated object keys. JSON consumers differ on whether the
first or last repeated value wins, so a receipt or archived manifest could have
one byte representation and multiple effective identities. Repeating the same
value still leaves evidence ambiguous because later tooling can normalize it
differently.

One duplicate-rejecting object parser now covers checkout hosting metadata,
candidate receipts, and archived hosting and manifest documents at every
nesting depth. Preparation and read-only verification fail on the duplicate key
before accepting later digest or identity evidence. Valid schema-4 documents
and their serialization do not change, so a schema bump would add migration
cost without strengthening the invariant.

This removes parser-dependent interpretation from the paid-distribution
approval boundary. It does not export source, save or deploy a Sites version,
approve either controlled action, or create a visit, pilot request, payment, or
revenue event.

## 2026-07-25: Bind The Sites Source Ref To The Actual Checkout

Every candidate manifest recorded `source_ref` as `refs/heads/main`, while the
source preflight proved only that a clean checkout's commit SHA matched
`origin/main`. A detached HEAD or another local branch pointing at that commit
could therefore pass and produce approval evidence claiming a branch that was
not actually checked out.

The shared synchronized-source proof now reads the active branch before either
commit SHA. Preparation repeats that exact `refs/heads/main` requirement after
the test phase and after packaging; read-only verification repeats it after
validating the receipt and archive. Detached and alternate-branch checkouts fail
before a receipt or approval-ready result, including when their commit bytes
are otherwise identical to `origin/main`.

The schema remains at version 4 because valid receipts already record the
required source ref; this change enforces that existing claim. It does not
export source, save or deploy a Sites version, approve either controlled action,
or create a visit, pilot request, payment, or revenue event.

## 2026-07-25: Bracket Sites Archive Identity Through Acceptance

Candidate preparation structurally validated the packaged archive and then
hashed it for the receipt. Read-only verification hashed the receipt-bound
archive before structural validation. In both paths, later synchronized-source
checks created a window where the archive path could change after the trusted
digest or structure was observed but before a receipt or verification success
was emitted.

Preparation now hashes the regular archive before structural validation, then
requires the same regular path and digest after the final branch and source
checkpoint. Read-only verification retains its initial receipt comparison and
performs the same final archive check after validating structure and source.
A persistent byte change or replacement with a symlink or non-file fails before
acceptance.

Archive bytes and schema-4 receipts remain unchanged, so no schema migration is
needed. This strengthens the source-export and version-save evidence boundary;
it does not export source, save or deploy a Sites version, approve either
controlled action, or create a visit, pilot request, payment, or revenue event.

## 2026-07-25: Preserve Pre-Existing Sites Candidate Evidence

Candidate preparation passed the requested archive path to the external
packaging helper and atomically replaced the requested receipt. Repeating an
otherwise valid command with the same paths could therefore replace an
artifact pair already referenced in an approval review, even though the
receipt and archive were internally bound.

Preparation now rejects any pre-existing archive or receipt path during local
output-policy validation, before Git, Node, npm, site-test, or packaging
commands run. Regression coverage preserves sentinel bytes for either existing
artifact and proves the command runner is never called. Operators must choose a
fresh outside-repository output pair for a new preparation run; read-only
verification continues to consume the original pair.

This protects normal reruns rather than claiming a cross-process reservation
after preflight. Valid schema-4 evidence is unchanged, so no migration is
needed. The guard does not export source, save or deploy a Sites version,
approve either controlled action, or create a visit, pilot request, payment, or
revenue event.

## 2026-07-25: Publish Sites Candidate Evidence Without Clobbering

Fail-fast output checks protected evidence that existed when preparation
started, but an output path could still appear during the long build and
validation window. The packaging helper wrote directly to the requested
archive, and receipt publication used replacement semantics, so either late
claim could be overwritten or become the content preparation validated.

The packaging helper now writes to a private temporary directory under the
archive destination's parent. Preparation hashes, structurally validates, and
rechecks synchronized source against that staged regular file before using a
same-filesystem hard link to claim the requested archive path atomically. The
receipt is serialized to a flushed and synced same-directory staging file and
published with the same create-only link. If either destination exists at
publication, the other file's bytes are preserved and preparation fails
without reporting approval-ready success. Staging paths are removed.

Archive publication necessarily precedes receipt publication. If another
process claims the receipt path in that interval, the validated archive remains
as an unpaired output while the competing receipt remains untouched; neither
is accepted as a candidate pair. The operator must inspect or remove the
unpaired archive and retry with fresh paths. Valid schema-4 bytes are unchanged,
so no migration is needed. This boundary exports no source, saves or deploys no
Sites version, grants no controlled approval, and creates no visit, pilot
request, payment, or revenue event.

## 2026-07-25: Bracket Sites Receipt Identity Through Verification

Read-only candidate verification parsed the requested receipt before archive
and synchronized-source validation, but did not recheck the receipt path before
reporting success. A concurrent process could therefore change the receipt
bytes or replace the path after its trusted fields were read, leaving an
approval-ready result whose visible receipt no longer matched the evidence
that was validated.

Verification now reads and parses one exact receipt byte buffer, retains its
SHA-256 digest, and requires the requested path to remain a regular file with
the same digest after archive and source validation. Persistent byte changes,
symlink replacement, and non-file replacement fail before success. Regression
tests force both a post-parse edit and post-parse link replacement through the
acceptance window.

Schema-4 receipt bytes remain unchanged, so no migration is needed. This
strengthens the source-export and version-save evidence boundary; it does not
export source, save or deploy a Sites version, approve either controlled
action, or create a visit, pilot request, payment, or revenue event.

## 2026-07-25: Pin The Exact Sites Receipt Across Approval

Candidate preparation last checked synchronized source and archive identity
before publishing the receipt, so persistent drift during receipt publication
could still receive a success result. Read-only verification retained the
receipt digest only within one invocation. Reformatting a semantically
equivalent receipt between source-export approval and the later pre-save check
therefore passed both checks even though the owner had reviewed different
bytes.

Receipt publication now returns the SHA-256 of its flushed staging file.
Preparation publishes the receipt, then repeats the synchronized-source,
archive, and receipt checks before reporting success. Preparation and
verification results and CLI output expose `receipt_sha256`. A later
`--verify-only` invocation can require the owner-approved digest with
`--expected-receipt-sha256`, rejecting malformed digests, changed bytes, and
semantically equivalent reserialization.

Schema-4 receipt contents remain unchanged, so no migration is needed. The
digest is approval evidence rather than approval itself. This change exports no
source, saves or deploys no Sites version, grants no controlled approval, and
creates no visit, pilot request, payment, or revenue event.

## 2026-07-25: Bind Pre-Save Verification To Exported Sites Source

The pre-save command required the receipt digest recorded in owner approval,
but still verified only the local checkout, archive, and receipt. If the wrong
commit reached the separate Sites source repository, that local evidence could
pass even though saving the candidate would join an approved archive to
different exported source.

Pre-save verification now requires the credential-free Git repository identity
used for the approved export. It resolves that repository's
`refs/heads/main` with read-only `git ls-remote`, requires the exported commit
to equal the receipt commit, and repeats the resolution before reporting
success so persistent movement fails closed. The exported-source option itself
requires `--expected-receipt-sha256`; ordinary pre-approval verification stays
offline.

The repository identity must not embed an access token; authentication remains
in the same per-command Git credential context used for the approved push. The
check follows the project's CI/CD integrity guidance while performing no source
export, version save, deployment, approval, customer contact, or revenue event.

## 2026-07-25: Pin The Sites Repository In Export Approval

The exported-ref verifier accepted any caller-selected repository containing
the receipt commit. Because Repo Scout already requires local
`HEAD == origin/main`, passing `origin`, the local checkout, or an unrelated
fork with the same commit could report pre-save success without proving that
the approved source reached the existing Sites project. Repeating that lookup
proved stability only for the wrong repository.

Source-export approval now records the credential-free canonical Sites
repository identity alongside the receipt digest, source ref, and commit. The
pre-save command takes that approved identity separately from its operational
URL or configured remote alias. It resolves and canonicalizes the operational
argument, requires a genuinely remote repository matching approval, rejects
the local checkout and anything equivalent to `origin`, and repeats identity
resolution before its final exported-ref check. An unrelated fork or repointed
alias therefore fails even when `refs/heads/main` contains the expected commit.

Authentication remains outside both identity arguments, and malformed remote
URLs fail with a controlled error. The change follows the project's CI/CD
integrity guidance while performing no source export, version save, deployment,
approval, customer contact, or revenue event.

## 2026-07-25: Retain Non-Default Sites Repository Ports

Canonical repository identity validated URL ports but omitted them from the
identity string. An approved `https://host/repository` and an operational
`https://host:8443/repository` therefore compared equal even though the
non-default port can serve an unrelated Git repository. Matching the receipt
commit on that endpoint could satisfy the repository and ref checks without
using the authority recorded in approval.

Canonicalization now removes only each protocol's standard port: Git `9418`,
HTTP `80`, HTTPS `443`, and SSH `22`. Every non-default port remains in the
canonical authority. This preserves legitimate default-port and cross-protocol
aliases while making an unapproved port mismatch fail before exported-ref
verification. Regression coverage proves both boundaries.

The change follows the project's CI/CD integrity guidance while performing no
source export, version save, deployment, approval, customer contact, or revenue
event.

## 2026-07-25: Keep The Sites Pre-Save Approval Tuple Atomic

`--expected-receipt-sha256` remained usable without either exported-source
repository argument. That legacy digest-only mode checked the reviewed receipt
bytes but returned the same generic verification success while skipping every
network, canonical repository identity, and exported-commit check. The current
operator contract defines no digest-only post-approval stage, so omitting both
repository lines from the pre-save command could silently weaken the gate.

An approved receipt digest now requires the operational exported repository,
which already requires the approved canonical repository identity. The same
all-or-none rule applies to direct Python callers and the CLI before any
candidate evidence is read. Plain `--verify-only` remains the offline
pre-approval operation and continues to print the receipt digest for review.

This removes an ambiguous weaker success mode while following the project's
CI/CD integrity guidance. It performs no source export, version save,
deployment, approval, customer contact, or revenue event.

## 2026-07-25: Preserve Sites Evidence Leaves During Normalization

Candidate preparation and verification called `Path.resolve()` on requested
archive and receipt paths before applying their no-clobber and regular-file
checks. That dereferenced an initial symlink and replaced the operator-supplied
leaf with its target. Verification therefore accepted symlinked evidence, and
preparation could follow a dangling output symlink to a different location
without recognizing that the requested path already existed.

Candidate evidence normalization now makes the path absolute, resolves its
parent directory, and appends the unresolved leaf name. Initial and dangling
leaf symlinks remain visible to `lexists` and regular-file checks, while
resolving the parent retains the prior defense against an existing symlinked
directory that points an apparently external output back inside the repository.
Regression coverage rejects archive and receipt verification links, preserves a
dangling output link and its absent target, and keeps parent-alias rejection.

This change closes stable initial-leaf redirection. It does not claim to pin a
parent directory against concurrent replacement or make every type-check and
file-open pair atomic; those stronger filesystem-identity guarantees remain a
separate approval-boundary task.

This protects the exact evidence leaf reviewed for paid distribution while
following the project's CI/CD integrity guidance. It performs no source export,
version save, deployment, approval, customer contact, or revenue event.

## 2026-07-25: Compare Sites Output Ancestry By Filesystem Identity

Resolving each requested evidence parent removed symlink aliases before the
outside-repository check, but containment still compared path text. On a
case-insensitive or Unicode-normalizing filesystem, an alternate spelling can
identify the checkout while remaining lexically unrelated. A stable
whole-repository alias can have the same effect, and an ignored in-repository
output would not necessarily make the final source check dirty.

Candidate preparation now walks each requested archive and receipt parent's
ancestors and compares their filesystem identity with the checkout root after
the existing lexical check. Missing intermediate directories do not stop the
walk, while permission and other ambiguous identity failures stop preparation
before any source, build, test, or packaging command. Regression coverage
proves both evidence labels, a missing intermediate directory, and fail-closed
lookup errors.

This closes stable alternate-spelling and whole-repository aliases only. A
mount exposing one checkout subdirectory may report a different root identity,
and a checked parent can still be replaced before a later path-based operation.
Descriptor-bound evidence reads and publication therefore remain required
before a replacement candidate is approval-ready. The change performs no
source export, version save, deployment, approval, customer contact, or revenue
event.

## 2026-07-25: Compare Sites Outputs With Every Checkout Directory

Comparing output ancestors only with the checkout root closed stable
alternate-spelling and whole-repository aliases, but a bind or equivalent
alias can expose one checkout subdirectory with that subdirectory's identity.
An ignored evidence directory could therefore remain lexically external and
avoid the root-only comparison while still writing into the protected source
tree.

Candidate preparation now inventories every repository directory with
`follow_symlinks=False`, records each unique device and inode pair, and skips a
repeated identity rather than traversing a mount cycle. Every existing archive
and receipt parent ancestor is compared with that inventory. Stable aliases to
the root or any subdirectory fail before source, build, test, or packaging
commands, while reported traversal or ambiguous stat failures stop preparation.
Regression coverage proves root and subdirectory aliases for both evidence
labels, missing intermediate output directories, symlink exclusion, duplicate-
identity cycle suppression, and traversal failure.

This closes stable subdirectory aliases only when the filesystem preserves
directory identity. It does not anchor later staging, reads, publication, or
cleanup against concurrent parent or leaf replacement, and an identity-
remapping filesystem remains outside the guarantee. Descriptor-bound evidence
operations therefore remain required before a replacement candidate is
approval-ready. The change performs no source export, version save, deployment,
approval, customer contact, or revenue event.

## 2026-07-25: Anchor Sites Publication To The Validated Parent

Candidate preparation recorded output containment before long-running build
and validation commands, but final archive and receipt hard links still
resolved the destination parent from its path. Replacing that directory after
preflight could therefore move a create-only publication into a different
location without overwriting an existing leaf.

Preparation now requires both direct output parents to exist and the host to
support POSIX descriptor-relative hard links before any Git, Node, npm, test,
or packaging command runs. It records each parent's filesystem identity,
opens the parent without following a symlink at publication, verifies the open
descriptor still has that identity, and creates the output leaf relative to
the descriptor. Replacement before the open fails, while a rename after the
identity check cannot redirect the link into a newly created directory at the
requested parent path. Existing late-leaf claims retain their bytes and the
same controlled no-clobber failure.

This decision anchors only the final destination operation. The parent
descriptor is reopened rather than held from preflight, and staging,
staged-file reads, post-publication reads, and cleanup remain path-based.
Identity-remapping filesystems and inode reuse across the reopen interval also
remain outside this guarantee. Those operations must become descriptor-bound
before a replacement candidate is approval-ready. The change performs no
source export, version save, deployment, approval, customer contact, or
revenue event.

## 2026-07-25: Hold Sites Publication Parents From Preflight

Opening an output parent only at final publication and comparing its device and
inode with a preflight stat closed ordinary replacement, but it retained a
reopen interval. Inode reuse during the long build and validation phase could
make a different directory satisfy that comparison, and opening archive and
receipt parents independently could bind two outputs to different directory
instances when both requested paths shared one parent.

Candidate preparation now opens every unique direct output parent before the
first Git or Node command with directory-only, no-follow, close-on-exec
semantics. It verifies repository containment and each requested leaf relative
to the opened descriptor, reuses one descriptor when archive and receipt share
a parent, and keeps those descriptors live and non-inheritable through all
validation and final no-clobber links. Context-managed ownership closes every
descriptor after success, runner failure, or partial acquisition when a later
parent cannot be opened. A parent path replaced after preflight cannot change
the directory that receives publication.

Staging directories and files, staged-file hashing and validation,
post-publication evidence reads, and staging cleanup still resolve paths.
Replacing a parent can therefore leave correctly anchored evidence in the
displaced original directory while a later path-based check rejects the
candidate. Those operations remain required before replacement evidence is
approval-ready. This change performs no source export, version save,
deployment, approval, customer contact, or revenue event.

## 2026-07-25: Hold Published Sites Evidence Through Final Checks

Holding each validated output parent through final no-clobber publication
prevented destination redirection, but preparation still reopened the archive
and receipt by path for its post-publication digest checks. The interval between
the hard link and that reopen could bind validation to a replacement leaf, and
a byte-identical replacement could satisfy a digest while changing the file
identity. Checking only a leaf relative to the original parent would also miss
a requested parent replaced with another directory that re-linked the same
published inode.

Publication now opens the staged source without following links or blocking on
a special file, links it relative to the held destination parent, opens the new
leaf relative to that parent, and requires both descriptors to identify the
same regular file. Preparation registers the returned archive and receipt
descriptors with context-managed ownership immediately, keeps them
non-inheritable and live through the final synchronized-source and digest
checks, and hashes those borrowed descriptors directly. Before success it
reopens each requested parent without following a symlink, compares that
directory with the held parent, and compares the leaf relative to it with the
published file descriptor. Every descriptor closes after success, partial
publication, or later validation failure.

Staging-directory creation, staged archive validation, and staging cleanup
still resolve paths and remain required before replacement evidence is
approval-ready. This change performs no source export, version save,
deployment, approval, customer contact, or revenue event.

## 2026-07-28: Anchor Sites Archive Staging To Held Descriptors

The archive destination parent was held from preflight and each published
evidence file was retained through final checks, but the private staging
directory, staged archive read, tar validation, and cleanup still reopened
visible paths. Replacing the archive parent could make the external helper
write a valid package under a different directory from the one held for final
publication. A staged-leaf replacement could also move validation and
publication onto different inodes, while path cleanup could delete an object
the candidate process did not create.

Preparation now creates a high-entropy `0700` staging directory relative to
the archive-parent descriptor held from preflight, opens it without following
links, and verifies its identity, mode, and owner. The external packaging
helper still receives the visible path it requires, but acceptance opens only
the regular archive leaf relative to the held staging directory with
no-follow, nonblocking, close-on-exec semantics. Hashing, tar validation,
post-packaging source validation, digest recheck, and publication all borrow
that exact archive descriptor. The hard-link source remains a name resolved
relative to the held staging directory because Python cannot link directly
from a file descriptor; the new destination is therefore opened and required
to share the held archive's filesystem identity before it can advance. The
source leaf is also checked against the held archive immediately before that
name-based link, narrowing the unavoidable interval to the link syscall while
the destination check catches a substitution within it.

Cleanup records both staging-directory and accepted archive identities. It
unlinks only a matching archive leaf and removes only the matching staging
directory. Missing objects are tolerated where ownership is unambiguous, while
a replacement, unverified helper artifact, unknown extra entry, or failed
identity lookup is preserved and reported. The final check-to-remove interval
cannot be made perfectly atomic with portable POSIX directory APIs, so the
operator contract intentionally prefers a failed candidate and retained
artifact over deleting an uncertain object. If the visible parent path was
replaced, helper output written there is neither chased nor removed and cannot
satisfy acceptance.

This decision completes descriptor binding for archive staging, reads,
validation, and cleanup only. Receipt staging, staged receipt hashing, and
receipt cleanup still use visible paths and remain required before replacement
evidence is approval-ready. The change performs no source export, version
save, deployment, approval, customer contact, or revenue event.

## 2026-07-28: Anchor Sites Receipt Staging To Held Descriptors

Archive staging and final publication were bound to descriptors held from
preflight, but receipt staging still used `NamedTemporaryFile` under the
visible parent, closed that file, and reopened its path independently for
hashing and publication. Replacing the parent could split staging from its
held publication destination. Replacing the staged leaf could also make
different bytes become the trusted receipt and digest, while path-only cleanup
could delete the replacement and leak the file the process actually created.

Preparation now creates a high-entropy `0600` receipt staging leaf relative to
the held receipt-parent descriptor with create-only, no-follow, close-on-exec
semantics. It retains one read/write regular-file descriptor while writing and
syncing the deterministic JSON, hashes that exact descriptor, requires the
digest to equal the intended serialized bytes, and hashes it again immediately
before publication. The hard-link source remains a name because Python cannot
link directly from a file descriptor, so publication resolves that name
relative to the same held parent and requires it to match the staged file
immediately before linking. The published leaf must then share that identity.

Cleanup compares the current temporary leaf with the identity recorded from
the held staged descriptor. It unlinks only a matching regular file, preserves
and reports a replacement or uncertain object, and closes the staged
descriptor in every outcome. If cleanup fails after publication, the published
descriptor is closed rather than transferred to the remaining candidate
checks. As with archive staging, the portable POSIX name-to-link and
name-to-unlink intervals cannot be made perfectly atomic, so the contract
prefers a failed candidate and retained evidence over deleting an object it
cannot prove it owns.

This decision completes descriptor binding for both archive and receipt
staging, reads, publication, and cleanup. It performs no source export, version
save, deployment, approval, customer contact, or revenue event.

## 2026-07-28: Bind Sites Approval To The Public Release Version

Schema-4 candidate evidence bound the exact source commit, branch, Node
runtime, lockfile, Sites project, complete deployable tree, archive, and receipt
bytes. It did not state the public Repo Scout release that the owner was being
asked to approve. That omission mattered while production still advertised
`v0.3.50` and the replacement source advertised `v0.3.51`: a receipt digest
could identify exact bytes without giving the approval record a direct,
human-readable release identity.

Sites evidence now uses schema 5. Before any Git, Node, npm, test, or packaging
command runs, preparation strictly parses `project.version` from
`pyproject.toml`, requires a semantic `MAJOR.MINOR.PATCH` value, finds exactly
one semantic `RELEASE_VERSION` declaration in `app/site-config.ts`, and requires
the two values to match. The reconciled version is embedded in the candidate
manifest and therefore in both the archive and receipt. Independent
verification recomputes it from the checkout and rejects missing, malformed,
mismatched, removed, or changed release identity. Prior schema-4 receipts fail
closed instead of acquiring the new meaning implicitly.

Preparation and verification print `release_version` beside the source commit,
archive digest, and receipt digest. Source-export approval must record that
version with the exact receipt SHA-256, canonical Sites repository identity,
`refs/heads/main`, and receipt commit. This makes the intended production
upgrade legible without weakening the digest-bound source and artifact proof.
The read-only site dependency contract watches both `pyproject.toml` and
`app/site-config.ts`, so either identity source receives the complete hosted
contract instead of waiting for an unrelated dependency or script change.

The change performs no candidate export, source push, version save, deployment,
approval, customer contact, or revenue event.

## 2026-07-28: Name The Existing Sites Project In Export Approval

Schema-5 receipts already bound the existing Sites `project_id`, but candidate
results and owner-facing success output omitted it. The source-export approval
instructions therefore required the release version, receipt digest, canonical
source repository, source ref, and commit while leaving the target Sites
project to be inferred from the receipt or a later reuse instruction.

Preparation and independent verification now carry the already validated
`project_id` through `SiteCandidateResult` and print it beside the other
approval evidence. The source-export handoff requires that value in the explicit
owner approval, so the controlled source push remains tied to the existing
project before any version-save step.

The receipt schema and artifact bytes do not change. Printed identity is
evidence rather than approval, and this change performs no source export,
version save, deployment, customer contact, or revenue event.

## 2026-07-28: Emit A Pending Sites Source-Export Request

Independent verification produced every candidate-derived approval value, but
the operator still had to resolve the existing Sites source repository and
manually assemble it with the release version, project ID, receipt digest,
source ref, and commit. That reconstruction left a completed integrity contract
one manual transcription away from owner review.

Plain `--verify-only` now accepts `--approval-source-repository` for this
pre-approval purpose. After the archive and receipt pass independent
verification, the command resolves the supplied credential-free URL or alias
locally, canonicalizes protocol-equivalent identities, and rejects a repository
matching `origin`. It then prints one copy-ready request containing the complete
tuple and `deployment_approved=false`. The normal archive digest label is now
`archive_sha256`, keeping it distinct from `receipt_sha256`.

The request option cannot be combined with approved-receipt or exported-source
arguments, performs no remote-ref lookup, and remains a pending request rather
than consent. The existing post-export pre-save mode remains the authoritative
network and commit check. This change performs no source export, version save,
deployment, customer contact, or revenue event.

## 2026-07-28: Separate Outreach Review Content From Decision Time

The first owner-only review bundle was prepared on July 21, but its generated
approval command reused July 21 as both the ledger-audit date and the human
approval date. The same date was included in the schema-4 content digest.
Consequently, changing the command to the truthful later decision date made the
receipt fail, while running it unchanged would backdate approval evidence. A
bundle intended for asynchronous human review therefore became unusable after
UTC midnight without clearly saying so.

Schema-5 review receipts bind the normalized selected ledger row, selected
private draft, and five displayed checks, but not the bundle's audit date. The
generated approval and decline commands now use `YYYY-MM-DD` for the decision
audit, and approval uses the same placeholder for `approved_on`. The operator
must replace those values with the actual UTC decision date. Approval and
decline still reload the current private files and recompute the digest, so any
source, channel, draft, status, or checklist change forces a fresh review even
when the calendar date changes.

Existing schema-4 bundles do not acquire schema-5 meaning and must not be used
for a later decision. This change records no review judgment, approval,
contact, pilot request, payment, or revenue event.

## 2026-07-28: Keep Decline Continuations Out Of Terminal Capture

A content-bound no-send decision preserved the next review's private evidence
and draft flags, but its generated continuation omitted `--write-review`.
Following that command therefore printed the next prospect alias, qualification
sources, and personalized message to the terminal even though the previous
complete review had used an owner-only file. The queue retained content
integrity while silently regressing its disclosure boundary.

Nonterminal content-bound decline receipts now carry
`--write-review PRIVATE-REVIEW-PATH` into the next review command. The operator
must replace that literal with a new destination in the ignored owner-only
workspace. An unchanged placeholder fails before Repo Scout reads the private
ledger or draft notes. A valid replacement uses the existing no-clobber,
owner-only writer, prints only its alias-free confirmation, and keeps the next
alias, sources, message, checklist, and digest in the `600` review file.
Alias-only continuations retain their existing terminal checklist, and terminal
declines still emit no next command.

The decline decision and the later review-file creation remain separate
operations. This change does not approve or send outreach, create demand,
collect payment, or record revenue.

## 2026-07-28: Encode Sites Approval Evidence As Single-Line JSON

The offline Sites source-export request used a flat, space-delimited list of
`key=value` fields. Candidate status used the same representation. Repository
identities with raw spaces made the approval tuple ambiguous, while an opaque
project ID or output filename containing a newline could create a misleading
sibling field or extra terminal line. The receipt still bound the real value,
but the copy-ready owner evidence could present another interpretation.

Candidate status and the pending source-export request now keep their stable
human-readable prefixes and place every field in a compact, deterministic JSON
object. Opaque values remain exact JSON strings, and
`deployment_approved=false` is a boolean that embedded text cannot replace or
duplicate as a sibling field. Configured and resolved source repository
identities reject raw whitespace; legitimate URL path spaces must be
percent-encoded and remain unchanged through canonicalization.

This hardens the existing approval handoff only. It does not run Node or npm,
query a remote ref, export source, save or deploy a Sites version, approve
publication, contact a customer, or create revenue evidence.

## 2026-07-28: Keep Private Review Path Replacement Shell-Safe

The content-bound decline continuation included a literal
`PRIVATE-REVIEW-PATH` marker, but the command formatter treated it as an
ordinary shell-safe token. Operator guidance said to replace that literal.
Replacing it with an owner-only destination containing spaces therefore split
the intended path into multiple arguments and made the copy-ready continuation
fail.

Generated outreach commands now force that marker into single quotes while
retaining normal shell quoting for every other argument. Literal replacement
inside the existing quotes keeps an ordinary spaced path intact. The source
test exercises the emitted command as shell text, and the installed-wheel
lifecycle smoke test proves the same behavior through the packaged command.

This change preserves the private review handoff after a human no-send
decision. It does not make that decision, approve or send outreach, save or
deploy a Sites version, validate willingness to pay, or record revenue.

## 2026-07-28: Reject Ambiguous Pilot JSON Before Revenue Accounting

The pilot reporter decoded issue exports with normal JSON last-key-wins
semantics. An otherwise valid issue object could therefore contain two
`labels` keys, with one omitting `pilot-paid` and the other including it. The
decoder silently selected the latter value before the funnel applied its
otherwise strict payment rules, allowing ambiguous input to change booked
pilot and revenue totals.

Pilot issue ingestion now rejects duplicate JSON keys at every object depth
before issue parsing. The controlled error names only the repeated field and
emits no report. A source regression proves the fail-closed CLI boundary, and
the installed commercial smoke test proves the packaged command rejects
conflicting payment-label evidence without echoing either label value.

This hardens the accounting input contract only. It does not create a pilot
request, apply a payment label, contact a buyer, collect payment, or record
revenue.

## 2026-07-28: Bind Bootstrap Receipts To Direct Policy Outputs

Bootstrap built its JSON receipt before writing the selected policy and
resolved the receipt's output through any existing symlink leaf. Force mode
then atomically replaced the symlink itself. The command could therefore
succeed with a direct policy at the requested path while its receipt named the
link's unchanged former target. A repository-relative custom output was worse:
path preparation resolved through the leaf before the writer saw it, so force
mode replaced the target instead.

Relative bootstrap normalization now resolves only the output parent and
preserves the requested leaf. The shared policy writer rejects initial and
dangling symlink leaves before force or no-force writes. Bootstrap emits no
receipt, and both link and target remain unchanged. Source regressions cover
the default and custom relative paths; the installed activation smoke test
proves the custom path through the packaged command.

This protects free-to-paid policy activation and first-repository handoff
evidence. It does not establish customer use, pilot demand, payment, or
revenue.

## 2026-07-28: Keep Receipt Verification On Direct Policy Leaves

Bootstrap required a direct output leaf, but later receipt verification
resolved the receipt-recorded path or `--policy` override through any symlink
before loading the policy. Replacing a valid bootstrap output with a link to an
identical policy therefore returned `pass` and changed the report's policy path
to the referent. The archived receipt could appear to validate its named
first-repository output while the verifier had inspected another leaf.

Verification now resolves only the selected policy's parent and preserves its
requested leaf. It inspects that leaf without following it and returns the
existing exit-6 mismatch contract for an initial or dangling symlink. The report
retains the requested policy path and expected version and fingerprint, marks
actual identity unavailable, and neither names nor modifies the referent.
Source regressions cover both the receipt-recorded path and an explicit
override; the installed activation journey covers the packaged default path.

Because every successful bootstrap emits an absolute, parent-resolved output
with a file leaf, receipt parsing now enforces that contract before honoring a
policy override. Relative outputs and embedded NUL characters fail as malformed
receipt evidence with exit 2 and no report. A crafted receipt can no longer
select a matching file relative to the verifier's working directory, hide a
malformed recorded path behind `--policy`, or raise an uncaught path error. The
installed activation journey also proves the relative-output rejection through
the packaged command.

This keeps free-to-paid policy activation evidence tied to the policy location
under review. It does not establish customer use, pilot demand, payment, or
revenue.

## 2026-07-28: Reject Non-Regular Policy Leaves Before Receipt Reads

Receipt verification rejected symlink policy leaves but passed every other
direct filesystem type to the TOML loader. A directory returned an ordinary
read error, while a FIFO caused the command to block waiting for a writer.
Sockets, devices, and similar special files also had no explicit boundary even
though successful bootstrap and initialization create regular policy files.

Verification now inspects the selected leaf type before loading it. Any present
leaf that is neither a symlink nor a regular file returns the existing exit-6
mismatch report with expected identity retained, actual identity unavailable,
and a controlled regular-file reason. The leaf remains unchanged and the policy
loader is never called. Source regressions prove both directory and FIFO cases;
the installed activation journey proves the packaged command rejects a direct
non-regular leaf with the same evidence.

This prevents a crafted policy path from stalling first-repository or paid-CI
activation while retaining the free verifier's useful failure report. It does
not establish customer use, pilot demand, payment, or revenue.

## 2026-07-28: Bind Receipt Verification To One Policy Descriptor

Receipt verification inspected the selected policy leaf with `lstat()` but
then reopened it through the path-based policy loader. The leaf could be
replaced between those operations. A symlink to the original matching file or
a different regular file containing identical bytes could therefore produce a
false `pass` even though the requested first-repository policy leaf had changed.

Verification now opens the inspected leaf with read-only, close-on-exec,
no-follow, and nonblocking flags where the platform provides them. The opened
descriptor must be a regular file with the same filesystem identity as the
initial inspection. Policy bytes, normalization, and fingerprinting all use
that descriptor, and the requested leaf must still name the same regular file
after fingerprinting. Any transition returns the existing exit-6 report with
expected identity retained and actual identity unavailable.

Deterministic source regressions replace the leaf after initial inspection with
both a symlink and an identical-byte regular file, then replace it again during
fingerprinting. All three paths fail closed without disclosing a referent.

This keeps free first-repository and paid-CI activation evidence tied to the
policy leaf under review. It does not deploy the site, approve outreach,
establish customer use, validate demand, collect payment, or record revenue.

## 2026-07-28: Bind Bootstrap Receipt Inputs To Stable Evidence

`verify-receipt` resolved the receipt argument through its leaf and then used a
path-based text read. A symlink could silently select another receipt, a FIFO
could block the command before policy verification, and a different file could
replace the receipt between reading and acceptance. The archived evidence had
strict JSON semantics but no matching filesystem boundary.

Receipt normalization now resolves only the parent and preserves the requested
leaf. The leaf must be a direct regular file before opening. JSON bytes are read
and validated through one non-inheritable descriptor opened with no-follow and
nonblocking flags where available. Before validated evidence is returned, the
descriptor bytes are reread exactly and the requested leaf must still identify
the originally inspected file. Symlinks, special files, different-inode
replacement, and same-inode mutation all fail with exit 2 and no verification
report.

The shared descriptor helper now gives policy fingerprinting the same
exact-byte acceptance check in addition to its existing leaf-identity check.
Source regressions cover symlink, directory, FIFO, pre-read replacement,
post-validation replacement, and in-place mutation. The installed activation
journey proves the packaged command rejects symlink and non-regular receipt
inputs without changing or disclosing their evidence.

This prevents untrusted receipt input from redirecting or stalling free
first-repository and paid-CI activation. It does not approve outreach, export
or deploy the site, establish customer use, validate demand, collect payment,
or record revenue.

## 2026-07-28: Bind Primary Policy Loading To Stable Evidence

The bootstrap-receipt verifier had a direct-leaf, descriptor-bound policy read,
but the primary `repo-scout --policy` command still resolved through its input
leaf and reopened the result by path. A symlink therefore selected and reported
its referent as the policy source. A FIFO or other special file could also block
the copy-ready customer gate, and path replacement or same-inode mutation had
no acceptance check around parsing and validation.

Primary policy loading now resolves only the parent and preserves the requested
leaf. It rejects symlinks and non-regular files before opening, then uses the
shared read-only, non-inheritable descriptor helper already proven by receipt
verification, including no-follow and nonblocking flags where the platform
provides them. The descriptor must match the initially inspected regular file.
One exact UTF-8 byte buffer is parsed and validated, then the bytes are reread
and the requested leaf must still identify that file at the acceptance
checkpoint. Symlink or distinct regular-file replacement and in-place mutation
detected there return exit 2 without a scan report.

Source regressions cover static symlink, directory, and FIFO leaves, replacement
between inspection and open, replacement after validation, and same-inode byte
mutation. The installed activation journey proves the packaged primary command
rejects symlink and directory inputs without naming or changing the referent.

This closes the remaining input-integrity gap in the command used by the
copy-ready paid-CI workflow. It does not approve outreach, establish an install
or customer use, validate demand, collect payment, deploy the site, or record
revenue.

## 2026-07-28: Bound Activation Evidence Before Parsing

Descriptor binding prevented policy and bootstrap-receipt redirection and
mutation, but the shared reader still accumulated regular-file bytes until EOF
and repeated that unbounded allocation at the acceptance checkpoint. A sparse
or growing policy or receipt could therefore consume excessive memory or CI
runtime before TOML or JSON validation returned a controlled result.

Primary policies, bootstrap receipts, and policies selected by receipt
verification now share a 128 KiB ceiling. The opened descriptor's regular-file
size is checked before content is read, rejecting oversized sparse files before
allocation or parsing. Each descriptor read requests at most the remaining
ceiling plus one byte. Crossing the limit during the initial read raises a
dedicated internal size error. Crossing it during the post-validation reread is
reported as changed content because the initially accepted bytes grew while
they were under review. In either case, same-inode growth cannot force an
unbounded allocation.

An oversized primary policy returns exit 2 before scanning or emitting a
report. An oversized receipt also returns exit 2 without verification evidence.
An oversized receipt-selected policy keeps the archived expected identity,
marks actual identity unavailable, and returns the existing exit-6 mismatch
report. Source regressions prove pre-parse rejection, receipt-policy evidence,
and growth during validation. The installed activation journey covers sparse
primary-policy and receipt inputs without changing their bytes.

This is a corrective availability boundary for free first-repository and paid
CI activation. It does not add a policy feature, approve or send outreach,
establish customer use, validate demand, deploy the site, collect payment, or
record revenue.

## 2026-07-28: Bind Rollout Aggregation Inputs To Stable Evidence

`repo-scout-rollout` aggregated the paid delivery bundle for each repository,
but opened each Markdown argument with a path-based, unbounded text read. A
symlink could redirect one repository's evidence, a FIFO could stall the
operator command, and replacement or same-inode mutation could race metadata
validation. An oversized regular or sparse file could also consume
uncontrolled memory before the command returned a parsing error.

Each rollout argument must now be a direct regular-file leaf no larger than
1 MiB. The 1,048,576-byte ceiling is roughly 380 times the current
repository's generated 2.7 KiB bundle while bounding customer-controlled input.
The initially inspected leaf and opened descriptor must identify the same
regular file. One exact UTF-8 buffer is parsed and validated, then the
descriptor bytes and requested leaf are rechecked before the metadata can enter
a cross-repository summary.

Symlinks and special files fail before opening. Oversized sparse files fail
before reading or parsing. Different-inode replacement, same-inode mutation,
or growth detected at acceptance also fails with exit 2 and no summary.
Source regressions cover directory, symlink, FIFO, sparse oversize, the exact
size boundary, and mutation during parsing. The installed rollout smoke proves
the packaged command rejects symlink and oversized evidence without changing
the files.

This protects the counts-only acceptance record required by the $299 pilot.
It adds no policy capability or acquisition asset, does not approve outreach or
site deployment, and does not establish activation, demand, payment, or
revenue.

## 2026-07-28: Reject Unsafe Rollout Branch Text Before Output

Schema-1 and schema-2 rollout metadata previously accepted any string for
`git.branch`. Detailed text output interpolated that value directly, so a
crafted evidence bundle could add a fake metric line or terminal control
sequence to an otherwise valid operator summary. Even though rollout bundles
are not authenticated, parsed evidence must not be able to change the
structure or presentation of the command's own output.

`git.branch` must now be null or a non-empty printable string of at most 1,024
characters without surrounding whitespace. This permits normal Unicode branch
names while rejecting newlines, escape sequences, bidirectional controls,
Unicode line separators, blank values, and unbounded text. Rejection uses one
generic error that never includes the supplied branch value.

Validation happens before summary construction. Invalid evidence returns exit
2 with no partial text or JSON report and leaves the input unchanged. Source
tests cover each rejected class plus exact-limit and printable-Unicode
acceptance. The installed rollout smoke reproduces the former fake-metric and
terminal-control payload against the packaged command.

This protects the paid pilot's counts-only and detailed acceptance evidence.
It adds no acquisition asset or policy feature, does not approve outreach or
site deployment, and does not establish activation, demand, payment, or
revenue.

## 2026-07-28: Keep Public Pilot Text Out Of Commercial Report Structure

`repo-scout-pilot` printed each public issue title directly in its Deals,
Stale deals, and Sales queue sections. A request author could put a newline and
terminal control sequence in a title, causing the operator report to display a
fake sibling line such as booked revenue even though the underlying funnel
arithmetic was unchanged.
Edited dropdown answers created the same risk because unknown source, readiness,
and purchase-criterion values were interpolated into terminal-facing warning
messages.
Edited export URLs were also appended directly to three report sections, and
unknown `pilot-*` label names were interpolated into warnings.

The reporter now trims surrounding whitespace once, then requires the title to
be non-empty printable text of at most 1,024 characters. Internal newlines,
escape sequences, bidirectional controls, Unicode line separators, and
oversized titles fail with one generic error that does not include the supplied
value. Valid printable Unicode and the exact length boundary remain accepted.
Issue URLs must be empty or printable text of at most 2,048 characters without
surrounding whitespace. Unsafe URL errors likewise omit the supplied value.

Validation occurs while the issue export is parsed, before funnel totals or
text and JSON output are built. Invalid evidence returns exit 2 with no partial
report. Source tests cover each rejected class, normalized and exact-limit
acceptance, and no payload echo. The installed commercial smoke replays the
former forged-revenue and ANSI payload through the packaged command and proves
the export remains unchanged.

Unknown edited form answers remain available in the report's raw JSON deal
fields, and unknown labels remain in warning label arrays, where JSON escaping
preserves structure. Human-facing warning messages now name only the
unrecognized field, so public answer or label text cannot create sibling
terminal lines. Source and installed smoke tests prove the warnings remain
actionable without exposing injected values, and separately prove an unsafe URL
cannot reach output.

This protects the canonical $299/$897 revenue review from public-input display
spoofing. It does not qualify a lead, approve or send outreach, deploy the site,
prove willingness to pay, collect payment, or record revenue.

## 2026-07-28: Gate Ready-Buyer Actions On Copy-Ready CI

The paid delivery contract says GitHub Actions is the only copy-ready gate and
requires an explicit private integration decision for every other provider
before payment. The schema-7 pilot reporter already normalized CI provider
evidence, but its sales action used only purchase readiness and funnel stage. A
ready GitLab CI, CircleCI, Buildkite, `Other`, missing, or edited request could
therefore tell an operator to send pilot terms or confirm payment before the
required integration decision.

Ready-to-purchase requests now receive the normal stage-specific action only
when `qualification.ci_provider` is `github_actions`. Recognized non-GitHub
providers receive one action to record the private CI integration decision
before further terms or payment. Missing, no-response, edited, or ambiguous
provider evidence receives a separate action to confirm both the provider and
decision. Approval-dependent, exploratory, missing-readiness, and
unrecognized-readiness actions retain their existing purpose because none
directs the operator to terms or payment.

The action stays identical in the deal, stale-follow-up, and sorted sales-queue
views. Queue membership, readiness priority, stage and age ordering,
qualification status, target-profile counts, labels, schema version, and
revenue accounting do not change. Source regressions cover every recognized
provider, unresolved provider shapes, every readiness bucket, all three
pre-payment stages, and view consistency. The installed commercial smoke
proves the packaged command withholds payment guidance for a ready GitLab
request.

The private delivery record remains the source of truth for an accepted
non-GitHub integration. The public report cannot observe that decision and
therefore continues to present the advisory gate; it does not add a lifecycle
label or infer payment. Aggregate growth recommendations do not carry
provider-level actionability, so schema-7 offer, payment, and open pilot-target
bottlenecks with a sales action point back to the provider-aware queue instead
of issuing a conflicting instruction. The offer handoff retains the validated
pilot price. Growth does not infer that capability from the unchanged schema
number alone: it reconciles the queue length and validates each ready
non-GitHub or unresolved-provider action before deferring. Saved schema-7
evidence carrying the former provider-blind action fails closed, while older
pilot schemas keep their prior aggregate behavior. This does not approve
outreach, make an integration decision, collect payment, or record revenue.

## 2026-07-28: Gate Ready Buyer Actions On Pilot Scope

Schema-7 qualification classified team size, repository count, CI provider,
and the presence of a requested standard, but the sales action used only
readiness, stage, price, and CI provider. A ready GitHub Actions request marked
incomplete or outside the 5-to-50-developer and multi-repository target could
therefore receive an instruction to send terms or confirm payment. A target
request above the 10-repository offer could receive the same instruction before
its required first-10 scope was agreed.

Ready GitHub Actions requests now receive normal stage-specific terms or payment
guidance only when qualification is `target` and repository scope is
`within_offer`. Incomplete and outside-target evidence receives one
qualification-review action, while `subset_required` receives a
first-10-repository scope action. The existing non-GitHub integration decision
and unresolved-provider clarification retain precedence, so unsupported CI
cannot advance while the broader qualification evidence is reviewed. Actions
for approval-dependent, exploratory, missing, and unrecognized readiness remain
unchanged because they do not direct terms or payment.

Pilot reporting and growth ingestion now use one sales-action resolver. Growth
requires every schema-7 queue entry to carry a recognized open pre-payment
stage, readiness value, qualification status, repository scope, and provider,
then reproduces the exact action with the report's validated pilot price.
Provider-blind, scope-blind, stage-skipping, and price-divergent saved actions
fail closed before a growth bottleneck can defer to the queue. Schema-5 and
schema-6 aggregate recommendations remain unchanged.

Source coverage spans target, outside-target, incomplete, and first-10 scope
requests while preserving non-ready coaching and consistent deal, stale, and
queue views. The installed commercial smoke proves an out-of-profile request
cannot retain payment guidance. This corrects the $299 pilot operating contract;
it does not approve outreach, change qualification labels, make a private scope
or CI decision, collect payment, or record revenue.

## 2026-07-28: Fail Closed Before Running The Portable Quick Start

The public website, README, and release guide each presented a `curl` download
followed by an independent `python3` command. If the transfer failed, a pasted
block continued and could execute an older `/tmp/repo-scout.pyz` from a prior
evaluation. Because that Python process could succeed, the complete quick start
could also hide the transport failure behind exit 0.

Each published quick start is now one shell AND-list. The website and release
guide run the scan only after `curl` succeeds. The README additionally requires
its version check to pass before scanning. The commands remain POSIX-shell
compatible and keep the same versioned release URL, output path, and free CLI
behavior.

An executable contract extracts the exact three public snippets, replaces
`curl` with a stub that exits 22 and `python3` with an invocation marker, and
runs each block through `/bin/sh`. Every surface must preserve exit 22 without
reaching Python. The rendered-site contract separately proves the visible
command includes the conditional boundary.

This is an activation reliability correction for the free adoption path. It
does not create another acquisition asset or paid-policy capability, establish
an install or customer use, approve outreach or deployment, validate
willingness to pay, collect payment, or record revenue.

## 2026-07-28: Bind Schema-7 Pricing To The Public Intake Price

Public readiness and commercial-fit answers explicitly name the $299 pilot,
but `repo-scout-pilot --pilot-price` previously accepted any positive integer.
A request saying it was ready to purchase at $299 could therefore be queued
with an instruction to send $400 terms. Paid labels and source segments could
also be multiplied by that unrelated configured price, overstating booked
revenue without corresponding public evidence.

The schema-7 producer now requires `pilot_price_usd` to equal the price named
in public intake. Price-bearing readiness and commercial-fit option strings are
derived from that same constant. A mismatch fails before issue parsing, queue
construction, revenue arithmetic, or output for both direct API and CLI calls.
The CLI performs that check before reading stdin or a file. The `--pilot-price`
argument remains as an explicit compatibility guard so automation using the
current value continues to work and stale assumptions fail closed.

Joined growth ingestion applies the same price boundary to saved schema-7
reports before trusting their qualification-aware sales queue. Older aggregate
schemas remain readable, including their historical custom-price behavior,
because they predate deal-level qualification evidence. Pilot targets and
staleness windows remain independently configurable positive integers.

This supersedes the July 22 decision that treated a custom schema-7 price as a
valid current commercial assumption. A future price change must update the
public offer, issue-form answers, reporter constant, and commercial contracts
together. This correction protects willingness-to-pay and booked-revenue truth;
it does not change the $299 offer, create demand, approve outreach or
deployment, collect payment, or record revenue.

## 2026-07-29: Do Not Turn Empty Schema-7 Queues Into Phantom Deals

Pilot milestones are cumulative, while the schema-7 sales queue intentionally
contains only open pre-payment issues. A closed qualified or offered issue
therefore remained in historical qualification and offer totals but left no
queue entry. Joined growth collapsed that valid empty queue into the same false
value used for legacy reports without deal-level evidence, then emitted a
legacy instruction to send terms or resolve a top offered deal that did not
exist. Correctly lost records reproduced the same problem without a
`closed_without_lost` warning.

Growth now distinguishes four states: a legacy aggregate report, a validated
active schema-7 queue, a validated empty schema-7 queue, and a repair-required
schema-7 state with open lifecycle evidence. Active queues retain their exact
qualification-aware handoff when repair is not required. Legacy schema-5 and
schema-6 reports retain their historical aggregate recommendations. During
qualification through an open pilot target, a historical empty queue keeps
cumulative milestone evidence but explicitly says no open pre-payment deal is
available and recommends replenishing live opportunities. Open untracked or
conflicting records instead require lifecycle-label repair before another
sales action, even when a different deal remains active. Acquisition and
post-target retention keep their prior evidence priorities.

Schema-7 ingestion now validates the complete `deals` array and requires every
open lead, qualified, or offered issue number, stage, readiness, and
action-driving qualification fields to appear exactly once in the sales queue.
Detailed deal stages must also reproduce `by_stage`, while their visible
qualification and offer progression must agree with cumulative `by_source`
totals. Deleting a real open deal and changing `summary.sales_actions` to the
forged queue length, self-authorizing GitHub Actions in only the queue, or
escalating both detail and queue stage while leaving stage or source totals
unchanged therefore fails instead of acquiring new commercial meaning.

Integration regressions cover empty queues at qualification, offer, payment,
and open pilot-target stages, including mislabeled closed, correctly lost,
paid, open-untracked, mixed active-plus-repair, self-authorized,
coordinated-stage, aggregate-divergent, and forged-empty records. This protects
sales-operating truth without rewriting history or guessing an outcome. It
does not create a lead, approve or send outreach, reopen an issue, apply a
lifecycle label, collect payment, or record revenue.

## 2026-07-29: Keep Sites Approval Bound To The Exact SSH Authority

The pending source-export request prints a credential-free canonical
repository identity such as `sites.example/repo-scout`, but the later pre-save
check accepted only a URL-shaped approved value. Following the documented
instruction to reuse the approved canonical identity therefore failed before
the exported-source check. Canonicalization also discarded every SSH and SCP
username. `ssh://alice@sites.example/repo-scout.git`,
`bob@sites.example:repo-scout.git`, and the approved HTTPS repository all
collapsed to the same identity even when a host uses the SSH username to select
a repository namespace.

Pre-save verification now accepts either a credential-free remote repository
URL or the exact normalized identity emitted by the pending request.
Conventional `git@` remains protocol-neutral so HTTPS and normal Git hosting
aliases still reconcile, and default ports remain normalized. Every other SSH
URL or SCP username is retained in canonical authority. For those users, SCP
home-relative paths carry the out-of-band `scp-relative://` canonical prefix and
remain distinct from absolute SSH URL or SCP paths, including a literal
absolute `/~/` path. An operational repository under a different username,
non-default port, or path mode therefore cannot inherit approval from a
matching host, visible path, and commit.

Integration regressions replay the emitted canonical identity, preserve an
explicitly approved SSH username across canonical and URL forms, reject
unapproved usernames in both SSH URL and SCP syntax, and retain the existing
default-port and `git@` alias behavior. They also reject an SCP home-relative
path as an alias of an approved absolute path while accepting the explicit
absolute SCP form. This makes the owner-approved source-export tuple executable
without weakening repository identity. It does not grant approval, export
source, save or deploy a Sites version, or create customer, demand, payment, or
revenue evidence.

## 2026-07-29: Authenticate Schema-7 Sales Queue Order In Growth

The pilot funnel emits a deterministic sales queue ordered by disclosed
purchase readiness, funnel stage, issue age, and issue number. Joined growth
validated the same queue by converting both the reported entries and canonical
open deals into dictionaries keyed by issue number. That proved membership and
action content but discarded list order. A saved report could therefore place
lower-intent work ahead of a ready buyer and still be treated as an active
qualification-aware queue.

Schema-7 growth validation now preserves the reported issue sequence and
derives the expected sequence with the funnel producer's shared sort key.
Queued priority must match the normalized readiness answer, and both priority
and age must match the canonical detailed deal before ordering is checked.
Membership, stage, qualification, CI-provider, scope, price-derived action, and
aggregate progression checks remain unchanged. Reordering two otherwise valid
entries, forging priority, or drifting queue age from deal age now fails before
growth can defer a commercial action to the queue.

The regression uses two ready offered deals with different issue ages, confirms
the producer's older-first order, then rejects its reversal along with priority
and age drift. This protects the paid-pilot operating cadence without changing
the public issue, applying a lifecycle label, sending outreach, selecting a
buyer automatically, collecting payment, or recording revenue.

## 2026-07-29: Derive Pilot Queue Age From Activity Evidence

The previous queue-order correction bound each queued age to its detailed deal,
but both values were copied from the same schema-7 report. Joined growth did not
read `follow_up.as_of` or `updated_at`. Coordinating both age copies could
therefore make a newer issue appear older, reorder otherwise valid queue
members, and pass the shared sort contract while the unchanged activity
timestamps contradicted that order.

Schema-7 growth ingestion now requires a canonical `YYYY-MM-DD` report date and
derives every actionable deal age from that date and a canonical UTC activity
timestamp. Missing timestamps require null age, future timestamps retain their
negative age, and source offsets remain valid after the funnel producer
normalizes them to UTC. The normalized queue timestamp is included in the
existing queue/detail reconciliation before canonical order is checked.

Regressions reject coordinated age-and-order edits, missing and noncanonical
report dates, and a queue timestamp that drifts from its detailed deal. They
also preserve producer-generated null, future, and UTC-offset activity cases.
This makes paid-pilot prioritization internally consistent with its own public
activity evidence. It does not authenticate a wholly rewritten report, contact
a buyer, apply a lifecycle label, collect payment, or record revenue.

## 2026-07-29: Reconcile Pilot Bookings To Detailed Deal Evidence

Schema-7 joined growth reconciled booked pilots and revenue across the summary,
source, and purchase-criterion aggregates, but those tables were all copied
from one saved report. It did not inspect the explicit `booked` value retained
on each detailed deal. Coordinating the aggregate tables could therefore turn
an unchanged offered deal into one booked $299 pilot and move the reported
bottleneck from payment to pilot delivery.

Growth now requires every detailed schema-7 deal to carry a genuine boolean
booking value and requires their sum to equal `summary.booked_pilots` before
aggregate revenue is trusted. A booked lead, qualified, offered, or untracked
deal is rejected because the producer cannot emit payment evidence at those
stages. A paid-stage deal must remain booked. Later active or converted stages
may still lack booking when their public lifecycle labels skipped payment, and
lost or conflicting outcomes may retain a prior booking, preserving the
producer's existing payment-backed accounting semantics.

Regression coverage starts with a valid offered deal and proves coordinated
summary, source, and criterion edits cannot manufacture a booking. It also
rejects non-boolean evidence, a coordinated detailed booking on the offered
deal, and coordinated removal of booking evidence from a paid-stage deal while
preserving valid payment and non-payment reports. This prevents saved aggregate
edits from changing booked revenue or the commercial bottleneck. It does not
authenticate a wholly rewritten report, apply `pilot-paid`, collect payment, or
record revenue.
