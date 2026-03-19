import { useState, useEffect, useCallback } from 'react'
import { api } from '../api/client'
import type { EvaluationSummary, TestSuiteInfo, StartEvaluationRequest } from '../types'

export function useEvaluations() {
  const [evaluations, setEvaluations] = useState<EvaluationSummary[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchEvaluations = useCallback(async () => {
    try {
      const { data } = await api.get<EvaluationSummary[]>('/evaluations')
      setEvaluations(data)
    } catch (err) {
      console.error('Failed to fetch evaluations:', err)
    }
  }, [])

  useEffect(() => {
    fetchEvaluations()
    const interval = setInterval(fetchEvaluations, 3000)
    return () => clearInterval(interval)
  }, [fetchEvaluations])

  const startEvaluation = useCallback(async (request: StartEvaluationRequest) => {
    setLoading(true)
    setError(null)
    try {
      const { data } = await api.post<EvaluationSummary>('/evaluations', request)
      await fetchEvaluations()
      return data
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || 'Failed to start evaluation'
      setError(msg)
      return null
    } finally {
      setLoading(false)
    }
  }, [fetchEvaluations])

  return { evaluations, loading, error, startEvaluation, refetch: fetchEvaluations }
}

export function useTestSuites() {
  const [suites, setSuites] = useState<TestSuiteInfo[]>([])

  useEffect(() => {
    api.get<TestSuiteInfo[]>('/test-suites').then(({ data }) => setSuites(data)).catch(console.error)
  }, [])

  return suites
}
