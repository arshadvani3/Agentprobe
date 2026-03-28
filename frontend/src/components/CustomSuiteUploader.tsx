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
    } catch (err) {
      console.error('Failed to delete suite:', err)
    }
  }

  const downloadTemplate = () => {
    window.open('/api/v1/custom-suites/template', '_blank')
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
      {/* Drop zone */}
      <div
        onDragOver={(e) => { e.preventDefault(); setDragging(true) }}
        onDragLeave={() => setDragging(false)}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
        style={{
          border: `1px dashed ${dragging ? '#E8C96A' : '#92722a'}`,
          background: dragging ? '#1a1200' : '#111113',
          padding: '20px 16px',
          textAlign: 'center',
          cursor: 'pointer',
          transition: 'all 0.2s ease',
          opacity: uploading ? 0.6 : 1,
          pointerEvents: uploading ? 'none' : 'auto',
        }}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".py"
          style={{ display: 'none' }}
          onChange={handleFileChange}
        />
        <div style={{ fontSize: 18, marginBottom: 6 }}>{ uploading ? '⏳' : '📄' }</div>
        <div style={{ fontSize: 12, color: '#A1A1AA', fontWeight: 500 }}>
          {uploading ? 'Uploading…' : 'Drop your .py test file here, or click to browse'}
        </div>
        <div style={{ fontSize: 10, color: '#52525b', marginTop: 4 }}>Max 256 KB · Python files only</div>
      </div>

      {/* Template download */}
      <button
        type="button"
        onClick={downloadTemplate}
        style={{
          background: 'none',
          border: 'none',
          padding: 0,
          fontSize: 11,
          color: '#C9A84C',
          cursor: 'pointer',
          textAlign: 'left',
          letterSpacing: '0.05em',
          textDecoration: 'none',
        }}
        onMouseEnter={(e) => { e.currentTarget.style.color = '#E8C96A' }}
        onMouseLeave={(e) => { e.currentTarget.style.color = '#C9A84C' }}
      >
        Download starter template →
      </button>

      {error && (
        <div style={{
          background: '#1c0909',
          border: '1px solid #7f1d1d',
          padding: '8px 12px',
          fontSize: 11,
          color: '#fca5a5',
        }}>
          {error}
        </div>
      )}

      {/* Uploaded suites list */}
      {suites.length > 0 && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          <div style={{
            fontSize: 9,
            fontWeight: 600,
            letterSpacing: '0.2em',
            textTransform: 'uppercase',
            color: '#7A6030',
          }}>
            Your Test Suites
          </div>
          {suites.map((s) => (
            <div
              key={s.suite_id}
              style={{
                display: 'flex',
                alignItems: 'flex-start',
                justifyContent: 'space-between',
                gap: 8,
                background: '#18181b',
                borderLeft: '3px solid #C9A84C',
                padding: '10px 12px',
              }}
            >
              <div style={{ minWidth: 0 }}>
                <div style={{
                  fontSize: 12,
                  fontWeight: 500,
                  color: '#FAFAFA',
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  whiteSpace: 'nowrap',
                }}>
                  {s.name}
                </div>
                {s.description && (
                  <div style={{
                    fontSize: 10,
                    color: '#52525b',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    whiteSpace: 'nowrap',
                    marginTop: 2,
                  }}>
                    {s.description}
                  </div>
                )}
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4, marginTop: 6 }}>
                  <span style={{ fontSize: 10, color: '#A1A1AA' }}>{s.test_count} tests</span>
                  {s.categories.slice(0, 4).map((c) => (
                    <span
                      key={c}
                      style={{
                        fontSize: 9,
                        color: '#7A6030',
                        background: '#18181b',
                        border: '1px solid #27272a',
                        padding: '1px 6px',
                        letterSpacing: '0.08em',
                        textTransform: 'uppercase',
                      }}
                    >
                      {c}
                    </span>
                  ))}
                </div>
              </div>
              <button
                type="button"
                onClick={() => handleDelete(s.suite_id)}
                style={{
                  background: 'none',
                  border: 'none',
                  color: '#52525b',
                  cursor: 'pointer',
                  fontSize: 16,
                  lineHeight: 1,
                  padding: 0,
                  flexShrink: 0,
                  transition: 'color 0.15s',
                }}
                onMouseEnter={(e) => { e.currentTarget.style.color = '#ef4444' }}
                onMouseLeave={(e) => { e.currentTarget.style.color = '#52525b' }}
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
