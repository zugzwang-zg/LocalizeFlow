"""Auditable OpenAI-compatible model gateway for the LocalizeFlow Closed Beta."""

from __future__ import annotations

import hashlib
import json
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Protocol
from urllib.parse import urlparse

import httpx
from jsonschema import ValidationError, validate
from openai import OpenAI

from src.beta_quality import (
    claim_semantic_support_findings,
    claim_traceability_findings,
    target_language_findings,
    unavailable_attribute_findings,
)
from src.operations import OperationsMonitor
from src.trial_limits import TrialLimitError, TrialUsageGuard, TrialUsageSubject

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROMPT_PATH = PROJECT_ROOT / "prompts" / "beta_generation_prompt.md"
SCHEMA_PATH = PROJECT_ROOT / "prompts" / "schemas" / "content_output.schema.json"
PROMPT_ID = "LF-PROMPT-BETA-GENERATOR-1.7"
PROMPT_VERSION = "1.7.0"
SCHEMA_VERSION = "content-output-v1.2"
RULE_SET_ID = "LF-PLATFORM-RULES-2026-08-15.7"


class BetaModelError(RuntimeError):
    """Raised for a blocked or failed model run."""


class BetaOutputRepairableError(BetaModelError):
    """Raised when one constrained semantic repair may make an output releasable."""

    def __init__(self, reasons: list[str]) -> None:
        self.reasons = reasons
        super().__init__("; ".join(reasons))


class RunStore(Protocol):
    def get(self, key: str) -> dict[str, Any] | None: ...

    def put(self, key: str, value: dict[str, Any]) -> None: ...


class InMemoryRunStore:
    def __init__(self) -> None:
        self._runs: dict[str, dict[str, Any]] = {}

    def get(self, key: str) -> dict[str, Any] | None:
        value = self._runs.get(key)
        return json.loads(json.dumps(value, ensure_ascii=False)) if value else None

    def put(self, key: str, value: dict[str, Any]) -> None:
        self._runs[key] = json.loads(json.dumps(value, ensure_ascii=False))


@dataclass(frozen=True)
class BetaModelSettings:
    enabled: bool
    base_url: str
    api_key: str
    model: str
    api_style: str = "openai_chat_completions"
    timeout_seconds: float = 45.0
    max_retries: int = 1
    max_output_tokens: int = 3000
    input_usd_per_million: float = 0.0
    output_usd_per_million: float = 0.0
    max_request_cost_usd: float = 0.10
    supports_json_schema: bool = False

    @classmethod
    def from_env(cls) -> BetaModelSettings:
        return cls(
            enabled=os.getenv("LOCALIZEFLOW_BETA_MODEL_ENABLED", "false").lower() == "true",
            base_url=os.getenv("LOCALIZEFLOW_MODEL_BASE_URL", ""),
            api_key=os.getenv("LOCALIZEFLOW_MODEL_API_KEY", ""),
            model=os.getenv("LOCALIZEFLOW_MODEL_NAME", ""),
            api_style=os.getenv("LOCALIZEFLOW_MODEL_API_STYLE", "openai_chat_completions"),
            timeout_seconds=float(os.getenv("LOCALIZEFLOW_MODEL_TIMEOUT_SECONDS", "45")),
            max_retries=int(os.getenv("LOCALIZEFLOW_MODEL_MAX_RETRIES", "1")),
            max_output_tokens=int(os.getenv("LOCALIZEFLOW_MODEL_MAX_OUTPUT_TOKENS", "3000")),
            input_usd_per_million=float(os.getenv("LOCALIZEFLOW_MODEL_INPUT_USD_PER_MILLION", "0")),
            output_usd_per_million=float(
                os.getenv("LOCALIZEFLOW_MODEL_OUTPUT_USD_PER_MILLION", "0")
            ),
            max_request_cost_usd=float(
                os.getenv("LOCALIZEFLOW_MODEL_MAX_REQUEST_COST_USD", "0.10")
            ),
            supports_json_schema=os.getenv(
                "LOCALIZEFLOW_MODEL_SUPPORTS_JSON_SCHEMA", "false"
            ).lower()
            == "true",
        )

    def validate(self) -> None:
        if not self.enabled:
            raise BetaModelError("Closed Beta model calls are disabled.")
        if not self.api_key or not self.model or not self.base_url:
            raise BetaModelError("Model base URL, API key, and model name are required.")
        if self.api_style not in {"openai_chat_completions", "anthropic_messages"}:
            raise BetaModelError("Unsupported model API style.")
        parsed = urlparse(self.base_url)
        if parsed.scheme != "https" and parsed.hostname not in {"127.0.0.1", "localhost"}:
            raise BetaModelError("Model base URL must use HTTPS, except for localhost testing.")
        if not 1 <= self.timeout_seconds <= 120:
            raise BetaModelError("Model timeout must be between 1 and 120 seconds.")
        if not 0 <= self.max_retries <= 2:
            raise BetaModelError("Model retries must be between 0 and 2.")
        if not 256 <= self.max_output_tokens <= 8000:
            raise BetaModelError("Model output token limit is invalid.")
        if self.max_request_cost_usd <= 0:
            raise BetaModelError("Per-request cost limit must be positive.")


