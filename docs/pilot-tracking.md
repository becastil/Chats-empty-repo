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

Use `--format json` for a machine-readable report. `--target-pilots` changes
the validation target without changing issue data. The retained
`--pilot-price` input must match the current $299 public intake price; a
mismatch fails before input I/O or issue parsing because the saved readiness and
commercial-fit answers do not establish willingness to pay another price.

When calling `build_funnel` directly, `pilot_price_usd`, `target_pilots`, and
`stale_days` must be genuine positive integers. Booleans, floats, and numeric
strings fail before issue parsing so the emitted pricing and follow-up schema
remains compatible with joined growth validation. A positive
`pilot_price_usd` must also equal the public intake price.

For direct API calls, only `as_of=None` selects the current UTC date. Any
supplied `as_of` value must be a real `date`; falsey booleans, numbers, and
strings fail instead of silently changing the report window to today.

Funnel JSON declares `schema_version: 8`. Its `follow_up` object records the
UTC `as_of` date, the inactivity threshold, and a deterministic deal list.
Omit `--as-of` to use the current UTC date. `--stale-days` changes the default
seven-day threshold.

Every schema-8 detailed deal carries boolean `qualified` and `offered`
milestones in addition to its current stage and booking evidence. These values
preserve cumulative lifecycle history after a deal advances or closes.

The `sales_queue.deals` array contains every open lead, qualified, or offered
pilot, including fresh deals. Priorities come only from the declared readiness
answer: ready is `P1`, needs approval is `P2`, exploring is `P3`, and missing
or unrecognized readiness is `P4`. Within one priority, offered deals come
before qualified deals, then leads; older issue activity breaks ties before
issue number. Each record includes a stage-specific `next_action`.
Joined growth accepts that schema-7+ queue only when each priority and age
matches the canonical detailed deal and the list preserves the same
readiness-stage-age-number order. A reordered saved queue fails before growth
can defer a commercial action to it.
It also derives each actionable age from `follow_up.as_of` and the canonical
UTC `updated_at` value. Changing both copied ages cannot reorder the queue while
the activity timestamps remain unchanged; queue timestamps must also match the
detailed deal.

For a ready-to-purchase request, GitHub Actions keeps the normal terms or
payment action only when the qualification is `target` and
`pilot_repository_scope` is `within_offer`. GitLab CI, CircleCI, Buildkite,
and `Other` first require the operator to record the private CI integration
decision. Missing, no-response, edited, or duplicate provider evidence requires
provider clarification first. For GitHub Actions, incomplete or outside-target
qualification requires scope review, and `subset_required` requires an explicit
first-10-repository scope before another terms or payment action.
Approval-dependent, exploratory, and unclear-readiness actions retain their
existing purpose because they do not direct payment. These overrides do not
change queue membership, priority, ordering, qualification status, or booked
revenue. The queue cannot observe private decisions and therefore remains
advisory; it does not apply labels, send messages, infer willingness to pay, or
count revenue.
Schema-7+ growth reviews likewise defer offer, payment, and open pilot-target
actions to this queue rather than reconstructing a provider-blind commercial
recommendation. Older pilot-report schemas retain their existing aggregate
actions because they predate qualification evidence. During qualification
through an open pilot target, a validated empty schema-7+ queue remains distinct
from those legacy reports: growth preserves cumulative milestone history,
states that no open pre-payment deal is available, and recommends replenishing
the queue rather than sending terms, confirming payment, closing, or naming a
nonexistent deal. An open request with an untracked or conflicting lifecycle
stage instead requires label repair before another sales action, even when a
different deal remains active. Acquisition, retention, and validated stages
retain their existing evidence priorities.
Before deferring, growth reconciles `summary.sales_actions` with the embedded
queue, requires every open pre-payment deal identity, stage, readiness, and
action-driving qualification field to appear exactly once, and requires
detailed deal stages to reproduce `by_stage`. Schema 8 also requires explicit
qualification and offer milestones to reproduce cumulative totals by source,
purchase readiness, and purchase criterion. It then
validates each queued deal's public-intake-bound pilot price and exact next
action. Missing, incomplete, self-authorized, stage-divergent, or
aggregate-divergent queues and saved schema-7+ reports carrying a provider-blind,
scope-blind, or stage-skipping action fail closed.

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

`repo-scout-growth` consumes these schema-6, schema-7, and schema-8 criterion
totals in its weekly commercial review. It requires the exact taxonomy,
validates each cumulative stage and revenue value, and reconciles aggregate
criterion outcomes to source outcomes. For schema 8, qualification and offer
totals must also derive from each detailed deal's explicit milestones. Schema-5
pilot reports remain readable with criterion reporting marked unavailable
rather than zero.

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
Pilot issue JSON with duplicate keys is rejected before issue parsing, so
conflicting `labels` fields cannot silently change booked-pilot or revenue
totals.
Public issue titles are normalized around surrounding whitespace, then must be
non-empty printable text of at most 1,024 characters. Any remaining line break,
terminal control, bidirectional control, Unicode separator, or oversized text
fails with exit code 2 before text or JSON output. Issue URLs must be empty or
printable text of at most 2,048 characters without surrounding whitespace.
Controlled errors do not repeat the unsafe title or URL.
Unrecognized edited source, readiness, and purchase-criterion answers and
unrecognized pilot labels remain in escaped JSON review fields. Text warnings
are generic and do not interpolate those public values into terminal output.

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
