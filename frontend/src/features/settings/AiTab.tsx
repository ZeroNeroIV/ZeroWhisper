import { useEffect, useState } from 'react'
import { toast } from 'sonner'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Label } from '@/components/ui/Label'
import { Card } from '@/components/ui/Card'
import { useAiSettings, type AiProvider } from '@/hooks/useAiSettings'

// Suggestions only — the backend accepts any free-form model name.
const OPENAI_MODELS = ['gpt-4o-mini', 'gpt-4o', 'gpt-4.1-mini', 'gpt-4.1', 'o3-mini', 'o4-mini']
const GEMINI_MODELS = ['gemini-2.5-flash', 'gemini-2.5-pro', 'gemini-2.0-flash', 'gemma-3-27b-it', 'gemma-3-12b-it']
const GROQ_MODELS   = ['llama-3.3-70b-versatile', 'llama-3.1-8b-instant', 'mixtral-8x7b-32768', 'gemma2-9b-it', 'gemma-7b-it']
const WHISPER_SIZES = ['tiny', 'base', 'small', 'medium', 'large-v3']

function ModelInput({ id, value, onChange, list }: {
  id: string
  value: string
  onChange: (v: string) => void
  list: string[]
}) {
  const listId = `${id}-list`
  return (
    <>
      <input
        id={id}
        type="text"
        list={listId}
        value={value}
        onChange={e => onChange(e.target.value)}
        placeholder="Type or choose a model name"
        className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
        autoComplete="off"
        spellCheck={false}
      />
      <datalist id={listId}>
        {list.map(m => <option key={m} value={m} />)}
      </datalist>
    </>
  )
}

function StatusBadge({ ok, label }: { ok: boolean; label: string }) {
  return (
    <div className="flex items-center gap-2">
      <span className={`w-2 h-2 rounded-full shrink-0 ${ok ? 'bg-green-500' : 'bg-amber-400'}`} />
      <span className="text-sm">{label}</span>
    </div>
  )
}

