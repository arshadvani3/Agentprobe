import type { EvalStatus } from '../types'

const STATUS_STYLES: Record<EvalStatus, string> = {
  pending: 'bg-gray-700 text-gray-300',
  planning: 'bg-blue-900 text-blue-300',
  generating: 'bg-purple-900 text-purple-300',
  executing: 'bg-yellow-900 text-yellow-300',
  evaluating: 'bg-orange-900 text-orange-300',
  complete: 'bg-green-900 text-green-300',
  error: 'bg-red-900 text-red-300',
}

const STATUS_DOT: Record<EvalStatus, string> = {
  pending: 'bg-gray-400',
  planning: 'bg-blue-400',
  generating: 'bg-purple-400',
  executing: 'bg-yellow-400 animate-pulse',
  evaluating: 'bg-orange-400 animate-pulse',
  complete: 'bg-green-400',
  error: 'bg-red-400',
}

interface Props {
  status: EvalStatus
}

export function StatusBadge({ status }: Props) {
  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium ${STATUS_STYLES[status]}`}>
      <span className={`w-1.5 h-1.5 rounded-full ${STATUS_DOT[status]}`} />
      {status}
    </span>
  )
}
