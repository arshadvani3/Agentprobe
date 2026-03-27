import { useState } from 'react'
import { useEvaluations, useTestSuites } from './hooks/useEvaluations'
import { EvaluationList } from './components/EvaluationList'
import { EvaluationDetail } from './components/EvaluationDetail'
import { NewEvaluationForm } from './components/NewEvaluationForm'
import type { StartEvaluationRequest } from './types'

export default function App() {
  const { evaluations, loading, error, startEvaluation } = useEvaluations()
  const suites = useTestSuites()
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [showForm, setShowForm] = useState(false)

  const selectedEval = evaluations.find((e) => e.eval_id === selectedId) ?? null
  const hasRunning = evaluations.some(
    (e) => e.status !== 'complete' && e.status !== 'error' && e.status !== 'pending',
  )

  const handleStart = async (req: StartEvaluationRequest) => {
    const ev = await startEvaluation(req)
    if (ev) {
      setSelectedId(ev.eval_id)
      setShowForm(false)
    }
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100vh', background: 'var(--black)', overflow: 'hidden' }}>
      {/* ── Header ──────────────────────────────────────────────────── */}
      <header style={{
        height: 56,
        flexShrink: 0,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '0 28px',
        borderBottom: '1px solid var(--gold)',
        background: 'var(--black)',
      }}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
          <span style={{
            fontFamily: "'Inter', sans-serif",
            fontWeight: 600,
            fontSize: 16,
            letterSpacing: '0.3em',
            textTransform: 'uppercase',
            color: 'var(--white)',
          }}>
            AgentProbe
          </span>
          <div style={{ height: 2, background: 'var(--gold)', width: '100%' }} />
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 20 }}>
          {hasRunning && (
            <span style={{
              display: 'flex',
              alignItems: 'center',
              gap: 6,
              fontSize: 11,
              letterSpacing: '0.12em',
              textTransform: 'uppercase',
              color: 'var(--gold)',
            }}>
              <span style={{
                width: 6,
                height: 6,
                borderRadius: '50%',
                background: 'var(--gold)',
                animation: 'pulse 2s infinite',
              }} />
              Live
            </span>
          )}
          <span style={{
            fontSize: 10,
            letterSpacing: '0.15em',
            textTransform: 'uppercase',
            color: 'var(--gray-2)',
          }}>
            Multi-Agent Testing
          </span>
        </div>
      </header>

      {/* ── Body ────────────────────────────────────────────────────── */}
      <div style={{ flex: 1, display: 'flex', overflow: 'hidden' }}>
        {/* Sidebar */}
        <aside style={{
          width: 300,
          flexShrink: 0,
          display: 'flex',
          flexDirection: 'column',
          borderRight: '1px solid var(--border)',
          background: 'var(--black)',
        }}>
          {/* New eval button */}
          <div style={{ padding: '16px 16px 12px' }}>
            <button
              onClick={() => setShowForm(!showForm)}
              style={{
                width: '100%',
                background: showForm ? 'transparent' : 'var(--gold)',
                color: showForm ? 'var(--gray-1)' : 'var(--black)',
                border: showForm ? '1px solid var(--border)' : '1px solid var(--gold)',
                padding: '10px 16px',
                fontSize: 11,
                fontWeight: 600,
                letterSpacing: '0.15em',
                textTransform: 'uppercase',
                cursor: 'pointer',
                transition: 'all 0.2s ease',
                borderRadius: 0,
              }}
              onMouseEnter={(e) => {
                if (!showForm) {
                  e.currentTarget.style.background = 'var(--gold-bright)'
                }
              }}
              onMouseLeave={(e) => {
                if (!showForm) {
                  e.currentTarget.style.background = 'var(--gold)'
                }
              }}
            >
              {showForm ? '✕ Cancel' : '+ New Evaluation'}
            </button>
          </div>

          <div style={{ height: 1, background: 'var(--border)', margin: '0 16px' }} />

          {/* Eval list / Form */}
          <div style={{ flex: 1, overflowY: 'auto', padding: '12px 16px' }}>
            {showForm ? (
              <NewEvaluationForm
                suites={suites}
                onSubmit={handleStart}
                loading={loading}
                error={error}
              />
            ) : (
              <EvaluationList
                evaluations={evaluations}
                selectedId={selectedId}
                onSelect={setSelectedId}
              />
            )}
          </div>
        </aside>

        {/* Main */}
        <main style={{
          flex: 1,
          overflowY: 'auto',
          padding: '32px 36px',
          background: 'var(--black)',
        }}>
          {selectedEval ? (
            <EvaluationDetail evaluation={selectedEval} />
          ) : (
            <div style={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              height: '100%',
              gap: 24,
              textAlign: 'center',
            }}>
              <div style={{ marginBottom: 8 }}>
                <div style={{
                  fontSize: 11,
                  letterSpacing: '0.3em',
                  textTransform: 'uppercase',
                  color: 'var(--gray-2)',
                  marginBottom: 12,
                }}>
                  AI Agent Testing Platform
                </div>
                <h1 style={{
                  fontSize: 36,
                  fontWeight: 300,
                  letterSpacing: '0.2em',
                  textTransform: 'uppercase',
                  color: 'var(--white)',
                  margin: 0,
                }}>
                  AGENT<span style={{ color: 'var(--gold)' }}>PROBE</span>
                </h1>
                <div style={{
                  height: 1,
                  background: 'linear-gradient(to right, transparent, var(--gold), transparent)',
                  margin: '16px auto',
                  width: 200,
                }} />
                <p style={{
                  color: 'var(--gray-1)',
                  maxWidth: 420,
                  margin: '0 auto',
                  lineHeight: 1.7,
                  fontSize: 14,
                }}>
                  Stress-test any AI agent for failures, hallucinations,
                  security vulnerabilities, and reliability issues.
                </p>
              </div>

              <button
                onClick={() => setShowForm(true)}
                style={{
                  background: 'var(--gold)',
                  color: 'var(--black)',
                  border: 'none',
                  padding: '12px 32px',
                  fontSize: 11,
                  fontWeight: 600,
                  letterSpacing: '0.2em',
                  textTransform: 'uppercase',
                  cursor: 'pointer',
                  borderRadius: 0,
                  transition: 'background 0.2s ease',
                }}
                onMouseEnter={(e) => { e.currentTarget.style.background = 'var(--gold-bright)' }}
                onMouseLeave={(e) => { e.currentTarget.style.background = 'var(--gold)' }}
              >
                Start Evaluation
              </button>

              <div style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(3, 1fr)',
                gap: 1,
                width: '100%',
                maxWidth: 560,
                marginTop: 24,
                background: 'var(--border)',
              }}>
                {[
                  { label: 'Agents', value: '7' },
                  { label: 'Test Vectors', value: '45+' },
                  { label: 'Dimensions', value: '5' },
                ].map((s) => (
                  <div key={s.label} style={{
                    background: 'var(--surface)',
                    padding: '20px 16px',
                    textAlign: 'center',
                  }}>
                    <div style={{ fontSize: 28, fontWeight: 300, color: 'var(--gold)', marginBottom: 4 }}>{s.value}</div>
                    <div style={{ fontSize: 10, letterSpacing: '0.15em', textTransform: 'uppercase', color: 'var(--gray-2)' }}>{s.label}</div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </main>
      </div>
    </div>
  )
}