export function AiTab() {
  const { settings: cfg, loading, fetchSettings, saveSettings } = useAiSettings()
  const [saving, setSaving] = useState(false)

  // Editable fields — keys left blank = keep current
  const [provider, setProvider] = useState<AiProvider>('openai')
  const [openaiKey, setOpenaiKey] = useState('')
  const [openaiModel, setOpenaiModel] = useState('gpt-4o-mini')
  const [geminiKey, setGeminiKey] = useState('')
  const [geminiModel, setGeminiModel] = useState('gemini-2.5-flash')
  const [groqKey, setGroqKey] = useState('')
  const [groqModel, setGroqModel] = useState('llama-3.3-70b-versatile')
  const [localModel, setLocalModel] = useState('small')

  useEffect(() => {
    fetchSettings()
      .then((data) => {
        setProvider(data.ai_provider)
        setOpenaiModel(data.openai_model)
        setGeminiModel(data.gemini_model)
        setGroqModel(data.groq_model)
        setLocalModel(data.local_whisper_model)
        // Don't pre-fill key fields — user types to update
      })
      .catch(() => toast.error('Failed to load AI settings.'))
  }, [fetchSettings])

  const handleSave = async () => {
    setSaving(true)
    try {
      await saveSettings({
        ai_provider: provider,
        openai_model: openaiModel,
        gemini_model: geminiModel,
        groq_model: groqModel,
        local_whisper_model: localModel,
        // Only send key if user typed something; null = keep existing
        openai_api_key: openaiKey || null,
        gemini_api_key: geminiKey || null,
        groq_api_key: groqKey || null,
      })
      setOpenaiKey('')
      setGeminiKey('')
      setGroqKey('')
      toast.success('AI settings saved.')
    } catch {
      toast.error('Failed to save AI settings.')
    } finally {
      setSaving(false)
    }
  }

  if (loading && !cfg) return <p className="text-sm text-muted-foreground">Loading…</p>

  return (
    <div className="space-y-6">

      {/* Status */}
      {cfg && (
        <Card className="p-4">
          <h3 className="text-base font-semibold mb-3">Status</h3>
          <div className="grid grid-cols-2 gap-3 text-sm">
            <div>
              <p className="text-xs text-muted-foreground mb-1">Active model</p>
              <code className="text-xs bg-muted px-1.5 py-0.5 rounded">{cfg.model}</code>
            </div>
            <div>
              <p className="text-xs text-muted-foreground mb-1">Transcription</p>
              <code className="text-xs bg-muted px-1.5 py-0.5 rounded">{cfg.transcription_backend}</code>
            </div>
            <StatusBadge ok={cfg.ai_ready} label={cfg.ai_ready ? 'Expense parsing ready' : 'Expense parsing — no API key'} />
            <StatusBadge ok={cfg.transcription_ready} label="Voice transcription ready" />
          </div>
        </Card>
      )}

      {/* Provider */}
      <Card className="p-4 space-y-4">
        <h3 className="text-base font-semibold">LLM Provider</h3>

        <div className="grid grid-cols-3 gap-2">
          {(['openai', 'gemini', 'groq'] as AiProvider[]).map(p => (
            <button
              key={p}
              type="button"
              onClick={() => setProvider(p)}
              className={`rounded-lg border-2 px-3 py-2.5 text-sm font-medium transition-colors capitalize ${
                provider === p ? 'border-primary bg-primary/5 text-primary' : 'border-border hover:border-muted-foreground/50'
              }`}
            >
              {p === 'openai' ? 'OpenAI' : p === 'gemini' ? 'Gemini' : 'Groq'}
            </button>
          ))}
        </div>

        {/* OpenAI */}
        {provider === 'openai' && (
          <div className="space-y-3">
            <div className="space-y-1.5">
              <Label htmlFor="openai-key">API Key</Label>
              <Input
                id="openai-key"
                type="password"
                placeholder={cfg?.openai_api_key || 'sk-… (leave blank to keep current)'}
                value={openaiKey}
                onChange={e => setOpenaiKey(e.target.value)}
                autoComplete="off"
              />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="openai-model">Model</Label>
              <ModelInput id="openai-model" value={openaiModel} onChange={setOpenaiModel} list={OPENAI_MODELS} />
            </div>
          </div>
        )}

        {/* Gemini */}
        {provider === 'gemini' && (
          <div className="space-y-3">
            <div className="space-y-1.5">
              <Label htmlFor="gemini-key">API Key</Label>
              <Input
                id="gemini-key"
                type="password"
                placeholder={cfg?.gemini_api_key || 'AIza… (leave blank to keep current)'}
                value={geminiKey}
                onChange={e => setGeminiKey(e.target.value)}
                autoComplete="off"
              />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="gemini-model">Model</Label>
              <ModelInput id="gemini-model" value={geminiModel} onChange={setGeminiModel} list={GEMINI_MODELS} />
            </div>
          </div>
        )}

        {/* Groq */}
        {provider === 'groq' && (
          <div className="space-y-3">
            <p className="text-xs text-muted-foreground">
              Groq provides a free tier. Get a key at console.groq.com. Uses <code className="bg-muted px-1 rounded">llama-3.3-70b-versatile</code> for expense parsing and <code className="bg-muted px-1 rounded">whisper-large-v3</code> for transcription.
            </p>
            <div className="space-y-1.5">
              <Label htmlFor="groq-key">API Key</Label>
              <Input
                id="groq-key"
                type="password"
                placeholder={cfg?.groq_api_key || 'gsk_… (leave blank to keep current)'}
                value={groqKey}
                onChange={e => setGroqKey(e.target.value)}
                autoComplete="off"
              />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="groq-model">Model</Label>
              <ModelInput id="groq-model" value={groqModel} onChange={setGroqModel} list={GROQ_MODELS} />
            </div>
          </div>
        )}
      </Card>

      {/* Voice transcription */}
      <Card className="p-4 space-y-3">
        <div>
          <h3 className="text-base font-semibold">Voice Transcription</h3>
          <p className="text-xs text-muted-foreground mt-0.5">
            Groq key → Groq (free). OpenAI key → OpenAI. Neither → local faster-whisper (offline, ~484 MB download on first use).
          </p>
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="groq-transcription-key">Groq Key (for free cloud transcription)</Label>
          <Input
            id="groq-transcription-key"
            type="password"
            placeholder={cfg?.groq_api_key || 'gsk_… (leave blank to keep current)'}
            value={groqKey}
            onChange={e => setGroqKey(e.target.value)}
            autoComplete="off"
          />
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="local-model">Local Whisper model (offline fallback)</Label>
          <ModelInput id="local-model" value={localModel} onChange={setLocalModel} list={WHISPER_SIZES} />
        </div>
      </Card>

      <Button appearance="primary" onClick={handleSave} disabled={saving}>
        {saving ? 'Saving…' : 'Save Settings'}
      </Button>
    </div>
  )
}
