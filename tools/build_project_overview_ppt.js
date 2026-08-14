const pptxgen = require("pptxgenjs");
const path = require("path");

const pptx = new pptxgen();
pptx.layout = "LAYOUT_WIDE";
pptx.author = "LocalizeFlow";
pptx.subject = "跨境商品本地化 Copilot 项目概览";
pptx.title = "LocalizeFlow 项目概览";
pptx.company = "LocalizeFlow";
pptx.lang = "zh-CN";
pptx.theme = {
  headFontFace: "Microsoft YaHei",
  bodyFontFace: "Microsoft YaHei",
  lang: "zh-CN",
};
pptx.defineSlideMaster({
  title: "BASE",
  background: { color: "F5F7F6" },
  objects: [
    {
      text: {
        text: "LOCALIZEFLOW  ·  EVIDENCE-FIRST LOCALIZATION",
        options: {
          x: 0.55, y: 7.13, w: 6.7, h: 0.18,
          fontFace: "Arial", fontSize: 7.5, bold: true,
          color: "65736F", charSpacing: 1.2, margin: 0,
        },
      },
    },
    {
      text: {
        text: "2026",
        options: {
          x: 12.15, y: 7.13, w: 0.55, h: 0.18,
          fontFace: "Arial", fontSize: 7.5,
          color: "65736F", align: "right", margin: 0,
        },
      },
    },
  ],
  slideNumber: {
    x: 12.72, y: 7.13, w: 0.22, h: 0.18,
    fontFace: "Arial", fontSize: 7.5, color: "65736F",
    align: "right", margin: 0,
  },
});

const C = {
  ink: "0D2F2A",
  ink2: "173E37",
  green: "1E6658",
  mint: "DCEFE7",
  mint2: "B9DDD0",
  paper: "F5F7F6",
  white: "FFFFFF",
  text: "1D2926",
  muted: "65736F",
  amber: "E8B44F",
  amberSoft: "F8EDCF",
  coral: "D66456",
  coralSoft: "F7DDD8",
  line: "CED8D4",
  blue: "4A718A",
};

const root = path.resolve(__dirname, "..").replace(/\\/g, "/");
const img = {
  home: `${root}/assets/streamlit_demo_home.jpg`,
  quality: `${root}/assets/streamlit_demo_quality.jpg`,
  export: `${root}/assets/streamlit_demo_export.jpg`,
  eval: `${root}/assets/evaluation_ab_comparison.png`,
  value: `${root}/assets/business_value_cost_efficiency.png`,
};

function rect(slide, x, y, w, h, fill, radius = 0.14, line = null) {
  slide.addShape(
    radius > 0 ? pptx.ShapeType.roundRect : pptx.ShapeType.rect,
    {
      x, y, w, h,
      rectRadius: radius,
      fill: { color: fill },
      line: line ? { color: line, width: 1 } : { color: fill, transparency: 100 },
    }
  );
}

function text(slide, value, x, y, w, h, opts = {}) {
  const base = {
    x, y, w, h,
    fontFace: opts.fontFace || "Microsoft YaHei",
    fontSize: opts.fontSize || 18,
    color: opts.color || C.text,
    bold: opts.bold || false,
    margin: opts.margin === undefined ? 0 : opts.margin,
    breakLine: false,
    valign: opts.valign || "mid",
    align: opts.align || "left",
    fit: "shrink",
    paraSpaceAfterPt: opts.paraSpaceAfterPt || 0,
    isTextBox: true,
  };
  slide.addText(value, { ...base, ...opts });
}

function title(slide, kicker, headline, sub = "") {
  text(slide, kicker.toUpperCase(), 0.62, 0.36, 3.6, 0.25, {
    fontFace: "Arial", fontSize: 9, bold: true, color: C.green, charSpacing: 1.6,
  });
  text(slide, headline, 0.62, 0.68, 12.0, 0.55, {
    fontSize: 27, bold: true, color: C.ink,
  });
  if (sub) {
    text(slide, sub, 0.64, 1.28, 11.8, 0.32, {
      fontSize: 11.5, color: C.muted,
    });
  }
}

