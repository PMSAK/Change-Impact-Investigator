from pathlib import Path
import zipfile

import pytest

from impact_investigator.analyzer import analyze_repository


def create_test_repo(tmp_path):
    repo = tmp_path / "repo"
    app = repo / "app"
    tests = repo / "tests"

    app.mkdir(parents=True)
    tests.mkdir()

    (app / "pricing.py").write_text(
        """
def calculate_subtotal(items):
    total = 0.0
    for item in items:
        total += item["price"] * item["quantity"]
    return round(total, 2)


def calculate_total(items):
    return calculate_subtotal(items)
""",
        encoding="utf-8",
    )

    (tests / "test_pricing.py").write_text(
        """
from app.pricing import calculate_subtotal


def test_subtotal():
    assert calculate_subtotal([
        {"price": 10, "quantity": 2}
    ]) == 20
""",
        encoding="utf-8",
    )

    return repo


def test_analyze_local_repository(tmp_path):
    repo = create_test_repo(tmp_path)

    report, handle = analyze_repository(
        str(repo),
        "app/pricing.py",
        "calculate_subtotal",
        test_dirs=["tests"],
    )

    try:
        assert report["target_func"] == "calculate_subtotal"

        assert report["target_file"].endswith(
            "app\\pricing.py"
        ) or report["target_file"].endswith(
            "app/pricing.py"
        )

        assert len(report["direct_callers"]) == 1
        assert report["direct_callers"][0].name == "calculate_total"

    finally:
        assert handle is None


def test_analyze_zip_repository(tmp_path):
    repo = create_test_repo(tmp_path)

    zip_path = tmp_path / "repo.zip"

    with zipfile.ZipFile(zip_path, "w") as archive:
        for path in repo.rglob("*"):
            if path.is_file():
                archive.write(
                    path,
                    path.relative_to(repo.parent),
                )

    report, handle = analyze_repository(
        str(zip_path),
        "app/pricing.py",
        "calculate_subtotal",
        test_dirs=["tests"],
    )

    try:
        assert report["target_func"] == "calculate_subtotal"
        assert len(report["direct_callers"]) == 1
        assert handle is not None
    finally:
        if handle is not None:
            handle.cleanup()


def test_missing_target_file(tmp_path):
    repo = create_test_repo(tmp_path)

    with pytest.raises(FileNotFoundError):
        analyze_repository(
            str(repo),
            "app/missing.py",
            "calculate_subtotal",
        )


def test_target_cannot_escape_repository(tmp_path):
    repo = create_test_repo(tmp_path)

    with pytest.raises(ValueError):
        analyze_repository(
            str(repo),
            "../outside.py",
            "calculate_subtotal",
        )