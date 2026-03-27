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
      <div style={{
        textAlign: 'center',
        color: '#52525b',
        fontSize: 12,
        paddingTop: 40,
        lineHeight: 1.8,
      }}>
        No evaluations yet.
        <br />
        Start one to begin testing.
      </div>
    )
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
      {evaluations.map((ev) => {
        const isSelected = selectedId === ev.eval_id
        return (
          <button
            key={ev.eval_id}
            onClick={() => onSelect(ev.eval_id)}
            style={{
              width: '100%',
              textAlign: 'left',
              padding: '12px 14px',
              background: isSelected ? '#111113' : 'transparent',
              border: 'none',
              borderLeft: isSelected ? '3px solid #C9A84C' : '3px solid transparent',
              cursor: 'pointer',
              transition: 'all 0.15s ease',
              display: 'block',
            }}
            onMouseEnter={(e) => {
              if (!isSelected) {
                e.currentTarget.style.background = '#111113'
                e.currentTarget.style.borderLeftColor = '#7A6030'
              }
            }}
            onMouseLeave={(e) => {
              if (!isSelected) {
                e.currentTarget.style.background = 'transparent'
                e.currentTarget.style.borderLeftColor = 'transparent'
              }
            }}
          >
            <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 8 }}>
              <div style={{ minWidth: 0, flex: 1 }}>
                <div style={{
                  fontFamily: 'monospace',
                  fontSize: 10,
                  color: '#52525b',
                  marginBottom: 3,
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  whiteSpace: 'nowrap',
                }}>
                  {ev.eval_id}
                </div>
                <div style={{
                  fontSize: 13,
                  fontWeight: 500,
                  color: '#FAFAFA',
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  whiteSpace: 'nowrap',
                  marginBottom: 2,
                }}>
                  {ev.suite}
                </div>
                <div style={{
                  fontSize: 11,
                  color: '#52525b',
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  whiteSpace: 'nowrap',
                }}>
                  {ev.target_url}
                </div>
              </div>
              <div style={{ flexShrink: 0 }}>
                {ev.overall_score != null ? (
                  <ScoreGauge score={ev.overall_score} size="sm" />
                ) : (
                  <StatusBadge status={ev.status} />
                )}
              </div>
            </div>

            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: 8,
              marginTop: 8,
              fontSize: 10,
              color: '#52525b',
            }}>
              <span>{ev.passed}/{ev.total_tests} passed</span>
              <span style={{ color: '#27272a' }}>·</span>
              <span style={{ textTransform: 'uppercase', letterSpacing: '0.08em' }}>{ev.depth}</span>
              {ev.overall_score != null && (
                <>
                  <span style={{ color: '#27272a' }}>·</span>
                  <StatusBadge status={ev.status} />
                </>
              )}
            </div>
          </button>
        )
      })}
    </div>
  )
}
