from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from cryptography.fernet import Fernet

from scripts.check_free_trial_release_gate import evaluate_gate
from src.demo_service import (
    DemoExportError,
    generate_content_pack,
    pack_as_json_bytes,
    update_pack_with_manual_text,
)
from src.operations import OperationsError, OperationsSettings, readiness_report
from src.tenant_store import EncryptedTenantStore, TenantAccessError, TenantStoreSettings
from src.trial_limits import (
    InMemoryTrialUsageStore,
    TrialLimitError,
    TrialLimitSettings,
    TrialUsageGuard,
    TrialUsageSubject,
)


class StageDReleaseGateTests(unittest.TestCase):
    def test_machine_gate_computes_no_go_without_errors(self) -> None:
        result = evaluate_gate()
        self.assertEqual(result["computed_decision"], "NO_GO")
        self.assertEqual(result["gate_count"], 6)
        self.assertEqual(result["ready_count"], 1)
        self.assertEqual(result["errors"], [])
        self.assertEqual(result["model_api_calls"], 0)

    def test_local_safeguards_compose_but_never_claim_hosted_readiness(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            tenant_store = EncryptedTenantStore(
                TenantStoreSettings(
                    enabled=True,
                    database_path=Path(temporary_directory) / "stage-d.sqlite3",
                    master_key=Fernet.generate_key().decode("ascii"),
                    session_ttl_minutes=30,
                )
            )
            password = "correct horse battery"
            tenant_store.create_account(email="owner@example.invalid", password=password)
            tenant_store.create_account(email="other@example.invalid", password=password)
            owner = tenant_store.authenticate(
                email="owner@example.invalid", password=password
            ).token
            other = tenant_store.authenticate(
                email="other@example.invalid", password=password
            ).token
            tenant_store.create_project(
                owner, project_id="project-001", name="Synthetic project"
            )
            tenant_store.save_project(
                owner,
                project_id="project-001",
                payload={"facts": [{"value": "synthetic-only"}]},
            )
            with self.assertRaises(TenantAccessError):
                tenant_store.export_project(other, project_id="project-001")

            operations = OperationsSettings(
                enabled=True,
                model_calls_enabled=False,
                exports_enabled=False,
                identifier_hmac_secret=(
                    "stage-d-test-operations-secret-with-at-least-32-characters"
                ),
            )
            with self.assertRaises(OperationsError):
                operations.require_model_calls()
            readiness = readiness_report(operations)
            self.assertFalse(readiness["hosted_trial_ready"])

            usage_store = InMemoryTrialUsageStore()
            guard = TrialUsageGuard(
                TrialLimitSettings(
                    enabled=True,
                    identifier_hmac_secret=(
                        "stage-d-test-usage-secret-with-at-least-32-characters"
                    ),
                    monthly_generations_per_account=1,
                    monthly_generations_per_project=1,
                    max_requests_per_account_window=10,
                    max_requests_per_project_window=10,
                    max_requests_per_client_window=10,
                    max_cost_per_account_day_usd=1.0,
                    max_cost_global_day_usd=2.0,
                    max_cost_global_month_usd=10.0,
                ),
                usage_store,
            )
            subject = TrialUsageSubject(
                account_id="owner@example.invalid",
                project_id="project-001",
                client_id="trusted-test-client",
                language="en-US",
            )
            reservation = guard.reserve(
                subject, idempotency_key="stage-d-1", estimated_cost_usd=0.01
            )
            guard.complete(reservation, actual_cost_usd=0.005)
            with self.assertRaises(TrialLimitError):
                guard.reserve(
                    subject, idempotency_key="stage-d-2", estimated_cost_usd=0.01
                )
            self.assertNotIn("owner@example.invalid", repr(usage_store.events))

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

            deleted = tenant_store.delete_account(owner, password=password)
            self.assertEqual(deleted["status"], "deleted")


if __name__ == "__main__":
    unittest.main()
