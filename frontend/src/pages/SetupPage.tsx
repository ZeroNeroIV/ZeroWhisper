import { useState, useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { api } from '@/lib/api'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'

// ── Types ──────────────────────────────────────────────────────────────────────

type SetupStatus =
  | { state: 'UNINITIALIZED' }
  | { state: 'INITIALIZED'; db_ready: boolean }

type View = 'loading' | 'initialize' | 'recovery-phrase' | 'unlock' | 'recover' | 'ready'

// ── Helpers ────────────────────────────────────────────────────────────────────

function getErrorMessage(err: unknown): string {
  const e = err as { response?: { data?: { detail?: string } }; message?: string }
  return e?.response?.data?.detail ?? e?.message ?? 'An unexpected error occurred.'
}

// ── Sub-views ──────────────────────────────────────────────────────────────────

function InitializeView({ onDone }: { onDone: (phrase: string) => void }) {
  const [passphrase, setPassphrase] = useState('')
  const [confirm, setConfirm] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    if (passphrase.length < 8) {
      setError('Passphrase must be at least 8 characters.')
      return
    }
    if (passphrase !== confirm) {
      setError('Passphrases do not match.')
      return
    }
    setLoading(true)
    try {
      const { data } = await api.post('/setup/initialize', { passphrase })
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
        Choose a strong passphrase to encrypt your database. You will need it every time the
        server restarts.
      </p>

      <div className="space-y-2">
        <label className="text-sm font-medium">Passphrase</label>
        <Input
          type="password"
          placeholder="Min. 8 characters"
          value={passphrase}
          onChange={(e) => setPassphrase(e.target.value)}
          autoComplete="new-password"
        />
      </div>

      <div className="space-y-2">
        <label className="text-sm font-medium">Confirm passphrase</label>
        <Input
          type="password"
          placeholder="Repeat passphrase"
          value={confirm}
          onChange={(e) => setConfirm(e.target.value)}
          autoComplete="new-password"
        />
      </div>

      {error && <p className="text-sm font-medium text-destructive">{error}</p>}

      <Button type="submit" className="w-full" disabled={loading}>
        {loading ? 'Initializing…' : 'Initialize database'}
      </Button>
    </form>
  )
}

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
        Save this recovery phrase now — it will not be shown again. Store it somewhere safe
        offline.
      </div>

      <div
        className="rounded-md bg-muted p-4 font-mono text-sm leading-relaxed break-all cursor-pointer select-all"
        onClick={handleCopy}
        title="Click to copy"
      >
        {phrase}
      </div>

      <Button variant="outline" size="sm" className="w-full" onClick={handleCopy}>
        {copied ? 'Copied!' : 'Copy to clipboard'}
      </Button>

      <Button className="w-full" onClick={onContinue}>
        I've saved my recovery phrase — continue
      </Button>
    </div>
  )
}

function UnlockView({ onDone }: { onDone: () => void }) {
  const [passphrase, setPassphrase] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setLoading(true)
    try {
      await api.post('/setup/unlock', { passphrase })
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
        The database exists but the key is not loaded. Enter your passphrase to unlock it.
      </p>

      <div className="space-y-2">
        <label className="text-sm font-medium">Passphrase</label>
        <Input
          type="password"
          placeholder="Your database passphrase"
          value={passphrase}
          onChange={(e) => setPassphrase(e.target.value)}
          autoComplete="current-password"
          autoFocus
        />
      </div>

      {error && <p className="text-sm font-medium text-destructive">{error}</p>}

      <Button type="submit" className="w-full" disabled={loading}>
        {loading ? 'Unlocking…' : 'Unlock database'}
      </Button>
    </form>
  )
}

