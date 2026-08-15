"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import factsData from "./data/product_facts.json";
import contentData from "./data/content_library.json";
import packagingData from "./data/packaging_facts.json";

type Market = "US" | "MX";
type ContentType = "product_listing" | "short_video_script" | "social_ad_copy";
type Status = "pass" | "warning" | "fail";
type Fact = {
  fact_id: string;
  sku: string;
  attribute: string;
  value: string | number;
  unit: string | null;
  evidence_level: string;
  source: string;
  allowed_expression: string[];
  prohibited_expression: string[];
  generation_policy: string;
  status: string;
};
type ContentGroup = {
  sku: string;
  market: Market;
  language: string;
  content_type: ContentType;
  versions: { baseline: string; localizeflow: string };
};
type QualityCheck = { id: string; name: string; status: Status; detail: string; suggestion?: string; matchedText?: string; replacement?: string; factIds?: string[]; source?: string };
type PackagingRecord = { fact_id: string; source: string; capacity: number[]; container_type?: string[]; material?: string[]; dispenser?: string[]; closure?: string[]; cap_material?: string[]; inner_lid?: string[]; transparency?: string[]; outer_container?: string[] };

const PRODUCTS: Record<string, string> = {
  "MV-CLEAN-001": "云柔氨基酸洁面乳 · Facial Cleanser",
  "MV-SERUM-001": "水衡保湿精华 · Hydrating Serum",
  "MV-CREAM-001": "静润无香面霜 · Face Moisturizer",
  "MV-HAND-001": "柔护无香护手霜 · Hand Cream",
  "MV-KIT-001": "轻行基础护肤套装 · Travel Skincare Set",
};

const MARKET_META = {
  US: { label: "美国 · English (US)", language: "en-US", currency: "USD" },
  MX: { label: "墨西哥 · Español (MX)", language: "es-MX", currency: "MXN" },
} as const;

const TYPE_META: Record<ContentType, { label: string; platform: string }> = {
  product_listing: { label: "商品 Listing", platform: "Google Merchant Center" },
  short_video_script: { label: "15 秒短视频脚本", platform: "TikTok Ads" },
  social_ad_copy: { label: "社媒广告文案", platform: "Generic Social" },
};

const STEPS = ["商品资料", "营销任务", "生成结果", "质量检查", "版本与导出"];
const STEP_META = [
  { purpose: "核对来源事实", time: "约 30 秒" },
  { purpose: "定义市场与任务", time: "约 30 秒" },
  { purpose: "查看证据绑定结果", time: "约 40 秒" },
  { purpose: "定位并修复风险", time: "约 60 秒" },
  { purpose: "人工签署与导出", time: "约 20 秒" },
];
const TONES = ["温和", "可信", "清晰", "克制"];

const facts = factsData.facts as Fact[];
const groups = contentData.groups as ContentGroup[];
const packaging = packagingData.products as Record<string, PackagingRecord>;

const PACKAGING_TERMS = {
  container_type: { bottle: ["bottle", "botella", "envase PET", "envase opaco de PP", "envase de PP"], jar: ["jar", "tarro", "frasco"], tube: ["tube", "tubo"] },
  material: { PET: ["PET pump bottle", "envase PET", "botella PET"], PP: ["PP pump bottle", "PP jar", "botella de PP", "tarro de PP", "envase opaco de PP", "envase de PP"], aluminum: ["aluminum", "aluminium", "aluminio"], glass: ["glass", "vidrio", "cristal"] },
  dispenser: { pump: ["pump bottle", "bomba", "con bomba"] },
  closure: { "screw cap": ["screw cap", "tapa roscada", "tapón de rosca"], "flip cap": ["flip cap", "tapa abatible"] },
  cap_material: { PP: ["PP cap", "cap made of PP", "tapa de PP", "tapón de PP"], glass: ["glass cap", "tapa de vidrio"] },
  inner_lid: { present: ["inner lid", "tapa interior"] },
  transparency: { opaque: ["opaque", "opaco", "opaca"], transparent: ["transparent", "clear bottle", "transparente"] },
  outer_container: { "paper box": ["paper box", "caja de papel", "carton box", "caja de cartón"] },
} as const;

function firstMatch(text: string, pattern: RegExp) { return text.match(pattern)?.[0]; }

