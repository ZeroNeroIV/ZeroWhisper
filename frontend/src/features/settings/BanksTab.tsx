import { useEffect, useState } from 'react'
import { toast } from 'sonner'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Field } from '@/components/ui/Field'
import { Card } from '@/components/ui/Card'
import { Dialog, DialogSurface, DialogBody, DialogTitle, DialogContent, DialogActions } from '@/components/ui/Dialog'
import { useBankConnections, type BankConnection } from '@/hooks/useBankConnections'

const BANK_NAMES = ['Etihad Bank', 'Bank of Jordan', 'Arab Bank', 'Jordan Islamic Bank', 'HBTF', 'Cairo Amman Bank', 'Other']

export function BanksTab() {
  const { connections, loading, fetchConnections, createConnection, updateConnection, deleteConnection, syncConnection } = useBankConnections()

  const [dialogOpen, setDialogOpen] = useState(false)
  const [formName, setFormName] = useState('')
  const [formAuthType, setFormAuthType] = useState<'api_key' | 'basic'>('api_key')
  const [formApiUrl, setFormApiUrl] = useState('')
  const [formApiKey, setFormApiKey] = useState('')
  const [formUsername, setFormUsername] = useState('')
  const [formPassword, setFormPassword] = useState('')
  const [formAccount, setFormAccount] = useState('')
  const [saving, setSaving] = useState(false)
  const [syncingId, setSyncingId] = useState<number | null>(null)

  useEffect(() => {
    fetchConnections()
  }, [fetchConnections])

  const openCreate = () => {
    setFormName('')
    setFormAuthType('api_key')
    setFormApiUrl('')
    setFormApiKey('')
    setFormUsername('')
    setFormPassword('')
    setFormAccount('')
    setDialogOpen(true)
  }

  const handleCreate = async () => {
    if (!formName.trim()) { toast.error('Bank name is required.'); return }
    setSaving(true)
    try {
      const credentials: Record<string, string> = {}
      if (formAuthType === 'basic') {
        credentials.api_url = formApiUrl
        credentials.username = formUsername
        credentials.password = formPassword
      } else {
        credentials.api_url = formApiUrl
        credentials.api_key = formApiKey
      }
      await createConnection({
        bank_name: formName.trim(),
        auth_type: formAuthType,
        credentials,
        account_number: formAccount.trim(),
      })
      toast.success('Bank connection created.')
      setDialogOpen(false)
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : 'Failed to create connection.')
    } finally {
      setSaving(false)
    }
  }

  const handleToggle = async (conn: BankConnection) => {
    try {
      await updateConnection(conn.id, { is_active: !conn.is_active })
      toast.success(conn.is_active ? 'Disabled.' : 'Enabled.')
    } catch {
      toast.error('Failed to update.')
    }
  }

  const handleDelete = async (conn: BankConnection) => {
    try {
      await deleteConnection(conn.id)
      toast.success('Connection removed.')
    } catch {
      toast.error('Failed to delete.')
    }
  }

  const handleSync = async (conn: BankConnection) => {
    setSyncingId(conn.id)
    try {
      const result = await syncConnection(conn.id)
      toast.success(`Synced: ${result.imported} imported, ${result.skipped} skipped.`)
      await fetchConnections()
    } catch {
      toast.error('Sync failed.')
    } finally {
      setSyncingId(null)
    }
  }

  const formatDate = (iso: string | null) => {
    if (!iso) return 'Never'
    return new Date(iso).toLocaleDateString()
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold">Bank Connections</h2>
        <Button appearance="primary" onClick={openCreate}>Add Bank</Button>
      </div>

      {loading ? (
        <p className="text-sm text-muted-foreground">Loading…</p>
      ) : connections.length === 0 ? (
        <p className="text-sm text-muted-foreground">No bank connections yet.</p>
      ) : (
        <div className="space-y-2">
          {connections.map((conn) => (
            <Card key={conn.id} className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium">{conn.bank_name}</p>
                  <p className="text-xs text-muted-foreground">
                    {conn.account_number} · {conn.auth_type} · Last sync: {formatDate(conn.last_sync_at)}
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <Button
                    size="small"
                    appearance="secondary"
                    disabled={syncingId === conn.id}
                    onClick={() => handleSync(conn)}
                  >
                    {syncingId === conn.id ? 'Syncing…' : 'Sync'}
                  </Button>
                  <label className="relative inline-flex cursor-pointer items-center">
                    <input
                      type="checkbox"
                      className="peer sr-only"
                      checked={conn.is_active}
                      onChange={() => handleToggle(conn)}
                    />
                    <div className="peer h-5 w-9 rounded-full bg-muted after:absolute after:left-[1px] after:top-[1px] after:h-[18px] after:w-[18px] after:rounded-full after:border after:border-gray-300 after:bg-white after:transition-all after:content-[''] peer-checked:bg-primary peer-checked:after:translate-x-full peer-checked:after:border-white" />
                  </label>
                  <Button
                    size="small"
                    appearance="ghost"
                    className="text-red-500"
                    onClick={() => handleDelete(conn)}
                  >
                    Remove
                  </Button>
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}

      <Dialog open={dialogOpen} onOpenChange={(open) => { if (!open) setDialogOpen(false) }}>
        <DialogSurface>
          <DialogBody>
            <DialogTitle>Add Bank Connection</DialogTitle>
            <DialogContent>
              <div className="space-y-4 pt-2">
                <Field label="Bank Name">
                  <div className="flex flex-wrap gap-2 mb-2">
                    {BANK_NAMES.map((name) => (
                      <button
                        key={name}
                        type="button"
                        onClick={() => setFormName(name === formName ? '' : name)}
                        className={`rounded-lg border px-3 py-1.5 text-xs font-medium transition-colors ${
                          formName === name ? 'border-primary bg-primary/5 text-primary' : 'border-border hover:border-muted-foreground/50'
                        }`}
                      >
                        {name}
                      </button>
                    ))}
                  </div>
                  <Input
                    value={formName}
                    onChange={(e) => setFormName(e.target.value)}
                    placeholder="Or type a custom name…"
                  />
                </Field>

                <Field label="Account Number">
                  <Input
                    value={formAccount}
                    onChange={(e) => setFormAccount(e.target.value)}
                    placeholder="e.g. 1234567890"
                  />
                </Field>

                <Field label="Auth Type">
                  <div className="grid grid-cols-2 gap-2">
                    {(['api_key', 'basic'] as const).map((t) => (
                      <button
                        key={t}
                        type="button"
                        onClick={() => setFormAuthType(t)}
                        className={`rounded-lg border-2 px-3 py-2 text-sm font-medium capitalize transition-colors ${
                          formAuthType === t ? 'border-primary bg-primary/5 text-primary' : 'border-border'
                        }`}
                      >
                        {t === 'api_key' ? 'API Key' : 'Basic Auth'}
                      </button>
                    ))}
                  </div>
                </Field>

                <Field label="API URL">
                  <Input
                    value={formApiUrl}
                    onChange={(e) => setFormApiUrl(e.target.value)}
                    placeholder="https://api.bank.com/transactions"
                  />
                </Field>

                {formAuthType === 'basic' ? (
                  <>
                    <Field label="Username">
                      <Input
                        value={formUsername}
                        onChange={(e) => setFormUsername(e.target.value)}
                        autoComplete="off"
                      />
                    </Field>
                    <Field label="Password">
                      <Input
                        type="password"
                        value={formPassword}
                        onChange={(e) => setFormPassword(e.target.value)}
                        autoComplete="off"
                      />
                    </Field>
                  </>
                ) : (
                  <Field label="API Key">
                    <Input
                      type="password"
                      value={formApiKey}
                      onChange={(e) => setFormApiKey(e.target.value)}
                      autoComplete="off"
                    />
                  </Field>
                )}
              </div>
            </DialogContent>
            <DialogActions>
              <Button appearance="secondary" onClick={() => setDialogOpen(false)} disabled={saving}>
                Cancel
              </Button>
              <Button appearance="primary" onClick={handleCreate} disabled={saving}>
                {saving ? 'Saving…' : 'Add'}
              </Button>
            </DialogActions>
          </DialogBody>
        </DialogSurface>
      </Dialog>
    </div>
  )
}