function badge(slide, value, x, y, w, fill = C.mint, color = C.ink) {
  rect(slide, x, y, w, 0.34, fill, 0.17);
  text(slide, value, x + 0.08, y + 0.02, w - 0.16, 0.29, {
    fontFace: "Arial", fontSize: 8.8, bold: true, color, align: "center",
  });
}

function stat(slide, value, label, x, y, w, fill = C.white, accent = C.green) {
  rect(slide, x, y, w, 1.05, fill, 0.16, C.line);
  text(slide, value, x + 0.16, y + 0.13, w - 0.32, 0.38, {
    fontFace: "Arial", fontSize: 24, bold: true, color: accent,
  });
  text(slide, label, x + 0.16, y + 0.57, w - 0.32, 0.30, {
    fontSize: 10.5, color: C.muted,
  });
}

function node(slide, n, name, x, y, w, color = C.white) {
  rect(slide, x, y, w, 0.62, color, 0.15, C.line);
  badge(slide, n, x + 0.10, y + 0.14, 0.48, C.ink, C.white);
  text(slide, name, x + 0.68, y + 0.08, w - 0.78, 0.44, {
    fontSize: 10.5, bold: true, color: C.ink,
  });
}

function arrow(slide, x, y, w, color = C.green) {
  slide.addShape(pptx.ShapeType.chevron, {
    x, y, w, h: 0.25,
    fill: { color },
    line: { color, transparency: 100 },
  });
}

function screenshot(slide, path, x, y, w, h, label) {
  rect(slide, x - 0.04, y - 0.04, w + 0.08, h + 0.30, C.white, 0.12, C.line);
  slide.addImage({ path, x, y, w, h, altText: label });
  text(slide, label, x + 0.08, y + h + 0.03, w - 0.16, 0.18, {
    fontSize: 8.5, bold: true, color: C.muted, align: "center",
  });
}

// Slide 1 — Business problem
{
  const s = pptx.addSlide("BASE");
  s.background = { color: C.ink };
  text(s, "LOCALIZEFLOW", 0.72, 0.65, 4.7, 0.35, {
    fontFace: "Arial", fontSize: 12, bold: true, color: C.mint2, charSpacing: 2.5,
  });
  text(s, "让跨境内容\n有据可查，再谈本地表达", 0.72, 1.25, 5.55, 1.55, {
    fontSize: 33, bold: true, color: C.white, breakLine: true, valign: "top",
    breakLineChars: "\n",
  });
  text(s, "面向美国英语与墨西哥西班牙语市场的商品本地化 Copilot", 0.75, 3.08, 5.3, 0.56, {
    fontSize: 15, color: "CFE2DB",
  });
  badge(s, "5 SKU", 0.75, 4.03, 1.18, C.mint, C.ink);
  badge(s, "2 MARKETS", 2.05, 4.03, 1.48, C.amberSoft, C.ink);
  badge(s, "30 A/B PAIRS", 3.65, 4.03, 1.72, C.coralSoft, C.ink);
  text(s, "核心问题", 0.75, 4.72, 1.2, 0.26, {
    fontSize: 10, bold: true, color: C.amber,
  });
  text(s, "直译难兼顾事实准确、语言自然、品牌一致与平台适配；生成后仍需高成本人工复核。", 0.75, 5.03, 5.35, 0.78, {
    fontSize: 15, color: C.white, valign: "top",
  });
  rect(s, 6.55, 0.62, 6.02, 5.96, C.white, 0.24);
  s.addImage({ path: img.home, x: 6.78, y: 0.87, w: 5.56, h: 3.13, altText: "LocalizeFlow Streamlit Demo 首页" });
  text(s, "不是“翻译器”", 6.92, 4.33, 2.1, 0.36, {
    fontSize: 16, bold: true, color: C.ink,
  });
  text(s, "事实 → 洞察 → 本地化 → 规则预检 → 人工终审", 6.92, 4.77, 5.1, 0.42, {
    fontSize: 13, color: C.green, bold: true,
  });
  text(s, "每条内容保留 fact_id / insight_id / rule_id 与版本记录。", 6.92, 5.34, 5.1, 0.52, {
    fontSize: 11.5, color: C.muted,
  });
  text(s, "产品原型 · 可本地运行 · 无需 API", 6.92, 6.05, 4.5, 0.24, {
    fontFace: "Arial", fontSize: 9.5, bold: true, color: C.coral,
  });
  s.addNotes("LocalizeFlow 不是一个只把中文翻成英文或西班牙文的工具。它把商品事实、消费者洞察、品牌语言和平台规则放进同一条可追溯工作流，重点解决跨境内容生成后的事实风险和复核成本。当前原型覆盖五个虚拟 SKU、美国和墨西哥两个市场，并且无需 API 即可本地演示。");
}

