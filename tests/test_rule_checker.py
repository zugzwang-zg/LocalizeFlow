from __future__ import annotations

import json
import unittest
from copy import deepcopy
from pathlib import Path

from src.rule_checker import QUALITY_WEIGHTS, RuleChecker


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def load_json(relative_path: str) -> dict:
    with (PROJECT_ROOT / relative_path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


class RuleCheckerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.checker = RuleChecker(
            PROJECT_ROOT / "data/platform_rules/platform_rules.json",
            PROJECT_ROOT / "data/brand/terminology.xlsx",
            PROJECT_ROOT / "data/brand/prohibited_terms.csv",
        )
        cls.valid_listing = load_json(
            "tests/fixtures/rule_checker/MV-SERUM-001_US_listing_revised.json"
        )
        cls.valid_fact = load_json(
            "reports/fact_check/MV-SERUM-001_US_listing_v02_fact_check.json"
        )
        cls.invalid_listing = load_json(
            "prompts/tests/fixtures/MV-SERUM-001_US_high_risk_content.json"
        )
        cls.invalid_fact = load_json(
            "reports/fact_check/MV-SERUM-001_US_high_risk_fact_check.json"
        )

    def result_for(self, report: dict, rule_id: str) -> dict:
        matches = [
            item for item in report["rule_results"] if item["rule_id"] == rule_id
        ]
        self.assertTrue(matches, f"Missing rule result: {rule_id}")
        return matches[0]

    def test_valid_listing_has_every_platform_hard_rule_result(self) -> None:
        report = self.checker.check(self.valid_listing, self.valid_fact)
        hard_rules = [
            item
            for item in report["rule_results"]
            if item["rule_type"] == "platform_hard_rule"
        ]
        self.assertEqual(len(hard_rules), 15)
        self.assertFalse(
            any(item["status"] in {"fail", "needs_human_review"} for item in hard_rules)
        )

    def test_valid_listing_passes_rule_gate_but_not_final_export(self) -> None:
        report = self.checker.check(self.valid_listing, self.valid_fact)
        self.assertEqual(report["export_gate"]["status"], "pass")
        self.assertFalse(report["export_gate"]["export_allowed"])
        self.assertTrue(report["export_gate"]["human_final_review_required"])

    def test_fact_error_has_highest_blocking_priority(self) -> None:
        report = self.checker.check(self.invalid_listing, self.invalid_fact)
        self.assertEqual(report["export_gate"]["status"], "blocked")
        self.assertEqual(report["export_gate"]["blocking_priority"], "fact_error")
        self.assertFalse(report["export_gate"]["quality_score_can_override"])

    def test_missing_required_feed_id_fails_with_reason_and_action(self) -> None:
        payload = deepcopy(self.valid_listing)
        payload["platform_context"]["feed_fields"]["id"] = ""
        report = self.checker.check(payload, self.valid_fact)
        item = self.result_for(report, "GMC-H-001")
        self.assertEqual(item["status"], "fail")
        self.assertTrue(item["reason"])
        self.assertTrue(item["suggested_action"])

    def test_title_length_is_checked(self) -> None:
        payload = deepcopy(self.valid_listing)
        long_title = "Hydrating Serum " * 20
        payload["content"]["title"] = long_title
        payload["platform_context"]["feed_fields"]["structured_title"][
            "content"
        ] = long_title
        report = self.checker.check(payload, self.valid_fact)
        self.assertEqual(self.result_for(report, "GMC-H-002")["status"], "fail")

    def test_all_caps_and_free_shipping_fail_title_editorial_rule(self) -> None:
        payload = deepcopy(self.valid_listing)
        payload["content"]["title"] = "MIRACLE SERUM!!! FREE SHIPPING"
        payload["platform_context"]["feed_fields"]["structured_title"][
            "content"
        ] = payload["content"]["title"]
        report = self.checker.check(payload, self.valid_fact)
        item = self.result_for(report, "GMC-H-004")
        self.assertEqual(item["status"], "fail")
        self.assertIn("content.title", item["content_location"])

    def test_wrong_market_currency_fails(self) -> None:
        payload = deepcopy(self.valid_listing)
        payload["platform_context"]["feed_fields"]["price"]["currency"] = "MXN"
        report = self.checker.check(payload, self.valid_fact)
        self.assertEqual(self.result_for(report, "GMC-H-012")["status"], "fail")
        self.assertEqual(self.result_for(report, "INT-MKT-001")["status"], "fail")

    def test_prohibited_brand_term_blocks(self) -> None:
        payload = deepcopy(self.valid_listing)
        payload["content"]["bullet_points"][2] = "A miracle serum with guaranteed results."
        report = self.checker.check(payload, self.valid_fact)
        matched_ids = {
            item["rule_id"]
            for item in report["rule_results"]
            if item["status"] == "fail"
        }
        self.assertIn("R-P012", matched_ids)
        self.assertIn("R-P013", matched_ids)
        self.assertEqual(report["export_gate"]["status"], "blocked")

    def test_caution_term_enters_human_review(self) -> None:
        payload = deepcopy(self.valid_listing)
        payload["content"]["bullet_points"][0] = "A natural water-based gel serum."
        report = self.checker.check(payload, self.valid_fact)
        item = self.result_for(report, "R-C005")
        self.assertEqual(item["status"], "needs_human_review")
        self.assertTrue(report["human_review_items"])

    def test_spanish_unaccented_serum_is_terminology_failure(self) -> None:
        payload = deepcopy(self.valid_listing)
        payload["market"] = "MX"
        payload["language"] = "es-MX"
        payload["content"]["title"] = "Serum hidratante, 30 mL"
        payload["content"]["bullet_points"] = [
            "Serum hidratante.",
            "Con glicerina.",
            "Ayuda a que la piel se sienta hidratada.",
            "Aplica de 1 a 2 dosis.",
            "Envase de 30 mL."
        ]
        payload["content"]["description"] = "Serum hidratante para tu rutina diaria."
        payload["platform_context"]["feed_fields"]["structured_title"][
            "content"
        ] = payload["content"]["title"]
        payload["platform_context"]["feed_fields"]["structured_description"][
            "content"
        ] = payload["content"]["description"]
        payload["platform_context"]["feed_fields"]["price"]["currency"] = "MXN"
        report = self.checker.check(payload, self.valid_fact)
        item = self.result_for(report, "TERM-CONSISTENCY")
        self.assertEqual(item["status"], "fail")
        self.assertIn("serum", [value.casefold() for value in item["matched_text"]])

    def test_valid_pump_bottle_is_not_cross_product_false_positive(self) -> None:
        report = self.checker.check(self.valid_listing, self.valid_fact)
        self.assertEqual(
            self.result_for(report, "TERM-CONSISTENCY")["status"], "pass"
        )

    def test_missing_ai_disclosure_field_blocks(self) -> None:
        payload = deepcopy(self.valid_listing)
        del payload["ai_disclosure"]["method"]
        report = self.checker.check(payload, self.valid_fact)
        item = self.result_for(report, "INT-AI-001")
        self.assertEqual(item["status"], "fail")
        self.assertEqual(report["export_gate"]["status"], "blocked")

    def test_quality_weights_sum_to_100_and_deductions_have_reasons(self) -> None:
        payload = deepcopy(self.valid_listing)
        payload["content"]["title"] = "MIRACLE SERUM!!! FREE SHIPPING"
        report = self.checker.check(payload, self.valid_fact)
        self.assertEqual(sum(QUALITY_WEIGHTS.values()), 100)
        self.assertEqual(report["quality_score"]["weights_total"], 100)
        for dimension in report["quality_score"]["dimensions"].values():
            self.assertGreaterEqual(dimension["score"], 0)
            self.assertLessEqual(dimension["score"], 100)
            for deduction in dimension["deductions"]:
                self.assertTrue(deduction["reason"])

    def test_hard_rules_and_subjective_scores_are_separate(self) -> None:
        report = self.checker.check(self.valid_listing, self.valid_fact)
        self.assertIn("platform_hard_rule", report["summary_by_rule_type"]["by_rule_type"])
        self.assertIn("brand_rule", report["summary_by_rule_type"]["by_rule_type"])
        self.assertIn("terminology_rule", report["summary_by_rule_type"]["by_rule_type"])
        self.assertIn("dimensions", report["quality_score"])
        self.assertTrue(report["quality_score"]["hard_gate_independent"])

    def test_before_and_after_snapshots_are_retained(self) -> None:
        report = self.checker.check(
            self.valid_listing,
            self.valid_fact,
            previous_content_output=self.invalid_listing,
        )
        version = report["content_version_record"]
        self.assertTrue(version["chain_valid"])
        self.assertEqual(
            version["previous_snapshot_version_id"],
            "content_MV-SERUM-001_US_high_risk_fixture_v01",
        )
        self.assertEqual(
            version["current_content_snapshot"]["content"]["title"],
            self.valid_listing["content"]["title"],
        )
        self.assertEqual(
            version["previous_content_snapshot"]["content"]["title"],
            self.invalid_listing["content"]["title"],
        )

    def test_broken_version_chain_blocks(self) -> None:
        payload = deepcopy(self.valid_listing)
        payload["content_version"]["parent_version_id"] = "wrong_parent"
        report = self.checker.check(
            payload,
            self.valid_fact,
            previous_content_output=self.invalid_listing,
        )
        self.assertFalse(report["content_version_record"]["chain_valid"])
        self.assertEqual(
            report["export_gate"]["blocking_priority"],
            "content_version_integrity",
        )

    def test_tiktok_duration_and_caption_hard_rules(self) -> None:
        payload = self._valid_tiktok_payload()
        payload["platform_context"]["video"]["duration_seconds"] = 61
        payload["platform_fields"]["duration_seconds"] = 61
        payload["content"]["caption"] = "See details #skincare @brand"
        report = self.checker.check(payload, self.valid_fact)
        self.assertEqual(self.result_for(report, "TTA-H-005")["status"], "fail")
        self.assertEqual(self.result_for(report, "TTA-H-008")["status"], "fail")
        hard_rules = [
            item
            for item in report["rule_results"]
            if item["rule_type"] == "platform_hard_rule"
        ]
        self.assertEqual(len(hard_rules), 12)

    def test_high_pressure_cta_blocks(self) -> None:
        payload = self._valid_tiktok_payload()
        payload["content"]["cta"] = "Buy now before it's gone"
        payload["content"]["scenes"][-1]["voiceover"] = payload["content"]["cta"]
        report = self.checker.check(payload, self.valid_fact)
        self.assertEqual(self.result_for(report, "BRAND-CTA-001")["status"], "fail")

    @staticmethod
    def _valid_tiktok_payload() -> dict:
        return {
            "status": "success",
            "sku": "MV-SERUM-001",
            "market": "US",
            "language": "en-US",
            "platform": "tiktok_ads",
            "content_type": "short_video_script",
            "content_version": {
                "content_id": "content_tiktok",
                "version_id": "content_tiktok_v01",
                "parent_version_id": None,
                "created_by": "model",
                "change_reason": "test"
            },
            "content": {
                "title": None,
                "bullet_points": [],
                "description": None,
                "scenes": [
                    {
                        "timecode": "00:00-00:03",
                        "role": "hook",
                        "visual": "Show the bottle.",
                        "voiceover": "A simple hydrating step.",
                        "on_screen_text": "Hydrating serum",
                        "fact_ids": ["MV-SERUM-001-F002"]
                    },
                    {
                        "timecode": "00:03-00:12",
                        "role": "verified_product_fact",
                        "visual": "Apply the serum.",
                        "voiceover": "Helps skin feel hydrated.",
                        "on_screen_text": "Made without added fragrance",
                        "fact_ids": ["MV-SERUM-001-F018", "MV-SERUM-001-F022"]
                    },
                    {
                        "timecode": "00:12-00:15",
                        "role": "cta",
                        "visual": "Show the product.",
                        "voiceover": "See product details.",
                        "on_screen_text": "See product details",
                        "fact_ids": []
                    }
                ],
                "caption": "A simple hydrating step.",
                "hook": "A simple hydrating step.",
                "body": "Helps skin feel hydrated.",
                "cta": "See product details."
            },
            "claims": [
                {
                    "claim_id": "tiktok_claim_001",
                    "text": "Helps skin feel hydrated.",
                    "location": "content.scenes[1].voiceover",
                    "fact_ids": ["MV-SERUM-001-F022"],
                    "evidence_level": "B"
                }
            ],
            "platform_fields": {
                "title_field_name": None,
                "description_field_name": None,
                "digital_source_type": None,
                "duration_seconds": 15,
                "aspect_ratio": "9:16"
            },
            "platform_context": {
                "currency": "USD",
                "duration_seconds": 15,
                "video": {
                    "duration_seconds": 15,
                    "aspect_ratio": "9:16",
                    "resolution": "1080x1920",
                    "audio_clear": True,
                    "static_share_percent": 20,
                    "file_format": ".mp4",
                    "file_size_mb": 20,
                    "bitrate_kbps": 1000
                },
                "creative": {
                    "no_distorted_before_after": True,
                    "no_fake_play_button": True,
                    "no_fake_close_button": True,
                    "no_fake_carousel_indicator": True,
                    "no_fake_cta": True
                },
                "landing_page": {
                    "functional_in_target_market": True,
                    "complete": True,
                    "mobile_friendly": True,
                    "no_automatic_download": True,
                    "no_forced_personal_information": True,
                    "content_context_localized": True,
                    "ad_consistency": {
                        "product": True,
                        "promotion": True,
                        "price": True,
                        "discount": True,
                        "disclaimers": True,
                        "terms": True
                    },
                    "required_information": {
                        "contact_details": True,
                        "company_name": True,
                        "company_address": True,
                        "business_license_when_applicable": True,
                        "price_in_local_currency": True,
                        "shipping_information": True,
                        "return_and_refund_policy": True,
                        "terms_and_conditions": True,
                        "privacy_policy": True
                    }
                }
            },
            "ai_disclosure": {
                "aigc_status": "generative_ai_text",
                "label_required": True,
                "method": "tiktok_aigc_label",
                "disclosure_text": None
            },
            "warnings": [],
            "insufficient_information": [],
            "human_review": {"required": True, "status": "pending"}
        }


if __name__ == "__main__":
    unittest.main()
