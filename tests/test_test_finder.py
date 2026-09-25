"""
test_test_finder.py
~~~~~~~~~~~~~~~~~~~
Tests for impact_investigator.test_finder using the demo_project as fixture.
"""

import os
import sys
import tempfile
import textwrap
from pathlib import Path

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from impact_investigator.test_finder import (
    scan_tests,
    find_related_tests,
    detect_coverage_gaps,
    detect_value_path_gaps,
    _collect_string_literals_in_calls,
    _collect_dict_string_keys,
    _imported_names,
)

DEMO_ROOT = Path(__file__).parent.parent / "demo_project"
TEST_DIR = str(DEMO_ROOT / "tests")
PRICING_PY = str(DEMO_ROOT / "app" / "pricing.py")
TEST_PRICING_PY = str(DEMO_ROOT / "tests" / "test_pricing.py")
TEST_CHECKOUT_PY = str(DEMO_ROOT / "tests" / "test_checkout.py")


# ---------------------------------------------------------------------------
# scan_tests
# ---------------------------------------------------------------------------

class TestScanTests:
    @pytest.fixture(scope="module")
    def all_tests(self):
        return scan_tests(TEST_DIR)

    def test_finds_test_functions(self, all_tests):
        names = [t.name for t in all_tests]
        assert "test_single_item" in names
        assert "test_regular_customer_gets_no_discount" in names
        assert "test_member_gets_five_percent" in names

    def test_class_tests_have_class_name(self, all_tests):
        class_tests = [t for t in all_tests if t.class_name is not None]
        assert len(class_tests) > 0
        class_names = {t.class_name for t in class_tests}
        assert "TestSubtotal" in class_names
        assert "TestDiscount" in class_names

    def test_no_duplicates(self, all_tests):
        ids = [t.pytest_id for t in all_tests]
        assert len(ids) == len(set(ids)), "Duplicate test IDs found"

    def test_total_count_matches_demo_suite(self, all_tests):
        # The demo project has 31 tests
        assert len(all_tests) == 31

    def test_test_references_include_imported_names(self, all_tests):
        # test_pricing.py imports calculate_discount, calculate_total, etc.
        pricing_tests = [t for t in all_tests if "test_pricing" in t.file_path]
        all_refs = set().union(*[t.references for t in pricing_tests])
        assert "calculate_discount" in all_refs
        assert "calculate_total" in all_refs


# ---------------------------------------------------------------------------
# find_related_tests
# ---------------------------------------------------------------------------

class TestFindRelatedTests:
    @pytest.fixture(scope="module")
    def all_tests(self):
        return scan_tests(TEST_DIR)

    def test_calculate_discount_has_related_tests(self, all_tests):
        related = find_related_tests("calculate_discount", all_tests)
        assert len(related) > 0

    def test_calculate_discount_related_tests_are_from_pricing_file(self, all_tests):
        related = find_related_tests("calculate_discount", all_tests)
        files = {t.file_path for t in related}
        assert any("test_pricing" in f for f in files)

    def test_create_order_related_tests_include_checkout_tests(self, all_tests):
        related = find_related_tests("create_order", all_tests)
        names = [t.name for t in related]
        assert any("domestic" in n or "order" in n.lower() for n in names)

    def test_unknown_function_returns_empty(self, all_tests):
        related = find_related_tests("nonexistent_xyz_func", all_tests)
        assert related == []


# ---------------------------------------------------------------------------
# detect_coverage_gaps
# ---------------------------------------------------------------------------

class TestDetectCoverageGaps:
    @pytest.fixture(scope="module")
    def all_tests(self):
        return scan_tests(TEST_DIR)

    def test_no_gaps_for_well_tested_function(self, all_tests):
        from impact_investigator.ast_analysis import build_call_graph, find_callers
        graph = build_call_graph(str(DEMO_ROOT / "app"))
        callers = [c for c in find_callers("calculate_total", graph)
                   if not c.module.startswith("test")]
        gaps = detect_coverage_gaps("calculate_total", all_tests, callers)
        # calculate_total has good coverage, structural gaps should be 0
        assert len(gaps) == 0

    def test_uncovered_function_flagged(self, all_tests):
        # A function with a made-up name should be flagged
        gaps = detect_coverage_gaps("completely_uncovered_func", all_tests, [])
        assert len(gaps) == 1
        assert "no test coverage" in gaps[0].lower()


