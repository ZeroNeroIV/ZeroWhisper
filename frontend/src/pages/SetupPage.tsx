import { useState, useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { api } from '@/lib/api'
import { Card, Button, Input, Field } from '@fluentui/react-components'
import { Lock, Unlock, Plus, ShieldCheck } from 'lucide-react'

// ── Types ──────────────────────────────────────────────────────────────────────

interface Vault {
  id: string
  name: string
  created_at: string
  is_active: boolean
}

type View =
  | 'loading'
  | 'vaults'
  | 'new-vault'
  | 'unlock-vault'
  | 'recovery-phrase'
  | 'recover'

function getErrorMessage(err: unknown): string {
  const e = err as { response?: { data?: { detail?: string } }; message?: string }
  return e?.response?.data?.detail ?? e?.message ?? 'An unexpected error occurred.'
}

// ── Vault List ─────────────────────────────────────────────────────────────────

function VaultsView({
  vaults,
  onUnlock,
  onNew,
}: {
  vaults: Vault[]
  onUnlock: (vault: Vault) => void
  onNew: () => void
}) {
  const navigate = useNavigate()

  return (
    <div className="space-y-3">
      {vaults.length === 0 && (
        <p className="text-sm text-muted-foreground text-center py-4">
          No vaults yet. Create one to get started.
        </p>
      )}

      {vaults.map((vault) => (
        <div
          key={vault.id}
          className="flex items-center gap-3 rounded-lg border px-4 py-3"
        >
          {vault.is_active
            ? <Unlock size={16} className="text-green-600 shrink-0" />
            : <Lock size={16} className="text-muted-foreground shrink-0" />
          }
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium truncate">{vault.name}</p>
            <p className="text-xs text-muted-foreground">
              {new Date(vault.created_at).toLocaleDateString()}
            </p>
          </div>
          {vault.is_active ? (
            <Button
              size="small"
              appearance="primary"
              onClick={() => navigate('/login')}
            >
              Open
            </Button>
          ) : (
            <Button
              size="small"
              appearance="outline"
              onClick={() => onUnlock(vault)}
            >
              Unlock
            </Button>
          )}
        </div>
      ))}

      <button
        type="button"
        onClick={onNew}
        className="w-full rounded-lg border-2 border-dashed border-muted-foreground/30 px-4 py-3 flex items-center justify-center gap-2 text-sm text-muted-foreground hover:border-primary/50 hover:text-foreground transition-colors"
      >
        <Plus size={15} />
        New vault
      </button>
    </div>
  )
}

// ── New Vault ──────────────────────────────────────────────────────────────────

function NewVaultView({ onDone }: { onDone: (phrase: string) => void }) {
  const [name, setName] = useState('')
  const [passphrase, setPassphrase] = useState('')
  const [confirm, setConfirm] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    if (!name.trim()) { setError('Vault name is required.'); return }
    if (passphrase.length < 8) { setError('Passphrase must be at least 8 characters.'); return }
    if (passphrase !== confirm) { setError('Passphrases do not match.'); return }
    setLoading(true)
    try {
      const { data } = await api.post('/setup/vaults', { name: name.trim(), passphrase })
      onDone(data.recovery_phrase)
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setLoading(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <p className="text-sm text-muted-foreground">
        Each vault is an independent encrypted database with its own passphrase.
      </p>

      <Field label="Vault name">
        <Input
          placeholder="e.g. Personal, Work"
          value={name}
          onChange={e => setName(e.target.value)}
          autoFocus
          className="w-full"
        />
      </Field>

      <Field label="Passphrase">
        <Input
          type="password"
          placeholder="Min. 8 characters"
          value={passphrase}
          onChange={e => setPassphrase(e.target.value)}
          autoComplete="new-password"
          className="w-full"
        />
      </Field>

      <Field label="Confirm passphrase">
        <Input
          type="password"
          placeholder="Repeat passphrase"
          value={confirm}
          onChange={e => setConfirm(e.target.value)}
          autoComplete="new-password"
          className="w-full"
        />
      </Field>

      {error && <p className="text-sm text-red-600">{error}</p>}

      <Button type="submit" appearance="primary" className="w-full" disabled={loading}>
        {loading ? 'Creating…' : 'Create vault'}
      </Button>
    </form>
  )
}

// ── Unlock Vault ───────────────────────────────────────────────────────────────

function UnlockVaultView({
  vault,
  onDone,
  onRecover,
}: {
  vault: Vault
  onDone: () => void
  onRecover: () => void
}) {
  const [passphrase, setPassphrase] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setLoading(true)
    try {
      await api.post(`/setup/vaults/${vault.id}/unlock`, { passphrase })
      navigate('/login')
      onDone()
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setLoading(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <p className="text-sm text-muted-foreground">
        Enter the passphrase for <span className="font-medium text-foreground">"{vault.name}"</span>.
      </p>

      <Field label="Passphrase">
        <Input
          type="password"
          placeholder="Your vault passphrase"
          value={passphrase}
          onChange={e => setPassphrase(e.target.value)}
          autoComplete="current-password"
          autoFocus
          className="w-full"
        />
      </Field>

      {error && <p className="text-sm text-red-600">{error}</p>}

      <Button type="submit" appearance="primary" className="w-full" disabled={loading}>
        {loading ? 'Unlocking…' : 'Unlock'}
      </Button>

      <button
        type="button"
        className="w-full text-xs text-muted-foreground underline underline-offset-4 hover:text-foreground"
        onClick={onRecover}
      >
        Forgot passphrase? Recover with recovery phrase
      </button>
    </form>
  )
}

// ── Recovery Phrase Display ────────────────────────────────────────────────────

function RecoveryPhraseView({ phrase, onContinue }: { phrase: string; onContinue: () => void }) {
  const [copied, setCopied] = useState(false)

  const handleCopy = () => {
    navigator.clipboard.writeText(phrase)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div className="space-y-4">
      <div className="rounded-md bg-amber-50 border border-amber-200 p-3 text-sm text-amber-800 dark:bg-amber-950 dark:border-amber-800 dark:text-amber-300">
        Save this recovery phrase — it will <strong>not</strong> be shown again. Store it somewhere safe offline.
      </div>

      <div
        className="rounded-md bg-muted p-4 font-mono text-sm leading-relaxed break-all cursor-pointer select-all"
        onClick={handleCopy}
        title="Click to copy"
      >
        {phrase}
      </div>

      <Button appearance="outline" className="w-full" onClick={handleCopy}>
        {copied ? 'Copied!' : 'Copy to clipboard'}
      </Button>

      <Button appearance="primary" className="w-full" onClick={onContinue}>
        I've saved my recovery phrase — continue
      </Button>
    </div>
  )
}

// ── Recover Vault ──────────────────────────────────────────────────────────────

function RecoverView({
  vault,
  onDone,
  onBack,
}: {
  vault: Vault | null
  onDone: (phrase: string) => void
  onBack: () => void
}) {
  const [recoveryPhrase, setRecoveryPhrase] = useState('')
  const [newPassphrase, setNewPassphrase] = useState('')
  const [confirm, setConfirm] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    if (newPassphrase.length < 8) { setError('New passphrase must be at least 8 characters.'); return }
    if (newPassphrase !== confirm) { setError('Passphrases do not match.'); return }
    setLoading(true)
    try {
      const url = vault ? `/setup/vaults/${vault.id}/recover` : '/setup/recover'
      const { data } = await api.post(url, {
        recovery_phrase: recoveryPhrase.trim(),
        new_passphrase: newPassphrase,
      })
      onDone(data.new_recovery_phrase ?? data.recovery_phrase)
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setLoading(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <p className="text-sm text-muted-foreground">
        Enter your 24-word BIP39 recovery phrase and set a new passphrase.
      </p>

      <Field label="Recovery phrase (24 words)">
        <textarea
          className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm font-mono min-h-[96px] resize-none focus:outline-none focus:ring-2 focus:ring-ring"
          placeholder="word1 word2 word3 … word24"
          value={recoveryPhrase}
          onChange={e => setRecoveryPhrase(e.target.value)}
        />
      </Field>

      <Field label="New passphrase">
        <Input
          type="password"
          placeholder="Min. 8 characters"
          value={newPassphrase}
          onChange={e => setNewPassphrase(e.target.value)}
          autoComplete="new-password"
          className="w-full"
        />
      </Field>

      <Field label="Confirm new passphrase">
        <Input
          type="password"
          placeholder="Repeat passphrase"
          value={confirm}
          onChange={e => setConfirm(e.target.value)}
          autoComplete="new-password"
          className="w-full"
        />
      </Field>

      {error && <p className="text-sm text-red-600">{error}</p>}

      <Button type="submit" appearance="primary" className="w-full" disabled={loading}>
        {loading ? 'Recovering…' : 'Recover vault'}
      </Button>

      <button
        type="button"
        className="w-full text-xs text-muted-foreground underline underline-offset-4 hover:text-foreground"
        onClick={onBack}
      >
        Back
      </button>
    </form>
  )
}

// ── Page ───────────────────────────────────────────────────────────────────────

export default function SetupPage() {
  const [view, setView] = useState<View>('loading')
  const [vaults, setVaults] = useState<Vault[]>([])
  const [selectedVault, setSelectedVault] = useState<Vault | null>(null)
  const [recoveryPhrase, setRecoveryPhrase] = useState('')
  const [statusError, setStatusError] = useState<string | null>(null)

  const loadVaults = async () => {
    try {
      const [statusRes, vaultsRes] = await Promise.all([
        api.get<{ state: string; db_ready: boolean; active_vault_id: string | null }>('/setup/status'),
        api.get<{ vaults: Vault[] }>('/setup/vaults'),
      ])
      const enriched = vaultsRes.data.vaults.map(v => ({
        ...v,
        is_active: v.id === statusRes.data.active_vault_id,
      }))
      setVaults(enriched)
      setView('vaults')
    } catch {
      setStatusError('Could not reach the server. Is the backend running?')
    }
  }

  useEffect(() => { loadVaults() }, [])

  const titles: Record<View, string> = {
    loading: 'ZeroWhisper',
    vaults: 'Vaults',
    'new-vault': 'New vault',
    'unlock-vault': 'Unlock vault',
    'recovery-phrase': 'Recovery phrase',
    recover: 'Recover vault',
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-background px-4">
      <div className="w-full max-w-sm">
        <Card className="p-6">
          <div className="flex items-center gap-2 mb-6">
            {view !== 'vaults' && view !== 'loading' && (
              <button
                type="button"
                className="text-xs text-muted-foreground underline underline-offset-4 hover:text-foreground mr-auto"
                onClick={() => {
                  if (view === 'recover') {
                    setView(selectedVault ? 'unlock-vault' : 'vaults')
                  } else {
                    setView('vaults')
                  }
                }}
              >
                ← Back
              </button>
            )}
            <h1 className="text-xl font-bold text-center flex-1">{titles[view]}</h1>
            {view === 'vaults' && <ShieldCheck size={18} className="text-muted-foreground" />}
          </div>

          {statusError && (
            <p className="text-sm text-red-600 text-center">{statusError}</p>
          )}

          {view === 'loading' && !statusError && (
            <p className="text-sm text-muted-foreground text-center">Checking status…</p>
          )}

          {view === 'vaults' && (
            <VaultsView
              vaults={vaults}
              onUnlock={(vault) => { setSelectedVault(vault); setView('unlock-vault') }}
              onNew={() => setView('new-vault')}
            />
          )}

          {view === 'new-vault' && (
            <NewVaultView
              onDone={(phrase) => {
                setRecoveryPhrase(phrase)
                setView('recovery-phrase')
                loadVaults()
              }}
            />
          )}

          {view === 'unlock-vault' && selectedVault && (
            <UnlockVaultView
              vault={selectedVault}
              onDone={() => loadVaults()}
              onRecover={() => setView('recover')}
            />
          )}

          {view === 'recovery-phrase' && (
            <RecoveryPhraseView
              phrase={recoveryPhrase}
              onContinue={() => setView('vaults')}
            />
          )}

          {view === 'recover' && (
            <RecoverView
              vault={selectedVault}
              onDone={(phrase) => {
                setRecoveryPhrase(phrase)
                setView('recovery-phrase')
              }}
              onBack={() => setView(selectedVault ? 'unlock-vault' : 'vaults')}
            />
          )}

          {view !== 'recovery-phrase' && (
            <p className="mt-6 text-center text-xs text-muted-foreground">
              <Link to="/login" className="underline underline-offset-4 hover:text-foreground">
                Back to login
              </Link>
            </p>
          )}
        </Card>
      </div>
    </div>
  )
}
