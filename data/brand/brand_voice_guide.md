# Mirevane Botanics 品牌语调与本地化指南

> 版本：v1.0  
> 日期：2026-07-28  
> 适用市场：美国英语市场、墨西哥西班牙语市场  
> 数据性质：LocalizeFlow 产品原型模拟规则

## 1. 品牌核心

Mirevane Botanics 用清楚、克制的语言介绍适合日常使用的基础护肤产品。品牌不依赖“奇迹”“治愈”“无毒”等刺激性承诺，而是让消费者知道产品是什么、如何使用，以及在商品事实允许范围内可能带来的使用感受。

### 一句话品牌声音

> Calm clarity for everyday care.  
> Claridad y calma para el cuidado diario.

这句话是品牌表达方向，不是商品功效宣称。

## 2. 品牌人格

| 维度 | 强度 | 说明 |
|---|---:|---|
| 温和 | 5/5 | 尊重消费者，不制造焦虑或羞耻 |
| 清晰 | 5/5 | 优先使用短句、具体名词和明确步骤 |
| 可信 | 5/5 | 只使用有 `fact_id` 支持的事实 |
| 简洁 | 4/5 | 删除空泛修饰，但保留必要限定条件 |
| 亲近 | 3/5 | 使用自然第二人称，不刻意装可爱 |
| 权威 | 2/5 | 提供信息而非模仿医生或监管机构口吻 |
| 兴奋 | 1/5 | 不使用高压、全大写或过多感叹号 |

## 3. 全局写作原则

### 应该

- 先说明商品类型和已验证特征，再说明谨慎功效；
- 使用“helps / ayuda a”“skin feels / la piel se siente”等限定表达；
- 说明容量、用法和包装时保持数字、单位与事实库一致；
- 对条件性信息保留限定语，例如“recyclability depends on local facilities”；
- 保留人工审核空间，不把自动评分描述成合规批准；
- 每个关键商品陈述关联至少一个 `fact_id`。

### 不应该

- 把商品写成药品、医疗器械或临床方案；
- 使用治疗、预防疾病或改变人体结构/功能的表达；
- 使用“miracle”“perfect”“guaranteed”“milagroso”“perfecto”“garantizado”等绝对化词；
- 使用未经验证的“hypoallergenic”“dermatologist tested”“FDA approved”“aprobado por COFEPRIS”；
- 使用宽泛且无证据的“clean”“non-toxic”“eco-friendly”“natural”；
- 编造消费者评价、认证、折扣、库存紧张或销售排名；
- 用消费者洞察创造商品事实。

## 4. 美国英语市场语调

### 4.1 语言特征

- 使用美式英语拼写；
- 使用 `you / your skin`，语气直接但不命令；
- 标题优先呈现商品类型和可验证特征；
- 卖点采用“特征 + 谨慎体验”结构；
- 句子尽量控制在一个核心信息内；
- 避免堆叠形容词和伪科学表达。

### 4.2 推荐句式

```text
Fragrance-free hydration for a simple daily routine.

Helps skin feel hydrated without adding fragrance.

Apply 1–2 pumps after cleansing, then follow with moisturizer.

Packaged in a 30 mL airless pump bottle.
```

### 4.3 不推荐句式

```text
Miracle hydration that repairs your skin barrier instantly.

The cleanest, safest serum for every skin type.

Clinically proven to erase fine lines.

FDA-approved natural skincare.
```

### 4.4 英语表达约束

| 场景 | 推荐 | 避免 |
|---|---|---|
| 谨慎功效 | `helps skin feel hydrated` | `deeply hydrates for 72 hours` |
| 无香 | `fragrance-free`、`made without added fragrance` | `allergy-free` |
| 日常使用 | `for a simple daily routine` | `safe for daily use by everyone` |
| 成分 | `made with glycerin and panthenol` | `powered by miracle actives` |
| 包装 | `recyclability depends on local facilities` | `100% eco-friendly` |

## 5. 墨西哥西班牙语市场语调

### 5.1 语言特征

