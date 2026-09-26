import factsData from "../app/data/product_facts.json";
import packagingData from "../app/data/packaging_facts.json";
import rules from "../../data/rules/demo_quality_rules.json";
export type Market = "US" | "MX";
export type ContentType = "product_listing" | "short_video_script" | "social_ad_copy";
export type Status = "pass" | "warning" | "fail" | "not_checked";
export type Fact = {
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
export type ContentGroup = {
  sku: string;
  market: Market;
  language: string;
  content_type: ContentType;
  versions: { baseline: string; localizeflow: string };
};
export type QualityCheck = { id: string; name: string; status: Status; detail: string; suggestion?: string; matchedText?: string; replacement?: string; factIds?: string[]; source?: string };
export type PackagingRecord = { fact_id: string; source: string; capacity: number[]; container_type?: string[]; material?: string[]; dispenser?: string[]; closure?: string[]; cap_material?: string[]; inner_lid?: string[]; transparency?: string[]; outer_container?: string[] };


const facts = factsData.facts as Fact[];
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

export function packagingChecks(text: string, sku: string): QualityCheck[] {
  const record = packaging[sku];
  const issues: QualityCheck[] = [];
  for (const [field, candidates] of Object.entries(PACKAGING_TERMS)) {
    for (const [candidate, terms] of Object.entries(candidates)) {
      const hit = terms.find((term: string) => new RegExp(`\\b${term}\\b`, "i").test(text));
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

export function valueOf(fact?: Fact) {
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

export function inspectContent(text: string, type: ContentType, market: Market, sku: string) {
  const checks: QualityCheck[] = [];
  const prohibitedPattern = new RegExp(rules.risk_patterns.join("|"), "i");
  const prohibited = firstMatch(text.normalize("NFKC"), prohibitedPattern);
  if (!text.trim()) checks.push({ id: "empty", name: "内容完整性", status: "fail", detail: "内容不能为空。" });
  checks.push({
    id: "fact-boundary",
    name: "事实与功效边界",
    status: prohibited ? "fail" : "pass",
    detail: prohibited ? "发现医疗化、保证性或超出证据边界的表述。" : "未命中已配置的风险表达；未执行通用语义核验。",
    suggestion: prohibited ? "改为 helps skin feel… / ayuda a que la piel se sienta… 等感受型表达。" : undefined,
    matchedText: prohibited,

  });
  const unsupportedIngredients = rules.ingredient_aliases;
  for (const [value, aliases] of Object.entries(unsupportedIngredients)) {
    const hit = aliases.find((alias) => new RegExp(`(?<![\\p{L}\\p{N}_])${alias}(?![\\p{L}\\p{N}_])`, "iu").test(text.normalize("NFKC")));
    if (hit && !facts.some((fact) => fact.sku === sku && fact.attribute === "ingredient" && fact.value === value && fact.status === "active")) {
      checks.push({ id: `ingredient-${value}`, name: "成分证据", status: "fail", matchedText: hit, detail: `当前 SKU 没有支持 ${hit} 的成分事实。`, suggestion: "删除该表述或补充并核实商品事实。" });
    }
  }
  checks.push(...packagingChecks(text, sku));
  let structure: Status = "pass";
  let structureDetail = "结构字段完整。";
  if (type === "product_listing") {
    const parsed = parseContent(text, type);
    structure = parsed.title && parsed.bullets.length === 5 && parsed.bullets.every((bullet) => bullet.trim()) && parsed.description ? "pass" : "fail";
    structureDetail = structure === "pass" ? "标题、5 个卖点和描述齐全。" : `当前识别到 ${parsed.bullets.length} 个卖点。`;
  } else if (type === "short_video_script") {
    structure = /\d{1,2}:\d{2}|\d+\s*[–-]\s*\d+\s*s/.test(text) && /CTA|consulta los detalles/i.test(text) ? "pass" : "fail";
    structureDetail = structure === "pass" ? "包含分镜时间与 CTA。" : "分镜时间或 CTA 不完整。";
  } else {
    structure = /^(HOOK|GANCHO):[ \t]*\S.*$/m.test(text) && /^(BODY|CUERPO|TEXTO):[ \t]*\S.*$/m.test(text) && /^CTA:[ \t]*\S.*$/m.test(text) ? "pass" : "fail";
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
  if (type === "product_listing") {
    const length = Array.from(parseContent(text, type).title).length;
    checks.push({ id: "length", name: "字符预检", status: length <= rules.listing_title_max ? "pass" : "fail", detail: `标题长度 ${length}/${rules.listing_title_max}。` });
  } else {
    checks.push({ id: "length", name: "字符预检", status: "not_checked", detail: "未配置平台字符/时长规则；请人工复核。" });
  }
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

