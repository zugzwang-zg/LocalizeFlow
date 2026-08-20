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
EXPECTED_TAG = "v0.2.0-preview.2"
EXPECTED_RELEASE_DATE = "2026-08-16"
EXPECTED_CRYPTOGRAPHY_REQUIREMENT = "cryptography>=50.0.0,<51"
EXPECTED_CRYPTOGRAPHY_VERSION = "50.0.0"
ADDRESSED_ADVISORIES = (
    "GHSA-537c-gmf6-5ccf",
    "GHSA-g6cj-pr64-35w5",
    "GHSA-jwv3-5hgf-82ww",
    "GHSA-m2h6-j472-rp4c",
)
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
    requirements = read_text("requirements.txt").splitlines()
    uv_lock = tomllib.loads(read_text("uv.lock"))

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

    project_dependencies = pyproject["project"]["dependencies"]
    if EXPECTED_CRYPTOGRAPHY_REQUIREMENT not in project_dependencies:
        errors.append("pyproject.toml does not require the patched cryptography range.")
    if EXPECTED_CRYPTOGRAPHY_REQUIREMENT not in requirements:
        errors.append("requirements.txt does not require the patched cryptography range.")
    locked_cryptography = next(
        (package for package in uv_lock["package"] if package["name"] == "cryptography"),
        None,
    )
    if locked_cryptography is None:
        errors.append("uv.lock does not contain cryptography.")
    elif locked_cryptography["version"] != EXPECTED_CRYPTOGRAPHY_VERSION:
        errors.append("uv.lock does not pin the patched cryptography version.")
    for advisory in ADDRESSED_ADVISORIES:
        if advisory not in changelog or advisory not in release_notes:
            errors.append(f"Security advisory is missing from release materials: {advisory}")

    for marker in (
        PUBLIC_DEMO_URL,
        "## 90 秒项目摘要",
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
        "cryptography_requirement": EXPECTED_CRYPTOGRAPHY_REQUIREMENT,
        "cryptography_version": (
            locked_cryptography["version"] if locked_cryptography is not None else None
        ),
        "addressed_security_advisories": list(ADDRESSED_ADVISORIES),
        "formal_release_authorized": False,
        "required_next_gate": (
            "owner acceptance plus protected merge and main release smoke"
        ),
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
