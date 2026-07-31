# 单 SKU 离线提示词验证记录

> 日期：2026-07-28  
> SKU：`MV-SERUM-001`  
> 市场：US  
> 内容类型：Google Merchant Center 商品 Listing  
> 调试性质：离线结构与约束验证  
> API 调用：0

## 调试输入

- 商品：水衡保湿精华；
- 目标语言：`en-US`；
- 选用洞察：`IN-US-001`、`IN-US-003`、`IN-US-004`、`IN-US-006`；
- 事实输入同时包含 A、B、C 级记录，用于确认 C 级事实不会进入输出；
- 明确测试的禁用表达包括 24/72 小时保湿、修复屏障、临床证明、non-sticky 和 fast-absorbing。

输入夹具：`prompts/tests/fixtures/MV-SERUM-001_US_listing_input.json`

## 预期输出

预期输出包含：

- 1 个不超过 150 字符的标题；
- 5 个卖点；
- 1 个不超过 5000 字符的描述；
- 13 条 claim 记录；
- 33 个 `fact_id` 引用；
- Google AI 文本字段 `structured_title`、`structured_description` 与 `trained_algorithmic_media`；
- 人工复核状态 `pending`。

预期夹具：`prompts/tests/expected/MV-SERUM-001_US_listing_expected.json`

该文件是人工建立的“预期模型输出夹具”，用于验证 Schema 和约束，不应描述为真实 API 生成结果。

## 执行记录

### 第一次

- 结果：失败；
- 原因：验证脚本把 `prompts/` 错误上溯为项目根目录，无法找到 fixture；
- 处理：将测试根路径由 `parents[2]` 修正为 `parents[1]`；
- 内容与 Schema 未发生修改。

### 第二次

```json
{
  "status": "pass",
  "schema_files_validated": 5,
  "prompt_files_checked": 9,
  "fixture_sku": "MV-SERUM-001",
  "fixture_market": "US",
  "fixture_content_type": "product_listing",
  "claim_count": 13,
  "fact_refs_checked": 33,
  "api_calls_made": 0,
  "errors": []
}
```

## 已验证项目

- 5 份 JSON Schema 均符合 Draft 2020-12；
- Schema 中所有对象均设置 `additionalProperties=false`；
- 9 份提示词文件存在且非空；
- Listing 符合标题、五点和描述结构；
- 所有 claim 均有 `fact_id`；
- 输出只引用 A/B 级事实；
- B 级功效保留 `helps / skin feel` 限定；
- C 级 non-sticky 假设没有进入输出；
- 禁用宣称没有进入输出；
- AI 来源字段与人工审核字段存在。

## 尚未验证

- 未验证真实模型的生成稳定性、解析成功率、语言自然度、延迟或成本；
- 未验证墨西哥西语真实模型输出；
- 未验证全部 5 个 SKU；
- 未验证 Google 或 TikTok 的真实平台审核。

这些项目需要在配置 API key、确定测试模型并获得调用授权后执行，结果不能由本次离线测试推断。
