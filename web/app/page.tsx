"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import factsData from "./data/product_facts.json";
import contentData from "./data/content_library.json";
import packagingData from "./data/packaging_facts.json";
import { buildImportedContent, parseProductFile, type ImportResult, type ImportedProductFact } from "./lib/product-import";

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
  product_listing: { label: "商品页内容", platform: "商品页格式" },
  short_video_script: { label: "15 秒短视频脚本", platform: "短视频格式" },
  social_ad_copy: { label: "社媒广告文案", platform: "社媒文案格式" },
};

const STEPS = ["商品资料", "营销任务", "生成结果", "质量检查", "版本与导出"];
const STEP_META = [
  { purpose: "确认商品资料", time: "约 30 秒" },
  { purpose: "选择市场和内容形式", time: "约 30 秒" },
  { purpose: "查看整理后的草稿", time: "约 40 秒" },
  { purpose: "找出问题并修改", time: "约 60 秒" },
  { purpose: "确认并下载记录", time: "约 20 秒" },
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
  if (!record) return [{ id: "packaging-uploaded", name: "包装信息", status: "pass", detail: "已读取表格中的包装信息；示例商品专用的包装用词检查不会套用到你的资料。", factIds: [] }];
  const issues: QualityCheck[] = [];
  const fieldLabels: Record<string, string> = { container_type: "容器类型", material: "包装材质", dispenser: "取用方式", closure: "封口方式", cap_material: "瓶盖材质", inner_lid: "内盖", transparency: "透明度", outer_container: "外包装" };
  for (const [field, candidates] of Object.entries(PACKAGING_TERMS)) {
    for (const [candidate, terms] of Object.entries(candidates)) {
      const hit = terms.find((term) => new RegExp(`\\b${term}\\b`, "i").test(text));
      if (!hit) continue;
      const allowed = record[field as keyof PackagingRecord] as string[] | undefined;
      if (!allowed?.includes(candidate)) {
        const expected = allowed?.join(" / ") ?? "unknown（无证据）";
        issues.push({ id: `packaging-${field}-${candidate}`, name: "包装信息", status: "fail", matchedText: hit, replacement: allowed?.length === 1 ? allowed[0] : "", detail: `“${hit}”与已填写的${fieldLabels[field] ?? "包装信息"}不一致；当前资料为：${expected}。`, suggestion: allowed?.length === 1 ? `改为 ${allowed[0]} 后重新检查。` : "删除这句话，或先补充并确认包装资料。", factIds: allowed ? [record.fact_id] : [], source: allowed ? record.source : "" });
      }
    }
  }
  for (const match of text.matchAll(/(?<!\d)(\d+(?:\.\d+)?)\s*m[lL]\b/g)) {
    if (!record.capacity.includes(Number(match[1]))) issues.push({ id: `packaging-capacity-${match.index}`, name: "包装信息", status: "fail", matchedText: match[0], replacement: record.capacity.length === 1 ? `${record.capacity[0]} mL` : "", detail: `“${match[0]}”与已填写的容量不一致；当前资料为：${record.capacity.join(" / ")} mL。`, suggestion: record.capacity.length === 1 ? `改为 ${record.capacity[0]} mL。` : "请按商品资料重新核对容量。", factIds: [record.fact_id], source: record.source });
  }
  return issues.length ? issues : [{ id: "packaging-pass", name: "包装信息", status: "pass", detail: "内容中的包装说法与商品资料一致。", factIds: [record.fact_id], source: record.source }];
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

function inspectContent(text: string, type: ContentType, market: Market, sku: string, prohibitedTerms: string[] = []) {
  const checks: QualityCheck[] = [];
  const prohibitedPattern = /\b(cure|cures|clinically proven|guaranteed|miracle|repair|repairs)\b|repara(?:r|n|s)?|all of your skincare needs|todas tus necesidades/i;
  const prohibited = firstMatch(text, prohibitedPattern) ?? prohibitedTerms.find((term) => term.length > 2 && text.toLowerCase().includes(term.toLowerCase()));
  checks.push({
    id: "fact-boundary",
    name: "是否超出商品资料",
    status: prohibited ? "fail" : "pass",
    detail: prohibited ? "这句话可能超出了表格资料，或带有保证、治疗意味。" : "没有发现明显超出资料的保证性表达。",
    suggestion: prohibited ? "改成“帮助肌肤感觉……”这类不过度保证的表达。" : undefined,
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
    structureDetail = structure === "pass" ? "时间段和结尾提示齐全。" : "时间段或结尾提示不完整。";
  } else {
    structure = /(HOOK|GANCHO):/i.test(text) && /CTA:/i.test(text) ? "pass" : "warning";
    structureDetail = structure === "pass" ? "开头、正文和结尾提示齐全。" : "开头、正文或结尾提示不完整。";
  }
  checks.push({ id: "platform-structure", name: "内容结构", status: structure, detail: structureDetail });
  const terminologyPattern = market === "MX" ? /\bserum\b|crema de cara/i : /on the wet face|a opaque/i;
  const terminologyIssue = firstMatch(text, terminologyPattern);
  checks.push({
    id: "terminology",
    name: "语言表达",
    status: terminologyIssue ? "warning" : "pass",
    detail: terminologyIssue ? "发现一个可以改得更自然的词或句子。" : "没有发现明显的词语或语法问题。",
    suggestion: terminologyIssue ? (market === "MX" ? "优先使用 sérum / crema hidratante facial。" : "使用 over a wet face / an opaque。") : undefined,
    matchedText: terminologyIssue,
    replacement: terminologyIssue ? ({ serum: "sérum", "crema de cara": "crema hidratante facial", "on the wet face": "over a wet face", "a opaque": "an opaque" } as Record<string, string>)[terminologyIssue.toLowerCase()] : undefined,
  });
  const brandRisk = firstMatch(text, /buy now|compra ahora|must-have|life-changing/i);
  checks.push({
    id: "brand",
    name: "语气",
    status: brandRisk ? "warning" : "pass",
    detail: brandRisk ? "这句促销感偏强，可以换成更克制的说法。" : "语气整体清楚、可信、不过度承诺。",
    suggestion: brandRisk ? "改为 See product details / Consulta los detalles。" : undefined,
    matchedText: brandRisk,
    replacement: brandRisk ? (market === "MX" ? "Consulta los detalles" : "See product details") : undefined,
  });
  checks.push({ id: "length", name: "长度", status: "pass", detail: `当前 ${text.length} 个字符；发布前仍请按实际渠道要求确认。` });
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

function importedFactToAppFact(fact: ImportedProductFact): Fact {
  const attributeMap: Record<string, string> = {
    product_name: "product_name_zh",
    specification: "specification",
    ingredient: "ingredient",
    usage_instruction: "usage_instruction",
    packaging_container: "packaging_feature",
    packaging_material: "packaging_feature",
    packaging_capacity: "packaging_feature",
    allowed_claim: "allowed_benefit",
    prohibited_claim: "prohibited_claim",
  };
  const splitExpressions = (value: string) => value ? value.split(/[;|]/).map((item) => item.trim()).filter(Boolean) : [];
  return {
    fact_id: fact.fact_id,
    sku: fact.sku,
    attribute: attributeMap[fact.attribute] ?? fact.attribute,
    value: fact.value,
    unit: fact.unit || null,
    evidence_level: fact.evidence_level,
    source: `${fact.source} · 上传表格`,
    allowed_expression: splitExpressions(fact.allowed_expression),
    prohibited_expression: splitExpressions(fact.prohibited_expression),
    generation_policy: fact.generation_policy,
    status: fact.attribute === "prohibited_claim" ? "prohibited" : "active",
  };
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
  const [importedFacts, setImportedFacts] = useState<ImportedProductFact[]>([]);
  const [importedFileName, setImportedFileName] = useState("");
  const [importMessage, setImportMessage] = useState("");
  const [importWarnings, setImportWarnings] = useState<string[]>([]);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const editorRef = useRef<HTMLTextAreaElement>(null);
  const startedAt = useRef<number | null>(null);

  const importedSkus = useMemo(() => [...new Set(importedFacts.map((fact) => fact.sku))], [importedFacts]);
  const isImportedProduct = importedSkus.includes(sku);
  const productFacts = useMemo(() => isImportedProduct ? importedFacts.filter((fact) => fact.sku === sku).map(importedFactToAppFact) : facts.filter((fact) => fact.sku === sku && ["active", "caution", "prohibited", "non_fact"].includes(fact.status)), [importedFacts, isImportedProduct, sku]);
  const findFact = (attribute: string) => productFacts.find((fact) => fact.attribute === attribute);
  const findFacts = (...attributes: string[]) => productFacts.filter((fact) => attributes.includes(fact.attribute));
  const currentGroup = groups.find((group) => group.sku === sku && group.market === market && group.content_type === contentType);
  const importedContent = useMemo(() => isImportedProduct ? buildImportedContent(importedFacts.filter((fact) => fact.sku === sku), market, contentType) : null, [contentType, importedFacts, isImportedProduct, market, sku]);
  const enhanced = importedContent?.enhanced ?? currentGroup?.versions.localizeflow ?? "";
  const baseline = importedContent?.baseline ?? currentGroup?.versions.baseline ?? "";
  const finalText = edited || enhanced;
  const preGenerationPackaging = packagingChecks(enhanced, sku);
  const configuredProhibitedTerms = productFacts.filter((fact) => fact.attribute === "prohibited_claim").flatMap((fact) => [String(fact.value), ...fact.prohibited_expression]).filter(Boolean);
  const quality = inspectContent(finalText, contentType, market, sku, configuredProhibitedTerms);
  const unresolvedWarnings = quality.checks.filter((check) => check.status === "warning" && !reviewedWarnings[check.id]);
  const evidenceIds = findFacts("verified_feature", "ingredient", "allowed_benefit", "usage_instruction", "packaging_feature", "specification").slice(0, 8).map((fact) => fact.fact_id);
  const allowed = productFacts.filter((fact) => ["direct", "cautious"].includes(fact.generation_policy) && ["verified_feature", "allowed_benefit", "usage_instruction", "packaging_feature"].includes(fact.attribute)).slice(0, 8);
  const prohibited = productFacts.filter((fact) => fact.attribute === "prohibited_claim").slice(0, 8);
  const contentTypes = Object.keys(TYPE_META) as ContentType[];
  const productOptions = [...Object.entries(PRODUCTS), ...importedSkus.filter((id) => !PRODUCTS[id]).map((id) => [id, `${id} · 上传的商品`] as [string, string])];

  async function handleFileImport(file?: File) {
    if (!file) return;
    setImportMessage("正在读取表格…");
    setImportWarnings([]);
    try {
      const result: ImportResult = await parseProductFile(file);
      setImportedFacts(result.facts);
      setImportedFileName(file.name);
      setImportWarnings(result.warnings);
      const firstSku = result.facts[0]?.sku;
      if (firstSku) setSku(firstSku);
      setGenerated(false);
      setEdited("");
      setConfirmed(false);
      setImportMessage(`已载入 ${result.facts.length} 条资料，可在浏览器内免费试用。`);
      setStep(1);
    } catch (error) {
      setImportMessage(error instanceof Error ? error.message : "表格读取失败，请检查模板格式。");
    }
    if (fileInputRef.current) fileInputRef.current.value = "";
  }

  function clearImportedFacts() {
    setImportedFacts([]);
    setImportedFileName("");
    setImportWarnings([]);
    setImportMessage("已切回示例资料。");
    setSku("MV-SERUM-001");
    setGenerated(false);
    setEdited("");
  }

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
          <div className="brandNote">资料 / 表达 / 导出</div>
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
          <p><span>内容草稿</span>{generated ? "已生成" : "未生成"}</p>
          <div className="progress"><i style={{ width: generated ? "100%" : "28%" }} /></div>
          <small>浏览器内处理 · 不上传文件</small>
        </div>
      </aside>

      <section className="workspace">
        <header className="topbar">
          <div className="offline"><span /> 在浏览器里处理 · 不上传文件</div>
          <div className="topLinks"><a href="/status">状态</a><a href="/support">支持</a><a href="/privacy">隐私</a><a href="/terms">条款</a><a href="/acceptable-use">可接受使用</a><a href="https://github.com/zugzwang-zg/LocalizeFlow" target="_blank" rel="noreferrer">GitHub ↗</a></div>
        </header>

        <div className="stepStrip" aria-label="当前进度">
          {STEPS.map((label, index) => <div className={`${step === index + 1 ? "active" : ""} ${step > index + 1 ? "done" : ""}`} key={label}><b>{step > index + 1 ? "✓" : String(index + 1).padStart(2, "0")} · {STEP_META[index].time}</b>{label}<small>{STEP_META[index].purpose}</small></div>)}
        </div>

        {step === 1 && (
          <div className="page">
            <section className="portfolioHero" aria-labelledby="portfolio-title">
              <div className="heroCopy">
                <div className="eyebrow">跨境商品内容工作台 · 在线体验</div>
                <h1 id="portfolio-title">把商品资料变成能检查、能修改、能放心交付的跨境内容。</h1>
                <p className="lede">把商品资料、目标市场表达、发布要求和人工确认放在同一条清晰的处理流程里。你可以先用示例数据了解步骤，也可以按模板导入自己的表格，直接在浏览器内试用。</p>
                <div className="introActions"><button className="primary" onClick={() => setStep(2)}>开始在线体验 →</button><a className="secondaryLink" href="#portfolio-evidence">了解工作方式 ↓</a></div>
              </div>
              <aside className="releaseManifest" aria-label="LocalizeFlow 放行路线与项目边界">
                <header><span>LF / 处理流程</span><b>从资料到可下载结果</b></header>
                <div className="manifestRoute">
                  <div><span>01</span><b>资料</b><small>查来源</small></div>
                  <div><span>02</span><b>表达</b><small>按市场整理</small></div>
                  <div><span>03</span><b>检查</b><small>发现问题先停</small></div>
                  <div><span>04</span><b>下载</b><small>确认后导出</small></div>
                </div>
                <div className="manifestDecisions"><span className="decisionReady">公开体验 · 可用</span><span className="decisionReady">浏览器试用 · 已开放</span></div>
                <p>可以先用示例，也可以上传自己的表格 · 文件只在本机处理，不会上传</p>
              </aside>
            </section>

            <section className="portfolioEvidence" id="portfolio-evidence" aria-labelledby="evidence-title">
              <div className="portfolioEvidenceHeader"><div><span>使用前先了解</span><h2 id="evidence-title">先看能做什么，再开始操作。</h2></div><p>覆盖 5 个示例商品、2 个市场和 3 类内容<br />可在浏览器内完成整理、检查和下载</p></div>
              <div className="portfolioMetrics">
                <article><small>同组内容对比</small><strong>30 / 30</strong><p>LocalizeFlow 版本被选中</p></article>
                <article><small>平均复核时间</small><strong>−25.8%</strong><p>6.33 → 4.70 分钟</p></article>
                <article><small>平均修改次数</small><strong>−61.5%</strong><p>3.63 → 1.40 次</p></article>
                <article><small>测试范围</small><strong>5 × 2 × 3</strong><p>商品 × 市场 × 内容类型</p></article>
              </div>
              <div className="portfolioReadoutGrid">
                <article className="ownershipCard"><span>你可以完成的事情</span><h3>从商品资料到可下载结果</h3><ul><li>选择商品、市场和内容形式</li><li>查看资料来源和可用范围</li><li>查看草稿、定位问题并直接修改</li><li>确认后下载 CSV / JSON 记录</li></ul></article>
                <article className="decisionCard"><span>处理方式</span><h3>每一步都清楚、可查看、可回头修改</h3><ol><li><b>先看资料，再整理内容</b><small>可以查看每段内容参考了哪些商品信息。</small></li><li><b>发现不一致就先停下来</b><small>资料或包装对不上时，不会直接下载。</small></li><li><b>示例和自己的资料分开</b><small>上传内容只在当前浏览器页面中处理。</small></li><li><b>确认后再下载</b><small>下载的记录会保留修改和确认时间。</small></li></ol></article>
              </div>
              <div className="evidenceCaveat"><b>结果说明</b><span>事实检查通过率从 40.0% 提升到 66.7%，仍有 10 条内容没有达到要求；当前结果来自项目样本，尚无真实用户采用或独立评审数据。</span><a href="https://github.com/zugzwang-zg/LocalizeFlow/blob/main/reports/evaluation_report.md" target="_blank" rel="noreferrer">查看完整评测 ↗</a></div>
            </section>

            <section className="importPanel" aria-labelledby="import-title">
              <div className="sectionHeading"><h2 id="import-title">用自己的表格试一遍</h2><span>免费 · 浏览器内处理</span></div>
              <p>先下载模板，按示例填写商品名称、规格、成分和使用方法，再上传自己的 CSV 或 XLSX。文件只在当前页面内读取，不会发送到服务器；请使用虚构或已脱敏的资料。</p>
              <div className="importActions"><a className="buttonLink" href="/templates/localizeflow-demo-template.csv" download>下载 CSV 模板 ↓</a><a className="buttonLink" href="/templates/localizeflow-demo-template.xlsx" download>下载 XLSX 模板 ↓</a><label className="uploadButton"><input ref={fileInputRef} type="file" accept=".csv,.xlsx,text/csv,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" onChange={(event) => void handleFileImport(event.target.files?.[0])} />上传 CSV / XLSX</label>{isImportedProduct && <button className="textButton" onClick={clearImportedFacts}>返回示例资料</button>}</div>
              {importedFileName && <div className="importSuccess"><b>{importedFileName}</b><span>{importMessage}</span></div>}
              {!importedFileName && importMessage && <div className="importError" role="status">{importMessage}</div>}
              {importWarnings.length > 0 && <ul className="importWarnings">{importWarnings.map((warning) => <li key={warning}>{warning}</li>)}</ul>}
            </section>
            <div className="beforeAfter"><article><small>原始资料</small><p>{baseline.split("\n").slice(0, 2).join("\n")}</p><b>信息分散 · 缺少检查 · 无确认记录</b></article><article><small>整理后的内容</small><p>{enhanced.split("\n").slice(0, 2).join("\n")}</p><b>资料可回查 · 表达更清楚 · 可留下处理记录</b></article></div>
            <div className="sectionHeading compactHeading"><h2>商品资料</h2><span>先确认资料，再开始处理</span></div>
            <label className="field wide"><span>选择商品</span><select value={sku} onChange={(event) => { setSku(event.target.value); setGenerated(false); setConfirmed(false); }}>{productOptions.map(([id, label]) => <option value={id} key={id}>{label}</option>)}</select></label>
            <div className="ledgerGrid">
              <article><small>商品</small><strong>{valueOf(findFact("product_name_zh"))}</strong></article>
              <article><small>规格 / 品类</small><strong>{valueOf(findFact("category") ?? findFact("specification"))}</strong></article>
              <article><small>容量 / 包装</small><strong>{valueOf(findFact("net_volume") ?? findFact("total_volume") ?? findFact("packaging_feature"))}</strong></article>
              <article><small>参考价格 · {MARKET_META[market].currency}</small><strong>{valueOf(findFact(market === "US" ? "price_usd" : "price_mxn"))}</strong></article>
            </div>
            <section className="sectionBlock">
              <div className="sectionHeading"><h2>已读取的资料</h2><span>{productFacts.filter((fact) => fact.generation_policy === "direct").length} 条可以直接使用</span></div>
              {findFacts("verified_feature", "ingredient", "allowed_benefit", "usage_instruction", "packaging_feature").slice(0, advancedFacts ? 10 : 4).map((fact) => (
                <div className="factRow" key={fact.fact_id}>
                  <div><small>{fact.attribute.replaceAll("_", " ")}</small><p>{valueOf(fact)}</p></div>
                  <div className="evidenceRail"><b>资料来源</b><EvidenceChips ids={[fact.fact_id]} /><small>{fact.source}</small></div>
                </div>
              ))}
              <button className="textButton" aria-expanded={advancedFacts} onClick={() => setAdvancedFacts((value) => !value)}>{advancedFacts ? "收起更多资料" : "查看更多资料和来源"}</button>
            </section>
            <div className="split">
              <section className="sectionBlock"><div className="sectionHeading"><h2>可以这样说</h2><span>可直接使用或适当调整</span></div>{allowed.map((fact) => <div className="ruleRow" key={fact.fact_id}><span className={fact.generation_policy === "direct" ? "tag pass" : "tag warning"}>{fact.generation_policy === "direct" ? "可以直接用" : "建议调整"}</span><code>{fact.fact_id}</code><p>{valueOf(fact)}</p></div>)}</section>
              <section className="sectionBlock"><div className="sectionHeading"><h2>不要这样说</h2><span>发现后需要修改</span></div>{prohibited.map((fact) => <div className="ruleRow" key={fact.fact_id}><span className="tag fail">需要修改</span><code>{fact.fact_id}</code><p>{valueOf(fact)}</p></div>)}</section>
            </div>
            <div className="actions"><button className="primary" onClick={() => setStep(2)}>设置营销任务 →</button></div>
          </div>
        )}

        {step === 2 && (
          <div className="page">
            <div className="eyebrow">02 / 设置内容任务</div>
            <h1>把目标市场写进任务。</h1>
            <p className="lede">选择目标市场、内容形式和表达重点。示例资料使用固定内容；上传自己的表格后，草稿会根据表格里的信息整理。</p>
            <div className="formGrid">
              <label className="field"><span>目标市场</span><select value={market} onChange={(event) => { setMarket(event.target.value as Market); setGenerated(false); }}>{Object.entries(MARKET_META).map(([id, meta]) => <option value={id} key={id}>{meta.label}</option>)}</select></label>
              <label className="field"><span>内容类型</span><select value={contentType} onChange={(event) => { setContentType(event.target.value as ContentType); setGenerated(false); }}>{contentTypes.map((id) => <option value={id} key={id}>{TYPE_META[id].label} · {TYPE_META[id].platform}</option>)}</select></label>
              <label className="field"><span>目标用户</span><input value={targetUser} onChange={(event) => setTargetUser(event.target.value)} /></label>
              <label className="field"><span>营销目标</span><input value={goal} onChange={(event) => setGoal(event.target.value)} /></label>
            </div>
            <section className="sectionBlock toneBlock"><div className="sectionHeading"><h2>品牌语气</h2><span>可多选</span></div><div className="choiceRow">{TONES.map((tone) => <button className={tones.includes(tone) ? "choice selected" : "choice"} key={tone} onClick={() => setTones((current) => current.includes(tone) ? current.filter((item) => item !== tone) : [...current, tone])}>{tone}</button>)}</div></section>
            <div className="briefCard"><div><small>本次记录</small><strong>LF-WEB-{sku}-{market}-{contentType}</strong></div><div><small>语言</small><strong>{MARKET_META[market].language}</strong></div><div><small>内容格式</small><strong>{TYPE_META[contentType].platform}</strong></div><div><small>生成前检查</small><strong>{preGenerationPackaging.some((check) => check.status === "fail") ? "暂缓" : "已通过"}</strong></div></div>
              <div className="sourceNotice"><b>检查依据</b><span>项目内置的发布要求 · 更新于 2026-07-28</span><a href="https://support.google.com/merchants/answer/7052112?hl=en" target="_blank" rel="noreferrer">Google 官方要求 ↗</a><a href="https://ads.tiktok.com/help/article/tiktok-ads-policy-ad-format-and-functionality?lang=en" target="_blank" rel="noreferrer">TikTok 官方要求 ↗</a></div>
            <div className="actions"><button onClick={() => setStep(1)}>← 返回商品资料</button><button className="primary" disabled={preGenerationPackaging.some((check) => check.status === "fail")} onClick={generate}>生成内容草稿 →</button></div>
          </div>
        )}

        {step === 3 && (
          <div className="page">
            <div className="eyebrow">03 / 内容草稿</div>
            <h1>每句话都有来路。</h1>
            <p className="lede">这里会展示按资料整理的内容草稿。你可以切换内容形式，并查看每段文字引用了哪些商品信息。</p>
            {!generated ? <div className="empty"><b>还没有内容草稿</b><p>先设置内容任务，再生成草稿。</p><button className="primary" onClick={() => setStep(2)}>前往设置任务</button></div> : <>
              <div className="tabBar">{contentTypes.map((id) => <button className={contentType === id ? "selected" : ""} key={id} onClick={() => { setContentType(id); setEdited(groups.find((group) => group.sku === sku && group.market === market && group.content_type === id)?.versions.localizeflow ?? ""); }}>{TYPE_META[id].label}</button>)}</div>
              <article className="contentSheet"><div className="sheetHeader"><div><small>{TYPE_META[contentType].platform}</small><h2>{TYPE_META[contentType].label}</h2></div><span className="tag pass">内容草稿</span></div><pre>{enhanced}</pre><div className="evidenceBundle"><b>这份草稿参考了这些资料</b><EvidenceChips ids={evidenceIds} /></div></article>
              <div className="noteBand">这里的整理结果只基于当前表格资料；发布前仍请按实际渠道要求做最后确认。</div>
              <div className="actions"><button onClick={() => setStep(2)}>← 调整任务</button><button className="primary" onClick={() => { setEdited(enhanced); setStep(4); recordEvent("quality_check_run", { step: 4 }); }}>运行质量检查 →</button></div>
            </>}
          </div>
        )}

        {step === 4 && (
          <div className="page">
            <div className="eyebrow">04 / 检查和修改</div>
            <h1>先找出问题，再决定是否下载。</h1>
            <p className="lede">修改内容后，商品资料、包装信息、语言表达、语气和结构会在浏览器中立即重新检查。</p>
            {!generated ? <div className="empty"><b>请先生成内容草稿</b><button className="primary" onClick={() => setStep(2)}>前往设置任务</button></div> : <>
              <div className="metricGrid"><article><small>检查结果</small><strong>{quality.score}<i>/100</i></strong></article><article><small>风险提示</small><strong>{quality.risk}</strong></article><article><small>需要修改</small><strong>{quality.failed}</strong></article><article><small>导出状态</small><strong>{quality.failed ? "暂不能导出" : "等待人工确认"}</strong></article></div>
              <div className="qualityGrid"><label className="editor"><span>修改内容</span><textarea ref={editorRef} value={finalText} onChange={(event) => { setEdited(event.target.value); setConfirmed(false); setReviewedWarnings({}); setLastFix(null); }} spellCheck="false" /></label><section className="checkPanel" aria-live="polite"><div className="sectionHeading"><h2>检查结果</h2><span>{quality.checks.length} 项</span></div>{quality.checks.map((check) => <div className="checkRow" key={check.id}><span className={`tag ${check.status}`}>{check.status === "pass" ? "通过" : check.status === "warning" ? "需要确认" : "需要修改"}</span><div><b>{check.name}</b><p>{check.detail}</p>{check.matchedText && <mark>发现：{check.matchedText}</mark>}{check.suggestion && <small>可以这样改：{check.suggestion}</small>}{check.factIds?.length ? <small>参考资料：{check.factIds.join(", ")} · {check.source}</small> : null}<div className="checkActions">{check.matchedText && <button onClick={() => locateIssue(check)}>查看原文</button>}{check.replacement && <button onClick={() => applyFix(check)}>直接修改</button>}</div>{check.status === "warning" && <div className="disposition"><input aria-label={`${check.name}保留原因`} placeholder="如果保留，请说明原因" value={reviewReasons[check.id] ?? ""} onChange={(event) => setReviewReasons((current) => ({ ...current, [check.id]: event.target.value }))} /><button disabled={!reviewReasons[check.id]?.trim()} onClick={() => setReviewedWarnings((current) => ({ ...current, [check.id]: { action: "accepted", reason: reviewReasons[check.id].trim(), reviewed_at: new Date().toISOString() } }))}>{reviewedWarnings[check.id] ? "已记录" : "记录处理结果"}</button></div>}</div></div>)}</section></div>
              {lastFix && <div className="diffCard" aria-live="polite"><small>最近一次直接修改 · 已重新检查</small><del>{lastFix.before}</del><span>→</span><ins>{lastFix.after}</ins><b>{lastFix.check}</b></div>}
              <div className="actions"><button onClick={() => { setEdited(enhanced); setReviewedWarnings({}); setLastFix(null); setRepairHistory([]); }}>恢复整理后的版本</button><button className="primary" disabled={quality.failed > 0 || unresolvedWarnings.length > 0} onClick={() => setStep(5)}>{quality.failed ? "修改问题后继续" : unresolvedWarnings.length ? `处理 ${unresolvedWarnings.length} 个提示后继续` : "进入最终确认 →"}</button></div>
            </>}
          </div>
        )}

        {step === 5 && (
          <div className="page">
            <div className="eyebrow">05 / 确认和下载</div>
            <h1>确认内容后，再下载记录。</h1>
            <p className="lede">对照原始草稿、整理后的版本和最终修改稿。完成检查并确认后，可以下载处理记录。</p>
            {!generated ? <div className="empty"><b>请先生成内容草稿</b><button className="primary" onClick={() => setStep(2)}>前往设置任务</button></div> : <>
              <div className="compareGrid"><article><header><span>V00</span><b>原始草稿</b></header><pre>{baseline}</pre></article><article><header><span>V01</span><b>整理后的版本</b></header><pre>{enhanced}</pre></article><article className="final"><header><span>V02</span><b>最终修改稿</b></header><pre>{finalText}</pre></article></div>
              <div className="outcomeGrid"><article><small>减少重复操作</small><strong>3 类检查合并</strong></article><article><small>本次提示</small><strong>{quality.failed + quality.warned} 项问题</strong></article><article><small>参考资料</small><strong>{evidenceIds.length} 条商品信息</strong></article><article><small>下一步</small><strong>发布前再次确认</strong></article></div>
              <label className={`confirm ${confirmed ? "checked" : ""}`}><input type="checkbox" checked={confirmed} disabled={quality.failed > 0 || unresolvedWarnings.length > 0} onChange={(event) => { const checked = event.target.checked; setConfirmed(checked); setConfirmedAt(checked ? new Date().toISOString() : ""); if (checked) recordEvent("human_signoff_completed", { step: 5 }); }} /><span><b>我已核对商品资料、表达和发布要求</b><small>{quality.failed ? "还有需要修改的内容，暂时不能确认。" : unresolvedWarnings.length ? "还有需要确认的提示，请先记录处理结果。" : "确认时间会写入下载记录；不会上传。"}</small></span></label>
              <div className="exportPanel"><div><small>下载条件</small><strong>{confirmed ? "可以下载" : quality.failed ? "需要修改" : "等待确认"}</strong></div><div className="actions compact"><button disabled={!confirmed} onClick={exportCsv}>下载 CSV</button><button className="primary" disabled={!confirmed} onClick={exportPack}>下载 JSON</button></div></div>
              <section className="feedbackPanel"><div className="sectionHeading"><h2>结果是否有用？</h2><span>体验反馈 · 由维护者定期查看</span></div><div className="feedbackGrid"><label className="field"><span>结果评价</span><select value={feedbackUseful} onChange={(event) => setFeedbackUseful(event.target.value)}><option value="yes">有用</option><option value="no">无用</option></select></label><label className="field"><span>问题类别</span><select value={feedbackCategory} onChange={(event) => setFeedbackCategory(event.target.value)}><option value="localization">目标市场表达</option><option value="fact_error">商品资料错误</option><option value="platform_rule">发布要求</option><option value="usability">操作体验</option></select></label><label className="field feedbackNote"><span>补充说明</span><input value={feedbackNote} onChange={(event) => setFeedbackNote(event.target.value)} placeholder="不要粘贴敏感或未公开内容" /></label></div><label className="contentConsent"><input type="checkbox" checked={includeContent} onChange={(event) => setIncludeContent(event.target.checked)} />同意在下载的反馈文件中附带完整内容（默认不附带；GitHub 反馈也不会自动附带）</label><div className="actions compact"><button onClick={downloadFeedback}>下载反馈单</button><button onClick={openFeedbackIssue}>在 GitHub 报告错误 ↗</button><a className="buttonLink" href="https://github.com/zugzwang-zg/LocalizeFlow/issues/new?template=beta_application.yml" target="_blank" rel="noreferrer">登记后续体验意向 ↗</a></div></section>
              <details className="privacyPanel"><summary>本机保存记录与数据控制</summary><p>页面可以在你的浏览器中保存匿名的操作时间、市场、内容类型和步骤，方便你查看本次体验；最多保留 100 条且不超过 30 天。不会保存正文、上传文件，也不会自动发送给项目维护者。</p><label className="contentConsent"><input type="checkbox" checked={metricsEnabled} onChange={(event) => { const enabled = event.target.checked; setMetricsEnabled(enabled); localStorage.setItem("localizeflow_metrics_disabled", String(!enabled)); }} />允许在本机保存匿名操作记录</label><div className="actions compact"><button onClick={exportPrivateMetrics}>下载本机记录</button><button onClick={clearPrivateMetrics}>清除本机记录</button></div></details>
              <p className="fineprint">所有品牌、商品编号、商品资料、价格、营销内容和评测材料均为 AI 生成的模拟数据；社交预览图也由 AI 生成，不作为项目结果依据。除此之外，代码、文档、测量、图表与演示资产为原创。自动检查不能替代平台、法务或目标语言人员的最终审核。参见 <a href="/disclaimer">免责声明</a>。</p>
            </>}
          </div>
        )}
      </section>
    </main>
  );
}
