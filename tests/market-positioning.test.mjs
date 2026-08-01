import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const comparisonUrl = new URL(
  "../docs/competitive-positioning.md",
  import.meta.url,
);

test("grounds paid positioning in current official competitor categories", async () => {
  const comparison = await readFile(comparisonUrl, "utf8");
  const normalized = comparison.replace(/\s+/g, " ");

  assert.match(normalized, /Reviewed: 2026-08-01/i);
  assert.match(normalized, /not a replacement for a source-code scanner/i);
  assert.match(normalized, /implementation-service advantage, not a proven technical moat/i);
  assert.match(normalized, /paid demand remains unvalidated/i);

  const officialSources = [
    "https://docs.semgrep.dev/semgrep-code/overview",
    "https://docs.sonarsource.com/sonarqube-server/user-guide/rules/overview",
    "https://docs.trunk.io/code-quality/overview",
    "https://www.conftest.dev/",
    "https://www.openpolicyagent.org/docs/latest/",
    "https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/about-rulesets",
  ];

  for (const source of officialSources) {
    assert.match(comparison, new RegExp(source.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")));
  }

  assert.match(normalized, /strongest build-it-yourself substitute/i);
  assert.match(normalized, /show whether submitted rollout bundles report the same normalized policy fingerprint/i);
  assert.match(normalized, /Do not build billing or license enforcement before the first paid pilot/i);
  assert.match(normalized, /does not measure market share, customer satisfaction, total cost of ownership, or direct feature parity/i);
});
