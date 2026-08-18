import Papa from "papaparse";
import readXlsxFile from "read-excel-file/browser";

export const IMPORT_COLUMNS = [
  "sku",
  "attribute",
  "value",
  "unit",
  "evidence_level",
  "source",
  "source_type",
  "market_scope",
  "allowed_expression",
  "prohibited_expression",
  "generation_policy",
] as const;

export type ImportedProductFact = Record<(typeof IMPORT_COLUMNS)[number], string> & {
  fact_id: string;
};

export type ImportResult = {
  facts: ImportedProductFact[];
  warnings: string[];
};

const MAX_UPLOAD_BYTES = 2 * 1024 * 1024;
const MAX_ROWS = 50;
const SKU_PATTERN = /^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$/;
const ATTRIBUTES = new Set([
  "product_name",
  "specification",
  "ingredient",
  "usage_instruction",
  "packaging_container",
  "packaging_material",
  "packaging_capacity",
  "allowed_claim",
  "prohibited_claim",
]);
const EVIDENCE_LEVELS = new Set(["A", "B", "C", "U"]);
const SOURCE_TYPES = new Set(["primary_spec", "label", "testing_report", "brand_policy", "legal_review", "participant_statement", "unknown"]);
const MARKET_SCOPES = new Set(["US", "MX", "US;MX"]);
const POLICIES = new Set(["direct", "cautious", "blocked", "not_directly_usable"]);
const DANGEROUS_PREFIXES = ["=", "+", "-", "@"];

type Cell = string | number | boolean | Date | null | undefined;

function asText(value: Cell) {
  if (value == null) return "";
  if (value instanceof Date) return value.toISOString();
  return String(value).trim();
}

function locateTable(rows: Cell[][]) {
  const headerIndex = rows.findIndex((row) => {
    const values = row.map(asText);
    if (values[0]?.charCodeAt(0) === 0xfeff) values[0] = values[0].slice(1);
    return IMPORT_COLUMNS.every((column, index) => values[index] === column);
  });
  if (headerIndex < 0) throw new Error("没有找到模板中的表头。请直接使用页面提供的模板，并保留第一行列名不变。");

  const header = rows[headerIndex].map(asText);
  if (header.filter(Boolean).length !== IMPORT_COLUMNS.length) {
    throw new Error("表格列数与模板不一致，请删除额外的列后重试。");
  }
  return rows.slice(headerIndex + 1).filter((row) => {
    if (!row.some((cell) => asText(cell))) return false;
    const firstCell = asText(row[0]);
    const hasTemplateData = row.slice(1, IMPORT_COLUMNS.length).some((cell) => asText(cell));
    return SKU_PATTERN.test(firstCell) || hasTemplateData;
  });
}

function validateRows(rows: Cell[][]): ImportResult {
  if (!rows.length) throw new Error("表格中没有商品资料。");
  if (rows.length > MAX_ROWS) throw new Error(`一次最多导入 ${MAX_ROWS} 行商品资料。`);

  const facts: ImportedProductFact[] = rows.map((cells, rowIndex) => {
    if (cells.slice(IMPORT_COLUMNS.length).some((cell) => asText(cell))) {
      throw new Error(`第 ${rowIndex + 1} 条资料包含模板之外的列。`);
    }
    const values = IMPORT_COLUMNS.map((_, index) => asText(cells[index]));
    const row = Object.fromEntries(IMPORT_COLUMNS.map((column, index) => [column, values[index]])) as Omit<ImportedProductFact, "fact_id">;
    const displayRow = rowIndex + 1;

    if (!SKU_PATTERN.test(row.sku)) throw new Error(`第 ${displayRow} 条资料的商品编号格式不正确。`);
    if (!ATTRIBUTES.has(row.attribute)) throw new Error(`第 ${displayRow} 条资料的“资料类型”不在模板示例范围内。`);
    if (!row.value) throw new Error(`第 ${displayRow} 条资料的“内容”不能为空。`);
    if (!EVIDENCE_LEVELS.has(row.evidence_level)) throw new Error(`第 ${displayRow} 条资料的可信程度应填写 A、B、C 或 U。`);
    if (!row.source) throw new Error(`第 ${displayRow} 条资料需要填写来源。`);
    if (!SOURCE_TYPES.has(row.source_type)) throw new Error(`第 ${displayRow} 条资料的来源类别不在模板示例范围内。`);
    if (!MARKET_SCOPES.has(row.market_scope)) throw new Error(`第 ${displayRow} 条资料的适用市场应填写 US、MX 或 US;MX。`);
    if (!POLICIES.has(row.generation_policy)) throw new Error(`第 ${displayRow} 条资料的使用方式不在模板示例范围内。`);
    if (row.attribute === "prohibited_claim" && row.generation_policy !== "blocked") {
      throw new Error(`第 ${displayRow} 条资料属于“不要使用的表达”，使用方式必须填写 blocked。`);
    }
    for (const value of Object.values(row)) {
      if (DANGEROUS_PREFIXES.some((prefix) => value.startsWith(prefix))) {
        throw new Error(`第 ${displayRow} 条资料中有内容以 ${value[0]} 开头。为避免表格公式风险，请改成普通文字。`);
      }
    }
    return { ...row, fact_id: `UPLOAD-${row.sku}-${String(displayRow).padStart(3, "0")}` };
  });

  const warnings: string[] = [];
  for (const sku of [...new Set(facts.map((fact) => fact.sku))]) {
    const skuFacts = facts.filter((fact) => fact.sku === sku);
    const attributes = new Set(skuFacts.map((fact) => fact.attribute));
    if (!attributes.has("product_name")) warnings.push(`${sku} 没有填写商品名称，页面会暂时使用商品编号。`);
    if (!attributes.has("allowed_claim")) warnings.push(`${sku} 没有填写可用卖点，草稿中会提示补充资料。`);
    if (skuFacts.some((fact) => fact.evidence_level === "C" || fact.evidence_level === "U")) warnings.push(`${sku} 含有待核对或未确认的资料，请在下载前再次确认。`);
  }
  return { facts, warnings };
}

