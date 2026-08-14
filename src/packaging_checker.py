"""Deterministic, evidence-bound packaging gates for LocalizeFlow."""

from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PACKAGING_FACTS_PATH = PROJECT_ROOT / "data" / "products" / "packaging_facts.json"

TERM_FIELDS: dict[str, dict[str, tuple[str, ...]]] = {
    "container_type": {
        "bottle": ("bottle", "botella", "envase pet", "envase opaco de pp", "envase de pp"),
        "jar": ("jar", "tarro", "frasco"),
        "tube": ("tube", "tubo"),
    },
    "material": {
        "PET": ("pet bottle", "pet plastic", "botella pet", "envase pet", "plástico pet"),
        "PP": ("pp bottle", "pp jar", "pp plastic", "botella de pp", "tarro de pp", "envase de pp", "envase opaco de pp", "plástico pp"),
        "aluminum": ("aluminum", "aluminium", "aluminio"),
        "glass": ("glass", "vidrio", "cristal"),
    },
    "dispenser": {"pump": ("pump", "bomba", "dosificador")},
    "closure": {"screw cap": ("screw cap", "tapa roscada", "tapón de rosca")},
    "cap_material": {
        "PP": ("pp cap", "cap made of pp", "tapa de pp", "tapón de pp"),
        "glass": ("glass cap", "tapa de vidrio"),
    },
    "inner_lid": {"present": ("inner lid", "tapa interior")},
    "transparency": {
        "opaque": ("opaque", "opaca", "opaco"),
        "transparent": ("transparent", "transparente", "clear bottle", "botella transparente"),
    },
    "outer_container": {"paper box": ("paper box", "caja de papel", "carton box", "caja de cartón")},
}


@lru_cache(maxsize=1)
def packaging_dataset() -> dict[str, Any]:
    with PACKAGING_FACTS_PATH.open(encoding="utf-8") as handle:
        return json.load(handle)


def packaging_facts(sku: str, market: str | None = None) -> list[dict[str, Any]]:
    facts = packaging_dataset()["products"][sku]["facts"]
    if market is None:
        return facts
    return [fact for fact in facts if market in fact["market_scope"]]


def pre_generation_gate(sku: str, requested_fields: list[str], market: str) -> dict[str, Any]:
    available = {fact["field"]: fact for fact in packaging_facts(sku, market)}
    missing = [field for field in requested_fields if field not in available]
    return {
        "status": "blocked" if missing else "pass",
        "unknown_fields": missing,
        "fact_ids": sorted({available[field]["fact_id"] for field in requested_fields if field in available}),
        "detail": "缺少证据的包装字段视为 unknown，不允许推断。" if missing else "请求字段均有可追溯证据。",
    }


def _mentions(text: str, terms: tuple[str, ...]) -> list[str]:
    return [term for term in terms if re.search(rf"(?<!\w){re.escape(term)}(?!\w)", text, flags=re.I)]


def check_packaging_text(sku: str, text: str, market: str) -> dict[str, Any]:
    facts = packaging_facts(sku, market)
    by_field = {fact["field"]: fact for fact in facts}
    component_fact = by_field.get("components")
    findings: list[dict[str, Any]] = []

    for field, values in TERM_FIELDS.items():
        for candidate, terms in values.items():
            hits = _mentions(text, terms)
            if not hits:
                continue
            expected_fact = by_field.get(field)
            component_values = {
                str(item[field])
                for item in (component_fact["value"] if component_fact else [])
                if field in item
            }
            if expected_fact is None and candidate in component_values:
                continue
            if expected_fact is None and component_values and component_fact:
                findings.append({
                    "field": field, "status": "contradicted", "matched_text": hits[0],
                    "expected": sorted(component_values), "replacement": "",
                    "fact_ids": [component_fact["fact_id"]], "source": component_fact["source"],
                })
            elif expected_fact is None:
                findings.append({
                    "field": field, "status": "unsupported", "matched_text": hits[0],
                    "expected": "unknown", "replacement": "", "fact_ids": [], "source": "",
                })
            elif expected_fact["value"] != candidate:
                replacement = str(expected_fact["value"])
                findings.append({
                    "field": field, "status": "contradicted", "matched_text": hits[0],
                    "expected": expected_fact["value"], "replacement": replacement,
                    "fact_ids": [expected_fact["fact_id"]], "source": expected_fact["source"],
                })

    capacity_facts = [fact for fact in facts if fact["field"] in {"capacity", "total_capacity"}]
    allowed_capacities = {float(fact["value"]) for fact in capacity_facts}
    if component_fact:
        allowed_capacities.update(float(item["capacity"]) for item in component_fact["value"])
    for match in re.finditer(r"(?<!\d)(\d+(?:\.\d+)?)\s*m[lL]\b", text):
        value = float(match.group(1))
        if value not in allowed_capacities:
            expected_capacities = sorted(allowed_capacities)
            evidence = capacity_facts or ([component_fact] if component_fact else [])
            findings.append({
                "field": "capacity", "status": "contradicted" if evidence else "unsupported",
                "matched_text": match.group(0), "expected": expected_capacities or "unknown",
                "replacement": f"{expected_capacities[0]:g} mL" if len(expected_capacities) == 1 else "",
                "fact_ids": sorted({fact["fact_id"] for fact in evidence}),
                "source": ", ".join(sorted({fact["source"] for fact in evidence})),
            })

    return {
        "status": "blocked" if findings else "pass",
        "findings": findings,
        "checked_fact_ids": sorted({fact["fact_id"] for fact in facts}),
        "detail": "发现无证据或与事实冲突的包装表述。" if findings else "包装表述与字段级事实一致。",
    }
