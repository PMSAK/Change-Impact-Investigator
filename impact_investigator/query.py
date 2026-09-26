"""
query.py

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

    Supported examples:
        "What happens if I change calculate_subtotal in app/pricing.py?"
        "What will break if I modify calculate_total in pricing.py?"
        "What could break if app/pricing.py calculate_subtotal changes?"
        "What happens if I change app/pricing.py calculate_subtotal?"
        "What happens if I modify the calculate_subtotal function?"
        "What happens if I change app/pricing.py?"

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
        r"([A-Za-z0-9_./\\-]+\.py)\b",
        question,
        re.IGNORECASE,
    )

    target_file = file_match.group(1) if file_match else None

    # ---------------------------------------------------------
    # Find function reference
    # ---------------------------------------------------------

    target_func = None

    # Words that should never be interpreted as function names.
    ignored_words = {
        "i",
        "a",
        "an",
        "the",
        "it",
        "this",
        "that",
        "what",
        "could",
        "would",
        "will",
        "if",
        "is",
        "are",
        "was",
        "were",
        "change",
        "changes",
        "changed",
        "modify",
        "modified",
        "edit",
        "edited",
        "update",
        "updated",
        "alter",
        "refactor",
        "break",
        "breaks",
        "happen",
        "function",
        "file",
        "code",
        "anything",
        "something",
    }

    # ---------------------------------------------------------
    # Pattern 1:
    #
    # "calculate_subtotal in app/pricing.py"
    # "function calculate_subtotal in app/pricing.py"
    # ---------------------------------------------------------

    if file_match:
        before_file = question[:file_match.start()]

        func_match = re.search(
            r"\b(?:function\s+)?"
            r"([A-Za-z_][A-Za-z0-9_]*)"
            r"\s+(?:in|inside|within)\s*$",
            before_file,
            re.IGNORECASE,
        )

        if func_match:
            candidate = func_match.group(1)

            if candidate.lower() not in ignored_words:
                target_func = candidate

    # ---------------------------------------------------------
    # Pattern 2:
    #
    # "app/pricing.py calculate_subtotal"
    # "app/pricing.py calculate_subtotal changes"
    # ---------------------------------------------------------

    if target_func is None and file_match:
        after_file = question[file_match.end():].strip()

        func_match = re.match(
            r"^([A-Za-z_][A-Za-z0-9_]*)"
            r"(?:\s+(?:changes?|is\s+changed|is\s+modified|"
            r"is\s+updated))?"
            r"\s*[?.!,]*$",
            after_file,
            re.IGNORECASE,
        )

        if func_match:
            candidate = func_match.group(1)

            if candidate.lower() not in ignored_words:
                target_func = candidate

    # ---------------------------------------------------------
    # Pattern 3:
    #
    # "change calculate_subtotal"
    # "modify calculate_subtotal"
    # "edit calculate_subtotal"
    # "update calculate_subtotal"
    # "refactor calculate_subtotal"
    #
    # IMPORTANT:
    # If a file exists, only inspect the text BEFORE the file.
    #
    # This prevents:
    #
    #   "What happens if I change app/pricing.py?"
    #
    # from interpreting "I" as the function name.
    # ---------------------------------------------------------

    if target_func is None:
        search_text = question

        if file_match:
            search_text = question[:file_match.start()]

        func_match = re.search(
            r"\b(?:change|modify|edit|update|alter|refactor)\s+"
            r"(?:the\s+)?"
            r"(?:function\s+)?"
            r"([A-Za-z_][A-Za-z0-9_]*)\b",
            search_text,
            re.IGNORECASE,
        )

        if func_match:
            candidate = func_match.group(1)

            if candidate.lower() not in ignored_words:
                target_func = candidate

    # ---------------------------------------------------------
    # Pattern 4:
    #
    # "if calculate_subtotal changes"
    # "if calculate_subtotal is changed"
    # "calculate_subtotal changes"
    # ---------------------------------------------------------

    if target_func is None:
        func_match = re.search(
            r"\b([A-Za-z_][A-Za-z0-9_]*)\b"
            r"\s+(?:changes?|is\s+changed|is\s+modified|"
            r"is\s+updated|changes\s+significantly)\b",
            question,
            re.IGNORECASE,
        )

        if func_match:
            candidate = func_match.group(1)

            if candidate.lower() not in ignored_words:
                target_func = candidate

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