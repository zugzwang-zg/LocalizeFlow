from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from scripts.check_hosted_trial_prerequisites import evaluate_prerequisites

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_current_prerequisite_register_is_valid_and_unresolved() -> None:
    result = evaluate_prerequisites()

    assert result["computed_decision"] == "UNRESOLVED"
    assert result["declared_decision"] == "UNRESOLVED"
    assert result["prerequisite_count"] == 11
    assert result["selected_count"] == 0
    assert result["verified_count"] == 0
    assert len(result["unresolved_ids"]) == 11
    assert result["errors"] == []
    assert result["model_api_calls"] == 0


def test_public_register_contains_no_selection_or_private_evidence_path() -> None:
    register = json.loads(
        (PROJECT_ROOT / "reports" / "hosted_trial_prerequisites.json").read_text(
            encoding="utf-8"
        )
    )

    for item in register["prerequisites"]:
        assert item["selection"] is None
        assert item["evidence_paths"] == []
        assert item["safe_default"]


def test_cli_requires_explicit_expectation_and_refuses_verified_state() -> None:
    script = PROJECT_ROOT / "scripts" / "check_hosted_trial_prerequisites.py"
    expected = subprocess.run(
        [sys.executable, str(script), "--expect-unresolved"],
        cwd=PROJECT_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    required = subprocess.run(
        [sys.executable, str(script), "--require-verified"],
        cwd=PROJECT_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert expected.returncode == 0
    assert required.returncode == 1
    assert '"computed_decision": "UNRESOLVED"' in expected.stdout


def test_beta_application_is_interest_only_and_content_free() -> None:
    form = (
        PROJECT_ROOT / ".github" / "ISSUE_TEMPLATE" / "beta_application.yml"
    ).read_text(encoding="utf-8")
    runbook = (PROJECT_ROOT / "docs" / "beta" / "recruitment_runbook.md").read_text(
        encoding="utf-8"
    )

    for boundary in (
        "interest registration",
        "does not grant Beta access",
        "Do not submit personal data",
        "Do not submit product files",
    ):
        assert boundary in form
    assert "interest registration only" in runbook
    assert "AI review may supplement quality evidence" in runbook
