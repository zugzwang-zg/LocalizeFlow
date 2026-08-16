from __future__ import annotations

import json
import unittest

from src.demo_service import (
    CONTENT_TYPES,
    DemoExportError,
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
                    self.assertEqual(
                        pack["primary_quality"]["packaging_gate"]["status"],
                        "pass",
                        f"{product['sku']} {market} {content_type}",
                    )

    def test_profile_contains_traceable_facts(self) -> None:
        profile = product_profile("MV-SERUM-001", "US")
        self.assertEqual(profile["size"], "30 mL")
        self.assertTrue(profile["features"])
        self.assertTrue(
            all(item["fact_id"].startswith("MV-SERUM-001") for item in profile["features"])
        )

    def test_verified_hand_cream_aluminum_tube_passes_packaging_gate(self) -> None:
        pack = generate_content_pack(
            sku="MV-HAND-001",
            market="US",
            primary_content_type="short_video_script",
            target_user="default",
            marketing_goal="consideration",
            selling_points=[],
            brand_tone=["温和", "可信"],
        )
        self.assertEqual(pack["primary_quality"]["packaging_gate"]["status"], "pass")

    def test_manual_revision_is_rechecked_for_packaging(self) -> None:
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
        revised = original.replace("aluminum tube", "glass jar")
        final = update_pack_with_manual_text(pack, revised)
        self.assertEqual(final["final_quality"]["export_gate"], "blocked")

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
        with self.assertRaises(DemoExportError):
            pack_as_json_bytes(pack)
        reviewed = update_pack_with_manual_text(
            pack, pack["versions"]["product_listing"]["enhanced"]
        )
        self.assertEqual(
            json.loads(pack_as_json_bytes(reviewed))["sku"], "MV-CLEAN-001"
        )
        self.assertIn(b"run_id", pack_as_csv_bytes(reviewed))

    def test_blocked_manual_revision_cannot_use_low_level_serializers(self) -> None:
        pack = generate_content_pack(
            sku="MV-HAND-001",
            market="US",
            primary_content_type="short_video_script",
            target_user="default",
            marketing_goal="consideration",
            selling_points=[],
            brand_tone=["温和", "可信"],
        )
        blocked = update_pack_with_manual_text(
            pack,
            pack["versions"]["short_video_script"]["enhanced"].replace(
                "aluminum tube", "glass jar"
            ),
        )
        with self.assertRaises(DemoExportError):
            pack_as_json_bytes(blocked)
        with self.assertRaises(DemoExportError):
            pack_as_csv_bytes(blocked)


if __name__ == "__main__":
    unittest.main()