// Slide 2 — Users and scenario
{
  const s = pptx.addSlide("BASE");
  title(s, "02 · USERS & SCENARIO", "核心用户：跨境电商内容运营", "从收到中文商品资料，到交付可进入发布审核的多语言内容包");
  rect(s, 0.62, 1.82, 3.05, 4.73, C.ink, 0.22);
  badge(s, "PRIMARY USER", 0.92, 2.13, 1.44, C.amberSoft, C.ink);
  text(s, "内容运营 / 本地化项目助理", 0.92, 2.68, 2.45, 0.67, {
    fontSize: 20, bold: true, color: C.white, valign: "top",
  });
  text(s, "日常任务", 0.92, 3.60, 1.1, 0.25, {
    fontSize: 10, bold: true, color: C.mint2,
  });
  text(s, "• 接收中文商品资料\n• 编写多市场 Listing / 脚本 / 社媒文案\n• 核对功效、术语、语气和平台格式\n• 记录修改并交付后续审核", 0.92, 3.94, 2.40, 1.55, {
    fontSize: 12, color: C.white, breakLine: true, valign: "top",
  });
  text(s, "需要的是“带证据的草稿”，不是自动发布。", 0.92, 5.77, 2.42, 0.48, {
    fontSize: 11, bold: true, color: C.amber,
  });

  const steps = [
    ["01", "选商品", "查看事实与禁限表达"],
    ["02", "定任务", "市场、平台、受众、目标"],
    ["03", "看生成", "三类内容 + 来源引用"],
    ["04", "做质检", "事实 / 术语 / 规则门槛"],
    ["05", "修订导出", "复检、终审、CSV / JSON"],
  ];
  let x = 4.05;
  for (let i = 0; i < steps.length; i++) {
    const [n, h, d] = steps[i];
    rect(s, x, 2.05 + (i % 2) * 0.52, 1.58, 3.45, i === 4 ? C.mint : C.white, 0.18, C.line);
    badge(s, n, x + 0.15, 2.28 + (i % 2) * 0.52, 0.52, i === 4 ? C.ink : C.mint, i === 4 ? C.white : C.ink);
    text(s, h, x + 0.15, 3.07 + (i % 2) * 0.52, 1.27, 0.42, {
      fontSize: 15, bold: true, color: C.ink,
    });
    text(s, d, x + 0.15, 3.68 + (i % 2) * 0.52, 1.28, 0.90, {
      fontSize: 10.5, color: C.muted, valign: "top",
    });
    if (i < steps.length - 1) arrow(s, x + 1.62, 3.66, 0.28, C.green);
    x += 1.80;
  }
  text(s, "放行边界", 4.05, 6.15, 1.2, 0.26, {
    fontSize: 10, bold: true, color: C.coral,
  });
  text(s, "自动检查通过后仍显示“等待人工终审”；系统不发布、不代替法务，也不保证平台批准。", 5.20, 6.07, 7.3, 0.42, {
    fontSize: 11.2, color: C.text,
  });
  s.addNotes("目标用户是需要同时处理商品资料、多语言表达和平台格式的跨境内容运营。典型任务从选择商品和市场开始，系统生成三类内容并显示事实来源，运营人员完成质量检查、人工修订和终审后才能导出。这里的产品边界非常明确：系统交付的是带证据的候选稿，不负责自动发布，也不替代专业审核。");
}

