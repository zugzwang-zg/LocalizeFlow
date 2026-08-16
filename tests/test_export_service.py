from __future__ import annotations

import json
import unittest

from src.export_service import ExportGateError, beta_audit_export_bytes
from src.operations import OperationsError, OperationsSettings
from tests.test_beta_model import confirmed_import, request, sync_claim_inventory, valid_output


def operations_settings(*, exports_enabled: bool = True) -> OperationsSettings:
    return OperationsSettings(
        enabled=True,
        model_calls_enabled=False,
        exports_enabled=exports_enabled,
        identifier_hmac_secret="test-export-secret-with-at-least-32-characters",
    )


def safe_run() -> tuple[dict, dict]:
    imported = confirmed_import()
    output = valid_output(request())
    output["content"]["title"] = "Authorized face serum, 30 mL PP bottle"
    output["content"]["bullet_points"] = ["Glycerin"] * 4 + ["30 mL PP bottle"]
    output["content"]["description"] = "Authorized face serum in a 30 mL PP bottle."
    packaging_ids = [
        fact["fact_id"]
        for fact in imported["facts"]
        if fact["attribute"].startswith("packaging_")
        or fact["attribute"] in {"specification", "product_name"}
    ]
    sync_claim_inventory(output, packaging_ids)
    return imported, {"run_id": "BETA-RUN-TEST", "model": "test-model", "output": output}


class ExportServiceTests(unittest.TestCase):
    def test_reviewed_safe_output_exports_with_fresh_quality_report(self) -> None:
        imported, run = safe_run()
        payload = json.loads(
            beta_audit_export_bytes(
                imported,
                run,
                approved_at="2026-08-16T09:00:00+00:00",
                operations_settings=operations_settings(),
            )
        )
        self.assertEqual(payload["human_review"]["status"], "approved")
        self.assertEqual(payload["quality"]["export_gate"], "human_review")
        self.assertNotIn("output", payload["run"])

    def test_current_output_is_rechecked_and_blocked_after_tampering(self) -> None:
        imported, run = safe_run()
        run["output"]["content"]["title"] = "Clinically proven glass jar treatment"
        with self.assertRaisesRegex(ExportGateError, "checks block export"):
            beta_audit_export_bytes(
                imported,
                run,
                approved_at="2026-08-16T09:00:00+00:00",
                operations_settings=operations_settings(),
            )

    def test_human_approval_and_timezone_are_required(self) -> None:
        imported, run = safe_run()
        for approved_at in (None, "2026-08-16T09:00:00"):
            with self.subTest(approved_at=approved_at), self.assertRaises(ExportGateError):
                beta_audit_export_bytes(
                    imported,
                    run,
                    approved_at=approved_at,
                    operations_settings=operations_settings(),
                )

    def test_operations_export_switch_blocks_serialization(self) -> None:
        imported, run = safe_run()
        with self.assertRaisesRegex(OperationsError, "exports disabled"):
            beta_audit_export_bytes(
                imported,
                run,
                approved_at="2026-08-16T09:00:00+00:00",
                operations_settings=operations_settings(exports_enabled=False),
            )


if __name__ == "__main__":
    unittest.main()
