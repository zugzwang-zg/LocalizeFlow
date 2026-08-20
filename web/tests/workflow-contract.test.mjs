import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

test("web packaging facts preserve the canonical verified fields", async () => {
  const [canonicalRaw, webRaw] = await Promise.all([
    readFile(new URL("../../data/products/packaging_facts.json", import.meta.url), "utf8"),
    readFile(new URL("../app/data/packaging_facts.json", import.meta.url), "utf8"),
  ]);
  const canonical = JSON.parse(canonicalRaw).products;
  const web = JSON.parse(webRaw).products;
  for (const [sku, product] of Object.entries(web)) {
    const facts = canonical[sku].facts;
    assert.ok(facts.some((fact) => fact.fact_id === product.fact_id));
    for (const [field, values] of Object.entries(product)) {
      if (["fact_id", "source", "capacity"].includes(field)) continue;
      const canonicalValues = facts.filter((fact) => fact.field === field).map((fact) => fact.value);
      if (canonicalValues.length) assert.ok(values.every((value) => canonicalValues.includes(value)));
    }
  }
  assert.deepEqual(web["MV-HAND-001"].material, ["aluminum"]);
  assert.deepEqual(web["MV-HAND-001"].container_type, ["tube"]);
});

test("quality workflow exposes locate, deterministic repair, warning disposition and timestamp", async () => {
  const page = await readFile(new URL("../app/page.tsx", import.meta.url), "utf8");
  assert.match(page, /setSelectionRange/);
  assert.match(page, /一键修复/);
  assert.match(page, /确认保留/);
  assert.match(page, /confirmed_at/);
  assert.match(page, /localizeflow_private_metrics/);
  assert.doesNotMatch(page, /events\.push\([^\n]*(finalText|edited|enhanced|baseline)/);
});

test("product readout exposes implementation scope, evidence and honest release boundaries", async () => {
  const page = await readFile(new URL("../app/page.tsx", import.meta.url), "utf8");
  assert.match(page, /PRODUCT CASE STUDY · EVIDENCE-LED WORKFLOW/);
  assert.match(page, /IMPLEMENTATION SCOPE/);
  assert.match(page, /从问题定义到发布闸门/);
  assert.match(page, /评测含 AI 辅助评分/);
  assert.match(page, /30 \/ 30/);
  assert.match(page, /−25\.8%/);
  assert.match(page, /−61\.5%/);
  assert.match(page, /FREE TRIAL · NO-GO/);
  assert.match(page, /仍有 10 个阈值失败候选/);
});

test("public trust pages exist", async () => {
  const pages = await Promise.all(["status", "support", "privacy", "terms", "acceptable-use", "disclaimer"].map((name) => readFile(new URL(`../app/${name}/page.tsx`, import.meta.url), "utf8")));
  assert.ok(pages.every((page) => page.includes("返回 Demo")));
});
