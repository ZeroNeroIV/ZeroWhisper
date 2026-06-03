import { useState, useRef, useEffect } from 'react'
import { toast } from 'sonner'
import {
  Button,
  Dialog,
  DialogSurface,
  DialogBody,
  DialogTitle,
  DialogContent,
  DialogActions,
  Field,
  Input,
  Select,
} from '@fluentui/react-components'
import type { TransactionFormData } from '@/types/transaction'
import type { Category } from '@/types/category'

interface TransactionFormProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  initialData?: Partial<TransactionFormData>
  onSubmit: (data: TransactionFormData) => Promise<void>
  title?: string
  categories: Category[]
}

function FormContent({
  initialData,
  onSubmit,
  onOpenChange,
  title,
  categories,
}: {
  initialData?: Partial<TransactionFormData>
  onSubmit: (data: TransactionFormData) => Promise<void>
  onOpenChange: (open: boolean) => void
  title: string
  categories: Category[]
}) {
  const [amount, setAmount] = useState(
    initialData?.amount_original != null ? String(initialData.amount_original) : ''
  )
  const [currency, setCurrency] = useState(initialData?.currency_original ?? 'JOD')
  const [category, setCategory] = useState(initialData?.category ?? '')
  const [description, setDescription] = useState(initialData?.description ?? '')
  const [date, setDate] = useState(initialData?.transaction_date ?? '')
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
            <Select value={currency} onChange={(e) => setCurrency(e.target.value)}>
              <option value="JOD">JOD</option>
              <option value="USD">USD</option>
            </Select>
          </Field>
          <Field label="Category">
            <Select value={category} onChange={(e) => setCategory(e.target.value)}>
              <option value="">Select a category</option>
              {categories.map((cat) => (
                <option key={cat.id} value={cat.name}>
                  {cat.icon ? `${cat.icon} ${cat.name}` : cat.name}
                </option>
              ))}
            </Select>
          </Field>
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
        <Button appearance="outline" onClick={() => onOpenChange(false)} disabled={saving}>
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
    <Dialog open={open} onOpenChange={(_, data) => { if (!data.open) onOpenChange(false) }}>
      <DialogSurface key={resetKey}>
        <FormContent
          initialData={initialData}
          onSubmit={onSubmit}
          onOpenChange={onOpenChange}
          title={title}
          categories={categories}
        />
      </DialogSurface>
    </Dialog>
  )
}