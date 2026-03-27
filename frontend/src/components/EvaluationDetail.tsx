import { useState, useEffect } from 'react'
import { api } from '../api/client'
import { useEventStream } from '../hooks/useEventStream'
import { AgentGraph } from './AgentGraph'
import { EventFeed } from './EventFeed'
import { ScoreChart } from './ScoreChart'
import { ScoreGauge } from './ScoreGauge'
import { StatusBadge } from './StatusBadge'
import type { EvaluationSummary, EvaluationReport } from '../types'

interface Props {
  evaluation: EvaluationSummary
}

const Card = ({ children, style }: { children: React.ReactNode; style?: React.CSSProperties }) => (
  <div style={{
    background: '#111113',
    border: '1px solid #27272a',
    padding: '16px 20px',
    ...style,
  }}>
    {children}
  </div>
)

const SectionLabel = ({ children }: { children: React.ReactNode }) => (
  <div style={{
    fontSize: 10,
    fontWeight: 600,
    letterSpacing: '0.2em',
    textTransform: 'uppercase',
    color: '#7A6030',
    marginBottom: 12,
  }}>
    ▸ {children}
  </div>
)

export function EvaluationDetail({ evaluation }: Props) {
  const { events, connected, done } = useEventStream(
    evaluation.status !== 'complete' && evaluation.status !== 'error' ? evaluation.eval_id : null,
  )
  const [report, setReport] = useState<EvaluationReport | null>(null)

  useEffect(() => {
    if (evaluation.status === 'complete' || done) {
      api.get<EvaluationReport>(`/evaluations/${evaluation.eval_id}/report`)
        .then(({ data }) => setReport(data))
        .catch(() => setReport(null))
    }
  }, [evaluation.eval_id, evaluation.status, done])

  const scoreBreakdown = report?.summary?.score_breakdown

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>

      {/* ── Header ──────────────────────────────────────────────────── */}
      <div style={{
        display: 'flex',
        alignItems: 'flex-start',
        justifyContent: 'space-between',
        paddingBottom: 20,
        borderBottom: '1px solid #27272a',
      }}>
        <div>
          <div style={{
            fontFamily: 'monospace',
            fontSize: 10,
            color: '#52525b',
            marginBottom: 6,
          }}>
            {evaluation.eval_id}
          </div>
          <h2 style={{
            margin: 0,
            fontSize: 20,
            fontWeight: 400,
            letterSpacing: '0.1em',
            textTransform: 'uppercase',
            color: '#FAFAFA',
          }}>
            {evaluation.suite}
          </h2>
          <div style={{
            fontSize: 11,
            color: '#A1A1AA',
            marginTop: 4,
            letterSpacing: '0.05em',
          }}>
            {evaluation.target_url}
          </div>
          <div style={{ marginTop: 10 }}>
            <StatusBadge status={evaluation.status} />
          </div>
        </div>

        {evaluation.overall_score != null && (
          <div>
            <ScoreGauge score={evaluation.overall_score} size="lg" />
          </div>
        )}
      </div>

      {/* ── Stats row ───────────────────────────────────────────────── */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 1, background: '#27272a' }}>
        {[
          { label: 'Total Tests', value: evaluation.total_tests,  color: '#FAFAFA' },
          { label: 'Passed',      value: evaluation.passed,        color: '#22c55e' },
          { label: 'Failed',      value: evaluation.failed,        color: '#ef4444' },
        ].map((s) => (
          <div key={s.label} style={{
            background: '#111113',
            padding: '16px 20px',
            textAlign: 'center',
          }}>
            <div style={{
              fontSize: 28,
              fontWeight: 300,
              color: s.color,
              fontVariantNumeric: 'tabular-nums',
              lineHeight: 1,
              marginBottom: 6,
            }}>
              {s.value}
            </div>
            <div style={{
              fontSize: 9,
              letterSpacing: '0.2em',
              textTransform: 'uppercase',
              color: '#7A6030',
            }}>
              {s.label}
            </div>
          </div>
        ))}
      </div>

      {/* ── Score chart ─────────────────────────────────────────────── */}
      {scoreBreakdown && Object.keys(scoreBreakdown).length > 0 && (
        <Card>
          <SectionLabel>Score Breakdown</SectionLabel>
          <ScoreChart scores={scoreBreakdown} />
        </Card>
      )}

      {/* ── Graph + feed ────────────────────────────────────────────── */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 1, background: '#27272a' }}>
        <div style={{ background: '#111113', padding: '16px 20px' }}>
          <SectionLabel>Agent Graph</SectionLabel>
          <AgentGraph events={events} />
        </div>

        <div style={{ background: '#111113', overflow: 'hidden', height: 660 }}>
          <EventFeed events={events} connected={connected} />
        </div>
      </div>

      {/* ── Narrative ───────────────────────────────────────────────── */}
      {report?.narrative && (
        <Card>
          <SectionLabel>Report</SectionLabel>
          <p style={{
            margin: 0,
            fontSize: 13,
            color: '#A1A1AA',
            whiteSpace: 'pre-wrap',
            lineHeight: 1.8,
          }}>
            {report.narrative}
          </p>
        </Card>
      )}
    </div>
  )
}
