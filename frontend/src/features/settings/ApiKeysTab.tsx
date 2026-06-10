import { useEffect, useState } from 'react'
import { toast } from 'sonner'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Field } from '@/components/ui/Field'
import { Dialog, DialogSurface, DialogBody, DialogTitle, DialogContent, DialogActions } from '@/components/ui/Dialog'
import { Table, TableHeader, TableBody, TableRow, TableHeaderCell, TableCell } from '@/components/ui/Table'
import { useApiKeys } from '@/hooks/useSettings'

export function ApiKeysTab() {
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
                      appearance="secondary"
                      size="small"
                      onClick={() => handleRevoke(k.id, k.name)}
                      className="text-red-500 border-red-500"
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

      <Dialog open={dialogOpen} onOpenChange={(open) => { if (!open) handleCloseDialog() }}>
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
                    <Button appearance="secondary" size="small" onClick={handleCopy}>
                      {copied ? 'Copied!' : 'Copy'}
                    </Button>
                  </div>
                </div>
              )}
            </DialogContent>
            <DialogActions>
              {!generatedKey ? (
                <>
                  <Button appearance="secondary" onClick={handleCloseDialog} disabled={creating}>
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
