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

export function EvaluationDetail({ evaluation }: Props) {
  const { events, connected, done } = useEventStream(
    evaluation.status !== 'complete' && evaluation.status !== 'error' ? evaluation.eval_id : null
  )
  const [report, setReport] = useState<EvaluationReport | null>(null)

  // Fetch report when eval completes
  useEffect(() => {
    if (evaluation.status === 'complete' || done) {
      api.get<EvaluationReport>(`/evaluations/${evaluation.eval_id}/report`)
        .then(({ data }) => setReport(data))
        .catch(() => setReport(null))
    }
  }, [evaluation.eval_id, evaluation.status, done])

  const scoreBreakdown = report?.summary?.score_breakdown

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <div className="font-mono text-xs text-gray-500 mb-1">{evaluation.eval_id}</div>
          <h2 className="text-lg font-bold text-gray-100">{evaluation.suite}</h2>
          <div className="text-sm text-gray-400">{evaluation.target_url}</div>
        </div>
        <div className="flex flex-col items-end gap-2">
          <StatusBadge status={evaluation.status} />
          {evaluation.overall_score != null && (
            <ScoreGauge score={evaluation.overall_score} size="lg" />
          )}
        </div>
      </div>

      {/* Stats row */}
      <div className="grid grid-cols-3 gap-3">
        {[
          { label: 'Total Tests', value: evaluation.total_tests },
          { label: 'Passed', value: evaluation.passed, color: 'text-green-400' },
          { label: 'Failed', value: evaluation.failed, color: 'text-red-400' },
        ].map((s) => (
          <div key={s.label} className="bg-gray-900 border border-gray-800 rounded-lg p-3 text-center">
            <div className={`text-2xl font-bold tabular-nums ${s.color || 'text-gray-100'}`}>{s.value}</div>
            <div className="text-xs text-gray-500 mt-0.5">{s.label}</div>
          </div>
        ))}
      </div>

      {/* Score radar (when report available) */}
      {scoreBreakdown && Object.keys(scoreBreakdown).length > 0 && (
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
          <div className="text-sm font-semibold text-gray-300 mb-3">Score Breakdown</div>
          <ScoreChart scores={scoreBreakdown} />
        </div>
      )}

      {/* Agent graph + event feed */}
      <div className="grid grid-cols-2 gap-4">
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-3">
          <div className="text-sm font-semibold text-gray-300 mb-3">Agent Graph</div>
          <AgentGraph events={events} />
        </div>

        <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden" style={{ height: 640 }}>
          <EventFeed events={events} connected={connected} />
        </div>
      </div>

      {/* Narrative report */}
      {report?.narrative && (
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
          <div className="text-sm font-semibold text-gray-300 mb-3">Narrative Report</div>
          <p className="text-sm text-gray-400 whitespace-pre-wrap leading-relaxed">{report.narrative}</p>
        </div>
      )}
    </div>
  )
}
