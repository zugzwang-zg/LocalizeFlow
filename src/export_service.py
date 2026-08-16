"""Central reviewed-export boundary for the model-backed Closed Beta path."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from src.beta_quality import evaluate_beta_output
from src.operations import OperationsSettings


class ExportGateError(RuntimeError):
    """Raised when reviewed content is not eligible for export."""


def beta_audit_export_bytes(
    confirmed_import: dict[str, Any],
    run_record: dict[str, Any],
    *,
    approved_at: str | None,
    operations_settings: OperationsSettings,
) -> bytes:
    """Re-evaluate current output and serialize only after every hard boundary passes."""

    output = run_record.get("output")
    if not isinstance(output, dict):
        raise ExportGateError("A structured model output is required before export.")
    quality = evaluate_beta_output(confirmed_import, output)
    if quality["export_gate"] == "blocked":
        raise ExportGateError("Current fact, language, or packaging checks block export.")
    if not approved_at:
        raise ExportGateError("Human review approval is required before export.")
    try:
        approval_time = datetime.fromisoformat(approved_at)
    except ValueError as error:
        raise ExportGateError("Human review approval time is invalid.") from error
    if approval_time.tzinfo is None:
        raise ExportGateError("Human review approval time must include a timezone.")
    operations_settings.require_exports()
    payload = {
        "run": {
            key: value
            for key, value in run_record.items()
            if key not in {"output", "quality"}
        },
        "output": output,
        "quality": quality,
        "human_review": {"status": "approved", "approved_at": approved_at},
    }
    return json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
