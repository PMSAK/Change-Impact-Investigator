"""
repository.py
~~~~~~~~~~~~~
Repository input handling for Change Impact Investigator.

Supports:
- Existing local repositories/directories
- ZIP archives containing a repository
- GitHub repositories via URL
"""

import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path
from urllib.parse import urlparse


class RepositoryError(Exception):
    """Raised when a repository cannot be loaded."""


def _is_github_url(source: str) -> bool:
    """Return True if source looks like a GitHub repository URL."""
    parsed = urlparse(source)

    return (
        parsed.scheme in ("http", "https")
        and parsed.netloc.lower() in {
            "github.com",
            "www.github.com",
        }
    )


def _run_git_clone(url: str, destination: Path) -> None:
    """Clone a Git repository into destination."""
    try:
        result = subprocess.run(
            ["git", "clone", "--depth", "1", url, str(destination)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=120,
        )
    except FileNotFoundError:
        raise RepositoryError(
            "Git is not installed or is not available on PATH."
        )
    except subprocess.TimeoutExpired:
        raise RepositoryError("Git clone timed out.")

    if result.returncode != 0:
        message = result.stderr.strip() or "Unknown git error."
        raise RepositoryError(f"Failed to clone repository: {message}")


def _find_repository_root(path: Path) -> Path:
    """
    Find the actual repository root.

    This handles ZIP files that contain a single top-level directory,
    such as:

        project.zip
        └── project/
            ├── .git/
            └── app/

    or a normal source directory.
    """
    path = path.resolve()

    if (path / ".git").exists():
        return path

    # If there is exactly one directory inside the supplied directory,
    # check whether that directory is the actual repository root.
    children = list(path.iterdir())

    directories = [child for child in children if child.is_dir()]

    if len(directories) == 1:
        candidate = directories[0]

        if (candidate / ".git").exists():
            return candidate

        # Also allow source-only repositories without .git.
        return candidate

    return path


def prepare_repository(source: str) -> tuple[Path, tempfile.TemporaryDirectory | None]:
    """
    Prepare a repository for analysis.

    Parameters
    ----------
    source:
        One of:
        - local repository directory
        - ZIP archive
        - GitHub repository URL

    Returns
    -------
    (repository_path, temporary_directory)

    temporary_directory is returned so callers can keep the temporary
    repository alive for the duration of the analysis.

    For local repositories, temporary_directory is None.
    """
    source_path = Path(source).expanduser()

    # ---------------------------------------------------------
    # 1. GitHub URL
    # ---------------------------------------------------------
    if _is_github_url(source):
        temp_dir = tempfile.TemporaryDirectory(prefix="impact_repo_")
        clone_path = Path(temp_dir.name) / "repository"

        _run_git_clone(source, clone_path)

        return clone_path, temp_dir

    # ---------------------------------------------------------
    # 2. Local source
    # ---------------------------------------------------------
    if not source_path.exists():
        raise RepositoryError(
            f"Repository source does not exist: {source}"
        )

    # ---------------------------------------------------------
    # 3. ZIP archive
    # ---------------------------------------------------------
    if source_path.is_file() and source_path.suffix.lower() == ".zip":
        temp_dir = tempfile.TemporaryDirectory(prefix="impact_repo_")
        extract_path = Path(temp_dir.name) / "extracted"
        extract_path.mkdir()

        try:
            with zipfile.ZipFile(source_path, "r") as archive:
                for member in archive.infolist():
                    member_path = (extract_path / member.filename).resolve()

                    try:
                        member_path.relative_to(extract_path.resolve())
                    except ValueError:
                        raise RepositoryError(
                            "ZIP archive contains an unsafe path."
                        )

                archive.extractall(extract_path)
        except zipfile.BadZipFile:
            temp_dir.cleanup()
            raise RepositoryError(
                f"Invalid ZIP archive: {source}"
            )

        repository_path = _find_repository_root(extract_path)

        return repository_path, temp_dir

    # ---------------------------------------------------------
    # 4. Local directory
    # ---------------------------------------------------------
    if source_path.is_dir():
        return _find_repository_root(source_path), None

    raise RepositoryError(
        "Unsupported repository source. "
        "Provide a directory, ZIP archive, or GitHub URL."
    )