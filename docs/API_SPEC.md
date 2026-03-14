# API Spec

## POST /api/upload
Upload one or more documents.

Request:
- multipart form-data
- files[]

Response:
```json
{
  "status": "ok",
  "files": [
    {
      "file_name": "alarm_guide.pdf",
      "document_id": "doc_123",
      "chunks_created": 42
    }
  ]
}
```

## POST /api/ask
Ask a troubleshooting question.

Request:
```json
{
  "question": "Why is the conveyor motor not starting after reset?",
  "top_k": 5
}
```

Response:
```json
{
  "issue_summary": "Conveyor motor start failure after reset.",
  "likely_causes": [
    "Safety interlock open",
    "Overload relay trip",
    "VFD fault still active"
  ],
  "recommended_actions": [
    "Verify safety chain status",
    "Check overload relay reset state",
    "Inspect VFD alarm code and clear conditions"
  ],
  "escalation_note": "Escalate if motor starter command is present but no physical output is observed.",
  "sources": [
    {
      "document": "motor_sop.pdf",
      "chunk_id": "chunk_12",
      "excerpt": "..."
    }
  ]
}
```

## POST /api/incident-summary
Generate a concise incident summary.

Request:
```json
{
  "question": "Why is the conveyor motor not starting after reset?",
  "answer_context": "optional returned answer payload or source ids"
}
```

Response:
```json
{
  "incident_title": "Conveyor start failure after reset",
  "summary": "...",
  "recommended_handoff": "..."
}
```

## GET /api/documents
List uploaded docs.

## DELETE /api/documents/{document_id}
Remove a document and its vectors.
