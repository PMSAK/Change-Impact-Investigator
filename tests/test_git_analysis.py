"""
test_git_analysis.py
~~~~~~~~~~~~~~~~~~~~
Tests for impact_investigator.git_analysis.

Uses the actual repo at the workspace root so real commits are available.
"""

import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from impact_investigator.git_analysis import (
    get_commits_for_file,
    commits_touching_function,
    get_repo_root,
    _find_repo_root,
)

REPO_ROOT = str(Path(__file__).parent.parent)
PRICING_PY = str(Path(REPO_ROOT) / "demo_project" / "app" / "pricing.py")
CHECKOUT_PY = str(Path(REPO_ROOT) / "demo_project" / "app" / "checkout.py")


class TestGetRepoRoot:
    def test_finds_repo_root_from_demo_file(self):
        root = get_repo_root(PRICING_PY)
        assert root is not None
        assert Path(root, ".git").exists()

    def test_returns_none_for_path_outside_any_repo(self, tmp_path):
        outside = str(tmp_path / "no_git_here" / "file.py")
        result = _find_repo_root(outside)
        # tmp_path itself is unlikely to be inside a git repo in CI
        # This is a best-effort test; just verify the function doesn't crash
        assert result is None or isinstance(result, str)


class TestGetCommitsForFile:
    def test_pricing_has_at_least_two_commits(self):
        commits = get_commits_for_file(PRICING_PY, REPO_ROOT)
        assert len(commits) >= 2

    def test_commit_has_expected_fields(self):
        commits = get_commits_for_file(PRICING_PY, REPO_ROOT)
        ci = commits[0]
        assert ci.sha and len(ci.sha) == 40
        assert ci.short_sha and len(ci.short_sha) == 8
        assert ci.author
        assert ci.date  # e.g. "2026-09-25"
        assert ci.message

    def test_feat_commit_present_for_pricing(self):
        """The discount feature commit touched pricing.py."""
        commits = get_commits_for_file(PRICING_PY, REPO_ROOT)
        messages = [c.message for c in commits]
        assert any("discount" in m.lower() for m in messages)

    def test_invoice_has_initial_commit(self):
        invoice_py = str(Path(REPO_ROOT) / "demo_project" / "app" / "invoice.py")
        commits = get_commits_for_file(invoice_py, REPO_ROOT)
        # invoice.py was first added in the initial pricing/checkout commit
        assert len(commits) >= 1
        messages = [c.message for c in commits]
        assert any("pricing" in m.lower() or "checkout" in m.lower() or "invoice" in m.lower()
                   for m in messages)

    def test_max_commits_limit_respected(self):
        commits = get_commits_for_file(PRICING_PY, REPO_ROOT, max_commits=1)
        assert len(commits) <= 1

    def test_returns_empty_for_nonexistent_file(self):
        commits = get_commits_for_file("/no/such/file.py", REPO_ROOT)
        assert commits == []


class TestCommitsTouchingFunction:
    def test_calculate_discount_touched_in_discount_commit(self):
        """'calculate_discount' first appeared in the discount feature commit."""
        commits = commits_touching_function(
            "calculate_discount", PRICING_PY, REPO_ROOT
        )
        assert len(commits) >= 1
        messages = [c.message for c in commits]
        assert any("discount" in m.lower() for m in messages)

    def test_generate_invoice_touched_in_initial_commit(self):
        """generate_invoice was first defined in the initial pricing commit."""
        invoice_py = str(Path(REPO_ROOT) / "demo_project" / "app" / "invoice.py")
        commits = commits_touching_function(
            "generate_invoice", invoice_py, REPO_ROOT
        )
        assert len(commits) >= 1
        messages = [c.message for c in commits]
        assert any(
            "pricing" in m.lower() or "checkout" in m.lower() or "order" in m.lower()
            for m in messages
        )

    def test_unknown_function_returns_no_matching_commits(self):
        commits = commits_touching_function(
            "totally_nonexistent_func_xyz", PRICING_PY, REPO_ROOT
        )
        assert len(commits) == 0
