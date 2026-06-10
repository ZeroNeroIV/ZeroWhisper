import { useCallback, useState } from 'react'
import { api } from '@/lib/api'

export type AiProvider = 'openai' | 'gemini' | 'groq'

export interface AiSettings {
  ai_provider: AiProvider
  openai_api_key: string
  openai_model: string
  gemini_api_key: string
  gemini_model: string
  groq_api_key: string
  groq_model: string
  local_whisper_model: string
  ai_ready: boolean
  transcription_ready: boolean
  transcription_backend: string
  model: string
}

export type AiSettingsPatch = Record<string, string | null>

export function useAiSettings() {
  const [settings, setSettings] = useState<AiSettings | null>(null)
  const [loading, setLoading] = useState(true)

  const fetchSettings = useCallback(async () => {
    setLoading(true)
    try {
      const { data } = await api.get<AiSettings>('/api/ai-settings')
      setSettings(data)
      return data
    } finally {
      setLoading(false)
    }
  }, [])

  const saveSettings = useCallback(async (patch: AiSettingsPatch) => {
    const { data } = await api.put<AiSettings>('/api/ai-settings', patch)
    setSettings(data)
    return data
  }, [])

  return { settings, loading, fetchSettings, saveSettings }
}
