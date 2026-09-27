import os

import streamlit as st

from impact_investigator.engine import analyze_question
from .components import render_brand
from .helpers import safe


def render_landing():
    render_brand()

    st.markdown(
        """
        <div class="hero">
            <div class="eyebrow">✦ Repository intelligence</div>
            <h1>Know the blast radius<br><span>before you change code.</span></h1>
            <div class="hero-copy">
                Analyze callers, tests, coverage and Git context first — Let AI
                turn the evidence into a concise impact assessment.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="analysis-card">',
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="card-heading">
            <div class="card-heading-title">Start an impact analysis</div>
            <div class="card-heading-meta">
                GitHub repository · static analysis · AI reasoning
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.form("analysis_form", clear_on_submit=False):

        source = st.text_input(
            "GitHub repository",
            placeholder="https://github.com/username/repository",
        )

        question = st.text_area(
            "What are you changing?",
            placeholder=(
                "Something like - What happens if I change calculate_subtotal "
                "in app/pricing.py?"
            ),
            height=105,
        )

        test_dirs_text = st.text_input(
            "Test directories",
            value="tests, demo_project/tests",
        )

        submitted = st.form_submit_button(
            "Analyze Impact  →",
            use_container_width=True,
        )

    st.markdown(
        """
        <div class="hint-row">
            <div class="hint">caller graph</div>
            <div class="hint">test coverage</div>
            <div class="hint">git history</div>
            <div class="hint">AI assessment</div>
        </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ------------------------------------------------------------
    # Feature cards
    # ------------------------------------------------------------

    feature_cols = st.columns(3)

    features = [
        (
            "⌁",
            "Dependency mapping",
            "Trace direct and indirect callers around the target change.",
        ),
        (
            "✓",
            "Test evidence",
            "Find related tests and inspect their current results.",
        ),
        (
            "✦",
            "Evidence-backed AI",
            "Summarize impact without asking the model to invent dependencies.",
        ),
    ]

    for col, (icon, title, copy) in zip(feature_cols, features):
        with col:
            st.markdown(
                f"""
                <div class="feature">
                    <div class="feature-icon">{safe(icon)}</div>
                    <div class="feature-title">{safe(title)}</div>
                    <div class="feature-copy">{safe(copy)}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown(
        """
        <div class="footer-note">
            Analyze before you change · built for developers who want evidence, not guesses.
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ------------------------------------------------------------
    # Form submission
    # ------------------------------------------------------------

    if not submitted:
        return

    # Validate repository
    if not source.strip():
        st.error("Enter a GitHub repository URL.")
        return

    # Validate question
    if not question.strip():
        st.error("Enter a question describing the change.")
        return

    # Check API key
    if not os.getenv("OPENAI_API_KEY"):
        st.error(
            "OPENAI_API_KEY is not loaded. Make sure your .env file contains "
            "OPENAI_API_KEY=your_key_here"
        )
        return

    # Parse test directories
    test_dirs = [
        item.strip()
        for item in test_dirs_text.split(",")
        if item.strip()
    ]

    # ------------------------------------------------------------
    # Run analysis
    # ------------------------------------------------------------

    try:
        with st.spinner("Analyzing repository impact…"):
            query, report, ai_answer, repository_handle = analyze_question(
                source=source.strip(),
                question=question.strip(),
                test_dirs=test_dirs or None,
            )

            if repository_handle is not None:
                repository_handle.cleanup()

        st.session_state.result = {
            "question": question.strip(),
            "query": query,
            "report": report,
            "ai_answer": ai_answer,
        }

        st.rerun()

    except ValueError as exc:
        st.error(f"❌ {exc}")

    except FileNotFoundError as exc:
        st.error(f"❌ {exc}")

    except Exception as exc:
        st.error(
            f"❌ Analysis failed: {type(exc).__name__}: {exc}"
        )
