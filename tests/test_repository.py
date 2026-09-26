import zipfile
from pathlib import Path

import pytest

from impact_investigator.repository import (
    RepositoryError,
    _is_github_url,
    prepare_repository,
)


def test_is_github_url():
    assert _is_github_url(
        "https://github.com/example/project"
    )

    assert _is_github_url(
        "https://www.github.com/example/project"
    )

    assert not _is_github_url(
        "https://google.com/example/project"
    )


def test_prepare_local_repository(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()

    (repo / "app.py").write_text(
        "def hello():\n    return 'hello'\n",
        encoding="utf-8",
    )

    result, temp_dir = prepare_repository(str(repo))

    assert result == repo.resolve()
    assert temp_dir is None
    assert (result / "app.py").exists()


def test_prepare_zip_repository(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()

    (repo / "app.py").write_text(
        "def hello():\n    return 'hello'\n",
        encoding="utf-8",
    )

    zip_path = tmp_path / "repo.zip"

    with zipfile.ZipFile(zip_path, "w") as archive:
        archive.write(
            repo / "app.py",
            "repo/app.py",
        )

    result, temp_dir = prepare_repository(str(zip_path))

    try:
        assert result.exists()
        assert (result / "app.py").exists()
        assert temp_dir is not None
    finally:
        if temp_dir is not None:
            temp_dir.cleanup()


def test_missing_source_raises_error(tmp_path):
    missing = tmp_path / "does_not_exist"

    with pytest.raises(RepositoryError):
        prepare_repository(str(missing))


def test_unsupported_file_raises_error(tmp_path):
    file_path = tmp_path / "file.txt"
    file_path.write_text("hello", encoding="utf-8")

    with pytest.raises(RepositoryError):
        prepare_repository(str(file_path))