// Slide 3 — Fact database
{
  const s = pptx.addSlide("BASE");
  title(s, "03 · PRODUCT FACT DATABASE", "先建立事实边界，再允许生成", "将产品描述拆成最小事实单元：来源、证据等级、市场范围与生成门控");
  rect(s, 0.62, 1.78, 6.15, 4.95, C.white, 0.22, C.line);
  badge(s, "MV-SERUM-001", 0.92, 2.04, 1.68, C.ink, C.white);
  text(s, "水衡保湿精华 · 30 mL", 0.92, 2.52, 3.9, 0.40, {
    fontSize: 19, bold: true, color: C.ink,
  });
  const facts = [
    ["F003", "容量", "30 mL", "不可变"],
    ["F008", "包装", "不透明 PP 按压泵瓶", "需核验"],
    ["F014", "配方", "透明质酸钠、泛醇", "谨慎复述"],
    ["F022", "肤感", "helps skin feel hydrated", "允许"],
    ["F038", "不黏腻", "缺少产品测试", "阻断"],
  ];
  let yy = 3.05;
  for (const [id, field, val, gate] of facts) {
    badge(s, id, 0.94, yy, 0.62, C.mint, C.ink);
    text(s, field, 1.72, yy - 0.01, 0.72, 0.34, {
      fontSize: 10.5, bold: true, color: C.muted,
    });
    text(s, val, 2.40, yy - 0.01, 2.85, 0.34, {
      fontSize: 11.2, color: C.text,
    });
    badge(s, gate, 5.38, yy, 0.96, gate === "阻断" ? C.coralSoft : C.amberSoft, gate === "阻断" ? C.coral : C.ink);
    yy += 0.62;
  }
  text(s, "每个声明都能追到具体字段，而不是只引用一份笼统产品说明。", 0.94, 6.30, 5.45, 0.27, {
    fontSize: 10.5, color: C.green, bold: true,
  });

  text(s, "一条内容如何被追溯", 7.24, 1.92, 3.0, 0.35, {
    fontSize: 16, bold: true, color: C.ink,
  });
  const trace = [
    ["CLAIM", "“Helps skin feel soft.”", C.white],
    ["FACT", "MV-SERUM-001-F022", C.mint],
    ["SOURCE", "SIM-CLAIM-SERUM-V1", C.amberSoft],
    ["GATE", "supported → 可进入规则检查", C.white],
  ];
  let ty = 2.54;
  for (let i = 0; i < trace.length; i++) {
    rect(s, 7.24, ty, 5.03, 0.79, trace[i][2], 0.16, C.line);
    badge(s, trace[i][0], 7.42, ty + 0.20, 0.78, C.ink, C.white);
    text(s, trace[i][1], 8.40, ty + 0.12, 3.58, 0.48, {
      fontFace: i === 1 || i === 2 ? "Arial" : "Microsoft YaHei",
      fontSize: 11.2, bold: i === 1, color: C.ink,
    });
    if (i < trace.length - 1) {
      s.addShape(pptx.ShapeType.downArrow, {
        x: 9.60, y: ty + 0.80, w: 0.30, h: 0.24,
        fill: { color: C.green }, line: { color: C.green, transparency: 100 },
      });
    }
    ty += 1.03;
  }
  badge(s, "事实错误优先级最高", 7.24, 6.48, 2.04, C.coralSoft, C.coral);
  text(s, "高分不能覆盖 unsupported / contradicted。", 9.48, 6.48, 2.8, 0.34, {
    fontSize: 9.8, color: C.muted,
  });
  s.addNotes("项目先把五个商品拆成结构化事实，而不是让模型直接阅读一整段产品说明。每条事实保存来源、证据等级、适用市场和生成门控。以精华为例，容量、配方和允许宣称都有明确边界，而“不黏腻”因为缺少产品测试会被阻断。生成后的每条声明都能追到 fact_id 和来源，事实错误也不能被较高的语言分数覆盖。");
}

