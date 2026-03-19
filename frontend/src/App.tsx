import { useState } from 'react'
import { useEvaluations, useTestSuites } from './hooks/useEvaluations'
import { EvaluationList } from './components/EvaluationList'
import { EvaluationDetail } from './components/EvaluationDetail'
import { NewEvaluationForm } from './components/NewEvaluationForm'
import type { StartEvaluationRequest } from './types'

export default function App() {
  const { evaluations, loading, error, startEvaluation } = useEvaluations()
  const suites = useTestSuites()
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [showForm, setShowForm] = useState(false)

  const selectedEval = evaluations.find((e) => e.eval_id === selectedId) ?? null

  const handleStart = async (req: StartEvaluationRequest) => {
    const ev = await startEvaluation(req)
    if (ev) {
      setSelectedId(ev.eval_id)
      setShowForm(false)
    }
  }

  return (
    <div className="flex h-screen bg-[#0f1117] text-gray-100 overflow-hidden">
      {/* Sidebar */}
      <aside className="w-80 shrink-0 flex flex-col border-r border-gray-800">
        {/* Logo */}
        <div className="px-4 py-4 border-b border-gray-800">
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 bg-blue-600 rounded-lg flex items-center justify-center text-sm font-bold">A</div>
            <span className="font-bold text-gray-100">AgentProbe</span>
            <span className="ml-auto text-xs text-gray-600">v0.1</span>
          </div>
        </div>

        {/* New eval button */}
        <div className="px-3 py-3 border-b border-gray-800">
          <button
            onClick={() => setShowForm(!showForm)}
            className="w-full bg-blue-600 hover:bg-blue-500 text-white font-semibold rounded-lg px-3 py-2 text-sm transition-colors"
          >
            {showForm ? 'Cancel' : '+ New Evaluation'}
          </button>
        </div>

        {/* Form or list */}
        <div className="flex-1 overflow-y-auto p-3">
          {showForm ? (
            <NewEvaluationForm
              suites={suites}
              onSubmit={handleStart}
              loading={loading}
              error={error}
            />
          ) : (
            <EvaluationList
              evaluations={evaluations}
              selectedId={selectedId}
              onSelect={setSelectedId}
            />
          )}
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 overflow-y-auto p-6">
        {selectedEval ? (
          <EvaluationDetail evaluation={selectedEval} />
        ) : (
          <div className="flex flex-col items-center justify-center h-full text-center gap-4">
            <div className="w-16 h-16 bg-blue-600 rounded-2xl flex items-center justify-center text-3xl font-bold">A</div>
            <div>
              <h1 className="text-2xl font-bold text-gray-100 mb-2">AgentProbe</h1>
              <p className="text-gray-400 max-w-md">
                Multi-agent AI stress-testing platform. Start an evaluation to test any AI agent
                for failures, hallucinations, security vulnerabilities, and reliability issues.
              </p>
            </div>
            <button
              onClick={() => setShowForm(true)}
              className="bg-blue-600 hover:bg-blue-500 text-white font-semibold rounded-xl px-6 py-3 transition-colors"
            >
              Start Your First Evaluation
            </button>
          </div>
        )}
      </main>
    </div>
  )
}
