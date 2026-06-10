import { useState, useRef, useEffect } from 'react'
import { toast } from 'sonner'
import { Button } from '@/components/ui/Button'
import { Dialog, DialogSurface, DialogBody, DialogTitle, DialogContent, DialogActions } from '@/components/ui/Dialog'
import { Field } from '@/components/ui/Field'
import { Input } from '@/components/ui/Input'
import { Select } from '@/components/ui/Select'
import type { TransactionFormData } from '@/types/transaction'
import type { Category } from '@/types/category'
import type { Wallet } from '@/types/wallet'

interface TransactionFormProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  initialData?: Partial<TransactionFormData>
  onSubmit: (data: TransactionFormData) => Promise<void>
  title?: string
  categories: Category[]
  wallets?: Wallet[]
}

function categoryLabel(cat: Category) {
  return cat.icon ? `${cat.icon} ${cat.name}` : cat.name
}

/** Top-level categories first, each followed by its indented sub-categories. */
function CategoryOptions({ categories }: { categories: Category[] }) {
  const selectable = categories.filter((c) => c.type !== 'transfer')
  const roots = selectable.filter((c) => !c.parent_id)
  const childrenOf = (id: string) => selectable.filter((c) => c.parent_id === id)
  return (
    <>
      {roots.map((root) => (
        <optgroup key={root.id} label={categoryLabel(root)}>
          <option value={root.name}>{categoryLabel(root)}</option>
          {childrenOf(root.id).map((child) => (
            <option key={child.id} value={child.name}>
              {'  '}↳ {categoryLabel(child)}
            </option>
          ))}
        </optgroup>
      ))}
    </>
  )
}

function FormContent({
  initialData,
  onSubmit,
  onOpenChange,
  title,
  categories,
  wallets,
}: {
  initialData?: Partial<TransactionFormData>
  onSubmit: (data: TransactionFormData) => Promise<void>
  onOpenChange: (open: boolean) => void
  title: string
  categories: Category[]
  wallets: Wallet[]
}) {
  const [amount, setAmount] = useState(
    initialData?.amount_original != null ? String(initialData.amount_original) : ''
  )
  const [currency, setCurrency] = useState(initialData?.currency_original ?? 'JOD')
  const [category, setCategory] = useState(initialData?.category ?? '')
  const [description, setDescription] = useState(initialData?.description ?? '')
  const [date, setDate] = useState(initialData?.transaction_date ?? '')
  const [walletId, setWalletId] = useState(initialData?.wallet_id ?? '')
  const [saving, setSaving] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!amount || parseFloat(amount) <= 0) {
      toast.error('Amount must be positive')
      return
    }
    if (!category) {
      toast.error('Category is required')
      return
    }
    if (!date) {
      toast.error('Date is required')
      return
    }
    setSaving(true)
    try {
      await onSubmit({
        amount_original: parseFloat(amount),
        currency_original: currency as 'JOD' | 'USD',
        category,
        description: description || undefined,
        transaction_date: date,
        wallet_id: walletId || undefined,
      })
      onOpenChange(false)
    } catch {
      toast.error('Failed to save transaction')
    } finally {
      setSaving(false)
    }
  }

  return (
    <DialogBody>
      <DialogTitle>{title}</DialogTitle>
      <DialogContent>
        <form id="tx-form" onSubmit={handleSubmit} className="space-y-4 pt-2">
          <Field label="Amount">
            <Input
              type="number"
              step="0.01"
              placeholder="0.00"
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
            />
          </Field>
          <Field label="Currency">
            <Select value={currency} onChange={(e) => setCurrency(e.target.value as 'JOD' | 'USD')}>
              <option value="JOD">JOD</option>
              <option value="USD">USD</option>
            </Select>
          </Field>
          <Field label="Category">
            <Select value={category} onChange={(e) => setCategory(e.target.value)}>
              <option value="">Select a category</option>
              <CategoryOptions categories={categories} />
            </Select>
          </Field>
          {wallets.length > 0 && (
            <Field label="Wallet (optional)">
              <Select value={walletId ?? ''} onChange={(e) => setWalletId(e.target.value)}>
                <option value="">No wallet</option>
                {wallets.filter((w) => w.is_active).map((w) => (
                  <option key={w.id} value={w.id}>
                    {w.icon ? `${w.icon} ` : ''}{w.name}
                  </option>
                ))}
              </Select>
            </Field>
          )}
          <Field label="Description (optional)">
            <Input
              type="text"
              placeholder="Enter description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
            />
          </Field>
          <Field label="Date">
            <Input
              type="date"
              value={date}
              onChange={(e) => setDate(e.target.value)}
            />
          </Field>
        </form>
      </DialogContent>
      <DialogActions>
        <Button appearance="secondary" onClick={() => onOpenChange(false)} disabled={saving}>
          Cancel
        </Button>
        <Button appearance="primary" type="submit" form="tx-form" disabled={saving}>
          {saving ? 'Saving...' : 'Save'}
        </Button>
      </DialogActions>
    </DialogBody>
  )
}

export function TransactionForm({
  open,
  onOpenChange,
  initialData,
  onSubmit,
  title = 'Transaction',
  categories,
  wallets = [],
}: TransactionFormProps) {
  const [resetKey, setResetKey] = useState(0)
  const prevOpen = useRef(open)

  useEffect(() => {
    if (open && !prevOpen.current) {
      setResetKey((k) => k + 1)
    }
    prevOpen.current = open
  }, [open])

  return (
    <Dialog open={open} onOpenChange={(open) => { if (!open) onOpenChange(false) }}>
      <DialogSurface key={resetKey}>
        <FormContent
          initialData={initialData}
          onSubmit={onSubmit}
          onOpenChange={onOpenChange}
          title={title}
          categories={categories}
          wallets={wallets}
        />
      </DialogSurface>
    </Dialog>
  )
}