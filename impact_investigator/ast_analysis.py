"""
ast_analysis.py
~~~~~~~~~~~~~~~
Static Python AST analysis for the Change Impact Investigator.

Responsibilities:
  - Parse a Python source file and extract all top-level and nested function/class definitions.
  - For each function, record the set of names it calls.
  - Walk an entire source directory and build a project-wide call graph.
  - Given a target function name, return:
      * direct callers  (functions that call the target)
      * direct callees  (functions the target itself calls)
      * the modules those live in

All analysis is purely static (no imports executed).
"""

import ast
import os
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

class FunctionInfo:
    """Metadata about a single function definition found in source."""

    __slots__ = ("name", "module", "file_path", "lineno", "calls")

    def __init__(self, name: str, module: str, file_path: str, lineno: int):
        self.name = name
        self.module = module          # dotted module name, e.g. "app.pricing"
        self.file_path = file_path    # absolute or relative path to source file
        self.lineno = lineno
        self.calls: Set[str] = set()  # bare names of functions/attrs called

    def __repr__(self) -> str:  # pragma: no cover
        return f"FunctionInfo({self.module}.{self.name} @ line {self.lineno})"


# ---------------------------------------------------------------------------
# Single-file parsing
# ---------------------------------------------------------------------------

class _CallCollector(ast.NodeVisitor):
    """Collect all names/attributes that are *called* inside a node."""

    def __init__(self):
        self.calls: Set[str] = set()

    def visit_Call(self, node: ast.Call):
        func = node.func
        if isinstance(func, ast.Name):
            self.calls.add(func.id)
        elif isinstance(func, ast.Attribute):
            # e.g. pricing.calculate_total → record both "pricing.calculate_total"
            # and just "calculate_total" so name-only lookups work too.
            parts = _attr_chain(func)
            if parts:
                self.calls.add(".".join(parts))
                self.calls.add(parts[-1])
        self.generic_visit(node)


def _attr_chain(node: ast.expr) -> List[str]:
    """Recursively unpack an Attribute node into a list of name parts."""
    if isinstance(node, ast.Name):
        return [node.id]
    if isinstance(node, ast.Attribute):
        parent = _attr_chain(node.value)
        if parent:
            return parent + [node.attr]
    return []


def parse_file(file_path: str, module_name: str = "") -> List[FunctionInfo]:
    """
    Parse *file_path* and return a list of FunctionInfo objects, one per
    function/method defined in that file (including nested defs).

    module_name is used to populate FunctionInfo.module; if empty, the
    stem of the file path is used.
    """
    path = Path(file_path)
    if not module_name:
        module_name = path.stem

    try:
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(path))
    except (OSError, SyntaxError):
        return []

    functions: List[FunctionInfo] = []

    class _FuncVisitor(ast.NodeVisitor):
        def visit_FunctionDef(self, node: ast.FunctionDef):
            info = FunctionInfo(
                name=node.name,
                module=module_name,
                file_path=str(path),
                lineno=node.lineno,
            )
            collector = _CallCollector()
            collector.visit(node)
            info.calls = collector.calls
            functions.append(info)
            self.generic_visit(node)  # capture nested defs

        visit_AsyncFunctionDef = visit_FunctionDef

    _FuncVisitor().visit(tree)
    return functions


def extract_imports(file_path: str) -> List[Tuple[str, Optional[str]]]:
    """
    Return a list of (module, name_or_None) pairs for all imports in a file.

    Examples:
        import os                     → [("os", None)]
        from app.pricing import foo   → [("app.pricing", "foo")]
    """
    path = Path(file_path)
    try:
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(path))
    except (OSError, SyntaxError):
        return []

    imports: List[Tuple[str, Optional[str]]] = []

    class _ImportVisitor(ast.NodeVisitor):
        def visit_Import(self, node: ast.Import):
            for alias in node.names:
                imports.append((alias.name, None))

        def visit_ImportFrom(self, node: ast.ImportFrom):
            mod = node.module or ""
            for alias in node.names:
                imports.append((mod, alias.name))

    _ImportVisitor().visit(tree)
    return imports


# ---------------------------------------------------------------------------
# Project-wide call graph
# ---------------------------------------------------------------------------

def _module_name_for_path(file_path: Path, root: Path) -> str:
    """Convert a file path to a dotted module name relative to *root*."""
    try:
        rel = file_path.relative_to(root)
    except ValueError:
        rel = file_path
    parts = list(rel.with_suffix("").parts)
    if parts and parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join(parts)


def build_call_graph(root_dir: str) -> Dict[str, FunctionInfo]:
    """
    Walk *root_dir* recursively, parse every .py file, and return a dict
    mapping "module.funcname" → FunctionInfo.

    Files inside __pycache__ or starting with "." are skipped.
    """
    root = Path(root_dir).resolve()
    graph: Dict[str, FunctionInfo] = {}

    for py_file in sorted(root.rglob("*.py")):
        # Skip cache dirs and hidden files
        if "__pycache__" in py_file.parts or py_file.name.startswith("."):
            continue
        module_name = _module_name_for_path(py_file, root)
        infos = parse_file(str(py_file), module_name)
        for info in infos:
            key = f"{info.module}.{info.name}"
            graph[key] = info

    return graph


# ---------------------------------------------------------------------------
# Impact queries
# ---------------------------------------------------------------------------

def find_callers(
    target_func: str,
    graph: Dict[str, FunctionInfo],
) -> List[FunctionInfo]:
    """
    Return all FunctionInfo objects whose call set contains *target_func*.

    Matches on bare function name OR qualified "module.funcname".
    """
    # Accept both "calculate_discount" and "pricing.calculate_discount"
    bare = target_func.split(".")[-1]
    callers = []
    for info in graph.values():
        if target_func in info.calls or bare in info.calls:
            callers.append(info)
    return callers


def find_callees(
    target_func: str,
    graph: Dict[str, FunctionInfo],
) -> List[FunctionInfo]:
    """
    Return all FunctionInfo objects that are called by *target_func*.
    """
    # Resolve the target to a FunctionInfo
    info = _resolve(target_func, graph)
    if info is None:
        return []

    results = []
    for call_name in info.calls:
        resolved = _resolve(call_name, graph)
        if resolved is not None:
            results.append(resolved)
    return results


def _resolve(name: str, graph: Dict[str, FunctionInfo]) -> Optional[FunctionInfo]:
    """
    Attempt to find a FunctionInfo matching *name*.
    Tries exact key first, then bare-name suffix match.
    """
    if name in graph:
        return graph[name]
    bare = name.split(".")[-1]
    for key, info in graph.items():
        if info.name == bare:
            return info
    return None


def indirect_callers(
    target_func: str,
    graph: Dict[str, FunctionInfo],
    max_depth: int = 3,
) -> Dict[int, List[FunctionInfo]]:
    """
    BFS from target_func following *callers* edges up to max_depth levels.

    Returns {depth: [FunctionInfo, ...]} so the report can show "depth 1 callers",
    "depth 2 callers", etc.
    """
    seen: Set[str] = set()
    current_level = [target_func]
    result: Dict[int, List[FunctionInfo]] = {}

    for depth in range(1, max_depth + 1):
        next_level = []
        level_infos = []
        for func in current_level:
            for caller in find_callers(func, graph):
                key = f"{caller.module}.{caller.name}"
                if key not in seen:
                    seen.add(key)
                    level_infos.append(caller)
                    next_level.append(caller.name)
        if not level_infos:
            break
        result[depth] = level_infos
        current_level = next_level

    return result