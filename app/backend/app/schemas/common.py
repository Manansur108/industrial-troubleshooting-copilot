from __future__ import annotations

from typing import Any
from pydantic import BaseModel, Field


class SourceCitation(BaseModel):
    document: str
    chunk_id: str
    excerpt: str
    page_ref: str | None = None
    score: float | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class DocumentInfo(BaseModel):
    document_id: str
    file_name: str
    source_type: str
    uploaded_at: str
    page_count: int = 0
    chunk_count: int = 0
    status: str = 'processed'
