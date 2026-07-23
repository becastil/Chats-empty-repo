# Verified Releases

Repo Scout publishes versioned portable, wheel, and source artifacts on GitHub Releases.
Each release includes:

- `repo-scout-X.Y.Z.pyz`, the portable primary CLI
- `repo_scout-X.Y.Z-py3-none-any.whl`
- `repo_scout-X.Y.Z.tar.gz`
- `SHA256SUMS`
- GitHub build-provenance attestations for all three executable or package artifacts

The checksum file detects accidental or malicious byte changes after download.
The provenance attestation separately verifies that GitHub Actions built the
artifact from this repository's tagged source.

Repository-level release immutability locks a published release's tag and
assets against modification or deletion. The release workflow queries the
exact tag after publication and fails unless GitHub reports `immutable: true`.
The `v0.3.51` publication is the first release boundary protected by this
setting. Paid CI now pins its independently verified source commit and wheel
digest after separately reconciling the manifest, annotated tag, main ancestry,
release workflow, immutable state, and all three provenance attestations.

## Install A Release

The shortest path downloads one executable Python file and does not modify the
Python environment:

```bash
curl -fL https://github.com/becastil/Chats-empty-repo/releases/download/v0.3.51/repo-scout-0.3.51.pyz -o /tmp/repo-scout.pyz
python3 /tmp/repo-scout.pyz --languages .
```

The zipapp exposes the primary `repo-scout` command. Download and install the
wheel when the distribution, policy-template, rollout-summary, pilot-funnel, or
maintainer outreach-audit commands are also needed:

```bash
gh release download v0.3.51 \
  --repo becastil/Chats-empty-repo \
  --pattern "repo_scout-*" \
  --pattern "repo-scout-*.pyz" \
  --pattern SHA256SUMS
python3 -m pip install ./repo_scout-0.3.51-py3-none-any.whl
```

Repo Scout requires Python 3.11 or newer and has no runtime dependencies.

## Verify A Release

Run the checksum command from the directory containing all 4 downloaded
files:

```bash
(
  set -euo pipefail

  REPO_SCOUT_REPOSITORY="becastil/Chats-empty-repo"
  REPO_SCOUT_VERSION="0.3.51"
  REPO_SCOUT_TAG="v${REPO_SCOUT_VERSION}"
  REPO_SCOUT_SIGNER_WORKFLOW="${REPO_SCOUT_REPOSITORY}/.github/workflows/release.yml"

  [[ "$REPO_SCOUT_VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]
  REPO_SCOUT_TAG_LINE="$(
    git ls-remote --exit-code --tags \
      "https://github.com/${REPO_SCOUT_REPOSITORY}.git" \
      "refs/tags/${REPO_SCOUT_TAG}^{}"
  )"
  read -r REPO_SCOUT_SOURCE_SHA REPO_SCOUT_RESOLVED_REF \
    <<<"$REPO_SCOUT_TAG_LINE"
  [[ "$REPO_SCOUT_RESOLVED_REF" == "refs/tags/${REPO_SCOUT_TAG}^{}" ]]
  [[ "$REPO_SCOUT_SOURCE_SHA" =~ ^[0-9a-f]{40}$ ]]

  if command -v sha256sum >/dev/null 2>&1; then
    sha256sum --check SHA256SUMS
  else
    shasum -a 256 -c SHA256SUMS
  fi
  gh attestation verify "repo-scout-${REPO_SCOUT_VERSION}.pyz" \
    --repo "$REPO_SCOUT_REPOSITORY" \
    --signer-workflow "$REPO_SCOUT_SIGNER_WORKFLOW" \
    --source-ref "refs/tags/${REPO_SCOUT_TAG}" \
    --source-digest "$REPO_SCOUT_SOURCE_SHA" \
    --deny-self-hosted-runners
  gh attestation verify "repo_scout-${REPO_SCOUT_VERSION}-py3-none-any.whl" \
    --repo "$REPO_SCOUT_REPOSITORY" \
    --signer-workflow "$REPO_SCOUT_SIGNER_WORKFLOW" \
    --source-ref "refs/tags/${REPO_SCOUT_TAG}" \
    --source-digest "$REPO_SCOUT_SOURCE_SHA" \
    --deny-self-hosted-runners
  gh attestation verify "repo_scout-${REPO_SCOUT_VERSION}.tar.gz" \
    --repo "$REPO_SCOUT_REPOSITORY" \
    --signer-workflow "$REPO_SCOUT_SIGNER_WORKFLOW" \
    --source-ref "refs/tags/${REPO_SCOUT_TAG}" \
    --source-digest "$REPO_SCOUT_SOURCE_SHA" \
    --deny-self-hosted-runners
)
```

