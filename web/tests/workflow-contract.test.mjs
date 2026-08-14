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

test("public trust pages exist", async () => {
  const pages = await Promise.all(["privacy", "terms", "disclaimer"].map((name) => readFile(new URL(`../app/${name}/page.tsx`, import.meta.url), "utf8")));
  assert.ok(pages.every((page) => page.includes("返回 Demo")));
});
