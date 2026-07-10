# Distribution

Repo Scout distributes a genuinely useful free CLI to create qualified demand
for the paid cross-repository policy pilot. Distribution work is part of the
product, not a release afterthought.

## Adoption Path

1. A developer discovers Repo Scout through the hosted site, GitHub search, a
   release, or a referral.
2. The developer downloads the versioned `.pyz` and gets a local snapshot
   without cloning the repository or modifying a Python environment.
3. A team installs the provenance-attested wheel when it needs all four
   commands or adopts the verified GitHub Actions policy gate.
4. Cross-repository rollout evidence exposes the need for shared policy
   operations and leads to the $299 founding-team pilot.

The portable artifact is the lowest-friction adoption path. The wheel is the
complete command distribution. The CI example is the team activation path.
None requires an API key or sends source code to Repo Scout.

## Release Contract

Every tagged release must publish and attest exactly these artifacts:

- `repo-scout-X.Y.Z.pyz`
- `repo_scout-X.Y.Z-py3-none-any.whl`
- `repo_scout-X.Y.Z.tar.gz`
- `SHA256SUMS`

The release workflow runs the primary CLI from the zipapp, installs the wheel
in a clean environment, exercises all packaged commands, and covers every
artifact with the checksum manifest and GitHub build provenance.

## Channel Metrics

Review these signals before weekly roadmap work:

- Unique GitHub repository views and clones.
- Release downloads by artifact, especially portable versus wheel adoption.
- Pilot requests attributed to the website, GitHub release, outreach, or a
  referral.
- Purchase readiness and booked revenue by discovery source.

Downloads and clones are adoption signals, not revenue. Only `pilot-paid` and
later paid stages count toward the initial $897 goal.

## Channel Constraints

As of 2026-07-10, PyPI's normalized `repo-scout` name belongs to an unrelated
package. Do not upload this project under a confusing name or weaken artifact
verification to gain another channel. A future PyPI launch needs a distinct
distribution name, verified ownership, trusted publishing, and matching install
documentation while preserving the `repo-scout` command name.