def _read_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def _bounded_text(value: str, *, field: str, limit: int) -> str:
    normalized = value.strip()
    if not normalized:
        raise BetaModelError(f"{field} is required.")
    if len(normalized) > limit:
        raise BetaModelError(f"{field} exceeds the {limit}-character limit.")
    if any(ord(character) < 32 and character not in "\t\n\r" for character in normalized):
        raise BetaModelError(f"{field} contains unsupported control characters.")
    return normalized


def build_beta_request(
    confirmed_import: dict[str, Any],
    *,
    sku: str,
    market: str,
    content_type: str,
    target_user: str,
    marketing_goal: str,
    brand_tone: list[str],
) -> dict[str, Any]:
    if not confirmed_import.get("generation_enabled") or not confirmed_import.get("confirmation"):
        raise BetaModelError("Facts must be confirmed before generation.")
    if market not in {"US", "MX"}:
        raise BetaModelError("Unsupported market.")
    if content_type not in {"product_listing", "short_video_script", "social_ad_copy"}:
        raise BetaModelError("Unsupported content type.")
    target_user = _bounded_text(target_user, field="Target user", limit=500)
    marketing_goal = _bounded_text(marketing_goal, field="Marketing goal", limit=200)
    if len(brand_tone) > 6:
        raise BetaModelError("Brand tone supports at most 6 entries.")
    brand_tone = [_bounded_text(value, field="Brand tone", limit=80) for value in brand_tone]
    selected = [
        fact
        for fact in confirmed_import["facts"]
        if fact["sku"] == sku and market in fact["markets"]
    ]
    if not selected:
        raise BetaModelError("No confirmed facts match this SKU and market.")
    allowed = [
        fact
        for fact in selected
        if fact["evidence_level"] in {"A", "B"}
        and fact["generation_policy"] in {"direct", "cautious"}
        and fact["value"].lower() != "unknown"
    ]
    blocked = [fact for fact in selected if fact not in allowed]
    if not allowed:
        raise BetaModelError("No A/B evidence facts are eligible for generation.")
    facts_payload = [
        {
            "fact_id": fact["fact_id"],
            "attribute": fact["attribute"],
            "value": fact["value"],
            "unit": fact["unit"] or None,
            "evidence_level": fact["evidence_level"],
            "generation_policy": fact["generation_policy"],
            "allowed_expression": fact["allowed_expression"] or None,
        }
        for fact in allowed
    ]
    prohibited_constraints: list[dict[str, str]] = []
    unavailable_attributes: set[str] = set()
    for fact in blocked:
        expression = fact["prohibited_expression"]
        if not expression and fact["attribute"] == "prohibited_claim":
            expression = fact["value"]
        if expression and expression.lower() != "unknown":
            prohibited_constraints.append(
                {"attribute": fact["attribute"], "prohibited_expression": expression}
            )
        else:
            unavailable_attributes.add(fact["attribute"])
    task = {
        "project_id": confirmed_import["project_id"],
        "sku": sku,
        "market": market,
        "language": "en-US" if market == "US" else "es-MX",
        "content_type": content_type,
        "platform": {
            "product_listing": "google_merchant_center",
            "short_video_script": "tiktok_ads",
            "social_ad_copy": "generic_social",
        }[content_type],
        "target_user": target_user,
        "marketing_goal": marketing_goal,
        "brand_tone": brand_tone,
    }
    return {
        "system": PROMPT_PATH.read_text(encoding="utf-8")
        + "\n\nOUTPUT_SCHEMA_JSON\n"
        + SCHEMA_PATH.read_text(encoding="utf-8"),
        "user": "PRODUCT_FACTS_JSON\n"
        + json.dumps(
            {
                "eligible_facts": facts_payload,
                "prohibited_constraints": prohibited_constraints,
                "unavailable_attributes": sorted(unavailable_attributes),
            },
            ensure_ascii=False,
            separators=(",", ":"),
        )
        + "\nTASK_JSON\n"
        + json.dumps(task, ensure_ascii=False, separators=(",", ":")),
        "task": task,
        "eligible_fact_ids": [fact["fact_id"] for fact in allowed],
        "eligible_fact_support": {
            fact["fact_id"]: {
                "value": fact["value"],
                "unit": fact["unit"] or None,
                "allowed_expression": fact["allowed_expression"] or None,
            }
            for fact in allowed
        },
        "input_fact_ids": [fact["fact_id"] for fact in selected],
        "unavailable_attributes": sorted(unavailable_attributes),
    }


