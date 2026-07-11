import assert from "node:assert/strict";
import test from "node:test";

let renderCount = 0;

function countOccurrences(text, value) {
  return text.split(value).length - 1;
}

async function render(headers = {}, path = "/") {
  const workerUrl = new URL("../dist/server/index.js", import.meta.url);
  renderCount += 1;
  workerUrl.searchParams.set("test", `${process.pid}-${Date.now()}-${renderCount}`);
  const { default: worker } = await import(workerUrl.href);

  return worker.fetch(
    new Request(new URL(path, "http://localhost"), {
      headers: { accept: "text/html", ...headers },
    }),
    {
      ASSETS: {
        fetch: async () => new Response("Not found", { status: 404 }),
      },
    },
    { waitUntil() {}, passThroughOnException() {} },
  );
}

test("server-renders the Repo Scout companion page", async () => {
  const response = await render();
  assert.equal(response.status, 200);
  assert.match(response.headers.get("content-type") ?? "", /^text\/html\b/i);

  const html = await response.text();
  assert.match(html, /<title>Repo Scout \| Local repository policy for teams<\/title>/i);
  assert.match(html, /One-file local repository snapshots/i);
  assert.match(html, /property="og:image" content="http:\/\/localhost\/og\.png"/i);
  assert.match(html, /name="twitter:card" content="summary_large_image"/i);
  assert.match(html, /Repo Scout for every handoff\./i);
  assert.match(html, /Repo Scout Snapshot/i);
  assert.match(html, /Languages:/i);
  assert.match(html, /--languages \./i);
  assert.match(html, /Copy no-install setup/i);
  assert.match(html, /One file\. Python 3\.11\+\. No API key\./i);
  assert.match(html, /curl -fL/i);
  assert.match(html, /repo-scout-0\.3\.13\.pyz/i);
  assert.match(html, /python3 \/tmp\/repo-scout\.pyz --languages \./i);
  assert.match(html, /Download v/i);
  assert.match(
    html,
    /releases\/download\/v0\.3\.13\/repo-scout-0\.3\.13\.pyz/i,
  );
  assert.doesNotMatch(html, /PYTHONPATH=src python3 -m repo_scout/i);
  assert.match(html, /Snapshot lab/i);
  assert.match(html, /id="why-teams-buy"/i);
  assert.match(html, /An AI can build checks\. We make them work across your team\./i);
  assert.match(html, /not payment for another scanner/i);
  assert.match(html, /Your rules, made repeatable/i);
  assert.match(html, /One rollout across 10 projects/i);
  assert.match(html, /Proof and support when something fails/i);
  assert.match(html, /Your code stays with you\. The scanner stays free and open source\./i);
  assert.match(html, /Apply for the \$299 pilot/i);
  assert.match(html, /See the rollout proof/i);
  assert.match(html, /Share with your engineering lead/i);
  assert.match(
    html,
    /href="mailto:\?subject=Repo\+Scout%3A\+one\+repository\+standard\+across\+10\+projects&amp;body=[^"]+source%3Dreferral%23why-teams-buy"/i,
  );
  assert.equal(countOccurrences(html, 'href="mailto:'), 1);
  assert.match(html, /id="team-pilot"/i);
  assert.ok(html.indexOf('id="why-teams-buy"') < html.indexOf('id="team-pilot"'));
  assert.match(html, /Prove one policy across every repository\./i);
  assert.match(html, /\$299/i);
  assert.match(html, /90 days/i);
  assert.match(html, /up to 10 repositories/i);
  assert.match(html, /shared policy \/ verified/i);
  assert.match(html, /3 \/ 3/i);
  assert.match(html, /policy fingerprints/i);
  assert.match(html, /commits recorded/i);
  assert.match(html, /platform\/worker/i);
  assert.match(html, /remediation required/i);
  assert.match(html, /bundle-reported evidence/i);
  assert.match(html, /repo-scout-rollout api\.md web\.md worker\.md/i);
  assert.match(html, /Apply for the \$299 pilot/i);
  assert.match(
    html,
    /github\.com\/becastil\/Chats-empty-repo\/issues\/new\?template=founding-team-pilot\.yml(?:&amp;|&)discovery_source=Repo\+Scout\+website/i,
  );
  assert.equal(
    countOccurrences(
      html,
      'href="https://github.com/becastil/Chats-empty-repo/issues/new?template=founding-team-pilot.yml&amp;discovery_source=Repo+Scout+website"',
    ),
    2,
  );
  assert.equal((html.match(/<h1\b/gi) ?? []).length, 1);
  assert.doesNotMatch(html, /codex-preview|Your site is taking shape|react-loading-skeleton/i);
});

