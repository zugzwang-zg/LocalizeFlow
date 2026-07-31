from __future__ import annotations

import json
import unittest

from src.demo_service import (
    CONTENT_TYPES,
    generate_content_pack,
    list_products,
    pack_as_csv_bytes,
    pack_as_json_bytes,
    product_profile,
    update_pack_with_manual_text,
)


class DemoServiceTests(unittest.TestCase):
    def test_five_products_are_available(self) -> None:
        self.assertEqual(len(list_products()), 5)

    def test_every_product_market_and_content_type_generates(self) -> None:
        for product in list_products():
            for market in ("US", "MX"):
                for content_type in CONTENT_TYPES:
                    pack = generate_content_pack(
                        sku=product["sku"],
                        market=market,
                        primary_content_type=content_type,
                        target_user="default",
                        marketing_goal="consideration",
                        selling_points=[],
                        brand_tone=["温和", "可信"],
                    )
                    self.assertEqual(len(pack["versions"]), 3)
                    self.assertTrue(pack["claims"])

    def test_profile_contains_traceable_facts(self) -> None:
        profile = product_profile("MV-SERUM-001", "US")
        self.assertEqual(profile["size"], "30 mL")
        self.assertTrue(profile["features"])
        self.assertTrue(
            all(item["fact_id"].startswith("MV-SERUM-001") for item in profile["features"])
        )

    def test_hand_cream_packaging_mismatch_is_blocked(self) -> None:
        pack = generate_content_pack(
            sku="MV-HAND-001",
            market="US",
            primary_content_type="short_video_script",
            target_user="default",
            marketing_goal="consideration",
            selling_points=[],
            brand_tone=["温和", "可信"],
        )
        self.assertEqual(pack["primary_quality"]["risk_level"], "high")
        self.assertEqual(pack["primary_quality"]["export_gate"], "blocked")

    def test_manual_revision_can_remove_packaging_blocker(self) -> None:
        pack = generate_content_pack(
            sku="MV-HAND-001",
            market="US",
            primary_content_type="short_video_script",
            target_user="default",
            marketing_goal="consideration",
            selling_points=[],
            brand_tone=["温和", "可信"],
        )
        original = pack["versions"]["short_video_script"]["enhanced"]
        revised = original.replace("aluminum tube", "tube")
        final = update_pack_with_manual_text(pack, revised)
        self.assertNotEqual(final["final_quality"]["export_gate"], "blocked")

    def test_exports_are_valid(self) -> None:
        pack = generate_content_pack(
            sku="MV-CLEAN-001",
            market="US",
            primary_content_type="product_listing",
            target_user="default",
            marketing_goal="consideration",
            selling_points=[],
            brand_tone=["温和", "可信"],
        )
        self.assertEqual(json.loads(pack_as_json_bytes(pack))["sku"], "MV-CLEAN-001")
        self.assertIn(b"run_id", pack_as_csv_bytes(pack))


if __name__ == "__main__":
    unittest.main()
