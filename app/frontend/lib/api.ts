import type {
  AskResponse,
  DocumentsResponse,
  IncidentSummaryResponse,
  LLMConfig,
  OllamaModel,
  UploadResponse,
} from '@/lib/types'

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000'

async function parseResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let detail = 'Request failed.'
    try {
      const body = await res.json()
      detail = body.detail || body.message || detail
    } catch {
      detail = await res.text()
    }
    throw new Error(detail)
  }
  return res.json() as Promise<T>
}

// --- Documents ---
export async function fetchDocuments(): Promise<DocumentsResponse> {
  const res = await fetch(`${API_BASE}/api/documents`, { cache: 'no-store' })
  return parseResponse<DocumentsResponse>(res)
}

export async function uploadDocuments(files: File[]): Promise<UploadResponse> {
  const form = new FormData()
  files.forEach((file) => form.append('files', file))

  const res = await fetch(`${API_BASE}/api/upload`, {
    method: 'POST',
    body: form,
  })

  return parseResponse<UploadResponse>(res)
}

export async function deleteDocument(documentId: string): Promise<void> {
  const res = await fetch(`${API_BASE}/api/documents/${documentId}`, {
    method: 'DELETE',
  })

  await parseResponse<{ status: string; document_id: string }>(res)
}

// --- Ask & Summarize ---
export async function askQuestion(question: string, top_k: number): Promise<AskResponse> {
  const res = await fetch(`${API_BASE}/api/ask`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question, top_k }),
  })

  return parseResponse<AskResponse>(res)
}

export async function generateIncidentSummary(question: string, answer_context: AskResponse): Promise<IncidentSummaryResponse> {
  const res = await fetch(`${API_BASE}/api/incident-summary`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question, answer_context }),
  })

  return parseResponse<IncidentSummaryResponse>(res)
}

// --- LLM Configuration ---
export async function fetchLLMConfig(): Promise<LLMConfig> {
  const res = await fetch(`${API_BASE}/api/llm-config`, { cache: 'no-store' })
  return parseResponse<LLMConfig>(res)
}

export async function updateLLMConfig(config: {
  provider?: string
  ollama_base_url?: string
  ollama_model?: string
  openai_model?: string
}): Promise<LLMConfig> {
  const res = await fetch(`${API_BASE}/api/llm-config`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(config),
  })
  return parseResponse<LLMConfig>(res)
}

export async function fetchOllamaModels(): Promise<OllamaModel[]> {
  const res = await fetch(`${API_BASE}/api/llm-models`, { cache: 'no-store' })
  const data = await parseResponse<{ models: OllamaModel[] }>(res)
  return data.models
}
