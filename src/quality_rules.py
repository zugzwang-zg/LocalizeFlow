"""Shared, bounded deterministic rules for public demos and the Beta gate."""

from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path
from typing import Any

RULES = json.loads(
    (Path(__file__).resolve().parents[1] / "data/rules/demo_quality_rules.json").read_text(
        encoding="utf-8"
    )
)


def risk_matches(text: str) -> list[str]:
    normalized = unicodedata.normalize("NFKC", text).lower()
    return [
        match.group()
        for pattern in RULES["risk_patterns"]
        if (match := re.search(pattern, normalized, flags=re.I))
    ]


def ingredient_findings(text: str, facts: list[dict[str, Any]]) -> list[str]:
    """Reject recognized ingredient mentions without eligible ingredient facts.

    This deliberately does not infer ingredients from product names or benefits,
    nor claim that an unrecognized substance has been semantically checked.
    """
    normalized = unicodedata.normalize("NFKC", text).lower()
    ingredient_values = [
        str(fact["value"]).lower()
        for fact in facts
        if fact["attribute"] == "ingredient" and fact.get("status") in {"active", "confirmed"}
    ]
    findings = []
    for value, aliases in RULES["ingredient_aliases"].items():
        hit = next(
            (
                alias
                for alias in aliases
                if re.search(r"(?<!\w)" + re.escape(alias) + r"(?!\w)", normalized)
            ),
            None,
        )
        if hit and not any(
            value == fact_value or fact_value in aliases for fact_value in ingredient_values
        ):
            findings.append(hit)
    return findings
