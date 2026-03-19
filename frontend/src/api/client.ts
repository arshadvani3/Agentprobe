import axios from 'axios'

export const api = axios.create({
  baseURL: '/api/v1',
  headers: { 'Content-Type': 'application/json' },
})

export function createWebSocket(evalId: string): WebSocket {
  const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws'
  // Use same host as the page — nginx (or Vite dev proxy) routes /api/v1/stream/ to backend
  return new WebSocket(`${protocol}://${window.location.host}/api/v1/stream/${evalId}`)
}
