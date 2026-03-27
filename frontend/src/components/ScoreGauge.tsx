interface Props {
  score: number
  size?: 'sm' | 'lg'
}

export function ScoreGauge({ score, size = 'lg' }: Props) {
  const pct = Math.round(score * 100)
  const r = size === 'lg' ? 40 : 22
  const stroke = size === 'lg' ? 6 : 4
  const dim = (r + stroke) * 2
  const circumference = 2 * Math.PI * r
  const dashOffset = circumference - (circumference * pct) / 100

  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 4 }}>
      <svg width={dim} height={dim} style={{ transform: 'rotate(-90deg)' }}>
        {/* Track */}
        <circle
          cx={dim / 2} cy={dim / 2} r={r}
          fill="none"
          stroke="#27272a"
          strokeWidth={stroke}
        />
        {/* Fill */}
        <circle
          cx={dim / 2} cy={dim / 2} r={r}
          fill="none"
          stroke="#C9A84C"
          strokeWidth={stroke}
          strokeDasharray={circumference}
          strokeDashoffset={dashOffset}
          strokeLinecap="butt"
          style={{ transition: 'stroke-dashoffset 0.6s ease' }}
        />
      </svg>
      <span style={{
        fontFamily: "'Inter', monospace",
        fontWeight: 600,
        fontSize: size === 'lg' ? 22 : 12,
        color: '#C9A84C',
        letterSpacing: '0.02em',
        lineHeight: 1,
      }}>
        {pct}
      </span>
      {size === 'lg' && (
        <span style={{
          fontSize: 9,
          letterSpacing: '0.15em',
          textTransform: 'uppercase',
          color: '#7A6030',
        }}>
          Score
        </span>
      )}
    </div>
  )
}
