# Roadmap

## Delivery Goal

- Reach 1,000 meaningful, tested commits without artificial commit splitting.
- Update `COMMIT_GOAL.md` with the new count on every successful run.

## Near Term

- Select the exact Node `22.13.0` runtime from `.nvmrc` with `nvm install` and
  `nvm use`, run the fail-closed preflight for patched `main`, then obtain
  read-only independent verification of its schema-4 complete-tree,
  duplicate-free, branch-bound, archive-stable, receipt-stable, test-bracketed,
  scope-constrained, atomically no-clobber-published archive and receipt while
  `refs/heads/main`, the same synchronized source commit, and the same archive
  and receipt digests survive every acceptance checkpoint, before asking for
  explicit source-export approval that records the printed `receipt_sha256`.
  After approval, push its receipt-bound source to the separate Sites source
  repository, verify the unchanged archive and receipt again while requiring
  the approved digest and canonical Sites repository identity, and resolve
  that repository's exported `refs/heads/main` twice to prove it still equals
  the receipt commit before saving only that matched candidate. The digest and
  both repository arguments must remain one atomic pre-save mode. Local source,
  `origin`, unrelated forks, aliases that resolve to them, and repository
  identity or non-default-port drift must fail closed. Versions 46 and 47 are
  superseded and must not be deployed. Keep the replacement behind separate
  deployment approval and the immediate post-deployment production audit.
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