// Slide 4 — Consumer insight
{
  const s = pptx.addSlide("BASE");
  title(s, "04 · CONSUMER INSIGHT", "消费者语言只决定“怎么说”，不能决定“产品有什么”", "开发样本用于选择角度；只有事实支持的洞察才可进入生成");
  rect(s, 0.62, 1.78, 3.45, 4.95, C.ink, 0.22);
  badge(s, "LANGUAGE PROXY", 0.92, 2.08, 1.60, C.amberSoft, C.ink);
  text(s, "探索样本", 0.92, 2.63, 1.6, 0.34, {
    fontSize: 18, bold: true, color: C.white,
  });
  stat(s, "50", "英语评论 · US 内容语言代理", 0.92, 3.16, 2.82, C.ink2, C.mint2);
  stat(s, "50", "西语评论 · MX 内容语言代理", 0.92, 4.40, 2.82, C.ink2, C.mint2);
  text(s, "没有评论者国家字段，因此不代表两国总体消费者趋势。", 0.92, 5.82, 2.76, 0.58, {
    fontSize: 10.5, color: C.amber,
  });

  text(s, "洞察进入工作流的三道门", 4.49, 1.93, 3.2, 0.35, {
    fontSize: 16, bold: true, color: C.ink,
  });
  const gates = [
    ["ELIGIBLE", "柔软、舒适的可感知肤感", "有 F022 / F024 支持", C.mint, C.green],
    ["STRATEGY ONLY", "强调日常护理步骤", "只影响结构与语气", C.amberSoft, C.ink],
    ["BLOCKED", "不黏腻、快速吸收", "只有评论信号，无产品测试", C.coralSoft, C.coral],
  ];
  let gy = 2.52;
  for (const [g, insight, rule, fill, color] of gates) {
    rect(s, 4.49, gy, 8.05, 1.00, fill, 0.18, C.line);
    badge(s, g, 4.73, gy + 0.31, 1.35, C.ink, C.white);
    text(s, insight, 6.34, gy + 0.16, 3.05, 0.32, {
      fontSize: 13.5, bold: true, color,
    });
    text(s, rule, 6.34, gy + 0.53, 4.90, 0.26, {
      fontSize: 10.2, color: C.muted,
    });
    gy += 1.27;
  }
  rect(s, 4.49, 6.28, 8.05, 0.45, C.white, 0.14, C.line);
  text(s, "洞察 → 事实匹配 → 品牌限定语 → 生成；任何一步缺失都不能把偏好改写成功效。", 4.72, 6.35, 7.56, 0.25, {
    fontSize: 10.8, bold: true, color: C.green, align: "center",
  });
  s.addNotes("消费者洞察在这里是一种语言与策略资源，而不是产品证据。项目人工通读了五十条英语和五十条西语评论，但源数据没有评论者国家，所以只能作为内容语言代理。洞察分为 eligible、strategy only 和 blocked 三类。比如柔软肤感有商品事实支持，可以谨慎生成；不黏腻和快速吸收没有产品测试，因此即使评论中出现，也不能写成产品结论。");
}

