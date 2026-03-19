import { useEffect, useRef } from 'react'
import type { AgentEvent } from '../types'

const EVENT_COLORS: Record<string, string> = {
  plan_created: 'text-blue-400',
  tests_generated: 'text-purple-400',
  test_executed: 'text-yellow-400',
  test_evaluated: 'text-orange-400',
  security_finding: 'text-red-400',
  consistency_result: 'text-cyan-400',
  report_ready: 'text-green-400',
  complete: 'text-green-400',
  error: 'text-red-400',
}

const AGENT_COLORS: Record<string, string> = {
  supervisor: 'text-blue-300',
  scenario_generator: 'text-purple-300',
  security_agent: 'text-red-300',
  consistency_agent: 'text-cyan-300',
  executor: 'text-yellow-300',
  evaluator: 'text-orange-300',
  report_generator: 'text-green-300',
  system: 'text-gray-400',
}

interface Props {
  events: AgentEvent[]
  connected: boolean
}

export function EventFeed({ events, connected }: Props) {
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [events])

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between px-4 py-2 border-b border-gray-800">
        <span className="text-sm font-semibold text-gray-300">Live Events</span>
        <span className={`flex items-center gap-1.5 text-xs ${connected ? 'text-green-400' : 'text-gray-500'}`}>
          <span className={`w-1.5 h-1.5 rounded-full ${connected ? 'bg-green-400 animate-pulse' : 'bg-gray-500'}`} />
          {connected ? 'connected' : 'disconnected'}
        </span>
      </div>
      <div className="flex-1 overflow-y-auto p-3 space-y-1 font-mono text-xs">
        {events.length === 0 && (
          <div className="text-gray-600 text-center mt-8">Waiting for events...</div>
        )}
        {events.map((e, i) => (
          <div key={i} className="flex gap-2 leading-5">
            <span className="text-gray-600 shrink-0">{e.timestamp ? new Date(e.timestamp).toLocaleTimeString() : '--:--:--'}</span>
            <span className={`shrink-0 ${AGENT_COLORS[e.agent] || 'text-gray-400'}`}>[{e.agent}]</span>
            <span className={`${EVENT_COLORS[e.type] || 'text-gray-300'}`}>{e.type}</span>
            {e.data && Object.keys(e.data).length > 0 && (
              <span className="text-gray-500 truncate">{JSON.stringify(e.data)}</span>
            )}
          </div>
        ))}
        <div ref={bottomRef} />
      </div>
    </div>
  )
}
