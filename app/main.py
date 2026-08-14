"""LocalizeFlow Streamlit demonstration."""

from __future__ import annotations

import html
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.demo_service import (  # noqa: E402
    CONTENT_TYPE_LABELS,
    CONTENT_TYPES,
    MARKET_CONFIG,
    PRODUCT_LABELS,
    allowed_and_prohibited,
    evaluate_text,
    generate_content_pack,
    list_products,
    pack_as_csv_bytes,
    pack_as_json_bytes,
    product_profile,
    selling_point_options,
    update_pack_with_manual_text,
)

STEP_LABELS = {
    1: "商品资料",
    2: "营销任务",
    3: "生成结果",
    4: "质量检查",
    5: "版本与导出",
}

STATUS_LABELS = {
    "pass": "通过",
    "warning": "需复核",
    "fail": "阻断",
}


def run_smoke_test() -> None:
    """Confirm that the project assets and demo service are available."""
    products = list_products()
    if len(products) != 5:
        raise RuntimeError(f"Expected 5 products, found {len(products)}")
    pack = generate_content_pack(
        sku=products[0]["sku"],
        market="US",
        primary_content_type="product_listing",
        target_user="demo",
        marketing_goal="consideration",
        selling_points=[],
        brand_tone=["温和", "可信"],
    )
    if len(pack["versions"]) != 3:
        raise RuntimeError("Content pack is incomplete.")
    print("LocalizeFlow startup check passed.")


