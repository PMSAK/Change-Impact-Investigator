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

from impact_investigator.test_runner import run_tests

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
    get_working_tree_diff,
    get_changed_functions,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _is_test_module(module_name: str) -> bool:
    """Return True if the module path looks like a test file."""
    parts = module_name.lower().split(".")
    return any(p.startswith("test") for p in parts)


def _normalize_test_id(test_id: str) -> str:
    """
    Normalize pytest node IDs so Windows and Unix path separators
    compare consistently.
    """
    return str(test_id).replace("\\", "/")


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
    """

    if test_dirs is None:
        test_dirs = [project_root]

    # ── 1. Build call graph ──────────────────────────────────────────────
    graph = build_call_graph(project_root)

    # ── 2. Validate the target function ──────────────────────────────────
    #
    # An unknown function must NOT be treated as a valid function with
    # zero callers/tests. That would produce a misleading impact report.
    #
    # Validate against BOTH:
    #   1. function name
    #   2. exact target file
    #
    # This prevents a function with the same name in another file from
    # being accepted accidentally.
    if target_func:
        target_path_resolved = Path(target_path).resolve()

        target_exists = any(
            info.name == target_func
            and Path(info.file_path).resolve() == target_path_resolved
            for info in graph.values()
        )

        if not target_exists:
            raise ValueError(
                f"Function '{target_func}' does not exist in the selected file."
            )

    # ── 2. Resolve the target function ───────────────────────────────────
    direct_callers_list: List[FunctionInfo] = []
    indirect_callers_map: Dict[int, List[FunctionInfo]] = {}
    direct_callees_list: List[FunctionInfo] = []

    if target_func:
        _raw_callers = find_callers(target_func, graph)

        # Exclude test functions from production callers.
        direct_callers_list = [
            c
            for c in _raw_callers
            if not _is_test_module(c.module)
        ]

        indirect_callers_map = indirect_callers(
            target_func,
            graph,
            max_depth=3,
        )

        # Filter test functions from indirect callers.
        indirect_callers_map = {
            depth: [
                c
                for c in infos
                if not _is_test_module(c.module)
            ]
            for depth, infos in indirect_callers_map.items()
        }

        # A direct caller should not also appear as an indirect caller.
        direct_caller_keys = {
            (c.module, c.name, c.file_path, c.lineno)
            for c in direct_callers_list
        }

        for depth in list(indirect_callers_map):
            indirect_callers_map[depth] = [
                c
                for c in indirect_callers_map[depth]
                if (
                    c.module,
                    c.name,
                    c.file_path,
                    c.lineno,
                ) not in direct_caller_keys
            ]

        # Remove empty depth levels.
        indirect_callers_map = {
            depth: callers
            for depth, callers in indirect_callers_map.items()
            if callers
        }

        direct_callees_list = find_callees(
            target_func,
            graph,
        )

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
    test_results = {}

    if target_func:
        related_tests = find_related_tests(
            target_func,
            all_tests,
        )

        if related_tests:
            test_node_ids = [
                test.pytest_id
                for test in related_tests
            ]

            test_results = run_tests(
                project_root,
                test_node_ids,
            )

        coverage_gaps = detect_coverage_gaps(
            target_func,
            all_tests,
            direct_callers_list,
        )

        # Value-path gap detection.
        value_gaps = detect_value_path_gaps(
            target_func,
            target_path,
            all_test_files,
        )

        coverage_gaps.extend(value_gaps)

    else:
        # File-level analysis.
        target_stem = Path(target_path).stem

        target_funcs_in_file = {
            info.name
            for key, info in graph.items()
            if Path(info.file_path).resolve()
            == Path(target_path).resolve()
        }

        seen_test_files: set = set()

        for ti in all_tests:
            if ti.file_path in seen_test_files:
                continue

            if (
                any(
                    target_stem in ref
                    for ref in ti.references
                )
                or target_funcs_in_file & ti.references
            ):
                related_tests.append(ti)
                seen_test_files.add(ti.file_path)

    # ── 4. Git history ───────────────────────────────────────────────────
    repo_root = get_repo_root(target_path)

    git_file_history: List[CommitInfo] = []
    git_func_history: List[CommitInfo] = []

    if repo_root:
        git_file_history = get_commits_for_file(
            target_path,
            repo_root,
        )

        if target_func:
            git_func_history = commits_touching_function(
                target_func,
                target_path,
                repo_root,
            )

    # ── 5. Risk summary ──────────────────────────────────────────────────
    risk_summary = _compute_risk_summary(
        target_func=target_func,
        direct_callers=direct_callers_list,
        indirect_callers_map=indirect_callers_map,
        related_tests=related_tests,
        coverage_gaps=coverage_gaps,
        git_func_history=git_func_history,
        test_results=test_results,
    )

    return {
        "target_file": str(Path(target_path)),
        "target_func": target_func,
        "direct_callers": direct_callers_list,
        "indirect_callers": indirect_callers_map,
        "direct_callees": direct_callees_list,
        "related_tests": related_tests,
        "test_results": test_results,
        "coverage_gaps": coverage_gaps,
        "git_file_history": git_file_history,
        "git_func_history": git_func_history,
        "risk_summary": risk_summary,
    }


# ---------------------------------------------------------------------------
# Risk summary
# ---------------------------------------------------------------------------

def _compute_risk_summary(
    target_func,
    direct_callers,
    indirect_callers_map,
    related_tests,
    coverage_gaps,
    git_func_history,
    test_results=None,
) -> str:
    """Produce a short evidence-based risk narrative."""

    lines = []

    total_indirect = sum(
        len(v)
        for v in indirect_callers_map.values()
    )

    if target_func:
        n_callers = len(direct_callers)
        n_tests = len(related_tests)
        n_gaps = len(coverage_gaps)
        n_commits = len(git_func_history)

        failed_tests = (
            len(test_results.get("failed_tests", []))
            if test_results
            else 0
        )

        # Determine how many RELATED tests are actually failing.
        failed_related = 0

        if test_results:
            failed_test_ids = {
                _normalize_test_id(test_id)
                for test_id in test_results.get(
                    "failed_tests",
                    [],
                )
            }

            for test in related_tests:
                test_id = _normalize_test_id(
                    test.pytest_id
                )

                if test_id in failed_test_ids:
                    failed_related += 1

        lines.append(
            f"Function '{target_func}' was targeted."
        )

        # Direct callers
        if n_callers == 0:
            lines.append(
                "  - No other functions call this function directly "
                "-- limited blast radius."
            )
        else:
            names = ", ".join(
                f"{c.module}.{c.name}"
                for c in direct_callers
            )

            lines.append(
                f"  - {n_callers} direct caller(s): {names}."
            )

        # Indirect callers
        if total_indirect > 0:
            lines.append(
                f"  - {total_indirect} indirect caller(s) "
                f"reachable within 3 hops."
            )

        # Related tests
        if n_tests == 0:
            lines.append(
                "  - [WARN] No tests directly cover this function "
                "-- change is unverified."
            )
        else:
            lines.append(
                f"  - {n_tests} test(s) cover this function."
            )

        # Test failures
        if test_results:
            if failed_tests > 0:
                lines.append(
                    f"  - [WARN] {failed_tests} test(s) "
                    "are currently failing."
                )
            else:
                lines.append(
                    "  - All related tests are currently passing."
                )

            if failed_related > 0:
                lines.append(
                    f"  - [WARN] {failed_related}/{n_tests} "
                    "related test(s) are currently failing."
                )

        # Coverage gaps
        if n_gaps > 0:
            lines.append(
                f"  - [WARN] {n_gaps} coverage gap(s) detected "
                "(see Coverage Gaps section)."
            )

        # Git history
        if n_commits == 0:
            lines.append(
                "  - No recent Git history found for this function."
            )
        else:
            lines.append(
                f"  - This function was touched in {n_commits} "
                "commit(s) -- review Git history for context."
            )

        # Risk heuristic
        risk_score = (
            n_callers
            + total_indirect
            + (n_gaps * 2)
            + (failed_tests * 2)
        )

        if n_tests == 0:
            risk_score += 2

        if risk_score <= 2:
            level = "LOW"
        elif risk_score <= 5:
            level = "MEDIUM"
        else:
            level = "HIGH"

        lines.append(
            f"\n  Risk level: {level}"
        )

    else:
        lines.append(
            "File-level analysis (no specific function targeted)."
        )

        lines.append(
            f"  - {len(related_tests)} related test(s) found."
        )

        lines.append(
            f"  - {len(git_func_history)} relevant commits "
            "in history."
        )

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Text formatter
# ---------------------------------------------------------------------------

def format_report(report: dict) -> str:
    """
    Convert a report dict into a human-readable text report.

    IMPORTANT:
    A test is marked PASS only when its pytest ID is explicitly present
    in `passed_tests`.

    A test is marked FAIL only when its pytest ID is explicitly present
    in `failed_tests`.

    Anything else is marked UNKNOWN rather than incorrectly being treated
    as passing.
    """

    sep = "=" * 60
    thin = "-" * 60

    lines = [
        sep,
        "  CHANGE IMPACT REPORT",
        sep,
    ]

    lines.append(
        f"Target file : {report['target_file']}"
    )

    if report["target_func"]:
        lines.append(
            f"Target func : {report['target_func']}"
        )

    lines.append("")

    # ── Direct callees ────────────────────────────────────────────────────
    callees = report["direct_callees"]

    lines.append(
        f"[Functions called BY target] ({len(callees)})"
    )

    if callees:
        for c in callees:
            lines.append(
                f"  -> {c.module}.{c.name}  "
                f"(line {c.lineno}  {c.file_path})"
            )
    else:
        lines.append("  (none detected)")

    lines.append("")

    # ── Direct callers ────────────────────────────────────────────────────
    callers = report["direct_callers"]

    lines.append(
        f"[Direct callers of target] ({len(callers)})"
    )

    if callers:
        for c in callers:
            lines.append(
                f"  <- {c.module}.{c.name}  "
                f"(line {c.lineno}  {c.file_path})"
            )
    else:
        lines.append("  (none detected)")

    lines.append("")

    # ── Indirect callers ─────────────────────────────────────────────────
    indirect = report["indirect_callers"]

    total_indirect = sum(
        len(v)
        for v in indirect.values()
    )

    lines.append(
        f"[Indirect callers] "
        f"({total_indirect} across "
        f"{len(indirect)} depth level(s))"
    )

    for depth, infos in sorted(indirect.items()):
        for c in infos:
            lines.append(
                f"  depth {depth}  <- "
                f"{c.module}.{c.name}  "
                f"(line {c.lineno})"
            )

    if not indirect:
        lines.append("  (none detected)")

    lines.append("")

    # ── Related tests ────────────────────────────────────────────────────
    tests = report["related_tests"]
    test_results = report.get("test_results") or {}

    # IMPORTANT:
    # Build BOTH sets explicitly.
    #
    # We do NOT assume that every test that isn't failed is passed.
    # This prevents failed/errored/unreported tests from being displayed
    # as passing.
    failed_test_ids = {
        _normalize_test_id(test_id)
        for test_id in test_results.get(
            "failed_tests",
            [],
        )
    }

    passed_test_ids = {
        _normalize_test_id(test_id)
        for test_id in test_results.get(
            "passed_tests",
            [],
        )
    }

    error_test_ids = {
        _normalize_test_id(test_id)
        for test_id in test_results.get(
            "error_tests",
            [],
        )
    }

    lines.append(
        f"[Related tests] ({len(tests)})"
    )

    if tests:
        for test in tests:
            normalized = _normalize_test_id(
                test.pytest_id
            )

            if normalized in failed_test_ids:
                lines.append(
                    f"  [FAIL] {test.pytest_id}"
                )

            elif normalized in error_test_ids:
                lines.append(
                    f"  [ERROR] {test.pytest_id}"
                )

            elif normalized in passed_test_ids:
                lines.append(
                    f"  [PASS] {test.pytest_id}"
                )

            else:
                # Unknown is deliberately NOT treated as PASS.
                lines.append(
                    f"  [UNKNOWN] {test.pytest_id}"
                )

    else:
        lines.append(
            "  [WARN] No related tests found!"
        )

    lines.append("")

    # ── Test execution summary ───────────────────────────────────────────
    if test_results:
        total = test_results.get("total", 0)
        passed = test_results.get("passed", 0)
        failed = test_results.get("failed", 0)
        errors = test_results.get("errors", 0)

        lines.append("[Test results]")
        lines.append(f"  Total  : {total}")
        lines.append(f"  Passed : {passed}")
        lines.append(f"  Failed : {failed}")
        lines.append(f"  Errors : {errors}")

        if tests:
            related_failed = sum(
                1
                for test in tests
                if _normalize_test_id(
                    test.pytest_id
                ) in failed_test_ids
            )

            related_passed = sum(
                1
                for test in tests
                if _normalize_test_id(
                    test.pytest_id
                ) in passed_test_ids
            )

            related_errors = sum(
                1
                for test in tests
                if _normalize_test_id(
                    test.pytest_id
                ) in error_test_ids
            )

            related_unknown = (
                len(tests)
                - related_failed
                - related_passed
                - related_errors
            )

            lines.append("")

            lines.append(
                f"  Related tests passing: "
                f"{related_passed}/{len(tests)}"
            )

            lines.append(
                f"  Related tests failing: "
                f"{related_failed}/{len(tests)}"
            )

            if related_errors:
                lines.append(
                    f"  Related tests with errors: "
                    f"{related_errors}/{len(tests)}"
                )

            if related_unknown:
                lines.append(
                    f"  Related tests with unknown status: "
                    f"{related_unknown}/{len(tests)}"
                )

        lines.append("")

    # ── Coverage gaps ────────────────────────────────────────────────────
    gaps = report["coverage_gaps"]

    lines.append(
        f"[Coverage gaps] ({len(gaps)})"
    )

    if gaps:
        for gap in gaps:
            lines.append(
                f"  [WARN] {gap}"
            )
    else:
        lines.append(
            "  (none detected)"
        )

    lines.append("")

    # ── Git file history ─────────────────────────────────────────────────
    file_history = report["git_file_history"]

    lines.append(
        f"[Git history — file] "
        f"({len(file_history)} commits)"
    )

    for commit in file_history:
        lines.append(
            f"  {commit.one_line()}"
        )

    if not file_history:
        lines.append(
            "  (no history found — not a git repo, "
            "or file not committed)"
        )

    lines.append("")

    # ── Git function history ─────────────────────────────────────────────
    func_history = report["git_func_history"]

    if report["target_func"]:
        lines.append(
            f"[Git history — function "
            f"'{report['target_func']}'] "
            f"({len(func_history)} commits)"
        )

        for commit in func_history:
            lines.append(
                f"  {commit.one_line()}"
            )

        if not func_history:
            lines.append(
                "  (function name not found in any diff)"
            )

        lines.append("")

    # ── Risk summary ─────────────────────────────────────────────────────
    lines.append(thin)
    lines.append("[Risk summary]")
    lines.append(report["risk_summary"])
    lines.append(sep)

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Working-tree analysis
# ---------------------------------------------------------------------------

def analyze_working_tree(
    repo_root: str,
    test_dirs: Optional[List[str]] = None,
    source_dirs: Optional[List[str]] = None,
    diff: Optional[str] = None,
) -> List[dict]:
    """
    Analyze changes and produce impact reports.

    If `diff` is provided, analyze that diff directly.
    Otherwise, analyze the current unstaged working-tree diff.

    Pipeline:
        diff
        -> changed functions
        -> related tests
        -> full impact reports
    """

    # ---------------------------------------------------------------
    # 1. Get the diff
    # ---------------------------------------------------------------

    if diff is None:
        diff = get_working_tree_diff(repo_root)

    if not diff:
        return []

    # ---------------------------------------------------------------
    # 2. Find functions affected by the diff
    # ---------------------------------------------------------------

    changed_functions = get_changed_functions(
        diff,
        repo_root,
    )

    if not changed_functions:
        return []

    # ---------------------------------------------------------------
    # 3. Default test directory
    # ---------------------------------------------------------------

    if test_dirs is None:
        test_dirs = [repo_root]

    # ---------------------------------------------------------------
    # 4. Restrict analysis to source directories
    # ---------------------------------------------------------------

    if source_dirs:
        normalized_source_dirs = [
            source_dir.replace("\\", "/").rstrip("/")
            for source_dir in source_dirs
        ]

        changed_functions = [
            changed
            for changed in changed_functions
            if any(
                changed["file"]
                .replace("\\", "/")
                .startswith(
                    source_dir + "/"
                )
                for source_dir in normalized_source_dirs
            )
        ]

    # ---------------------------------------------------------------
    # 5. Build impact report for every changed function
    # ---------------------------------------------------------------

    reports = []

    for changed in changed_functions:
        report = build_report(
            target_path=str(
                Path(repo_root) / changed["file"]
            ),
            target_func=changed["function"],
            project_root=repo_root,
            test_dirs=test_dirs,
        )

        # Keep information about the actual change that triggered
        # this report.
        report["changed_line"] = changed["line"]

        reports.append(report)

    return reports