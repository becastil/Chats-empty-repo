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
curl -fL https://github.com/becastil/Chats-empty-repo/releases/download/v0.3.51/repo-scout-0.3.51.pyz -o /tmp/repo-scout.pyz &&
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

1. From a clean `main` checkout whose `HEAD` matches `origin/main`, use the
   hosted Node `22.13.0` runtime to validate and package the exact source:

   ```bash
   nvm install
   nvm use
   python3 scripts/prepare_site_candidate.py \
     --package-script "$SITES_PACKAGE_SCRIPT" \
     --archive /tmp/repo-scout-site.tar.gz \
     --receipt /tmp/repo-scout-site-receipt.json
   ```

   Run `nvm use` before every candidate build. The version manager reads the
   exact runtime from `.nvmrc`; the same file configures the hosted dependency
   contract and the candidate receipt.
   `SITES_PACKAGE_SCRIPT` must name the trusted Sites `package-site.sh` helper.
   The preflight runs `npm ci`, `npm run audit:dependencies`,
   `npm run lint`, and `npm run build`, binds the candidate payload, then runs
   `npm run test:site` against the exact existing `dist/` without rebuilding.
   The complete dependency audit must report zero vulnerabilities. The command
   refuses a detached or non-`main` branch, dirty or unsynchronized source,
   malformed or mismatched package/site release versions, runtime-pin or
   active-runtime drift, and an archive whose embedded commit, public release
   version, lock digest, Sites project, or Node version differs from the tested
   source. `project.version` in `pyproject.toml` and the website's single
   `RELEASE_VERSION` declaration must be the same semantic version before any
   Git, Node, or npm command runs.
   Archive members outside `dist/`, path aliases, links, devices, pipes, and
   other special files are rejected; only canonical regular files and
   directories can cross the candidate boundary. Rejected printable member
   names remain exact in the error; presentation-unsafe names are serialized as
   one JSON string so they cannot forge a candidate result or source-export
   request. After the build and before the test-only command, the preflight
   adds the candidate manifest and digests
   every regular directory and file's canonical path, entry type, and
   permission mode plus each file's size and bytes. It recomputes that digest
   after the tests and rejects any candidate payload changed during site tests.
   Every tested payload directory must use mode `0755`; packaging runs under an
   explicit `umask 022` so helper-created staging directories reproduce that
   mode. The packaged payload must also match, so a noncanonical source mode,
   unexpected empty directory, or changed archive permission fails closed. This
   test-brackets built server and client output; hosting metadata, Drizzle
   configuration, and the embedded manifest are integrity-bound and
   structurally checked. The schema-5 receipt records the public release
   version alongside the resulting archive digest and tested payload digest
   for later read-only verification.
   Duplicate JSON keys fail even when repeated values match in checkout hosting
   metadata, candidate receipts, or archived manifests, so approval evidence
   never depends on a decoder selecting the first or last value. The rejected
   duplicate key remains exact when printable; otherwise it is serialized as
   one JSON string in operator errors, so decoded line, terminal,
   Unicode-separator, or bidirectional controls cannot forge a candidate result
   or source-export request.
   Packaging sets `COPYFILE_DISABLE=1` so macOS cannot inject AppleDouble
   metadata outside the allowed archive root. The preflight also repeats the
   active `refs/heads/main` and clean `HEAD == origin/main` checks after
   validation and after packaging, requiring the same synchronized commit at
   every acceptance checkpoint while remaining on the same branch. It hashes
   the packaged archive before structural validation, publishes the archive
   and receipt without replacing existing paths, then repeats synchronized
   source, archive digest, and exact staged receipt digest checks before
   reporting success. Requested archive and receipt leaf paths remain
   unresolved so initial or dangling symlinks are rejected instead of silently
   redirecting evidence; their parent directories are resolved so an existing
   symlink that points into the repository fails the containment check.
   Containment also rejects an output parent whose existing ancestor has the
   filesystem identity of any non-symlink repository directory, including
   stable alternate case or Unicode spellings and whole-repository or
   subdirectory-only aliases even when lexical paths differ. Repeated
   identities stop directory cycles, and reported traversal or ambiguous
   identity lookup failures stop preparation. Both output parent directories
   must already exist, and candidate preparation requires POSIX
   descriptor-relative staging and hard-link support. Before any Git or Node
   command, it opens each unique direct parent without following a symlink,
   verifies its filesystem identity and both requested leaves through that
   descriptor, and keeps the descriptor open and non-inheritable through
   validation and publication. Archive and receipt outputs in one parent reuse
   the same descriptor.
   Archive staging is a private `0700` directory created and opened relative
   to the held archive parent. The external helper receives its visible path,
   but preparation accepts only the regular archive opened relative to the held
   staging descriptor. That exact file remains open and non-inheritable through
   hashing, tar validation, the synchronized-source recheck, and publication.
   The publication source leaf is resolved relative to the held staging
   directory only after its identity is rechecked against the held archive; the
   new output must share that identity again after the link. Cleanup removes the
   archive and staging directory only when their current identities match the
   recorded objects. A replacement is preserved and fails cleanup instead of
   being deleted. If the visible archive parent is replaced, helper output
   written under that replacement remains untouched and cannot satisfy
   acceptance.
   Receipt staging is a private `0600` leaf created relative to the held
   receipt parent. Preparation writes, syncs, hashes, and rechecks one
   non-inheritable regular-file descriptor, requiring its digest to equal the
   exact serialized JSON bytes intended for the receipt. Publication resolves
   the source name relative to that held parent and requires it to retain the
   staged file identity before linking. Cleanup removes only the recorded
   identity; a replacement is preserved and reported, and staged or partially
   transferred descriptors close on failure.
   Each final no-clobber link names its leaf relative to its held parent, so
   replacing or renaming the parent path after preflight cannot redirect
   publication into a different directory. Publication opens the staged source
   without following links, opens the new leaf relative to the held parent, and
   requires both descriptors to identify the same regular file. The exact
   archive and receipt descriptors remain open and non-inheritable through the
   final synchronized-source and digest checks.
   Before success, preparation reopens each requested parent, requires it to
   match the held parent, and compares the leaf relative to it with the
   published file descriptor. Link-to-open substitution, byte-identical leaf
   replacement, and a replacement parent that re-links the same file therefore
   fail. Archive and receipt staging, staged reads, publication, and cleanup
   remain bound to the descriptors held from preflight.
   Persistent drift during receipt publication therefore leaves no
   approval-ready result. The stable `site candidate ready:` prefix is followed
   by one compact JSON object. Its archive digest field is `archive_sha256` and
   it includes the receipt-bound `release_version`, Sites `project_id`, and
   `receipt_sha256`; parse and retain that record with the candidate evidence.
   Do not use `npm audit fix --force` when it proposes a framework downgrade;
   review and test a supported patch or explicit transitive override instead.
