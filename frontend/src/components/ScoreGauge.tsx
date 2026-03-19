interface Props {
  score: number
  size?: 'sm' | 'lg'
}

function getColor(score: number) {
  if (score >= 0.8) return '#22c55e'
  if (score >= 0.6) return '#eab308'
  return '#ef4444'
}

export function ScoreGauge({ score, size = 'lg' }: Props) {
  const pct = Math.round(score * 100)
  const r = size === 'lg' ? 40 : 24
  const stroke = size === 'lg' ? 8 : 5
  const dim = (r + stroke) * 2
  const circumference = 2 * Math.PI * r
  const dashOffset = circumference - (circumference * pct) / 100
  const color = getColor(score)

  return (
    <div className="flex flex-col items-center gap-1">
      <svg width={dim} height={dim} style={{ transform: 'rotate(-90deg)' }}>
        <circle
          cx={dim / 2} cy={dim / 2} r={r}
          fill="none" stroke="#1e2433" strokeWidth={stroke}
        />
        <circle
          cx={dim / 2} cy={dim / 2} r={r}
          fill="none" stroke={color} strokeWidth={stroke}
          strokeDasharray={circumference}
          strokeDashoffset={dashOffset}
          strokeLinecap="round"
          style={{ transition: 'stroke-dashoffset 0.6s ease' }}
        />
      </svg>
      <span className={`font-bold tabular-nums ${size === 'lg' ? 'text-2xl' : 'text-sm'}`} style={{ color }}>
        {pct}
      </span>
      {size === 'lg' && <span className="text-xs text-gray-400">/ 100</span>}
    </div>
  )
}
