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
version = 2

[repository]
required_files = ["README.md", "SECURITY.md"]
forbidden_files = [".env", ".env.local"]
max_files = 10000
max_total_bytes = 100000000
require_clean_git = true
```

The installed `repo-scout-policy init` command can generate a baseline,
Python, npm, or agent-ready profile before the workflow is copied. Review and
commit the generated file first; see [Starter Policy Profiles](policy-starters.md).

Start with rules the team already follows. Add stricter limits after the first
successful run so rollout work is separated from existing repository debt.
The starter rejects tracked or unignored `.env` and `.env.local` files while
leaving properly ignored local environment files alone.

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
persisted checkout credentials, and pins every external action by commit. It downloads the exact
Repo Scout `v0.3.18` wheel and `SHA256SUMS` from the public GitHub Release using
the runner-provided token. No team-managed secret or API key is required.

Before installation, the gate verifies:

- The wheel matches the independently pinned SHA-256 digest in the workflow.
- The wheel matches the release's `SHA256SUMS` manifest.
- GitHub's signed provenance names the pinned source commit and `v0.3.18` tag.
- The signer is this repository's `.github/workflows/release.yml` workflow.
- The attested build used a GitHub-hosted runner.

Repo Scout is installed without dependencies into a virtual environment under
`RUNNER_TEMP`. The target checkout is never used as an install location, and
the rollout bundle is also written outside it, so enforcement does not dirty
the repository being checked. Any download, digest, manifest, provenance, or
install failure stops the job before the policy scan.

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

## Pilot Rollout

The $299 founding-team pilot includes policy design, rollout help, and one
custom policy pack for up to 10 repositories over 90 days. Use the
[public pilot request form](https://github.com/becastil/Chats-empty-repo/issues/new?template=founding-team-pilot.yml&discovery_source=GitHub+repository+or+release)
without including source code, credentials, customer data, or other sensitive
details.
