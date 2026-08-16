from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def read(relative_path: str) -> str:
    return (PROJECT_ROOT / relative_path).read_text(encoding="utf-8")


def normalized(relative_path: str) -> str:
    return " ".join(read(relative_path).split())


def test_public_documents_define_the_current_preview_boundary() -> None:
    privacy = normalized("PRIVACY.md")
    terms = normalized("TERMS.md")
    acceptable_use = normalized("ACCEPTABLE_USE_POLICY.md")
    disclaimer = normalized("DISCLAIMER.md")

    assert "public deterministic Web Demo" in privacy
    assert "does not call a model API" in privacy
    assert "at most 100 events" in privacy
    assert "no more than 30 days" in privacy
    assert "no hosted trial is active" in privacy.lower()
    assert "not terms for a hosted account" in terms
    assert "intellectual-property rights" in acceptable_use
    assert "other lawful basis" in acceptable_use
    assert "bypass access controls" in acceptable_use
    assert "express and implied claims" in disclaimer
    assert "does not establish truth" in disclaimer


def test_model_policy_blocks_unverified_user_data_processing() -> None:
    policy = normalized("docs/legal/MODEL_DATA_POLICY.md")

    assert "does not authorize" in policy
    assert "train or improve a third-party model" in policy
    assert "model-backed path must remain disabled for user data" in policy
    assert "public Web Demo does not call a model API" in policy


def test_hosted_templates_cannot_be_mistaken_for_active_policies() -> None:
    privacy_draft = normalized("docs/legal/HOSTED_TRIAL_PRIVACY_DRAFT.md")
    terms_draft = normalized("docs/legal/HOSTED_TRIAL_TERMS_DRAFT.md")
    disclosure = normalized("docs/legal/MODEL_PROVIDER_DISCLOSURE_TEMPLATE.md")

    for draft in (privacy_draft, terms_draft):
        assert "BLOCKED DRAFT / NOT ACTIVE" in draft
        assert "[REQUIRED]" in draft
    assert "release-blocking template" in disclosure
    assert "must be no for user data" in disclosure
    assert "Do not enable hosted model processing" in disclosure


def test_release_checklist_has_contacts_rights_transfers_and_official_sources() -> None:
    checklist = normalized("docs/legal/LEGAL_RELEASE_CHECKLIST.md")

    for required_text in (
        "Dedicated privacy request channel",
        "Security incident channel",
        "Access, correction, deletion",
        "international data routes",
        "uploaded material",
        "Federal Trade Commission",
        "eur-lex.europa.eu",
        "oag.ca.gov",
        "miit.gov.cn",
        "diputados.gob.mx",
    ):
        assert required_text in checklist


def test_readme_links_all_public_trust_documents() -> None:
    readme = read("README.md")

    for relative_path in (
        "PRIVACY.md",
        "TERMS.md",
        "ACCEPTABLE_USE_POLICY.md",
        "DISCLAIMER.md",
        "docs/legal/",
    ):
        assert relative_path in readme