// Slide 5 — AI workflow
{
  const s = pptx.addSlide("BASE");
  title(s, "05 · MULTI-NODE WORKFLOW", "七节点工作流：把生成、核验与人工责任拆开", "统一 JSON envelope 保存输入引用、资产版本、节点 attempt、错误位置与人工修改");
  node(s, "N01", "Fact\nExtractor", 0.62, 2.05, 1.46, C.white);
  arrow(s, 2.11, 2.24, 0.28);
  node(s, "N02", "Campaign\nPlanner", 2.43, 2.05, 1.58, C.white);
  arrow(s, 4.04, 2.24, 0.28);
  node(s, "N03", "Localizer", 4.36, 2.05, 1.50, C.white);
  arrow(s, 5.89, 2.24, 0.28);
  node(s, "N04", "Content\nGenerator", 6.21, 2.05, 1.64, C.mint);
  arrow(s, 7.88, 2.24, 0.28);
  node(s, "N05", "Fact\nChecker", 8.20, 2.05, 1.48, C.amberSoft);
  arrow(s, 9.71, 2.24, 0.28);
  node(s, "N06", "Rule\nChecker", 10.03, 2.05, 1.48, C.amberSoft);
  arrow(s, 11.54, 2.24, 0.28);
  node(s, "N07", "Score", 11.86, 2.05, 1.30, C.white);

  rect(s, 0.62, 3.15, 4.02, 2.82, C.white, 0.20, C.line);
  badge(s, "TRACEABILITY", 0.90, 3.45, 1.55, C.ink, C.white);
  text(s, "run_id  ·  trace_id  ·  version_id", 0.90, 4.04, 3.30, 0.33, {
    fontFace: "Arial", fontSize: 13, bold: true, color: C.green,
  });
  text(s, "每个节点输出统一 envelope；重试创建新 attempt，人工修改创建新版本，旧内容和失败记录不覆盖。", 0.90, 4.55, 3.36, 0.88, {
    fontSize: 11.2, color: C.text, valign: "top",
  });

  rect(s, 4.88, 3.15, 3.60, 2.82, C.coralSoft, 0.20, C.coral);
  badge(s, "HARD GATE", 5.16, 3.45, 1.20, C.coral, C.white);
  text(s, "高风险事实错误\n平台硬规则失败", 5.16, 4.02, 2.80, 0.70, {
    fontSize: 17, bold: true, color: C.coral, breakLine: true,
  });
  text(s, "立即阻断导出；不能靠质量总分放行。", 5.16, 5.00, 2.84, 0.48, {
    fontSize: 10.8, color: C.text,
  });

  rect(s, 8.72, 3.15, 4.16, 2.82, C.mint, 0.20, C.green);
  badge(s, "HUMAN LOOP", 9.00, 3.45, 1.32, C.green, C.white);
  text(s, "编辑 → 新版本 → 重新执行 N05 / N06", 9.00, 4.01, 3.45, 0.65, {
    fontSize: 15, bold: true, color: C.ink,
  });
  text(s, "自动检查全部通过后，仍必须由人工明确批准才能导出。", 9.00, 4.91, 3.45, 0.56, {
    fontSize: 10.8, color: C.text,
  });

  rect(s, 0.62, 6.23, 12.26, 0.48, C.ink, 0.14);
  text(s, "EXPORT GATE  =  fact_check pass  +  rule_check pass  +  high-risk errors 0  +  human approved", 0.84, 6.32, 11.82, 0.25, {
    fontFace: "Arial", fontSize: 10.5, bold: true, color: C.white, align: "center",
  });
  s.addNotes("核心工作流拆成七个单一职责节点，从事实加载、策略选择、本地化、内容生成，到事实核验、规则检查和质量评分。所有节点使用统一 JSON envelope 保存输入引用、资产版本、运行 attempt 和错误位置。高风险事实错误或平台硬规则失败会直接阻断。人工修改后必须创建新版本，并重新运行事实与规则检查，最后仍需人工批准。");
}

// Slide 6 — Product demo
{
  const s = pptx.addSlide("BASE");
  title(s, "06 · PRODUCT DEMO", "一个离线可复现的五步编辑台", "冻结评测内容 + 确定性模板：无需 API，也能完整演示生成、核验、修订与导出");
  screenshot(s, img.home, 0.62, 1.87, 4.00, 2.25, "① 商品资料 / 营销任务");
  screenshot(s, img.quality, 4.67, 1.87, 4.00, 2.25, "② 质量检查 / 风险定位");
  screenshot(s, img.export, 8.72, 1.87, 4.00, 2.25, "③ 版本对比 / 人工终审 / 导出");
  const demoSteps = [
    ["选择", "5 SKU · US/MX · 3 内容类型"],
    ["生成", "Listing + TikTok + 社媒内容包"],
    ["追溯", "每条声明显示事实来源"],
    ["复检", "人工修改后重新执行质量门槛"],
    ["导出", "通过终审后开放 CSV / JSON"],
  ];
  let dx = 0.62;
  for (let i = 0; i < demoSteps.length; i++) {
    rect(s, dx, 4.78, 2.27, 1.33, i === 4 ? C.ink : C.white, 0.17, i === 4 ? C.ink : C.line);
    badge(s, `0${i + 1}`, dx + 0.15, 4.96, 0.49, i === 4 ? C.amber : C.mint, C.ink);
    text(s, demoSteps[i][0], dx + 0.76, 4.92, 1.24, 0.35, {
      fontSize: 14, bold: true, color: i === 4 ? C.white : C.ink,
    });
    text(s, demoSteps[i][1], dx + 0.15, 5.43, 1.95, 0.42, {
      fontSize: 9.3, color: i === 4 ? "CFE2DB" : C.muted, align: "center",
    });
    dx += 2.49;
  }
  badge(s, "DEMO BOUNDARY", 0.62, 6.39, 1.47, C.coralSoft, C.coral);
  text(s, "不调用模型 API · 不连接发布平台 · 不代表法务或平台批准", 2.28, 6.38, 6.9, 0.30, {
    fontSize: 10.5, bold: true, color: C.muted,
  });
  s.addNotes("Demo 把核心链路压缩成五个页面。演示时可以选择商品和市场，一次查看 Listing、短视频和社媒内容，随后进入质量检查定位事实和语言问题。人工修改后系统会重新复检，只有勾选最终确认才开放 CSV 和 JSON。为了保证项目可复现，当前使用冻结内容和确定性模板，不调用 API，也不连接真实发布平台。");
}

