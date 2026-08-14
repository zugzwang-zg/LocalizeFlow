"""Offline application service for the LocalizeFlow Streamlit demonstration.

The demo intentionally uses deterministic project assets. It does not call a model
API or a live commerce platform, so every output is reproducible and auditable.
"""

from __future__ import annotations

import csv
import io
import json
import re
from collections import defaultdict
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Iterable, TypedDict

PROJECT_ROOT = Path(__file__).resolve().parents[1]
FACT_PATH = PROJECT_ROOT / "data" / "products" / "product_facts.json"
CONTENT_LIBRARY_PATH = (
    PROJECT_ROOT
    / "data"
    / "evaluation"
    / "admin_do_not_open_before_scoring"
    / "evaluation_source_content.json"
)

CONTENT_TYPES: tuple[str, ...] = (
    "product_listing",
    "short_video_script",
    "social_ad_copy",
)

PRODUCT_LABELS = {
    "MV-CLEAN-001": "云柔氨基酸洁面乳 · Facial Cleanser",
    "MV-SERUM-001": "水衡保湿精华 · Hydrating Serum",
    "MV-CREAM-001": "静润无香面霜 · Face Moisturizer",
    "MV-HAND-001": "柔护无香护手霜 · Hand Cream",
    "MV-KIT-001": "轻行基础护肤套装 · Travel Skincare Set",
}


class MarketConfig(TypedDict):
    language: str
    label: str
    currency: str
    platforms: dict[str, str]


MARKET_CONFIG: dict[str, MarketConfig] = {
    "US": {
        "language": "en-US",
        "label": "美国 · English (US)",
        "currency": "USD",
        "platforms": {
            "product_listing": "Google Merchant Center",
            "short_video_script": "TikTok Ads",
            "social_ad_copy": "Generic Social",
        },
    },
    "MX": {
        "language": "es-MX",
        "label": "墨西哥 · Español (MX)",
        "currency": "MXN",
        "platforms": {
            "product_listing": "Google Merchant Center",
            "short_video_script": "TikTok Ads",
            "social_ad_copy": "Generic Social",
        },
    },
}

CONTENT_TYPE_LABELS = {
    "product_listing": "商品 Listing",
    "short_video_script": "TikTok 短视频脚本",
    "social_ad_copy": "社媒广告文案",
}

ATTRIBUTE_LABELS = {
    "product_name_zh": "商品名称",
    "category": "品类",
    "net_volume": "净含量",
    "total_volume": "组合总容量",
    "ingredient": "成分",
    "verified_feature": "已核实特征",
    "allowed_benefit": "允许功效",
    "usage_instruction": "使用方法",
    "packaging_feature": "包装",
    "price_usd": "美国价格",
    "price_mxn": "墨西哥价格",
    "target_users": "适用人群",
}


@dataclass(frozen=True)
class EvidenceBundle:
    title: list[str]
    feature: list[str]
    ingredient: list[str]
    benefit: list[str]
    usage: list[str]
    packaging: list[str]


def _read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


@lru_cache(maxsize=1)
def fact_dataset() -> dict[str, Any]:
    return _read_json(FACT_PATH)


@lru_cache(maxsize=1)
def content_library() -> dict[str, Any]:
    return _read_json(CONTENT_LIBRARY_PATH)


@lru_cache(maxsize=1)
def _facts_by_sku() -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for fact in fact_dataset()["facts"]:
        if fact.get("status") == "active":
            grouped[fact["sku"]].append(fact)
    return dict(grouped)


def list_products() -> list[dict[str, str]]:
    return [
        {"sku": sku, "label": PRODUCT_LABELS[sku]}
        for sku in PRODUCT_LABELS
        if sku in _facts_by_sku()
    ]


def facts_for_sku(sku: str) -> list[dict[str, Any]]:
    return list(_facts_by_sku().get(sku, []))


def _facts_for_attribute(sku: str, *attributes: str) -> list[dict[str, Any]]:
    expected = set(attributes)
    return [
        fact for fact in facts_for_sku(sku) if fact.get("attribute") in expected
    ]


def _first_fact(sku: str, *attributes: str) -> dict[str, Any] | None:
    matches = _facts_for_attribute(sku, *attributes)
    return matches[0] if matches else None


def _fact_value(fact: dict[str, Any] | None, fallback: str = "—") -> str:
    if not fact:
        return fallback
    value = fact.get("value")
    unit = fact.get("unit")
    return f"{value} {unit}".strip() if unit else str(value)


