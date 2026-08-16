from __future__ import annotations

import unittest
from datetime import UTC, datetime, timedelta

from src.operations import (
    InMemoryOperationsStore,
    OperationsError,
    OperationsMonitor,
    OperationsSettings,
    readiness_report,
)


def settings(**overrides: object) -> OperationsSettings:
    values = {
        "enabled": True,
        "model_calls_enabled": True,
        "exports_enabled": True,
        "identifier_hmac_secret": "test-only-operations-secret-with-32-characters",
        "min_samples": 5,
    }
    values.update(overrides)
    return OperationsSettings(**values)


class OperationsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.now = [datetime(2026, 8, 16, 8, 0, tzinfo=UTC)]
        self.store = InMemoryOperationsStore()
        self.monitor = OperationsMonitor(
            settings(), self.store, clock=lambda: self.now[0]
        )

    def test_emergency_controls_fail_closed_and_require_monitoring(self) -> None:
        disabled = OperationsSettings()
        with self.assertRaisesRegex(OperationsError, "model calls disabled"):
            disabled.require_model_calls()
        with self.assertRaisesRegex(OperationsError, "exports disabled"):
            disabled.require_exports()
        with self.assertRaisesRegex(OperationsError, "monitoring is off"):
            settings(enabled=False).validate()

    def test_raw_account_and_sku_are_never_stored(self) -> None:
        self.monitor.record_generation(
            account_id="person@example.invalid",
            sku="PRIVATE-SKU-001",
            market="US",
            content_type="product_listing",
            outcome="success",
            duration_ms=1200,
            attempts=1,
            cost_usd=0.01,
            schema_valid=True,
        )
        stored = repr(self.store.events[0])
        self.assertNotIn("person@example.invalid", stored)
        self.assertNotIn("PRIVATE-SKU-001", stored)
        self.assertEqual(len(self.store.events[0].account_hash or ""), 64)
        self.assertEqual(len(self.store.events[0].sku_hash or ""), 64)

    def test_snapshot_covers_required_metrics_and_threshold_alerts(self) -> None:
        for index in range(5):
            self.monitor.record_health(available=index < 4, duration_ms=50)
            self.monitor.record_page_request(success=index < 4, duration_ms=100)
            outcome = "success" if index < 3 else "timeout" if index == 3 else "failure"
            self.monitor.record_generation(
                account_id="account-a" if index < 3 else "account-b",
                sku="SKU-A" if index < 4 else "SKU-B",
                market="US",
                content_type="product_listing",
                outcome=outcome,
                duration_ms=70000 if index == 4 else 1000 + index,
                attempts=2 if index >= 3 else 1,
                cost_usd=0.01,
                schema_valid=index < 3,
                error_code=None if index < 3 else "provider_timeout",
            )
            self.monitor.record_export(
                account_id="account-a", sku="SKU-A", success=index < 4
            )
        self.monitor.record_quality_gate(
            account_id="account-a", sku="SKU-A", hard_block_count=2
        )
        self.monitor.record_feedback(false_positive=True)

        snapshot = self.monitor.snapshot()
        metrics = snapshot["metrics"]
        self.assertEqual(metrics["availability"], 0.8)
        self.assertEqual(metrics["request_success_rate"], 0.6)
        self.assertEqual(metrics["page_error_rate"], 0.2)
        self.assertEqual(metrics["model_timeout_rate"], 0.2)
        self.assertEqual(metrics["retry_rate"], 0.4)
        self.assertEqual(metrics["schema_success_rate"], 0.6)
        self.assertEqual(metrics["generation_p95_ms"], 70000)
        self.assertEqual(metrics["hard_block_count"], 2)
        self.assertEqual(metrics["false_positive_feedback_count"], 1)
        self.assertEqual(metrics["export_completion_rate"], 0.8)
        self.assertEqual(sum(metrics["cost_by_account_hash_usd"].values()), 0.05)
        self.assertEqual(sum(metrics["cost_by_sku_hash_usd"].values()), 0.05)
        self.assertEqual(snapshot["status"], "critical")
        alert_codes = {item["code"] for item in snapshot["alerts"]}
        self.assertIn("availability_critical", alert_codes)
        self.assertIn("generation_p95_critical", alert_codes)
        self.assertFalse(snapshot["content_bodies_logged"])

    def test_cache_hits_count_as_requests_but_not_provider_cost_or_latency(self) -> None:
        self.monitor.record_generation(
            account_id="account-a",
            sku="SKU-A",
            market="MX",
            content_type="social_ad_copy",
            outcome="success",
            duration_ms=0,
            attempts=1,
            cost_usd=0,
            schema_valid=True,
            cache_hit=True,
        )
        snapshot = self.monitor.snapshot()
        self.assertEqual(snapshot["samples"]["generation_requests"], 1)
        self.assertEqual(snapshot["samples"]["provider_generation_requests"], 0)
        self.assertEqual(snapshot["metrics"]["cost_by_account_hash_usd"], {})
        self.assertIsNone(snapshot["metrics"]["generation_p95_ms"])
        self.assertEqual(snapshot["status"], "insufficient_data")

    def test_retention_and_capacity_prune_old_events(self) -> None:
        monitor = OperationsMonitor(
            settings(retention_hours=1, max_events=2),
            self.store,
            clock=lambda: self.now[0],
        )
        monitor.record_health(available=True, duration_ms=10)
        self.now[0] += timedelta(hours=2)
        for _ in range(3):
            monitor.record_health(available=True, duration_ms=10)
        self.assertEqual(len(self.store.events), 2)

    def test_safety_event_creates_immediate_p0_without_minimum_samples(self) -> None:
        self.monitor.record_safety_event(code="fact_gate_bypass")
        snapshot = self.monitor.snapshot()
        self.assertEqual(snapshot["status"], "critical")
        self.assertEqual(snapshot["alerts"][0]["severity"], "P0")
        self.assertEqual(snapshot["alerts"][0]["code"], "fact_gate_bypass")
        with self.assertRaises(OperationsError):
            self.monitor.record_safety_event(code="free_text_not_allowed")

    def test_readiness_report_never_claims_local_monitor_is_hosted_ready(self) -> None:
        report = readiness_report(settings())
        self.assertEqual(report["status"], "local_validation_only")
        self.assertFalse(report["hosted_trial_ready"])
        self.assertEqual(report["storage_scope"], "process_local")


if __name__ == "__main__":
    unittest.main()
