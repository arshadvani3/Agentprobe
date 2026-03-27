import type { EvalStatus } from '../types'

const STATUS_CONFIG: Record<EvalStatus, { color: string; dot: string; pulse: boolean }> = {
  pending:    { color: '#A1A1AA', dot: '#52525b',  pulse: false },
  planning:   { color: '#93c5fd', dot: '#3b82f6',  pulse: true  },
  generating: { color: '#c4b5fd', dot: '#8b5cf6',  pulse: true  },
  executing:  { color: '#fcd34d', dot: '#f59e0b',  pulse: true  },
  evaluating: { color: '#fdba74', dot: '#f97316',  pulse: true  },
  complete:   { color: '#86efac', dot: '#22c55e',  pulse: false },
  error:      { color: '#fca5a5', dot: '#ef4444',  pulse: false },
}

interface Props {
  status: EvalStatus
}

export function StatusBadge({ status }: Props) {
  const cfg = STATUS_CONFIG[status] ?? STATUS_CONFIG.pending
  return (
    <span style={{
      display: 'inline-flex',
      alignItems: 'center',
      gap: 6,
      fontSize: 10,
      fontWeight: 600,
      letterSpacing: '0.12em',
      textTransform: 'uppercase',
      color: cfg.color,
    }}>
      <span style={{
        width: 5,
        height: 5,
        borderRadius: '50%',
        background: cfg.dot,
        flexShrink: 0,
        animation: cfg.pulse ? 'pulse 2s ease-in-out infinite' : 'none',
      }} />
      {status}
    </span>
  )
}
