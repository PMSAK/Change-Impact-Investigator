"""
git_analysis.py
~~~~~~~~~~~~~~~
Lightweight Git history analysis for the Change Impact Investigator.

Uses `git log` and `git diff` via subprocess — no third-party library needed.

Provides:
  - Commits that touched a given file path.
  - For each commit, a short summary (hash, author, date, message).
  - The diff hunks for a file in a given commit, used to check whether a
    specific function was modified.
  - A "blame-adjacent" scan: find commits that touched lines near a function
    definition.
"""

import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class CommitInfo:
    sha: str
    short_sha: str
    author: str
    date: str
    message: str
    files_changed: List[str] = field(default_factory=list)

    def one_line(self) -> str:
        return f"{self.short_sha}  {self.date}  {self.author}  {self.message}"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _run(args: List[str], cwd: str) -> str:
    """Run a git command and return stdout; return '' on failure."""
    try:
        result = subprocess.run(
            args,
            cwd=cwd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=15,
        )
        return result.stdout
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return ""


def _find_repo_root(start: str) -> Optional[str]:
    """Walk up from *start* until a .git directory is found."""
    path = Path(start).resolve()
    for candidate in [path] + list(path.parents):
        if (candidate / ".git").exists():
            return str(candidate)
    return None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_commits_for_file(
    file_path: str,
    repo_root: Optional[str] = None,
    max_commits: int = 20,
) -> List[CommitInfo]:
    """
    Return up to *max_commits* commits that modified *file_path*.
    """
    if repo_root is None:
        repo_root = _find_repo_root(file_path)
    if repo_root is None:
        return []

    # Make the path relative to repo root for git log
    try:
        rel = str(Path(file_path).resolve().relative_to(Path(repo_root).resolve()))
    except ValueError:
        rel = file_path

    # Format: sha|author|date|message  (separated by |)
    fmt = "%H|%an|%ad|%s"
    out = _run(
        ["git", "log", f"--max-count={max_commits}", f"--format={fmt}",
         "--date=short", "--follow", "--", rel],
        cwd=repo_root,
    )

    commits = []
    for line in out.strip().splitlines():
        parts = line.split("|", 3)
        if len(parts) < 4:
            continue
        sha, author, date, message = parts
        ci = CommitInfo(
            sha=sha,
            short_sha=sha[:8],
            author=author,
            date=date,
            message=message,
        )
        commits.append(ci)

    # Attach file list to each commit
    for ci in commits:
        files_out = _run(
            ["git", "diff-tree", "--no-commit-id", "-r", "--name-only", ci.sha],
            cwd=repo_root,
        )
        ci.files_changed = [f for f in files_out.strip().splitlines() if f]

    return commits


def get_diff_for_commit(
    sha: str,
    file_path: str,
    repo_root: str,
) -> str:
    """Return the unified diff for *file_path* in commit *sha*."""
    try:
        rel = str(Path(file_path).resolve().relative_to(Path(repo_root).resolve()))
    except ValueError:
        rel = file_path

    return _run(
        ["git", "show", "--unified=3", f"{sha}", "--", rel],
        cwd=repo_root,
    )


def commits_touching_function(
    func_name: str,
    file_path: str,
    repo_root: Optional[str] = None,
    max_commits: int = 20,
) -> List[CommitInfo]:
    """
    Return commits where the diff for *file_path* mentions *func_name*
    (i.e. lines changed near or within the function definition).

    This is a heuristic: we grep the diff text for the function name string.
    It catches direct modifications and renames reliably for small files.
    """
    all_commits = get_commits_for_file(file_path, repo_root, max_commits)
    if repo_root is None:
        repo_root = _find_repo_root(file_path)
    if repo_root is None:
        return all_commits  # can't filter, return all

    matching = []
    for ci in all_commits:
        diff = get_diff_for_commit(ci.sha, file_path, repo_root)
        # Look for the function name in changed lines (lines starting with + or -)
        for line in diff.splitlines():
            if line.startswith(("+", "-")) and func_name in line:
                matching.append(ci)
                break

    return matching


def get_repo_root(path: str) -> Optional[str]:
    """Public accessor for the repo root detection."""
    return _find_repo_root(path)