def _inject_css(st: Any) -> None:
    st.markdown(
        """
        <style>
        :root {
          --ink: #0b302c;
          --spruce: #1f6e63;
          --sea-glass: #dff2ea;
          --paper: #f7f4ec;
          --amber: #e6a84a;
          --coral: #d85d4a;
          --fog: #e8ece8;
          --muted: #68756f;
        }
        .stApp {
          background:
            linear-gradient(90deg, rgba(31,110,99,.035) 1px, transparent 1px),
            var(--paper);
          background-size: 28px 28px;
          color: var(--ink);
        }
        [data-testid="stHeader"] { background: rgba(247,244,236,.92); }
        [data-testid="stSidebar"] {
          background: var(--ink);
          border-right: 1px solid rgba(255,255,255,.09);
        }
        [data-testid="stSidebar"] * { color: #f8fbf9; }
        [data-testid="stSidebar"] [data-baseweb="radio"] > div {
          gap: .2rem;
        }
        [data-testid="stSidebar"] label {
          border-radius: 8px;
          padding: .34rem .5rem;
        }
        [data-testid="stSidebar"] label:hover {
          background: rgba(255,255,255,.08);
        }
        .block-container {
          max-width: 1240px;
          padding-top: 1.2rem;
          padding-bottom: 4rem;
        }
        h1, h2, h3 {
          font-family: Georgia, "Noto Serif SC", "Songti SC", serif !important;
          color: var(--ink) !important;
          letter-spacing: -.025em;
        }
        h1 { font-size: clamp(2.3rem, 5vw, 4.8rem) !important; line-height: .98 !important; }
        p, label, input, textarea, button, [data-testid="stMarkdownContainer"] {
          font-family: Inter, "Microsoft YaHei", "PingFang SC", sans-serif;
        }
        .lf-brand {
          font-family: Georgia, serif;
          font-size: 1.65rem;
          letter-spacing: -.04em;
          color: #fff;
          margin: .2rem 0 .15rem;
        }
        .lf-brand-note {
          font-family: ui-monospace, "Cascadia Code", monospace;
          color: #a9c9c0;
          font-size: .72rem;
          letter-spacing: .11em;
          text-transform: uppercase;
          margin-bottom: 1.1rem;
        }
        .nav-active {
          background: rgba(255,255,255,.13);
          border-left: 3px solid var(--amber);
          border-radius: 4px;
          color: #fff;
          font-weight: 700;
          padding: .58rem .7rem;
          margin: .2rem 0;
        }
        [data-testid="stSidebar"] div[data-testid="stButton"] button {
          background: transparent;
          border: 0;
          color: #f8fbf9;
          justify-content: flex-start;
          padding-left: .7rem;
        }
        [data-testid="stSidebar"] div[data-testid="stButton"] button:hover {
          background: rgba(255,255,255,.08);
        }
        .eyebrow {
          color: var(--spruce);
          font: 700 .74rem/1.2 ui-monospace, "Cascadia Code", monospace;
          letter-spacing: .12em;
          text-transform: uppercase;
          margin-bottom: .65rem;
        }
        .page-lede {
          max-width: 760px;
          font-size: 1.04rem;
          color: #4b5b55;
          line-height: 1.8;
          margin: -.35rem 0 1.7rem;
        }
        .step-strip {
          display: grid;
          grid-template-columns: repeat(5, minmax(0, 1fr));
          border: 1px solid #b7c8c1;
          background: rgba(255,255,255,.65);
          margin: .35rem 0 2rem;
        }
        .step-item {
          padding: .72rem .75rem;
          border-right: 1px solid #b7c8c1;
          color: #73817b;
          font-size: .82rem;
          min-height: 58px;
        }
        .step-item:last-child { border-right: 0; }
        .step-item strong {
          display: block;
          font-family: ui-monospace, "Cascadia Code", monospace;
          font-size: .68rem;
          letter-spacing: .08em;
          margin-bottom: .18rem;
        }
        .step-item.active {
          color: #fff;
          background: var(--spruce);
        }
        .step-item.done {
          color: var(--ink);
          background: var(--sea-glass);
        }
        .ledger {
          border-top: 4px solid var(--ink);
          border-bottom: 1px solid #b7c8c1;
          background: rgba(255,255,255,.62);
          padding: 1.05rem 1.15rem;
          margin-bottom: 1rem;
        }
        .ledger-label {
          color: var(--muted);
          font: 700 .68rem ui-monospace, "Cascadia Code", monospace;
          letter-spacing: .08em;
          text-transform: uppercase;
        }
        .ledger-value {
          font-family: Georgia, "Noto Serif SC", serif;
          color: var(--ink);
          font-size: 1.3rem;
          margin-top: .25rem;
        }
        .fact-row {
          display: grid;
          grid-template-columns: minmax(0,1fr) minmax(220px,.38fr);
          border-top: 1px solid #c8d3ce;
          padding: .9rem 0;
          gap: 1rem;
        }
        .fact-row:last-child { border-bottom: 1px solid #c8d3ce; }
        .fact-text { color: #273b36; line-height: 1.55; }
        .fact-rail {
          border-left: 3px solid var(--spruce);
          padding-left: .8rem;
        }
        .rail-title {
          color: var(--spruce);
          font: 700 .66rem ui-monospace, "Cascadia Code", monospace;
          letter-spacing: .1em;
          text-transform: uppercase;
          margin-bottom: .35rem;
        }
        .fact-chip {
          display: inline-block;
          font: 600 .68rem ui-monospace, "Cascadia Code", monospace;
          background: var(--sea-glass);
          color: var(--ink);
          border: 1px solid #a8c9bd;
          border-radius: 99px;
          padding: .18rem .46rem;
          margin: .1rem .18rem .1rem 0;
        }
        .rule-line {
          display: grid;
          grid-template-columns: 112px 150px minmax(0,1fr);
          gap: 1rem;
          align-items: start;
          border-top: 1px solid #c8d3ce;
          padding: .78rem 0;
        }
        .rule-line:last-child { border-bottom: 1px solid #c8d3ce; }
        .tag {
          display: inline-block;
          width: fit-content;
          border-radius: 99px;
          padding: .2rem .55rem;
          font: 700 .68rem ui-monospace, "Cascadia Code", monospace;
          letter-spacing: .04em;
        }
        .tag.pass { color: #175946; background: #d8f0e4; }
        .tag.warning { color: #755006; background: #f9e6b7; }
        .tag.fail { color: #8b2d24; background: #f8d4cf; }
        .content-sheet {
          background: #fff;
          border: 1px solid #c8d3ce;
          border-top: 4px solid var(--spruce);
          padding: 1.1rem 1.2rem;
          margin: .45rem 0 1.1rem;
          box-shadow: 0 10px 26px rgba(11,48,44,.055);
        }
        .content-sheet h4 {
          font-family: Georgia, "Noto Serif SC", serif;
          font-size: 1.28rem;
          margin: 0 0 .4rem;
          color: var(--ink);
        }
        .content-sheet p { margin: 0; color: #334942; line-height: 1.65; }
        .note-band {
          border-left: 4px solid var(--amber);
          background: #fff5da;
          padding: .78rem .95rem;
          color: #624915;
          margin: .7rem 0 1.1rem;
        }
        .risk-high { color: #982f26; }
        .risk-medium { color: #805711; }
        .risk-low { color: #175946; }
        div[data-testid="stMetric"] {
          background: rgba(255,255,255,.72);
          border-top: 3px solid var(--spruce);
          padding: .75rem .8rem;
        }
        div[data-testid="stButton"] button,
        div[data-testid="stDownloadButton"] button {
          border-radius: 4px;
          border: 1px solid var(--ink);
          font-weight: 700;
        }
        div[data-testid="stButton"] button[kind="primary"],
        div[data-testid="stDownloadButton"] button[kind="primary"] {
          background: var(--ink);
          color: #fff;
        }
        div[data-baseweb="select"] > div,
        div[data-baseweb="base-input"],
        textarea {
          border-radius: 4px !important;
        }
        .micro {
          color: var(--muted);
          font: .72rem/1.5 ui-monospace, "Cascadia Code", monospace;
        }
        @media (max-width: 780px) {
          .step-strip { grid-template-columns: 1fr; }
          .step-item { border-right: 0; border-bottom: 1px solid #b7c8c1; min-height: auto; }
          .fact-row, .rule-line { grid-template-columns: 1fr; }
          .block-container { padding-left: 1rem; padding-right: 1rem; }
        }
        @media (prefers-reduced-motion: reduce) {
          * { scroll-behavior: auto !important; transition: none !important; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _initialize_state(st: Any) -> None:
    defaults = {
        "step": 1,
        "product_sku": "MV-SERUM-001",
        "market": "US",
        "primary_content_type": "product_listing",
        "source_text": "",
        "source_note": "",
        "pack": None,
        "final_pack": None,
        "final_editor": "",
        "confirmed": False,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def _navigate(st: Any, step: int) -> None:
    st.session_state.step = step
    st.rerun()


def _render_sidebar(st: Any) -> None:
    with st.sidebar:
        st.markdown('<div class="lf-brand">LocalizeFlow</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="lf-brand-note">evidence-led localization desk</div>',
            unsafe_allow_html=True,
        )
        for step, label in STEP_LABELS.items():
            button_label = f"{step:02d}  {label}"
            if step == st.session_state.step:
                st.markdown(
                    f'<div class="nav-active">{html.escape(button_label)}</div>',
                    unsafe_allow_html=True,
                )
            elif st.button(
                button_label,
                key=f"sidebar_nav_{step}",
                use_container_width=True,
            ):
                _navigate(st, step)
        st.divider()
        completed = 60 if st.session_state.pack else 0
        st.caption("演示状态")
        st.write(f"**商品**  {st.session_state.product_sku}")
        st.write(f"**市场**  {st.session_state.market}")
        st.write(f"**内容包**  {'已生成' if st.session_state.pack else '未生成'}")
        st.progress(completed / 60, text="内容准备度")
        st.caption("离线确定性 Demo · 不调用模型 API")


def _render_stepper(st: Any) -> None:
    active = st.session_state.step
    items = []
    for step, label in STEP_LABELS.items():
        state_class = "active" if step == active else "done" if step < active else ""
        items.append(
            f'<div class="step-item {state_class}"><strong>{step:02d}</strong>'
            f"{html.escape(label)}</div>"
        )
    st.markdown(
        f'<div class="step-strip">{"".join(items)}</div>',
        unsafe_allow_html=True,
    )


def _page_heading(st: Any, eyebrow: str, title: str, lede: str) -> None:
    st.markdown(f'<div class="eyebrow">{html.escape(eyebrow)}</div>', unsafe_allow_html=True)
    st.title(title)
    st.markdown(f'<div class="page-lede">{html.escape(lede)}</div>', unsafe_allow_html=True)


def _ledger(st: Any, label: str, value: str) -> None:
    st.markdown(
        '<div class="ledger">'
        f'<div class="ledger-label">{html.escape(label)}</div>'
        f'<div class="ledger-value">{html.escape(value)}</div>'
        "</div>",
        unsafe_allow_html=True,
    )


def _render_expression_rows(st: Any, records: list[dict[str, str]], mode: str) -> None:
    if not records:
        st.info("当前商品没有该类记录。")
        return
    for record in records:
        chip_class = "pass" if mode == "allowed" else "fail"
        st.markdown(
            '<div class="rule-line">'
            f'<span class="tag {chip_class}">{html.escape(record["mode"])}</span>'
            f'<span class="micro">{html.escape(record["fact_id"])}</span>'
            f'<div>{html.escape(record["text"])}</div>'
            "</div>",
            unsafe_allow_html=True,
        )


def _claim_for(
    pack: dict[str, Any], content_type: str, location: str
) -> dict[str, Any] | None:
    for claim in pack.get("claims", []):
        if claim["content_type"] == content_type and claim["location"] == location:
            return claim
    return None


def _render_claim(
    st: Any,
    *,
    title: str,
    text: str,
    claim: dict[str, Any] | None,
) -> None:
    fact_ids = claim["fact_ids"] if claim else []
    chips = "".join(
        f'<span class="fact-chip">{html.escape(fact_id)}</span>'
        for fact_id in fact_ids
    )
    evidence = chips or '<span class="micro">CTA / 非事实陈述</span>'
    st.markdown(
        '<div class="fact-row">'
        '<div class="fact-text">'
        f'<div class="micro">{html.escape(title)}</div>'
        f"{html.escape(text)}"
        "</div>"
        '<div class="fact-rail"><div class="rail-title">证据 / Evidence</div>'
        f"{evidence}</div></div>",
        unsafe_allow_html=True,
    )


def _render_quality(st: Any, quality: dict[str, Any]) -> None:
    risk_labels = {"low": "低风险", "medium": "中风险", "high": "高风险"}
    gate_labels = {"human_review": "等待人工确认", "blocked": "阻断导出"}
    columns = st.columns(4)
    columns[0].metric("质量分", f'{quality["quality_score"]}/100')
    columns[1].metric("风险等级", risk_labels[quality["risk_level"]])
    columns[2].metric("事实错误", quality["fact_error_count"])
    columns[3].metric("导出闸门", gate_labels[quality["export_gate"]])
    st.markdown("### 检查明细")
    for check in quality["checks"]:
        status = check["status"]
        suggestion = (
            f'<div class="micro">建议：{html.escape(check["suggestion"])}</div>'
            if check["suggestion"]
            else ""
        )
        st.markdown(
            '<div class="rule-line">'
            f'<span class="tag {status}">{STATUS_LABELS[status]}</span>'
            f'<strong>{html.escape(check["name"])}</strong>'
            f'<div>{html.escape(check["detail"])}{suggestion}</div>'
            "</div>",
            unsafe_allow_html=True,
        )


def _render_page_product(st: Any) -> None:
    _page_heading(
        st,
        "01 / source of truth",
        "先把商品事实钉牢。",
        "生成之前先看证据。选择商品、核对允许与禁止表达；粘贴的中文资料只保存在当前会话，不会覆盖已冻结的事实库。",
    )
    product_options = [item["sku"] for item in list_products()]
    selected_sku = st.selectbox(
        "选择商品",
        product_options,
        format_func=lambda sku: f"{sku} · {PRODUCT_LABELS[sku]}",
        key="product_sku",
    )
    profile = product_profile(selected_sku, st.session_state.market)
    columns = st.columns(4)
    for column, label, value in zip(
        columns,
        ("商品", "品类", "规格", f"参考价格 · {profile['currency']}"),
        (
            profile["name_zh"],
            profile["category"],
            profile["size"],
            profile["price"],
        ),
    ):
        with column:
            _ledger(st, label, value)

    st.markdown("### 结构化事实")
    fact_columns = st.columns([1.1, 1])
    with fact_columns[0]:
        st.markdown("**已核实特征**")
        for fact in profile["features"][:5]:
            st.markdown(
                f'- `{fact["fact_id"]}` · {fact["value"]}',
            )
        st.markdown("**适用人群与用法**")
        st.write(profile["target_users"])
        st.write(profile["usage"])
    with fact_columns[1]:
        st.markdown("**核心成分**")
        for fact in profile["ingredients"]:
            st.markdown(f'- `{fact["fact_id"]}` · {fact["value"]}')
        st.markdown("**包装事实**")
        for fact in profile["packaging"][:4]:
            st.markdown(f'- `{fact["fact_id"]}` · {fact["value"]}')

    expression_tabs = st.tabs(["允许表达", "禁止表达"])
    expressions = allowed_and_prohibited(selected_sku)
    with expression_tabs[0]:
        _render_expression_rows(st, expressions["allowed"], "allowed")
    with expression_tabs[1]:
        _render_expression_rows(st, expressions["prohibited"], "prohibited")

    st.markdown("### 补充中文商品资料")
    uploaded = st.file_uploader(
        "上传 TXT、MD、CSV 或 JSON",
        type=["txt", "md", "csv", "json"],
        help="Demo 只读取文本，不写回事实库。",
    )
    if uploaded is not None:
        uploaded_text = uploaded.getvalue().decode("utf-8-sig", errors="replace")
        st.session_state.source_text = uploaded_text
        st.session_state.source_note = f"uploaded:{uploaded.name}"
    st.text_area(
        "或粘贴资料",
        key="source_text",
        height=150,
        placeholder="例如：商品中文名称、规格、成分、使用方式、包装信息……",
    )
    st.markdown(
        '<div class="note-band">新增资料不会直接成为可用事实。正式流程中需要先完成来源分级与人工确认。</div>',
        unsafe_allow_html=True,
    )
    if st.button("保存资料并进入营销任务 →", type="primary", use_container_width=True):
        if st.session_state.source_text and not st.session_state.source_note:
            st.session_state.source_note = "pasted_in_session"
        st.session_state.pack = None
        st.session_state.final_pack = None
        st.session_state.confirmed = False
        _navigate(st, 2)


def _render_page_task(st: Any) -> None:
    _page_heading(
        st,
        "02 / campaign brief",
        "把“翻译”变成一份营销任务。",
        "市场、平台、目标用户和卖点会共同决定内容结构。语言由目标市场锁定，避免市场与语言错配。",
    )
    left, right = st.columns(2)
    with left:
        market = st.selectbox(
            "目标市场",
            options=list(MARKET_CONFIG),
            format_func=lambda key: MARKET_CONFIG[key]["label"],
            key="market",
        )
        language = MARKET_CONFIG[market]["language"]
        st.text_input("输出语言", value=language, disabled=True)
        user_options = [
            product_profile(st.session_state.product_sku, market)["target_users"],
            "注重成分透明与日常使用体验的消费者",
            "希望精简护肤步骤的旅行用户",
        ]
        target_user = st.selectbox("目标用户", user_options)
        marketing_goal = st.selectbox(
            "营销目标",
            options=["awareness", "consideration", "conversion", "retention"],
            index=1,
            format_func={
                "awareness": "认知 · Awareness",
                "consideration": "考虑 · Consideration",
                "conversion": "转化 · Conversion",
                "retention": "复购 · Retention",
            }.get,
            key="marketing_goal",
        )
    with right:
        content_type = st.selectbox(
            "平台和内容类型",
            options=list(CONTENT_TYPES),
            format_func=lambda item: (
                f"{CONTENT_TYPE_LABELS[item]} · "
                f"{MARKET_CONFIG[market]['platforms'][item]}"
            ),
            key="primary_content_type",
        )
        st.text_input(
            "目标平台",
            value=MARKET_CONFIG[market]["platforms"][content_type],
            disabled=True,
        )
        point_options = selling_point_options(st.session_state.product_sku)
        selling_points = st.multiselect(
            "核心卖点",
            options=point_options,
            default=point_options[: min(3, len(point_options))],
        )
        brand_tone = st.multiselect(
            "品牌语调",
            options=["温和", "清晰", "可信", "简洁", "克制", "有行动导向"],
            default=["温和", "清晰", "可信"],
            key="brand_tone",
        )

    _ledger(
        st,
        "任务摘要",
        f"{st.session_state.product_sku} → {market} / {language} → "
        f"{MARKET_CONFIG[market]['platforms'][content_type]}",
    )
    back, action = st.columns([1, 2])
    with back:
        if st.button("← 返回商品资料", use_container_width=True):
            _navigate(st, 1)
    with action:
        if st.button("生成本地化内容包 →", type="primary", use_container_width=True):
            with st.spinner("正在组合事实、品牌与平台约束……"):
                pack = generate_content_pack(
                    sku=st.session_state.product_sku,
                    market=market,
                    primary_content_type=content_type,
                    target_user=target_user,
                    marketing_goal=marketing_goal,
                    selling_points=selling_points,
                    brand_tone=brand_tone,
                    source_note=st.session_state.source_note,
                )
                st.session_state.pack = pack
                st.session_state.final_pack = None
                st.session_state.final_editor = pack["versions"][content_type][
                    "enhanced"
                ]
                st.session_state.confirmed = False
            _navigate(st, 3)


def _require_pack(st: Any) -> dict[str, Any] | None:
    pack = st.session_state.pack
    if pack:
        return pack
    st.warning("尚未生成内容包。请先完成营销任务。")
    if st.button("前往营销任务", type="primary"):
        _navigate(st, 2)
    return None


def _render_listing(st: Any, pack: dict[str, Any]) -> None:
    parsed = pack["versions"]["product_listing"]["enhanced_parsed"]
    st.markdown(
        f'<div class="content-sheet"><div class="micro">商品标题</div>'
        f'<h4>{html.escape(parsed["title"])}</h4></div>',
        unsafe_allow_html=True,
    )
    _render_claim(
        st,
        title="title",
        text=parsed["title"],
        claim=_claim_for(pack, "product_listing", "title"),
    )
    for index, bullet in enumerate(parsed["bullet_points"]):
        _render_claim(
            st,
            title=f"bullet {index + 1}",
            text=bullet,
            claim=_claim_for(pack, "product_listing", f"bullet_points[{index}]"),
        )
    _render_claim(
        st,
        title="description",
        text=parsed["description"],
        claim=_claim_for(pack, "product_listing", "description"),
    )


def _render_video(st: Any, pack: dict[str, Any]) -> None:
    parsed = pack["versions"]["short_video_script"]["enhanced_parsed"]
    for index, scene in enumerate(parsed["scenes"]):
        _render_claim(
            st,
            title=f"scene {index + 1}",
            text=scene,
            claim=_claim_for(pack, "short_video_script", f"scenes[{index}]"),
        )
    _render_claim(
        st,
        title="caption",
        text=parsed["caption"],
        claim=_claim_for(pack, "short_video_script", "caption"),
    )


def _render_social(st: Any, pack: dict[str, Any]) -> None:
    parsed = pack["versions"]["social_ad_copy"]["enhanced_parsed"]
    for field, label in (("hook", "广告标题 / Hook"), ("body", "正文"), ("cta", "CTA")):
        _render_claim(
            st,
            title=label,
            text=parsed[field],
            claim=_claim_for(pack, "social_ad_copy", field),
        )


def _render_page_results(st: Any) -> None:
    pack = _require_pack(st)
    if not pack:
        return
    _page_heading(
        st,
        "03 / generated pack",
        "内容与证据一起交付。",
        "同一任务一次生成 Listing、15 秒 TikTok 脚本和社媒广告文案。右侧证据条显示每项事实陈述所依据的 fact_id。",
    )
    columns = st.columns(4)
    columns[0].metric("市场", pack["market"])
    columns[1].metric("语言", pack["language"])
    columns[2].metric("内容类型", "3")
    columns[3].metric("模型调用", "0")
    st.markdown(
        '<div class="note-band">这是离线确定性演示输出。内容可复现，但不代表平台批准；发布前仍需质量检查和人工确认。</div>',
        unsafe_allow_html=True,
    )
    tabs = st.tabs(["商品 Listing", "TikTok 脚本", "社媒广告文案"])
    with tabs[0]:
        _render_listing(st, pack)
    with tabs[1]:
        _render_video(st, pack)
    with tabs[2]:
        _render_social(st, pack)
    back, action = st.columns([1, 2])
    with back:
        if st.button("← 返回营销任务", use_container_width=True):
            _navigate(st, 2)
    with action:
        if st.button("查看质量检查 →", type="primary", use_container_width=True):
            _navigate(st, 4)


def _render_page_quality(st: Any) -> None:
    pack = _require_pack(st)
    if not pack:
        return
    _page_heading(
        st,
        "04 / quality gate",
        "分数不能盖过事实错误。",
        "主内容会依次检查事实边界、包装、术语、平台结构、字符限制、品牌语气与本地化表现。任何事实失败都会阻断导出。",
    )
    content_type = pack["primary_content_type"]
    current_text = st.session_state.final_editor or pack["versions"][content_type][
        "enhanced"
    ]
    quality = evaluate_text(
        sku=pack["sku"],
        market=pack["market"],
        content_type=content_type,
        text=current_text,
    )
    _ledger(
        st,
        "当前检查对象",
        f"{CONTENT_TYPE_LABELS[content_type]} · {pack['primary_platform']} · enhanced",
    )
    _render_quality(st, quality)
    st.markdown("### 事实来源")
    primary_claims = [
        claim
        for claim in pack["claims"]
        if claim["content_type"] == content_type
    ]
    for claim in primary_claims:
        _render_claim(
            st,
            title=claim["location"],
            text=claim["text"],
            claim=claim,
        )
    back, action = st.columns([1, 2])
    with back:
        if st.button("← 返回生成结果", use_container_width=True):
            _navigate(st, 3)
    with action:
        if st.button("进入版本与导出 →", type="primary", use_container_width=True):
            _navigate(st, 5)


def _render_page_export(st: Any) -> None:
    pack = _require_pack(st)
    if not pack:
        return
    _page_heading(
        st,
        "05 / version desk",
        "比较、修改、确认，再导出。",
        "Baseline 与增强版始终并列保留。人工编辑后重新检查；只有事实闸门未阻断并完成最终确认，下载按钮才会开放。",
    )
    content_type = pack["primary_content_type"]
    payload = pack["versions"][content_type]
    st.markdown(f"### {CONTENT_TYPE_LABELS[content_type]} · 版本对比")
    baseline_col, enhanced_col = st.columns(2)
    with baseline_col:
        st.caption("BASELINE · v01")
        st.code(payload["baseline"], language=None, wrap_lines=True)
    with enhanced_col:
        st.caption("LOCALIZEFLOW · v02")
        st.code(payload["enhanced"], language=None, wrap_lines=True)

    st.markdown("### 人工编辑最终版本")
    if not st.session_state.final_editor:
        st.session_state.final_editor = payload["enhanced"]
    edited_text = st.text_area(
        "最终内容",
        key="final_editor",
        height=340,
        label_visibility="collapsed",
    )
    live_quality = evaluate_text(
        sku=pack["sku"],
        market=pack["market"],
        content_type=content_type,
        text=edited_text,
    )
    status_text = (
        "当前版本存在事实阻断，修改后才能确认并导出。"
        if live_quality["export_gate"] == "blocked"
        else "自动预检未发现事实阻断，仍需人工最终确认。"
    )
    status_class = "fail" if live_quality["export_gate"] == "blocked" else "pass"
    st.markdown(
        f'<span class="tag {status_class}">{html.escape(status_text)}</span>',
        unsafe_allow_html=True,
    )
    st.write("")
    st.checkbox(
        "我已核对事实来源、目标市场、平台字段和最终文案",
        key="final_confirm_check",
    )
    confirm_disabled = (
        not st.session_state.final_confirm_check
        or live_quality["export_gate"] == "blocked"
    )
    if st.button(
        "确认最终版本",
        type="primary",
        disabled=confirm_disabled,
        use_container_width=True,
    ):
        final_pack = update_pack_with_manual_text(pack, edited_text)
        st.session_state.final_pack = final_pack
        st.session_state.confirmed = True
        st.success("最终版本已确认。CSV 与 JSON 导出已开放。")

    final_pack = st.session_state.final_pack
    if st.session_state.confirmed and final_pack:
        st.markdown("### 最终检查")
        _render_quality(st, final_pack["final_quality"])
        json_bytes = pack_as_json_bytes(final_pack)
        csv_bytes = pack_as_csv_bytes(final_pack)
        download_columns = st.columns(2)
        with download_columns[0]:
            st.download_button(
                "下载 JSON",
                data=json_bytes,
                file_name=f"{pack['run_id']}_final.json",
                mime="application/json",
                type="primary",
                use_container_width=True,
            )
        with download_columns[1]:
            st.download_button(
                "下载 CSV",
                data=csv_bytes,
                file_name=f"{pack['run_id']}_final.csv",
                mime="text/csv",
                use_container_width=True,
            )
    elif live_quality["export_gate"] == "blocked":
        st.error("导出被事实错误阻断。请按上一步的修改建议修正文案。")

    if st.button("← 返回质量检查", use_container_width=True):
        _navigate(st, 4)


def run_app() -> None:
    import streamlit as st

    st.set_page_config(
        page_title="LocalizeFlow · 本地化编辑台",
        page_icon="◫",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    _inject_css(st)
    _initialize_state(st)
    _render_sidebar(st)
    _render_stepper(st)

    pages = {
        1: _render_page_product,
        2: _render_page_task,
        3: _render_page_results,
        4: _render_page_quality,
        5: _render_page_export,
    }
    pages[st.session_state.step](st)


if __name__ == "__main__":
    if "--smoke-test" in sys.argv:
        run_smoke_test()
    else:
        run_app()