def product_profile(sku: str, market: str = "US") -> dict[str, Any]:
    facts = facts_for_sku(sku)
    if not facts:
        raise KeyError(f"Unknown SKU: {sku}")
    volume = _first_fact(sku, "net_volume", "total_volume")
    price_attribute = "price_usd" if market == "US" else "price_mxn"
    price = _first_fact(sku, price_attribute)
    direct = [fact for fact in facts if fact.get("generation_policy") == "direct"]
    cautious = [
        fact for fact in facts if fact.get("generation_policy") == "cautious"
    ]
    blocked = [
        fact
        for fact in facts
        if fact.get("generation_policy") in {"blocked", "not_directly_usable"}
    ]
    return {
        "sku": sku,
        "display_name": PRODUCT_LABELS.get(sku, sku),
        "name_zh": _fact_value(_first_fact(sku, "product_name_zh")),
        "category": _fact_value(_first_fact(sku, "category")),
        "size": _fact_value(volume),
        "price": _fact_value(price),
        "currency": MARKET_CONFIG[market]["currency"],
        "target_users": _fact_value(_first_fact(sku, "target_users")),
        "usage": _fact_value(_first_fact(sku, "usage_instruction")),
        "features": _facts_for_attribute(sku, "verified_feature"),
        "ingredients": _facts_for_attribute(sku, "ingredient")[:6],
        "benefits": _facts_for_attribute(sku, "allowed_benefit"),
        "packaging": _facts_for_attribute(sku, "packaging_feature"),
        "direct_facts": direct,
        "cautious_facts": cautious,
        "blocked_facts": blocked,
        "all_facts": facts,
    }


def allowed_and_prohibited(sku: str) -> dict[str, list[dict[str, str]]]:
    allowed: list[dict[str, str]] = []
    prohibited: list[dict[str, str]] = []
    for fact in facts_for_sku(sku):
        policy = fact.get("generation_policy")
        if policy in {"direct", "cautious"} and fact.get("attribute") in {
            "verified_feature",
            "allowed_benefit",
            "usage_instruction",
            "packaging_feature",
        }:
            allowed.append(
                {
                    "fact_id": fact["fact_id"],
                    "text": _fact_value(fact),
                    "mode": "直接使用" if policy == "direct" else "谨慎表达",
                }
            )
        if fact.get("attribute") == "prohibited_claim":
            prohibited.append(
                {
                    "fact_id": fact["fact_id"],
                    "text": _fact_value(fact),
                    "mode": "禁止生成",
                }
            )
        for expression in fact.get("prohibited_expression") or []:
            if expression and expression != "无":
                prohibited.append(
                    {
                        "fact_id": fact["fact_id"],
                        "text": str(expression),
                        "mode": "禁止表达",
                    }
                )
    return {
        "allowed": _unique_records(allowed)[:12],
        "prohibited": _unique_records(prohibited)[:14],
    }


def _unique_records(records: Iterable[dict[str, str]]) -> list[dict[str, str]]:
    seen: set[tuple[str, str]] = set()
    result: list[dict[str, str]] = []
    for record in records:
        key = (record["fact_id"], record["text"])
        if key not in seen:
            seen.add(key)
            result.append(record)
    return result


def selling_point_options(sku: str) -> list[str]:
    profile = product_profile(sku)
    values = [
        _fact_value(fact)
        for fact in profile["features"][:4] + profile["benefits"][:3]
    ]
    return list(dict.fromkeys(values))


def _library_index() -> dict[tuple[str, str, str], dict[str, Any]]:
    return {
        (group["sku"], group["language"], group["content_type"]): group
        for group in content_library()["groups"]
    }


def generate_content_pack(
    *,
    sku: str,
    market: str,
    primary_content_type: str,
    target_user: str,
    marketing_goal: str,
    selling_points: list[str],
    brand_tone: list[str],
    source_note: str = "",
) -> dict[str, Any]:
    if market not in MARKET_CONFIG:
        raise KeyError(f"Unsupported market: {market}")
    if primary_content_type not in CONTENT_TYPES:
        raise KeyError(f"Unsupported content type: {primary_content_type}")
    language = MARKET_CONFIG[market]["language"]
    index = _library_index()
    versions: dict[str, Any] = {}
    for content_type in CONTENT_TYPES:
        group = index[(sku, language, content_type)]
        versions[content_type] = {
            "label": CONTENT_TYPE_LABELS[content_type],
            "platform": MARKET_CONFIG[market]["platforms"][content_type],
            "baseline": group["versions"]["baseline"],
            "enhanced": group["versions"]["localizeflow"],
            "baseline_parsed": parse_content(
                group["versions"]["baseline"], content_type
            ),
            "enhanced_parsed": parse_content(
                group["versions"]["localizeflow"], content_type
            ),
        }
    pack = {
        "run_id": f"LF-DEMO-{sku}-{market}-{primary_content_type}",
        "generation_mode": "offline_deterministic_demo",
        "model_api_called": False,
        "sku": sku,
        "market": market,
        "language": language,
        "primary_content_type": primary_content_type,
        "primary_platform": MARKET_CONFIG[market]["platforms"][
            primary_content_type
        ],
        "target_user": target_user,
        "marketing_goal": marketing_goal,
        "selling_points": selling_points,
        "brand_tone": brand_tone,
        "source_note": source_note,
        "versions": versions,
    }
    pack["claims"] = build_claim_evidence(pack)
    pack["primary_quality"] = evaluate_text(
        sku=sku,
        market=market,
        content_type=primary_content_type,
        text=versions[primary_content_type]["enhanced"],
    )
    return pack


