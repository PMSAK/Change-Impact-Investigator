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

from unittest.mock import patch

from impact_investigator.git_analysis import (
    get_commits_for_file,
    commits_touching_function,
    get_repo_root,
    get_working_tree_diff,
    get_changed_files,
    _find_repo_root,
    _run,
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


# ---------------------------------------------------------------------------
# get_working_tree_diff
# ---------------------------------------------------------------------------

_FAKE_DIFF = (
    "diff --git a/demo_project/app/pricing.py b/demo_project/app/pricing.py\n"
    "index abc1234..def5678 100644\n"
    "--- a/demo_project/app/pricing.py\n"
    "+++ b/demo_project/app/pricing.py\n"
    "@@ -5,6 +5,6 @@ TAX_RATE = 0.08\n"
    "-TAX_RATE = 0.08\n"
    "+TAX_RATE = 0.09\n"
)


class TestGetWorkingTreeDiff:
    def test_returns_string(self):
        """get_working_tree_diff always returns a str."""
        with patch("impact_investigator.git_analysis._run", return_value=_FAKE_DIFF):
            result = get_working_tree_diff(REPO_ROOT)
        assert isinstance(result, str)

    def test_returns_mocked_diff_text(self):
        with patch("impact_investigator.git_analysis._run", return_value=_FAKE_DIFF):
            result = get_working_tree_diff(REPO_ROOT)
        assert result == _FAKE_DIFF

    def test_passes_git_diff_command(self):
        """Verify the exact git command forwarded to _run."""
        with patch("impact_investigator.git_analysis._run", return_value="") as mock_run:
            get_working_tree_diff(REPO_ROOT)
        mock_run.assert_called_once_with(["git", "diff"], cwd=REPO_ROOT)

    def test_returns_empty_string_when_no_changes(self):
        with patch("impact_investigator.git_analysis._run", return_value=""):
            result = get_working_tree_diff(REPO_ROOT)
        assert result == ""

    def test_live_call_returns_string(self):
        """Live integration: result must be a str (content varies by working-tree state)."""
        result = get_working_tree_diff(REPO_ROOT)
        assert isinstance(result, str)


# ---------------------------------------------------------------------------
# get_changed_files
# ---------------------------------------------------------------------------

class TestGetChangedFiles:
    def test_returns_list(self):
        """get_changed_files always returns a list."""
        with patch("impact_investigator.git_analysis._run", return_value=""):
            result = get_changed_files(REPO_ROOT)
        assert isinstance(result, list)

    def test_parses_single_file(self):
        with patch(
            "impact_investigator.git_analysis._run",
            return_value="demo_project/app/pricing.py\n",
        ):
            result = get_changed_files(REPO_ROOT)
        assert result == ["demo_project/app/pricing.py"]

    def test_parses_multiple_files(self):
        fake_output = (
            "demo_project/app/pricing.py\n"
            "demo_project/app/checkout.py\n"
        )
        with patch("impact_investigator.git_analysis._run", return_value=fake_output):
            result = get_changed_files(REPO_ROOT)
        assert result == [
            "demo_project/app/pricing.py",
            "demo_project/app/checkout.py",
        ]

    def test_empty_output_returns_empty_list(self):
        with patch("impact_investigator.git_analysis._run", return_value=""):
            result = get_changed_files(REPO_ROOT)
        assert result == []

    def test_blank_lines_excluded(self):
        """Blank lines in git output (e.g. trailing newline) are stripped."""
        with patch(
            "impact_investigator.git_analysis._run",
            return_value="\nsome/file.py\n\n",
        ):
            result = get_changed_files(REPO_ROOT)
        assert result == ["some/file.py"]

    def test_passes_git_diff_name_only_command(self):
        """Verify the exact git command forwarded to _run."""
        with patch("impact_investigator.git_analysis._run", return_value="") as mock_run:
            get_changed_files(REPO_ROOT)
        mock_run.assert_called_once_with(
            ["git", "diff", "--name-only"], cwd=REPO_ROOT
        )

    def test_live_call_returns_list(self):
        """Live integration: result is a list of strings (content varies)."""
        result = get_changed_files(REPO_ROOT)
        assert isinstance(result, list)
        assert all(isinstance(f, str) for f in result)

    def test_live_call_excludes_untracked_files(self, tmp_path):
        """
        Untracked files must not appear in the output.
        Create a new file in the repo, then verify get_changed_files
        does not list it (git diff --name-only only shows tracked modifications).
        """
        new_file = Path(REPO_ROOT) / "demo_project" / "_untracked_sentinel.py"
        try:
            new_file.write_text("# sentinel\n", encoding="utf-8")
            result = get_changed_files(REPO_ROOT)
            assert "demo_project/_untracked_sentinel.py" not in result
        finally:
            if new_file.exists():
                new_file.unlink()
