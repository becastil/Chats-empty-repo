# Pilot Revenue Tracking

Repo Scout tracks founding-team pilot requests as public GitHub issues and
turns their cumulative labels into a deterministic funnel report. The reporter
reads a local JSON export; it does not call GitHub, store credentials, or treat
an offer as revenue.

Every new request declares one public purchase-readiness state: ready to
purchase the $299 pilot, needs internal approval, or exploring before requesting
budget. Do not infer a stronger state from free text or move a deal forward
based on readiness alone.

Every new request also declares one primary purchase criterion. This is the
result the buyer says matters most when evaluating the pilot, not a claim that
Repo Scout has already satisfied it.

## Funnel Labels

Keep each earlier milestone label when a request advances:

| Label | Apply when |
| --- | --- |
| `pilot-lead` | The public request form creates the issue. |
| `pilot-qualified` | The team fits the target profile and has a concrete multi-repository policy need. |
| `pilot-offered` | A written $299, 90-day scope has been sent. |
| `pilot-paid` | Payment has been received. This is the first booked-revenue stage. |
| `pilot-active` | The paid pilot is running in at least one repository. |
| `pilot-converted` | The pilot has converted to an annual team license. |
| `pilot-lost` | The opportunity is no longer being pursued. |

Use the [paid delivery contract](pilot-rollout.md#paid-pilot-delivery-contract)
as the activation evidence boundary. Apply `pilot-active` only after
`pilot-paid` is already present and every activation condition in that contract
is satisfied, including customer acknowledgement of the first-repository
handoff. Keep repository identity, access, CI evidence, payment details, and
the acknowledgement record in the customer-approved private system or
short-lived ignored `pilot-private/` fallback. The public issue receives only
the cumulative label and a non-sensitive status note.

`pilot-lost` can retain the milestones reached before the opportunity ended.
Never apply both `pilot-converted` and `pilot-lost`; the reporter flags that as
a terminal conflict. It also flags skipped milestones and unknown `pilot-*`
labels.

## Weekly Report

After installing the project in editable mode, export the public pilot issues
and pipe them into the local reporter:

```bash
gh issue list \
  --repo becastil/Chats-empty-repo \
  --state all \
  --label pilot-lead \
  --limit 100 \
  --json number,title,body,state,labels,createdAt,updatedAt,closedAt,url \
  | repo-scout-pilot --as-of "$(date -u +%F)"
```

Use `--format json` for a machine-readable report. `--pilot-price` and
`--target-pilots` change the commercial assumptions without changing issue
data.

Funnel JSON declares `schema_version: 7`. Its `follow_up` object records the
UTC `as_of` date, the inactivity threshold, and a deterministic deal list.
Omit `--as-of` to use the current UTC date. `--stale-days` changes the default
seven-day threshold.

The `sales_queue.deals` array contains every open lead, qualified, or offered
pilot, including fresh deals. Priorities come only from the declared readiness
answer: ready is `P1`, needs approval is `P2`, exploring is `P3`, and missing
or unrecognized readiness is `P4`. Within one priority, offered deals come
before qualified deals, then leads; older issue activity breaks ties before
issue number. Each record includes a stage-specific `next_action`. The queue
does not apply labels, send messages, infer willingness to pay, or count
revenue.

Every deal, stale-deal, and sales-queue record also contains a `qualification`
object derived from the four required scope fields. It includes normalized
positive integers for team and repository counts, a closed CI-provider key,
whether a repository-standard answer is present, and review reasons. Status is
`target` for teams of 5 to 50 developers with at least two repositories,
`outside_target` for complete requests outside that profile, and `incomplete`
for missing, duplicate, or invalid answers. Repository counts above 10 remain
target-profile candidates but use `pilot_repository_scope: subset_required` so
the written pilot scope selects the first 10 repositories. The reporter never
copies repository-standard free text into its output.

The request form also asks how the buyer discovered Repo Scout. The reporter
maps that issue-body answer to a stable source key:

| Source key | Intake answer |
| --- | --- |
| `github` | GitHub repository or release |
| `website` | Repo Scout website |
| `outreach` | Direct outreach |
| `referral` | Teammate or referral |
| `search` | Search |
| `social` | Social media or community |
| `other` | Other |

The `by_source` object reports deals, qualified pilots, offered pilots, booked
pilots, booked revenue, annual conversions, and losses for every source key.
Deal records and stale follow-up records include their normalized source.
Legacy issues without the form answer use `unattributed`; edited answers that
do not match the taxonomy, or duplicate source headings, use `unknown`. Each
case produces a warning rather than silently guessing a channel.

The `by_readiness` object reports the same funnel and revenue totals for
`ready`, `needs_approval`, `exploring`, `unattributed`, and `unknown`. Deal
records include normalized `purchase_readiness` and the original
`purchase_readiness_raw` answer; stale follow-up records carry the normalized
state for prioritization. Missing, unrecognized, and duplicate answers produce
warnings rather than a guessed readiness state.

The `by_decision_criterion` object reports the same funnel and revenue totals
for the buyer's selected primary criterion:

| Criterion key | Intake answer |
| --- | --- |
| `policy_fit` | Supports our required repository standards |
| `rollout_fit` | Works across our repositories and CI |
| `evidence_fit` | Produces evidence our leaders or auditors need |
| `privacy_security` | Meets our privacy and security requirements |
| `effort_timing` | Fits our implementation capacity and timing |
| `commercial_fit` | The $299 scope and price fit |
| `other` | Other |

Deal, stale-follow-up, and sales-queue records include the normalized
`decision_criterion`; deal records also preserve `decision_criterion_raw`.
Legacy issues without the answer use `unattributed`. Edited answers that do not
match the taxonomy, or duplicate criterion headings, use `unknown`. Both remain
visible in summary totals and warnings. Sales priority remains based on purchase
readiness, not on the criterion selected.

`repo-scout-growth` consumes these schema-6 and schema-7 criterion totals in its weekly
commercial review. It requires the exact taxonomy, validates each cumulative
stage and revenue value, and reconciles aggregate criterion outcomes to source
outcomes. Schema-5 pilot reports remain readable with criterion reporting marked
unavailable rather than zero.

Source attribution is self-reported discovery data. It does not prove which
touchpoint caused a purchase, and it should be used directionally when deciding
where to focus outreach. Repo Scout does not add cookies, tracking pixels, or a
hosted analytics service for this report.

The default report measures the current founding goal:

- $299 per paid pilot.
- Three paid pilots.
- $897 target initial revenue.
- One annual conversion as the retention milestone.

Booked revenue requires the `pilot-paid` label itself; later labels do not
substitute for missing payment evidence. A later `pilot-lost` label does not
erase cash already received. If a payment is refunded, remove `pilot-paid` and
later paid-stage labels before the next report, and retain the refund evidence
outside the public issue.

Resolved annual-conversion totals also require `pilot-paid`. A
`pilot-converted` issue that skipped payment keeps its visible stage and
`missing_prior_stage` warning for repair, but contributes zero conversions to
the overall, source, readiness, and purchase-criterion totals.

The readiness summary is willingness-to-pay evidence, not accounting. A
`ready` request contributes $0 until payment is received and the issue reaches
`pilot-paid`.

## Operating Cadence

Run the report weekly and before each roadmap review. Resolve label, source,
readiness, and decision-criterion warnings before sharing totals. Work the sales
queue from lowest priority number to highest, recording the actual outcome
separately. The
follow-up list includes only
open `pilot-lead`, `pilot-qualified`, and `pilot-offered` issues whose UTC
`updatedAt` date is at least the threshold age. The boundary is inclusive.

GitHub `updatedAt` measures issue inactivity, not customer contact. Comments,
label changes, and title edits all refresh it, so a fresh issue is not evidence
that a buyer received a follow-up. Closed pre-payment issues without
`pilot-lost`, missing activity timestamps, and future timestamps are warnings
and are excluded from follow-up.

For every open deal, record only non-sensitive status notes in the issue and
keep source code, credentials, customer data, contracts, payment details, and
private contact information outside GitHub.

The pipeline is evidence, not the sale: `pilot-offered` measures conversion
work, while only `pilot-paid` moves booked revenue toward $897.

Compare purchase criteria only after outcomes exist. Repeated paid or
payment-backed converted results can show which proof, policy pack, or rollout
playbook deserves more investment; unqualified requests and stated preferences
alone do not establish a moat or willingness to pay.
