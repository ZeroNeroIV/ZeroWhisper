import { useState, useCallback, useEffect } from 'react'
import { api } from '@/lib/api'

export interface TransactionProposal {
  kind: 'transaction' | 'transfer'
  intent: string
  amount_original: string
  currency_original: 'JOD' | 'USD'
  description: string | null
  confidence: number
  transaction_date?: string | null
  // kind === 'transaction'
  category?: string
  wallet_id?: string | null
  wallet_name?: string | null
  // kind === 'transfer'
  from_wallet_id?: string
  from_wallet_name?: string
  to_wallet_id?: string
  to_wallet_name?: string
}

export interface SpendingContext {
  category: string
  this_month_total: number
  transaction_count: number
}

export interface WhisperResponse {
  action: 'proposal' | 'reply'
  proposal_id: string | null
  proposal: TransactionProposal | null
  persona_message: string
  spending_context: SpendingContext | null
}

type MessageRole = 'user' | 'whisper'

export interface ChatMessage {
  id: string
  role: MessageRole
  text?: string
  response?: WhisperResponse
  status?: 'confirmed' | 'rejected'
}

const MAX_HISTORY = 200

function storageKey(username: string) {
  return `whisper_history_${username}`
}

function loadHistory(username: string): ChatMessage[] {
  try {
    const raw = localStorage.getItem(storageKey(username))
    if (!raw) return []
    return JSON.parse(raw) as ChatMessage[]
  } catch {
    return []
  }
}

function saveHistory(username: string, messages: ChatMessage[]) {
  try {
    const trimmed = messages.slice(-MAX_HISTORY)
    localStorage.setItem(storageKey(username), JSON.stringify(trimmed))
  } catch {
    // storage quota exceeded — fail silently
  }
}

export function useWhisper(username: string) {
  const [messages, setMessages] = useState<ChatMessage[]>(() => loadHistory(username))
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    saveHistory(username, messages)
  }, [username, messages])

  const clearHistory = useCallback(() => {
    setMessages([])
    localStorage.removeItem(storageKey(username))
  }, [username])

  const sendMessage = useCallback(async (text: string) => {
    const userMsg: ChatMessage = { id: crypto.randomUUID(), role: 'user', text }
    setMessages(prev => [...prev, userMsg])
    setLoading(true)
    try {
      const { data } = await api.post<WhisperResponse>('/api/whisper/parse', { message: text })
      const whisperMsg: ChatMessage = { id: crypto.randomUUID(), role: 'whisper', response: data }
      setMessages(prev => [...prev, whisperMsg])
      return data
    } catch {
      const errorMsg: ChatMessage = {
        id: crypto.randomUUID(),
        role: 'whisper',
        text: 'Sorry, something went wrong. Please try again.',
      }
      setMessages(prev => [...prev, errorMsg])
      return null
    } finally {
      setLoading(false)
    }
  }, [])

  const confirmProposal = useCallback(async (proposalId: string, messageId: string) => {
    await api.post('/api/whisper/confirm', { proposal_id: proposalId })
    setMessages(prev =>
      prev.map(m => (m.id === messageId ? { ...m, status: 'confirmed' as const } : m))
    )
  }, [])

  const rejectProposal = useCallback(async (proposalId: string, messageId: string) => {
    await api.post('/api/whisper/reject', { proposal_id: proposalId })
    setMessages(prev =>
      prev.map(m => (m.id === messageId ? { ...m, status: 'rejected' as const } : m))
    )
  }, [])

  return { messages, loading, sendMessage, confirmProposal, rejectProposal, clearHistory }
}
