import json
from openai import OpenAI


SYSTEM_PROMPT = """
You are the AI reasoning layer of Change Impact Investigator.

You receive a developer's question and evidence produced by a
deterministic code-impact analysis system.

Your job is to explain the impact of the change using the supplied
evidence.

Rules:
- Use only the evidence provided by the analyzer.
- Do not invent callers, dependencies, tests, Git history, or bugs.
- Clearly distinguish confirmed evidence from reasonable implications.
- If the evidence is insufficient to answer something, say so.
- Focus on what the developer should investigate or test next.
- Be concise but technically useful.
"""


def analyze_with_ai(question: str, report: dict) -> str:
    """
    Use OpenAI to explain a deterministic impact-analysis report.
    """

    client = OpenAI()

    response = client.responses.create(
        model="gpt-5.6-luna",
        instructions=SYSTEM_PROMPT,
        input=json.dumps(
            {
                "question": question,
                "impact_report": report,
            },
            indent=2,
            default=str,
        ),
    )

    return response.output_text