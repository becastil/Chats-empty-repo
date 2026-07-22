# Roadmap

## Delivery Goal

- Reach 1,000 meaningful, tested commits without artificial commit splitting.
- Update `COMMIT_GOAL.md` with the new count on every successful run.

## Near Term

- Publish the next patch release through the enabled immutable-release setting,
  verify the exact GitHub release reports `immutable: true`, and only then
  advance paid-CI pins away from mutable `v0.3.50`.
- Human-review the five prepared, publicly qualified drafts. The first
  owner-only `--write-review` bundle is ready in the ignored private workspace;
  use its content-bound `--approve-next` or
  `--decline-next` command emitted by each complete private review, send only
  approved messages one at a time, record
  each human send through guarded `--record-contact`, then record the one
  human-sent, day-seven follow-up through guarded `--record-follow-up`. Record
  any human-observed reply, pilot request, rejection, or opt-out through guarded
  `--record-outcome`. Do not add another acquisition asset before executing
  this bounded review queue.
- Collect the first three public pilot requests, work the prioritized sales queue, and compare readiness and purchase criteria by source.
- Add a private pilot contact path after public intake validates demand.

## Revenue Validation

- Sell three $299 pilots before building billing or license enforcement.
- Validate weekly CI usage with at least two pilot teams.

## Later

- Publish to PyPI under a distinct distribution name after trusted-publisher ownership is configured.
- Add a configurable comparison path-detail limit.
