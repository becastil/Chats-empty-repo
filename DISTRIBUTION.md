# Distribution

Repo Scout distributes a genuinely useful free CLI to create qualified demand
for the paid cross-repository policy pilot. Distribution work is part of the
product, not a release afterthought.

## Adoption Path

1. A developer discovers Repo Scout through the hosted site, GitHub search, a
   release, or a referral.
2. The developer downloads the versioned `.pyz` and gets a local snapshot
   without cloning the repository or modifying a Python environment.
3. A team installs the provenance-attested wheel when it needs all 7
   commands or adopts the verified GitHub Actions policy gate.
4. Cross-repository rollout evidence exposes the need for shared policy
   operations and leads to the $299 founding-team pilot.

The portable artifact is the lowest-friction adoption path. The wheel is the
complete command distribution. The CI example is the team activation path.
None requires an API key or sends source code to Repo Scout.

## Active Website Experiment

- **Started:** 2026-07-10
- **Channels:** Website, GitHub, direct outreach, referral, search, and
  social/community paths through one hosted offer.
- **Audience:** Engineering leads at 5-50 person software teams using coding
  agents across multiple repositories.
- **Hypothesis:** A plain-language answer to "why pay when an AI can recreate
  the scanner?" placed before the disclosed $299 offer will produce the first
  pilot request with a recognized, source-matched discovery answer.
- **Change:** The public site now contrasts the copyable free scan with three
  paid operational outcomes: a repeatable rulebook, one rollout across up to
  10 projects, and evidence plus help when a project fails.
- **Acquisition path:** The GitHub README now introduces the team outcome near
  the top and links into this section before the longer CLI reference.
- **Source handling:** A closed `source` query maps hosted application buttons
  to the existing intake taxonomy. Missing and unknown values safely default to
  `Repo Scout website`; all answers remain visible and editable in intake.
- **Primary outcome:** The first public pilot request with a recognized source
  matching the distributed campaign route.
- **Secondary evidence:** That request's qualification, purchase readiness,
  primary criterion, offer, and paid stages.
- **Review point:** 2026-07-24 or after three public pilot requests, whichever
  comes first.
- **Observed baseline:** On 2026-07-10 the public pilot queue had zero requests.
  The five newest releases had zero requests except one `v0.3.9` wheel request,
  which may be Repo Scout's own verified CI and is not a prospect.
- **Measured checkpoint:** On 2026-07-12 the generated public baseline contained
  34 contract-complete releases, 61 cumulative primary artifact requests
  (1 portable and 60 wheel), and zero pilot requests or booked revenue. Repo
  Scout's CI and maintainer verification materially confound the wheel total.
  The machine-readable reports and capture contract live in `metrics/`.
- **Traffic checkpoint:** The owner-visible 14-day window ending 2026-07-16
  contained 3 views from 1 unique viewer, 293 unique cloners, and 962 clone
  events. Compared with the overlapping window ending 2026-07-11, views rose
  by 2 without another unique viewer while clone events rose by 652. The
  clone-heavy mismatch is consistent with CI, hosting, and maintainer
  automation and is not evidence of 293 users.

This experiment has no browser analytics. Release requests and site visits are
not unique prospects, and self-reported source does not prove causation. Only
funnel labels and payment evidence count as conversion and revenue. If no
request arrives, the result is inconclusive because qualified site traffic is
not measured.

The source-prefill keys use the issue form's canonical `discovery_source` field
ID and exact option values. They reduce intake friction but do not silently set
labels, prove attribution, or prevent a buyer from correcting the answer.

## Campaign Routes

Share only the route matching the actual discovery context:

| Context | Hosted offer route | Intake prefill |
| --- | --- | --- |
| Organic website | `https://repo-scout.becastil.chatgpt.site/#why-teams-buy` | Repo Scout website |
| GitHub | `https://repo-scout.becastil.chatgpt.site/?source=github#why-teams-buy` | GitHub repository or release |
| Direct outreach | `https://repo-scout.becastil.chatgpt.site/?source=outreach#why-teams-buy` | Direct outreach |
| Teammate or referral | `https://repo-scout.becastil.chatgpt.site/?source=referral#why-teams-buy` | Teammate or referral |
| Search | `https://repo-scout.becastil.chatgpt.site/?source=search#why-teams-buy` | Search |
| Social or community | `https://repo-scout.becastil.chatgpt.site/?source=social#why-teams-buy` | Social media or community |

The server accepts only `github`, `website`, `outreach`, `referral`, `search`,
`social`, and `other`. For repeated parameters, only the first value is
considered. An absent or unsupported first value uses the website default
instead of reflecting arbitrary text into intake.

The hosted offer also includes a user-initiated email action for sharing the
team workflow with an engineering lead. Its prewritten message names the $299
scope and local-code boundary, then links through the referral route above. It
opens the visitor's email client and sends nothing automatically; Repo Scout
does not receive an address, click event, or proof that the message was sent.

## Direct Outreach Experiment

The [direct outreach playbook](docs/direct-outreach.md) defines the first
operator-led acquisition batch: 10 individually qualified prospects, one
accurate public observation per message, the source-preserving outreach route,
and at most one follow-up after seven days. An opt-out or not-interested reply
ends contact immediately. Sales messages never belong in GitHub issues, pull
requests, or security channels.

