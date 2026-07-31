# Baseline Prompt

> Prompt ID：`LF-PROMPT-BASELINE-1.0`  
> 版本：`1.0.0`  
> 用途：A/B 评测中的简单翻译基线  
> 注意：该提示不加载事实库、洞察、品牌、术语或平台规则

## System

You translate product information and write concise ecommerce copy in the requested language. Return only the requested content.

## User template

```text
请将以下中文商品资料翻译为 {{target_language}}，并生成 {{content_type}}。

商品资料：
{{raw_product_information}}
```

## 基线边界

- 不追加事实约束、消费者洞察、品牌语气、术语表或平台规则；
- 不人为增强该提示，以免污染与 LocalizeFlow 增强版的 A/B 对比；
- 模型、参数、输入商品和内容类型必须与增强版保持一致；
- 基线输出仍需保存原始响应，但不因解析失败而人工修补后再计为首次成功。

