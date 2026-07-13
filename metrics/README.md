# Commercial Evidence Baseline

These generated reports preserve public or privacy-safe starting points for
future commercial comparisons. Distribution, pilot, growth, and traffic reports
were captured on 2026-07-12 at 19:22 UTC. The outreach draft report was captured
on 2026-07-13 at 02:32 UTC from:

- GitHub's public release API for `becastil/Chats-empty-repo`.
- Public issues carrying the repository's `pilot-lead` label.
- Repo Scout's dependency-free distribution, pilot, and growth commands.
- An ignored private outreach ledger whose fit links were reviewed against
  narrow company-controlled public evidence.

## Current Readout

- 34 stable releases, all satisfying their version-aware artifact contracts.
- 61 cumulative primary artifact requests: 1 portable and 60 wheel.
- 55 manifest requests, 6 source requests, and 0 unknown requests.
- 0 tracked pilot requests, 0 booked pilots, and $0 booked revenue.
- 0 evidence warnings in the distribution, pilot, and joined growth reports.
- 5 qualified outreach drafts backed by 16 fit-evidence links, with 0 contact
  attempts, replies, pilot requests, or revenue claims.
- A 14-day GitHub traffic window with 1 unique viewer, 119 unique cloners, and
  310 clone events.

GitHub reports cumulative asset requests, not unique people or installations.
The wheel and manifest totals include Repo Scout's own CI and maintainer
verification, so they are directional reach evidence only. The joined report
correctly identifies acquisition as the commercial bottleneck.
The gap between one viewer and 119 unique cloners is consistent with CI,
hosting, and maintainer automation. It cannot support a claim of 119 users or
organic visitors.

## Files

- `distribution-baseline.json` is the schema-2 baseline needed for signed
  per-channel deltas and release-set changes.
- `pilot-baseline.json` is the schema-6 aggregate from the empty public pilot
  queue.
- `growth-baseline.json` joins a zero-delta comparison against the distribution
  baseline with the pilot baseline.
- `github-traffic-baseline.json` preserves the owner-visible 14-day aggregate,
  daily series, top referrers, and popular paths without visitor identities.
- `outreach-draft-baseline.json` preserves only schema-3 aggregate counts; it
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
repo-scout-pilot --format json --as-of "$(date -u +%F)" \
  pilot-issues.json > pilot-current.json
gh api repos/becastil/Chats-empty-repo/traffic/views > traffic-views.json
gh api repos/becastil/Chats-empty-repo/traffic/clones > traffic-clones.json
gh api repos/becastil/Chats-empty-repo/traffic/popular/referrers \
  > traffic-referrers.json
gh api repos/becastil/Chats-empty-repo/traffic/popular/paths \
  > traffic-paths.json
```

Compare the current distribution report to `distribution-baseline.json` before
replacing the baseline. Public pilot issues still require a privacy review
before any non-empty report is committed. Never interpret artifact requests,
clone events, drafts, replies, or page activity as leads, payment, or revenue.
