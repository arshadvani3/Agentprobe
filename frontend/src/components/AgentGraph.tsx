import { useMemo } from 'react'
import {
  ReactFlow,
  Background,
  BackgroundVariant,
  type Node,
  type Edge,
} from '@xyflow/react'
import '@xyflow/react/dist/style.css'
import type { AgentEvent } from '../types'

const AGENT_NODES: { id: string; label: string; x: number; y: number }[] = [
  { id: 'supervisor', label: 'Supervisor', x: 250, y: 20 },
  { id: 'scenario_generator', label: 'Scenario\nGenerator', x: 50, y: 140 },
  { id: 'security_agent', label: 'Security\nAgent', x: 220, y: 140 },
  { id: 'consistency_agent', label: 'Consistency\nAgent', x: 390, y: 140 },
  { id: 'executor', label: 'Executor', x: 220, y: 260 },
  { id: 'evaluator', label: 'Evaluator', x: 220, y: 370 },
  { id: 'report_generator', label: 'Report\nGenerator', x: 220, y: 480 },
]

const EDGES: Edge[] = [
  { id: 'e1', source: 'supervisor', target: 'scenario_generator', animated: false },
  { id: 'e2', source: 'supervisor', target: 'security_agent', animated: false },
  { id: 'e3', source: 'supervisor', target: 'consistency_agent', animated: false },
  { id: 'e4', source: 'scenario_generator', target: 'executor', animated: false },
  { id: 'e5', source: 'security_agent', target: 'executor', animated: false },
  { id: 'e6', source: 'consistency_agent', target: 'executor', animated: false },
  { id: 'e7', source: 'executor', target: 'evaluator', animated: false },
  { id: 'e8', source: 'evaluator', target: 'report_generator', animated: false },
]

// Map event types/agents to active node ids
function getActiveAgents(events: AgentEvent[]): Set<string> {
  const recent = events.slice(-5)
  const active = new Set<string>()
  for (const e of recent) {
    if (e.agent && e.agent !== 'system') active.add(e.agent)
  }
  return active
}

function getCompletedAgents(events: AgentEvent[]): Set<string> {
  const completed = new Set<string>()
  const agentOrder = ['supervisor', 'scenario_generator', 'security_agent', 'consistency_agent', 'executor', 'evaluator', 'report_generator']
  const active = getActiveAgents(events)

  // An agent is complete if a later agent has been seen
  for (const e of events) {
    if (e.agent && e.agent !== 'system') {
      const idx = agentOrder.indexOf(e.agent)
      if (idx > -1) {
        agentOrder.slice(0, idx).forEach(a => completed.add(a))
      }
    }
  }
  // Remove currently active ones from completed
  for (const a of active) completed.delete(a)
  return completed
}

interface Props {
  events: AgentEvent[]
}

export function AgentGraph({ events }: Props) {
  const activeAgents = getActiveAgents(events)
  const completedAgents = getCompletedAgents(events)

  const nodes: Node[] = useMemo(() => AGENT_NODES.map((n) => {
    const isActive = activeAgents.has(n.id)
    const isComplete = completedAgents.has(n.id)

    let bg = '#1e2433'
    let border = '#334155'
    let color = '#94a3b8'

    if (isActive) { bg = '#1e3a5f'; border = '#3b82f6'; color = '#93c5fd' }
    else if (isComplete) { bg = '#14532d'; border = '#22c55e'; color = '#86efac' }

    return {
      id: n.id,
      position: { x: n.x, y: n.y },
      data: { label: n.label },
      style: {
        background: bg,
        border: `2px solid ${border}`,
        color,
        borderRadius: 8,
        padding: '8px 14px',
        fontSize: 12,
        fontWeight: 600,
        whiteSpace: 'pre-line',
        textAlign: 'center' as const,
        minWidth: 100,
        boxShadow: isActive ? `0 0 16px ${border}66` : 'none',
        transition: 'all 0.3s ease',
      },
    }
  }), [activeAgents, completedAgents])

  const edges: Edge[] = useMemo(() => EDGES.map(e => ({
    ...e,
    style: { stroke: '#334155' },
    animated: activeAgents.has(e.source),
  })), [activeAgents])

  return (
    <div style={{ height: 580, background: '#0f1117', borderRadius: 12, border: '1px solid #1e2433' }}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        fitView
        fitViewOptions={{ padding: 0.2 }}
        nodesDraggable={false}
        nodesConnectable={false}
        elementsSelectable={false}
        zoomOnScroll={false}
        panOnDrag={false}
      >
        <Background variant={BackgroundVariant.Dots} gap={20} size={1} color="#1e2433" />
      </ReactFlow>
    </div>
  )
}
