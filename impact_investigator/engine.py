"""
engine.py
~~~~~~~~~
High-level orchestration for Change Impact Investigator.

Connects:
    natural-language query
        -> repository loading
        -> repository analysis
        -> structured impact report
"""

from typing import Optional

from impact_investigator.query import AnalysisQuery, parse_query
from impact_investigator.analyzer import analyze_repository

from impact_investigator.ai import analyze_with_ai


def analyze_question(
    source: str,
    question: str,
    test_dirs: Optional[list[str]] = None,
):
    """
    Analyze a natural-language impact question against a repository.

    Parameters
    ----------
    source:
        Local repository, ZIP archive, or GitHub repository URL.

    question:
        Natural-language question such as:

        "What happens if I change calculate_subtotal in app/pricing.py?"

    test_dirs:
        Optional repository-relative test directories.

    Returns
    -------
    tuple
        (query, report, repository_handle)

    The repository handle must remain alive while the report is being used.
    Call handle.cleanup() when finished if it is not None.
    """

    # ---------------------------------------------------------
    # 1. Parse the user's question
    # ---------------------------------------------------------

    query: AnalysisQuery = parse_query(question)

    # parse_query() guarantees that a valid target file exists,
    # but the type checker cannot infer that from the function.
    if query.target_file is None:
        raise ValueError("No target file found in query.")

    # ---------------------------------------------------------
    # 2. Analyze the requested repository target
    # ---------------------------------------------------------

    report, repository_handle = analyze_repository(
        source=source,
        target_file=query.target_file,
        target_func=query.target_func,
        test_dirs=test_dirs,
    )

    # ---------------------------------------------------------
    # 3. Return both the parsed query and evidence report
    # ---------------------------------------------------------

    return query, report, repository_handle

def analyze_question_with_ai(
    source: str,
    question: str,
    test_dirs: Optional[list[str]] = None,
):
    """
    Analyze a repository question and generate an AI-assisted explanation.

    Returns
    -------
    tuple
        (query, report, ai_answer, repository_handle)
    """

    query, report, repository_handle = analyze_question(
        source=source,
        question=question,
        test_dirs=test_dirs,
    )

    try:
        ai_answer = analyze_with_ai(
            question=question,
            report=report,
        )
    except Exception:
        if repository_handle is not None:
            repository_handle.cleanup()
        raise

    return query, report, ai_answer, repository_handle