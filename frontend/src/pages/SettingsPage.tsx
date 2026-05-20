import { useEffect, useState } from 'react'
import { toast } from 'sonner'
import {
  TabList,
  Tab,
  Button,
  Input,
  Label,
  Card,
  Dialog,
  DialogSurface,
  DialogBody,
  DialogTitle,
  DialogContent,
  DialogActions,
  Table,
  TableHeader,
  TableBody,
  TableRow,
  TableHeaderCell,
  TableCell,
  Field,
} from '@fluentui/react-components'
import { useApiKeys, useExchangeRates } from '@/hooks/useSettings'
import { api } from '@/lib/api'

// ─── API Keys Tab ─────────────────────────────────────────────────────────────

function ApiKeysTab() {
  const { keys, loading, fetchKeys, createKey, revokeKey } = useApiKeys()

  const [dialogOpen, setDialogOpen] = useState(false)
  const [newKeyName, setNewKeyName] = useState('')
  const [creating, setCreating] = useState(false)
  const [generatedKey, setGeneratedKey] = useState<string | null>(null)
  const [copied, setCopied] = useState(false)

  useEffect(() => {
    fetchKeys()
  }, [fetchKeys])

  const handleOpenDialog = () => {
    setNewKeyName('')
    setGeneratedKey(null)
    setCopied(false)
    setDialogOpen(true)
  }

  const handleCloseDialog = () => {
    setDialogOpen(false)
    setGeneratedKey(null)
    setCopied(false)
    fetchKeys()
  }

  const handleCreate = async () => {
    if (!newKeyName.trim()) {
      toast.error('Key name is required.')
      return
    }
    setCreating(true)
    try {
      const result = await createKey(newKeyName.trim())
      setGeneratedKey(result.key)
      toast.success('API key created.')
    } catch {
      toast.error('Failed to create API key.')
    } finally {
      setCreating(false)
    }
  }

  const handleCopy = () => {
    if (generatedKey) {
      navigator.clipboard.writeText(generatedKey).then(() => {
        setCopied(true)
        toast.success('Copied to clipboard!')
      })
    }
  }

  const handleRevoke = async (id: number, name: string) => {
    try {
      await revokeKey(id)
      toast.success(`API key "${name}" revoked.`)
    } catch {
      toast.error('Failed to revoke API key.')
    }
  }

  const formatDate = (iso: string | null) => {
    if (!iso) return 'Never'
    return new Date(iso).toLocaleDateString()
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold">Your API Keys</h2>
        <Button appearance="primary" onClick={handleOpenDialog}>Generate New Key</Button>
      </div>

      {loading ? (
        <p className="text-sm text-muted-foreground">Loading keys…</p>
      ) : keys.length === 0 ? (
        <p className="text-sm text-muted-foreground">No API keys yet.</p>
      ) : (
        <div className="overflow-x-auto">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHeaderCell>Name</TableHeaderCell>
                <TableHeaderCell>Key</TableHeaderCell>
                <TableHeaderCell>Created</TableHeaderCell>
                <TableHeaderCell>Last Used</TableHeaderCell>
                <TableHeaderCell></TableHeaderCell>
              </TableRow>
            </TableHeader>
            <TableBody>
              {keys.map((k) => (
                <TableRow key={k.id}>
                  <TableCell className="font-medium">{k.name}</TableCell>
                  <TableCell>
                    <code className="rounded bg-muted px-1.5 py-0.5 text-xs">
                      {k.prefix}***
                    </code>
                  </TableCell>
                  <TableCell className="text-sm text-muted-foreground">
                    {formatDate(k.created_at)}
                  </TableCell>
                  <TableCell className="text-sm text-muted-foreground">
                    {formatDate(k.last_used_at)}
                  </TableCell>
                  <TableCell>
                    <Button
                      appearance="outline"
                      size="small"
                      onClick={() => handleRevoke(k.id, k.name)}
                      style={{ color: 'var(--colorStatusDangerForeground1)', borderColor: 'var(--colorStatusDangerForeground1)' }}
                    >
                      Revoke
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      )}

      <Dialog open={dialogOpen} onOpenChange={(_, data) => { if (!data.open) handleCloseDialog() }}>
        <DialogSurface>
          <DialogBody>
            <DialogTitle>Generate New API Key</DialogTitle>
            <DialogContent>
              <p className="text-sm text-muted-foreground mb-4">
                Give your key a name to identify it later.
              </p>
              {!generatedKey ? (
                <Field label="Key Name">
                  <Input
                    id="key-name"
                    placeholder="e.g. My Script"
                    value={newKeyName}
                    onChange={(e) => setNewKeyName(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') handleCreate()
                    }}
                    disabled={creating}
                  />
                </Field>
              ) : (
                <div className="space-y-4">
                  <p className="text-sm font-medium text-red-600">
                    Save this key — it won't be shown again.
                  </p>
                  <div className="flex items-center gap-2">
                    <code className="flex-1 overflow-x-auto rounded border bg-muted px-3 py-2 text-sm">
                      {generatedKey}
                    </code>
                    <Button appearance="outline" size="small" onClick={handleCopy}>
                      {copied ? 'Copied!' : 'Copy'}
                    </Button>
                  </div>
                </div>
              )}
            </DialogContent>
            <DialogActions>
              {!generatedKey ? (
                <>
                  <Button appearance="outline" onClick={handleCloseDialog} disabled={creating}>
                    Cancel
                  </Button>
                  <Button appearance="primary" onClick={handleCreate} disabled={creating}>
                    {creating ? 'Creating…' : 'Create'}
                  </Button>
                </>
              ) : (
                <Button appearance="primary" onClick={handleCloseDialog}>Done</Button>
              )}
            </DialogActions>
          </DialogBody>
        </DialogSurface>
      </Dialog>
    </div>
  )
}

// ─── Exchange Rates Tab ───────────────────────────────────────────────────────

function ExchangeRatesTab() {
  const { current, history, loading, fetch, setRate, toggleAutoFetch } = useExchangeRates()

  const [rateInput, setRateInput] = useState('')
  const [dateInput, setDateInput] = useState(() => new Date().toISOString().slice(0, 10))
  const [saving, setSaving] = useState(false)
  const [autoFetch, setAutoFetch] = useState(false)
  const [togglingAuto, setTogglingAuto] = useState(false)

  useEffect(() => {
    fetch()
  }, [fetch])

  const handleSetRate = async () => {
    const parsed = parseFloat(rateInput)
    if (isNaN(parsed) || parsed <= 0) {
      toast.error('Enter a valid positive rate.')
      return
    }
    setSaving(true)
    try {
      await setRate(parsed, dateInput)
      toast.success('Exchange rate saved.')
      await fetch()
      setRateInput('')
    } catch {
      toast.error('Failed to save exchange rate.')
    } finally {
      setSaving(false)
    }
  }

  const handleToggleAutoFetch = async (checked: boolean) => {
    setAutoFetch(checked)
    setTogglingAuto(true)
    try {
      await toggleAutoFetch(checked)
      toast.success(checked ? 'Auto-fetch enabled.' : 'Auto-fetch disabled.')
    } catch {
      setAutoFetch(!checked)
      toast.error('Failed to update auto-fetch setting.')
    } finally {
      setTogglingAuto(false)
    }
  }

  const displayedHistory = history.slice(0, 10)

  return (
    <div className="space-y-6">
      {/* Current rate */}
      <Card className="p-4">
        <h3 className="text-base font-semibold mb-3">Current Rate</h3>
        {loading ? (
          <p className="text-sm text-muted-foreground">Loading…</p>
        ) : current ? (
          <p className="text-lg font-semibold">
            1 USD = <span className="text-primary">{current.jod_per_usd}</span> JOD
            <span className="ml-2 text-xs font-normal text-muted-foreground">
              ({current.date}, via {current.source})
            </span>
          </p>
        ) : (
          <p className="text-sm text-muted-foreground">No rate set.</p>
        )}
      </Card>

      {/* Set rate form */}
      <Card className="p-4">
        <h3 className="text-base font-semibold mb-1">Set Rate</h3>
        <p className="text-sm text-muted-foreground mb-4">Manually set a JOD per USD exchange rate.</p>
        <div className="flex flex-col gap-4 sm:flex-row sm:items-end">
          <div className="flex-1 space-y-1.5">
            <Label htmlFor="rate-input">Rate (JOD per USD)</Label>
            <Input
              id="rate-input"
              type="number"
              step="0.001"
              min="0"
              placeholder="0.709"
              value={rateInput}
              onChange={(e) => setRateInput(e.target.value)}
            />
          </div>
          <div className="flex-1 space-y-1.5">
            <Label htmlFor="date-input">Date</Label>
            <Input
              id="date-input"
              type="date"
              value={dateInput}
              onChange={(e) => setDateInput(e.target.value)}
            />
          </div>
          <Button appearance="primary" onClick={handleSetRate} disabled={saving} className="shrink-0">
            {saving ? 'Saving…' : 'Save'}
          </Button>
        </div>
      </Card>

      {/* Auto-fetch toggle */}
      <Card className="p-4">
        <div className="flex items-center justify-between">
          <div>
            <p className="font-medium">Auto-fetch from Frankfurter API</p>
            <p className="text-sm text-muted-foreground">
              Automatically update exchange rates daily.
            </p>
          </div>
          <label className="relative inline-flex cursor-pointer items-center">
            <input
              type="checkbox"
              className="peer sr-only"
              checked={autoFetch}
              disabled={togglingAuto}
              onChange={(e) => handleToggleAutoFetch(e.target.checked)}
            />
            <div className="peer h-6 w-11 rounded-full bg-muted after:absolute after:left-[2px] after:top-[2px] after:h-5 after:w-5 after:rounded-full after:border after:border-gray-300 after:bg-white after:transition-all after:content-[''] peer-checked:bg-primary peer-checked:after:translate-x-full peer-checked:after:border-white peer-disabled:opacity-50" />
          </label>
        </div>
      </Card>

      {/* Rate history */}
      <div>
        <h3 className="mb-3 font-semibold">Rate History</h3>
        {loading ? (
          <p className="text-sm text-muted-foreground">Loading…</p>
        ) : displayedHistory.length === 0 ? (
          <p className="text-sm text-muted-foreground">No history yet.</p>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHeaderCell>Date</TableHeaderCell>
                <TableHeaderCell>Rate (JOD/USD)</TableHeaderCell>
                <TableHeaderCell>Source</TableHeaderCell>
              </TableRow>
            </TableHeader>
            <TableBody>
              {displayedHistory.map((r) => (
                <TableRow key={r.id}>
                  <TableCell>{r.date}</TableCell>
                  <TableCell>{r.jod_per_usd}</TableCell>
                  <TableCell className="text-muted-foreground">{r.source}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </div>
    </div>
  )
}

// ─── Security Tab ─────────────────────────────────────────────────────────────

function SecurityTab() {
  const [currentPassword, setCurrentPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [submitting, setSubmitting] = useState(false)

  const handleChangePassword = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    if (!currentPassword || !newPassword || !confirmPassword) {
      toast.error('Please fill in all fields.')
      return
    }
    if (newPassword !== confirmPassword) {
      toast.error('New passwords do not match.')
      return
    }
    setSubmitting(true)
    try {
      toast.info('Password change not yet available in this version.')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="space-y-6">
      {/* Change Password */}
      <Card className="p-4">
        <h3 className="text-base font-semibold mb-1">Change Password</h3>
        <p className="text-sm text-muted-foreground mb-4">Update your account password.</p>
        <form onSubmit={handleChangePassword} className="space-y-4">
          <div className="space-y-1.5">
            <Label htmlFor="current-password">Current Password</Label>
            <Input
              id="current-password"
              type="password"
              value={currentPassword}
              onChange={(e) => setCurrentPassword(e.target.value)}
              autoComplete="current-password"
            />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="new-password">New Password</Label>
            <Input
              id="new-password"
              type="password"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              autoComplete="new-password"
            />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="confirm-password">Confirm New Password</Label>
            <Input
              id="confirm-password"
              type="password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              autoComplete="new-password"
            />
          </div>
          <Button type="submit" appearance="primary" disabled={submitting}>
            {submitting ? 'Saving…' : 'Change Password'}
          </Button>
        </form>
      </Card>

      {/* Recovery Phrase */}
      <Card className="p-4 opacity-60">
        <h3 className="text-base font-semibold mb-1">Recovery Phrase</h3>
        <p className="text-sm text-muted-foreground mb-4">
          Recovery phrase can be viewed after entering your passphrase.
        </p>
        <p className="mb-4 text-sm text-muted-foreground">
          Recovery phrase display — coming soon.
        </p>
        <Button appearance="outline" disabled>
          View Recovery Phrase
        </Button>
      </Card>
    </div>
  )
}

// ─── AI Tab ───────────────────────────────────────────────────────────────────

interface AiStatus {
  provider: string
  model: string
  ai_ready: boolean
  transcription_ready: boolean
}

function AiTab() {
  const [status, setStatus] = useState<AiStatus | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.get<AiStatus>('/api/whisper/ai-status')
      .then(r => setStatus(r.data))
      .catch(() => setStatus(null))
      .finally(() => setLoading(false))
  }, [])

  const StatusBadge = ({ ok }: { ok: boolean }) => (
    <span className={`inline-flex items-center gap-1 text-xs font-medium px-2 py-0.5 rounded-full ${ok ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
      <span className={`w-1.5 h-1.5 rounded-full ${ok ? 'bg-green-500' : 'bg-red-500'}`} />
      {ok ? 'Ready' : 'Not configured'}
    </span>
  )

  return (
    <div className="space-y-6">
      <Card className="p-4">
        <h3 className="text-base font-semibold mb-1">AI Provider</h3>
        <p className="text-sm text-muted-foreground mb-4">Configure via environment variables in your .env file.</p>
        {loading ? (
          <p className="text-sm text-muted-foreground">Loading…</p>
        ) : !status ? (
          <p className="text-sm text-red-600">Failed to load AI status.</p>
        ) : (
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <p className="text-muted-foreground mb-1">Provider</p>
              <p className="font-medium capitalize">{status.provider}</p>
            </div>
            <div>
              <p className="text-muted-foreground mb-1">Model</p>
              <code className="text-xs bg-muted px-1.5 py-0.5 rounded">{status.model}</code>
            </div>
            <div>
              <p className="text-muted-foreground mb-1">Expense parsing</p>
              <StatusBadge ok={status.ai_ready} />
            </div>
            <div>
              <p className="text-muted-foreground mb-1">Voice transcription</p>
              <StatusBadge ok={status.transcription_ready} />
            </div>
          </div>
        )}
      </Card>

      <Card className="p-4">
        <h3 className="text-base font-semibold mb-3">Configuration</h3>
        <div className="space-y-3 text-sm">
          <div>
            <p className="font-medium mb-1">OpenAI (default)</p>
            <code className="block bg-muted rounded px-3 py-2 text-xs leading-relaxed whitespace-pre">
              {'AI_PROVIDER=openai\nOPENAI_API_KEY=sk-...\nWHISPER_MODEL=gpt-4o-mini'}
            </code>
          </div>
          <div>
            <p className="font-medium mb-1">Google Gemini</p>
            <code className="block bg-muted rounded px-3 py-2 text-xs leading-relaxed whitespace-pre">
              {'AI_PROVIDER=gemini\nGEMINI_API_KEY=AIza...\nGEMINI_MODEL=gemini-2.5-flash\nOPENAI_API_KEY=sk-...  # still needed for voice'}
            </code>
          </div>
        </div>
      </Card>
    </div>
  )
}

// ─── About Tab ────────────────────────────────────────────────────────────────

function AboutTab() {
  return (
    <div className="space-y-6">
      <Card className="p-4">
        <h3 className="text-lg font-semibold mb-1">ZeroWhisper</h3>
        <p className="text-sm text-muted-foreground mb-4">Version 0.1.0</p>
        <p className="text-sm text-muted-foreground mb-4">
          Self-hosted personal financial manager with encrypted storage.
        </p>
        <div>
          <p className="mb-2 text-sm font-semibold">Tech Stack</p>
          <ul className="space-y-1 text-sm text-muted-foreground">
            <li>FastAPI</li>
            <li>SQLCipher</li>
            <li>React</li>
            <li>Fluent UI v9</li>
            <li>OpenAI / Google Gemini</li>
          </ul>
        </div>
      </Card>
    </div>
  )
}

// ─── Main Page ────────────────────────────────────────────────────────────────

export default function SettingsPage() {
  const [activeTab, setActiveTab] = useState('api-keys')

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <h1 className="text-2xl font-bold">Settings</h1>
      <div className="overflow-x-auto -mx-1 px-1">
        <TabList
          selectedValue={activeTab}
          onTabSelect={(_, d) => setActiveTab(d.value as string)}
          className="mb-4 flex-nowrap"
        >
          <Tab value="api-keys">API Keys</Tab>
          <Tab value="exchange-rates">Rates</Tab>
          <Tab value="security">Security</Tab>
          <Tab value="ai">AI</Tab>
          <Tab value="about">About</Tab>
        </TabList>
      </div>

      {activeTab === 'api-keys' && <ApiKeysTab />}
      {activeTab === 'exchange-rates' && <ExchangeRatesTab />}
      {activeTab === 'security' && <SecurityTab />}
      {activeTab === 'ai' && <AiTab />}
      {activeTab === 'about' && <AboutTab />}
    </div>
  )
}
