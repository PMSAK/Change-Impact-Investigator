"""
analyzer.py
~~~~~~~~~~
High-level analysis interface.

Connects repository inputs to the existing impact-reporting engine.
"""

from pathlib import Path
from typing import Optional
import tempfile

from impact_investigator.reporter import build_report
from impact_investigator.repository import (
    prepare_repository,
)

def _resolve_target_file(repository_root: Path, target_file: str) -> Path:
    """
    Resolve a user-provided target file inside the repository.

    Supports both:
        app/pricing.py
    and:
        demo_project/app/pricing.py

    when the latter is the actual repository path.
    """

    repository_root = repository_root.resolve()

    # Normalize Windows-style paths.
    normalized_target = target_file.replace("\\", "/").lstrip("./")

    # ---------------------------------------------------------
    # 1. Exact repository-relative path
    # ---------------------------------------------------------

    direct_path = (repository_root / normalized_target).resolve()

    try:
        direct_path.relative_to(repository_root)
    except ValueError:
        direct_path = None

    if (
        direct_path is not None
        and direct_path.exists()
        and direct_path.is_file()
    ):
        return direct_path

    # ---------------------------------------------------------
    # 2. Search for a unique suffix match
    #
    # Example:
    # app/pricing.py
    #
    # matches:
    # demo_project/app/pricing.py
    # ---------------------------------------------------------

    matches = []

    for path in repository_root.rglob(Path(normalized_target).name):
        if not path.is_file():
            continue

        relative_path = path.relative_to(repository_root).as_posix()

        if relative_path.endswith("/" + normalized_target):
            matches.append(path)

    if len(matches) == 1:
        return matches[0]

    if len(matches) > 1:
        candidates = "\n".join(
            f"  - {path.relative_to(repository_root)}"
            for path in matches
        )

        raise ValueError(
            f"Multiple files match '{target_file}':\n"
            f"{candidates}\n"
            "Please specify the full repository-relative path."
        )

    raise FileNotFoundError(
        f"Target file not found in repository: {target_file}"
    )

def _to_repo_relative(path: str, repository_root: Path) -> str:
    """Return a repository-relative path without exposing local filesystem paths."""
    try:
        return (
            Path(path)
            .resolve()
            .relative_to(repository_root.resolve())
            .as_posix()
        )
    except ValueError:
        return "<outside repository>"


def _sanitize_report_paths(
    report: dict,
    repository_root: Path,
) -> dict:
    """Remove machine-specific repository paths from the public report."""

    report["target_file"] = _to_repo_relative(
        report["target_file"],
        repository_root,
    )

    for key in ("direct_callers", "direct_callees"):
        for info in report.get(key, []):
            info.file_path = _to_repo_relative(
                info.file_path,
                repository_root,
            )

    for infos in report.get("indirect_callers", {}).values():
        for info in infos:
            info.file_path = _to_repo_relative(
                info.file_path,
                repository_root,
            )

    for test in report.get("related_tests", []):
        test.file_path = _to_repo_relative(
            test.file_path,
            repository_root,
        )

    # Test execution output can also contain the temporary repository path.
    test_results = report.get("test_results") or {}

    if "output" in test_results:
        root_text = str(repository_root.resolve())
        output = str(test_results["output"])

        test_results["output"] = output.replace(
            root_text,
            ".",
        )

        test_results["output"] = test_results["output"].replace(
            root_text.replace("\\", "/"),
            ".",
        )

    report["test_results"] = test_results

    return report


def analyze_repository(
    source: str,
    target_file: str,
    target_func: Optional[str] = None,
    test_dirs: Optional[list[str]] = None,
) -> tuple[dict, tempfile.TemporaryDirectory | None]:
    """
    Analyze a function or file inside a repository.

    Parameters
    ----------
    source:
        Local repository path, ZIP archive, or GitHub URL.

    target_file:
        Repository-relative path to the target Python file.

    target_func:
        Optional function name.

    test_dirs:
        Optional repository-relative test directories.

    Returns
    -------
    (report, repository_handle)

    repository_handle must remain alive while the report is being used.
    For local repositories it is None.
    For temporary repositories it owns the temporary directory.
    """

    repository_root, repository_handle = prepare_repository(source)

    # ---------------------------------------------------------
    # Resolve target file inside repository
    # ---------------------------------------------------------

    try:
        target_path = _resolve_target_file(
            repository_root,
            target_file,
        )
    except (FileNotFoundError, ValueError):
        if repository_handle is not None:
            repository_handle.cleanup()
        raise

    # ---------------------------------------------------------
    # Resolve test directories
    # ---------------------------------------------------------

    resolved_test_dirs = None

    if test_dirs:
        resolved_test_dirs = []

        for test_dir in test_dirs:
            test_path = (repository_root / test_dir).resolve()

            try:
                test_path.relative_to(repository_root.resolve())
            except ValueError:
                if repository_handle is not None:
                    repository_handle.cleanup()

                raise ValueError(
                    "Test directory must be located inside the repository."
                )

            resolved_test_dirs.append(str(test_path))

    # ---------------------------------------------------------
    # Run existing impact analysis
    # ---------------------------------------------------------

    report = build_report(
        target_path=str(target_path),
        target_func=target_func,
        project_root=str(repository_root),
        test_dirs=resolved_test_dirs,
    )

    # Keep absolute paths internal only.
    # The returned report is passed to the UI, API, and AI layer,
    # so expose repository-relative paths instead.
    report = _sanitize_report_paths(
        report,
        repository_root,
    )

    return report, repository_handle