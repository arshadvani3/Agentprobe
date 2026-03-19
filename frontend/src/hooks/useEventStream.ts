import { useState, useEffect, useRef, useCallback } from 'react'
import { createWebSocket } from '../api/client'
import type { AgentEvent } from '../types'

export function useEventStream(evalId: string | null) {
  const [events, setEvents] = useState<AgentEvent[]>([])
  const [connected, setConnected] = useState(false)
  const [done, setDone] = useState(false)
  const wsRef = useRef<WebSocket | null>(null)
  const doneRef = useRef(false)
  const reconnectTimer = useRef<ReturnType<typeof setTimeout> | null>(null)

  const connect = useCallback(() => {
    if (!evalId || doneRef.current) return

    const ws = createWebSocket(evalId)
    wsRef.current = ws

    ws.onopen = () => setConnected(true)

    ws.onmessage = (e) => {
      try {
        const event: AgentEvent = JSON.parse(e.data)
        if (event.type === 'ping') return
        if (event.type === 'complete') {
          doneRef.current = true
          setDone(true)
          return
        }
        // Ignore stream timeout errors — we'll reconnect
        if (event.type === 'error' && (event.data as { message?: string })?.message === 'Stream timeout') {
          return
        }
        setEvents((prev) => [...prev, event])
      } catch {
        // ignore parse errors
      }
    }

    ws.onclose = () => {
      setConnected(false)
      // Auto-reconnect if eval isn't done yet
      if (!doneRef.current) {
        reconnectTimer.current = setTimeout(connect, 2000)
      }
    }

    ws.onerror = () => {
      setConnected(false)
    }
  }, [evalId])

  useEffect(() => {
    if (!evalId) return

    setEvents([])
    setDone(false)
    doneRef.current = false

    connect()

    return () => {
      doneRef.current = true
      if (reconnectTimer.current) clearTimeout(reconnectTimer.current)
      wsRef.current?.close()
      wsRef.current = null
    }
  }, [evalId, connect])

  return { events, connected, done }
}
