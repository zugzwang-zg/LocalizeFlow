from __future__ import annotations

import unittest
from datetime import UTC, datetime, timedelta

from src.trial_limits import (
    InMemoryTrialUsageStore,
    TrialLimitError,
    TrialLimitSettings,
    TrialUsageGuard,
    TrialUsageSubject,
)


def settings(**overrides: object) -> TrialLimitSettings:
    values = {
        "enabled": True,
        "identifier_hmac_secret": "test-only-hmac-secret-with-at-least-32-characters",
        "monthly_generations_per_account": 3,
        "monthly_generations_per_project": 3,
        "max_languages_per_project": 2,
        "rate_window_seconds": 600,
        "max_requests_per_account_window": 10,
        "max_requests_per_project_window": 10,
        "max_requests_per_client_window": 10,
        "max_cost_per_account_day_usd": 1.0,
        "max_cost_global_day_usd": 2.0,
        "max_cost_global_month_usd": 10.0,
        "rejections_before_alert": 2,
    }
    values.update(overrides)
    return TrialLimitSettings(**values)


def subject(**overrides: str) -> TrialUsageSubject:
    values = {
        "account_id": "account@example.invalid",
        "project_id": "project-001",
        "client_id": "trusted-client-token",
        "language": "en-US",
    }
    values.update(overrides)
    return TrialUsageSubject(**values)


