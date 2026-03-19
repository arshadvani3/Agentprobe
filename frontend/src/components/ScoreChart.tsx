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
    { subject: 'Accuracy', value: Math.round((scores.accuracy ?? 0) * 100) },
    { subject: 'Relevance', value: Math.round((scores.relevance ?? 0) * 100) },
    { subject: 'Safety', value: Math.round((scores.safety ?? 0) * 100) },
    { subject: 'Helpfulness', value: Math.round((scores.helpfulness ?? 0) * 100) },
    { subject: 'Hallucination\nFree', value: Math.round((scores.hallucination ?? 0) * 100) },
  ]

  return (
    <ResponsiveContainer width="100%" height={220}>
      <RadarChart data={data}>
        <PolarGrid stroke="#1e2433" />
        <PolarAngleAxis dataKey="subject" tick={{ fill: '#64748b', fontSize: 11 }} />
        <Radar
          name="Score"
          dataKey="value"
          stroke="#3b82f6"
          fill="#3b82f6"
          fillOpacity={0.25}
        />
        <Tooltip
          contentStyle={{ background: '#1e2433', border: '1px solid #334155', borderRadius: 8 }}
          labelStyle={{ color: '#94a3b8' }}
          formatter={(v) => [`${v}%`, 'Score']}
        />
      </RadarChart>
    </ResponsiveContainer>
  )
}