// Slide 7 — Evaluation and business value
{
  const s = pptx.addSlide("BASE");
  title(s, "07 · EVALUATION & VALUE", "30 组盲评：质量更高，复核负担更低", "真实评测与情景估算分层呈现；不把估算数字包装成已验证成果");
  rect(s, 0.62, 1.79, 5.18, 3.42, C.white, 0.20, C.line);
  text(s, "七维总体均分（1–5）", 0.92, 2.05, 2.65, 0.32, {
    fontSize: 15, bold: true, color: C.ink,
  });
  s.addChart(
    pptx.ChartType.bar,
    [{ name: "平均分", labels: ["Baseline", "LocalizeFlow"], values: [2.78, 4.20] }],
    {
      x: 0.94, y: 2.55, w: 4.50, h: 2.18,
      catAxisLabelFontFace: "Arial",
      catAxisLabelFontSize: 11,
      valAxisLabelFontFace: "Arial",
      valAxisLabelFontSize: 9,
      valAxisMinVal: 0,
      valAxisMaxVal: 5,
      valAxisMajorUnit: 1,
      showLegend: false,
      showTitle: false,
      showValue: true,
      dataLabelPosition: "outEnd",
      dataLabelColor: C.ink,
      chartColors: [C.green],
      showCatName: false,
      showValAxisTitle: false,
      showCatAxisTitle: false,
      showValue: true,
      showGridLines: true,
      gridLine: { color: "E2E8E5", width: 1 },
      border: { pt: 0, color: C.white },
    }
  );
  badge(s, "ACTUAL BLIND REVIEW", 0.94, 4.74, 1.76, C.mint, C.ink);
  text(s, "n = 30 pairs / 60 candidates", 2.90, 4.76, 2.34, 0.24, {
    fontFace: "Arial", fontSize: 9.5, color: C.muted,
  });

  stat(s, "−61.5%", "平均修改次数 · 3.63 → 1.40", 6.08, 1.79, 3.04, C.mint, C.green);
  stat(s, "−25.8%", "平均审核时间 · 6.33 → 4.70 分钟", 9.34, 1.79, 3.54, C.mint, C.green);
  stat(s, "+26.7 pp", "事实通过率 · 40.0% → 66.7%", 6.08, 3.08, 3.04, C.white, C.green);
  stat(s, "30 / 30", "A/B 配对中 LocalizeFlow 胜出", 9.34, 3.08, 3.54, C.white, C.green);

  rect(s, 6.08, 4.42, 6.80, 1.46, C.coralSoft, 0.18, C.coral);
  badge(s, "KNOWN FAILURE", 6.36, 4.72, 1.48, C.coral, C.white);
  text(s, "代表性 SKU 的事实错误率仍为 33.3%", 8.08, 4.63, 4.35, 0.36, {
    fontSize: 14.5, bold: true, color: C.coral,
  });
  text(s, "主要来自包装字段补全；项目保留失败案例，不用平均分掩盖。", 8.08, 5.08, 4.35, 0.36, {
    fontSize: 10.2, color: C.text,
  });

  rect(s, 0.62, 6.12, 12.26, 0.60, C.amberSoft, 0.16, C.amber);
  badge(s, "SCENARIO", 0.84, 6.25, 1.02, C.amber, C.ink);
  text(s, "84.4% 仅为 AI 估算纯人工时间 + 实际复核/系统记录的情景结果，不是人工实测，不能表述为已验证效率提升。", 2.06, 6.20, 10.45, 0.39, {
    fontSize: 10.8, bold: true, color: C.ink,
  });
  s.addNotes("评测采用三十组 A/B、六十条匿名候选。LocalizeFlow 的七维总体均分从二点七八提高到四点二，修改次数减少百分之六十一点五，审核时间减少百分之二十五点八，事实通过率提升二十六点七个百分点。与此同时，代表性 SKU 的事实错误率仍然是百分之三十三点三，主要与包装字段有关。业务报告里的百分之八十四点四只是一项 AI 情景估算，不是人工实测，不能表述为已验证效率提升。");
}

