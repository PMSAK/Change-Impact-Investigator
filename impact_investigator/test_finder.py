"""
test_finder.py
~~~~~~~~~~~~~~
Scan a test directory and map test functions/classes to the production
functions/modules they exercise.

Strategy
--------
For each test file:
  1. Collect all `from X import Y` and `import X` statements to know which
     production modules and names the test file touches.
  2. Collect all function names that appear in *calls* inside that file
     (the same _CallCollector from ast_analysis).
  3. Build TestInfo records that link a test item (file + function name)
     to the set of production names it references.

A test is considered "related" to a target function if:
  - The target's name appears in the test file's imports, OR
  - The target's name appears in any call inside a test function body.
"""

import ast
import os
from pathlib import Path
from typing import Dict, List, Optional, Set

from impact_investigator.ast_analysis import (
    _CallCollector,
    extract_imports,
    parse_file,
)


# ---------------------------------------------------------------------------
# Data structure
# ---------------------------------------------------------------------------

class TestInfo:
    """Metadata about a single test function."""

    __test__ = False

    __slots__ = ("name", "file_path", "references", "class_name")

    def __init__(self, name: str, file_path: str, class_name: Optional[str] = None):
        self.name = name
        self.file_path = file_path
        self.class_name = class_name          # None for module-level tests
        self.references: Set[str] = set()     # production names referenced

    @property
    def full_name(self) -> str:
        if self.class_name:
            return f"{self.class_name}::{self.name}"
        return self.name

    @property
    def pytest_id(self) -> str:
        path = Path(self.file_path)

        if path.is_absolute():
            rel = os.path.relpath(self.file_path)
        else:
            rel = path.as_posix()

        return f"{rel}::{self.full_name}"

    def __repr__(self) -> str:  # pragma: no cover
        return f"TestInfo({self.pytest_id})"


# ---------------------------------------------------------------------------
# Single test-file parsing
# ---------------------------------------------------------------------------

def _collect_test_functions(file_path: str) -> List[TestInfo]:
    """
    Return all test functions (names starting with 'test_') found in *file_path*,
    along with the set of names each one calls.
    """
    path = Path(file_path)
    try:
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(path))
    except (OSError, SyntaxError):
        return []

    tests: List[TestInfo] = []

    # Only iterate direct children of the module to avoid double-counting
    # class methods (ast.walk visits them both inside the class and standalone).
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if item.name.startswith("test"):
                        ti = TestInfo(item.name, str(path), class_name=node.name)
                        collector = _CallCollector()
                        collector.visit(item)
                        ti.references = collector.calls
                        tests.append(ti)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name.startswith("test"):
                ti = TestInfo(node.name, str(path))
                collector = _CallCollector()
                collector.visit(node)
                ti.references = collector.calls
                tests.append(ti)

    return tests


# ---------------------------------------------------------------------------
# Project-wide test scan
# ---------------------------------------------------------------------------

def scan_tests(test_dir: str) -> List[TestInfo]:
    """
    Walk *test_dir* recursively and return all TestInfo objects found.
    """
    root = Path(test_dir)
    results: List[TestInfo] = []

    for py_file in sorted(root.rglob("test_*.py")):
        if "__pycache__" in py_file.parts:
            continue

        tests = _collect_test_functions(str(py_file))
        results.extend(tests)

    return results


def _imported_names(file_path: str) -> Set[str]:
    """
    Return the set of *names* (bare identifiers) imported in a file.
    e.g. `from app.pricing import calculate_total` → {"calculate_total"}
         `from app.pricing import calculate_total, calculate_tax` → both
    """
    names: Set[str] = set()
    for module, name in extract_imports(file_path):
        if name is not None:
            names.add(name)
        else:
            # `import foo.bar` – add the leaf name
            names.add(module.split(".")[-1])
    return names


# ---------------------------------------------------------------------------
# Query: which tests cover a target function?
# ---------------------------------------------------------------------------

def find_related_tests(
    target_func: str,
    all_tests: List[TestInfo],
) -> List[TestInfo]:
    """
    Return all TestInfo objects whose references include *target_func*
    (by bare name or qualified name).

    A test is related if it:
      - imports the target function by name, OR
      - calls the target function (directly or indirectly by name).
    """
    bare = target_func.split(".")[-1]
    related = []
    for ti in all_tests:
        if target_func in ti.references or bare in ti.references:
            related.append(ti)
    return related


# ---------------------------------------------------------------------------
# Coverage gap detection
# ---------------------------------------------------------------------------

def detect_coverage_gaps(
    target_func: str,
    all_tests: List[TestInfo],
    callers: list,           # List[FunctionInfo] from ast_analysis
) -> List[str]:
    """
    Return a list of human-readable gap descriptions.

    Gaps detected:
    1. No tests at all reference the target function.
    2. A direct caller of the target is not referenced by any test.
    """
    gaps: List[str] = []

    related = find_related_tests(target_func, all_tests)
    if not related:
        gaps.append(
            f"No tests reference '{target_func}' — this function has no test coverage."
        )

    for caller in callers:
        caller_related = find_related_tests(caller.name, all_tests)
        if not caller_related:
            gaps.append(
                f"'{caller.module}.{caller.name}' calls '{target_func}' but has no test coverage."
            )

    return gaps