- 使用面向墨西哥消费者的中性西班牙语；
- 使用 `tú / tu piel`，不用西班牙本土复数 `vosotros`；
- 保留必要重音符号，如 `sérum`、`hidratación`、`aplícalo`；
- 优先自然表达，不逐词复制英语语序；
- 使用 `ayuda a`、`deja la piel con sensación de...` 等谨慎句式；
- 价格单位写作 `MXN`，容量保留 `mL`；
- 对首次出现的专业成分可使用消费者易懂名称，成分表仍以标准名称为准。

### 5.2 推荐句式

```text
Hidratación sin fragancia añadida para una rutina sencilla.

Ayuda a que la piel se sienta hidratada y suave.

Después de limpiar el rostro, aplica de 1 a 2 dosis y continúa con tu crema hidratante.

Presentación de 30 mL con envase de bomba.
```

### 5.3 不推荐句式

```text
Hidratación milagrosa que repara la barrera de tu piel al instante.

El sérum más limpio y seguro para todo tipo de piel.

Clínicamente comprobado para borrar las líneas de expresión.

Producto natural aprobado por COFEPRIS.
```

### 5.4 西班牙语表达约束

| 场景 | 推荐 | 避免 |
|---|---|---|
| 保湿精华 | `sérum hidratante` | 将 `serum` 无重音作为正式首选词 |
| 无添加香精 | `sin fragancia añadida` | `libre de alergias` |
| 谨慎功效 | `ayuda a que la piel se sienta hidratada` | `hidrata durante 72 horas` |
| 日常护理 | `para tu rutina diaria` | `seguro para todas las personas` |
| 使用量 | `de 1 a 2 dosis` | 生硬直译 `1–2 bombas` |
| 面霜 | `crema hidratante facial` | 仅写含义模糊的 `crema` |
| 套装 | `set básico de cuidado facial` | `kit aprobado para viajar` |

## 6. 英西语人格对齐

| 表达意图 | 英语 | 墨西哥西班牙语 |
|---|---|---|
| 温和说明 | `A gentle step for your daily routine.` | `Un paso suave para tu rutina diaria.` |
| 谨慎保湿 | `Helps skin feel hydrated.` | `Ayuda a que la piel se sienta hidratada.` |
| 无香 | `Made without added fragrance.` | `Sin fragancia añadida.` |
| 使用顺序 | `Apply after cleansing.` | `Aplícalo después de limpiar el rostro.` |
| 条件性回收 | `Recyclability depends on local facilities.` | `La posibilidad de reciclaje depende de las instalaciones locales.` |
| 信息不足 | `This information has not been verified.` | `Esta información no ha sido verificada.` |

两种语言允许句法和节奏不同，但不得改变容量、成分、使用方法、价格、适用人群和功效边界。

## 7. 证据等级对应语气

| 证据等级 | 内容处理 | 语言要求 |
|---|---|---|
| A | 可作为事实使用 | 精确复述，保留数值与单位 |
| B | 可谨慎使用 | 必须使用 `helps` / `ayuda a` 或感受型表达 |
| C | 不得直接输出 | 仅作为待消费者洞察验证的内容方向 |
| D | 阻断输出 | 检测原词、变体和语义等价表达 |

### B 级功效改写模式

```text
中文：帮助肌肤感觉水润
EN：Helps skin feel hydrated.
ES-MX：Ayuda a que la piel se sienta hidratada.
```

禁止升级为：

```text
EN：Repairs the skin barrier and delivers 72-hour hydration.
ES-MX：Repara la barrera cutánea y brinda hidratación por 72 horas.
```

## 8. 平台语调变化

本节只规定品牌允许的语调变化，不替代平台硬性规则库。

| 内容类型 | 允许变化 | 不可变化 |
|---|---|---|
| 商品 Listing | 信息密度较高，先写规格与特征 | 事实、单位、功效边界 |
| TikTok 脚本 | 更口语化，可使用短句和场景化开头 | 不得虚构亲测、评价、折扣或稀缺性 |
| 社媒文案 | 可增加节奏和一个轻量 CTA | 不得制造皮肤焦虑或使用绝对化承诺 |
| 广告标题 | 更短、更直接 | 不得删除必要限定词以换取冲击力 |
| CTA | 可使用邀请式动词 | 不得使用虚假倒计时或高压购买话术 |

