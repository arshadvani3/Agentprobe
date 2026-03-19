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

  // Load existing custom suites on mount
  useEffect(() => {
    api.get<CustomSuiteInfo[]>('/custom-suites')
      .then((r) => setCustomSuites(r.data))
      .catch(() => {/* silently ignore */})
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
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="grid grid-cols-2 gap-4">
        <div className="col-span-2">
          <label className="block text-xs font-medium text-gray-400 mb-1">Target URL</label>
          <input
            type="text"
            value={form.target_url}
            onChange={(e) => set('target_url', e.target.value)}
            className="w-full bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-100 focus:outline-none focus:border-blue-500"
            placeholder="http://localhost:11434"
            required
          />
        </div>

        <div>
          <label className="block text-xs font-medium text-gray-400 mb-1">Target Type</label>
          <select
            value={form.target_type}
            onChange={(e) => set('target_type', e.target.value as TargetType)}
            className="w-full bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-100 focus:outline-none focus:border-blue-500"
          >
            <option value="ollama">Ollama</option>
            <option value="openai">OpenAI-compatible</option>
            <option value="simple">Simple API</option>
          </select>
        </div>

        <div>
          <label className="block text-xs font-medium text-gray-400 mb-1">Model</label>
          <input
            type="text"
            value={form.model || ''}
            onChange={(e) => set('model', e.target.value)}
            className="w-full bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-100 focus:outline-none focus:border-blue-500"
            placeholder="llama3.1:8b"
          />
        </div>

        <div>
          <label className="block text-xs font-medium text-gray-400 mb-1">Test Suite</label>
          <select
            value={form.suite}
            onChange={(e) => set('suite', e.target.value)}
            className="w-full bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-100 focus:outline-none focus:border-blue-500"
          >
            {suites.map((s) => (
              <option key={s.name} value={s.name}>
                {s.name} ({s.test_count} tests)
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-xs font-medium text-gray-400 mb-1">Depth</label>
          <select
            value={form.depth}
            onChange={(e) => set('depth', e.target.value as EvalDepth)}
            className="w-full bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-100 focus:outline-none focus:border-blue-500"
          >
            <option value="quick">Quick</option>
            <option value="standard">Standard</option>
            <option value="deep">Deep</option>
          </select>
        </div>

        <div>
          <label className="block text-xs font-medium text-gray-400 mb-1">Timeout (seconds)</label>
          <input
            type="number"
            value={form.timeout}
            onChange={(e) => set('timeout', Number(e.target.value))}
            className="w-full bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-100 focus:outline-none focus:border-blue-500"
            min={5}
            max={300}
          />
        </div>

        <div className="col-span-2">
          <label className="block text-xs font-medium text-gray-400 mb-1">Target Description</label>
          <input
            type="text"
            value={form.target_description || ''}
            onChange={(e) => set('target_description', e.target.value)}
            className="w-full bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-100 focus:outline-none focus:border-blue-500"
            placeholder="A general-purpose AI assistant"
          />
        </div>

        <div className="col-span-2">
          <label className="block text-xs font-medium text-gray-400 mb-1">
            API Key <span className="text-gray-600">(optional — for Groq, OpenAI, etc.)</span>
          </label>
          <input
            type="password"
            value={form.api_key || ''}
            onChange={(e) => set('api_key', e.target.value)}
            className="w-full bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-100 focus:outline-none focus:border-blue-500"
            placeholder="gsk_..."
          />
        </div>
      </div>

      {/* ── Custom test suite ─────────────────────────────────────────────── */}
      <div className="border border-dashed border-gray-700 rounded-lg overflow-hidden">
        <button
          type="button"
          onClick={() => setShowCustom((v) => !v)}
          className="w-full flex items-center justify-between px-4 py-3 hover:bg-gray-900 transition-colors"
        >
          <div className="flex items-center gap-2">
            <span className="text-sm font-medium text-gray-200">Custom test suite</span>
            {selectedCustom && (
              <span className="text-xs bg-blue-900 text-blue-300 rounded-full px-2 py-0.5">
                {selectedCustom.name} · {selectedCustom.test_count} tests
              </span>
            )}
            {!selectedCustom && (
              <span className="text-xs text-gray-500">optional — add your own tests</span>
            )}
          </div>
          <span className="text-gray-500 text-xs">{showCustom ? '▲' : '▼'}</span>
        </button>

        {showCustom && (
          <div className="px-4 pb-4 space-y-4 border-t border-gray-800 pt-3">
            <CustomSuiteUploader
              suites={customSuites}
              onUploaded={handleUploaded}
              onDeleted={handleDeleted}
            />

            {/* Suite selector — shown when there are uploaded suites */}
            {customSuites.length > 0 && (
              <div>
                <label className="block text-xs font-medium text-gray-400 mb-1">
                  Run alongside evaluation
                </label>
                <select
                  value={form.custom_suite_id ?? ''}
                  onChange={(e) => set('custom_suite_id', e.target.value || null)}
                  className="w-full bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-100 focus:outline-none focus:border-blue-500"
                >
                  <option value="">None — don't add custom tests</option>
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

      {/* Demo mode toggle */}
      <label className="flex items-center gap-3 cursor-pointer p-3 rounded-lg border border-dashed border-gray-700 hover:border-blue-600 transition-colors">
        <input
          type="checkbox"
          checked={form.demo ?? false}
          onChange={(e) => set('demo', e.target.checked)}
          className="w-4 h-4 accent-blue-500"
        />
        <div>
          <div className="text-sm font-medium text-gray-200">Demo mode</div>
          <div className="text-xs text-gray-500">Pre-canned results, completes in ~30s. No Ollama needed.</div>
        </div>
      </label>

      {error && (
        <div className="bg-red-950 border border-red-800 rounded-lg px-3 py-2 text-sm text-red-300">
          {error}
        </div>
      )}

      <button
        type="submit"
        disabled={loading}
        className="w-full bg-blue-600 hover:bg-blue-500 disabled:bg-blue-900 disabled:text-blue-500 text-white font-semibold rounded-lg px-4 py-2.5 text-sm transition-colors"
      >
        {loading ? 'Starting...' : (form.demo ? 'Start Demo' : 'Start Evaluation')}
      </button>
    </form>
  )
}
