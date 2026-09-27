"""
ai_assessment.py

OpenAI-powered reasoning layer for Change Impact Investigator.

The deterministic analyzer produces the evidence.

This module interprets that evidence and produces a human-readable
impact assessment.
"""

import json
import os
from typing import Any

from impact_investigator.serialization import report_to_json

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()


SYSTEM_PROMPT = """
You are the reasoning layer of Change Impact Investigator.

Your job is to interpret software-change impact evidence produced by a
deterministic repository analyzer.

Rules:

1. Treat the supplied analyzer evidence as the source of truth.
2. Do not invent callers, tests, dependencies, files, or repository behavior.
3. Clearly distinguish confirmed evidence from reasonable inference.
4. If the evidence is insufficient, explicitly say so.
5. Do not claim a dependency exists unless the analyzer found evidence for it.
6. Explain why each identified component could be affected.
7. Use Git history only as contextual evidence, not proof of runtime behavior.
8. Mention test and coverage evidence when available.
9. Recommend practical next checks when appropriate.
10. Do not modify the repository.
11. Keep the assessment concise and developer-friendly.

Structure the response as:

## Impact Summary

A short explanation of the likely impact.

## Confirmed Impact

List components that the analyzer directly or indirectly identified.

## Evidence

Summarize callers, tests, coverage, Git history, and other relevant evidence.

## Potential Risks

Explain what could go wrong, clearly distinguishing inference from
confirmed dependencies.

## Recommended Checks

Give practical tests or investigation steps.

Never invent evidence that is not present in the supplied report.
"""


def _serialize_report(report: dict[str, Any]) -> dict[str, Any]:
    """
    Convert the analyzer report into JSON-safe data.
    """

    return report_to_json(report)


def generate_impact_assessment(
    question: str,
    report: dict[str, Any],
) -> str:
    """
    Generate an AI impact assessment from deterministic analyzer evidence.
    """

    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        raise RuntimeError(
            "OPENAI_API_KEY is not set. "
            "Please configure your OpenAI API key before running "
            "the AI impact assessment."
        )

    client = OpenAI(api_key=api_key)

    evidence = {
        "question": question,
        "report": _serialize_report(report),
    }

    response = client.responses.create(
        model="gpt-5-mini",
        instructions=SYSTEM_PROMPT,
        input=(
            "Analyze the following Change Impact Investigator evidence.\n\n"
            + json.dumps(evidence, indent=2)
        ),
    )

    return response.output_text