2. Verify the archive and receipt immediately before asking for source-export
   approval:

   ```bash
   python3 scripts/prepare_site_candidate.py --verify-only \
     --archive /tmp/repo-scout-site.tar.gz \
     --receipt /tmp/repo-scout-site-receipt.json \
     --approval-source-repository "$SITES_SOURCE_REPOSITORY"
   ```

   This pre-approval verification is read-only and runs no Node, npm,
   packaging, network, source export, version save, or deployment operation.
   It requires the checkout to remain on `refs/heads/main`, clean, and
   synchronized with `origin/main`, reconciles its commit, public release
   version, lockfile, and Sites project with the strict receipt, recomputes the
   archive digest, validates the embedded manifest, and then proves the same
   branch and synchronized commit still hold. The supplied archive and receipt
   paths must themselves name regular files rather than symlinks. It requires
   the same regular archive and digest once more at that final acceptance
   checkpoint before reporting success. Record the printed `release_version`,
   `project_id`, and `receipt_sha256` with the source-export approval so later
   verification can require the exact receipt bytes and the approval remains
   tied to the existing Sites project and release identity the owner reviewed.
   `SITES_SOURCE_REPOSITORY` may be the existing Sites source repository's
   credential-free remote URL or a configured alias. The request mode resolves
   that argument locally with Git, rejects the local checkout and the repository
   configured as `origin`, and prints its canonical identity without querying a
   remote ref. Canonical identity normalizes the standard Git, HTTP, HTTPS, and
   SSH ports across protocol aliases but retains any non-default port as part of
   the repository authority. Conventional `git@` remains protocol-neutral, but
   any other SSH URL or SCP username remains part of the canonical identity.
   For those users, home-relative SCP paths remain distinct from absolute SSH
   URL or SCP paths and are printed with the `scp-relative://` identity prefix.
   The second output line starts `source-export request pending`, carries the
   public release version, Sites project ID, receipt digest, canonical source
   repository, `refs/heads/main`, and receipt commit, and states
   `deployment_approved=false`. It is a copy-ready request for a human decision,
   not approval. Confirm that the canonical repository belongs to the printed
   existing Sites project, then retain that identity as
   `APPROVED_SITES_SOURCE_REPOSITORY` exactly as printed only if the owner
   approves the exact request.
   The stable `source-export request pending:` prefix is followed by one compact
   JSON object. Parse that object rather than splitting its contents on spaces;
   `deployment_approved` is the boolean `false`, and opaque values cannot add a
   sibling field or terminal line. Configured aliases and resolved repository
   URLs containing raw whitespace fail closed. Percent-encode any legitimate
   URL path space, for example `%20`, before requesting approval.
3. Obtain explicit owner approval before pushing the exact committed source to
   the approved separate Sites source repository. The approval must identify
   the public release version, Sites project ID, receipt digest, canonical
   repository identity, `refs/heads/main`, and receipt commit from the exact
   pending request. Request output is not consent. This source-export approval
   is separate from deployment approval, and the source export does not
   authorize production deployment.
4. Push the receipt's exact source commit to the separate Sites source
   repository (the existing Sites source repository for this project), and
   reuse the existing Sites project in `.openai/hosting.json`.
   `SITES_SOURCE_REPOSITORY` may be the approved URL or a configured remote
   alias that resolves to it. Pass authentication through the same per-command
   Git credential context rather than embedding a token in either repository
   identity. Do not create a replacement project for a version update.
