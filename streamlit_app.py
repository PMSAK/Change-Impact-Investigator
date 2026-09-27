import os

import streamlit as st
from dotenv import load_dotenv

from impact_investigator.engine import analyze_question


# ---------------------------------------------------------------------------
# Environment
# ---------------------------------------------------------------------------

# Load variables from .env
load_dotenv()


# ---------------------------------------------------------------------------
# Page setup
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="Change Impact Investigator",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
        .stApp {
            background:
                radial-gradient(circle at 78% 8%, rgba(112, 76, 255, 0.10), transparent 28%),
                radial-gradient(circle at 20% 0%, rgba(76, 105, 255, 0.07), transparent 24%),
                #08090d;
        }

        .block-container {
            max-width: 1180px;
            padding-top: 2.2rem;
            padding-bottom: 4rem;
        }

        .brand {
            display: flex;
            align-items: center;
            gap: 14px;
            margin-bottom: 4px;
        }

        .brand-icon {
            width: 42px;
            height: 42px;
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            background: linear-gradient(135deg, #6d5dfc, #7c4dff);
            color: white;
            font-size: 22px;
            font-weight: 800;
            box-shadow: 0 8px 30px rgba(109, 93, 252, .25);
        }

        .brand-title {
            font-size: 27px;
            font-weight: 750;
            color: #f7f7fb;
            letter-spacing: -0.7px;
        }

        .subtitle {
            color: #9295a3;
            margin: 0 0 32px 56px;
            font-size: 15px;
        }

        .section-title {
            color: #f2f2f7;
            font-size: 20px;
            font-weight: 700;
            margin: 12px 0 18px 0;
        }

        .result-header {
            padding: 24px 0 18px 0;
        }

        .target-function {
            color: #f7f7fb;
            font-size: 30px;
            font-weight: 750;
            letter-spacing: -0.8px;
            margin-bottom: 4px;
        }

        .target-file {
            color: #8f93a3;
            font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
            font-size: 14px;
        }

        .metric-card {
            background: rgba(20, 21, 29, .78);
            border: 1px solid rgba(255,255,255,.08);
            border-radius: 15px;
            padding: 18px 20px;
            min-height: 108px;
        }

        .metric-label {
            color: #8e92a0;
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: .7px;
            margin-bottom: 8px;
        }

        .metric-value {
            color: #f6f6fa;
            font-size: 28px;
            font-weight: 750;
        }

        .risk-low {
            color: #63d995;
        }

        .risk-medium {
            color: #f4c95d;
        }

        .risk-high {
            color: #ff6f78;
        }

        .evidence-card {
            background: rgba(16, 17, 23, .85);
            border: 1px solid rgba(255,255,255,.075);
            border-radius: 16px;
            padding: 22px 24px;
            margin-top: 14px;
        }

        .evidence-card h3 {
            margin: 0 0 14px 0;
            color: #f5f5f8;
            font-size: 18px;
        }

        .item {
            padding: 12px 0;
            border-bottom: 1px solid rgba(255,255,255,.06);
        }

        .item:last-child {
            border-bottom: none;
        }

        .item-name {
            color: #e8e8ee;
            font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
            font-size: 14px;
        }

        .item-meta {
            color: #858997;
            font-size: 12px;
            margin-top: 4px;
        }

        .pass {
            color: #63d995;
            font-weight: 700;
        }

        .fail {
            color: #ff6f78;
            font-weight: 700;
        }

        .warn {
            color: #f4c95d;
            font-weight: 700;
        }

        div[data-testid="stTextInput"] input,
        div[data-testid="stTextArea"] textarea {
            background: #252631 !important;
            border: 1px solid rgba(255,255,255,.04) !important;
            color: #eeeeF4 !important;
            border-radius: 9px !important;
        }

        div[data-testid="stTextInput"] input:focus,
        div[data-testid="stTextArea"] textarea:focus {
            border-color: rgba(123, 92, 255, .75) !important;
            box-shadow: 0 0 0 1px rgba(123, 92, 255, .2) !important;
        }

        div.stButton > button {
            background: linear-gradient(135deg, #6657ee, #8246f4);
            color: white;
            border: 0;
            border-radius: 9px;
            min-height: 44px;
            font-weight: 650;
        }

        div.stButton > button:hover {
            background: linear-gradient(135deg, #7465f5, #925af6);
            color: white;
        }

        .small-note {
            color: #777b89;
            font-size: 12px;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def get_field(obj, field, default=None):
    """
    Safely retrieve a field from either:
    - a dictionary
    - a dataclass/object
    """
    if obj is None:
        return default

    if isinstance(obj, dict):
        return obj.get(field, default)

    return getattr(obj, field, default)


def risk_level(report: dict) -> str:
    text = str(report.get("risk_summary", "")).upper()

    if "RISK LEVEL: HIGH" in text:
        return "HIGH"

    if "RISK LEVEL: MEDIUM" in text:
        return "MEDIUM"

    if "RISK LEVEL: LOW" in text:
        return "LOW"

    return "UNKNOWN"


def risk_class(level: str) -> str:
    return {
        "LOW": "risk-low",
        "MEDIUM": "risk-medium",
        "HIGH": "risk-high",
    }.get(level, "")


def count_indirect(report: dict) -> int:
    indirect = report.get("indirect_callers", {})

    if not indirect:
        return 0

    total = 0

    for callers in indirect.values():
        if callers:
            total += len(callers)

    return total


def get_test_counts(report: dict):
    results = report.get("test_results") or {}

    total = int(
        get_field(
            results,
            "total",
            len(report.get("related_tests", [])),
        )
        or 0
    )

    passed = int(get_field(results, "passed", 0) or 0)
    failed = int(get_field(results, "failed", 0) or 0)
    errors = int(get_field(results, "errors", 0) or 0)

    return total, passed, failed, errors


def display_caller_list(title, callers, icon):
    st.subheader(f"{icon} {title}")

    if not callers:
        st.caption("None detected.")
        return

    for caller in callers:

        name = get_field(caller, "name", "unknown")
        file_path = get_field(caller, "file_path", "")
        line = get_field(caller, "line", "")
        module = get_field(caller, "module", "")

        with st.container(border=True):

            st.markdown(f"**{name}**")

            if module:
                st.caption(module)

            if file_path:
                st.caption(f"📄 `{file_path}`")

            if line:
                st.caption(f"Line {line}")


def display_indirect_callers(indirect):
    """
    Display indirect callers while supporting both dictionaries
    and FunctionInfo-style objects.
    """

    if not indirect:
        st.caption("None detected.")
        return

    for depth, callers in sorted(
        indirect.items(),
        key=lambda item: int(item[0]),
    ):

        st.caption(f"Depth {depth}")

        for caller in callers:

            module = get_field(caller, "module", "")
            name = get_field(caller, "name", "unknown")
            line = get_field(caller, "line", "?")

            if module:
                display_name = f"{module}.{name}"
            else:
                display_name = name

            st.markdown(
                f"- `{display_name}` — line {line}"
            )


def display_tests(tests, report):
    if not tests:
        st.warning("No related tests found.")
        return

    failed_ids = {
        str(x).replace("\\", "/")
        for x in (report.get("failed_test_ids") or [])
    }

    for test in tests:

        test_id = get_field(
            test,
            "pytest_id",
            get_field(test, "name", "unknown test"),
        )

        normalized = str(test_id).replace("\\", "/")

        if normalized in failed_ids:
            st.markdown(f"🔴 `{test_id}`")
        else:
            st.markdown(f"🟢 `{test_id}`")


def display_git_history(history):
    if not history:
        st.caption("No function-level Git history found.")
        return

    for commit in history:

        sha = get_field(commit, "sha", "")
        date = get_field(commit, "date", "")
        author = get_field(commit, "author", "")
        message = get_field(commit, "message", "")

        st.markdown(
            f"**`{sha}`** — {date} — {author}"
        )

        if message:
            st.caption(message)


# ---------------------------------------------------------------------------
# Report renderer
# ---------------------------------------------------------------------------

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

    # -----------------------------------------------------------------------
    # Header
    # -----------------------------------------------------------------------

    st.markdown(
        """
        <div class="brand">
            <div class="brand-icon">◈</div>
            <div class="brand-title">Change Impact Investigator</div>
        </div>

        <div class="subtitle">
            Evidence-backed analysis of your proposed code change.
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.button("← New analysis"):
        st.session_state.pop("result", None)
        st.rerun()

    st.markdown(
        '<div class="result-header">',
        unsafe_allow_html=True,
    )

    st.markdown(
        f'<div class="target-function">{target_func}</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        f'<div class="target-file">{target_file}</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '</div>',
        unsafe_allow_html=True,
    )

    # -----------------------------------------------------------------------
    # Metrics
    # -----------------------------------------------------------------------

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">Risk level</div>
                <div class="metric-value {level_cls}">
                    {level}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with c2:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">Direct callers</div>
                <div class="metric-value">
                    {len(direct)}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with c3:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">Indirect callers</div>
                <div class="metric-value">
                    {count_indirect(report)}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with c4:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">Related tests</div>
                <div class="metric-value">
                    {len(tests)}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # -----------------------------------------------------------------------
    # AI assessment
    # -----------------------------------------------------------------------

    st.markdown("## AI impact assessment")

    with st.container(border=True):
        if ai_answer:
            st.markdown(ai_answer)
        else:
            st.warning("No AI assessment was generated.")

    # -----------------------------------------------------------------------
    # Repository evidence
    # -----------------------------------------------------------------------

    st.markdown("## Repository evidence")

    left, right = st.columns(2)

    # -----------------------------------------------------------------------
    # LEFT COLUMN
    # -----------------------------------------------------------------------

    with left:

        with st.container(border=True):
            display_caller_list(
                "Direct callers",
                direct,
                "←",
            )

        with st.container(border=True):
            display_caller_list(
                "Functions called by target",
                callees,
                "→",
            )

    # -----------------------------------------------------------------------
    # RIGHT COLUMN
    # -----------------------------------------------------------------------

    with right:

        with st.container(border=True):

            st.markdown("### Indirect callers")

            display_indirect_callers(indirect)

        with st.container(border=True):

            st.markdown("### Tests")

            t1, t2, t3, t4 = st.columns(4)

            t1.metric("Total", total)
            t2.metric("Passed", passed)
            t3.metric("Failed", failed)
            t4.metric("Errors", errors)

            display_tests(tests, report)

    # -----------------------------------------------------------------------
    # Coverage
    # -----------------------------------------------------------------------

    if gaps:

        with st.container(border=True):

            st.markdown("### Coverage gaps")

            for gap in gaps:
                st.warning(str(gap))

    else:

        st.success("No coverage gaps detected.")

    # -----------------------------------------------------------------------
    # Git history
    # -----------------------------------------------------------------------

    with st.expander("Git history"):
        display_git_history(history)

    # -----------------------------------------------------------------------
    # Analysis question
    # -----------------------------------------------------------------------

    with st.expander("Analysis question"):
        st.code(question)

    # -----------------------------------------------------------------------
    # Raw risk summary
    # -----------------------------------------------------------------------

    with st.expander("Raw risk summary"):
        st.code(report.get("risk_summary", ""))


# ---------------------------------------------------------------------------
# Main screen
# ---------------------------------------------------------------------------

if "result" not in st.session_state:

    st.markdown(
        """
        <div class="brand">
            <div class="brand-icon">◈</div>
            <div class="brand-title">
                Change Impact Investigator
            </div>
        </div>

        <div class="subtitle">
            Understand the blast radius of a code change before you make it.
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="section-title">Analyze a repository</div>',
        unsafe_allow_html=True,
    )

    source = st.text_input(
        "GitHub repository",
        placeholder="https://github.com/username/repository",
    )

    question = st.text_area(
        "What are you changing?",
        placeholder=(
            "What happens if I change calculate_subtotal "
            "in app/pricing.py?"
        ),
        height=100,
    )

    test_dirs_text = st.text_input(
        "Test directories (optional)",
        value="tests, demo_project/tests",
    )

    _, button_col = st.columns([3, 1])

    with button_col:

        analyze_clicked = st.button(
            "Analyze Impact →",
            use_container_width=True,
        )

    st.markdown(
        """
        <div class="small-note">
            Change Impact Investigator · Analyze before you change.
        </div>
        """,
        unsafe_allow_html=True,
    )

    # -----------------------------------------------------------------------
    # Analyze
    # -----------------------------------------------------------------------

    if analyze_clicked:

        if not source.strip():
            st.error("Enter a GitHub repository URL.")
            st.stop()

        if not question.strip():
            st.error("Enter a question describing the change.")
            st.stop()

        # Check API key before doing expensive repository analysis
        if not os.getenv("OPENAI_API_KEY"):
            st.error(
                "OPENAI_API_KEY is not loaded. "
                "Make sure your .env file contains "
                "OPENAI_API_KEY=your_key_here"
            )
            st.stop()

        test_dirs = [
            item.strip()
            for item in test_dirs_text.split(",")
            if item.strip()
        ]

        try:

            with st.spinner(
                "Cloning repository and analyzing impact..."
            ):

                (
                    query,
                    report,
                    ai_answer,
                    repository_handle,
                ) = analyze_question(
                    source=source.strip(),
                    question=question.strip(),
                    test_dirs=test_dirs or None,
                )

                # The repository may be a temporary clone.
                # Analysis is complete, so it is safe to clean it up.
                if repository_handle is not None:
                    repository_handle.cleanup()

            st.session_state.result = {
                "question": question.strip(),
                "query": query,
                "report": report,
                "ai_answer": ai_answer,
            }

            st.rerun()

        except Exception as exc:

            st.error(
                f"Analysis failed: {type(exc).__name__}: {exc}"
            )

else:

    result = st.session_state.result

    render_report(
        question=result["question"],
        query=result["query"],
        report=result["report"],
        ai_answer=result["ai_answer"],
    )