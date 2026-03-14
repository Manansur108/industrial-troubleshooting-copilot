"""
Incident summary generator — produces handoff summaries.

Uses the configured LLM provider for AI-powered summaries.
Falls back to rule-based generation if LLM is unavailable.
"""
from __future__ import annotations

import logging

from app.backend.app.schemas.requests import IncidentSummaryRequest
from app.backend.app.schemas.responses import IncidentSummaryResponse
from app.backend.app.services.llm_provider import get_provider, parse_json_response

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an industrial incident documentation specialist. \
Given a troubleshooting question and its answer context, produce a structured \
incident handoff summary as JSON.

Return ONLY valid JSON with these exact keys:
{
  "incident_title": "Brief title for the incident",
  "summary": "1-2 sentence summary of the situation and investigation",
  "likely_root_cause": "Most probable root cause",
  "actions_taken_or_recommended": ["action 1", "action 2", ...],
  "handoff_note": "Instructions for next shift / team"
}

Rules:
- Be concise and professional.
- Focus on actionable handoff information.
- Keep actions_taken_or_recommended to 3-5 items.
"""


def build_incident_summary(payload: IncidentSummaryRequest) -> IncidentSummaryResponse:
    """Build an incident summary — tries LLM first, falls back to heuristics."""
    ctx = payload.answer_context or {}

    # Try LLM-powered summary
    try:
        provider = get_provider()
        if provider.is_available():
            prompt = _build_prompt(payload.question, ctx)
            raw = provider.generate(prompt, system_prompt=SYSTEM_PROMPT)
            parsed = parse_json_response(raw)

            if parsed and "incident_title" in parsed:
                return IncidentSummaryResponse(
                    incident_title=parsed.get("incident_title", _titleize(payload.question)),
                    summary=parsed.get("summary", ""),
                    likely_root_cause=parsed.get("likely_root_cause", "Under investigation"),
                    actions_taken_or_recommended=parsed.get("actions_taken_or_recommended", [])[:5],
                    handoff_note=parsed.get("handoff_note", ""),
                )
            logger.warning("LLM summary response missing expected keys, falling back")
    except Exception as exc:
        logger.warning("LLM summary failed, falling back to heuristic: %s", exc)

    # Heuristic fallback
    return _heuristic_summary(payload, ctx)


def _build_prompt(question: str, ctx: dict) -> str:
    parts = [f"Original Question: {question}"]
    if ctx.get("issue_summary"):
        parts.append(f"Issue Summary: {ctx['issue_summary']}")
    if ctx.get("likely_causes"):
        parts.append(f"Likely Causes: {', '.join(ctx['likely_causes'])}")
    if ctx.get("recommended_actions"):
        parts.append(f"Recommended Actions: {', '.join(ctx['recommended_actions'])}")
    if ctx.get("escalation_note"):
        parts.append(f"Escalation Note: {ctx['escalation_note']}")
    return "\n".join(parts)


def _titleize(question: str) -> str:
    cleaned = question.strip().rstrip('?')
    return cleaned[:1].upper() + cleaned[1:]


def _heuristic_summary(payload: IncidentSummaryRequest, ctx: dict) -> IncidentSummaryResponse:
    likely_causes = ctx.get('likely_causes') or ['Cause still under investigation based on available documents.']
    actions = ctx.get('recommended_actions') or ['Review cited documents and verify the affected equipment state.']
    title = payload.question.strip().rstrip('?')
    return IncidentSummaryResponse(
        incident_title=title[:1].upper() + title[1:],
        summary=f"Issue reviewed using uploaded technical documentation. Initial troubleshooting focused on the question: {payload.question.strip()}",
        likely_root_cause=likely_causes[0],
        actions_taken_or_recommended=actions[:4],
        handoff_note='Use the cited sources and recommended actions to continue troubleshooting or hand off to the next technician/engineer.',
    )
