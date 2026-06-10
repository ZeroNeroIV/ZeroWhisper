import { useEffect, useMemo, useState } from 'react'
import { Button } from '@/components/ui/Button'
import { Dialog, DialogActions, DialogBody, DialogContent, DialogSurface, DialogTitle } from '@/components/ui/Dialog'
import { Field } from '@/components/ui/Field'
import { Input } from '@/components/ui/Input'
import { Select } from '@/components/ui/Select'
import { Switch } from '@/components/ui/Switch'
import { ArrowLeftRight, Archive, ArchiveRestore, Pencil, Plus, Trash2 } from 'lucide-react'
import { toast } from 'sonner'
import { useWallets } from '@/hooks/useWallets'
import {
  WALLET_TYPE_ICONS,
  WALLET_TYPE_LABELS,
  type Wallet,
  type WalletType,
} from '@/types/wallet'
import { ConfirmDialog } from '@/components/ui/ConfirmDialog'
import { apiErrorDetail } from '@/lib/api'

const WALLET_TYPES = Object.keys(WALLET_TYPE_LABELS) as WalletType[]

interface WalletDialogState {
  open: boolean
  editing: Wallet | null
}

export default function WalletsPage() {
  const { wallets, loading, fetchWallets, createWallet, updateWallet, deleteWallet, transfer } =
    useWallets()

  const [showArchived, setShowArchived] = useState(false)
  const [dialog, setDialog] = useState<WalletDialogState>({ open: false, editing: null })
  const [transferOpen, setTransferOpen] = useState(false)
  const [deleteTarget, setDeleteTarget] = useState<Wallet | null>(null)

  useEffect(() => { fetchWallets(showArchived) }, [fetchWallets, showArchived])

  const activeWallets = wallets.filter((w) => w.is_active)
  const totalBalance = activeWallets.reduce((sum, w) => sum + parseFloat(w.balance), 0)

  const grouped = useMemo(() => {
    const groups = new Map<WalletType, Wallet[]>()
    for (const type of WALLET_TYPES) {
      const items = wallets.filter((w) => w.type === type)
      if (items.length) groups.set(type, items)
    }
    return groups
  }, [wallets])

  const handleArchiveToggle = async (wallet: Wallet) => {
    try {
      await updateWallet(wallet.id, { is_active: !wallet.is_active })
      toast.success(wallet.is_active ? 'Wallet archived' : 'Wallet restored')
      fetchWallets(showArchived)
    } catch (err: unknown) {
      toast.error(apiErrorDetail(err) || 'Failed to update wallet')
    }
  }

  const confirmDelete = async () => {
    if (!deleteTarget) return
    try {
      await deleteWallet(deleteTarget.id)
      toast.success('Wallet deleted')
    } catch (err: unknown) {
      toast.error(apiErrorDetail(err) || 'Failed to delete wallet')
    }
    setDeleteTarget(null)
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between gap-2 flex-wrap">
        <div>
          <h1 className="text-2xl font-bold">Wallets</h1>
          <p className="text-sm text-muted-foreground">
            Total: <span className="font-semibold text-foreground">{totalBalance.toFixed(2)} JOD</span>
            {' '}across {activeWallets.length} active wallet{activeWallets.length !== 1 ? 's' : ''}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Switch
            label="Show archived"
            checked={showArchived}
            onChange={(checked) => setShowArchived(checked)}
          />
          <Button
            appearance="secondary"
            onClick={() => setTransferOpen(true)}
            disabled={activeWallets.length < 2}
            title={activeWallets.length < 2 ? 'You need at least two wallets to transfer' : 'Transfer between wallets'}
          >
            <ArrowLeftRight size={16} />
            Transfer
          </Button>
          <Button appearance="primary" onClick={() => setDialog({ open: true, editing: null })}>
            <Plus size={16} />
            Add Wallet
          </Button>
        </div>
      </div>

      {loading ? (
        <div className="text-center py-8 text-muted-foreground">Loading...</div>
      ) : wallets.length === 0 ? (
        <div className="text-center py-12 text-muted-foreground space-y-2">
          <p>No wallets yet.</p>
          <p className="text-xs">
            Create wallets for your held money, digital accounts, and savings — then move money
            between them and track every balance.
          </p>
        </div>
      ) : (
        [...grouped.entries()].map(([type, items]) => (
          <section key={type} className="space-y-2">
            <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wide">
              {WALLET_TYPE_ICONS[type]} {WALLET_TYPE_LABELS[type]}
            </h2>
            <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
              {items.map((wallet) => (
                <div
                  key={wallet.id}
                  className={`rounded-lg border p-4 space-y-2 transition-colors hover:bg-muted/30 ${
                    wallet.is_active ? '' : 'opacity-60'
                  }`}
                >
                  <div className="flex items-center justify-between gap-2">
                    <span className="text-sm font-medium truncate">
                      {wallet.icon ? `${wallet.icon} ` : ''}{wallet.name}
                    </span>
                    {!wallet.is_active && (
                      <span className="text-[10px] rounded bg-muted px-1.5 py-0.5 text-muted-foreground">archived</span>
                    )}
                  </div>
                  <p className="text-2xl font-semibold">
                    {parseFloat(wallet.balance).toFixed(2)}
                    <span className="text-xs text-muted-foreground ml-1.5">JOD</span>
                  </p>
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-muted-foreground">{wallet.currency} wallet</span>
                    <div className="flex items-center gap-0.5">
                      <Button
                        appearance="ghost"
                        onClick={() => setDialog({ open: true, editing: wallet })}
                        aria-label="Edit wallet"
                      >
                        <Pencil size={14} />
                      </Button>
                      <Button
                        appearance="ghost"
                        onClick={() => handleArchiveToggle(wallet)}
                        aria-label={wallet.is_active ? 'Archive wallet' : 'Restore wallet'}
                        title={wallet.is_active ? 'Archive' : 'Restore'}
                      >
                        {wallet.is_active ? <Archive size={14} /> : <ArchiveRestore size={14} />}
                      </Button>
                      <Button
                        appearance="ghost"
                        onClick={() => setDeleteTarget(wallet)}
                        aria-label="Delete wallet"
                        className="text-red-500"
                      >
                        <Trash2 size={14} />
                      </Button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </section>
        ))
      )}

      <WalletDialog
        key={dialog.editing?.id ?? 'new'}
        state={dialog}
        onClose={() => setDialog({ open: false, editing: null })}
        onSave={async (data) => {
          if (dialog.editing) {
            await updateWallet(dialog.editing.id, data)
            toast.success('Wallet updated')
          } else {
            await createWallet(data)
            toast.success('Wallet created')
          }
          fetchWallets(showArchived)
        }}
      />

      <TransferDialog
        open={transferOpen}
        wallets={activeWallets}
        onClose={() => setTransferOpen(false)}
        onTransfer={async (data) => {
          await transfer(data)
          toast.success('Transfer complete')
          fetchWallets(showArchived)
          window.dispatchEvent(new CustomEvent('transaction-created'))
        }}
      />

      <ConfirmDialog
        open={deleteTarget !== null}
        onOpenChange={(open) => { if (!open) setDeleteTarget(null) }}
        title="Delete wallet?"
        message={`Delete "${deleteTarget?.name ?? ''}"? Wallets with transactions can't be deleted — archive them instead.`}
        confirmLabel="Delete"
        destructive
        onConfirm={confirmDelete}
      />
    </div>
  )
}

function WalletDialog({
  state,
  onClose,
  onSave,
}: {
  state: WalletDialogState
  onClose: () => void
  onSave: (data: {
    name: string
    type: WalletType
    currency: 'JOD' | 'USD'
    initial_balance?: string
    icon?: string
  }) => Promise<void>
}) {
  const editing = state.editing
  const [name, setName] = useState(editing?.name ?? '')
  const [type, setType] = useState<WalletType>(editing?.type ?? 'cash')
  const [currency, setCurrency] = useState<'JOD' | 'USD'>((editing?.currency as 'JOD' | 'USD') ?? 'JOD')
  const [initialBalance, setInitialBalance] = useState(editing ? parseFloat(editing.initial_balance).toString() : '0')
  const [icon, setIcon] = useState(editing?.icon ?? '')
  const [saving, setSaving] = useState(false)

  const handleSave = async () => {
    if (!name.trim()) { toast.error('Name is required'); return }
    const balanceNum = parseFloat(initialBalance || '0')
    if (Number.isNaN(balanceNum)) { toast.error('Starting balance must be a number'); return }
    setSaving(true)
    try {
      await onSave({
        name: name.trim(),
        type,
        currency,
        initial_balance: String(balanceNum),
        icon: icon.trim() || undefined,
      })
      onClose()
    } catch (err: unknown) {
      toast.error(apiErrorDetail(err) || 'Failed to save wallet')
    } finally {
      setSaving(false)
    }
  }

  return (
    <Dialog open={state.open} onOpenChange={(open) => { if (!open) onClose() }}>
      <DialogSurface>
        <DialogBody>
          <DialogTitle>{editing ? 'Edit Wallet' : 'Add Wallet'}</DialogTitle>
          <DialogContent>
            <div className="space-y-4 pt-2">
              <Field label="Name">
                <Input value={name} onChange={(e) => setName(e.target.value)} placeholder="e.g. Family Savings" />
              </Field>
              <Field label="Type">
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
                  {WALLET_TYPES.map((t) => (
                    <button
                      key={t}
                      type="button"
                      onClick={() => setType(t)}
                      className={`rounded-lg border-2 px-2 py-2 text-xs font-medium transition-colors ${
                        type === t ? 'border-primary bg-primary/5 text-primary' : 'border-border'
                      }`}
                    >
                      {WALLET_TYPE_ICONS[t]} {WALLET_TYPE_LABELS[t]}
                    </button>
                  ))}
                </div>
              </Field>
              <Field label="Currency">
                <Select value={currency} onChange={(e) => setCurrency(e.target.value as 'JOD' | 'USD')}>
                  <option value="JOD">JOD</option>
                  <option value="USD">USD</option>
                </Select>
              </Field>
              <Field label="Starting balance (JOD)">
                <Input
                  type="number"
                  step="0.01"
                  value={initialBalance}
                  onChange={(e) => setInitialBalance(e.target.value)}
                />
              </Field>
              <Field label="Icon (emoji, optional)">
                <Input value={icon} onChange={(e) => setIcon(e.target.value)} placeholder="💵" maxLength={10} />
              </Field>
            </div>
          </DialogContent>
          <DialogActions>
            <Button appearance="secondary" onClick={onClose} disabled={saving}>Cancel</Button>
            <Button appearance="primary" onClick={handleSave} disabled={saving}>
              {saving ? 'Saving...' : 'Save'}
            </Button>
          </DialogActions>
        </DialogBody>
      </DialogSurface>
    </Dialog>
  )
}

function TransferDialog({
  open,
  wallets,
  onClose,
  onTransfer,
}: {
  open: boolean
  wallets: Wallet[]
  onClose: () => void
  onTransfer: (data: {
    from_wallet_id: string
    to_wallet_id: string
    amount_original: string
    currency_original: 'JOD' | 'USD'
    transaction_date?: string
    description?: string
  }) => Promise<void>
}) {
  const [fromId, setFromId] = useState('')
  const [toId, setToId] = useState('')
  const [amount, setAmount] = useState('')
  const [currency, setCurrency] = useState<'JOD' | 'USD'>('JOD')
  const [date, setDate] = useState('')
  const [description, setDescription] = useState('')
  const [saving, setSaving] = useState(false)

  const handleTransfer = async () => {
    if (!fromId || !toId) { toast.error('Pick both wallets'); return }
    if (fromId === toId) { toast.error('Source and destination must differ'); return }
    const amountNum = parseFloat(amount)
    if (!amount || Number.isNaN(amountNum) || amountNum <= 0) {
      toast.error('Amount must be positive'); return
    }
    setSaving(true)
    try {
      await onTransfer({
        from_wallet_id: fromId,
        to_wallet_id: toId,
        amount_original: amount,
        currency_original: currency,
        transaction_date: date || undefined,
        description: description.trim() || undefined,
      })
      setFromId(''); setToId(''); setAmount(''); setDate(''); setDescription('')
      onClose()
    } catch (err: unknown) {
      toast.error(apiErrorDetail(err) || 'Transfer failed')
    } finally {
      setSaving(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={(open) => { if (!open) onClose() }}>
      <DialogSurface>
        <DialogBody>
          <DialogTitle>Transfer Between Wallets</DialogTitle>
          <DialogContent>
            <div className="space-y-4 pt-2">
              <Field label="From">
                <Select value={fromId} onChange={(e) => setFromId(e.target.value)}>
                  <option value="">Select source wallet</option>
                  {wallets.map((w) => (
                    <option key={w.id} value={w.id} disabled={w.id === toId}>
                      {w.icon ? `${w.icon} ` : ''}{w.name} ({parseFloat(w.balance).toFixed(2)} JOD)
                    </option>
                  ))}
                </Select>
              </Field>
              <Field label="To">
                <Select value={toId} onChange={(e) => setToId(e.target.value)}>
                  <option value="">Select destination wallet</option>
                  {wallets.map((w) => (
                    <option key={w.id} value={w.id} disabled={w.id === fromId}>
                      {w.icon ? `${w.icon} ` : ''}{w.name} ({parseFloat(w.balance).toFixed(2)} JOD)
                    </option>
                  ))}
                </Select>
              </Field>
              <div className="flex gap-2">
                <Field label="Amount" className="flex-1">
                  <Input type="number" step="0.01" placeholder="0.00" value={amount} onChange={(e) => setAmount(e.target.value)} />
                </Field>
                <Field label="Currency">
                  <Select value={currency} onChange={(e) => setCurrency(e.target.value as 'JOD' | 'USD')}>
                    <option value="JOD">JOD</option>
                    <option value="USD">USD</option>
                  </Select>
                </Field>
              </div>
              <Field label="Date (optional, defaults to today)">
                <Input type="date" value={date} onChange={(e) => setDate(e.target.value)} />
              </Field>
              <Field label="Description (optional)">
                <Input value={description} onChange={(e) => setDescription(e.target.value)} placeholder="e.g. monthly savings top-up" />
              </Field>
            </div>
          </DialogContent>
          <DialogActions>
            <Button appearance="secondary" onClick={onClose} disabled={saving}>Cancel</Button>
            <Button appearance="primary" onClick={handleTransfer} disabled={saving}>
              {saving ? 'Transferring...' : 'Transfer'}
            </Button>
          </DialogActions>
        </DialogBody>
      </DialogSurface>
    </Dialog>
  )
}