def _validate_output(output: dict[str, Any], request: dict[str, Any]) -> None:
    try:
        validate(output, _read_json(SCHEMA_PATH))
    except ValidationError as error:
        raise BetaModelError(
            f"Model output failed JSON Schema validation: {error.message}"
        ) from error
    task = request["task"]
    for field in ("sku", "market", "language", "content_type", "platform"):
        if output[field] != task[field]:
            raise BetaModelError(f"Model changed immutable task field: {field}.")
    if output["status"] == "insufficient_information":
        if output["human_review"] != {"required": True, "status": "pending"}:
            raise BetaModelError("Model output attempted to bypass human review.")
        return
    repair_reasons: list[str] = []
    eligible = set(request["eligible_fact_ids"])
    for claim in output["claims"]:
        if not claim["fact_ids"] or set(claim["fact_ids"]) - eligible:
            repair_reasons.append("claims cite missing or ineligible fact IDs")
            break
    traceability_issues = claim_traceability_findings(output)
    if traceability_issues:
        repair_reasons.append(
            "claim text/location traceability is invalid: " + " | ".join(traceability_issues[:3])
        )
    semantic_support_issues = claim_semantic_support_findings(
        output, request["eligible_fact_support"]
    )
    if semantic_support_issues:
        repair_reasons.append(
            "claim citations omit facts needed for product type or capacity: "
            + " | ".join(semantic_support_issues[:3])
        )
    language_issues = target_language_findings(output)
    if language_issues:
        repair_reasons.append(
            f"consumer copy is not consistently in {task['language']}: "
            + " | ".join(language_issues[:3])
        )
    unavailable_issues = unavailable_attribute_findings(
        output, request.get("unavailable_attributes", [])
    )
    if unavailable_issues:
        repair_reasons.append(" | ".join(unavailable_issues))
    if repair_reasons:
        raise BetaOutputRepairableError(repair_reasons)
    if output["human_review"] != {"required": True, "status": "pending"}:
        raise BetaModelError("Model output attempted to bypass human review.")


