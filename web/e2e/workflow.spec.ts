import { test, expect, type Page } from "@playwright/test";

async function generate(page: Page) {
  await page.goto("/");
  await page.getByRole("button", { name: "设置营销任务 →" }).click();
  await page.getByRole("button", { name: "生成可追溯内容包 →" }).click();
  await page.getByRole("button", { name: "运行质量检查 →" }).click();
  // The frozen sample intentionally contains "a opaque". Exercise the real
  // repair/recheck flow instead of bypassing its unresolved-warning gate.
  await page.getByRole("button", { name: "一键修复", exact: true }).click();
  await expect(page.getByRole("textbox", { name: "人工编辑区" })).toHaveValue(/an opaque/);
}

test("approval belongs to the exact edited version; JSON download contains it", async ({ page }) => {
  await generate(page);
  await page.getByRole("button", { name: /版本与导出/ }).click();
  const approval = page.getByRole("checkbox", { name: /我已核对事实/ });
  await approval.check();
  const downloaded = page.waitForEvent("download");
  await page.getByRole("button", { name: "下载 JSON" }).click();
  const download = await downloaded;
  const stream = await download.createReadStream();
  const chunks = [];
  for await (const chunk of stream!) chunks.push(chunk);
  const payload = JSON.parse(Buffer.concat(chunks).toString("utf8"));
  expect(payload.human_review.status).toBe("confirmed");
  expect(payload.versions.final).toContain("TITLE:");
  await page.getByRole("button", { name: /质量检查/ }).first().click();
  const editor = page.getByRole("textbox", { name: "人工编辑区" });
  await editor.fill((await editor.inputValue()) + " A calm routine.");
  await page.getByRole("button", { name: /版本与导出/ }).click();
  await expect(approval).not.toBeChecked();
  await expect(page.getByRole("button", { name: "下载 JSON" })).toBeDisabled();
});

test("unsafe edits and empty content cannot be approved or exported", async ({ page }) => {
  await generate(page);
  const editor = page.getByRole("textbox", { name: "人工编辑区" });
  const original = await editor.inputValue();
  for (const text of [original + " FDA-approved. Contains retinol.", original.replace(/^TITLE:.*$/m, "TITLE: " + "A".repeat(151)), ""]) {
    await editor.fill(text);
    await expect(editor).toHaveValue(text);
    await page.getByRole("button", { name: /版本与导出/ }).click();
    await expect(page.getByRole("checkbox", { name: /我已核对事实/ })).toBeDisabled();
    await expect(page.getByRole("button", { name: "下载 JSON" })).toBeDisabled();
    await page.getByRole("button", { name: /质量检查/ }).first().click();
  }
});

test("changing the content tab invalidates an existing approval", async ({ page }) => {
  await generate(page);
  await page.getByRole("button", { name: /版本与导出/ }).click();
  await page.getByRole("checkbox", { name: /我已核对事实/ }).check();
  await page.getByRole("button", { name: /生成结果/ }).click();
  await page.getByRole("button", { name: "社媒广告文案", exact: true }).click();
  await page.getByRole("button", { name: /版本与导出/ }).click();
  await expect(page.getByRole("button", { name: "下载 JSON" })).toBeDisabled();
});
