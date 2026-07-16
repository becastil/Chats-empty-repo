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
