from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def read(relative_path: str) -> str:
    return (PROJECT_ROOT / relative_path).read_text(encoding="utf-8")


def test_portfolio_readout_preserves_evidence_and_release_boundaries() -> None:
    page = read("web/app/page.tsx")
    report = read("reports/portfolio_experience_readiness.md")
    normalized_report = " ".join(report.split())

    for required_text in (
        "跨境商品内容工作台 · 在线体验",
        "你可以完成的事情",
        "30 / 30",
        "浏览器试用 · 已开放",
        "用自己的表格试一遍",
        "10 条内容没有达到要求",
    ):
        assert required_text in page

    assert "Hosted status: published on 2026-08-16" in normalized_report
    assert "not professional independent review" in normalized_report
    assert "hosted free-trial release decision remains `NO-GO`" in normalized_report


def test_ai_social_card_is_present_and_disclosed_everywhere() -> None:
    social_card = PROJECT_ROOT / "web/public/og-portfolio.png"

    assert social_card.is_file()
    assert social_card.stat().st_size > 100_000

    for relative_path in (
        "README.md",
        "DATA_LICENSE.md",
        "THIRD_PARTY_NOTICES.md",
        "docs/open_source_asset_inventory.md",
        "reports/portfolio_experience_readiness.md",
    ):
        document = read(relative_path)
        assert "og-portfolio.png" in document
        assert "AI" in document