# ---------------------------------------------------------------------------
# detect_value_path_gaps  (VIP gap detection)
# ---------------------------------------------------------------------------

class TestDetectValuePathGaps:
    def test_vip_path_detected_for_calculate_discount(self):
        """The intentional gap: 'vip' customer type has no test."""
        test_files = [
            TEST_PRICING_PY,
            TEST_CHECKOUT_PY,
        ]
        gaps = detect_value_path_gaps("calculate_discount", PRICING_PY, test_files)
        gap_texts = " ".join(gaps)
        assert "vip" in gap_texts.lower()

    def test_tested_values_not_flagged(self):
        """'member' and 'regular' ARE tested, so they must not appear as gaps."""
        test_files = [TEST_PRICING_PY, TEST_CHECKOUT_PY]
        gaps = detect_value_path_gaps("calculate_discount", PRICING_PY, test_files)
        gap_texts = " ".join(gaps)
        assert "member" not in gap_texts.lower()
        assert "regular" not in gap_texts.lower()

    def test_no_gaps_when_all_values_tested(self):
        """If tests cover all known values, no gaps are returned."""
        with tempfile.NamedTemporaryFile(
            suffix=".py", mode="w", delete=False, encoding="utf-8"
        ) as prod:
            prod.write(textwrap.dedent("""
                RATES = {"a": 1, "b": 2}
                def my_func(x, kind): return RATES.get(kind, 0) * x
            """))
            prod_name = prod.name

        with tempfile.NamedTemporaryFile(
            suffix=".py", mode="w", delete=False, encoding="utf-8"
        ) as test:
            test.write(textwrap.dedent("""
                def test_a(): assert my_func(10, "a") == 10
                def test_b(): assert my_func(10, "b") == 20
            """))
            test_name = test.name

        try:
            gaps = detect_value_path_gaps("my_func", prod_name, [test_name])
            assert gaps == []
        finally:
            os.unlink(prod_name)
            os.unlink(test_name)

    def test_no_uppercase_dict_returns_no_gaps(self):
        """Files without UPPER_CASE dicts should not generate false gaps."""
        with tempfile.NamedTemporaryFile(
            suffix=".py", mode="w", delete=False, encoding="utf-8"
        ) as f:
            # lowercase dict name → not a constant → should not be scanned
            f.write('rates = {"a": 1}\ndef fn(x): return rates.get(x, 0)\n')
            name = f.name
        try:
            gaps = detect_value_path_gaps("fn", name, [])
            assert gaps == []
        finally:
            os.unlink(name)


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

class TestCollectStringLiterals:
    def test_extracts_customer_type_literals_from_test_pricing(self):
        literals = _collect_string_literals_in_calls(
            TEST_PRICING_PY, "calculate_discount"
        )
        # test_pricing.py passes "regular", "member", "guest" to calculate_discount
        assert "regular" in literals
        assert "member" in literals
        assert "guest" in literals
        assert "vip" not in literals

    def test_empty_for_unknown_function(self):
        literals = _collect_string_literals_in_calls(TEST_PRICING_PY, "no_such_func")
        assert literals == set()


class TestCollectDictKeys:
    def test_finds_discount_rates_keys(self):
        keys = _collect_dict_string_keys(PRICING_PY)
        assert "regular" in keys
        assert "member" in keys
        assert "vip" in keys

    def test_ignores_lowercase_dict_names(self):
        with tempfile.NamedTemporaryFile(
            suffix=".py", mode="w", delete=False, encoding="utf-8"
        ) as f:
            f.write('my_dict = {"a": 1, "b": 2}\n')
            name = f.name
        try:
            keys = _collect_dict_string_keys(name)
            assert keys == set()
        finally:
            os.unlink(name)
