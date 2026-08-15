"""Post-model fact and packaging gates for confirmed Closed Beta imports."""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from collections import defaultdict
from typing import Any, Iterable

PACKAGING_TERMS: dict[str, dict[str, tuple[str, ...]]] = {
    "packaging_container": {
        "bottle": ("bottle", "botella", "envase pet", "envase de pp"),
        "pump bottle": (
            "pump bottle",
            "bottle with pump",
            "botella con bomba",
            "frasco con bomba",
            "envase con bomba",
        ),
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

ENGLISH_LANGUAGE_MARKERS = {
    "a",
    "an",
    "and",
    "apply",
    "barrier",
    "bottle",
    "cleanse",
    "cleanser",
    "container",
    "cotton",
    "daily",
    "do",
    "evening",
    "face",
    "for",
    "formulated",
    "free",
    "gently",
    "impurities",
    "in",
    "makeup",
    "morning",
    "no",
    "of",
    "or",
    "over",
    "pad",
    "repeat",
    "rinse",
    "sensitive",
    "shower",
    "skin",
    "soap",
    "supports",
    "that",
    "the",
    "to",
    "use",
    "water",
    "with",
    "without",
}
SPANISH_LANGUAGE_MARKERS = {
    "agua",
    "aplicar",
    "barrera",
    "con",
    "de",
    "del",
    "desmaquillante",
    "el",
    "en",
    "enjuague",
    "gel",
    "la",
    "las",
    "limpia",
    "limpiador",
    "los",
    "mañana",
    "noche",
    "o",
    "para",
    "piel",
    "rostro",
    "sensible",
    "sin",
    "suave",
    "un",
    "una",
    "uso",
    "y",
}
ENGLISH_GRAMMAR_MARKERS = {
    "a",
    "an",
    "and",
    "do",
    "for",
    "in",
    "no",
    "of",
    "or",
    "over",
    "that",
    "the",
    "to",
    "with",
    "without",
}

PRODUCT_CONCEPTS: dict[str, tuple[str, ...]] = {
    "serum": ("serum", "sérum"),
    "cleanser": ("cleanser", "limpiador", "limpiadora"),
    "micellar": ("micellar", "micelar"),
    "lotion": ("lotion", "loción"),
    "refill": ("refill", "recarga"),
}

SPANISH_LOCALIZATION_PATTERNS: tuple[tuple[str, str], ...] = (
    (
        r"\b(?:envase|formato|presentación)\s+refill\b",
        "untranslated generic refill construction",
    ),
    (r"\brefill\s+de\b", "untranslated refill construction"),
    (
        r"\b(?:posicionado|posicionada)\s+para\s+apoyar\b",
        "literal positioned-to-support calque",
    ),
    (r"\bapoyar\s+la\s+barrera\s+cutánea\b", "literal skin-barrier calque"),
)


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


def _claim_location_text(output: dict[str, Any], location: str) -> str | None:
    content = output["content"]
    scalar = re.fullmatch(r"content\.(title|description|caption|hook|body|cta)", location)
    if scalar:
        value = content.get(scalar.group(1))
        return value if isinstance(value, str) else None
    bullet = re.fullmatch(r"content\.bullet_points\[(\d+)]", location)
    if bullet:
        index = int(bullet.group(1))
        values = content.get("bullet_points") or []
        return values[index] if index < len(values) and isinstance(values[index], str) else None
    scene = re.fullmatch(r"content\.scenes\[(\d+)]\.(visual|voiceover|on_screen_text)", location)
    if scene:
        index = int(scene.group(1))
        values = content.get("scenes") or []
        if index < len(values):
            value = values[index].get(scene.group(2))
            return value if isinstance(value, str) else None
    return None


def _normalized_excerpt(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().casefold().rstrip(" .,:;!?")


def claim_traceability_findings(
    output: dict[str, Any], eligible_ids: set[str] | None = None
) -> list[str]:
    findings: list[str] = []
    covered_locations: set[str] = set()
    claims_by_location: dict[str, list[str]] = defaultdict(list)
    for claim in output["claims"]:
        if eligible_ids is not None and (
            not claim["fact_ids"]
            or any(fact_id not in eligible_ids for fact_id in claim["fact_ids"])
        ):
            findings.append(f"{claim['claim_id']} 引用了缺失或不可用事实")
        location_text = _claim_location_text(output, claim["location"])
        if location_text is None:
            findings.append(f"{claim['claim_id']} 的 location 无效或为空")
            continue
        covered_locations.add(claim["location"])
        claims_by_location[claim["location"]].append(claim["text"])
        if _normalized_excerpt(claim["text"]) not in _normalized_excerpt(location_text):
            findings.append(f"{claim['claim_id']} 的 text 不是 location 中的原文片段")
    if output["content_type"] == "product_listing":
        required_locations = {"content.title", "content.description"} | {
            f"content.bullet_points[{index}]"
            for index in range(len(output["content"]["bullet_points"]))
        }
        missing_locations = sorted(required_locations - covered_locations)
        if missing_locations:
            findings.append(f"缺少 claim 覆盖：{', '.join(missing_locations)}")
        for location in sorted(required_locations & covered_locations):
            location_text = _claim_location_text(output, location) or ""
            claimed_text = " ".join(claims_by_location[location])
            critical_expressions = re.findall(r"(?<!\d)\d+(?:\.\d+)?\s*m[lL]\b", location_text)
            for aliases in PRODUCT_CONCEPTS.values():
                critical_expressions.extend(
                    alias for alias in aliases if _contains(location_text, alias)
                )
            missing = [
                expression
                for expression in critical_expressions
                if not _contains(claimed_text, expression)
            ]
            if missing:
                findings.append(
                    f"{location} 的关键表达未被 claim text 覆盖：{', '.join(sorted(set(missing)))}"
                )
    return findings


def claim_semantic_support_findings(
    output: dict[str, Any], fact_by_id: dict[str, dict[str, Any]]
) -> list[str]:
    findings: list[str] = []
    for claim in output["claims"]:
        cited_facts = [
            fact_by_id[fact_id] for fact_id in claim["fact_ids"] if fact_id in fact_by_id
        ]
        cited_text = " ".join(
            " ".join(
                str(fact.get(field) or "") for field in ("value", "unit", "allowed_expression")
            )
            for fact in cited_facts
        )
        for concept, aliases in PRODUCT_CONCEPTS.items():
            if any(_contains(claim["text"], alias) for alias in aliases) and not any(
                _contains(cited_text, alias) for alias in aliases
            ):
                findings.append(f"{claim['claim_id']} 的 {concept} 表达未由所引事实支持")
        for capacity in re.findall(r"(?<!\d)\d+(?:\.\d+)?\s*m[lL]\b", claim["text"]):
            if _normalized_excerpt(capacity) not in _normalized_excerpt(cited_text):
                findings.append(f"{claim['claim_id']} 的容量 {capacity} 未由所引事实支持")
    return findings


def _fold_word(word: str) -> str:
    return "".join(
        character
        for character in unicodedata.normalize("NFKD", word.casefold())
        if not unicodedata.combining(character)
    )


def _consumer_locations(output: dict[str, Any]) -> Iterable[tuple[str, str]]:
    content = output["content"]
    for field in ("title", "description", "caption", "hook", "body", "cta"):
        value = content.get(field)
        if isinstance(value, str) and value.strip():
            yield f"content.{field}", value
    for index, value in enumerate(content.get("bullet_points") or []):
        if isinstance(value, str) and value.strip():
            yield f"content.bullet_points[{index}]", value
    for index, scene in enumerate(content.get("scenes") or []):
        for field in ("visual", "voiceover", "on_screen_text"):
            value = scene.get(field)
            if isinstance(value, str) and value.strip():
                yield f"content.scenes[{index}].{field}", value


def target_language_findings(output: dict[str, Any]) -> list[str]:
    expected = output["language"]
    findings: list[str] = []
    for location, text in _consumer_locations(output):
        words = [_fold_word(word) for word in re.findall(r"[A-Za-zÀ-ÖØ-öø-ÿ]+", text)]
        if len(words) < 4:
            continue
        english = sum(word in ENGLISH_LANGUAGE_MARKERS for word in words)
        spanish = sum(word in SPANISH_LANGUAGE_MARKERS for word in words)
        english_grammar = sum(word in ENGLISH_GRAMMAR_MARKERS for word in words)
        ingredient_only = text.count(";") >= 3 and english_grammar < 2 and spanish < 2
        if ingredient_only:
            continue
        unexpected = (expected == "es-MX" and english >= 2 and english >= spanish + 2) or (
            expected == "en-US" and spanish >= 2 and spanish >= english + 2
        )
        if expected == "es-MX" and re.search(r"\brefill\s+container\b", text, flags=re.I):
            unexpected = True
        matched_pattern = next(
            (
                label
                for pattern, label in SPANISH_LOCALIZATION_PATTERNS
                if expected == "es-MX" and re.search(pattern, text, flags=re.I)
            ),
            None,
        )
        if matched_pattern:
            unexpected = True
        if unexpected:
            excerpt = re.sub(r"\s+", " ", text).strip()
            if len(excerpt) > 90:
                excerpt = excerpt[:87] + "..."
            reason = f"（{matched_pattern}）" if matched_pattern else ""
            findings.append(f"{location} 疑似主要使用非目标语言{reason}：{excerpt}")
    return findings


def unavailable_attribute_findings(
    output: dict[str, Any], unavailable_attributes: Iterable[str]
) -> list[str]:
    content_text = "\n".join(_content_strings(output["content"]))
    findings: list[str] = []
    for attribute in unavailable_attributes:
        if attribute in PACKAGING_TERMS:
            hits = sorted(
                {
                    term
                    for terms in PACKAGING_TERMS[attribute].values()
                    for term in terms
                    if _contains(content_text, term)
                }
            )
            if hits:
                findings.append(
                    f"{attribute} is unavailable but consumer copy uses: {', '.join(hits)}"
                )
        elif attribute == "packaging_capacity" and re.search(
            r"(?<!\d)\d+(?:\.\d+)?\s*m[lL]\b", content_text
        ):
            findings.append("packaging_capacity is unavailable but consumer copy states a capacity")
    return findings


def evaluate_beta_output(
    confirmed_import: dict[str, Any], output: dict[str, Any]
) -> dict[str, Any]:
    sku = output["sku"]
    market = output["market"]
    facts = [
        fact
        for fact in confirmed_import["facts"]
        if fact["sku"] == sku and market in fact["markets"]
    ]
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

    if output["status"] == "insufficient_information":
        detail = "；".join(output["insufficient_information"]) or "模型未提供可评审候选。"
        return {
            "checks": [
                {"name": "信息充分性", "status": "fail", "detail": detail, "category": "fact"}
            ],
            "summary": {"pass": 0, "fail": 1},
            "export_gate": "blocked",
            "human_review_required": True,
            "output_digest": hashlib.sha256(
                json.dumps(output, ensure_ascii=False, sort_keys=True).encode()
            ).hexdigest(),
            "eligible_fact_ids": sorted(eligible_ids),
            "referenced_fact_ids": [],
        }

    claim_findings = claim_traceability_findings(output, eligible_ids)
    claim_findings.extend(claim_semantic_support_findings(output, by_id))
    checks.append(
        {
            "name": "声明证据绑定",
            "status": "fail" if claim_findings else "pass",
            "detail": "；".join(claim_findings)
            if claim_findings
            else "声明事实、原文片段和内容位置均可追溯。",
            "category": "fact",
        }
    )

    content_text = "\n".join(_content_strings(output["content"]))
    prohibited_hits: list[str] = []
    for fact in facts:
        if fact["attribute"] == "prohibited_claim" or fact["generation_policy"] == "blocked":
            for expression in (fact["value"], fact["prohibited_expression"]):
                if (
                    expression
                    and expression.lower() != "unknown"
                    and _contains(content_text, expression)
                ):
                    prohibited_hits.append(expression)
    checks.append(
        {
            "name": "禁止宣称",
            "status": "fail" if prohibited_hits else "pass",
            "detail": f"命中：{', '.join(sorted(set(prohibited_hits)))}"
            if prohibited_hits
            else "未命中导入项目的禁止表达。",
            "category": "fact",
        }
    )

    facts_by_attribute: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for fact in facts:
        facts_by_attribute[fact["attribute"]].append(fact)
    packaging_findings: list[str] = []
    for attribute, candidates in PACKAGING_TERMS.items():
        supported_facts = [
            fact
            for fact in facts_by_attribute.get(attribute, [])
            if fact["fact_id"] in eligible_ids
        ]
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
        if fact["attribute"] in {"packaging_capacity", "specification"}
        and fact["fact_id"] in eligible_ids
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
        fact["fact_id"]
        for fact in facts
        if fact["attribute"].startswith("packaging_") or fact["attribute"] == "specification"
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
            "detail": "；".join(packaging_findings)
            if packaging_findings
            else "包装容器、材质与容量均受当前项目事实支持。",
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
            "detail": "；".join(structure_findings)
            if structure_findings
            else "目标内容结构完整，且未泄漏内部事实 ID。",
            "category": "platform",
        }
    )

    language_findings = target_language_findings(output)
    checks.append(
        {
            "name": "目标语言硬门禁",
            "status": "fail" if language_findings else "pass",
            "detail": "；".join(language_findings)
            if language_findings
            else "消费者可见自然语言与任务目标语言一致。",
            "category": "localization",
        }
    )

    failed = [check for check in checks if check["status"] == "fail"]
    return {
        "checks": checks,
        "summary": {"pass": len(checks) - len(failed), "fail": len(failed)},
        "export_gate": "blocked" if failed else "human_review",
        "human_review_required": True,
        "output_digest": hashlib.sha256(
            json.dumps(output, ensure_ascii=False, sort_keys=True).encode()
        ).hexdigest(),
        "eligible_fact_ids": sorted(eligible_ids),
        "referenced_fact_ids": sorted(
            {
                fact_id
                for claim in output["claims"]
                for fact_id in claim["fact_ids"]
                if fact_id in by_id
            }
        ),
    }
