"""Validate the machine-readable hosted free-trial release decision."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

try:
    from scripts.check_hosted_trial_prerequisites import evaluate_prerequisites
except ModuleNotFoundError:  # Direct execution adds scripts/, not its parent, to sys.path.
    from check_hosted_trial_prerequisites import evaluate_prerequisites

PROJECT_ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = PROJECT_ROOT / "reports" / "free_trial_gate.json"
EXPECTED_GATES = {
    "user_data_policy",
    "tenant_authorization",
    "quota_cost_abuse",
    "fact_packaging_export_gate",
    "monitoring_incident_rollback_support",
    "self_service_export_deletion",
}


def evaluate_gate(manifest_path: Path = MANIFEST_PATH) -> dict[str, Any]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    errors: list[str] = []
    if manifest.get("schema_version") != "1.0":
        errors.append("Unsupported gate schema version.")
    if manifest.get("scope") != "hosted_free_trial":
        errors.append("Gate scope must be hosted_free_trial.")
    gates = manifest.get("gates")
    if not isinstance(gates, list):
        return {"computed_decision": "NO_GO", "errors": ["Gate list is missing."]}
    ids = {gate.get("id") for gate in gates if isinstance(gate, dict)}
    if ids != EXPECTED_GATES:
        errors.append("Gate identifiers do not match the required Stage D set.")

    ready_count = 0
    blocked_ids: list[str] = []
    for gate in gates:
        if not isinstance(gate, dict):
            errors.append("Every gate must be an object.")
            continue
        gate_id = str(gate.get("id", "unknown"))
        local_status = gate.get("local_status")
        release_status = gate.get("release_status")
        blockers = gate.get("blockers")
        evidence = gate.get("evidence")
        if local_status not in {"passed", "partial", "blocked"}:
            errors.append(f"{gate_id}: invalid local status.")
        if release_status not in {"ready", "blocked"}:
            errors.append(f"{gate_id}: invalid release status.")
        if not isinstance(blockers, list) or not all(
            isinstance(item, str) and item.strip() for item in blockers
        ):
            errors.append(f"{gate_id}: blockers must be non-empty strings in a list.")
            blockers = []
        if release_status == "ready":
            ready_count += 1
            if blockers:
                errors.append(f"{gate_id}: a ready gate cannot retain blockers.")
        else:
            blocked_ids.append(gate_id)
            if not blockers:
                errors.append(f"{gate_id}: a blocked gate must explain its blockers.")
        if not isinstance(evidence, list) or not evidence:
            errors.append(f"{gate_id}: evidence paths are required.")
            continue
        for relative_path in evidence:
            if not isinstance(relative_path, str) or Path(relative_path).is_absolute():
                errors.append(f"{gate_id}: evidence paths must be repository-relative strings.")
                continue
            if relative_path == ".env" or relative_path.startswith(".private/"):
                errors.append(f"{gate_id}: private files cannot be release evidence.")
                continue
            if not (PROJECT_ROOT / relative_path).exists():
                errors.append(f"{gate_id}: missing evidence path {relative_path}.")

    prerequisite_result = evaluate_prerequisites()
    if prerequisite_result.get("errors"):
        errors.append("Hosted prerequisite register has validation errors.")
    prerequisite_decision = prerequisite_result.get("computed_decision")
    computed_decision = (
        "GO"
        if not blocked_ids and not errors and prerequisite_decision == "VERIFIED"
        else "NO_GO"
    )
    if manifest.get("decision") != computed_decision:
        errors.append("Declared decision does not match the computed gate decision.")
        computed_decision = "NO_GO"

    public_status = (PROJECT_ROOT / "STATUS.md").read_text(encoding="utf-8")
    example_env = (PROJECT_ROOT / ".env.example").read_text(encoding="utf-8")
    hosted_privacy = (
        PROJECT_ROOT / "docs" / "legal" / "HOSTED_TRIAL_PRIVACY_DRAFT.md"
    ).read_text(encoding="utf-8")
    hosted_terms = (
        PROJECT_ROOT / "docs" / "legal" / "HOSTED_TRIAL_TERMS_DRAFT.md"
    ).read_text(encoding="utf-8")
    if "Hosted account / free trial | **Not launched**" not in public_status:
        errors.append("Public status no longer states that the hosted trial is not launched.")
    for setting in (
        "LOCALIZEFLOW_OPS_MONITORING_ENABLED=false",
        "LOCALIZEFLOW_OPS_MODEL_CALLS_ENABLED=false",
        "LOCALIZEFLOW_OPS_EXPORTS_ENABLED=false",
    ):
        if setting not in example_env:
            errors.append(f"Fail-closed example configuration is missing {setting}.")
    if "[REQUIRED]" not in hosted_privacy or "[REQUIRED]" not in hosted_terms:
        errors.append("Hosted legal drafts lost their release-blocking placeholders.")
    if errors:
        computed_decision = "NO_GO"

    return {
        "computed_decision": computed_decision,
        "declared_decision": manifest.get("decision"),
        "gate_count": len(gates),
        "ready_count": ready_count,
        "blocked_ids": sorted(blocked_ids),
        "prerequisite_decision": prerequisite_decision,
        "active_strategy": prerequisite_result.get("active_strategy"),
        "strategy_status": prerequisite_result.get("strategy_status"),
        "errors": errors,
        "model_api_calls": 0,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    expectation = parser.add_mutually_exclusive_group(required=True)
    expectation.add_argument("--expect-no-go", action="store_true")
    expectation.add_argument("--require-go", action="store_true")
    args = parser.parse_args()

    result = evaluate_gate()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if result["errors"]:
        return 2
    if args.expect_no_go:
        return 0 if result["computed_decision"] == "NO_GO" else 1
    return 0 if result["computed_decision"] == "GO" else 1


if __name__ == "__main__":
    raise SystemExit(main())
