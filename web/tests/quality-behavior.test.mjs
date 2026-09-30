import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";
import { fileURLToPath } from "node:url";
import { spawnSync } from "node:child_process";
import { build } from "esbuild";

const bundle = await build({ entryPoints: [fileURLToPath(new URL("../lib/demo-quality.ts", import.meta.url))], bundle: true, write: false, platform: "node", format: "esm" });
const { inspectContent } = await import(`data:text/javascript;base64,${Buffer.from(bundle.outputFiles[0].text).toString("base64")}`);
const cases = JSON.parse(await readFile(new URL("../../data/rules/quality_cases.json", import.meta.url), "utf8"));

test("video duration requires review and Spanish pieces has a concrete repair", () => {
  const video = inspectContent("00:00-00:15 Voice: Helps skin feel soft. CTA: Read more.", "short_video_script", "US", "MV-SERUM-001");
  assert.equal(video.checks.find((check) => check.id === "narration-review").status, "warning");
  const kit = inspectContent("GANCHO: 3 pieces\nTEXTO: Rutina\nCTA: Consulta los detalles", "social_ad_copy", "MX", "MV-KIT-001");
  assert.equal(kit.checks.find((check) => check.id === "terminology").replacement, "3 piezas");
});

for (const fixture of cases) {
  test(`shared Python/browser gate: ${fixture.name}`, () => {
    const result = inspectContent(fixture.text, fixture.type, fixture.market, fixture.sku);
    assert.equal(result.failed > 0, fixture.blocked);
  });
}

test("unimplemented duration/length check is explicitly not checked", () => {
  const result = inspectContent("HOOK: Hi\nBODY: Care\nCTA: Read", "social_ad_copy", "US", "MV-SERUM-001");
  assert.equal(result.checks.find((check) => check.id === "length").status, "not_checked");
});

test("Python and browser agree on gates for all frozen content and regression cases", async () => {
  const { groups } = JSON.parse(await readFile(new URL("../app/data/content_library.json", import.meta.url), "utf8"));
  const inputs = [...cases, ...groups.flatMap((group) => Object.entries(group.versions).map(([version, text]) => ({ name: `${group.sku}/${group.market}/${group.content_type}/${version}`, sku: group.sku, market: group.market, type: group.content_type, text })))];
  const result = spawnSync(process.env.PYTHON || "python", ["-c", "import json,sys; from src.demo_service import evaluate_text; print(json.dumps([evaluate_text(sku=c['sku'],market=c['market'],content_type=c['type'],text=c['text'])['export_gate']=='blocked' for c in json.load(sys.stdin)]))"], { cwd: fileURLToPath(new URL("../../", import.meta.url)), input: JSON.stringify(inputs), encoding: "utf8", env: { ...process.env, PYTHONUTF8: "1" } });
  assert.equal(result.status, 0, result.stderr);
  const python = JSON.parse(result.stdout);
  inputs.forEach((fixture, index) => assert.equal(inspectContent(fixture.text, fixture.type, fixture.market, fixture.sku).failed > 0, python[index], fixture.name));
});
