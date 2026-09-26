"""
engine.py
~~~~~~~~~

High-level orchestration for Change Impact Investigator.

Connects:

    natural-language query
        -> repository loading
        -> repository analysis
        -> structured impact report
        -> AI impact assessment
"""

from typing import Optional

from impact_investigator.query import AnalysisQuery, parse_query
from impact_investigator.analyzer import analyze_repository
from impact_investigator.ai_assessment import generate_impact_assessment


def analyze_question(
    source: str,
    question: str,
    test_dirs: Optional[list[str]] = None,
):
    """
    Analyze a natural-language impact question against a repository.

    Returns:
        (query, report, ai_assessment, repository_handle)
    """

    # ---------------------------------------------------------
    # 1. Parse the user's question
    # ---------------------------------------------------------

    query: AnalysisQuery = parse_query(question)

    if query.target_file is None:
        raise ValueError("No target file found in query.")

    # ---------------------------------------------------------
    # 2. Analyze the repository
    # ---------------------------------------------------------

    report, repository_handle = analyze_repository(
        source=source,
        target_file=query.target_file,
        target_func=query.target_func,
        test_dirs=test_dirs,
    )

    # ---------------------------------------------------------
    # 3. Generate AI assessment
    # ---------------------------------------------------------

    ai_assessment = generate_impact_assessment(
        question=question,
        report=report,
    )

    # ---------------------------------------------------------
    # 4. Return everything
    # ---------------------------------------------------------

    return (
        query,
        report,
        ai_assessment,
        repository_handle,
    )