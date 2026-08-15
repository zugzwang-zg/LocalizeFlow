"""Post-model fact and packaging gates for confirmed Closed Beta imports."""

from __future__ import annotations

import hashlib
import json
import re
from collections import defaultdict
from typing import Any, Iterable

PACKAGING_TERMS: dict[str, dict[str, tuple[str, ...]]] = {
    "packaging_container": {
        "bottle": ("bottle", "botella", "envase pet", "envase de pp"),
        "pump bottle": ("pump bottle", "bottle with pump", "botella con bomba", "frasco con bomba", "envase con bomba"),
        "jar": ("jar", "tarro"),
        "tube": ("tube", "tubo"),
    },
    "packaging_material": {
        "PET": ("pet bottle", "botella pet", "envase pet"),
        "PP": ("pp bottle", "pp jar", "botella de pp", "tarro de pp", "envase de pp"),
        "aluminum": ("aluminum", "aluminium", "aluminio"),
        "glass": ("glass", "vidrio", "cristal"),
    },
}


def _content_strings(value: Any) -> Iterable[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, list):
        for item in value:
            yield from _content_strings(item)
    elif isinstance(value, dict):
        for item in value.values():
            yield from _content_strings(item)


def _contains(text: str, term: str) -> bool:
    return bool(re.search(rf"(?<!\w){re.escape(term)}(?!\w)", text, flags=re.I))


def evaluate_beta_output(confirmed_import: dict[str, Any], output: dict[str, Any]) -> dict[str, Any]:
    sku = output["sku"]
    market = output["market"]
    facts = [fact for fact in confirmed_import["facts"] if fact["sku"] == sku and market in fact["markets"]]
    by_id = {fact["fact_id"]: fact for fact in facts}
    eligible_ids = {
        fact["fact_id"]
        for fact in facts
        if fact["status"] == "confirmed"
        and fact["evidence_level"] in {"A", "B"}
        and fact["generation_policy"] in {"direct", "cautious"}
        and fact["value"].lower() != "unknown"
    }
    checks: list[dict[str, Any]] = []

    bad_claims = [
        claim["claim_id"]
        for claim in output["claims"]
        if not claim["fact_ids"] or any(fact_id not in eligible_ids for fact_id in claim["fact_ids"])
    ]
    checks.append(
        {
            "name": "声明证据绑定",
            "status": "fail" if bad_claims else "pass",
            "detail": f"无效声明：{', '.join(bad_claims)}" if bad_claims else "所有可验证声明只引用当前项目的 A/B 级已确认事实。",
            "category": "fact",
        }
    )

    content_text = "\n".join(_content_strings(output["content"]))
    prohibited_hits: list[str] = []
    for fact in facts:
        if fact["attribute"] == "prohibited_claim" or fact["generation_policy"] == "blocked":
            for expression in (fact["value"], fact["prohibited_expression"]):
                if expression and expression.lower() != "unknown" and _contains(content_text, expression):
                    prohibited_hits.append(expression)
    checks.append(
        {
            "name": "禁止宣称",
            "status": "fail" if prohibited_hits else "pass",
            "detail": f"命中：{', '.join(sorted(set(prohibited_hits)))}" if prohibited_hits else "未命中导入项目的禁止表达。",
            "category": "fact",
        }
    )

    facts_by_attribute: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for fact in facts:
        facts_by_attribute[fact["attribute"]].append(fact)
    packaging_findings: list[str] = []
    for attribute, candidates in PACKAGING_TERMS.items():
        supported_facts = [fact for fact in facts_by_attribute.get(attribute, []) if fact["fact_id"] in eligible_ids]
        supported_candidates = {
            candidate.casefold()
            for candidate, terms in candidates.items()
            if any(
                fact["value"].casefold() == candidate.casefold()
                or any(_contains(fact["value"], term) for term in terms)
                for fact in supported_facts
            )
        }
        for candidate, terms in candidates.items():
            hit = next((term for term in terms if _contains(content_text, term)), None)
            if hit and candidate.casefold() not in supported_candidates:
                expected = " / ".join(fact["value"] for fact in supported_facts) or "unknown"
                packaging_findings.append(f"{attribute}: “{hit}” 与已确认值 {expected} 不一致")

    capacity_facts = [
        fact
        for fact in facts
        if fact["attribute"] in {"packaging_capacity", "specification"} and fact["fact_id"] in eligible_ids
    ]
    allowed_capacities = {
        float(match.group(1))
        for fact in capacity_facts
        if (match := re.search(r"(\d+(?:\.\d+)?)", fact["value"]))
    }
    for match in re.finditer(r"(?<!\d)(\d+(?:\.\d+)?)\s*m[lL]\b", content_text):
        if float(match.group(1)) not in allowed_capacities:
            packaging_findings.append(f"packaging_capacity: “{match.group(0)}” 无匹配事实")

    packaging_fact_ids = {
        fact["fact_id"] for fact in facts if fact["attribute"].startswith("packaging_") or fact["attribute"] == "specification"
    }
    for claim in output["claims"]:
        packaging_language = any(
            _contains(claim["text"], term)
            for values in PACKAGING_TERMS.values()
            for terms in values.values()
            for term in terms
        ) or bool(re.search(r"(?<!\d)\d+(?:\.\d+)?\s*m[lL]\b", claim["text"]))
        if packaging_language and not (set(claim["fact_ids"]) & packaging_fact_ids):
            packaging_findings.append(f"{claim['claim_id']} 的包装表述未绑定包装/规格事实")
    checks.append(
        {
            "name": "包装事实硬门禁",
            "status": "fail" if packaging_findings else "pass",
            "detail": "；".join(packaging_findings) if packaging_findings else "包装容器、材质与容量均受当前项目事实支持。",
            "category": "fact",
        }
    )

    structure_findings: list[str] = []
    content = output["content"]
    if output["content_type"] == "product_listing":
        if not content["title"] or len(content["bullet_points"]) != 5 or not content["description"]:
            structure_findings.append("目标内容类型的必填结构不完整。")
    elif output["content_type"] == "short_video_script":
        if not content["scenes"] or not content["caption"]:
            structure_findings.append("目标内容类型的必填结构不完整。")
    else:
        if not content["hook"] or not content["body"] or not content["cta"]:
            structure_findings.append("目标内容类型的必填结构不完整。")
    if re.search(r"\bBETA-[A-Z0-9-]+\b", content_text, flags=re.I):
        structure_findings.append("消费者可见内容泄漏了内部事实 ID。")
    checks.append(
        {
            "name": "内容结构",
            "status": "fail" if structure_findings else "pass",
            "detail": "；".join(structure_findings) if structure_findings else "目标内容结构完整，且未泄漏内部事实 ID。",
            "category": "platform",
        }
    )

    failed = [check for check in checks if check["status"] == "fail"]
    return {
        "checks": checks,
        "summary": {"pass": len(checks) - len(failed), "fail": len(failed)},
        "export_gate": "blocked" if failed else "human_review",
        "human_review_required": True,
        "output_digest": hashlib.sha256(json.dumps(output, ensure_ascii=False, sort_keys=True).encode()).hexdigest(),
        "eligible_fact_ids": sorted(eligible_ids),
        "referenced_fact_ids": sorted({fact_id for claim in output["claims"] for fact_id in claim["fact_ids"] if fact_id in by_id}),
    }
