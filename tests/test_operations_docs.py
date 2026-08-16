from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def read(relative_path: str) -> str:
    return (PROJECT_ROOT / relative_path).read_text(encoding="utf-8")


def normalized(relative_path: str) -> str:
    return " ".join(read(relative_path).split())


def test_status_and_support_do_not_claim_a_hosted_service_or_sla() -> None:
    status = normalized("STATUS.md")
    support = normalized("SUPPORT.md")

    assert "Hosted account / free trial | **Not launched**" in status
    assert "machine-checked release decision is `NO_GO`" in status
    assert "not a live status page or uptime guarantee" in status
    assert "does not offer 24/7 support" in support
    assert "not a public SLA" in support
    for severity in ("P0 critical", "P1 major", "P2 standard"):
        assert severity in support


def test_operations_docs_cover_metrics_containment_and_rollback() -> None:
    monitoring = normalized("docs/operations/MONITORING_AND_ALERTING.md")
    incident = normalized("docs/operations/INCIDENT_RESPONSE.md")
    release = normalized("docs/operations/RELEASE_RUNBOOK.md")

    for metric in (
        "Availability",
        "Generation request success",
        "Page error rate",
        "Generation p95 latency",
        "Schema success",
        "Cost by account/SKU",
        "Fact hard blocks",
        "Export completion",
    ):
        assert metric in monitoring
    assert "LOCALIZEFLOW_OPS_MODEL_CALLS_ENABLED=false" in incident
    assert "LOCALIZEFLOW_OPS_EXPORTS_ENABLED=false" in incident
    assert "does not disable privacy access/export or deletion controls" in monitoring
    assert "do not move an existing Git tag" in release
    assert "scripts\\run_operations_drill.py" in release


def test_operations_flags_default_closed_in_example_environment() -> None:
    example = read(".env.example")

    assert "LOCALIZEFLOW_OPS_MONITORING_ENABLED=false" in example
    assert "LOCALIZEFLOW_OPS_MODEL_CALLS_ENABLED=false" in example
    assert "LOCALIZEFLOW_OPS_EXPORTS_ENABLED=false" in example
    assert "LOCALIZEFLOW_OPS_IDENTIFIER_HMAC_SECRET=" in example


def test_release_smoke_and_support_issue_contracts_exist() -> None:
    workflow = normalized(".github/workflows/release-smoke.yml")
    issue = normalized(".github/ISSUE_TEMPLATE/support_request.yml")

    for command in (
        "uv run pytest -q",
        "uv run python app/main.py --smoke-test",
        "uv run python scripts/run_operations_drill.py",
        "uv run python scripts/check_free_trial_release_gate.py --expect-no-go",
        "pnpm security:audit",
        "pnpm test",
        "pnpm build",
    ):
        assert command in workflow
    assert "Do not submit secrets" in issue
    assert "Use SECURITY.md" in issue


def test_readme_and_roadmap_expose_the_free_trial_no_go_decision() -> None:
    readme = normalized("README.md")
    roadmap = normalized("ROADMAP.md")
    readiness = normalized("reports/free_trial_readiness.md")

    assert "托管免费试用发布结论：NO-GO" in readme
    assert "reports/free_trial_readiness.md" in readme
    assert "Current release decision: **NO-GO**" in roadmap
    assert "Decision: **NO-GO" in readiness
