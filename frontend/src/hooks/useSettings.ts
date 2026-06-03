import { useState, useCallback } from 'react'
import { api } from '@/lib/api'

export interface ApiKey {
  id: number
  name: string
  prefix: string
  is_active: boolean
  last_used_at: string | null
  created_at: string
}

export interface ExchangeRate {
  id: number
  date: string
  jod_per_usd: string
  source: string
  created_at: string
}

export function useApiKeys() {
  const [keys, setKeys] = useState<ApiKey[]>([])
  const [loading, setLoading] = useState(false)

  const fetchKeys = useCallback(async () => {
    setLoading(true)
    try {
      const { data } = await api.get<ApiKey[]>('/api/api-keys')
      setKeys(data)
    } finally {
      setLoading(false)
    }
  }, [])

  const createKey = async (name: string): Promise<{ key: string; prefix: string }> => {
    const { data } = await api.post<{ id: number; name: string; prefix: string; key: string }>(
      '/api/api-keys',
      { name }
    )
    return { key: data.key, prefix: data.prefix }
  }

  const revokeKey = async (id: number) => {
    await api.delete(`/api/api-keys/${id}`)
    setKeys((prev) => prev.filter((k) => k.id !== id))
  }

  return { keys, loading, fetchKeys, createKey, revokeKey }
}

export function useExchangeRates() {
  const [current, setCurrent] = useState<ExchangeRate | null>(null)
  const [history, setHistory] = useState<ExchangeRate[]>([])
  const [loading, setLoading] = useState(false)

  const fetchRates = useCallback(async () => {
    setLoading(true)
    try {
      const [cur, hist] = await Promise.all([
        api.get<ExchangeRate>('/api/exchange-rates/current').catch(() => ({ data: null })),
        api.get<ExchangeRate[]>('/api/exchange-rates/history'),
      ])
      setCurrent(cur.data)
      setHistory(hist.data)
    } finally {
      setLoading(false)
    }
  }, [])

  const setRate = async (rate: number, date: string): Promise<ExchangeRate> => {
    const { data } = await api.post<ExchangeRate>('/api/exchange-rates', { rate, date })
    return data
  }

  const toggleAutoFetch = async (enabled: boolean): Promise<{ auto_fetch: boolean }> => {
    const { data } = await api.put<{ auto_fetch: boolean }>('/api/exchange-rates/auto-fetch', {
      enabled,
    })
    return data
  }

  return { current, history, loading, fetch: fetchRates, setRate, toggleAutoFetch }
}

export interface FxSettings {
  fx_api_url: string
  fx_api_key: string
}

export function useExchangeRateSettings() {
  const [settings, setSettings] = useState<FxSettings | null>(null)
  const [loading, setLoading] = useState(false)

  const fetchSettings = useCallback(async () => {
    setLoading(true)
    try {
      const { data } = await api.get<FxSettings>('/api/exchange-rates/settings')
      setSettings(data)
    } finally {
      setLoading(false)
    }
  }, [])

  const updateSettings = async (patch: Partial<FxSettings>) => {
    const { data } = await api.put<FxSettings>('/api/exchange-rates/settings', patch)
    setSettings(data)
    return data
  }

  return { settings, loading, fetchSettings, updateSettings }
}
