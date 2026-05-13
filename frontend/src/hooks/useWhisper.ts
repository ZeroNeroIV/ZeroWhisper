import { useState, useCallback } from 'react'
import { api } from '@/lib/api'

export interface TransactionProposal {
  amount_original: number
  currency_original: 'JOD' | 'USD'
  description: string
  category: string
  confidence: number
}

export interface SpendingContext {
  category: string
  this_month_total: number
  transaction_count: number
}

export interface WhisperResponse {
  proposal_id: string
  proposal: TransactionProposal
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

export function useWhisper() {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [loading, setLoading] = useState(false)

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
      const errorMsg: ChatMessage = { id: crypto.randomUUID(), role: 'whisper', text: 'Sorry, something went wrong. Please try again.' }
      setMessages(prev => [...prev, errorMsg])
      return null
    } finally {
      setLoading(false)
    }
  }, [])

  const confirmProposal = useCallback(async (proposalId: string, messageId: string) => {
    await api.post('/api/whisper/confirm', { proposal_id: proposalId })
    setMessages(prev => prev.map(m => m.id === messageId ? { ...m, status: 'confirmed' as const } : m))
  }, [])

  const rejectProposal = useCallback(async (proposalId: string, messageId: string) => {
    await api.post('/api/whisper/reject', { proposal_id: proposalId })
    setMessages(prev => prev.map(m => m.id === messageId ? { ...m, status: 'rejected' as const } : m))
  }, [])

  return { messages, loading, sendMessage, confirmProposal, rejectProposal }
}
