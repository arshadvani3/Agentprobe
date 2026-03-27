import { useEffect, useRef } from 'react'
import type { AgentEvent } from '../types'

const AGENT_COLOR: Record<string, string> = {
  supervisor:         '#C9A84C',
  scenario_generator: '#a78bfa',
  security_agent:     '#f87171',
  consistency_agent:  '#67e8f9',
  executor:           '#fbbf24',
  evaluator:          '#fb923c',
  report_generator:   '#86efac',
  system:             '#52525b',
}

const EVENT_COLOR: Record<string, string> = {
  plan_created:       '#93c5fd',
  tests_generated:    '#c4b5fd',
  test_executed:      '#fcd34d',
  test_evaluated:     '#fdba74',
  security_finding:   '#fca5a5',
  consistency_result: '#a5f3fc',
  report_ready:       '#86efac',
  complete:           '#86efac',
  error:              '#fca5a5',
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
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      {/* Header */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '10px 14px',
        borderBottom: '1px solid #27272a',
        flexShrink: 0,
      }}>
        <span style={{
          fontSize: 10,
          fontWeight: 600,
          letterSpacing: '0.15em',
          textTransform: 'uppercase',
          color: '#A1A1AA',
        }}>
          Live Feed
        </span>
        <span style={{
          display: 'flex',
          alignItems: 'center',
          gap: 5,
          fontSize: 10,
          letterSpacing: '0.1em',
          textTransform: 'uppercase',
          color: connected ? '#C9A84C' : '#52525b',
        }}>
          <span style={{
            width: 5,
            height: 5,
            borderRadius: '50%',
            background: connected ? '#C9A84C' : '#52525b',
            animation: connected ? 'pulse 2s infinite' : 'none',
          }} />
          {connected ? 'Connected' : 'Offline'}
        </span>
      </div>

      {/* Events */}
      <div style={{
        flex: 1,
        overflowY: 'auto',
        padding: '8px 0',
        fontFamily: 'monospace',
        fontSize: 11,
      }}>
        {events.length === 0 && (
          <div style={{
            textAlign: 'center',
            color: '#52525b',
            marginTop: 32,
            fontSize: 11,
            letterSpacing: '0.1em',
          }}>
            Waiting for events…
          </div>
        )}

        {events.map((e, i) => {
          const isNewest = i === events.length - 1
          return (
            <div
              key={i}
              style={{
                display: 'flex',
                gap: 8,
                padding: '3px 14px',
                lineHeight: 1.6,
                borderLeft: isNewest ? '2px solid #C9A84C' : '2px solid transparent',
                background: isNewest ? '#111113' : 'transparent',
              }}
            >
              <span style={{ color: '#52525b', flexShrink: 0 }}>
                {e.timestamp ? new Date(e.timestamp).toLocaleTimeString() : '--:--:--'}
              </span>
              <span style={{ color: AGENT_COLOR[e.agent] ?? '#A1A1AA', flexShrink: 0 }}>
                {e.agent}
              </span>
              <span style={{ color: EVENT_COLOR[e.type] ?? '#FAFAFA' }}>
                {e.type}
              </span>
              {e.data && Object.keys(e.data).length > 0 && (
                <span style={{ color: '#52525b', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {JSON.stringify(e.data)}
                </span>
              )}
            </div>
          )
        })}
        <div ref={bottomRef} />
      </div>
    </div>
  )
}
