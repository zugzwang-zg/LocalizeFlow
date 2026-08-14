"""Claim-level fact checking for LocalizeFlow.

The checker is deliberately deterministic for identifiers, evidence gates,
numbers, units, market scope, and high-risk phrases. It does not rewrite content
or claim to replace legal, platform, or human review.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import unicodedata
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

CHECKER_VERSION = "1.0.0"
SUPPORTED_STATUSES = {
    "supported",
    "partially_supported",
    "unsupported",
    "contradicted",
    "subjective",
}
GENERATABLE_LEVELS = {"A", "B"}
CAUTIOUS_PATTERNS = {
    "en": (
        r"\bhelps?\b",
        r"\bskin (?:feel|feels)\b",
        r"\bmay help\b",
    ),
    "es": (
        r"\bayuda a\b",
        r"\bla piel se sient[ae]\b",
        r"\bpuede ayudar\b",
    ),
}
FACTUAL_CUES = (
    "serum",
    "sérum",
    "cream",
    "cleanser",
    "bottle",
    "pump",
    "ml",
    "usd",
    "mxn",
    "contains",
    "made with",
    "made without",
    "apply",
    "ingredient",
    "formula",
    "helps",
    "skin feel",
    "crema",
    "limpiador",
    "frasco",
    "dosis",
    "contiene",
    "sin fragancia",
    "aplica",
    "fórmula",
    "ayuda a",
    "la piel se siente",
)
HIGH_RISK_PATTERNS = {
    "medical_claim": (
        r"\bcures?\b",
        r"\btreats?\b.*\b(?:acne|eczema|disease|condition)\b",
        r"\bprevents?\b.*\bdisease\b",
        r"\bheals?\b",
        r"\bcur[ae]\b",
        r"\btrat[ae]\b.*\b(?:acné|eczema|enfermedad)\b",
        r"\bpreviene\b.*\benfermedad\b",
    ),
    "clinical_claim": (
        r"\bclinically proven\b",
        r"\bclinical(?:ly)? tested\b",
        r"\bclínicamente comprobado\b",
        r"\bpruebas clínicas\b",
    ),
    "regulatory_or_certification_claim": (
        r"\bfda[- ]approved\b",
        r"\bapproved by (?:the )?fda\b",
        r"\bcofepris\b",
        r"\bdermatologist[- ]tested\b",
        r"\bhypoallergenic\b",
        r"\bcertified\b",
        r"\baprobado por\b",
        r"\bhipoalergénic[oa]\b",
    ),
    "structure_function_claim": (
        r"\brepairs?\b.*\bskin barrier\b",
        r"\brebuilds?\b.*\bskin barrier\b",
        r"\brepara\b.*\bbarrera cutánea\b",
        r"\breconstruye\b.*\bbarrera cutánea\b",
    ),
    "anti_aging_claim": (
        r"\b(?:removes?|erases?)\b.*\b(?:wrinkles?|fine lines?)\b",
        r"\breverses?\b.*\baging\b",
        r"\b(?:elimina|borra)\b.*\b(?:arrugas|líneas de expresión)\b",
        r"\brevierte\b.*\benvejecimiento\b",
    ),
    "guarantee_or_absolute_claim": (
        r"\bguaranteed\b",
        r"\bmiracle\b",
        r"\bperfect skin\b",
        r"\b100%\s+safe\b",
        r"\bfor everyone\b",
        r"\bgarantizad[oa]\b",
        r"\bmilagros[oa]\b",
        r"\bpiel perfecta\b",
        r"\b100%\s+segur[oa]\b",
        r"\bpara todas las personas\b",
    ),
    "unsupported_duration_claim": (
        r"\b(?:24|72)[- ]?hour\b",
        r"\b(?:24|72)\s*horas\b",
    ),
}
NUMBER_PATTERN = re.compile(
    r"(?<![\w.])(?:[$€£]\s*)?(\d+(?:\.\d+)?)\s*"
    r"(m[lL]|USD|MXN|pumps?|doses?|seconds?|secs?|pH|horas?|hours?)?\b",
    re.IGNORECASE,
)
SENTENCE_SPLIT_PATTERN = re.compile(r"(?<=[.!?。！？])\s+")


def _normalize_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value)
    normalized = normalized.replace("–", "-").replace("—", "-")
    return re.sub(r"\s+", " ", normalized).strip().lower()


def _normalize_unit(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip().lower()
    aliases = {
        "ml": "ml",
        "pump": "pump",
        "pumps": "pump",
        "dose": "pump",
        "doses": "pump",
        "second": "second",
        "seconds": "second",
        "sec": "second",
        "secs": "second",
        "hour": "hour",
        "hours": "hour",
        "hora": "hour",
        "horas": "hour",
        "usd": "usd",
        "mxn": "mxn",
        "ph": "ph",
    }
    return aliases.get(normalized, normalized)


def _coerce_number(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    return None


def _numbers_equal(first: float, second: float) -> bool:
    return math.isclose(first, second, rel_tol=1e-9, abs_tol=1e-9)


def _language_family(language: str) -> str:
    return "es" if language.lower().startswith("es") else "en"


@dataclass(frozen=True)
class ContentUnit:
    location: str
    text: str


class FactRepository:
    """Load and index the LocalizeFlow product fact dataset."""

    def __init__(self, dataset: dict[str, Any], source_path: str) -> None:
        self.dataset = dataset
        self.source_path = source_path
        self.version = str(dataset.get("dataset_version", "unknown"))
        facts = dataset.get("facts")
        if not isinstance(facts, list):
            raise ValueError("Product fact dataset must contain a 'facts' array.")
        self.by_id: dict[str, dict[str, Any]] = {}
        for fact in facts:
            fact_id = fact.get("fact_id")
            if not fact_id:
                raise ValueError("Every fact must have a fact_id.")
            if fact_id in self.by_id:
                raise ValueError(f"Duplicate fact_id: {fact_id}")
            self.by_id[fact_id] = fact

    @classmethod
    def from_path(cls, path: str | Path) -> "FactRepository":
        resolved = Path(path)
        with resolved.open("r", encoding="utf-8") as handle:
            dataset = json.load(handle)
        return cls(dataset, str(resolved))

    def facts_for_sku(self, sku: str) -> list[dict[str, Any]]:
        return [fact for fact in self.by_id.values() if fact.get("sku") == sku]


class FactChecker:
    """Check declared and uncovered content claims against product facts."""

    def __init__(self, repository: FactRepository) -> None:
        self.repository = repository

    def check(self, content_record: dict[str, Any]) -> dict[str, Any]:
        sku = str(content_record.get("sku", ""))
        market = str(content_record.get("market", ""))
        language = str(content_record.get("language", "en-US"))
        content_version = content_record.get("content_version") or {}
        content_version_id = str(content_version.get("version_id", "unknown"))

        declared_claims = self._declared_claims(content_record)
        content_units = self._content_units(content_record)
        uncovered_claims = self._uncovered_claims(content_units, declared_claims)
        all_claims = declared_claims + uncovered_claims

        checked_claims = [
            self._check_claim(claim, sku=sku, market=market, language=language)
            for claim in all_claims
        ]
        factual_claims = [
            claim for claim in checked_claims if claim["status"] != "subjective"
        ]
        fact_errors = [
            claim
            for claim in factual_claims
            if claim["status"] in {"unsupported", "contradicted"}
        ]
        high_risk = [
            claim for claim in checked_claims if claim["risk_level"] == "high"
        ]
        review_items = [
            claim
            for claim in checked_claims
            if claim["risk_level"] in {"high", "medium"}
        ]
        numeric_claims = [
            claim for claim in checked_claims if claim["checks"]["numbers"]["detected"]
        ]

        if high_risk:
            gate_status = "blocked"
        elif review_items:
            gate_status = "needs_human_review"
        else:
            gate_status = "pass"

        denominator = len(factual_claims)
        error_rate = len(fact_errors) / denominator if denominator else 0.0
        now = datetime.now(timezone.utc).isoformat()
        return {
            "schema_version": "1.0",
            "checker_version": CHECKER_VERSION,
            "fact_check_id": f"factcheck_{content_version_id}",
            "checked_at": now,
            "sku": sku,
            "market": market,
            "language": language,
            "content_version_id": content_version_id,
            "fact_dataset": {
                "path": self.repository.source_path,
                "version": self.repository.version,
            },
            "claim_results": checked_claims,
            "summary": {
                "declared_claim_count": len(declared_claims),
                "auto_extracted_claim_count": len(uncovered_claims),
                "total_claim_count": len(checked_claims),
                "factual_claim_count": denominator,
                "subjective_claim_count": sum(
                    claim["status"] == "subjective" for claim in checked_claims
                ),
                "supported_count": sum(
                    claim["status"] == "supported" for claim in checked_claims
                ),
                "partially_supported_count": sum(
                    claim["status"] == "partially_supported"
                    for claim in checked_claims
                ),
                "unsupported_count": sum(
                    claim["status"] == "unsupported" for claim in checked_claims
                ),
                "contradicted_count": sum(
                    claim["status"] == "contradicted" for claim in checked_claims
                ),
                "high_risk_count": len(high_risk),
                "numeric_claim_count": len(numeric_claims),
                "numeric_claims_checked": len(numeric_claims),
                "fact_error_rate": round(error_rate, 6),
                "fact_error_rate_formula": (
                    "(unsupported + contradicted) / factual_claim_count"
                ),
            },
            "export_gate": {
                "status": gate_status,
                "export_allowed": False,
                "reason": self._gate_reason(gate_status, high_risk, review_items),
                "human_final_review_required": True,
                "quality_score_can_override": False,
            },
            "review_queue": [
                {
                    "claim_id": claim["claim_id"],
                    "risk_level": claim["risk_level"],
                    "reason": claim["reason"],
                    "suggestion": claim["suggestion"],
                }
                for claim in review_items
            ],
            "limitations": [
                "Deterministic checks cannot prove every semantic paraphrase is equivalent.",
                "A pass does not replace target-language, legal, brand, or platform review.",
            ],
        }

    @staticmethod
    def _declared_claims(content_record: dict[str, Any]) -> list[dict[str, Any]]:
        claims = content_record.get("claims") or []
        normalized: list[dict[str, Any]] = []
        for index, claim in enumerate(claims, start=1):
            normalized.append(
                {
                    "claim_id": str(
                        claim.get("claim_id") or f"DECLARED-{index:03d}"
                    ),
                    "text": str(claim.get("text") or "").strip(),
                    "location": str(claim.get("location") or "unknown"),
                    "fact_ids": list(claim.get("fact_ids") or []),
                    "declared_evidence_level": claim.get("evidence_level"),
                    "extraction_source": "declared",
                }
            )
        return normalized

    @staticmethod
    def _content_units(content_record: dict[str, Any]) -> list[ContentUnit]:
        content = content_record.get("content") or {}
        units: list[ContentUnit] = []

        def add(location: str, value: Any) -> None:
            if isinstance(value, str) and value.strip():
                units.append(ContentUnit(location=location, text=value.strip()))

        add("content.title", content.get("title"))
        for index, bullet in enumerate(content.get("bullet_points") or []):
            add(f"content.bullet_points[{index}]", bullet)
        description = content.get("description")
        if isinstance(description, str):
            sentences = [
                item.strip()
                for item in SENTENCE_SPLIT_PATTERN.split(description)
                if item.strip()
            ]
            if not sentences and description.strip():
                sentences = [description.strip()]
            for sentence in sentences:
                add("content.description", sentence)
        for index, scene in enumerate(content.get("scenes") or []):
            add(f"content.scenes[{index}].voiceover", scene.get("voiceover"))
            add(
                f"content.scenes[{index}].on_screen_text",
                scene.get("on_screen_text"),
            )
        for field in ("caption", "hook", "body", "cta"):
            add(f"content.{field}", content.get(field))
        return units

    @staticmethod
    def _uncovered_claims(
        units: list[ContentUnit], declared_claims: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        by_location: dict[str, list[str]] = {}
        for claim in declared_claims:
            by_location.setdefault(claim["location"], []).append(claim["text"])

        uncovered: list[dict[str, Any]] = []
        for index, unit in enumerate(units, start=1):
            candidates = by_location.get(unit.location, [])
            if FactChecker._unit_is_covered(unit.text, candidates):
                continue
            uncovered.append(
                {
                    "claim_id": f"AUTO-{index:03d}",
                    "text": unit.text,
                    "location": unit.location,
                    "fact_ids": [],
                    "declared_evidence_level": None,
                    "extraction_source": "auto_extracted_uncovered_unit",
                }
            )
        return uncovered

    @staticmethod
    def _unit_is_covered(unit_text: str, claim_texts: Iterable[str]) -> bool:
        normalized_unit = _normalize_text(unit_text)
        candidates = [_normalize_text(text) for text in claim_texts if text]
        if not candidates:
            return False
        if any(
            candidate in normalized_unit or normalized_unit in candidate
            for candidate in candidates
        ):
            return True
        unit_tokens = set(re.findall(r"[\wáéíóúüñ]+", normalized_unit))
        covered_tokens: set[str] = set()
        for candidate in candidates:
            covered_tokens.update(re.findall(r"[\wáéíóúüñ]+", candidate))
        if not unit_tokens:
            return True
        return len(unit_tokens & covered_tokens) / len(unit_tokens) >= 0.6

    def _check_claim(
        self, claim: dict[str, Any], *, sku: str, market: str, language: str
    ) -> dict[str, Any]:
        text = claim["text"]
        normalized = _normalize_text(text)
        submitted_ids = list(claim.get("fact_ids") or [])
        resolved: list[dict[str, Any]] = []
        unknown_ids: list[str] = []
        wrong_sku_ids: list[str] = []
        inactive_ids: list[str] = []
        market_mismatch_ids: list[str] = []
        language_mismatch_ids: list[str] = []

        language_code = _language_family(language)
        for fact_id in submitted_ids:
            fact = self.repository.by_id.get(fact_id)
            if fact is None:
                unknown_ids.append(fact_id)
                continue
            if fact.get("sku") != sku:
                wrong_sku_ids.append(fact_id)
                continue
            if fact.get("status") not in {"active", "caution"}:
                inactive_ids.append(fact_id)
            if market and not self._fact_matches_market(fact, market):
                market_mismatch_ids.append(fact_id)
            fact_languages = fact.get("language_scope") or []
            if language_code not in fact_languages:
                language_mismatch_ids.append(fact_id)
            resolved.append(fact)

        risk_matches = self._risk_matches(normalized)
        numeric_result = self._check_numbers(text, resolved)
        prohibited_level_ids = [
            fact["fact_id"]
            for fact in resolved
            if fact.get("evidence_level") not in GENERATABLE_LEVELS
            or fact.get("generation_policy")
            in {"not_directly_usable", "blocked"}
        ]
        b_facts = [
            fact for fact in resolved if fact.get("evidence_level") == "B"
        ]
        cautious_present = self._has_cautious_language(
            normalized, language_code
        )
        declared_level = claim.get("declared_evidence_level")
        resolved_levels = sorted(
            {str(fact.get("evidence_level")) for fact in resolved}
        )

        reasons: list[str] = []
        status = "supported"
        risk_level = "none"

        if risk_matches:
            status = "unsupported"
            risk_level = "high"
            reasons.append(
                "High-risk absolute, medical, clinical, certification, "
                "structure/function, anti-aging, or unsupported-duration language "
                f"was detected: {', '.join(risk_matches)}."
            )
        if numeric_result["status"] == "contradicted":
            status = "contradicted"
            risk_level = "high"
            reasons.extend(numeric_result["reasons"])
        elif numeric_result["status"] == "unsupported" and status != "contradicted":
            status = "unsupported"
            risk_level = "high"
            reasons.extend(numeric_result["reasons"])
        if unknown_ids or wrong_sku_ids:
            status = "unsupported"
            risk_level = "high"
            if unknown_ids:
                reasons.append(f"Unknown fact_id values: {unknown_ids}.")
            if wrong_sku_ids:
                reasons.append(
                    f"Fact IDs belong to another SKU: {wrong_sku_ids}."
                )
        if prohibited_level_ids:
            status = "unsupported"
            risk_level = "high"
            reasons.append(
                "C/D-level or non-generatable facts cannot support output claims: "
                f"{prohibited_level_ids}."
            )
        if inactive_ids:
            status = "unsupported"
            risk_level = "high"
            reasons.append(f"Inactive or prohibited fact records used: {inactive_ids}.")
        if market_mismatch_ids or language_mismatch_ids:
            market_mismatch_facts = [
                fact
                for fact in resolved
                if fact["fact_id"] in market_mismatch_ids
            ]
            price_market_mismatch = any(
                fact.get("fact_category") == "price"
                for fact in market_mismatch_facts
            )
            if price_market_mismatch:
                status = "unsupported"
                risk_level = "high"
            elif risk_level != "high":
                status = "partially_supported"
                risk_level = "medium"
            if market_mismatch_ids:
                reasons.append(
                    f"Facts do not cover market {market}: {market_mismatch_ids}."
                )
                if price_market_mismatch:
                    reasons.append(
                        "A price from another market cannot be used in this output."
                    )
            if language_mismatch_ids:
                reasons.append(
                    f"Facts do not cover language {language_code}: "
                    f"{language_mismatch_ids}."
                )

        if not submitted_ids:
            if self._is_subjective(normalized) and not risk_matches:
                status = "subjective"
                risk_level = "none"
                reasons.append(
                    "No objectively verifiable product statement was detected."
                )
            elif risk_level != "high":
                status = "unsupported"
                if self._unsupported_without_reference_is_high(normalized):
                    risk_level = "high"
                    reasons.append(
                        "An ingredient, formula, certification, price, or other "
                        "high-impact factual statement has no submitted fact_id."
                    )
                else:
                    risk_level = "medium"
                    reasons.append(
                        "The statement is verifiable but has no submitted fact_id."
                    )
        elif submitted_ids and not resolved and risk_level != "high":
            status = "unsupported"
            risk_level = "high"
            reasons.append("No submitted fact_id could be resolved.")

        if (
            b_facts
            and not cautious_present
            and status not in {"unsupported", "contradicted"}
        ):
            status = "partially_supported"
            risk_level = "medium"
            reasons.append(
                "B-level benefit evidence requires cautious language such as "
                "'helps / skin feels' or 'ayuda a / la piel se siente'."
            )
        if (
            declared_level
            and resolved_levels
            and declared_level not in resolved_levels
            and status == "supported"
        ):
            status = "partially_supported"
            risk_level = "medium"
            reasons.append(
                f"Declared evidence level {declared_level} does not match resolved "
                f"levels {resolved_levels}."
            )

        if status == "supported" and not reasons:
            reasons.append(
                "All submitted fact IDs resolved to active A/B-level records and "
                "deterministic checks found no contradiction."
            )

        suggestion = self._suggestion(
            status=status,
            language=language_code,
            resolved=resolved,
            numeric_result=numeric_result,
            risk_matches=risk_matches,
            unknown_ids=unknown_ids,
            wrong_sku_ids=wrong_sku_ids,
            cautious_present=cautious_present,
        )
        evidence_sources = sorted(
            {
                str(fact.get("source"))
                for fact in resolved
                if fact.get("source")
            }
        )
        result = {
            "claim_id": claim["claim_id"],
            "text": text,
            "location": claim["location"],
            "extraction_source": claim["extraction_source"],
            "submitted_fact_ids": submitted_ids,
            "resolved_fact_ids": [fact["fact_id"] for fact in resolved],
            "resolved_evidence_levels": resolved_levels,
            "status": status,
            "risk_level": risk_level,
            "reason": " ".join(reasons),
            "suggestion": suggestion,
            "evidence_sources": evidence_sources,
            "checks": {
                "numbers": numeric_result,
                "high_risk_language": {
                    "detected": bool(risk_matches),
                    "categories": risk_matches,
                },
                "evidence_gate": {
                    "prohibited_fact_ids": prohibited_level_ids,
                    "b_level_fact_ids": [
                        fact["fact_id"] for fact in b_facts
                    ],
                    "cautious_language_present": cautious_present,
                },
                "identity_and_scope": {
                    "unknown_fact_ids": unknown_ids,
                    "wrong_sku_fact_ids": wrong_sku_ids,
                    "inactive_fact_ids": inactive_ids,
                    "market_mismatch_fact_ids": market_mismatch_ids,
                    "language_mismatch_fact_ids": language_mismatch_ids,
                },
            },
        }
        if result["status"] not in SUPPORTED_STATUSES:
            raise AssertionError(f"Unexpected status: {result['status']}")
        return result

    @staticmethod
    def _check_numbers(
        text: str, resolved_facts: list[dict[str, Any]]
    ) -> dict[str, Any]:
        detected: list[dict[str, Any]] = []
        for match in NUMBER_PATTERN.finditer(_normalize_text(text)):
            detected.append(
                {
                    "value": float(match.group(1)),
                    "unit": _normalize_unit(match.group(2)),
                }
            )
        numeric_facts = []
        for fact in resolved_facts:
            number = _coerce_number(fact.get("value"))
            if number is not None:
                numeric_facts.append(
                    {
                        "fact_id": fact["fact_id"],
                        "value": number,
                        "unit": _normalize_unit(fact.get("unit")),
                    }
                )

        reasons: list[str] = []
        status = "pass"
        if detected and not numeric_facts:
            status = "unsupported"
            reasons.append(
                "Numeric information is present but no numeric fact record was cited."
            )
        else:
            for item in detected:
                value_matches = [
                    fact
                    for fact in numeric_facts
                    if _numbers_equal(item["value"], fact["value"])
                ]
                if not value_matches:
                    status = "contradicted"
                    reasons.append(
                        f"Value {item['value']:g} does not match cited numeric facts."
                    )
                    continue
                if item["unit"] and all(
                    fact["unit"] != item["unit"] for fact in value_matches
                ):
                    status = "contradicted"
                    reasons.append(
                        f"Unit {item['unit']} does not match the unit for "
                        f"value {item['value']:g}."
                    )
        return {
            "detected": detected,
            "cited_numeric_facts": numeric_facts,
            "status": status,
            "reasons": reasons,
        }

    @staticmethod
    def _risk_matches(normalized_text: str) -> list[str]:
        matches: list[str] = []
        for category, patterns in HIGH_RISK_PATTERNS.items():
            if any(re.search(pattern, normalized_text) for pattern in patterns):
                matches.append(category)
        return matches

    @staticmethod
    def _fact_matches_market(fact: dict[str, Any], market: str) -> bool:
        if market not in (fact.get("market_scope") or []):
            return False
        attribute = str(fact.get("attribute", "")).lower()
        if attribute.endswith("_usd"):
            return market == "US"
        if attribute.endswith("_mxn"):
            return market == "MX"
        if attribute == "target_market":
            return str(fact.get("value")) == market
        return True

    @staticmethod
    def _has_cautious_language(normalized_text: str, language: str) -> bool:
        patterns = CAUTIOUS_PATTERNS.get(language, CAUTIOUS_PATTERNS["en"])
        return any(re.search(pattern, normalized_text) for pattern in patterns)

    @staticmethod
    def _is_subjective(normalized_text: str) -> bool:
        if NUMBER_PATTERN.search(normalized_text):
            return False
        return not any(cue in normalized_text for cue in FACTUAL_CUES)

    @staticmethod
    def _unsupported_without_reference_is_high(normalized_text: str) -> bool:
        high_impact_cues = (
            "contains",
            "made with",
            "ingredient",
            "formula",
            "price",
            "usd",
            "mxn",
            "contiene",
            "hecho con",
            "ingrediente",
            "fórmula",
            "precio",
            "certified",
            "approved",
            "clínicamente",
        )
        return any(cue in normalized_text for cue in high_impact_cues)

    @staticmethod
    def _suggestion(
        *,
        status: str,
        language: str,
        resolved: list[dict[str, Any]],
        numeric_result: dict[str, Any],
        risk_matches: list[str],
        unknown_ids: list[str],
        wrong_sku_ids: list[str],
        cautious_present: bool,
    ) -> str:
        if status in {"supported", "subjective"}:
            return "No factual correction required; retain human review."
        if risk_matches and numeric_result["status"] == "contradicted":
            verified = [
                f"{fact['value']:g} {fact['unit'] or ''}".strip()
                for fact in numeric_result["cited_numeric_facts"]
            ]
            if verified:
                return (
                    "Remove the high-risk language and replace the numeric statement "
                    f"with verified value(s): {verified}."
                )
        if risk_matches:
            return (
                "Remove the high-risk claim. Use a supported cautious expression such "
                "as 'Ayuda a que la piel se sienta hidratada.'"
                if language == "es"
                else "Remove the high-risk claim. Use a supported cautious expression "
                "such as 'Helps skin feel hydrated.'"
            )
        if numeric_result["status"] in {"unsupported", "contradicted"}:
            verified = [
                f"{fact['value']:g} {fact['unit'] or ''}".strip()
                for fact in numeric_result["cited_numeric_facts"]
            ]
            if verified:
                return f"Replace the numeric statement with verified value(s): {verified}."
            return "Remove the numeric statement or cite an active numeric fact record."
        if unknown_ids or wrong_sku_ids:
            return (
                "Remove the claim or attach active fact_id values for the same SKU "
                "before regeneration."
            )
        has_b_fact = any(fact.get("evidence_level") == "B" for fact in resolved)
        if has_b_fact and not cautious_present:
            return (
                "Rewrite with 'ayuda a' or 'la piel se siente' and preserve the "
                "original benefit boundary."
                if language == "es"
                else "Rewrite with 'helps' or 'skin feels' and preserve the original "
                "benefit boundary."
            )
        return "Remove unsupported detail or rewrite it using only the cited fact values."

    @staticmethod
    def _gate_reason(
        status: str,
        high_risk: list[dict[str, Any]],
        review_items: list[dict[str, Any]],
    ) -> str:
        if status == "blocked":
            return (
                f"{len(high_risk)} high-risk claim(s) require removal or correction "
                "before export."
            )
        if status == "needs_human_review":
            return (
                f"{len(review_items)} general-risk or partially supported claim(s) "
                "require human confirmation."
            )
        return (
            "Automated fact checks passed; export remains disabled until rule checks "
            "and human final review also pass."
        )


def check_content_file(
    content_path: str | Path,
    fact_path: str | Path,
) -> dict[str, Any]:
    """Load a structured content file and return its fact-check result."""
    with Path(content_path).open("r", encoding="utf-8") as handle:
        content = json.load(handle)
    repository = FactRepository.from_path(fact_path)
    return FactChecker(repository).check(content)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Check LocalizeFlow content facts.")
    parser.add_argument("--content", required=True, help="Structured content JSON.")
    parser.add_argument("--facts", required=True, help="Product fact dataset JSON.")
    parser.add_argument(
        "--output",
        help="Optional output path. If omitted, JSON is written to stdout.",
    )
    return parser


def main() -> int:
    args = _build_parser().parse_args()
    result = check_content_file(args.content, args.facts)
    rendered = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(rendered + "\n", encoding="utf-8")
    else:
        print(rendered)
    return 0 if result["export_gate"]["status"] != "blocked" else 2


if __name__ == "__main__":
    raise SystemExit(main())
