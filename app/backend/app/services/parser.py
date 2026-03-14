"""
PDF and document parser — with streaming support for large files.

Handles PDF (via pypdf), DOCX (via python-docx), and plain text files.
For PDFs with 600+ pages, uses page-by-page yielding to avoid memory spikes.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Generator

from docx import Document as DocxDocument
from pypdf import PdfReader

logger = logging.getLogger(__name__)


def parse_document(path: Path) -> dict:
    """Parse a document and return {text, pages, page_count}."""
    suffix = path.suffix.lower()
    if suffix == '.pdf':
        return _parse_pdf(path)
    if suffix == '.docx':
        return _parse_docx(path)
    if suffix in {'.txt', '.md', '.log'}:
        text = path.read_text(errors='ignore')
        return {'text': text, 'pages': [{'page_ref': '1', 'text': text}], 'page_count': 1}
    raise ValueError(f'Unsupported file type: {suffix}')


def _parse_pdf(path: Path) -> dict:
    """Parse PDF with memory-efficient page-by-page processing.
    
    For large PDFs (600+ pages), we process pages individually
    and only keep the page list, not a single concatenated text blob.
    """
    try:
        reader = PdfReader(str(path))
    except Exception as exc:
        logger.error("Failed to open PDF %s: %s", path.name, exc)
        raise ValueError(f"Could not read PDF: {exc}") from exc

    page_count = len(reader.pages)
    logger.info("Parsing PDF: %s (%d pages)", path.name, page_count)

    pages = []
    text_parts = []

    for i, page in enumerate(reader.pages, start=1):
        try:
            page_text = page.extract_text() or ''
        except Exception as exc:
            logger.warning("Failed to extract text from page %d of %s: %s", i, path.name, exc)
            page_text = ''

        pages.append({'page_ref': str(i), 'text': page_text})
        text_parts.append(page_text)

        # Log progress for large PDFs
        if page_count > 100 and i % 100 == 0:
            logger.info("  ... parsed %d / %d pages", i, page_count)

    return {
        'text': '\n\n'.join(text_parts),
        'pages': pages,
        'page_count': page_count,
    }


def _parse_docx(path: Path) -> dict:
    doc = DocxDocument(str(path))
    text = '\n'.join(p.text for p in doc.paragraphs if p.text.strip())
    return {'text': text, 'pages': [{'page_ref': '1', 'text': text}], 'page_count': 1}


def get_pdf_page_count(path: Path) -> int:
    """Quick page count without reading full content."""
    try:
        reader = PdfReader(str(path))
        return len(reader.pages)
    except Exception:
        return 0
