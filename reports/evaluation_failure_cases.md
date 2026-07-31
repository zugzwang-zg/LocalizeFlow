# A/B 评测失败案例

失败阈值：Fact Accuracy=Fail、Publishability≤2 或七维平均分≤3。实际共识别 30 条失败候选，最终工作簿的 `Failure Cases` 工作表保留全部记录。以下列出 10 个代表性案例，包含 Baseline 与 LocalizeFlow 的失败项。

| 候选 | 版本 | 语言 / 类型 | 均分 | 主要问题 | 评审结论与修改方向 |
|---|---|---|---:|---|---|
| G015-A | Baseline | es-MX / Listing | 1.86 | 禁止功效、本地化、结构 | 仅 3 个要点且中英混排；“Cubre todas tus necesidades”属于全能承诺，需要重写并补足 Listing 结构。 |
| G027-B | Baseline | es-MX / Listing | 1.86 | 禁止功效、包装矛盾、结构 | 西语搭配生硬，“Repara”越界，包装材质不一致；需要重写。 |
| G007-B | Baseline | en-US / Listing | 2.14 | 禁止功效、包装无依据、结构 | “Repairs”越界，铝管材质无事实支持，且仅有 3 个要点。 |
| G016-B | Baseline | en-US / Listing | 2.14 | 全能承诺、结构 | “Covers all of your skincare needs”违反事实边界，需要重写并补齐 Listing。 |
| G003-A | Baseline | es-MX / 短视频 | 2.14 | 禁止功效、语言 | “Repara las manos secas”超出允许功效边界，多处搭配生硬。 |
| G004-B | Baseline | es-MX / 短视频 | 2.14 | 全能承诺、本地化 | 存在禁止的全能表述及中英混排，削弱墨西哥市场适配。 |
| G003-B | LocalizeFlow | es-MX / 短视频 | 3.71 | 包装矛盾 | 脚本自然完整，但 “tubo de aluminio” 与事实参考的软管包装不一致；需修正并补 AIGC 标识。 |
| G006-A | LocalizeFlow | en-US / 短视频 | 3.86 | 包装矛盾 | 节奏与语言良好，但 “aluminum tube” 与事实参考不一致。 |
| G018-B | LocalizeFlow | en-US / Listing | 3.86 | 包装无依据、语言 | 不透明 PP 瓶无事实支持，且存在 “a opaque” 冠词错误；修正后方可发布。 |
| G007-A | LocalizeFlow | en-US / Listing | 4.00 | 包装无依据 | 结构和卖点完整，但铝管及 PP 盖未获事实参考支持；需要核验或删除。 |

## 失败模式汇总

| 标签 | 出现次数 |
|---|---:|
| Unsupported packaging | 14 |
| Prohibited claim | 12 |
| Platform structure | 10 |
| Language issue | 6 |
| Packaging mismatch | 6 |
| Brand risk | 4 |
| Borderline mean score | 2 |
| Localization issue | 2 |

## 关键发现

Baseline 的失败跨越事实、功效、品牌、语言与平台结构。LocalizeFlow 的失败范围明显收窄，10 条失败全部包含包装事实问题。这说明下一步最有价值的改进不是继续增加营销措辞，而是完善包装字段、禁止缺失事实补全，并把包装核验设为发布前硬闸门。
