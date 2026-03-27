import {
  RadarChart,
  Radar,
  PolarGrid,
  PolarAngleAxis,
  ResponsiveContainer,
  Tooltip,
} from 'recharts'
import type { ScoreBreakdown } from '../types'

interface Props {
  scores: ScoreBreakdown
}

export function ScoreChart({ scores }: Props) {
  const data = [
    { subject: 'ACCURACY',    value: Math.round((scores.accuracy    ?? 0) * 100) },
    { subject: 'RELEVANCE',   value: Math.round((scores.relevance   ?? 0) * 100) },
    { subject: 'SAFETY',      value: Math.round((scores.safety      ?? 0) * 100) },
    { subject: 'HELPFULNESS', value: Math.round((scores.helpfulness ?? 0) * 100) },
    { subject: 'HALLUC FREE', value: Math.round((scores.hallucination ?? 0) * 100) },
  ]

  return (
    <ResponsiveContainer width="100%" height={200}>
      <RadarChart data={data} margin={{ top: 10, right: 20, bottom: 10, left: 20 }}>
        <PolarGrid stroke="#27272a" />
        <PolarAngleAxis
          dataKey="subject"
          tick={{ fill: '#A1A1AA', fontSize: 9, fontWeight: 500, letterSpacing: 1 }}
        />
        <Radar
          name="Score"
          dataKey="value"
          stroke="#C9A84C"
          fill="#C9A84C"
          fillOpacity={0.12}
          strokeWidth={1.5}
        />
        <Tooltip
          contentStyle={{
            background: '#111113',
            border: '1px solid #27272a',
            borderRadius: 0,
            fontSize: 11,
          }}
          labelStyle={{ color: '#A1A1AA', letterSpacing: '0.1em' }}
          formatter={(v) => [`${v}%`, 'Score']}
        />
      </RadarChart>
    </ResponsiveContainer>
  )
}
