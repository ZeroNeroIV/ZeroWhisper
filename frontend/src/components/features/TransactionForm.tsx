import { useEffect } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { toast } from 'sonner'
import {
  Dialog,
  DialogSurface,
  DialogBody,
  DialogTitle,
  DialogContent,
  DialogActions,
  Field,
  Input,
  Select,
  Option,
  Button,
} from '@fluentui/react-components'
import type { TransactionFormData } from '@/types/transaction'
import { VALID_CATEGORIES, VALID_CURRENCIES } from '@/types/transaction'

const formSchema = z.object({
  amount_original: z.number({ error: 'Amount is required' }).positive('Amount must be positive'),
  currency_original: z.enum(['JOD', 'USD']),
  category: z.string().nonempty('Category is required'),
  description: z.string().optional(),
  transaction_date: z.string().nonempty('Date is required'),
})

type FormSchema = z.infer<typeof formSchema>

interface TransactionFormProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  initialData?: Partial<TransactionFormData>
  onSubmit: (data: TransactionFormData) => Promise<void>
  title?: string
}

export function TransactionForm({
  open,
  onOpenChange,
  initialData,
  onSubmit,
  title = 'Transaction',
}: TransactionFormProps) {
  const {
    register,
    handleSubmit,
    setValue,
    watch,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<FormSchema>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      amount_original: initialData?.amount_original ?? undefined,
      currency_original: initialData?.currency_original ?? 'JOD',
      category: initialData?.category ?? '',
      description: initialData?.description ?? '',
      transaction_date: initialData?.transaction_date ?? '',
    },
  })

  const currencyValue = watch('currency_original')
  const categoryValue = watch('category')

  useEffect(() => {
    if (open) {
      reset({
        amount_original: initialData?.amount_original ?? undefined,
        currency_original: initialData?.currency_original ?? 'JOD',
        category: initialData?.category ?? '',
        description: initialData?.description ?? '',
        transaction_date: initialData?.transaction_date ?? '',
      })
    }
  }, [open, initialData, reset])

  const handleFormSubmit = async (values: FormSchema) => {
    try {
      await onSubmit(values as TransactionFormData)
      onOpenChange(false)
    } catch {
      toast.error('Failed to save transaction')
    }
  }

  return (
    <Dialog open={open} onOpenChange={(_, data) => onOpenChange(data.open)}>
      <DialogSurface>
        <DialogBody>
          <DialogTitle>{title}</DialogTitle>
          <DialogContent>
            <form id="transaction-form" onSubmit={handleSubmit(handleFormSubmit)} className="space-y-4 pt-2">
              <Field
                label="Amount"
                validationMessage={errors.amount_original?.message}
                validationState={errors.amount_original ? 'error' : 'none'}
              >
                <Input
                  type="number"
                  step="0.01"
                  placeholder="0.00"
                  {...register('amount_original', { valueAsNumber: true })}
                />
              </Field>

              <Field
                label="Currency"
                validationMessage={errors.currency_original?.message}
                validationState={errors.currency_original ? 'error' : 'none'}
              >
                <Select
                  value={currencyValue}
                  onChange={(_, data) => setValue('currency_original', data.value as 'JOD' | 'USD')}
                >
                  {VALID_CURRENCIES.map((currency) => (
                    <Option key={currency} value={currency}>
                      {currency}
                    </Option>
                  ))}
                </Select>
              </Field>

              <Field
                label="Category"
                validationMessage={errors.category?.message}
                validationState={errors.category ? 'error' : 'none'}
              >
                <Select
                  value={categoryValue}
                  onChange={(_, data) => setValue('category', data.value)}
                >
                  {VALID_CATEGORIES.map((category) => (
                    <Option key={category} value={category}>
                      {category}
                    </Option>
                  ))}
                </Select>
              </Field>

              <Field
                label="Description (optional)"
                validationMessage={errors.description?.message}
                validationState={errors.description ? 'error' : 'none'}
              >
                <Input placeholder="Enter description" {...register('description')} />
              </Field>

              <Field
                label="Date"
                validationMessage={errors.transaction_date?.message}
                validationState={errors.transaction_date ? 'error' : 'none'}
              >
                <Input type="date" {...register('transaction_date')} />
              </Field>
            </form>
          </DialogContent>
          <DialogActions>
            <Button
              appearance="outline"
              onClick={() => onOpenChange(false)}
              disabled={isSubmitting}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              form="transaction-form"
              appearance="primary"
              disabled={isSubmitting}
            >
              {isSubmitting ? 'Saving...' : 'Save'}
            </Button>
          </DialogActions>
        </DialogBody>
      </DialogSurface>
    </Dialog>
  )
}
