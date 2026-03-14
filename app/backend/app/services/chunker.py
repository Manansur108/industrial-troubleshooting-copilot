"""
Chunker — splits document pages into overlapping text chunks.

Supports configurable chunk size and overlap. Processes pages
sequentially so large documents (600+ pages) don't require
holding the full text in memory at once.
"""
from __future__ import annotations


def chunk_pages(
    pages: list[dict],
    chunk_size: int = 900,
    chunk_overlap: int = 120,
) -> list[dict]:
    """Split pages into overlapping chunks.
    
    Each chunk carries its page_ref for citation purposes.
    For very large documents, this processes one page at a time.
    """
    chunks: list[dict] = []
    index = 0

    for page in pages:
        text = _normalize(page.get('text', ''))
        if not text:
            continue

        page_ref = page.get('page_ref')
        start = 0

        while start < len(text):
            end = min(len(text), start + chunk_size)
            chunk_text = text[start:end].strip()

            if chunk_text:
                chunks.append({
                    'chunk_index': index,
                    'page_ref': page_ref,
                    'text': chunk_text,
                })
                index += 1

            if end >= len(text):
                break
            start = max(0, end - chunk_overlap)

    return chunks


def _normalize(text: str) -> str:
    """Collapse whitespace for cleaner chunks."""
    return ' '.join((text or '').split())
