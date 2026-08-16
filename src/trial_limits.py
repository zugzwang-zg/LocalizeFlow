"""In-process quota, rate, and cost guard for a tightly capped trial."""

from __future__ import annotations

import hashlib
import hmac
import os
import threading
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any, Callable


class TrialLimitError(RuntimeError):
    """Raised before a provider call when a configured trial limit is reached."""

    def __init__(
        self,
        code: str,
        message: str,
        *,
        retry_after_seconds: int | None = None,
    ) -> None:
        self.code = code
        self.retry_after_seconds = retry_after_seconds
        super().__init__(message)


@dataclass(frozen=True)
class TrialLimitSettings:
    enabled: bool = False
    funding_mode: str = "owner_funded_capped"
    identifier_hmac_secret: str = ""
    monthly_generations_per_account: int = 3
    monthly_generations_per_project: int = 3
    max_languages_per_project: int = 2
    rate_window_seconds: int = 600
    max_requests_per_account_window: int = 3
    max_requests_per_project_window: int = 3
    max_requests_per_client_window: int = 5
    max_cost_per_account_day_usd: float = 0.10
    max_cost_global_day_usd: float = 1.00
    max_cost_global_month_usd: float = 10.00
    rejections_before_alert: int = 3

    @classmethod
    def from_env(cls) -> TrialLimitSettings:
        return cls(
            enabled=os.getenv("LOCALIZEFLOW_TRIAL_LIMITS_ENABLED", "false").lower() == "true",
            funding_mode=os.getenv(
                "LOCALIZEFLOW_TRIAL_FUNDING_MODE", "owner_funded_capped"
            ),
            identifier_hmac_secret=os.getenv(
                "LOCALIZEFLOW_TRIAL_IDENTIFIER_HMAC_SECRET", ""
            ),
            monthly_generations_per_account=int(
                os.getenv("LOCALIZEFLOW_TRIAL_ACCOUNT_MONTHLY_GENERATIONS", "3")
            ),
            monthly_generations_per_project=int(
                os.getenv("LOCALIZEFLOW_TRIAL_PROJECT_MONTHLY_GENERATIONS", "3")
            ),
            max_languages_per_project=int(
                os.getenv("LOCALIZEFLOW_TRIAL_PROJECT_MAX_LANGUAGES", "2")
            ),
            rate_window_seconds=int(
                os.getenv("LOCALIZEFLOW_TRIAL_RATE_WINDOW_SECONDS", "600")
            ),
            max_requests_per_account_window=int(
                os.getenv("LOCALIZEFLOW_TRIAL_ACCOUNT_RATE_LIMIT", "3")
            ),
            max_requests_per_project_window=int(
                os.getenv("LOCALIZEFLOW_TRIAL_PROJECT_RATE_LIMIT", "3")
            ),
            max_requests_per_client_window=int(
                os.getenv("LOCALIZEFLOW_TRIAL_CLIENT_RATE_LIMIT", "5")
            ),
            max_cost_per_account_day_usd=float(
                os.getenv("LOCALIZEFLOW_TRIAL_ACCOUNT_DAILY_COST_USD", "0.10")
            ),
            max_cost_global_day_usd=float(
                os.getenv("LOCALIZEFLOW_TRIAL_GLOBAL_DAILY_COST_USD", "1.00")
            ),
            max_cost_global_month_usd=float(
                os.getenv("LOCALIZEFLOW_TRIAL_GLOBAL_MONTHLY_COST_USD", "10.00")
            ),
            rejections_before_alert=int(
                os.getenv("LOCALIZEFLOW_TRIAL_REJECTIONS_BEFORE_ALERT", "3")
            ),
        )

    def validate(self) -> None:
        if self.funding_mode not in {"owner_funded_capped", "bring_your_own_key"}:
            raise TrialLimitError("invalid_config", "Unsupported trial funding mode.")
        if self.enabled and len(self.identifier_hmac_secret) < 32:
            raise TrialLimitError(
                "invalid_config",
                "Trial identifier HMAC secret must contain at least 32 characters.",
            )
        integer_limits = {
            "monthly generations per account": self.monthly_generations_per_account,
            "monthly generations per project": self.monthly_generations_per_project,
            "languages per project": self.max_languages_per_project,
            "rate window": self.rate_window_seconds,
            "account rate limit": self.max_requests_per_account_window,
            "project rate limit": self.max_requests_per_project_window,
            "client rate limit": self.max_requests_per_client_window,
            "rejection alert threshold": self.rejections_before_alert,
        }
        for label, value in integer_limits.items():
            if value <= 0:
                raise TrialLimitError("invalid_config", f"Trial {label} must be positive.")
        cost_limits = {
            "account daily cost": self.max_cost_per_account_day_usd,
            "global daily cost": self.max_cost_global_day_usd,
            "global monthly cost": self.max_cost_global_month_usd,
        }
        for cost_label, cost_value in cost_limits.items():
            if cost_value <= 0:
                raise TrialLimitError("invalid_config", f"Trial {cost_label} must be positive.")
        if self.max_cost_per_account_day_usd > self.max_cost_global_day_usd:
            raise TrialLimitError(
                "invalid_config", "Account daily cost cannot exceed the global daily cost."
            )
        if self.max_cost_global_day_usd > self.max_cost_global_month_usd:
            raise TrialLimitError(
                "invalid_config", "Global daily cost cannot exceed the global monthly cost."
            )


