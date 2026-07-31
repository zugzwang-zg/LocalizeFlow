from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_DIR = ROOT / "schemas"
FIXTURE_PATH = ROOT / "tests" / "fixtures" / "MV-SERUM-001_US_listing_input.json"
EXPECTED_PATH = ROOT / "tests" / "expected" / "MV-SERUM-001_US_listing_expected.json"


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def check_closed_objects(value: object, path: str, errors: list[str]) -> None:
    if isinstance(value, dict):
        if value.get("type") == "object" and value.get("additionalProperties") is not False:
            errors.append(f"open_object_schema:{path}")
        for key, child in value.items():
            check_closed_objects(child, f"{path}.{key}", errors)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            check_closed_objects(child, f"{path}[{index}]", errors)


def main() -> int:
    errors: list[str] = []
    schema_paths = sorted(SCHEMA_DIR.glob("*.schema.json"))
    schemas = {path.name: load_json(path) for path in schema_paths}

    for name, schema in schemas.items():
        Draft202012Validator.check_schema(schema)
        check_closed_objects(schema, name, errors)

    fixture = load_json(FIXTURE_PATH)
    expected = load_json(EXPECTED_PATH)
    content_schema = schemas["content_output.schema.json"]
    validation_errors = sorted(
        Draft202012Validator(content_schema).iter_errors(expected),
        key=lambda item: list(item.path),
    )
    errors.extend(
        f"schema_validation:{'.'.join(map(str, item.path))}:{item.message}"
        for item in validation_errors
    )

    facts = {item["fact_id"]: item for item in fixture["facts"]}
    if len(expected["content"]["bullet_points"]) != 5:
        errors.append("listing_bullet_count_not_5")
    if len(expected["content"]["title"]) > 150:
        errors.append("listing_title_over_150")
    if len(expected["content"]["description"]) > 5000:
        errors.append("listing_description_over_5000")

    claim_ids: set[str] = set()
    for claim in expected["claims"]:
        if claim["claim_id"] in claim_ids:
            errors.append(f"duplicate_claim_id:{claim['claim_id']}")
        claim_ids.add(claim["claim_id"])
        if not claim["fact_ids"]:
            errors.append(f"claim_without_fact_id:{claim['claim_id']}")
        for fact_id in claim["fact_ids"]:
            if fact_id not in facts:
                errors.append(f"unknown_fact_id:{claim['claim_id']}:{fact_id}")
                continue
            if facts[fact_id]["evidence_level"] not in {"A", "B"}:
                errors.append(f"blocked_fact_used:{claim['claim_id']}:{fact_id}")
        if claim["evidence_level"] == "B":
            cautious = ("helps" in claim["text"].lower()) or ("skin feel" in claim["text"].lower())
            if not cautious:
                errors.append(f"missing_cautious_qualifier:{claim['claim_id']}")

    prohibited = [term.lower() for term in fixture["blocked_claim_examples"]]
    rendered = json.dumps(expected["content"], ensure_ascii=False).lower()
    for term in prohibited:
        if term in rendered:
            errors.append(f"prohibited_claim_present:{term}")

    prompt_paths = [
        ROOT / "baseline_prompt.md",
        ROOT / "fact_extraction_prompt.md",
        ROOT / "campaign_planner_prompt.md",
        ROOT / "localization_prompt_en.md",
        ROOT / "localization_prompt_es.md",
        ROOT / "listing_prompt.md",
        ROOT / "tiktok_script_prompt.md",
        ROOT / "social_copy_prompt.md",
        ROOT / "evaluator_prompt.md",
    ]
    for path in prompt_paths:
        if not path.exists() or path.stat().st_size == 0:
            errors.append(f"missing_or_empty_prompt:{path.name}")

    manifest = load_json(ROOT / "prompt_manifest.json")
    if manifest["api_calls_made_in_stage_8"] != 0:
        errors.append("unexpected_api_call_count")
    if manifest["provider_configuration"]["structured_output"]["strict"] is not True:
        errors.append("structured_output_not_strict")

    report = {
        "status": "pass" if not errors else "fail",
        "schema_files_validated": len(schema_paths),
        "prompt_files_checked": len(prompt_paths),
        "fixture_sku": fixture["task"]["sku"],
        "fixture_market": fixture["task"]["market"],
        "fixture_content_type": fixture["task"]["content_type"],
        "claim_count": len(expected["claims"]),
        "fact_refs_checked": sum(len(item["fact_ids"]) for item in expected["claims"]),
        "api_calls_made": 0,
        "errors": errors,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
