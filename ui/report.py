import streamlit as st

from .components import (
    render_brand,
    render_metric,
    render_section_heading,
    render_entity_list,
    render_indirect_card,
    render_tests_card,
    render_git_history,
)

from .helpers import (
    get_field,
    risk_level,
    risk_class,
    count_indirect,
    get_test_counts,
    safe,
)


def render_report(
    question: str,
    query,
    report: dict,
    ai_answer: str,
):
    level = risk_level(report)
    level_cls = risk_class(level)

    target_file = (
        report.get("target_file")
        or get_field(query, "target_file", None)
        or "Unknown file"
    )

    if target_file:
        target_file = str(target_file).replace("\\", "/")

        if "/repository/" in target_file:
            target_file = target_file.split("/repository/", 1)[1]

    target_func = (
        report.get("target_func")
        or get_field(query, "target_func", None)
        or "File-level change"
    )

    direct = report.get("direct_callers", []) or []
    indirect = report.get("indirect_callers", {}) or {}
    callees = report.get("direct_callees", []) or []
    tests = report.get("related_tests", []) or []
    gaps = report.get("coverage_gaps", []) or []
    history = report.get("git_func_history", []) or []

    total, passed, failed, errors = get_test_counts(report)

    # ------------------------------------------------------------
    # Header
    # ------------------------------------------------------------

    render_brand()

    if st.button("←  New analysis"):
        st.session_state.pop("result", None)
        st.rerun()

    st.markdown(
        f"""
    <div class="results-top">
        <div class="target-kicker">Impact analysis</div>
        <div class="target-name">{safe(target_func)}</div>
        <div class="target-path">{safe(target_file)}</div>
        <div style="margin-top:14px;">
            <span class="risk-pill {safe(level_cls)}">
                ● &nbsp; {safe(level)} risk
            </span>
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # ------------------------------------------------------------
    # Metrics
    # ------------------------------------------------------------

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        render_metric(
            "Risk level",
            level,
            level_cls,
        )

    with c2:
        render_metric(
            "Direct callers",
            len(direct),
        )

    with c3:
        render_metric(
            "Indirect callers",
            count_indirect(report),
        )

    with c4:
        render_metric(
            "Related tests",
            len(tests),
        )

    # ------------------------------------------------------------
    # AI assessment
    # ------------------------------------------------------------

    render_section_heading(
        "AI impact assessment",
        "Reasoning grounded in the repository evidence above.",
    )

    with st.container(border=True):

        st.markdown(
            '<div class="ai-label">✦ Evidence-backed assessment</div>',
            unsafe_allow_html=True,
        )

        if ai_answer:
            st.markdown(ai_answer)
        else:
            st.warning("No AI assessment was generated.")

    # ------------------------------------------------------------
    # Repository evidence
    # ------------------------------------------------------------

    render_section_heading(
        "Repository evidence",
        "The concrete dependency, test and history signals behind the assessment.",
    )

    left, right = st.columns(2)

    # ------------------------------------------------------------
    # Left column
    # ------------------------------------------------------------

    with left:

        render_entity_list(
            "Direct callers",
            "Functions that directly call the target.",
            direct,
        )

        st.markdown(
            "<div style='height:12px'></div>",
            unsafe_allow_html=True,
        )

        render_entity_list(
            "Functions called by target",
            "Direct dependencies discovered inside the target.",
            callees,
        )

    # ------------------------------------------------------------
    # Right column
    # ------------------------------------------------------------

    with right:

        render_indirect_card(indirect)

        st.markdown(
            "<div style='height:12px'></div>",
            unsafe_allow_html=True,
        )

        render_tests_card(
            tests,
            report,
            total,
            passed,
            failed,
            errors,
        )

    # ------------------------------------------------------------
    # Coverage
    # ------------------------------------------------------------

    render_section_heading(
        "Coverage",
        "Gaps reported by the deterministic analyzer.",
    )

    if gaps:

        for gap in gaps:

            st.markdown(
                f"""
                <div class="gap-card">
                    ⚠ &nbsp; {safe(gap)}
                </div>
                """,
                unsafe_allow_html=True,
            )

            st.markdown(
                "<div style='height:7px'></div>",
                unsafe_allow_html=True,
            )

    else:

        st.markdown(
            """
            <div class="clean-card">
                ✓ &nbsp; No coverage gaps were detected for the analyzed target.
            </div>
            """,
            unsafe_allow_html=True,
        )

    # ------------------------------------------------------------
    # Git context
    # ------------------------------------------------------------

    render_section_heading(
        "Git context",
        "Recent function-level history available to the analyzer.",
    )

    with st.expander(
        "View Git history",
        expanded=bool(history),
    ):
        render_git_history(history)

    # ------------------------------------------------------------
    # Analysis details
    # ------------------------------------------------------------

    render_section_heading(
        "Analysis details",
        "Useful context for reproducing or reviewing this analysis.",
    )

    with st.expander("Original analysis question"):

        st.markdown(
            f"""
            <div class="question-box">
                {safe(question)}
            </div>
            """,
            unsafe_allow_html=True,
        )

    with st.expander("Raw risk summary"):

        st.code(
            report.get("risk_summary", "")
        )

    # ------------------------------------------------------------
    # Footer
    # ------------------------------------------------------------

    st.markdown(
        """
        <div class="bottom-note">
            Change Impact Investigator · Analyze before you change.
        </div>
        """,
        unsafe_allow_html=True,
    )