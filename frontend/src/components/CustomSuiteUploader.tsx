import { useRef, useState } from 'react'
import { api } from '../api/client'
import type { CustomSuiteInfo } from '../types'

interface Props {
  suites: CustomSuiteInfo[]
  onUploaded: (suite: CustomSuiteInfo) => void
  onDeleted: (suiteId: string) => void
}

export function CustomSuiteUploader({ suites, onUploaded, onDeleted }: Props) {
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [dragging, setDragging] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const uploadFile = async (file: File) => {
    if (!file.name.endsWith('.py')) {
      setError('Only .py files are accepted.')
      return
    }
    setError(null)
    setUploading(true)
    try {
      const formData = new FormData()
      formData.append('file', file)
      const res = await api.post<CustomSuiteInfo>('/custom-suites', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      onUploaded(res.data)
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ??
        'Upload failed.'
      setError(msg)
    } finally {
      setUploading(false)
    }
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setDragging(false)
    const file = e.dataTransfer.files[0]
    if (file) uploadFile(file)
  }

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) uploadFile(file)
    e.target.value = ''
  }

  const handleDelete = async (suiteId: string) => {
    try {
      await api.delete(`/custom-suites/${suiteId}`)
      onDeleted(suiteId)
    } catch {
      // ignore
    }
  }

  const downloadTemplate = () => {
    window.open('/api/v1/custom-suites/template', '_blank')
  }

  return (
    <div className="space-y-3">
      {/* Drop zone */}
      <div
        onDragOver={(e) => { e.preventDefault(); setDragging(true) }}
        onDragLeave={() => setDragging(false)}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
        className={`
          relative border-2 border-dashed rounded-lg px-4 py-5 text-center cursor-pointer transition-colors
          ${dragging ? 'border-blue-500 bg-blue-950/30' : 'border-gray-700 hover:border-gray-500'}
          ${uploading ? 'opacity-60 pointer-events-none' : ''}
        `}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".py"
          className="hidden"
          onChange={handleFileChange}
        />
        <div className="text-2xl mb-1">📄</div>
        <div className="text-sm text-gray-300 font-medium">
          {uploading ? 'Uploading…' : 'Drop your .py test file here, or click to browse'}
        </div>
        <div className="text-xs text-gray-500 mt-1">Max 256 KB · Python files only</div>
      </div>

      {/* Template download */}
      <button
        type="button"
        onClick={downloadTemplate}
        className="w-full text-xs text-blue-400 hover:text-blue-300 underline text-left transition-colors"
      >
        Download starter template →
      </button>

      {error && (
        <div className="bg-red-950 border border-red-800 rounded-lg px-3 py-2 text-xs text-red-300">
          {error}
        </div>
      )}

      {/* Uploaded suites list */}
      {suites.length > 0 && (
        <div className="space-y-2">
          <div className="text-xs font-medium text-gray-400 uppercase tracking-wide">
            Your test suites
          </div>
          {suites.map((s) => (
            <div
              key={s.suite_id}
              className="flex items-start justify-between gap-2 bg-gray-900 border border-gray-700 rounded-lg px-3 py-2"
            >
              <div className="min-w-0">
                <div className="text-sm font-medium text-gray-200 truncate">{s.name}</div>
                {s.description && (
                  <div className="text-xs text-gray-500 truncate">{s.description}</div>
                )}
                <div className="flex flex-wrap gap-1 mt-1">
                  <span className="text-xs text-gray-400">{s.test_count} tests</span>
                  {s.categories.slice(0, 4).map((c) => (
                    <span
                      key={c}
                      className="text-xs bg-gray-800 text-gray-400 rounded px-1.5 py-0.5"
                    >
                      {c}
                    </span>
                  ))}
                </div>
              </div>
              <button
                type="button"
                onClick={() => handleDelete(s.suite_id)}
                className="text-gray-600 hover:text-red-400 transition-colors flex-shrink-0 text-lg leading-none"
                title="Delete suite"
              >
                ×
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