test("preserves supported campaign sources in pilot application links", async () => {
  const campaigns = new Map([
    ["github", "GitHub+repository+or+release"],
    ["website", "Repo+Scout+website"],
    ["outreach", "Direct+outreach"],
    ["referral", "Teammate+or+referral"],
    ["search", "Search"],
    ["social", "Social+media+or+community"],
    ["other", "Other"],
  ]);

  for (const [campaign, expectedSource] of campaigns) {
    const response = await render({}, `/?source=${campaign}`);
    const html = await response.text();
    assert.equal(
      countOccurrences(
        html,
        `href="https://github.com/becastil/Chats-empty-repo/issues/new?template=founding-team-pilot.yml&amp;discovery_source=${expectedSource}"`,
      ),
      2,
      campaign,
    );
  }

  const fallback = await render({}, "/?source=unrecognized");
  const fallbackHtml = await fallback.text();
  assert.equal(
    countOccurrences(
      fallbackHtml,
      'href="https://github.com/becastil/Chats-empty-repo/issues/new?template=founding-team-pilot.yml&amp;discovery_source=Repo+Scout+website"',
    ),
    2,
  );
  assert.doesNotMatch(fallbackHtml, /discovery_source=unrecognized/i);

  const inheritedName = await render({}, "/?source=toString");
  const inheritedNameHtml = await inheritedName.text();
  assert.equal(
    countOccurrences(
      inheritedNameHtml,
      'href="https://github.com/becastil/Chats-empty-repo/issues/new?template=founding-team-pilot.yml&amp;discovery_source=Repo+Scout+website"',
    ),
    2,
  );

  const repeated = await render({}, "/?source=outreach&source=github");
  const repeatedHtml = await repeated.text();
  assert.equal(
    countOccurrences(
      repeatedHtml,
      'href="https://github.com/becastil/Chats-empty-repo/issues/new?template=founding-team-pilot.yml&amp;discovery_source=Direct+outreach"',
    ),
    2,
  );
  assert.doesNotMatch(
    repeatedHtml,
    /href="[^"]+discovery_source=GitHub\+repository\+or\+release"/i,
  );
});

test("builds social metadata from the incoming public host", async () => {
  const response = await render({
    "x-forwarded-host": "repo-scout.example",
    "x-forwarded-proto": "https",
  });
  const html = await response.text();

  assert.match(
    html,
    /property="og:image" content="https:\/\/repo-scout\.example\/og\.png"/i,
  );
  assert.match(
    html,
    /name="twitter:image" content="https:\/\/repo-scout\.example\/og\.png"/i,
  );
});

test("ships a qualified founding-team pilot intake", async () => {
  const { readFile } = await import("node:fs/promises");
  const form = await readFile(
    new URL("../.github/ISSUE_TEMPLATE/founding-team-pilot.yml", import.meta.url),
    "utf8",
  );

  assert.match(form, /name: Founding-team pilot/i);
  assert.match(form, /pilot-lead/i);
  assert.match(form, /\$299 for 90 days/i);
  assert.match(form, /up to 10 repositories/i);
  assert.match(form, /public/i);
  assert.match(form, /id: team_size/i);
  assert.match(form, /id: repository_count/i);
  assert.match(form, /id: ci_provider/i);
  assert.match(form, /id: discovery_source/i);
  assert.match(form, /How did you hear about Repo Scout\?/i);
  assert.match(form, /Repo Scout website/i);
  assert.match(form, /GitHub repository or release/i);
  assert.match(form, /Teammate or referral/i);
  assert.match(form, /id: repository_standard/i);
  assert.match(form, /id: decision_criterion/i);
  assert.match(form, /label: Primary purchase criterion/i);
  assert.match(form, /Works across our repositories and CI/i);
  assert.match(form, /Meets our privacy and security requirements/i);
  assert.match(form, /The \$299 scope and price fit/i);
  assert.match(form, /id: purchase_readiness/i);
  assert.match(form, /label: Purchase readiness/i);
  assert.match(form, /Ready to purchase the \$299 pilot/i);
  assert.match(form, /Need internal approval for \$299/i);
  assert.match(form, /Exploring before requesting budget/i);
  assert.match(form, /required: true/i);
});
