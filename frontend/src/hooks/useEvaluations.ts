import { useState, useEffect, useCallback } from 'react'
import { api } from '../api/client'
import type { EvaluationSummary, TestSuiteInfo, StartEvaluationRequest } from '../types'

export function useEvaluations() {
  const [evaluations, setEvaluations] = useState<EvaluationSummary[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Poll only in-progress evals started this session — never load from DB on mount
  useEffect(() => {
    const running = evaluations.filter(
      (e) => e.status !== 'complete' && e.status !== 'error'
    )
    if (running.length === 0) return

    const interval = setInterval(async () => {
      try {
        const updates = await Promise.all(
          running.map((e) =>
            api.get<EvaluationSummary>(`/evaluations/${e.eval_id}`).then((r) => r.data)
          )
        )
        setEvaluations((prev) =>
          prev.map((e) => updates.find((u) => u.eval_id === e.eval_id) ?? e)
        )
      } catch (err) {
        console.error('Failed to poll evaluations:', err)
      }
    }, 3000)

    return () => clearInterval(interval)
  }, [evaluations])

  const startEvaluation = useCallback(async (request: StartEvaluationRequest) => {
    setLoading(true)
    setError(null)
    try {
      const { data } = await api.post<EvaluationSummary>('/evaluations', request)
      setEvaluations((prev) => [data, ...prev])
      return data
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || 'Failed to start evaluation'
      setError(msg)
      return null
    } finally {
      setLoading(false)
    }
  }, [])

  return { evaluations, loading, error, startEvaluation }
}

export function useTestSuites() {
  const [suites, setSuites] = useState<TestSuiteInfo[]>([])

  useEffect(() => {
    api.get<TestSuiteInfo[]>('/test-suites').then(({ data }) => setSuites(data)).catch(console.error)
  }, [])

  return suites
}
