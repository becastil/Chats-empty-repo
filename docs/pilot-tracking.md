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
  | repo-scout-pilot
```

Use `--format json` for a machine-readable report. `--pilot-price` and
`--target-pilots` change the commercial assumptions without changing issue
data.

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
before sharing totals. For every open deal, record only non-sensitive status
notes in the issue and keep source code, credentials, customer data, contracts,
payment details, and private contact information outside GitHub.

The pipeline is evidence, not the sale: `pilot-offered` measures conversion
work, while only `pilot-paid` moves booked revenue toward $897.
