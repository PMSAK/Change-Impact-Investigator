"""
test_reporter.py
~~~~~~~~~~~~~~~~
Integration tests for impact_investigator.reporter using demo_project.
"""

import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from impact_investigator.reporter import build_report, format_report, _is_test_module

REPO_ROOT = str(Path(__file__).parent.parent)
DEMO_ROOT = str(Path(REPO_ROOT) / "demo_project")
PRICING_PY = str(Path(DEMO_ROOT) / "app" / "pricing.py")
TEST_DIR = str(Path(DEMO_ROOT) / "tests")


# ---------------------------------------------------------------------------
# _is_test_module helper
# ---------------------------------------------------------------------------

class TestIsTestModule:
    def test_test_module_detected(self):
        assert _is_test_module("tests.test_pricing") is True
        assert _is_test_module("test_checkout") is True

    def test_production_module_not_detected(self):
        assert _is_test_module("app.pricing") is False
        assert _is_test_module("app.checkout") is False


# ---------------------------------------------------------------------------
# build_report — calculate_discount (main demo scenario)
# ---------------------------------------------------------------------------

class TestBuildReportDiscountFunction:
    @pytest.fixture(scope="module")
    def report(self):
        return build_report(
            target_path=PRICING_PY,
            target_func="calculate_discount",
            project_root=DEMO_ROOT,
            test_dirs=[TEST_DIR],
        )

    def test_report_has_expected_keys(self, report):
        expected = {
            "target_file", "target_func",
            "direct_callers", "indirect_callers",
            "direct_callees",
            "related_tests", "coverage_gaps",
            "git_file_history", "git_func_history",
            "risk_summary",
        }
        assert set(report.keys()) == expected

    def test_target_func_is_set(self, report):
        assert report["target_func"] == "calculate_discount"

    def test_direct_caller_is_calculate_total(self, report):
        caller_names = [c.name for c in report["direct_callers"]]
        assert "calculate_total" in caller_names

    def test_no_test_functions_in_callers(self, report):
        for c in report["direct_callers"]:
            assert not c.name.startswith("test_"), (
                f"Test function {c.name!r} should not appear in direct_callers"
            )

    def test_create_order_in_indirect_callers(self, report):
        all_indirect = [
            c.name
            for level in report["indirect_callers"].values()
            for c in level
        ]
        assert "create_order" in all_indirect

    def test_related_tests_present(self, report):
        assert len(report["related_tests"]) > 0

    def test_vip_gap_detected(self, report):
        gap_texts = " ".join(report["coverage_gaps"])
        assert "vip" in gap_texts.lower(), (
            "Expected VIP coverage gap to be detected but it was not.\n"
            f"Gaps found: {report['coverage_gaps']}"
        )

    def test_git_file_history_has_discount_commit(self, report):
        messages = [c.message for c in report["git_file_history"]]
        assert any("discount" in m.lower() for m in messages)

    def test_git_func_history_not_empty(self, report):
        assert len(report["git_func_history"]) >= 1

    def test_risk_summary_is_string(self, report):
        assert isinstance(report["risk_summary"], str)
        assert len(report["risk_summary"]) > 10


# ---------------------------------------------------------------------------
# build_report — file-level (no function specified)
# ---------------------------------------------------------------------------

class TestBuildReportFileLevel:
    @pytest.fixture(scope="module")
    def report(self):
        return build_report(
            target_path=PRICING_PY,
            target_func=None,
            project_root=DEMO_ROOT,
            test_dirs=[TEST_DIR],
        )

    def test_target_func_is_none(self, report):
        assert report["target_func"] is None

    def test_related_tests_found(self, report):
        # File-level: at least the test_pricing.py file should be linked
        assert len(report["related_tests"]) > 0, (
            "Expected at least one test file related to pricing.py"
        )

    def test_direct_callers_empty_for_file_level(self, report):
        # No function targeted → callers are not computed
        assert report["direct_callers"] == []


# ---------------------------------------------------------------------------
# format_report
# ---------------------------------------------------------------------------

class TestFormatReport:
    @pytest.fixture(scope="module")
    def report(self):
        return build_report(
            target_path=PRICING_PY,
            target_func="calculate_discount",
            project_root=DEMO_ROOT,
            test_dirs=[TEST_DIR],
        )

    def test_formatted_output_is_string(self, report):
        text = format_report(report)
        assert isinstance(text, str)

    def test_formatted_output_contains_target_func(self, report):
        text = format_report(report)
        assert "calculate_discount" in text

    def test_formatted_output_contains_section_headers(self, report):
        text = format_report(report)
        assert "[Direct callers of target]" in text
        assert "[Related tests]" in text
        assert "[Coverage gaps]" in text
        assert "[Risk summary]" in text

    def test_formatted_output_shows_vip_gap(self, report):
        text = format_report(report)
        assert "vip" in text.lower()

    def test_formatted_output_shows_calculate_total_caller(self, report):
        text = format_report(report)
        assert "calculate_total" in text