The header-only `examples/outreach-ledger.csv` can be copied into the ignored
`outreach-private/` directory. Its current ten-column shape retains outcome
observation dates, while legacy nine-column ledgers remain readable without
inventing missing history. The ledger uses prospect aliases and records
operator activity without committing names, addresses, message bodies, source
code, or confidential company details. `repo-scout-outreach` validates the
10-prospect cap, qualification keys, permitted channels, alias format, and the
single seven-day follow-up before reporting due aliases. It sends nothing.
Replies remain outreach activity; only public intake and cumulative funnel
labels become demand and revenue evidence.

## Search Discovery

The hosted companion publishes a deterministic `robots.txt` and `sitemap.xml`
for its one production page. Every campaign-query variant declares the same
production canonical URL, so GitHub, outreach, referral, search, and social
links retain their buyer-facing source behavior without asking crawlers to
index duplicate pages. Open Graph metadata also names that canonical page.

Crawler access and a sitemap improve discoverability hygiene; they do not prove
indexing, search visits, activation, pilot demand, or revenue. Search becomes
commercial evidence only when a buyer self-reports it in intake and advances
through the labeled funnel.

The canonical page also publishes one JSON-LD graph describing the free CLI as
a `SoftwareApplication` with its exact versioned download and $0 offer, and the
founding-team pilot as a separate `Service` with the visible $299, 90-day,
up-to-10-project scope. The graph contains no reviews, ratings, hidden urgency,
or campaign URLs. Machine-readable offers can help crawlers understand the
page, but they do not guarantee a rich result or count as acquisition evidence.

## Release Contract

Every tagged release must publish and attest exactly these artifacts:

- `repo-scout-X.Y.Z.pyz`
- `repo_scout-X.Y.Z-py3-none-any.whl`
- `repo_scout-X.Y.Z.tar.gz`
- `SHA256SUMS`

The release workflow runs the primary CLI from the zipapp, installs the wheel
in a clean environment, exercises all packaged commands, and covers every
artifact with the checksum manifest and GitHub build provenance.

## Channel Metrics

Review these signals before weekly roadmap work:

- Unique GitHub repository views and clones.
- Release requests by artifact, especially portable versus wheel distribution.
- Pilot requests attributed to the website, GitHub release, outreach, or a
  referral.
- Purchase readiness and booked revenue by discovery source.

Export GitHub's public release records and analyze them locally:

```bash
curl -fsSL 'https://api.github.com/repos/becastil/Chats-empty-repo/releases?per_page=100' \
  | repo-scout-distribution
```

`repo-scout-distribution` performs no network calls. Its schema-2 JSON and text
reports validate the version-aware artifact contract, separate portable and
wheel primary requests from source, manifest, and unknown requests, and flag
missing or unexpected assets. The portable artifact became required in
`v0.3.4`; earlier releases remain valid without it.

For weekly movement, save the current JSON report and compare the next public
release export to it:

```bash
curl -fsSL 'https://api.github.com/repos/becastil/Chats-empty-repo/releases?per_page=100' \
  -o releases.json
repo-scout-distribution --format json releases.json > distribution-baseline.json
repo-scout-distribution releases.json --baseline distribution-baseline.json
```

Schema 2 accepts schema-1 and schema-2 baselines. It reports signed channel
deltas plus new and removed releases. A download counter decrease, removed
artifact, or removed release is a warning because GitHub release assets are
expected to be immutable. Baselines contain public aggregate release metadata,
not repository source or customer data.

GitHub counts requests rather than unique users. Wheel counts include Repo
Scout's own verified CI bootstrap, and all channels may include maintainer
checks or retries. Treat the report as directional distribution evidence, not
an install, activation, or revenue count. Booked revenue requires the
`pilot-paid` label itself; later labels do not substitute for missing payment
evidence.

## Weekly Growth Review

Generate both machine-readable evidence streams, then review them together:

```bash
repo-scout-distribution --format json releases.json \
  --baseline distribution-baseline.json > distribution-current.json
repo-scout-pilot --format json --as-of "$(date -u +%F)" \
  pilot-issues.json > pilot-current.json
repo-scout-growth distribution-current.json pilot-current.json
```

`repo-scout-growth` emits schema 2 from schema-2 distribution and schema-5 or
schema-6 pilot reports. It shows signed primary, portable, and wheel movement
beside attributed pilot requests, qualification, offers, booked revenue, source
totals, and schema-6 purchase-criterion outcomes. Schema-5 criterion evidence is
explicitly unavailable rather than reported as zero. Its
deterministic bottleneck names one next action for missing measurement,
acquisition, qualification, offer, payment, pilot-target progress, retention,
or validated commercial evidence.

The review strictly reconciles schema-6 criterion keys and outcomes to source
totals, then surfaces warnings from both inputs and attribution gaps. It
does not divide pilot requests by artifact requests, join a download to a lead,
assign artifact movement to a criterion, or infer that stated criteria caused
revenue. Save the current distribution report as the next baseline only after
reviewing any release-evidence warnings.

The repository's current reviewed baseline is committed under `metrics/` with
tests that reconcile release totals and preserve zero pilot and revenue truth.
It is a deliberate comparison point, not a counter to refresh on every commit.
The same directory retains the owner-visible rolling traffic aggregate and
daily series; GitHub does not expose visitor identities in this report.

## Channel Constraints

As of 2026-07-10, PyPI's normalized `repo-scout` name belongs to an unrelated
package. Do not upload this project under a confusing name or weaken artifact
verification to gain another channel. A future PyPI launch needs a distinct
distribution name, verified ownership, trusted publishing, and matching install
documentation while preserving the `repo-scout` command name.
