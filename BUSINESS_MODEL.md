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
- A copy-ready, read-only GitHub Actions policy gate with failure evidence.
- Offline starter policies for baseline, Python, npm, and agent-ready services.
- Versioned GitHub release artifacts with checksums and verifiable build provenance.

The free CLI should be good enough to adopt without a sales conversation.

Verified GitHub releases remove source-checkout trust and installation friction
from pilot onboarding. PyPI distribution, billing, and license enforcement stay
deferred until paid demand justifies their operational cost.

### Founding Team Pilot

Price: $299 for 90 days, covering up to 10 repositories.

The pilot includes:

- A shared, version-controlled repository policy.
- CI enforcement guidance and rollout support.
- One custom policy pack for the team's repository standards.
- Direct feedback access and priority fixes during the pilot.

The paid value is consistency across repositories and teams, not access to the
basic local scanner.

The first shared-policy release supports required files, repository file and
byte limits, and clean Git enforcement through a strict TOML file that can be
committed once and reused in CI.

## Conversion Path

1. A developer adopts the free CLI for handoffs or reviews.
2. The team initializes and commits the closest starter policy.
3. The team copies the GitHub Actions gate into its first repository.
4. The team needs one custom standard applied consistently across repositories.
5. The engineering lead reviews the hosted offer and submits a qualified pilot request.
6. The engineering lead buys a pilot for shared policies and rollout support.

The current request form is a public GitHub issue and warns teams not to share
source code or sensitive details. A private intake channel is deferred until
pilot demand validates the additional infrastructure.

## Validation Milestones

- Sell three pilots before building billing or license enforcement.
- At least two pilot teams run Repo Scout in CI weekly.
- At least one pilot policy is reused across three repositories.
- At least one pilot converts to an annual team license.

## Revenue Evidence

Founding-team requests are tracked with cumulative `pilot-*` labels and the
dependency-free `repo-scout-pilot` report. Only issues that reach `pilot-paid`
or a later paid stage count toward the three-pilot and $897 initial-revenue
targets. Qualified leads and written offers remain pipeline, not booked
revenue. Label warnings must be resolved before totals are used in a roadmap or
sales decision.

Open lead, qualified, and offered issues inactive for seven UTC calendar days
appear in the funnel's follow-up list. This is an operating prompt based on
GitHub issue activity, not evidence that a buyer was or was not contacted.

The intake records one required, self-reported discovery channel. Funnel source
totals connect those channels to qualification, offers, booked revenue,
conversion, and loss. Missing or edited legacy answers remain explicit warning
buckets. This is directional acquisition evidence, not proof that a single
touchpoint caused a purchase.

## Product Filter

New work must improve acquisition, activation, conversion, or retention for the
paid team workflow. Generic features that do not strengthen that path stay out
of the near-term roadmap.

The 1,000-commit delivery goal does not weaken this filter. Commit count is a
measure of sustained execution; revenue evidence remains the measure of product
success.