function RecoverView({ onDone }: { onDone: (phrase: string) => void }) {
  const [recoveryPhrase, setRecoveryPhrase] = useState('')
  const [newPassphrase, setNewPassphrase] = useState('')
  const [confirm, setConfirm] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    if (newPassphrase.length < 8) {
      setError('New passphrase must be at least 8 characters.')
      return
    }
    if (newPassphrase !== confirm) {
      setError('Passphrases do not match.')
      return
    }
    setLoading(true)
    try {
      const { data } = await api.post('/setup/recover', {
        recovery_phrase: recoveryPhrase.trim(),
        new_passphrase: newPassphrase,
      })
      onDone(data.new_recovery_phrase)
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

      <div className="space-y-2">
        <label className="text-sm font-medium">Recovery phrase (24 words)</label>
        <textarea
          className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm font-mono min-h-[96px] resize-none focus:outline-none focus:ring-2 focus:ring-ring"
          placeholder="word1 word2 word3 … word24"
          value={recoveryPhrase}
          onChange={(e) => setRecoveryPhrase(e.target.value)}
        />
      </div>

      <div className="space-y-2">
        <label className="text-sm font-medium">New passphrase</label>
        <Input
          type="password"
          placeholder="Min. 8 characters"
          value={newPassphrase}
          onChange={(e) => setNewPassphrase(e.target.value)}
          autoComplete="new-password"
        />
      </div>

      <div className="space-y-2">
        <label className="text-sm font-medium">Confirm new passphrase</label>
        <Input
          type="password"
          placeholder="Repeat passphrase"
          value={confirm}
          onChange={(e) => setConfirm(e.target.value)}
          autoComplete="new-password"
        />
      </div>

      {error && <p className="text-sm font-medium text-destructive">{error}</p>}

      <Button type="submit" className="w-full" disabled={loading}>
        {loading ? 'Recovering…' : 'Recover database'}
      </Button>
    </form>
  )
}

function ReadyView() {
  return (
    <div className="space-y-4 text-center">
      <p className="text-sm text-muted-foreground">
        The database is unlocked and ready.
      </p>
      <Link to="/login">
        <Button className="w-full">Go to login</Button>
      </Link>
    </div>
  )
}

// ── Page ───────────────────────────────────────────────────────────────────────

export default function SetupPage() {
  const navigate = useNavigate()
  const [view, setView] = useState<View>('loading')
  const [recoveryPhrase, setRecoveryPhrase] = useState('')
  const [statusError, setStatusError] = useState<string | null>(null)

  useEffect(() => {
    api
      .get<SetupStatus>('/setup/status')
      .then(({ data }) => {
        if (data.state === 'UNINITIALIZED') {
          setView('initialize')
        } else if (data.db_ready) {
          setView('ready')
        } else {
          setView('unlock')
        }
      })
      .catch(() => setStatusError('Could not reach the server. Is the backend running?'))
  }, [])

  const title: Record<View, string> = {
    loading: 'ZeroWhisper',
    initialize: 'Initialize database',
    'recovery-phrase': 'Your recovery phrase',
    unlock: 'Unlock database',
    recover: 'Recover database',
    ready: 'Database ready',
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-background px-4">
      <div className="w-full max-w-sm">
        <Card>
          <CardHeader className="text-center">
            <CardTitle className="text-2xl">{title[view]}</CardTitle>
          </CardHeader>

          <CardContent>
            {statusError && (
              <p className="text-sm text-destructive text-center">{statusError}</p>
            )}

            {view === 'loading' && !statusError && (
              <p className="text-sm text-muted-foreground text-center">Checking status…</p>
            )}

            {view === 'initialize' && (
              <InitializeView
                onDone={(phrase) => {
                  setRecoveryPhrase(phrase)
                  setView('recovery-phrase')
                }}
              />
            )}

            {view === 'recovery-phrase' && (
              <RecoveryPhraseView
                phrase={recoveryPhrase}
                onContinue={() => navigate('/login')}
              />
            )}

            {view === 'unlock' && (
              <>
                <UnlockView onDone={() => navigate('/login')} />
                <button
                  type="button"
                  className="mt-4 w-full text-xs text-muted-foreground underline underline-offset-4 hover:text-foreground"
                  onClick={() => setView('recover')}
                >
                  Forgot passphrase? Recover with recovery phrase
                </button>
              </>
            )}

            {view === 'recover' && (
              <>
                <RecoverView
                  onDone={(phrase) => {
                    setRecoveryPhrase(phrase)
                    setView('recovery-phrase')
                  }}
                />
                <button
                  type="button"
                  className="mt-4 w-full text-xs text-muted-foreground underline underline-offset-4 hover:text-foreground"
                  onClick={() => setView('unlock')}
                >
                  Back to unlock
                </button>
              </>
            )}

            {view === 'ready' && <ReadyView />}

            {view !== 'recovery-phrase' && (
              <p className="mt-6 text-center text-xs text-muted-foreground">
                <Link
                  to="/login"
                  className="underline underline-offset-4 hover:text-foreground"
                >
                  Back to login
                </Link>
              </p>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
