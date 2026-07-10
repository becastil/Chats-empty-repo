# GitHub Actions Policy Gate

Repo Scout can enforce one committed repository policy on every pull request
without uploading source code or requiring an API key. A completed scan writes
a Markdown report before returning exit code 6 for policy violations, so a
failed check still leaves useful evidence in the job summary and artifact.

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
version = 1

[repository]
required_files = ["README.md", "SECURITY.md"]
max_files = 10000
max_total_bytes = 100000000
require_clean_git = true
```

The installed `repo-scout-policy init` command can generate a baseline,
Python, npm, or agent-ready profile before the workflow is copied. Review and
commit the generated file first; see [Starter Policy Profiles](policy-starters.md).

Start with rules the team already follows. Add stricter limits after the first
successful run so rollout work is separated from existing repository debt.

## Read A Failure

The `Repo Scout policy` check returns exit code 6 when a policy rule fails. Its
Markdown report appears in the job summary and in the
`repo-scout-policy-report` artifact for 14 days. Configuration errors return
exit code 2; scan-limit failures return exit code 3.

The workflow grants only `contents: read`, disables persisted checkout
credentials, and pins every external action and the Repo Scout source checkout
to an immutable commit. Repo Scout runs directly from that isolated checkout,
so policy enforcement does not install packages or mutate the repository being
checked. Update pins deliberately after reviewing upstream release notes.

## Pilot Rollout

The $299 founding-team pilot includes policy design, rollout help, and one
custom policy pack for up to 10 repositories over 90 days. Use the
[public pilot request form](https://github.com/becastil/Chats-empty-repo/issues/new?template=founding-team-pilot.yml)
without including source code, credentials, customer data, or other sensitive
details.
