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

Would a 15-minute fit check be useful, or is repository standardization not a priority right now?

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

Copy `examples/outreach-ledger.csv` into
`outreach-private/outreach-ledger.csv`. The destination directory is ignored by
Git. Use an alias such as `prospect-001`; do not store names, email addresses,
message bodies, source code, or confidential company details in this public
repository.

Separate fit-signal keys with semicolons. Use `warm-intro` or
`published-business` as the channel. Allowed statuses are `researched`,
`drafted`, `approved`, `contacted`, `followed-up`, `replied`,
`pilot-requested`, `not-a-fit`, and `do-not-contact`. Use `drafted` only after a
personalized message has been saved for review through a permitted channel.
Change it to `approved` only after a human confirms that the public observation
is accurate and current, the recipient and published business channel are
appropriate, and the message accurately states the price, scope, local-code
boundary, and opt-out behavior. Record that calendar date in `approved_on`.
Drafted rows cannot have an approval date. Approved rows require one but still
have no contact or follow-up dates. Neither status counts as attempted
outreach.

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
must inspect the private evidence and saved draft before recording `approved`
and `approved_on` manually. The checklist is private operator material because
it names a ledger alias; do not commit it as a measurement baseline.

After review, the aggregate `Approved to send` count must include the selected
row before contact; the report still does not reveal its alias. Immediately
after sending, change that row to `contacted`, record `contacted_on`, and set
`next_action_on` to exactly seven days later before sending the next message.
Keep `approved_on` on every later status. The command rejects a missing or
future approval date and requires it to be no later than `contacted_on`. The
approval record preserves a human decision; the command does not approve or
send anything itself.

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