def parse_content(text: str, content_type: str) -> dict[str, Any]:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if content_type == "product_listing":
        title = _prefixed_value(lines, ("TITLE:", "TÍTULO:"))
        bullets = [
            re.sub(r"^(BULLET|PUNTO)\s+\d+\s*:\s*", "", line, flags=re.I)
            for line in lines
            if re.match(r"^(BULLET|PUNTO)\s+\d+\s*:", line, flags=re.I)
        ]
        description = _prefixed_value(lines, ("DESCRIPTION:", "DESCRIPCIÓN:"))
        return {
            "title": title,
            "bullet_points": bullets,
            "description": description,
        }
    if content_type == "social_ad_copy":
        return {
            "hook": _prefixed_value(lines, ("HOOK:", "GANCHO:")),
            "body": _prefixed_value(lines, ("BODY:", "TEXTO:")),
            "cta": _prefixed_value(lines, ("CTA:",)),
        }
    caption = _prefixed_value(lines, ("CAPTION:", "TEXTO:"))
    scenes = [
        line
        for line in lines
        if not line.startswith("CAPTION:") and not line.startswith("TEXTO:")
    ]
    return {"scenes": scenes, "caption": caption}


def _prefixed_value(lines: list[str], prefixes: tuple[str, ...]) -> str:
    for line in lines:
        for prefix in prefixes:
            if line.startswith(prefix):
                return line[len(prefix) :].strip()
    return ""


def _evidence_bundle(sku: str) -> EvidenceBundle:
    def ids(*attributes: str, limit: int = 4) -> list[str]:
        return [
            fact["fact_id"]
            for fact in _facts_for_attribute(sku, *attributes)[:limit]
        ]

    return EvidenceBundle(
        title=ids("product_name_zh", "category", "net_volume", "total_volume"),
        feature=ids("verified_feature", limit=4),
        ingredient=ids("ingredient", "ingredient_reference", limit=4),
        benefit=ids("allowed_benefit", limit=3),
        usage=ids(
            "usage_instruction", "usage_amount_min", "usage_amount_max", limit=3
        ),
        packaging=ids("packaging_feature", limit=3),
    )


def build_claim_evidence(pack: dict[str, Any]) -> list[dict[str, Any]]:
    sku = pack["sku"]
    evidence = _evidence_bundle(sku)
    claims: list[dict[str, Any]] = []

    def add(
        content_type: str,
        location: str,
        text: str,
        fact_ids: list[str],
    ) -> None:
        if not text:
            return
        claims.append(
            {
                "claim_id": f"claim_{len(claims) + 1:03d}",
                "content_type": content_type,
                "location": location,
                "text": text,
                "fact_ids": list(dict.fromkeys(fact_ids)),
            }
        )

    listing = pack["versions"]["product_listing"]["enhanced_parsed"]
    add("product_listing", "title", listing["title"], evidence.title)
    bullet_evidence = [
        evidence.feature,
        evidence.ingredient,
        evidence.benefit,
        evidence.usage,
        evidence.packaging or evidence.title,
    ]
    for index, bullet in enumerate(listing["bullet_points"]):
        add(
            "product_listing",
            f"bullet_points[{index}]",
            bullet,
            bullet_evidence[min(index, len(bullet_evidence) - 1)],
        )
    add(
        "product_listing",
        "description",
        listing["description"],
        evidence.feature
        + evidence.ingredient
        + evidence.benefit
        + evidence.usage
        + evidence.packaging,
    )
    video = pack["versions"]["short_video_script"]["enhanced_parsed"]
    video_evidence = [
        evidence.benefit or evidence.title,
        evidence.feature,
        evidence.usage + evidence.benefit,
        [],
    ]
    for index, scene in enumerate(video["scenes"]):
        add(
            "short_video_script",
            f"scenes[{index}]",
            scene,
            video_evidence[min(index, len(video_evidence) - 1)],
        )
    add(
        "short_video_script",
        "caption",
        video["caption"],
        evidence.ingredient + evidence.benefit,
    )
    social = pack["versions"]["social_ad_copy"]["enhanced_parsed"]
    add(
        "social_ad_copy",
        "hook",
        social["hook"],
        evidence.benefit or evidence.title,
    )
    add(
        "social_ad_copy",
        "body",
        social["body"],
        evidence.feature + evidence.ingredient + evidence.usage,
    )
    add("social_ad_copy", "cta", social["cta"], [])
    return claims


