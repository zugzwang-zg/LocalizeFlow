from __future__ import annotations

import argparse
import json
import re
import tomllib
from pathlib import Path
from typing import Any
from urllib.parse import unquote

PROJECT_ROOT = Path(__file__).resolve().parents[1]
EXPECTED_VERSION = "0.2.0"
EXPECTED_TAG = "v0.2.0-preview.1"
EXPECTED_RELEASE_DATE = "2026-08-16"
PUBLIC_DEMO_URL = "https://localizeflow-demo-86182.reidmozzie.chatgpt.site"


def read_text(relative_path: str) -> str:
    return (PROJECT_ROOT / relative_path).read_text(encoding="utf-8")


def read_json(relative_path: str) -> dict[str, Any]:
    return json.loads(read_text(relative_path))


def evaluate_candidate() -> dict[str, Any]:
    errors: list[str] = []

    pyproject = tomllib.loads(read_text("pyproject.toml"))
    web_package = read_json("web/package.json")
    free_trial = read_json("reports/free_trial_gate.json")
    prerequisites = read_json("reports/hosted_trial_prerequisites.json")
    readme = read_text("README.md")
    changelog = read_text("CHANGELOG.md")
    release_notes = read_text("RELEASE_NOTES.md")

    if pyproject["project"]["version"] != EXPECTED_VERSION:
        errors.append("pyproject.toml version does not match the candidate.")
    if web_package["version"] != EXPECTED_VERSION:
        errors.append("web/package.json version does not match the candidate.")
    expected_heading = (
        f"## [{EXPECTED_TAG.removeprefix('v')}] - {EXPECTED_RELEASE_DATE}"
    )
    if expected_heading not in changelog:
        errors.append("CHANGELOG.md does not contain the expected release date.")
    if f"# LocalizeFlow {EXPECTED_TAG}" not in release_notes:
        errors.append("RELEASE_NOTES.md does not identify the release tag.")

    for marker in (
        PUBLIC_DEMO_URL,
        "## 90 秒看懂这个项目",
        "LocalizeFlow 30/30 配对胜出",
        "托管免费试用发布结论：NO-GO",
        "生产前置条件：UNRESOLVED",
        "web/public/og-portfolio.png",
    ):
        if marker not in readme:
            errors.append(f"README.md is missing required marker: {marker}")

    for target in re.findall(r"\[[^\]]+\]\(([^)]+)\)", readme):
        if target.startswith(("http://", "https://", "#")):
            continue
        relative_path = unquote(target.split("#", maxsplit=1)[0])
        if relative_path and not (PROJECT_ROOT / relative_path).exists():
            errors.append(f"README.md has a missing local link target: {target}")

    if free_trial.get("decision") != "NO_GO":
        errors.append("Hosted free-trial gate must remain NO_GO.")
    if prerequisites.get("decision") != "UNRESOLVED":
        errors.append("Hosted prerequisites must remain UNRESOLVED.")
    if prerequisites.get("active_strategy") != "portfolio_only_public_demo":
        errors.append("Strategy A must remain the active release strategy.")

    for relative_path in (
        "LICENSE",
        "NOTICE",
        "DATA_LICENSE.md",
        "THIRD_PARTY_NOTICES.md",
        "SECURITY.md",
        "DISCLAIMER.md",
        "docs/open_source_asset_inventory.md",
        "docs/maintainer_release_checklist.md",
        "reports/open_source_release_candidate.md",
        "web/public/og-portfolio.png",
    ):
        if not (PROJECT_ROOT / relative_path).is_file():
            errors.append(f"Required release file is missing: {relative_path}")

    return {
        "computed_decision": "RELEASE_READY" if not errors else "BLOCKED",
        "candidate_tag": EXPECTED_TAG,
        "package_version": EXPECTED_VERSION,
        "release_date": EXPECTED_RELEASE_DATE,
        "formal_release_authorized": False,
        "required_next_gate": "protected merge plus main release smoke",
        "hosted_free_trial_decision": free_trial.get("decision"),
        "hosted_prerequisite_decision": prerequisites.get("decision"),
        "public_demo_url": PUBLIC_DEMO_URL,
        "errors": errors,
        "model_api_calls": 0,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--require-release-ready", action="store_true", required=True)
    args = parser.parse_args()

    result = evaluate_candidate()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if result["errors"]:
        return 2
    if args.require_release_ready:
        return 0 if result["computed_decision"] == "RELEASE_READY" else 1
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
