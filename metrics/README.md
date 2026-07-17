# Commercial Evidence Baseline

These generated reports preserve public or privacy-safe starting points for
future commercial comparisons. Distribution, pilot, and growth reports were
refreshed on 2026-07-17 at 22:41 UTC. The outreach draft report was captured on
2026-07-14, and the traffic report was captured on 2026-07-17 at 18:40 UTC,
from:

- GitHub's public release API for `becastil/Chats-empty-repo`.
- Public issues carrying the repository's `pilot-lead` label.
- Repo Scout's dependency-free distribution, pilot, and growth commands.
- An ignored private outreach ledger whose fit links were reviewed against
  narrow company-controlled public evidence.

## Current Readout

- 47 stable releases, all satisfying their version-aware artifact contracts.
- 190 cumulative primary artifact requests: 25 portable and 165 wheel.
- 156 manifest requests, 28 source requests, and 0 unknown requests.
- 14 additional primary artifact requests since the prior checkpoint: 3
  portable and 11 wheel. The new `v0.3.43` release accounts for 7 requests,
  while `v0.3.42` gained 7 wheel requests.
- 0 tracked pilot requests, 0 booked pilots, and $0 booked revenue.
- 0 evidence warnings in the distribution, pilot, and joined growth reports.
- 5 qualified outreach drafts backed by 16 fit-evidence links, with 0 approvals,
  contact attempts, replies, pilot requests, or revenue claims.
- A 14-day GitHub traffic window with 3 views from 1 unique viewer, 293 unique
  cloners, and 962 clone events.

GitHub reports cumulative asset requests, not unique people or installations.
The wheel and manifest totals include Repo Scout's own CI and maintainer
verification, so they are directional reach evidence only. The 14-request
increase did not produce a pilot request; the joined report correctly keeps
acquisition as the commercial bottleneck.
The prior overlapping window contained 1 view from 1 unique viewer, 119 unique
cloners, and 310 clone events. The new window adds only 2 views and no unique
viewer while clone activity rises by 652 events and 174 unique cloners. That
widening gap is consistent with CI, hosting, and maintainer automation and
cannot support a claim of 293 users or organic visitors. Overlapping rolling
windows are not additive, and GitHub's popular referrer and path lists are
partial rankings rather than exhaustive traffic reconciliations.

## Files

- `distribution-baseline.json` is the schema-2 baseline needed for signed
  per-channel deltas and release-set changes.
- `pilot-baseline.json` is the schema-7 aggregate from the empty public pilot
  queue.
- `growth-baseline.json` joins the signed 14-request movement from the prior
  distribution checkpoint with the schema-7 pilot baseline.
- `github-traffic-baseline.json` preserves the owner-visible 14-day aggregate,
  daily series, partial top referrers, and partial popular paths without visitor
  identities.
- `outreach-draft-baseline.json` preserves only schema-5 aggregate counts; it
  contains no prospect alias, company, contact address, draft, or source URL.

## Refresh Contract

Refresh these files only at a deliberate review point, not on every automated
builder run. Export public evidence, inspect all warnings, then generate the
reports with:

```bash
gh api 'repos/becastil/Chats-empty-repo/releases?per_page=100' > releases.json
gh issue list --repo becastil/Chats-empty-repo --state all \
  --label pilot-lead --limit 100 \
  --json number,title,body,state,labels,createdAt,updatedAt,closedAt,url \
  > pilot-issues.json
repo-scout-distribution --format json releases.json \
  > distribution-current.json
repo-scout-distribution --format json \
  --baseline metrics/distribution-baseline.json releases.json \
  > distribution-comparison.json
repo-scout-pilot --format json --as-of "$(date -u +%F)" \
  pilot-issues.json > pilot-current.json
repo-scout-growth --format json distribution-comparison.json pilot-current.json \
  > growth-current.json
repo-scout-outreach outreach-private/outreach-ledger.csv \
  --as-of "$(date -u +%F)" --format json > outreach-current.json
gh api repos/becastil/Chats-empty-repo/traffic/views > traffic-views.json
gh api repos/becastil/Chats-empty-repo/traffic/clones > traffic-clones.json
gh api repos/becastil/Chats-empty-repo/traffic/popular/referrers \
  > traffic-referrers.json
gh api repos/becastil/Chats-empty-repo/traffic/popular/paths \
  > traffic-paths.json
```

Generate and inspect the comparison and growth reports before replacing any
baseline. Public pilot issues still require a privacy review
before any non-empty report is committed. Never interpret artifact requests,
clone events, drafts, replies, or page activity as leads, payment, or revenue.
