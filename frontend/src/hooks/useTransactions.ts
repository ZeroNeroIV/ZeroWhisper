import { useState, useCallback } from 'react'
import { api } from '@/lib/api'
import type { Transaction, TransactionFormData } from '@/types/transaction'

interface Filters {
  page?: number
  page_size?: number
  category?: string
  date_from?: string
  date_to?: string
  wallet_id?: string
  type?: string
}

export function useTransactions() {
  const [transactions, setTransactions] = useState<Transaction[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchTransactions = useCallback(async (filters: Filters = {}) => {
    setLoading(true)
    setError(null)
    try {
      const params = { page: 1, page_size: 20, ...filters }
      const { data } = await api.get('/api/transactions', { params })
      setTransactions(data.items)
      setTotal(data.total)
    } catch {
      setError('Failed to load transactions')
    } finally {
      setLoading(false)
    }
  }, [])

  const createTransaction = async (body: TransactionFormData) => {
    const { data } = await api.post('/api/transactions', body)
    return data as Transaction
  }

  const updateTransaction = async (id: string, body: Partial<TransactionFormData>) => {
    const { data } = await api.put(`/api/transactions/${id}`, body)
    return data as Transaction
  }

  const deleteTransaction = async (id: string) => {
    await api.delete(`/api/transactions/${id}`)
  }

  return { transactions, total, loading, error, fetchTransactions, createTransaction, updateTransaction, deleteTransaction }
}