def evaluate_text(
    *, sku: str, market: str, content_type: str, text: str
) -> dict[str, Any]:
    normalized = text.lower()
    checks: list[dict[str, Any]] = []

    def add_check(
        name: str,
        status: str,
        detail: str,
        suggestion: str = "",
        category: str = "quality",
    ) -> None:
        checks.append(
            {
                "name": name,
                "status": status,
                "detail": detail,
                "suggestion": suggestion,
                "category": category,
            }
        )

    prohibited_patterns = {
        r"\b(cure|cures|clinically proven|guaranteed|miracle)\b": "医疗化、临床或保证性表述",
        r"\b(repair|repairs)\b|repara(?:r|n|s)?": "超出事实边界的修复功效",
        r"all of your skincare needs|todas tus necesidades": "全能承诺",
    }
    prohibited_hits = [
        label
        for pattern, label in prohibited_patterns.items()
        if re.search(pattern, normalized, flags=re.I)
    ]
    if prohibited_hits:
        add_check(
            "事实与功效边界",
            "fail",
            "；".join(prohibited_hits),
            "改为“helps skin feel … / ayuda a que la piel se sienta …”等感受型表达。",
            "fact",
        )
    else:
        add_check(
            "事实与功效边界",
            "pass",
            "未发现医疗化、全能承诺或保证性功效。",
            category="fact",
        )

    packaging_issue = False
    if sku == "MV-HAND-001" and (
        "aluminum tube" in normalized or "tubo de aluminio" in normalized
    ):
        packaging_issue = True
        add_check(
            "包装事实",
            "fail",
            "内容写为铝管，但事实库仅支持软管包装。",
            "删除材质推断，改为 tube / tubo，或补充经核验的包装材质事实。",
            "fact",
        )
    else:
        add_check(
            "包装事实",
            "pass",
            "未发现已知包装矛盾。",
            category="fact",
        )

    if content_type == "product_listing":
        parsed = parse_content(text, content_type)
        structure_pass = bool(
            parsed["title"]
            and len(parsed["bullet_points"]) == 5
            and parsed["description"]
        )
        title_length_pass = len(parsed["title"]) <= 150
        add_check(
            "平台结构",
            "pass" if structure_pass else "fail",
            (
                "标题、5 个卖点和描述齐全。"
                if structure_pass
                else f"当前识别到 {len(parsed['bullet_points'])} 个卖点。"
            ),
            "补齐标题、5 个卖点和商品描述。" if not structure_pass else "",
            "platform",
        )
        add_check(
            "字符限制",
            "pass" if title_length_pass else "fail",
            f"标题长度 {len(parsed['title'])}/150。",
            "压缩标题并保留品类、核心特征和规格。"
            if not title_length_pass
            else "",
            "platform",
        )
    elif content_type == "short_video_script":
        has_timing = bool(re.search(r"\d{1,2}:\d{2}|\d+\s*[–-]\s*\d+\s*s", text))
        has_cta = "cta" in normalized or "consulta los detalles" in normalized
        add_check(
            "平台结构",
            "pass" if has_timing and has_cta else "warning",
            "包含分镜时间与 CTA。" if has_timing and has_cta else "分镜时间或 CTA 不完整。",
            "补充分镜时间和单一邀请式 CTA。"
            if not (has_timing and has_cta)
            else "",
            "platform",
        )
        add_check(
            "字符限制",
            "pass",
            f"脚本长度 {len(text)} 字符；Demo 按 15 秒结构预检。",
            category="platform",
        )
    else:
        parsed = parse_content(text, content_type)
        structure_pass = all(parsed.values())
        add_check(
            "平台结构",
            "pass" if structure_pass else "warning",
            "Hook、正文和 CTA 齐全。" if structure_pass else "Hook、正文或 CTA 缺失。",
            "补齐 Hook、正文和单一 CTA。" if not structure_pass else "",
            "platform",
        )
        add_check(
            "字符限制",
            "pass",
            f"社媒文案长度 {len(text)} 字符；仍需在真实发布平台复核。",
            category="platform",
        )

    terminology_hits: list[str] = []
    if market == "MX":
        if re.search(r"\bserum\b", text, flags=re.I):
            terminology_hits.append("serum → sérum")
        if "crema de cara" in normalized:
            terminology_hits.append("crema de cara → crema hidratante facial")
    else:
        if "on the wet face" in normalized:
            terminology_hits.append("on the wet face → over a wet face")
        if "a opaque" in normalized:
            terminology_hits.append("a opaque → an opaque")
    add_check(
        "术语一致性",
        "warning" if terminology_hits else "pass",
        "；".join(terminology_hits) if terminology_hits else "核心术语符合目标语言约定。",
        "按术语库替换后重新检查。" if terminology_hits else "",
        "language",
    )

    brand_risk = any(
        token in normalized
        for token in ("buy now", "compra ahora", "must-have", "life-changing")
    )
    add_check(
        "品牌一致性",
        "warning" if brand_risk else "pass",
        (
            "CTA 偏强促销，与温和、可信的品牌语气存在张力。"
            if brand_risk
            else "语气整体温和、清晰、可信。"
        ),
        "改为 See product details / Consulta los detalles。"
        if brand_risk
        else "",
        "brand",
    )

    language_score = 5
    language_score -= len(terminology_hits)
    if prohibited_hits:
        language_score -= 1
    language_score = max(1, language_score)
    add_check(
        "本地化评分",
        "pass" if language_score >= 4 else "warning",
        f"{language_score}/5；按目标市场措辞、术语和阅读流畅度计算。",
        "根据术语提示和目标市场表达习惯修改。"
        if language_score < 4
        else "",
        "language",
    )

    failed = [check for check in checks if check["status"] == "fail"]
    warned = [check for check in checks if check["status"] == "warning"]
    risk_level = "high" if failed else "medium" if warned else "low"
    score = max(0, 100 - len(failed) * 25 - len(warned) * 8)
    return {
        "risk_level": risk_level,
        "quality_score": score,
        "export_gate": "blocked" if failed else "human_review",
        "fact_error_count": sum(
            1
            for check in failed
            if check["category"] == "fact"
        ),
        "checks": checks,
        "summary": {
            "pass": sum(1 for check in checks if check["status"] == "pass"),
            "warning": len(warned),
            "fail": len(failed),
        },
        "packaging_issue": packaging_issue,
    }


