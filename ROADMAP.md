# Roadmap

## Delivery Goal

- Reach 1,000 meaningful, tested commits without artificial commit splitting.
- Update `COMMIT_GOAL.md` with the new count on every successful run.

## Near Term

- Select the exact Node `22.13.0` runtime from `.nvmrc` with `nvm install` and
  `nvm use`, run the fail-closed preflight for patched `main`, then obtain
  read-only independent verification of its schema-5 release-bound,
  complete-tree, duplicate-free, branch-bound, archive-stable, receipt-stable,
  test-bracketed, scope-constrained, atomically no-clobber-published archive and
  receipt while `refs/heads/main`, the public release version, the same
  synchronized source commit, and the same archive and receipt digests survive
  every acceptance checkpoint. The requested
  evidence leaves must remain direct regular files rather than initial or
  dangling symlinks. Stable alternate case or Unicode spellings and
  whole-repository or subdirectory-only aliases must fail by filesystem
  identity. Final archive and receipt publication must retain its existing
  no-clobber semantics while requiring existing output parents and creating
  each leaf relative to a parent descriptor held from preflight through the
  complete candidate operation, reusing that descriptor when both outputs
  share a parent. Archive staging, staged archive reads, validation, and cleanup
  must remain bound to the archive-parent and staged-file descriptors now held
  across packaging; output written only through a replaced visible path must
  remain untrusted. Receipt staging, intended-byte validation, staged receipt
  reads, publication, and identity-aware cleanup must likewise remain bound to
  the held receipt-parent and regular-file descriptors now implemented. Hold
  each exact newly published regular file through final source, digest,
  requested-parent, and requested-leaf identity checks before asking for
  explicit source-export approval. Use the offline request mode to locally
  canonicalize the existing Sites source repository, reject `origin`, and
  print one pending tuple containing `release_version`, existing Sites
  `project_id`, `receipt_sha256`, canonical repository identity,
  `refs/heads/main`, and commit as one compact JSON record while keeping
  `deployment_approved=false` as a boolean. Candidate status must use the same
  single-line JSON boundary so opaque IDs and filenames cannot inject approval
  fields or lines. Reject raw whitespace in source repository identities and
  require percent-encoded URL paths where needed. Preserve nonstandard SSH and
  SCP usernames and their relative-versus-absolute path semantics in that
  canonical identity while treating conventional `git@` as protocol-neutral.
  After approval, push its receipt-bound source to the separate Sites source
  repository, verify the unchanged archive and receipt again while requiring
  the approved digest and the exact canonical Sites repository identity from
  the pending request, and resolve that repository's exported
  `refs/heads/main` twice to prove it still equals the receipt commit before
  saving only that matched candidate. The digest and both repository arguments
  must remain one atomic pre-save mode. Local source, `origin`, unrelated
  forks, aliases that resolve to them, and repository identity, username, or
  non-default-port or SCP path-mode drift must fail closed. Versions 46 and 47
  are superseded and must not be deployed. Keep the replacement behind
  separate deployment approval and the immediate post-deployment production
  audit.
- Human-review the five prepared, publicly qualified drafts. The fresh
  owner-only schema-5 bundle is ready at
  `outreach-private/next-review-v5.md`; keep the July 21 schema-4 bundle
  superseded, replace the chosen decision command's `YYYY-MM-DD` values with
  the actual UTC decision date, and use its content-bound `--approve-next` or
  `--decline-next` command. After a decline, replace
  `PRIVATE-REVIEW-PATH` inside its existing single quotes with a new ignored
  owner-only destination before generating the next complete review; paths
  containing spaces remain one shell argument. Send only approved messages one
  at a time, record
  each human send through guarded `--record-contact`, then record the one
  human-sent, day-seven follow-up through guarded `--record-follow-up`. Record
  any human-observed reply, pilot request, rejection, or opt-out through guarded
  `--record-outcome`. Do not add another acquisition asset before executing
  this bounded review queue.
- Collect the first three public pilot requests, work only the schema-10 sales
  queue whose detailed source, purchase-readiness, and purchase-criterion
  attribution for requests, qualification, offers, bookings, revenue,
  payment-backed activation, and resolved outcomes, plus membership, priority,
  canonical activity-derived age, and readiness-stage-age-number order pass
  joined-growth validation. After payment, verify the private delivery contract
  and work the ordered schema-9+ activation queue through payment-backed
  first-repository activation or terminal reconciliation before pursuing
  another sale. Compare readiness and purchase criteria by source.
- Add a private pilot contact path after public intake validates demand.

## Revenue Validation

- Sell three $299 pilots before building billing or license enforcement.
- Validate weekly CI usage with at least two pilot teams.

## Later

- Publish to PyPI under a distinct distribution name after trusted-publisher ownership is configured.
- Add a configurable comparison path-detail limit.