All 3 checksum lines must report `OK`, and all 3 attestation commands must verify
against `becastil/Chats-empty-repo`, the exact semantic tag and peeled source
commit, the release workflow, and a GitHub-hosted runner. The subshell stops if
the annotated tag does not resolve to a 40-character commit. A checksum alone
is not proof of origin because an attacker who replaces an artifact could also
replace an unattested checksum file.

The lookup verifies the annotated tag target currently published by GitHub.
The paid CI examples go further by pinning the separately reviewed source
commit and wheel digest directly, so a later tag move cannot change their
trusted artifact identity.

## Prepare And Approve A Site Deployment

A release identity change is not complete on the public site until the exact
committed source is built, saved, approved, deployed, and audited. For every
site release:

1. Install the lockfile dependencies and validate the production build and
   source before packaging it:

   ```bash
   npm ci
   npm run audit:dependencies
   npm test
   npm run lint
   ```

   The dependency audit must report zero vulnerabilities. Do not use
   `npm audit fix --force` when it proposes a framework downgrade; review and
   test a supported patch or explicit transitive override instead.
2. Build and package that exact committed source, push the same commit to the
   existing Sites source repository, and reuse the existing Sites project in
   `.openai/hosting.json`. Do not create a replacement project for a version
   update.
3. Save the packaged version against that same source commit. Saving a version
   does not make that version live.
4. Obtain explicit owner approval before deploying the saved version to the
   existing public production site.
5. Only after the approved deployment succeeds, immediately run the production
   audit in the next section. A prepared or saved version must not be described
   as deployed before both steps finish.

## Audit The Production Download

After publishing the site, maintainers can verify that its canonical metadata,
free software offer, release version, portable download URL, $299 founding-team
service, and website-attributed pilot application link match the current
commercial contract:

```bash
python3 scripts/audit_production_site.py
```

The audit reads the public HTML without changing production. A stale version,
stale download URL, malformed free or paid offer, missing pilot application
link, unexpected content type, or network failure exits nonzero instead of
accepting a partial check.

The read-only `Production site audit` workflow runs the same command once per
day and can be dispatched manually after a deployment. It uses no repository
secrets and does not change the site, a release, or any commercial evidence.

## Maintainer Release Contract

Before a maintainer creates a tag, the read-only `Release tooling contract`
workflow runs when release inputs change or when manually dispatched. It tests
the release contracts on Python 3.11, force-installs every hash-locked build
tool into a fresh runner-temp virtual environment, runs `pip check`, and builds
candidate zipapp, wheel, source, and checksum artifacts in runner temp. It
cannot use secrets, upload or attest artifacts, write repository content, or
publish a release.

The release workflow runs only for `vMAJOR.MINOR.PATCH` tags. Before tests or
builds, it rejects a lightweight tag, an annotated tag whose peeled commit does
not exactly match the GitHub push commit, or a tagged commit outside `main`.
The tag must also exactly match both `project.version` in `pyproject.toml` and
`repo_scout.__version__`.

Before publication, the workflow:

1. Runs the complete Python test suite.
2. Creates a fresh runner-temp build environment, force-installs every
   hash-locked release-only dependency, and requires `pip check` to pass.
3. Uses only that isolated interpreter to build one portable zipapp, one wheel,
   one source distribution, and the checksum manifest.
4. Rejects missing, extra, or incorrectly named artifacts.
5. Runs the zipapp directly, then installs the wheel in a fresh virtual
   environment, reconciles all command versions to the tag, exercises all
   seven commands, verifies every starter-
   recommendation route plus Node policy enforcement, and checks the guarded
   outreach review-to-observed-outcome lifecycle and its privacy boundaries.
6. Generates deterministic SHA-256 checksums and GitHub provenance attestations.
7. Creates the GitHub Release, queries the exact published tag through GitHub's
   versioned REST API, and fails unless the release reports `immutable: true`.

All actions use full commit pins. Release permissions are limited to creating
the release, requesting the short-lived identity token, and writing artifact
attestations. The normalized `repo-scout` name on PyPI belongs to an unrelated
project, so PyPI publication requires a distinct distribution name and trusted
publisher setup before it can become a supported channel.
