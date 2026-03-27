import { useMemo } from 'react'
import {
  ReactFlow,
  type Node,
  type Edge,
} from '@xyflow/react'
import '@xyflow/react/dist/style.css'
import type { AgentEvent } from '../types'

const AGENT_NODES: { id: string; label: string; x: number; y: number }[] = [
  { id: 'supervisor',         label: 'Supervisor',         x: 250, y: 20  },
  { id: 'scenario_generator', label: 'Scenario\nGenerator', x: 50,  y: 140 },
  { id: 'security_agent',     label: 'Security\nAgent',     x: 220, y: 140 },
  { id: 'consistency_agent',  label: 'Consistency\nAgent',  x: 390, y: 140 },
  { id: 'executor',           label: 'Executor',            x: 220, y: 260 },
  { id: 'evaluator',          label: 'Evaluator',           x: 220, y: 370 },
  { id: 'report_generator',   label: 'Report\nGenerator',   x: 220, y: 480 },
]

const EDGES: Edge[] = [
  { id: 'e1', source: 'supervisor',         target: 'scenario_generator', animated: false },
  { id: 'e2', source: 'supervisor',         target: 'security_agent',     animated: false },
  { id: 'e3', source: 'supervisor',         target: 'consistency_agent',  animated: false },
  { id: 'e4', source: 'scenario_generator', target: 'executor',           animated: false },
  { id: 'e5', source: 'security_agent',     target: 'executor',           animated: false },
  { id: 'e6', source: 'consistency_agent',  target: 'executor',           animated: false },
  { id: 'e7', source: 'executor',           target: 'evaluator',          animated: false },
  { id: 'e8', source: 'evaluator',          target: 'report_generator',   animated: false },
]

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
  const agentOrder = [
    'supervisor', 'scenario_generator', 'security_agent',
    'consistency_agent', 'executor', 'evaluator', 'report_generator',
  ]
  const active = getActiveAgents(events)
  for (const e of events) {
    if (e.agent && e.agent !== 'system') {
      const idx = agentOrder.indexOf(e.agent)
      if (idx > -1) agentOrder.slice(0, idx).forEach((a) => completed.add(a))
    }
  }
  for (const a of active) completed.delete(a)
  return completed
}

interface Props {
  events: AgentEvent[]
}

export function AgentGraph({ events }: Props) {
  const activeAgents   = getActiveAgents(events)
  const completedAgents = getCompletedAgents(events)

  const nodes: Node[] = useMemo(() => AGENT_NODES.map((n) => {
    const isActive   = activeAgents.has(n.id)
    const isComplete = completedAgents.has(n.id)

    let bg     = '#18181b'
    let border = '#27272a'
    let color  = '#A1A1AA'
    let shadow = 'none'

    if (isActive) {
      bg     = '#7A6030'
      border = '#C9A84C'
      color  = '#E8C96A'
      shadow = '0 0 14px #C9A84C44'
    } else if (isComplete) {
      bg     = '#18181b'
      border = '#22c55e'
      color  = '#86efac'
    }

    return {
      id: n.id,
      position: { x: n.x, y: n.y },
      data: { label: n.label },
      style: {
        background: bg,
        border: `1px solid ${border}`,
        color,
        borderRadius: 0,
        padding: '8px 14px',
        fontSize: 11,
        fontWeight: 500,
        fontFamily: "'Inter', sans-serif",
        letterSpacing: '0.05em',
        whiteSpace: 'pre-line' as const,
        textAlign: 'center' as const,
        minWidth: 100,
        boxShadow: shadow,
        transition: 'all 0.3s ease',
      },
    }
  }), [activeAgents, completedAgents])

  const edges: Edge[] = useMemo(() => EDGES.map((e) => ({
    ...e,
    style: {
      stroke: activeAgents.has(e.source) ? '#C9A84C' : '#27272a',
      strokeWidth: activeAgents.has(e.source) ? 1.5 : 1,
    },
    animated: activeAgents.has(e.source),
  })), [activeAgents])

  return (
    <div style={{
      height: 580,
      background: '#09090b',
      border: '1px solid #27272a',
    }}>
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
      />
    </div>
  )
}
