# Policy Exceptions

Repo Scout policy exceptions are temporary, repository-local decisions. They
do not alter the shared team policy or its fingerprint, and they do not erase
the raw policy failure. A current exact decision can produce the separate
enforcement status `pass-with-exceptions`; every other unresolved state exits
with code 6 after the report is written.

## Create A Decision

1. Run the policy without an exception ledger and retain the JSON report:

   ```bash
   repo-scout --format json --policy repo-scout-policy.toml . > policy.json
   ```

2. Copy the reported `policy.fingerprint` and the exact `violation_ids` entry
   that a reviewer intends to approve. Violation IDs include the observed
   evidence, not the human-readable message. Numeric drift, a changed forbidden
   match set, or changed Git evidence therefore creates a different ID.

3. Create `repo-scout-exceptions.toml` inside the repository:

   ```toml
   version = 1
   repository_id = "platform/api"
   policy_fingerprint = "sha256:REPLACE_WITH_64_LOWERCASE_HEX_CHARACTERS"

   [[exceptions]]
   id = "EXC-2026-001"
   violation_id = "sha256:REPLACE_WITH_64_LOWERCASE_HEX_CHARACTERS"
   owner = "platform-team"
   approved_by = "engineering-lead"
   reason = "Migration is tracked in ENG-123."
   approved_on = 2026-08-08
   expires_on = 2026-09-08
   ```

4. Review and commit the ledger. The scan refuses to apply an untracked,
   outside-repository, symlinked, dirty, oversized, or concurrently changed
   ledger.

5. Run the bound scan:

   ```bash
   repo-scout --format markdown --policy repo-scout-policy.toml \
     --exception-ledger repo-scout-exceptions.toml \
     --repository-id platform/api .
   ```

## Enforcement States

| State | Meaning | Exit |
| --- | --- | ---: |
| `pass` | The raw policy passes and no decision is needed. | 0 |
| `pass-with-exceptions` | Every raw violation has one current exact decision. | 0 |
| `fail` | A violation is unresolved, or a decision is pending, expired, stale, or unmatched. | 6 |

The raw `policy.status`, `policy.violations`, and `policy.violation_ids` remain
available in every case. Exception evidence appears separately under
`policy.exceptions`, including a normalized ledger fingerprint and the applied,
pending, expired, stale, and unresolved sets.

## Review Boundary

The ledger proves only what the committed file asserts. Repo Scout does not
authenticate `approved_by`, contact an identity provider, or infer approval
from command output. Use branch protection, CODEOWNERS, or an equivalent review
control for the ledger path. Remove a decision after remediation or expiration;
Git history retains the earlier decision for audit.

Rollout schema 3 carries privacy-safe counts and fingerprints only. Keep the
full ledger and JSON policy report in the customer-approved private system when
the rationale or actor fields are sensitive.
