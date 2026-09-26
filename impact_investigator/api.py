"""
api.py
~~~~~~

HTTP API for Change Impact Investigator.

The API accepts:
    - a repository source (local path or GitHub URL)
    - a natural-language impact question

and returns:
    - deterministic analyzer evidence
    - OpenAI-generated impact assessment
"""

from typing import Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from impact_investigator.engine import analyze_question
from impact_investigator.serialization import report_to_json


app = FastAPI(
    title="Change Impact Investigator",
    description="AI-powered software change impact analysis",
    version="0.1.0",
)


class AnalyzeRequest(BaseModel):
    source: str
    question: str
    test_dirs: Optional[list[str]] = None


@app.get("/")
def root():
    return {
        "name": "Change Impact Investigator",
        "status": "running",
    }


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/analyze")
def analyze(request: AnalyzeRequest):
    try:
        query, report, ai_answer, repository_handle = (
            analyze_question(
                source=request.source,
                question=request.question,
                test_dirs=request.test_dirs,
            )
        )

        try:
            return {
                "question": query.raw_question,
                "target_file": query.target_file,
                "target_function": query.target_func,
                "evidence": report_to_json(report),
                "assessment": ai_answer,
            }

        finally:
            if repository_handle is not None:
                repository_handle.cleanup()

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )