"""Validate the owner-decision register that precedes hosted implementation."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
REGISTER_PATH = PROJECT_ROOT / "reports" / "hosted_trial_prerequisites.json"
EXPECTED_IDS = {
    "operator_jurisdiction",
    "privacy_support_contacts",
    "hosting_runtime_region",
    "identity_tenant_boundary",
    "primary_data_backup_kms",
    "relay_model_data_terms",
    "durable_quota_billing_abuse",
    "monitoring_alerting_oncall",
    "deployment_rollback_drills",
    "beta_participants_reviewers",
    "final_owner_legal_security_approval",
}
BLOCKED_GATE_IDS = {
    "user_data_policy",
    "tenant_authorization",
    "quota_cost_abuse",
    "monitoring_incident_rollback_support",
    "self_service_export_deletion",
}


def evaluate_prerequisites(register_path: Path = REGISTER_PATH) -> dict[str, Any]:
    register = json.loads(register_path.read_text(encoding="utf-8"))
    errors: list[str] = []
    if register.get("schema_version") != "1.0":
        errors.append("Unsupported prerequisite schema version.")
    if register.get("scope") != "hosted_free_trial_preconditions":
        errors.append("Prerequisite scope must be hosted_free_trial_preconditions.")
    if register.get("active_strategy") != "portfolio_only_public_demo":
        errors.append("The safe portfolio-only strategy must remain active while unresolved.")
    strategy_decision = register.get("strategy_decision")
    if not isinstance(strategy_decision, dict):
        errors.append("The Strategy A decision record is missing.")
        strategy_status = None
    else:
        strategy_status = strategy_decision.get("status")
        if strategy_status != "approved_for_current_portfolio_phase":
            errors.append("Strategy A must be approved for the current portfolio phase.")
        if strategy_decision.get("selection") != register.get("active_strategy"):
            errors.append("The strategy decision does not match the active strategy.")
        if strategy_decision.get("selected_by") != "project_owner":
            errors.append("The current strategy must be selected by the project owner.")
        if not isinstance(strategy_decision.get("selected_at"), str):
            errors.append("The strategy selection date is missing.")
        revisit_triggers = strategy_decision.get("revisit_triggers")
        if not isinstance(revisit_triggers, list) or len(revisit_triggers) < 3:
            errors.append("At least three strategy reassessment triggers are required.")

    prerequisites = register.get("prerequisites")
    if not isinstance(prerequisites, list):
        return {
            "computed_decision": "UNRESOLVED",
            "errors": ["Prerequisite list is missing."],
        }
    ids = {item.get("id") for item in prerequisites if isinstance(item, dict)}
    if ids != EXPECTED_IDS:
        errors.append("Prerequisite identifiers do not match the required D5 set.")

    selected_count = 0
    verified_count = 0
    unresolved_ids: list[str] = []
    for item in prerequisites:
        if not isinstance(item, dict):
            errors.append("Every prerequisite must be an object.")
            continue
        item_id = str(item.get("id", "unknown"))
        status = item.get("status")
        if status not in {"unresolved", "selected", "verified"}:
            errors.append(f"{item_id}: invalid status.")
            continue
        if status == "unresolved":
            unresolved_ids.append(item_id)
        else:
            selected_count += 1
            if not isinstance(item.get("selection"), str) or not item["selection"].strip():
                errors.append(f"{item_id}: selected or verified items require a selection.")
        if status == "verified":
            verified_count += 1

        blocked_gates = item.get("blocking_gate_ids")
        if not isinstance(blocked_gates, list) or not blocked_gates:
            errors.append(f"{item_id}: at least one blocking gate is required.")
        elif not set(blocked_gates).issubset(BLOCKED_GATE_IDS):
            errors.append(f"{item_id}: unknown blocking gate identifier.")
        for field in ("required_decision", "safe_default"):
            if not isinstance(item.get(field), str) or not item[field].strip():
                errors.append(f"{item_id}: {field} is required.")
        required_evidence = item.get("required_evidence")
        if not isinstance(required_evidence, list) or not all(
            isinstance(value, str) and value.strip() for value in required_evidence
        ):
            errors.append(f"{item_id}: required evidence descriptions are missing.")

        evidence_paths = item.get("evidence_paths")
        if not isinstance(evidence_paths, list):
            errors.append(f"{item_id}: evidence_paths must be a list.")
            continue
        if status == "verified" and not evidence_paths:
            errors.append(f"{item_id}: verified status requires evidence paths.")
        for relative_path in evidence_paths:
            if not isinstance(relative_path, str) or Path(relative_path).is_absolute():
                errors.append(f"{item_id}: evidence paths must be repository-relative strings.")
                continue
            if relative_path == ".env" or relative_path.startswith(".private/"):
                errors.append(f"{item_id}: private configuration cannot be public evidence.")
                continue
            if not (PROJECT_ROOT / relative_path).exists():
                errors.append(f"{item_id}: missing evidence path {relative_path}.")

    all_verified = verified_count == len(EXPECTED_IDS)
    computed_decision = (
        "VERIFIED"
        if all_verified and register.get("owner_approval_recorded") is True and not errors
        else "UNRESOLVED"
    )
    if register.get("decision") != computed_decision:
        errors.append("Declared decision does not match the computed prerequisite decision.")
        computed_decision = "UNRESOLVED"

    example_env = (PROJECT_ROOT / ".env.example").read_text(encoding="utf-8")
    status_page = (PROJECT_ROOT / "STATUS.md").read_text(encoding="utf-8")
    beta_form = (
        PROJECT_ROOT / ".github" / "ISSUE_TEMPLATE" / "beta_application.yml"
    ).read_text(encoding="utf-8")
    for setting in (
        "LOCALIZEFLOW_BETA_MODEL_ENABLED=false",
        "LOCALIZEFLOW_TRIAL_LIMITS_ENABLED=false",
        "LOCALIZEFLOW_OPS_MODEL_CALLS_ENABLED=false",
        "LOCALIZEFLOW_OPS_EXPORTS_ENABLED=false",
    ):
        if setting not in example_env:
            errors.append(f"Fail-closed example configuration is missing {setting}.")
    if "reports/hosted_trial_prerequisites.json" not in status_page:
        errors.append("STATUS.md does not expose the prerequisite decision register.")
    for required_text in (
        "interest registration",
        "does not grant Beta access",
        "Do not submit personal data",
    ):
        if required_text not in beta_form:
            errors.append(f"Beta interest form is missing boundary: {required_text}.")
    if errors:
        computed_decision = "UNRESOLVED"

    return {
        "computed_decision": computed_decision,
        "declared_decision": register.get("decision"),
        "active_strategy": register.get("active_strategy"),
        "strategy_status": strategy_status,
        "prerequisite_count": len(prerequisites),
        "selected_count": selected_count,
        "verified_count": verified_count,
        "unresolved_ids": sorted(unresolved_ids),
        "errors": errors,
        "model_api_calls": 0,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    expectation = parser.add_mutually_exclusive_group(required=True)
    expectation.add_argument("--expect-unresolved", action="store_true")
    expectation.add_argument("--require-verified", action="store_true")
    args = parser.parse_args()

    result = evaluate_prerequisites()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if result["errors"]:
        return 2
    if args.expect_unresolved:
        return 0 if result["computed_decision"] == "UNRESOLVED" else 1
    return 0 if result["computed_decision"] == "VERIFIED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
