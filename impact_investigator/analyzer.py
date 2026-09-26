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
    # Resolve target file safely inside repository
    # ---------------------------------------------------------

    target_path = (repository_root / target_file).resolve()

    try:
        target_path.relative_to(repository_root.resolve())
    except ValueError:
        if repository_handle is not None:
            repository_handle.cleanup()

        raise ValueError(
            "Target file must be located inside the repository."
        )

    if not target_path.exists():
        if repository_handle is not None:
            repository_handle.cleanup()

        raise FileNotFoundError(
            f"Target file not found in repository: {target_file}"
        )

    if not target_path.is_file():
        if repository_handle is not None:
            repository_handle.cleanup()

        raise ValueError(
            f"Target path is not a file: {target_file}"
        )

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

    return report, repository_handle