def _insufficient_information_output(request: dict[str, Any]) -> dict[str, Any]:
    task = request["task"]
    return {
        "status": "insufficient_information",
        "sku": task["sku"],
        "market": task["market"],
        "language": task["language"],
        "platform": task["platform"],
        "content_type": task["content_type"],
        "content_version": {
            "content_id": f"{task['sku']}-{task['market']}-insufficient",
            "version_id": "application-fallback-v1",
            "parent_version_id": None,
            "created_by": "model",
            "change_reason": "Application fallback after one targeted fact-ID repair.",
        },
        "content": {
            "title": None,
            "bullet_points": [],
            "description": None,
            "scenes": [],
            "caption": None,
            "hook": None,
            "body": None,
            "cta": None,
        },
        "claims": [],
        "platform_fields": {
            "title_field_name": None,
            "description_field_name": None,
            "digital_source_type": None,
            "duration_seconds": None,
            "aspect_ratio": None,
        },
        "ai_disclosure": {
            "aigc_status": "not_applicable",
            "label_required": False,
            "method": None,
            "disclosure_text": None,
        },
        "warnings": ["No candidate was released after application validation failed twice."],
        "insufficient_information": [
            "A valid claim-to-fact binding could not be produced from the eligible facts."
        ],
        "human_review": {"required": True, "status": "pending"},
    }


def _estimate_cost(settings: BetaModelSettings, input_tokens: int, output_tokens: int) -> float:
    return round(
        input_tokens * settings.input_usd_per_million / 1_000_000
        + output_tokens * settings.output_usd_per_million / 1_000_000,
        8,
    )


