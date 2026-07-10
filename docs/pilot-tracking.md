# Pilot Revenue Tracking

Repo Scout tracks founding-team pilot requests as public GitHub issues and
turns their cumulative labels into a deterministic funnel report. The reporter
reads a local JSON export; it does not call GitHub, store credentials, or treat
an offer as revenue.

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
  --json number,title,state,labels,createdAt,updatedAt,closedAt,url \
  | repo-scout-pilot --as-of "$(date -u +%F)"
```

Use `--format json` for a machine-readable report. `--pilot-price` and
`--target-pilots` change the commercial assumptions without changing issue
data.

Funnel JSON declares `schema_version: 2`. Its `follow_up` object records the
UTC `as_of` date, the inactivity threshold, and a deterministic deal list.
Omit `--as-of` to use the current UTC date. `--stale-days` changes the default
seven-day threshold.

The default report measures the current founding goal:

- $299 per paid pilot.
- Three paid pilots.
- $897 target initial revenue.
- One annual conversion as the retention milestone.

Booked revenue includes issues that reached `pilot-paid` or a later cumulative
stage. A later `pilot-lost` label does not erase cash already received. If a
payment is refunded, remove `pilot-paid` and later paid-stage labels before the
next report, and retain the refund evidence outside the public issue.

## Operating Cadence

Run the report weekly and before each roadmap review. Resolve label warnings
before sharing totals. The follow-up list includes only open `pilot-lead`,
`pilot-qualified`, and `pilot-offered` issues whose UTC `updatedAt` date is at
least the threshold age. The boundary is inclusive.

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
