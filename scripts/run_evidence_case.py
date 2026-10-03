"""Offline evidence handoff example; deliberately never grants human approval."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.demo_service import (  # noqa: E402
    DemoExportError,
    evaluate_text,
    generate_content_pack,
    pack_as_json_bytes,
)


def build_case() -> dict:
    dataset = json.loads(
        (ROOT / "data/insights/consumer_insights.json").read_text(encoding="utf-8")
    )
    insights = {item["insight_id"]: item for item in dataset["insights"]}
    assert insights["IN-US-001"]["mapping_status"] == "eligible"
    assert insights["IN-US-002"]["mapping_status"] == "blocked"
    variants = []
    for market in ("US", "MX"):
        pack = generate_content_pack(
            sku="MV-SERUM-001",
            market=market,
            primary_content_type="product_listing",
            target_user="default",
            marketing_goal="consideration",
            selling_points=[],
            brand_tone=[],
        )
        text = pack["versions"]["product_listing"]["enhanced"]
        rejected = evaluate_text(
            sku=pack["sku"],
            market=market,
            content_type="product_listing",
            text=text + " FDA-approved. Contains retinol.",
        )
        assert rejected["export_gate"] == "blocked"
        try:
            pack_as_json_bytes(pack)
        except DemoExportError:
            pass
        else:
            raise AssertionError("Unreviewed content must not export")
        variants.append(
            {
                "market": market,
                "candidate": text,
                "quality": pack["primary_quality"],
                "unsafe_edit_gate": rejected["export_gate"],
                "human_review": "pending",
            }
        )
    return {
        "mode": "offline_handoff_example",
        "source": dataset["source"],
        "eligible_insight": insights["IN-US-001"],
        "blocked_insight": insights["IN-US-002"],
        "variants": variants,
    }


if __name__ == "__main__":
    print(json.dumps(build_case(), ensure_ascii=True, indent=2))
