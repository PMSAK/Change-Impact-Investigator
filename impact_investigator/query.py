"""
query.py
~~~~~~~~
Natural-language query parsing for Change Impact Investigator.

Converts questions such as:

    "What happens if I change calculate_subtotal in app/pricing.py?"

into structured analysis targets.
"""

import re
from dataclasses import dataclass
from typing import Optional


@dataclass
class AnalysisQuery:
    """Structured representation of a user's impact-analysis question."""

    target_file: Optional[str] = None
    target_func: Optional[str] = None
    raw_question: str = ""


def parse_query(question: str) -> AnalysisQuery:
    """
    Parse a natural-language impact-analysis question.

    Currently supports explicit file/function references such as:

        "What happens if I change calculate_subtotal in app/pricing.py?"

        "What will break if I modify calculate_total in pricing.py?"

    Raises
    ------
    ValueError
        If a target file cannot be identified.
    """

    if not question or not question.strip():
        raise ValueError("Question cannot be empty.")

    question = question.strip()

    # ---------------------------------------------------------
    # Find Python file reference
    # ---------------------------------------------------------

    file_match = re.search(
        r"([A-Za-z0-9_./\\-]+\.py)",
        question,
        re.IGNORECASE,
    )

    target_file = file_match.group(1) if file_match else None

    # ---------------------------------------------------------
    # Find function reference
    # ---------------------------------------------------------

    target_func = None

    if file_match:
        before_file = question[:file_match.start()]

        func_match = re.search(
            r"\b(?:function\s+)?"
            r"([A-Za-z_][A-Za-z0-9_]*)"
            r"\s+"
            r"(?:in|inside|within)\s*$",
            before_file,
            re.IGNORECASE,
        )

        if func_match:
            target_func = func_match.group(1)

        # ---------------------------------------------------------
        # Fallback: look for function after an action word
        # ---------------------------------------------------------

        if target_func is None and not file_match:
            func_match = re.search(
                r"\b(?:change|modify|edit|update|alter|refactor)"
                r"\s+"
                r"(?:the\s+)?"
                r"(?:function\s+)?"
                r"([A-Za-z_][A-Za-z0-9_]*)\b",
                question,
                re.IGNORECASE,
            )

            if func_match:
                target_func = func_match.group(1)

    # ---------------------------------------------------------
    # Validate
    # ---------------------------------------------------------

    if target_file is None:
        raise ValueError(
            "Could not identify a Python target file in the question."
        )

    return AnalysisQuery(
        target_file=target_file,
        target_func=target_func,
        raw_question=question,
    )