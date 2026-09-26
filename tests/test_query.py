import pytest

from impact_investigator.query import (
    AnalysisQuery,
    parse_query,
)


def test_parse_function_and_file():
    query = parse_query(
        "What happens if I change calculate_subtotal in app/pricing.py?"
    )

    assert query.target_file == "app/pricing.py"
    assert query.target_func == "calculate_subtotal"


def test_parse_modify_function():
    query = parse_query(
        "What will break if I modify calculate_total in pricing.py?"
    )

    assert query.target_file == "pricing.py"
    assert query.target_func == "calculate_total"


def test_parse_file_without_function():
    query = parse_query(
        "What happens if I change app/pricing.py?"
    )

    assert query.target_file == "app/pricing.py"
    assert query.target_func is None


def test_empty_question():
    with pytest.raises(ValueError):
        parse_query("")


def test_missing_file():
    with pytest.raises(ValueError):
        parse_query(
            "What happens if I change calculate_subtotal?"
        )