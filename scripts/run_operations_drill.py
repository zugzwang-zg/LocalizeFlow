"""Run a content-free local D4 alert, containment, and recovery drill."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta

from src.operations import (
    InMemoryOperationsStore,
    OperationsError,
    OperationsMonitor,
    OperationsSettings,
)

SECRET = "synthetic-drill-operations-secret-with-at-least-32-characters"


def run_drill() -> dict[str, object]:
    moment = [datetime(2026, 8, 16, 8, 0, tzinfo=UTC)]
    disabled = OperationsSettings(
        enabled=True,
        model_calls_enabled=False,
        exports_enabled=False,
        identifier_hmac_secret=SECRET,
    )
    blocked_controls: list[str] = []
    for name, check in (
        ("model_calls", disabled.require_model_calls),
        ("hosted_exports", disabled.require_exports),
    ):
        try:
            check()
        except OperationsError:
            blocked_controls.append(name)

    active = OperationsSettings(
        enabled=True,
        model_calls_enabled=True,
        exports_enabled=True,
        identifier_hmac_secret=SECRET,
        min_samples=5,
    )
    store = InMemoryOperationsStore()
    monitor = OperationsMonitor(active, store, clock=lambda: moment[0])
    for index in range(5):
        monitor.record_health(available=index == 0, duration_ms=80)
        monitor.record_page_request(success=index < 2, duration_ms=250)
        monitor.record_generation(
            account_id="synthetic-account",
            sku="SYNTHETIC-SKU",
            market="US",
            content_type="product_listing",
            outcome="timeout" if index >= 2 else "success",
            duration_ms=70000 if index >= 2 else 1200,
            attempts=2 if index >= 2 else 1,
            cost_usd=0.01,
            schema_valid=index < 2,
            error_code="provider_timeout" if index >= 2 else None,
        )
        monitor.record_export(
            account_id="synthetic-account",
            sku="SYNTHETIC-SKU",
            success=index == 0,
        )
    monitor.record_safety_event(code="fact_gate_bypass")
    incident = monitor.snapshot()

    moment[0] += timedelta(minutes=16)
    for _ in range(5):
        monitor.record_health(available=True, duration_ms=40)
        monitor.record_page_request(success=True, duration_ms=100)
        monitor.record_generation(
            account_id="synthetic-account",
            sku="SYNTHETIC-SKU",
            market="US",
            content_type="product_listing",
            outcome="success",
            duration_ms=1000,
            attempts=1,
            cost_usd=0.0,
            schema_valid=True,
        )
        monitor.record_export(
            account_id="synthetic-account",
            sku="SYNTHETIC-SKU",
            success=True,
        )
    recovery = monitor.snapshot()

    passed = (
        sorted(blocked_controls) == ["hosted_exports", "model_calls"]
        and incident["status"] == "critical"
        and any(alert["code"] == "fact_gate_bypass" for alert in incident["alerts"])
        and recovery["status"] == "healthy"
        and incident["content_bodies_logged"] is False
    )
    return {
        "drill": "D4-local-operations",
        "passed": passed,
        "model_api_calls": 0,
        "blocked_controls": blocked_controls,
        "incident_status": incident["status"],
        "incident_alert_codes": [alert["code"] for alert in incident["alerts"]],
        "recovery_status": recovery["status"],
        "storage_scope": incident["storage_scope"],
        "content_bodies_logged": incident["content_bodies_logged"],
    }


if __name__ == "__main__":
    result = run_drill()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(0 if result["passed"] else 1)
