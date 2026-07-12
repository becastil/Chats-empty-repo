# Commercial Evidence Baseline

These generated reports preserve a public-only starting point for future
distribution and pilot-funnel comparisons. They were captured on
2026-07-12 at 19:22 UTC from:

- GitHub's public release API for `becastil/Chats-empty-repo`.
- Public issues carrying the repository's `pilot-lead` label.
- Repo Scout's dependency-free distribution, pilot, and growth commands.

## Current Readout

- 34 stable releases, all satisfying their version-aware artifact contracts.
- 61 cumulative primary artifact requests: 1 portable and 60 wheel.
- 55 manifest requests, 6 source requests, and 0 unknown requests.
- 0 tracked pilot requests, 0 booked pilots, and $0 booked revenue.
- 0 evidence warnings in the distribution, pilot, and joined growth reports.

GitHub reports cumulative asset requests, not unique people or installations.
The wheel and manifest totals include Repo Scout's own CI and maintainer
verification, so they are directional reach evidence only. The joined report
correctly identifies acquisition as the commercial bottleneck.

## Files

- `distribution-baseline.json` is the schema-2 baseline needed for signed
  per-channel deltas and release-set changes.
- `pilot-baseline.json` is the schema-6 aggregate from the empty public pilot
  queue.
- `growth-baseline.json` joins a zero-delta comparison against the distribution
  baseline with the pilot baseline.

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
repo-scout-pilot --format json --as-of "$(date -u +%F)" \
  pilot-issues.json > pilot-current.json
```

Compare the current distribution report to `distribution-baseline.json` before
replacing the baseline. Public pilot issues still require a privacy review
before any non-empty report is committed. Never interpret artifact requests,
drafts, replies, or page activity as leads, payment, or revenue.
