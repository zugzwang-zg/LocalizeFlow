"""Privacy-safe operational telemetry and emergency controls for trial readiness."""

from __future__ import annotations

import hashlib
import hmac
import math
import os
import re
import threading
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any, Callable


class OperationsError(RuntimeError):
    """Raised when operational configuration or an emergency control blocks work."""


@dataclass(frozen=True)
class OperationsSettings:
    enabled: bool = False
    model_calls_enabled: bool = False
    exports_enabled: bool = False
    identifier_hmac_secret: str = ""
    retention_hours: int = 168
    max_events: int = 5000
    window_minutes: int = 15
    min_samples: int = 5
    availability_warning: float = 0.99
    availability_critical: float = 0.95
    request_success_warning: float = 0.95
    request_success_critical: float = 0.80
    page_error_warning: float = 0.05
    page_error_critical: float = 0.15
    schema_success_warning: float = 0.98
    schema_success_critical: float = 0.90
    retry_rate_warning: float = 0.10
    retry_rate_critical: float = 0.25
    generation_p95_warning_ms: int = 30000
    generation_p95_critical_ms: int = 60000
    export_success_warning: float = 0.95
    export_success_critical: float = 0.80

    @classmethod
    def from_env(cls) -> OperationsSettings:
        return cls(
            enabled=_env_bool("LOCALIZEFLOW_OPS_MONITORING_ENABLED", False),
            model_calls_enabled=_env_bool("LOCALIZEFLOW_OPS_MODEL_CALLS_ENABLED", False),
            exports_enabled=_env_bool("LOCALIZEFLOW_OPS_EXPORTS_ENABLED", False),
            identifier_hmac_secret=os.getenv(
                "LOCALIZEFLOW_OPS_IDENTIFIER_HMAC_SECRET",
                os.getenv("LOCALIZEFLOW_TRIAL_IDENTIFIER_HMAC_SECRET", ""),
            ),
            retention_hours=int(os.getenv("LOCALIZEFLOW_OPS_RETENTION_HOURS", "168")),
            max_events=int(os.getenv("LOCALIZEFLOW_OPS_MAX_EVENTS", "5000")),
            window_minutes=int(os.getenv("LOCALIZEFLOW_OPS_WINDOW_MINUTES", "15")),
            min_samples=int(os.getenv("LOCALIZEFLOW_OPS_MIN_SAMPLES", "5")),
            availability_warning=float(
                os.getenv("LOCALIZEFLOW_OPS_AVAILABILITY_WARNING", "0.99")
            ),
            availability_critical=float(
                os.getenv("LOCALIZEFLOW_OPS_AVAILABILITY_CRITICAL", "0.95")
            ),
            request_success_warning=float(
                os.getenv("LOCALIZEFLOW_OPS_REQUEST_SUCCESS_WARNING", "0.95")
            ),
            request_success_critical=float(
                os.getenv("LOCALIZEFLOW_OPS_REQUEST_SUCCESS_CRITICAL", "0.80")
            ),
            page_error_warning=float(
                os.getenv("LOCALIZEFLOW_OPS_PAGE_ERROR_WARNING", "0.05")
            ),
            page_error_critical=float(
                os.getenv("LOCALIZEFLOW_OPS_PAGE_ERROR_CRITICAL", "0.15")
            ),
            schema_success_warning=float(
                os.getenv("LOCALIZEFLOW_OPS_SCHEMA_SUCCESS_WARNING", "0.98")
            ),
            schema_success_critical=float(
                os.getenv("LOCALIZEFLOW_OPS_SCHEMA_SUCCESS_CRITICAL", "0.90")
            ),
            retry_rate_warning=float(
                os.getenv("LOCALIZEFLOW_OPS_RETRY_RATE_WARNING", "0.10")
            ),
            retry_rate_critical=float(
                os.getenv("LOCALIZEFLOW_OPS_RETRY_RATE_CRITICAL", "0.25")
            ),
            generation_p95_warning_ms=int(
                os.getenv("LOCALIZEFLOW_OPS_GENERATION_P95_WARNING_MS", "30000")
            ),
            generation_p95_critical_ms=int(
                os.getenv("LOCALIZEFLOW_OPS_GENERATION_P95_CRITICAL_MS", "60000")
            ),
            export_success_warning=float(
                os.getenv("LOCALIZEFLOW_OPS_EXPORT_SUCCESS_WARNING", "0.95")
            ),
            export_success_critical=float(
                os.getenv("LOCALIZEFLOW_OPS_EXPORT_SUCCESS_CRITICAL", "0.80")
            ),
        )

    def validate(self) -> None:
        if self.enabled and len(self.identifier_hmac_secret) < 32:
            raise OperationsError(
                "Operational monitoring requires a 32+ character identifier HMAC secret."
            )
        if self.model_calls_enabled and not self.enabled:
            raise OperationsError("Model calls cannot open while operational monitoring is off.")
        if self.exports_enabled and not self.enabled:
            raise OperationsError("Hosted exports cannot open while operational monitoring is off.")
        if self.retention_hours <= 0 or self.max_events <= 0:
            raise OperationsError("Operational retention and event limits must be positive.")
        if self.window_minutes <= 0 or self.min_samples <= 0:
            raise OperationsError("Operational window and sample limits must be positive.")
        for label, value in {
            "availability warning": self.availability_warning,
            "availability critical": self.availability_critical,
            "request success warning": self.request_success_warning,
            "request success critical": self.request_success_critical,
            "page error warning": self.page_error_warning,
            "page error critical": self.page_error_critical,
            "schema success warning": self.schema_success_warning,
            "schema success critical": self.schema_success_critical,
            "retry warning": self.retry_rate_warning,
            "retry critical": self.retry_rate_critical,
            "export success warning": self.export_success_warning,
            "export success critical": self.export_success_critical,
        }.items():
            if not 0 <= value <= 1:
                raise OperationsError(f"Operational {label} threshold must be between 0 and 1.")
        if not self.availability_critical < self.availability_warning:
            raise OperationsError("Availability critical threshold must be below warning.")
        if not self.request_success_critical < self.request_success_warning:
            raise OperationsError("Request success critical threshold must be below warning.")
        if not self.schema_success_critical < self.schema_success_warning:
            raise OperationsError("Schema success critical threshold must be below warning.")
        if not self.export_success_critical < self.export_success_warning:
            raise OperationsError("Export success critical threshold must be below warning.")
        if not self.page_error_warning < self.page_error_critical:
            raise OperationsError("Page error warning threshold must be below critical.")
        if not self.retry_rate_warning < self.retry_rate_critical:
            raise OperationsError("Retry warning threshold must be below critical.")
        if not 0 < self.generation_p95_warning_ms < self.generation_p95_critical_ms:
            raise OperationsError("Generation latency thresholds are invalid.")

    def require_model_calls(self) -> None:
        self.validate()
        if not self.model_calls_enabled:
            raise OperationsError("Emergency control keeps model calls disabled.")

    def require_exports(self) -> None:
        self.validate()
        if not self.exports_enabled:
            raise OperationsError("Emergency control keeps hosted exports disabled.")


