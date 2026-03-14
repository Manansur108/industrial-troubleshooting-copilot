export type UploadFileResult = {
  file_name: string
  document_id: string
  chunks_created: number
}

export type UploadResponse = {
  status: string
  files: UploadFileResult[]
}

export type SourceCitation = {
  document: string
  chunk_id: string
  excerpt: string
  page_ref?: string | null
  score?: number | null
  metadata?: Record<string, unknown>
}

export type AskResponse = {
  issue_summary: string
  likely_causes: string[]
  recommended_actions: string[]
  escalation_note: string
  sources: SourceCitation[]
}

export type IncidentSummaryResponse = {
  incident_title: string
  summary: string
  likely_root_cause: string
  actions_taken_or_recommended: string[]
  handoff_note: string
}

export type DocumentInfo = {
  document_id: string
  file_name: string
  source_type: string
  uploaded_at: string
  page_count: number
  chunk_count: number
  status: string
}

export type DocumentsResponse = {
  documents: DocumentInfo[]
}

// LLM configuration
export type LLMConfig = {
  provider: string
  ollama_base_url: string
  ollama_model: string
  openai_model: string
  openai_configured: boolean
  ollama_available: boolean
}

export type OllamaModel = {
  name: string
  size: number
  modified_at: string
}
