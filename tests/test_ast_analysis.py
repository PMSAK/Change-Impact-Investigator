"""
test_ast_analysis.py
~~~~~~~~~~~~~~~~~~~~
Tests for impact_investigator.ast_analysis using the demo_project as fixture.
"""

import os
import sys
import tempfile
import textwrap
from pathlib import Path

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from impact_investigator.ast_analysis import (
    parse_file,
    extract_imports,
    build_call_graph,
    find_callers,
    find_callees,
    indirect_callers,
    _resolve,
)

# ---------------------------------------------------------------------------
# Paths to demo_project files (used as real-world fixtures)
# ---------------------------------------------------------------------------

DEMO_ROOT = Path(__file__).parent.parent / "demo_project"
PRICING_PY = str(DEMO_ROOT / "app" / "pricing.py")
CHECKOUT_PY = str(DEMO_ROOT / "app" / "checkout.py")
SHIPPING_PY = str(DEMO_ROOT / "app" / "shipping.py")
INVOICE_PY = str(DEMO_ROOT / "app" / "invoice.py")


# ---------------------------------------------------------------------------
# parse_file
# ---------------------------------------------------------------------------

class TestParseFile:
    def test_finds_all_functions_in_pricing(self):
        funcs = parse_file(PRICING_PY, "app.pricing")
        names = [f.name for f in funcs]
        assert "calculate_subtotal" in names
        assert "calculate_discount" in names
        assert "calculate_tax" in names
        assert "calculate_total" in names

    def test_function_info_has_correct_module(self):
        funcs = parse_file(PRICING_PY, "app.pricing")
        for f in funcs:
            assert f.module == "app.pricing"

    def test_function_lineno_is_positive(self):
        funcs = parse_file(PRICING_PY, "app.pricing")
        for f in funcs:
            assert f.lineno > 0

    def test_calculate_total_calls_other_pricing_funcs(self):
        funcs = parse_file(PRICING_PY, "app.pricing")
        total_fn = next(f for f in funcs if f.name == "calculate_total")
        # calculate_total calls calculate_subtotal, calculate_discount, calculate_tax
        assert "calculate_subtotal" in total_fn.calls
        assert "calculate_discount" in total_fn.calls
        assert "calculate_tax" in total_fn.calls

    def test_checkout_calls_calculate_total_and_calculate_shipping(self):
        funcs = parse_file(CHECKOUT_PY, "app.checkout")
        create_order = next(f for f in funcs if f.name == "create_order")
        assert "calculate_total" in create_order.calls
        assert "calculate_shipping" in create_order.calls

    def test_nonexistent_file_returns_empty(self):
        result = parse_file("/nonexistent/path/file.py", "fake.module")
        assert result == []

    def test_syntax_error_returns_empty(self):
        with tempfile.NamedTemporaryFile(
            suffix=".py", mode="w", delete=False, encoding="utf-8"
        ) as f:
            f.write("def broken(\n    missing_close")
            name = f.name
        try:
            result = parse_file(name, "broken")
            assert result == []
        finally:
            os.unlink(name)

    def test_uses_stem_as_module_when_not_provided(self):
        funcs = parse_file(PRICING_PY)
        # Default module name should be file stem "pricing"
        assert all(f.module == "pricing" for f in funcs)


# ---------------------------------------------------------------------------
# extract_imports
# ---------------------------------------------------------------------------

class TestExtractImports:
    def test_checkout_imports_pricing_and_shipping(self):
        imports = extract_imports(CHECKOUT_PY)
        modules = [m for m, _ in imports]
        names = [n for _, n in imports if n is not None]
        assert "app.pricing" in modules
        assert "app.shipping" in modules
        assert "calculate_total" in names
        assert "calculate_shipping" in names

    def test_nonexistent_file_returns_empty(self):
        assert extract_imports("/no/such/file.py") == []


# ---------------------------------------------------------------------------
# build_call_graph
# ---------------------------------------------------------------------------

class TestBuildCallGraph:
    @pytest.fixture(scope="module")
    def graph(self):
        return build_call_graph(str(DEMO_ROOT / "app"))

    def test_graph_contains_pricing_functions(self, graph):
        keys = list(graph.keys())
        assert any("calculate_discount" in k for k in keys)
        assert any("calculate_total" in k for k in keys)
        assert any("create_order" in k for k in keys)

    def test_graph_keys_are_module_dot_name(self, graph):
        for key in graph.keys():
            assert "." in key, f"Key {key!r} has no module prefix"

    def test_graph_excludes_pycache(self, graph):
        for key, info in graph.items():
            assert "__pycache__" not in info.file_path


# ---------------------------------------------------------------------------
# find_callers
# ---------------------------------------------------------------------------

class TestFindCallers:
    @pytest.fixture(scope="module")
    def graph(self):
        return build_call_graph(str(DEMO_ROOT / "app"))

    def test_calculate_discount_is_called_by_calculate_total(self, graph):
        callers = find_callers("calculate_discount", graph)
        names = [c.name for c in callers]
        assert "calculate_total" in names

    def test_calculate_shipping_is_called_by_create_order(self, graph):
        callers = find_callers("calculate_shipping", graph)
        names = [c.name for c in callers]
        assert "create_order" in names

    def test_no_callers_for_unknown_function(self, graph):
        callers = find_callers("nonexistent_func_xyz", graph)
        assert callers == []


# ---------------------------------------------------------------------------
# find_callees
# ---------------------------------------------------------------------------

class TestFindCallees:
    @pytest.fixture(scope="module")
    def graph(self):
        return build_call_graph(str(DEMO_ROOT / "app"))

    def test_calculate_total_callees_include_discount_and_tax(self, graph):
        callees = find_callees("calculate_total", graph)
        names = [c.name for c in callees]
        assert "calculate_discount" in names
        assert "calculate_tax" in names
        assert "calculate_subtotal" in names

    def test_create_order_callees_include_pricing_and_shipping(self, graph):
        callees = find_callees("create_order", graph)
        names = [c.name for c in callees]
        assert "calculate_total" in names
        assert "calculate_shipping" in names

    def test_unknown_function_returns_empty(self, graph):
        assert find_callees("no_such_func", graph) == []


# ---------------------------------------------------------------------------
# indirect_callers
# ---------------------------------------------------------------------------

class TestIndirectCallers:
    @pytest.fixture(scope="module")
    def graph(self):
        return build_call_graph(str(DEMO_ROOT / "app"))

    def test_calculate_discount_reaches_create_order_within_2_hops(self, graph):
        result = indirect_callers("calculate_discount", graph, max_depth=3)
        all_names = [c.name for level in result.values() for c in level]
        # depth 1: calculate_total; depth 2: create_order
        assert "calculate_total" in all_names
        assert "create_order" in all_names

    def test_returns_empty_for_unknown_target(self, graph):
        result = indirect_callers("ghost_function", graph, max_depth=3)
        assert result == {}

    def test_max_depth_respected(self, graph):
        result = indirect_callers("calculate_discount", graph, max_depth=1)
        assert max(result.keys(), default=0) <= 1
