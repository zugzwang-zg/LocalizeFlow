# 事实核验模块验证报告

## 1. 模块交付

- `src/fact_checker.py`：确定性、声明级事实核验器及命令行入口。
- `tests/test_fact_checker.py`：16 项单元测试。
- `reports/fact_check/MV-SERUM-001_US_listing_fact_check.json`：通过案例。
- `reports/fact_check/MV-SERUM-001_US_high_risk_fact_check.json`：阻断案例。
- `reports/fact_check/risk_cases.json`：7 类代表性错误与风险案例。

## 2. 核验逻辑

模块从标题、卖点、描述、视频脚本和社媒文案中提取可核验声明，并与商品事实库逐项匹配。每项声明只使用以下五种状态：

- `supported`
- `partially_supported`
- `unsupported`
- `contradicted`
- `subjective`

确定性检查覆盖：

- 事实 ID、SKU、事实状态、证据等级、市场和语言范围；
- 数值与单位，包括容量和 US/MX 市场价格；
- 成分、配方、功效、认证、适用人群；
- 医疗、临床、抗衰老、认证、保证、绝对化及无依据时效表达；
- B 级功效证据是否使用 `helps`、`skin feels`、`ayuda a` 等谨慎限定语；
- 内容中未声明但可核验的事实陈述自动补提取。

事实错误率计算公式：

`(unsupported + contradicted) / factual_claim_count`

## 3. 导出闸门

- 高风险声明：`blocked`，禁止导出。
- 一般风险或部分支持：`needs_human_review`，进入人工确认。
- 自动事实核验通过：`pass`，但仍需后续平台规则检查和人工终审，因此本模块不会单独把 `export_allowed` 改为 `true`。
- 质量分不能覆盖事实闸门。

## 4. 验证结果

| 检查项 | 结果 | 验证证据 |
|---|---:|---|
| 所有数值信息均被检查 | 通过 | 正例 5/5 项数值完成核验 |
| 所有功效声明均有来源 | 通过 | 正例 2/2 项 B 级功效声明含事实 ID、来源和谨慎限定语 |
| 高风险内容不能导出 | 通过 | 反例状态为 `blocked`，`export_allowed=false` |
| 错误声明包含原因与修改建议 | 通过 | 反例 2/2 项问题声明字段完整 |
| 状态分类完整 | 通过 | 单元测试覆盖五种状态及导出闸门 |
| JSON 结果可解析 | 通过 | 4/4 份 JSON 资产通过解析 |

## 5. 正反例摘要

### 正例

- 声明数：13
- 支持：13
- 数值声明：5，已检查：5
- 高风险：0
- 事实错误率：0
- 事实闸门：`pass`

### 高风险反例

- 声明数：2
- `contradicted`：1（50 mL 与事实库 30 mL 矛盾）
- `unsupported`：1（治愈、保证和 72 小时功效无有效事实支持）
- 高风险：2
- 事实错误率：1.0
- 事实闸门：`blocked`

## 6. 测试记录

最终回归结果：

```text
Ran 16 tests in 0.013s
OK
compile=PASS
json_parse=4/4 PASS
numeric_checks=5/5 PASS
benefit_source_checks=2/2 PASS
high_risk_gate=blocked, export_allowed=False PASS
problem_claim_explanations=2/2 PASS
```

开发中曾发现事实错误率测试对已四舍五入结果使用过高精度比较，已改为按输出精度校验；随后加入无依据时效、US/MX 价格归属和绝对化适用人群测试，最终 16 项全部通过。

## 7. 已知边界

当前版本优先保证可解释、可复现的精确匹配和规则判断。复杂改写、隐喻、跨句指代或语义等价声明可能仍需模型辅助和人工复核；本模块也不替代平台、法律、医学或认证机构的最终判断。
