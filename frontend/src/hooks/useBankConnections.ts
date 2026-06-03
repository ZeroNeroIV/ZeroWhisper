import { useState, useCallback } from 'react'
import { api } from '@/lib/api'

export interface BankConnection {
  id: number
  bank_name: string
  auth_type: string
  account_number: string
  is_active: boolean
  last_sync_at: string | null
  created_at: string
}

export function useBankConnections() {
  const [connections, setConnections] = useState<BankConnection[]>([])
  const [loading, setLoading] = useState(false)

  const fetchConnections = useCallback(async () => {
    setLoading(true)
    try {
      const { data } = await api.get<BankConnection[]>('/api/banks')
      setConnections(data)
    } finally {
      setLoading(false)
    }
  }, [])

  const createConnection = async (body: {
    bank_name: string
    auth_type: string
    credentials: Record<string, string>
    account_number: string
  }): Promise<BankConnection> => {
    const { data } = await api.post<BankConnection>('/api/banks', body)
    setConnections(prev => [data, ...prev])
    return data
  }

  const updateConnection = async (id: number, body: Partial<BankConnection>): Promise<BankConnection> => {
    const { data } = await api.put<BankConnection>(`/api/banks/${id}`, body)
    setConnections(prev => prev.map(c => (c.id === id ? data : c)))
    return data
  }

  const deleteConnection = async (id: number) => {
    await api.delete(`/api/banks/${id}`)
    setConnections(prev => prev.filter(c => c.id !== id))
  }

  const syncConnection = async (id: number): Promise<{ imported: number; skipped: number; total: number }> => {
    const { data } = await api.post<{ imported: number; skipped: number; total: number }>(`/api/banks/${id}/sync`)
    return data
  }

  return { connections, loading, fetchConnections, createConnection, updateConnection, deleteConnection, syncConnection }
}
