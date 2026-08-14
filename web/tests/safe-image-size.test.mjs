import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

import { imageSize } from "image-size";

test("reads the reviewed PNG social-card dimensions", async () => {
  const image = await readFile(new URL("../public/og.png", import.meta.url));
  assert.deepEqual(imageSize(image), { type: "png", width: 1536, height: 1024 });
});

test("rejects unsupported ICNS, JXL, and HEIF inputs without parsing", () => {
  for (const signature of ["icns", "\xff\x0a", "ftypheic"]) {
    const input = Buffer.from(signature, "latin1");
    assert.throws(() => imageSize(input), /Unsupported image type/);
  }
});

test("rejects malformed JPEG data without an unbounded scan", () => {
  const malformed = Buffer.from([0xff, 0xd8, 0xff, 0xc0, 0x7f, 0xff]);
  assert.throws(() => imageSize(malformed), /Malformed JPEG segment length/);
});
