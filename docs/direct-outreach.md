# Direct Outreach Playbook

This playbook turns the founding-team pilot into one bounded acquisition test.
It is for relevant, individual business outreach, not bulk email.

## Qualified Prospect

Contact a prospect only when public evidence supports at least three of these
signals:

- `team_5_50`: a software team with roughly 5 to 50 developers.
- `multi_repo`: multiple actively maintained repositories or services.
- `agent_use`: visible use of coding agents or AI-assisted development.
- An engineering lead who owns CI, repository standards, review quality, or
  developer productivity (`engineering_owner`).
- `local_privacy`: a stated preference for local or privacy-conscious developer
  tooling.

Use warm introductions or a clearly published business contact address. Do not
scrape personal addresses, buy contact lists, or place sales messages in GitHub
issues, pull requests, or security-reporting channels.

## Experiment Boundary

- Contact 10 qualified prospects, one at a time.
- Personalize every message with one accurate, public observation.
- Use the direct-outreach route:
  `https://repo-scout.becastil.chatgpt.site/?source=outreach#why-teams-buy`.
- Send at most one follow-up after seven days without a reply.
- Stop immediately after an opt-out or a not-interested response.
- Review the batch after 14 days or after three pilot requests, whichever comes
  first.

The primary outcome is the first pilot request self-reporting `Direct outreach`.
Qualification, a written offer, and a paid label are separate later outcomes.
Do not count a reply, page visit, or release request as a lead or revenue.

## Initial Message

Subject: One repository standard across your team's projects

```text
Hi [first name],

I noticed [one specific public observation about the team's repositories, coding-agent use, or CI standards].

Repo Scout is a free local scanner plus a $299, 90-day pilot that helps a software team turn its repository rules into one shared policy across up to 10 projects, without uploading source code.

The team workflow is here:
https://repo-scout.becastil.chatgpt.site/?source=outreach#why-teams-buy

Would a 15-minute fit check be useful? If this is not relevant, say so and I
will not follow up.

Bennett
```

## One Follow-Up

```text
Hi [first name],

One follow-up in case repository standards across projects are on your roadmap. The $299 pilot covers one shared policy, rollout guidance, and one custom policy pack for up to 10 projects over 90 days:

https://repo-scout.becastil.chatgpt.site/?source=outreach#why-teams-buy

If this is not relevant, no reply is needed and I will not follow up again.

Bennett
```

## Private Ledger

Create the private workspace with owner-only directory and file permissions:

```bash
install -d -m 700 outreach-private
install -m 600 examples/outreach-ledger.csv \
  outreach-private/outreach-ledger.csv
touch outreach-private/drafts.md
chmod 600 outreach-private/drafts.md
```

The destination directory is ignored by Git. Live review, approval, contact,
and follow-up actions refuse any in-repository ledger or draft file that is
tracked, not ignored, or a symbolic link. On POSIX systems, those actions also
refuse a ledger or draft file with group/world permissions, or one stored in a
group/world-accessible parent directory; use `600` for files and `700` for the
workspace. The counts-only audit remains available for the empty tracked
example. Use an alias such as `prospect-001`; do not store names, email
addresses, message bodies, source code, or confidential company details in
this public repository.

Separate fit-signal keys with semicolons. Use `warm-intro` or
`published-business` as the channel. Allowed statuses are `researched`,
`drafted`, `review-declined`, `approved`, `contacted`, `followed-up`, `replied`,
`pilot-requested`, `not-a-fit`, and `do-not-contact`. Use `drafted` only after a
personalized message has been saved for review through a permitted channel.
Change it to `approved` only after a human confirms that the public observation
is accurate and current, the recipient and published business channel are
appropriate, and the message accurately states the price, scope, local-code
boundary, and a clear opt-out promising no further contact. Record that calendar
date in `approved_on`.
Drafted and review-declined rows cannot have an approval date. Approved rows
require one but still have no contact or follow-up dates. None of those three
statuses counts as attempted outreach. A review-declined row is closed before
contact and must retain blank approval, contact, follow-up, and next-action
dates.

Map every declared signal to the source reviewed for that claim in
`fit_evidence`, using semicolon-separated `signal=https://...` entries. For
example:

```text
team_5_50=https://provider.example/company/123;multi_repo=https://github.com/example
```

The links may point to a connected Sales Intelligence record or narrow public
evidence. They must use HTTPS and must not contain embedded credentials. Keep
them only in the ignored private ledger: a provider URL is traceability for
human review, not automatic proof that the claim is accurate or current.

Audit the ledger before each contact session:

```bash
repo-scout-outreach outreach-private/outreach-ledger.csv \
  --as-of "$(date +%F)"
```

Then surface one drafted alias at a time for human review:

```bash
repo-scout-outreach outreach-private/outreach-ledger.csv \
  --as-of "$(date +%F)" --review-next
```

This mode prints five unchecked criteria plus only the alias, permitted channel,
and qualification counts. It does not expose evidence URLs or draft text, does
not edit the ledger, and does not approve or send a message. The human reviewer
must inspect the private evidence and saved draft before using a guarded review
decision. The checklist is private operator material because it names a ledger
alias; do not commit it as a measurement baseline. Text mode ends with complete,
shell-quoted commands to approve or decline the selected alias using the current
`as_of` date and supplied ledger path. Choose exactly one after human review.

To inspect the selected draft and its qualification links without manually
cross-referencing the CSV and notes file, request both explicitly in the same
private review session:

```bash
repo-scout-outreach outreach-private/outreach-ledger.csv \
  --as-of "$(date +%F)" --review-next \
  --include-private-evidence \
  --include-private-draft outreach-private/drafts.md
```

