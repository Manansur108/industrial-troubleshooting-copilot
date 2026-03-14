from __future__ import annotations

from pydantic import BaseModel, Field
from .common import SourceCitation, DocumentInfo


class UploadFileResult(BaseModel):
    file_name: str
    document_id: str
    chunks_created: int


class UploadResponse(BaseModel):
    status: str = 'ok'
    files: list[UploadFileResult]


class AskResponse(BaseModel):
    issue_summary: str
    likely_causes: list[str] = Field(default_factory=list)
    recommended_actions: list[str] = Field(default_factory=list)
    escalation_note: str
    sources: list[SourceCitation] = Field(default_factory=list)


class IncidentSummaryResponse(BaseModel):
    incident_title: str
    summary: str
    likely_root_cause: str
    actions_taken_or_recommended: list[str] = Field(default_factory=list)
    handoff_note: str


class DocumentsResponse(BaseModel):
    documents: list[DocumentInfo] = Field(default_factory=list)
