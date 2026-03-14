# Data Schema

## Document
- document_id
- file_name
- source_type
- uploaded_at
- page_count
- chunk_count
- status

## Chunk
- chunk_id
- document_id
- chunk_index
- text
- page_ref
- metadata

## AskResponse
- issue_summary: string
- likely_causes: string[]
- recommended_actions: string[]
- escalation_note: string
- sources: SourceCitation[]

## SourceCitation
- document: string
- chunk_id: string
- excerpt: string
- page_ref: string | null
- score: float | null

## IncidentSummary
- incident_title
- summary
- likely_root_cause
- actions_taken_or_recommended
- handoff_note
