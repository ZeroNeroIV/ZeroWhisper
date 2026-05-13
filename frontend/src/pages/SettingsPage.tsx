import { useEffect, useState } from 'react'
import { toast } from 'sonner'
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from '@/components/ui/dialog'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { useApiKeys, useExchangeRates } from '@/hooks/useSettings'

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
    // Refresh keys list after closing so new key appears
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
        <Button onClick={handleOpenDialog}>Generate New Key</Button>
      </div>

      {loading ? (
        <p className="text-sm text-muted-foreground">Loading keys…</p>
      ) : keys.length === 0 ? (
        <p className="text-sm text-muted-foreground">No API keys yet.</p>
      ) : (
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Name</TableHead>
              <TableHead>Key</TableHead>
              <TableHead>Created</TableHead>
              <TableHead>Last Used</TableHead>
              <TableHead></TableHead>
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
                    variant="destructive"
                    size="sm"
                    onClick={() => handleRevoke(k.id, k.name)}
                  >
                    Revoke
                  </Button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      )}

      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Generate New API Key</DialogTitle>
            <DialogDescription>
              Give your key a name to identify it later.
            </DialogDescription>
          </DialogHeader>

          {!generatedKey ? (
            <>
              <div className="space-y-2">
                <Label htmlFor="key-name">Key Name</Label>
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
              </div>
              <DialogFooter>
                <Button variant="outline" onClick={() => setDialogOpen(false)} disabled={creating}>
                  Cancel
                </Button>
                <Button onClick={handleCreate} disabled={creating}>
                  {creating ? 'Creating…' : 'Create'}
                </Button>
              </DialogFooter>
            </>
          ) : (
            <div className="space-y-4">
              <p className="text-sm font-medium text-destructive">
                Save this key — it won't be shown again.
              </p>
              <div className="flex items-center gap-2">
                <code className="flex-1 overflow-x-auto rounded border bg-muted px-3 py-2 text-sm">
                  {generatedKey}
                </code>
                <Button variant="outline" size="sm" onClick={handleCopy}>
                  {copied ? 'Copied!' : 'Copy'}
                </Button>
              </div>
              <DialogFooter>
                <Button onClick={handleCloseDialog}>Done</Button>
              </DialogFooter>
            </div>
          )}
        </DialogContent>
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
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Current Rate</CardTitle>
        </CardHeader>
        <CardContent>
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
        </CardContent>
      </Card>

      {/* Set rate form */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Set Rate</CardTitle>
          <CardDescription>Manually set a JOD per USD exchange rate.</CardDescription>
        </CardHeader>
        <CardContent>
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
            <Button onClick={handleSetRate} disabled={saving} className="shrink-0">
              {saving ? 'Saving…' : 'Save'}
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Auto-fetch toggle */}
      <Card>
        <CardContent className="pt-6">
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
        </CardContent>
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
                <TableHead>Date</TableHead>
                <TableHead>Rate (JOD/USD)</TableHead>
                <TableHead>Source</TableHead>
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
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Change Password</CardTitle>
          <CardDescription>Update your account password.</CardDescription>
        </CardHeader>
        <CardContent>
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
            <Button type="submit" disabled={submitting}>
              {submitting ? 'Saving…' : 'Change Password'}
            </Button>
          </form>
        </CardContent>
      </Card>

      {/* Recovery Phrase */}
      <Card className="opacity-60">
        <CardHeader>
          <CardTitle className="text-base">Recovery Phrase</CardTitle>
          <CardDescription>
            Recovery phrase can be viewed after entering your passphrase.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <p className="mb-4 text-sm text-muted-foreground">
            Recovery phrase display — coming soon.
          </p>
          <Button disabled variant="outline">
            View Recovery Phrase
          </Button>
        </CardContent>
      </Card>
    </div>
  )
}

// ─── About Tab ────────────────────────────────────────────────────────────────

function AboutTab() {
  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>ZeroWhisper</CardTitle>
          <CardDescription>Version 0.1.0</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="text-sm text-muted-foreground">
            Self-hosted personal financial manager with encrypted storage.
          </p>
          <div>
            <p className="mb-2 text-sm font-semibold">Tech Stack</p>
            <ul className="space-y-1 text-sm text-muted-foreground">
              <li>FastAPI</li>
              <li>SQLCipher</li>
              <li>React</li>
              <li>Shadcn UI</li>
              <li>OpenAI</li>
            </ul>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

// ─── Main Page ────────────────────────────────────────────────────────────────

export default function SettingsPage() {
  return (
    <div className="mx-auto max-w-3xl space-y-6 p-6">
      <h1 className="text-2xl font-bold">Settings</h1>
      <Tabs defaultValue="api-keys">
        <TabsList className="mb-4">
          <TabsTrigger value="api-keys">API Keys</TabsTrigger>
          <TabsTrigger value="exchange-rates">Exchange Rates</TabsTrigger>
          <TabsTrigger value="security">Security</TabsTrigger>
          <TabsTrigger value="about">About</TabsTrigger>
        </TabsList>

        <TabsContent value="api-keys">
          <ApiKeysTab />
        </TabsContent>

        <TabsContent value="exchange-rates">
          <ExchangeRatesTab />
        </TabsContent>

        <TabsContent value="security">
          <SecurityTab />
        </TabsContent>

        <TabsContent value="about">
          <AboutTab />
        </TabsContent>
      </Tabs>
    </div>
  )
}
