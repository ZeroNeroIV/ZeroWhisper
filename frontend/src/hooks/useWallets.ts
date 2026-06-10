import { useState, useCallback } from 'react'
import { api, apiErrorDetail } from '@/lib/api'
import type { Wallet, WalletFormData, TransferFormData } from '@/types/wallet'

export function useWallets() {
  const [wallets, setWallets] = useState<Wallet[]>([])
  const [loading, setLoading] = useState(false)

  const fetchWallets = useCallback(async (includeInactive = false) => {
    setLoading(true)
    try {
      const { data } = await api.get<Wallet[]>('/api/wallets', {
        params: includeInactive ? { include_inactive: true } : undefined,
      })
      setWallets(data)
    } catch (err: unknown) {
      console.error('Failed to fetch wallets:', err)
      const { toast } = await import('sonner')
      toast.error(apiErrorDetail(err) || 'Failed to load wallets')
    } finally {
      setLoading(false)
    }
  }, [])

  const createWallet = async (body: WalletFormData): Promise<Wallet> => {
    const { data } = await api.post<Wallet>('/api/wallets', body)
    setWallets((prev) => [...prev, data])
    return data
  }

  const updateWallet = async (id: string, body: Partial<WalletFormData> & { is_active?: boolean }): Promise<Wallet> => {
    const { data } = await api.patch<Wallet>(`/api/wallets/${id}`, body)
    setWallets((prev) => prev.map((w) => (w.id === id ? data : w)))
    return data
  }

  const deleteWallet = async (id: string) => {
    await api.delete(`/api/wallets/${id}`)
    setWallets((prev) => prev.filter((w) => w.id !== id))
  }

  const transfer = async (body: TransferFormData) => {
    const { data } = await api.post('/api/wallets/transfer', body)
    return data
  }

  return { wallets, loading, fetchWallets, createWallet, updateWallet, deleteWallet, transfer }
}
