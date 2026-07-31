# 品牌、术语和平台规则检查验证报告

## 1. 模块交付

- `src/rule_checker.py`：品牌、术语、平台规则检查器及命令行入口。
- `tests/test_rule_checker.py`：18 项单元测试。
- `tests/fixtures/rule_checker/MV-SERUM-001_US_listing_revised.json`：修改后内容及模拟平台检查上下文。
- `reports/rule_check/MV-SERUM-001_US_listing_before_rule_check.json`：修改前阻断报告。
- `reports/rule_check/MV-SERUM-001_US_listing_revised_rule_check.json`：修改后通过报告。
- `reports/fact_check/MV-SERUM-001_US_listing_v02_fact_check.json`：修改后内容重新执行的事实核验结果。

## 2. 检查范围

模块读取以下既有资产：

- 品牌指南：`data/brand/brand_voice_guide.md`
- 术语库：`data/brand/terminology.xlsx`
- 禁用词与谨慎词：`data/brand/prohibited_terms.csv`
- 平台规则：`data/platform_rules/platform_rules.json`
- 事实检查报告：`reports/fact_check/`

确定性检查覆盖：

- 字符长度与必填字段；
- 全大写、异常标点、异常符号、异常空格和关键词重复；
- Listing 中的价格、免邮、折扣等促销信息；
- 品牌禁用词和需要证据/人工确认的谨慎词；
- 英语及墨西哥西班牙语术语一致性；
- 品牌语调和 CTA；
- AI 文本、图片或显著编辑内容的标识字段；
- US/en-US/USD 与 MX/es-MX/MXN 的市场匹配；
- Google Merchant Center、TikTok Ads 和 Generic Social 的适用规则。

无法本地自动确认的落地页、媒体文件或语言自然度项目不会伪装为通过，而是输出 `needs_human_review`。

## 3. 规则与评分分层

规则结果只使用：

- `pass`
- `fail`
- `not_applicable`
- `needs_human_review`

规则类型分别统计：

- `platform_hard_rule`
- `platform_best_practice`
- `brand_rule`
- `terminology_rule`
- `project_internal_rule`

六维质量评分与硬规则独立：

| 维度 | 权重 |
|---|---:|
| 事实准确性 | 30 |
| 平台适配度 | 20 |
| 语言自然度 | 15 |
| 品牌一致性 | 15 |
| 本地化程度 | 10 |
| 营销说服力 | 10 |
| 合计 | 100 |

每个扣分项都包含扣分数、原因和规则或证据。语言自然度、本地化程度和营销说服力明确标记为启发式预检，需要人工复核。

## 4. 闸门优先级

1. 事实错误：最高优先级，直接 `blocked`。
2. 平台、品牌、术语或项目内部 block 级失败：`blocked`。
3. 需确认项目：`needs_human_review`。
4. 自动检查无问题：`pass`，但 `export_allowed` 仍为 `false`，等待人工最终审核。

质量分无论多高都不能覆盖上述闸门。

## 5. 修改前后结果

| 指标 | 修改前 | 修改后 |
|---|---:|---:|
| 规则结果总数 | 29 | 27 |
| 通过 | 10 | 25 |
| 失败 | 14 | 0 |
| 不适用 | 2 | 2 |
| 需人工复核 | 3 | 0 |
| block 级失败 | 14 | 0 |
| 质量分 | 35.0 | 100.0 |
| 闸门 | `blocked` | `pass` |
| 最终可导出 | 否 | 否，仍需人工终审 |

修改前的事实错误优先于总分，阻断原因包括临床/治愈/保证/72 小时功效、容量矛盾、Listing 结构不完整和平台字段缺失。

修改后：

- 15/15 条适用的 Google 平台硬规则均有明确结果；
- 无硬规则失败或未决项；
- 品牌、术语、CTA、AI 标识、市场语言和 USD 价格检查通过；
- 报告中的 `content_version_record` 同时保留修改前和修改后内容快照；
- `parent_version_id` 与修改前版本一致，版本链验证通过。

修改后 100 分只表示当前确定性及启发式预检未发现扣分项，不表示 Google 批准、法律合规或可直接发布。

## 6. 验证门槛

| 检查项 | 结果 | 验证证据 |
|---|---:|---|
| 每个扣分项都有原因 | 通过 | 18/18 项扣分记录包含原因 |
| 每个失败/复核项都有原因与建议 | 通过 | 17/17 项字段完整 |
| 硬性规则和主观评分分开 | 通过 | 5 类规则统计与 6 个评分维度独立保存 |
| 事实错误拥有最高阻断优先级 | 通过 | 修改前 `blocking_priority=fact_error` |
| 修改前后内容均被保留 | 通过 | 当前与上一版本完整快照同时存在 |
| 质量分不能覆盖硬闸门 | 通过 | 两份报告均为 `quality_score_can_override=false` |

## 7. 最终回归

事实核验与规则检查模块的完整回归结果：

```text
compile=PASS
unit_tests=34/34 PASS
json_parse=4/4 PASS
applicable_platform_hard_rules=15/15 resolved
problem_item_reason_action=17/17 PASS
quality_deduction_reasons=18/18 PASS
rule_types_separated=5 categories PASS
fact_priority=fact_error PASS
version_snapshots=current+previous PASS
revised_gate=pass, export_allowed=False PASS
```

## 8. 开发中发现并修复的问题

- 修复重复标点正则表达式的捕获组错误。
- 修复术语库跨商品反例造成的误报：当某表达是全库中的有效首选词或允许变体时，不再被另一商品条目的反例错误阻断。
- 修复 TikTok 时长字段优先级：以最终视频素材对象的时长为准。

## 9. 使用边界

- 示例域名和落地页确认字段均为离线模拟上下文，没有执行真实网络、账户或平台审核。
- 自动规则检查不替代平台政策、当地法律、法务、医学、认证或母语审校。
- 平台规则会变化，真实发布前必须加载当时有效的规则版本并重新检查。
