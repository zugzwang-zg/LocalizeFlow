import json
import unittest
from pathlib import Path

from src.demo_service import (
    DemoExportError,
    evaluate_text,
    generate_content_pack,
    pack_as_json_bytes,
    update_pack_with_manual_text,
)

ROOT = Path(__file__).resolve().parents[1]


class SharedQualityTests(unittest.TestCase):
    def test_video_timestamps_do_not_prove_narration_duration(self):
        quality = evaluate_text(sku="MV-SERUM-001", market="US", content_type="short_video_script", text="00:00-00:15 Voice: Helps skin feel soft. CTA: Read more.")
        self.assertTrue(any(check["name"] == "口播时长复核" and check["status"] == "warning" for check in quality["checks"]))

    def test_cross_runtime_contract(self):
        cases = json.loads((ROOT / "data/rules/quality_cases.json").read_text(encoding="utf-8"))
        for case in cases:
            with self.subTest(case=case["name"]):
                quality = evaluate_text(
                    sku=case["sku"],
                    market=case["market"],
                    content_type=case["type"],
                    text=case["text"],
                )
                self.assertEqual(quality["export_gate"] == "blocked", case["blocked"])

    def test_editing_an_approved_pack_requires_new_approval(self):
        pack = generate_content_pack(
            sku="MV-SERUM-001",
            market="US",
            primary_content_type="product_listing",
            target_user="default",
            marketing_goal="consideration",
            selling_points=[],
            brand_tone=[],
        )
        approved = update_pack_with_manual_text(
            pack, pack["versions"]["product_listing"]["enhanced"]
        )
        self.assertTrue(pack_as_json_bytes(approved))
        approved["versions"]["product_listing"]["final"] += " A calm daily routine."
        with self.assertRaisesRegex(DemoExportError, "changed since human review"):
            pack_as_json_bytes(approved)


if __name__ == "__main__":
    unittest.main()
