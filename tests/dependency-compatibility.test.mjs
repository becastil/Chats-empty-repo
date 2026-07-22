import assert from "node:assert/strict";
import test from "node:test";

import { Miniflare } from "miniflare";
import sharp from "sharp";

test("the patched Sharp override processes an image", async () => {
  const output = await sharp({
    create: {
      width: 1,
      height: 1,
      channels: 4,
      background: { r: 0, g: 0, b: 0, alpha: 1 },
    },
  })
    .png()
    .toBuffer();

  assert.ok(output.length > 0);
});

test("Miniflare runs with the patched Sharp override", async () => {
  const worker = new Miniflare({
    modules: true,
    script: 'export default { fetch() { return new Response("ok") } }',
  });

  try {
    const response = await worker.dispatchFetch("http://localhost");
    assert.equal(await response.text(), "ok");
  } finally {
    await worker.dispose();
  }
});