# ---------------------------------------------------------------------------
# Value-path / string-constant gap detection
# ---------------------------------------------------------------------------

def _collect_string_literals_in_calls(file_path: str, func_name: str) -> Set[str]:
    """
    Scan *file_path* for calls to *func_name* and return all string literal
    arguments passed in those calls.

    Example: calculate_discount(100, "member") → {"member"}
    """
    path = Path(file_path)
    try:
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(path))
    except (OSError, SyntaxError):
        return set()

    literals: Set[str] = set()

    class _Visitor(ast.NodeVisitor):
        def visit_Call(self, node: ast.Call):
            func = node.func
            name = None
            if isinstance(func, ast.Name):
                name = func.id
            elif isinstance(func, ast.Attribute):
                name = func.attr
            if name == func_name:
                for arg in node.args:
                    if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                        literals.add(arg.value)
                for kw in node.keywords:
                    if isinstance(kw.value, ast.Constant) and isinstance(kw.value.value, str):
                        literals.add(kw.value.value)
            self.generic_visit(node)

    _Visitor().visit(tree)
    return literals


def _uppercase_names_referenced_in_func(file_path: str, func_name: str) -> Set[str]:
    """
    Parse *file_path*, find the function named *func_name*, and return all
    UPPER_CASE names whose attributes are accessed inside that function's body.

    This covers both direct accesses (``DISCOUNT_RATES[x]``) and method calls
    (``DISCOUNT_RATES.get(x, 0)``).

    Only the function's own AST body is walked — other functions in the same
    file are excluded, so constants belonging to sibling functions are ignored.
    """
    path = Path(file_path)
    try:
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(path))
    except (OSError, SyntaxError):
        return set()

    # Find the target function node (top-level or nested)
    target_node = None
    for node in ast.walk(tree):
        if (
            isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and node.name == func_name
        ):
            target_node = node
            break

    if target_node is None:
        return set()

    # Walk only the function body and collect UPPER_CASE Name references
    upper_names: Set[str] = set()
    for node in ast.walk(target_node):
        if isinstance(node, ast.Name) and node.id == node.id.upper() and len(node.id) > 1:
            upper_names.add(node.id)
    return upper_names


def _collect_dict_string_keys_for_names(
    file_path: str, constant_names: Set[str]
) -> Set[str]:
    """
    Scan the top-level UPPER_CASE dict assignments in *file_path* and return
    all string keys from assignments whose variable name is in *constant_names*.

    Example: if constant_names = {"DISCOUNT_RATES"} and the file contains
        DISCOUNT_RATES = {"regular": 0.0, "member": 0.05, "vip": 0.10}
    then {"regular", "member", "vip"} is returned.

    Assignments whose name is not in *constant_names* are ignored entirely,
    so constants belonging to other functions produce no false positives.
    """
    if not constant_names:
        return set()

    path = Path(file_path)
    try:
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(path))
    except (OSError, SyntaxError):
        return set()

    keys: Set[str] = set()
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        for target in node.targets:
            if (
                isinstance(target, ast.Name)
                and target.id in constant_names
                and isinstance(node.value, ast.Dict)
            ):
                for k in node.value.keys:
                    if isinstance(k, ast.Constant) and isinstance(k.value, str):
                        keys.add(k.value)
    return keys


def detect_value_path_gaps(
    target_func: str,
    target_file: str,
    all_test_files: List[str],
) -> List[str]:
    """
    Detect untested value paths for *target_func*.

    Strategy:
    1. Find which UPPER_CASE constant names the target function's own body
       references (e.g. ``DISCOUNT_RATES``).
    2. Collect the string keys of those specific dicts from the file.
    3. Collect all string literals passed to *target_func* across all test files.
    4. Any key present in step 2 but absent from step 3 is an untested value path.

    Only dicts actually used by the target function are considered, so sibling
    functions in the same file cannot inject false positives.

    Returns a list of human-readable gap descriptions.
    """
    # Step 1: which UPPER_CASE names does this function touch?
    constant_names = _uppercase_names_referenced_in_func(target_file, target_func)
    if not constant_names:
        return []

    # Step 2: string keys from only those dicts
    known_values = _collect_dict_string_keys_for_names(target_file, constant_names)
    if not known_values:
        return []

    # Step 3: values actually exercised by tests
    tested_values: Set[str] = set()
    for tf in all_test_files:
        tested_values |= _collect_string_literals_in_calls(tf, target_func)

    # Step 4: gaps
    gaps = []
    for value in sorted(known_values - tested_values):
        gaps.append(
            f"Value path '{value}' in '{target_func}' has no test coverage "
            f"(defined in {Path(target_file).name} but never passed in a test call)."
        )
    return gaps
