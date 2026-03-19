export type TargetType = 'ollama' | 'openai' | 'simple'
export type EvalDepth = 'quick' | 'standard' | 'deep'
export type EvalStatus = 'pending' | 'planning' | 'generating' | 'executing' | 'evaluating' | 'complete' | 'error'

export interface StartEvaluationRequest {
  target_url: string
  target_type: TargetType
  suite: string
  depth: EvalDepth
  model?: string
  categories?: string[]
  timeout?: number
  target_description?: string
  api_key?: string
  demo?: boolean
  custom_suite_id?: string | null
}

export interface CustomSuiteInfo {
  suite_id: string
  name: string
  description: string
  test_count: number
  categories: string[]
}

export interface EvaluationSummary {
  eval_id: string
  target_url: string
  target_type: TargetType
  suite: string
  depth: EvalDepth
  status: EvalStatus
  created_at: string
  completed_at?: string
  overall_score?: number
  total_tests: number
  passed: number
  failed: number
}

export interface TestSuiteInfo {
  name: string
  description: string
  test_count: number
  categories: string[]
}

export interface AgentEvent {
  event_id?: string
  eval_id?: string
  agent: string
  type: string
  data: Record<string, unknown>
  timestamp?: string
}

export interface ScoreBreakdown {
  accuracy?: number
  relevance?: number
  hallucination?: number
  safety?: number
  helpfulness?: number
}

export interface TestResult {
  test_id: string
  input: string
  response: string
  latency_ms: number
  scores: ScoreBreakdown
  passed: boolean
  reasoning: string
  category: string
}

export interface EvaluationReport {
  eval_id: string
  summary: {
    overall_score: number
    total_tests: number
    passed: number
    failed: number
    pass_rate: number
    score_breakdown: ScoreBreakdown
  }
  results_by_category: Record<string, TestResult[]>
  security_findings: unknown[]
  consistency_issues: unknown[]
  narrative: string
}
