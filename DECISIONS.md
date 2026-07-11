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