@dataclass(frozen=True)
class OperationalEvent:
    occurred_at: datetime
    event_type: str
    outcome: str
    account_hash: str | None = None
    sku_hash: str | None = None
    market: str | None = None
    content_type: str | None = None
    duration_ms: int | None = None
    attempts: int = 1
    cost_usd: float = 0.0
    schema_valid: bool | None = None
    hard_block_count: int = 0
    error_code: str | None = None
    cache_hit: bool = False
    false_positive_feedback: bool = False


class InMemoryOperationsStore:
    """Process-local evidence store; hosted monitoring requires durable infrastructure."""

    def __init__(self) -> None:
        self.lock = threading.RLock()
        self.events: list[OperationalEvent] = []


DEFAULT_OPERATIONS_STORE = InMemoryOperationsStore()


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.lower() == "true"


def _digest(value: str, secret: str) -> str:
    return hmac.new(secret.encode(), value.strip().encode(), hashlib.sha256).hexdigest()


def _ratio(numerator: int, denominator: int) -> float | None:
    return round(numerator / denominator, 6) if denominator else None


def _percentile(values: list[int], percentile: float) -> int | None:
    if not values:
        return None
    ordered = sorted(values)
    index = max(0, math.ceil(percentile * len(ordered)) - 1)
    return ordered[index]


