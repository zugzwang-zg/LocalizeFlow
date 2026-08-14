from __future__ import annotations

import copy
import unittest

from src.beta_quality import evaluate_beta_output
from tests.test_beta_model import confirmed_import, request, valid_output


class BetaQualityTests(unittest.TestCase):
    def test_supported_output_waits_for_human_review(self) -> None:
        imported = confirmed_import()
        req = request()
        output = valid_output(req)
        output["content"]["title"] = "Authorized face serum, 30 mL PP bottle"
        output["content"]["bullet_points"] = ["Glycerin"] * 4 + ["30 mL PP bottle"]
        output["content"]["description"] = "Authorized face serum in a 30 mL PP bottle."
        packaging_ids = [fact["fact_id"] for fact in imported["facts"] if fact["attribute"].startswith("packaging_") or fact["attribute"] == "specification"]
        output["claims"][0]["text"] = output["content"]["title"]
        output["claims"][0]["fact_ids"] = packaging_ids
        report = evaluate_beta_output(imported, output)
        self.assertEqual(report["export_gate"], "human_review")

    def test_wrong_material_blocks(self) -> None:
        imported = confirmed_import()
        output = valid_output(request())
        output["content"]["title"] = "Authorized face serum in a glass bottle"
        report = evaluate_beta_output(imported, output)
        self.assertEqual(report["export_gate"], "blocked")

    def test_prohibited_claim_blocks(self) -> None:
        imported = confirmed_import()
        output = valid_output(request())
        output["content"]["description"] = "Clinically proven for daily use."
        report = evaluate_beta_output(imported, output)
        self.assertEqual(report["export_gate"], "blocked")

    def test_packaging_claim_without_packaging_fact_id_blocks(self) -> None:
        imported = confirmed_import()
        req = request()
        output = valid_output(req)
        output["claims"][0]["text"] = "30 mL PP bottle"
        non_packaging = next(fact["fact_id"] for fact in imported["facts"] if fact["attribute"] == "product_name")
        output["claims"][0]["fact_ids"] = [non_packaging]
        report = evaluate_beta_output(imported, output)
        self.assertEqual(report["export_gate"], "blocked")

    def test_other_project_fact_id_blocks(self) -> None:
        imported = confirmed_import()
        output = copy.deepcopy(valid_output(request()))
        output["claims"][0]["fact_ids"] = ["OTHER-FACT"]
        report = evaluate_beta_output(imported, output)
        self.assertEqual(report["export_gate"], "blocked")


if __name__ == "__main__":
    unittest.main()
