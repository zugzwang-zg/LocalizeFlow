from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from src.fact_checker import FactChecker, FactRepository


ROOT = Path(__file__).resolve().parents[1]
FACT_PATH = ROOT / "data" / "products" / "product_facts.json"
EXPECTED_PATH = (
    ROOT
    / "prompts"
    / "tests"
    / "expected"
    / "MV-SERUM-001_US_listing_expected.json"
)


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def minimal_record(
    text: str,
    fact_ids: list[str],
    *,
    evidence_level: str = "A",
    sku: str = "MV-SERUM-001",
    language: str = "en-US",
) -> dict:
    return {
        "sku": sku,
        "market": "US" if language == "en-US" else "MX",
        "language": language,
        "content_version": {
            "version_id": "test_v01",
        },
        "content": {
            "title": text,
            "bullet_points": [],
            "description": None,
            "scenes": [],
            "caption": None,
            "hook": None,
            "body": None,
            "cta": None,
        },
        "claims": [
            {
                "claim_id": "test_claim_001",
                "text": text,
                "location": "content.title",
                "fact_ids": fact_ids,
                "evidence_level": evidence_level,
            }
        ],
    }


class FactCheckerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.repository = FactRepository.from_path(FACT_PATH)
        cls.checker = FactChecker(cls.repository)

    def test_valid_listing_fixture_passes_fact_gate(self) -> None:
        result = self.checker.check(load_json(EXPECTED_PATH))
        self.assertEqual(result["export_gate"]["status"], "pass")
        self.assertFalse(result["export_gate"]["export_allowed"])
        self.assertEqual(result["summary"]["fact_error_rate"], 0)
        self.assertEqual(
            result["summary"]["numeric_claim_count"],
            result["summary"]["numeric_claims_checked"],
        )
        self.assertGreater(result["summary"]["numeric_claim_count"], 0)
        self.assertTrue(
            all(
                item["status"] == "supported"
                for item in result["claim_results"]
            )
        )

    def test_numeric_contradiction_blocks_export(self) -> None:
        record = minimal_record(
            "Mirevane Botanics Hydrating Serum, 50 mL",
            ["MV-SERUM-001-F002", "MV-SERUM-001-F003"],
        )
        result = self.checker.check(record)
        claim = result["claim_results"][0]
        self.assertEqual(claim["status"], "contradicted")
        self.assertEqual(claim["risk_level"], "high")
        self.assertEqual(result["export_gate"]["status"], "blocked")
        self.assertIn("30 ml", claim["suggestion"].lower())

    def test_medical_and_clinical_claim_blocks_export(self) -> None:
        record = minimal_record(
            "Clinically proven to cure dry skin.",
            ["MV-SERUM-001-F022"],
            evidence_level="B",
        )
        result = self.checker.check(record)
        claim = result["claim_results"][0]
        self.assertEqual(claim["status"], "unsupported")
        self.assertEqual(claim["risk_level"], "high")
        self.assertIn("medical_claim", claim["checks"]["high_risk_language"]["categories"])
        self.assertIn("clinical_claim", claim["checks"]["high_risk_language"]["categories"])
        self.assertEqual(result["export_gate"]["status"], "blocked")
        self.assertIn("Helps skin feel hydrated", claim["suggestion"])

    def test_unsupported_duration_without_numeric_fact_is_not_a_contradiction(self) -> None:
        record = minimal_record(
            "Guaranteed 72-hour hydration.",
            ["MV-SERUM-001-F022"],
            evidence_level="B",
        )
        result = self.checker.check(record)
        claim = result["claim_results"][0]
        self.assertEqual(claim["status"], "unsupported")
        self.assertEqual(claim["checks"]["numbers"]["status"], "unsupported")
        self.assertEqual(claim["risk_level"], "high")
        self.assertEqual(result["export_gate"]["status"], "blocked")

    def test_b_level_benefit_without_qualifier_needs_review(self) -> None:
        record = minimal_record(
            "Hydrates skin.",
            ["MV-SERUM-001-F022"],
            evidence_level="B",
        )
        result = self.checker.check(record)
        claim = result["claim_results"][0]
        self.assertEqual(claim["status"], "partially_supported")
        self.assertEqual(claim["risk_level"], "medium")
        self.assertEqual(result["export_gate"]["status"], "needs_human_review")
        self.assertIn("helps", claim["suggestion"])

    def test_c_level_hypothesis_cannot_support_output(self) -> None:
        record = minimal_record(
            "A non-sticky hydrating serum.",
            ["MV-SERUM-001-F038"],
            evidence_level="C",
        )
        result = self.checker.check(record)
        claim = result["claim_results"][0]
        self.assertEqual(claim["status"], "unsupported")
        self.assertEqual(claim["risk_level"], "high")
        self.assertEqual(result["export_gate"]["status"], "blocked")
        self.assertIn("MV-SERUM-001-F038", claim["reason"])

    def test_subjective_copy_is_labeled_subjective(self) -> None:
        record = minimal_record("A calm step for your routine.", [])
        result = self.checker.check(record)
        claim = result["claim_results"][0]
        self.assertEqual(claim["status"], "subjective")
        self.assertEqual(claim["risk_level"], "none")
        self.assertEqual(result["summary"]["factual_claim_count"], 0)
        self.assertEqual(result["summary"]["fact_error_rate"], 0)

    def test_uncovered_ingredient_statement_is_auto_extracted_and_blocked(self) -> None:
        record = minimal_record(
            "Mirevane Botanics Hydrating Serum",
            ["MV-SERUM-001-F002"],
        )
        record["content"]["bullet_points"] = ["Contains gold flakes."]
        result = self.checker.check(record)
        automatic = [
            item
            for item in result["claim_results"]
            if item["extraction_source"] == "auto_extracted_uncovered_unit"
        ]
        self.assertEqual(len(automatic), 1)
        self.assertEqual(automatic[0]["status"], "unsupported")
        self.assertEqual(automatic[0]["risk_level"], "high")
        self.assertEqual(result["export_gate"]["status"], "blocked")

    def test_wrong_sku_fact_id_blocks_export(self) -> None:
        record = minimal_record(
            "120 mL cleanser.",
            ["MV-CLEAN-001-F003"],
        )
        result = self.checker.check(record)
        claim = result["claim_results"][0]
        self.assertEqual(claim["status"], "unsupported")
        self.assertEqual(claim["risk_level"], "high")
        self.assertEqual(
            claim["checks"]["identity_and_scope"]["wrong_sku_fact_ids"],
            ["MV-CLEAN-001-F003"],
        )

    def test_supported_ingredient_claim_passes(self) -> None:
        record = minimal_record(
            "Made with glycerin and panthenol.",
            ["MV-SERUM-001-F005", "MV-SERUM-001-F008"],
        )
        result = self.checker.check(record)
        self.assertEqual(result["claim_results"][0]["status"], "supported")
        self.assertEqual(result["export_gate"]["status"], "pass")

    def test_supported_us_price_passes_numeric_and_market_checks(self) -> None:
        record = minimal_record(
            "Price: 24 USD.",
            ["MV-SERUM-001-F032"],
        )
        result = self.checker.check(record)
        claim = result["claim_results"][0]
        self.assertEqual(claim["status"], "supported")
        self.assertEqual(claim["checks"]["numbers"]["status"], "pass")
        self.assertEqual(result["export_gate"]["status"], "pass")

    def test_mexico_price_in_us_content_blocks_export(self) -> None:
        record = minimal_record(
            "Price: 479 MXN.",
            ["MV-SERUM-001-F033"],
        )
        result = self.checker.check(record)
        claim = result["claim_results"][0]
        self.assertEqual(claim["status"], "unsupported")
        self.assertEqual(claim["risk_level"], "high")
        self.assertEqual(result["export_gate"]["status"], "blocked")
        self.assertIn("another market", claim["reason"])

    def test_absolute_target_user_claim_blocks_export(self) -> None:
        record = minimal_record(
            "Perfect for everyone.",
            ["MV-SERUM-001-F014"],
        )
        result = self.checker.check(record)
        claim = result["claim_results"][0]
        self.assertEqual(claim["status"], "unsupported")
        self.assertEqual(claim["risk_level"], "high")
        self.assertEqual(result["export_gate"]["status"], "blocked")

    def test_unverified_certification_blocks_export(self) -> None:
        record = minimal_record(
            "FDA-approved and dermatologist-tested.",
            ["MV-SERUM-001-F037"],
        )
        result = self.checker.check(record)
        claim = result["claim_results"][0]
        self.assertEqual(claim["status"], "unsupported")
        self.assertEqual(claim["risk_level"], "high")
        self.assertEqual(result["export_gate"]["status"], "blocked")

    def test_spanish_cautious_benefit_passes(self) -> None:
        record = minimal_record(
            "Ayuda a que la piel se sienta hidratada.",
            ["MV-SERUM-001-F022"],
            evidence_level="B",
            language="es-MX",
        )
        result = self.checker.check(record)
        self.assertEqual(result["claim_results"][0]["status"], "supported")
        self.assertEqual(result["export_gate"]["status"], "pass")

    def test_fact_error_rate_uses_only_unsupported_and_contradicted(self) -> None:
        record = copy.deepcopy(load_json(EXPECTED_PATH))
        record["claims"].append(
            {
                "claim_id": "bad_claim",
                "text": "50 mL",
                "location": "content.title",
                "fact_ids": ["MV-SERUM-001-F003"],
                "evidence_level": "A",
            }
        )
        result = self.checker.check(record)
        expected_rate = (
            result["summary"]["unsupported_count"]
            + result["summary"]["contradicted_count"]
        ) / result["summary"]["factual_claim_count"]
        self.assertEqual(
            result["summary"]["fact_error_rate"],
            round(expected_rate, 6),
        )


if __name__ == "__main__":
    unittest.main()
