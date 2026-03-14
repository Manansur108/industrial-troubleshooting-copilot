# MVP Architecture

## Product goal
A practical AI assistant for technicians, engineers, and operators to troubleshoot industrial issues from uploaded technical documentation.

## Core user flows
1. Upload technical documents
2. Ask a troubleshooting question
3. Get a cited answer with likely causes and recommended actions
4. Generate an incident summary from the response

## MVP components

### 1. Frontend
Purpose:
- upload documents
- ask questions
- display answers, citations, and follow-up actions
- trigger incident summary generation

Recommended stack:
- Next.js 14+
- TypeScript
- Tailwind CSS

Pages:
- `/` dashboard
- `/upload` document upload
- `/ask` troubleshooting query workspace
- `/incident` summary/export view

Core UI panels:
- document list
- question input
- answer panel
- citations panel
- recommended actions panel

### 2. Backend API
Purpose:
- parse docs
- chunk docs
- create embeddings
- store/retrieve vectors
- orchestrate LLM responses
- return structured outputs

Recommended stack:
- FastAPI
- Pydantic
- Uvicorn

Core modules:
- ingest service
- retrieval service
- answer service
- summary service
- storage service

### 3. Vector store
Purpose:
- store embedded chunks
- query relevant chunks for troubleshooting prompts

MVP choice:
- Chroma local persistent store

Future upgrade:
- Postgres + pgvector

### 4. LLM layer
Purpose:
- synthesize retrieved context into useful, cited outputs

MVP behavior:
- answer only from retrieved docs when possible
- explicitly say when evidence is not found
- always return citations
- produce structured format:
  - issue summary
  - likely causes
  - recommended actions
  - escalation note
  - sources

## System flow
1. User uploads documents
2. Backend extracts text from PDF/DOCX/TXT
3. Backend chunks text and stores vectors
4. User asks troubleshooting question
5. Retrieval layer fetches top-k chunks
6. Prompt builder sends chunks + question to LLM
7. Backend returns structured JSON response
8. Frontend renders answer and citations
9. User can generate/export incident summary

## MVP constraints
- single user
- local file storage
- no auth
- no PLC live integration
- no multi-tenant support
- no training/fine-tuning

## Non-goals for v1
- real-time plant data ingestion
- SCADA integration
- enterprise access control
- analytics dashboard
- multi-user collaboration

## Key differentiation
Unlike a generic RAG chatbot, this product is positioned around industrial troubleshooting and maintenance workflows.
