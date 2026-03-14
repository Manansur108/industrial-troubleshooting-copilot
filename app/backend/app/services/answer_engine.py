"""
Answer engine — generates troubleshooting answers from retrieved chunks.

Uses the configured LLM provider (Ollama by default) with a structured
system prompt. Falls back to rule-based heuristics if the LLM is unavailable.
"""
from __future__ import annotations

import logging

from app.backend.app.schemas.responses import AskResponse
from app.backend.app.schemas.common import SourceCitation
from app.backend.app.services.llm_provider import get_provider, parse_json_response

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an expert industrial troubleshooting assistant. \
Given a technician's question and relevant excerpts from technical documents \
(manuals, SOPs, alarm guides), produce a structured JSON answer.

Return ONLY valid JSON with these exact keys:
{
  "issue_summary": "One-line summary of the issue",
  "likely_causes": ["cause 1", "cause 2", ...],
  "recommended_actions": ["action 1", "action 2", ...],
  "escalation_note": "When to escalate this issue"
}

Rules:
- Base your answer strictly on the provided document excerpts.
- Be specific and actionable — reference equipment names, fault codes, procedure steps.
- Keep likely_causes to 3-5 items max.
- Keep recommended_actions to 3-5 items max.
- If the excerpts don't contain enough information, say so honestly.
"""

# --- Heuristic fallbacks (used when LLM is unavailable) ---
CAUSE_HINTS = [
    'safety interlock open',
    'overload relay trip',
    'fault code still active',
    'sensor not detected',
    'communication loss',
    'power supply issue',
]

ACTION_HINTS = [
    'Verify relevant safety and interlock conditions.',
    'Check active alarms, fault codes, and reset state.',
    'Inspect sensor status, wiring, and device feedback.',
    'Compare observed behavior against the cited procedure/manual steps.',
]


def build_answer(question: str, chunks: list[dict]) -> AskResponse:
    """Build a troubleshooting answer — tries LLM first, falls back to heuristics."""
    if not chunks:
        return AskResponse(
            issue_summary=_titleize(question),
            likely_causes=['No matching evidence found in uploaded documents.'],
            recommended_actions=['Upload relevant manuals, SOPs, or alarm guides and re-run the query.'],
            escalation_note='Do not rely on AI guidance alone when no supporting source was found.',
            sources=[],
        )

    # Build citations from top chunks
    citations = _build_citations(chunks)

    # Try LLM-powered answer
    try:
        provider = get_provider()
        if provider.is_available():
            context = _format_context(chunks[:5])
            prompt = f"Question: {question}\n\nDocument Excerpts:\n{context}"
            raw = provider.generate(prompt, system_prompt=SYSTEM_PROMPT)
            parsed = parse_json_response(raw)

            if parsed and "issue_summary" in parsed:
                return AskResponse(
                    issue_summary=parsed.get("issue_summary", _titleize(question)),
                    likely_causes=parsed.get("likely_causes", [])[:5],
                    recommended_actions=parsed.get("recommended_actions", [])[:5],
                    escalation_note=parsed.get("escalation_note", "Escalate if the issue persists after following the recommended actions."),
                    sources=citations,
                )
            logger.warning("LLM response did not contain expected keys, falling back to heuristics")
    except Exception as exc:
        logger.warning("LLM call failed, falling back to heuristics: %s", exc)

    # Heuristic fallback
    return _heuristic_answer(question, chunks, citations)


def _build_citations(chunks: list[dict]) -> list[SourceCitation]:
    citations = []
    for chunk in chunks[:3]:
        excerpt = chunk['text'][:260].strip()
        citations.append(SourceCitation(
            document=chunk['file_name'],
            chunk_id=f"{chunk['document_id']}:{chunk['chunk_index']}",
            excerpt=excerpt,
            page_ref=chunk.get('page_ref'),
            score=chunk.get('score'),
            metadata={'document_id': chunk['document_id']},
        ))
    return citations


def _format_context(chunks: list[dict]) -> str:
    parts = []
    for i, chunk in enumerate(chunks, 1):
        source = chunk.get('file_name', 'Unknown')
        page = chunk.get('page_ref', 'N/A')
        parts.append(f"[Excerpt {i} — {source}, Page {page}]\n{chunk['text'][:500]}\n")
    return "\n".join(parts)


def _heuristic_answer(question: str, chunks: list[dict], citations: list[SourceCitation]) -> AskResponse:
    likely_causes = _derive_causes(question, chunks)
    recommended_actions = _derive_actions(question, chunks)

    return AskResponse(
        issue_summary=_titleize(question),
        likely_causes=likely_causes[:4],
        recommended_actions=recommended_actions[:4],
        escalation_note='Escalate if commanded behavior is present but the physical output, device state, or safety condition does not match expected operation.',
        sources=citations,
    )


def _titleize(question: str) -> str:
    cleaned = question.strip().rstrip('?')
    return cleaned[:1].upper() + cleaned[1:]


def _derive_causes(question: str, chunks: list[dict]) -> list[str]:
    text = ' '.join(chunk['text'].lower() for chunk in chunks[:4])
    causes = []
    mapping = {
        'motor': ['Motor overload or starter fault', 'Safety permissive not satisfied'],
        'sensor': ['Sensor alignment, power, or wiring issue', 'Interlock condition not met'],
        'alarm': ['Active fault condition still latched', 'Alarm reset condition not satisfied'],
        'vfd': ['Drive fault or parameter mismatch', 'Run enable condition missing'],
        'conveyor': ['Safety chain or device interlock preventing start', 'Motor starter or drive condition preventing run'],
    }
    q = question.lower()
    for key, vals in mapping.items():
        if key in q or key in text:
            causes.extend(vals)
    if not causes:
        causes.extend(['Procedure mismatch or missing permissive', 'Device state not matching expected sequence'])
    return list(dict.fromkeys(causes))


def _derive_actions(question: str, chunks: list[dict]) -> list[str]:
    text = ' '.join(chunk['text'].lower() for chunk in chunks[:4])
    actions = []
    if any(k in question.lower() or k in text for k in ['alarm', 'fault', 'vfd']):
        actions.append('Review active alarms/faults and confirm all reset conditions are cleared.')
    if any(k in question.lower() or k in text for k in ['motor', 'conveyor', 'start']):
        actions.append('Verify run permissives, starter/drive status, and output command path.')
    if any(k in question.lower() or k in text for k in ['sensor', 'photoeye', 'barcode']):
        actions.append('Check sensor power, alignment, feedback state, and related interlocks.')
    actions.extend([a for a in ACTION_HINTS if a not in actions])
    return list(dict.fromkeys(actions))
