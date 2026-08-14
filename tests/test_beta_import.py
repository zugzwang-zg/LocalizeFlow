from __future__ import annotations

import csv
import io
import json
import unittest
import zipfile
from pathlib import Path

from src.beta_import import (
    COLUMNS,
    BetaImportError,
    BetaProjectStore,
    confirm_beta_import,
    parse_beta_upload,
)

ROOT = Path(__file__).resolve().parents[1]


def complete_rows(sku: str = "REAL-SKU-001") -> list[dict[str, str]]:
    base = {
        "sku": sku,
        "unit": "",
        "evidence_level": "A",
        "source": "AUTHORIZED-SPEC-001",
        "source_type": "primary_spec",
        "market_scope": "US;MX",
        "allowed_expression": "",
        "prohibited_expression": "",
        "generation_policy": "direct",
    }
    values = {
        "product_name": "Authorized face serum",
        "specification": "30 mL",
        "ingredient": "Glycerin",
        "usage_instruction": "Apply once daily",
        "packaging_container": "bottle",
        "packaging_material": "PP",
        "packaging_capacity": "30",
        "allowed_claim": "helps skin feel hydrated",
        "prohibited_claim": "clinically proven",
    }
    rows = []
    for attribute, value in values.items():
        row = {**base, "attribute": attribute, "value": value}
        if attribute == "packaging_capacity":
            row["unit"] = "mL"
        if attribute == "prohibited_claim":
            row["generation_policy"] = "blocked"
            row["prohibited_expression"] = value
        rows.append(row)
    return rows


def as_csv(rows: list[dict[str, str]]) -> bytes:
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=COLUMNS, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue().encode()


class BetaImportTests(unittest.TestCase):
    def test_complete_csv_requires_confirmation_before_generation(self) -> None:
        preview = parse_beta_upload("facts.csv", as_csv(complete_rows()), project_id="project-001")
        self.assertTrue(preview["ready_for_confirmation"])
        self.assertFalse(preview["generation_enabled"])
        confirmed = confirm_beta_import(preview, confirmed_by="user-001")
        self.assertTrue(confirmed["generation_enabled"])
        self.assertTrue(all(fact["status"] == "confirmed" for fact in confirmed["facts"]))

    def test_json_uses_same_validation(self) -> None:
        payload = json.dumps({"schema_version": "1.0.0", "facts": complete_rows()}).encode()
        preview = parse_beta_upload("facts.json", payload, project_id="project-001")
        self.assertEqual(preview["summary"]["fact_count"], 9)

    def test_missing_and_conflicting_fields_block(self) -> None:
        rows = complete_rows()[:-1]
        rows.append({**rows[0], "value": "Different product name"})
        preview = parse_beta_upload("facts.csv", as_csv(rows), project_id="project-001")
        codes = {issue["code"] for issue in preview["issues"]}
        self.assertIn("missing_required_attribute", codes)
        self.assertIn("conflicting_values", codes)
        self.assertFalse(preview["ready_for_confirmation"])

    def test_unknown_field_is_not_generatable(self) -> None:
        rows = complete_rows()
        rows[5].update(value="unknown", evidence_level="U", generation_policy="direct")
        preview = parse_beta_upload("facts.csv", as_csv(rows), project_id="project-001")
        self.assertIn("unknown_generation", {issue["code"] for issue in preview["issues"]})

    def test_formula_prefix_is_rejected(self) -> None:
        rows = complete_rows()
        rows[0]["value"] = "=HYPERLINK(\"https://example.invalid\")"
        preview = parse_beta_upload("facts.csv", as_csv(rows), project_id="project-001")
        self.assertIn("formula_prefix", {issue["code"] for issue in preview["issues"]})

    def test_reviewed_xlsx_template_parses_without_archive_error(self) -> None:
        template = ROOT / "templates" / "LocalizeFlow_Beta_SKU_Import_Template.xlsx"
        preview = parse_beta_upload(template.name, template.read_bytes(), project_id="project-001")
        self.assertEqual(preview["summary"]["fact_count"], 1)
        self.assertFalse(preview["ready_for_confirmation"])

    def test_xlsx_embedded_object_is_rejected(self) -> None:
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w") as archive:
            archive.writestr("xl/embeddings/object.bin", b"unsafe")
        with self.assertRaises(BetaImportError):
            parse_beta_upload("facts.xlsx", buffer.getvalue(), project_id="project-001")

    def test_project_isolation_and_clear(self) -> None:
        store = BetaProjectStore()
        store.create(project_id="project-001", owner_id="user-a")
        store.save(project_id="project-001", actor_id="user-a", payload={"facts": []})
        with self.assertRaises(PermissionError):
            store.get(project_id="project-001", actor_id="user-b")
        result = store.clear(project_id="project-001", actor_id="user-a")
        self.assertEqual(result["status"], "deleted")
        self.assertIsNone(store.get(project_id="project-001", actor_id="user-a"))


if __name__ == "__main__":
    unittest.main()
