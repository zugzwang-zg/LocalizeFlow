# LocalizeFlow 商品事实库数据字典

> 数据集版本：1.0.0  
> 日期：2026-07-28  
> 上游来源：`data/products/product_master.xlsx`  
> 数据性质：产品原型模拟数据
> 当前规模：5 个 SKU，191 条事实记录

## 1. 文件说明

| 文件 | 用途 |
|---|---|
| `product_facts.csv` | 供人工检查、筛选、批量处理和数据分析使用 |
| `product_facts.json` | 供提示词、生成节点、事实核验模块和 Streamlit Demo 读取 |
| `data_dictionary.md` | 说明字段、证据等级、生成策略和更新规则 |

CSV 与 JSON 使用同一批记录和相同的 `fact_id`。JSON 保留数组、布尔值和数值类型；CSV 将数组序列化为 JSON 字符串，以避免分隔符歧义。

## 2. 事实 ID 规则

```text
{SKU}-F{三位流水号}
```

示例：

```text
MV-CLEAN-001-F003
```

- `MV-CLEAN-001`：商品 SKU；
- `F`：事实记录；
- `003`：该 SKU 内稳定递增的事实编号。

已有 `fact_id` 不得因排序变化而复用给其他事实。若事实被删除，应将其状态改为停用并保留历史记录；如确需重建数据库，应提升数据集主版本号。

## 3. 字段定义

| 字段 | 类型 | 必填 | 说明 |
|---|---|---:|---|
| `fact_id` | string | 是 | 全局唯一事实标识 |
| `sku` | string | 是 | 所属商品 SKU |
| `fact_category` | enum | 是 | 事实类别 |
| `attribute` | string | 是 | 机器可读属性名 |
| `value` | string / number | 是 | 事实值；数值必须保存为 number |
| `value_type` | enum | 是 | `string` 或 `number` |
| `unit` | string / null | 数值必填 | 数值单位，如 `mL`、`USD`、`MXN`、`second` |
| `sequence` | integer / null | 条件必填 | 成分、功效、风险项等有序记录的位置 |
| `evidence_level` | enum | 是 | `A`、`B`、`C` 或 `D` |
| `source` | string | 是 | 来源 ID 或可定位到具体章节的项目文件路径 |
| `source_type` | enum | 是 | 来源性质，明确区分规格、内部审核和营销假设 |
| `allowed_expression` | array[string] | 是 | 允许使用的表达；C、D 级必须为空数组 |
| `prohibited_expression` | array[string] | 是 | 禁止或需要拦截的表达 |
| `generation_policy` | enum | 是 | `direct`、`cautious`、`not_directly_usable` 或 `blocked` |
| `market_scope` | array[string] | 是 | 适用市场，MVP 使用 `US`、`MX` |
| `language_scope` | array[string] | 是 | 适用语言，使用 `zh`、`en`、`es` |
| `is_numeric` | boolean | 是 | `value` 是否为数值 |
| `status` | enum | 是 | `active`、`caution`、`non_fact` 或 `prohibited` |
| `linked_fact_ids` | array[string] | 是 | 关联事实 ID；套装用于引用组件商品 |
| `notes` | string | 否 | 限制、使用条件和维护说明 |

## 4. 事实类别

| `fact_category` | 含义 | 示例属性 |
|---|---|---|
| `basic_info` | 商品基础身份 | `product_name_zh`、`category` |
| `ingredient` | 成分或组件配方引用 | `ingredient`、`ingredient_reference` |
| `specification` | 容量、特征、pH、变体 | `net_volume`、`ph_nominal`、`verified_feature` |
| `usage` | 使用方法、用量和时长 | `usage_instruction`、`usage_amount_min` |
| `target_user` | 适用人群描述 | `target_users` |
| `function` | 项目内部允许的谨慎功效 | `allowed_benefit` |
| `packaging` | 包装形式、组件和条件性材料说明 | `packaging_feature` |
| `certification` | 当前可验证认证状态 | `verified_certification` |
| `price` | 分市场模拟建议零售价 | `price_usd`、`price_mxn` |
| `market` | 目标市场 | `target_market` |
| `risk_limit` | 明确禁止的宣称 | `prohibited_claim` |
| `marketing_direction` | 待消费者洞察验证的内容假设 | `content_hypothesis` |

## 5. 证据等级

| 等级 | 当前项目中的含义 | 是否可直接生成 | 默认策略 |
|---|---|---:|---|
| A | 有项目模拟产品规格支持 | 是 | `direct` |
| B | 有项目模拟内部宣称审核支持，但没有外部功效证明 | 谨慎 | `cautious` |
| C | 仅为营销方向或待验证假设，不是商品事实 | 否 | `not_directly_usable` |
| D | 明确禁止输出的风险表达 | 否 | `blocked` |

注意：A 级只代表在本项目模拟资料内部具有明确来源，不代表真实品牌文件、外部检测、临床研究或监管认证。

## 6. 生成策略

