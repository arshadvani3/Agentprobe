import axios from 'axios'

const BASE = import.meta.env.VITE_API_URL ?? ''

export const api = axios.create({
  baseURL: `${BASE}/api/v1`,
  headers: { 'Content-Type': 'application/json' },
})

export function createWebSocket(evalId: string): WebSocket {
  const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws'
  if (BASE) {
    const wsBase = BASE.replace('https://', 'wss://').replace('http://', 'ws://')
    return new WebSocket(`${wsBase}/api/v1/stream/${evalId}`)
  }
  return new WebSocket(`${protocol}://${window.location.host}/api/v1/stream/${evalId}`)
}
