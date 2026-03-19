import type { EvaluationSummary } from '../types'
import { StatusBadge } from './StatusBadge'
import { ScoreGauge } from './ScoreGauge'

interface Props {
  evaluations: EvaluationSummary[]
  selectedId: string | null
  onSelect: (id: string) => void
}

export function EvaluationList({ evaluations, selectedId, onSelect }: Props) {
  if (evaluations.length === 0) {
    return (
      <div className="text-center text-gray-600 text-sm py-10">
        No evaluations yet.<br />Start one to begin testing.
      </div>
    )
  }

  return (
    <div className="space-y-2">
      {evaluations.map((ev) => (
        <button
          key={ev.eval_id}
          onClick={() => onSelect(ev.eval_id)}
          className={`w-full text-left p-3 rounded-lg border transition-colors ${
            selectedId === ev.eval_id
              ? 'border-blue-500 bg-blue-950'
              : 'border-gray-800 bg-gray-900 hover:border-gray-600'
          }`}
        >
          <div className="flex items-start justify-between gap-2">
            <div className="min-w-0">
              <div className="text-xs font-mono text-gray-500 mb-0.5">{ev.eval_id}</div>
              <div className="text-sm font-medium text-gray-100 truncate">{ev.suite}</div>
              <div className="text-xs text-gray-500 truncate">{ev.target_url}</div>
            </div>
            <div className="shrink-0">
              {ev.overall_score != null ? (
                <ScoreGauge score={ev.overall_score} size="sm" />
              ) : (
                <StatusBadge status={ev.status} />
              )}
            </div>
          </div>
          <div className="mt-2 flex items-center gap-3 text-xs text-gray-500">
            <span>{ev.passed}/{ev.total_tests} passed</span>
            <span>·</span>
            <span>{ev.depth}</span>
            {ev.overall_score != null && (
              <>
                <span>·</span>
                <StatusBadge status={ev.status} />
              </>
            )}
          </div>
        </button>
      ))}
    </div>
  )
}