5. Verify the unchanged archive and receipt again before saving:

   ```bash
   python3 scripts/prepare_site_candidate.py --verify-only \
     --archive /tmp/repo-scout-site.tar.gz \
     --receipt /tmp/repo-scout-site-receipt.json \
     --expected-receipt-sha256 APPROVED_RECEIPT_SHA256 \
     --exported-source-repository "$SITES_SOURCE_REPOSITORY" \
     --expected-exported-source-repository "$APPROVED_SITES_SOURCE_REPOSITORY"
   ```

   The three approval arguments form one atomic pre-save mode: the command
   rejects the approved digest without both repository arguments, rather than
   reporting a digest-only success that omitted exported-source verification.
   This check fails if the receipt was even semantically reserialized after
   approval. It resolves the operational repository argument, requires its
   canonical remote identity to equal the exact canonical repository string
   recorded in approval, and rejects the local checkout, `origin`, equivalent
   aliases, or an unrelated fork even when they contain the same commit. A
   matching host and path on an unapproved non-default port or nonstandard SSH
   username is a different repository and also fails, as does switching an
   approved absolute path to home-relative SCP syntax. The resolved identity
   must remain stable while read-only `git ls-remote` calls resolve
   `refs/heads/main` twice; the check fails if that exported ref differs from
   the approved candidate commit or moves during verification. This pre-save
   form therefore uses the network but performs no source export, version save,
   or deployment. Save the verified preflight archive against the receipt's
   exact source commit. Saving a version does not make that version live.
6. Obtain separate explicit owner approval before deploying the saved version
   to the existing public production site.
7. Only after the approved deployment succeeds, immediately run the production
   audit in the next section. A prepared or saved version must not be described
   as deployed before both steps finish.

## Audit The Production Download

After publishing the site, maintainers can verify that its canonical metadata,
free software offer, release version, structured and visitor-visible portable
download URLs, $299 founding-team service, and website-attributed pilot
application link with the same visible $299 price match the current commercial
contract:

```bash
python3 scripts/audit_production_site.py
```

The audit reads the public HTML without changing production. A stale version,
stale structured download URL, missing or stale visible download link,
malformed free or paid offer, missing pilot application link, unpriced or
mispriced application CTA, unexpected content type, or network failure exits
nonzero instead of accepting a partial check.

The read-only `Production site audit` workflow runs the same command once per
day and can be dispatched manually after a deployment. Before the live request,
it runs the workflow contract and complete auditor behavior suite. It uses no
repository secrets and does not change the site, a release, or any commercial
evidence.

## Maintainer Release Contract

Before a maintainer creates a tag, the read-only `Release tooling contract`
workflow runs when release inputs change or when manually dispatched. It tests
the release contracts on Python 3.11, force-installs every hash-locked build
tool into a fresh runner-temp virtual environment, runs `pip check`, and builds
candidate zipapp, wheel, source, and checksum artifacts in runner temp. It
then rebuilds the exact source archive without package indexes, a wheel cache,
dependency resolution, build isolation, or a second toolchain. Every
rebuilt-wheel member path, byte, and stored mode must match the direct wheel
before the workflow installs that direct wheel into a separate smoke
environment with package indexes, dependency resolution, and pip's remote
version check disabled. It reconciles every packaged command version and
directly executes the same four installed-wheel acceptance journeys used by
publication: policy activation, guarded outreach, pilot-funnel accounting, and
rollout summary. It then executes the zipapp for help and a JSON repository
scan. It cannot use secrets, upload or attest artifacts, write repository
content, or publish a release.

At both build boundaries, release preparation refuses a symlinked or other
non-regular `SHA256SUMS` path. It writes the deterministic manifest through a
flushed and synced same-directory staging file, then atomically replaces the
destination. Revalidation preserves the mode of an existing regular manifest,
and a failed replacement leaves its prior bytes intact.

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
5. Rebuilds the exact source distribution without package indexes, a wheel
   cache, dependency resolution, or build isolation, then requires its wheel to
   match every member path, byte, and stored mode in the direct wheel.
6. Installs the exact canonical wheel in a fresh package-index-free virtual
   environment with dependency resolution and pip's remote version check
   disabled, reconciles all command versions to the tag, exercises all seven
   commands, then directly runs the zipapp and verifies every starter-
   recommendation route plus Node policy enforcement, and checks the guarded
   outreach review-to-observed-outcome lifecycle and its privacy boundaries.
7. Revalidates all three built artifacts against the deterministic SHA-256
   manifest after smoke tests, then submits that same manifest for GitHub
   provenance attestations.
8. Uploads only the exact tag-derived wheel, source, portable, and checksum
   paths to the GitHub Release without shell globs, queries the exact published
   tag through GitHub's versioned REST API, and fails unless the release reports
   `immutable: true`.

All actions use full commit pins. Release permissions are limited to creating
the release, requesting the short-lived identity token, and writing artifact
attestations. The normalized `repo-scout` name on PyPI belongs to an unrelated
project, so PyPI publication requires a distinct distribution name and trusted
publisher setup before it can become a supported channel.