def _request_identity(
    request: dict[str, Any], settings: BetaModelSettings
) -> tuple[str, str, int, float]:
    request_digest = hashlib.sha256((request["system"] + request["user"]).encode()).hexdigest()
    idempotency_key = hashlib.sha256(
        f"{request['task']['project_id']}|{request['task']['sku']}|{request_digest}|{settings.model}".encode()
    ).hexdigest()
    estimated_input_tokens = max(1, (len(request["system"]) + len(request["user"])) // 4)
    provider_call_ceiling = 2 * (settings.max_retries + 1)
    conservative_input_tokens = (
        estimated_input_tokens + settings.max_output_tokens
    ) * provider_call_ceiling
    conservative_output_tokens = settings.max_output_tokens * provider_call_ceiling
    estimated_max_cost = _estimate_cost(
        settings, conservative_input_tokens, conservative_output_tokens
    )
    return request_digest, idempotency_key, estimated_input_tokens, estimated_max_cost


def _is_retryable_provider_error(error: Exception) -> bool:
    """Retry only transport, throttling, and server failures.

    Relay SDKs do not expose one stable exception hierarchy, so the status code is
    preferred and a small class-name allowlist is used as a compatibility fallback.
    """
    status_code = getattr(error, "status_code", None)
    if status_code is None:
        status_code = getattr(getattr(error, "response", None), "status_code", None)
    if status_code == 429 or (isinstance(status_code, int) and status_code >= 500):
        return True
    return type(error).__name__ in {
        "APIConnectionError",
        "APITimeoutError",
        "InternalServerError",
        "RateLimitError",
    }


def _provider_error_label(error: Exception) -> str:
    status_code = getattr(error, "status_code", None)
    if status_code is None:
        status_code = getattr(getattr(error, "response", None), "status_code", None)
    suffix = f" (HTTP {status_code})" if isinstance(status_code, int) else ""
    return f"{type(error).__name__}{suffix}"


def run_beta_generation(
    request: dict[str, Any],
    *,
    settings: BetaModelSettings,
    run_store: RunStore,
    client_factory: Callable[..., Any] = OpenAI,
    http_requester: Callable[..., Any] = httpx.post,
) -> dict[str, Any]:
    settings.validate()
    request_digest, idempotency_key, estimated_input_tokens, estimated_max_cost = (
        _request_identity(request, settings)
    )
    cached = run_store.get(idempotency_key)
    if cached:
        return {**cached, "cache_hit": True}
    if estimated_max_cost > settings.max_request_cost_usd:
        raise BetaModelError("Estimated request cost exceeds the configured per-request limit.")

    schema = _read_json(SCHEMA_PATH)
    client: Any = None
    response_format: dict[str, Any] | None = None
    if settings.api_style == "openai_chat_completions":
        client = client_factory(
            base_url=settings.base_url,
            api_key=settings.api_key,
            timeout=settings.timeout_seconds,
            max_retries=0,
        )
        if settings.supports_json_schema:
            response_format = {
                "type": "json_schema",
                "json_schema": {"name": "localizeflow_content", "strict": True, "schema": schema},
            }
        else:
            response_format = {"type": "json_object"}
    started = time.perf_counter()
    provider_attempt_count = 0

    def invoke(messages: list[dict[str, str]], call_key: str) -> tuple[str, int, int]:
        nonlocal provider_attempt_count
        last_error: Exception | None = None
        response: Any = None
        for retry_index in range(settings.max_retries + 1):
            provider_attempt_count += 1
            try:
                if settings.api_style == "openai_chat_completions":
                    response = client.chat.completions.create(
                        model=settings.model,
                        messages=[{"role": "system", "content": request["system"]}, *messages],
                        response_format=response_format,
                        temperature=0.2,
                        max_tokens=settings.max_output_tokens,
                        extra_headers={"Idempotency-Key": call_key},
                    )
                else:
                    response = http_requester(
                        f"{settings.base_url.rstrip('/')}/messages",
                        headers={
                            "Authorization": f"Bearer {settings.api_key}",
                            "anthropic-version": "2023-06-01",
                            "content-type": "application/json",
                            "Idempotency-Key": call_key,
                        },
                        json={
                            "model": settings.model,
                            "system": request["system"],
                            "messages": messages,
                            "temperature": 0.2,
                            "max_tokens": settings.max_output_tokens,
                        },
                        timeout=settings.timeout_seconds,
                    )
                    response.raise_for_status()
                break
            except Exception as error:  # provider SDK exceptions vary by relay
                last_error = error
                if not _is_retryable_provider_error(error) or retry_index >= settings.max_retries:
                    raise BetaModelError(
                        f"Model request failed after {retry_index + 1} attempt(s): {_provider_error_label(error)}"
                    ) from error
        if response is None:
            label = _provider_error_label(last_error) if last_error else "unknown"
            raise BetaModelError(f"Model request failed: {label}")
        if settings.api_style == "openai_chat_completions":
            response_content = response.choices[0].message.content
            usage = getattr(response, "usage", None)
            response_input_tokens = int(
                getattr(usage, "prompt_tokens", estimated_input_tokens) or estimated_input_tokens
            )
            response_output_tokens = int(getattr(usage, "completion_tokens", 0) or 0)
        else:
            try:
                payload = response.json()
            except (ValueError, json.JSONDecodeError) as error:
                raise BetaModelError(
                    "Model returned invalid provider JSON; response body was not stored."
                ) from error
            response_content = "".join(
                block.get("text", "")
                for block in payload.get("content", [])
                if isinstance(block, dict) and block.get("type") == "text"
            )
            usage = payload.get("usage", {})
            response_input_tokens = int(
                usage.get("input_tokens", estimated_input_tokens) or estimated_input_tokens
            )
            response_output_tokens = int(usage.get("output_tokens", 0) or 0)
        if not response_content:
            raise BetaModelError("Model returned an empty response.")
        return response_content, response_input_tokens, response_output_tokens

    messages = [{"role": "user", "content": request["user"]}]
    content, input_tokens, output_tokens = invoke(messages, idempotency_key)
    semantic_repair_count = 0
    degraded_to_insufficient_information = False
    try:
        output = json.loads(content)
    except json.JSONDecodeError as error:
        raise BetaModelError(
            "Model returned invalid JSON; response body was not stored."
        ) from error
    try:
        _validate_output(output, request)
    except BetaOutputRepairableError as error:
        semantic_repair_count = 1
        repair_instruction = (
            "APPLICATION_VALIDATION_ERROR\n"
            "One repair is allowed. Return one complete corrected JSON object. "
            "Correct every listed validation reason: "
            + json.dumps(error.reasons, ensure_ascii=False)
            + ". Write every natural-language consumer sentence in "
            + request["task"]["language"]
            + "; translate supported source expressions instead of copying source-language sentences. "
            "Remove every mention of unavailable attributes: "
            + json.dumps(request.get("unavailable_attributes", []), ensure_ascii=False)
            + ". "
            "Every claims[].fact_ids value must be selected only from this eligible list: "
            + json.dumps(request["eligible_fact_ids"], ensure_ascii=False)
            + ". Never cite unavailable, omitted, or invented IDs. If an exact claim cannot be supported, "
            "remove it or return status=insufficient_information. Preserve immutable task fields and keep human review pending."
        )
        messages.extend(
            [
                {"role": "assistant", "content": content},
                {"role": "user", "content": repair_instruction},
            ]
        )
        repair_key = hashlib.sha256(f"{idempotency_key}|semantic-repair-1".encode()).hexdigest()
        repaired_content, repair_input_tokens, repair_output_tokens = invoke(messages, repair_key)
        input_tokens += repair_input_tokens
        output_tokens += repair_output_tokens
        content = repaired_content
        try:
            output = json.loads(content)
        except json.JSONDecodeError as repair_error:
            raise BetaModelError(
                "Model returned invalid JSON during fact-ID repair; response body was not stored."
            ) from repair_error
        try:
            _validate_output(output, request)
        except BetaOutputRepairableError:
            output = _insufficient_information_output(request)
            _validate_output(output, request)
            degraded_to_insufficient_information = True

    latency_ms = round((time.perf_counter() - started) * 1000)
    actual_cost = _estimate_cost(settings, input_tokens, output_tokens)
    record = {
        "run_id": f"BETA-RUN-{idempotency_key[:16].upper()}",
        "idempotency_key": idempotency_key,
        "project_id": request["task"]["project_id"],
        "sku": request["task"]["sku"],
        "market": request["task"]["market"],
        "content_type": request["task"]["content_type"],
        "provider_base_host": urlparse(settings.base_url).hostname,
        "model": settings.model,
        "api_style": settings.api_style,
        "prompt_id": PROMPT_ID,
        "prompt_version": PROMPT_VERSION,
        "schema_version": SCHEMA_VERSION,
        "rule_set_id": RULE_SET_ID,
        "request_digest": request_digest,
        "response_digest": hashlib.sha256(content.encode()).hexdigest(),
        "input_fact_ids": request["input_fact_ids"],
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "latency_ms": latency_ms,
        "estimated_cost_usd": actual_cost,
        "estimated_request_ceiling_usd": estimated_max_cost,
        "attempt_count": provider_attempt_count,
        "semantic_repair_count": semantic_repair_count,
        "degraded_to_insufficient_information": degraded_to_insufficient_information,
        "output": output,
        "cache_hit": False,
        "body_logging": "disabled",
    }
    run_store.put(idempotency_key, record)
    return record


def run_limited_beta_generation(
    request: dict[str, Any],
    *,
    settings: BetaModelSettings,
    run_store: RunStore,
    trial_guard: TrialUsageGuard,
    trial_subject: TrialUsageSubject,
    operations_monitor: OperationsMonitor | None = None,
    client_factory: Callable[..., Any] = OpenAI,
    http_requester: Callable[..., Any] = httpx.post,
) -> dict[str, Any]:
    """Run one generation behind cumulative trial quotas and cost reservations."""

    if operations_monitor is not None:
        operations_monitor.settings.require_model_calls()
    operation_started = time.perf_counter()
    settings.validate()
    _, idempotency_key, _, estimated_max_cost = _request_identity(request, settings)
    cached = run_store.get(idempotency_key)
    if cached:
        if operations_monitor is not None:
            operations_monitor.record_generation(
                account_id=trial_subject.account_id,
                sku=request["task"]["sku"],
                market=request["task"]["market"],
                content_type=request["task"]["content_type"],
                outcome="success",
                duration_ms=0,
                attempts=1,
                cost_usd=0.0,
                schema_valid=True,
                cache_hit=True,
            )
        return {
            **cached,
            "cache_hit": True,
            "trial_usage": trial_guard.snapshot(trial_subject),
        }
    if estimated_max_cost > settings.max_request_cost_usd:
        raise BetaModelError("Estimated request cost exceeds the configured per-request limit.")
    try:
        reservation = trial_guard.reserve(
            trial_subject,
            idempotency_key=idempotency_key,
            estimated_cost_usd=estimated_max_cost,
        )
    except TrialLimitError as error:
        if operations_monitor is not None:
            operations_monitor.record_generation(
                account_id=trial_subject.account_id,
                sku=request["task"]["sku"],
                market=request["task"]["market"],
                content_type=request["task"]["content_type"],
                outcome="blocked",
                duration_ms=round((time.perf_counter() - operation_started) * 1000),
                attempts=1,
                cost_usd=0.0,
                schema_valid=None,
                error_code=error.code,
            )
        retry_note = (
            f" Retry after {error.retry_after_seconds} seconds."
            if error.retry_after_seconds
            else ""
        )
        raise BetaModelError(f"Trial limit [{error.code}]: {error}{retry_note}") from error
    try:
        result = run_beta_generation(
            request,
            settings=settings,
            run_store=run_store,
            client_factory=client_factory,
            http_requester=http_requester,
        )
    except Exception as error:
        trial_guard.fail(reservation, failure_code=type(error).__name__)
        if operations_monitor is not None:
            error_code, outcome, schema_valid = _operational_failure(error)
            operations_monitor.record_generation(
                account_id=trial_subject.account_id,
                sku=request["task"]["sku"],
                market=request["task"]["market"],
                content_type=request["task"]["content_type"],
                outcome=outcome,
                duration_ms=round((time.perf_counter() - operation_started) * 1000),
                attempts=1,
                cost_usd=estimated_max_cost,
                schema_valid=schema_valid,
                error_code=error_code,
            )
        raise
    trial_guard.complete(reservation, actual_cost_usd=result["estimated_cost_usd"])
    if operations_monitor is not None:
        operations_monitor.record_generation(
            account_id=trial_subject.account_id,
            sku=request["task"]["sku"],
            market=request["task"]["market"],
            content_type=request["task"]["content_type"],
            outcome="success",
            duration_ms=result["latency_ms"],
            attempts=result["attempt_count"],
            cost_usd=result["estimated_cost_usd"],
            schema_valid=True,
        )
    return {**result, "trial_usage": trial_guard.snapshot(trial_subject)}


def _operational_failure(error: Exception) -> tuple[str, str, bool | None]:
    """Map provider/application errors to bounded labels without logging messages."""

    detail = str(error).lower()
    if "timeout" in detail or "timed out" in detail:
        return "provider_timeout", "timeout", None
    if "json schema" in detail or "invalid json" in detail or "provider json" in detail:
        return "schema_validation_failure", "failure", False
    if isinstance(error, BetaModelError):
        return "model_gateway_failure", "failure", None
    return "generation_failure", "failure", None
