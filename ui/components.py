import streamlit as st

from .helpers import get_field, safe

def render_brand():
    st.markdown(
        """
        <div class="brand-row">
            <div class="brand-mark">◈</div>
            <div>
                <div class="brand-name">Change Impact Investigator</div>
                <div class="brand-mini">Evidence-backed change analysis</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_section_heading(title: str, subtitle: str = ""):
    st.markdown(
        f"""
        <div class="section-heading">
            <div class="section-dot"></div>
            <div>
                <h2>{safe(title)}</h2>
                {f'<p>{safe(subtitle)}</p>' if subtitle else ''}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_metric(label: str, value, tone: str = ""):
    st.markdown(
        f"""
        <div class="metric">
            <div class="metric-label">{safe(label)}</div>
            <div class="metric-value {safe(tone)}">{safe(value)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_entity_card(name, module="", file_path="", line=""):
    meta = []
    if module:
        meta.append(str(module))
    if file_path:
        meta.append(f"📄 {file_path}")
    if line:
        meta.append(f"line {line}")

    st.markdown(
        f"""
        <div class="entity">
            <div class="entity-name">{safe(name)}</div>
            {f'<div class="entity-meta">{" · ".join(safe(x) for x in meta)}</div>' if meta else ''}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_entity_list(title, subtitle, callers):
    parts = [
        '<div class="evidence-card">',
        f'<div class="evidence-title">{safe(title)}</div>',
        f'<div class="evidence-subtitle">{safe(subtitle)}</div>',
    ]

    if not callers:
        parts.append('<div class="empty-state">None detected.</div>')
    else:
        for caller in callers:
            name = get_field(caller, "name", "unknown")
            module = get_field(caller, "module", "")
            file_path = get_field(caller, "file_path", "")
            line = get_field(caller, "line", "")
            meta = []
            if module:
                meta.append(str(module))
            if file_path:
                meta.append(f"📄 {file_path}")
            if line:
                meta.append(f"line {line}")
            meta_html = (
                f'<div class="entity-meta">{" · ".join(safe(x) for x in meta)}</div>'
                if meta else ""
            )
            parts.append(
                f'<div class="entity"><div class="entity-name">{safe(name)}</div>{meta_html}</div>'
            )

    parts.append('</div>')
    st.markdown("".join(parts), unsafe_allow_html=True)

def render_indirect_card(indirect):
    parts = [
        '<div class="evidence-card">',
        '<div class="evidence-title">Indirect callers</div>',
        '<div class="evidence-subtitle">Reachable through the dependency graph</div>',
    ]

    if not indirect:
        parts.append('<div class="empty-state">None detected.</div>')
    else:
        for depth, callers in sorted(indirect.items(), key=lambda item: int(item[0])):
            parts.append(
                f'<div class="evidence-subtitle" style="margin-top:10px;margin-bottom:2px;">DEPTH {safe(depth)}</div>'
            )
            for caller in callers:
                name = get_field(caller, "name", "unknown")
                module = get_field(caller, "module", "")
                line = get_field(caller, "line", "?")
                display_name = f"{module}.{name}" if module else name
                parts.append(
                    f'<div class="entity"><div class="entity-name">{safe(display_name)}</div>'
                    f'<div class="entity-meta">line {safe(line)}</div></div>'
                )

    parts.append('</div>')
    st.markdown("".join(parts), unsafe_allow_html=True)

def render_tests_card(tests, report, total, passed, failed, errors):
    failed_ids = {
        str(x).replace("\\", "/")
        for x in (report.get("failed_test_ids") or [])
    }

    parts = [
        '<div class="evidence-card">',
        '<div class="evidence-title">Tests</div>',
        '<div class="evidence-subtitle">Test evidence associated with the change</div>',
        '<div class="test-summary">',
    ]

    stats = [
        (total, "total", ""),
        (passed, "passed", "test-pass"),
        (failed, "failed", "test-fail"),
        (errors, "errors", "test-fail"),
    ]

    for value, label, cls in stats:
        parts.append(
            f'<div class="test-stat"><div class="test-stat-value {cls}">{safe(value)}</div>'
            f'<div class="test-stat-label">{safe(label)}</div></div>'
        )

    parts.append('</div>')

    if not tests:
        parts.append('<div class="empty-state">No related tests found.</div>')
    else:
        for test in tests:
            test_id = get_field(test, "pytest_id", get_field(test, "name", "unknown test"))
            normalized = str(test_id).replace("\\", "/")
            is_failed = normalized in failed_ids
            icon = "✕" if is_failed else "✓"
            cls = "test-fail" if is_failed else "test-pass"
            parts.append(
                f'<div class="entity"><div class="entity-name {cls}">{icon} &nbsp; {safe(test_id)}</div></div>'
            )

    parts.append('</div>')
    st.markdown("".join(parts), unsafe_allow_html=True)

def render_git_history(history):
    if not history:
        st.caption("No function-level Git history found.")
        return

    for commit in history:
        sha = get_field(commit, "sha", "")
        date = get_field(commit, "date", "")
        author = get_field(commit, "author", "")
        message = get_field(commit, "message", "")

        st.markdown(
            f"""
            <div class="timeline-item">
                <div class="timeline-dot"></div>
                <div class="timeline-meta">{safe(date)} · {safe(author)} · {safe(sha)}</div>
                <div class="timeline-message">{safe(message)}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )