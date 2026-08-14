"use client";

import { useMemo, useState } from "react";
import factsData from "./data/product_facts.json";
import contentData from "./data/content_library.json";

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
type QualityCheck = { name: string; status: Status; detail: string; suggestion?: string };

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
const TONES = ["温和", "可信", "清晰", "克制"];

const facts = factsData.facts as Fact[];
const groups = contentData.groups as ContentGroup[];

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
  const prohibited = /\b(cure|cures|clinically proven|guaranteed|miracle|repair|repairs)\b|repara(?:r|n|s)?|all of your skincare needs|todas tus necesidades/i.test(text);
  checks.push({
    name: "事实与功效边界",
    status: prohibited ? "fail" : "pass",
    detail: prohibited ? "发现医疗化、保证性或超出证据边界的表述。" : "未发现医疗化、全能承诺或保证性功效。",
    suggestion: prohibited ? "改为 helps skin feel… / ayuda a que la piel se sienta… 等感受型表达。" : undefined,
  });
  const packagingIssue = sku === "MV-HAND-001" && /aluminum tube|tubo de aluminio/i.test(text);
  checks.push({
    name: "包装事实",
    status: packagingIssue ? "fail" : "pass",
    detail: packagingIssue ? "内容写为铝管，但事实库仅支持软管包装。" : "未发现已知包装矛盾。",
    suggestion: packagingIssue ? "删除材质推断，改为 tube / tubo。" : undefined,
  });
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
  checks.push({ name: "平台结构", status: structure, detail: structureDetail });
  const terminologyIssue = market === "MX" ? /\bserum\b|crema de cara/i.test(text) : /on the wet face|a opaque/i.test(text);
  checks.push({
    name: "术语一致性",
    status: terminologyIssue ? "warning" : "pass",
    detail: terminologyIssue ? "发现目标市场术语或语法提示。" : "核心术语符合目标语言约定。",
    suggestion: terminologyIssue ? (market === "MX" ? "优先使用 sérum / crema hidratante facial。" : "使用 over a wet face / an opaque。") : undefined,
  });
  const brandRisk = /buy now|compra ahora|must-have|life-changing/i.test(text);
  checks.push({
    name: "品牌一致性",
    status: brandRisk ? "warning" : "pass",
    detail: brandRisk ? "CTA 偏强促销，与温和可信的语气存在张力。" : "语气整体温和、清晰、可信。",
    suggestion: brandRisk ? "改为 See product details / Consulta los detalles。" : undefined,
  });
  checks.push({ name: "字符预检", status: "pass", detail: `${text.length} 字符；真实发布前仍需按平台最新规则复核。` });
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

  const productFacts = useMemo(() => facts.filter((fact) => fact.sku === sku && ["active", "caution", "prohibited", "non_fact"].includes(fact.status)), [sku]);
  const findFact = (attribute: string) => productFacts.find((fact) => fact.attribute === attribute);
  const findFacts = (...attributes: string[]) => productFacts.filter((fact) => attributes.includes(fact.attribute));
  const currentGroup = groups.find((group) => group.sku === sku && group.market === market && group.content_type === contentType)!;
  const enhanced = currentGroup?.versions.localizeflow ?? "";
  const baseline = currentGroup?.versions.baseline ?? "";
  const finalText = edited || enhanced;
  const quality = inspectContent(finalText, contentType, market, sku);
  const evidenceIds = findFacts("verified_feature", "ingredient", "allowed_benefit", "usage_instruction", "packaging_feature").slice(0, 8).map((fact) => fact.fact_id);
  const allowed = productFacts.filter((fact) => ["direct", "cautious"].includes(fact.generation_policy) && ["verified_feature", "allowed_benefit", "usage_instruction", "packaging_feature"].includes(fact.attribute)).slice(0, 8);
  const prohibited = productFacts.filter((fact) => fact.attribute === "prohibited_claim").slice(0, 8);
  const contentTypes = Object.keys(TYPE_META) as ContentType[];

  function generate() {
    setGenerated(true);
    setEdited(enhanced);
    setConfirmed(false);
    setStep(3);
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
      human_review: { required: true, status: confirmed ? "confirmed" : "pending" },
    };
    download(`${sku}_${market}_${contentType}.json`, JSON.stringify(payload, null, 2), "application/json;charset=utf-8");
  }

  function exportCsv() {
    const escape = (value: string) => `"${value.replaceAll('"', '""')}"`;
    const rows = [
      ["run_id", "sku", "market", "language", "content_type", "version", "content", "fact_ids"],
      [`LF-WEB-${sku}-${market}-${contentType}`, sku, market, MARKET_META[market].language, contentType, "final", finalText, evidenceIds.join("|")],
    ];
    download(`${sku}_${market}_${contentType}.csv`, `\uFEFF${rows.map((row) => row.map((cell) => escape(String(cell))).join(",")).join("\n")}`, "text/csv;charset=utf-8");
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
          <a href="https://github.com/zugzwang-zg/LocalizeFlow" target="_blank" rel="noreferrer">查看项目资料 ↗</a>
        </header>

        <div className="stepStrip" aria-label="当前进度">
          {STEPS.map((label, index) => <div className={`${step === index + 1 ? "active" : ""} ${step > index + 1 ? "done" : ""}`} key={label}><b>{String(index + 1).padStart(2, "0")}</b>{label}</div>)}
        </div>

        {step === 1 && (
          <div className="page">
            <div className="eyebrow">01 / SOURCE OF TRUTH</div>
            <h1>先把商品事实钉牢。</h1>
            <p className="lede">生成之前先看证据。选择商品，核对允许和禁止表达；所有数据都在浏览器中处理，不会发送到外部模型。</p>
            <label className="field wide"><span>选择商品</span><select value={sku} onChange={(event) => { setSku(event.target.value); setGenerated(false); setConfirmed(false); }}>{Object.entries(PRODUCTS).map(([id, label]) => <option value={id} key={id}>{id} · {label}</option>)}</select></label>
            <div className="ledgerGrid">
              <article><small>商品</small><strong>{valueOf(findFact("product_name_zh"))}</strong></article>
              <article><small>品类</small><strong>{valueOf(findFact("category"))}</strong></article>
              <article><small>规格</small><strong>{valueOf(findFact("net_volume") ?? findFact("total_volume"))}</strong></article>
              <article><small>参考价格 · {MARKET_META[market].currency}</small><strong>{valueOf(findFact(market === "US" ? "price_usd" : "price_mxn"))}</strong></article>
            </div>
            <section className="sectionBlock">
              <div className="sectionHeading"><h2>结构化事实</h2><span>{productFacts.filter((fact) => fact.generation_policy === "direct").length} 条可直接使用</span></div>
              {findFacts("verified_feature", "ingredient", "allowed_benefit", "usage_instruction", "packaging_feature").slice(0, 10).map((fact) => (
                <div className="factRow" key={fact.fact_id}>
                  <div><small>{fact.attribute.replaceAll("_", " ")}</small><p>{valueOf(fact)}</p></div>
                  <div className="evidenceRail"><b>证据 / EVIDENCE</b><EvidenceChips ids={[fact.fact_id]} /><small>{fact.source}</small></div>
                </div>
              ))}
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
            <div className="briefCard"><div><small>运行编号</small><strong>LF-WEB-{sku}-{market}-{contentType}</strong></div><div><small>语言</small><strong>{MARKET_META[market].language}</strong></div><div><small>发布表面</small><strong>{TYPE_META[contentType].platform}</strong></div><div><small>生成模式</small><strong>Offline deterministic</strong></div></div>
            <div className="actions"><button onClick={() => setStep(1)}>← 返回事实</button><button className="primary" onClick={generate}>生成可追溯内容包 →</button></div>
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
              <div className="actions"><button onClick={() => setStep(2)}>← 调整任务</button><button className="primary" onClick={() => { setEdited(enhanced); setStep(4); }}>运行质量检查 →</button></div>
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
              <div className="qualityGrid"><label className="editor"><span>人工编辑区</span><textarea value={finalText} onChange={(event) => { setEdited(event.target.value); setConfirmed(false); }} spellCheck="false" /></label><section className="checkPanel"><div className="sectionHeading"><h2>检查明细</h2><span>{quality.checks.length} 项</span></div>{quality.checks.map((check) => <div className="checkRow" key={check.name}><span className={`tag ${check.status}`}>{check.status === "pass" ? "通过" : check.status === "warning" ? "需复核" : "阻断"}</span><div><b>{check.name}</b><p>{check.detail}</p>{check.suggestion && <small>建议：{check.suggestion}</small>}</div></div>)}</section></div>
              <div className="actions"><button onClick={() => setEdited(enhanced)}>恢复增强版</button><button className="primary" disabled={quality.failed > 0} onClick={() => setStep(5)}>{quality.failed ? "修复阻断项后继续" : "进入人工终审 →"}</button></div>
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
              <label className={`confirm ${confirmed ? "checked" : ""}`}><input type="checkbox" checked={confirmed} disabled={quality.failed > 0} onChange={(event) => setConfirmed(event.target.checked)} /><span><b>我已核对事实、术语和平台规则</b><small>{quality.failed ? "仍有阻断项，暂不能确认。" : "此确认只作用于当前浏览器会话。"}</small></span></label>
              <div className="exportPanel"><div><small>EXPORT GATE</small><strong>{confirmed ? "READY TO EXPORT" : quality.failed ? "BLOCKED" : "AWAITING REVIEW"}</strong></div><div className="actions compact"><button disabled={!confirmed} onClick={exportCsv}>下载 CSV</button><button className="primary" disabled={!confirmed} onClick={exportPack}>下载 JSON</button></div></div>
              <p className="fineprint">所有商品、品牌与价格均为项目模拟数据。自动预检不替代平台、法务或目标语言专业人员的最终审核。</p>
            </>}
          </div>
        )}
      </section>
    </main>
  );
}
