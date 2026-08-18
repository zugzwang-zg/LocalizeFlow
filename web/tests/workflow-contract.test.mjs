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

test("quality workflow exposes locate, direct repair, warning disposition and timestamp", async () => {
  const page = await readFile(new URL("../app/page.tsx", import.meta.url), "utf8");
  assert.match(page, /setSelectionRange/);
  assert.match(page, /直接修改/);
  assert.match(page, /记录处理结果/);
  assert.match(page, /confirmed_at/);
  assert.match(page, /localizeflow_private_metrics/);
  assert.doesNotMatch(page, /events\.push\([^\n]*(finalText|edited|enhanced|baseline)/);
});

test("product overview explains scope, results and honest release boundaries", async () => {
  const page = await readFile(new URL("../app/page.tsx", import.meta.url), "utf8");
  assert.match(page, /跨境商品内容工作台 · 在线体验/);
  assert.match(page, /从商品资料到可下载结果/);
  assert.match(page, /用自己的表格试一遍/);
  assert.match(page, /30 \/ 30/);
  assert.match(page, /−25\.8%/);
  assert.match(page, /−61\.5%/);
  assert.match(page, /浏览器试用 · 已开放/);
  assert.match(page, /仍有 10 条内容没有达到要求/);
});

test("public trust pages exist", async () => {
  const pages = await Promise.all(["status", "support", "privacy", "terms", "acceptable-use", "disclaimer"].map((name) => readFile(new URL(`../app/${name}/page.tsx`, import.meta.url), "utf8")));
  assert.ok(pages.every((page) => page.includes("返回在线体验")));
});

test("browser-local spreadsheet trial exposes templates and guarded CSV/XLSX parsing", async () => {
  const [page, importer, csvTemplate, xlsxTemplate] = await Promise.all([
    readFile(new URL("../app/page.tsx", import.meta.url), "utf8"),
    readFile(new URL("../app/lib/product-import.ts", import.meta.url), "utf8"),
    readFile(new URL("../public/templates/localizeflow-demo-template.csv", import.meta.url), "utf8"),
    readFile(new URL("../public/templates/localizeflow-demo-template.xlsx", import.meta.url)),
  ]);
  assert.match(page, /accept="\.csv,\.xlsx/);
  assert.match(page, /不会上传/);
  assert.match(importer, /MAX_UPLOAD_BYTES = 2 \* 1024 \* 1024/);
  assert.match(importer, /read-excel-file\/browser/);
  assert.match(importer, /papaparse/);
  assert.doesNotMatch(importer, /fetch\(|XMLHttpRequest|sendBeacon/);
  assert.match(page, /下载 XLSX 模板/);
  assert.match(csvTemplate, /^sku,attribute,value,unit,evidence_level,source,source_type,market_scope,allowed_expression,prohibited_expression,generation_policy/m);
  assert.ok(xlsxTemplate.byteLength > 1024);
});
