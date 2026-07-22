# GitHub Actions Policy Gate

Repo Scout can enforce one committed repository policy on every pull request
without uploading source code or requiring an API key. A completed scan writes
a schema-2 rollout bundle before returning exit code 6 for policy violations,
so a failed check still leaves aggregatable evidence in the job summary and
artifact.

## Add The Gate

Copy these two files into the repository being protected:

- `examples/github-actions/repo-scout-policy.yml` to
  `.github/workflows/repo-scout-policy.yml`
- `examples/github-actions/repo-scout-policy.toml` to
  `repo-scout-policy.toml`

Commit both files and open a pull request. The workflow runs on pull requests,
pushes to `main`, and manual dispatches.

## Set The Policy

Edit `repo-scout-policy.toml` to match the repository's actual standards:

```toml
version = 3

[repository]
required_files = ["README.md", "SECURITY.md"]
forbidden_files = [".env", ".env.local"]
forbidden_file_patterns = ["**/.env", "**/.env.local"]
max_files = 10000
max_total_bytes = 100000000
require_clean_git = true
```

The installed `repo-scout-policy init` command can generate a baseline,
Python, npm, or agent-ready profile before the workflow is copied. Review and
commit the generated file first; see [Starter Policy Profiles](policy-starters.md).

Start with rules the team already follows. Add stricter limits after the first
successful run so rollout work is separated from existing repository debt.
The starter rejects tracked or unignored `.env` and `.env.local` files at the
root and under nested service folders while leaving properly ignored local
environment files alone.

The workflow automatically uses GitHub's `owner/repository` value as the stable
rollout repository ID. Review the first generated
[rollout bundle](pilot-rollout.md) before enabling the required check; it
preserves the baseline, remediation list, ownership handoff, policy
fingerprint, scanned commit, and next-repository sequence.

## Read A Failure

The `Repo Scout policy` check returns exit code 6 when a policy rule fails. Its
Markdown bundle appears in the job summary and in the
`repo-scout-rollout-evidence` artifact for 14 days. The artifact is uploaded
after passing and failing policy scans, allowing pilot operators to download
bundles from multiple repositories and run `repo-scout-rollout` locally.
Configuration errors return exit code 2; scan-limit failures return exit code
3 and may not produce evidence because no scan completed.

The workflow grants only `contents: read` and `attestations: read`, disables
persisted checkout credentials, and pins every external action by commit. It
downloads the exact Repo Scout version and wheel digest declared in the
workflow, plus `SHA256SUMS`, from the public GitHub Release using the
runner-provided token. No team-managed secret or API key is required. The
download uses up to four isolated attempts with 5, 10, and 15-second waits so a
brief GitHub REST failure cannot leave partial files in a later attempt.
An attempt succeeds only when the download command returns successfully, both
the wheel and manifest are regular files, and both promote into the trusted
release directory. A successful one-asset response therefore follows the same
bounded retry path instead of aborting at the missing-file move.

Before installation, the gate verifies:

- The wheel matches the independently pinned SHA-256 digest in the workflow.
- The manifest contains exactly one canonical entry binding that digest to the
  pinned wheel filename.
- The wheel matches the release's `SHA256SUMS` manifest.
- GitHub's signed provenance names the pinned source commit and semantic release
  tag.
- The signer is this repository's `.github/workflows/release.yml` workflow.
- The attested build used a GitHub-hosted runner.

The exact-entry check runs before checksum or provenance verification. A
manifest that omits the wheel, changes its digest, or repeats its canonical
entry therefore fails even though `sha256sum --ignore-missing` can return
success when every listed artifact is absent from the download directory.

Provenance verification also uses up to four attempts with the same bounded
backoff. Every attempt retains the exact wheel, repository, source commit, tag,
signer workflow, and hosted-runner requirements.

Repo Scout is installed without dependencies into a virtual environment under
`RUNNER_TEMP`. The local wheel install disables package indexes, dependency
resolution, and pip's remote version check, so no Python registry is consulted
after the verified GitHub release download. The target checkout is never used
as an install location, and the rollout bundle is also written outside it, so
enforcement does not dirty the repository being checked. Any download, digest,
manifest, provenance, or install failure stops the job before the policy scan.
A download or provenance check that still fails after its fourth attempt exits
explicitly instead of using stale, partial, or unverified evidence.

The bundle contains repository filenames, policy findings, a policy
fingerprint, and the checked-out commit. GitHub job summaries and artifacts
follow the repository's access model; teams should not copy private-repository
evidence into public issues or unrelated systems. On pull requests, the commit
identity describes the exact checkout GitHub Actions scanned, which may be a
temporary merge commit.

To upgrade Repo Scout, review the release notes and provenance, then update the
workflow's `REPO_SCOUT_VERSION`, `REPO_SCOUT_SOURCE_SHA`, and
`REPO_SCOUT_WHEEL_SHA256` values together. Open a pull request and require the
gate to pass before merging. Never update only the version tag or replace the
digest with a mutable URL.

Repo Scout maintainers can update the dogfood workflow, copy-ready example,
buyer-facing README, business-model and project-state claims, and contract-test
identity together after independently verifying the release:

```bash
python3 scripts/update_release_pin.py \
  --version X.Y.Z \
  --source-sha VERIFIED_40_CHARACTER_COMMIT \
  --wheel-sha256 INDEPENDENTLY_MEASURED_64_CHARACTER_DIGEST
```

Add `--check` to that command first to validate the same release identity,
six-target layout, and downgrade boundary without staging or replacing files.
After review, rerun the command without `--check` to perform the atomic update.

The updater validates all identity shapes and preflights all six
version-bearing targets before writing. It refuses a numerically older release
before staging, while same-version revalidation and forward upgrades remain
supported. Any workflow, README, business-model, project-state, or test layout
drift stops the command without changing the other files; the normal test suite
remains the final contract check before commit. Successful writes preserve each
target's permission bits. If a later filesystem write fails, the updater rolls
back every target it already replaced from a staged original. A recovery copy
is retained and named in the error only if that rollback also fails.

## Pilot Rollout

The $299 founding-team pilot includes policy design, rollout help, and one
custom policy pack for up to 10 repositories over 90 days. Use the
[public pilot request form](https://github.com/becastil/Chats-empty-repo/issues/new?template=founding-team-pilot.yml&discovery_source=GitHub+repository+or+release)
without including source code, credentials, customer data, or other sensitive
details. After payment, use the
[paid delivery contract](pilot-rollout.md#paid-pilot-delivery-contract) to
define scope, acceptance evidence, privacy boundaries, and funnel-label
transitions.
