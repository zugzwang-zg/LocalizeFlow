# LocalizeFlow 平台规则来源与适用说明

> 规则集：`LF-PLATFORM-RULES-2026-07-28`  
> 版本：`1.0.0`  
> 最近核验：2026-07-28  
> 状态：已核验

## 1. 适用范围

| 内容类型 | 采用的规则范围 | 市场 |
|---|---|---|
| 商品 Listing | Google Merchant Center 商品数据规范与购物政策 | 美国英语、墨西哥西班牙语 |
| 15/30 秒短视频脚本 | TikTok Ads 广告政策与 Non-Spark In-Feed 规格 | 美国英语、墨西哥西班牙语 |
| 社媒/广告文案 | 通用项目模板；发布平台未指定 | 美国英语、墨西哥西班牙语 |

“Generic Social” 不是现实平台名称。它只解决项目内部的内容结构问题，不包含或暗示 Instagram、Facebook、X、Pinterest 等平台的字符上限和审核规则。选择真实发布平台后，必须加载该平台当时有效的官方规则并重新审核。

## 2. 规则层级

| `rule_type` | 含义 | 自动处理 |
|---|---|---|
| `platform_hard_rule` | 官方页面明确要求或禁止 | 不通过则阻断导出 |
| `platform_best_practice` | 官方推荐，但不是单独的放行条件 | 给出优化提示 |
| `brand_rule` | Mirevane Botanics 的品牌与风险边界 | 按严重度阻断或复核 |
| `project_internal_rule` | 为结构化、事实追踪和评测设置 | 不得描述为平台官方要求 |

平台上传规格与审核政策可能同时生效。若同一字段存在不同上限，执行更严格的有效规则。例如，TikTok Non-Spark 文件规格允许上传最长 10 分钟的视频，但广告格式政策将广告时长限定为 5–60 秒，因此本项目按 60 秒的更严格上限检查，并只生成 15 秒或 30 秒脚本。

## 3. 官方来源清单

