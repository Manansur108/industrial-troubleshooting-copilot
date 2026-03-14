'use client'

import { useEffect, useMemo, useState, useRef, useCallback } from 'react'
import styles from '../app/page.module.css'
import {
  askQuestion,
  deleteDocument,
  fetchDocuments,
  fetchLLMConfig,
  fetchOllamaModels,
  generateIncidentSummary,
  updateLLMConfig,
  uploadDocuments,
} from '@/lib/api'
import type { AskResponse, DocumentInfo, IncidentSummaryResponse, LLMConfig, OllamaModel } from '@/lib/types'

const examplePrompts = [
  'Why is the motor not starting?',
  'Conveyor fault reset procedure',
  'Photoeye not detected — what to check?',
]

export default function CopilotDashboard() {
  // --- Document state ---
  const [documents, setDocuments] = useState<DocumentInfo[]>([])
  const [question, setQuestion] = useState('')
  const [topK, setTopK] = useState(4)
  const [answer, setAnswer] = useState<AskResponse | null>(null)
  const [summary, setSummary] = useState<IncidentSummaryResponse | null>(null)

  // --- Loading states ---
  const [loadingDocs, setLoadingDocs] = useState(true)
  const [uploading, setUploading] = useState(false)
  const [asking, setAsking] = useState(false)
  const [summarizing, setSummarizing] = useState(false)
  const [deletingId, setDeletingId] = useState<string | null>(null)

  // --- LLM config state ---
  const [llmConfig, setLlmConfig] = useState<LLMConfig | null>(null)
  const [ollamaModels, setOllamaModels] = useState<OllamaModel[]>([])
  const [llmLoading, setLlmLoading] = useState(false)

  // --- UI state ---
  const [toast, setToast] = useState<{ msg: string; type: 'success' | 'error' } | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const stats = useMemo(() => ({
    docs: documents.length,
    chunks: documents.reduce((sum, doc) => sum + doc.chunk_count, 0),
    pages: documents.reduce((sum, doc) => sum + doc.page_count, 0),
  }), [documents])

  // --- Data fetching ---
  const loadDocuments = useCallback(async () => {
    setLoadingDocs(true)
    try {
      const res = await fetchDocuments()
      setDocuments(res.documents)
    } catch {
      showToast('Unable to load documents.', 'error')
    } finally {
      setLoadingDocs(false)
    }
  }, [])

  const loadLLMConfig = useCallback(async () => {
    try {
      const config = await fetchLLMConfig()
      setLlmConfig(config)
      if (config.ollama_available) {
        const models = await fetchOllamaModels()
        setOllamaModels(models)
      }
    } catch {
      // Backend might not be running yet
    }
  }, [])

  useEffect(() => {
    void loadDocuments()
    void loadLLMConfig()
  }, [loadDocuments, loadLLMConfig])

  function showToast(msg: string, type: 'success' | 'error' = 'success') {
    setToast({ msg, type })
    setTimeout(() => setToast(null), 4000)
  }

  // --- LLM Provider toggle ---
  async function handleToggleProvider() {
    if (!llmConfig) return
    setLlmLoading(true)
    const newProvider = llmConfig.provider === 'ollama' ? 'openai' : 'ollama'
    try {
      const updated = await updateLLMConfig({ provider: newProvider })
      setLlmConfig(updated as LLMConfig)
      showToast(`Switched to ${newProvider === 'ollama' ? 'Ollama (Local)' : 'OpenAI (Cloud)'}`)
    } catch {
      showToast('Failed to switch provider', 'error')
    } finally {
      setLlmLoading(false)
    }
  }

  async function handleModelChange(model: string) {
    if (!llmConfig) return
    setLlmLoading(true)
    try {
      const updated = await updateLLMConfig({ ollama_model: model })
      setLlmConfig(updated as LLMConfig)
      showToast(`Model: ${model}`)
    } catch {
      showToast('Failed to update model', 'error')
    } finally {
      setLlmLoading(false)
    }
  }

  // --- Document operations ---
  async function handleUpload(files: FileList | null) {
    if (!files?.length) return
    setUploading(true)
    try {
      const res = await uploadDocuments(Array.from(files))
      showToast(`Indexed ${res.files.length} document${res.files.length > 1 ? 's' : ''}.`)
      await loadDocuments()
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Upload failed. Check backend connection.'
      showToast(msg, 'error')
    } finally {
      setUploading(false)
      if (fileInputRef.current) fileInputRef.current.value = ''
    }
  }

  async function handleAsk(event?: React.FormEvent) {
    event?.preventDefault()
    if (!question.trim()) return
    setAsking(true)
    setSummary(null)
    try {
      const res = await askQuestion(question.trim(), topK)
      setAnswer(res)
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Analysis failed.'
      showToast(msg, 'error')
    } finally {
      setAsking(false)
    }
  }

  async function handleGenerateSummary() {
    if (!answer) return
    setSummarizing(true)
    try {
      const res = await generateIncidentSummary(question.trim(), answer)
      setSummary(res)
      showToast('Handoff summary generated.')
    } catch {
      showToast('Summary generation failed.', 'error')
    } finally {
      setSummarizing(false)
    }
  }

  async function handleDelete(documentId: string) {
    setDeletingId(documentId)
    try {
      await deleteDocument(documentId)
      setDocuments((prev) => prev.filter((doc) => doc.document_id !== documentId))
      showToast('Document removed.')
    } catch {
      showToast('Delete failed.', 'error')
    } finally {
      setDeletingId(null)
    }
  }

  // --- Helpers ---
  function formatSize(bytes: number): string {
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1048576) return `${(bytes / 1024).toFixed(1)} KB`
    return `${(bytes / 1048576).toFixed(1)} MB`
  }

  const isOllama = llmConfig?.provider === 'ollama'

  return (
    <div className={styles.layout}>
      {/* ── Sidebar ── */}
      <aside className={styles.sidebar}>
        <div className={styles.brand}>
          <div className={styles.logoMark}>
            <svg width="28" height="28" viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
              <defs>
                <linearGradient id="logoGrad" x1="0" y1="0" x2="32" y2="32">
                  <stop offset="0%" stopColor="#22c55e" />
                  <stop offset="100%" stopColor="#0a0a0b" />
                </linearGradient>
              </defs>
              <rect width="32" height="32" rx="6" fill="url(#logoGrad)" />
              <text x="16" y="21" textAnchor="middle" fill="#fff" fontFamily="Space Grotesk, sans-serif" fontWeight="700" fontSize="16">M</text>
            </svg>
            <span className={styles.logoText}>MananSurati</span>
          </div>
          <h1>Troubleshooting<br />Copilot</h1>
        </div>

        {/* LLM Provider Panel */}
        <div className={styles.llmSection}>
          <div className={styles.llmHeader}>
            <h2>LLM Provider</h2>
            <span
              className={`${styles.statusDot} ${
                llmConfig?.ollama_available ? styles.online : styles.offline
              }`}
              title={llmConfig?.ollama_available ? 'Ollama connected' : 'Ollama offline'}
            />
          </div>

          <div className={styles.toggleRow}>
            <span className={styles.toggleLabel}>
              {isOllama ? 'Ollama (Local)' : 'OpenAI (Cloud)'}
            </span>
            <div
              className={`${styles.toggleSwitch} ${isOllama ? styles.active : ''}`}
              onClick={handleToggleProvider}
              role="switch"
              aria-checked={isOllama}
              tabIndex={0}
              title="Toggle between Ollama and OpenAI"
            >
              <div className={styles.toggleKnob} />
            </div>
          </div>

          {isOllama && ollamaModels.length > 0 && (
            <select
              className={styles.modelSelect}
              value={llmConfig?.ollama_model || ''}
              onChange={(e) => void handleModelChange(e.target.value)}
              disabled={llmLoading}
            >
              {ollamaModels.map((m) => (
                <option key={m.name} value={m.name}>
                  {m.name} ({formatSize(m.size)})
                </option>
              ))}
            </select>
          )}
        </div>

        {/* Documents */}
        <div className={styles.sidebarSection}>
          <h2>Documents</h2>
          <div className={styles.docList}>
            {loadingDocs ? (
              <div className={styles.loading}>Loading…</div>
            ) : documents.length > 0 ? (
              documents.map((doc) => (
                <div className={styles.docItem} key={doc.document_id}>
                  <div className={styles.docInfo}>
                    <span className={styles.docName} title={doc.file_name}>
                      {doc.file_name}
                    </span>
                    <span className={styles.docMeta}>
                      {doc.source_type.toUpperCase()} · {doc.page_count}p · {doc.chunk_count} chunks
                    </span>
                  </div>
                  <div className={styles.docActions}>
                    <button
                      className={styles.iconButton}
                      onClick={() => void handleDelete(doc.document_id)}
                      disabled={deletingId === doc.document_id}
                      title="Remove"
                    >
                      <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <path d="M3 6h18m-2 0v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6m3 0V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2M10 11v6m4-6v6" />
                      </svg>
                    </button>
                  </div>
                </div>
              ))
            ) : (
              <div className={styles.emptyState} style={{ padding: '16px', fontSize: '0.75rem' }}>
                No documents indexed
              </div>
            )}
          </div>
        </div>

        {/* Upload */}
        <div className={styles.sidebarSection}>
          <h2>Upload</h2>
          <div className={styles.uploadZone} onClick={() => fileInputRef.current?.click()}>
            <div className={styles.uploadIcon}>
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4m14-7-5-5-5 5m5-5v12" />
              </svg>
            </div>
            <span>{uploading ? 'Processing…' : 'Drop files or click'}</span>
            <span className={styles.uploadSubtext}>PDF · DOCX · TXT · LOG</span>
            <input
              type="file"
              ref={fileInputRef}
              className={styles.fileInput}
              multiple
              accept=".pdf,.docx,.txt,.md,.log"
              onChange={(e) => void handleUpload(e.target.files)}
            />
          </div>
        </div>

        {/* Footer stats */}
        <div className={styles.sidebarFooter}>
          <div className={styles.docMeta}>
            <span>{stats.docs} files</span>
            <span>·</span>
            <span>{stats.pages} pages</span>
            <span>·</span>
            <span>{stats.chunks} chunks</span>
          </div>
        </div>
      </aside>

      {/* ── Main ── */}
      <main className={styles.main}>
        <header className={styles.header}>
          <h2>Troubleshooting</h2>
          <p>Search your document workspace for faults, procedures, and operational intelligence.</p>
        </header>

        {/* Search */}
        <section className={styles.searchContainer}>
          <form className={styles.searchWrapper} onSubmit={(e) => void handleAsk(e)}>
            <textarea
              className={styles.textarea}
              placeholder="Describe the issue or ask for a procedure…"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault()
                  void handleAsk()
                }
              }}
            />
            <div className={styles.searchActions}>
              <div className={styles.searchOptions}>
                <div className={styles.option}>
                  <span>Chunks:</span>
                  <input
                    type="number"
                    className={styles.numberInput}
                    value={topK}
                    min={1}
                    max={10}
                    onChange={(e) => setTopK(Number(e.target.value))}
                  />
                </div>
                {llmConfig && (
                  <div className={styles.option}>
                    <span style={{ opacity: 0.5 }}>
                      via {isOllama ? llmConfig.ollama_model : 'OpenAI'}
                    </span>
                  </div>
                )}
              </div>
              <div className={styles.actionButtons}>
                <button
                  type="submit"
                  className={styles.primaryButton}
                  disabled={asking || !question.trim() || documents.length === 0}
                >
                  {asking ? 'Analyzing…' : 'Search'}
                </button>
              </div>
            </div>
          </form>

          <div className={styles.promptChips}>
            {examplePrompts.map((p) => (
              <button
                key={p}
                className={styles.chipButton}
                onClick={() => setQuestion(p)}
                type="button"
              >
                {p}
              </button>
            ))}
          </div>
        </section>

        {/* Results */}
        <div className={styles.results}>
          {asking ? (
            /* Skeleton loader */
            <div className={styles.resultCard}>
              <div className={styles.cardSection}>
                <div className={`${styles.skeleton} ${styles.skeletonLine}`} style={{ width: '40%' }} />
                <div className={`${styles.skeleton} ${styles.skeletonLine}`} style={{ width: '70%', height: '20px' }} />
              </div>
              <div className={styles.twoCol}>
                <div className={styles.cardSection}>
                  <div className={`${styles.skeleton} ${styles.skeletonLine}`} />
                  <div className={`${styles.skeleton} ${styles.skeletonLine}`} />
                  <div className={`${styles.skeleton} ${styles.skeletonLine}`} />
                </div>
                <div className={styles.cardSection}>
                  <div className={`${styles.skeleton} ${styles.skeletonLine}`} />
                  <div className={`${styles.skeleton} ${styles.skeletonLine}`} />
                </div>
              </div>
            </div>
          ) : answer ? (
            <div className="animate-fade">
              <div className={styles.resultCard}>
                <div className={styles.cardSection}>
                  <h3>Investigation Result</h3>
                  <h4 className={styles.issueTitle}>{answer.issue_summary}</h4>
                </div>

                <div className={styles.twoCol}>
                  <div className={styles.cardSection}>
                    <h3>Likely Causes</h3>
                    <ul className={styles.list}>
                      {answer.likely_causes.map((c, i) => (
                        <li key={i} className={styles.listItem}>{c}</li>
                      ))}
                    </ul>
                  </div>
                  <div className={styles.cardSection}>
                    <h3>Recommended Actions</h3>
                    <ul className={styles.list}>
                      {answer.recommended_actions.map((a, i) => (
                        <li key={i} className={styles.listItem}>{a}</li>
                      ))}
                    </ul>
                  </div>
                </div>

                <div className={styles.escalation}>
                  <strong>Escalation:</strong> {answer.escalation_note}
                </div>

                <div className={styles.cardSection}>
                  <h3>Source Citations</h3>
                  <div className={styles.citations}>
                    {answer.sources.map((src, i) => (
                      <div className={styles.citationCard} key={`${src.chunk_id}-${i}`}>
                        <div className={styles.citationHeader}>
                          <div className={styles.citationInfo}>
                            <div className={styles.citationSource}>{src.document}</div>
                            <div className={styles.citationMeta}>Page {src.page_ref || 'N/A'}</div>
                          </div>
                          <div className={styles.citationScore}>
                            {typeof src.score === 'number' ? Math.round(src.score * 100) : 0}%
                          </div>
                        </div>
                        <p className={styles.citationText}>&ldquo;{src.excerpt}&hellip;&rdquo;</p>
                      </div>
                    ))}
                  </div>
                </div>

                <div className={styles.cardSection} style={{ alignItems: 'center', marginTop: '4px' }}>
                  <button
                    className={styles.secondaryButton}
                    onClick={() => void handleGenerateSummary()}
                    disabled={summarizing || !!summary}
                  >
                    {summarizing ? 'Building Handoff…' : summary ? 'Handoff Ready ✓' : 'Generate Incident Summary'}
                  </button>
                </div>
              </div>

              {summary && (
                <div className={styles.summaryCard} style={{ marginTop: '20px' }}>
                  <div className={styles.summaryHeader}>
                    <h3>Incident Handoff</h3>
                  </div>
                  <div className={styles.twoCol}>
                    <div className={styles.cardSection}>
                      <p><strong style={{ color: 'var(--text-secondary)' }}>Status:</strong> {summary.summary}</p>
                      <p style={{ marginTop: '8px' }}>
                        <strong style={{ color: 'var(--text-secondary)' }}>Root Cause:</strong> {summary.likely_root_cause}
                      </p>
                    </div>
                    <div className={styles.cardSection}>
                      <strong style={{ color: 'var(--text-secondary)', fontSize: '0.8rem' }}>Actions:</strong>
                      <ul className={styles.list}>
                        {summary.actions_taken_or_recommended.map((a, i) => (
                          <li key={i} className={styles.listItem}>{a}</li>
                        ))}
                      </ul>
                    </div>
                  </div>
                  <div className={styles.escalation} style={{
                    background: 'var(--success-muted)',
                    borderColor: 'rgba(34, 197, 94, 0.12)',
                    color: 'var(--success)'
                  }}>
                    <strong>Handoff:</strong> {summary.handoff_note}
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className={styles.emptyState}>
              Upload documents and enter a troubleshooting query to begin.
            </div>
          )}
        </div>
      </main>

      {/* Toast */}
      {toast && (
        <div
          className={styles.statusToast}
          style={{
            borderColor: toast.type === 'error' ? 'var(--danger)' : 'var(--border-strong)',
            color: toast.type === 'error' ? 'var(--danger)' : 'var(--text)',
          }}
        >
          {toast.msg}
        </div>
      )}
    </div>
  )
}
