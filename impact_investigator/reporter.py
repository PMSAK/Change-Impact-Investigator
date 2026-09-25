"""
reporter.py
~~~~~~~~~~~
Assembles evidence from AST analysis, test finding, and Git history into
a structured impact report.

The report is returned as a plain dict (so callers can render it as they
please) and also as a formatted text string via `format_report()`.
"""

from pathlib import Path
from typing import Dict, List, Optional

from impact_investigator.ast_analysis import (
    FunctionInfo,
    build_call_graph,
    find_callers,
    find_callees,
    indirect_callers,
)
from impact_investigator.test_finder import (
    TestInfo,
    scan_tests,
    find_related_tests,
    detect_coverage_gaps,
    detect_value_path_gaps,
)
from impact_investigator.git_analysis import (
    CommitInfo,
    get_commits_for_file,
    commits_touching_function,
    get_repo_root,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _is_test_module(module_name: str) -> bool:
    """Return True if the module path looks like a test file."""
    parts = module_name.lower().split(".")
    return any(p.startswith("test") for p in parts)


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def build_report(
    target_path: str,
    target_func: Optional[str],
    project_root: str,
    test_dirs: Optional[List[str]] = None,
) -> dict:
    """
    Produce a full impact report for the given target.

    Parameters
    ----------
    target_path : str
        Path to the Python source file that was changed.
    target_func : str or None
        Name of the specific function that was changed, or None to report
        at the file level.
    project_root : str
        Root directory of the project (used for call-graph scanning).
    test_dirs : list[str] or None
        Directories to scan for tests. Defaults to ``[project_root]``.

    Returns
    -------
    dict with keys:
        target_file, target_func,
        direct_callers, indirect_callers,
        direct_callees,
        related_tests, coverage_gaps,
        git_file_history, git_func_history,
        risk_summary
    """
    if test_dirs is None:
        test_dirs = [project_root]

    # ── 1. Build call graph ──────────────────────────────────────────────
    graph = build_call_graph(project_root)

    # ── 2. Resolve the target function ───────────────────────────────────
    direct_callers_list: List[FunctionInfo] = []
    indirect_callers_map: Dict[int, List[FunctionInfo]] = {}
    direct_callees_list: List[FunctionInfo] = []

    if target_func:
        _raw_callers = find_callers(target_func, graph)
        # Exclude test functions from production callers — test files are
        # handled separately via the test_finder module.
        direct_callers_list = [
            c for c in _raw_callers
            if not _is_test_module(c.module)
        ]
        indirect_callers_map = indirect_callers(target_func, graph, max_depth=3)
        # Filter test functions from all indirect levels too
        indirect_callers_map = {
            depth: [c for c in infos if not _is_test_module(c.module)]
            for depth, infos in indirect_callers_map.items()
            if infos
        }
        indirect_callers_map = {k: v for k, v in indirect_callers_map.items() if v}
        direct_callees_list = find_callees(target_func, graph)

    # ── 3. Scan tests ────────────────────────────────────────────────────
    all_tests: List[TestInfo] = []
    all_test_files: List[str] = []
    for td in test_dirs:
        for ti in scan_tests(td):
            all_tests.append(ti)
            if ti.file_path not in all_test_files:
                all_test_files.append(ti.file_path)

    related_tests: List[TestInfo] = []
    coverage_gaps: List[str] = []

    if target_func:
        related_tests = find_related_tests(target_func, all_tests)
        coverage_gaps = detect_coverage_gaps(
            target_func, all_tests, direct_callers_list
        )
        # Value-path gap detection (e.g. untested 'vip' discount path)
        value_gaps = detect_value_path_gaps(
            target_func, target_path, all_test_files
        )
        coverage_gaps.extend(value_gaps)
    else:
        # File-level: find tests whose file imports from the target module.
        # Check both the module stem and any name imported from that module.
        target_stem = Path(target_path).stem
        # Build a set of all function/class names defined in the target file
        target_funcs_in_file = {
            info.name
            for key, info in graph.items()
            if Path(info.file_path).resolve() == Path(target_path).resolve()
        }
        seen_test_files: set = set()
        for ti in all_tests:
            if ti.file_path in seen_test_files:
                continue
            # Match if the test imports anything from the target module,
            # or if a defined function name appears in the test's references.
            if (
                any(target_stem in ref for ref in ti.references)
                or target_funcs_in_file & ti.references
            ):
                related_tests.append(ti)
                seen_test_files.add(ti.file_path)

    # ── 4. Git history ───────────────────────────────────────────────────
    repo_root = get_repo_root(target_path)
    git_file_history: List[CommitInfo] = []
    git_func_history: List[CommitInfo] = []

    if repo_root:
        git_file_history = get_commits_for_file(target_path, repo_root)
        if target_func:
            git_func_history = commits_touching_function(
                target_func, target_path, repo_root
            )

    # ── 5. Risk summary ──────────────────────────────────────────────────
    risk_summary = _compute_risk_summary(
        target_func=target_func,
        direct_callers=direct_callers_list,
        indirect_callers_map=indirect_callers_map,
        related_tests=related_tests,
        coverage_gaps=coverage_gaps,
        git_func_history=git_func_history,
    )

    return {
        "target_file": str(Path(target_path)),
        "target_func": target_func,
        "direct_callers": direct_callers_list,
        "indirect_callers": indirect_callers_map,
        "direct_callees": direct_callees_list,
        "related_tests": related_tests,
        "coverage_gaps": coverage_gaps,
        "git_file_history": git_file_history,
        "git_func_history": git_func_history,
        "risk_summary": risk_summary,
    }


def _compute_risk_summary(
    target_func,
    direct_callers,
    indirect_callers_map,
    related_tests,
    coverage_gaps,
    git_func_history,
) -> str:
    """Produce a short evidence-based risk narrative."""
    lines = []

    total_indirect = sum(len(v) for v in indirect_callers_map.values())

    if target_func:
        n_callers = len(direct_callers)
        n_tests = len(related_tests)
        n_gaps = len(coverage_gaps)
        n_commits = len(git_func_history)

        lines.append(f"Function '{target_func}' was targeted.")

        if n_callers == 0:
            lines.append("  - No other functions call this function directly -- limited blast radius.")
        else:
            names = ", ".join(f"{c.module}.{c.name}" for c in direct_callers)
            lines.append(f"  - {n_callers} direct caller(s): {names}.")

        if total_indirect > 0:
            lines.append(f"  - {total_indirect} indirect caller(s) reachable within 3 hops.")

        if n_tests == 0:
            lines.append("  - [WARN] No tests directly cover this function -- change is unverified.")
        else:
            lines.append(f"  - {n_tests} test(s) cover this function.")

        if n_gaps > 0:
            lines.append(f"  - [WARN] {n_gaps} coverage gap(s) detected (see Coverage Gaps section).")

        if n_commits == 0:
            lines.append("  - No recent Git history found for this function.")
        else:
            lines.append(
                f"  - This function was touched in {n_commits} commit(s) --"
                " review Git history for context."
            )

        # Risk level heuristic
        risk_score = n_callers + total_indirect + n_gaps * 2 - n_tests
        if risk_score <= 0:
            level = "LOW"
        elif risk_score <= 3:
            level = "MEDIUM"
        else:
            level = "HIGH"
        lines.append(f"\n  Risk level: {level}")
    else:
        lines.append("File-level analysis (no specific function targeted).")
        lines.append(f"  - {len(related_tests)} related test(s) found.")
        lines.append(f"  - {len(git_func_history)} relevant commits in history.")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Text formatter
# ---------------------------------------------------------------------------

def format_report(report: dict) -> str:
    """
    Convert a report dict into a human-readable text report.
    """
    sep = "=" * 60
    thin = "-" * 60
    lines = [sep, "  CHANGE IMPACT REPORT", sep]

    lines.append(f"Target file : {report['target_file']}")
    if report["target_func"]:
        lines.append(f"Target func : {report['target_func']}")
    lines.append("")

    # Direct callees
    callees = report["direct_callees"]
    lines.append(f"[Functions called BY target] ({len(callees)})")
    if callees:
        for c in callees:
            lines.append(f"  -> {c.module}.{c.name}  (line {c.lineno}  {c.file_path})")
    else:
        lines.append("  (none detected)")
    lines.append("")

    # Direct callers
    callers = report["direct_callers"]
    lines.append(f"[Direct callers of target] ({len(callers)})")
    if callers:
        for c in callers:
            lines.append(f"  <- {c.module}.{c.name}  (line {c.lineno}  {c.file_path})")
    else:
        lines.append("  (none detected)")
    lines.append("")

    # Indirect callers
    indirect = report["indirect_callers"]
    total_indirect = sum(len(v) for v in indirect.values())
    lines.append(f"[Indirect callers] ({total_indirect} across {len(indirect)} depth level(s))")
    for depth, infos in sorted(indirect.items()):
        for c in infos:
            lines.append(f"  depth {depth}  <- {c.module}.{c.name}  (line {c.lineno})")
    if not indirect:
        lines.append("  (none detected)")
    lines.append("")

    # Related tests
    tests = report["related_tests"]
    lines.append(f"[Related tests] ({len(tests)})")
    if tests:
        for t in tests:
            lines.append(f"  [PASS] {t.pytest_id}")
    else:
        lines.append("  [WARN] No related tests found!")
    lines.append("")

    # Coverage gaps
    gaps = report["coverage_gaps"]
    lines.append(f"[Coverage gaps] ({len(gaps)})")
    if gaps:
        for g in gaps:
            lines.append(f"  [WARN] {g}")
    else:
        lines.append("  (none detected)")
    lines.append("")

    # Git file history
    file_history = report["git_file_history"]
    lines.append(f"[Git history — file] ({len(file_history)} commits)")
    for ci in file_history:
        lines.append(f"  {ci.one_line()}")
    if not file_history:
        lines.append("  (no history found — not a git repo, or file not committed)")
    lines.append("")

    # Git function history
    func_history = report["git_func_history"]
    if report["target_func"]:
        lines.append(f"[Git history — function '{report['target_func']}'] ({len(func_history)} commits)")
        for ci in func_history:
            lines.append(f"  {ci.one_line()}")
        if not func_history:
            lines.append("  (function name not found in any diff)")
        lines.append("")

    # Risk summary
    lines.append(thin)
    lines.append("[Risk summary]")
    lines.append(report["risk_summary"])
    lines.append(sep)

    return "\n".join(lines)