The notes file uses one exact `## prospect-NNN` heading per draft. Before
showing anything, the opt-in requires a section for every ledger row still in
`drafted` status and rejects any section whose alias is absent from the ledger.
Sections for review-declined, approved, or contacted aliases may remain as
private history. The output then selects only the section matching the next
ledger alias, maps every declared fit signal to its private HTTPS source, and
marks both disclosures.
Duplicate, malformed, empty, oversized, missing, or unknown sections fail
without changing the ledger or exposing message text. Keep this output in the
ignored workspace and do not redirect it into committed reports, logs, issue
comments, or CI artifacts.
Without the flags, review output remains redacted. Showing the bundle still does
not verify a claim, approve a draft, or send a message; the human must read the
draft, open each source, and complete every displayed check.

If a human decides the selected draft must not be sent, close it without
creating contact activity:

```bash
repo-scout-outreach outreach-private/outreach-ledger.csv \
  --as-of "$(date +%F)" \
  --decline-next prospect-001 \
  --confirm-not-send
```

`--decline-next` requires the lowest drafted alias selected by `--review-next`
and explicit confirmation of the human no-send decision. It validates the
complete ledger before and after the transition, preserves file permissions,
and atomically changes only `status` to `review-declined`. Missing confirmation,
out-of-order aliases, invalid ledger state, or write failures leave the file
unchanged. The private receipt contains no evidence URL or persisted decision
date and ends with a complete command for reviewing the next draft. This status
counts as closed but never as attempted outreach; it does not approve, send,
schedule, or record contact.

After a human completes every displayed check, record that decision for the
same alias:

```bash
repo-scout-outreach outreach-private/outreach-ledger.csv \
  --as-of "$(date +%F)" \
  --approve-next prospect-001 \
  --approved-on "$(date +%F)" \
  --confirm-reviewed
```

`--approve-next` requires the lowest drafted alias selected by `--review-next`,
an explicit review date, and the confirmation flag. It validates the complete
ledger before and after the transition, preserves file permissions, and
atomically changes only `status` and `approved_on`. Missing confirmation,
out-of-order aliases, future dates, or invalid ledger state leave the file
unchanged. The private receipt omits evidence URLs and the review date. This
action records a human decision; it does not send outreach or create a contact
or follow-up date. Its text receipt ends with a complete command for recording
the manual send, using the same alias, `as_of` date, and private ledger path.

After review, the aggregate `Approved to send` count must include the selected
row before contact; the report still does not reveal its alias. A human must
then send that approved message through the permitted channel. Immediately
after the send, record it:

```bash
repo-scout-outreach outreach-private/outreach-ledger.csv \
  --as-of "$(date +%F)" \
  --record-contact prospect-001 \
  --contacted-on "$(date +%F)" \
  --confirm-sent
```

`--record-contact` requires the lowest approved alias, an explicit send date,
and confirmation that a human already sent the message. It retains
`approved_on`, changes only `status`, `contacted_on`, and `next_action_on`, and
computes the next action at exactly seven days. Keep `approved_on` on every
later status. Missing confirmation,
out-of-order aliases, dates before approval, future dates, invalid ledger state,
or write failures leave the file unchanged. The private receipt omits evidence,
approval dates, and the explicit contact field while naming the manual follow-up
due date. That date makes send timing inferable, so keep the receipt private.
Repo Scout sends nothing and schedules no automatic message. The text receipt
ends with a complete follow-up recording command whose `as_of` and
`followed-up-on` values are the exact due date; run it only after the human
follow-up has actually been sent.

On the due date, after a human sends the one allowed follow-up, record it:

```bash
repo-scout-outreach outreach-private/outreach-ledger.csv \
  --as-of "$(date +%F)" \
  --record-follow-up prospect-001 \
  --followed-up-on "$(date +%F)" \
  --confirm-follow-up-sent
```

`--record-follow-up` selects the contacted alias with the earliest due date,
requires an explicit send date and confirmation that a human already sent it,
and rejects early, future, or out-of-order records. It retains `approved_on`
and `contacted_on`, changes only `status`, `followed_up_on`, and
`next_action_on`, then clears the next action so a second follow-up is not
scheduled. Invalid state or write failure leaves the file unchanged. Its
receipt omits explicit approval, contact, and follow-up fields; keep it private
because it includes the alias and `as_of` context. Repo Scout sends nothing and
schedules no additional message.

The command requires at least three recognized fit signals and one secure
source link for each, accepts only `prospect-NNN` aliases, caps the batch at 10,
schedules a contacted prospect's single follow-up exactly seven days later,
and rejects next actions after a follow-up, reply, pilot request, rejection, or
opt-out. Every CSV row must contain exactly the nine header columns; missing or
extra cells and malformed quoting fail without echoing private values. Missing,
extra, duplicate, insecure, and credential-bearing evidence links also fail
validation. A separate
`followed_up_on` field rejects a second message sent before that date. It
reports drafts awaiting review and approved messages separately from sent
attempts, aliases, and aggregate evidence-link counts only; source URLs never
appear in report output. Approval dates also remain private. The command never
sends outreach, and its
reply or pilot-requested counts do not become public demand or revenue evidence;
only public pilot intake and cumulative funnel labels do.

A reviewed batch may publish the command's counts-only JSON as a measurement
baseline. Before committing it, verify that it contains no `prospect-` alias,
URL, email address, company name, or message text. The ignored ledger and draft
notes remain the only source for identities and qualification links.