## 9. CTA 指南

### 推荐

| 英语 | 西班牙语 |
|---|---|
| `Explore the routine` | `Conoce la rutina` |
| `See product details` | `Consulta los detalles` |
| `Build your simple routine` | `Arma una rutina sencilla` |
| `Learn how to use it` | `Descubre cómo usarlo` |

### 避免

| 英语 | 西班牙语 | 原因 |
|---|---|---|
| `Buy now before it’s gone` | `Compra antes de que se agote` | 未验证稀缺性 |
| `Transform your skin today` | `Transforma tu piel hoy` | 结果承诺过强 |
| `Get perfect skin` | `Consigue una piel perfecta` | 绝对化且制造焦虑 |
| `Doctors recommend it` | `Recomendado por médicos` | 未提供专业背书 |

## 10. 语言与文化检查清单

### 英语

- [ ] 使用美式拼写；
- [ ] 不出现医疗、治疗或保证性表达；
- [ ] `fragrance-free` 不被扩大为 `allergy-free`；
- [ ] 数字与单位和事实库一致；
- [ ] 一个句子只承载一个主要卖点。

### 墨西哥西班牙语

- [ ] 使用 `tú` 体系，不出现 `vosotros`；
- [ ] `sérum`、`hidratación` 等重音正确；
- [ ] 使用 `de 1 a 2 dosis` 等自然用量表达；
- [ ] 避免英语语序和不自然名词堆叠；
- [ ] 不把 `fragrance-free` 扩大为 `libre de alergias`；
- [ ] 保留 `ayuda a` 等必要限定；
- [ ] 数字、单位和目标市场价格一致。

## 11. 机器可读规则

后续提示词或程序可直接加载以下结构：

```json
{
  "brand": "Mirevane Botanics",
  "voice": ["gentle", "clear", "trustworthy", "concise"],
  "markets": {
    "US": {
      "language": "en-US",
      "pronoun": "you",
      "style": "direct, calm, experience-focused"
    },
    "MX": {
      "language": "es-MX",
      "pronoun": "tú",
      "style": "natural, clear, warm but restrained",
      "avoid_regional_form": ["vosotros"]
    }
  },
  "claim_language": {
    "B": {
      "en": ["helps", "skin feels"],
      "es": ["ayuda a", "la piel se siente"]
    },
    "C": "not_directly_usable",
    "D": "blocked"
  },
  "punctuation": {
    "max_exclamation_marks": 1,
    "all_caps": false,
    "emoji_default": false
  },
  "human_review_required": true
}
```

## 12. 权威来源与使用边界

- RAE 在 DLE 23.8 中收录了 `sérum`，并将 `suero` 关联为同义用法。本项目在墨西哥消费者文案中首选 `sérum hidratante`，允许 `suero facial hidratante` 作为清晰变体：  
  https://dle.rae.es/docs/Novedades_DLE_23.8-Seleccion.pdf
- 美国 FDA 说明，化妆品若宣称治疗或预防疾病，或影响身体结构和功能，可能按药品监管；因此本项目阻断 `cure`、`treat eczema`、`repair skin structure` 等表达：  
  https://www.fda.gov/cosmetics/cosmetics-labeling/cosmetics-labeling-claims
- FDA 明确化妆品不得暗示 `FDA Approved`：  
  https://www.fda.gov/cosmetics/cosmetics-labeling/cosmetics-labeling-regulations
- 美国 FTC Green Guides 不建议使用无明确依据的宽泛 `green`、`eco-friendly`、`non-toxic` 等环境或安全表达，并要求按回收设施可用性限定可回收声明：  
  https://www.ftc.gov/business-guidance/resources/environmental-claims-summary-green-guides
- 墨西哥化妆品标签的正式要求应依据适用版本的 NOM-141 和官方页面单独维护；本指南不替代法律或平台审核。
