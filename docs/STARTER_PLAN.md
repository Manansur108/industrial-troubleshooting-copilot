# Starter Repo Plan

## Phase 0 — Setup
- initialize git repo
- add `.env.example`
- add backend requirements
- add frontend package scaffold
- create sample doc folder

## Phase 1 — Backend first
Build these in order:
1. `POST /api/upload`
2. file parsing service
3. chunking service
4. embedding + Chroma write
5. `POST /api/ask`
6. retrieval + prompt orchestration
7. `POST /api/incident-summary`

## Phase 2 — Frontend MVP
Build these in order:
1. upload page
2. ask page
3. answer card
4. citations card
5. incident summary card

## Phase 3 — Polish
- error handling
- loading states
- sample docs
- screenshots
- README images
- deploy

## Best first coding order
### Backend
- `main.py`
- `app/api/routes.py`
- `app/services/parser.py`
- `app/services/chunker.py`
- `app/services/vector_store.py`
- `app/services/retriever.py`
- `app/services/answer_engine.py`
- `app/services/summarizer.py`

### Frontend
- `app/page.tsx`
- `app/upload/page.tsx`
- `app/ask/page.tsx`
- `components/FileUpload.tsx`
- `components/AnswerCard.tsx`
- `components/CitationsPanel.tsx`
- `components/IncidentSummaryCard.tsx`

## MVP prompt contract
The answer engine should always output:
- issue summary
- likely causes
- recommended actions
- escalation note
- sources

## Demo story
Upload 3 docs → ask “Why is motor not starting?” → show cited answer → generate incident summary.
