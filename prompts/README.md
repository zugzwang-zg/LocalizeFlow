# LocalizeFlow 提示词资产

> 提示词集：`LF-PROMPTS-2026-07-28`  
> 版本：`1.0.0`  
> 日期：2026-07-28

## 文件结构

```text
prompts/
├── baseline_prompt.md
├── fact_extraction_prompt.md
├── campaign_planner_prompt.md
├── localization_prompt_en.md
├── localization_prompt_es.md
├── listing_prompt.md
├── tiktok_script_prompt.md
├── social_copy_prompt.md
├── evaluator_prompt.md
├── prompt_manifest.json
├── schemas/
│   ├── fact_extraction_output.schema.json
│   ├── campaign_strategy_output.schema.json
│   ├── localization_plan_output.schema.json
│   ├── content_output.schema.json
│   └── evaluation_output.schema.json
└── tests/
    ├── fixtures/
    ├── expected/
    └── validate_prompts_offline.py
```

## Baseline 与增强版

Baseline 仅要求翻译和生成指定内容，不加载事实、洞察、品牌、术语或平台规则。增强版按七节点设计拆分上下文和职责，并使用结构化 Schema。A/B 评测时两组必须使用相同 SKU、语言、内容类型、模型与参数。

## Structured Outputs

后续 API 实现使用 Responses API 的 `text.format`、`type="json_schema"` 和 `strict=true`。所有对象均设置 `additionalProperties=false`。JSON mode 只能保证 JSON 可解析，不能保证符合 Schema，因此不作为首选。

应用层仍需处理：

- 模型拒绝；
- 达到输出上限导致内容不完整；
- API/网络错误；
- Schema 不受所选模型支持；
- 业务规则错误，即使 JSON 本身符合 Schema。

参考：

- [OpenAI Structured model outputs](https://developers.openai.com/api/docs/guides/structured-outputs)
- [OpenAI model guidance](https://developers.openai.com/api/docs/guides/latest-model)

## 模型与参数

模型从 `.env` 的 `OPENAI_MODEL` 读取，不在提示词中写死。每次运行必须记录实际模型、提示词版本、参数、Schema 版本、原始响应、耗时和费用。

当前离线验证未配置 API key 和模型，因此没有产生付费 API 调用；单 SKU 测试只验证结构与约束，不作为真实模型质量结论。

## 本地校验

```powershell
.\.venv\Scripts\python.exe prompts\tests\validate_prompts_offline.py
```

校验覆盖 Schema 合法性、对象封闭性、提示词完整性、单 SKU Listing 字段、字符上限、五点数量、事实引用、B 级限定语与禁用宣称。
