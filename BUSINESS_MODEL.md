# Business Model

## Revenue Goal

Repo Scout will become a paid local and CI policy tool for small software teams
that use coding agents heavily and need consistent repository handoffs and
guardrails without sending source code to a hosted service.

The immediate target is three paid founding-team pilots, producing $897 in
initial revenue before licensing or billing infrastructure is built.

## Ideal Customer

- Software teams with 5 to 50 developers.
- Teams using coding agents across multiple repositories.
- Engineering leads who own review quality, repository standards, or handoffs.
- Security-conscious teams that prefer local tooling over source-code uploads.

## Offer

### Free Core

- Local repository snapshots in text, JSON, and Markdown.
- Attention findings and CI-friendly exit codes.
- Saved snapshot comparison and bounded changed-path details.

The free CLI should be good enough to adopt without a sales conversation.

### Founding Team Pilot

Price: $299 for 90 days, covering up to 10 repositories.

The pilot includes:

- A shared, version-controlled repository policy.
- CI enforcement guidance and rollout support.
- One custom policy pack for the team's repository standards.
- Direct feedback access and priority fixes during the pilot.

The paid value is consistency across repositories and teams, not access to the
basic local scanner.

## Conversion Path

1. A developer adopts the free CLI for handoffs or reviews.
2. The team adds `--fail-on-attention` to CI.
3. Different repositories need consistent thresholds and required documents.
4. The engineering lead buys a pilot for shared policies and rollout support.

## Validation Milestones

- Sell three pilots before building billing or license enforcement.
- At least two pilot teams run Repo Scout in CI weekly.
- At least one pilot policy is reused across three repositories.
- At least one pilot converts to an annual team license.

## Product Filter

New work must improve acquisition, activation, conversion, or retention for the
paid team workflow. Generic features that do not strengthen that path stay out
of the near-term roadmap.
