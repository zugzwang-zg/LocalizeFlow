"""Run one sanitized Closed Beta smoke call with the repository's synthetic SKU."""

from __future__ import annotations

import csv
import io
import json
from pathlib import Path

from dotenv import load_dotenv

from src.beta_import import COLUMNS, confirm_beta_import, parse_beta_upload
from src.beta_model import (
    BetaModelError,
    BetaModelSettings,
    InMemoryRunStore,
    build_beta_request,
    run_beta_generation,
)
from src.beta_quality import evaluate_beta_output

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _synthetic_import() -> dict:
    base = {
        "sku": "MV-SERUM-001",
        "unit": "",
        "evidence_level": "A",
        "source": "AI-SYNTHETIC-SPEC-001",
        "source_type": "primary_spec",
        "market_scope": "US;MX",
        "allowed_expression": "",
        "prohibited_expression": "",
        "generation_policy": "direct",
    }
    facts = {
        "product_name": "MiraVale Daily Hydration Serum",
        "specification": "30 mL",
        "ingredient": "Glycerin",
        "usage_instruction": "Apply once daily to clean skin",
        "packaging_container": "bottle",
        "packaging_material": "PP",
        "packaging_capacity": "30",
        "allowed_claim": "helps skin feel hydrated",
        "prohibited_claim": "clinically proven",
    }
    rows = []
    for attribute, value in facts.items():
        row = {**base, "attribute": attribute, "value": value}
        if attribute == "packaging_capacity":
            row["unit"] = "mL"
        if attribute == "prohibited_claim":
            row.update(generation_policy="blocked", prohibited_expression=value)
        rows.append(row)
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=COLUMNS, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    preview = parse_beta_upload(
        "ai-synthetic-facts.csv",
        buffer.getvalue().encode(),
        project_id="synthetic-smoke-project",
    )
    return confirm_beta_import(preview, confirmed_by="automated-synthetic-smoke")


def main() -> None:
    load_dotenv(PROJECT_ROOT / ".env")
    settings = BetaModelSettings.from_env()
    confirmed = _synthetic_import()
    request = build_beta_request(
        confirmed,
        sku="MV-SERUM-001",
        market="US",
        content_type="product_listing",
        target_user="Adults seeking a simple daily hydration step",
        marketing_goal="Explain the product clearly without unsupported performance claims",
        brand_tone=["clear", "restrained", "helpful"],
    )
    store = InMemoryRunStore()
    record = run_beta_generation(request, settings=settings, run_store=store)
    cached = run_beta_generation(request, settings=settings, run_store=store)
    quality = evaluate_beta_output(confirmed, record["output"])
    if not cached["cache_hit"] or cached["run_id"] != record["run_id"]:
        raise RuntimeError("Idempotency cache check failed.")
    summary = {
        "status": "passed",
        "run_id": record["run_id"],
        "model": record["model"],
        "prompt_version": record["prompt_version"],
        "schema_version": record["schema_version"],
        "rule_set_id": record["rule_set_id"],
        "input_tokens": record["input_tokens"],
        "output_tokens": record["output_tokens"],
        "latency_ms": record["latency_ms"],
        "estimated_cost_usd": record["estimated_cost_usd"],
        "attempt_count": record["attempt_count"],
        "idempotency_cache_hit": cached["cache_hit"],
        "quality_pass": quality["summary"]["pass"],
        "quality_fail": quality["summary"]["fail"],
        "export_gate": quality["export_gate"],
        "body_logging": record["body_logging"],
        "response_digest": record["response_digest"],
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    try:
        main()
    except BetaModelError as error:
        print(json.dumps({"status": "failed", "error": str(error), "body_logging": "disabled"}, indent=2))
        raise SystemExit(1) from None
