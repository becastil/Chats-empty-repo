# Repo Scout Paid Pilot Delivery Record

> Blank operator template. Store the completed copy in a customer-approved
> private system. Do not commit customer information, repository evidence,
> access details, payment details, or the completed record to this repository
> or a public pilot issue.
> If a short-lived local copy is necessary, use the ignored `pilot-private/`
> workspace with an owner-only directory and file.

## Commercial Scope

- Payment received: [ ]
- `pilot-paid` applied after payment: [ ]
- Payment confirmed at (UTC): `YYYY-MM-DDTHH:MM:SSZ`
- Payment confirmed by: `[PRIVATE]`
- Private payment evidence reference: `[PRIVATE]`
- Price: $299 one time
- Pilot start date (UTC): `YYYY-MM-DD`
- Pilot end date (UTC): `YYYY-MM-DD`
- Maximum repository scope: 10
- Customer: `[PRIVATE]`
- Public funnel issue number: `[PUBLIC ISSUE NUMBER]`
- Customer owner: `[PRIVATE]`
- Repo Scout delivery owner: `[PRIVATE]`
- CI provider: `[PRIVATE]`
- Customer-controlled access method: `[PRIVATE]`
- Private communication and evidence location: `[PRIVATE]`
- Agreed policy objective: `[PRIVATE]`
- Exception owner: `[PRIVATE]`
- First repository: `[PRIVATE REPOSITORY ID]`

### CI Integration Decision

Record the option agreed before payment:

- [ ] Shipped, independently pinned GitHub Actions gate
- [ ] Customer-authored command integration for another provider
- [ ] Separately agreed custom integration work
- Custom integration agreement reference, if applicable: `[PRIVATE]`

GitHub Actions is the only copy-ready gate currently shipped. Do not imply
shipped GitLab CI, CircleCI, Buildkite, or other provider support.

### In-Scope Repositories

Use stable private IDs. Leave unused slots blank.
Scope changes require dated written approval; never add an eleventh slot.

- Repository 01: `[PRIVATE REPOSITORY ID]` | Status: `In scope / Unused`
- Repository 02: `[PRIVATE REPOSITORY ID]` | Status: `In scope / Unused`
- Repository 03: `[PRIVATE REPOSITORY ID]` | Status: `In scope / Unused`
- Repository 04: `[PRIVATE REPOSITORY ID]` | Status: `In scope / Unused`
- Repository 05: `[PRIVATE REPOSITORY ID]` | Status: `In scope / Unused`
- Repository 06: `[PRIVATE REPOSITORY ID]` | Status: `In scope / Unused`
- Repository 07: `[PRIVATE REPOSITORY ID]` | Status: `In scope / Unused`
- Repository 08: `[PRIVATE REPOSITORY ID]` | Status: `In scope / Unused`
- Repository 09: `[PRIVATE REPOSITORY ID]` | Status: `In scope / Unused`
- Repository 10: `[PRIVATE REPOSITORY ID]` | Status: `In scope / Unused`

## Deliverable Acceptance

### 1. Custom Policy Pack

- [ ] Reviewed policy committed in the customer-controlled repository
- [ ] Bootstrap receipt retained beside the policy
- [ ] `repo-scout-policy verify-receipt bootstrap-receipt.json` passes
- Private evidence reference: `[PRIVATE]`

### 2. CI Integration

- [ ] Agreed integration implemented
- Repo Scout version: `[VERSION]`
- Exact source and artifact pin reference: `[PRIVATE]`
- [ ] Repo Scout release identity verified
- [ ] First completed CI policy run retained
- First CI run result: `Passing / Remediation required`
- Private evidence reference: `[PRIVATE]`

### 3. Repository Rollout Bundles

- [ ] Current bundle retained for every in-scope repository
- [ ] Each bundle records passing or remediation-required status
- [ ] Each bundle records the exact scanned commit
- Private evidence location: `[PRIVATE]`

### 4. Counts-Only Rollout Summary

- [ ] `repo-scout-rollout` summary generated
- [ ] Repository details remain private
- [ ] Shared-policy fingerprint coverage reviewed
- Private evidence reference: `[PRIVATE]`

### 5. Closeout Record

- [ ] Current repository readiness recorded
- [ ] Approved exceptions recorded
- [ ] Weekly CI evidence retained
- [ ] Open remediation assigned
- [ ] Annual-license decision recorded

## Shipped-Command Evidence

| Command | Version | Run at (UTC) | Exit | Private evidence reference | Reviewed by |
| --- | --- | --- | ---: | --- | --- |
| `repo-scout-policy verify-receipt` | `[VERSION]` | `YYYY-MM-DDTHH:MM:SSZ` | `[EXIT]` | `[PRIVATE]` | `[PRIVATE]` |
| `repo-scout --rollout-checklist` | `[VERSION]` | `YYYY-MM-DDTHH:MM:SSZ` | `[EXIT]` | `[PRIVATE]` | `[PRIVATE]` |
| `repo-scout-rollout` | `[VERSION]` | `YYYY-MM-DDTHH:MM:SSZ` | `[EXIT]` | `[PRIVATE]` | `[PRIVATE]` |

## First-Repository Handoff

- [ ] Reviewed policy committed
- [ ] CI policy run completed
- [ ] Passing or remediation-required rollout bundle retained
- Remediation owner: `[PRIVATE]`
- Next repository: `[PRIVATE REPOSITORY ID]`
- Customer acknowledgement date (UTC): `YYYY-MM-DD`
- [ ] Customer acknowledged the handoff
- [ ] `pilot-active` applied only after acknowledgement

## Revenue Stage Ledger

| Stage | Confirmed at (UTC) | Confirmed by | Private evidence reference | Label applied at (UTC) |
| --- | --- | --- | --- | --- |
| `pilot-paid` | `YYYY-MM-DDTHH:MM:SSZ` | `[PRIVATE]` | `[PRIVATE]` | `YYYY-MM-DDTHH:MM:SSZ` |
| `pilot-active` | `YYYY-MM-DDTHH:MM:SSZ` | `[PRIVATE]` | `[PRIVATE]` | `YYYY-MM-DDTHH:MM:SSZ` |
| `pilot-converted` | `YYYY-MM-DDTHH:MM:SSZ` | `[PRIVATE]` | `[PRIVATE]` | `YYYY-MM-DDTHH:MM:SSZ` |

## 90-Day Closeout

- Final readiness summary: `[PRIVATE]`
- Approved exceptions: `[PRIVATE]`
- Open remediation and owners: `[PRIVATE]`
- Weekly CI evidence summary: `[PRIVATE]`
- Annual-license decision: `[PRIVATE]`
- Customer closeout acknowledgement (UTC): `YYYY-MM-DDTHH:MM:SSZ`
- Annual license accepted: [ ]
- `pilot-converted` applied after acceptance: [ ]
- [ ] `pilot-converted` and `pilot-lost` are not both applied

## Evidence Boundary

The operator applies `pilot-paid`, `pilot-active`, and `pilot-converted` only
after the corresponding human-observed business event. A receipt, passing
bundle, CI run, or completed template is not by itself payment, multi-repository
activation, weekly usage, annual conversion, or revenue.
