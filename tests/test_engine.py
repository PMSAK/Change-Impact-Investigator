from unittest.mock import patch

from impact_investigator.engine import analyze_question


@patch(
    "impact_investigator.engine.generate_impact_assessment",
    return_value="Mock AI assessment",
)
def test_analyze_question_local_repository(
    mock_ai,
    tmp_path,
):
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

    query, report, ai_assessment, handle = analyze_question(
        str(repo),
        "What happens if I change calculate_subtotal in app/pricing.py?",
        test_dirs=["tests"],
    )

    try:
        assert query.target_file == "app/pricing.py"
        assert query.target_func == "calculate_subtotal"

        assert report["target_func"] == "calculate_subtotal"

        assert len(report["direct_callers"]) == 1
        assert report["direct_callers"][0].name == "calculate_total"

        assert ai_assessment == "Mock AI assessment"

        assert handle is None

    finally:
        if handle is not None:
            handle.cleanup()