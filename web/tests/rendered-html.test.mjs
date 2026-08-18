import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

async function render() {
  const workerUrl = new URL("../dist/server/index.js", import.meta.url);
  workerUrl.searchParams.set("test", `${process.pid}-${Date.now()}`);
  const { default: worker } = await import(workerUrl.href);
  return worker.fetch(
    new Request("http://localhost/", { headers: { accept: "text/html" } }),
    { ASSETS: { fetch: async () => new Response("Not found", { status: 404 }) } },
    { waitUntil() {}, passThroughOnException() {} },
  );
}

test("server-renders the LocalizeFlow demo shell", async () => {
  const response = await render();
  assert.equal(response.status, 200);
  const html = await response.text();
  assert.match(html, /<title>LocalizeFlow｜跨境商品内容工作台<\/title>/i);
  assert.match(html, /把商品资料变成能检查、能修改、能放心交付的跨境内容/);
  assert.match(html, /开始在线体验/);
  assert.match(html, /30 \/ 30/);
  assert.match(html, /从商品资料到可下载结果/);
  assert.match(html, /浏览器试用 · 已开放/);
  assert.match(html, /在浏览器里处理 · 不上传文件/);
  assert.match(html, /上传 CSV \/ XLSX/);
  assert.match(html, /商品资料/);
  assert.doesNotMatch(html, /codex-preview|Your site is taking shape|react-loading-skeleton/i);
});

test("keeps the public demo deterministic and accessible", async () => {
  const [page, layout, css, packageJson] = await Promise.all([
    readFile(new URL("../app/page.tsx", import.meta.url), "utf8"),
    readFile(new URL("../app/layout.tsx", import.meta.url), "utf8"),
    readFile(new URL("../app/globals.css", import.meta.url), "utf8"),
    readFile(new URL("../package.json", import.meta.url), "utf8"),
  ]);
  assert.match(page, /offline_deterministic_demo/);
  assert.match(page, /model_api_called:\s*false/);
  assert.match(page, /aria-label="工作流步骤"/);
  assert.match(page, /同意在下载的反馈文件中附带完整内容/);
  assert.match(page, /Content body included: no/);
  assert.match(page, /登记后续体验意向/);
  assert.doesNotMatch(page, /申请 Beta 试用/);
  assert.match(css, /prefers-reduced-motion:\s*reduce/);
  assert.match(layout, /lang="zh-CN"/);
  assert.match(layout, /og-portfolio\.png/);
  assert.doesNotMatch(packageJson, /react-loading-skeleton/);
});