function packagingChecks(text: string, sku: string): QualityCheck[] {
  const record = packaging[sku];
  const issues: QualityCheck[] = [];
  for (const [field, candidates] of Object.entries(PACKAGING_TERMS)) {
    for (const [candidate, terms] of Object.entries(candidates)) {
      const hit = terms.find((term) => new RegExp(`\\b${term}\\b`, "i").test(text));
      if (!hit) continue;
      const allowed = record[field as keyof PackagingRecord] as string[] | undefined;
      if (!allowed?.includes(candidate)) {
        const expected = allowed?.join(" / ") ?? "unknown（无证据）";
        issues.push({ id: `packaging-${field}-${candidate}`, name: "包装事实", status: "fail", matchedText: hit, replacement: allowed?.length === 1 ? allowed[0] : "", detail: `“${hit}”与 ${field} 字段冲突；已核实值：${expected}。`, suggestion: allowed?.length === 1 ? `替换为 ${allowed[0]} 后重新检查。` : "删除无证据表述，或先补充经核验的字段。", factIds: allowed ? [record.fact_id] : [], source: allowed ? record.source : "" });
      }
    }
  }
  for (const match of text.matchAll(/(?<!\d)(\d+(?:\.\d+)?)\s*m[lL]\b/g)) {
    if (!record.capacity.includes(Number(match[1]))) issues.push({ id: `packaging-capacity-${match.index}`, name: "包装事实", status: "fail", matchedText: match[0], replacement: record.capacity.length === 1 ? `${record.capacity[0]} mL` : "", detail: `“${match[0]}”与容量字段冲突；允许值：${record.capacity.join(" / ")} mL。`, suggestion: record.capacity.length === 1 ? `替换为 ${record.capacity[0]} mL。` : "按组件事实核对容量。", factIds: [record.fact_id], source: record.source });
  }
  return issues.length ? issues : [{ id: "packaging-pass", name: "包装事实", status: "pass", detail: "包装表述与字段级事实一致。", factIds: [record.fact_id], source: record.source }];
}

function valueOf(fact?: Fact) {
  if (!fact) return "—";
  return `${fact.value}${fact.unit ? ` ${fact.unit}` : ""}`;
}

function parseContent(text: string, type: ContentType) {
  const lines = text.split("\n").map((line) => line.trim()).filter(Boolean);
  if (type === "product_listing") {
    return {
      title: lines.find((line) => /^(TITLE|TÍTULO):/.test(line))?.replace(/^[^:]+:\s*/, "") ?? "",
      bullets: lines.filter((line) => /^(BULLET|PUNTO)\s+\d+\s*:/.test(line)).map((line) => line.replace(/^[^:]+:\s*/, "")),
      description: lines.find((line) => /^(DESCRIPTION|DESCRIPCIÓN):/.test(line))?.replace(/^[^:]+:\s*/, "") ?? "",
    };
  }
  return { title: "", bullets: lines, description: "" };
}

function inspectContent(text: string, type: ContentType, market: Market, sku: string) {
  const checks: QualityCheck[] = [];
  const prohibitedPattern = /\b(cure|cures|clinically proven|guaranteed|miracle|repair|repairs)\b|repara(?:r|n|s)?|all of your skincare needs|todas tus necesidades/i;
  const prohibited = firstMatch(text, prohibitedPattern);
  checks.push({
    id: "fact-boundary",
    name: "事实与功效边界",
    status: prohibited ? "fail" : "pass",
    detail: prohibited ? "发现医疗化、保证性或超出证据边界的表述。" : "未发现医疗化、全能承诺或保证性功效。",
    suggestion: prohibited ? "改为 helps skin feel… / ayuda a que la piel se sienta… 等感受型表达。" : undefined,
    matchedText: prohibited,
    replacement: prohibited ? (market === "MX" ? "ayuda a que la piel se sienta" : "helps skin feel") : undefined,
  });
  checks.push(...packagingChecks(text, sku));
  let structure: Status = "pass";
  let structureDetail = "结构字段完整。";
  if (type === "product_listing") {
    const parsed = parseContent(text, type);
    structure = parsed.title && parsed.bullets.length === 5 && parsed.description ? "pass" : "fail";
    structureDetail = structure === "pass" ? "标题、5 个卖点和描述齐全。" : `当前识别到 ${parsed.bullets.length} 个卖点。`;
  } else if (type === "short_video_script") {
    structure = /00:00|0–3|0-3/.test(text) && /CTA/i.test(text) ? "pass" : "warning";
    structureDetail = structure === "pass" ? "包含分镜时间与 CTA。" : "分镜时间或 CTA 不完整。";
  } else {
    structure = /(HOOK|GANCHO):/i.test(text) && /CTA:/i.test(text) ? "pass" : "warning";
    structureDetail = structure === "pass" ? "Hook、正文和 CTA 齐全。" : "Hook、正文或 CTA 缺失。";
  }
  checks.push({ id: "platform-structure", name: "平台结构", status: structure, detail: structureDetail });
  const terminologyPattern = market === "MX" ? /\bserum\b|crema de cara/i : /on the wet face|a opaque/i;
  const terminologyIssue = firstMatch(text, terminologyPattern);
  checks.push({
    id: "terminology",
    name: "术语一致性",
    status: terminologyIssue ? "warning" : "pass",
    detail: terminologyIssue ? "发现目标市场术语或语法提示。" : "核心术语符合目标语言约定。",
    suggestion: terminologyIssue ? (market === "MX" ? "优先使用 sérum / crema hidratante facial。" : "使用 over a wet face / an opaque。") : undefined,
    matchedText: terminologyIssue,
    replacement: terminologyIssue ? ({ serum: "sérum", "crema de cara": "crema hidratante facial", "on the wet face": "over a wet face", "a opaque": "an opaque" } as Record<string, string>)[terminologyIssue.toLowerCase()] : undefined,
  });
  const brandRisk = firstMatch(text, /buy now|compra ahora|must-have|life-changing/i);
  checks.push({
    id: "brand",
    name: "品牌一致性",
    status: brandRisk ? "warning" : "pass",
    detail: brandRisk ? "CTA 偏强促销，与温和可信的语气存在张力。" : "语气整体温和、清晰、可信。",
    suggestion: brandRisk ? "改为 See product details / Consulta los detalles。" : undefined,
    matchedText: brandRisk,
    replacement: brandRisk ? (market === "MX" ? "Consulta los detalles" : "See product details") : undefined,
  });
  checks.push({ id: "length", name: "字符预检", status: "pass", detail: `${text.length} 字符；真实发布前仍需按平台最新规则复核。` });
  const failed = checks.filter((check) => check.status === "fail").length;
  const warned = checks.filter((check) => check.status === "warning").length;
  return {
    checks,
    failed,
    warned,
    score: Math.max(0, 100 - failed * 25 - warned * 8),
    risk: failed ? "高风险" : warned ? "中风险" : "低风险",
  };
}

