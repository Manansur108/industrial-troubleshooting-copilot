from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel

from app.backend.app.core.config import PROCESSED_DIR, UPLOAD_DIR
from app.backend.app.schemas.common import DocumentInfo
from app.backend.app.schemas.requests import AskRequest, IncidentSummaryRequest
from app.backend.app.schemas.responses import AskResponse, DocumentsResponse, IncidentSummaryResponse, UploadFileResult, UploadResponse
from app.backend.app.services.answer_engine import build_answer
from app.backend.app.services.chunker import chunk_pages
from app.backend.app.services.parser import parse_document
from app.backend.app.services.retriever import retrieve_relevant_chunks
from app.backend.app.services.summarizer import build_incident_summary
from app.backend.app.services.vector_store import LocalVectorStore
from app.backend.app.services.llm_provider import (
    get_ollama_provider,
    runtime_config,
)

router = APIRouter(prefix='/api')
_ALLOWED = {'.pdf', '.docx', '.txt', '.md', '.log'}


# ---------------------------------------------------------------------------
# Document management
# ---------------------------------------------------------------------------
@router.post('/upload', response_model=UploadResponse)
async def upload_documents(files: list[UploadFile] = File(...)) -> UploadResponse:
    import logging
    logger = logging.getLogger(__name__)
    results: list[UploadFileResult] = []
    store = LocalVectorStore()

    for file in files:
        suffix = Path(file.filename or '').suffix.lower()
        if suffix not in _ALLOWED:
            raise HTTPException(status_code=400, detail=f'Unsupported file type: {suffix}')

        document_id = f'doc_{uuid4().hex[:12]}'
        saved_path = UPLOAD_DIR / f'{document_id}{suffix}'

        # Save uploaded file to disk
        try:
            content = await file.read()
            saved_path.write_bytes(content)
        except Exception as exc:
            logger.error("Failed to save uploaded file %s: %s", file.filename, exc)
            raise HTTPException(status_code=500, detail=f'Failed to save file: {file.filename}')

        # Parse and chunk the document
        try:
            parsed = parse_document(saved_path)
            chunks = chunk_pages(parsed['pages'])
        except Exception as exc:
            logger.error("Failed to parse %s: %s", file.filename, exc, exc_info=True)
            # Clean up the saved file
            if saved_path.exists():
                saved_path.unlink()
            raise HTTPException(status_code=422, detail=f'Failed to parse {file.filename}: {str(exc)}')

        doc_info = DocumentInfo(
            document_id=document_id,
            file_name=file.filename or saved_path.name,
            source_type=suffix.lstrip('.'),
            uploaded_at=datetime.now(timezone.utc).isoformat(),
            page_count=parsed.get('page_count', len(parsed['pages'])),
            chunk_count=len(chunks),
            status='processed',
        )

        processed_doc_path = PROCESSED_DIR / f'{document_id}.txt'
        processed_doc_path.write_text(parsed['text'])
        store.upsert_document(doc_info.model_dump(), chunks)
        results.append(UploadFileResult(file_name=doc_info.file_name, document_id=document_id, chunks_created=len(chunks)))

    return UploadResponse(files=results)


@router.post('/ask', response_model=AskResponse)
def ask_question(payload: AskRequest) -> AskResponse:
    chunks = retrieve_relevant_chunks(payload.question, top_k=payload.top_k)
    return build_answer(payload.question, chunks)


@router.post('/incident-summary', response_model=IncidentSummaryResponse)
def incident_summary(payload: IncidentSummaryRequest) -> IncidentSummaryResponse:
    return build_incident_summary(payload)


@router.get('/documents', response_model=DocumentsResponse)
def list_documents() -> DocumentsResponse:
    store = LocalVectorStore()
    docs = [DocumentInfo(**doc) for doc in store.list_documents()]
    docs.sort(key=lambda x: x.uploaded_at, reverse=True)
    return DocumentsResponse(documents=docs)


@router.delete('/documents/{document_id}')
def delete_document(document_id: str) -> dict:
    store = LocalVectorStore()
    doc = store.get_document(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail='Document not found')
    store.delete_document(document_id)

    for path in [UPLOAD_DIR / f'{document_id}.pdf', UPLOAD_DIR / f'{document_id}.docx', UPLOAD_DIR / f'{document_id}.txt', UPLOAD_DIR / f'{document_id}.md', UPLOAD_DIR / f'{document_id}.log', PROCESSED_DIR / f'{document_id}.txt']:
        if path.exists():
            path.unlink()
    return {'status': 'deleted', 'document_id': document_id}


# ---------------------------------------------------------------------------
# LLM configuration
# ---------------------------------------------------------------------------
class LLMConfigUpdate(BaseModel):
    provider: str | None = None
    ollama_base_url: str | None = None
    ollama_model: str | None = None
    openai_model: str | None = None


@router.get('/llm-config')
def get_llm_config() -> dict:
    """Return the current LLM provider configuration."""
    cfg = runtime_config.to_dict()
    # Also check if Ollama is reachable
    try:
        ollama = get_ollama_provider()
        cfg['ollama_available'] = ollama.is_available()
    except Exception:
        cfg['ollama_available'] = False
    return cfg


@router.post('/llm-config')
def update_llm_config(payload: LLMConfigUpdate) -> dict:
    """Update the LLM provider configuration at runtime."""
    updates = payload.model_dump(exclude_none=True)
    if 'provider' in updates and updates['provider'] not in ('ollama', 'openai'):
        raise HTTPException(status_code=400, detail='Provider must be "ollama" or "openai"')
    runtime_config.update(**updates)
    return {'status': 'updated', **runtime_config.to_dict()}


@router.get('/llm-models')
def list_ollama_models() -> dict:
    """List available Ollama models."""
    try:
        ollama = get_ollama_provider()
        models = ollama.list_models()
        return {'models': models}
    except Exception:
        return {'models': []}
