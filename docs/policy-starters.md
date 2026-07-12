# Starter Policy Profiles

Repo Scout includes five policy profiles that turn the first team-policy setup
into a review-and-commit task instead of a blank-file design exercise. The
profiles are packaged with the CLI and require no network access.

## Choose A Profile

| Profile | Required files | Forbidden files | File limit | Byte limit |
| --- | --- | --- | ---: | ---: |
| `service-baseline` | `README.md` | `.env`, `.env.local` | 25,000 | 250,000,000 |
| `python-service` | `README.md`, `pyproject.toml` | `.env`, `.env.local` | 15,000 | 100,000,000 |
| `node-npm-service` | `README.md`, `package.json`, `package-lock.json` | `.env`, `.env.local` | 20,000 | 150,000,000 |
| `node-service` | `README.md`, `package.json`, one npm/pnpm/Yarn lockfile | `.env`, `.env.local` | 20,000 | 150,000,000 |
| `agent-ready-service` | `README.md`, `AGENTS.md` | `.env`, `.env.local` | 15,000 | 100,000,000 |

Every profile also requires a clean Git worktree. Forbidden files fail when
tracked or unignored; a local file covered by Git ignore rules remains allowed.
Every profile also applies `**/.env` and `**/.env.local` to nested service
folders. Broad filename patterns are intentionally absent from general
profiles because files such as public `.pem` certificates can be legitimate.
Use `node-service` when repositories may use npm, pnpm, or Yarn. It requires
one of `package-lock.json`, `pnpm-lock.yaml`, or `yarn.lock` without requiring
all three. `node-npm-service` remains available when npm itself is the standard.

## Discover And Inspect

List profiles for a person:

```bash
repo-scout-policy list
```

List the same catalog as stable JSON:

```bash
repo-scout-policy list --format json
```

Inspect the exact TOML before writing anything:

```bash
repo-scout-policy show python-service
```

JSON catalog output contains `schema_version: 1` and a `templates` array with
each profile's name, title, description, and normalized rules.

## Initialize And Enforce

Write a profile to `repo-scout-policy.toml` in the current directory:

```bash
repo-scout-policy init python-service
```

The command refuses to overwrite an existing file. `--force` performs an
atomic replacement, and `--output PATH` selects another filename. Missing
parent directories are not created. Use `show` rather than `--output -` for
stdout.

Review the limits and required files, then add standards the repository already
follows, such as `SECURITY.md`, `CONTRIBUTING.md`, or an ownership file. Commit
the generated policy before enforcing it because every starter requires a clean
Git worktree:

```bash
git add repo-scout-policy.toml
git commit -m "Add Repo Scout policy"
repo-scout --policy repo-scout-policy.toml .
```

Use the [GitHub Actions policy gate](github-actions.md) after the local clean
run passes. Command errors return exit code 2; output conflicts and write errors
return exit code 4.

## Custom Pilot Pack

The free profiles cover common repository shapes. The $299 founding-team pilot
adds one custom policy pack, rollout help, and shared enforcement for up to 10
repositories over 90 days. A custom pack should encode standards the team has
already agreed to rather than creating new process by surprise. That includes
the team's own forbidden credential, generated-secret, or local-configuration
paths rather than a generic list imposed without review. Forbidden-file rules
use policy version 2; version 1 policies remain readable for existing teams.
Policy version 3 adds bounded `forbidden_file_patterns` for nested monorepo
paths. General profiles protect nested environment files; filename-wide rules
such as `*.pem` should be added only when the team confirms they cannot block
legitimate public certificates or fixtures.

Policy version 4 adds `required_file_groups` for standards with valid
alternatives. Every group needs at least one existing file. The packaged
`node-service` profile uses this rule for `package-lock.json`,
`pnpm-lock.yaml`, or `yarn.lock`, which lets one shared starting point cover
mixed JavaScript package managers without making a lockfile optional. The
existing profiles remain unchanged, including the npm-only option.
