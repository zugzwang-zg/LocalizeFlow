from scripts.check_open_source_release_candidate import evaluate_candidate


def test_open_source_candidate_is_release_ready_but_not_self_authorized() -> None:
    result = evaluate_candidate()

    assert result["computed_decision"] == "RELEASE_READY"
    assert result["candidate_tag"] == "v0.2.0-preview.1"
    assert result["package_version"] == "0.2.0"
    assert result["release_date"] == "2026-08-16"
    assert result["formal_release_authorized"] is False
    assert result["required_next_gate"] == "protected merge plus main release smoke"
    assert result["hosted_free_trial_decision"] == "NO_GO"
    assert result["hosted_prerequisite_decision"] == "UNRESOLVED"
    assert result["model_api_calls"] == 0
    assert result["errors"] == []