class OperationsMonitor:
    EVENT_TYPES = {
        "health_check",
        "page_request",
        "generation",
        "quality_gate",
        "export",
        "feedback",
        "safety_event",
    }
    OUTCOMES = {"available", "unavailable", "success", "failure", "timeout", "blocked"}
    MARKETS = {"US", "MX"}
    CONTENT_TYPES = {"product_listing", "short_video_script", "social_ad_copy"}
    SAFETY_CODES = {
        "cross_tenant_access",
        "secret_or_personal_data_leak",
        "fact_gate_bypass",
        "uncontrolled_model_cost",
        "undisclosed_provider_route_change",
        "deletion_failure",
    }

    def __init__(
        self,
        settings: OperationsSettings,
        store: InMemoryOperationsStore,
        *,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self.settings = settings
        self.store = store
        self.clock = clock or (lambda: datetime.now(UTC))

    def _now(self) -> datetime:
        moment = self.clock()
        return moment if moment.tzinfo else moment.replace(tzinfo=UTC)

    def _identity_hash(self, value: str | None) -> str | None:
        self.settings.validate()
        if value is None:
            return None
        if not value.strip() or len(value) > 200:
            raise OperationsError("Operational identifier is invalid.")
        return _digest(value, self.settings.identifier_hmac_secret)

    def _append(self, event: OperationalEvent) -> None:
        self.settings.validate()
        if not self.settings.enabled:
            return
        self._validate_event(event)
        with self.store.lock:
            cutoff = self._now() - timedelta(hours=self.settings.retention_hours)
            retained = [item for item in self.store.events if item.occurred_at >= cutoff]
            retained.append(event)
            self.store.events = retained[-self.settings.max_events :]

    def _validate_event(self, event: OperationalEvent) -> None:
        if event.event_type not in self.EVENT_TYPES or event.outcome not in self.OUTCOMES:
            raise OperationsError("Unsupported operational event type or outcome.")
        if event.duration_ms is not None and not 0 <= event.duration_ms <= 900000:
            raise OperationsError("Operational duration is outside the accepted range.")
        if not 1 <= event.attempts <= 10:
            raise OperationsError("Operational attempt count is outside the accepted range.")
        if not 0 <= event.cost_usd <= 1000:
            raise OperationsError("Operational cost is outside the accepted range.")
        if not 0 <= event.hard_block_count <= 1000:
            raise OperationsError("Operational hard-block count is invalid.")
        if event.market is not None and event.market not in self.MARKETS:
            raise OperationsError("Operational market is not supported.")
        if event.content_type is not None and event.content_type not in self.CONTENT_TYPES:
            raise OperationsError("Operational content type is not supported.")
        if event.error_code is not None and not re.fullmatch(r"[a-z0-9_]{1,80}", event.error_code):
            raise OperationsError("Operational error code must be a bounded machine label.")

    def record_health(self, *, available: bool, duration_ms: int) -> None:
        self._append(
            OperationalEvent(
                occurred_at=self._now(),
                event_type="health_check",
                outcome="available" if available else "unavailable",
                duration_ms=duration_ms,
            )
        )

    def record_page_request(self, *, success: bool, duration_ms: int) -> None:
        self._append(
            OperationalEvent(
                occurred_at=self._now(),
                event_type="page_request",
                outcome="success" if success else "failure",
                duration_ms=duration_ms,
            )
        )

    def record_generation(
        self,
        *,
        account_id: str,
        sku: str,
        market: str,
        content_type: str,
        outcome: str,
        duration_ms: int | None,
        attempts: int,
        cost_usd: float,
        schema_valid: bool | None,
        error_code: str | None = None,
        cache_hit: bool = False,
    ) -> None:
        self._append(
            OperationalEvent(
                occurred_at=self._now(),
                event_type="generation",
                outcome=outcome,
                account_hash=self._identity_hash(account_id),
                sku_hash=self._identity_hash(sku),
                market=market,
                content_type=content_type,
                duration_ms=duration_ms,
                attempts=attempts,
                cost_usd=cost_usd,
                schema_valid=schema_valid,
                error_code=error_code,
                cache_hit=cache_hit,
            )
        )

    def record_quality_gate(
        self,
        *,
        account_id: str,
        sku: str,
        hard_block_count: int,
    ) -> None:
        self._append(
            OperationalEvent(
                occurred_at=self._now(),
                event_type="quality_gate",
                outcome="blocked" if hard_block_count else "success",
                account_hash=self._identity_hash(account_id),
                sku_hash=self._identity_hash(sku),
                hard_block_count=hard_block_count,
            )
        )

    def record_export(self, *, account_id: str, sku: str, success: bool) -> None:
        self._append(
            OperationalEvent(
                occurred_at=self._now(),
                event_type="export",
                outcome="success" if success else "failure",
                account_hash=self._identity_hash(account_id),
                sku_hash=self._identity_hash(sku),
            )
        )

    def record_feedback(self, *, false_positive: bool) -> None:
        self._append(
            OperationalEvent(
                occurred_at=self._now(),
                event_type="feedback",
                outcome="success",
                false_positive_feedback=false_positive,
            )
        )

    def record_safety_event(self, *, code: str) -> None:
        if code not in self.SAFETY_CODES:
            raise OperationsError("Unsupported safety event code.")
        self._append(
            OperationalEvent(
                occurred_at=self._now(),
                event_type="safety_event",
                outcome="failure",
                error_code=code,
            )
        )

    def snapshot(self) -> dict[str, Any]:
        self.settings.validate()
        now = self._now()
        cutoff = now - timedelta(minutes=self.settings.window_minutes)
        retention_cutoff = now - timedelta(hours=self.settings.retention_hours)
        with self.store.lock:
            self.store.events = [
                item for item in self.store.events if item.occurred_at >= retention_cutoff
            ][-self.settings.max_events :]
            events = [item for item in self.store.events if item.occurred_at >= cutoff]

        health = [item for item in events if item.event_type == "health_check"]
        pages = [item for item in events if item.event_type == "page_request"]
        generations = [item for item in events if item.event_type == "generation"]
        provider_generations = [item for item in generations if not item.cache_hit]
        exports = [item for item in events if item.event_type == "export"]
        quality = [item for item in events if item.event_type == "quality_gate"]
        feedback = [item for item in events if item.event_type == "feedback"]
        safety = [item for item in events if item.event_type == "safety_event"]

        cost_by_account: dict[str, float] = {}
        cost_by_sku: dict[str, float] = {}
        for item in provider_generations:
            if item.account_hash:
                cost_by_account[item.account_hash] = round(
                    cost_by_account.get(item.account_hash, 0.0) + item.cost_usd, 8
                )
            if item.sku_hash:
                cost_by_sku[item.sku_hash] = round(
                    cost_by_sku.get(item.sku_hash, 0.0) + item.cost_usd, 8
                )

        metrics = {
            "availability": _ratio(
                sum(item.outcome == "available" for item in health), len(health)
            ),
            "request_success_rate": _ratio(
                sum(item.outcome == "success" for item in generations), len(generations)
            ),
            "page_error_rate": _ratio(
                sum(item.outcome == "failure" for item in pages), len(pages)
            ),
            "generation_p95_ms": _percentile(
                [
                    item.duration_ms
                    for item in provider_generations
                    if item.duration_ms is not None
                ],
                0.95,
            ),
            "model_timeout_rate": _ratio(
                sum(item.outcome == "timeout" for item in provider_generations),
                len(provider_generations),
            ),
            "retry_rate": _ratio(
                sum(item.attempts > 1 for item in provider_generations),
                len(provider_generations),
            ),
            "schema_success_rate": _ratio(
                sum(item.schema_valid is True for item in provider_generations),
                sum(item.schema_valid is not None for item in provider_generations),
            ),
            "cost_by_account_hash_usd": cost_by_account,
            "cost_by_sku_hash_usd": cost_by_sku,
            "hard_block_count": sum(item.hard_block_count for item in quality),
            "false_positive_feedback_count": sum(
                item.false_positive_feedback for item in feedback
            ),
            "export_completion_rate": _ratio(
                sum(item.outcome == "success" for item in exports), len(exports)
            ),
            "feedback_count": len(feedback),
        }
        samples = {
            "health_checks": len(health),
            "page_requests": len(pages),
            "generation_requests": len(generations),
            "provider_generation_requests": len(provider_generations),
            "schema_outcomes": sum(
                item.schema_valid is not None for item in provider_generations
            ),
            "quality_gate_runs": len(quality),
            "export_attempts": len(exports),
            "feedback_items": len(feedback),
        }
        alerts = self._alerts(metrics, samples, safety)
        enough_samples = any(
            samples[name] >= self.settings.min_samples
            for name in (
                "health_checks",
                "page_requests",
                "generation_requests",
                "provider_generation_requests",
                "export_attempts",
            )
        )
        status = (
            "critical"
            if any(item["severity"] == "P0" for item in alerts)
            else "degraded"
            if alerts
            else "healthy"
            if enough_samples
            else "insufficient_data"
        )
        return {
            "generated_at": now.isoformat(),
            "status": status,
            "window_minutes": self.settings.window_minutes,
            "storage_scope": "process_local",
            "content_bodies_logged": False,
            "identifier_storage": "hmac_sha256",
            "metrics": metrics,
            "samples": samples,
            "alerts": alerts,
        }

    def _alerts(
        self,
        metrics: dict[str, Any],
        samples: dict[str, int],
        safety: list[OperationalEvent],
    ) -> list[dict[str, Any]]:
        alerts: list[dict[str, Any]] = [
            {
                "severity": "P0",
                "code": item.error_code,
                "metric": "safety_event",
                "observed": 1,
                "threshold": 0,
            }
            for item in safety
        ]
        checks = (
            (
                "availability",
                samples["health_checks"],
                self.settings.availability_warning,
                self.settings.availability_critical,
                "low",
            ),
            (
                "request_success_rate",
                samples["generation_requests"],
                self.settings.request_success_warning,
                self.settings.request_success_critical,
                "low",
            ),
            (
                "page_error_rate",
                samples["page_requests"],
                self.settings.page_error_warning,
                self.settings.page_error_critical,
                "high",
            ),
            (
                "schema_success_rate",
                samples["schema_outcomes"],
                self.settings.schema_success_warning,
                self.settings.schema_success_critical,
                "low",
            ),
            (
                "retry_rate",
                samples["provider_generation_requests"],
                self.settings.retry_rate_warning,
                self.settings.retry_rate_critical,
                "high",
            ),
            (
                "export_completion_rate",
                samples["export_attempts"],
                self.settings.export_success_warning,
                self.settings.export_success_critical,
                "low",
            ),
        )
        for name, count, warning, critical, direction in checks:
            value = metrics[name]
            if count < self.settings.min_samples or value is None:
                continue
            critical_hit = value < critical if direction == "low" else value > critical
            warning_hit = value < warning if direction == "low" else value > warning
            if critical_hit or warning_hit:
                alerts.append(
                    {
                        "severity": "P0" if critical_hit else "P1",
                        "code": f"{name}_{'critical' if critical_hit else 'warning'}",
                        "metric": name,
                        "observed": value,
                        "threshold": critical if critical_hit else warning,
                    }
                )
        latency = metrics["generation_p95_ms"]
        if samples["provider_generation_requests"] >= self.settings.min_samples and latency:
            if latency > self.settings.generation_p95_critical_ms:
                alerts.append(
                    {
                        "severity": "P0",
                        "code": "generation_p95_critical",
                        "metric": "generation_p95_ms",
                        "observed": latency,
                        "threshold": self.settings.generation_p95_critical_ms,
                    }
                )
            elif latency > self.settings.generation_p95_warning_ms:
                alerts.append(
                    {
                        "severity": "P1",
                        "code": "generation_p95_warning",
                        "metric": "generation_p95_ms",
                        "observed": latency,
                        "threshold": self.settings.generation_p95_warning_ms,
                    }
                )
        return alerts


def readiness_report(settings: OperationsSettings) -> dict[str, Any]:
    """Describe switch state without claiming the local monitor is production-ready."""

    try:
        settings.validate()
        configuration = "valid"
    except OperationsError as error:
        return {
            "status": "blocked",
            "configuration": "invalid",
            "reason": str(error),
            "storage_scope": "process_local",
        }
    return {
        "status": "local_validation_only",
        "configuration": configuration,
        "monitoring_enabled": settings.enabled,
        "model_calls_enabled": settings.model_calls_enabled,
        "exports_enabled": settings.exports_enabled,
        "storage_scope": "process_local",
        "hosted_trial_ready": False,
        "reason": "Durable metrics, external alerts, probes, and on-call delivery are not configured.",
    }


DEFAULT_OPERATIONS_MONITOR = OperationsMonitor(
    OperationsSettings.from_env(), DEFAULT_OPERATIONS_STORE
)
