# First-Repository Pilot Rollout

Repo Scout can turn a policy scan into a durable first-repository onboarding
artifact. The bundle combines the complete Markdown scan and policy evidence
with an automated readiness checklist and explicit team handoff actions.

## Generate The Bundle

Commit the reviewed policy before scanning when it requires a clean Git
worktree, then run:

```bash
repo-scout --format markdown \
  --policy repo-scout-policy.toml \
  --rollout-checklist \
  --repository-id platform/api \
  --output repo-scout-rollout.md \
  .
```

Use `--force` only when intentionally refreshing an existing bundle. Without
`--output`, the report is printed to standard output.

The copy-ready GitHub Actions gate runs the same command with
`${{ github.repository }}` as the logical ID and uploads
`repo-scout-rollout-evidence` for 14 days after every completed policy scan.
This makes passing and remediation bundles downloadable for local aggregation
without adding a hosted Repo Scout service.

`--rollout-checklist` requires both `--policy` and `--format markdown`. It
cannot be used for snapshot comparisons because a before/after report does not
establish a current rollout baseline.

Use the same required `--repository-id` across local and CI runs, preferably
the `owner/repository` name. Directory basenames are not accepted as implicit
identity because unrelated repositories can share a directory name. IDs cannot
be empty, exceed 128 characters, contain control characters, or have
surrounding whitespace.

## Read The Evidence

The automated section records only facts available at scan time:

- Whether the policy loaded and how many configured rules were evaluated.
- The SHA-256 identity of the normalized policy version and repository rules.
- Whether every policy rule passed.
- Whether the target is a Git repository, which branch was scanned, and the
  exact checked-out commit when one exists.
- Whether the worktree was clean when scanned.
- Whether the separate attention scan found additional review items.

`ready-for-ci` requires a passing policy in a clean Git repository with an
identifiable initial commit. Any policy violation, missing or unborn Git
repository, or changed worktree produces `remediation-required`.

The team handoff section always starts unchecked. A local scan cannot prove
that a pull request was reviewed, an owner was assigned, a required check was
enabled, or a week of CI evidence exists. Those boxes are completed by the
pilot team as rollout work happens.

Each bundle ends with a visible `Rollout Metadata` JSON block. Schema version 2
contains the logical repository ID, readiness, policy counts and fingerprint,
Git state and commit, and attention count. The fingerprint hashes normalized
policy semantics, so TOML key order, source paths, required-file ordering,
required-group ordering, member ordering within a required group,
forbidden-file or forbidden-pattern ordering, and an explicit no-op
`require_clean_git = false` do not change it. It excludes
absolute repository and policy paths even though those remain visible
elsewhere in the human evidence report. Schema-1 bundles
remain accepted but have no policy-fingerprint or Git-commit coverage.

## Summarize Pilot Repositories

Combine two or more evidence bundles without a database or hosted service:

```bash
repo-scout-rollout api-rollout.md web-rollout.md worker-rollout.md
repo-scout-rollout --details api-rollout.md web-rollout.md
repo-scout-rollout --format json api-rollout.md web-rollout.md > rollout-summary.json
```

The default summary reports counts and identity coverage only; it omits
repository IDs, branches, commits, policy fingerprints, and evidence paths.
`--details` explicitly includes those fields when an operator needs
repository-level action. Shared policy is verified only when two or more input
bundles all carry the same valid fingerprint. Mixed schema-1/schema-2 input,
missing identities, or differing fingerprints keep that claim false. Detailed
repository rows are sorted by logical ID, so input order does not change the
result. Duplicate IDs, duplicate JSON keys, missing metadata, unknown fields,
unsupported schemas, invalid types, and internally contradictory evidence
fail with exit code 2 instead of being counted.
Duplicate-key failures JSON-escape the decoded key before it enters the
operator error. Legal JSON escapes for newlines, C1 terminal controls, or
bidirectional controls therefore remain visible as escaped text on one line
and cannot forge rollout metrics.
Unknown top-level, policy, and Git fields preserve ordinary printable key names
in validation errors. A control-bearing decoded key is JSON-escaped before it
enters operator output, so rejection remains one line.
Evidence filenames and direct source labels use the same display boundary in
parser, validation, inspection, and loading errors. Ordinary printable paths
remain unchanged; control-bearing paths are JSON-escaped on one line.
Successful `--format json --details` output preserves the exact path as a
structurally escaped JSON value.

Repository IDs must be non-empty printable strings of at most 128 characters
without surrounding whitespace. Newlines, terminal controls, bidirectional
controls, Unicode separators, and oversized values fail before either the
primary CLI generates a bundle or the aggregator emits text or JSON. The error
does not echo the untrusted value.
Printable repository IDs may contain backticks. The Markdown bundle uses a
code-span delimiter longer than the longest embedded run, adding delimiter
padding only when an ID starts or ends with a backtick. The visible identity
therefore remains one inline code value while the metadata preserves the exact
ID.