| 来源 ID | 平台 | 官方页面 | 发布方页面日期 | 本项目核验日期 | 主要覆盖 |
|---|---|---|---|---|---|
| `GMC-PDS` | Google Merchant Center | [Product data specification](https://support.google.com/merchants/answer/7052112?hl=en) | 页面未显示 | 2026-07-28 | 必填字段、标题/描述上限、链接、图片、库存、价格、AI 文本与图片 |
| `GMC-MISREP` | Google Merchant Center | [Misrepresentation](https://support.google.com/merchants/answer/6150127?hl=en) | 页面未显示 | 2026-07-28 | 虚假/不现实宣称、遗漏价格与条款、不可用商品 |
| `GMC-EDITORIAL` | Google Merchant Center | [Editorial & professional requirements](https://support.google.com/merchants/answer/6150244?hl=en) | 页面未显示 | 2026-07-28 | 拼写语法、异常标点和大小写、落地页相关性与完整性 |
| `GMC-AI-2024` | Google Merchant Center | [2024 Merchant Center product data specification update](https://support.google.com/merchants/answer/14784710?hl=en) | 2024-04-09 | 2026-07-28 | AI 标题、描述和图片披露字段 |
| `TTA-FORMAT` | TikTok Ads | [Ad format and functionality](https://ads.tiktok.com/help/article/tiktok-ads-policy-ad-format-and-functionality?lang=en) | 2026-04 | 2026-07-28 | 落地页、广告一致性、文案质量、5–60 秒、画幅、音频、市场语言与货币 |
| `TTA-INFEED` | TikTok Ads | [TikTok Auction In-Feed Ads](https://ads.tiktok.com/help/article/tiktok-auction-in-feed-ads?lang=en&redirected=2) | 2026-06 | 2026-07-28 | Non-Spark 分辨率、文件格式、大小、码率、说明文字和安全区 |
| `TTA-MISLEADING` | TikTok Ads | [Misleading and false content](https://ads.tiktok.com/help/article/tiktok-ads-policy-misleading-and-false-content?lang=en) | 2026-04 | 2026-07-28 | 夸大效果、信息不一致、虚假交互、前后对比、AIGC 标识 |

Google 部分页面不展示“最后更新”日期，不能据此虚构发布日期；规则文件将 `publisher_last_updated` 设为 `null`，同时保留实际核验日期。

## 4. 关键规则摘要

### 4.1 Google Merchant Center 商品 Listing

- `id` 必填，最多 50 字符。
- `title` 或 `structured_title` 必填，最多 150 字符。
- `description` 或 `structured_description` 必填，最多 5000 字符。
- AI 生成的标题和描述分别使用 `structured_title`、`structured_description`，并标记 `trained_algorithmic_media`。
- `link`、`image_link`、`availability`、`price` 必填；库存和价格需与落地页/结账页一致。
- AI 生成的商品图片须保留相应 IPTC 数字来源元数据。
- 标题和描述不得加入免邮等促销文字、全大写、花哨符号或与商品无关的信息。
- 不得使用虚假、无支持、不现实或医学误导式宣称，也不得虚构关联、认证或背书。
- 项目的“五点卖点”是内部内容结构，不是 Google Merchant Center 的统一必填字段。

### 4.2 TikTok Ads 15/30 秒脚本

- 广告政策时长为 5–60 秒；项目仅生成 15 秒或 30 秒版本。
- 视频使用 9:16、1:1 或 16:9；Non-Spark In-Feed 优先采用推荐的 9:16。
- 广告应包含清晰音频，主要内容应保持动态，静态画面不得超过 50%。
- Non-Spark 规格支持 `.mp4`、`.mov`、`.mpeg`、`.3gp`、`.avi`，文件不超过 500 MB，码率不低于 516 kbps。
- Non-Spark 说明文字不支持可点击链接、`@` 或话题标签。核验所用官方页面没有给出统一字符上限，因此规则库不虚构具体数值。
- 商品、价格、促销、折扣、免责声明和条款须在广告与落地页之间保持一致。
- 禁止夸大/保证结果、误导性前后对比、虚假 CTA 或模拟界面。
- 显著编辑的媒体或 AIGC 须使用平台标签或清晰的自有披露方式。
- 电商落地页必须完整、可用、适合移动端，并展示当地法律要求的价格、配送、退换退款、条款和隐私信息。

### 4.3 通用社媒文案

- 固定输出 Hook、正文、CTA、事实绑定和 AI 使用状态。
- 不设置未经官方来源支持的“平台字符上限”。
- 价格、折扣、免邮、稀缺性、评论、认证和背书必须有事实依据，否则保持为空。
- 发布前必须先选择真实平台，再加载该平台的最新规则。

## 5. 美国与墨西哥市场叠加规则

| 市场 | 语言 | 货币 | 项目要求 |
|---|---|---|---|
| US | `en-US` | `USD` | 美式拼写；价格与落地页/结账页一致 |
| MX | `es-MX` | `MXN` | 使用面向墨西哥的自然西语；价格使用本地货币并与落地页一致 |

本地化只能改变表达，不能改变容量、成分、用法、市场价格或功效边界。平台页面所列要求也可能被当地法律、商品类目、账户配置或广告目标进一步收紧。

## 6. AI 内容标识处理

| 场景 | 规则 |
|---|---|
| Google AI 标题 | 使用 `structured_title`，`digital_source_type=trained_algorithmic_media` |
| Google AI 描述 | 使用 `structured_description`，`digital_source_type=trained_algorithmic_media` |
| Google AI 商品图 | 保留适用的 IPTC `DigitalSourceType` 元数据 |
| TikTok 显著编辑媒体/AIGC | 使用 TikTok AIGC 标签，或清晰的免责声明、说明文字、水印或贴纸 |
| Generic Social | 记录 `aigc_status`；选定真实平台后再判断披露方式 |

Google 的 AI 标签设置本身不保证满足特定地区法规；TikTok 对未披露的 AIGC 可能拒绝或限制投放。本项目因此把 AI 来源和披露状态设为显式字段，并保留人工复核。

## 7. 版本与维护

1. 每次规则核验后更新 `version`、`updated_at` 和每条规则的 `verified_date`。
2. 官方规则变化时保留旧版本，不覆盖既有评测所使用的规则集。
3. A/B 评测、生成记录和规则检查结果必须写入所用 `rule_set_id`。
4. 页面无法显示发布日期时记录“未显示”，不得估算或补写。
5. 若平台、市场、内容类型或广告目标发生变化，先扩充规则库再生成内容。

## 8. 使用边界

本规则库只用于内容生成前的约束和自动预检，不替代：

- Google、TikTok 或其他平台的最终审核；
- 美国、墨西哥及其他司法辖区的法律意见；
- 品牌方、合规人员或目标语言专业人员的最终确认；
- 广告账户、商品类目和落地页在真实环境中的检查。

规则预检通过不等于“平台已批准”“法律合规”或“保证发布”。LocalizeFlow 不自动发布内容。