function download(name: string, content: string, type: string) {
  const blob = new Blob([content], { type });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = name;
  link.click();
  URL.revokeObjectURL(url);
}

function EvidenceChips({ ids }: { ids: string[] }) {
  return <div className="chips">{ids.map((id) => <span className="chip" key={id}>{id}</span>)}</div>;
}

export default function Home() {
  const [step, setStep] = useState(1);
  const [sku, setSku] = useState("MV-SERUM-001");
  const [market, setMarket] = useState<Market>("US");
  const [contentType, setContentType] = useState<ContentType>("product_listing");
  const [targetUser, setTargetUser] = useState("注重成分与肤感的日常护肤用户");
  const [goal, setGoal] = useState("产品认知与考虑");
  const [tones, setTones] = useState(TONES.slice(0, 2));
  const [generated, setGenerated] = useState(false);
  const [edited, setEdited] = useState("");
  const [confirmed, setConfirmed] = useState(false);
  const [confirmedAt, setConfirmedAt] = useState("");
  const [advancedFacts, setAdvancedFacts] = useState(false);
  const [reviewReasons, setReviewReasons] = useState<Record<string, string>>({});
  const [reviewedWarnings, setReviewedWarnings] = useState<Record<string, { action: "accepted"; reason: string; reviewed_at: string }>>({});
  const [lastFix, setLastFix] = useState<{ before: string; after: string; check: string } | null>(null);
  const [repairHistory, setRepairHistory] = useState<{ check: string; action: "deterministic_replace"; before: string; after: string; repaired_at: string }[]>([]);
  const [feedbackUseful, setFeedbackUseful] = useState("yes");
  const [feedbackCategory, setFeedbackCategory] = useState("localization");
  const [feedbackNote, setFeedbackNote] = useState("");
  const [includeContent, setIncludeContent] = useState(false);
  const [metricsEnabled, setMetricsEnabled] = useState(true);
  const editorRef = useRef<HTMLTextAreaElement>(null);
  const startedAt = useRef<number | null>(null);

  const productFacts = useMemo(() => facts.filter((fact) => fact.sku === sku && ["active", "caution", "prohibited", "non_fact"].includes(fact.status)), [sku]);
  const findFact = (attribute: string) => productFacts.find((fact) => fact.attribute === attribute);
  const findFacts = (...attributes: string[]) => productFacts.filter((fact) => attributes.includes(fact.attribute));
  const currentGroup = groups.find((group) => group.sku === sku && group.market === market && group.content_type === contentType)!;
  const enhanced = currentGroup?.versions.localizeflow ?? "";
  const baseline = currentGroup?.versions.baseline ?? "";
  const finalText = edited || enhanced;
  const preGenerationPackaging = packagingChecks(enhanced, sku);
  const quality = inspectContent(finalText, contentType, market, sku);
  const unresolvedWarnings = quality.checks.filter((check) => check.status === "warning" && !reviewedWarnings[check.id]);
  const evidenceIds = findFacts("verified_feature", "ingredient", "allowed_benefit", "usage_instruction", "packaging_feature").slice(0, 8).map((fact) => fact.fact_id);
  const allowed = productFacts.filter((fact) => ["direct", "cautious"].includes(fact.generation_policy) && ["verified_feature", "allowed_benefit", "usage_instruction", "packaging_feature"].includes(fact.attribute)).slice(0, 8);
  const prohibited = productFacts.filter((fact) => fact.attribute === "prohibited_claim").slice(0, 8);
  const contentTypes = Object.keys(TYPE_META) as ContentType[];

  function recordEvent(event: string, extra: { step?: number } = {}) {
    if (!metricsEnabled || typeof window === "undefined" || localStorage.getItem("localizeflow_metrics_disabled") === "true") return;
    const sessionKey = "localizeflow_anonymous_session";
    const eventsKey = "localizeflow_private_metrics";
    const sessionId = localStorage.getItem(sessionKey) ?? crypto.randomUUID();
    localStorage.setItem(sessionKey, sessionId);
    const cutoff = Date.now() - 30 * 24 * 60 * 60 * 1000;
    const events = (JSON.parse(localStorage.getItem(eventsKey) ?? "[]") as { at?: string }[]).filter((item) => item.at && new Date(item.at).getTime() >= cutoff);
    events.push({ event, anonymous_run_id: sessionId, at: new Date().toISOString(), duration_ms: startedAt.current ? Date.now() - startedAt.current : 0, market, content_type: contentType, ...extra });
    localStorage.setItem(eventsKey, JSON.stringify(events.slice(-100)));
  }

  useEffect(() => {
    startedAt.current = Date.now();
    const disabled = localStorage.getItem("localizeflow_metrics_disabled") === "true";
    if (disabled) setTimeout(() => setMetricsEnabled(false), 0);
    else recordEvent("demo_started", { step: 1 });
    // 仅在首次挂载记录；事件不包含文案正文。
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function generate() {
    if (preGenerationPackaging.some((check) => check.status === "fail")) return;
    setGenerated(true);
    setEdited(enhanced);
    setConfirmed(false);
    setReviewedWarnings({});
    setLastFix(null);
    setRepairHistory([]);
    recordEvent("content_generated", { step: 2 });
    setStep(3);
  }

  function locateIssue(check: QualityCheck) {
    if (!check.matchedText || !editorRef.current) return;
    const start = finalText.toLowerCase().indexOf(check.matchedText.toLowerCase());
    if (start < 0) return;
    editorRef.current.focus();
    editorRef.current.setSelectionRange(start, start + check.matchedText.length);
    editorRef.current.scrollIntoView({ behavior: "smooth", block: "center" });
  }

  function applyFix(check: QualityCheck) {
    if (!check.matchedText || !check.replacement) return;
    const start = finalText.toLowerCase().indexOf(check.matchedText.toLowerCase());
    if (start < 0) return;
    const next = `${finalText.slice(0, start)}${check.replacement}${finalText.slice(start + check.matchedText.length)}`;
    setEdited(next);
    setConfirmed(false);
    setReviewedWarnings({});
    setLastFix({ before: check.matchedText, after: check.replacement, check: check.name });
    setRepairHistory((current) => [...current, { check: check.name, action: "deterministic_replace", before: check.matchedText!, after: check.replacement!, repaired_at: new Date().toISOString() }]);
  }

  function exportPack() {
    const payload = {
      run_id: `LF-WEB-${sku}-${market}-${contentType}`,
      generation_mode: "offline_deterministic_demo",
      model_api_called: false,
      sku,
      market,
      language: MARKET_META[market].language,
      content_type: contentType,
      platform: TYPE_META[contentType].platform,
      target_user: targetUser,
      marketing_goal: goal,
      brand_tone: tones,
      versions: { baseline, enhanced, final: finalText },
      evidence_fact_ids: evidenceIds,
      quality,
      review_dispositions: reviewedWarnings,
      repair_history: repairHistory,
      human_review: { required: true, status: confirmed ? "confirmed" : "pending", confirmed_at: confirmedAt || null },
    };
    download(`${sku}_${market}_${contentType}.json`, JSON.stringify(payload, null, 2), "application/json;charset=utf-8");
    recordEvent("export_completed", { step: 5 });
  }

  function exportCsv() {
    const escape = (value: string) => `"${value.replaceAll('"', '""')}"`;
    const rows = [
      ["run_id", "sku", "market", "language", "content_type", "version", "content", "fact_ids", "warning_dispositions", "repair_history", "confirmed_at"],
      [`LF-WEB-${sku}-${market}-${contentType}`, sku, market, MARKET_META[market].language, contentType, "final", finalText, evidenceIds.join("|"), JSON.stringify(reviewedWarnings), JSON.stringify(repairHistory), confirmedAt],
    ];
    download(`${sku}_${market}_${contentType}.csv`, `\uFEFF${rows.map((row) => row.map((cell) => escape(String(cell))).join(",")).join("\n")}`, "text/csv;charset=utf-8");
    recordEvent("export_completed", { step: 5 });
  }

  function feedbackPayload() {
    return {
      feedback_id: `LF-FEEDBACK-${Date.now()}`,
      sku, market, content_type: contentType,
      useful: feedbackUseful === "yes",
      category: feedbackCategory,
      note: feedbackNote,
      full_edited_content: includeContent ? finalText : null,
      content_consent: includeContent,
      owner: "project_maintainer",
      status: "new",
      submitted_at: new Date().toISOString(),
    };
  }

  function downloadFeedback() {
    download(`LocalizeFlow_feedback_${Date.now()}.json`, JSON.stringify(feedbackPayload(), null, 2), "application/json;charset=utf-8");
    recordEvent("feedback_prepared", { step: 5 });
  }

  function openFeedbackIssue() {
    const payload = feedbackPayload();
    const body = [`SKU: ${sku}`, `Market: ${market}`, `Content type: ${contentType}`, `Useful: ${payload.useful}`, `Category: ${feedbackCategory}`, "", feedbackNote || "(no note)", "", "Content body included: no"].join("\n");
    window.open(`https://github.com/zugzwang-zg/LocalizeFlow/issues/new?title=${encodeURIComponent(`[Demo feedback] ${feedbackCategory}`)}&body=${encodeURIComponent(body)}`, "_blank", "noopener,noreferrer");
    recordEvent("feedback_submitted", { step: 5 });
  }

  function exportPrivateMetrics() {
    download("LocalizeFlow_private_metrics.json", localStorage.getItem("localizeflow_private_metrics") ?? "[]", "application/json;charset=utf-8");
  }

  function clearPrivateMetrics() {
    localStorage.removeItem("localizeflow_private_metrics");
    localStorage.removeItem("localizeflow_anonymous_session");
  }

  return (
    <main className="shell">
      <aside className="sidebar">
        <div>
          <div className="brand">LocalizeFlow</div>
          <div className="brandNote">evidence-led localization desk</div>
        </div>
        <nav aria-label="工作流步骤">
          {STEPS.map((label, index) => {
            const number = index + 1;
            return (
              <button className={`navItem ${step === number ? "active" : ""} ${step > number ? "done" : ""}`} key={label} onClick={() => setStep(number)}>
                <span>{String(number).padStart(2, "0")}</span>{label}
              </button>
            );
          })}
        </nav>
        <div className="sidebarStatus">
          <div className="statusLabel">演示状态</div>
          <p><span>商品</span>{sku}</p>
          <p><span>市场</span>{market}</p>
          <p><span>内容包</span>{generated ? "已生成" : "未生成"}</p>
          <div className="progress"><i style={{ width: generated ? "100%" : "28%" }} /></div>
          <small>离线确定性 Demo · 不调用模型 API</small>
        </div>
      </aside>

      <section className="workspace">
        <header className="topbar">
          <div className="offline"><span /> NO API · REPRODUCIBLE</div>
          <div className="topLinks"><a href="/privacy">隐私</a><a href="/terms">条款</a><a href="/acceptable-use">可接受使用</a><a href="https://github.com/zugzwang-zg/LocalizeFlow" target="_blank" rel="noreferrer">项目资料 ↗</a></div>
        </header>

        <div className="stepStrip" aria-label="当前进度">
          {STEPS.map((label, index) => <div className={`${step === index + 1 ? "active" : ""} ${step > index + 1 ? "done" : ""}`} key={label}><b>{step > index + 1 ? "✓" : String(index + 1).padStart(2, "0")} · {STEP_META[index].time}</b>{label}<small>{STEP_META[index].purpose}</small></div>)}
        </div>

        {step === 1 && (
          <div className="page">
            <div className="eyebrow">01 / SOURCE OF TRUTH</div>
            <h1>不是翻译器，而是跨境内容的证据与放行工作台。</h1>
            <p className="lede">沿推荐路径，在约 3 分钟内完成事实核对、目标市场改写、风险修复和人工放行。所有数据只在浏览器中处理，不会发送到外部模型。</p>
            <div className="introActions"><button className="primary" onClick={() => setStep(2)}>开始 3 分钟演示 →</button><span>推荐路径：事实 → 任务 → 结果 → 修复 → 放行</span></div>
            <div className="beforeAfter"><article><small>普通直译</small><p>{baseline.split("\n").slice(0, 2).join("\n")}</p><b>事实孤立 · 语气生硬 · 无放行记录</b></article><article><small>LocalizeFlow</small><p>{enhanced.split("\n").slice(0, 2).join("\n")}</p><b>证据绑定 · 市场化表达 · 可审计放行</b></article></div>
            <div className="sectionHeading compactHeading"><h2>核心事实</h2><span>本步约 30 秒 · 选定商品即完成</span></div>
            <label className="field wide"><span>选择商品</span><select value={sku} onChange={(event) => { setSku(event.target.value); setGenerated(false); setConfirmed(false); }}>{Object.entries(PRODUCTS).map(([id, label]) => <option value={id} key={id}>{id} · {label}</option>)}</select></label>
            <div className="ledgerGrid">
              <article><small>商品</small><strong>{valueOf(findFact("product_name_zh"))}</strong></article>
              <article><small>品类</small><strong>{valueOf(findFact("category"))}</strong></article>
              <article><small>规格</small><strong>{valueOf(findFact("net_volume") ?? findFact("total_volume"))}</strong></article>
              <article><small>参考价格 · {MARKET_META[market].currency}</small><strong>{valueOf(findFact(market === "US" ? "price_usd" : "price_mxn"))}</strong></article>
            </div>
            <section className="sectionBlock">
              <div className="sectionHeading"><h2>结构化事实</h2><span>{productFacts.filter((fact) => fact.generation_policy === "direct").length} 条可直接使用</span></div>
              {findFacts("verified_feature", "ingredient", "allowed_benefit", "usage_instruction", "packaging_feature").slice(0, advancedFacts ? 10 : 4).map((fact) => (
                <div className="factRow" key={fact.fact_id}>
                  <div><small>{fact.attribute.replaceAll("_", " ")}</small><p>{valueOf(fact)}</p></div>
                  <div className="evidenceRail"><b>证据 / EVIDENCE</b><EvidenceChips ids={[fact.fact_id]} /><small>{fact.source}</small></div>
                </div>
              ))}
              <button className="textButton" aria-expanded={advancedFacts} onClick={() => setAdvancedFacts((value) => !value)}>{advancedFacts ? "收起高级事实" : "展开完整事实与证据"}</button>
            </section>
            <div className="split">
              <section className="sectionBlock"><div className="sectionHeading"><h2>允许表达</h2><span>可用边界</span></div>{allowed.map((fact) => <div className="ruleRow" key={fact.fact_id}><span className={fact.generation_policy === "direct" ? "tag pass" : "tag warning"}>{fact.generation_policy === "direct" ? "直接使用" : "谨慎表达"}</span><code>{fact.fact_id}</code><p>{valueOf(fact)}</p></div>)}</section>
              <section className="sectionBlock"><div className="sectionHeading"><h2>禁止表达</h2><span>命中即阻断</span></div>{prohibited.map((fact) => <div className="ruleRow" key={fact.fact_id}><span className="tag fail">禁止生成</span><code>{fact.fact_id}</code><p>{valueOf(fact)}</p></div>)}</section>
            </div>
            <div className="actions"><button className="primary" onClick={() => setStep(2)}>设置营销任务 →</button></div>
          </div>
        )}

        {step === 2 && (
          <div className="page">
            <div className="eyebrow">02 / CAMPAIGN BRIEF</div>
            <h1>把目标市场写进任务。</h1>
            <p className="lede">选择市场、内容类型和传播目标。生成结果来自冻结评测样本，确保每次试用都能复现。</p>
            <div className="formGrid">
              <label className="field"><span>目标市场</span><select value={market} onChange={(event) => { setMarket(event.target.value as Market); setGenerated(false); }}>{Object.entries(MARKET_META).map(([id, meta]) => <option value={id} key={id}>{meta.label}</option>)}</select></label>
              <label className="field"><span>内容类型</span><select value={contentType} onChange={(event) => { setContentType(event.target.value as ContentType); setGenerated(false); }}>{contentTypes.map((id) => <option value={id} key={id}>{TYPE_META[id].label} · {TYPE_META[id].platform}</option>)}</select></label>
              <label className="field"><span>目标用户</span><input value={targetUser} onChange={(event) => setTargetUser(event.target.value)} /></label>
              <label className="field"><span>营销目标</span><input value={goal} onChange={(event) => setGoal(event.target.value)} /></label>
            </div>
            <section className="sectionBlock toneBlock"><div className="sectionHeading"><h2>品牌语气</h2><span>可多选</span></div><div className="choiceRow">{TONES.map((tone) => <button className={tones.includes(tone) ? "choice selected" : "choice"} key={tone} onClick={() => setTones((current) => current.includes(tone) ? current.filter((item) => item !== tone) : [...current, tone])}>{tone}</button>)}</div></section>
            <div className="briefCard"><div><small>运行编号</small><strong>LF-WEB-{sku}-{market}-{contentType}</strong></div><div><small>语言</small><strong>{MARKET_META[market].language}</strong></div><div><small>发布表面</small><strong>{TYPE_META[contentType].platform}</strong></div><div><small>生成前包装门禁</small><strong>{preGenerationPackaging.some((check) => check.status === "fail") ? "BLOCKED" : "PASS · evidence bound"}</strong></div></div>
              <div className="sourceNotice"><b>冻结规则来源</b><span>LF-PLATFORM-RULES-2026-07-28 · v1.0.0 · 核验于 2026-07-28</span><a href="https://support.google.com/merchants/answer/7052112?hl=en" target="_blank" rel="noreferrer">Google 官方规范 ↗</a><a href="https://ads.tiktok.com/help/article/tiktok-ads-policy-ad-format-and-functionality?lang=en" target="_blank" rel="noreferrer">TikTok 官方规范 ↗</a></div>
            <div className="actions"><button onClick={() => setStep(1)}>← 返回事实</button><button className="primary" disabled={preGenerationPackaging.some((check) => check.status === "fail")} onClick={generate}>生成可追溯内容包 →</button></div>
          </div>
        )}

        {step === 3 && (
          <div className="page">
            <div className="eyebrow">03 / TRACEABLE OUTPUT</div>
            <h1>每句话都有来路。</h1>
            <p className="lede">增强版内容同时使用商品事实、目标市场术语、品牌语气和平台结构。证据编号可回查原始事实库。</p>
            {!generated ? <div className="empty"><b>还没有内容包</b><p>先完成营销任务，生成离线可复现结果。</p><button className="primary" onClick={() => setStep(2)}>前往营销任务</button></div> : <>
              <div className="tabBar">{contentTypes.map((id) => <button className={contentType === id ? "selected" : ""} key={id} onClick={() => { setContentType(id); setEdited(groups.find((group) => group.sku === sku && group.market === market && group.content_type === id)?.versions.localizeflow ?? ""); }}>{TYPE_META[id].label}</button>)}</div>
              <article className="contentSheet"><div className="sheetHeader"><div><small>{TYPE_META[contentType].platform}</small><h2>{TYPE_META[contentType].label}</h2></div><span className="tag pass">增强版</span></div><pre>{enhanced}</pre><div className="evidenceBundle"><b>本内容包引用的事实</b><EvidenceChips ids={evidenceIds} /></div></article>
              <div className="noteBand">洞察只用于选择内容角度，不能替代商品事实；规则预检也不代表平台最终批准。</div>
              <div className="actions"><button onClick={() => setStep(2)}>← 调整任务</button><button className="primary" onClick={() => { setEdited(enhanced); setStep(4); recordEvent("quality_check_run", { step: 4 }); }}>运行质量检查 →</button></div>
            </>}
          </div>
        )}

        {step === 4 && (
          <div className="page">
            <div className="eyebrow">04 / QUALITY GATE</div>
            <h1>先定位风险，再决定放行。</h1>
            <p className="lede">修改文案后，事实、包装、术语、品牌和结构检查会在浏览器中立即重算。</p>
            {!generated ? <div className="empty"><b>请先生成内容包</b><button className="primary" onClick={() => setStep(2)}>前往营销任务</button></div> : <>
              <div className="metricGrid"><article><small>质量分</small><strong>{quality.score}<i>/100</i></strong></article><article><small>风险等级</small><strong>{quality.risk}</strong></article><article><small>阻断项</small><strong>{quality.failed}</strong></article><article><small>导出闸门</small><strong>{quality.failed ? "阻断" : "等待人工确认"}</strong></article></div>
              <div className="qualityGrid"><label className="editor"><span>人工编辑区</span><textarea ref={editorRef} value={finalText} onChange={(event) => { setEdited(event.target.value); setConfirmed(false); setReviewedWarnings({}); setLastFix(null); }} spellCheck="false" /></label><section className="checkPanel" aria-live="polite"><div className="sectionHeading"><h2>检查明细</h2><span>{quality.checks.length} 项</span></div>{quality.checks.map((check) => <div className="checkRow" key={check.id}><span className={`tag ${check.status}`}>{check.status === "pass" ? "通过" : check.status === "warning" ? "需复核" : "阻断"}</span><div><b>{check.name}</b><p>{check.detail}</p>{check.matchedText && <mark>命中文本：{check.matchedText}</mark>}{check.suggestion && <small>建议：{check.suggestion}</small>}{check.factIds?.length ? <small>证据：{check.factIds.join(", ")} · {check.source}</small> : null}<div className="checkActions">{check.matchedText && <button onClick={() => locateIssue(check)}>定位原文</button>}{check.replacement && <button onClick={() => applyFix(check)}>一键修复</button>}</div>{check.status === "warning" && <div className="disposition"><input aria-label={`${check.name}保留原因`} placeholder="填写保留原因（必填）" value={reviewReasons[check.id] ?? ""} onChange={(event) => setReviewReasons((current) => ({ ...current, [check.id]: event.target.value }))} /><button disabled={!reviewReasons[check.id]?.trim()} onClick={() => setReviewedWarnings((current) => ({ ...current, [check.id]: { action: "accepted", reason: reviewReasons[check.id].trim(), reviewed_at: new Date().toISOString() } }))}>{reviewedWarnings[check.id] ? "已记录复核" : "确认保留"}</button></div>}</div></div>)}</section></div>
              {lastFix && <div className="diffCard" aria-live="polite"><small>最近一次确定性修复 · 已自动复检</small><del>{lastFix.before}</del><span>→</span><ins>{lastFix.after}</ins><b>{lastFix.check}</b></div>}
              <div className="actions"><button onClick={() => { setEdited(enhanced); setReviewedWarnings({}); setLastFix(null); setRepairHistory([]); }}>恢复增强版</button><button className="primary" disabled={quality.failed > 0 || unresolvedWarnings.length > 0} onClick={() => setStep(5)}>{quality.failed ? "修复阻断项后继续" : unresolvedWarnings.length ? `处理 ${unresolvedWarnings.length} 个复核项后继续` : "进入人工终审 →"}</button></div>
            </>}
          </div>
        )}

        {step === 5 && (
          <div className="page">
            <div className="eyebrow">05 / HUMAN SIGN-OFF</div>
            <h1>版本清楚，责任清楚。</h1>
            <p className="lede">对照直译基线、规则增强版与人工终稿。只有质量闸门通过并完成确认，才开放导出。</p>
            {!generated ? <div className="empty"><b>请先生成内容包</b><button className="primary" onClick={() => setStep(2)}>前往营销任务</button></div> : <>
              <div className="compareGrid"><article><header><span>V00</span><b>直译基线</b></header><pre>{baseline}</pre></article><article><header><span>V01</span><b>LocalizeFlow 增强版</b></header><pre>{enhanced}</pre></article><article className="final"><header><span>V02</span><b>人工终稿</b></header><pre>{finalText}</pre></article></div>
              <div className="outcomeGrid"><article><small>节省的机械步骤</small><strong>3 类检查合并</strong></article><article><small>本次拦截</small><strong>{quality.failed + quality.warned} 项风险</strong></article><article><small>证据覆盖</small><strong>{evidenceIds.length} 个事实编号</strong></article><article><small>下一步</small><strong>目标平台人工复核</strong></article></div>
              <label className={`confirm ${confirmed ? "checked" : ""}`}><input type="checkbox" checked={confirmed} disabled={quality.failed > 0 || unresolvedWarnings.length > 0} onChange={(event) => { const checked = event.target.checked; setConfirmed(checked); setConfirmedAt(checked ? new Date().toISOString() : ""); if (checked) recordEvent("human_signoff_completed", { step: 5 }); }} /><span><b>我已核对事实、术语和平台规则</b><small>{quality.failed ? "仍有阻断项，暂不能确认。" : unresolvedWarnings.length ? "仍有警告未记录处理结论。" : "确认时间会写入导出记录；不会上传。"}</small></span></label>
              <div className="exportPanel"><div><small>EXPORT GATE</small><strong>{confirmed ? "READY TO EXPORT" : quality.failed ? "BLOCKED" : "AWAITING REVIEW"}</strong></div><div className="actions compact"><button disabled={!confirmed} onClick={exportCsv}>下载 CSV</button><button className="primary" disabled={!confirmed} onClick={exportPack}>下载 JSON</button></div></div>
              <section className="feedbackPanel"><div className="sectionHeading"><h2>结果是否有用？</h2><span>结构化反馈 · 每周由维护者复盘</span></div><div className="feedbackGrid"><label className="field"><span>结果评价</span><select value={feedbackUseful} onChange={(event) => setFeedbackUseful(event.target.value)}><option value="yes">有用</option><option value="no">无用</option></select></label><label className="field"><span>问题类别</span><select value={feedbackCategory} onChange={(event) => setFeedbackCategory(event.target.value)}><option value="localization">本地化</option><option value="fact_error">事实错误</option><option value="platform_rule">平台规则</option><option value="usability">操作体验</option></select></label><label className="field feedbackNote"><span>补充说明</span><input value={feedbackNote} onChange={(event) => setFeedbackNote(event.target.value)} placeholder="不要粘贴敏感或未公开内容" /></label></div><label className="contentConsent"><input type="checkbox" checked={includeContent} onChange={(event) => setIncludeContent(event.target.checked)} />明确同意在下载的本地反馈文件中附带完整终稿（默认不附带；GitHub 提交始终不附带）</label><div className="actions compact"><button onClick={downloadFeedback}>下载反馈单</button><button onClick={openFeedbackIssue}>在 GitHub 报告错误 ↗</button><a className="buttonLink" href="https://github.com/zugzwang-zg/LocalizeFlow/issues/new?template=beta_application.yml" target="_blank" rel="noreferrer">申请 Beta 试用 ↗</a></div></section>
              <details className="privacyPanel"><summary>本地隐私指标与数据控制</summary><p>Demo 只在你的浏览器 localStorage 保存匿名运行 ID、事件名、完成时间、耗时、市场和内容类型；用途仅为你自行检查体验路径；最多保留 100 条且不超过 30 天。不记录正文，不设置第三方 Cookie，不会自动传输。</p><label className="contentConsent"><input type="checkbox" checked={metricsEnabled} onChange={(event) => { const enabled = event.target.checked; setMetricsEnabled(enabled); localStorage.setItem("localizeflow_metrics_disabled", String(!enabled)); }} />允许在本机保存匿名体验事件</label><div className="actions compact"><button onClick={exportPrivateMetrics}>导出本地指标</button><button onClick={clearPrivateMetrics}>清除本地指标</button></div></details>
              <p className="fineprint">所有品牌、SKU、商品事实、价格、营销内容和评测材料均为 AI 生成的模拟数据，其余项目材料为原创。自动预检不替代平台、法务或目标语言专业人员的最终审核。参见 <a href="/disclaimer">免责声明</a>。</p>
            </>}
          </div>
        )}
      </section>
    </main>
  );
}