@dataclass(frozen=True)
class TrialUsageSubject:
    account_id: str
    project_id: str
    client_id: str
    language: str

    def validate(self) -> None:
        for label, value in {
            "account": self.account_id,
            "project": self.project_id,
            "client": self.client_id,
        }.items():
            if not value.strip() or len(value) > 200:
                raise TrialLimitError("invalid_subject", f"Trial {label} identifier is invalid.")
        if self.language not in {"en-US", "es-MX"}:
            raise TrialLimitError("invalid_subject", "Trial language is not supported.")


@dataclass(frozen=True)
class TrialReservation:
    reservation_id: str


class InMemoryTrialUsageStore:
    """Process-local store for local validation; hosted use requires durable atomic storage."""

    def __init__(self) -> None:
        self.lock = threading.RLock()
        self.events: list[dict[str, Any]] = []
        self.rejections: list[dict[str, Any]] = []
        self.alerts: list[dict[str, Any]] = []


DEFAULT_TRIAL_USAGE_STORE = InMemoryTrialUsageStore()


def _digest_identifier(value: str, secret: str) -> str:
    return hmac.new(
        secret.encode("utf-8"), value.strip().encode("utf-8"), hashlib.sha256
    ).hexdigest()


def _month_key(moment: datetime) -> tuple[int, int]:
    return moment.year, moment.month


