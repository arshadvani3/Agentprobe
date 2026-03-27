import { useEffect, useState } from 'react'
import type { StartEvaluationRequest, TargetType, EvalDepth, CustomSuiteInfo } from '../types'
import type { TestSuiteInfo } from '../types'
import { api } from '../api/client'
import { CustomSuiteUploader } from './CustomSuiteUploader'

interface Props {
  suites: TestSuiteInfo[]
  onSubmit: (req: StartEvaluationRequest) => Promise<void>
  loading: boolean
  error: string | null
}

const inputStyle: React.CSSProperties = {
  width: '100%',
  background: '#18181b',
  border: 'none',
  borderBottom: '1px solid #27272a',
  padding: '8px 4px',
  fontSize: 12,
  color: '#FAFAFA',
  fontFamily: "'Inter', sans-serif",
  transition: 'border-bottom-color 0.2s',
  outline: 'none',
  borderRadius: 0,
}

const labelStyle: React.CSSProperties = {
  display: 'block',
  fontSize: 9,
  fontWeight: 600,
  letterSpacing: '0.18em',
  textTransform: 'uppercase',
  color: '#7A6030',
  marginBottom: 6,
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column' }}>
      <label style={labelStyle}>{label}</label>
      {children}
    </div>
  )
}

export function NewEvaluationForm({ suites, onSubmit, loading, error }: Props) {
  const [form, setForm] = useState<StartEvaluationRequest>({
    target_url: 'http://localhost:11434',
    target_type: 'ollama',
    suite: 'general_chatbot',
    depth: 'standard',
    model: 'llama3.1:8b',
    timeout: 30,
    target_description: 'A general-purpose AI assistant',
    api_key: '',
    demo: false,
    custom_suite_id: null,
  })

  const [customSuites, setCustomSuites] = useState<CustomSuiteInfo[]>([])
  const [showCustom, setShowCustom] = useState(false)

  useEffect(() => {
    api.get<CustomSuiteInfo[]>('/custom-suites')
      .then((r) => setCustomSuites(r.data))
      .catch(() => { /* silently ignore */ })
  }, [])

  const set = (k: keyof StartEvaluationRequest, v: unknown) =>
    setForm((f) => ({ ...f, [k]: v }))

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    await onSubmit(form)
  }

  const handleUploaded = (suite: CustomSuiteInfo) => {
    setCustomSuites((prev) => [suite, ...prev])
    set('custom_suite_id', suite.suite_id)
  }

  const handleDeleted = (suiteId: string) => {
    setCustomSuites((prev) => prev.filter((s) => s.suite_id !== suiteId))
    if (form.custom_suite_id === suiteId) set('custom_suite_id', null)
  }

  const selectedCustom = customSuites.find((s) => s.suite_id === form.custom_suite_id)

  return (
    <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>

      <Field label="Target URL">
        <input
          type="text"
          value={form.target_url}
          onChange={(e) => set('target_url', e.target.value)}
          style={inputStyle}
          placeholder="http://localhost:11434"
          required
        />
      </Field>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
        <Field label="Target Type">
          <select
            value={form.target_type}
            onChange={(e) => set('target_type', e.target.value as TargetType)}
            style={{ ...inputStyle, cursor: 'pointer' }}
          >
            <option value="ollama">Ollama</option>
            <option value="openai">OpenAI-compatible</option>
            <option value="simple">Simple API</option>
          </select>
        </Field>

        <Field label="Model">
          <input
            type="text"
            value={form.model || ''}
            onChange={(e) => set('model', e.target.value)}
            style={inputStyle}
            placeholder="llama3.1:8b"
          />
        </Field>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
        <Field label="Test Suite">
          <select
            value={form.suite}
            onChange={(e) => set('suite', e.target.value)}
            style={{ ...inputStyle, cursor: 'pointer' }}
          >
            {suites.map((s) => (
              <option key={s.name} value={s.name}>
                {s.name} ({s.test_count})
              </option>
            ))}
          </select>
        </Field>

        <Field label="Depth">
          <select
            value={form.depth}
            onChange={(e) => set('depth', e.target.value as EvalDepth)}
            style={{ ...inputStyle, cursor: 'pointer' }}
          >
            <option value="quick">Quick</option>
            <option value="standard">Standard</option>
            <option value="deep">Deep</option>
          </select>
        </Field>
      </div>

      <Field label="Timeout (seconds)">
        <input
          type="number"
          value={form.timeout}
          onChange={(e) => set('timeout', Number(e.target.value))}
          style={inputStyle}
          min={5}
          max={300}
        />
      </Field>

      <Field label="Target Description">
        <input
          type="text"
          value={form.target_description || ''}
          onChange={(e) => set('target_description', e.target.value)}
          style={inputStyle}
          placeholder="A general-purpose AI assistant"
        />
      </Field>

      <Field label="API Key (optional — Groq, OpenAI, etc.)">
        <input
          type="password"
          value={form.api_key || ''}
          onChange={(e) => set('api_key', e.target.value)}
          style={inputStyle}
          placeholder="gsk_..."
        />
      </Field>

      {/* ── Custom test suite ──────────────────────────────────────── */}
      <div style={{
        border: '1px dashed #92722a',
        overflow: 'hidden',
      }}>
        <button
          type="button"
          onClick={() => setShowCustom((v) => !v)}
          style={{
            width: '100%',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '10px 14px',
            background: 'transparent',
            border: 'none',
            cursor: 'pointer',
            color: '#A1A1AA',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <span style={{
              fontSize: 10,
              fontWeight: 600,
              letterSpacing: '0.15em',
              textTransform: 'uppercase',
              color: '#A1A1AA',
            }}>
              Custom Test Suite
            </span>
            {selectedCustom && (
              <span style={{
                fontSize: 10,
                color: '#C9A84C',
                letterSpacing: '0.05em',
              }}>
                {selectedCustom.name} · {selectedCustom.test_count} tests
              </span>
            )}
          </div>
          <span style={{ fontSize: 10, color: '#7A6030' }}>{showCustom ? '▲' : '▼'}</span>
        </button>

        {showCustom && (
          <div style={{ padding: '0 14px 14px', borderTop: '1px solid #27272a' }}>
            <div style={{ paddingTop: 14 }}>
              <CustomSuiteUploader
                suites={customSuites}
                onUploaded={handleUploaded}
                onDeleted={handleDeleted}
              />
            </div>

            {customSuites.length > 0 && (
              <div style={{ marginTop: 12 }}>
                <label style={labelStyle}>Run alongside evaluation</label>
                <select
                  value={form.custom_suite_id ?? ''}
                  onChange={(e) => set('custom_suite_id', e.target.value || null)}
                  style={{ ...inputStyle, cursor: 'pointer' }}
                >
                  <option value="">None — use standard suite only</option>
                  {customSuites.map((s) => (
                    <option key={s.suite_id} value={s.suite_id}>
                      {s.name} ({s.test_count} tests)
                    </option>
                  ))}
                </select>
              </div>
            )}
          </div>
        )}
      </div>

      {/* ── Demo mode ─────────────────────────────────────────────── */}
      <label style={{
        display: 'flex',
        alignItems: 'center',
        gap: 12,
        cursor: 'pointer',
        padding: '10px 14px',
        border: `1px dashed ${form.demo ? '#C9A84C' : '#27272a'}`,
        transition: 'border-color 0.2s',
      }}>
        <input
          type="checkbox"
          checked={form.demo ?? false}
          onChange={(e) => set('demo', e.target.checked)}
          style={{ accentColor: '#C9A84C', width: 14, height: 14 }}
        />
        <div>
          <div style={{
            fontSize: 11,
            fontWeight: 500,
            color: form.demo ? '#C9A84C' : '#FAFAFA',
            letterSpacing: '0.05em',
          }}>
            Demo Mode
          </div>
          <div style={{ fontSize: 10, color: '#52525b', marginTop: 2 }}>
            Pre-canned results · ~30s · No Ollama required
          </div>
        </div>
      </label>

      {error && (
        <div style={{
          background: '#1c0909',
          border: '1px solid #7f1d1d',
          padding: '10px 14px',
          fontSize: 12,
          color: '#fca5a5',
        }}>
          {error}
        </div>
      )}

      <button
        type="submit"
        disabled={loading}
        style={{
          width: '100%',
          background: loading ? '#7A6030' : '#C9A84C',
          color: '#09090b',
          border: 'none',
          padding: '12px 16px',
          fontSize: 11,
          fontWeight: 600,
          letterSpacing: '0.2em',
          textTransform: 'uppercase',
          cursor: loading ? 'not-allowed' : 'pointer',
          borderRadius: 0,
          transition: 'background 0.2s ease',
          opacity: loading ? 0.7 : 1,
        }}
        onMouseEnter={(e) => { if (!loading) e.currentTarget.style.background = '#E8C96A' }}
        onMouseLeave={(e) => { if (!loading) e.currentTarget.style.background = '#C9A84C' }}
      >
        {loading ? 'Starting…' : (form.demo ? 'Start Demo' : 'Start Evaluation')}
      </button>
    </form>
  )
}
