from __future__ import annotations

import unittest

from src.packaging_checker import check_packaging_text, pre_generation_gate


class PackagingCheckerTests(unittest.TestCase):
    def test_verified_material_and_container_pass(self) -> None:
        report = check_packaging_text("MV-HAND-001", "60 mL aluminum tube with screw cap", "US")
        self.assertEqual(report["status"], "pass")

    def test_wrong_material_blocks(self) -> None:
        report = check_packaging_text("MV-HAND-001", "60 mL glass tube", "US")
        self.assertEqual(report["status"], "blocked")
        self.assertEqual(report["findings"][0]["field"], "material")

    def test_wrong_container_blocks(self) -> None:
        report = check_packaging_text("MV-CREAM-001", "50 mL bottle", "US")
        self.assertEqual(report["status"], "blocked")
        self.assertEqual(report["findings"][0]["field"], "container_type")

    def test_missing_field_is_unknown_and_blocks_claim(self) -> None:
        gate = pre_generation_gate("MV-CLEAN-001", ["transparency"], "US")
        report = check_packaging_text("MV-CLEAN-001", "transparent 120 mL PET pump bottle", "US")
        self.assertEqual(gate["status"], "blocked")
        self.assertEqual(gate["unknown_fields"], ["transparency"])
        self.assertEqual(report["status"], "blocked")
        self.assertEqual(report["findings"][0]["status"], "unsupported")

    def test_mixed_sku_packaging_blocks(self) -> None:
        report = check_packaging_text("MV-SERUM-001", "50 mL PP jar with inner lid", "US")
        self.assertEqual(report["status"], "blocked")
        self.assertGreaterEqual(len(report["findings"]), 2)

    def test_kit_component_capacities_pass(self) -> None:
        report = check_packaging_text("MV-KIT-001", "30 mL pump bottle, 10 mL pump bottle and 15 mL jar", "US")
        self.assertEqual(report["status"], "pass")

    def test_spanish_pump_bottle_phrase_is_not_classified_as_jar(self) -> None:
        report = check_packaging_text("MV-KIT-001", "frasco con bomba de 30 mL, frasco con bomba de 10 mL y tarro de 15 mL", "MX")
        self.assertEqual(report["status"], "pass")


if __name__ == "__main__":
    unittest.main()
