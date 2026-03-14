from __future__ import annotations

from pydantic import BaseModel, Field


class AskRequest(BaseModel):
    question: str = Field(min_length=3)
    top_k: int = Field(default=5, ge=1, le=12)


class IncidentSummaryRequest(BaseModel):
    question: str = Field(min_length=3)
    answer_context: dict | None = None
