# Direct Outreach Playbook

This playbook turns the founding-team pilot into one bounded acquisition test.
It is for relevant, individual business outreach, not bulk email.

## Qualified Prospect

Contact a prospect only when public evidence supports at least three of these
signals:

- A software team with roughly 5 to 50 developers.
- Multiple actively maintained repositories or services.
- Visible use of coding agents or AI-assisted development.
- An engineering lead who owns CI, repository standards, review quality, or
  developer productivity.
- A stated preference for local or privacy-conscious developer tooling.

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

Allowed statuses are `researched`, `contacted`, `replied`, `pilot-requested`,
`not-a-fit`, and `do-not-contact`. A private ledger records operator activity;
only the public pilot intake and cumulative funnel labels become demand and
revenue evidence.