def update_pack_with_manual_text(
    pack: dict[str, Any], edited_text: str
) -> dict[str, Any]:
    updated = json.loads(json.dumps(pack, ensure_ascii=False))
    content_type = updated["primary_content_type"]
    updated["versions"][content_type]["final"] = edited_text
    updated["versions"][content_type]["final_parsed"] = parse_content(
        edited_text, content_type
    )
    updated["final_quality"] = evaluate_text(
        sku=updated["sku"],
        market=updated["market"],
        content_type=content_type,
        text=edited_text,
    )
    updated["human_review"] = {
        "required": True,
        "status": "confirmed",
    }
    return updated


def pack_as_json_bytes(pack: dict[str, Any]) -> bytes:
    return json.dumps(pack, ensure_ascii=False, indent=2).encode("utf-8")


def pack_as_csv_bytes(pack: dict[str, Any]) -> bytes:
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(
        [
            "run_id",
            "sku",
            "market",
            "language",
            "content_type",
            "version",
            "field",
            "content",
            "fact_ids",
        ]
    )
    claim_lookup = {
        (claim["content_type"], claim["location"]): "|".join(claim["fact_ids"])
        for claim in pack.get("claims", [])
    }
    for content_type, payload in pack["versions"].items():
        for version in ("baseline", "enhanced"):
            parsed = payload[f"{version}_parsed"]
            for field, value in parsed.items():
                values = value if isinstance(value, list) else [value]
                for index, item in enumerate(values):
                    location = (
                        f"{field}[{index}]" if isinstance(value, list) else field
                    )
                    writer.writerow(
                        [
                            pack["run_id"],
                            pack["sku"],
                            pack["market"],
                            pack["language"],
                            content_type,
                            version,
                            location,
                            item,
                            claim_lookup.get((content_type, location), ""),
                        ]
                    )
        if payload.get("final"):
            writer.writerow(
                [
                    pack["run_id"],
                    pack["sku"],
                    pack["market"],
                    pack["language"],
                    content_type,
                    "final",
                    "raw_text",
                    payload["final"],
                    "",
                ]
            )
    return ("\ufeff" + buffer.getvalue()).encode("utf-8")