Branch metadata must be null or a non-empty printable string of at most 1,024
characters without surrounding whitespace. Newlines, terminal controls,
bidirectional controls, and oversized values fail with exit code 2 before any
text or JSON summary is emitted. The error does not echo the untrusted value.

Each evidence argument must name a direct regular-file leaf no larger than
1 MiB (1,048,576 bytes). Symlinks, directories, FIFOs, and other special files
fail with exit code 2 before a summary is emitted. The command reads and parses
one descriptor-bound UTF-8 buffer, then rereads the same descriptor and
rechecks the requested leaf before accepting the metadata. Replacement,
same-file mutation, or growth detected at that checkpoint also fails closed.

Fingerprint equality proves only that the normalized rules recorded in the
bundles match. It is not a digital signature or freshness check. A person who
can modify an evidence file can replace its prose, metadata, fingerprint, and
commit; a recorded commit does not prove when the scan ran. Retain bundles in
access-controlled artifacts or an approved internal system when decisions
depend on their provenance.

## Failure Evidence

A policy failure still writes the complete bundle before returning exit code
6. This lets the team assign concrete remediation from the failed baseline.
Invalid policy or flag configuration returns exit code 2, scan limits return
exit code 3, and protected output conflicts return exit code 4.

The report can contain local paths, repository filenames, and policy violation
details. Keep evidence for private repositories in access-controlled CI
artifacts or approved internal systems; do not paste it into the public pilot
request.

## Rollout Sequence

1. Initialize or review the closest starter policy.
2. Commit the policy and generate the first evidence bundle.
3. Resolve policy violations and review additional attention findings.
4. Add the verified GitHub Actions gate in a reviewed pull request.
5. Require the check only after the baseline passes.
6. Assign an owner and retain one week of CI evidence.
7. Reuse the approved policy pack in the next pilot repository.

## Paid Pilot Delivery Contract

Use this contract only after payment is received. The public pilot issue remains
the funnel record; keep delivery details in a customer-approved private system.
Start from the
[blank delivery record template](../examples/pilot-delivery-record.md), but
complete and retain the copy only in that private system.
When a short-lived local copy is necessary on a POSIX operator machine, create
an owner-only ignored workspace and verify the boundary before adding data:

```bash
install -d -m 700 pilot-private
install -m 600 examples/pilot-delivery-record.md \
  pilot-private/delivery-record.md
git check-ignore --quiet pilot-private/delivery-record.md
```

An ignored path is not encryption or access control. Keep the `700` directory
and `600` record modes, never force-add the completed copy, and move durable
evidence to the customer-approved private system.
Before work starts, record the 90-day start and end dates, customer owner,
Repo Scout operator, CI provider, customer-controlled access method, agreed
standards and exception owner, private communication and evidence location, and
no more than 10 stable repository IDs with the first repository identified. Do
not put private repository names, source code, credentials, customer data,
payment details, or rollout bundles in the public issue.

The $299 pilot is accepted through these concrete deliverables:

1. One reviewed, version-controlled custom policy pack with its bootstrap
   receipt retained beside the policy.
2. One independently pinned CI integration accepted for the agreed provider.
   GitHub Actions is the only copy-ready gate currently shipped. For GitLab CI,
   CircleCI, Buildkite, or another provider, record before payment whether the
   pilot uses a customer-authored command integration or includes separately
   agreed custom integration work; do not imply shipped provider support.
3. One current rollout bundle for every repository in the agreed scope,
   recording either passing evidence or explicit remediation.
4. One counts-only rollout summary, with repository details kept private unless
   the customer explicitly approves sharing them.
5. One closeout record listing current readiness, approved exceptions, retained
   weekly CI evidence, open remediation, and the annual-license decision.

Generate acceptance evidence through the shipped commands:

```bash
repo-scout-policy verify-receipt bootstrap-receipt.json
repo-scout --format markdown \
  --policy repo-scout-policy.toml \
  --rollout-checklist \
  --repository-id owner/repository \
  --output repo-scout-rollout.md \
  .
repo-scout-rollout repo-scout-rollout.md second-repository-rollout.md
```

Apply `pilot-paid` only after payment is received. Apply `pilot-active` only
after the first scoped repository has a reviewed policy committed, one
completed CI policy run, a retained passing or remediation-required rollout
bundle, a remediation owner and next repository recorded, and customer
acknowledgement of the handoff. Apply
`pilot-converted` only after the team actually accepts an annual license.
Artifacts and command output never apply labels automatically, and a passing
bundle alone is not payment, activation across multiple repositories, weekly
usage, or annual conversion.

The $299 founding-team pilot adds policy design, exception handling, and
rollout support across up to 10 repositories. The bundle is evidence for that
work; it is not proof of payment, customer contact, or policy adoption by
another repository.