class TrialUsageGuard:
    def __init__(
        self,
        settings: TrialLimitSettings,
        store: InMemoryTrialUsageStore,
        *,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        settings.validate()
        self.settings = settings
        self.store = store
        self.clock = clock or (lambda: datetime.now(UTC))

    def _now(self) -> datetime:
        moment = self.clock()
        return moment if moment.tzinfo else moment.replace(tzinfo=UTC)

    @staticmethod
    def _charge(event: dict[str, Any]) -> float:
        if event["status"] == "completed":
            return float(event["actual_cost_usd"])
        return float(event["estimated_cost_usd"])

    def _reject(
        self,
        *,
        now: datetime,
        client_hash: str,
        code: str,
        message: str,
        retry_after_seconds: int | None = None,
    ) -> None:
        rejection = {
            "occurred_at": now,
            "client_hash": client_hash,
            "code": code,
        }
        self.store.rejections.append(rejection)
        window_start = now - timedelta(seconds=self.settings.rate_window_seconds)
        recent_count = sum(
            item["client_hash"] == client_hash and item["occurred_at"] >= window_start
            for item in self.store.rejections
        )
        if recent_count % self.settings.rejections_before_alert == 0:
            self.store.alerts.append(
                {
                    "occurred_at": now,
                    "code": "repeated_trial_limit_rejections",
                    "client_hash": client_hash,
                    "rejection_count": recent_count,
                    "severity": "warning",
                }
            )
        raise TrialLimitError(code, message, retry_after_seconds=retry_after_seconds)

    def reserve(
        self,
        subject: TrialUsageSubject,
        *,
        idempotency_key: str,
        estimated_cost_usd: float,
    ) -> TrialReservation:
        if not self.settings.enabled:
            raise TrialLimitError("limits_disabled", "Trial limits must be enabled before calls.")
        subject.validate()
        if estimated_cost_usd <= 0:
            raise TrialLimitError("invalid_estimate", "Estimated request cost must be positive.")
        now = self._now()
        account_hash = _digest_identifier(
            subject.account_id, self.settings.identifier_hmac_secret
        )
        project_hash = _digest_identifier(
            subject.project_id, self.settings.identifier_hmac_secret
        )
        client_hash = _digest_identifier(subject.client_id, self.settings.identifier_hmac_secret)
        window_start = now - timedelta(seconds=self.settings.rate_window_seconds)

        with self.store.lock:
            self.store.events = [
                event
                for event in self.store.events
                if event["reserved_at"] >= now - timedelta(days=35)
            ]
            events = self.store.events
            if any(event["idempotency_key"] == idempotency_key for event in events):
                self._reject(
                    now=now,
                    client_hash=client_hash,
                    code="duplicate_in_progress",
                    message="This generation is already reserved or completed.",
                )

            recent = [event for event in events if event["reserved_at"] >= window_start]
            rate_checks = (
                (
                    "account",
                    sum(event["account_hash"] == account_hash for event in recent),
                    self.settings.max_requests_per_account_window,
                ),
                (
                    "project",
                    sum(event["project_hash"] == project_hash for event in recent),
                    self.settings.max_requests_per_project_window,
                ),
                (
                    "client",
                    sum(event["client_hash"] == client_hash for event in recent),
                    self.settings.max_requests_per_client_window,
                ),
            )
            for scope, used, limit in rate_checks:
                if used >= limit:
                    retry_after = max(
                        1,
                        int(
                            self.settings.rate_window_seconds
                            - (now - min(event["reserved_at"] for event in recent)).total_seconds()
                        ),
                    )
                    self._reject(
                        now=now,
                        client_hash=client_hash,
                        code=f"rate_limit_{scope}",
                        message=(
                            f"Trial {scope} rate limit reached. Try again after the window resets."
                        ),
                        retry_after_seconds=retry_after,
                    )

            this_month = [
                event for event in events if _month_key(event["reserved_at"]) == _month_key(now)
            ]
            account_generations = sum(
                event["account_hash"] == account_hash and event["status"] == "completed"
                for event in this_month
            )
            if account_generations >= self.settings.monthly_generations_per_account:
                self._reject(
                    now=now,
                    client_hash=client_hash,
                    code="quota_account_month",
                    message="Monthly trial generation quota reached for this account.",
                )
            project_generations = sum(
                event["project_hash"] == project_hash and event["status"] == "completed"
                for event in this_month
            )
            if project_generations >= self.settings.monthly_generations_per_project:
                self._reject(
                    now=now,
                    client_hash=client_hash,
                    code="quota_project_month",
                    message="Monthly trial generation quota reached for this project.",
                )
            project_languages = {
                event["language"]
                for event in this_month
                if event["project_hash"] == project_hash
            }
            if (
                subject.language not in project_languages
                and len(project_languages) >= self.settings.max_languages_per_project
            ):
                self._reject(
                    now=now,
                    client_hash=client_hash,
                    code="quota_project_languages",
                    message="Trial language quota reached for this project.",
                )

            today = [event for event in events if event["reserved_at"].date() == now.date()]
            account_day_cost = sum(
                self._charge(event) for event in today if event["account_hash"] == account_hash
            )
            global_day_cost = sum(self._charge(event) for event in today)
            global_month_cost = sum(self._charge(event) for event in this_month)
            cost_checks = (
                (
                    "cost_account_day",
                    account_day_cost,
                    self.settings.max_cost_per_account_day_usd,
                    "Daily trial model budget reached for this account.",
                ),
                (
                    "cost_global_day",
                    global_day_cost,
                    self.settings.max_cost_global_day_usd,
                    "Global daily trial model budget reached.",
                ),
                (
                    "cost_global_month",
                    global_month_cost,
                    self.settings.max_cost_global_month_usd,
                    "Global monthly trial model budget reached.",
                ),
            )
            for code, used_cost, cost_limit, message in cost_checks:
                if used_cost + estimated_cost_usd > cost_limit + 1e-12:
                    self._reject(
                        now=now,
                        client_hash=client_hash,
                        code=code,
                        message=message,
                    )

            reservation_id = str(uuid.uuid4())
            events.append(
                {
                    "reservation_id": reservation_id,
                    "idempotency_key": idempotency_key,
                    "reserved_at": now,
                    "finished_at": None,
                    "account_hash": account_hash,
                    "project_hash": project_hash,
                    "client_hash": client_hash,
                    "language": subject.language,
                    "estimated_cost_usd": round(estimated_cost_usd, 8),
                    "actual_cost_usd": None,
                    "status": "reserved",
                    "failure_code": None,
                }
            )
            return TrialReservation(reservation_id=reservation_id)

    def complete(self, reservation: TrialReservation, *, actual_cost_usd: float) -> None:
        if actual_cost_usd < 0:
            raise TrialLimitError("invalid_actual_cost", "Actual request cost cannot be negative.")
        with self.store.lock:
            event = self._reservation_event(reservation)
            event["status"] = "completed"
            event["actual_cost_usd"] = round(actual_cost_usd, 8)
            event["finished_at"] = self._now()
            if actual_cost_usd > float(event["estimated_cost_usd"]) + 1e-12:
                self.store.alerts.append(
                    {
                        "occurred_at": event["finished_at"],
                        "code": "trial_cost_reservation_overrun",
                        "client_hash": event["client_hash"],
                        "estimated_cost_usd": event["estimated_cost_usd"],
                        "actual_cost_usd": event["actual_cost_usd"],
                        "severity": "critical",
                    }
                )

    def fail(self, reservation: TrialReservation, *, failure_code: str) -> None:
        with self.store.lock:
            event = self._reservation_event(reservation)
            event["status"] = "failed"
            event["failure_code"] = failure_code[:80]
            event["finished_at"] = self._now()

    def _reservation_event(self, reservation: TrialReservation) -> dict[str, Any]:
        for event in self.store.events:
            if event["reservation_id"] == reservation.reservation_id:
                if event["status"] != "reserved":
                    raise TrialLimitError("invalid_reservation", "Trial reservation is closed.")
                return event
        raise TrialLimitError("invalid_reservation", "Trial reservation was not found.")

    def snapshot(self, subject: TrialUsageSubject) -> dict[str, Any]:
        subject.validate()
        now = self._now()
        account_hash = _digest_identifier(
            subject.account_id, self.settings.identifier_hmac_secret
        )
        project_hash = _digest_identifier(
            subject.project_id, self.settings.identifier_hmac_secret
        )
        with self.store.lock:
            this_month = [
                event
                for event in self.store.events
                if _month_key(event["reserved_at"]) == _month_key(now)
            ]
            today = [
                event for event in self.store.events if event["reserved_at"].date() == now.date()
            ]
            account_generations = sum(
                event["account_hash"] == account_hash and event["status"] == "completed"
                for event in this_month
            )
            project_generations = sum(
                event["project_hash"] == project_hash and event["status"] == "completed"
                for event in this_month
            )
            account_day_cost = sum(
                self._charge(event) for event in today if event["account_hash"] == account_hash
            )
            global_day_cost = sum(self._charge(event) for event in today)
            global_month_cost = sum(self._charge(event) for event in this_month)
            return {
                "funding_mode": self.settings.funding_mode,
                "account_monthly_generations_used": account_generations,
                "account_monthly_generations_limit": (
                    self.settings.monthly_generations_per_account
                ),
                "project_monthly_generations_used": project_generations,
                "project_monthly_generations_limit": (
                    self.settings.monthly_generations_per_project
                ),
                "account_daily_cost_used_usd": round(account_day_cost, 8),
                "account_daily_cost_limit_usd": self.settings.max_cost_per_account_day_usd,
                "global_daily_cost_used_usd": round(global_day_cost, 8),
                "global_daily_cost_limit_usd": self.settings.max_cost_global_day_usd,
                "global_monthly_cost_used_usd": round(global_month_cost, 8),
                "global_monthly_cost_limit_usd": self.settings.max_cost_global_month_usd,
                "recent_alert_count": len(self.store.alerts),
                "storage_scope": "process_local",
            }
