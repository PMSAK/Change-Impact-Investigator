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