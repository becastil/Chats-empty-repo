import assert from "node:assert/strict";
import test from "node:test";

async function render(headers = {}) {
  const workerUrl = new URL("../dist/server/index.js", import.meta.url);
  workerUrl.searchParams.set("test", `${process.pid}-${Date.now()}`);
  const { default: worker } = await import(workerUrl.href);

  return worker.fetch(
    new Request("http://localhost/", {
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
  assert.match(html, /property="og:image" content="http:\/\/localhost\/og\.png"/i);
  assert.match(html, /name="twitter:card" content="summary_large_image"/i);
  assert.match(html, /Repo Scout for every handoff\./i);
  assert.match(html, /Repo Scout Snapshot/i);
  assert.match(html, /Languages:/i);
  assert.match(html, /--languages \./i);
  assert.match(html, /Snapshot lab/i);
  assert.match(html, /id="team-pilot"/i);
  assert.match(html, /One policy your repositories can prove\./i);
  assert.match(html, /\$299/i);
  assert.match(html, /90 days/i);
  assert.match(html, /up to 10 repositories/i);
  assert.match(html, /repo-scout --policy team-policy\.toml \./i);
  assert.match(html, /Request a founding pilot/i);
  assert.match(html, /github\.com\/becastil\/Chats-empty-repo\/issues\/new\?template=founding-team-pilot\.yml/i);
  assert.equal((html.match(/<h1\b/gi) ?? []).length, 1);
  assert.doesNotMatch(html, /codex-preview|Your site is taking shape|react-loading-skeleton/i);
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
  assert.match(form, /\$299 for 90 days/i);
  assert.match(form, /up to 10 repositories/i);
  assert.match(form, /public/i);
  assert.match(form, /id: team_size/i);
  assert.match(form, /id: repository_count/i);
  assert.match(form, /id: ci_provider/i);
  assert.match(form, /id: repository_standard/i);
  assert.match(form, /required: true/i);
});