class TrialLimitTests(unittest.TestCase):
    def setUp(self) -> None:
        self.now = [datetime(2026, 8, 15, 8, 0, tzinfo=UTC)]
        self.store = InMemoryTrialUsageStore()

    def guard(self, **overrides: object) -> TrialUsageGuard:
        return TrialUsageGuard(
            settings(**overrides), self.store, clock=lambda: self.now[0]
        )

    def test_raw_subject_identifiers_are_not_stored(self) -> None:
        guard = self.guard()
        reservation = guard.reserve(
            subject(), idempotency_key="request-1", estimated_cost_usd=0.02
        )
        guard.complete(reservation, actual_cost_usd=0.01)
        event_text = repr(self.store.events[0])
        self.assertNotIn("account@example.invalid", event_text)
        self.assertNotIn("project-001", event_text)
        self.assertNotIn("trusted-client-token", event_text)
        self.assertEqual(self.store.events[0]["status"], "completed")

    def test_account_rate_limit_blocks_before_reservation_and_emits_alert(self) -> None:
        guard = self.guard(max_requests_per_account_window=1)
        first = guard.reserve(
            subject(), idempotency_key="request-1", estimated_cost_usd=0.01
        )
        guard.complete(first, actual_cost_usd=0.005)
        for key in ("request-2", "request-3"):
            with self.assertRaisesRegex(TrialLimitError, "rate limit") as captured:
                guard.reserve(subject(), idempotency_key=key, estimated_cost_usd=0.01)
            self.assertEqual(captured.exception.code, "rate_limit_account")
            self.assertGreater(captured.exception.retry_after_seconds or 0, 0)
        self.assertEqual(len(self.store.events), 1)
        self.assertEqual(self.store.alerts[0]["code"], "repeated_trial_limit_rejections")

    def test_rate_window_reset_allows_a_new_request(self) -> None:
        guard = self.guard(max_requests_per_account_window=1)
        first = guard.reserve(
            subject(), idempotency_key="request-1", estimated_cost_usd=0.01
        )
        guard.complete(first, actual_cost_usd=0.005)
        self.now[0] += timedelta(seconds=601)
        second = guard.reserve(
            subject(), idempotency_key="request-2", estimated_cost_usd=0.01
        )
        guard.complete(second, actual_cost_usd=0.005)
        self.assertEqual(len(self.store.events), 2)

    def test_project_and_client_rate_limits_cover_cross_account_requests(self) -> None:
        project_guard = self.guard(max_requests_per_project_window=1)
        first = project_guard.reserve(
            subject(account_id="account-a", client_id="client-a"),
            idempotency_key="project-request-1",
            estimated_cost_usd=0.01,
        )
        project_guard.complete(first, actual_cost_usd=0.005)
        with self.assertRaises(TrialLimitError) as project_error:
            project_guard.reserve(
                subject(account_id="account-b", client_id="client-b"),
                idempotency_key="project-request-2",
                estimated_cost_usd=0.01,
            )
        self.assertEqual(project_error.exception.code, "rate_limit_project")

        client_store = InMemoryTrialUsageStore()
        client_guard = TrialUsageGuard(
            settings(max_requests_per_client_window=1),
            client_store,
            clock=lambda: self.now[0],
        )
        second = client_guard.reserve(
            subject(account_id="account-a", project_id="project-a"),
            idempotency_key="client-request-1",
            estimated_cost_usd=0.01,
        )
        client_guard.complete(second, actual_cost_usd=0.005)
        with self.assertRaises(TrialLimitError) as client_error:
            client_guard.reserve(
                subject(account_id="account-b", project_id="project-b"),
                idempotency_key="client-request-2",
                estimated_cost_usd=0.01,
            )
        self.assertEqual(client_error.exception.code, "rate_limit_client")

    def test_monthly_account_generation_quota_blocks_next_call(self) -> None:
        guard = self.guard(monthly_generations_per_account=1)
        first = guard.reserve(
            subject(), idempotency_key="request-1", estimated_cost_usd=0.01
        )
        guard.complete(first, actual_cost_usd=0.005)
        with self.assertRaises(TrialLimitError) as captured:
            guard.reserve(subject(), idempotency_key="request-2", estimated_cost_usd=0.01)
        self.assertEqual(captured.exception.code, "quota_account_month")

    def test_project_language_quota_is_enforced(self) -> None:
        guard = self.guard(max_languages_per_project=1)
        first = guard.reserve(
            subject(language="en-US"),
            idempotency_key="request-1",
            estimated_cost_usd=0.01,
        )
        guard.complete(first, actual_cost_usd=0.005)
        with self.assertRaises(TrialLimitError) as captured:
            guard.reserve(
                subject(language="es-MX"),
                idempotency_key="request-2",
                estimated_cost_usd=0.01,
            )
        self.assertEqual(captured.exception.code, "quota_project_languages")

    def test_failed_provider_call_keeps_conservative_cost_reservation(self) -> None:
        guard = self.guard(max_cost_per_account_day_usd=0.10)
        first = guard.reserve(
            subject(), idempotency_key="request-1", estimated_cost_usd=0.06
        )
        guard.fail(first, failure_code="ProviderTimeout")
        with self.assertRaises(TrialLimitError) as captured:
            guard.reserve(subject(), idempotency_key="request-2", estimated_cost_usd=0.06)
        self.assertEqual(captured.exception.code, "cost_account_day")
        snapshot = guard.snapshot(subject())
        self.assertEqual(snapshot["account_daily_cost_used_usd"], 0.06)

    def test_actual_cost_overrun_is_accounted_and_alerted(self) -> None:
        guard = self.guard()
        reservation = guard.reserve(
            subject(), idempotency_key="request-1", estimated_cost_usd=0.01
        )
        guard.complete(reservation, actual_cost_usd=0.02)
        snapshot = guard.snapshot(subject())
        self.assertEqual(snapshot["account_daily_cost_used_usd"], 0.02)
        self.assertEqual(self.store.alerts[0]["code"], "trial_cost_reservation_overrun")
        self.assertEqual(self.store.alerts[0]["severity"], "critical")

    def test_global_monthly_budget_covers_all_accounts(self) -> None:
        guard = self.guard(max_cost_global_day_usd=1.0, max_cost_global_month_usd=1.0)
        first = guard.reserve(
            subject(account_id="account-a"),
            idempotency_key="request-1",
            estimated_cost_usd=0.6,
        )
        guard.complete(first, actual_cost_usd=0.6)
        self.now[0] += timedelta(days=1)
        with self.assertRaises(TrialLimitError) as captured:
            guard.reserve(
                subject(account_id="account-b", client_id="client-b"),
                idempotency_key="request-2",
                estimated_cost_usd=0.5,
            )
        self.assertEqual(captured.exception.code, "cost_global_month")

    def test_invalid_cost_hierarchy_is_rejected(self) -> None:
        with self.assertRaisesRegex(TrialLimitError, "cannot exceed"):
            settings(
                max_cost_per_account_day_usd=2.0,
                max_cost_global_day_usd=1.0,
            ).validate()


if __name__ == "__main__":
    unittest.main()