```text
A → 可作为事实输入，但仍须遵守允许表达和平台规则
B → 仅使用谨慎表达，禁止升级为医学、临床或保证性宣称
C → 不可直接进入生成上下文；需消费者洞察支持并与A/B级事实匹配
D → 不可进入生成内容；命中相同或语义等价表达时阻断导出
```

程序判断示例：

```python
if fact["evidence_level"] == "A":
    allow_for_generation = True
elif fact["evidence_level"] == "B":
    allow_for_generation = True
    requires_cautious_language = True
else:
    allow_for_generation = False
```

## 7. 数值结构化规则

所有影响事实核验的数值必须拆成独立记录，不得只保留在描述字符串中。

| 数值类型 | 属性示例 | 值 | 单位 |
|---|---|---:|---|
| 净含量 | `net_volume` | 120 | `mL` |
| 套装组件容量 | `serum_volume` | 10 | `mL` |
| 套装总容量 | `total_volume` | 55 | `mL` |
| 使用量下限 | `usage_amount_min` | 1 | `pump` |
| 使用量上限 | `usage_amount_max` | 2 | `pump` |
| 按摩时长 | `massage_duration` | 30 | `second` |
| pH 标称值 | `ph_nominal` | 5.5 | `pH` |
| pH 公差 | `ph_tolerance` | 0.5 | `pH` |
| 美国价格 | `price_usd` | 16 | `USD` |
| 墨西哥价格 | `price_mxn` | 319 | `MXN` |

数值记录必须满足：

- `value_type = "number"`；
- `is_numeric = true`；
- `unit` 非空；
- CSV 中能被解析为数值；
- JSON 中不得写成带单位的字符串。

## 8. 来源与可追溯规则

- A 级事实通常引用 `SIM-SPEC-*-V1`；
- B、D 级记录引用 `SIM-CLAIM-*-V1`；
- C 级营销假设引用具体商品卡的“营销建议（不是商品事实）”章节；
- `source` 不得为空；
- 上游模拟来源可在 `product_master.xlsx` 的 `Source Registry` 中核对；
- 每条生成内容后续必须返回使用到的 `fact_id`，不能只返回 SKU 或来源文件名。

## 9. 套装引用规则

`MV-KIT-001` 不创建一套新的独立成分表。其 `ingredient_reference` 记录通过 `linked_fact_ids` 关联洁面乳、精华和面霜的组件事实。

生成套装内容时：

1. 先读取套装组成和容量；
2. 再读取组件商品事实；
3. 不得把三个组件的成分合并成一个虚构配方；
4. 不得添加 TSA、航空公司或监管机构认证。

## 10. JSON 顶层结构

```json
{
  "dataset_name": "LocalizeFlow Product Facts",
  "dataset_version": "1.0.0",
  "generated_date": "2026-07-28",
  "source_workbook": "data/products/product_master.xlsx",
  "data_nature": "project_simulated",
  "record_count": 191,
  "sku_count": 5,
  "evidence_summary": {
    "A": 135,
    "B": 14,
    "C": 10,
    "D": 32
  },
  "facts": []
}
```

## 11. 记录示例

```json
{
  "fact_id": "MV-CLEAN-001-F003",
  "sku": "MV-CLEAN-001",
  "fact_category": "specification",
  "attribute": "net_volume",
  "value": 120,
  "value_type": "number",
  "unit": "mL",
  "sequence": null,
  "evidence_level": "A",
  "source": "SIM-SPEC-CLEAN-V1",
  "source_type": "project_simulated_product_specification",
  "allowed_expression": [
    "120 mL"
  ],
  "prohibited_expression": [
    "超过或少于120 mL"
  ],
  "generation_policy": "direct",
  "market_scope": [
    "US",
    "MX"
  ],
  "language_scope": [
    "zh",
    "en",
    "es"
  ],
  "is_numeric": true,
  "status": "active",
  "linked_fact_ids": [],
  "notes": ""
}
```

## 12. 更新规则

1. 商品规格发生变化时，先更新 `product_master.xlsx` 和对应商品卡；
2. 确认来源版本后更新受影响的事实记录；
3. 不得静默修改已有 `fact_id` 的含义；
4. 价格、容量、用量和 pH 等数值变化必须同步更新值、单位和允许表达；
5. 新增成分时维护 `sequence`；
6. 新增 C、D 级记录时必须保持 `allowed_expression = []`；
7. 每次更新后重新执行唯一 ID、必填字段、证据等级、数值类型和来源完整性检查；
8. CSV 与 JSON 必须由同一事实集合重新生成，禁止手工分别维护。

## 13. 当前完整性检查

- [x] 5 个 SKU 均有基础信息、成分、规格、用法、适用人群、包装、价格和市场记录；
- [x] A、B、C、D 四级记录均存在且可由程序识别；
- [x] C 级记录全部使用 `not_directly_usable`；
- [x] D 级记录全部使用 `blocked` 和 `prohibited`；
- [x] 所有关键数值均有独立数值记录和单位；
- [x] 191 个 `fact_id` 唯一；
- [x] CSV 与 JSON 记录数一致；
- [x] 所有记录均有来源。