export async function parseProductFile(file: File): Promise<ImportResult> {
  if (file.size > MAX_UPLOAD_BYTES) throw new Error("文件超过 2 MB，请减少行数或图片后重试。");
  const extension = file.name.split(".").pop()?.toLowerCase();
  let rows: Cell[][];

  if (extension === "csv") {
    const parsed = Papa.parse<Cell[]>(await file.text(), { skipEmptyLines: "greedy" });
    if (parsed.errors.length) throw new Error(`CSV 无法读取：${parsed.errors[0].message}`);
    rows = parsed.data;
  } else if (extension === "xlsx") {
    const sheets = await readXlsxFile(file);
    const matchingSheet = sheets.find((sheet) => sheet.data.some((row) => row.map(asText).slice(0, IMPORT_COLUMNS.length).every((value, index) => value === IMPORT_COLUMNS[index])));
    if (!matchingSheet) throw new Error("没有找到模板中的资料页。请保留 XLSX 模板里的“SKU Facts”工作表和表头。");
    rows = matchingSheet.data;
  } else {
    throw new Error("目前支持 CSV 或 XLSX 文件。");
  }

  return validateRows(locateTable(rows));
}

function valuesFor(facts: ImportedProductFact[], attribute: string, market?: "US" | "MX") {
  return facts
    .filter((fact) => fact.attribute === attribute && fact.generation_policy !== "blocked" && (!market || !fact.market_scope || fact.market_scope.split(";").includes(market)))
    .map((fact) => fact.allowed_expression || `${fact.value}${fact.unit ? ` ${fact.unit}` : ""}`);
}

export function buildImportedContent(facts: ImportedProductFact[], market: "US" | "MX", type: "product_listing" | "short_video_script" | "social_ad_copy") {
  const sku = facts[0]?.sku ?? "UPLOADED-SKU";
  const name = valuesFor(facts, "product_name", market)[0] || sku;
  const details = [
    ...valuesFor(facts, "allowed_claim", market),
    ...valuesFor(facts, "ingredient", market).map((value) => `${market === "MX" ? "Ingredientes indicados" : "Listed ingredients"}: ${value}`),
    ...valuesFor(facts, "specification", market),
    ...valuesFor(facts, "packaging_capacity", market),
    ...valuesFor(facts, "packaging_container", market),
  ];
  const usage = valuesFor(facts, "usage_instruction", market)[0];
  const fallback = market === "MX" ? "Añade más información verificada en la plantilla." : "Add more verified information in the template.";
  const claim = details[0] || fallback;

  if (type === "product_listing") {
    const bulletLabel = market === "MX" ? "PUNTO" : "BULLET";
    const descriptionLabel = market === "MX" ? "DESCRIPCIÓN" : "DESCRIPTION";
    const titleLabel = market === "MX" ? "TÍTULO" : "TITLE";
    const bullets = Array.from({ length: 5 }, (_, index) => details[index] || (index === 4 && usage ? usage : fallback));
    return {
      baseline: `${titleLabel}: ${name}\n${descriptionLabel}: ${facts.map((fact) => fact.value).join("; ")}`,
      enhanced: [`${titleLabel}: ${name}`, ...bullets.map((value, index) => `${bulletLabel} ${index + 1}: ${value}`), `${descriptionLabel}: ${usage || claim}`].join("\n"),
    };
  }

  if (type === "short_video_script") {
    return {
      baseline: `${name}\n${facts.map((fact) => fact.value).join("; ")}`,
      enhanced: [`00:00–00:03 · ${name}`, `00:03–00:08 · ${claim}`, `00:08–00:12 · ${usage || details[1] || fallback}`, `00:12–00:15 · CTA: ${market === "MX" ? "Consulta los detalles" : "See product details"}`].join("\n"),
    };
  }

  return {
    baseline: `${name}\n${facts.map((fact) => fact.value).join("; ")}`,
    enhanced: [`${market === "MX" ? "GANCHO" : "HOOK"}: ${name}`, `${market === "MX" ? "TEXTO" : "BODY"}: ${claim}`, `CTA: ${market === "MX" ? "Consulta los detalles" : "See product details"}`].join("\n"),
  };
}
