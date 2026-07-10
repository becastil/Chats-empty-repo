# Verified Releases

Repo Scout publishes versioned wheel and source artifacts on GitHub Releases.
Each release includes:

- `repo_scout-X.Y.Z-py3-none-any.whl`
- `repo_scout-X.Y.Z.tar.gz`
- `SHA256SUMS`
- GitHub build-provenance attestations for both package artifacts

The checksum file detects accidental or malicious byte changes after download.
The provenance attestation separately verifies that GitHub Actions built the
artifact from this repository's tagged source.

## Install A Release

Download a specific version rather than relying on a moving latest-release URL:

```bash
gh release download v0.2.7 \
  --repo becastil/Chats-empty-repo \
  --pattern "repo_scout-*" \
  --pattern SHA256SUMS
python3 -m pip install ./repo_scout-0.2.7-py3-none-any.whl
```

Repo Scout requires Python 3.11 or newer and has no runtime dependencies.

## Verify A Release

Run the checksum command from the directory containing all three downloaded
files:

```bash
shasum -a 256 -c SHA256SUMS
gh attestation verify repo_scout-0.2.7-py3-none-any.whl \
  --repo becastil/Chats-empty-repo
gh attestation verify repo_scout-0.2.7.tar.gz \
  --repo becastil/Chats-empty-repo
```

Both checksum lines must report `OK`, and both attestation commands must verify
against `becastil/Chats-empty-repo`. A checksum alone is not proof of origin
because an attacker who replaces an artifact could also replace an unattested
checksum file.

## Maintainer Release Contract

The release workflow runs only for `vMAJOR.MINOR.PATCH` tags. It rejects a tag
unless it exactly matches both `project.version` in `pyproject.toml` and
`repo_scout.__version__`, and the tagged commit must be on `main`.

Before publication, the workflow:

1. Runs the complete Python test suite.
2. Installs hash-locked release-only build dependencies.
3. Builds one wheel and one source distribution without build isolation.
4. Rejects missing, extra, or incorrectly named artifacts.
5. Installs the wheel in a fresh virtual environment and exercises all three commands.
6. Generates deterministic SHA-256 checksums and GitHub provenance attestations.
7. Creates the GitHub Release from the existing immutable tag.

All actions use full commit pins. Release permissions are limited to creating
the release, requesting the short-lived identity token, and writing artifact
attestations. PyPI publication is intentionally deferred until customer demand
justifies operating another distribution channel.