// Slide 8 — Limitations and next
{
  const s = pptx.addSlide("BASE");
  title(s, "08 · LIMITS & NEXT", "把局限写清楚，也把下一步做成路线图", "这是一套可演示、可验证的 MVP，不是已上线的自动发布系统");
  text(s, "当前局限", 0.62, 1.85, 2.0, 0.35, {
    fontSize: 17, bold: true, color: C.ink,
  });
  const limits = [
    ["样本", "1 品牌 / 5 SKU，不能外推到其他品类"],
    ["评审", "单评审者，无法计算评审者间一致性"],
    ["洞察", "缺少国家字段，只能作为语言代理"],
    ["模型", "离线确定性 Demo，未测在线延迟与成本"],
    ["合规", "规则预检不代表平台或法务批准"],
  ];
  let ly = 2.38;
  for (const [tag, desc] of limits) {
    rect(s, 0.62, ly, 5.24, 0.67, C.white, 0.14, C.line);
    badge(s, tag, 0.79, ly + 0.16, 0.72, C.coralSoft, C.coral);
    text(s, desc, 1.73, ly + 0.10, 3.84, 0.45, {
      fontSize: 10.8, color: C.text,
    });
    ly += 0.82;
  }

  text(s, "下一步", 6.25, 1.85, 2.0, 0.35, {
    fontSize: 17, bold: true, color: C.ink,
  });
  const roadmap = [
    ["01", "事实层", "拆分包装材质/结构字段；缺失即阻断"],
    ["02", "评测层", "增加双评审者与目标国家本地样本"],
    ["03", "模型层", "配置 API 后记录结构成功率、延迟、费用"],
    ["04", "产品层", "接入真实商品后台前先完成权限与审计设计"],
  ];
  let ry = 2.38;
  for (let i = 0; i < roadmap.length; i++) {
    const [n, head, desc] = roadmap[i];
    rect(s, 6.25, ry, 6.63, 0.83, i === 0 ? C.mint : C.white, 0.16, C.line);
    badge(s, n, 6.46, ry + 0.24, 0.52, i === 0 ? C.ink : C.mint, i === 0 ? C.white : C.ink);
    text(s, head, 7.22, ry + 0.10, 0.84, 0.32, {
      fontSize: 12.5, bold: true, color: C.ink,
    });
    text(s, desc, 8.12, ry + 0.10, 4.40, 0.49, {
      fontSize: 10.5, color: C.muted,
    });
    ry += 1.03;
  }

  rect(s, 6.25, 6.52, 6.63, 0.35, C.ink, 0.14);
  text(s, "API 接入前先提醒配置；密钥只进入本地 .env，不进代码、文档或截图。", 6.49, 6.57, 6.16, 0.22, {
    fontSize: 9.5, bold: true, color: C.white, align: "center",
  });

  rect(s, 0.62, 6.52, 5.24, 0.35, C.green, 0.14);
  text(s, "PROJECT PACKAGE  ·  README  ·  DEMO  ·  PPT  ·  VIDEO  ·  TRACEABLE METRICS", 0.82, 6.57, 4.84, 0.22, {
    fontFace: "Arial", fontSize: 8.4, bold: true, color: C.white, align: "center",
  });
  s.addNotes("这个项目的价值不只在于展示结果，也在于把局限和责任边界写清楚。当前样本规模小、只有一位评审者，洞察也没有国家字段，在线模型的延迟和成本尚未测试。下一步会先补强包装事实字段和多评审评测，然后在配置 API 后记录真实模型调用。任何密钥都只进入本地环境变量，不写入代码、文档或截图。");
}

pptx.writeFile({ fileName: `${root}/demo/LocalizeFlow_Project_Overview.pptx` });
